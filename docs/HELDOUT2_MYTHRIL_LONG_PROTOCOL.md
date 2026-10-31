# Protocol amendment: Mythril rerun on timed-out files, held-out benchmark 2

Written and frozen before the rerun. Freeze hash in `docs/HELDOUT2_MYTHRIL_LONG_FREEZE.sha256`.
It amends `docs/HELDOUT2_EVAL_PROTOCOL.md` only for Mythril's execution limit. Everything else in that protocol is unchanged.

## Why
In the primary run (60 s per file), Mythril timed out on 231 of 389 files. Those timeouts count as unflagged, so Mythril's recall on that benchmark is an underestimate. This amendment measures how much of that is due to the time limit.

## What is run
- Input: the 231 files whose Mythril status was `timeout` in `results/heldout2/mythril_files_*.csv`, listed by `contract_id` in `results/heldout2/mythril_long_ids.json`.
- Mythril 0.24.8, with the same invocation as the primary run (`-o json`), except `--execution-timeout 290` and a 300 s process kill.
- The same category mapping (`MYTHRIL_MAP` in `src/eval/run_external_baselines.py`), the same solc versions, and the same catalog.
- 8 shards, run with `--shard i --of 8`.

## Reporting
- Primary result: unchanged. Mythril's 60 s results are reported as before.
- Secondary result: the 231 files are rescored with the rerun output in place of the 60 s status. This shows the ceiling Mythril reaches with more time. It is labelled as a secondary, time-extended analysis.
- Files that still time out at 300 s stay unflagged. Their count is reported.
- No other changes to the scoring.

## Rules
- The set of files, the time limits, and the mapping are fixed here.
- Results are reported whatever they show.
