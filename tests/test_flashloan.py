from brownie import (
    accounts,
    Liquidatooor
)

import pytest

#hardcoded for testing for now -> need to loop through???
lender_address = "0xC22F01ddc8010Ee05574028528614634684EC29e" #jAVAX
token = "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7" #wAVAX
repayToken = "0xA7D7079b0FEaD91F3e65f86E8915Cb59c1a4C664" #USDC.e
accountToLiquidate = "0xA000000000000000000000000000000000000000"
collateralToken = "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7" #jAVAX

amount = 10

@pytest.fixture
def liquidator():
    account = accounts[0]
    JoeTroller_address = "0xdc13687554205E5b89Ac783db14bb5bba4A1eDaC"
    return account.deploy(Liquidatooor,JoeTroller_address)

def test_flash(liquidator):
    account = accounts[0]
    result = liquidator.liquidateWithFlashLoan(
        lender_address,
        token,amount,
        repayToken,
        accountToLiquidate,
        collateralToken,
        {'from':account}
        )
    print(result)
