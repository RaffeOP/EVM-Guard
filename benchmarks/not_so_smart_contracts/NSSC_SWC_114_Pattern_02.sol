// Canonical Upstream Reference: Trail of Bits Not-So-Smart-Contracts
// Upstream URL: https://github.com/crytic/not-so-smart-contracts
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract NSSC_SWC_114_Pattern_02 {
    uint256 public reserveX = 10000000e18;
    uint256 public reserveY = 10000000e18;

    function getSpotPrice() public view returns (uint256) {
        // BUG: Instantaneous spot price vulnerable to flash swap distortion
        return (reserveX * 1e18) / reserveY;
    }

    function borrowAgainstCollateral(uint256 collateral) external view returns (uint256) {
        uint256 price = getSpotPrice();
        return (collateral * price) / 1e18;
    }
}