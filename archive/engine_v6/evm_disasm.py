"""Disassembly with PUSH0 (EIP-3855) support on top of pyevmasm.

pyevmasm does not know opcode 0x5f, so it decodes PUSH0 as INVALID. Both are one byte,
so decoding stays aligned and only the decoded instruction needs replacing. Solc 0.8.20
and later emit PUSH0 by default (Shanghai EVM), so without this step their CFG stops at
the first dispatcher branch.
"""
from typing import Any, List

import pyevmasm

PUSH0_OPCODE = 0x5F
PUSH0_FEE = 2


def _push0_at(pc: int) -> Any:
    return pyevmasm.evmasm.Instruction(opcode=PUSH0_OPCODE, name="PUSH0", operand_size=0, pops=0,
                                       pushes=1, fee=PUSH0_FEE, description="Place 0 on stack",
                                       operand=0, pc=pc)


def disassemble_bytes(code: bytes, should_decode_push0: bool = True) -> List[Any]:
    """Return pyevmasm instructions for the code, with PUSH0 decoded as PUSH0 unless disabled."""
    instructions = list(pyevmasm.disassemble_all(code))
    if not should_decode_push0:
        return instructions
    return [_push0_at(inst.pc) if inst.name == "INVALID" and code[inst.pc] == PUSH0_OPCODE else inst
            for inst in instructions]
