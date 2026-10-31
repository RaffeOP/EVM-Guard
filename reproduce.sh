#!/usr/bin/env bash
# Rebuild every corpus and rerun EVM-Guard (engine v5) on it.
# Outputs go to results/reproduction/<corpus>/; compare them with docs/REPRODUCIBILITY.md.
set -euo pipefail
cd "$(dirname "$0")"

SMARTBUGS_COMMIT=230e649123477eff332742a59a1c7cc6dc286cab
LABELED_COMMIT=8b903aae40648ad0ead87662857c6685542710d5
SOLC_VERSIONS="0.4.0 0.4.2 0.4.9 0.4.10 0.4.11 0.4.13 0.4.15 0.4.16 0.4.18 0.4.19 0.4.21 0.4.22 0.4.23 0.4.24 0.4.25 0.5.0 0.5.8 0.5.12 0.8.20"

python3 -m venv .venv
.venv/bin/pip install -q -r requirements-eval.txt
for version in $SOLC_VERSIONS; do .venv/bin/solc-select install "$version" >/dev/null; done

if [ ! -d external/smartbugs-curated ]; then
  git clone -q https://github.com/smartbugs/smartbugs-curated external/smartbugs-curated
fi
git -C external/smartbugs-curated checkout -q "$SMARTBUGS_COMMIT"

if [ ! -d external/smartcontract-benchmark ]; then
  git clone -q https://github.com/bit-smartcontract-analysis/smartcontract-benchmark external/smartcontract-benchmark
fi
git -C external/smartcontract-benchmark checkout -q "$LABELED_COMMIT"
# The labeled benchmark has no licence, so its sources are copied locally (git-ignored) and recompiled.
.venv/bin/python src/eval/build_heldout2_catalog.py external/smartcontract-benchmark

.venv/bin/python src/eval/compile_catalog.py \
  benchmarks/benchmark_catalog_external.json \
  benchmarks/heldout_catalog.json \
  benchmarks/injected05_catalog.json \
  benchmarks/injected05c_catalog.json

run() { mkdir -p "results/reproduction/$2"; .venv/bin/python src/eval/run_external_eval.py "benchmarks/$1" "results/reproduction/$2"; }
run benchmark_catalog_external.json smartbugs
run heldout_catalog.json solidifi
run heldout2_catalog.json labeled
run injected05_catalog.json synthetic_seed1
run injected05c_catalog.json synthetic_final
