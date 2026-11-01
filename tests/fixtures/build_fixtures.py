"""Compile the fixture contracts with solc-select binaries and write each runtime bytecode as .hex.

Run from the repository root: python tests/fixtures/build_fixtures.py
"""
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SOLC = os.path.expanduser("~/.solc-select/artifacts/solc-{v}/solc-{v}")
PRAGMA = re.compile(r"pragma solidity (\d+\.\d+\.\d+);")


def build(source: str) -> None:
    path = os.path.join(HERE, source)
    with open(path, encoding="utf-8") as handle:
        version = PRAGMA.search(handle.read()).group(1)
    output = subprocess.run([SOLC.format(v=version), "--bin-runtime", path],
                            capture_output=True, text=True, check=True).stdout
    runtime = output.strip().splitlines()[-1]
    with open(path.replace(".sol", ".hex"), "w", encoding="utf-8") as handle:
        handle.write(runtime + "\n")


def main() -> None:
    for source in sorted(os.listdir(HERE)):
        if source.endswith(".sol"):
            build(source)


if __name__ == "__main__":
    main()
