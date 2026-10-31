// Canonical Upstream Reference: Trail of Bits Not-So-Smart-Contracts
// Upstream URL: https://github.com/crytic/not-so-smart-contracts
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract NSSC_SWC_114_Pattern_15 {
    uint256 public cumulativePrice;
    uint32 public lastBlockTimestamp;

    function getTWAP() external view returns (uint256) {
        // SAFE: Time-weighted price observation resistant to single-block flash loan
        uint32 timeElapsed = uint32(block.timestamp) - lastBlockTimestamp;
        if (timeElapsed == 0) return 1e18;
        return cumulativePrice / timeElapsed;
    }
}