"""Z3 feasibility of reentrancy paths over the context-sensitive CFG.

A reentrancy candidate is an external call followed, in the same function, by a storage
write. Two questions are sent to Z3:

1. Can the transaction execute from the dispatcher through the call to the write? The
   search runs symbolic execution along CFG paths and prunes a branch as soon as its
   path condition is unsatisfiable.
2. Can a re-entrant invocation, started from the storage state at the call, reach the
   same call again, or read in another public function a slot that the write updates?
   A lock that rejects re-entry makes this query unsatisfiable, whatever its encoding.

Only an UNSAT answer removes a candidate. A search that runs out of budget, or a solver
that returns unknown, keeps the candidate, so the check removes paths that cannot
execute and does not add findings.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import z3

from evm_dataflow import FlowGraph, node_pc
from symbolic_path import ADDRESS_MASK, TERMINATORS, SymbolicState, bv, concrete, execute

FEASIBLE, INFEASIBLE, UNKNOWN = "feasible", "infeasible", "unknown"
MAX_NODE_VISITS = 2
BLOCK_BUDGET = 3000
SOLVER_TIMEOUT_MS = 1000
SEARCH_DEADLINE_S = 4.0
Goal = Tuple[int, int]  # (block pc, instruction index)


@dataclass
class Stage:
    """Reach one of the goals while moving only through the allowed nodes."""
    goals: Set[Goal]
    allowed: Set[int]
    stop_before_goal: bool = False


@dataclass
class SearchResult:
    verdict: str
    state: Optional[SymbolicState] = None
    constraints: List[z3.BoolRef] = field(default_factory=list)
    reached: Optional[Goal] = None


@dataclass
class _Frame:
    node: int
    index: int
    state: SymbolicState
    stage: int
    constraints: List[z3.BoolRef]
    visits: Dict[int, int]


def backward_reach(graph: FlowGraph, targets: Set[int], allowed: Set[int]) -> Set[int]:
    """Nodes in allowed from which some target node is reachable (targets included)."""
    preds = graph.predecessors()
    seen = {t for t in targets if t in allowed}
    frontier = list(seen)
    while frontier:
        node = frontier.pop()
        for pred in preds.get(node, []):
            if pred in allowed and pred not in seen:
                seen.add(pred)
                frontier.append(pred)
    return seen


def nodes_at(graph: FlowGraph, pcs: Set[int]) -> Set[int]:
    return {node for node in graph.reachable if node_pc(node) in pcs}


def is_satisfiable(constraints: List[z3.BoolRef]) -> str:
    solver = z3.Solver()
    solver.set("timeout", SOLVER_TIMEOUT_MS)
    solver.add(*constraints)
    result = solver.check()
    if result == z3.sat:
        return FEASIBLE
    return INFEASIBLE if result == z3.unsat else UNKNOWN


class IncrementalSolver:
    """One solver per search. Depth-first frames share constraint prefixes, so the solver keeps
    the asserted prefix and only pops and pushes the part that differs, reusing learned lemmas."""

    def __init__(self):
        self.solver = z3.Solver()
        self.solver.set("timeout", SOLVER_TIMEOUT_MS)
        self.asserted: List[z3.BoolRef] = []

    def check(self, constraints: List[z3.BoolRef]) -> str:
        common = 0
        for mine, theirs in zip(self.asserted, constraints):
            if mine is not theirs:
                break
            common += 1
        for _ in range(len(self.asserted) - common):
            self.solver.pop()
        self.asserted = self.asserted[:common]
        for constraint in constraints[common:]:
            self.solver.push()
            self.solver.add(constraint)
            self.asserted.append(constraint)
        result = self.solver.check()
        if result == z3.sat:
            return FEASIBLE
        return INFEASIBLE if result == z3.unsat else UNKNOWN


def search(graph: FlowGraph, start: _Frame, stages: List[Stage],
           finalize: Optional[Callable[[SymbolicState], List[z3.BoolRef]]] = None) -> SearchResult:
    """Depth-first symbolic search through the stages; prunes unsatisfiable branches. At the
    last goal, finalize may add constraints that depend on the state reached there."""
    deadline = time.monotonic() + SEARCH_DEADLINE_S
    stack, budget, exhausted = [start], BLOCK_BUDGET, False
    solver = IncrementalSolver()
    while stack:
        if budget <= 0 or time.monotonic() > deadline:
            exhausted = True
            break
        budget -= 1
        frame = stack.pop()
        outcome = _run_frame(graph, frame, stages, solver)
        if isinstance(outcome, SearchResult):
            if finalize is not None:
                outcome.constraints = outcome.constraints + finalize(outcome.state)
            final = solver.check(outcome.constraints)
            if final != INFEASIBLE:
                outcome.verdict = final
                return outcome
            continue
        stack.extend(outcome)
    return SearchResult(UNKNOWN if exhausted else INFEASIBLE)


def _run_frame(graph: FlowGraph, frame: _Frame, stages: List[Stage], solver: IncrementalSolver):
    """Execute one block from frame.index; return a SearchResult at the last goal, or successor frames."""
    pc = node_pc(frame.node)
    first, end = graph.block_ranges[pc]
    return _run_instructions(graph, frame, (stages, frame.stage, solver), pc, first, end)


def _take_pending(frame: _Frame) -> None:
    """Move constraints emitted by the executor (hash bounds) into the frame's path condition."""
    if frame.state.pending:
        frame.constraints = frame.constraints + frame.state.pending
        frame.state.pending = []


