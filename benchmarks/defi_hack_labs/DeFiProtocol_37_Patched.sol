// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract DeFiProtocol_37_Patched {
    mapping(address => uint256) public pendingWithdrawals;

    function claim() external {
        // SAFE: Pull pattern replaces unbounded iteration
        uint256 amount = pendingWithdrawals[msg.sender];
        require(amount > 0);
        pendingWithdrawals[msg.sender] = 0;
        payable(msg.sender).transfer(amount);
    }
}