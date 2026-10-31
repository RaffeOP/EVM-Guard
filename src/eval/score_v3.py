"""Score an EVM-Guard run directory with the shared scoring functions.

Usage: score_v3.py <run-dir> <category> [<category> ...]

Reads <run-dir>/evm_guard_files.csv and writes <run-dir>/scores.json with TP, FP, FN, TN,
recall, precision and FPR, with exact 95% Clopper-Pearson intervals, for each category
given. Replay-confirmed results are scored the same way.
"""
import csv
import json
import os
import sys

from score_external import score_category

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> None:
    run_dir = sys.argv[1]
    categories = sys.argv[2:]
    rows = list(csv.DictReader(open(os.path.join(run_dir, "evm_guard_files.csv"), encoding="utf-8")))
    scores = {
        "files": len(rows),
        "flagged_any": {c: score_category(rows, c, "flagged_categories") for c in categories},
        "replay_confirmed": {c: score_category(rows, c, "confirmed_categories") for c in categories},
    }
    with open(os.path.join(run_dir, "scores.json"), "w", encoding="utf-8") as handle:
        json.dump(scores, handle, indent=2)
    for name in ("flagged_any", "replay_confirmed"):
        for category in categories:
            block = scores[name][category]
            print(name, category, {k: block[k] for k in ("tp", "fp", "fn", "tn", "recall", "precision", "fpr")})


if __name__ == "__main__":
    main()
