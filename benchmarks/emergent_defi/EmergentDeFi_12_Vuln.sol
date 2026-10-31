// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract EmergentDeFi_12_Vuln {
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