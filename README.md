# EVM-Guard

Bytecode-only reentrancy triage for Solidity 0.4–0.5 contracts, with sandbox witness replay.

EVM-Guard builds a control-flow graph from runtime bytecode with an abstract stack dataflow,
flags an external call followed on some path by a storage write with no mutex in between,
excludes calls that forward only the 2300-gas stipend, and replays candidate transactions in a
`py-evm` sandbox. Engine v5 (the default for Solidity 0.4–0.5) does not solve path
conditions; a Z3 `SAT` result only supplies witness parameters for a fixed template. Engine v6
(`run_external_eval.py <catalog> <out> v6`) adds return-site tracking, a Z3 path-feasibility
search under an unprivileged-attacker model, and witness-seeded replay; it also analyses
Solidity 0.8 bytecode, but on 0.4–0.5 benchmarks it reports more false positives than v5.
A finding is a hazard indicator, not a proof of exploitability: on deployed contracts most
flags need manual review (paper, Section "Deployed Contracts").

Author: Devarsh Patel, School of Computer Science and Engineering, Vellore Institute of Technology.

## Reproducing the results

```bash
./reproduce.sh
```

Requires Python 3.12 and `git`. The script installs `requirements-eval.txt` and the solc
compilers, clones SmartBugs-curated and the labeled benchmark at their pinned commits,
rebuilds the bytecode, and runs engine v5 on all five corpora. See
[`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) for the expected numbers and the known
differences from the frozen records, and for the v6, baseline and deployed-contract runs
that the script does not cover.

## Layout

| Path | Contents |
|---|---|
| `src/` | Engine: disassembly, CFG dataflow, hazard checks, Z3 templates, replay oracles |
| `src/eval/` | Catalog builders, evaluation runners, scoring, tables and figures |
| `benchmarks/` | Catalogs and the SolidiFI and synthetic sources (bytecode is rebuilt, not committed) |
| `docs/` | Evaluation protocols, freeze digests and engine manifests |
| `results/` | Archived runs of every engine version and baseline |
| `archive/` | Earlier engine versions (v1, v2), byte copies of v5 and the frozen v6, legacy corpus tools, and an experimental 0.8 attempt |
| `tests/` | Engine v6 unit tests and their fixtures |
| `paper/` | Manuscript sources |

## Licence

MIT (see `LICENSE`).
