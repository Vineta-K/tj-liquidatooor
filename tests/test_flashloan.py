from brownie import (
    accounts,
    Liquidatooor
)

import pytest

#hardcoded for testing for now -> need to loop through???
lender_address = "0xC22F01ddc8010Ee05574028528614634684EC29e" #jAVAX
borrow_token = "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7" #wAVAX
repayAmount = int(1949929905)
repayJToken = "0xEd6AaF91a2B084bd594DBd1245be3691F9f637aC" #jUSDC.e
accountToLiquidate = "0xb9aec4db7082b0519074d84c6bbd854403d6b968"
collateralJToken = "0xC22F01ddc8010Ee05574028528614634684EC29e" #jAVAX



@pytest.fixture
def liquidator():
    account = accounts[0]
    JoeTroller_address = "0xdc13687554205E5b89Ac783db14bb5bba4A1eDaC"
    JoeRouter_address = "0x60aE616a2155Ee3d9A68541Ba4544862310933d4"
    return account.deploy(Liquidatooor,JoeTroller_address,JoeRouter_address)

def test_flash(liquidator):
    account = accounts[0]
    result = liquidator.liquidateWithFlashLoan(
        lender_address,
        borrow_token,
        repayAmount,
        repayJToken,
        accountToLiquidate,
        collateralJToken,
        {'from':account}
        )
    print(result)
