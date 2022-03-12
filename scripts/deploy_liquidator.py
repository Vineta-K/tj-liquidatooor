from brownie import (
    Liquidatooor,
    accounts,
)
from scripts.useful_scripts import trace_on_revert
from bot.constants import contract_addresses

def deploy_liquidator():
    account = accounts[0]
    Joetroller_address = contract_addresses["Joetroller"]
    JoeRouter_address = contract_addresses["JoeRouter"]
    return Liquidatooor.deploy(Joetroller_address,JoeRouter_address,{'from': account})

def main():
    tx = deploy_liquidator()
    print(tx)

