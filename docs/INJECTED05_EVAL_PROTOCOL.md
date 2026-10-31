# Pre-registered evaluation protocol 4: fresh injected corpus, Solidity 0.5.12

Written and frozen before any run on this corpus. Freeze hashes: `docs/INJECTED05_EVAL_FREEZE.sha256`
(covers this file, the generator `src/eval/build_injected_corpus_05.py`, its catalog
`benchmarks/injected05_catalog.json`, and the engine manifest `docs/INJECTED05_ENGINE_MANIFEST.sha256`).

## Why this corpus
Protocol 3 (solc 0.8.20, seed 20261014) gave zero flags, because of two engine defects on
0.8 bytecode (see the report, §9). Engine v3 plus the PUSH0 decoder is scoped to Solidity 0.4–0.5.
This corpus is the same families and skeletons as protocol 3, written in Solidity 0.5 syntax,
with a new seed (`20261015`). It is a new sample, not a re-run of the spent corpus.

## Limitation stated up front
It is still synthetic: labels come from construction, the families are few, and the same
skeleton generator makes all files. It tests the detector on its own injection patterns, not
on real contracts. It can give a precision estimate on this distribution only.

## Corpus
- 210 files, Solidity 0.5.12, 30 per group. Groups and labels as in protocol 3:
  `reentrancy_injected` (reentrancy), `dos_injected` (denial of service), and five negative
  groups: `neg_cei`, `neg_mutex`, `neg_transfer`, `neg_bounded_loop`, `neg_clean`.
- All 210 compile with solc 0.5.12, no optimizer.

## Engine and baselines
- EVM-Guard: the working tree at freeze time (manifest). It is v3 (stipend bound) plus the PUSH0
  decoder. The candidate-set experiment is archived and not in the engine.
- Slither 0.11.6 and Mythril 0.24.8, same runners and mappings as the other protocols, 60 s.

## Scoring and analysis (fixed)
Unit: file. Categories: reentrancy (SWC-107) and denial of service (SWC-128). Arithmetic and
access control are not scored, since the corpus has no injected instance of them.
Per category: TP, FP, FN, TN, recall, precision, FPR, with exact 95% Clopper–Pearson intervals.
Breakdown of false positives by group. Comparison with Slither and Mythril on the same files.

## Rules
- Any engine change after the run spends this corpus; the result is then post hoc.
- Report whatever the run shows.
