"""Build the benchmark catalog from SmartBugs-curated, with measured metrics only.

Each source file is compiled with the solc version listed in the dataset's own
versions.csv. Labels come from vulnerabilities.json. SLOC counts non-blank,
non-comment source lines. Instruction counts and cyclomatic complexity are
computed later by the engine from the compiled runtime bytecode.
"""
import csv
import json
import os
import re
import subprocess

from repo_paths import relative

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATASET = os.path.join(REPO, "external/smartbugs-curated")
OUT_DIR = os.path.join(REPO, "benchmarks/external")
CATALOG = os.path.join(REPO, "benchmarks/benchmark_catalog_external.json")
SOLC_TEMPLATE = os.path.expanduser("~/.solc-select/artifacts/solc-{v}/solc-{v}")
COMMENT_PATTERN = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)


def count_sloc(source: str) -> int:
    stripped = COMMENT_PATTERN.sub("", source)
    return sum(1 for line in stripped.splitlines() if line.strip())


def compile_runtime(sol_path: str, version: str) -> dict:
    solc = SOLC_TEMPLATE.format(v=version)
    done = subprocess.run([solc, "--combined-json", "bin-runtime", sol_path],
                          capture_output=True, text=True, check=False)
    if done.returncode != 0:
        return {"error": done.stderr.strip()[-300:]}
    contracts = json.loads(done.stdout)["contracts"]
    return {name.split(":")[-1]: info["bin-runtime"] for name, info in contracts.items()
            if info.get("bin-runtime")}


def load_versions() -> dict:
    with open(os.path.join(DATASET, "versions.csv"), newline="", encoding="utf-8") as handle:
        return {row["file"]: row["compiled version"] for row in csv.DictReader(handle)}


def build() -> list:
    versions = load_versions()
    with open(os.path.join(DATASET, "vulnerabilities.json"), encoding="utf-8") as handle:
        labels = json.load(handle)
    os.makedirs(OUT_DIR, exist_ok=True)
    catalog = []
    for item in labels:
        rel = item["path"]
        sol_path = os.path.join(DATASET, rel)
        with open(sol_path, encoding="utf-8", errors="replace") as handle:
            source = handle.read()
        version = versions[rel]
        compiled = compile_runtime(sol_path, version)
        entry_id = rel.replace("dataset/", "").replace("/", "__").replace(".sol", "")
        bin_paths = {}
        if "error" not in compiled:
            for cname, runtime in compiled.items():
                path = os.path.join(OUT_DIR, f"{entry_id}__{cname}.bin-runtime")
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write(runtime)
                bin_paths[cname] = relative(path)
        catalog.append({
            "contract_id": entry_id,
            "source_path": relative(sol_path),
            "dataset_category_dir": rel.split("/")[1],
            "labels": sorted({v["category"] for v in item["vulnerabilities"]}),
            "label_lines": item["vulnerabilities"],
            "upstream_source": item.get("source"),
            "solc_version": version,
            "sloc": count_sloc(source),
            "compile_error": compiled.get("error"),
            "runtime_bytecode_paths": bin_paths,
        })
    with open(CATALOG, "w", encoding="utf-8") as handle:
        json.dump(catalog, handle, indent=2)
    return catalog


def main() -> None:
    catalog = build()
    ok = sum(1 for c in catalog if not c["compile_error"] and c["runtime_bytecode_paths"])
    print(json.dumps({"files": len(catalog), "compiled_with_runtime_code": ok,
                      "runtime_contracts": sum(len(c["runtime_bytecode_paths"]) for c in catalog)}))


if __name__ == "__main__":
    main()
