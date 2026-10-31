# EVM-Guard

Bytecode-only reentrancy triage for Solidity 0.4–0.5 contracts, with sandbox witness replay.

EVM-Guard builds a control-flow graph from runtime bytecode with an abstract stack dataflow,
flags an external call followed on some path by a storage write with no mutex in between,
excludes calls that forward only the 2300-gas stipend, and replays candidate transactions in a
`py-evm` sandbox. Its checks approximate the hazard specifications in the paper; they do not
solve path conditions, and a finding is a hazard indicator, not a proof of exploitability.
A Z3 `SAT` result only supplies witness parameters for a fixed template. Solidity 0.8 bytecode
is out of scope.

Author: Devarsh Patel, School of Computer Science and Engineering, Vellore Institute of Technology.

## Reproducing the results

```bash
./reproduce.sh
```

Requires Python 3.12 and `git`. The script installs `requirements-eval.txt` and the solc
compilers, clones SmartBugs-curated and the labeled benchmark at their pinned commits,
rebuilds the bytecode, and runs engine v5 on all five corpora. See
[`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) for the expected numbers and the known
differences from the frozen records.

## Layout

| Path | Contents |
|---|---|
| `src/` | Engine: disassembly, CFG dataflow, hazard checks, Z3 templates, replay oracles |
| `src/eval/` | Catalog builders, evaluation runners, scoring, tables and figures |
| `tests/` | Unit tests for disassembler and stipend bounds |
| `benchmarks/` | Catalogs and the SolidiFI and synthetic sources (bytecode is rebuilt, not committed) |
| `docs/` | Evaluation protocols, freeze digests and engine manifests |
| `results/` | Archived runs of every engine version and baseline |
| `literature/` | Peer-reviewed taxonomy mapping, literature metadata, and gap resolution matrix |
| `archive/` | Earlier engine versions (v1, v2) and an experimental 0.8 attempt |
| `paper/` | Manuscript sources and compiled PDFs |

## Licence

MIT (see `LICENSE`).
