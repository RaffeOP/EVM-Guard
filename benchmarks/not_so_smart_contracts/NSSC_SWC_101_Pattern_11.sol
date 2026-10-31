// Canonical Upstream Reference: Trail of Bits Not-So-Smart-Contracts
// Upstream URL: https://github.com/crytic/not-so-smart-contracts
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract NSSC_SWC_101_Pattern_11 {
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