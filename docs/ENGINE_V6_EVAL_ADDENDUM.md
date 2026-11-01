# Addendum to protocol 7 (written 2026-11-01, before the mainnet corpus existed)

`src/eval/build_mainnet_catalog.py` was changed after the freeze digest
`docs/ENGINE_V6_EVAL_FREEZE.sha256` was written. Two sequential runs of the frozen builder
stopped with an RPC error part way through and wrote no catalog (the endpoint rate-limited
the roughly 940 balance batches). The change reads balances with one `eth_call` per 500
addresses, running a 27-byte balance reader through state override (checked against
`eth_getBalance` on 200 addresses at the same block: identical), reads code only for
holders, pauses between requests, allows 8 retries instead of 6, and reports the RPC error. The selection rule (index, compiler filter, exclusions, one block, non-zero balance
and non-empty code) is unchanged. No engine had been run on any mainnet contract when this
change was made. The engine sources are unchanged and still match `archive/engine_v6/`.
Builder after the change: 11312f107a8b6db3ed9a0b9a26b875186edd8d6ff8bd84bcb665b4c85a01bb52  src/eval/build_mainnet_catalog.py

## Second change (2026-11-01, baseline runner only)

`src/eval/run_evmlisa.py` was changed after the freeze, after its first pass over the four
baseline corpora and before any protocol-7 engine run. (1) Files without runtime code (13
labeled files whose source does not compile) are recorded as `no_bytecode`, not `error`.
(2) Runtime code with unlinked library placeholders (LedgerChannel in spank_chain_payment)
is skipped and noted, as EVM-Guard skips it. (3) A rerun mode runs only the files that ended
in error or timeout, with a 600 s budget and a jar built from the same EVMLiSA commit with the
CFG dump turned off (it crashes on some graphs after the analysis ends; identical findings on
20 of 20 SmartBugs files). The 60 s results of the first pass are kept unchanged; the rerun is
reported separately as a sensitivity run. EVM-Guard sources are unchanged.
Runner after the change: 15a3ec45a435c840b16a09ac62787bc2022ef4f5a34a916fc3bda8954623d3bc  src/eval/run_evmlisa.py
