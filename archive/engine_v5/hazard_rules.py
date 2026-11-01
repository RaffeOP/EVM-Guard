"""Hazard checks over a FlowGraph (CFG reachability, dominance and dataflow patterns).

Each check returns evidence for one finding or None. Evidence names the
program points involved, so the replay oracle can target them. The checks do
not solve path conditions.
"""

from typing import Any, Dict, List, Optional, Set

from engine_options import FULL_ENGINE, EngineOptions
from evm_dataflow import FlowGraph, value_bound
from evm_regions import Dominance, loop_exit_jumpis, natural_loops, reach_within

STIPEND_GAS = 2300
MUTEX_SET_VALUES = (1, 2)
MUTEX_RESET_VALUES = (0, 1)


def dominates_event(dominance: Dominance, earlier: Dict[str, Any], later: Dict[str, Any]) -> bool:
    if earlier["block"] == later["block"]:
        return earlier["order"] < later["order"]
    return dominance.block_dominates(earlier["block"], later["block"])


def reaches_event(graph: FlowGraph, start: Dict[str, Any], target: Dict[str, Any], scope: Set[int]) -> bool:
    if target["block"] == start["block"] and target["order"] > start["order"]:
        return True
    return target["block"] in reach_within(graph, start["block"], scope)


def events_of(graph: FlowGraph, kind: str) -> List[Dict[str, Any]]:
    return [event for event in graph.events if event["kind"] == kind]


def check_reentrancy(graph: FlowGraph, dominance: Dominance,
                     scopes: Dict[str, Set[int]], options: EngineOptions = FULL_ENGINE) -> Optional[Dict[str, Any]]:
    """SWC-107: a CALL that can re-enter, followed on some path by an SSTORE, with no mutex around it."""
    stores = events_of(graph, "sstore")
    for call in events_of(graph, "call"):
        if call["op"] not in ("CALL", "CALLCODE") or _excluded_by_stipend(call, options):
            continue
        for selector, scope in scopes.items():
            if call["block"] not in scope:
                continue
            later = [s for s in stores if s["block"] in scope and reaches_event(graph, call, s, scope)]
            if not later or _mutex_protected(graph, dominance, call, scope, stores, options):
                continue
            return {"block": call["block"], "call_pc": call["pc"], "store_pc": later[0]["pc"], "scope": selector}
    return None


def _excluded_by_stipend(call: Dict[str, Any], options: EngineOptions) -> bool:
    """A call that forwards at most the stipend cannot re-enter, so the check does not report it."""
    return options.should_apply_stipend_bound and _is_stipend_only(call, options)


def _is_stipend_only(call: Dict[str, Any], options: EngineOptions = FULL_ENGINE) -> bool:
    """A call whose gas is at most the stipend. Without bound propagation, only a constant gas operand counts."""
    gas = call["gas"]
    bound = value_bound(gas) if options.should_propagate_gas_bounds else gas.const
    return bound is not None and bound <= STIPEND_GAS


def _precedes(graph: FlowGraph, dominance: Dominance, earlier: Dict[str, Any], later: Dict[str, Any],
              scope: Set[int], options: EngineOptions) -> bool:
    """Whether an earlier event guards a later one. The check requires dominance. The ablation
    accepts any earlier event that reaches the later one inside the same function scope."""
    if options.should_require_mutex_dominance:
        return dominates_event(dominance, earlier, later)
    return reaches_event(graph, earlier, later, scope)


def _mutex_protected(graph: FlowGraph, dominance: Dominance, call: Dict[str, Any],
                     scope: Set[int], stores: List[Dict[str, Any]], options: EngineOptions) -> bool:
    """A lock: constant-valued set and reset, or a slot-based lock (see _slot_lock_protected)."""
    if options.should_recognise_constant_mutex and _constant_mutex_protected(
            graph, dominance, call, scope, stores, options):
        return True
    return options.should_recognise_slot_mutex and _slot_lock_protected(
        graph, dominance, call, scope, stores, options)


def _constant_mutex_protected(graph: FlowGraph, dominance: Dominance, call: Dict[str, Any],
                              scope: Set[int], stores: List[Dict[str, Any]], options: EngineOptions) -> bool:
    """Constant-valued lock: a write of 1 or 2 before the call, a storage-derived branch before it,
    and a reset to 0 or 1 reachable after it."""
    guards = [s for s in stores if s["value"].const in MUTEX_SET_VALUES
              and _precedes(graph, dominance, s, call, scope, options)]
    checks = [e for e in events_of(graph, "jumpi")
              if e["cond"].from_storage and _precedes(graph, dominance, e, call, scope, options)]
    resets = [s for s in stores if s["value"].const in MUTEX_RESET_VALUES
              and reaches_event(graph, call, s, scope)]
    return bool(guards and checks and resets)


