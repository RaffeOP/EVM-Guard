// Canonical Upstream Reference: Smart Contract Weakness Classification (SWC-Registry)
// Upstream URL: https://github.com/SmartContractSecurity/SWC-registry
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SWC_SWC_128_Case_007 {
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