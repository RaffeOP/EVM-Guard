"""Run EVMLiSA's reentrancy checker on the runtime bytecode of a catalog.

EVMLiSA (Arceri et al., lisa-analyzer/evm-lisa, built from commit 44ae6dd) analyses bytecode,
so it receives the same runtime code as EVM-Guard. The solc CBOR metadata trailer is stripped
first, as EVM-Guard does, because EVMLiSA stops with an exception on the truncated PUSH that
the trailer decodes to. A file is flagged for reentrancy if EVMLiSA reports at least one
reentrancy warning on any of its runtime contracts. Output has the schema of
run_external_baselines.py.

Files without runtime code (the source does not compile, or only abstract contracts) get
status no_bytecode, and runtime code with unlinked library placeholders is skipped; EVM-Guard
receives the same input and skips the same code.

Rerun (--rerun-from <dir> --jar <jar> --timeout 600): only the files whose status in <dir> is
error or timeout are run again, written to evmlisa_rerun_<shard>.csv. The rerun jar is built
from the same commit with one change in EVMLiSA.buildCFG, createConfiguration(contract, false),
which turns off the DOT/JSON dump of the CFG; that dump crashes on some graphs with a duplicate
edge id ("edge-... already in use") after the analysis has finished. It does not change the
findings: identical reentrancy counts on 20 SmartBugs files that the stock jar completes.

Usage: run_evmlisa.py --catalog <catalog> --out-dir <dir> [--shard i --of n] [--timeout s]
                      [--jar <jar> --rerun-from <dir>]
"""
import argparse
import csv
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.join(REPO, "src", "eval"))

from repo_paths import resolve  # noqa: E402
from symbolic_engine import SymbolicEVMInterpreter  # noqa: E402

JAR = os.path.join(REPO, "external/tools/evm-lisa/build/libs/evm-lisa-all.jar")
JAVA = "/Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home/bin/java"
DEFAULT_TIMEOUT_S = 60


def run_contract(runtime_hex: str, work: str, timeout_s: int, jar: str = JAR) -> tuple:
    """Return (status, reentrancy warnings, milliseconds) for one runtime contract."""
    body = runtime_hex[2:] if runtime_hex.startswith("0x") else runtime_hex
    code = SymbolicEVMInterpreter.strip_cbor_metadata(bytes.fromhex(body)).hex()
    name = "contract"
    shutil.rmtree(os.path.join(work, "out"), ignore_errors=True)
    with open(os.path.join(work, f"{name}.bytecode"), "w", encoding="utf-8") as handle:
        handle.write("0x" + code)
    command = [JAVA, "-jar", jar, "--bytecode-path", f"{name}.bytecode", "--checker-reentrancy",
               "--output-directory-path", "out"]
    start = time.perf_counter()
    try:
        subprocess.run(command, cwd=work, capture_output=True, timeout=timeout_s, check=False)
    except subprocess.TimeoutExpired:
        return "timeout", 0, timeout_s * 1000.0
    elapsed = (time.perf_counter() - start) * 1000.0
    try:
        with open(os.path.join(work, "out", name, "results.json"), encoding="utf-8") as handle:
            warnings = int(json.load(handle)["vulnerabilities"]["reentrancy"])
    except (OSError, ValueError, KeyError, TypeError):
        return "error", 0, elapsed
    return "ok", warnings, elapsed


def file_status(statuses: list) -> str:
    """ok if every runtime contract finished; otherwise timeout if any timed out, else error."""
    if not statuses:
        return "no_bytecode"
    if all(s == "ok" for s in statuses):
        return "ok"
    return "timeout" if "timeout" in statuses else "error"


def run_file(entry: dict, work: str, timeout_s: int, jar: str = JAR) -> dict:
    statuses, warnings, latency, unlinked = [], 0, 0.0, []
    for name, path in entry["runtime_bytecode_paths"].items():
        with open(resolve(path), encoding="utf-8") as handle:
            runtime_hex = handle.read().strip()
        try:
            bytes.fromhex(runtime_hex[2:] if runtime_hex.startswith("0x") else runtime_hex)
        except ValueError:
            unlinked.append(name)
            continue
        status, count, ms = run_contract(runtime_hex, work, timeout_s, jar)
        statuses.append(status)
        warnings += count
        latency += ms
    return {"contract_id": entry["contract_id"], "labels": ";".join(entry["labels"]), "status": file_status(statuses),
            "flagged_categories": "reentrancy" if warnings else "", "latency_ms": round(latency, 2),
            "raw_findings": f"reentrancy={warnings}" + "".join(f";unlinked={n}" for n in unlinked)}


def failed_ids(result_dir: str) -> set:
    """Files whose status in an earlier run of this script was error or timeout."""
    failed = set()
    for path in glob.glob(os.path.join(result_dir, "evmlisa_files_*.csv")):
        with open(path, newline="", encoding="utf-8") as handle:
            failed |= {r["contract_id"] for r in csv.DictReader(handle) if r["status"] in ("error", "timeout")}
    return failed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--of", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S)
    parser.add_argument("--jar", default=JAR)
    parser.add_argument("--rerun-from")
    args = parser.parse_args()
    with open(args.catalog, encoding="utf-8") as handle:
        catalog = json.load(handle)
    prefix = "evmlisa_files"
    if args.rerun_from:
        failed = failed_ids(args.rerun_from)
        catalog, prefix = [e for e in catalog if e["contract_id"] in failed], "evmlisa_rerun"
    catalog = catalog[args.shard::args.of]
    os.makedirs(args.out_dir, exist_ok=True)
    out = os.path.join(args.out_dir, f"{prefix}_{args.shard}.csv")
    fields = ["contract_id", "labels", "status", "flagged_categories", "latency_ms", "raw_findings"]
    with tempfile.TemporaryDirectory() as work, open(out, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for entry in catalog:
            writer.writerow(run_file(entry, work, args.timeout, os.path.abspath(args.jar)))
            handle.flush()
    print(out)


if __name__ == "__main__":
    main()
