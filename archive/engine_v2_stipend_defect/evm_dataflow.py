"""Basic-block control-flow graph and abstract stack dataflow for EVM runtime code.

Every stack slot carries an AbstractValue: a constant if one is known, and
flags for calldata, caller, storage and DIV provenance. Jump edges come from
constant jump targets found during the fixpoint, so the CFG contains only
edges the abstract stack justifies. Unresolved jumps are counted, not guessed.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

WORD_MODULUS = 2 ** 256
STACK_CAP = 1024
CALLDATA_PARAMETER_OFFSET = 4
TERMINATORS = frozenset({"STOP", "RETURN", "REVERT", "INVALID", "SELFDESTRUCT"})
BLOCK_ENDERS = TERMINATORS | {"JUMP", "JUMPI"}
CALL_FAMILY = frozenset({"CALL", "CALLCODE", "DELEGATECALL", "STATICCALL"})
FOLDABLE_OPS = {
    "ADD": lambda a, b: (a + b) % WORD_MODULUS,
    "SUB": lambda a, b: (a - b) % WORD_MODULUS,
    "MUL": lambda a, b: (a * b) % WORD_MODULUS,
    "AND": lambda a, b: a & b,
    "OR": lambda a, b: a | b,
    "XOR": lambda a, b: a ^ b,
}


@dataclass(frozen=True)
class AbstractValue:
    const: Optional[int] = None
    from_calldata: bool = False
    from_caller: bool = False
    from_storage: bool = False
    storage_slot: Optional[int] = None
    div_sites: FrozenSet[int] = frozenset()


UNKNOWN = AbstractValue()


def join_values(left: AbstractValue, right: AbstractValue) -> AbstractValue:
    if left == right:
        return left
    return AbstractValue(
        const=left.const if left.const == right.const else None,
        from_calldata=left.from_calldata or right.from_calldata,
        from_caller=left.from_caller or right.from_caller,
        from_storage=left.from_storage or right.from_storage,
        storage_slot=left.storage_slot if left.storage_slot == right.storage_slot else None,
        div_sites=left.div_sites | right.div_sites,
    )


def derive(operands: List[AbstractValue], const: Optional[int] = None, div_site: Optional[int] = None) -> AbstractValue:
    sites = frozenset().union(*(value.div_sites for value in operands))
    if div_site is not None:
        sites = sites | {div_site}
    slot = next((v.storage_slot for v in operands if v.from_storage and v.storage_slot is not None), None)
    return AbstractValue(
        const=const,
        from_calldata=any(v.from_calldata for v in operands),
        from_caller=any(v.from_caller for v in operands),
        from_storage=any(v.from_storage for v in operands),
        storage_slot=slot,
        div_sites=sites,
    )


def join_states(current: Tuple[AbstractValue, ...], incoming: Tuple[AbstractValue, ...]) -> Tuple[AbstractValue, ...]:
    """Join two stacks by keeping the top min(len) slots and joining them pointwise."""
    size = min(len(current), len(incoming))
    top_current = current[len(current) - size:]
    top_incoming = incoming[len(incoming) - size:]
    return tuple(join_values(a, b) for a, b in zip(top_current, top_incoming))


class _Frame:
    """Mutable abstract stack for one basic block; underflow yields UNKNOWN."""

    def __init__(self, state: Tuple[AbstractValue, ...]):
        self.stack: List[AbstractValue] = list(state)
        self.jump_target: Optional[int] = None

    def pop(self) -> AbstractValue:
        return self.stack.pop() if self.stack else UNKNOWN

    def push(self, value: AbstractValue) -> None:
        if len(self.stack) < STACK_CAP:
            self.stack.append(value)

    def peek(self, depth: int) -> AbstractValue:
        return self.stack[-depth] if len(self.stack) >= depth else UNKNOWN

    def snapshot(self) -> Tuple[AbstractValue, ...]:
        return tuple(self.stack)


@dataclass
class FlowGraph:
    """CFG over basic blocks keyed by their first pc, with per-block dataflow events."""

    instructions: List[Any]
    jumpdests: Set[int]
    block_ranges: Dict[int, Tuple[int, int]] = field(default_factory=dict)
    block_last_op: Dict[int, str] = field(default_factory=dict)
    successors: Dict[int, List[int]] = field(default_factory=dict)
    reachable: Set[int] = field(default_factory=set)
    events: List[Dict[str, Any]] = field(default_factory=list)
    unresolved_jumps: int = 0
    entry: int = 0

    def predecessors(self) -> Dict[int, List[int]]:
        preds: Dict[int, List[int]] = {node: [] for node in self.reachable}
        for node in self.reachable:
            for target in self.successors.get(node, []):
                if target in preds:
                    preds[target].append(node)
        return preds


def split_blocks(instructions: List[Any]) -> Dict[int, Tuple[int, int]]:
    """Return {block_start_pc: (first_index, end_index)} with leaders at JUMPDESTs and after block enders."""
    count = len(instructions)
    leaders = {0}
    for index, inst in enumerate(instructions):
        if inst.name == "JUMPDEST":
            leaders.add(index)
        if inst.name in BLOCK_ENDERS and index + 1 < count:
            leaders.add(index + 1)
    starts = sorted(leaders)
    ranges = {}
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else count
        ranges[instructions[start].pc] = (start, end)
    return ranges


def _execute_call(frame: _Frame, inst: Any, index: int, block: int, events: List[Dict[str, Any]]) -> None:
    gas = frame.peek(1)
    target = frame.peek(2)
    value = frame.peek(3) if inst.name in ("CALL", "CALLCODE") else UNKNOWN
    events.append({"kind": "call", "op": inst.name, "block": block, "pc": inst.pc, "order": index,
                   "gas": gas, "target": target, "value": value})
    if inst.name == "DELEGATECALL":
        events.append({"kind": "delegatecall", "block": block, "pc": inst.pc, "order": index, "target": target})
    for _ in range(inst.pops):
        frame.pop()
    for _ in range(inst.pushes):
        frame.push(UNKNOWN)


def _execute_instruction(frame: _Frame, inst: Any, index: int, block: int, events: List[Dict[str, Any]]) -> None:
    name = inst.name
    if name.startswith("PUSH"):
        frame.push(AbstractValue(const=inst.operand or 0))
    elif name.startswith("DUP"):
        frame.push(frame.peek(int(name[3:])))
    elif name.startswith("SWAP"):
        depth = int(name[4:])
        if len(frame.stack) > depth:
            frame.stack[-1], frame.stack[-depth - 1] = frame.stack[-depth - 1], frame.stack[-1]
    elif name in CALL_FAMILY:
        _execute_call(frame, inst, index, block, events)
    else:
        _execute_data_op(frame, inst, index, block, events)


def _execute_data_op(frame: _Frame, inst: Any, index: int, block: int, events: List[Dict[str, Any]]) -> None:
    name = inst.name
    if name == "CALLDATALOAD":
        offset = frame.pop()
        tainted = offset.const is None or offset.const >= CALLDATA_PARAMETER_OFFSET
        frame.push(AbstractValue(from_calldata=tainted))
    elif name == "CALLER":
        events.append({"kind": "caller", "block": block, "pc": inst.pc, "order": index})
        frame.push(AbstractValue(from_caller=True))
    elif name == "SLOAD":
        slot = frame.pop()
        frame.push(AbstractValue(from_storage=True, storage_slot=slot.const))
    elif name == "SSTORE":
        slot = frame.pop()
        value = frame.pop()
        events.append({"kind": "sstore", "block": block, "pc": inst.pc, "order": index,
                       "slot": slot, "value": value})
    elif name in ("DIV", "SDIV"):
        dividend, divisor = frame.pop(), frame.pop()
        frame.push(derive([dividend, divisor], div_site=inst.pc))
    elif name in ("MUL", "SMUL") or name in FOLDABLE_OPS:
        _execute_binary(frame, inst, index, block, events)
    elif name == "JUMP":
        frame.jump_target = frame.pop().const
    elif name == "JUMPI":
        target, condition = frame.pop(), frame.pop()
        frame.jump_target = target.const
        events.append({"kind": "jumpi", "block": block, "pc": inst.pc, "order": index,
                       "cond": condition, "target": target.const})
    else:
        operands = [frame.pop() for _ in range(inst.pops)]
        for _ in range(inst.pushes):
            frame.push(derive(operands))


def _execute_binary(frame: _Frame, inst: Any, index: int, block: int, events: List[Dict[str, Any]]) -> None:
    left, right = frame.pop(), frame.pop()
    if inst.name in ("MUL", "SMUL"):
        events.append({"kind": "mul", "block": block, "pc": inst.pc, "order": index,
                       "div_sites": left.div_sites | right.div_sites})
    const = None
    folder = FOLDABLE_OPS.get(inst.name)
    if folder and left.const is not None and right.const is not None:
        const = folder(left.const, right.const)
    frame.push(derive([left, right], const=const))


def _run_block(graph: FlowGraph, start_pc: int, state: Tuple[AbstractValue, ...],
               events: Optional[List[Dict[str, Any]]]) -> Tuple[Tuple[AbstractValue, ...], Optional[int], List[int]]:
    """Run one block; return (out_state, jump_target, successor pcs)."""
    first, end = graph.block_ranges[start_pc]
    frame = _Frame(state)
    sink = events if events is not None else []
    for index in range(first, end):
        _execute_instruction(frame, graph.instructions[index], index, start_pc, sink)
    last = graph.instructions[end - 1]
    successors = _block_successors(graph, start_pc, end, last.name, frame.jump_target)
    return frame.snapshot(), frame.jump_target, successors


def _block_successors(graph: FlowGraph, block: int, end: int, last_name: str,
                      jump_target: Optional[int]) -> List[int]:
    fallthrough = graph.instructions[end].pc if end < len(graph.instructions) else None
    if last_name in TERMINATORS:
        return []
    if last_name == "JUMP":
        return [jump_target] if jump_target in graph.jumpdests else []
    if last_name == "JUMPI":
        targets = [jump_target] if jump_target in graph.jumpdests else []
        return targets + ([fallthrough] if fallthrough is not None else [])
    return [fallthrough] if fallthrough is not None else []


def analyze_flow(instructions: List[Any]) -> FlowGraph:
    """Compute reachable blocks, resolved edges and dataflow events by worklist fixpoint."""
    jumpdests = {inst.pc for inst in instructions if inst.name == "JUMPDEST"}
    graph = FlowGraph(instructions=instructions, jumpdests=jumpdests, entry=instructions[0].pc)
    graph.block_ranges = split_blocks(instructions)
    for start, (first, end) in graph.block_ranges.items():
        graph.block_last_op[start] = instructions[end - 1].name
    in_states: Dict[int, Tuple[AbstractValue, ...]] = {graph.entry: ()}
    worklist = [graph.entry]
    while worklist:
        block = worklist.pop()
        out_state, _, successors = _run_block(graph, block, in_states[block], None)
        for target in successors:
            previous = in_states.get(target)
            joined = out_state if previous is None else join_states(previous, out_state)
            if previous is None or joined != previous:
                in_states[target] = joined
                worklist.append(target)
    _record_final_pass(graph, in_states)
    graph.reachable = set(in_states)
    return graph


def _record_final_pass(graph: FlowGraph, in_states: Dict[int, Tuple[AbstractValue, ...]]) -> None:
    for block, state in in_states.items():
        _, _, successors = _run_block(graph, block, state, graph.events)
        graph.successors[block] = successors
        if graph.block_last_op[block] == "JUMP" and not successors:
            graph.unresolved_jumps += 1
