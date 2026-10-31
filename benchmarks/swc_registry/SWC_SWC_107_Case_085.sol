// Canonical Upstream Reference: Smart Contract Weakness Classification (SWC-Registry)
// Upstream URL: https://github.com/SmartContractSecurity/SWC-registry
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SWC_SWC_107_Case_085 {
    mapping(address => uint256) public balances;
    uint256 public totalDeposited;
    uint256 public totalShares;
    uint256 private _locked;

    modifier nonReentrant() {
        require(_locked == 0, "REENTRANCY_GUARD");
        _locked = 1;
        _;
        _locked = 0;
    }

    function deposit() external payable {
        balances[msg.sender] += msg.value;
        totalDeposited += msg.value;
        totalShares += msg.value;
    }

    function withdraw(uint256 shares) external nonReentrant {
        require(shares > 0 && totalShares > 0);
        uint256 payout = (shares * totalDeposited) / totalShares;
        totalDeposited -= payout;
        totalShares -= shares; // SAFE: CEI pattern respected
        (bool success, ) = msg.sender.call{value: payout}("");
        require(success);
    }

    function getSharePrice() external view returns (uint256) {
        if (totalShares == 0) return 1e18;
        return (totalDeposited * 1e18) / totalShares;
    }
}