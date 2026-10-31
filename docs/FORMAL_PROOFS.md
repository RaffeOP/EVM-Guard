# EVM-Guard: Formal Proofs and Semantic Specifications

This document provides the formal semantic specifications, abstract interpretation domain definitions, convergence proofs, and gas-stipend bounds for **EVM-Guard: Bytecode-Level Semantic Hazard Triage and State-Falsifiable Sandbox Replay for Ethereum Smart Contracts**.

---

## 1. Formal Specification of Abstract Domains

The abstract interpretation domain is structured as a bounded product lattice over stack slots:

$$\mathcal{L} = \langle \mathbb{Z}_{\bot} \times \mathcal{P}(\mathrm{DivSites}) \times \mathbb{B}^3 \times \mathbb{N}_{\bot}, \sqsubseteq, \sqcup, \sqcap, \top, \bot \rangle$$

The join operator pointwise merges constant values and unions provenance sets:

$$v_1 \sqcup v_2 = \langle c_1 \cap c_2, \mathrm{div}_1 \cup \mathrm{div}_2, \tau_1 \lor \tau_2, \max(u_1, u_2) \rangle$$

### Theorem 1 (Termination and Soundness)
The abstract worklist fixpoint algorithm terminates in a finite number of iterations:

$$k \le |\mathcal{B}| \times 1024 \times h(\mathcal{V})$$

where $h(\mathcal{V}) \le 5$ is the maximum chain height of the abstract value domain $\mathcal{V}$, and $|\mathcal{B}|$ is the number of basic blocks in the control flow graph.

#### Proof:
Because the abstract stack depth is strictly bounded by 1,024 words (enforced by the EVM execution model) and each stack element belongs to a finite-height lattice where:
1. Constants transition to $\bot$ monotonically (chain height 2),
2. Taint flags monotonically join via boolean disjunction (chain height 2),
3. Provenance division site sets monotonically join via set union over finite instruction addresses (chain height $\le |\mathrm{DivSites}|$),
4. Upper value bounds monotonically increase via $\max$ up to $2^{256}-1$ or widen after a fixed threshold,

the product lattice satisfies the Ascending Chain Condition (ACC). By Tarski's fixpoint theorem, the worklist iteration monotonically converges to the least fixpoint in finite steps. $\blacksquare$

---

## 2. Gas-Stipend Bound Proof

### Proposition 1 (Gas-Stipend Bound on State Modification)
An external call forwarding a gas bound $g \le 2300$ cannot execute state modifications (`SSTORE`) in the callee sub-execution context.

#### Proof:
Under EVM operational semantics (Yellow Paper, Berlin/London/Cancun specifications), executing an `SSTORE` instruction requires:
- A minimum base gas cost of 5,000 gas (to update an existing non-zero storage slot),
- 20,000 gas when initializing a zero-valued slot to non-zero,
- 2,100 gas for cold storage access under EIP-2929 rules.

In addition, under EIP-2200 and EIP-2929 rules, an explicit sentry check halts execution with an out-of-gas error whenever remaining gas is $\le 2300$. Because $2300 < 5000$ and remaining gas in the sub-call cannot exceed 2,300, any sub-execution context initialized with at most 2,300 gas will immediately revert with an out-of-gas error upon attempting an `SSTORE`. Therefore, stipend-limited external calls cannot produce reentrant state mutations. $\blacksquare$

---

## 3. Abstract Stack Transfer Functions for Core Opcodes

The table below formalizes the abstract transfer functions $\llbracket \mathrm{op} \rrbracket : \mathcal{S} \to \mathcal{S}$ for core EVM operations over the stack state $\sigma = [v_0, v_1, \dots, v_n]$:

| Opcode | Operand Pop | Abstract Stack Push Result |
| :--- | :--- | :--- |
| `PUSHn c` | None | $\langle c, \mathrm{False}, \mathrm{False}, \mathrm{False}, \bot, c \rangle$ |
| `CALLER` | None | $\langle \bot, \mathrm{False}, \mathrm{True}, \mathrm{False}, \bot, 2^{160}-1 \rangle$ |
| `ORIGIN` | None | $\langle \bot, \mathrm{False}, \mathrm{True}, \mathrm{False}, \bot, 2^{160}-1 \rangle$ |
| `CALLDATALOAD` | $\mathrm{offset}$ | $\langle \bot, \mathrm{offset} \ge 4, \mathrm{False}, \mathrm{False}, \bot, 2^{256}-1 \rangle$ |
| `SLOAD` | $\mathrm{slot}$ | $\langle \bot, \mathrm{False}, \mathrm{False}, \mathrm{True}, \mathrm{slot}.c, 2^{256}-1 \rangle$ |
| `ISZERO` | $x$ | $\langle x.c \neq \bot ? (x.c == 0 ? 1 : 0) : \bot, \tau_x, \dots, 1 \rangle$ |
| `MUL` | $x, y$ | $\langle x.c \times y.c \pmod{2^{256}}, \tau_x \lor \tau_y, \dots, \min(u(x) \cdot u(y), 2^{256}-1) \rangle$ |
| `AND` | $x, y$ | $\langle x.c \land y.c, \tau_x \lor \tau_y, \dots, \min(u(x), u(y)) \rangle$ |

---

## 4. Benchmark Dataset Integrity and Cryptographic Digests

All benchmark datasets, catalog mappings, baseline execution receipts, and scoring scripts are preserved with cryptographic SHA-256 integrity digests in `docs/`:
- `docs/FINAL_V5_EVAL_FREEZE.sha256`
- `docs/FINAL_V5_ENGINE_MANIFEST.sha256`
- `docs/HELDOUT_EVAL_FREEZE.sha256`
- `docs/HELDOUT2_EVAL_FREEZE.sha256`

These digests ensure deterministic, independent verification across heterogeneous research platforms.
