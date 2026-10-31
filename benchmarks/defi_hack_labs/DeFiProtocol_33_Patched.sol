// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract DeFiProtocol_33_Patched {
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