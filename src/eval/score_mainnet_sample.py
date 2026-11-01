"""Score the hand-labelled mainnet sample of protocol 7 after the labels were locked.

Joins the blind labels (results/protocol7/mainnet_labels_blind.csv, hash in the .sha256 file)
with the blind key, then reports for v5 and v6 the precision on the sampled contracts each
flagged, with exact 95% intervals, and an exact McNemar test of v5 against v6 on the sample.
Only `exploitable` counts as correct (docs/LABELLING_RUBRIC.md). Slither 0.11.6 on the
verified sources of the same contracts is scored the same way (mapped: any reentrancy-*
detector; strict: reentrancy-eth or reentrancy-no-eth). The sample is drawn from contracts
EVM-Guard flagged, so Slither's figures are conditional on that selection.
Output: results/protocol7/mainnet_sample_scores.json
"""
import csv
import glob
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUNS = os.path.join(REPO, "results", "protocol7")
sys.path.insert(0, os.path.join(REPO, "src", "eval"))

from paired_stats import mcnemar  # noqa: E402
from score_external import clopper_pearson  # noqa: E402

CORRECT = "exploitable"
STRICT_DETECTORS = {"reentrancy-eth", "reentrancy-no-eth"}


def slither_flags() -> dict:
    """Contracts Slither flags on the sample, under the mapped and the strict detector sets."""
    rows = []
    for path in glob.glob(os.path.join(RUNS, "slither_sample", "slither_files_*.csv")):
        with open(path, newline="", encoding="utf-8") as handle:
            rows += [r for r in csv.DictReader(handle) if r["status"] == "ok"]
    found = {r["contract_id"]: set(filter(None, r["raw_findings"].split(";"))) for r in rows}
    return {"slither_mapped": {c for c, d in found.items() if any(x.startswith("reentrancy") for x in d)},
            "slither_strict": {c for c, d in found.items() if d & STRICT_DETECTORS}}


def flagged(engine: str) -> set:
    found = set()
    for path in glob.glob(os.path.join(RUNS, engine, "mainnet_shard*", "evm_guard_contracts.csv")):
        with open(path, newline="", encoding="utf-8") as handle:
            found |= {r["contract_id"] for r in csv.DictReader(handle) if "SWC-107" in r["finding_swcs"].split(";")}
    return found


def main() -> None:
    with open(os.path.join(RUNS, "mainnet_labels_blind.csv"), newline="", encoding="utf-8") as handle:
        labels = {r["blind_id"]: r["label"] for r in csv.DictReader(handle)}
    with open(os.path.join(RUNS, "blind_key_DO_NOT_OPEN.csv"), newline="", encoding="utf-8") as handle:
        key = {r["blind_id"]: r["original_file"][:-4] for r in csv.DictReader(handle)}
    by_contract = {f"mainnet__{address}": labels[blind] for blind, address in key.items()}
    engines = {e: flagged(e) & set(by_contract) for e in ("v5", "v6")}
    engines.update(slither_flags())
    report = {"sample": len(by_contract), "labels": {}}
    for label in sorted(set(by_contract.values())):
        report["labels"][label] = sum(v == label for v in by_contract.values())
    for engine, contracts in engines.items():
        tp = sum(by_contract[c] == CORRECT for c in contracts)
        report[engine] = {"flagged_in_sample": len(contracts), "exploitable": tp,
                          "precision": round(tp / len(contracts), 4) if contracts else None,
                          "precision_ci95": clopper_pearson(tp, len(contracts))}
    only = {e: engines[e] - engines[o] for e, o in (("v5", "v6"), ("v6", "v5"))}
    for tool in ("slither_mapped", "slither_strict"):
        report[f"v5_vs_{tool}"] = {"false_positives": mcnemar(
            sum(by_contract[c] != CORRECT for c in engines["v5"] - engines[tool]),
            sum(by_contract[c] != CORRECT for c in engines[tool] - engines["v5"]))}
    count = lambda cs, want: sum((by_contract[c] == CORRECT) == want for c in cs)  # noqa: E731
    report["v5_vs_v6"] = {"false_positives": mcnemar(count(only["v5"], False), count(only["v6"], False)),
                          "true_positives": mcnemar(count(only["v5"], True), count(only["v6"], True))}
    # Aggregate only: the protocol forbids publishing the address of an exploitable contract.
    exploitable = [c for c, v in by_contract.items() if v == CORRECT]
    report["exploitable_flagged_by"] = {e: sum(c in engines[e] for c in exploitable) for e in engines}
    with open(os.path.join(RUNS, "mainnet_sample_scores.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
