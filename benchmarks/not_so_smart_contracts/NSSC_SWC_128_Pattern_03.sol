// Canonical Upstream Reference: Trail of Bits Not-So-Smart-Contracts
// Upstream URL: https://github.com/crytic/not-so-smart-contracts
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract NSSC_SWC_128_Pattern_03 {
    address[] public payees;

    function register() external {
        payees.push(msg.sender); // Unbounded mutation!
    }

    function distribute() external {
        // BUG: Gas limit exhaustion on large array
        for (uint256 i = 0; i < payees.length; i++) {
            payable(payees[i]).transfer(1 wei);
        }
    }
}