# External evaluation protocol (fixed before any EVM-Guard run on this corpus)

## Corpus
- SmartBugs-curated, commit 230e649123477eff332742a59a1c7cc6dc286cab (2024-06-16), 143 files.
- Labels: the dataset's own `vulnerabilities.json` (category per labelled line).
- Compilation: each file with the solc version in the dataset's `versions.csv`
  (0.4.0–0.5.0). All 143 compile; 216 runtime contracts.
- No contract in this corpus is labelled safe. Negatives are therefore per category:
  a file is a negative for category X if it carries no label in X.

## Mapping from EVM-Guard properties to SmartBugs categories
| EVM-Guard finding | SmartBugs category |
|---|---|
| SWC-107 (read-only / cross-frame reentrancy) | reentrancy |
| SWC-101 (fixed-point truncation) | arithmetic |
| SWC-128 (loop gas exhaustion) | denial_of_service |
| SWC-112 (delegatecall taint) | access_control |
| SWC-124 (storage-slot collision) | access_control |
| SWC-114 (flash-loan oracle) | no SmartBugs category; reported separately, not scored |

Out of scope (no EVM-Guard property): unchecked_low_level_calls, bad_randomness,
front_running, time_manipulation, short_addresses, other. No recall is claimed for them.

Known construct mismatch: SmartBugs `arithmetic` is integer overflow/underflow,
while EVM-Guard's SWC-101 property targets truncation. Results for that row measure
how the property behaves on overflow-labelled code, not truncation detection.

## Scoring
- Unit: file. A file is flagged for category X if any runtime contract in it yields a
  finding that maps to X.
- Per category: TP, FP, FN, TN over all 143 files; precision, recall and FPR with exact
  95% Clopper-Pearson intervals. Undefined ratios (0/0) are reported as n/a.
- Every finding is counted, not just the first, and replay outcomes are reported
  separately as confirmed (`N_conf`) and SMT-only (`N_smt`).
- Latency: wall time of `analyze_bytecode` per runtime contract, summed per file.

## Rules
- The engine is not modified between this protocol and the run.
- Every contract is reported, including errors.

## Addendum A (added after the EVM-Guard run, before any baseline run on this corpus)
EVM-Guard results were known when this addendum was written; it fixes only how
baseline output is mapped, using each tool's own vulnerability names.

Slither 0.11.6 (detector name → category; impact not filtered for mapped detectors):
- reentrancy: reentrancy-eth, reentrancy-no-eth, reentrancy-benign, reentrancy-events, reentrancy-unlimited-gas
- arithmetic: none (Slither has no overflow detector) → not scored
- denial_of_service: calls-loop, costly-loop
- access_control: arbitrary-send-eth, arbitrary-send-erc20, suicidal, controlled-delegatecall, unprotected-upgrade, tx-origin, protected-vars, incorrect-modifier

Mythril 0.24.8 (reported SWC ID → category):
- reentrancy: SWC-107
- arithmetic: SWC-101
- denial_of_service: SWC-113, SWC-128
- access_control: SWC-105, SWC-106, SWC-112, SWC-115, SWC-124

Both tools are given the source file and the dataset-listed solc version. One run per
file (Mythril: 60 s process timeout, recorded as timeout, not as unflagged).
