# Engine v2 (commit 4164799): stipend defect

These two files are engine v2 as committed in `4164799`. They produced every v2 result in the paper, including the SmartBugs, SolidiFI and second-benchmark tables.

Defect: `_is_stipend_only` tested only constant gas. Solidity lowers `address.transfer` to a CALL whose gas is `2300 * ISZERO(v)`, a computed value, so these calls were not excluded from SWC-107 even though the paper's specification excludes them.

Corrected in engine v3 (working tree): `evm_dataflow.py` propagates a sound upper bound on each stack value, and `hazard_rules.py` excludes a call when its gas bound is at most 2300. Tests: `tests/test_stipend_bound.py`.

To reproduce v2 results, copy these two files over `src/` before running `src/eval/run_external_eval.py`.
