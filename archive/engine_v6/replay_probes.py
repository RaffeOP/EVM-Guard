"""Hand-assembled probe contracts for the replay oracles.

The sandbox has no Solidity compiler, so the probes are written as EVM
assembly and assembled here. Each probe has a fixed, documented behavior that
the oracles check on-chain.

Reentrancy attacker storage layout:
  slot 0: re-entry flag (set to 1 when the attacker re-enters the victim)
  slot 1-4: the first 128 bytes of the outer calldata
  slot 5: the outer calldata length
Outer calls are forwarded to the victim with the same calldata and value.
A plain ETH receipt (no calldata) re-enters the victim once with the stored calldata.
"""

from typing import List, Tuple, Union

from replay_sandbox import PROBE_ADDRESS, VICTIM_ADDRESS, address_word

OPCODES = {
    "STOP": 0x00, "ADD": 0x01, "CALLER": 0x33, "ISZERO": 0x15, "CALLVALUE": 0x34, "CALLDATALOAD": 0x35,
    "CALLDATASIZE": 0x36, "DUP1": 0x80, "DUP5": 0x84, "CALLDATACOPY": 0x37, "POP": 0x50, "MSTORE": 0x52, "SLOAD": 0x54,
    "SSTORE": 0x55, "JUMPI": 0x57, "GAS": 0x5A, "JUMPDEST": 0x5B,
    "CALL": 0xF1,
}
PUSH1, PUSH2 = 0x60, 0x61
CALLDATA_WORDS = 4
WORD_SIZE = 32
Item = Union[str, Tuple[str, int, int], Tuple[str, str]]


def push(value: int, size: int) -> List[Item]:
    return [("PUSH", value, size)]


def label_ref(name: str) -> Item:
    return ("PUSHL", name)


def assemble(items: List[Item]) -> bytes:
    """Two-pass assembler: PUSH n literal, PUSHL label (PUSH2 of a JUMPDEST offset), LABEL pseudo-op."""
    labels = {}
    position = 0
    for item in items:
        if isinstance(item, tuple) and item[0] == "LABEL":
            labels[item[1]] = position
        elif isinstance(item, tuple) and item[0] == "PUSH":
            position += 1 + item[2]
        elif isinstance(item, tuple) and item[0] == "PUSHL":
            position += 3
        else:
            position += 1
    code = bytearray()
    for item in items:
        if isinstance(item, tuple) and item[0] == "LABEL":
            continue
        if isinstance(item, tuple) and item[0] == "PUSH":
            code.append(PUSH1 + item[2] - 1)
            code += item[1].to_bytes(item[2], "big")
        elif isinstance(item, tuple) and item[0] == "PUSHL":
            code.append(PUSH2)
            code += labels[item[1]].to_bytes(2, "big")
        else:
            code.append(OPCODES[item])
    return bytes(code)


def _store_outer_calldata() -> List[Item]:
    items: List[Item] = []
    items += push(0, 1) + push(0, 1) + ["SSTORE"]
    items += ["CALLDATASIZE"] + push(5, 1) + ["SSTORE"]
    for index in range(CALLDATA_WORDS):
        items += push(WORD_SIZE * index, 1) + ["CALLDATALOAD"] + push(1 + index, 1) + ["SSTORE"]
    return items


def _forward_outer_call() -> List[Item]:
    items: List[Item] = []
    items += ["CALLDATASIZE"] + push(0, 1) + push(0, 1) + ["CALLDATACOPY"]
    items += push(0, 1) + push(0, 1) + ["CALLDATASIZE"] + push(0, 1) + ["CALLVALUE"]
    items += [("PUSH", int.from_bytes(VICTIM_ADDRESS, "big"), 20), "GAS", "CALL", "POP", "STOP"]
    return items


def _reenter_victim() -> List[Item]:
    items: List[Item] = [("LABEL", "reenter"), "JUMPDEST"]
    items += push(1, 1) + push(0, 1) + ["SSTORE"]
    for index in range(CALLDATA_WORDS):
        items += push(1 + index, 1) + ["SLOAD"] + push(WORD_SIZE * index, 1) + ["MSTORE"]
    items += push(0, 1) + push(0, 1) + push(5, 1) + ["SLOAD"] + push(0, 1) + push(0, 1)
    items += [("PUSH", int.from_bytes(VICTIM_ADDRESS, "big"), 20), "GAS", "CALL", "POP", "STOP"]
    return items


def attacker_code() -> bytes:
    """Attacker runtime: outer calls forward calldata and value; a receipt re-enters once."""
    items: List[Item] = ["CALLDATASIZE", "ISZERO", label_ref("receive"), "JUMPI"]
    items += _store_outer_calldata()
    items += _forward_outer_call()
    items += [("LABEL", "receive"), "JUMPDEST"]
    items += push(0, 1) + ["SLOAD", "ISZERO", label_ref("reenter"), "JUMPI", "STOP"]
    items += _reenter_victim()
    return assemble(items)


def passive_attacker_code() -> bytes:
    """Control for the witness replay: forwards outer calls like the attacker, but a receipt only
    stops, so the victim's call completes without re-entry."""
    items: List[Item] = ["CALLDATASIZE", "ISZERO", label_ref("receive"), "JUMPI"]
    items += _store_outer_calldata()
    items += _forward_outer_call()
    items += [("LABEL", "receive"), "JUMPDEST", "STOP"]
    return assemble(items)


def delegatecall_probe_code() -> bytes:
    """Probe logic: writes 0x2a to slot 0x5afe of whichever context runs it."""
    return assemble(push(0x2A, 1) + push(PROBE_MARK_SLOT, 2) + ["SSTORE", "STOP"])


PROBE_MARK_SLOT = 0x5AFE
PROBE_MARK_VALUE = 0x2A
PROBE_CODE = delegatecall_probe_code()
ATTACKER_CODE = attacker_code()
PASSIVE_ATTACKER_CODE = passive_attacker_code()
PROBE_ARGUMENT_WORDS = address_word(PROBE_ADDRESS) * CALLDATA_WORDS
