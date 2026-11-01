"""Run Slither or Mythril on SmartBugs-curated with the mappings in Addendum A."""
import argparse
import csv
import json
import os
import subprocess
import tempfile
import time

from repo_paths import resolve

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CATALOG = os.path.join(REPO, "benchmarks/benchmark_catalog_external.json")
OUT_DIR = os.path.join(REPO, "results/external")
SLITHER = os.environ.get("SLITHER_BIN", os.path.join(REPO, ".venv/bin/slither"))
MYTHRIL = os.environ.get("MYTHRIL_BIN", "myth")
SOLC_TEMPLATE = os.path.expanduser("~/.solc-select/artifacts/solc-{v}/solc-{v}")
TIMEOUT_S = 60
SLITHER_MAP = {
    "reentrancy": {"reentrancy-eth", "reentrancy-no-eth", "reentrancy-benign",
                   "reentrancy-events", "reentrancy-unlimited-gas"},
    "denial_of_service": {"calls-loop", "costly-loop"},
    "access_control": {"arbitrary-send-eth", "arbitrary-send-erc20", "suicidal",
                       "controlled-delegatecall", "unprotected-upgrade", "tx-origin",
                       "protected-vars", "incorrect-modifier"},
}
MYTHRIL_MAP = {
    "reentrancy": {"107"},
    "arithmetic": {"101"},
    "denial_of_service": {"113", "128"},
    "access_control": {"105", "106", "112", "115", "124"},
}


def categories_for(found: set, mapping: dict) -> list:
    return sorted(c for c, names in mapping.items() if found & names)


def run_slither(entry: dict) -> tuple:
    report = os.path.join(tempfile.gettempdir(), f"sb_slither_{os.getpid()}.json")
    if os.path.exists(report):
        os.remove(report)
    solc = SOLC_TEMPLATE.format(v=entry["solc_version"])
    command = [SLITHER, resolve(entry["source_path"]), "--solc", solc, "--json", report, "--disable-color"]
    start = time.perf_counter()
    try:
        subprocess.run(command, capture_output=True, text=True, timeout=TIMEOUT_S, check=False)
    except subprocess.TimeoutExpired:
        return "timeout", [], TIMEOUT_S * 1000.0, []
    elapsed = (time.perf_counter() - start) * 1000.0
    try:
        with open(report, encoding="utf-8") as handle:
            detectors = json.load(handle)["results"].get("detectors", [])
    except (OSError, json.JSONDecodeError, KeyError):
        return "error", [], elapsed, []
    checks = {d["check"] for d in detectors}
    return "ok", categories_for(checks, SLITHER_MAP), elapsed, sorted(checks)


def solc_path_dir(version: str) -> str:
    """Directory holding a `solc` link to the requested version (Mythril uses PATH)."""
    directory = os.path.join(tempfile.gettempdir(), f"solc_{version}")
    link = os.path.join(directory, "solc")
    os.makedirs(directory, exist_ok=True)
    try:
        os.symlink(SOLC_TEMPLATE.format(v=version), link)
    except FileExistsError:
        pass
    return directory


def run_mythril(entry: dict) -> tuple:
    command = [MYTHRIL, "analyze", resolve(entry["source_path"]),
               "-o", "json", "--execution-timeout", str(TIMEOUT_S - 10)]
    env = dict(os.environ, PATH=solc_path_dir(entry["solc_version"]) + os.pathsep + os.environ["PATH"])
    start = time.perf_counter()
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=TIMEOUT_S,
                              check=False, env=env)
    except subprocess.TimeoutExpired:
        return "timeout", [], TIMEOUT_S * 1000.0, []
    elapsed = (time.perf_counter() - start) * 1000.0
    try:
        output = json.loads(done.stdout)
    except json.JSONDecodeError:
        return "error", [], elapsed, []
    if not output.get("success", True):
        return "error", [], elapsed, []
    swc_ids = {str(i.get("swc-id", "")) for i in output.get("issues", [])}
    return "ok", categories_for(swc_ids, MYTHRIL_MAP), elapsed, sorted(swc_ids)


def main() -> None:
    global TIMEOUT_S
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool", choices=["slither", "mythril"], required=True)
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--of", type=int, default=1)
    parser.add_argument("--catalog", default=CATALOG)
    parser.add_argument("--out-dir", default=OUT_DIR)
    parser.add_argument("--timeout", type=int, default=TIMEOUT_S)
    parser.add_argument("--ids", default=None, help="JSON list of contract_ids to run (default: all)")
    args = parser.parse_args()
    TIMEOUT_S = args.timeout
    with open(args.catalog, encoding="utf-8") as handle:
        catalog = json.load(handle)
    if args.ids:
        with open(args.ids, encoding="utf-8") as handle:
            wanted = set(json.load(handle))
        catalog = [entry for entry in catalog if entry["contract_id"] in wanted]
    catalog = catalog[args.shard::args.of]
    runner = run_slither if args.tool == "slither" else run_mythril
    os.makedirs(args.out_dir, exist_ok=True)
    out = os.path.join(args.out_dir, f"{args.tool}_files_{args.shard}.csv")
    with open(out, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["contract_id", "labels", "status",
                                                    "flagged_categories", "latency_ms", "raw_findings"])
        writer.writeheader()
        for entry in catalog:
            status, cats, ms, raw = runner(entry)
            writer.writerow({"contract_id": entry["contract_id"], "labels": ";".join(entry["labels"]),
                             "status": status, "flagged_categories": ";".join(cats),
                             "latency_ms": round(ms, 2), "raw_findings": ";".join(raw)})
            handle.flush()
    print(out)


if __name__ == "__main__":
    main()
