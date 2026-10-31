# Pre-registered evaluation protocol 6: engine v5 on a final fresh corpus (Solidity 0.5.12)

Frozen before any run on this corpus. Hashes: `docs/FINAL_V5_EVAL_FREEZE.sha256`
(covers this file, the generator, the catalog, and the engine manifest `docs/FINAL_V5_ENGINE_MANIFEST.sha256`).

## Engine v5 (frozen)
- v3 stipend bound + `PUSH0` decoding (`src/evm_disasm.py`) + slot-based lock rule
  (`src/hazard_rules.py`, `_slot_lock_protected`).
- The return-site fallback of v4 is removed: it lowered real-benchmark precision (SmartBugs
  reentrancy 78.4% to 55.6%, SolidiFI 58.8% to 23.6%) and is out of the 0.4–0.5 scope.

## Corpus
- `injected05c`: solc 0.5.12, seed 20261018, 210 files, same groups as protocols 3–5.
- This corpus has not been used for any engine version. Protocol 5's corpora (seeds 20261016,
  20261017) were run with v4 and are now spent for v5.
- Synthetic. Labels by construction. Limits as stated in the paper.

## Analysis (fixed)
Reentrancy and denial of service: TP, FP, FN, TN, recall, precision, FPR, exact 95% intervals;
false positives by group; Slither 0.11.6 and Mythril 0.24.8 on the same files.

## Rules
- Any engine change after this freeze spends this corpus.
