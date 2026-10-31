// Canonical Upstream Reference: Trail of Bits Not-So-Smart-Contracts
// Upstream URL: https://github.com/crytic/not-so-smart-contracts
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract NSSC_SWC_124_Pattern_19 {
    // Proxy layout collision: slot 0 uint256 overwriting slot 0 address
    uint256 public criticalMultiplier;
    address public owner;

    function initialize(uint256 mult) external {
        criticalMultiplier = mult; // Overwrites implementation slot 0
    }
}