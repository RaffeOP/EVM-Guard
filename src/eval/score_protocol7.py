"""Score the protocol 7 runs of the frozen engines v5 and v6 (docs/ENGINE_V6_EVAL_PROTOCOL.md).

Labelled corpora: file-level TP, FP, FN, TN, recall, precision and FPR with exact 95%
Clopper-Pearson intervals per engine and category, and an exact McNemar test of v5 against v6
on the same files, for false positives and for true positives.
Mainnet corpus: contracts analysed, errors, contracts flagged for reentrancy and the ether they
hold, per-contract analysis time, v6 reentrancy kinds and feasibility verdicts, and replay
confirmations in both tiers. Mainnet results are read from the shard directories and merged.

Output: results/protocol7/scores.json
"""
import csv
import glob
import json
import os
import statistics
import sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUNS = os.path.join(REPO, "results", "protocol7")
sys.path.insert(0, os.path.join(REPO, "src", "eval"))

from paired_stats import mcnemar  # noqa: E402
from score_external import clopper_pearson  # noqa: E402

ENGINES = ("v5", "v6")
LABELLED = {"solidifi": ["reentrancy", "arithmetic"],
            "labeled": ["reentrancy", "access_control", "arithmetic"],
            "injected05d": ["reentrancy", "denial_of_service"],
            "injected8c": ["reentrancy", "denial_of_service"]}
REENTRANCY_SWC = "SWC-107"
WEI_PER_ETHER = 10 ** 18
PERCENTILE_95 = 0.95


def read_rows(engine: str, corpus: str, table: str) -> list:
    rows = []
    for path in sorted(glob.glob(os.path.join(RUNS, engine, f"{corpus}*", f"evm_guard_{table}.csv"))):
        with open(path, newline="", encoding="utf-8") as handle:
            rows += list(csv.DictReader(handle))
    return rows


def file_flags(engine: str, corpus: str) -> dict:
    return {r["contract_id"]: (set(filter(None, r["labels"].split(";"))),
                               set(filter(None, r["flagged_categories"].split(";"))))
            for r in read_rows(engine, corpus, "files")}


def confusion(flags: dict, category: str) -> dict:
    tp = sum(category in labels and category in flagged for labels, flagged in flags.values())
    fp = sum(category not in labels and category in flagged for labels, flagged in flags.values())
    fn = sum(category in labels and category not in flagged for labels, flagged in flags.values())
    tn = len(flags) - tp - fp - fn
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "recall": round(tp / (tp + fn), 4) if tp + fn else None, "recall_ci95": clopper_pearson(tp, tp + fn),
            "precision": round(tp / (tp + fp), 4) if tp + fp else None,
            "precision_ci95": clopper_pearson(tp, tp + fp),
            "fpr": round(fp / (fp + tn), 4) if fp + tn else None, "fpr_ci95": clopper_pearson(fp, fp + tn)}


def paired(v5: dict, v6: dict, category: str) -> dict:
    """McNemar of v5 against v6 on the files both engines report."""
    shared = sorted(set(v5) & set(v6))
    only = Counter()
    for contract in shared:
        side = "pos" if category in v5[contract][0] else "neg"
        in_v5, in_v6 = category in v5[contract][1], category in v6[contract][1]
        only[(side, "v5")] += in_v5 and not in_v6
        only[(side, "v6")] += in_v6 and not in_v5
    fp_test, tp_test = mcnemar(only[("neg", "v5")], only[("neg", "v6")]), mcnemar(only[("pos", "v5")],
                                                                                 only[("pos", "v6")])
    rename = {"only_evm_guard": "only_v5", "only_baseline": "only_v6"}
    return {"files": len(shared),
            "mcnemar_false_positives": {rename.get(k, k): v for k, v in fp_test.items()},
            "mcnemar_true_positives": {rename.get(k, k): v for k, v in tp_test.items()}}


def score_labelled() -> dict:
    report = {}
    for corpus, categories in LABELLED.items():
        flags = {engine: file_flags(engine, corpus) for engine in ENGINES}
        report[corpus] = {cat: {**{engine: confusion(flags[engine], cat) for engine in ENGINES},
                                "v5_vs_v6": paired(flags["v5"], flags["v6"], cat)} for cat in categories}
    return report


def time_summary(values: list) -> dict:
    ordered = sorted(values)
    return {"median_ms": round(statistics.median(ordered), 1), "mean_ms": round(statistics.fmean(ordered), 1),
            "p95_ms": round(ordered[int(PERCENTILE_95 * (len(ordered) - 1))], 1), "max_ms": round(ordered[-1], 1)}


def wall_seconds(engine: str) -> float:
    with open(os.path.join(RUNS, "wall_times.txt"), encoding="utf-8") as handle:
        return sum(int(line.split("wall_s=")[1]) for line in handle if line.startswith(f"{engine} ")
                   and "/mainnet_shard" in line)


def score_mainnet(balances: dict) -> dict:
    report = {}
    for engine in ENGINES:
        rows = read_rows(engine, "mainnet_shard", "contracts")
        flagged = [r for r in rows if REENTRANCY_SWC in r["finding_swcs"].split(";")]
        flagged_wei = sum(balances[r["contract_id"]] for r in flagged)
        report[engine] = {
            "contracts": len(rows), "errors": sum(r["status"] != "ok" for r in rows),
            "flagged_reentrancy": len(flagged), "flagged_ether": round(flagged_wei / WEI_PER_ETHER, 2),
            "flagged_holding_1_ether": sum(balances[r["contract_id"]] >= WEI_PER_ETHER for r in flagged),
            "analysis_time": time_summary([float(r["latency_ms"]) for r in rows]),
            "wall_seconds_total_cpu_processes": wall_seconds(engine),
            "replay_confirmed_reentrancy": sum(REENTRANCY_SWC in r["confirmed_swcs"].split(";") for r in rows),
            "witness_confirmed_reentrancy": sum(REENTRANCY_SWC in r["witness_confirmed_swcs"].split(";")
                                                for r in rows),
            "reentrancy_kinds": dict(Counter(kind for r in flagged
                                             for kind in filter(None, r["reentrancy_kinds"].split(";")))),
            "unresolved_jumps_contracts": sum(int(r["unresolved_jumps"] or 0) > 0 for r in rows)}
    flagged_by = {e: {r["contract_id"] for r in read_rows(e, "mainnet_shard", "contracts")
                      if REENTRANCY_SWC in r["finding_swcs"].split(";")} for e in ENGINES}
    report["overlap"] = {"both": len(flagged_by["v5"] & flagged_by["v6"]),
                         "only_v5": len(flagged_by["v5"] - flagged_by["v6"]),
                         "only_v6": len(flagged_by["v6"] - flagged_by["v5"]),
                         "union": len(flagged_by["v5"] | flagged_by["v6"])}
    return report


def main() -> None:
    with open(os.path.join(REPO, "benchmarks", "mainnet_catalog.json"), encoding="utf-8") as handle:
        catalog = json.load(handle)
    balances = {e["contract_id"]: int(e["balance_wei"]) for e in catalog}
    report = {"labelled": score_labelled(), "mainnet": score_mainnet(balances),
              "mainnet_corpus": {"contracts": len(catalog), "block": catalog[0]["block"],
                                 "ether": round(sum(balances.values()) / WEI_PER_ETHER, 2)}}
    with open(os.path.join(RUNS, "scores.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
