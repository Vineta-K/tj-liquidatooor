from brownie import (
    accounts,
    Liquidatooor
)

import pytest

lender_address = "0xC22F01ddc8010Ee05574028528614634684EC29e" #jAVAX
token = "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7" #wAVAX

amount = 10

@pytest.fixture
def liquidatooor():
    account = accounts[0]
    JoeTroller_address = "0xdc13687554205E5b89Ac783db14bb5bba4A1eDaC"
    return account.deploy(Liquidatooor,JoeTroller_address)

def test_flash(liquidatooor):
    account = accounts[0]
    result = liquidatoor.liquidateWithFlashLoan(lender_address,token,amount,{'from':account})
    print(result)
