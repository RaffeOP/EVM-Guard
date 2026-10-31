# Held-out evaluation protocol: SolidiFI bug-injection benchmark

Written and frozen before any EVM-Guard run on this corpus. The freeze hash is in
`docs/HELDOUT_EVAL_FREEZE.sha256`. This corpus was not used to design or tune any
version of EVM-Guard. It is therefore the held-out test of v2 that the SmartBugs
evaluation could not provide.

## Corpus
- Buggy contracts: `DependableSystemsLab/SolidiFI-benchmark`, commit
  `4b0573e1b3f7031396de6f48f7f3e7380222ad3a` (2020-06-23), folder `buggy_contracts/`.
  350 files: 50 per injected bug type.
- Clean contracts: `DependableSystemsLab/SolidiFI`, commit
  `ebb02e3c511a3c93975822101cbbbdaa12a33da0` (2022-05-17), folder `contracts/`.
  50 files, used as additional negatives.
- Archive hashes (SHA-256): `solidifi_bench.zip` =
  `cd0f797718932ef4fe89de756e0ed894fc749749037b5dfb21e6f5ab4123ef5f`;
  `solidifi.zip` = `04c0d8d6ae1766894696648cea90d7854622929ef62dbf695e47ce0fbc38066b`.

## Labels and mapping (fixed here)
The label of a buggy file is its folder. The mapping to EVM-Guard properties is:

| Folder | Label | EVM-Guard property | Scored |
|---|---|---|---|
| `Re-entrancy` | reentrancy | SWC-107 | yes |
| `Overflow-Underflow` | arithmetic | SWC-101 (truncation) | yes, construct mismatch as in SmartBugs |
| `tx.origin` | access control (SWC-115) | none | no |
| `TOD` | transaction order | none (SWC-114 is not this class) | no |
| `Timestamp-Dependency` | timestamp | none | no |
| `Unchecked-Send` | unchecked low-level call | none | no |
| `Unhandled-Exceptions` | unchecked return value | none | no |

There is no denial-of-service folder, so denial of service is **not** evaluated on
this corpus. Its precision is not estimated by this protocol.

Negatives follow the SmartBugs protocol: a file is a negative for category `X` if it
carries no label in `X`. The clean contracts are negatives for every category.

## Compilation
Each file is compiled with `solc --combined-json bin-runtime`, with no optimizer,
as in `src/eval/build_external_catalog.py`. The compiler is the highest installed
version whose range satisfies the file's `pragma solidity` line. Installed versions
are 0.4.0, 0.4.9 to 0.4.25, 0.5.0, 0.5.8, 0.5.12 and 0.8.20. Files that do not
compile are recorded as errors and reported. They count as unflagged.

## Engine and baselines
- EVM-Guard: engine v2 as in the git commit recorded at run time.
- Slither 0.11.6 and Mythril 0.24.8, with the same runners and category mappings
  as the SmartBugs protocol (`src/eval/run_external_baselines.py`), including the
  60 s Mythril timeout.

## Scoring
Identical to the SmartBugs protocol. Unit: file. Flagged for `X` if any runtime
contract yields a finding mapping to `X`. Per category: TP, FP, FN, TN, recall,
precision, FPR, with exact 95% Clopper–Pearson intervals. Undefined ratios are n/a.
Errors and timeouts count as unflagged. Confirmed results are reported separately.

## Rules
- The mapping above is fixed. It may not be changed after any result is seen.
- Every file is reported, including errors.
- Any engine change after this freeze makes the run a new revision, labelled as such.
