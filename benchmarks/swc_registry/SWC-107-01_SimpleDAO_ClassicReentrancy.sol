// Canonical Upstream Reference: Smart Contract Weakness Classification (SWC-Registry)
// Upstream URL: https://github.com/SmartContractSecurity/SWC-registry
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract SimpleDAO {
    mapping(address => uint256) public credit;
    function donate(address to) public payable { credit[to] += msg.value; }
    function withdraw(uint256 amount) public {
        if (credit[msg.sender] >= amount) {
            (bool success, ) = msg.sender.call{value: amount}("");
            require(success);
            credit[msg.sender] -= amount; // BUG: State update after call
        }
    }
}