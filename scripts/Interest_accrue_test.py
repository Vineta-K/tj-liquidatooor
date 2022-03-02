from brownie import Contract,chain,accounts

from scripts.constants import jToken_addresses,contract_addresses

account = "0xb9aec4db7082b0519074d84c6bbd854403d6b968"

Joetroller = Contract.from_explorer(contract_addresses["Joetroller"])
jUSDC = Contract.from_explorer(jToken_addresses['jUSDC'])

def check_liquidity(address):
    r = Joetroller.getAccountLiquidity(address)
    print(f"liquidity: {r[1]}")
    print(f"shortfall: {r[2]}")

def accrue_interest_test(address):
    for i in range(0,10):
        chain.mine(2000)
        jUSDC.accrueInterest({'from': accounts[0]})
        check_liquidity(address)

def main():
    accrue_interest_test(account)