def _run_instructions(graph: FlowGraph, frame: _Frame, position: Tuple[List[Stage], int, IncrementalSolver],
                      pc: int, first: int, end: int):
    stages, stage, solver = position
    state = frame.state
    for index in range(max(first, frame.index), end):
        inst = graph.instructions[index]
        if (pc, index) in stages[stage].goals:
            last = stage == len(stages) - 1
            if last and stages[stage].stop_before_goal:
                return SearchResult(FEASIBLE, state, frame.constraints, (pc, index))
            if inst.name not in ("JUMP", "JUMPI"):
                execute(state, inst)
                _take_pending(frame)
            if last:
                return SearchResult(FEASIBLE, state, frame.constraints, (pc, index))
            stage += 1
            continue
        if inst.name in TERMINATORS:
            return []
        if inst.name in ("JUMP", "JUMPI"):
            return _branch(graph, frame, (stages, stage, solver), inst, end)
        execute(state, inst)
        _take_pending(frame)
    return _branch(graph, frame, (stages, stage, solver), None, end)


def _edge_condition(state: SymbolicState, inst: Any, target_pc: int, fallthrough: Optional[int],
                    jump: Tuple[Any, Any]) -> Optional[z3.BoolRef]:
    """Condition under which control moves to target_pc, or None if the edge is impossible."""
    if inst is None:
        return z3.BoolVal(True) if target_pc == fallthrough else None
    target_expr, condition = jump
    options = []
    if inst.name == "JUMP":
        options.append(target_expr == bv(target_pc))
    else:
        options.append(z3.And(target_expr == bv(target_pc), condition != bv(0)))
        if target_pc == fallthrough:
            options.append(condition == bv(0))
    edge = z3.simplify(z3.Or(*options))
    return None if z3.is_false(edge) else edge


