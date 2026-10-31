// Canonical Upstream Reference: Smart Contract Weakness Classification (SWC-Registry)
// Upstream URL: https://github.com/SmartContractSecurity/SWC-registry
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract RewardDistributor {
    address[] public recipients;
    function register() external { recipients.push(msg.sender); } // Unrestricted!
    function distribute() external {
        for (uint256 i = 0; i < recipients.length; i++) {
            payable(recipients[i]).transfer(1 wei); // Can exceed 30M gas limit
        }
    }
}