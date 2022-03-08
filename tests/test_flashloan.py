from brownie import (
    accounts)

from scripts.deploy_liquidator import deploy_liquidator
from scripts.useful_scripts import trace_on_revert
from scripts.constants import jToken_addresses,contract_addresses
import pytest

#hardcoded for testing for now -> need to loop through???
lender_address = jToken_addresses["jWETH"]
repayAmount = int(34710)
repayJToken = jToken_addresses["jUSDC"]
accountToLiquidate = "0xa3167c4ba7e6b61cbfa10f1ae0a93bb3f3c00957"
collateralJToken = jToken_addresses["jAVAX"]

#jAVAX = Contract("0xC22F01ddc8010Ee05574028528614634684EC29e")


@pytest.fixture
def liquidator():
    return deploy_liquidator()

def test_flash(liquidator):
    result = flashloan(liquidator)
    print(result)
    assert not isinstance(result,Exception) 

@trace_on_revert
def flashloan(liquidator):
    account = accounts[0]
    liquidator.liquidateWithFlashLoan(
        lender_address,
        repayAmount,
        repayJToken,
        accountToLiquidate,
        collateralJToken,
        {'from':account,
        'allow_revert': True},
        )