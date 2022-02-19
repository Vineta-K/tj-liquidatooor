pragma solidity 0.8.12;

import "./ERC3156FlashLenderInterface.sol";
import "./ERC3156FlashBorrowerInterface.sol";

interface Joetroller {
    function isMarketListed(address jTokenAddress) external view returns (bool);
}

interface ERC20 {
    function approve(address spender, uint256 amount) external;
}


contract Liquidatooor is ERC3156FlashBorrowerInterface{

    address public joetroller;
    constructor(address _joetroller){
        joetroller = _joetroller;
    }

    function doFlashloan(
        address flashloanLender,
        address borrowToken,
        uint256 borrowAmount
    ) external {
        bytes memory data = abi.encode(borrowToken, borrowAmount);
        ERC3156FlashLenderInterface(flashloanLender).flashLoan(this, borrowToken, borrowAmount, data);
    }

    function onFlashLoan(
        address initiator,
        address token,
        uint256 amount,
        uint256 fee,
        bytes calldata data
    ) override external returns(bytes32){
        require(Joetroller(joetroller).isMarketListed(msg.sender), "untrusted message sender");
        require(initiator == address(this), "FlashBorrower: Untrusted loan initiator");
        (address borrowToken, uint256 borrowAmount) = abi.decode(data, (address, uint256));
        require(borrowToken == token, "encoded data (borrowToken) does not match");
        require(borrowAmount == amount, "encoded data (borrowAmount) does not match");
        ERC20(token).approve(msg.sender, amount + fee);
        // your logic is written here...

        



        return keccak256("ERC3156FlashBorrowerInterface.onFlashLoan");
    }
}