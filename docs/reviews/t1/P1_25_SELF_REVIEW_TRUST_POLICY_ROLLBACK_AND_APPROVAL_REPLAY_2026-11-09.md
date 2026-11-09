# P1.25 — Adversarial self-review of P1.24 trust-policy lifecycle and approval replay

Date: 2026-11-09  
Review type: Same-session adversarial static review; NOT independent.  
Exact normative contract blob reviewed: dd33b60649d8881ca935d34b62b8b54b6d0e9d42  
Prior verdict: P1.24 DOCUMENTATION-LEVEL PASS for F02-R5 signature/authentication design.  
Branch: feature/t0-centralized-data-feeder-p1-20261101

## Verdict

**REQUEST CHANGES — F02-R6 HIGH; F02-R7 MEDIUM; F02-R8 MEDIUM.**

P1.24 materially improves approval authenticity, but this follow-up review found unresolved trust-policy freshness/rollback, approval replay semantics, and post-revocation lifecycle behavior. Therefore the signed-approval design is not yet closed at contract level. Do not treat P1.24's narrower F02-R5 self-review PASS as proof that the entire approval lifecycle is complete.

## Findings

### F02-R6 — HIGH: external approver trust policy has no anti-rollback/version-freshness mechanism

Evidence in §22.9:
- The policy schema fixes `policy_version` to exact string `1.0`.
- `policy_id` is a UUIDv4 and `policy_digest_sha256` is computed from the policy's own canonical bytes.
- The policy is outside the source root and provisioned through a separate administrative channel.
- There is no monotonic policy revision/sequence, trusted latest-policy digest, append-only revocation record, or other mechanism to distinguish the current policy from an older internally valid policy snapshot.

Attack/failure scenario:
1. An approver key is marked REVOKED in the current external policy.
2. An older, validly formatted policy backup still marks that same key ACTIVE.
3. An administrator or recovery operator restores that older external policy snapshot.
4. The policy's self-digest, schema, owner/mode and key ID checks can all pass; the old key becomes acceptable again.
5. A previously signed approval may then pass verification despite the intended immediate revocation.

The statement that policy is outside the source-root rollback domain does not prevent rollback of the policy itself. A self-digest proves internal integrity, not freshness. The assumption that the separately administered trust configuration is not compromised does not explicitly address accidental/stale policy restore.

Required correction:
- Define an independently controlled policy revision/sequence and latest accepted policy identity/digest, or an append-only revocation mechanism whose rollback boundary is explicitly outside the policy file's own backup/restore domain.
- Specify provisioning, atomic update, crash recovery, backup/restore, monotonicity, revocation persistence and fail-closed behavior.
- If no independent freshness anchor is provided, explicitly state that stale-policy rollback is NOT DETECTED and that revocation cannot be claimed immediate across policy restore; quarantine on any suspected policy rollback.
- Keep this policy-freshness mechanism distinct from the source-root anti-rollback mechanism and state its own threat boundary.

### F02-R7 — MEDIUM: approval replay/idempotency is not fully specified

Evidence in §22.9:
- Approval record contains `decision_record_id` (UUIDv4), root IDs and `recovery_epoch_id`.
- The recovery-epoch record binds the approval reference and exact bytes digest.
- No requirement was found for durable one-time consumption of `decision_record_id`, a consumed-approval receipt, uniqueness registry, or a rule defining whether repeated use for the same root/epoch is idempotent.

The unique ID and root/epoch binding prevent casual cross-root substitution, but uniqueness of a value is not proof that it has not already been consumed. The issue's independent-review question explicitly asks about replay/cross-root/epoch/scope substitution.

Required correction:
- Define the allowed replay domain precisely. If repeated verification of the same immutable epoch is intentionally idempotent, state why it cannot authorize a second recovery transition or expand scope.
- Otherwise require a durable, atomic, no-reuse consumption record bound to approval digest, decision ID, predecessor/new root IDs and recovery epoch; define crash ordering and duplicate/retry behavior.
- Add negative fixtures for duplicate decision ID, reuse across a different root/epoch, and retry after crash around approval consumption.

### F02-R8 — MEDIUM: revocation semantics after recovery acceptance are ambiguous

Evidence in §22.9:
- A REVOKED key invalidates every approval signed by it, including previously recorded approvals.
- Missing/revoked key causes reject/quarantine.
- The contract does not explicitly state whether approval/policy verification is repeated on every source-root open, only during initial recovery, or at another defined lifecycle point.
- It does not define the state transition for an already initialized recovery epoch if its signing key is later revoked.

Ambiguity:
- If verification occurs only once, revocation may not invalidate an already accepted recovery in operation.
- If verification occurs on every open, revocation could quarantine an existing isolated collection, but the exact transition and treatment of already collected bytes are unspecified.
- If revocation affects only future approvals, the phrase “including previously recorded approvals” overstates the behavior.

Required correction:
- Specify verification points and revocation effect on pending, accepted and currently active recovery epochs.
- Define whether a revoked approval forces immediate quarantine, blocks next open, or affects only future recovery decisions; specify immutable evidence retention and no promotion in every case.
- Add fixtures for revocation before verification, after approval but before recovery acceptance, after acceptance, and after restart.

## Checks that remain valid

- P1.24 exact contract blob re-fetched: `dd33b60649d8881ca935d34b62b8b54b6d0e9d42`.
- Twelve-field approval schema and eleven-field Ed25519/JCS signed payload are present.
- Key ID derives from raw Ed25519 public key; login is mapped through the external policy.
- The policy is specified outside the source-root rollback/clone/snapshot domain.
- Key validity uses verifier time at verification; approval timestamp is audit metadata only.
- F01 v1.1 canonical-resumption prohibition and F05 Envelope-record/Raw-body separation remain present.
- P1.24's static checks remain evidence only; no keypair/signature/policy was generated or cryptographically verified.

## Required next action

Correct F02-R6/R7/R8 in the normative contract, add negative fixtures, then run a new exact-SHA adversarial self-review. Only if that self-review passes may issue #138 be retargeted to the corrected SHA. Until then, keep issue #138 targeting P1.24 SHA and add these findings to its independent-review scope.

## Residual blockers and authorization boundary

F07 filesystem durability NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; C01–C145 NOT IMPLEMENTED / NOT EXECUTED. No implementation, executable tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes, trading or destructive data operations were performed or authorized.

T0 remains independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement. No destructive data operations without separate explicit approval.
