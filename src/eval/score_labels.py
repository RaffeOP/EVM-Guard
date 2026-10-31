"""Score tool output against locked independent labels.

Inputs: a labels CSV (blind_id, vulnerable_yes_no), a key CSV (blind_id,
original_file), and a tool-output CSV (original_file, flagged yes/no).
Reports the confusion matrix with exact Clopper-Pearson 95% intervals.
"""
import argparse
import csv
import json
from math import sqrt

from scipy.stats import beta


def clopper_pearson(successes: int, trials: int, alpha: float = 0.05):
    if trials == 0:
        return (0.0, 1.0)
    lower = 0.0 if successes == 0 else beta.ppf(alpha / 2, successes, trials - successes + 1)
    upper = 1.0 if successes == trials else beta.ppf(1 - alpha / 2, successes + 1, trials - successes)
    return (float(lower), float(upper))


def load_labels(labels_path: str, key_path: str) -> dict:
    with open(key_path, newline="", encoding="utf-8") as handle:
        key = {row["blind_id"]: row["original_file"] for row in csv.DictReader(handle)}
    labels = {}
    with open(labels_path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            value = row["vulnerable_yes_no"].strip().lower()
            if value not in {"yes", "no"}:
                raise ValueError(f"unlabelled or invalid entry for {row['blind_id']}")
            labels[key[row["blind_id"]]] = value == "yes"
    return labels


def load_tool(tool_path: str) -> dict:
    with open(tool_path, newline="", encoding="utf-8") as handle:
        return {row["original_file"]: row["flagged"].strip().lower() == "yes" for row in csv.DictReader(handle)}


def score(labels: dict, flags: dict) -> dict:
    missing = set(labels) - set(flags)
    if missing:
        raise ValueError(f"tool output missing {len(missing)} contracts")
    tp = sum(1 for k, v in labels.items() if v and flags[k])
    fn = sum(1 for k, v in labels.items() if v and not flags[k])
    fp = sum(1 for k, v in labels.items() if not v and flags[k])
    tn = sum(1 for k, v in labels.items() if not v and not flags[k])
    positives, negatives = tp + fn, fp + tn
    recall = tp / positives if positives else 0.0
    fpr = fp / negatives if negatives else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "recall": recall, "recall_ci95": clopper_pearson(tp, positives),
        "fpr": fpr, "fpr_ci95": clopper_pearson(fp, negatives),
        "precision": precision, "precision_ci95": clopper_pearson(tp, tp + fp),
        "n": len(labels), "sqrt_n": sqrt(len(labels)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--tool", required=True)
    args = parser.parse_args()
    result = score(load_labels(args.labels, args.key), load_tool(args.tool))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
