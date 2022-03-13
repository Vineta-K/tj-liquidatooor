from brownie import Contract,accounts,chain

from bot.constants import contract_addresses,jToken_addresses

def create_position(borrow_jToken,supply_amount_AVAX):
    """
    Creates a position close to collateralisation ratio for accounts[-1], lending AVAX and borrowing another token. jAVAX is chosen to lend because I cba swapping from the AVAX thats already initiated in hardhat accounts.
    """
    supply_jToken = 'jAVAX' 
    Joetroller = Contract.from_explorer(contract_addresses["Joetroller"])
    SupplyjToken = Contract.from_explorer(jToken_addresses[supply_jToken])
    PriceOracle = Contract.from_explorer(contract_addresses["PriceOracle"])
    BorrowjToken = Contract.from_explorer(jToken_addresses[borrow_jToken])
    #Calculate parameters for borrow
    _,collateral_factor,_ = Joetroller.markets(jToken_addresses[supply_jToken])
    supply_amount = supply_amount_AVAX*1e18
    supply_amount_usd = (supply_amount * PriceOracle.getUnderlyingPrice(jToken_addresses[supply_jToken]))
    borrow_amount_usd = (1 - 1e-16)*supply_amount_usd * collateral_factor/1e18 #(1-1e-N) factor used to account for floating point errors. Should probably use fixed point maths here but shoudn't matter as account will still be pushed to liquidation by interest acccrual
    borrow_amount_underlying = borrow_amount_usd / PriceOracle.getUnderlyingPrice(jToken_addresses[borrow_jToken])
    print( #Summarise calculations
        f"""
        Supply amount usd: {supply_amount_usd/1e36}
        Borrow amount usd: {borrow_amount_usd/1e36}
        Borrow amount underlying: {borrow_amount_underlying}
        """
    )

    SupplyjToken.mintNative({"from":accounts[-1],"value":supply_amount}) #Supply
    Joetroller.enterMarkets([jToken_addresses[supply_jToken],jToken_addresses[borrow_jToken]],{"from":accounts[-1]}) #Ensure entered for borrow
    tx = BorrowjToken.borrow(int(borrow_amount_underlying),{"from":accounts[-1]}) #Borrow extremely close to max allowed
    error,liquidity,shortfall = Joetroller.getAccountLiquidity(accounts[-1]) #Check account liquidity is as expected (very small liquidity)
    print(f"error: {error} Liquidity: {liquidity/1e18} Shortfall: {shortfall/1e18}")
    return borrow_amount_usd,borrow_amount_underlying,BorrowjToken,Joetroller

def create_shortfall_position(borrow_jToken,supply_amount_AVAX):
    """
    A position is opened very close to collateralisation ratio for accounts[-1] then block timestamp manipulated to accrue borrow interest and push the account underwater. 
    """
    borrow_amount_usd,borrow_amount_underlying,BorrowjToken,Joetroller = create_position(borrow_jToken,supply_amount_AVAX) #Open position

    while get_shortfall(Joetroller) <= 1e18: #Push account into shortfall by accrueing interest (note interest is calculated based on timestamp so chain.sleep() can be used to manipulate this)
        BorrowjToken.accrueInterest({"from":accounts[-1]})
        chain.sleep(42069)
        chain.mine()
    
    return borrow_amount_usd, borrow_amount_underlying
    
def get_shortfall(Joetroller): #Function to return only the shortfall value
    error,liquidity,shortfall = Joetroller.getAccountLiquidity(accounts[-1])
    print(f"New Liquidity: {liquidity/1e18} New shortfall: {shortfall/1e18}, Timestamp {chain[-1].timestamp}")
    return shortfall