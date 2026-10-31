"""Run EVM-Guard on the SmartBugs-curated catalog under docs/EXTERNAL_EVAL_PROTOCOL.md.

Writes one row per runtime contract to results/external/evm_guard_contracts.csv and
one row per file to results/external/evm_guard_files.csv. Nothing is simulated:
every value comes from analyze_bytecode, replay_in_sandbox or the catalog.
"""
import csv
import json
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.join(REPO, "src", "eval"))

from exploit_synthesizer import ExploitSynthesizer  # noqa: E402
from repo_paths import resolve  # noqa: E402
from symbolic_engine import SymbolicEVMInterpreter  # noqa: E402

CATALOG = os.path.join(REPO, "benchmarks/benchmark_catalog_external.json")
OUT_DIR = os.path.join(REPO, "results/external")
SWC_TO_CATEGORY = {
    "SWC-107": "reentrancy",
    "SWC-101": "arithmetic",
    "SWC-128": "denial_of_service",
    "SWC-112": "access_control",
    "SWC-124": "access_control",
}


def is_hex(text: str) -> bool:
    """True when the runtime code decodes as hexadecimal. Solc leaves library placeholders in code that does not."""
    body = text[2:] if text.startswith("0x") else text
    try:
        bytes.fromhex(body)
    except ValueError:
        return False
    return True


def analyze_contract(engine, synthesizer, name: str, runtime_hex: str) -> dict:
    if not is_hex(runtime_hex):
        raise ValueError("runtime bytecode is not hexadecimal (unlinked library placeholder)")
    start = time.perf_counter()
    report = engine.analyze_bytecode(name, runtime_hex, target_swc=None)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    findings = report.get("findings", [])
    selectors = report.get("dynamic_selectors", [])
    swcs = sorted({f.get("swc", "") for f in findings})
    confirmed = []
    for finding in findings:
        payload = synthesizer.synthesize_payload_for_finding(finding, selectors)
        replay = synthesizer.replay_in_sandbox(payload, runtime_bytecode_hex=runtime_hex)
        if replay["replay_verified"]:
            confirmed.append(finding.get("swc", ""))
    return {
        "latency_ms": round(elapsed_ms, 3),
        "instruction_count": report.get("instruction_count", 0),
        "cyclomatic_complexity": report.get("cyclomatic_complexity", 0),
        "selectors": len(selectors),
        "finding_swcs": ";".join(swcs),
        "confirmed_swcs": ";".join(sorted(set(confirmed))),
    }


def main() -> None:
    catalog_path = sys.argv[1] if len(sys.argv) > 1 else CATALOG
    out_dir = sys.argv[2] if len(sys.argv) > 2 else OUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    with open(catalog_path, encoding="utf-8") as handle:
        catalog = json.load(handle)
    engine = SymbolicEVMInterpreter()
    synthesizer = ExploitSynthesizer()
    contract_rows, file_rows = [], []
    for entry in catalog:
        flagged, confirmed, latency = set(), set(), 0.0
        for cname, path in entry["runtime_bytecode_paths"].items():
            with open(resolve(path), encoding="utf-8") as handle:
                runtime_hex = handle.read().strip()
            try:
                result = analyze_contract(engine, synthesizer, cname, runtime_hex)
                status = "ok"
            except Exception as error:  # record and continue; every contract is reported
                result = {"latency_ms": 0.0, "instruction_count": 0, "cyclomatic_complexity": 0,
                          "selectors": 0, "finding_swcs": "", "confirmed_swcs": "",
                          "error": f"{type(error).__name__}: {error}"[:200]}
                status = "error"
            contract_rows.append({"contract_id": entry["contract_id"], "runtime_contract": cname,
                                  "status": status, **result})
            latency += result["latency_ms"]
            flagged |= {SWC_TO_CATEGORY[s] for s in result["finding_swcs"].split(";") if s in SWC_TO_CATEGORY}
            confirmed |= {SWC_TO_CATEGORY[s] for s in result["confirmed_swcs"].split(";") if s in SWC_TO_CATEGORY}
        file_rows.append({"contract_id": entry["contract_id"], "labels": ";".join(entry["labels"]),
                          "sloc": entry["sloc"], "flagged_categories": ";".join(sorted(flagged)),
                          "confirmed_categories": ";".join(sorted(confirmed)),
                          "latency_ms": round(latency, 3)})
    for name, rows in (("evm_guard_contracts.csv", contract_rows), ("evm_guard_files.csv", file_rows)):
        fields = sorted({k for row in rows for k in row}, key=lambda k: list(rows[0]).index(k) if k in rows[0] else 99)
        with open(os.path.join(out_dir, name), "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    print(json.dumps({"files": len(file_rows), "contracts": len(contract_rows),
                      "errors": sum(r["status"] == "error" for r in contract_rows)}))


if __name__ == "__main__":
    main()
