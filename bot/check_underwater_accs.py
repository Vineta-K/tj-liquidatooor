import requests
from web3 import Web3
import json

from constants import (
    snowtrace_api,
    JoeTroller_address,
    JoeLens_address,
    rpc_endpoint
    )

from secrets import snowtrace_api_token

w3 = Web3(Web3.HTTPProvider(rpc_endpoint))


account_address = "0x2673A0a94D292d8F50E866D4f6915Ab35C2E9CF2"
#account to test

if __name__ == "__main__":
    if (w3.isConnected()):
        print ("Successfully connected to w3")
    else:
        print("Connection to w3 failed")

    params = {
        'module':'contract',
        'action':'getabi',
        'address': JoeLens_address,
        'apikey': snowtrace_api_token
  }

    JoeLens_abi = requests.get(snowtrace_api,params).json()['result']
    JoeLens = w3.eth.contract(address = JoeLens_address,abi = JoeLens_abi)

    names = ['liquidity','shortfall','collateralUSD','borrowUSD','health']

    ret = JoeLens.functions.getAccountLimits(JoeTroller_address, account_address).call()
    print("account: " + account_address)
    i = 0
    for r in ret:
        if type(r) == int:
            print(names[i] + ": " + str(r/1e18))
            i+= 1
