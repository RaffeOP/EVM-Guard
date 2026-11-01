"""Bit-precise symbolic execution of single EVM instructions over Z3 bit-vectors.

Used by path_feasibility to decide whether a CFG path can execute. Every value the
executor cannot model exactly (environment reads, hashes of unknown memory, external
call results) becomes an unconstrained symbol. The model therefore over-approximates
the real executions: an UNSAT path condition means the path cannot execute, while a
SAT result only means the path was not refuted.

Calldata is an array from offsets to 32-byte words. Reads at overlapping offsets are
independent words, which over-approximates the EVM; the model of a satisfiable path still
gives concrete words for the offsets the path reads.
Storage is an array from words to words. KECCAK256 is an uninterpreted function of the
hashed memory words; real hashes are recomputed from the model when replay needs them.
"""

from typing import Any, Dict, List, Optional

import z3

WORD_BITS = 256
WORD_BYTES = 32
ADDRESS_MASK = (1 << 160) - 1
MAX_HASHED_WORDS = 8
# A KECCAK256 output lies below 2**128 with probability 2**-128. Bounding the uninterpreted hash
# from below stops the solver from aliasing mapping entries with fixed low storage slots.
HASH_LOWER_BOUND = 1 << 128
ENV_SYMBOLS = {
    "ADDRESS": "address", "ORIGIN": "origin", "CALLER": "caller", "CALLVALUE": "callvalue",
    "CALLDATASIZE": "calldatasize", "GASPRICE": "gasprice", "COINBASE": "coinbase",
    "TIMESTAMP": "timestamp", "NUMBER": "number", "DIFFICULTY": "prevrandao", "PREVRANDAO": "prevrandao",
    "GASLIMIT": "gaslimit", "CHAINID": "chainid", "BASEFEE": "basefee", "CODESIZE": "codesize",
}
STATE_CHANGING_CALLS = frozenset({"CALL", "CALLCODE", "DELEGATECALL", "CREATE", "CREATE2"})
TERMINATORS = frozenset({"STOP", "RETURN", "REVERT", "INVALID", "SELFDESTRUCT"})


def bv(value: int) -> z3.BitVecRef:
    return z3.BitVecVal(value % (1 << WORD_BITS), WORD_BITS)


def concrete(expr: z3.BitVecRef) -> Optional[int]:
    if z3.is_bv_value(expr):
        return expr.as_long()
    simplified = z3.simplify(expr)
    return simplified.as_long() if z3.is_bv_value(simplified) else None


def flag(condition: z3.BoolRef) -> z3.BitVecRef:
    return z3.If(condition, bv(1), bv(0))


def power_of_two(expr: z3.BitVecRef) -> Optional[int]:
    """The exponent if expr is a concrete power of two."""
    value = expr.as_long() if z3.is_bv_value(expr) else None
    if value is None or value == 0 or value & (value - 1):
        return None
    return value.bit_length() - 1


def divide(a: z3.BitVecRef, b: z3.BitVecRef) -> z3.BitVecRef:
    shift = power_of_two(b)
    if shift is not None:
        return z3.LShR(a, bv(shift))
    return z3.If(b == 0, bv(0), z3.UDiv(a, b))


def multiply(a: z3.BitVecRef, b: z3.BitVecRef) -> z3.BitVecRef:
    for value, other in ((a, b), (b, a)):
        shift = power_of_two(value)
        if shift is not None:
            return other << bv(shift)
    return a * b


class SymbolicState:
    """Stack, memory, storage and environment of one symbolic execution, keyed by a run tag."""

    def __init__(self, tag: str, storage: Optional[z3.ArrayRef] = None):
        self.tag = tag
        self.stack: List[z3.BitVecRef] = []
        self.memory: Dict[int, z3.BitVecRef] = {}
        self.storage = storage if storage is not None else z3.Array(f"storage_{tag}", z3.BitVecSort(WORD_BITS),
                                                                     z3.BitVecSort(WORD_BITS))
        self.calldata = z3.Array(f"calldata_{tag}", z3.BitVecSort(WORD_BITS), z3.BitVecSort(WORD_BITS))
        self.calldata_offsets: List[int] = []
        self.sloads: List[z3.BitVecRef] = []
        self.calldata_end = 4
        self.pending: List[z3.BoolRef] = []
        self.attacker: Optional[z3.BitVecRef] = None
        self.storage_at_call: Optional[z3.ArrayRef] = None
        self.sloads_at_call: Optional[int] = None
        self.call_operands: Dict[str, z3.BitVecRef] = {}
        self._fresh = 0

    def copy(self) -> "SymbolicState":
        other = SymbolicState.__new__(SymbolicState)
        other.__dict__ = dict(self.__dict__)
        other.stack = list(self.stack)
        other.memory = dict(self.memory)
        other.sloads = list(self.sloads)
        other.pending = list(self.pending)
        other.calldata_offsets = list(self.calldata_offsets)
        other.call_operands = dict(self.call_operands)
        return other

    def fresh(self, hint: str) -> z3.BitVecRef:
        self._fresh += 1
        return z3.BitVec(f"{hint}_{self.tag}_{self._fresh}", WORD_BITS)

    def env(self, name: str) -> z3.BitVecRef:
        return z3.BitVec(f"{name}_{self.tag}", WORD_BITS)

    def pop(self) -> z3.BitVecRef:
        return self.stack.pop() if self.stack else self.fresh("underflow")

    def push(self, value: z3.BitVecRef) -> None:
        self.stack.append(value)


