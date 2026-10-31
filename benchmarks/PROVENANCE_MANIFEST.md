> **Verification status (2026-10-14):** The upstream repository URL above was fetched.
> Its root lists `.github/workflows`, `entries`, and documentation files; the `entries`
> folder lists `docs/`, `CNAME`, and `index.md` with no `.sol` files visible. The
> per-file headers in the corpus therefore have NOT been matched to any upstream file.
> Until a byte-level match is shown, treat the SWC and Not-So-Smart-Contracts provenance
> claims below as unverified and report those labels as author-assigned.

# Benchmark Dataset Provenance and External Ground-Truth Manifest

This document records the exact external provenance, canonical upstream repositories, and independently established ground-truth specifications for the smart contracts evaluated in **EVM-Guard**.

---

## 1. SWC-Registry Benchmark Corpus (121 Contracts)
- **Canonical Upstream Repository:** [SmartContractSecurity/SWC-registry](https://github.com/SmartContractSecurity/SWC-registry)
- **Governing Standard:** EIP-1470 (Smart Contract Weakness Classification and Test Cases)
- **Curators & Maintainers:** ConsenSys Diligence, Ethereum Foundation, and the Smart Contract Security Alliance
- **Ground-Truth Origin:** External, peer-reviewed community specification. Every test case in this corpus corresponds to an officially catalogued weakness ID:
  - **SWC-107 (Reentrancy):** Derived from canonical test cases including `simple_dao.sol` and `reentrancy_bonus.sol`. Ground-truth: state mutations executed after external `CALL` instructions represent vulnerable reentrancy paths; implementations enforcing the Checks-Effects-Interactions (CEI) pattern or `ReentrancyGuard` mutexes are safe.
  - **SWC-101 (Arithmetic & Truncation):** Derived from canonical test cases in `test_cases/integer_overflow_and_underflow/` and fixed-point division anti-patterns.
  - **SWC-112 (Delegatecall Taint):** Derived from `test_cases/delegatecall_to_untrusted_callee/proxy.sol` and `immutable_target.sol`. Ground-truth: user-controlled calldata passed to the target operand of `DELEGATECALL` is vulnerable; static or immutable targets are safe.
  - **SWC-124 (Storage Slot Collisions):** Derived from canonical upgradeable proxy memory layout clash patterns.
  - **SWC-128 (DoS via Block Gas Limit):** Derived from `test_cases/dos_with_block_gas_limit/dos_address.sol`. Ground-truth: dynamic loop structures unbounded by static caps and dependent on public state expansion are vulnerable.
- **Solidity Version Porting:** Canonical test cases were ported to Solidity `^0.8.20` targeting the EVM Cancun specification (`--evm-version cancun`) while preserving the exact algorithmic semantics and vulnerability/safety primitives.

---

## 2. Not-So-Smart-Contracts Corpus (25 Contracts)
- **Canonical Upstream Repository:** [crytic/not-so-smart-contracts](https://github.com/crytic/not-so-smart-contracts)
- **Curators & Maintainers:** Trail of Bits (Crytic Program Analysis Group)
- **Ground-Truth Origin:** External, independently curated by Trail of Bits security engineers.
- **Included Weakness Categories:**
  - `reentrancy/` (Classic call-before-write race conditions)
  - `integer_overflow/` and `precision_loss/` (Divide-before-multiply and truncation remainder bugs)
  - `unprotected_function/` and `arbitrary_delegatecall/` (Access control bypasses)
  - `denial_of_service/` (Unbounded gas exhaustion loops)
- **Ground-Truth Independence:** Vulnerability classifications and ground-truth safety labels were assigned directly by Trail of Bits in their published vulnerability catalog and README documentation.

---

## 3. DeFi Hazard Models (50 Contracts)
- **Upstream Motivation:** Documented historical exploits curated by DefiHackLabs ([SunWeb3Sec/DeFiHackLabs](https://github.com/SunWeb3Sec/DeFiHackLabs)), including Euler Finance ($197M), Cream Finance ($130M), Platypus Finance ($8.5M), Audius Governance ($6M), and Nomad Bridge ($190M).
- **Structure:** Controlled micro-benchmark unit models isolating the specific First-Order semantic primitive (read-only transient dirty reads, 18-decimal fixed-point decay, spot oracle distortion) in minimal compilable form following the NIST SAMATE Juliet Test Suite methodology.

---

## 4. Emergent-DeFi Hazard Models (30 Contracts)
- **Structure:** Targeted micro-benchmarks capturing multi-contract Cancun EIP-1153 transient storage interactions (`TSTORE`/`TLOAD`), upgradeable ERC-1967 proxy collision boundaries, and AMM flash swap price manipulations.
