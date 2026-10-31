"""Run an analyser command repeatedly with a hard timeout and report timing.

Each run is a fresh subprocess. A run that exceeds the timeout is recorded as
a timeout (not as a missed detection) so the two can be reported separately.
"""
import argparse
import json
import shlex
import statistics
import subprocess
import time

TIMEOUT_MARKER = "TIMEOUT"


def run_once(command: list, timeout_s: float) -> dict:
    start = time.perf_counter()
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout_s, check=False)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {"status": "ok" if completed.returncode == 0 else f"exit_{completed.returncode}", "ms": elapsed_ms, "stdout": completed.stdout}
    except subprocess.TimeoutExpired:
        return {"status": TIMEOUT_MARKER, "ms": timeout_s * 1000, "stdout": ""}


def summarise(runs: list) -> dict:
    times = [r["ms"] for r in runs]
    quartiles = statistics.quantiles(times, n=4, method="inclusive") if len(times) >= 2 else [times[0]] * 3
    return {
        "runs": len(runs),
        "timeouts": sum(1 for r in runs if r["status"] == TIMEOUT_MARKER),
        "median_ms": statistics.median(times),
        "iqr_ms": [quartiles[0], quartiles[2]],
        "min_ms": min(times),
        "max_ms": max(times),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", required=True, help="command to run; the contract path is appended")
    parser.add_argument("--target", required=True)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--timeout-s", type=float, default=60.0)
    args = parser.parse_args()
    command = shlex.split(args.command) + [args.target]
    runs = [run_once(command, args.timeout_s) for _ in range(args.repeats)]
    print(json.dumps(summarise(runs), indent=2))


if __name__ == "__main__":
    main()
