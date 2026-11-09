# Stage B.3 — V08 Durable Checkpoint, Seal and Ordering Contract

Date: 2026-11-10  
Type: documentary technical contract; no implementation or qualification

## 1. Purpose and constraints

Specify logical requirements for partition progress, event-time windows, watermarks, durable checkpoints, immutable seals, late events, corrections and recovery. No database, transaction mode, provider, commit token, numeric lateness allowance, clock tolerance or idle-partition timeout is selected.

Approved direction retained: UTC half-open windows [start,end); monotonic source-progress watermark; lateness derived from evidence; seal only when watermark >= window_end; uncertainty causes hold/quarantine; durable commit boundary tied to actual implementation; deterministic seal/commit linearization; immutable checkpoints and append-only idempotent corrections.

## 2. Identity and ordering domain

Each stream uses a stable, versioned partition identity. A checkpoint binds schema/version, immutable checkpoint ID, dataset/source identity and contract revision, partition ID and partition-set revision, exact source cursor/offset and sequence identity, event-time interval, progress evidence and watermark revision, lateness/idle/correction policy revision, trusted-time evidence and uncertainty, frozen input manifest/digests, prior checkpoint/seal and generation, adapter/backend identity, durable commit receipt and verifier evidence.

No cursor, watermark or seal is meaningful without its source, partition and policy revision.

## 3. Progress and watermark semantics

Per-partition progress derives from source observations accepted by a versioned source contract. A watermark is a conservative lower bound on event-time completeness under approved source and lateness semantics, not simply the maximum timestamp observed.

Aggregate watermark semantics MUST account for every required partition. Idle, disconnected, missing or newly discovered partitions cannot be silently omitted. Their state is explicit: ACTIVE, IDLE_CANDIDATE, IDLE_APPROVED, GAP, UNKNOWN or QUARANTINED. Any exclusion requires versioned policy and evidence. Partition-set changes invalidate the aggregate watermark until reconciled.

Lateness is derived from observed source-delay evidence and owner-approved requirements; this contract assigns no numeric allowance. Equality at the seal boundary follows the approved predicate watermark >= window_end, subject to complete partition coverage, uncertainty and durable commit proof. If the uncertainty interval crosses the boundary, hold/quarantine; do not round into eligibility.

## 4. Checkpoint and seal state machine

Required states: OPEN, PROGRESSING, SEAL_ELIGIBLE, SEAL_PENDING, SEALED, CORRECTION_PENDING, RECONCILIATION_REQUIRED and QUARANTINED.

A seal requires frozen partition-set and policy revisions; complete required partition progress; watermark proof satisfying the boundary; no unresolved gap, unknown source state or clock uncertainty; frozen input manifest/digest; durable checkpoint commit acknowledged by a qualified backend; independent readback/verifier confirmation; and a deterministic seal bound to checkpoint ID/digest and all revisions.

SEALED is immutable. ACK or process-local cache is not durable commit proof. The exact durability primitive and ordering guarantee must be supplied by RET-10 qualification.

## 5. Crash and concurrency semantics

One linearization order must cover checkpoint write, durable commit, ACK, seal publication, readback and fence release. Crash before durable commit leaves the checkpoint uncommitted. Crash after commit but before ACK requires readback and idempotent recovery; it must not duplicate or incorrectly advance the cursor. Concurrent writers require monotonic fencing generations; stale writers are rejected. Partial commit, lost ACK, conflicting digest, fence loss, backend uncertainty or verifier unavailability produces RECONCILIATION_REQUIRED or QUARANTINED, never READY.

No atomicity or durability claim is permitted until exact backend/adapter semantics and failure-domain tests are evidenced.

## 6. Late events, corrections and replay

Events arriving after seal cannot rewrite a sealed checkpoint or historical output. They create an append-only correction record binding correction ID/idempotency key, target checkpoint/window and prior digest, late input identity/cursor/event time/digest, reason/provenance, arrival observation, transformation/model/policy versions, before/after references, resulting digest, authorization context where required, and reconciliation/verifier evidence.

Duplicate correction IDs with identical content are idempotent; reuse with different content is a conflict. Corrections never silently replace history or advance canonical cursors outside the source-order contract.

Recovery starts from a verified checkpoint and exact input manifest. It reconciles partition cursors, watermark, seal generation, correction chain, policy/source revisions and restore epoch. Replay must be deterministic for identical frozen inputs and toolchain contract. Missing inputs, changed semantics, absent corrections, digest mismatch or incomplete partition coverage blocks READY.

## 7. Future vectors and status

Future vectors cover complete partition progress, idle/missing partitions, partition-set changes, watermark below/equal/above boundary, uncertainty crossing boundary, lateness, gaps/backfill, crashes before/after commit, lost/duplicate ACK, stale/concurrent writers, backend partial failure, verifier outage, late events, duplicate/conflicting corrections, replay mismatch and restore epoch mismatch. Each needs frozen synthetic inputs, exact adapter/backend version, deterministic schedule, independent oracle and retained artifact. None was executed here.

V07 supplies trusted time; RET-10 supplies durability/transaction proof; RET-05/LDA-05 consumes exact seal generation and restore epoch; Restore requires complete per-partition high-water marks and correction reconciliation.

**Status: DOCUMENTARY CONTRACT COMPLETE; V08 OPEN / BLOCKED / NOT QUALIFIED / NOT VERIFIED.** No watermark, cursor, checkpoint, seal, database or persisted data was changed. No backend/provider selected; no tests or runtime probes performed.
