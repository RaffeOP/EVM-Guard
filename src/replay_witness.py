"""Replay inputs from a Z3 model of a feasible call-then-write path.

The feasibility query leaves the caller and the call target free, so that it removes only
paths no caller can execute. For replay, a second query fixes the sandbox roles: the
attacker contract is the caller and the call target, the victim is the executing account,
and the externally owned account is the origin. Its model gives the calldata, the call
value and the storage the path reads before the call.

KECCAK256 is uninterpreted in the query, so storage keys built from hashes (mapping and
dynamic-array entries) are recomputed with the real hash of the model's hashed words.
The starting storage is chosen by the solver and need not be reachable from deployment,
so findings confirmed with it are reported separately from default-state confirmations.
"""

from typing import Any, Dict, List, Optional

import z3
from eth_hash.auto import keccak

from replay_sandbox import ATTACKER_ADDRESS, EOA_ADDRESS, VICTIM_ADDRESS
from symbolic_path import ADDRESS_MASK, WORD_BYTES, bv

MAX_CALLDATA_BYTES = 4 + 8 * WORD_BYTES
MAX_CALLVALUE_WEI = 10 * 10 ** 18
# The victim holds 10 ether in the sandbox; a transfer of at most a quarter of that leaves room
# for the re-entrant payout.
MAX_TRANSFER_WEI = 10 ** 18 * 10 // 4
SOLVER_TIMEOUT_MS = 2000


def _address(raw: bytes) -> z3.BitVecRef:
    return bv(int.from_bytes(raw, "big"))


def _role_constraints(state: Any) -> List[z3.BoolRef]:
    constraints = [
        state.env("caller") == _address(ATTACKER_ADDRESS),
        state.env("address") == _address(VICTIM_ADDRESS),
        state.env("origin") == _address(EOA_ADDRESS),
        z3.ULE(state.env("callvalue"), bv(MAX_CALLVALUE_WEI)),
        z3.ULE(state.env("calldatasize"), bv(MAX_CALLDATA_BYTES)),
        z3.UGE(state.env("calldatasize"), bv(4)),
    ]
    target = state.call_operands.get("target")
    if target is not None:
        constraints.append(target & bv(ADDRESS_MASK) == _address(ATTACKER_ADDRESS))
    value = state.call_operands.get("value")
    if value is not None:
        constraints += [z3.UGT(value, bv(0)), z3.ULE(value, bv(MAX_TRANSFER_WEI))]
    return constraints


def _keccak_apps(expr: z3.ExprRef, found: List[z3.ExprRef]) -> None:
    if z3.is_app(expr) and expr.decl().name().startswith("keccak") and expr.num_args() > 0:
        for arg in expr.children():
            _keccak_apps(arg, found)
        if not any(expr.eq(seen) for seen in found):
            found.append(expr)
        return
    for child in expr.children():
        _keccak_apps(child, found)


def real_value(expr: z3.ExprRef, model: z3.ModelRef) -> int:
    """Evaluate expr in the model after replacing each uninterpreted hash by the real KECCAK256."""
    apps: List[z3.ExprRef] = []
    _keccak_apps(expr, apps)
    substitutions = []
    for app in apps:
        words = [z3.substitute(arg, *substitutions) if substitutions else arg for arg in app.children()]
        data = b"".join(model.eval(w, model_completion=True).as_long().to_bytes(WORD_BYTES, "big") for w in words)
        substitutions.append((app, bv(int.from_bytes(keccak(data), "big"))))
    resolved = z3.substitute(expr, *substitutions) if substitutions else expr
    return model.eval(resolved, model_completion=True).as_long()


def _calldata_bytes(state: Any, model: z3.ModelRef, size: int) -> bytes:
    """Lay out the words the path read, in increasing offset order, so the selector comes from the
    word at offset 0 and each argument from its own word."""
    data = bytearray(size)
    for offset in sorted(set(state.calldata_offsets)):
        if offset >= size:
            continue
        value = model.eval(z3.Select(state.calldata, bv(offset)), model_completion=True).as_long()
        chunk = value.to_bytes(WORD_BYTES, "big")[: size - offset]
        data[offset:offset + len(chunk)] = chunk
    return bytes(data)


def witness_inputs(first: Any) -> Optional[Dict[str, Any]]:
    """Calldata, call value and pre-call storage for the sandbox roles, or None if UNSAT."""
    state = first.state
    if state is None:
        return None
    solver = z3.Solver()
    solver.set("timeout", SOLVER_TIMEOUT_MS)
    solver.add(*first.constraints, *_role_constraints(state))
    if solver.check() != z3.sat:
        return None
    model = solver.model()
    declared = model.eval(state.env("calldatasize"), model_completion=True).as_long()
    size = min(max(declared, state.calldata_end), MAX_CALLDATA_BYTES)
    calldata = _calldata_bytes(state, model, size)
    initial = z3.Array("storage_tx", z3.BitVecSort(256), z3.BitVecSort(256))
    storage = {}
    pre_call = state.sloads if state.sloads_at_call is None else state.sloads[:state.sloads_at_call]
    for key in pre_call:
        slot = real_value(key, model)
        storage[slot] = model.eval(z3.Select(initial, key), model_completion=True).as_long()
    return {"calldata": calldata, "callvalue": model.eval(state.env("callvalue"), model_completion=True).as_long(),
            "storage": {slot: value for slot, value in storage.items() if value}}
