pragma solidity ^0.8.12;

import "./Ownable.sol";

import "../interfaces/ERC3156FlashLenderInterface.sol";
import "../interfaces/ERC3156FlashBorrowerInterface.sol";
import "../interfaces/IJoeRouter02.sol";
import "../interfaces/IERC20.sol";
import "../interfaces/IJToken.sol";
import "../interfaces/Joetroller.sol";
import "../node_modules/hardhat/console.sol"; //Remove for production

/* 
Contract provides ablity for the owner to liquidate underwater accounts by calling liquidateWithFlashLoan
*/
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
    } //Helps with stack to deep issues

    function withdrawToken(address _tokenContract) external onlyOwner
    {
        IERC20 tokenContract = IERC20(_tokenContract);
        uint256 amount = tokenContract.balanceOf(address(this));
        bool success = tokenContract.transfer(address(msg.sender), amount);
        require(success, "Failed to send Token");
    } //To withdraw tokens from contract

    function setJoeRouter(address _joeRouter) external onlyOwner
    {
        joeRouter = _joeRouter;
    } //Incase the JoeRouter changes

    /*
    Liquidates an underwater account, using TJ implementation of ERC3156 flash loans
    */
    function liquidateWithFlashLoan(
        address flashLoanLender,
        uint256 repayAmount, //Amount of underlying token to repay
        address repayJToken,
        address accountToLiquidate,
        address collateralJToken
    ) external onlyOwner {
        TokenPair memory  repayPair = TokenPair(repayJToken, IJToken(repayJToken).underlying());  //repay jToken and underlying
        TokenPair memory collateralPair = TokenPair(collateralJToken, IJToken(collateralJToken).underlying()); //collateral jToken and underlying
        TokenPair memory flashPair = TokenPair(flashLoanLender, IJToken(flashLoanLender).underlying()); //flash loaned jToken and underlying 
        address[] memory path = new address[](2); //For JoeRouter
        path[0] = flashPair.underlying;
        path[1] = repayPair.underlying;

        //Work out how much needed to borrow in flashloan (Borrowed token must be swapped to other tokens in order to prevent re-entrancy)
        uint256 borrowAmount = IJoeRouter02(joeRouter).getAmountsIn(
            repayAmount,
            path
            )[0];

        console.log("Need ",borrowAmount,IERC20(flashPair.underlying).symbol());
        console.log("to repay ",repayAmount, IERC20(repayPair.underlying).symbol());
        
        //Perform flashloan
        bytes memory data = abi.encode(repayAmount, repayPair, accountToLiquidate, collateralPair); //Encode params to pass to flashloan callback
        ERC3156FlashLenderInterface(flashLoanLender).flashLoan(this, address(this), borrowAmount, data); //Initiator address used as second argument for TJ flash loans. On calling this the onFlashLoan function is called, where the liquidation is performed using the flash loaned funds.

        //log balance/profit
        console.log("Remaining token balance ",IERC20(flashPair.underlying).balanceOf(address(this)),IERC20(flashPair.underlying).symbol());
    }

    /*
    Callback function called after flashloan borrowed. Performs the following steps: 
    - Swaps flashloaned token to repay token,
    - Performs liquidation using repay token, seizing collateral as a jToken
    - Redeems underlying token for the seized jToken collateral
    - Swaps this underlying token back to flashloaned token so that the flashloan can be repayed
    */
    function onFlashLoan(
        address initiator,
        address token,
        uint256 amount,
        uint256 fee,
        bytes calldata data
    ) external returns(bytes32){
        //Checks
        require(Joetroller(joetroller).isMarketListed(msg.sender), "untrusted message sender");
        require(initiator == address(this), "FlashBorrower: Untrusted loan initiator");

        address[] memory path = new address[](2); //Used for JoeRouter swaps
        uint256[] memory amounts; //Used for JoeRouter swaps
        (uint256 repayAmount, TokenPair memory repayPair, address accountToLiquidate, TokenPair memory collateralPair) = 
            abi.decode(data, (uint256,TokenPair,address,TokenPair)); //Params from liquidate fcn

        IERC20(token).approve(joeRouter, amount); //Approve borrowed token for swap
        IERC20(token).approve(msg.sender, amount + fee); //Approve borrowed token for repaying to flashloanlender
        IERC20(repayPair.underlying).approve(repayPair.jToken, repayAmount); //Approve the repay token to repay debt to the lender 

        //Useful debug output
        console.log("Borrowed ",amount , IERC20(token).symbol());
        console.log("to liquidate",accountToLiquidate); 
        console.log("using ", IERC20(repayPair.underlying).symbol());
        console.log("seizing ", IERC20(collateralPair.jToken).symbol());

        //Swap flashloan token to account debt underlying token
        path[0] = token;
        path[1] = repayPair.underlying;
        IJoeRouter02(joeRouter).swapTokensForExactTokens(
            repayAmount,
            amount,
            path,    
            address(this),
            block.timestamp+15);
        console.log("After swap ready to repay ", IERC20(IJToken(repayPair.jToken).underlying()).balanceOf(address(this)),IERC20(repayPair.underlying).symbol());

        //Liquidate the account, seizing the jToken as collateral
        uint256 returnCode_liq = IJToken(repayPair.jToken).liquidateBorrow(
            accountToLiquidate,
            repayAmount,
            collateralPair.jToken);
        console.log("Seized_JToken ",IERC20(collateralPair.jToken).balanceOf(address(this)));
        require(returnCode_liq == 0,"Bad return code from liquidation"); //Check liquidation was successfil

        //Redeem the seized jTokens for the underlying tokens
        uint256 returnCode_redeem = IJToken(collateralPair.jToken).redeem(
            IERC20(collateralPair.jToken).balanceOf(address(this))
            );
        require(returnCode_redeem == 0,"Bad return code from redeem"); //Check redeem was successful

        uint256 seizedBalance = IERC20(collateralPair.underlying).balanceOf(address(this)); //Find how much underlying we recieved
        console.log("Redeemed ",seizedBalance);   

        //Swap the underlying token back to the flashloaned token so we can repay
        path[0] = collateralPair.underlying;
        path[1] = token;
        amounts = IJoeRouter02(joeRouter).getAmountsOut(
            seizedBalance,
            path
            ); 
        console.log("Borrowed token after swap",amounts[1]);
        IERC20(collateralPair.underlying).approve(joeRouter,seizedBalance); 
        IJoeRouter02(joeRouter).swapExactTokensForTokens(
            seizedBalance,
            amounts[1],//*(99*10^18)/(100*10^18), //slip 1% -doesn't work w/o this sometimes
            path,
            address(this),
            block.timestamp+15);
        //No need to check if we have made profit, if not flash loan repay will fail!
        return keccak256("ERC3156FlashBorrowerInterface.onFlashLoan");
    }

}
