from brownie import (
    accounts)

from scripts.deploy_liquidator import deploy_liquidator
from scripts.useful_scripts import trace_on_revert
from bot.constants import jToken_addresses,contract_addresses
import pytest

#hardcoded for testing for now -> need to loop through??? ->get specific block 
lender_address = jToken_addresses["jWETH"]
repayAmount = int(34710)
repayJToken = jToken_addresses["jUSDC"]
accountToLiquidate = "0xa3167c4ba7e6b61cbfa10f1ae0a93bb3f3c00957"
collateralJToken = jToken_addresses["jAVAX"]

@pytest.fixture
def liquidator():
    return deploy_liquidator()

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

def test_flash(liquidator):
    #create a borrow position to be liquidated here (with accounts[1]???) so can be tested any time
    #check with range of borrow/lend combos
    result = flashloan(liquidator)
    print(result)
    assert not isinstance(result,Exception) 

