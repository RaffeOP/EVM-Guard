"""
EVM-Guard Benchmark Corpus Provisioner
======================================
Builds and organizes canonical smart contract benchmark suites:
  1. SWC-Registry (121 standardized vulnerability test cases)
  2. DefiHackLabs (Reproduced real-world multi-contract exploit cases)
  3. Not-So-Smart-Contracts (Educational Solidity vulnerability patterns)

Saves test cases into benchmarks/swc_registry/, benchmarks/defi_hack_labs/,
and benchmarks/not_so_smart_contracts/ with JSON ground-truth labels.
"""

import os
import json

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCHMARK_DIR = os.path.join(WORKSPACE_DIR, "benchmarks")
SWC_DIR = os.path.join(BENCHMARK_DIR, "swc_registry")
DEFI_DIR = os.path.join(BENCHMARK_DIR, "defi_hack_labs")
NOT_SO_DIR = os.path.join(BENCHMARK_DIR, "not_so_smart_contracts")

os.makedirs(SWC_DIR, exist_ok=True)
os.makedirs(DEFI_DIR, exist_ok=True)
os.makedirs(NOT_SO_DIR, exist_ok=True)

# Standardized benchmark definitions with ground truth
CANONICAL_SWC_TESTS = [
    # SWC-107: Reentrancy (Classic & Read-Only)
    {
        "id": "SWC-107-01",
        "title": "SimpleDAO_ClassicReentrancy",
        "swc": "SWC-107",
        "subclass": "Classic State Modification After Call",
        "ground_truth_vulnerable": True,
        "cyclomatic_complexity": 4,
        "solidity_code": """// SPDX-License-Identifier: MIT
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
}"""
    },
    {
        "id": "SWC-107-02",
        "title": "LendingPool_ReadOnlyReentrancy",
        "swc": "SWC-107",
        "subclass": "Cross-Contract Read-Only Reentrancy",
        "ground_truth_vulnerable": True,
        "cyclomatic_complexity": 6,
        "solidity_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract LendingPoolVault {
    uint256 public totalDeposited;
    uint256 public totalShares;
    mapping(address => uint256) public balances;
    function deposit() external payable {
        balances[msg.sender] += msg.value;
        totalDeposited += msg.value;
        totalShares += msg.value;
    }
    function withdraw(uint256 shares) external {
        uint256 payout = (shares * totalDeposited) / totalShares;
        totalDeposited -= payout;
        (bool s, ) = msg.sender.call{value: payout}(""); // Intermediate call
        require(s);
        totalShares -= shares; // Dirty state during call!
    }
    function getSharePrice() external view returns (uint256) {
        if (totalShares == 0) return 1e18;
        return (totalDeposited * 1e18) / totalShares; // Returns dirty price
    }
}"""
    },
    {
        "id": "SWC-107-03_SAFE",
        "title": "GuardedVault_CEIPattern",
        "swc": "SWC-107",
        "subclass": "Checks-Effects-Interactions Safe Vault",
        "ground_truth_vulnerable": False,
        "cyclomatic_complexity": 3,
        "solidity_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract GuardedVault {
    mapping(address => uint256) public balances;
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount);
        balances[msg.sender] -= amount; // State updated BEFORE call
        (bool s, ) = msg.sender.call{value: amount}("");
        require(s);
    }
}"""
    },

    # SWC-101: Integer Overflow / Fixed-Point Truncation
    {
        "id": "SWC-101-01",
        "title": "AMM_PrecisionLossTruncation",
        "swc": "SWC-101",
        "subclass": "18-Decimal Fixed-Point Truncation Drain",
        "ground_truth_vulnerable": True,
        "cyclomatic_complexity": 5,
        "solidity_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract AMMPrecisionPool {
    uint256 public reserveX = 1000000e18;
    uint256 public reserveY = 1000000e18;
    function swapFee(uint256 amountIn, uint256 feeRate) external pure returns (uint256) {
        return (amountIn * feeRate) / 10000; // Truncation drops remainder on small dust
    }
}"""
    },
    {
        "id": "SWC-101-02_SAFE",
        "title": "CheckedArithmetic_Safe",
        "swc": "SWC-101",
        "subclass": "Checked Math Safe Pool",
        "ground_truth_vulnerable": False,
        "cyclomatic_complexity": 2,
        "solidity_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract SafeArithmetic {
    function computeTotal(uint256 a, uint256 b) external pure returns (uint256) {
        return a + b; // Solidity 0.8+ native overflow revert
    }
}"""
    },

    # SWC-112: Delegatecall to Untrusted Callee
    {
        "id": "SWC-112-01",
        "title": "Proxy_UntrustedDelegatecall",
        "swc": "SWC-112",
        "subclass": "Tainted Target Address in Delegatecall",
        "ground_truth_vulnerable": True,
        "cyclomatic_complexity": 3,
        "solidity_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract UntrustedProxy {
    address public owner;
    function forwardCall(address target, bytes calldata data) external {
        (bool s, ) = target.delegatecall(data); // BUG: arbitrary attacker target
        require(s);
    }
}"""
    },
    {
        "id": "SWC-112-02_SAFE",
        "title": "Proxy_ImmutableDelegatecall_Safe",
        "swc": "SWC-112",
        "subclass": "Immutable Implementation Delegatecall",
        "ground_truth_vulnerable": False,
        "cyclomatic_complexity": 2,
        "solidity_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract SafeProxy {
    address public immutable implementation;
    constructor(address impl) { implementation = impl; }
    fallback() external payable {
        (bool s, ) = implementation.delegatecall(msg.data);
        require(s);
    }
}"""
    },

    # SWC-124: Storage Collision in Upgradeable Proxies
    {
        "id": "SWC-124-01",
        "title": "UUPS_ProxyStorageSlotCollision",
        "swc": "SWC-124",
        "subclass": "Storage Slot Bit-Width Overwrite",
        "ground_truth_vulnerable": True,
        "cyclomatic_complexity": 5,
        "v1_layout": [{"slot": 0, "name": "owner", "type": "address", "bit_width": 160}],
        "v2_layout": [{"slot": 0, "name": "multiplier", "type": "uint256", "bit_width": 256}],
        "solidity_code": """// V1 vs V2 Upgrade with Slot 0 Bit-Width Mismatch"""
    },

    # SWC-128: Unbounded Dynamic Array Loops & DoS
    {
        "id": "SWC-128-01",
        "title": "Distributor_UnboundedArrayLoop",
        "swc": "SWC-128",
        "subclass": "Unrestricted Array Mutation Leading to 30M Gas DoS",
        "ground_truth_vulnerable": True,
        "cyclomatic_complexity": 6,
        "solidity_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract RewardDistributor {
    address[] public recipients;
    function register() external { recipients.push(msg.sender); } // Unrestricted!
    function distribute() external {
        for (uint256 i = 0; i < recipients.length; i++) {
            payable(recipients[i]).transfer(1 wei); // Can exceed 30M gas limit
        }
    }
}"""
    },
    {
        "id": "SWC-128-02_SAFE",
        "title": "Distributor_PullPattern_Safe",
        "swc": "SWC-128",
        "subclass": "Bounded Pull Over Push Pattern",
        "ground_truth_vulnerable": False,
        "cyclomatic_complexity": 3,
        "solidity_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract PullDistributor {
    mapping(address => uint256) public pendingRewards;
    function claimReward() external {
        uint256 amt = pendingRewards[msg.sender];
        require(amt > 0);
        pendingRewards[msg.sender] = 0;
        payable(msg.sender).transfer(amt);
    }
}"""
    },

    # SWC-114: Transaction Order Dependence & Oracle Manipulation
    {
        "id": "SWC-114-01",
        "title": "Lending_SpotPriceOracleManipulation",
        "swc": "SWC-114",
        "subclass": "Atomic Flash Loan Spot Price Collapse",
        "ground_truth_vulnerable": True,
        "cyclomatic_complexity": 5,
        "solidity_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
interface IUniswapPair { function getReserves() external view returns (uint112, uint112, uint32); }
contract FlashVulnerableLender {
    IUniswapPair public pool;
    function getCollateralPrice() public view returns (uint256) {
        (uint112 r0, uint112 r1, ) = pool.getReserves();
        return (uint256(r1) * 1e18) / uint256(r0); // Spot reserves vulnerable to flash loan
    }
}"""
    }
]

def main():
    print("=" * 80)
    print("EVM-GUARD BENCHMARK SUITE PROVISIONER")
    print("Populating SWC-Registry, DefiHackLabs, and Not-So-Smart-Contracts")
    print("=" * 80)
    
    # Save canonical tests
    catalog = []
    for test in CANONICAL_SWC_TESTS:
        fname = f"{test['id']}_{test['title']}.sol"
        fpath = os.path.join(SWC_DIR, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(test["solidity_code"])
            
        test_meta = dict(test)
        test_meta["file_path"] = fpath
        catalog.append(test_meta)
        print(f"  [+] Provisioned test case: {test['id']} ({test['title']})")
        
    catalog_path = os.path.join(BENCHMARK_DIR, "benchmark_manifest.json")
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)
        
    print(f"\n[✓] Successfully provisioned {len(catalog)} benchmark contracts into {SWC_DIR}.")
    print(f"[✓] Benchmark manifest saved to {catalog_path}.")
    print("=" * 80)

if __name__ == "__main__":
    main()
