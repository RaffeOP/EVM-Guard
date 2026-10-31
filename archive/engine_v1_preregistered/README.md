# EVM-Guard engine v1 (pre-registered SmartBugs run)

These are the `src/symbolic_engine.py` and `src/exploit_synthesizer.py` files that
produced `results/external_v1_preregistered/` (the run fixed by
`docs/EXTERNAL_EVAL_PROTOCOL.md`). They use opcode-order heuristics and permissive
replay criteria.

`src/` now holds engine v2 (CFG and abstract-stack dataflow checks, state-level
replay oracles), which produced `results/external/evm_guard_*`. v2 was written
after the v1 results on this corpus were known, so its results are post hoc.

To reproduce v1, copy these two files over `src/` and run
`src/eval/run_external_eval.py` followed by `src/eval/score_external.py`.
