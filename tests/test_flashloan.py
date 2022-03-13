from brownie import (
    accounts,
    Contract)

from scripts.deploy_liquidator import deploy_liquidator
from scripts.useful_scripts import trace_on_revert
from bot.constants import jToken_addresses,contract_addresses
from create_lending_positions import create_shortfall_position
import pytest


@pytest.fixture
def liquidator():
    return deploy_liquidator()

@trace_on_revert
def flashloan(
    liquidator,
    lender_address,
    repayAmount,
    repayJToken,
    accountToLiquidate,
    collateralJToken,
    ): #doing this in own function allows the trace_on_revert thingy to work

    return liquidator.liquidateWithFlashLoan(
        lender_address,
        repayAmount,
        repayJToken,
        accountToLiquidate,
        collateralJToken,
        {'from':accounts[0],
        'allow_revert': True},
        )

def test_liquidate(liquidator):
    Joetroller = Contract.from_explorer(contract_addresses['Joetroller'])
    lender_address = jToken_addresses['jWETH']
    borrow_jToken = 'jUSDC'

    #Create account to liquidate (accounts[-1] hardcoded for now)
    _,borrow_amount_underlying = create_shortfall_position(borrow_jToken , supply_amount_AVAX = 100)

    #Check account is in shortfall
    error,liquidity,shortfall = Joetroller.getAccountLiquidity(accounts[-1])
    assert error == 0
    assert liquidity == 0
    assert shortfall > 0

    #Perform the liquidation
    result = flashloan(
        liquidator,
        lender_address,
        borrow_amount_underlying*0.49,
        jToken_addresses[borrow_jToken],
        str(accounts[-1]),
        jToken_addresses['jAVAX'])       
    assert not isinstance(result,Exception) 

    #Check account now in liquidity
    error,liquidity,shortfall = Joetroller.getAccountLiquidity(accounts[-1])
    assert error == 0
    assert liquidity > 0
    assert shortfall == 0
