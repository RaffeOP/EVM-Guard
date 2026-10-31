"""Build the held-out SolidiFI catalog under docs/HELDOUT_EVAL_PROTOCOL.md.

Each Solidity file is compiled with `solc --combined-json bin-runtime` (no optimizer),
trying installed compilers from newest to oldest. The first compiler that accepts the
file is used, which is the highest version satisfying its pragma. Output:
  benchmarks/heldout_catalog.json          one entry per source file
  benchmarks/heldout/*.bin-runtime         one file per runtime contract
"""
import glob
import json
import os
import re
import shutil
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BENCH_ROOT = "/tmp/solidifi_bench/SolidiFI-benchmark-master"  # extracted from the pinned archive
CLEAN_ROOT = "/tmp/solidifi/SolidiFI-master/contracts"
SOLC_DIR = os.path.expanduser("~/.solc-select/artifacts")
OUT_CATALOG = os.path.join(REPO, "benchmarks/heldout_catalog.json")
OUT_BYTECODE = os.path.join(REPO, "benchmarks/heldout")
OUT_SOURCES = os.path.join(REPO, "benchmarks/heldout_sources")
FOLDER_LABELS = {
    "Re-entrancy": "reentrancy",
    "Overflow-Underflow": "arithmetic",
    "tx.origin": "tx_origin",
    "TOD": "transaction_order",
    "Timestamp-Dependency": "timestamp_dependency",
    "Unchecked-Send": "unchecked_send",
    "Unhandled-Exceptions": "unhandled_exceptions",
}
INSTALLED = ["0.8.20", "0.5.12", "0.5.8", "0.5.0", "0.4.25", "0.4.24", "0.4.23", "0.4.22",
             "0.4.21", "0.4.19", "0.4.18", "0.4.16", "0.4.15", "0.4.13", "0.4.11", "0.4.10",
             "0.4.9", "0.4.0"]


def solc_path(version: str) -> str:
    return os.path.join(SOLC_DIR, f"solc-{version}", f"solc-{version}")


def compile_file(sol_path: str):
    """Return (version, {contract_name: runtime_hex}) for the first compiler that accepts the file."""
    last_error = "no installed compiler accepted the file"
    for version in INSTALLED:
        done = subprocess.run([solc_path(version), "--combined-json", "bin-runtime", sol_path],
                              capture_output=True, text=True, check=False)
        if done.returncode != 0:
            last_error = done.stderr.strip().splitlines()[0][:200] if done.stderr.strip() else "compile error"
            continue
        contracts = json.loads(done.stdout).get("contracts", {})
        runtimes = {}
        for key, value in contracts.items():
            name = key.rsplit(":", 1)[-1]
            if value.get("bin-runtime"):
                runtimes[name] = value["bin-runtime"]
        return version, runtimes, None
    return None, {}, last_error


def sloc(path: str) -> int:
    with open(path, encoding="utf-8", errors="replace") as handle:
        return sum(1 for line in handle if line.strip())


def entries_from(root: str, folder: str, label: str):
    for sol in sorted(glob.glob(os.path.join(root, "*.sol"))):
        yield folder, label, sol


def main() -> None:
    os.makedirs(OUT_BYTECODE, exist_ok=True)
    os.makedirs(OUT_SOURCES, exist_ok=True)
    sources = []
    for folder, label in FOLDER_LABELS.items():
        sources += list(entries_from(os.path.join(BENCH_ROOT, "buggy_contracts", folder), folder, label))
    sources += [("clean", None, sol) for sol in sorted(glob.glob(os.path.join(CLEAN_ROOT, "*.sol")))]
    catalog, errors = [], []
    for folder, label, sol in sources:
        version, runtimes, error = compile_file(sol)
        base = os.path.basename(os.path.dirname(sol)) + "_" + os.path.basename(sol)[:-4]
        contract_id = re.sub(r"[^A-Za-z0-9_.-]", "_", f"{folder}__{base}")
        if error or not runtimes:
            errors.append({"contract_id": contract_id, "solc_error": error or "no runtime bytecode"})
            continue
        source_copy = os.path.join(OUT_SOURCES, f"{contract_id}.sol")
        shutil.copyfile(sol, source_copy)
        paths = {}
        for name, runtime_hex in runtimes.items():
            path = os.path.join(OUT_BYTECODE, f"{contract_id}__{name}.bin-runtime")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(runtime_hex)
            paths[name] = os.path.relpath(path, REPO)
        catalog.append({
            "contract_id": contract_id,
            "source_path": os.path.relpath(source_copy, REPO),
            "dataset_category_dir": folder,
            "labels": [label] if label else [],
            "sloc": sloc(sol),
            "solc_version": version,
            "runtime_bytecode_paths": paths,
        })
    with open(OUT_CATALOG, "w", encoding="utf-8") as handle:
        json.dump(catalog, handle, indent=2)
    print(json.dumps({"compiled_sources": len(catalog), "compile_errors": len(errors)}))
    for item in errors[:10]:
        print("ERR", item)


if __name__ == "__main__":
    main()
