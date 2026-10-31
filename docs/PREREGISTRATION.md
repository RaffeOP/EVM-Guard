# Evaluation Protocol (to be frozen before labelling)

## 1. Labelling specification
A contract is **vulnerable** if there exists a sequence of external transactions,
starting from a state reachable from deployment, that causes one of the following
and is reproducible on a forked chain at a stated block:
- unauthorised loss of funds or ownership;
- permanent denial of a function through unbounded gas use;
- a storage write to a protected slot that the source code does not intend.

A contract is **safe** if no such sequence was found after the labeller's documented
search procedure (time budget and method stated in the labelling log).
Labellers must record a rationale and a search log for every label.

## 2. Roles and limitation
- All labels are assigned by the single author using this protocol. No independent
  labeller is used. This is a declared limitation: labels can be checked for
  consistency and procedure, but not for independence.
- Blinding: the author labels from the blinded export only, before any tool output
  is opened. Labels are hashed and locked before scoring.
- Corpus provenance: labels for the SWC-Registry and Not-So-Smart-Contracts
  contracts are not independently sourced in this repository (no provenance headers
  found). They must be reported as author-assigned unless provenance is documented.

## 3. Steps
1. Freeze the code and this document (git tag).
2. Export blinded contracts with `src/eval/blind_export.py`.
3. The author labels from the blinded export only; record time, method, and rationale.
4. Re-label a random 20% subset after a 2-week gap and report intra-rater agreement (Cohen's kappa).
5. Lock labels (hash the labels file and publish the hash).
6. Release the key; run tools with repeated timing (10 repeats for Slither, 3 repeats for Mythril, 60 s timeout) and score results.

## 4. Primary outcomes (DeFi hazard models, n=80, author-labelled)
- Recall and false-positive rate with exact 95% Clopper-Pearson intervals.
- Timeouts reported separately from missed detections.
- Latency median and IQR over 10 repeats per tool per contract, with matched timing scope.

## 5. Reporting rules
- Report every contract, including ones where the tool timed out or errored.
- No post-hoc changes to thresholds, labels, or inclusion after lock.

## 6. Baseline configuration (fixed before any run)
- Slither 0.11.6 via `src/eval/run_baselines.py`. A contract is flagged only if a
  detector with impact High or Medium fires. Informational detectors (for example
  `solc-version`, `naming-convention`) are excluded, because counting them flags
  every contract. Repeats: 10 per contract. Timeout: 60 s.
- Mythril 0.24.8 (Python 3.12 venv). Flagged if any issue is reported. Repeats: 3 per
  contract (deviation from 10, to fit the time budget). Timeout: 60 s, recorded as
  `timeout` and never as an unflagged result.
- Securify2 is not evaluated. Its README states support for Solidity >= 0.5.8, with the
  default Docker build pinned to 0.5.12 and the compiler version configurable. It does not
  state that 0.8.20 fails. Running it on 0.8.20 would be an untested configuration, so
  it is reported as not evaluated rather than estimated.
- Both tools run with solc 0.8.20 and EVM version cancun. Toolchain paths are
  recorded in the runner.
