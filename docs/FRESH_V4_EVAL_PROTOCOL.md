# Pre-registered evaluation protocol 5: engine v4 on two fresh injected corpora

Frozen before any run on these corpora. Hashes: `docs/FRESH_V4_EVAL_FREEZE.sha256`
(covers this file, both generators, both catalogs, and the engine manifest `docs/FRESH_V4_ENGINE_MANIFEST.sha256`).

## Engine v4 (frozen)
- v3 stipend bound, plus `PUSH0` decoding (`src/evm_disasm.py`), plus the slot-based lock rule
  (`src/hazard_rules.py`, `_slot_lock_protected`), plus the return-site fallback for unresolved
  JUMPs (`src/evm_dataflow.py`, `return_sites`).
- The fallback is a sound over-approximation of return flow, so it can add paths and false
  positives but not remove findings.

## Corpora (both new seeds, never run before)
- `injected8b`: solc 0.8.20, seed 20261016, 210 files, groups as in the earlier injected corpora.
- `injected05b`: solc 0.5.12, seed 20261017, 210 files.
- Labels by construction, same groups and labels as protocols 3 and 4. Synthetic.

## Analysis (fixed)
Per corpus and category (reentrancy, denial of service): TP, FP, FN, TN, recall, precision,
FPR, exact 95% intervals; false positives by group; Slither 0.11.6 and Mythril 0.24.8 on the same files.
Solidity 0.8 is reported as an extension beyond the paper's stated scope, because the scope
was narrowed to 0.4–0.5 before this run. Its result is reported whatever it is.

## Rules
- Any engine change after this freeze spends both corpora.
