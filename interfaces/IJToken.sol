pragma solidity >=0.4.22;

interface IJToken {
    function liquidateBorrow(
        address borrower,
        uint256 repayAmount,
        address JTokenCollateral
    ) external returns (uint256);
    function underlying() external view returns (address);
}