"""Draw the protocol 7 hand-check sample and fetch its verified sources.

All contracts flagged for reentrancy by v5 or v6 if there are at most 120, otherwise a uniform
random sample of 120 from their union (random.Random(7) over the sorted addresses), as fixed in
docs/ENGINE_V6_EVAL_PROTOCOL.md. Sources come from smart-contract-sanctuary at the pinned commit.
Its index lists some addresses for which the repository holds no file; their source is read from
Sourcify (only a full or exact runtime match is accepted), else from the Blockscout Ethereum
explorer (Etherscan-compatible getsourcecode). The origin of each source is recorded.
Writes results/protocol7/mainnet_sample.json and results/protocol7/mainnet_sample_sources/.
"""
import csv
import glob
import json
import os
import random
import time
from collections import Counter

import requests
from eth_utils import to_checksum_address

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUNS = os.path.join(REPO, "results", "protocol7")
SAMPLE_SIZE = 120
SEED = 7
SANCTUARY = ("https://raw.githubusercontent.com/tintinweb/smart-contract-sanctuary-ethereum/"
             "015d0105102504dc8733a18c3543f87f1829a5e8/")
SOURCIFY = "https://sourcify.dev/server/v2/contract/1/{address}?fields=sources"
SOURCIFY_MATCHES = ("match", "exact_match")
BLOCKSCOUT = "https://eth.blockscout.com/api?module=contract&action=getsourcecode&address="
MAX_RETRIES = 9
TIMEOUT_S = 30
PAUSE_S = 1.0


def flagged(engine: str) -> set:
    found = set()
    for path in glob.glob(os.path.join(RUNS, engine, "mainnet_shard*", "evm_guard_contracts.csv")):
        with open(path, newline="", encoding="utf-8") as handle:
            found |= {r["contract_id"] for r in csv.DictReader(handle) if "SWC-107" in r["finding_swcs"].split(";")}
    return found


def candidate_paths(entry: dict) -> list:
    """The sanctuary names files by checksummed or lowercase address; try both."""
    address = entry["address"]
    prefix = address[2:4]
    names = list(dict.fromkeys([entry["sanctuary_source"].split("/")[-1].split("_")[0],
                                to_checksum_address(address)[2:], address[2:].lower()]))
    return [f"contracts/mainnet/{prefix}/{n}_{entry['name']}.sol" for n in names]


def blockscout_source(address: str):
    """Verified source text from Blockscout, or None if the contract is not verified there."""
    text = fetch(BLOCKSCOUT + address)
    if text is None:
        return None
    results = json.loads(text).get("result") or []
    source = results[0].get("SourceCode", "") if results and isinstance(results, list) else ""
    return source or None


def sourcify_source(address: str):
    """All source files of a Sourcify runtime match, concatenated with file headers, or None."""
    text = fetch(SOURCIFY.format(address=address))
    if text is None:
        return None
    record = json.loads(text)
    if record.get("runtimeMatch") not in SOURCIFY_MATCHES:
        return None
    files = record.get("sources") or {}
    return "\n".join(f"// File: {name}\n{body['content']}" for name, body in sorted(files.items())) or None


def fetch_source(entry: dict) -> tuple:
    """(origin, verified source); (None, None) if neither the sanctuary nor Blockscout has it."""
    for path in candidate_paths(entry):
        text = fetch(SANCTUARY + path)
        if text is not None:
            return "sanctuary", text
    text = sourcify_source(entry["address"])
    if text:
        return "sourcify", text
    text = blockscout_source(entry["address"])
    return ("blockscout", text) if text else (None, None)


def fetch(url: str):
    """Text of the url, or None on 404; retries other errors with backoff."""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=TIMEOUT_S)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.text
        except requests.RequestException as error:
            if attempt == MAX_RETRIES - 1:
                raise RuntimeError(f"cannot fetch {url}: {error}") from error
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def main() -> None:
    union = sorted(flagged("v5") | flagged("v6"))
    sample = union if len(union) <= SAMPLE_SIZE else sorted(random.Random(SEED).sample(union, SAMPLE_SIZE))
    with open(os.path.join(REPO, "benchmarks", "mainnet_catalog.json"), encoding="utf-8") as handle:
        catalog = {e["contract_id"]: e for e in json.load(handle)}
    out_dir = os.path.join(RUNS, "mainnet_sample_sources")
    os.makedirs(out_dir, exist_ok=True)
    origins = {}
    previous = {}
    if os.path.exists(os.path.join(RUNS, "mainnet_sample.json")):
        with open(os.path.join(RUNS, "mainnet_sample.json"), encoding="utf-8") as handle:
            previous = json.load(handle).get("source_origin", {})
    for contract_id in sample:
        target = os.path.join(out_dir, f"{catalog[contract_id]['address']}.sol")
        if os.path.exists(target) and previous.get(contract_id):
            origins[contract_id] = previous[contract_id]
            continue
        origin, text = fetch_source(catalog[contract_id])
        origins[contract_id] = origin
        if text is not None:
            with open(target, "w", encoding="utf-8") as handle:
                handle.write(text)
        time.sleep(PAUSE_S)
    missing = [c for c, origin in origins.items() if origin is None]
    with open(os.path.join(RUNS, "mainnet_sample.json"), "w", encoding="utf-8") as handle:
        json.dump({"union": len(union), "sample": sample, "source_origin": origins, "source_missing": missing},
                  handle, indent=1)
    print(json.dumps({"union": len(union), "sample": len(sample), "origins": dict(Counter(origins.values()))}))


if __name__ == "__main__":
    main()
