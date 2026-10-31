"""Build the held-out catalog 2 under docs/HELDOUT2_EVAL_PROTOCOL.md.

The contracts come from bit-smartcontract-analysis/smartcontract-benchmark at the pinned
commit. That repository has no licence, so the sources and bytecode are written to
benchmarks/heldout2_local/, which is git-ignored and not redistributed. The catalog
records the commit and the SHA-256 of every source file, so the build can be checked.

Usage: build_heldout2_catalog.py <path-to-clone-at-pinned-commit>
"""
import glob
import hashlib
import json
import os
import shutil
import sys

from build_heldout_catalog import compile_file, sloc

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PINNED_COMMIT = "8b903aae40648ad0ead87662857c6685542710d5"
LOCAL_ROOT = os.path.join(REPO, "benchmarks/heldout2_local")
OUT_CATALOG = os.path.join(REPO, "benchmarks/heldout2_catalog.json")
FOLDER_LABELS = {
    "reentrancy": ["reentrancy"],
    "arithmetic": ["arithmetic"],
    "unsafe_delegatecall": ["access_control"],
    "tx_origin": ["access_control"],
    "unsafe_suicide": ["access_control"],
    "unchecked_send": [],
    "TOD": [],
    "time_manipulation": [],
    "bad_randomness": [],
    "gasless_send": [],
    "safecontract": [],
}


def sha256_of(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        digest.update(handle.read())
    return digest.hexdigest()


def entries(clone_root: str):
    dataset = os.path.join(clone_root, "labelled-dataset")
    for folder in FOLDER_LABELS:
        for sol in sorted(glob.glob(os.path.join(dataset, folder, "*.sol"))):
            yield folder, sol


def build_entry(folder: str, sol: str, out_sources: str, out_bytecode: str) -> dict:
    """Compile one file. A file that does not compile stays in the catalog with no bytecode."""
    version, runtimes, error = compile_file(sol)
    contract_id = f"{folder}__{os.path.basename(sol)[:-4]}".replace(" ", "_")
    source_copy = os.path.join(out_sources, f"{contract_id}.sol")
    shutil.copyfile(sol, source_copy)
    paths = {}
    if not error:
        for name, runtime_hex in runtimes.items():
            path = os.path.join(out_bytecode, f"{contract_id}__{name}.bin-runtime")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(runtime_hex)
            paths[name] = os.path.relpath(path, REPO)
    return {
        "contract_id": contract_id,
        "source_path": os.path.relpath(source_copy, REPO),
        "source_sha256": sha256_of(sol),
        "dataset_category_dir": folder,
        "labels": FOLDER_LABELS[folder],
        "sloc": sloc(sol),
        "solc_version": version,
        "solc_error": (error or ("no runtime bytecode" if not paths else ""))[:200],
        "runtime_bytecode_paths": paths,
    }


def main() -> None:
    clone_root = sys.argv[1]
    out_sources = os.path.join(LOCAL_ROOT, "sources")
    out_bytecode = os.path.join(LOCAL_ROOT, "bytecode")
    os.makedirs(out_sources, exist_ok=True)
    os.makedirs(out_bytecode, exist_ok=True)
    catalog = []
    for folder, sol in entries(clone_root):
        catalog.append(build_entry(folder, sol, out_sources, out_bytecode))
    for entry in catalog:
        entry["repository_commit"] = PINNED_COMMIT
    with open(OUT_CATALOG, "w", encoding="utf-8") as handle:
        json.dump(catalog, handle, indent=2)
    compiled = sum(1 for e in catalog if e["runtime_bytecode_paths"])
    print(json.dumps({"files": len(catalog), "compiled": compiled, "compile_errors": len(catalog) - compiled}))


if __name__ == "__main__":
    main()
