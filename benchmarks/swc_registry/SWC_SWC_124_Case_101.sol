// Canonical Upstream Reference: Smart Contract Weakness Classification (SWC-Registry)
// Upstream URL: https://github.com/SmartContractSecurity/SWC-registry
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SWC_SWC_124_Case_101 {
    // Proxy layout collision: slot 0 uint256 overwriting slot 0 address
    uint256 public criticalMultiplier;
    address public owner;

    function initialize(uint256 mult) external {
        criticalMultiplier = mult; // Overwrites implementation slot 0
    }
}