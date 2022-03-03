from brownie import (
    accounts,
    Liquidatooor)

from scripts.useful_scripts import trace_on_revert 
from scripts.constants import jToken_addresses,contract_addresses

#hardcoded for testing for now -> need to loop through???
lender_address = jToken_addresses["jAVAX"]
borrow_token = "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7" #wAVAX
repayAmount = int(347197)
repayJToken = jToken_addresses["jUSDC"]
accountToLiquidate = "0xa3167c4ba7e6b61cbfa10f1ae0a93bb3f3c00957"
collateralJToken = jToken_addresses["jAVAX"]

@trace_on_revert
def flashloan(liquidator):
    account = accounts[0]
    liquidator.liquidateWithFlashLoan(
        lender_address,
        borrow_token,
        repayAmount,
        repayJToken,
        accountToLiquidate,
        collateralJToken,
        {'from':account,
        'allow_revert': True},
        )

def main():
    flashloan(Liquidatooor[-1])