def calldata_word(state: SymbolicState, offset: z3.BitVecRef) -> z3.BitVecRef:
    """CALLDATALOAD: the word at that offset. Words past CALLDATASIZE are left free rather than
    zero, which over-approximates the EVM and keeps every UNSAT answer valid."""
    known = concrete(offset)
    if known is not None:
        state.calldata_end = max(state.calldata_end, known + WORD_BYTES)
        state.calldata_offsets.append(known)
    return z3.Select(state.calldata, offset)


def invalidate_memory(state: SymbolicState, start: Optional[int], length: Optional[int]) -> None:
    """Forget memory words that a copy or call output may overwrite."""
    if start is None or length is None:
        state.memory.clear()
        return
    for offset in list(state.memory):
        if offset < start + length and start < offset + WORD_BYTES:
            del state.memory[offset]


def store_memory_word(state: SymbolicState, offset_expr: z3.BitVecRef, value: z3.BitVecRef) -> None:
    offset = concrete(offset_expr)
    if offset is None:
        state.memory.clear()
        return
    invalidate_memory(state, offset, WORD_BYTES)
    state.memory[offset] = value


def load_memory_word(state: SymbolicState, offset_expr: z3.BitVecRef) -> z3.BitVecRef:
    offset = concrete(offset_expr)
    if offset is not None and offset in state.memory:
        return state.memory[offset]
    return state.fresh("mload")


