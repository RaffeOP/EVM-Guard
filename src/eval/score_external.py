"""Score evm_guard_files.csv per SmartBugs category, as fixed in the external protocol."""
import csv
import json
import os
import statistics

from scipy.stats import beta

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILES_CSV = os.path.join(REPO, "results/external/evm_guard_files.csv")
OUT = os.path.join(REPO, "results/external/evm_guard_scores.json")
SCORED = ["reentrancy", "arithmetic", "denial_of_service", "access_control"]


def clopper_pearson(k: int, n: int):
    if n == 0:
        return None
    lower = 0.0 if k == 0 else float(beta.ppf(0.025, k, n - k + 1))
    upper = 1.0 if k == n else float(beta.ppf(0.975, k + 1, n - k))
    return [round(lower, 4), round(upper, 4)]


def ratio(k: int, n: int):
    return round(k / n, 4) if n else None


def score_category(rows: list, category: str, column: str) -> dict:
    tp = fp = fn = tn = 0
    for row in rows:
        labelled = category in row["labels"].split(";")
        flagged = category in row[column].split(";")
        tp += labelled and flagged
        fp += (not labelled) and flagged
        fn += labelled and not flagged
        tn += (not labelled) and not flagged
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "recall": ratio(tp, tp + fn), "recall_ci95": clopper_pearson(tp, tp + fn),
            "precision": ratio(tp, tp + fp), "precision_ci95": clopper_pearson(tp, tp + fp),
            "fpr": ratio(fp, fp + tn), "fpr_ci95": clopper_pearson(fp, fp + tn)}


def load_rows(paths: list) -> list:
    rows = []
    for path in paths:
        with open(path, newline="", encoding="utf-8") as handle:
            rows.extend(csv.DictReader(handle))
    return rows


def score_baseline(paths: list, out: str) -> dict:
    """Score a baseline; errors and timeouts count as unflagged and are reported."""
    rows = load_rows(paths)
    latencies = [float(r["latency_ms"]) for r in rows]
    result = {
        "files": len(rows),
        "status": {s: sum(r["status"] == s for r in rows) for s in sorted({r["status"] for r in rows})},
        "flagged_any": {c: score_category(rows, c, "flagged_categories") for c in SCORED},
        "latency_ms_per_file": {"mean": round(statistics.mean(latencies), 3),
                                "sd": round(statistics.stdev(latencies), 3),
                                "median": round(statistics.median(latencies), 3)},
    }
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
    return result


def main() -> None:
    import glob
    import sys
    if len(sys.argv) > 1:
        tool = sys.argv[1]
        paths = sorted(glob.glob(os.path.join(REPO, f"results/external/{tool}_files_*.csv")))
        print(json.dumps(score_baseline(paths, os.path.join(REPO, f"results/external/{tool}_scores.json")), indent=2))
        return
    with open(FILES_CSV, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    latencies = sorted(float(r["latency_ms"]) for r in rows)
    quartiles = statistics.quantiles(latencies, n=4, method="inclusive")
    result = {
        "files": len(rows),
        "flagged_any": {c: score_category(rows, c, "flagged_categories") for c in SCORED},
        "replay_confirmed": {c: score_category(rows, c, "confirmed_categories") for c in SCORED},
        "latency_ms_per_file": {"mean": round(statistics.mean(latencies), 3),
                                "sd": round(statistics.stdev(latencies), 3),
                                "median": round(statistics.median(latencies), 3),
                                "iqr": [round(quartiles[0], 3), round(quartiles[2], 3)],
                                "max": round(latencies[-1], 3)},
    }
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
