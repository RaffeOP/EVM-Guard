"""Generate the fresh injected corpus for Solidity 0.5.12, under docs/INJECTED05_EVAL_PROTOCOL.md.

Same families and skeletons as src/eval/build_injected_corpus.py (frozen for the 0.8.20 run),
written in Solidity 0.5 syntax and with a new seed, so the corpus is not the one already
evaluated. Groups and labels are the same as the 0.8 corpus.
Usage: build_injected_corpus_05.py   (writes benchmarks/injected05/ and benchmarks/injected05_catalog.json)
"""
import json
import os
import random
import shutil

from build_heldout_catalog import compile_file, sloc
from build_injected_corpus import GROUP_LABELS, identifiers, sha256_of

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_ROOT = os.path.join(REPO, "benchmarks/injected05")
OUT_CATALOG = os.path.join(REPO, "benchmarks/injected05_catalog.json")
SEED = 20261015
FILES_PER_GROUP = 30
SOLC_VERSION = "0.5.12"
PRAGMA = f"pragma solidity {SOLC_VERSION};"
FILLER_FUNCTIONS = [
    "function ownerOf_() public view returns (address) {{ return owner; }}",
    "function setOwner(address next) public {{ require(msg.sender == owner); owner = next; }}",
    "function totalDeposits() public view returns (uint256) {{ return {tot}; }}",
    "function balanceOf(address who) public view returns (uint256) {{ return {bal}[who]; }}",
]


def base(ids: dict) -> str:
    return f"""{PRAGMA}

contract {ids["contract"]} {{
    address public owner;
    uint256 public {ids["total"]};
    mapping(address => uint256) public {ids["balances"]};

    constructor() public {{ owner = msg.sender; }}

    function deposit() public payable {{
        {ids["balances"]}[msg.sender] += msg.value;
        {ids["total"]} += msg.value;
    }}
"""


def withdraw_body(kind: str, ids: dict) -> str:
    bal, tot = ids["balances"], ids["total"]
    if kind == "reentrancy_injected":
        return f"""    function withdraw(uint256 amount) public {{
        require({bal}[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call.value(amount)("");
        require(ok);
        {bal}[msg.sender] -= amount;
        {tot} -= amount;
    }}
"""
    if kind == "neg_cei":
        return f"""    function withdraw(uint256 amount) public {{
        require({bal}[msg.sender] >= amount);
        {bal}[msg.sender] -= amount;
        {tot} -= amount;
        (bool ok, ) = msg.sender.call.value(amount)("");
        require(ok);
    }}
"""
    if kind == "neg_mutex":
        return f"""    bool private locked;

    function withdraw(uint256 amount) public {{
        require(!locked);
        locked = true;
        require({bal}[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call.value(amount)("");
        require(ok);
        {bal}[msg.sender] -= amount;
        {tot} -= amount;
        locked = false;
    }}
"""
    if kind == "neg_transfer":
        return f"""    function withdraw(uint256 amount) public {{
        require({bal}[msg.sender] >= amount);
        msg.sender.transfer(amount);
        {bal}[msg.sender] -= amount;
        {tot} -= amount;
    }}
"""
    return ""


def loop_body(kind: str, rng: random.Random) -> str:
    if kind == "dos_injected":
        return """    address[] public members;

    function join() public {
        members.push(msg.sender);
    }

    function creditAll() public {
        for (uint256 i = 0; i < members.length; i++) {
            members[i].balance;
        }
    }
"""
    bound = rng.choice([8, 16, 32])
    return f"""    address[] public members;

    function join() public {{
        if (members.length < {bound}) members.push(msg.sender);
    }}

    function creditAll() public {{
        for (uint256 i = 0; i < {bound}; i++) {{
            if (i < members.length) members[i].balance;
        }}
    }}
"""


def filler(rng: random.Random, ids: dict) -> str:
    chosen = rng.sample(FILLER_FUNCTIONS, rng.randrange(0, 3))
    names = {"bal": ids["balances"], "tot": ids["total"]}
    return "".join(f"\n    {line.format(**names)}\n" for line in chosen)


def render(group: str, index: int) -> tuple:
    rng = random.Random(f"{SEED}:{group}:{index}")
    ids = identifiers(rng)
    body = base(ids)
    if group in ("dos_injected", "neg_bounded_loop"):
        body += loop_body(group, rng)
    elif group != "neg_clean":
        body += withdraw_body(group, ids)
    body += filler(rng, ids) + "}\n"
    return ids["contract"], body


def build() -> list:
    shutil.rmtree(OUT_ROOT, ignore_errors=True)
    os.makedirs(OUT_ROOT)
    entries = []
    for group, labels in GROUP_LABELS.items():
        for index in range(FILES_PER_GROUP):
            _, source = render(group, index)
            contract_id = f"{group}__{index:02d}"
            path = os.path.join(OUT_ROOT, f"{contract_id}.sol")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(source)
            entries.append({"contract_id": contract_id, "group": group, "labels": labels,
                            "source_path": os.path.relpath(path, REPO), "source_sha256": sha256_of(path),
                            "sloc": sloc(path), "solc_version": SOLC_VERSION})
    return entries


def compile_all(entries: list) -> list:
    for entry in entries:
        version, runtimes, error = compile_file(os.path.join(REPO, entry["source_path"]))
        paths = {}
        for name, runtime_hex in (runtimes or {}).items():
            path = os.path.join(OUT_ROOT, f"{entry['contract_id']}__{name}.bin-runtime")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(runtime_hex)
            paths[name] = os.path.relpath(path, REPO)
        entry["solc_version"] = version
        entry["compile_error"] = error or ("" if paths else "no runtime bytecode")
        entry["runtime_bytecode_paths"] = paths
    return entries


def parse_args() -> tuple:
    """Defaults reproduce the frozen corpus. Optional: <seed> <output-dir> <catalog-path>."""
    import sys
    args = sys.argv[1:]
    seed = int(args[0]) if len(args) > 0 else SEED
    out_root = os.path.join(REPO, args[1]) if len(args) > 1 else OUT_ROOT
    catalog = os.path.join(REPO, args[2]) if len(args) > 2 else OUT_CATALOG
    return seed, out_root, catalog


def main() -> None:
    global SEED, OUT_ROOT, OUT_CATALOG
    SEED, OUT_ROOT, OUT_CATALOG = parse_args()
    entries = compile_all(build())
    with open(OUT_CATALOG, "w", encoding="utf-8") as handle:
        json.dump(entries, handle, indent=2)
    compiled = sum(1 for e in entries if e["runtime_bytecode_paths"])
    print(json.dumps({"files": len(entries), "compiled": compiled}))


if __name__ == "__main__":
    main()
