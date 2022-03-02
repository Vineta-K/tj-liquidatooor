from brownie import chain,web3

import functools

def trace_on_revert(func):
    @functools.wraps(func)
    def wrapper(*args,**kwargs):
        try:
            receipt = func(*args,**kwargs)
            return receipt
        except Exception as e:
            block = web3.eth.get_block(
                block_identifier = web3.eth.default_block,
                full_transactions = False)
            tx = web3.toHex(block['transactions'][0])
            chain.get_transaction(tx).call_trace(True)
            return e
    return wrapper        


