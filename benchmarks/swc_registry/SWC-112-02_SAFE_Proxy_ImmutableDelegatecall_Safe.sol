// Canonical Upstream Reference: Smart Contract Weakness Classification (SWC-Registry)
// Upstream URL: https://github.com/SmartContractSecurity/SWC-registry
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract SafeProxy {
    address public immutable implementation;
    constructor(address impl) { implementation = impl; }
    fallback() external payable {
        (bool s, ) = implementation.delegatecall(msg.data);
        require(s);
    }
}