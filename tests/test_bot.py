import pytest

from bot.liquidator_bot import LiquidatorBot
from bot.constants import hh_endpoint

@pytest.fixture
def liquidator_bot():
    return LiquidatorBot(hh_endpoint)

def test_check_repay_calculations(liquidator):
    #find an account -> run the repay calcs. Check close factor. Check seizable amount is same as calcualted from tj contracts