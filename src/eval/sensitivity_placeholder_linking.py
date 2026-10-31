"""Sensitivity analysis: link unresolved library placeholders, then re-run SmartBugs-curated.

The main run records a runtime contract whose code still contains solc library placeholders
as an error, which counts as unflagged. This script replaces each 40-character placeholder with
zero digits, analyses every runtime contract with the functions the main run uses, and re-scores
the four scored categories. Every other file must reproduce its main-run flags; any other change
is reported in files_changed. The main results are not changed by this script.

Writes results/sensitivity/placeholder_linking.json.
"""
import csv
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.join(REPO, "src", "eval"))

from exploit_synthesizer import ExploitSynthesizer  # noqa: E402
from repo_paths import resolve  # noqa: E402
from run_external_eval import SWC_TO_CATEGORY, analyze_contract, is_hex  # noqa: E402
from score_external import score_category  # noqa: E402
from symbolic_engine import SymbolicEVMInterpreter  # noqa: E402

CATALOG = os.path.join(REPO, "benchmarks/benchmark_catalog_external.json")
MAIN_FILES = os.path.join(REPO, "results/external/evm_guard_files.csv")
OUT = os.path.join(REPO, "results/sensitivity/placeholder_linking.json")
PLACEHOLDER = re.compile(r"__.{36}__")
ZERO_ADDRESS_HEX = "0" * 40
SCORED = ["reentrancy", "denial_of_service", "access_control", "arithmetic"]


def linked_hex(runtime_text):
    """Replace library placeholders with a zero address. Code that already decodes is unchanged."""
    if is_hex(runtime_text):
        return runtime_text
    return PLACEHOLDER.sub(ZERO_ADDRESS_HEX, runtime_text)


def contract_categories(engine, synthesizer, contract_name, runtime_text):
    """Static categories of one runtime contract, derived as the main run derives them."""
    result = analyze_contract(engine, synthesizer, contract_name, runtime_text)
    return {SWC_TO_CATEGORY[swc] for swc in result["finding_swcs"].split(";") if swc in SWC_TO_CATEGORY}


def file_flags(engine, synthesizer, entry):
    """Union of the categories of a file's runtime contracts, and the names of the linked ones."""
    flags, linked = set(), []
    for contract_name, path in entry["runtime_bytecode_paths"].items():
        with open(resolve(path), encoding="utf-8") as handle:
            raw = handle.read().strip()
        text = linked_hex(raw)
        if text != raw:
            linked.append(contract_name)
        flags |= contract_categories(engine, synthesizer, contract_name, text)
    return ";".join(sorted(flags)), linked


def main() -> None:
    with open(CATALOG, encoding="utf-8") as handle:
        catalog = json.load(handle)
    with open(MAIN_FILES, newline="", encoding="utf-8") as handle:
        main_flags = {row["contract_id"]: row["flagged_categories"] for row in csv.DictReader(handle)}
    engine = SymbolicEVMInterpreter()
    synthesizer = ExploitSynthesizer()
    rows, changed, linked_files = [], [], []
    for entry in catalog:
        contract_id = entry["contract_id"]
        flags, linked = file_flags(engine, synthesizer, entry)
        if linked:
            linked_files.append({"contract_id": contract_id, "runtime_contracts": linked})
        if flags != main_flags[contract_id]:
            changed.append({"contract_id": contract_id, "main_run": main_flags[contract_id], "linked": flags})
        rows.append({"contract_id": contract_id, "labels": ";".join(entry["labels"]), "flagged_categories": flags})
    scores = {key: score_category(rows, key, "flagged_categories") for key in SCORED}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump({"linked": linked_files, "files_changed": changed, "scores": scores}, handle, indent=2)
    print(json.dumps({"linked": linked_files, "files_changed": changed, "reentrancy": scores["reentrancy"]}, indent=2))


if __name__ == "__main__":
    main()
