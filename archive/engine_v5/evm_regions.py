"""Dominators, dispatcher function regions and natural loops over a FlowGraph."""

from typing import Any, Dict, List, Optional, Set, Tuple

from evm_dataflow import FlowGraph

ERC1967_IMPLEMENTATION_SLOT = 0x360894A13BA1A3210667C828492DB98DCA3E2076CC3735A920A3CA505D382BBC
SELECTOR_WINDOW = 5


class Dominance:
    """Bitmask dominator sets over the reachable blocks, rooted at the entry block."""

    def __init__(self, graph: FlowGraph):
        self._index = {node: position for position, node in enumerate(sorted(graph.reachable))}
        self._masks = self._compute(graph)

    def _compute(self, graph: FlowGraph) -> Dict[int, int]:
        preds = graph.predecessors()
        full = (1 << len(self._index)) - 1
        masks = {node: full for node in self._index}
        masks[graph.entry] = 1 << self._index[graph.entry]
        changed = True
        while changed:
            changed = False
            for node in self._index:
                if node == graph.entry:
                    continue
                meet = full
                for pred in preds[node]:
                    meet &= masks[pred]
                meet |= 1 << self._index[node]
                if meet != masks[node]:
                    masks[node] = meet
                    changed = True
        return masks

    def block_dominates(self, dominator: int, node: int) -> bool:
        return bool((self._masks[node] >> self._index[dominator]) & 1)


def reach_within(graph: FlowGraph, start: int, allowed: Set[int]) -> Set[int]:
    """Blocks reachable by at least one edge from start, moving only through allowed blocks."""
    seen: Set[int] = set()
    frontier = [target for target in graph.successors.get(start, []) if target in allowed]
    while frontier:
        node = frontier.pop()
        if node in seen:
            continue
        seen.add(node)
        frontier.extend(t for t in graph.successors.get(node, []) if t in allowed)
    return seen


def dispatch_entries(instructions: List[Any], jumpdests: Set[int]) -> Dict[str, int]:
    """Map each dispatcher selector to the JUMPDEST its PUSH4/EQ/PUSH tag/JUMPI branch enters."""
    entries: Dict[str, int] = {}
    for index, inst in enumerate(instructions):
        if inst.name != "JUMPI" or index < 1:
            continue
        tag = instructions[index - 1].operand if instructions[index - 1].name.startswith("PUSH") else None
        if tag not in jumpdests:
            continue
        window = instructions[max(0, index - SELECTOR_WINDOW):index]
        selectors = [w.operand for w in window if w.name == "PUSH4"]
        if selectors and any(w.name == "EQ" for w in window):
            entries.setdefault(f"0x{selectors[-1]:08x}", tag)
    return entries


def function_scopes(graph: FlowGraph, entries: Dict[str, int]) -> Dict[str, Set[int]]:
    """Blocks reachable from each function entry without entering another function's entry."""
    if not entries:
        return {"": set(graph.reachable)}
    stops = set(entries.values())
    scopes = {}
    for selector, entry in entries.items():
        if entry not in graph.reachable:
            continue
        scopes[selector] = {entry} | reach_within(graph, entry, graph.reachable - (stops - {entry}))
    return scopes


def selectors_containing(scopes: Dict[str, Set[int]], block: Optional[int]) -> List[str]:
    """Dispatcher selectors whose function region contains the block."""
    if block is None:
        return []
    return [selector for selector, scope in scopes.items() if selector and block in scope]


def natural_loops(graph: FlowGraph, dominance: Dominance) -> List[Tuple[int, Set[int]]]:
    """Return (header, body) for each back edge u -> v where v dominates u."""
    preds = graph.predecessors()
    loops = []
    for tail in sorted(graph.reachable):
        for header in graph.successors.get(tail, []):
            if header not in graph.reachable or not dominance.block_dominates(header, tail):
                continue
            body = {header}
            stack = [tail]
            while stack:
                node = stack.pop()
                if node not in body:
                    body.add(node)
                    stack.extend(preds[node])
            loops.append((header, body))
    return loops


def loop_exit_jumpis(graph: FlowGraph, body: Set[int]) -> List[int]:
    """Blocks in body ending in JUMPI with a successor outside the loop that does not revert."""
    exits = []
    for block in body:
        if graph.block_last_op.get(block) != "JUMPI":
            continue
        for target in graph.successors.get(block, []):
            if target not in body and graph.block_last_op.get(target) not in ("REVERT", "INVALID"):
                exits.append(block)
                break
    return exits


def erc1967_present(instructions: List[Any]) -> bool:
    return any(inst.name.startswith("PUSH") and inst.operand == ERC1967_IMPLEMENTATION_SLOT
               for inst in instructions)
