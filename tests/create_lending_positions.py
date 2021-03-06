from brownie import Contract,accounts,chain

from bot.constants import contract_addresses, jToken_addresses

def create_position(borrow_jTokens, supply_amount_AVAX, acc_ind=-1):
    """
    Creates a position close to collateralisation ratio for accounts[acc_ind], lending AVAX and borrowing other tokens in ratio (i+1)/d where i is index and d is sum of numbers up to number of tokens (last token always has biggest positions, first smallest). jAVAX is chosen to lend because I cba swapping from the AVAX thats already initiated in hardhat accounts.
    """
    account = accounts[acc_ind]
    supply_jToken = 'jAVAX' 
    Joetroller = Contract.from_explorer(contract_addresses["Joetroller"])
    SupplyjToken = Contract.from_explorer(jToken_addresses[supply_jToken])
    PriceOracle = Contract.from_explorer(contract_addresses["PriceOracle"])
    BorrowjTokens = []
    for borrow_jToken in borrow_jTokens:
        BorrowjTokens.append(Contract.from_explorer(jToken_addresses[borrow_jToken]))

    #Calculate parameters for borrow
    _,collateral_factor,_ = Joetroller.markets(jToken_addresses[supply_jToken])
    supply_amount = supply_amount_AVAX*1e18
    supply_amount_usd = (supply_amount * PriceOracle.getUnderlyingPrice(jToken_addresses[supply_jToken]))
 
    borrow_amount_underlying = []
    borrow_amount_usd = []
    l = len(borrow_jTokens)
    d = l*(l+1)/2 #Scaling denominator is sum of l natural numbers.
    for i in range(l):
        borrow_amount_usd.append( ((i+1)/d) *(1 - 1e-9) * supply_amount_usd * collateral_factor / 1e18 ) #(1-1e-N) factor used to account for floating point errors. Should probably use fixed point maths here but shoudn't matter as account will still be pushed to liquidation by interest acccrual
        borrow_amount_underlying.append( borrow_amount_usd[i] / PriceOracle.getUnderlyingPrice(jToken_addresses[borrow_jTokens[i]]) )
    
    print( #Summarise calculations
        f"""
        Lending Position Created:
        Account: {accounts[-1]}
        Supply amount usd: {supply_amount_usd/1e36}
        Borrow amount usd total: {sum(borrow_amount_usd)/1e36}
        Borrow_jTokens: {borrow_jTokens}
        Borrow amount usd: {[amt/1e36 for amt in borrow_amount_usd]}
        Borrow amount underlying: {borrow_amount_underlying}
        """
    )

    SupplyjToken.mintNative({"from":account, "value":supply_amount}) #Supply
    Joetroller.enterMarkets([jToken_addresses[supply_jToken]], {"from":account}) #Ensure entered for borrow
    Joetroller.enterMarkets([jToken_addresses[borrow_jToken] for borrow_jToken in borrow_jTokens], {"from":account}) #Ensure entered for borrow

    for i in range(l):
        tx = BorrowjTokens[i].borrow(int(borrow_amount_underlying[i]), {"from":account}) #Borrow extremely close to max allowed
    error,liquidity,shortfall = Joetroller.getAccountLiquidity(account) #Check account liquidity is as expected (very small liquidity)
    print(f"error: {error} Liquidity: {liquidity/1e18} Shortfall: {shortfall/1e18}")
    return borrow_amount_usd, borrow_amount_underlying, BorrowjTokens, Joetroller,account

def create_shortfall_position(borrow_jToken, supply_amount_AVAX, acc_ind = -1):
    """
    A position is opened very close to collateralisation ratio for accounts[acc_ind] then block timestamp manipulated to accrue borrow interest and push the account underwater. 
    """
    borrow_amount_usd, borrow_amount_underlying, BorrowjTokens, Joetroller,account = create_position(borrow_jToken, supply_amount_AVAX, acc_ind) #Open position

    while get_shortfall(Joetroller, account) <= 1e18: #Push account into shortfall by accrueing interest (note interest is calculated based on timestamp so chain.sleep() can be used to manipulate this)
        for BorrowjToken in BorrowjTokens:
            BorrowjToken.accrueInterest({"from":account})
        chain.sleep(42069)
        chain.mine()
    
    return borrow_amount_usd, borrow_amount_underlying,account
    
def get_shortfall(Joetroller, account): #Function to return only the shortfall value
    error, liquidity, shortfall = Joetroller.getAccountLiquidity(account)
    print(f"New Liquidity: {liquidity/1e18} New shortfall: {shortfall/1e18}, Timestamp {chain[-1].timestamp}")
    return shortfall