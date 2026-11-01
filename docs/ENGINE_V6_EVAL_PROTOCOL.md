# Pre-registered evaluation protocol 7: engine v6

Frozen before engine v6 runs on any corpus listed under "Evaluation corpora". Hashes of this
file, the labelling rubric, the corpus builders and the v6 engine manifest are in
`docs/ENGINE_V6_EVAL_FREEZE.sha256`. The frozen engine sources are kept byte for byte in
`archive/engine_v6/` (`archive/engine_v6/MANIFEST.sha256`), so the v6 run can be repeated
from the frozen copies even if `src/` changes later.

## Engine v6 (frozen)

Engine v5 plus four components, each behind one switch in `src/engine_options.py`:

1. Return-site tracking (`should_track_return_sites`): the CFG fixpoint analyses each block
   once per context, the JUMPDEST addresses on the abstract stack (at most 4), with at most
   32 contexts per block (`src/evm_dataflow.py`).
2. Z3 path feasibility (`should_check_path_feasibility`): a reentrancy candidate that passes
   the v5 pattern and mutex rules is kept only if Z3 does not refute (a) a path from the entry
   through the call to the later write and (b) a re-entrant invocation, from the storage state
   at the call, that reaches the same call or a read in another public function of a slot
   the write updates (`src/path_feasibility.py`, `src/symbolic_path.py`). Only UNSAT
   rejects. Search limits: 1 s per solver call, 4 s and 3,000 blocks per search, 30 s per
   contract; past a limit the candidate is kept and recorded as `unknown`.
3. Attacker model (`should_assume_unprivileged_attacker`): the attacker is an address that
   is not a PUSH20 constant of the bytecode and not held, at any byte offset, in a fixed
   storage slot read on the path, unless some function writes that slot with the caller or
   with unguarded calldata. The attacker sends the transaction, is the callee of the call,
   and sends the re-entrant call.
4. Witness replay (`should_seed_replay_with_witness`): a second Z3 query fixes the sandbox
   roles and yields calldata, call value and starting storage. The transaction runs from that
   state with the re-entering attacker and with a passive receiver; the finding is confirmed
   in this tier only if re-entry yields strictly more. This tier is reported separately from
   the default-state replay of v5, which is unchanged.

The reentrancy finding records its kind: same-function (the re-entry reaches the call),
cross-function (it reaches a stale read in another public function), read-only (that
function writes no storage and makes no call), or unclassified (a search limit was hit).

The other classes (SWC-101, 112, 124, 128, Class E) are unchanged from v5.

## How v6 was developed

v6 was developed on SmartBugs-curated, on the five fixtures in `tests/fixtures/`, and on the
spent Solidity 0.8.20 corpus `injected8b` (spent by protocol 5). Its SmartBugs-curated and
`injected8b` results are therefore post hoc. v6 was not run on SolidiFI, the labelled
benchmark, either seed-1 or final synthetic corpus, or any corpus below before this freeze.

## Evaluation corpora (each run once with v5 and v6 after the freeze)

| Corpus | Status for v6 |
|---|---|
| SolidiFI (400 files) | not used in v6 development; used for v2, v3, v5 |
| Labelled benchmark (389 files) | not used in v6 development; used for v2, v3, v5 |
| `injected05d`: Solidity 0.5.12, seed 20261101, 210 files | new |
| `injected8c`: Solidity 0.8.20, seed 20261102, 210 files | new |
| `mainnet`: deployed contracts, built by `src/eval/build_mainnet_catalog.py` | new |

The synthetic corpora reuse the template families of protocols 3-6, so they test the detector on
its own injection patterns, as before. The engine developer has seen those families.

The mainnet corpus: every entry of the smart-contract-sanctuary mainnet index (repository
`tintinweb/smart-contract-sanctuary-ethereum` at commit
`015d0105102504dc8733a18c3543f87f1829a5e8`, `contracts/mainnet/contracts.json` with SHA-256
`fdb990d86b24c50b11f67f056422f9dc5fe6a44c4d4f2cb2917c4b601965dbed`) whose compiler is
v0.4.x or v0.5.x, minus every address that appears in an earlier corpus, that holds a non-zero
ether balance and non-empty code at the block where the builder starts. The engines analyse
the deployed runtime code read from the chain.

## Analysis (fixed)

- SolidiFI, labelled benchmark, synthetic corpora: as in the earlier protocols (file level;
  TP, FP, FN, TN; recall, precision, FPR with exact 95% Clopper-Pearson intervals), for v5
  and v6, with an exact McNemar test of v5 against v6 on the same files, for false positives
  and for true positives. Reentrancy is the claimed category; the others are reported.
- Mainnet corpus: per engine, the number of contracts analysed, errors, and contracts flagged
  for reentrancy; the ether they hold; per-contract analysis time (median, mean, 95th
  percentile, maximum); the reentrancy kinds and feasibility verdicts of v6; replay
  confirmations in both tiers.
- Hand-checked sample: all contracts flagged by v5 or v6 for reentrancy if there are at most
  120; otherwise a uniform random sample of 120 from their union (Python `random.Random(7)`
  over the sorted addresses). Each is labelled from its verified source with
  `docs/LABELLING_RUBRIC.md`, from an export that lists the contract and its source only, in
  shuffled order, without the engine that flagged it (`src/eval/blind_export.py`). Precision of
  each engine on the sample, with exact 95% intervals, and McNemar on the sample.
- A contract labelled exploitable that holds ether is handled under "Disclosure" below and is
  reported in the paper only in aggregate, without its address.

## Rules

- Any change to an engine source file after this freeze spends every corpus above for v6.
- Results are reported whatever they are, including if v6 is worse than v5.

## Disclosure

A contract labelled exploitable with a non-zero balance is not exploited, not tested on a
fork with real funds moved, and not published. Its owner or the responsible project is
contacted privately through a channel listed for it, if one exists, before any public
mention, and the paper gives aggregate counts only.
