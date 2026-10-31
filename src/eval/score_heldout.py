"""Score the held-out SolidiFI corpus under docs/HELDOUT_EVAL_PROTOCOL.md.

Reuses the SmartBugs scoring functions, so the definitions are identical. Only the
categories this corpus can test are scored: reentrancy and arithmetic. Denial of
service has no folder in the corpus and is not scored.

Reads results/heldout/{evm_guard_files.csv, slither_files_*.csv, mythril_files_*.csv}
and writes results/heldout/{evm_guard,slither,mythril}_heldout_scores.json.
"""
import csv
import glob
import json
import os
import statistics
import sys

from score_external import load_rows, score_category

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(REPO, "results/heldout")
SCORED = ["reentrancy", "arithmetic"]


def score_tool(rows: list, column: str, latency_key: str) -> dict:
    latencies = [float(r[latency_key]) for r in rows]
    return {
        "files": len(rows),
        "flagged_any": {c: score_category(rows, c, column) for c in SCORED},
        "latency_ms_per_file": {"mean": round(statistics.mean(latencies), 3),
                                "median": round(statistics.median(latencies), 3)},
    }


def main() -> None:
    """Score one held-out directory. Baselines are scored only where their files exist, so the
    post hoc EVM-Guard run can be scored in its own directory without overwriting the frozen run."""
    out_dir = sys.argv[1] if len(sys.argv) > 1 else OUT_DIR
    evm_rows = list(csv.DictReader(open(os.path.join(out_dir, "evm_guard_files.csv"), encoding="utf-8")))
    evm = score_tool(evm_rows, "flagged_categories", "latency_ms")
    evm["replay_confirmed"] = {c: score_category(evm_rows, c, "confirmed_categories") for c in SCORED}
    results = {"evm_guard": evm}
    for tool in ("slither", "mythril"):
        paths = sorted(glob.glob(os.path.join(out_dir, f"{tool}_files_*.csv")))
        if not paths:
            continue
        rows = load_rows(paths)
        status = {s: sum(r["status"] == s for r in rows) for s in sorted({r["status"] for r in rows})}
        block = score_tool(rows, "flagged_categories", "latency_ms")
        block["status"] = status
        results[tool] = block
    for name, block in results.items():
        with open(os.path.join(out_dir, f"{name}_heldout_scores.json"), "w", encoding="utf-8") as handle:
            json.dump(block, handle, indent=2)
    print(json.dumps({k: {c: {x: v["flagged_any"][c][x] for x in ("tp", "fp", "fn", "tn", "recall", "precision", "fpr")}
                          for c in SCORED} for k, v in results.items()}, indent=2))


if __name__ == "__main__":
    main()
