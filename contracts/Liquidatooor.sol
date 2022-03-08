pragma solidity ^0.8.12;

import "./Ownable.sol";

import "../interfaces/ERC3156FlashLenderInterface.sol";
import "../interfaces/ERC3156FlashBorrowerInterface.sol";
import "../interfaces/IJoeRouter02.sol";
import "../interfaces/IERC20.sol";
import "../interfaces/IJToken.sol";
import "../interfaces/Joetroller.sol";
import "../node_modules/hardhat/console.sol";

contract Liquidatooor is ERC3156FlashBorrowerInterface, Ownable{

    address public joetroller;
    address public joeRouter;
 
    constructor (address _joetroller, address _joeRouter)
    {
        //TJ contracts to interact with
        joetroller = _joetroller;
        joeRouter = _joeRouter;
    }

    struct TokenPair{
        address jToken;
        address underlying;
    }

    function set_joeRouter(address _joeRouter) external onlyOwner
    {
        joeRouter = _joeRouter;
    }

    function liquidateWithFlashLoan(
        address flashLoanLender,
        uint256 repayAmount,
        address repayJToken,
        address accountToLiquidate,
        address collateralJToken
    ) external {
        TokenPair memory  repayPair = TokenPair(
            repayJToken,
            IJToken(repayJToken).underlying()
            ); 
        TokenPair memory collateralPair = TokenPair(
            collateralJToken,
            IJToken(collateralJToken).underlying()
            );
        TokenPair memory flashPair = TokenPair(
            flashLoanLender,
            IJToken(flashLoanLender).underlying()
            );
        address[] memory path = new address[](2);
        path[0] = flashPair.underlying;
        path[1] = repayPair.underlying;

        //Work out how much needed to borrow in flashloan (Borrowed token must be swapped to other tokens in order to prevent re-entrancy)
        uint256 borrowAmount = IJoeRouter02(joeRouter).getAmountsIn(
            repayAmount,
            path
            )[0];

        console.log("need",borrowAmount,IERC20(flashPair.underlying).symbol());
        console.log("for",repayAmount, IERC20(repayPair.underlying).symbol());
        
        bytes memory data = abi.encode(repayAmount, repayPair, accountToLiquidate, collateralPair);
        ERC3156FlashLenderInterface(flashLoanLender).flashLoan(this, address(this), borrowAmount, data); //initiator address used as second argument for TJ flash loans
        console.log("remaining_balance",IERC20(flashPair.underlying).balanceOf(address(this)));
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

        address[] memory path = new address[](2);
        uint256[] memory amounts;
        (uint256 repayAmount, TokenPair memory repayPair, address accountToLiquidate, TokenPair memory collateralPair) = 
            abi.decode(data, (uint256,TokenPair,address,TokenPair));

        IERC20(token).approve(joeRouter, amount);
        IERC20(token).approve(msg.sender, amount + fee);
        //IERC20(repayPair.underlying).approve(joeRouter, repayAmount);
        IERC20(repayPair.underlying).approve(repayPair.jToken, repayAmount);

        console.log("borrowed ",amount , IERC20(token).symbol());
        console.log("to liquidate",accountToLiquidate); 
        console.log("using ", IERC20(repayPair.underlying).symbol());
        console.log("seizing ", IERC20(collateralPair.jToken).symbol());

        path[0] = token;
        path[1] = repayPair.underlying;

        IJoeRouter02(joeRouter).swapTokensForExactTokens(
            repayAmount,
            amount,
            path,    
            address(this),
            block.timestamp+15);

        console.log("After swap ready to repay ", IERC20(IJToken(repayPair.jToken).underlying()).balanceOf(address(this)),IERC20(repayPair.underlying).symbol());

        {
        uint256 returnCode_liq = IJToken(repayPair.jToken).liquidateBorrow(
            accountToLiquidate,
            repayAmount,
            collateralPair.jToken);
        console.log("return code",returnCode_liq);
        console.log("seized_JToken",IERC20(collateralPair.jToken).balanceOf(address(this)));
        require(returnCode_liq == 0,"bad return code from liquidation");
        }

        uint256 returnCode_redeem = IJToken(collateralPair.jToken).redeem(
            IERC20(collateralPair.jToken).balanceOf(address(this))
            );
        require(returnCode_redeem == 0,"bad return code from redeem");

        uint256 seizedBalance = IERC20(collateralPair.underlying).balanceOf(address(this));
        console.log("redeemed",seizedBalance);   

        path[0] = collateralPair.underlying;
        path[1] = token;
        amounts = IJoeRouter02(joeRouter).getAmountsOut(
            seizedBalance,
            path
            ); 
        
        for (uint i = 0; i< amounts.length; i++){
           console.log(amounts[i]);
        }
        console.log("out",amounts[1]*(99*10^18)/(100*10^18));

        IERC20(collateralPair.underlying).approve(joeRouter,seizedBalance); 
        IJoeRouter02(joeRouter).swapExactTokensForTokens(
            seizedBalance,
            amounts[1]*(99*10^18)/(100*10^18),
            path,
            address(this),
            block.timestamp+15);

        return keccak256("ERC3156FlashBorrowerInterface.onFlashLoan");
    }

}
