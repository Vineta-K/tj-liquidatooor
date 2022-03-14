from web3 import Web3
import json
import time

from bot.constants import (
contract_addresses,
graphql_uri,
rpc_endpoint,
jToken_addresses,
underlying_decimals)

from bot.utils import get_abi, run_graph_query, printv

#Download abis from block explorer
PriceOracle_abi = get_abi(contract_addresses['PriceOracle'])
Joetroller_abi = get_abi(contract_addresses["Joetroller_implementation"])
jWrappedNative_abi = get_abi(jToken_addresses['jAVAX'])
jERC20_abi = get_abi(jToken_addresses["jWETH"])
with open("bot/abi/Liquidatooor.json") as f:
  Liquidator_abi = json.load(f)["abi"]
#Constants
output = False
liq_query = """{
  accounts(where: {health_gt: 0, health_lt: 1, totalBorrowValueInUSD_gt: 0}) {
    id
    health
    totalBorrowValueInUSD
    totalCollateralValueInUSD
  }
}"""

class LiquidatorBot ():
  """
  Liquidator bot that queries graph api, works out liquidation parameters then calls liquidator smart contract in a loop.
  rpc_endpoint (str): endpoint to connect to w3
  * executor_account (str): account to call the liquidator contract from
  * liquidator_contract_address (str): address of liquidator contract.
  If executor contract and liquidator contract address aren't given, the bot will still track underwater accounts bot not attempt to perform the liquidation
  """
  def __init__(self,rpc_endpoint = rpc_endpoint, executor_account = None, liquidator_contract_address=  None):
    #Connect to w3
    w3 = Web3(Web3.HTTPProvider(rpc_endpoint))
    if (w3.isConnected()):
      print ("Successfully connected to w3")
    else:
      print("Connection to w3 failed")

    #Dodgy accounting
    if w3.eth.accounts:
      executor_account = w3.eth.accounts[0] #Pretty sure this needs to be changed for working with mainnet

    #Create contract objects to interact with
    PriceOracle = w3.eth.contract(address = contract_addresses["PriceOracle"], abi = PriceOracle_abi)
    Joetroller = w3.eth.contract(address = contract_addresses["Joetroller"], abi = Joetroller_abi)
    Liquidator = None
    if liquidator_contract_address:
      Liquidator = w3.eth.contract(address = liquidator_contract_address, abi = Liquidator_abi)

    #Print prices of underlying assets as a sanity check
    for symbol in jToken_addresses:
      underlying_price_test = PriceOracle.functions.getUnderlyingPrice(jToken_addresses[symbol]).call()
      print(symbol + ": " + str(underlying_price_test/(1e18*10**(18-underlying_decimals[symbol]))))

    #Get liquidation parameters
    close_factor = Joetroller.functions.closeFactorMantissa().call()/1e18
    liquidation_incentive = Joetroller.functions.liquidationIncentiveMantissa().call()/1e18
    print(f"Close Factor: {close_factor}")
    print(f"Liqudation Incentive: {liquidation_incentive}")

    self.w3 = w3
    self.Joetroller = Joetroller
    self.PriceOracle = PriceOracle
    self.close_factor = close_factor
    self.liquidation_incentive = liquidation_incentive
    self.Liquidator = Liquidator
    self.executor_account = executor_account
    self.flash_fee = 8e-4 #unhardcode at some point

  def run(self, verbose=False, delay=1):
    while True: #Probably a nicer way to do this
      self.main_loop(verbose)
      time.sleep(delay) #Delay so we aren't spamming graph api too hard (maybe not needed - bot isn't that fast!)

  def main_loop(self,verbose=False,test_accts=[]):
    """
    Queries graph api, works out liquidation parameters then calls liquidator smart contract
    """
    ##Fetch underwater accounts from the graph (kinda delayed, a bot to beat others probably needs to look at events and create own db of lending accounts!)
    if test_accts: #So we don't try and liq all the graph ones during tests
      underwater_accs = []
    else:
      underwater_accs = run_graph_query(graphql_uri, liq_query)["data"]["accounts"]

    ##Double check graph data with on chain contracts  
    checked_underwater_accounts = test_accts #Allows accts not on graph query to be added for testing purposes 
    for acc_data in underwater_accs:
      address = self.w3.toChecksumAddress(acc_data["id"].lower())
      error,liquidity,shortfall = self.Joetroller.functions.getAccountLiquidity(address).call() #Check liquidity of account
      if error!= 0:
        printv(f"Error getting account liquidity for {address}",verbose)
      if liquidity!=0:
        printv(f"{address}: Liquidity:{liquidity/1e18} ",verbose)
      else:
        printv(f"{address}: Shortfall: {shortfall/1e18}",verbose)
        checked_underwater_accounts.append(address) #Add account to new list if actually in shortfall

    ##Find the details of the lending and borrowing positions that the underwater accounts hold, work out liquidation parameters and perform the liquidation
    for account in checked_underwater_accounts: #Iterate through each account in the underwater list
      
      account_position = self.get_account_position(account)
      seize_jToken,max_seize_usd = self.largest_seizable(account_position)
      repay_jToken,repay_amount,repay_usd,= self.find_repay_amount(account_position, max_seize_usd,)

      actual_seize_usd = repay_usd * self.liquidation_incentive 
      profit_before_gas = actual_seize_usd - repay_usd*(1+self.flash_fee)
      pc = repay_usd/account_position[repay_jToken]['borrow_balance_usd']

      #quick dirty logic for lender -> this could be improved by looking for the most liquid market (largest possible loan)
      flash_lender_jToken = [jToken for jToken in jToken_addresses.values() if jToken != repay_jToken and jToken != seize_jToken][0] #lol python

      printv(
        f"""
        {account}: Repay {repay_usd}USD of {account_position[repay_jToken]['symbol']}, receive {actual_seize_usd}USD of {account_position[seize_jToken]['symbol']}
        Profit before gas: {profit_before_gas}
        Repay amount: {int(repay_amount)} ({pc})
        Flash Borrow jToken: {flash_lender_jToken}
        Repay jToken: {repay_jToken}
        Seized jToken {seize_jToken}
        """,verbose)

      if self.Liquidator and self.executor_account:

        tx = self.Liquidator.functions.liquidateWithFlashLoan(
              flash_lender_jToken,
              int(repay_amount),
              repay_jToken,
              account,
              seize_jToken
          )
        try:
          gas_cost = tx.estimateGas({"from":self.executor_account})
          printv(f"gas: {gas_cost}",verbose) #Need to utilise
          tx.transact({"from":self.executor_account})
          print(f"Liquidation attempted: {repay_usd}USD of {account_position[repay_jToken]['symbol']}, receiving {actual_seize_usd}USD of {account_position[seize_jToken]['symbol']} for {account} ")
        except Exception as e:
          printv(e,verbose)

  def get_account_position(self,account):
    assets = self.Joetroller.functions.getAssetsIn(account).call() #Get markets the account is in
    account_position = {}  
    for jToken in assets: #Iterate through assets, find accounts holdings and add to position dict
      #jToken details
      if jToken == jToken_addresses['jAVAX']:
        _abi = jWrappedNative_abi
      else:
        _abi = jERC20_abi
      contract = self.w3.eth.contract(address = jToken, abi = _abi)
      symbol = list(jToken_addresses.keys())[list(jToken_addresses.values()).index(jToken)] # could change this to lookup from jToken addresses for speed - DONE!
      decimals = underlying_decimals[symbol]

      #Details of accounts position
      price = self.PriceOracle.functions.getUnderlyingPrice(jToken).call()
      error, jToken_balance, borrow_balance, exchange_rate = contract.functions.getAccountSnapshot(account).call()
      borrow_balance_usd = borrow_balance/1e18 * price/1e18
      supply_balance_usd = jToken_balance/1e18 * price/1e18 * exchange_rate/1e18

      #Add the jToken position to dict of positions for this account
      account_position[jToken] = { 
        "symbol":symbol,
        "borrow_balance":borrow_balance,
        "borrow_balance_usd": borrow_balance_usd,
        "jToken_balance": jToken_balance,
        "jToken_decimals": decimals,
        "supply_balance_underlying": jToken_balance* exchange_rate/1e18,
        "underlying_decimals": underlying_decimals[symbol],
        "supply_balance_usd": supply_balance_usd
      }
    return account_position

  def largest_seizable(self,acc_position):
    jToken_to_seize =None
    seizable_usd = 0
    #Loop through and find largest supply position
    for jToken, position_data in acc_position.items():
      if position_data['supply_balance_usd'] > seizable_usd:
        jToken_to_seize = jToken
        seizable_usd = position_data['supply_balance_usd'] 
    return jToken_to_seize,seizable_usd

  def find_repay_amount(self, acc_position, max_seizable_usd):
    jToken_to_repay = None
    repay_amount_usd = 0
    #Loop through and find largest repay position
    for jToken, position_data in acc_position.items():
      if position_data["borrow_balance_usd"] * self.close_factor > repay_amount_usd:
        jToken_to_repay = jToken
        repay_amount = position_data["borrow_balance"] * self.close_factor
        repay_amount_usd = position_data["borrow_balance_usd"] * self.close_factor
    #If largest repay position results in too large a seizable amount, scale it so correct
    if repay_amount_usd * self.liquidation_incentive > max_seizable_usd:
      repay_amount_usd = max_seizable_usd/ self.liquidation_incentive
      repay_amount = repay_amount * max_seizable_usd / (repay_amount_usd * self.liquidation_incentive)
    return jToken_to_repay, repay_amount, repay_amount_usd,

  def check_accounts(self):
    pass #todo move some code out

if __name__ == "__main__":
    lb = LiquidatorBot("http://localhost:8545",verbose=True)
    lb.run()