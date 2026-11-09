# P1.27 — Adversarial self-review of ERA protocol and receipt schemas

Date: 2026-11-09  
Review type: Same-session adversarial static self-review; NOT independent.  
Exact normative contract blob reviewed: 19b6ce968776c6ff017966573ce53cbd3d33daa5  
Prior finding: P1.26 F02-R9 HIGH.  
Branch: feature/t0-centralized-data-feeder-p1-20261101

## Verdict

**REQUEST CHANGES — F02-R10 HIGH.**

P1.27 adds a versioned ERA response envelope, trust bootstrap, closed policy-head/advance/consumption payload schemas, nonce binding, distinct ERA key, caller roles and crash/retry requirements. However, the recovery-epoch record pins only the consumption receipt payload reference/digest. The payload itself contains no ERA signature; its authenticity is provided by the separately signed response envelope. The epoch record does not bind or require durable retention of that signed envelope.

## F02-R10 — HIGH: signed ERA response envelope is not durably bound to recovery epoch

Evidence:
- `ERA_RESPONSE_ENVELOPE_V1` contains the ERA identity, operation, nonce, authority sequence, payload digest, timestamp, ERA key ID and Ed25519 signature.
- `ERA_DECISION_CONSUMPTION_RECEIPT_V1` is the payload whose digest is signed by the response envelope; the payload itself has no signature field.
- The recovery-epoch schema adds only `era_consumption_receipt_ref` and `era_consumption_receipt_sha256`.
- No `era_consumption_envelope_ref`/digest or immutable evidence-bundle schema binds the exact signed envelope bytes to the receipt payload.
- A later verifier can re-fetch the unsigned receipt payload, check its digest, and see that the epoch refers to it, but cannot verify the ERA signature from the epoch's durable evidence if the signed envelope was not retained or the original response is unavailable.

Attack/failure scenario:
1. ERA consumes a decision and returns a valid signed response envelope plus receipt payload.
2. The implementation persists only the receipt payload and its digest into the recovery-epoch record.
3. The process restarts or the remote ERA becomes unavailable.
4. A verifier can validate payload integrity but has no retained signature envelope to prove ERA authenticity, authority sequence, nonce-bound response and ERA key identity.
5. An attacker able to replace/replay the receipt payload and its local reference/digest within the same permitted write boundary may present content that is internally consistent but not independently authenticated by the ERA.

Required correction:
- Define an immutable canonical evidence bundle containing the exact receipt payload bytes and exact signed response-envelope bytes, or add separate envelope reference/digest fields to the recovery-epoch schema.
- Bind the envelope's `payload_sha256` to the exact receipt bytes and validate operation=`CONSUME_DECISION`, ERA identity, nonce shape, authority sequence, ERA key ID and signature.
- Persist the bundle before recovery-epoch publication, fsync it and its parent directory under the same durability rules; epoch record must pin the bundle digest.
- Define verification after restart without requiring a live ERA response to reconstruct authenticity, while still requiring a fresh live ERA policy-head/status check before each gated operation.
- Add negative fixtures for missing envelope, mismatched envelope/payload digest, wrong operation/ERA identity, invalid signature, stale sequence and bundle replacement.

## Checks that passed at contract-text level

- Exact contract blob re-fetched: `19b6ce968776c6ff017966573ce53cbd3d33daa5`.
- ERA response envelope has a closed versioned schema and Ed25519 signature boundary.
- Response nonce is fresh, 32-byte CSPRNG material, echoed and operation-bound.
- ERA trust bootstrap is separate from source root and approver policy; ERA key is distinct from approver key.
- Policy-head, policy-advance and decision-consumption payload schemas are specified.
- Policy updates use exact compare-and-advance; consumption is tuple-bound and exact-retry idempotent.
- Separate administrator/verifier caller roles are specified.
- C157–C166 are present and ordered.
- P1.25 R6/R7/R8 intent remains addressed at documentation level, subject to closure of this evidence-binding finding.

Static checks do not prove ERA implementation, cryptographic verification, authority durability, filesystem semantics or runtime behavior.

## Residual blockers

F07 target filesystem/provider semantics NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; C01–C166 NOT IMPLEMENTED / NOT EXECUTED; ERA service, key bootstrap and monotonic store NOT IMPLEMENTED / NOT VERIFIED.

## Required next action

Bind the exact signed ERA envelope to the immutable recovery evidence, add negative fixtures, then self-review the exact new contract blob. Retarget issue #138 only after a subsequent exact-SHA self-review passes.

## Authorization boundary

No implementation, executable tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes, strategy/AI/ledger/risk changes, trading or destructive data operations are authorized.

T0 remains independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement. No destructive data operations without separate explicit approval.
