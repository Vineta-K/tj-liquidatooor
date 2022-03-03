from brownie import Contract,chain,accounts,web3

from scripts.constants import jToken_addresses,contract_addresses

account = "0xa3167c4ba7e6b61cbfa10f1ae0a93bb3f3c00957"

Joetroller = Contract.from_explorer(contract_addresses["Joetroller"])
jUSDC = Contract.from_explorer(jToken_addresses['jUSDC'])

def check_liquidity(address):
    r = Joetroller.getAccountLiquidity(address)
    print(web3.eth.block_number)
    print(f"liquidity: {r[1]}")
    print(f"shortfall: {r[2]}")

def accrue_interest_test(address):
    for i in range(0,10):
        jUSDC.accrueInterest({'from': accounts[0]})
        check_liquidity(address)
        chain.mine(200000)


def main():
    accrue_interest_test(account)