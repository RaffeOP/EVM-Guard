"""Engine v6: return-site tracking, Z3 path feasibility, the attacker model and witness replay.

Each fixture in tests/fixtures is a small contract with its runtime bytecode stored as .hex
(rebuild with tests/fixtures/build_fixtures.py), so these tests need no compiler.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import z3  # noqa: E402

from engine_options import ENGINE_V5, FULL_ENGINE, V6_ABLATIONS  # noqa: E402
from exploit_synthesizer import ExploitSynthesizer  # noqa: E402
from symbolic_engine import SymbolicEVMInterpreter  # noqa: E402
from symbolic_path import HASH_LOWER_BOUND, SymbolicState, bv, concrete, execute  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def runtime(name: str) -> str:
    with open(os.path.join(FIXTURES, f"{name}.hex"), encoding="utf-8") as handle:
        return handle.read().strip()


def reentrancy_findings(name: str, options=FULL_ENGINE) -> list:
    report = SymbolicEVMInterpreter(options=options).analyze_bytecode(name, runtime(name), target_swc="SWC-107")
    return report["findings"]


class Instruction:
    """The fields of a pyevmasm instruction that the symbolic executor reads."""

    def __init__(self, name: str, operand: int = 0, pops: int = 0, pushes: int = 0):
        self.name, self.operand, self.pops, self.pushes, self.pc = name, operand, pops, pushes, 0


def run(*instructions: Instruction) -> SymbolicState:
    state = SymbolicState("test")
    for inst in instructions:
        execute(state, inst)
    return state


class SymbolicExecutorTest(unittest.TestCase):
    def test_division_by_power_of_two_is_exact(self):
        state = run(Instruction("PUSH32", 1 << 224), Instruction("PUSH32", 0xABCD << 224), Instruction("DIV"))
        self.assertEqual(concrete(state.stack[-1]), 0xABCD)

    def test_exp_with_concrete_operands_folds(self):
        state = run(Instruction("PUSH1", 3), Instruction("PUSH2", 0x100), Instruction("EXP"))
        self.assertEqual(concrete(state.stack[-1]), 0x100 ** 3)

    def test_memory_word_round_trips(self):
        state = run(Instruction("PUSH1", 7), Instruction("PUSH1", 0x40), Instruction("MSTORE"),
                    Instruction("PUSH1", 0x40), Instruction("MLOAD"))
        self.assertEqual(concrete(state.stack[-1]), 7)

    def test_keccak_output_is_bounded_away_from_low_slots(self):
        state = run(Instruction("PUSH1", 1), Instruction("PUSH1", 0), Instruction("MSTORE"),
                    Instruction("PUSH1", 32), Instruction("PUSH1", 0), Instruction("SHA3"))
        solver = z3.Solver()
        solver.add(*state.pending, state.stack[-1] == bv(5))
        self.assertEqual(solver.check(), z3.unsat)
        self.assertEqual(len(state.pending), 1)
        self.assertIn(str(HASH_LOWER_BOUND), str(state.pending[0]))


class ReentrancyDecisionTest(unittest.TestCase):
    def test_should_flag_same_function_reentrancy(self):
        findings = reentrancy_findings("same_function")
        self.assertEqual(findings[0]["witness"]["reentrancy_kind"], "same-function")

    def test_should_reject_owner_only_call_under_attacker_model(self):
        self.assertTrue(reentrancy_findings("owner_only", ENGINE_V5))
        self.assertFalse(reentrancy_findings("owner_only"))

    def test_should_keep_owner_only_call_without_attacker_model(self):
        self.assertTrue(reentrancy_findings("owner_only", V6_ABLATIONS["no_attacker_model"]))

    def test_should_reject_same_function_reentry_through_packed_lock_by_solver_alone(self):
        findings = reentrancy_findings("packed_mutex", V6_ABLATIONS["no_heuristic_mutex"])
        self.assertTrue(all(f["witness"]["reentrancy_kind"] != "same-function" for f in findings))

    def test_should_find_call_in_internal_helper_only_with_return_sites(self):
        self.assertFalse(reentrancy_findings("internal_helper", ENGINE_V5))
        self.assertTrue(reentrancy_findings("internal_helper", V6_ABLATIONS["v6"]))
        self.assertFalse(reentrancy_findings("internal_helper", V6_ABLATIONS["no_return_sites"]))

    def test_should_flag_solidity_08_reentrancy(self):
        self.assertTrue(reentrancy_findings("same_function_08"))


class WitnessReplayTest(unittest.TestCase):
    def confirm(self, name: str, options=FULL_ENGINE) -> list:
        report = SymbolicEVMInterpreter(options=options).analyze_bytecode(name, runtime(name), target_swc="SWC-107")
        synthesizer = ExploitSynthesizer()
        payloads = [synthesizer.synthesize_payload_for_finding(f, report["dynamic_selectors"])
                    for f in report["findings"]]
        return [synthesizer.replay_with_witness(p, runtime(name)) for p in payloads]

    def test_witness_replay_confirms_real_reentrancy(self):
        self.assertEqual(self.confirm("same_function"), [True])
        self.assertEqual(self.confirm("internal_helper"), [True])

    def test_witness_replay_does_not_confirm_a_blocked_reentry(self):
        self.assertNotIn(True, self.confirm("packed_mutex", V6_ABLATIONS["no_heuristic_mutex"]))


if __name__ == "__main__":
    unittest.main()
