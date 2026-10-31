"""Merge raw baseline CSVs into one per-tool summary, reporting timeouts separately."""
import csv
import json
import statistics
from collections import defaultdict

RAW_FILES = ["results/baselines/raw/slither.csv", "results/baselines/raw/mythril_complete.csv"]
OUT = "results/baselines/summary.json"


def load_rows() -> list:
    rows = []
    for path in RAW_FILES:
        with open(path, newline="", encoding="utf-8") as handle:
            rows.extend(csv.DictReader(handle))
    return rows


def summarise(rows: list) -> dict:
    by_tool = defaultdict(list)
    for row in rows:
        by_tool[row["tool"]].append(row)
    summary = {}
    for tool, items in by_tool.items():
        ok = [r for r in items if r["status"] == "ok"]
        times = [float(r["ms"]) for r in items]
        summary[tool] = {
            "rows": len(items),
            "ok": len(ok),
            "timeouts": sum(1 for r in items if r["status"] == "timeout"),
            "errors": sum(1 for r in items if r["status"] == "error"),
            "median_ms_all_rows": statistics.median(times),
        }
    return summary


def main() -> None:
    rows = load_rows()
    summary = summarise(rows)
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
