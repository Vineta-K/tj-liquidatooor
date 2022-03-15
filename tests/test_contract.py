from brownie import (
    accounts,
    Contract)

from scripts.deploy_liquidator import deploy_liquidator
from scripts.useful_scripts import trace_on_revert
from bot.constants import jToken_addresses, contract_addresses
from create_lending_positions import create_shortfall_position

import pytest
import random


@pytest.fixture
def liquidator():
    return deploy_liquidator()

def test_set_joerouter(liquidator):
    #Change joeRouter to random address and verify updated
    assert liquidator.joeRouter() == contract_addresses["JoeRouter"]
    new_joeRouter = "0x" + "%040x" % random.randrange(16**40)
    tx = liquidator.setJoeRouter(new_joeRouter,{"from":accounts[0]})
    assert liquidator.joeRouter() == new_joeRouter

def test_only_owner(liquidator):
    #Check only the owner (deployer acct accounts[0) can modify joeRouter])
    new_joeRouter = "0x" + "%040x" % random.randrange(16**40)
    try:
        tx = liquidator.setJoeRouter(new_joeRouter, {"from":accounts[1]}) #Shouldn't be able to change joeRouter
    except:
        pass
    assert liquidator.joeRouter() == contract_addresses["JoeRouter"]

def test_withdraw_tokens(liquidator):
    #Check that ERC20 tokens can be withdrawn from the bot
    amount = 1000e18
    wAVAX = Contract.from_explorer("0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7")
    liquidator_address = liquidator.tx.contract_address

    wAVAX.deposit({"from":accounts[0], "value":amount}) #Get some wAVAX token
    assert wAVAX.balanceOf(liquidator_address) == 0
    assert wAVAX.balanceOf(accounts[0]) == amount

    wAVAX.transfer(liquidator_address,amount,{"from":accounts[0]}) #Send the wAVAX to contract (in reeality this would be profit from liquidations)
    assert wAVAX.balanceOf(liquidator_address) == amount
    assert wAVAX.balanceOf(accounts[0]) == 0

    liquidator.withdrawToken("0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7", {"from":accounts[0]}) #Withdraw the AVAX back to owner address
    assert wAVAX.balanceOf(liquidator_address) == 0
    assert wAVAX.balanceOf(accounts[0]) == amount

def test_liquidate(liquidator):
    ##Test the liquidation works on a position with three different borrowed tokens
    Joetroller = Contract.from_explorer(contract_addresses['Joetroller'])
    lender_address = jToken_addresses['jWETH']
    borrow_jTokens = ['jWBTC','jUSDT','jUSDC'] 

    #Create account to liquidate (accounts[-1] hardcoded for now)
    _,borrow_amount_underlying, test_account = create_shortfall_position(borrow_jTokens , supply_amount_AVAX = 100,acc_ind = -1) #Last jtoken in list is biggest posn (see fcn impl)

    #Check account is in shortfall
    error, liquidity, shortfall = Joetroller.getAccountLiquidity(test_account)
    assert error == 0
    assert liquidity == 0
    assert shortfall > 0

    #Perform the liquidation
    result = flashloan(
        liquidator,
        lender_address,
        int(borrow_amount_underlying[-1]*.5),
        jToken_addresses[borrow_jTokens[-1]],
        str(accounts[-1]),
        jToken_addresses['jAVAX'])       
    assert not isinstance(result, Exception) 

    #Check account is now in liquidity
    error, liquidity, shortfall = Joetroller.getAccountLiquidity(test_account)
    assert error == 0
    assert liquidity > 0
    assert shortfall == 0

@trace_on_revert
#If tx reverts find the tx in block and use call)trace to debug
def flashloan(
    liquidator,
    lender_address,
    repayAmount,
    repayJToken,
    accountToLiquidate,
    collateralJToken,
    ): #Doing this flashloan call in own function allows the trace_on_revert thingy to work

    return liquidator.liquidateWithFlashLoan(
        lender_address,
        repayAmount,
        repayJToken,
        accountToLiquidate,
        collateralJToken,
        {'from':accounts[0],
        'allow_revert': True},
        )