"""Score held-out catalog 2 under docs/HELDOUT2_EVAL_PROTOCOL.md.

Reuses the SmartBugs scoring functions, so the definitions are identical. Scored
categories are reentrancy, arithmetic and access control. Denial of service has no
positives in this corpus and is not scored.

Reads results/heldout2/{evm_guard_files.csv, slither_files_*.csv, mythril_files_*.csv}
and writes results/heldout2/{tool}_heldout2_scores.json.
"""
import csv
import glob
import json
import os
import statistics

from score_external import load_rows, score_category

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(REPO, "results/heldout2")
SCORED = ["reentrancy", "arithmetic", "access_control"]


def score_tool(rows: list, column: str, latency_key: str) -> dict:
    latencies = [float(r[latency_key]) for r in rows]
    return {
        "files": len(rows),
        "flagged_any": {c: score_category(rows, c, column) for c in SCORED},
        "latency_ms_per_file": {"mean": round(statistics.mean(latencies), 3),
                                "median": round(statistics.median(latencies), 3)},
    }


def main() -> None:
    evm_path = os.path.join(OUT_DIR, "evm_guard_files.csv")
    evm_rows = list(csv.DictReader(open(evm_path, encoding="utf-8")))
    evm = score_tool(evm_rows, "flagged_categories", "latency_ms")
    evm["replay_confirmed"] = {c: score_category(evm_rows, c, "confirmed_categories") for c in SCORED}
    results = {"evm_guard": evm}
    for tool in ("slither", "mythril"):
        paths = sorted(glob.glob(os.path.join(OUT_DIR, f"{tool}_files_*.csv")))
        rows = load_rows(paths)
        status = {s: sum(r["status"] == s for r in rows) for s in sorted({r["status"] for r in rows})}
        block = score_tool(rows, "flagged_categories", "latency_ms")
        block["status"] = status
        results[tool] = block
    for name, block in results.items():
        with open(os.path.join(OUT_DIR, f"{name}_heldout2_scores.json"), "w", encoding="utf-8") as handle:
            json.dump(block, handle, indent=2)
    summary = {k: {c: v["flagged_any"][c] for c in SCORED} for k, v in results.items()}
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
