"""py-evm sandbox used to replay witness transactions under Cancun rules.

Runtime bytecode is installed directly as account code, so no constructor runs.
Every transaction is sent from one externally owned account and its state
effects are read back with storage and balance queries.
"""

from typing import Any, Dict, Optional

from eth.chains.base import MiningChain
from eth.tools.builder.chain import build, cancun_at, disable_pow_check, genesis
from eth_keys import keys
from eth_utils import to_wei

WORD_BYTES = 32
ADDRESS_BYTES = 20
BLOCK_GAS_LIMIT = 30_000_000
TX_GAS_LIMIT = 3_000_000
GAS_PRICE_WEI = 10 ** 9
SANDBOX_GAS_LIMIT = 1_500_000
GENESIS_PARAMS = {
    "gas_limit": BLOCK_GAS_LIMIT,
    "difficulty": 0,
    "nonce": b"\x00" * 8,
    "mix_hash": b"\x00" * 32,
    "extra_data": b"",
}
EOA_KEY = keys.PrivateKey(b"\x13\x37" * 16)
EOA_ADDRESS = EOA_KEY.public_key.to_canonical_address()
EOA_FUNDING_WEI = to_wei(100, "ether")
VICTIM_ADDRESS = (0xDEF1).to_bytes(ADDRESS_BYTES, "big")
ATTACKER_ADDRESS = (0xA77A).to_bytes(ADDRESS_BYTES, "big")
PROBE_ADDRESS = (0xBEEF).to_bytes(ADDRESS_BYTES, "big")


def word(value: int) -> bytes:
    """ABI-encode one 256-bit word."""
    return (value % (1 << 256)).to_bytes(WORD_BYTES, "big")


def address_word(address: bytes) -> bytes:
    return b"\x00" * (WORD_BYTES - ADDRESS_BYTES) + address


def runtime_bytes(runtime_hex: str) -> bytes:
    clean = runtime_hex[2:] if runtime_hex.startswith("0x") else runtime_hex
    return bytes.fromhex(clean)


def account(code: bytes = b"", storage: Optional[Dict[int, int]] = None, balance: int = 0) -> Dict[str, Any]:
    return {"balance": balance, "code": code, "storage": dict(storage or {}), "nonce": 0}


class Sandbox:
    """One fresh chain per replay. Transactions are sent from EOA_KEY with a gas price above the base fee."""

    def __init__(self, accounts: Dict[bytes, Dict[str, Any]]):
        state = {EOA_ADDRESS: account(balance=EOA_FUNDING_WEI)}
        state.update(accounts)
        self._chain = build(
            MiningChain,
            cancun_at(0),
            disable_pow_check(),
            genesis(params=GENESIS_PARAMS, state=state),
        )
        self._nonce = 0

    def send(self, to: bytes, data: bytes, value: int = 0, gas: int = TX_GAS_LIMIT):
        """Send one transaction and return its py-evm computation (check is_error and gas remaining)."""
        vm = self._chain.get_vm()
        unsigned = vm.create_unsigned_transaction(
            nonce=self._nonce, gas_price=GAS_PRICE_WEI, gas=gas, to=to, value=value, data=data
        )
        self._nonce += 1
        _, _, computation = self._chain.apply_transaction(unsigned.as_signed_transaction(EOA_KEY))
        return computation

    def storage(self, address: bytes, slot: int) -> int:
        return self._chain.get_vm().state.get_storage(address, slot)

    def balance(self, address: bytes) -> int:
        return self._chain.get_vm().state.get_balance(address)
