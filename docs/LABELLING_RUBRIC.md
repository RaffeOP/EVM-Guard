# Labelling rubric for the hand-checked mainnet sample (protocol 7)

Each sampled contract is labelled from its verified source, without knowing which engine
flagged it. The label refers to reentrancy (SWC-107) only.

## Label `exploitable`

All of the following hold for some public or external function `f`:

1. `f` makes an external call that forwards more than the 2,300-gas stipend (a low-level
   `call`, a call to an interface, or `call.value`), to an address the attacker controls:
   `msg.sender`, an argument, or an address the attacker can register or set without a
   privileged role.
2. On some path, `f` updates storage after that call, or another public function reads, during
   the call, storage that `f` has not yet updated.
3. An unprivileged account can execute that path: every `require`, modifier and branch before
   the call can be satisfied by a caller with no special role, in a state an attacker can reach
   by ordinary transactions.
4. Re-entering during the call (into `f` or into the function from 2) lets the attacker obtain
   something it could not obtain without re-entry: more ether or tokens, or a state change it
   could not otherwise make. No lock (a boolean or counter guard, `nonReentrant`) prevents it.

## Label `privileged-only`

1, 2 and 4 hold, but 3 fails because only the owner or another privileged role can reach the
call, or the callee is an address fixed by a privileged role (an owner-set wallet, a token
contract configured by an admin).

## Label `not-exploitable`

The call cannot re-enter (stipend only, or the callee is a fixed trusted contract), or no
storage is updated after it and no stale read gives the attacker anything, or a lock blocks
re-entry, or re-entry gains the attacker nothing (the effect only hurts the attacker).

## Label `undetermined`

The source does not allow a decision (missing library code, assembly that cannot be followed,
or behaviour that depends on an external contract whose code is not available).

## Scoring

A flag is a true positive if the label is `exploitable`. `privileged-only`, `not-exploitable`
and `undetermined` are reported separately; the precision in the paper counts only
`exploitable` as correct and reports `undetermined` as a separate count, not as an error.
For each label the rater records the function, the source lines of the call and of the later
write or stale read, and one sentence of justification.
