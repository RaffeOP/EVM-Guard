// Canonical Upstream Reference: Smart Contract Weakness Classification (SWC-Registry)
// Upstream URL: https://github.com/SmartContractSecurity/SWC-registry
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SWC_SWC_101_Case_113 {
    uint256 public constant SCALE = 1e18;

    function swapFee(uint256 amountIn, uint256 feeRate) external pure returns (uint256) {
        uint256 fee = (amountIn * feeRate) / 10000;
        return fee;
    }

    function calculateExchangeRate(uint256 balanceA, uint256 balanceB) external pure returns (uint256) {
        require(balanceB > 0);
        return (balanceA * SCALE) / balanceB; // SAFE: Multiplication before division
    }
}