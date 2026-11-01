"""Score the round-3 reentrancy baselines against EVM-Guard on the same files.

Tools (results/baselines_round3/):
  slither_mapped   Slither 0.11.6, every reentrancy-* detector counts (the mapping used before)
  slither_strict   Slither 0.11.6, only reentrancy-eth and reentrancy-no-eth count; the
                   -benign, -events and -unlimited-gas detectors report patterns that Slither
                   itself does not rate as exploitable
  evmlisa_60s      EVMLiSA (commit 44ae6dd), 60 s per runtime contract
  evmlisa_600s     the same, with files that ended in error or timeout at 60 s rerun at 600 s
                   where a rerun row exists (sensitivity only)
  ethor            eThor (smartbugs/ethor:2023), 120 s per runtime contract
  sailfish_static  static stage of Sailfish only (its Racket verifier aborts on the evaluation
                   machine); an upper bound on full Sailfish's recall and flag count
A file that a tool did not finish (status other than ok) counts as not flagged, as for EVM-Guard;
the number of such files is reported. For each tool: TP, FP, FN, TN with exact 95% intervals,
and an exact McNemar test against EVM-Guard v5 and, where it was run on the corpus, v6.

Output: results/baselines_round3/scores.json
"""
import csv
import glob
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROUND3 = os.path.join(REPO, "results", "baselines_round3")
sys.path.insert(0, os.path.join(REPO, "src", "eval"))

from paired_stats import mcnemar  # noqa: E402
from score_protocol7 import confusion  # noqa: E402

CATEGORY = "reentrancy"
STRICT_DETECTORS = {"reentrancy-eth", "reentrancy-no-eth"}
GUARD = {"smartbugs": {"v5": "results/reproduction_reference/smartbugs"},
         "solidifi": {"v5": "results/protocol7/v5/solidifi", "v6": "results/protocol7/v6/solidifi"},
         "labeled": {"v5": "results/protocol7/v5/labeled", "v6": "results/protocol7/v6/labeled"},
         "synthetic_final": {"v5": "results/reproduction_reference/synthetic_final"}}


def read_csv(pattern: str) -> list:
    rows = []
    for path in sorted(glob.glob(pattern)):
        with open(path, newline="", encoding="utf-8") as handle:
            rows += list(csv.DictReader(handle))
    return rows


def labels_of(row: dict) -> set:
    return set(filter(None, row["labels"].split(";")))


def as_flags(rows: list, is_flagged) -> dict:
    return {r["contract_id"]: (labels_of(r), {CATEGORY} if r.get("status", "ok") == "ok" and is_flagged(r) else set())
            for r in rows}


def slither(corpus: str, detectors) -> dict:
    rows = read_csv(os.path.join(ROUND3, "slither", corpus, "slither_files_*.csv"))
    def is_flagged(row):
        found = set(filter(None, row["raw_findings"].split(";")))
        return any(d.startswith("reentrancy") for d in found) if detectors is None else bool(found & detectors)
    return as_flags(rows, is_flagged), rows


def evmlisa(corpus: str, with_rerun: bool):
    rows = {r["contract_id"]: r for r in read_csv(os.path.join(ROUND3, "evmlisa", corpus, "evmlisa_files_*.csv"))}
    if with_rerun:
        rows.update({r["contract_id"]: r for r in read_csv(os.path.join(ROUND3, "evmlisa", corpus,
                                                                         "evmlisa_rerun_*.csv"))})
    rows = list(rows.values())
    return as_flags(rows, lambda r: CATEGORY in r["flagged_categories"].split(";")), rows


def tool_rows(tool: str, corpus: str):
    """Flags and rows of a runner that writes <tool>_files_*.csv with flagged_categories."""
    rows = read_csv(os.path.join(ROUND3, tool, corpus, f"{tool}_files_*.csv"))
    return as_flags(rows, lambda r: CATEGORY in r["flagged_categories"].split(";")), rows


def guard(path: str) -> dict:
    rows = read_csv(os.path.join(REPO, path, "evm_guard_files.csv"))
    return {r["contract_id"]: (labels_of(r), set(filter(None, r["flagged_categories"].split(";")))) for r in rows}


def versus(engine: dict, tool: dict) -> dict:
    """McNemar of EVM-Guard against the tool on the files both report."""
    shared = sorted(set(engine) & set(tool))
    only = {"neg_g": 0, "neg_t": 0, "pos_g": 0, "pos_t": 0}
    for contract in shared:
        side = "pos" if CATEGORY in engine[contract][0] else "neg"
        in_g, in_t = CATEGORY in engine[contract][1], CATEGORY in tool[contract][1]
        only[f"{side}_g"] += in_g and not in_t
        only[f"{side}_t"] += in_t and not in_g
    return {"files": len(shared), "false_positives": mcnemar(only["neg_g"], only["neg_t"]),
            "true_positives": mcnemar(only["pos_g"], only["pos_t"])}


def score_tool(flags: dict, rows: list, engines: dict) -> dict:
    statuses = {}
    for row in rows:
        statuses[row.get("status", "ok")] = statuses.get(row.get("status", "ok"), 0) + 1
    return {"files": len(rows), "status": statuses, **confusion(flags, CATEGORY),
            **{f"vs_{name}": versus(engine, flags) for name, engine in engines.items()}}


def main() -> None:
    report = {}
    for corpus, paths in GUARD.items():
        engines = {name: guard(path) for name, path in paths.items()}
        tools = {"slither_mapped": slither(corpus, None), "slither_strict": slither(corpus, STRICT_DETECTORS),
                 "evmlisa_60s": evmlisa(corpus, False), "evmlisa_600s": evmlisa(corpus, True)}
        for tool, key in (("ethor", "ethor"), ("sailfish", "sailfish_static")):
            if glob.glob(os.path.join(ROUND3, tool, corpus, f"{tool}_files_*.csv")):
                tools[key] = tool_rows(tool, corpus)
        report[corpus] = {"evm_guard": {name: confusion(engine, CATEGORY) for name, engine in engines.items()},
                          **{name: score_tool(flags, rows, engines) for name, (flags, rows) in tools.items()}}
    with open(os.path.join(ROUND3, "scores.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    for corpus, tools in report.items():
        for name, s in tools.items():
            if name == "evm_guard":
                for engine, c in s.items():
                    print(f"{corpus:15s} evm_guard_{engine:9s} TP{c['tp']:3d} FP{c['fp']:3d} FN{c['fn']:3d} "
                          f"P={c['precision']} {c['precision_ci95']} R={c['recall']}")
                continue
            vs = " ".join(f"{k}:FP{v['false_positives']['only_evm_guard']}/{v['false_positives']['only_baseline']}"
                          f"(p={v['false_positives']['p_value']:.2g})" for k, v in s.items() if k.startswith("vs_"))
            print(f"{corpus:15s} {name:19s} TP{s['tp']:3d} FP{s['fp']:3d} FN{s['fn']:3d} P={s['precision']} "
                  f"{s['precision_ci95']} R={s['recall']} {s['status']} {vs}")


if __name__ == "__main__":
    main()
