pragma solidity >=0.4.22;

interface Joetroller {
    function isMarketListed(address jTokenAddress) external view returns (bool);
}