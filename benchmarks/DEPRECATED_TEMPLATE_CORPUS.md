# Deprecated: generated template corpus (do not use as evidence)

The 226 contracts under `swc_registry/`, `not_so_smart_contracts/`, `defi_hack_labs/` and
`emergent_defi/`, and `benchmark_catalog_226.json`, were produced by
`src/generate_expanded_benchmarks.py`. After removing names, comments and compiler metadata
they are 12 distinct programs (one vulnerable and one safe template per class). Labels were
drawn with `random.random()`, and the catalog's LOC, cyclomatic complexity and instruction
counts are `random.randint` values, not measurements. The "Canonical Upstream Reference"
headers in those files do not correspond to any upstream file.

The paper's evaluation uses SmartBugs-curated instead:
`benchmarks/benchmark_catalog_external.json`, built by `src/eval/build_external_catalog.py`,
under `docs/EXTERNAL_EVAL_PROTOCOL.md`.
