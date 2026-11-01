"""
EVM-Guard hazard analyzer for runtime bytecode.

Pipeline per contract:
  1. Strip the solc CBOR metadata trailer and disassemble with pyevmasm.
  2. Build a basic-block CFG and run an abstract stack dataflow (evm_dataflow).
  3. Run one path-sensitive check per hazard class (hazard_rules) over the CFG,
     dominators, function regions and natural loops (evm_regions).
  4. For each check that fires, ask the Z3 template encoder for a witness.

A finding means the bytecode matches a dataflow pattern. It is not a proof of
exploitability or of safety. Witness replay is handled by exploit_synthesizer.
"""

import os
import sys
import time
from typing import Any, Dict, List, Optional

import pyevmasm

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(WORKSPACE_DIR, "src")
for path in (WORKSPACE_DIR, SRC_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from src.z3_encoder import Z3EVMEncoder  # noqa: E402

from engine_options import FULL_ENGINE, EngineOptions  # noqa: E402
from evm_disasm import disassemble_bytes  # noqa: E402
from evm_dataflow import FlowGraph, analyze_flow  # noqa: E402
from evm_regions import (  # noqa: E402
    Dominance,
    dispatch_entries,
    erc1967_present,
    function_scopes,
    selectors_containing,
)
import hazard_rules as rules  # noqa: E402

ERC1967_SLOT_HEX = "360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
SWC_NAMES = {
    "SWC-107": "Cross-Contract Read-Only Reentrancy",
    "SWC-101": "Fixed-Point Precision Loss & Truncation",
    "SWC-112": "Delegatecall to Untrusted Callee",
    "SWC-124": "Proxy Storage-Slot Layout Collision",
    "SWC-128": "DoS With Block Gas Limit via Unbounded Loop",
    "SWC-114": "Transaction Order / Oracle Manipulation",
}
SELECTOR_CUTOFF_PC = 1000
CHECK_ORDER = ["SWC-107", "SWC-101", "SWC-112", "SWC-124", "SWC-128", "SWC-114"]


def cyclomatic_complexity(graph: FlowGraph) -> int:
    """McCabe complexity E - N + 2 over the reachable CFG."""
    edges = sum(len(graph.successors.get(node, [])) for node in graph.reachable)
    return edges - len(graph.reachable) + 2

class SymbolicEVMInterpreter:
    def __init__(self, timeout_ms: int = 5000, options: EngineOptions = FULL_ENGINE):
        self.encoder = Z3EVMEncoder(solver_timeout_ms=timeout_ms)
        self.options = options

    @staticmethod
    def strip_cbor_metadata(bytecode_bytes: bytes) -> bytes:
        """Strip solc auxiliary CBOR metadata trailer (Bzzr/IPFS hash) to prevent disassembly of non-code hash bytes."""
        if len(bytecode_bytes) < 4:
            return bytecode_bytes
        cbor_len = int.from_bytes(bytecode_bytes[-2:], "big")
        if 10 < cbor_len < 120 and len(bytecode_bytes) > cbor_len + 2:
            if bytecode_bytes[-(cbor_len + 2)] == 0xa2:
                return bytecode_bytes[:-(cbor_len + 2)]
        return bytecode_bytes

    def disassemble(self, bytecode_hex: str) -> List[Any]:
        """Disassemble raw EVM bytecode into pyevmasm Instruction objects."""
        if bytecode_hex.startswith("0x"):
            bytecode_hex = bytecode_hex[2:]
        if not bytecode_hex:
            return []
        try:
            bytecode_bytes = bytes.fromhex(bytecode_hex)
            clean_bytes = self.strip_cbor_metadata(bytecode_bytes) if self.options.should_strip_cbor else bytecode_bytes
            return disassemble_bytes(clean_bytes, should_decode_push0=self.options.should_decode_push0)
        except Exception:
            return []

    def extract_dynamic_selectors(self, instructions: List[Any]) -> List[str]:
        """Return 4-byte selectors from PUSH4 followed by EQ in the dispatcher region (pc < 1000)."""
        selectors = []
        count = len(instructions)
        for index, inst in enumerate(instructions):
            if inst.pc > SELECTOR_CUTOFF_PC:
                break
            if not (inst.name.startswith("PUSH") and inst.name != "PUSH0" and inst.operand is not None):
                continue
            followed_by_eq = index + 1 < count and instructions[index + 1].name == "EQ"
            followed_by_eq_later = index + 2 < count and instructions[index + 2].name == "EQ"
            if followed_by_eq or followed_by_eq_later:
                selector = hex(inst.operand)[2:].zfill(8)
                if len(selector) == 8:
                    selectors.append("0x" + selector)
        return list(dict.fromkeys(selectors))

    def analyze_bytecode(
        self,
        contract_name: str,
        bytecode_hex: str,
        target_swc: Optional[str] = None,
        v1_storage: Optional[List[Dict[str, Any]]] = None,
        v2_storage: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Analyze one runtime bytecode. The v1/v2 layout arguments are accepted for compatibility and ignored."""
        start_time = time.perf_counter()
        instructions = self.disassemble(bytecode_hex)
        if not instructions:
            return self._empty_report(contract_name, start_time)

        graph = analyze_flow(instructions)
        dominance = Dominance(graph)
        entries = dispatch_entries(instructions, graph.jumpdests)
        scopes = function_scopes(graph, entries)
        selectors = self.extract_dynamic_selectors(instructions)
        findings = []
        for swc in CHECK_ORDER:
            if target_swc is not None and target_swc != swc:
                continue
            evidence = self._run_check(swc, instructions, graph, dominance, scopes)
            if evidence is None:
                continue
            status, witness = self._solve(swc, instructions)
            if status == "SAT":
                witness.update(evidence)
                witness.setdefault("function_selectors", selectors_containing(scopes, evidence.get("block")))
                findings.append({"swc": swc, "name": SWC_NAMES[swc], "status": "SAT", "witness": witness})

        return {
            "contract_name": contract_name,
            "instruction_count": len(instructions),
            "cyclomatic_complexity": cyclomatic_complexity(graph),
            "basic_blocks_count": len(graph.block_ranges),
            "unresolved_jumps": graph.unresolved_jumps,
            "function_entries": len(entries),
            "dynamic_selectors": selectors,
            "execution_time_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            "findings_count": len(findings),
            "findings": findings,
        }

    def _run_check(self, swc: str, instructions: List[Any], graph: Any, dominance: Dominance,
                   scopes: Dict[str, set]) -> Optional[Dict[str, Any]]:
        if swc == "SWC-107":
            return rules.check_reentrancy(graph, dominance, scopes, self.options)
        if swc == "SWC-101":
            return rules.check_truncation(graph)
        if swc == "SWC-112":
            return rules.check_delegatecall_taint(graph, dominance)
        if swc == "SWC-124":
            return rules.check_proxy_collision(graph, erc1967_present(instructions))
        if swc == "SWC-128":
            return rules.check_unbounded_loop(graph, dominance, scopes)
        return rules.check_oracle_collapse(instructions)

    def _solve(self, swc: str, instructions: List[Any]) -> tuple:
        """Ask the Z3 template for witness parameters for a check that fired."""
        if swc == "SWC-107":
            return self.encoder.encode_swc107_read_only_reentrancy()
        if swc == "SWC-101":
            return self.encoder.encode_swc101_precision_loss()
        if swc == "SWC-112":
            return self.encoder.encode_swc112_delegatecall_taint(is_target_user_controlled=True)
        if swc == "SWC-124":
            return self._solve_collision(instructions)
        if swc == "SWC-128":
            return self.encoder.encode_swc128_unbounded_loop_gas_dos(is_mutator_unrestricted=True)
        return self.encoder.encode_swc114_atomic_oracle_collapse()

    def _solve_collision(self, instructions: List[Any]) -> tuple:
        """Collision query over the fixed layout pair used for proxies (slot 0 address vs uint256)."""
        erc1967 = erc1967_present(instructions)
        proxy_layout = [{"slot": 0, "name": "proxy_owner", "type": "address", "bit_width": 160}]
        if erc1967:
            impl_layout = [{"slot": int(ERC1967_SLOT_HEX, 16), "name": "impl_slot", "type": "address",
                            "bit_width": 160}]
        else:
            impl_layout = [{"slot": 0, "name": "impl_state", "type": "uint256", "bit_width": 256}]
        return self.encoder.encode_swc124_proxy_storage_collision(proxy_layout, impl_layout)

    @staticmethod
    def _empty_report(contract_name: str, start_time: float) -> Dict[str, Any]:
        return {
            "contract_name": contract_name,
            "instruction_count": 0,
            "cyclomatic_complexity": 1,
            "basic_blocks_count": 0,
            "unresolved_jumps": 0,
            "function_entries": 0,
            "dynamic_selectors": [],
            "execution_time_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            "findings_count": 0,
            "findings": [],
        }
