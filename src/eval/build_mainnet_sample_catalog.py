"""Catalog of the protocol 7 hand-checked sample for the source-level baseline (Slither).

One entry per sampled contract: its verified source, the compiler version it was deployed
with, and label `reentrancy` if the locked blind label is `exploitable`. The file names hold
addresses, so the catalog is kept local with the blind key (see .gitignore).
Output: results/protocol7/mainnet_sample_catalog.json
"""
import csv
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUNS = os.path.join(REPO, "results", "protocol7")
VERSION = re.compile(r"v(\d+\.\d+\.\d+)")


def main() -> None:
    with open(os.path.join(RUNS, "mainnet_sample.json"), encoding="utf-8") as handle:
        sample = json.load(handle)["sample"]
    with open(os.path.join(REPO, "benchmarks", "mainnet_catalog.json"), encoding="utf-8") as handle:
        catalog = {e["contract_id"]: e for e in json.load(handle)}
    with open(os.path.join(RUNS, "mainnet_labels_blind.csv"), newline="", encoding="utf-8") as handle:
        labels = {r["blind_id"]: r["label"] for r in csv.DictReader(handle)}
    with open(os.path.join(RUNS, "blind_key_DO_NOT_OPEN.csv"), newline="", encoding="utf-8") as handle:
        address_label = {r["original_file"][:-4]: labels[r["blind_id"]] for r in csv.DictReader(handle)}
    entries = []
    for contract_id in sample:
        entry = catalog[contract_id]
        entries.append({"contract_id": contract_id, "solc_version": VERSION.match(entry["compiler"]).group(1),
                        "source_path": f"results/protocol7/mainnet_sample_sources/{entry['address']}.sol",
                        "labels": ["reentrancy"] if address_label[entry["address"]] == "exploitable" else []})
    with open(os.path.join(RUNS, "mainnet_sample_catalog.json"), "w", encoding="utf-8") as handle:
        json.dump(entries, handle, indent=1)
    print(len(entries))


if __name__ == "__main__":
    main()
