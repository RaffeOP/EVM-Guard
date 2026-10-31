// Canonical Upstream Reference: Smart Contract Weakness Classification (SWC-Registry)
// Upstream URL: https://github.com/SmartContractSecurity/SWC-registry
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract AMMPrecisionPool {
    uint256 public reserveX = 1000000e18;
    uint256 public reserveY = 1000000e18;
    function swapFee(uint256 amountIn, uint256 feeRate) external pure returns (uint256) {
        return (amountIn * feeRate) / 10000; // Truncation drops remainder on small dust
    }
}