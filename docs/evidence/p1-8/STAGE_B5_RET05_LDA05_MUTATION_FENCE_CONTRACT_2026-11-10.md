# Stage B.5 — RET-05 / LDA-05 Mutation Fence State-Machine Contract

Date: 2026-11-10  
Type: documentary state-machine contract; no implementation or mutation authority

## 1. Objective and invariant

Specify preconditions and ordering required to make a lifecycle side effect impossible when any relevant object, policy, authorization, hold, dependency, trusted-time, checkpoint, inventory or restore revision changes before mutation linearization.

Core invariant: exact approved object set and every decision input are bound atomically, or through a demonstrably ordered compare/revalidation protocol, to the side effect. If ordering cannot be proven, no side effect occurs and the outcome is fail-closed.

No authority is granted to archive, expire, delete, clean up, compact, vacuum, remove backups/replicas, mutate exports or perform irreversible transitions. Option C remains controlling.

## 2. Immutable request envelope

A request binds request ID, operation type and idempotency key; exact object manifest with ID/class/generation/digest/location; explicit source/copy/evidence scope separation; policy ID/revision and operation-specific permission; authorization ID/issuer/principal/scope/validity; applicable hold/dependency set and registry/inventory revisions; V07 trusted-time evidence, uncertainty and revocation state; V08 checkpoint/seal generation and source high-water marks where relevant; RET-10 adapter/backend identity and capability revision; restore epoch/fencing generation; durable intent/audit evidence; verifier/oracle contract and required postcondition.

Wildcards, mutable aliases, dynamic predicates and inferred completeness are forbidden.

## 3. State machine

Required states:
DRAFT → FROZEN → VALIDATING → AUTHORIZED → FENCE_ACQUIRED → FINAL_REVALIDATION → MUTATION_PENDING → COMMITTED → READBACK_PENDING → VERIFIED.

Holding/terminal states:
REJECTED, BLOCKED, CANCELLED, EXPIRED, REVOKED, CONFLICT, UNKNOWN_OUTCOME, RECONCILIATION_REQUIRED and NOT_VERIFIED.

No transition skips final revalidation, durable intent, mutation boundary, independent readback or required evidence persistence.

## 4. Transition semantics

1. Freeze: create immutable manifest/digest; bind object and policy revisions.
2. Validate: resolve every object, class, owner, copy edge, dependency and hold within declared discovery boundary. Unknown/unclassified/orphan/incompletely inventoried objects block.
3. Authorize: validate exact operation-to-authorization match, identity, scope, issuer, validity and revocation using V07. Archive authority cannot be reused for deletion.
4. Acquire fence: obtain monotonic generation/token from a qualified RET-10 adapter; reject stale writers.
5. Final revalidation: compare exact object versions/digests, policy, holds, dependencies, inventory, authorization, V07 evidence, V08 seal and restore epoch against the frozen envelope.
6. Durable intent: persist exact decision and operation identity before side effect.
7. Mutation boundary: perform only the exact listed operation under atomic or provably ordered precondition/side-effect contract.
8. Commit/readback: persist durable result and obtain verifier-side readback.
9. Disposition: mark VERIFIED only when every required postcondition and evidence item matches; otherwise reconcile and stop.

## 5. Race and crash rules

- Hold/dependency added before linearization: reject operation.
- Policy/object/authorization/revocation/inventory revision changes before linearization: invalidate approval; re-freeze and re-authorize.
- Fence/lease lost or generation changes: stale actor cannot mutate.
- Cancellation/revocation races mutation: use authoritative linearization evidence; unknown order means UNKNOWN_OUTCOME and reconcile.
- Crash/lost response after possible side effect: do not retry blindly; query independent oracle by exact operation/object identity.
- Partial multi-object batch: preserve verified per-object outcomes, block remaining objects, reconcile ambiguous objects; never report batch success.
- Audit/evidence sink unavailable after possible side effect: stop subsequent objects; durable intent remains; NOT_VERIFIED until independent observation.
- Duplicate idempotency key with identical envelope: deterministic idempotent outcome; same key with different envelope: reject conflict.
- Unknown copy, consumer, hold or dependency: block; do not infer absence or global completeness.

## 6. Technical enforcement evidence

Future qualification requires exact adapter/backend build and transaction/fencing semantics; deterministic schedules for races; negative vectors for stale policy/object/hold/authorization/time/seal/epoch; proof of no side effect when preconditions fail; independent verifier/oracle and readback; crash/restart/partial-failure and idempotency results; exact manifest and per-object provenance; permission/credential boundaries and fail-closed behavior.

Policy approval alone is not technical enforcement. Synthetic model tests alone do not prove backend mutation fencing.

## 7. Status and boundaries

**Status: CONTRACT SPECIFIED; RET-05 POLICY BOUNDARY APPROVED; TECHNICAL ENFORCEMENT NOT VERIFIED; LDA-05 NOT VERIFIED.** No adapter implementation, test, mutation, permission change or destructive lifecycle operation was performed or authorized. Option C and protected data classes remain unchanged.
