pragma solidity>=0.4.22;

interface IERC20 {
    function approve(address spender, uint256 amount) external;
    function symbol() external view returns (string memory);
    function decimals() external view returns (uint8);
    function balanceOf(address account) external view returns (uint);
    function transfer(address recipient, uint256 amount) external returns (bool);
}