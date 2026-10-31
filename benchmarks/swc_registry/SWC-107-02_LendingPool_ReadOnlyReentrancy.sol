// Canonical Upstream Reference: Smart Contract Weakness Classification (SWC-Registry)
// Upstream URL: https://github.com/SmartContractSecurity/SWC-registry
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract LendingPoolVault {
    uint256 public totalDeposited;
    uint256 public totalShares;
    mapping(address => uint256) public balances;
    function deposit() external payable {
        balances[msg.sender] += msg.value;
        totalDeposited += msg.value;
        totalShares += msg.value;
    }
    function withdraw(uint256 shares) external {
        uint256 payout = (shares * totalDeposited) / totalShares;
        totalDeposited -= payout;
        (bool s, ) = msg.sender.call{value: payout}(""); // Intermediate call
        require(s);
        totalShares -= shares; // Dirty state during call!
    }
    function getSharePrice() external view returns (uint256) {
        if (totalShares == 0) return 1e18;
        return (totalDeposited * 1e18) / totalShares; // Returns dirty price
    }
}