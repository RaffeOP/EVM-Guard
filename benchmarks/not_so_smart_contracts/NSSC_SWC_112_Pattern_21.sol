// Canonical Upstream Reference: Trail of Bits Not-So-Smart-Contracts
// Upstream URL: https://github.com/crytic/not-so-smart-contracts
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract NSSC_SWC_112_Pattern_21 {
    address public immutable implementation;

    constructor(address impl) {
        implementation = impl;
    }

    fallback() external payable {
        // SAFE: Immutable target address
        (bool success, ) = implementation.delegatecall(msg.data);
        require(success);
    }
}