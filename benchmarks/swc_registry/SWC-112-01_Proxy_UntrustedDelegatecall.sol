// Canonical Upstream Reference: Smart Contract Weakness Classification (SWC-Registry)
// Upstream URL: https://github.com/SmartContractSecurity/SWC-registry
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract UntrustedProxy {
    address public owner;
    function forwardCall(address target, bytes calldata data) external {
        (bool s, ) = target.delegatecall(data); // BUG: arbitrary attacker target
        require(s);
    }
}