"""Engine configurations: the components each version enables, one switch per component.

FULL_ENGINE is engine v6. ENGINE_V5 turns off the four v6 components and reproduces the
v5 flags file by file; PRE_FIX_V2 also removes the v3 and v5 components. Ablations
remove one component at a time from v5 (ABLATIONS, as reported for v5) or from v6
(V6_ABLATIONS), so a result can be attributed to that component.
"""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class EngineOptions:
    should_strip_cbor: bool = True
    should_decode_push0: bool = True
    should_propagate_gas_bounds: bool = True
    should_apply_stipend_bound: bool = True
    should_recognise_constant_mutex: bool = True
    should_recognise_slot_mutex: bool = True
    should_require_mutex_dominance: bool = True
    should_track_return_sites: bool = True
    should_check_path_feasibility: bool = True
    should_assume_unprivileged_attacker: bool = True
    should_seed_replay_with_witness: bool = True


FULL_ENGINE = EngineOptions()
ENGINE_V5 = EngineOptions(
    should_track_return_sites=False,
    should_check_path_feasibility=False,
    should_assume_unprivileged_attacker=False,
    should_seed_replay_with_witness=False,
)
ENGINES = {"v5": ENGINE_V5, "v6": FULL_ENGINE}

# The pre-fix engine (v2) had constant-gas stipend checks, no slot-based mutex rule,
# and no PUSH0 decoding. It already stripped the CBOR trailer.
PRE_FIX_V2 = replace(
    ENGINE_V5,
    should_propagate_gas_bounds=False,
    should_recognise_slot_mutex=False,
    should_decode_push0=False,
)

ABLATIONS = {
    "full": ENGINE_V5,
    "no_stipend_exclusion": replace(ENGINE_V5, should_apply_stipend_bound=False),
    "constant_gas_only": replace(ENGINE_V5, should_propagate_gas_bounds=False),
    "no_slot_mutex": replace(ENGINE_V5, should_recognise_slot_mutex=False),
    "no_mutex": replace(ENGINE_V5, should_recognise_constant_mutex=False, should_recognise_slot_mutex=False),
    "mutex_by_reachability": replace(ENGINE_V5, should_require_mutex_dominance=False),
    "no_push0_decode": replace(ENGINE_V5, should_decode_push0=False),
    "no_cbor_strip": replace(ENGINE_V5, should_strip_cbor=False),
    "pre_fix_v2": PRE_FIX_V2,
}

V6_ABLATIONS = {
    "v6": FULL_ENGINE,
    "no_return_sites": replace(FULL_ENGINE, should_track_return_sites=False),
    "no_path_feasibility": replace(FULL_ENGINE, should_check_path_feasibility=False),
    "no_attacker_model": replace(FULL_ENGINE, should_assume_unprivileged_attacker=False),
    "no_heuristic_mutex": replace(FULL_ENGINE, should_recognise_constant_mutex=False,
                                  should_recognise_slot_mutex=False),
    "v5": ENGINE_V5,
}
