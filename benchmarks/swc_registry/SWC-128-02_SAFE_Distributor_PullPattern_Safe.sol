// Canonical Upstream Reference: Smart Contract Weakness Classification (SWC-Registry)
// Upstream URL: https://github.com/SmartContractSecurity/SWC-registry
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract PullDistributor {
    mapping(address => uint256) public pendingRewards;
    function claimReward() external {
        uint256 amt = pendingRewards[msg.sender];
        require(amt > 0);
        pendingRewards[msg.sender] = 0;
        payable(msg.sender).transfer(amt);
    }
}