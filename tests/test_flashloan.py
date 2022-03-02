
from brownie import (
    accounts)

from scripts.deploy_liquidator import deploy_liquidator
from scripts.useful_scripts import trace_on_revert
from scripts.constants import jToken_addresses,contract_addresses
import pytest

#hardcoded for testing for now -> need to loop through???
lender_address = jToken_addresses["jAVAX"]
borrow_token = "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7" #wAVAX
repayAmount = int(1949929905)
repayJToken = jToken_addresses["jUSDC"]
accountToLiquidate = "0xb9aec4db7082b0519074d84c6bbd854403d6b968"
collateralJToken = jToken_addresses["jAVAX"]

#jAVAX = Contract("0xC22F01ddc8010Ee05574028528614634684EC29e")


@pytest.fixture
def liquidator():
    return deploy_liquidator()

def test_flash(liquidator):
    result = flashloan(liquidator)
    print(result)

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