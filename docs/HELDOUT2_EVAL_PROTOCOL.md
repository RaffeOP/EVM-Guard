# Held-out evaluation protocol 2: labelled benchmark (bit-smartcontract-analysis)

Written and frozen before any EVM-Guard or baseline run on this corpus. The freeze
hash is in `docs/HELDOUT2_EVAL_FREEZE.sha256`. Engine v2 is unchanged since commit
`4164799` (the engine source files in `src/` have no modifications after that commit).
This corpus was not used to design, tune or evaluate any version of EVM-Guard, and
the SolidiFI and SmartBugs results were not used to choose any of the rules below.

## Corpus
- Repository: `bit-smartcontract-analysis/smartcontract-benchmark`, commit
  `8b903aae40648ad0ead87662857c6685542710d5` (committed 2023-09-14), folder
  `labelled-dataset/`. The repository has **no licence file**. Its contracts are not
  redistributed in the artifact package; only the catalog of hashes, the scripts and
  the results are included.
- 389 Solidity files in 11 folders (counted from the files at the pinned commit; the
  README table gives different per-folder numbers and is not used).

## Labels and mapping (fixed here)
The label of a file is its folder. Categories are the SmartBugs categories used in
`src/eval/run_external_baselines.py` and `src/eval/run_external_eval.py`.

| Folder | Files | Label | Category | Scored |
|---|---|---|---|---|
| `reentrancy` | 81 | SWC-107 | reentrancy | yes |
| `arithmetic` | 65 | SWC-101 | arithmetic | yes (construct mismatch: labels are overflow, EVM-Guard checks truncation) |
| `unsafe_delegatecall` | 12 | SWC-112 | access_control | yes |
| `tx_origin` | 10 | SWC-115 | access_control | yes (EVM-Guard has no tx.origin check) |
| `unsafe_suicide` | 11 | SWC-106 | access_control | yes (EVM-Guard has no SELFDESTRUCT check) |
| `unchecked_send` | 52 | SWC-104 | none | no |
| `TOD` | 60 | SWC-114 | none | no |
| `time_manipulation` | 60 | SWC-116 | none | no |
| `bad_randomness` | 10 | SWC-120 | none | no |
| `gasless_send` | 11 | SWC-126 | none | no |
| `safecontract` | 17 | none | none | negative for every category |

The access-control grouping follows the SmartBugs mapping of SWC-105, 106, 112, 115
and 124 to access control. Files in folders marked "none" are negatives for every scored
category, as the SmartBugs protocol treats unscored labels. No `denial_of_service` label
exists in this corpus, so **denial of service is not evaluated** here.
Gasless send (SWC-126, insufficient gas griefing) is not mapped to denial of service,
because it is a different weakness from the loop-gas class (SWC-128) that EVM-Guard checks.

Positives: reentrancy 81, arithmetic 65, access control 33 (12 + 10 + 11).

## Compilation
Each file is compiled with `solc --combined-json bin-runtime`, with no optimizer, by
the highest installed version whose range satisfies the file's pragma, as in
`src/eval/build_heldout_catalog.py`. Installed versions: 0.4.0, 0.4.9 to 0.4.25,
0.5.0, 0.5.8, 0.5.12, 0.8.20. Files that do not compile are recorded as errors and
count as unflagged. Nothing is excluded.

## Engine and baselines
- EVM-Guard: engine v2 at commit `4164799`.
- Slither 0.11.6 and Mythril 0.24.8 with the mappings in `run_external_baselines.py`,
  including the 60 s Mythril timeout. Slither's denial-of-service and Mythril's
  denial-of-service findings are computed but not scored, since there are no
  denial-of-service positives.

## Scoring
Identical to the SmartBugs and SolidiFI protocols. Unit: file. A file is flagged for
category `X` if any runtime contract yields a finding mapping to `X`. Per category:
TP, FP, FN, TN, recall, precision, FPR with exact 95% Clopper–Pearson intervals.
Undefined ratios are n/a. Errors and timeouts count as unflagged. Confirmed results
are reported separately.

## Rules
- The mapping above is fixed. It may not be changed after any result is seen.
- Every file is reported, including errors and timeouts.
- EVM-Guard v2 is not modified for this run. Any engine change after this freeze makes
  the result a new revision on a corpus that has been seen, so the held-out label of
  this corpus is then spent. Such a change would need a fourth corpus to be tested.
- No analysis is added after the run that is not listed in this document.
