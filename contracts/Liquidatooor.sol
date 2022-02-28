pragma solidity 0.8.12;

import "../interfaces/ERC3156FlashLenderInterface.sol";
import "../interfaces/ERC3156FlashBorrowerInterface.sol";
import "../interfaces/IJoeRouter02.sol";
import "../node_modules/hardhat/console.sol";

interface Joetroller {
    function isMarketListed(address jTokenAddress) external view returns (bool);
}

interface ERC20 {
    function approve(address spender, uint256 amount) external;
    function symbol() external view returns (string memory);
    function decimals() external view returns (uint8);
}


contract Liquidatooor is ERC3156FlashBorrowerInterface{

    address public joetroller;
    constructor(address _joetroller){
        joetroller = _joetroller;
    }

    function liquidateWithFlashLoan(
        address flashLoanLender,
        address borrowToken,
        uint256 borrowAmount,
        address repayToken,
        address accountToLiquidate,
        address collateralToken
    ) external {
        bytes memory data = abi.encode(borrowToken, borrowAmount, repayToken, accountToLiquidate, collateralToken);
        ERC3156FlashLenderInterface(flashLoanLender).flashLoan(this, address(this), borrowAmount, data); //initiator address used as second argument for TJ flash loans
    }

    function onFlashLoan(
        address initiator,
        address token,
        uint256 amount,
        uint256 fee,
        bytes calldata data
    ) override external returns(bytes32){
        console.log("initiator: ",initiator);
        console.log("this: ",address(this));
        console.log("msg.sender: ",msg.sender);
        console.log("token: ", token);

        require(Joetroller(joetroller).isMarketListed(msg.sender), "untrusted message sender");
        require(initiator == address(this), "FlashBorrower: Untrusted loan initiator");
        (address borrowToken, uint256 borrowAmount, address repayToken, address accountToLiquidate, address collateralToken) = 
            abi.decode(data, (address, uint256, address, address, address));
        require(borrowToken == token, "encoded data (borrowToken) does not match");
        require(borrowAmount == amount, "encoded data (borrowAmount) does not match");
        ERC20(token).approve(msg.sender, amount + fee);
        // your logic is written here...

        console.log("borrowed ",amount , ERC20(token).symbol());

        console.log("to liquidate",accountToLiquidate); 
        console.log("using ", ERC20(repayToken).symbol());
        console.log("seizing ", ERC20(collateralToken).symbol());

        return keccak256("ERC3156FlashBorrowerInterface.onFlashLoan");
    }
}
