from brownie import accounts,chain,web3

from bot.liquidator_bot import LiquidatorBot
from scripts.deploy_liquidator import deploy_liquidator
from create_lending_positions import create_position

def test_bot():
    #Setup bot and position that is almost underwater
    liquidator_addresss = deploy_liquidator().tx.contract_address
    liquidator_bot = LiquidatorBot(rpc_endpoint="http://127.0.0.1:8545", liquidator_contract_address=liquidator_addresss)
    _,_,BorrowjTokens,Joetroller,test_account = create_position(['jWBTC','jUSDT','jUSDC'], supply_amount_AVAX = 1000, acc_ind = -2)

    test_accts=[str(test_account)] #Feed this account to bot to also watch as well as graph queries
    while True: #Run a loop of bot then accrue interest on accounts borrow position until a liquidation of the test account is detected (other liquidations are a bonus!)
        start_block = chain[-1].number
        liquidator_bot.main_loop(test_accts=test_accts, verbose=False)
        end_block = chain[-1].number
        liquidated_test_acc = False
        for i in range(start_block, end_block+1):
            tx_name = chain[i]['transactions'][0] #Default hardhat behaviour one tx per block then new one mined
            tx = chain.get_transaction(web3.toHex(tx_name))
            if "LiquidateBorrow" in tx.events: #Look for liquidate borrow events
                print (tx.events['LiquidateBorrow'])
                if str(tx.events['LiquidateBorrow']["borrower"]) == str(test_account): #Check if the liquidated account was the test account
                    liquidated_test_acc = True
        if liquidated_test_acc: #Return and stop test if the test account has been liquidated
            return
        chain.sleep(42069) #Artificially increase timestamp
        chain.mine()
        for BorrowjToken in BorrowjTokens: #Accrue interest on each of the borrowed tokens
            BorrowjToken.accrueInterest({"from": test_account})
        error, liquidity, shortfall = Joetroller.getAccountLiquidity(test_account) #Print account liquidity/shortfall
        print(f"New Liquidity: {liquidity/1e18} New shortfall: {shortfall/1e18}, Timestamp {chain[-1].timestamp}")