def keccak(state: SymbolicState, offset_expr: z3.BitVecRef, size_expr: z3.BitVecRef) -> z3.BitVecRef:
    """KECCAK256 as an uninterpreted function of the hashed words, when all of them are known."""
    offset, size = concrete(offset_expr), concrete(size_expr)
    if offset is None or size is None or size == 0 or size % WORD_BYTES or size > MAX_HASHED_WORDS * WORD_BYTES:
        return state.fresh("sha3")
    words = [state.memory.get(offset + i * WORD_BYTES) for i in range(size // WORD_BYTES)]
    if any(w is None for w in words):
        return state.fresh("sha3")
    function = z3.Function(f"keccak{len(words)}", *([z3.BitVecSort(WORD_BITS)] * (len(words) + 1)))
    digest = function(*words)
    state.pending.append(z3.UGE(digest, bv(HASH_LOWER_BOUND)))
    return digest


BINARY_OPS = {
    "ADD": lambda a, b: a + b,
    "SUB": lambda a, b: a - b,
    "MUL": multiply,
    "DIV": divide,
    "SDIV": lambda a, b: z3.If(b == 0, bv(0), a / b),
    "MOD": lambda a, b: z3.If(b == 0, bv(0), z3.URem(a, b)),
    "SMOD": lambda a, b: z3.If(b == 0, bv(0), z3.SRem(a, b)),
    "LT": lambda a, b: flag(z3.ULT(a, b)),
    "GT": lambda a, b: flag(z3.UGT(a, b)),
    "SLT": lambda a, b: flag(a < b),
    "SGT": lambda a, b: flag(a > b),
    "EQ": lambda a, b: flag(a == b),
    "AND": lambda a, b: a & b,
    "OR": lambda a, b: a | b,
    "XOR": lambda a, b: a ^ b,
    "SHL": lambda shift, value: value << shift,
    "SHR": lambda shift, value: z3.LShR(value, shift),
    "SAR": lambda shift, value: value >> shift,
}


def execute(state: SymbolicState, inst: Any) -> None:
    """Apply one non-control-flow instruction to the state."""
    name = inst.name
    if name.startswith("PUSH"):
        state.push(bv(inst.operand or 0))
    elif name.startswith("DUP"):
        depth = int(name[3:])
        state.push(state.stack[-depth] if len(state.stack) >= depth else state.fresh("underflow"))
    elif name.startswith("SWAP"):
        depth = int(name[4:])
        while len(state.stack) <= depth:
            state.stack.insert(0, state.fresh("underflow"))
        state.stack[-1], state.stack[-depth - 1] = state.stack[-depth - 1], state.stack[-1]
    elif name in BINARY_OPS:
        left, right = state.pop(), state.pop()
        state.push(z3.simplify(BINARY_OPS[name](left, right)))
    elif name in ENV_SYMBOLS:
        state.push(state.env(ENV_SYMBOLS[name]))
    else:
        _execute_other(state, inst)


def _execute_other(state: SymbolicState, inst: Any) -> None:
    name = inst.name
    if name == "ISZERO":
        state.push(flag(state.pop() == 0))
    elif name == "NOT":
        state.push(~state.pop())
    elif name == "CALLDATALOAD":
        state.push(calldata_word(state, state.pop()))
    elif name in ("SHA3", "KECCAK256"):
        offset, size = state.pop(), state.pop()
        state.push(keccak(state, offset, size))
    elif name in ("MLOAD", "MSTORE", "MSTORE8", "SLOAD", "SSTORE"):
        _execute_memory_storage(state, name)
    elif name in ("CALLDATACOPY", "CODECOPY", "RETURNDATACOPY", "EXTCODECOPY", "MCOPY"):
        operands = [state.pop() for _ in range(inst.pops)]
        destination, length = (operands[1], operands[3]) if name == "EXTCODECOPY" else (operands[0], operands[2])
        invalidate_memory(state, concrete(destination), concrete(length))
    elif name in STATE_CHANGING_CALLS or name == "STATICCALL":
        _execute_call(state, inst)
    elif name in ("EXP", "BYTE", "SIGNEXTEND"):
        state.push(_fold_concrete(state, name, state.pop(), state.pop()))
    elif name == "PC":
        state.push(bv(inst.pc))
    else:
        for _ in range(inst.pops):
            state.pop()
        for _ in range(inst.pushes):
            state.push(state.fresh(name.lower()))


def _attacker_havoc(state: SymbolicState, name: str, operands: List[z3.BitVecRef],
                    havoc: z3.ArrayRef) -> z3.ArrayRef:
    """Under the attacker model, only a callee that is the attacker can change storage by re-entering.
    DELEGATECALL and CREATE run foreign code in or for this contract, so they always forget storage."""
    if name not in ("CALL", "CALLCODE"):
        return havoc
    callee = operands[1] & bv(ADDRESS_MASK)
    return z3.If(callee == state.attacker, havoc, state.storage)


def _fold_concrete(state: SymbolicState, name: str, first: z3.BitVecRef, second: z3.BitVecRef) -> z3.BitVecRef:
    """EXP, BYTE and SIGNEXTEND, computed exactly when both operands are concrete."""
    a, b = concrete(first), concrete(second)
    if name == "EXP" and a is not None and b is not None:
        return bv(pow(a, b, 1 << WORD_BITS))
    if name == "EXP" and a is not None:
        shift = power_of_two(bv(a))
        if shift is not None and a > 1:
            return z3.simplify(bv(1) << (second * shift))
    if name == "BYTE" and a is not None:
        return z3.simplify(bv(0) if a >= WORD_BYTES else z3.LShR(second, bv(8 * (31 - a))) & bv(0xFF))
    if name == "SIGNEXTEND" and a is not None:
        bits = 8 * (a + 1)
        return second if bits >= WORD_BITS else z3.SignExt(WORD_BITS - bits, z3.Extract(bits - 1, 0, second))
    return state.fresh(name.lower())


def _execute_memory_storage(state: SymbolicState, name: str) -> None:
    if name == "MLOAD":
        state.push(load_memory_word(state, state.pop()))
    elif name == "MSTORE":
        offset, value = state.pop(), state.pop()
        store_memory_word(state, offset, value)
    elif name == "MSTORE8":
        offset, _ = state.pop(), state.pop()
        invalidate_memory(state, concrete(offset), 1)
    elif name == "SLOAD":
        key = state.pop()
        state.sloads.append(key)
        state.push(z3.Select(state.storage, key))
    else:
        key, value = state.pop(), state.pop()
        state.storage = z3.Store(state.storage, key, value)


def _execute_call(state: SymbolicState, inst: Any) -> None:
    """An external call: record its operands, then forget storage the callee may change by re-entering."""
    operands = [state.pop() for _ in range(inst.pops)]
    if inst.name in ("CALL", "CALLCODE"):
        state.call_operands = {"gas": operands[0], "target": operands[1], "value": operands[2]}
        out_offset, out_size = operands[5], operands[6]
        invalidate_memory(state, concrete(out_offset), concrete(out_size))
    elif inst.name in ("DELEGATECALL", "STATICCALL"):
        invalidate_memory(state, concrete(operands[4]), concrete(operands[5]))
    if inst.name in STATE_CHANGING_CALLS:
        state.storage_at_call = state.storage
        state.sloads_at_call = len(state.sloads)
        havoc = z3.Array(state.fresh("storage_after_call").decl().name(), z3.BitVecSort(WORD_BITS),
                         z3.BitVecSort(WORD_BITS))
        state.storage = havoc if state.attacker is None else _attacker_havoc(state, inst.name, operands, havoc)
    state.push(state.fresh("call_result"))
