"""Falsifiable replay oracles, one per hazard class that has a state-level criterion.

A finding is confirmed only when the on-chain post-state meets the class's
criterion. Executing without reverting is never sufficient.

SWC-101 and SWC-114 have no oracle here: a truncation or spot-price effect
has no state criterion that this sandbox can check without a per-contract
economic model, so those findings are never marked confirmed.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple

from replay_probes import (
    ATTACKER_CODE,
    PROBE_ARGUMENT_WORDS,
    PROBE_CODE,
    PROBE_MARK_SLOT,
    PROBE_MARK_VALUE,
)
from replay_sandbox import (
    ATTACKER_ADDRESS,
    EOA_ADDRESS,
    address_word,
    PROBE_ADDRESS,
    SANDBOX_GAS_LIMIT,
    VICTIM_ADDRESS,
    Sandbox,
    account,
    runtime_bytes,
    word,
)

ETHER_WEI = 10 ** 18
VICTIM_FUNDING_WEI = 10 * ETHER_WEI
DEPOSIT_WEI = ETHER_WEI
ADDRESS_WIDTH_BITS = 160
REENTRY_FLAG_SLOT = 0
INFLATED_LOOP_LENGTH = 10 ** 6
COLLISION_PROBE_WORD = 2 ** 200 + 1
CALLDATA_WORDS = 4
OWNER_WORD = int.from_bytes(EOA_ADDRESS, "big")
Oracle = Callable[[str, Dict[str, Any]], Tuple[bool, Dict[str, Any]]]


def _selector_bytes(selector: str) -> bytes:
    return bytes.fromhex(selector[2:])


def _withdraw_variants(selector: str) -> List[bytes]:
    """Calldata with no arguments, and with a 1-ETH amount argument."""
    base = _selector_bytes(selector)
    return [base, base + word(DEPOSIT_WEI)]


def _deposit_variants(selector: str) -> List[bytes]:
    """Calldata that credits the attacker: no arguments, the attacker as an address argument, or a 1-ETH amount."""
    base = _selector_bytes(selector)
    return [base, base + address_word(ATTACKER_ADDRESS), base + word(DEPOSIT_WEI)]


def _victim(runtime_hex: str, storage: Optional[Dict[int, int]] = None) -> Dict[bytes, Dict[str, Any]]:
    return {VICTIM_ADDRESS: account(runtime_bytes(runtime_hex), storage=storage, balance=VICTIM_FUNDING_WEI)}


def _reentrancy_attempt(runtime_hex: str, deposit: Optional[Tuple[bytes, int]],
                        withdraw_data: bytes) -> Tuple[bool, Dict[str, Any]]:
    """One attack: optional deposit through the attacker, then a withdraw that may re-enter."""
    accounts = _victim(runtime_hex)
    accounts[ATTACKER_ADDRESS] = account(ATTACKER_CODE)
    sandbox = Sandbox(accounts)
    deposited = 0
    if deposit is not None:
        deposit_data, deposited = deposit
        sandbox.send(ATTACKER_ADDRESS, deposit_data, value=deposited)
    before = sandbox.balance(ATTACKER_ADDRESS)
    sandbox.send(ATTACKER_ADDRESS, withdraw_data)
    gained = sandbox.balance(ATTACKER_ADDRESS) - before
    reentered = sandbox.storage(ATTACKER_ADDRESS, REENTRY_FLAG_SLOT) == 1
    detail = {"deposit_wei": deposited, "gained_wei": gained, "reentered": reentered}
    return reentered and gained > deposited, detail


def replay_reentrancy(runtime_hex: str, payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """Confirmed when the victim calls back into the attacker and the attacker's gain exceeds its deposit."""
    deposits: List[Optional[Tuple[bytes, int]]] = [None]
    deposits += [(data, DEPOSIT_WEI) for sel in payload["all_selectors"] for data in _deposit_variants(sel)]
    withdraws = [data for sel in payload["selectors"] for data in _withdraw_variants(sel)]
    for deposit in deposits:
        for withdraw_data in withdraws:
            verified, detail = _reentrancy_attempt(runtime_hex, deposit, withdraw_data)
            if verified:
                return True, detail
    return False, {"attempts": len(deposits) * len(withdraws)}


def replay_delegatecall_taint(runtime_hex: str, payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """Confirmed when the victim executes probe code in its own storage context, which requires the
    DELEGATECALL target to be the attacker-supplied probe address."""
    for selector in payload["selectors"]:
        sandbox = Sandbox({**_victim(runtime_hex), PROBE_ADDRESS: account(PROBE_CODE)})
        sandbox.send(VICTIM_ADDRESS, _selector_bytes(selector) + PROBE_ARGUMENT_WORDS)
        if sandbox.storage(VICTIM_ADDRESS, PROBE_MARK_SLOT) == PROBE_MARK_VALUE:
            return True, {"selector": selector}
    return False, {}


def replay_storage_collision(runtime_hex: str, payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """Confirmed when a call overwrites slot 0, which holds an address, with a value wider than 160 bits."""
    wide_arguments = word(COLLISION_PROBE_WORD) * CALLDATA_WORDS
    for selector in payload["selectors"]:
        sandbox = Sandbox(_victim(runtime_hex, storage={0: OWNER_WORD}))
        before = sandbox.storage(VICTIM_ADDRESS, 0)
        sandbox.send(VICTIM_ADDRESS, _selector_bytes(selector) + wide_arguments)
        after = sandbox.storage(VICTIM_ADDRESS, 0)
        if before < 2 ** ADDRESS_WIDTH_BITS <= after:
            return True, {"selector": selector, "slot0_after": hex(after)}
    return False, {}


def replay_unbounded_loop(runtime_hex: str, payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """Confirmed when a call that completes on the original storage exhausts the sandbox gas limit
    after the loop bound slot is set to a large length."""
    slot = payload.get("loop_slot")
    if slot is None:
        return False, {"reason": "loop bound slot is not a constant"}
    for selector in payload["selectors"]:
        data = _selector_bytes(selector)
        baseline = Sandbox(_victim(runtime_hex)).send(VICTIM_ADDRESS, data, gas=SANDBOX_GAS_LIMIT)
        inflated = Sandbox(_victim(runtime_hex, storage={slot: INFLATED_LOOP_LENGTH}))
        computation = inflated.send(VICTIM_ADDRESS, data, gas=SANDBOX_GAS_LIMIT)
        exhausted = computation.is_error and computation.get_gas_remaining() == 0
        if exhausted and not baseline.is_error:
            return True, {"selector": selector, "bound_slot": slot}
    return False, {}


ORACLES: Dict[str, Oracle] = {
    "SWC-107": replay_reentrancy,
    "SWC-112": replay_delegatecall_taint,
    "SWC-124": replay_storage_collision,
    "SWC-128": replay_unbounded_loop,
}
