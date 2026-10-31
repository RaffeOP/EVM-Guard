"""Time the EVM-Guard analysis stage on SmartBugs-curated, excluding replay.

Per file, the time is the sum over its runtime contracts of the engine's own
execution_time_ms, which is the protocol's definition (wall time of analyze_bytecode,
summed per file). The whole catalog is analysed `repeats` times in one process. Each
repeat gives a median, a mean and a standard deviation over files, and the reported
figures are the averages over repeats. Run it on an otherwise idle machine.

Writes results/timing/evm_guard_analysis_timing.json.
"""
import argparse
import json
import os
import statistics
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.join(REPO, "src", "eval"))

from repo_paths import resolve  # noqa: E402
from symbolic_engine import SymbolicEVMInterpreter  # noqa: E402

CATALOG = os.path.join(REPO, "benchmarks/benchmark_catalog_external.json")
OUT = os.path.join(REPO, "results/timing/evm_guard_analysis_timing.json")


def file_times_ms(catalog: list) -> list:
    engine = SymbolicEVMInterpreter()
    times = []
    for entry in catalog:
        total = 0.0
        for contract_name, runtime_path in entry["runtime_bytecode_paths"].items():
            with open(resolve(runtime_path), encoding="utf-8") as handle:
                runtime_hex = handle.read().strip()
            total += engine.analyze_bytecode(contract_name, runtime_hex, target_swc=None)["execution_time_ms"]
        times.append(total)
    return times


def summarise(times: list) -> dict:
    return {"median_ms": statistics.median(times), "mean_ms": statistics.mean(times),
            "sd_ms": statistics.stdev(times)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    with open(CATALOG, encoding="utf-8") as handle:
        catalog = json.load(handle)
    per_repeat = [summarise(file_times_ms(catalog)) for _ in range(args.repeats)]
    result = {
        "files": len(catalog),
        "repeats": args.repeats,
        "per_repeat": per_repeat,
        "average": {key: statistics.mean(r[key] for r in per_repeat) for key in ("median_ms", "mean_ms", "sd_ms")},
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps(result["average"], indent=2))


if __name__ == "__main__":
    main()