def _branch(graph: FlowGraph, frame: _Frame, position: Tuple[List[Stage], int, IncrementalSolver],
            inst: Any, end: int) -> list:
    stages, stage, solver = position
    state = frame.state
    jump = (None, None)
    if inst is not None:
        target = state.pop()
        jump = (target, state.pop() if inst.name == "JUMPI" else None)
    fallthrough = graph.instructions[end].pc if end < len(graph.instructions) else None
    successors = []
    for successor in graph.successors.get(frame.node, []):
        if successor not in stages[stage].allowed or frame.visits.get(successor, 0) >= MAX_NODE_VISITS:
            continue
        edge = _edge_condition(state, inst, node_pc(successor), fallthrough, jump)
        if edge is None:
            continue
        constraints = frame.constraints if z3.is_true(edge) else frame.constraints + [edge]
        if concrete_free(edge) and solver.check(constraints) == INFEASIBLE:
            continue
        visits = dict(frame.visits)
        visits[successor] = visits.get(successor, 0) + 1
        successors.append(_Frame(successor, 0, state.copy(), stage, constraints, visits))
    return successors


def concrete_free(edge: z3.BoolRef) -> bool:
    """True when the edge condition depends on symbols, so only the solver can decide it."""
    return not (z3.is_true(edge) or z3.is_false(edge))


ADDRESS_BOUND = 1 << 160
# Solidity packs an address with smaller fields, so it can start at any byte offset from 0 to 12.
PACKED_ADDRESS_OFFSETS = 13


@dataclass
class AttackerModel:
    """The unprivileged attacker: an address A that is not hard-coded in the bytecode and not held,
    when the transaction starts, in a fixed storage slot that the attacker cannot set. A sends the
    transaction, receives the external call, and sends the re-entrant call. A slot is settable when
    some function writes it with the caller, or with calldata and no dominating CALLER check, so an
    earlier transaction may have stored A there. Disabled, every caller and callee is allowed."""
    enabled: bool
    code_addresses: Set[int]
    settable_slots: Set[int] = field(default_factory=set)
    attacker: z3.BitVecRef = field(default_factory=lambda: z3.BitVec("attacker", 256))

    def caller(self, state: SymbolicState) -> List[z3.BoolRef]:
        if not self.enabled:
            return []
        constraints = [state.env("caller") == self.attacker, z3.ULT(self.attacker, bv(ADDRESS_BOUND))]
        return constraints + [self.attacker != bv(address) for address in self.code_addresses]

    def not_stored(self, state: SymbolicState, initial: z3.ArrayRef) -> List[z3.BoolRef]:
        if not self.enabled:
            return []
        keys = state.sloads if state.sloads_at_call is None else state.sloads[:state.sloads_at_call]
        values = {concrete(key): z3.Select(initial, key) for key in keys
                  if concrete(key) is not None and concrete(key) not in self.settable_slots}
        return [self.attacker != (z3.LShR(value, bv(8 * offset)) & bv(ADDRESS_MASK))
                for value in values.values() for offset in range(PACKED_ADDRESS_OFFSETS)]

    def callee(self, state: SymbolicState) -> List[z3.BoolRef]:
        target = state.call_operands.get("target")
        if not self.enabled or target is None:
            return []
        return [(target & bv(ADDRESS_MASK)) == self.attacker]


def settable_slots(graph: FlowGraph, guarded: Callable[[Dict[str, Any]], bool]) -> Set[int]:
    """Fixed slots that a transaction can set to its caller or to an unguarded calldata value."""
    slots = set()
    for store in graph.events:
        if store["kind"] != "sstore" or store["slot"].const is None:
            continue
        value = store["value"]
        if value.from_caller or (value.from_calldata and not guarded(store)):
            slots.add(store["slot"].const)
    return slots


def code_addresses(graph: FlowGraph) -> Set[int]:
    return {inst.operand for inst in graph.instructions if inst.name == "PUSH20" and inst.operand}


def _goal(event: Dict[str, Any]) -> Goal:
    return node_pc(event["block"]), event["order"]


