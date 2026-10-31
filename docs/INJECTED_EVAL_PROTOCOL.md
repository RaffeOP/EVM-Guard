# Pre-registered evaluation protocol 3: injected reentrancy and denial-of-service corpus

Written and frozen before any run of any tool on this corpus. The freeze hashes are in
`docs/INJECTED_EVAL_FREEZE.sha256`, and they cover this file, the generator
`src/eval/build_injected_corpus.py`, the catalog `benchmarks/injected_catalog.json`, and the
engine files in `src/` (manifest `docs/INJECTED_ENGINE_MANIFEST.sha256`). Any change to a frozen
file after the run invalidates the run.

## Purpose
Engine v3 has been developed and tuned on SmartBugs-curated, SolidiFI and the second
benchmark, so none of those is a held-out test for v3. This corpus is a fresh test. Its labels
are assigned by construction, not by an external auditor. That is a limitation, and the paper
states it. The generator fixes the families and the seed before any run.

## Corpus
- 210 Solidity 0.8.20 contracts, 30 per group, produced by `src/eval/build_injected_corpus.py`
  with seed `20261014`. Each contract has one skeleton (a deposit/balance ledger) with seeded
  identifiers and 0–2 filler functions.
- Groups and labels (the label is the hazard the group injects):

| Group | Files | Label | Scored as |
|---|---|---|---|
| `reentrancy_injected` | 30 | reentrancy | positive, reentrancy |
| `dos_injected` | 30 | denial_of_service | positive, denial of service |
| `neg_cei` | 30 | none | negative: balance written before the external call |
| `neg_mutex` | 30 | none | negative: call guarded by a mutex |
| `neg_transfer` | 30 | none | negative: `.transfer` (2300-gas stipend, cannot re-enter) |
| `neg_bounded_loop` | 30 | none | negative: constant loop bound |
| `neg_clean` | 30 | none | negative: no injected pattern |

- Positives: reentrancy 30, denial of service 30. Negatives for each category: 180.
- Arithmetic and access control are **not scored**: the corpus has no injected overflow,
  truncation, tx.origin or delegatecall pattern. The paper does not claim them from this corpus.

## Compilation
`solc 0.8.20`, no optimizer, `--combined-json bin-runtime`, as in the other protocols.
All 210 files compile. Files that do not compile count as unflagged.

## Engine and baselines
- EVM-Guard: engine v3 as in the frozen engine manifest (working tree at freeze time).
- Slither 0.11.6 and Mythril 0.24.8, same runners and category mappings as the other protocols,
  60 s Mythril timeout. Mythril and Slither are run to give comparators on this corpus.

## Scoring
Identical to the other protocols: unit is the file, flagged for `X` if any runtime contract
yields a finding mapping to `X`. Per category: TP, FP, FN, TN, recall, precision, FPR,
exact 95% Clopper–Pearson intervals. Denial of service uses SWC-128 in EVM-Guard and in
Mythril's mapping. Slither uses the `calls-loop` and `costly-loop` detectors.

## Analysis plan (fixed here)
1. Primary: EVM-Guard v3 precision, recall and FPR for reentrancy and denial of service,
   with intervals.
2. Breakdown of false positives by group, so the hard negatives can be seen.
3. Comparison with Slither and Mythril on the same files.
4. No threshold is chosen after the run. Results are reported whatever they show.

## Rules
- The mapping, the groups, the seed and the engine are frozen. Nothing in them changes after
  any result on this corpus is seen.
- If the engine has to change after the run, the corpus is spent and this result is post hoc.
- Limitation stated in the paper: labels are by construction, the families are few, and the
  injection is a fixed template set, so external validity is limited.
