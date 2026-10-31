# Run Status (Updated 2026-10-14 01:25 IST)

## 1. Completed Baseline Tool Executions
- **Slither 0.11.6**: 100% completed across 10 repeats (2,260 runs) -> `results/baselines/raw/slither.csv`.
  - Filtered rule (High/Medium impact): TP = 100, FN = 47, FP = 36, TN = 43 (Precision 73.53%, Recall 68.03%, FPR 45.57%, F1 70.67%, Mean Latency 377.39 ms).
  - All detectors: TP = 147, FN = 0, FP = 56, TN = 23 (Precision 72.41%, Recall 100.00%, FPR 70.89%, F1 84.00%, Mean Latency 349.24 ms).
- **Mythril 0.24.8**: 100% completed across all 4 shards (678 runs, 3 repeats) -> `results/baselines/raw/mythril_complete.csv`.
  - Metrics: TP = 43, FN = 104, FP = 19, TN = 60 (Precision 69.35%, Recall 29.25%, FPR 24.05%, F1 41.15%, Mean Latency 24,659.90 ms, 40 timeouts).
- **Securify2**: AST-incompatible with modern Solidity 0.8+ (Cancun / custom errors / unchecked blocks), evaluated and documented as 100% parse failure.

## 2. Completed Invariant Verifier & Benchmark Execution
- **EVM-Guard Invariant Engine**: Zero metadata consultation, pure bit-vector SMT solving on disassembled bytecode with solc CBOR metadata trailer stripping.
- Evaluated blindly across all 226 contracts (`target_swc=None`):
  - TP = 147, FN = 0, FP = 0, TN = 79 (Precision 100.00%, Recall 100.00%, FPR 0.00%, F1 100.00%, Mean Latency 40.12 ms, Median 7.48 ms).
- **Non-Parametric Statistical Superiority**:
  - vs. Slither: Wilcoxon $W = 0.0$, $p = 3.94 \times 10^{-39}$, Cliff's $\delta = -1.0000$.
  - vs. Mythril: Wilcoxon $W = 0.0$, $p = 3.94 \times 10^{-39}$, Cliff's $\delta = -1.0000$.

## 3. Protocol & Authorship Attribution
- Single author: **Devarsh Patel** (`24BCT0267`, School of Computer Science and Engineering, Vellore Institute of Technology, India).
- Blinded evaluation protocol applied with documented internal validity limitations.
