import requests
from web3 import Web3
import json
from constants import (
graphql_uri,
snowtrace_api,
RPC_endpoint,
PriceOracle,
jToken_adresses)

from secrets import snowtrace_API_token

liq_query = """{
  accounts(where: {health_gt: 0, health_lt: 1, totalBorrowValueInUSD_gt: 0}) {
    id
    health
    totalBorrowValueInUSD
    totalCollateralValueInUSD
  }
}"""

#setup web3
w3 = Web3(Web3.HTTPProvider(RPC_endpoint))
if (w3.isConnected()):
  print ("Successfully connected to w3")
else:
  print("Connection tow3 failed")

def run_query(uri, query, statusCode=200, headers=None):
    request = requests.post(uri, json={'query': query}, headers=headers)
    if request.status_code == statusCode:
        return request.json()
    else:
        raise Exception(f"Unexpected status code returned: {request.status_code}")

if __name__ == "__main__":

  w3 = Web3(Web3.HTTPProvider(RPC_endpoint))
  if (w3.isConnected()):
    print ("Successfully connected to w3")
  else:
    print("Connection to w3 failed")

  params = {
    'module':'contract',
    'action':'getabi',
    'address': PriceOracle,
    'apikey': snowtrace_API_token
  }

  PriceOracleABI = requests.get(snowtrace_api,params).json()['result']

  price_oracle = w3.eth.contract(address=PriceOracle,abi=PriceOracleABI)
  underlying_price_test = price_oracle.caller.getUnderlyingPrice(jToken_adresses["jAVAX"])
  print(underlying_price_test)

  underwater_accs = run_query(graphql_uri,liq_query)
  with open("underwater_accs.json","w") as f:
      json.dump(underwater_accs,f)

  for acc_data in underwater_accs["data"]["accounts"]:
    token_query = """{
    accountJTokens(where: {account: \"%s\"}) {
      id
      market{
        id
        }
      symbol
      enteredMarket
    supplyBalanceUnderlying
    borrowBalanceUnderlying
      }
    }"""%acc_data["id"]

    acc_params = run_query(graphql_uri,token_query)

    #liquidate account!!

    with open("{address}".format(address = acc_data["id"])+".json","w") as f:
      json.dump(acc_params,f)


        

        

