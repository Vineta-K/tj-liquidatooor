# TJ-liquidatooor
Liquidation script + contracts for TJ learn web3 bounty. 
## Disclaimer:
This is my first proper solidity project and is shared here for educational/inspirational purposes. It was done in my spare time and often late at night. Do not use this in production/mainnet as it is likely there will be bugs.
## Specification:
https://docs.google.com/document/d/1k8GusDAk-dLO8heNG-d4YJkmx8Z8vVMsIfS1R6QeMUE/

The aim is to create a bot + smart contract that does the following:
- Monitor and identify underwater accounts in TraderJoe lending protocol.
- If underwater accounts are found attempt to liquidate them using flashloans to acquire the capital to repay the debt.
## Code:
### Install:
#### @Brownie
##### Using  `pipx`
This uses brownie for development and testing,

`pipx install eth-brownie`

`brownie networks import ./network-config.yaml true`

##### Using `venv`
If `venv` is used the path `/venv/bin` (on ubuntu) or equivalent will need to be used before any brownie commands later in the readme.

`python3 -m venv .venv`

`pip install eth-brownie`

`.venv/bin/brownie networks import ./network-config.yaml true`
`
#### Hardhat
Hardhat is used for forking avalanche mainnet.

`npm install --save-dev hardhat`

### Bot:
The bot is a Python script using web3.py libraries. An instance of the bot can be instantiated and run as follows. The executor account should be the owner of the liquidator smart contract.
```
import LiquidatorBot
liquidator_bot = LiquidatorBot(rpc_endpoint, executor_account, liquidator_contract_address)
liquidator_bot.run()
```
The bot is structured such that it runs `mainloop()` forever until stopped or interrupted.
This mainloop performs the following steps:
- Query the Graph to find a list of underwater accounts.
- Check the liquidity of these accounts with the Joetroller contract on chain to remove accounts where the Graph data is out of date
- Work out which lending markets these accounts have postions in, by making calls to the jToken contracts.
- Loop through the these account positions and:
    - Work out which collateral to seize, which borrow to repay, and how much to repay based on the accounts positions and protocol parameters.
    - Estimate the profit after gas of the liquidation.
    - If profitable, attempt the liquidation by calling a custom smart contract at liquidator_contract_address.
### Smart contract:
The smart contract effectively implements a single main function which performs the liquidation using TraderJoe's flashloan implementation (from the jToken contracts). It requires the jToken addresses of the flash borrow token, repay token and collateral token. The flash borrow token must be different from the repay and collateral tokens to avoid re-entrancy in the jToken contracts.
```
function liquidateWithFlashLoan(
    address flashLoanLender,
    uint256 repayAmount, //Amount of underlying token to repay
    address repayJToken,
    address accountToLiquidate,
    address collateralJToken
) external
```
This performs the following steps:
- Borrows the required capital from the flashLoanLender to liquidate repayAmount of underlying borrow for the accountToLiquidate .
- Swaps the flash loaned token to the underlying repay token (avoiding re-entrnacy when liquidating).
- Liquidates the account be repaying repayAmount of the underlying debt, seizing collateralJToken.
- Redeems the seized collateral jToken for its underlying.
- Swaps the underlying collateral tokens back to the flash loaned token so the flash loan can be repaid.

Note the profit is kept as the flash loaned token (for simplicity + to save gas). The token can be withdrawn using the `withdrawToken(address _tokenContract)`  function.
There are also functions to allow the JoeRouter to be changed in case it is upgraded.

### Tests:
There are two test files, one for testing the bot, and one for the smart contract. 
It is recommended to run `brownie test -s` where `-s` gives text output during the test. The tests can take quite long (a few mins), especially those which create lending positions to test.
#### Smart contract tests
The smart contract tests are as follows:

`test_set_joerouter()`- ensures joeRouter can be changed by the owner.

`test_only_owner()` - ensures only the owner can change the joeRouter.

`test_withdraw_tokens()` - transfers some wAVAX to the liquidator contract, then ensures that it can be withdrawn with the `withdrawToken()` function.

`test_liquidate()` - creates a lending position on chain that is in shortfall (by borrowing close to limit then accrueing interest over an artificially long time). Then liquidates this position using the `liquidateWithFlashLoan()` method, asserting that the previously underwater account is now no longer in shortfall after the liquidation.

#### Bot tests
At the moment there is only one test for the bot:

`test_bot()` - creates an account with a lending position that is close to being underwater. It then runs a loop where the `mainloop()` of the bot is run, followed by the accrual of interest on the account's position. When the test sees an event corresponding to the liquidation of this position (when it is pushed underwater and the bot liquidates it), the loop is broken and the test passes.

#### Network
Most of the development and testing was done on the `hardhat-dev` network (`brownie networks list` for details). However if you wan't call_trace debugging to have correct contract abis + function names it is recommended to manually start a local hardhat node and use `harhdhat-local` network.
## Todo/Further work:
As always there is much more to do that could improve this project:
- I didn't have time to do the extended parts of this bounty beyond the basics, so a telegram/discord bot hasn't been made.
- The smart contract could do with more tests, and maybe some of the onFlashLoan function could be broken out into fucntions that couod be unit tested.
- The liquidation tests have a position where there are three different borrow tokens, but only one collateral token. A position where there are multiple collateral tokens as well should be made and the liquidation funtions tested on it. During `test_bot()` it does appear the bot occasionally liquidates some accounts like this from the Graph dataset but this is not repeatable.
- The bot could do with unit tests of the logic that calculates the liquidation parameters.
- The tests heavily use `Contract.from_explorer()` which is very slow. Contract abis should be locally downloaded and used.
- The commenting of the smart contract is erratic and follows no standard unlike the ones seen in snowtrace/etherscan in production.
- The smart contract is not optimised for gas and therefore would likely have issues beating out more optimised bots on mainnet for liquidations. (i.e could do direct swaps rather than JoeRouter, maybe more efficient use of variables etc...).
- The smart contract acquires profit in the flash borrowed token. This might not be desirable and it should maybe all be converted to AVAX or USDC.
- The mixture of flaoting point maths in the bot and fixed point in solidity/EVM is likely to cause some errors due to floating point rounding. This hasn't properly been investigated, and hacky workarounds have been used when issues occur.
- The liquidation bot searches for the largest single repay/collateral pair available to repay, and seizes this. This is likely not optimal in all cases (see references wrt knapsack problem).
- The Graph data used by the liquidation bot is slow and slightly out of date. A custom local database that swatches and parses all TraderJoe lending events to work out account positions may be faster.
- The bot is generally very slow, it hasn't been determined whether the bottleneck is execution speed or waiting for contract/api calls.

