# Disclosure log, protocol 7 mainnet sample

Written 2026-11-01, after the blind labels were locked
(`results/protocol7/mainnet_labels_blind.sha256`). Aggregate only, as the protocol requires.

- Contracts labelled `exploitable`: 1 of 120 sampled (flagged by both v5 and v6).
- Balance at the corpus block (26,319,084): below 0.001 ether.
- Kind: a re-entrant call into a public payout loop lets a depositor skip the remaining
  payout queue of other depositors; it does not let the attacker take more than the
  contract's balance.
- Nothing was executed against the contract, on mainnet, a fork or a sandbox.
- Contact channel: none found. The verified source names no author, project, site or
  address for reports and states that the code is an unmaintained educational example
  placed in the public domain; no bug-bounty listing exists for it.
- Action: none sent. The address is not published in the paper or in tracked files; the
  files that would identify it are excluded from version control (see `.gitignore`).
