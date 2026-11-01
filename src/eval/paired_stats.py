"""Paired comparison of EVM-Guard v5 with the baselines on the same files.

For each corpus and category, the script joins the file-level flags of EVM-Guard and of
a baseline and reports: exact 95% Clopper-Pearson intervals for precision, and an exact
McNemar test (two-sided binomial test on the discordant files) separately on the
negatives (false positives) and on the positives (true positives). Interval overlap is a
weaker criterion than a paired test on the same files, so the paper reports both.

Output: results/statistics/paired_tests.json
"""
import csv
import glob
import json
import os
import sys

from scipy.stats import binomtest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULTS = os.path.join(REPO, "results")
sys.path.insert(0, os.path.join(REPO, "src", "eval"))

from score_external import clopper_pearson  # noqa: E402

V5 = "reproduction_reference"
CORPORA = {
    "smartbugs": {"evm_guard": f"{V5}/smartbugs", "baselines": "external",
                  "categories": ["reentrancy", "denial_of_service", "access_control", "arithmetic"]},
    "solidifi": {"evm_guard": f"{V5}/solidifi", "baselines": "heldout",
                 "categories": ["reentrancy", "arithmetic"]},
    "labeled": {"evm_guard": f"{V5}/labeled", "baselines": "heldout2",
                "categories": ["reentrancy", "access_control", "arithmetic"]},
    "synthetic_final": {"evm_guard": f"{V5}/synthetic_final", "baselines": "final_v5",
                        "categories": ["reentrancy", "denial_of_service"]},
}
BASELINES = ("slither", "mythril")


def read_flags(pattern: str) -> dict:
    """Map contract_id to (labels, flagged categories). Later shards overwrite earlier ones."""
    flags = {}
    for path in sorted(glob.glob(os.path.join(RESULTS, pattern))):
        with open(path, newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                labels = set(filter(None, row["labels"].split(";")))
                flagged = set(filter(None, row["flagged_categories"].split(";")))
                flags[row["contract_id"]] = (labels, flagged)
    return flags


def mcnemar(only_left: int, only_right: int) -> dict:
    discordant = only_left + only_right
    p_value = 1.0 if discordant == 0 else binomtest(only_left, discordant, 0.5).pvalue
    return {"only_evm_guard": only_left, "only_baseline": only_right, "p_value": float(f"{p_value:.3g}")}


def precision(tp: int, fp: int) -> dict:
    total = tp + fp
    return {"tp": tp, "fp": fp, "precision": round(tp / total, 4) if total else None,
            "precision_ci95": clopper_pearson(tp, total)}


def compare(guard: dict, baseline: dict, category: str) -> dict:
    """Paired counts over the files that both tools have a row for."""
    shared = sorted(set(guard) & set(baseline))
    counts = {"neg_g": 0, "neg_b": 0, "pos_g": 0, "pos_b": 0}
    tp_g = fp_g = tp_b = fp_b = 0
    for contract in shared:
        labels, guard_flags = guard[contract]
        _, base_flags = baseline[contract]
        positive = category in labels
        flagged_g, flagged_b = category in guard_flags, category in base_flags
        tp_g += positive and flagged_g
        fp_g += (not positive) and flagged_g
        tp_b += positive and flagged_b
        fp_b += (not positive) and flagged_b
        side = "pos" if positive else "neg"
        counts[f"{side}_g"] += flagged_g and not flagged_b
        counts[f"{side}_b"] += flagged_b and not flagged_g
    negatives = sum(1 for c in shared if category not in guard[c][0])
    return {
        "files": len(shared), "negatives": negatives, "positives": len(shared) - negatives,
        "evm_guard": precision(tp_g, fp_g), "baseline": precision(tp_b, fp_b),
        "mcnemar_false_positives": mcnemar(counts["neg_g"], counts["neg_b"]),
        "mcnemar_true_positives": mcnemar(counts["pos_g"], counts["pos_b"]),
    }


def main() -> None:
    report = {}
    for corpus, spec in CORPORA.items():
        guard = read_flags(f"{spec['evm_guard']}/evm_guard_files.csv")
        report[corpus] = {}
        for tool in BASELINES:
            baseline = read_flags(f"{spec['baselines']}/{tool}_files_*.csv")
            report[corpus][tool] = {cat: compare(guard, baseline, cat) for cat in spec["categories"]}
    out_dir = os.path.join(RESULTS, "statistics")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "paired_tests.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    for corpus, tools in report.items():
        for tool, cats in tools.items():
            for cat, r in cats.items():
                fp_test, tp_test = r["mcnemar_false_positives"], r["mcnemar_true_positives"]
                print(f"{corpus:16s} {tool:8s} {cat:18s} n={r['files']:3d} "
                      f"P_g={r['evm_guard']['precision']} {r['evm_guard']['precision_ci95']} "
                      f"P_b={r['baseline']['precision']} {r['baseline']['precision_ci95']} "
                      f"FP g/b-only={fp_test['only_evm_guard']}/{fp_test['only_baseline']} p={fp_test['p_value']:.2e} "
                      f"TP g/b-only={tp_test['only_evm_guard']}/{tp_test['only_baseline']} p={tp_test['p_value']:.2e}")


if __name__ == "__main__":
    main()
