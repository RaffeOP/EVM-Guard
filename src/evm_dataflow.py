"""Basic-block control-flow graph and abstract stack dataflow for EVM runtime code.

Every stack slot carries an AbstractValue: a constant if one is known, and
flags for calldata, caller, storage and DIV provenance. Jump edges come from
constant jump targets found during the fixpoint, so the CFG contains only
edges the abstract stack justifies. Unresolved jumps are counted, not guessed.

With return-site tracking, a block is analysed once per context: the sequence of
JUMPDEST addresses held on the abstract stack when control enters it (the pending
return addresses of internal calls, at most CONTEXT_DEPTH of them). An internal
function called from two sites is then analysed twice, and each copy returns only
to its own caller. A node of the graph is a (context index, block pc) pair packed
into one integer, so with tracking disabled every node is the block pc itself.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

WORD_MODULUS = 2 ** 256
STACK_CAP = 1024
CALLDATA_PARAMETER_OFFSET = 4
PC_BITS = 32
PC_MASK = (1 << PC_BITS) - 1
CONTEXT_DEPTH = 4
MAX_CONTEXTS_PER_BLOCK = 32
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
    upper: Optional[int] = None




UNKNOWN = AbstractValue()


def node_pc(node: int) -> int:
    """The block pc of a graph node."""
    return node & PC_MASK


def value_bound(value: AbstractValue) -> Optional[int]:
    """A sound upper bound on the unsigned value, from its constant or derivation, or None."""
    return value.const if value.const is not None else value.upper


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
        upper=_joined_bound(value_bound(left), value_bound(right)),
    )


def _joined_bound(left: Optional[int], right: Optional[int]) -> Optional[int]:
    if left is None or right is None:
        return None
    return max(left, right)


def derive(operands: List[AbstractValue], const: Optional[int] = None, div_site: Optional[int] = None,
           upper: Optional[int] = None) -> AbstractValue:
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
        upper=upper,
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

    def last_op(self, node: int) -> Optional[str]:
        return self.block_last_op.get(node_pc(node))

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
        events.append({"kind": "sload", "block": block, "pc": inst.pc, "order": index, "slot": slot})
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
        bound = 1 if name == "ISZERO" else None
        for _ in range(inst.pushes):
            frame.push(derive(operands, upper=bound))


def _execute_binary(frame: _Frame, inst: Any, index: int, block: int, events: List[Dict[str, Any]]) -> None:
    left, right = frame.pop(), frame.pop()
    if inst.name in ("MUL", "SMUL"):
        events.append({"kind": "mul", "block": block, "pc": inst.pc, "order": index,
                       "div_sites": left.div_sites | right.div_sites})
    const = None
    folder = FOLDABLE_OPS.get(inst.name)
    if folder and left.const is not None and right.const is not None:
        const = folder(left.const, right.const)
    frame.push(derive([left, right], const=const, upper=_binary_bound(inst.name, left, right)))


def _binary_bound(name: str, left: AbstractValue, right: AbstractValue) -> Optional[int]:
    """Upper bound for MUL (product of bounds) and AND (smallest known operand bound)."""
    left_bound, right_bound = value_bound(left), value_bound(right)
    if name == "MUL" and left_bound is not None and right_bound is not None:
        product = left_bound * right_bound
        return product if product < WORD_MODULUS else None
    if name == "AND" and (left_bound is not None or right_bound is not None):
        known = [b for b in (left_bound, right_bound) if b is not None]
        return min(known)
    return None


def _run_block(graph: FlowGraph, node: int, state: Tuple[AbstractValue, ...],
               events: Optional[List[Dict[str, Any]]]) -> Tuple[Tuple[AbstractValue, ...], Optional[int], List[int]]:
    """Run one block; return (out_state, jump_target, successor pcs). Events name the node."""
    first, end = graph.block_ranges[node_pc(node)]
    frame = _Frame(state)
    sink = events if events is not None else []
    for index in range(first, end):
        _execute_instruction(frame, graph.instructions[index], index, node, sink)
    last = graph.instructions[end - 1]
    successors = _block_successors(graph, node, end, last.name, frame.jump_target)
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


class _Contexts:
    """Interns (block pc, context) pairs as nodes. Past the per-block cap, a block's further
    contexts share one overflow node, whose joined state loses their return addresses."""

    def __init__(self, jumpdests: Set[int], should_track: bool):
        self.jumpdests = jumpdests
        self.should_track = should_track
        self.by_block: Dict[int, Dict[Tuple[int, ...], int]] = defaultdict(dict)

    def node(self, pc: int, state: Tuple[AbstractValue, ...]) -> int:
        if not self.should_track:
            return pc
        context = tuple(v.const for v in state if v.const in self.jumpdests)[-CONTEXT_DEPTH:]
        known = self.by_block[pc]
        if context not in known:
            known[context] = min(len(known), MAX_CONTEXTS_PER_BLOCK)
        return (known[context] << PC_BITS) | pc


def analyze_flow(instructions: List[Any], should_track_return_sites: bool = False) -> FlowGraph:
    """Compute reachable nodes, resolved edges and dataflow events by worklist fixpoint."""
    jumpdests = {inst.pc for inst in instructions if inst.name == "JUMPDEST"}
    graph = FlowGraph(instructions=instructions, jumpdests=jumpdests, entry=instructions[0].pc)
    graph.block_ranges = split_blocks(instructions)
    for start, (first, end) in graph.block_ranges.items():
        graph.block_last_op[start] = instructions[end - 1].name
    contexts = _Contexts(jumpdests, should_track_return_sites)
    in_states: Dict[int, Tuple[AbstractValue, ...]] = {graph.entry: ()}
    worklist = [graph.entry]
    while worklist:
        node = worklist.pop()
        out_state, _, successors = _run_block(graph, node, in_states[node], None)
        for target_pc in successors:
            target = contexts.node(target_pc, out_state)
            previous = in_states.get(target)
            joined = out_state if previous is None else join_states(previous, out_state)
            if previous is None or joined != previous:
                in_states[target] = joined
                worklist.append(target)
    _record_final_pass(graph, in_states, contexts)
    graph.reachable = set(in_states)
    return graph


def _record_final_pass(graph: FlowGraph, in_states: Dict[int, Tuple[AbstractValue, ...]],
                       contexts: _Contexts) -> None:
    unresolved: Set[int] = set()
    for node, state in in_states.items():
        out_state, _, successors = _run_block(graph, node, state, graph.events)
        graph.successors[node] = [contexts.node(pc, out_state) for pc in successors]
        if graph.last_op(node) == "JUMP" and not successors:
            unresolved.add(node_pc(node))
    graph.unresolved_jumps = len(unresolved)
