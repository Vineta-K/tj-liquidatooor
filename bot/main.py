from cgi import test
import requests
from web3 import Web3
import json
from constants import (
graphql_uri,
snowtrace_api,
rpc_endpoint,
PriceOracle_address,
jToken_addresses,
underlying_decimals)

from secrets import snowtrace_api_token

close_factor = 0.5 # get from contract at some point
#also need to look at liquidation incentive factor here

liq_query = """{
  accounts(where: {health_gt: 0, health_lt: 1, totalBorrowValueInUSD_gt: 0}) {
    id
    health
    totalBorrowValueInUSD
    totalCollateralValueInUSD
  }
}"""

def max_repayable_borrow(acc_positions,price_oracle):
  max_repayable = {
    "amount_underlying":0,
    "amount_USD":0,
    "jToken":None,
    "symbol": None
  }
  for jToken in acc_positions:
    symbol = jToken["symbol"]
    underlying_price = price_oracle.caller().getUnderlyingPrice(jToken_addresses[symbol])
    underlying_price_decimals = underlying_price/(1e18*10**(18-underlying_decimals[symbol]))
    underlying_value_USD = underlying_price_decimals * float(jToken['borrowBalanceUnderlying'])
    if underlying_value_USD > max_repayable['amount_USD']:
      max_repayable = {
        "amount_underlying": 0.5 * float(jToken["borrowBalanceUnderlying"]),
        "amount_USD":0.5 * underlying_value_USD,
        "jToken":jToken_addresses[symbol],
        "symbol":symbol
        }
  return max_repayable

    

def find_seizable_position(acc_positions,max_repay,price_oracle):
  seizeable = {
    "amount_underlying":0,
    "amount_USD":0,
    "jToken":None,
    "symbol": None
  }
  for jToken in acc_positions:
    if jToken['enteredMarket'] == True and float(jToken['supplyBalanceUnderlying'] )> 0:
      underlying_price = price_oracle.caller().getUnderlyingPrice(jToken_addresses[symbol])
      underlying_price_decimals = underlying_price/(1e18*10**(18-underlying_decimals[symbol]))
      underlying_value_USD = underlying_price_decimals * float(jToken['supplyBalanceUnderlying'])
      if underlying_value_USD > max_repay["amount_USD"]:
        seizeable = {
          "amount_underlying":jToken["supplyBalanceUnderlying"],
          "amount_USD":underlying_value_USD,
          "jToken":jToken_addresses[symbol],
          "symbol":symbol
        }
  return seizeable

def run_query(uri, query, statusCode=200, headers=None):
    request = requests.post(uri, json={'query': query}, headers=headers)
    if request.status_code == statusCode:
        return request.json()
    else:
        raise Exception(f"Unexpected status code returned: {request.status_code}")

if __name__ == "__main__":

  w3 = Web3(Web3.HTTPProvider(rpc_endpoint))
  if (w3.isConnected()):
    print ("Successfully connected to w3")
  else:
    print("Connection to w3 failed")

  params = {
    'module':'contract',
    'action':'getabi',
    'address': PriceOracle_address,
    'apikey': snowtrace_api_token
  }

  PriceOracle_abi = requests.get(snowtrace_api,params).json()['result']

  price_oracle = w3.eth.contract(address=PriceOracle_address,abi=PriceOracle_abi)
  for symbol in jToken_addresses:
    underlying_price_test = price_oracle.functions.getUnderlyingPrice(jToken_addresses[symbol]).call()
    print(symbol + ": " + str(underlying_price_test/(1e18*10**(18-underlying_decimals[symbol]))))


  underwater_accs = run_query(graphql_uri,liq_query)["data"]
  with open("underwater_accs.json","w") as f:
      json.dump(underwater_accs,f)

  
  for acc_data in underwater_accs["accounts"]:
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

    acc_positions = run_query(graphql_uri,token_query)["data"]["accountJTokens"]

  #maybe calculate price out here and pass in to cut down on contract calls

    max_repayable = max_repayable_borrow(acc_positions,price_oracle)
    seizeable = find_seizable_position(acc_positions,max_repayable,price_oracle)

    print("repayable:" + str(max_repayable))
    print("seizable:" + str(seizeable))

    #liquidate account()!!

    #with open("{address}".format(address = acc_data["id"])+".json","w") as f:
    #  json.dump(acc_positions,f)


        

        

