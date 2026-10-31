"""Recompile the runtime bytecode that a catalog lists, with the solc version it records.

The bytecode files are build outputs and are not committed. This script writes every
runtime contract named in the catalog to the path the catalog gives, using the solc
version recorded for that source file, and fails if solc emits a different set of
runtime contracts than the catalog lists.

Usage: compile_catalog.py <catalog.json> [<catalog.json> ...]
Compilers are taken from ~/.solc-select/artifacts (install with `solc-select install <v>`).
"""
import json
import os
import subprocess
import sys

from repo_paths import resolve

SOLC_DIR = os.path.expanduser("~/.solc-select/artifacts")


def compile_runtimes(source: str, version: str) -> dict:
    solc = os.path.join(SOLC_DIR, f"solc-{version}", f"solc-{version}")
    done = subprocess.run([solc, "--combined-json", "bin-runtime", source],
                          capture_output=True, text=True, check=False)
    if done.returncode != 0:
        raise RuntimeError(f"solc {version} failed on {source}: {done.stderr.strip()[-300:]}")
    contracts = json.loads(done.stdout).get("contracts", {})
    return {key.rsplit(":", 1)[-1]: value["bin-runtime"]
            for key, value in contracts.items() if value.get("bin-runtime")}


def compile_catalog(catalog_path: str) -> dict:
    with open(catalog_path, encoding="utf-8") as handle:
        catalog = json.load(handle)
    written = 0
    for entry in catalog:
        expected = entry.get("runtime_bytecode_paths") or {}
        if not expected:
            continue
        runtimes = compile_runtimes(resolve(entry["source_path"]), entry["solc_version"])
        if set(runtimes) != set(expected):
            raise RuntimeError(f"{entry['contract_id']}: solc emitted {sorted(runtimes)}, "
                               f"catalog lists {sorted(expected)}")
        for name, path in expected.items():
            target = resolve(path)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as handle:
                handle.write(runtimes[name])
            written += 1
    return {"catalog": catalog_path, "runtime_contracts_written": written}


def main() -> None:
    for catalog_path in sys.argv[1:]:
        print(json.dumps(compile_catalog(catalog_path)))


if __name__ == "__main__":
    main()
