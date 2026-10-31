"""PUSH0 (0x5f) decodes as PUSH0, not INVALID, and keeps the following instructions aligned."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from evm_disasm import disassemble_bytes  # noqa: E402


class Push0DisassemblyTest(unittest.TestCase):
    def test_push0_is_decoded_as_push0(self):
        names = [inst.name for inst in disassemble_bytes(bytes([0x5F, 0x35]))]
        self.assertEqual(names, ["PUSH0", "CALLDATALOAD"])

    def test_push0_operand_is_zero(self):
        push0 = disassemble_bytes(bytes([0x5F]))[0]
        self.assertEqual(push0.operand, 0)
        self.assertEqual(push0.pc, 0)

    def test_following_offsets_stay_aligned(self):
        instructions = disassemble_bytes(bytes([0x5F, 0x60, 0x01, 0x5F]))
        self.assertEqual([inst.pc for inst in instructions], [0, 1, 3])

    def test_real_invalid_opcode_stays_invalid(self):
        names = [inst.name for inst in disassemble_bytes(bytes([0xFE]))]
        self.assertEqual(names, ["INVALID"])


if __name__ == "__main__":
    unittest.main()
