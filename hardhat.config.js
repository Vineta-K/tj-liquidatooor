module.exports = {
  defaultNetwork: "hardhat",
  networks: {
    hardhat: {
      chainId: 43114,
      gasPrice: 225000000000,
      initialBaseFeePerGas: 0,
      forking: {
          url: "https://api.avax.network/ext/bc/C/rpc",
          blockNumber: 11319146 ,
          enabled: true,},
      },
  },
  solidity: {
    version: "0.8.12",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
    },
  },
};