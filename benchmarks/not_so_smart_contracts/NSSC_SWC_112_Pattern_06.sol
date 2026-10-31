// Canonical Upstream Reference: Trail of Bits Not-So-Smart-Contracts
// Upstream URL: https://github.com/crytic/not-so-smart-contracts
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract NSSC_SWC_112_Pattern_06 {
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