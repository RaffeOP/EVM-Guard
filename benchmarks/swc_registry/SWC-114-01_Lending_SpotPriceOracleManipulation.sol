// Canonical Upstream Reference: Smart Contract Weakness Classification (SWC-Registry)
// Upstream URL: https://github.com/SmartContractSecurity/SWC-registry
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
interface IUniswapPair { function getReserves() external view returns (uint112, uint112, uint32); }
contract FlashVulnerableLender {
    IUniswapPair public pool;
    function getCollateralPrice() public view returns (uint256) {
        (uint112 r0, uint112 r1, ) = pool.getReserves();
        return (uint256(r1) * 1e18) / uint256(r0); // Spot reserves vulnerable to flash loan
    }
}