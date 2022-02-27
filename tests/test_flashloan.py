from brownie import (
    accounts,
    Liquidatooor
)

import pytest

lender_address = "0xC22F01ddc8010Ee05574028528614634684EC29e" #jAVAX
token = "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7" #wAVAX
amount = 10


def test_flash():
    account = accounts[0]
    result = Liquidatooor[0].doFlashloan("0x1613beb3b2c4f22ee086b2b38c1476a3ce7f78e8",token,amount,{'from':account})
    print(result)