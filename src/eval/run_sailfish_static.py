"""Run the static stage of Sailfish (Bose et al., S&P 2022) on the sources of a catalog.

Sailfish has two stages: a static analysis over a storage dependency graph that emits
reentrancy (DAO) candidates, and a symbolic verifier, written in Racket, that discards
candidates it can refute. The authors' image (holmessherlock/sailfish:latest) is amd64 only.
On the arm64 evaluation machine its Racket runtime aborts with SIGABRT under both QEMU and
Rosetta emulation, even for `racket -e "(display 1)"` (results/baselines_round3/sailfish/),
so the verifier cannot run and the full tool cannot be evaluated here. This script runs the
static stage only (`--static-only`, DAO pattern, owner-only external-call heuristic). Because
the verifier only removes candidates, a file this stage does not flag would not be flagged
by full Sailfish either: the stage's recall and flag count are upper bounds for the full tool,
and its precision is not the full tool's precision.

A file is flagged for reentrancy if Sailfish writes a non-empty dao_path_info.json. Each file
is compiled with its catalog solc version; for 0.4.0, 0.4.2 and 0.4.9, which have no Linux
release, 0.4.10 is used and the substitution is recorded. Output has the schema of
run_external_baselines.py.

Usage: run_sailfish_static.py --catalog <catalog> --out-dir <dir> [--shard i --of n]
"""
import argparse
import csv
import json
import os
import subprocess
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IMAGE = "holmessherlock/sailfish:latest"
SOLC_DIR = "external/tools/solc-linux"
SUBSTITUTE_SOLC = "0.4.10"
TIMEOUT_S = 120
ANALYSIS_DIR = "/root/sailfish/code/static_analysis/analysis"


def start_container(name: str) -> None:
    subprocess.run(["docker", "rm", "-f", name], capture_output=True, check=False)
    subprocess.run(["docker", "run", "-d", "--platform", "linux/amd64", "--name", name,
                    "-v", f"{REPO}:/repo:ro", IMAGE, "sleep", "infinity"], capture_output=True, check=True)


def solc_for(version) -> tuple:
    """(solc path inside the container, version used) or (None, None) if the file has no compiler."""
    if not version:
        return None, None
    used = version if os.path.exists(os.path.join(REPO, SOLC_DIR, f"solc-{version}")) else SUBSTITUTE_SOLC
    return f"/repo/{SOLC_DIR}/solc-{used}", used


def run_file(container: str, entry: dict) -> dict:
    solc, used = solc_for(entry.get("solc_version"))
    row = {"contract_id": entry["contract_id"], "labels": ";".join(entry["labels"]), "status": "no_bytecode",
           "flagged_categories": "", "latency_ms": 0.0, "raw_findings": ""}
    if solc is None:
        return row
    name = os.path.splitext(os.path.basename(entry["source_path"]))[0]
    out = f"/tmp/out_{entry['contract_id']}"
    script = (f"rm -rf {out} && mkdir -p {out} && cd {ANALYSIS_DIR} && timeout {TIMEOUT_S} python contractlint.py "
              f"-c /repo/{entry['source_path']} -o {out} -r range -p DAO -oo -s -sc {solc} >/dev/null 2>&1; "
              f"echo rc=$?; cat {out}/{name}/dao_path_info.json 2>/dev/null")
    start = time.perf_counter()
    try:
        done = subprocess.run(["docker", "exec", container, "sh", "-c", script], capture_output=True, text=True,
                              timeout=TIMEOUT_S + 30, check=False)
    except subprocess.TimeoutExpired:
        return {**row, "status": "timeout", "latency_ms": TIMEOUT_S * 1000.0}
    row["latency_ms"] = round((time.perf_counter() - start) * 1000.0, 2)
    first, _, body = done.stdout.partition("\n")
    code = first.replace("rc=", "").strip()
    substituted = "" if used == entry["solc_version"] else f";solc={used}"
    if code == "124":
        return {**row, "status": "timeout", "raw_findings": substituted.lstrip(";")}
    try:
        paths = json.loads(body) if body.strip() else None
    except ValueError:
        paths = None
    if paths is None:
        return {**row, "status": "error", "raw_findings": f"rc={code}{substituted}"}
    return {**row, "status": "ok", "flagged_categories": "reentrancy" if paths else "",
            "raw_findings": f"dao_paths={len(paths)}{substituted}"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--of", type=int, default=1)
    args = parser.parse_args()
    with open(args.catalog, encoding="utf-8") as handle:
        catalog = json.load(handle)[args.shard::args.of]
    os.makedirs(args.out_dir, exist_ok=True)
    container = f"sailfish_shard_{os.getpid()}"
    start_container(container)
    out = os.path.join(args.out_dir, f"sailfish_files_{args.shard}.csv")
    fields = ["contract_id", "labels", "status", "flagged_categories", "latency_ms", "raw_findings"]
    try:
        with open(out, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for entry in catalog:
                writer.writerow(run_file(container, entry))
                handle.flush()
    finally:
        subprocess.run(["docker", "rm", "-f", container], capture_output=True, check=False)
    print(out)


if __name__ == "__main__":
    main()
