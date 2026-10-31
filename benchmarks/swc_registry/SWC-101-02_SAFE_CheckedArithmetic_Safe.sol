// Canonical Upstream Reference: Smart Contract Weakness Classification (SWC-Registry)
// Upstream URL: https://github.com/SmartContractSecurity/SWC-registry
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract SafeArithmetic {
    function computeTotal(uint256 a, uint256 b) external pure returns (uint256) {
        return a + b; // Solidity 0.8+ native overflow revert
    }
}