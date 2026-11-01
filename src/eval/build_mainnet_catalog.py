"""Build the real-world corpus of protocol 7: deployed Solidity 0.4-0.5 contracts that hold ether.

Selection (fixed in docs/MAINNET_EVAL_PROTOCOL.md before any engine run on these contracts):
  1. Every entry of the smart-contract-sanctuary mainnet index whose compiler is v0.4.x or v0.5.x.
  2. Minus every address that appears in a corpus used earlier (any 0x-address in benchmarks/
     and in the cloned external datasets).
  3. Balance and runtime code are read at one block, the latest block when the script starts.
     Contracts with zero balance or empty code (self-destructed) are dropped.

The engine analyses the deployed runtime code read from the chain, not a recompilation.
Writes benchmarks/mainnet_catalog.json and benchmarks/mainnet/<address>.bin-runtime.

Usage: build_mainnet_catalog.py <sanctuary contracts.json> <rpc url>
"""
import hashlib
import json
import os
import re
import sys
import time

import requests

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_CATALOG = os.path.join(REPO, "benchmarks", "mainnet_catalog.json")
OUT_CODE = os.path.join(REPO, "benchmarks", "mainnet")
SEEN_SOURCES = [os.path.join(REPO, "benchmarks"), os.path.join(REPO, "external", "smartbugs-curated"),
                os.path.join(REPO, "external", "smartcontract-benchmark")]
COMPILER = re.compile(r"^v0\.[45]\.\d+")
ADDRESS = re.compile(r"0x[0-9a-fA-F]{40}")
BATCH_SIZE = 50
BALANCE_CHUNK = 500
PAUSE_S = 0.3
MAX_RETRIES = 8
# Runtime code that returns BALANCE(a) for each 32-byte address a in its calldata. It is placed
# at an unused address through eth_call state override, so one call reads 500 balances at the
# pinned block. Checked against eth_getBalance on 200 addresses before use (identical).
BALANCE_READER = "0x60005b3681101560155780353181526020016002565b50366000f3"
READER_ADDRESS = "0x000000000000000000000000000000000000fa11"
TIMEOUT_S = 30
SANCTUARY_SOURCE = "contracts/mainnet/{prefix}/{address}_{name}.sol"


def seen_addresses() -> set:
    """Every 0x-address mentioned in an earlier corpus, by file name or file content."""
    found = set()
    for root_dir in SEEN_SOURCES:
        for root, _, files in os.walk(root_dir):
            if os.path.join("benchmarks", "mainnet") in root:
                continue
            for name in files:
                found |= {a.lower() for a in ADDRESS.findall(name)}
                if name.endswith((".json", ".sol", ".csv", ".md")):
                    with open(os.path.join(root, name), encoding="utf-8", errors="ignore") as handle:
                        found |= {a.lower() for a in ADDRESS.findall(handle.read())}
    return found


def candidates(index_path: str, excluded: set) -> list:
    by_address = {}
    with open(index_path, encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            entry = json.loads(line)
            address = entry["address"].lower()
            if COMPILER.match(entry.get("compiler", "")) and address not in excluded:
                by_address.setdefault(address, entry)
    return [by_address[a] for a in sorted(by_address)]


def rpc_batch(url: str, calls: list) -> list:
    """One JSON-RPC batch with exponential backoff on transport errors and rate limits."""
    payload = [{"jsonrpc": "2.0", "id": i, "method": m, "params": p} for i, (m, p) in enumerate(calls)]
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(url, json=payload, timeout=TIMEOUT_S)
            if response.status_code == 429:
                raise requests.RequestException("rate limited")
            response.raise_for_status()
            replies = {r["id"]: r for r in response.json()}
            if any("error" in r for r in replies.values()):
                raise requests.RequestException(str(next(r["error"] for r in replies.values() if "error" in r)))
            return [replies[i]["result"] for i in range(len(calls))]
        except (requests.RequestException, ValueError, KeyError) as error:
            if attempt == MAX_RETRIES - 1:
                raise RuntimeError(f"RPC batch failed after {MAX_RETRIES} attempts: {error}") from error
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def chunks(items: list, size: int):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def read_balances(url: str, entries: list, block: str) -> list:
    balances = []
    for chunk in chunks(entries, BALANCE_CHUNK):
        data = "0x" + "".join(e["address"][2:].lower().rjust(64, "0") for e in chunk)
        call = {"to": READER_ADDRESS, "data": data}
        output = rpc_batch(url, [("eth_call", [call, block, {READER_ADDRESS: {"code": BALANCE_READER}}])])[0][2:]
        balances += [int(output[i:i + 64], 16) for i in range(0, len(output), 64)]
        time.sleep(PAUSE_S)
    return balances


def read_chain(url: str, entries: list, block: str) -> list:
    """Balance and code of each candidate at the block; keep those with ether and code."""
    holders = [(e, wei) for e, wei in zip(entries, read_balances(url, entries, block)) if wei > 0]
    kept = []
    for batch in chunks(holders, BATCH_SIZE):
        codes = rpc_batch(url, [("eth_getCode", [e["address"], block]) for e, _ in batch])
        kept += [(e, wei, code[2:]) for (e, wei), code in zip(batch, codes) if len(code) > 2]
        time.sleep(PAUSE_S)
    return kept


def catalog_entry(entry: dict, wei: int, code: str, block_number: int) -> dict:
    address = entry["address"].lower()
    path = os.path.join("benchmarks", "mainnet", f"{address}.bin-runtime")
    with open(os.path.join(REPO, path), "w", encoding="utf-8") as handle:
        handle.write(code + "\n")
    return {
        "contract_id": f"mainnet__{address}", "address": address, "name": entry["name"],
        "compiler": entry["compiler"], "balance_wei": str(wei), "block": block_number,
        "labels": [], "sloc": 0, "runtime_bytecode_paths": {entry["name"]: path},
        "code_sha256": hashlib.sha256(bytes.fromhex(code)).hexdigest(),
        "sanctuary_source": SANCTUARY_SOURCE.format(prefix=address[2:4], address=entry["address"][2:],
                                                    name=entry["name"]),
    }


def main() -> None:
    index_path, url = sys.argv[1], sys.argv[2]
    excluded = seen_addresses()
    entries = candidates(index_path, excluded)
    block_number = int(rpc_batch(url, [("eth_blockNumber", [])])[0], 16)
    os.makedirs(OUT_CODE, exist_ok=True)
    kept = read_chain(url, entries, hex(block_number))
    catalog = [catalog_entry(e, wei, code, block_number) for e, wei, code in kept]
    with open(OUT_CATALOG, "w", encoding="utf-8") as handle:
        json.dump(catalog, handle, indent=1)
    print(json.dumps({"candidates": len(entries), "excluded_addresses": len(excluded),
                      "block": block_number, "holding_ether": len(catalog)}))


if __name__ == "__main__":
    main()
