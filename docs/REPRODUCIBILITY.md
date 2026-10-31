# Reproducing the EVM-Guard results

Verified on 2026-10-31 (macOS arm64, Python 3.12, `requirements-eval.txt`): a fresh copy of the repository ran `./reproduce.sh` end to end in 14 minutes.

## One command

```bash
./reproduce.sh
```

The script installs the pinned Python packages and solc compilers, clones the two
external datasets at their pinned commits, recompiles every runtime contract with the
solc version recorded in its catalog, and runs engine v5 on all five corpora. Outputs
go to `results/reproduction/<corpus>/`.

## Why a build step is needed

Compiled bytecode (`*.bin-runtime`) and the external datasets are not committed
(`.gitignore`). Earlier catalogs stored absolute paths from the author's machine, so
the evaluation could not run elsewhere. Catalogs now store paths relative to the
repository root (`src/eval/repo_paths.py`), and `src/eval/compile_catalog.py` rebuilds
the bytecode and fails if solc emits a different set of runtime contracts than the
catalog lists.

## Expected results (engine v5, file level)

| Corpus | Files | Reentrancy TP / FP | Precision | Other |
|---|---|---|---|---|
| SmartBugs-curated @ `230e6491` | 143 | 29 / 7 | 80.6% | DoS 5/34, access control 2/0, arithmetic 1/80 |
| SolidiFI | 400 | 50 / 35 | 58.8% | arithmetic 45/315 |
| Labeled benchmark @ `8b903aa` | 389 | 79 / 25 | 76.0% | access control 7/0, arithmetic 46/245 |
| Synthetic seed 1 (`injected05`) | 210 | 30 / 0 | 100% | DoS 30/0 |
| Synthetic final (`injected05c`) | 210 | 30 / 0 | 100% | DoS 30/0 |

On 2026-10-31 the flags of every file on all five corpora matched the archived v5 runs
(`results/v5_old/`, `results/final_v5/`) exactly. The reproduction outputs are in
`results/reproduction_2026-10-31/`.

## Known differences from the frozen records

- **Engine manifest.** Four files differ from `docs/FINAL_V5_ENGINE_MANIFEST.sha256`:
  `src/evm_disasm.py`, `src/hazard_rules.py`, `src/symbolic_engine.py` and
  `src/z3_encoder.py`. They were changed after the v5 freeze, and the frozen copies were not
  kept. The current sources include the ablation switches of `src/engine_options.py`,
  each of which defaults to the full engine. The current sources are recorded in `docs/V5_REPRODUCTION_MANIFEST.sha256`,
  and they reproduce the v5 flags file by file on all five corpora (above).
- **One contract is not analysed.** `LedgerChannel` in `reentrancy/spank_chain_payment.sol`
  (in SmartBugs-curated and in the labeled benchmark) contains an unlinked library
  placeholder, so its runtime code is not valid hexadecimal. The current runner records it
  as an error. Earlier runs recorded it as `ok` with zero instructions, so it was never
  analysed in any run. With the placeholder linked, SmartBugs reentrancy recall becomes
  96.8% (`results/sensitivity/placeholder_linking.json`).
- **`results/v5check/`.** This run flags one more SmartBugs file for reentrancy
  (`unchecked_low_level_calls__0xec329ffc...`, 78.4% precision) than the archived v5 run.
  It is not reproduced by the current sources, which match the archived v5 run, and it is
  not used in the paper.
- **SmartBugs protocol digest.** `docs/EXTERNAL_EVAL_FREEZE.sha256` matches lines 1–39 of
  `docs/EXTERNAL_EVAL_PROTOCOL.md`; Addendum A (lines 40–58) was added after the first
  EVM-Guard run and before any baseline run.

## Baselines

Slither 0.11.6 and Mythril 0.24.8 are run by `src/eval/run_external_baselines.py`. They
were not rerun on 2026-10-31; their archived outputs are in `results/external/`,
`results/heldout/`, `results/heldout2/` and the synthetic-test folders.
