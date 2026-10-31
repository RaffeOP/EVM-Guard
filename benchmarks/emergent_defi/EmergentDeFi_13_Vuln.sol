// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract EmergentDeFi_13_Vuln {
    mapping(address => uint256) public balances;
    uint256 public totalDeposited;
    uint256 public totalShares;

    function deposit() external payable {
        balances[msg.sender] += msg.value;
        totalDeposited += msg.value;
        totalShares += msg.value;
    }

    function withdraw(uint256 shares) external {
        require(shares > 0 && totalShares > 0);
        uint256 payout = (shares * totalDeposited) / totalShares;
        totalDeposited -= payout;
        (bool success, ) = msg.sender.call{value: payout}("");
        require(success);
        totalShares -= shares; // BUG: State mutation after external call
    }

    function getSharePrice() external view returns (uint256) {
        if (totalShares == 0) return 1e18;
        return (totalDeposited * 1e18) / totalShares;
    }
}