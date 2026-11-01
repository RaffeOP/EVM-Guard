"""Run eThor (smartbugs/ethor:2023) on the runtime bytecode of a catalog.

eThor (Schneidewind et al., CCS 2020) checks single-entrancy on EVM bytecode and prints
`<file> secure`, `insecure` or `unknown`. The authors' download links were dead on
2026-11-01, so the SmartBugs image is used, with the SmartBugs command line. The image is
amd64 and runs under emulation on the arm64 evaluation machine, so each contract gets 120 s
instead of the 60 s given to the native tools. A file is flagged for reentrancy if any of its
runtime contracts is reported insecure. Output has the schema of run_external_baselines.py.

eThor is a JVM program that peaks at about 1.6 GB per contract, so at most three shards run
at once in a 6 GB Docker VM; with four shards in 4 GB, contracts that finish alone in 25 s were
killed and recorded without a verdict. Files without runtime code get status no_bytecode;
for runs without a verdict the last line of eThor's output is kept in raw_findings.

Usage: run_ethor.py --catalog <catalog> --out-dir <dir> [--shard i --of n]
"""
import argparse
import csv
import json
import os
import subprocess
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IMAGE = "smartbugs/ethor:2023"
TIMEOUT_S = 120
ETHOR_FLAGS = "--prune-strategy=aggressive --predicate-inlining-strategy=linear --preanalysis -v"
VERDICTS = ("insecure", "secure", "unknown")
MAX_REASON = 160


def start_container(name: str) -> None:
    subprocess.run(["docker", "rm", "-f", name], capture_output=True, check=False)
    subprocess.run(["docker", "run", "-d", "--platform", "linux/amd64", "--name", name,
                    "-v", f"{REPO}:/repo:ro", IMAGE, "sleep", "infinity"], capture_output=True, check=True)


def run_contract(container: str, path: str) -> tuple:
    """Return (status, verdict, milliseconds) for one runtime bytecode file."""
    command = ["docker", "exec", container, "sh", "-c",
               f"timeout {TIMEOUT_S} ethor-with-reconstruction /repo/{path} {ETHOR_FLAGS}"]
    start = time.perf_counter()
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=TIMEOUT_S + 30, check=False)
    except subprocess.TimeoutExpired:
        return "timeout", "", TIMEOUT_S * 1000.0
    elapsed = (time.perf_counter() - start) * 1000.0
    lines = [line.strip() for line in done.stdout.splitlines() if line.strip()]
    verdict = next((line.split()[-1] for line in reversed(lines) if line.split()[-1] in VERDICTS), "")
    if done.returncode == 124:
        return "timeout", "", elapsed
    if verdict:
        return "ok", verdict, elapsed
    output = [line.strip() for line in (done.stdout + done.stderr).splitlines() if line.strip()]
    reason = output[-1][:MAX_REASON] if output else f"exit {done.returncode}"
    return "error", "error: " + reason.replace(",", " ").replace(";", " "), elapsed


def is_linked(path: str) -> bool:
    """False for runtime code with unlinked library placeholders, which EVM-Guard also skips."""
    with open(os.path.join(REPO, path), encoding="utf-8") as handle:
        body = handle.read().strip()
    try:
        bytes.fromhex(body[2:] if body.startswith("0x") else body)
    except ValueError:
        return False
    return True


def file_status(statuses: list) -> str:
    if not statuses:
        return "no_bytecode"
    if all(s == "ok" for s in statuses):
        return "ok"
    return "timeout" if "timeout" in statuses else "error"


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
    container = f"ethor_shard_{os.getpid()}"
    start_container(container)
    out = os.path.join(args.out_dir, f"ethor_files_{args.shard}.csv")
    fields = ["contract_id", "labels", "status", "flagged_categories", "latency_ms", "raw_findings"]
    try:
        with open(out, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for entry in catalog:
                paths = entry["runtime_bytecode_paths"]
                linked = {n: p for n, p in paths.items() if is_linked(p)}
                results = [run_contract(container, p) for p in linked.values()]
                verdicts = [verdict for _, verdict, _ in results]
                skipped = "".join(f";unlinked={n}" for n in paths if n not in linked)
                writer.writerow({"contract_id": entry["contract_id"], "labels": ";".join(entry["labels"]),
                                 "status": file_status([s for s, _, _ in results]),
                                 "flagged_categories": "reentrancy" if "insecure" in verdicts else "",
                                 "latency_ms": round(sum(ms for _, _, ms in results), 2),
                                 "raw_findings": ";".join(v or "-" for v in verdicts) + skipped})
                handle.flush()
    finally:
        subprocess.run(["docker", "rm", "-f", container], capture_output=True, check=False)
    print(out)


if __name__ == "__main__":
    main()
