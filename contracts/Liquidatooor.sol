pragma solidity ^0.8.12;

import "../interfaces/ERC3156FlashLenderInterface.sol";
import "../interfaces/ERC3156FlashBorrowerInterface.sol";
import "../interfaces/IJoeRouter02.sol";
import "../interfaces/IERC20.sol";
import "../interfaces/IJToken.sol";
import "../interfaces/Joetroller.sol";
import "../node_modules/hardhat/console.sol";

contract Liquidatooor is ERC3156FlashBorrowerInterface{

    address public joetroller;
    address public joeRouter;
    constructor (address _joetroller, address _joeRouter)
    {
        joetroller = _joetroller;
        joeRouter = _joeRouter;
    }

    function set_joeRouter(address _joeRouter) external 
        {joeRouter = _joeRouter;} //need to add admin only checks

    function liquidateWithFlashLoan(
        address flashLoanLender,
        address borrowToken,
        uint256 repayAmount,
        address repayJToken,
        address accountToLiquidate,
        address collateralJToken
    ) external {
        address repayTokenUnderlying = IJToken(repayJToken).underlying();
        address[] memory path = new address[](2);
        path[0] = borrowToken;
        path[1] = repayTokenUnderlying;
        uint256[] memory borrowAmount = IJoeRouter02(joeRouter).getAmountsIn(repayAmount,path);

        console.log("need",borrowAmount[0],IERC20(borrowToken).symbol());
        console.log("for",repayAmount, IERC20(repayTokenUnderlying).symbol());
        
        bytes memory data = abi.encode(repayAmount, repayJToken, accountToLiquidate, collateralJToken);
        ERC3156FlashLenderInterface(flashLoanLender).flashLoan(this, address(this), borrowAmount[0], data); //initiator address used as second argument for TJ flash loans
    }

    function onFlashLoan(
        address initiator,
        address token,
        uint256 amount,
        uint256 fee,
        bytes calldata data
    ) external returns(bytes32){
        //console.log("initiator: ",initiator);
        //console.log("this: ",address(this));
        //console.log("msg.sender: ",msg.sender);
        //console.log("token: ", token);

        require(Joetroller(joetroller).isMarketListed(msg.sender), "untrusted message sender");
        require(initiator == address(this), "FlashBorrower: Untrusted loan initiator");
        //(address borrowToken, uint256 borrowAmount, 
        (uint256 repayAmount, address repayJToken, address accountToLiquidate, address collateralJToken) = 
            abi.decode(data, (uint256, address, address, address));
        //require(borrowToken == token, "encoded data (borrowToken) does not match");
        //require(borrowAmount == amount, "encoded data (borrowAmount) does not match");
        address repayTokenUnderlying = IJToken(repayJToken).underlying();
        IERC20(token).approve(joeRouter, amount + fee);
        IERC20(repayTokenUnderlying).approve(joeRouter,repayAmount);
        // your logic is written here...

        console.log("borrowed ",IERC20(token).balanceOf(address(this)) , IERC20(token).symbol());
        //console.log("borrowed ",amount , IERC20(token).symbol());

        console.log("to liquidate",accountToLiquidate); 
        console.log("using ", IERC20(repayTokenUnderlying).symbol());
        console.log("seizing ", IERC20(collateralJToken).symbol());

        address[] memory path = new address[](2);
        path[0] = token;
        path[1] = repayTokenUnderlying;

        uint256[] memory amounts = IJoeRouter02(joeRouter).swapTokensForExactTokens(repayAmount,amount,path,address(this),block.timestamp+15);
        //add some checks here on amounts
        console.log("after swap ", IERC20(IJToken(repayJToken).underlying()).balanceOf(address(this)),IERC20(repayTokenUnderlying).symbol());

        for (uint i = 0; i< amounts.length; i++){
        //    console.log(amounts[i]);
        }

        uint256 returnCode_liq = IJToken(repayJToken).liquidateBorrow(accountToLiquidate,repayAmount,collateralJToken);
        console.log("return code",returnCode_liq);
        require(returnCode_liq == 0,"bad return code from liquidation");

        //redeem to avax
        //repay flashloan

        return keccak256("ERC3156FlashBorrowerInterface.onFlashLoan");
    }
}