def _slot_lock_protected(graph: FlowGraph, dominance: Dominance, call: Dict[str, Any],
                         scope: Set[int], stores: List[Dict[str, Any]], options: EngineOptions) -> bool:
    """A lock on a simple storage variable: a write to slot S before the call, a branch that reads S
    before the call, and a write to S after it. Packed booleans are written through masks, so their
    values are not constants, but the slot identifies the variable."""
    checks = [e for e in events_of(graph, "jumpi") if _precedes(graph, dominance, e, call, scope, options)]
    for guard in stores:
        slot = guard["slot"].const
        if slot is None or not _precedes(graph, dominance, guard, call, scope, options):
            continue
        read_before = any(e["cond"].storage_slot == slot for e in checks)
        reset_after = any(s["slot"].const == slot and reaches_event(graph, call, s, scope) for s in stores)
        if read_before and reset_after:
            return True
    return False


def check_truncation(graph: FlowGraph) -> Optional[Dict[str, Any]]:
    """SWC-101: a DIV result consumed by a MUL or stored by an SSTORE on the same dataflow path."""
    for mul in events_of(graph, "mul"):
        if mul["div_sites"]:
            return {"div_pc": min(mul["div_sites"]), "consumer_pc": mul["pc"], "consumer": "MUL"}
    for store in events_of(graph, "sstore"):
        if store["value"].div_sites:
            return {"div_pc": min(store["value"].div_sites), "consumer_pc": store["pc"], "consumer": "SSTORE"}
    return None


def check_delegatecall_taint(graph: FlowGraph, dominance: Dominance) -> Optional[Dict[str, Any]]:
    """SWC-112: DELEGATECALL whose target derives from calldata and is not guarded by a CALLER check."""
    callers = events_of(graph, "caller")
    for call in events_of(graph, "delegatecall"):
        target = call["target"]
        if target.const is not None or not target.from_calldata:
            continue
        if any(dominates_event(dominance, guard, call) for guard in callers):
            continue
        return {"block": call["block"], "delegatecall_pc": call["pc"]}
    return None


def check_proxy_collision(graph: FlowGraph, has_erc1967_slot: bool) -> Optional[Dict[str, Any]]:
    """SWC-124: a DELEGATECALL whose target is an EIP-1967 slot or a storage read (proxy dispatch)."""
    for call in events_of(graph, "delegatecall"):
        if has_erc1967_slot or call["target"].from_storage:
            return {"block": call["block"], "delegatecall_pc": call["pc"],
                    "proxy_pattern": "eip1967" if has_erc1967_slot else "storage-target"}
    return None


def check_unbounded_loop(graph: FlowGraph, dominance: Dominance,
                         scopes: Dict[str, Set[int]]) -> Optional[Dict[str, Any]]:
    """SWC-128: a loop exit branch on a storage read, inside a public function with no CALLER guard."""
    jumpi_by_block = {event["block"]: event for event in events_of(graph, "jumpi")}
    callers = events_of(graph, "caller")
    for header, body in natural_loops(graph, dominance):
        if any(dominance.block_dominates(guard["block"], header) for guard in callers):
            continue
        selectors = [sel for sel, scope in scopes.items() if header in scope and sel]
        if not selectors:
            continue
        for block in loop_exit_jumpis(graph, body):
            condition = jumpi_by_block[block]["cond"]
            if condition.from_storage:
                return {"block": header, "loop_header_pc": header, "loop_slot": condition.storage_slot,
                        "function_selectors": selectors}
    return None


def check_oracle_collapse(instructions: List[Any]) -> Optional[Dict[str, Any]]:
    """SWC-114 (not scored): a division over at least two storage reads in a view-like region with no
    state write, external call or timestamp. A heuristic, not a dataflow proof."""
    names = [inst.name for inst in instructions]
    sloads = names.count("SLOAD")
    blocked = {"SSTORE", "CALL", "CALLCODE", "DELEGATECALL", "TIMESTAMP"}
    if "DIV" in names and sloads >= 2 and not blocked.intersection(names):
        return {"sload_count": sloads}
    return None
