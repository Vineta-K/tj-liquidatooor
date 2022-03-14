import pytest

from brownie import Contract,accounts,chain,web3

from bot.liquidator_bot import LiquidatorBot
from scripts.deploy_liquidator import deploy_liquidator
from bot.constants import hh_endpoint,contract_addresses,jToken_addresses
from scripts.useful_scripts import trace_on_revert
from create_lending_positions import create_shortfall_position,create_position

def test_bot():


    #Setup bot and position that is almost underwater
    liquidator_addresss = deploy_liquidator().tx.contract_address
    liquidator_bot = LiquidatorBot(
        rpc_endpoint="http://127.0.0.1:8545",
        liquidator_contract_address=liquidator_addresss,
        )
    _,_,BorrowjTokens,Joetroller = create_position(['jWBTC','jUSDT','jUSDC'],1000)


    test_accts=[str(accounts[-1])] #Feed this account to bot to also watch as well as graph queries
    while True: #Rn a loop of bot then accrue interest on accounts borrow position until a liquidation is detected
        liquidator_bot.main_loop(test_accts=test_accts)
        block = chain[-1]
        for tx_name in block['transactions']:
            tx = chain.get_transaction(web3.toHex(tx_name))
            if "LiquidateBorrow" in tx.events:
                print (tx.events['LiquidateBorrow'])
                if str(tx.events['LiquidateBorrow']["borrower"]) == str(accounts[-1]):
                    return
        chain.sleep(42069)
        chain.mine()
        for BorrowjToken in BorrowjTokens:
            BorrowjToken.accrueInterest({"from":accounts[-1]})
        error,liquidity,shortfall = Joetroller.getAccountLiquidity(accounts[-1])
        print(f"New Liquidity: {liquidity/1e18} New shortfall: {shortfall/1e18}, Timestamp {chain[-1].timestamp}")

        
# def test_check_repay_calculations(liquidator_bot):
#     create_shortfall_position('jUSDT',100) #Make position underwater positon

#     acc_posn = liquidator_bot.get_account_position(str(accounts[-1])) #Bot fcn for finding positions of account
#     seize_jToken,max_seizable_usd = liquidator_bot.largest_seizable(acc_posn) #Bot fcn for deciding what to seize
#     assert(seize_jToken == jToken_addresses['jAVAX'])
#     repay_jToken,repay_amount,repay_usd,= liquidator_bot.find_repay_amount(acc_posn, max_seizable_usd) #Bot fcn for getting the repay amount to send to liquidator contract

