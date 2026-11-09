# P1.26 — Adversarial self-review of ERA policy freshness, replay and revocation

Date: 2026-11-09  
Review type: Same-session adversarial static self-review; NOT independent.  
Exact normative contract blob reviewed: 312f3062cdacbdbaa2480ef5a0b3fa8d7693bcec  
Prior findings: P1.25 F02-R6 HIGH, F02-R7 MEDIUM, F02-R8 MEDIUM.  
Branch: feature/t0-centralized-data-feeder-p1-20261101

## Verdict

**REQUEST CHANGES — F02-R9 HIGH.**

P1.26 materially addresses policy freshness, decision replay and post-acceptance revocation at the requirements level. However, the new External Recovery Authority (ERA) is a required security-critical dependency whose authenticated protocol, receipt schema and trust bootstrap are not specified sufficiently to implement or independently verify. A prose requirement that ERA returns an authenticated receipt is not itself a verifiable wire/storage contract.

## F02-R9 — HIGH: ERA trust protocol and receipt are underspecified

Evidence in the exact P1.26 contract:
- §22.9 requires an ERA with a monotonic policy head and consumed-decision set.
- It requires authenticated policy-head responses and immutable authenticated consumption receipts.
- The recovery-epoch schema references an ERA consumption receipt and its digest.
- C146–C156 cover stale policy, replay, crash windows, revocation and malformed receipt behavior.
- No closed schema was found for the ERA policy-head response or consumption receipt; no exact signature algorithm/key-ID encoding, canonicalization, field binding, protocol version, expiry/nonce, endpoint identity, or trusted ERA public-key bootstrap is specified.
- No initial provisioning rule binds the first policy head to an authenticated ERA state.
- The durability/failure semantics of ERA's monotonic store and consumed-ID set are asserted but not defined as an independently auditable service contract.

Adversarial consequence:
A verifier cannot determine exactly which response bytes to authenticate, what fields must be signed, how to prevent response substitution/replay, how to bootstrap the trusted ERA key/head, or how to distinguish a valid old receipt from a current response. Different implementations could accept different semantics while all claiming conformance.

Required correction:
1. Define a versioned, closed canonical schema for ERA policy-head responses and decision-consumption receipts.
2. Specify exact signature algorithm, key-ID derivation, canonical signed payload boundary, encoding and signature verification.
3. Bind every response to protocol version, ERA identity, policy_id/revision/digest, request operation, decision tuple, monotonically increasing authority sequence and request nonce/challenge or equivalent replay protection.
4. Define trust bootstrap, key rotation/revocation and the ERA key's separate custody/compromise boundary. The ERA key MUST NOT be derived from the approver key or a file within the source-root/policy backup domain.
5. Define initial policy-head provisioning, atomic compare-and-advance semantics, durable consumption transaction, read-after-write confirmation, crash recovery and retention/no-reuse guarantees.
6. Define exact behavior when the authority sequence advances but the client loses the response; exact tuple retry returns the same receipt, any tuple mismatch rejects, and the client must not invent a new decision ID.
7. Add negative fixtures for forged/unsigned response, stale sequence, wrong ERA identity, nonce/request mismatch, cross-operation response substitution, receipt replay, invalid bootstrap, key rotation/revocation, and ambiguous commit/readback.

## Checks that passed at contract-text level

- P1.26 contract was re-fetched at exact blob `312f3062cdacbdbaa2480ef5a0b3fa8d7693bcec`.
- Policy schema now includes monotonic revision and previous digest.
- Stale-policy restore is rejected when it disagrees with the ERA policy head.
- Policy updates require exact compare-and-advance and readback.
- Decision consumption is one-time, tuple-bound and exact-retry idempotent.
- Recovery epoch binds receipt reference and digest.
- Revocation is checked at initial acceptance, every open, before read/write transaction and before state transitions.
- Revocation blocks the next gated operation, quarantines and preserves bytes; no claim is made that an in-flight syscall can be retroactively canceled.
- C146–C156 are present and ordered.
- Canonical eligibility, sealing, watermark, aggregation and promotion remain prohibited for this recovery scope.

These are static document checks only. No ERA service, key, signature, monotonic store, receipt, cryptographic verification, executable fixture, GitHub Actions run, filesystem test or runtime test exists.

## Residual blockers

F07 target filesystem/provider semantics NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer f64/fixed-precision/parse-error-to-zero defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; C01–C156 NOT IMPLEMENTED / NOT EXECUTED. The ERA itself is NOT IMPLEMENTED and its independent durability/monotonicity is NOT VERIFIED.

## Required next action

Specify the ERA protocol and closed receipt schemas, add negative fixtures, then self-review the exact new contract blob. Only after a documentation-level PASS may issue #138 be retargeted to the corrected SHA for genuinely independent review.

## Authorization boundary

This review does not authorize implementation, executable tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes, strategy/AI/ledger/risk changes, trading or destructive data operations.

T0 remains independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement. No destructive data operations without separate explicit approval.