def call_write_path(graph: FlowGraph, call: Dict[str, Any], store: Dict[str, Any],
                    scope: Set[int], model: AttackerModel) -> SearchResult:
    """Question 1: a transaction that runs from the entry through the call to the write."""
    call_nodes = nodes_at(graph, {node_pc(call["block"])})
    store_nodes = nodes_at(graph, {node_pc(store["block"])}) & scope
    before = backward_reach(graph, call_nodes, graph.reachable)
    after = backward_reach(graph, store_nodes, scope) | call_nodes
    stages = [Stage({_goal(call)}, before), Stage({_goal(store)}, after, stop_before_goal=True)]
    state = SymbolicState("tx")
    state.attacker = model.attacker if model.enabled else None
    initial = state.storage

    def finalize(reached: SymbolicState) -> List[z3.BoolRef]:
        return model.not_stored(reached, initial) + model.callee(reached)

    start = _Frame(graph.entry, 0, state, 0, model.caller(state), {graph.entry: 1})
    return search(graph, start, stages, finalize)


def reentry_path(graph: FlowGraph, first: SearchResult, goals: Set[Goal], model: AttackerModel) -> SearchResult:
    """Question 2: a re-entrant invocation from the storage state at the call that reaches a goal."""
    storage = first.state.storage_at_call if first.state is not None else None
    if storage is None:
        return SearchResult(UNKNOWN)
    goal_nodes = nodes_at(graph, {pc for pc, _ in goals})
    allowed = backward_reach(graph, goal_nodes, graph.reachable)
    state = SymbolicState("reentry", storage=storage)
    state.attacker = model.attacker if model.enabled else None

    def finalize(reached: SymbolicState) -> List[z3.BoolRef]:
        return model.not_stored(reached, storage)

    start = _Frame(graph.entry, 0, state, 0, list(first.constraints) + model.caller(state), {graph.entry: 1})
    return search(graph, start, [Stage(goals, allowed, stop_before_goal=True)], finalize)


def stale_read_goals(graph: FlowGraph, scopes: Dict[str, Set[int]], selector: str,
                     written_slots: Set[Optional[int]]) -> Dict[Goal, str]:
    """SLOADs in other public functions that may read a slot the write updates, mapped to the
    reading function. An unknown slot (a mapping entry, for instance) may alias any slot."""
    goals = {}
    for event in graph.events:
        if event["kind"] != "sload":
            continue
        slot = event["slot"].const
        if slot is not None and None not in written_slots and slot not in written_slots:
            continue
        for other, scope in scopes.items():
            if other and other != selector and event["block"] in scope:
                goals.setdefault(_goal(event), other)
    return goals


def decide(graph: FlowGraph, scopes: Dict[str, Set[int]], selector: str, call: Dict[str, Any],
           stores: List[Dict[str, Any]], model: AttackerModel) -> Dict[str, Any]:
    """Run both questions for one call and its later writes. Only UNSAT answers reject."""
    scope = scopes[selector]
    first = SearchResult(INFEASIBLE)
    for store in stores:
        first = call_write_path(graph, call, store, scope, model)
        if first.verdict != INFEASIBLE:
            break
    if first.verdict == INFEASIBLE:
        return {"verdict": INFEASIBLE, "reason": "no feasible call-then-write path"}
    if first.verdict == UNKNOWN:
        return {"verdict": UNKNOWN, "kind": "unclassified", "reason": "call-then-write search budget"}
    cross = stale_read_goals(graph, scopes, selector, {store["slot"].const for store in stores})
    same = reentry_path(graph, first, {_goal(call)}, model)
    if same.verdict == FEASIBLE:
        return {"verdict": FEASIBLE, "kind": "same-function", "first": first}
    other = reentry_path(graph, first, set(cross), model) if cross else SearchResult(INFEASIBLE)
    if other.verdict == FEASIBLE:
        return {"verdict": FEASIBLE, "kind": "cross-function", "reader": cross[other.reached], "first": first}
    if same.verdict == INFEASIBLE and other.verdict == INFEASIBLE:
        return {"verdict": INFEASIBLE, "reason": "re-entry cannot reach the call or a stale read"}
    return {"verdict": UNKNOWN, "kind": "unclassified", "first": first, "reason": "re-entry search budget"}
