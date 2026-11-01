"""Run Slither and Mythril over the catalogued corpus with timing and timeouts.

Writes one row per (contract, tool, repeat) to a CSV. A timeout is recorded
as status=timeout and never as an unflagged result. Flags are derived from
each tool's own JSON output: Slither flags when a High or Medium impact detector fires (informational checks excluded); Mythril
flags when any issue is reported.
"""
import argparse
import csv
import json
import os
import subprocess
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SLITHER = os.environ.get("SLITHER_BIN", os.path.join(REPO, ".venv", "bin", "slither"))
MYTHRIL = os.environ.get("MYTHRIL_BIN", "myth")
FIELDS = ["contract_id", "dataset", "ground_truth", "tool", "repeat", "status", "flagged", "ms"]


def run_slither(sol_path: str, timeout_s: float) -> tuple:
    report = os.path.join(tempfile.gettempdir(), f"slither_{os.getpid()}.json")
    command = [SLITHER, sol_path, "--json", report, "--disable-color"]
    if os.path.exists(report):
        os.remove(report)
    status, flagged, ms = _run(command, timeout_s, parse=lambda _: None)
    if status != "ok":
        return status, flagged, ms
    try:
        with open(report, encoding="utf-8") as handle:
            return "ok", "yes" if _has_security_finding(json.load(handle)) else "no", ms
    except (OSError, json.JSONDecodeError, KeyError):
        return "error", "", ms


SECURITY_IMPACTS = {"High", "Medium"}


def _has_security_finding(report: dict) -> bool:
    return any(d["impact"] in SECURITY_IMPACTS for d in report["results"]["detectors"])


SECURIFY = os.environ.get("SECURIFY_PYTHON", "python3")
SECURIFY_ROOT = os.environ.get("SECURIFY_ROOT", "")
SOLC_BIN = os.environ.get("SOLC_BIN", "solc-0.8.20")
SOUFFLE_BIN_DIR = os.environ.get("SOUFFLE_BIN_DIR", "")


def run_securify(sol_path: str, timeout_s: float) -> tuple:
    env = dict(os.environ)
    env["PATH"] = SOUFFLE_BIN_DIR + os.pathsep + os.environ["PATH"]
    env["LD_LIBRARY_PATH"] = os.path.join(SECURIFY_ROOT, "securify/staticanalysis/libfunctors")
    command = [SECURIFY, "-m", "securify", sol_path, "--solidity", SOLC_BIN]
    start = time.perf_counter()
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=timeout_s, check=False,
                              env=env, cwd=SECURIFY_ROOT)
    except subprocess.TimeoutExpired:
        return "timeout", "", timeout_s * 1000
    elapsed_ms = (time.perf_counter() - start) * 1000
    combined = done.stdout + done.stderr
    # Securify exits 0 even after a crash, so success is judged from the output.
    if "Traceback" in combined or "GrammarError" in combined or "Error" in combined:
        return "grammar_error", "", elapsed_ms
    return "ok", "yes" if "Severity:" in combined else "no", elapsed_ms


def run_mythril(sol_path: str, timeout_s: float) -> tuple:
    command = [MYTHRIL, "analyze", sol_path, "-o", "json", "-t", "2", "--execution-timeout", str(int(timeout_s) - 10)]
    return _run(command, timeout_s, parse=lambda out: bool(json.loads(out)["issues"]))


def _run(command: list, timeout_s: float, parse) -> tuple:
    env = dict(os.environ, PATH=os.path.join(os.path.dirname(SLITHER)) + os.pathsep + os.environ["PATH"])
    start = time.perf_counter()
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=timeout_s, check=False, env=env)
    except subprocess.TimeoutExpired:
        return "timeout", "", timeout_s * 1000
    elapsed_ms = (time.perf_counter() - start) * 1000
    if parse is None:
        return "ok", "", elapsed_ms
    try:
        return "ok", "yes" if parse(done.stdout) else "no", elapsed_ms
    except (json.JSONDecodeError, KeyError, TypeError):
        return "error", "", elapsed_ms


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", default="benchmarks/benchmark_catalog_external.json")
    parser.add_argument("--out", required=True)
    parser.add_argument("--tool", choices=["slither", "mythril", "securify"], required=True)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--timeout-s", type=float, default=60.0)
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--of", type=int, default=1)
    args = parser.parse_args()
    with open(args.catalog, encoding="utf-8") as handle:
        contracts = json.load(handle)[args.shard::args.of]
    runner = {"slither": run_slither, "mythril": run_mythril, "securify": run_securify}[args.tool]
    with open(args.out, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for contract in contracts:
            truth = "vulnerable" if contract["is_vulnerable"] else "safe"
            for repeat in range(1, args.repeats + 1):
                status, flagged, ms = runner(contract["sol_path"], args.timeout_s)
                writer.writerow({"contract_id": contract["contract_id"], "dataset": contract["dataset"],
                                 "ground_truth": truth, "tool": args.tool, "repeat": repeat,
                                 "status": status, "flagged": flagged, "ms": round(ms, 2)})
                handle.flush()
    print(os.path.abspath(args.out))


if __name__ == "__main__":
    main()
