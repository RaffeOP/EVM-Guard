"""Ablation of the reentrancy check on SmartBugs-curated, one component at a time.

Every configuration in engine_options.ABLATIONS runs the SWC-107 check on each runtime
contract in the catalog. A file is flagged for reentrancy when any of its runtime
contracts yields a finding, which is the unit and rule used by run_external_eval.py.
Only detection is run here: replay does not change the static flags.

Writes results/ablation/<configuration>/evm_guard_files.csv for each configuration and
results/ablation/ablation_summary.json with the file-level scores.
"""
import csv
import json
import os
import sys
from dataclasses import asdict

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.join(REPO, "src", "eval"))

from engine_options import ABLATIONS  # noqa: E402
from repo_paths import resolve  # noqa: E402
from score_external import score_category  # noqa: E402
from symbolic_engine import SymbolicEVMInterpreter  # noqa: E402

CATALOG = os.path.join(REPO, "benchmarks/benchmark_catalog_external.json")
OUT_ROOT = os.path.join(REPO, "results/ablation")
CATEGORY = "reentrancy"
TARGET_SWC = "SWC-107"
FILE_FIELDS = ["contract_id", "labels", "flagged_categories"]


def file_is_flagged(engine: SymbolicEVMInterpreter, entry: dict) -> bool:
    for contract_name, runtime_path in entry["runtime_bytecode_paths"].items():
        with open(resolve(runtime_path), encoding="utf-8") as handle:
            runtime_hex = handle.read().strip()
        report = engine.analyze_bytecode(contract_name, runtime_hex, target_swc=TARGET_SWC)
        if report["findings"]:
            return True
    return False


def run_configuration(options, catalog: list) -> list:
    engine = SymbolicEVMInterpreter(options=options)
    rows = []
    for entry in catalog:
        flagged = file_is_flagged(engine, entry)
        rows.append({"contract_id": entry["contract_id"], "labels": ";".join(entry["labels"]),
                     "flagged_categories": CATEGORY if flagged else ""})
    return rows


def write_rows(path: str, rows: list) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FILE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    with open(CATALOG, encoding="utf-8") as handle:
        catalog = json.load(handle)
    summary = {}
    for name, options in ABLATIONS.items():
        rows = run_configuration(options, catalog)
        out_dir = os.path.join(OUT_ROOT, name)
        os.makedirs(out_dir, exist_ok=True)
        write_rows(os.path.join(out_dir, "evm_guard_files.csv"), rows)
        score = score_category(rows, CATEGORY, "flagged_categories")
        summary[name] = {"options": asdict(options), "reentrancy": score}
        print(f"{name}: tp={score['tp']} fp={score['fp']} fn={score['fn']} tn={score['tn']}", flush=True)
    with open(os.path.join(OUT_ROOT, "ablation_summary.json"), "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)


if __name__ == "__main__":
    main()
