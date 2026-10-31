// Canonical Upstream Reference: Smart Contract Weakness Classification (SWC-Registry)
// Upstream URL: https://github.com/SmartContractSecurity/SWC-registry
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SWC_SWC_112_Case_008 {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    function forwardCall(address target, bytes calldata data) external {
        // BUG: Arbitrary user-controlled callee address in delegatecall
        (bool success, ) = target.delegatecall(data);
        require(success);
    }
}