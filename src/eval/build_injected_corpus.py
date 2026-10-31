"""Generate the pre-registered injected corpus under docs/INJECTED_EVAL_PROTOCOL.md.

Each file is one Solidity 0.8.20 contract built from a fixed skeleton with a seeded
random choice of identifiers and filler functions. Four groups are generated:

  reentrancy_injected   withdraw() pays with .call before it updates the balance
  dos_injected          a public function loops over a user-growable storage array
  neg_cei               withdraw() updates the balance before its .call (safe order)
  neg_mutex             withdraw() is guarded by a mutex around its .call (safe)
  neg_transfer          withdraw() pays with .transfer, a 2300-gas stipend (cannot re-enter)
  neg_bounded_loop      the loop has a constant bound (no growable exit test)
  neg_clean             no injected pattern

Labels are assigned by construction: a file is labelled with the hazard it injects.
Usage: build_injected_corpus.py  (writes benchmarks/injected/ and benchmarks/injected_catalog.json)
"""
import hashlib
import json
import os
import random
import shutil

from build_heldout_catalog import compile_file, sloc

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_ROOT = os.path.join(REPO, "benchmarks/injected")
OUT_CATALOG = os.path.join(REPO, "benchmarks/injected_catalog.json")
SEED = 20261014
FILES_PER_GROUP = 30
PRAGMA = "pragma solidity 0.8.20;"
GROUP_LABELS = {
    "reentrancy_injected": ["reentrancy"],
    "dos_injected": ["denial_of_service"],
    "neg_cei": [],
    "neg_mutex": [],
    "neg_transfer": [],
    "neg_bounded_loop": [],
    "neg_clean": [],
}
NAME_POOL = ["vault", "pool", "escrow", "bank", "treasury", "locker", "wallet", "fund", "ledger", "safe"]
FILLER_FUNCTIONS = [
    "function ownerOf_() public view returns (address) {{ return owner; }}",
    "function setOwner(address next) public {{ require(msg.sender == owner); owner = next; }}",
    "function totalDeposits() public view returns (uint256) {{ return {tot}; }}",
    "function balanceOf(address who) public view returns (uint256) {{ return {bal}[who]; }}",
]


def sha256_of(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def identifiers(rng: random.Random) -> dict:
    suffix = rng.randrange(1000, 9999)
    return {
        "contract": f"{rng.choice(NAME_POOL).capitalize()}{suffix}",
        "balances": rng.choice(["balances", "credit", "deposits", "shares"]),
        "total": rng.choice(["total", "supply", "reserve"]),
        "owner": "owner",
    }


def base(ids: dict) -> str:
    return f"""{PRAGMA}

contract {ids["contract"]} {{
    address public owner;
    uint256 public {ids["total"]};
    mapping(address => uint256) public {ids["balances"]};

    constructor() {{ owner = msg.sender; }}

    function deposit() public payable {{
        {ids["balances"]}[msg.sender] += msg.value;
        {ids["total"]} += msg.value;
    }}
"""


def withdraw_body(kind: str, ids: dict) -> str:
    bal = ids["balances"]
    tot = ids["total"]
    if kind == "reentrancy_injected":
        return f"""    function withdraw(uint256 amount) public {{
        require({bal}[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call{{value: amount}}("");
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
        (bool ok, ) = msg.sender.call{{value: amount}}("");
        require(ok);
    }}
"""
    if kind == "neg_mutex":
        return f"""    bool private locked;

    function withdraw(uint256 amount) public {{
        require(!locked);
        locked = true;
        require({bal}[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call{{value: amount}}("");
        require(ok);
        {bal}[msg.sender] -= amount;
        {tot} -= amount;
        locked = false;
    }}
"""
    if kind == "neg_transfer":
        return f"""    function withdraw(uint256 amount) public {{
        require({bal}[msg.sender] >= amount);
        payable(msg.sender).transfer(amount);
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
            members[i].code.length;
        }
    }
"""
    if kind == "neg_bounded_loop":
        bound = rng.choice([8, 16, 32])
        return f"""    address[] public members;

    function join() public {{
        if (members.length < {bound}) members.push(msg.sender);
    }}

    function creditAll() public {{
        for (uint256 i = 0; i < {bound}; i++) {{
            if (i < members.length) members[i].code.length;
        }}
    }}
"""
    return ""


def filler(rng: random.Random, ids: dict) -> str:
    count = rng.randrange(0, 3)
    chosen = rng.sample(FILLER_FUNCTIONS, count)
    names = {"bal": ids["balances"], "tot": ids["total"]}
    return "".join(f"\n    {line.format(**names)}\n" for line in chosen)


def render(group: str, index: int) -> tuple:
    rng = random.Random(f"{SEED}:{group}:{index}")
    ids = identifiers(rng)
    body = base(ids)
    if group in ("dos_injected", "neg_bounded_loop"):
        body += loop_body(group, rng)
    elif group == "neg_clean":
        body += ""
    else:
        body += withdraw_body(group, ids)
    body += filler(rng, ids)
    body += "}\n"
    return ids["contract"], body


def build() -> list:
    shutil.rmtree(OUT_ROOT, ignore_errors=True)
    os.makedirs(OUT_ROOT)
    entries = []
    for group, labels in GROUP_LABELS.items():
        for index in range(FILES_PER_GROUP):
            contract, source = render(group, index)
            contract_id = f"{group}__{index:02d}"
            path = os.path.join(OUT_ROOT, f"{contract_id}.sol")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(source)
            entries.append({"contract_id": contract_id, "group": group, "labels": labels,
                            "source_path": os.path.relpath(path, REPO), "source_sha256": sha256_of(path),
                            "sloc": sloc(path), "solc_version": "0.8.20", "contract": contract})
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
