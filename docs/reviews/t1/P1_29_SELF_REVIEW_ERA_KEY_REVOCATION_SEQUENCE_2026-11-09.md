# P1.29 — Adversarial self-review of ERA key revocation sequence

Date: 2026-11-09  
Review type: Same-session adversarial static self-review; NOT independent.  
Exact normative contract blob reviewed: bfb8331d459b4caeb081af67c84d6ab2cc23edb3  
Prior finding: P1.28 F02-R11 MEDIUM.  
Branch: feature/t0-centralized-data-feeder-p1-20261101

## Verdict

**REQUEST CHANGES — F02-R12 MEDIUM.**

P1.29 distinguishes historical cryptographic verification from current authorization and defines pre-/post-revocation sequence behavior. However, the revocation-effective sequence stored in the separately provisioned ERA trust file is not bound to a specified signed ERA revocation event or operation. The text says the sequence comes from the authenticated ERA control plane, but the ERA protocol operation enum and receipt schemas do not include key revocation.

## F02-R12 — MEDIUM: revocation sequence provenance is not verifiable

Evidence:
- ERA response envelope operation enum is `READ_POLICY_HEAD`, `ADVANCE_POLICY_HEAD`, or `CONSUME_DECISION`.
- ERA trust key entries now include `revoked_at_authority_sequence`.
- The contract requires that sequence to come from the authenticated ERA control plane.
- No `REVOKE_ERA_KEY` request/receipt schema or signed revocation event is defined, nor is the trust-file update explicitly bound to such an event.

Failure scenario:
An administrator-provisioned trust file marks a key REVOKED at sequence N, but the verifier has no signed ERA evidence proving that N is the sequence at which ERA actually revoked that key. The local file's ownership/mode/digest checks prove only that the file is internally intact and admin-controlled, not that the sequence is authentic or consistent with ERA state. A stale or incorrectly transcribed sequence could misclassify a pre-/post-revocation envelope.

Required correction:
- Add `REVOKE_ERA_KEY` as a defined ERA operation with an exact closed request and signed payload/receipt schema.
- Bind the receipt to ERA identity, key ID, prior ACTIVE state, resulting REVOKED state, exact effective authority sequence and audit timestamp.
- Define the atomic sequence allocation and commit order; the revocation receipt must be durably committed before ERA treats the key as revoked.
- Require the external ERA trust file's REVOKED entry to match the exact signed revocation receipt and sequence; preserve the receipt as immutable evidence.
- Define behavior for ERA revocation committed but host trust-file update incomplete: fail closed, query the exact key revocation state, update only from authenticated evidence, and never accept the old key meanwhile.
- Add fixtures for forged/mismatched receipt, wrong key ID, stale sequence, lost revocation response, and crash between ERA revocation and trust-file update.

## Checks that passed at contract-text level

- Exact contract blob re-fetched: `bfb8331d459b4caeb081af67c84d6ab2cc23edb3`.
- ERA trust entry schema contains revocation-effective sequence.
- Pre-revocation envelope may remain historical evidence only.
- Equal/post-revocation envelope rejects.
- Current authorization is denied for a revoked key.
- Existing accepted epoch is quarantined before its next gated operation after revocation is observed.
- C171–C174 are present and ordered.
- Signed evidence retention and no-promotion guardrails remain.

Static checks do not prove ERA implementation, signed revocation event, key custody, trust-store freshness, filesystem behavior or runtime.

## Residual blockers

F07 target filesystem/provider semantics NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; C01–C174 NOT IMPLEMENTED / NOT EXECUTED; ERA and monotonic store NOT IMPLEMENTED / NOT VERIFIED.

## Required next action

Specify the signed ERA key-revocation operation and exact trust-file binding, add negative fixtures, then self-review the exact new contract SHA. Retarget issue #138 only after a subsequent exact-SHA self-review passes.

## Authorization boundary

No implementation, executable tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes, strategy/AI/ledger/risk changes, trading or destructive data operations are authorized.

T0 remains independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement. No destructive data operations without separate explicit approval.
