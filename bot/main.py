from cgi import test
import requests
from web3 import Web3
import json
from constants import (
Joetroller_address,
Joetroller_impl_address,
graphql_uri,
snowtrace_api,
rpc_endpoint,
PriceOracle_address,
jToken_addresses,
underlying_decimals)

from secrets import snowtrace_api_token

output = False

liq_query = """{
  accounts(where: {health_gt: 0, health_lt: 1, totalBorrowValueInUSD_gt: 0}) {
    id
    health
    totalBorrowValueInUSD
    totalCollateralValueInUSD
  }
}"""

def max_repayable_borrow(acc_positions,price_oracle):
  max_repayable = {
    "amount_underlying":0,
    "amount_USD":0,
    "jToken":None,
    "symbol": None
  }
  for jToken in acc_positions:
    symbol = jToken["symbol"]
    underlying_price = price_oracle.caller().getUnderlyingPrice(jToken_addresses[symbol])
    underlying_price_decimals = underlying_price/(1e18*10**(18-underlying_decimals[symbol]))
    underlying_value_USD = underlying_price_decimals * float(jToken['borrowBalanceUnderlying'])
    if underlying_value_USD > max_repayable['amount_USD']:
      max_repayable = {
        "amount_underlying": 0.5 * float(jToken["borrowBalanceUnderlying"]),
        "amount_USD":0.5 * underlying_value_USD,
        "jToken":jToken_addresses[symbol],
        "symbol":symbol
        }
  return max_repayable

def find_seizable_position(acc_positions,max_repay,price_oracle):
  seizeable = {
    "amount_underlying":0,
    "amount_USD":0,
    "jToken":None,
    "symbol": None
  }
  for jToken in acc_positions:
    symbol = jToken.symbol
    if jToken['enteredMarket'] == True and float(jToken['supplyBalanceUnderlying'] )> 0:
      underlying_price = price_oracle.caller().getUnderlyingPrice(jToken_addresses[symbol])
      underlying_price_decimals = underlying_price/(1e18*10**(18-underlying_decimals[symbol]))
      underlying_value_USD = underlying_price_decimals * float(jToken['supplyBalanceUnderlying'])
      if underlying_value_USD > max_repay["amount_USD"]:
        seizeable = {
          "amount_underlying":jToken["supplyBalanceUnderlying"],
          "amount_USD":underlying_value_USD,
          "jToken":jToken_addresses[symbol],
          "symbol":symbol
        }
  return seizeable

def run_query(uri, query, statusCode=200, headers=None):
    request = requests.post(uri, json={'query': query}, headers=headers)
    if request.status_code == statusCode:
        return request.json()
    else:
        raise Exception(f"Unexpected status code returned: {request.status_code}")

def get_abi(contract_address):
  params = {
    'module':'contract',
    'action':'getabi',
    'address': contract_address,
    'apikey': snowtrace_api_token
  }
  return requests.get(snowtrace_api,params).json()['result']

def main(rpc_endpoint):

  w3 = Web3(Web3.HTTPProvider(rpc_endpoint))
  if (w3.isConnected()):
    print ("Successfully connected to w3")
  else:
    print("Connection to w3 failed")

  PriceOracle_abi = get_abi(PriceOracle_address)
  Joetroller_abi = get_abi(Joetroller_impl_address)
  PriceOracle = w3.eth.contract(address = PriceOracle_address, abi = PriceOracle_abi)
  Joetroller = w3.eth.contract(address = Joetroller_address, abi = Joetroller_abi)

  jWrappedNative_abi = get_abi(jToken_addresses['jAVAX'])
  jERC20_abi = get_abi(jToken_addresses["jWETH"])

  #Visual oracle check
  for symbol in jToken_addresses:
    underlying_price_test = PriceOracle.functions.getUnderlyingPrice(jToken_addresses[symbol]).call()
    print(symbol + ": " + str(underlying_price_test/(1e18*10**(18-underlying_decimals[symbol]))))
  close_factor = Joetroller.functions.closeFactorMantissa().call()/1e18
  liquidation_incentive = Joetroller.functions.liquidationIncentiveMantissa().call()/1e18
  print(f"Close Factor: {close_factor}")
  print(f"Liqudation Incentive: {liquidation_incentive}")

  underwater_accs = run_query(graphql_uri,liq_query)["data"]["accounts"]
  if output == True:
    with open("underwater_accs.json","w") as f:
      json.dump(underwater_accs,f)
  
  checked_underwater_accounts = []
  #double check graph data
  for acc_data in underwater_accs:
    address = w3.toChecksumAddress(acc_data["id"].lower())
    error,liquidity,shortfall = Joetroller.functions.getAccountLiquidity(address).call()
    if error!= 0:
      print(f"Error getting account liquidity for {address}")
    if liquidity!=0:
      print(f"{address}: Liquidity:{liquidity/1e18} ")
    else:
      checked_underwater_accounts.append(address)
      print(f"{address}: Shortfall: {shortfall/1e18}")
    #acc_positions = run_query(graphql_uri,token_query)["data"]["accountJTokens"]

  account_positions = {}
  for account in checked_underwater_accounts:

    assets = Joetroller.functions.getAssetsIn(account).call()
    account_position = {}
    for jToken in assets:

      if jToken == jToken_addresses['jAVAX']:
        _abi = jWrappedNative_abi
      else:
        _abi = jERC20_abi

      contract = w3.eth.contract(address = jToken, abi = _abi)
      symbol = contract.functions.symbol().call()
      decimals = underlying_decimals[symbol]
      price = PriceOracle.functions.getUnderlyingPrice(jToken).call()

      error, jToken_balance, borrow_balance, exchange_rate = contract.functions.getAccountSnapshot(account).call()
      borrow_balance_usd = borrow_balance/1e18 * price/1e18
      supply_balance_usd = jToken_balance/1e18 * price/1e18 * exchange_rate/1e18

      account_position[jToken] = {
        "symbol":symbol,
        "borrow_balance":borrow_balance/10**decimals,
        "borrow_balance_usd": borrow_balance_usd,
        "jToken_balance": jToken_balance/1e8,
        "supply_balance_underlying": jToken_balance/1e18*exchange_rate/1e18,
        "supply_balance_usd": supply_balance_usd
      }

    account_positions[account] = account_position
  print(account_positions)
  with open("acc_posns.json","w") as f:
    json.dump(account_positions,f)

  #max_repayable = max_repayable_borrow(acc_positions,price_oracle)
  #seizeable = find_seizable_position(acc_positions,max_repayable,price_oracle)

    #print("repayable:" + str(max_repayable))
    #print("seizable:" + str(seizeable))

    #liquidate account()!!

if __name__ == "__main__":
  main("http://127.0.0.1:8545")



        

        

