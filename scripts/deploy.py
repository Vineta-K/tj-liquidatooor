from brownie import (
    Liquidatooor,
    accounts,
)

JoeTroller_address = "0xdc13687554205E5b89Ac783db14bb5bba4A1eDaC"

def deploy():
    account = accounts[0]
    Liquidatooor.deploy(JoeTroller_address,{'from': account})

def main():
    deploy()
