import requests
from web3 import Web3
import json

liq_query = """{
  accounts(where: {health_gt: 0, health_lt: 1, totalBorrowValueInUSD_gt: 0}) {
    id
    health
    totalBorrowValueInUSD
    totalCollateralValueInUSD
  }
}"""

graphql_URI = "https://api.thegraph.com/subgraphs/name/traderjoe-xyz/lending"

def run_query(uri, query, statusCode=200, headers=None):
    request = requests.post(uri, json={'query': query}, headers=headers)
    if request.status_code == statusCode:
        return request.json()
    else:
        raise Exception(f"Unexpected status code returned: {request.status_code}")

if __name__ == "__main__":
    r = run_query(graphql_URI,liq_query)
    with open("dump.json","w") as f:
        json.dump(r,f)

        

