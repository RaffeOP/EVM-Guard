"""Switches for the components that the ablation study removes one at a time.

Every switch is on by default. An engine built without options therefore runs the
configuration reported in the paper, and the switches only change behaviour when
an ablation sets them. Each switch names one component of the reentrancy check
or of the disassembly step, so a result can be attributed to that component.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EngineOptions:
    should_strip_cbor: bool = True
    should_decode_push0: bool = True
    should_propagate_gas_bounds: bool = True
    should_apply_stipend_bound: bool = True
    should_recognise_constant_mutex: bool = True
    should_recognise_slot_mutex: bool = True
    should_require_mutex_dominance: bool = True


FULL_ENGINE = EngineOptions()

# The pre-fix engine (v2) had constant-gas stipend checks, no slot-based mutex rule,
# and no PUSH0 decoding. It already stripped the CBOR trailer.
PRE_FIX_V2 = EngineOptions(
    should_propagate_gas_bounds=False,
    should_recognise_slot_mutex=False,
    should_decode_push0=False,
)

ABLATIONS = {
    "full": FULL_ENGINE,
    "no_stipend_exclusion": EngineOptions(should_apply_stipend_bound=False),
    "constant_gas_only": EngineOptions(should_propagate_gas_bounds=False),
    "no_slot_mutex": EngineOptions(should_recognise_slot_mutex=False),
    "no_mutex": EngineOptions(should_recognise_constant_mutex=False,
                              should_recognise_slot_mutex=False),
    "mutex_by_reachability": EngineOptions(should_require_mutex_dominance=False),
    "no_push0_decode": EngineOptions(should_decode_push0=False),
    "no_cbor_strip": EngineOptions(should_strip_cbor=False),
    "pre_fix_v2": PRE_FIX_V2,
}
