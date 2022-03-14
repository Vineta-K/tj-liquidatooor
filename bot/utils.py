import requests
from bot.secrets import snowtrace_api_token
from bot.constants import snowtrace_api

def get_abi(contract_address):
  params = {
    'module':'contract',
    'action':'getabi',
    'address': contract_address,
    'apikey': snowtrace_api_token
  }
  return requests.get(snowtrace_api, params).json()['result']

def run_graph_query(uri, query, statusCode=200, headers=None):
    request = requests.post(uri, json={'query': query}, headers=headers)
    if request.status_code == statusCode:
        return request.json()
    else:
        raise Exception(f"Unexpected status code returned: {request.status_code}")

def printv(str, bool):
    if bool:
        print(str)