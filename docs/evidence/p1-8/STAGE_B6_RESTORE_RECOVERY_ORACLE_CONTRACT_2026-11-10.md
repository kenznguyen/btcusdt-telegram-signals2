# Stage B.6 — Restore / Recovery Oracle and Evidence Contract

Date: 2026-11-10  
Type: documentary recovery contract; no restore execution or staging authorization

## 1. Objective

Define evidence needed to identify a recoverable point, restore an isolated copy, fence stale writers, reconcile lifecycle/data state and prove recovery with an oracle technically separate from the restore path. No provider/database, backup product, storage topology, failure domain or operational procedure is selected.

Owner-approved planning direction remains: explicit failure domain; acknowledged-transaction RPO 0 only within a proven boundary; snapshot RPO <=5 minutes; staging RTO <=60 minutes; three separate rehearsals. These are planning targets only, not SLOs, measured capability or execution authority.

## 2. Recovery point manifest

A recovery-point manifest freezes recovery-point ID and immutable digest; source system/dataset and exact object/class/version identities; source high-water marks/cursors by partition; V08 checkpoint, watermark, seal and correction-chain identities; database/backend/adapter and schema versions; lifecycle policy, hold, authorization and revocation revisions; trusted-time evidence/uncertainty; T0 canonical data and separately identified availability/recovery copies; CORE_LEDGER and AI_LEDGER as distinct protected datasets; T3 signal/risk/order/fill/reservation/event/reconciliation/replay evidence required for reconstruction; governance/audit/tombstone records required for provenance; backup/replica/copy lineage and failure-domain identities; restore epoch/fencing generation; digest/checksum algorithm versions and source evidence.

A snapshot timestamp alone is not a complete recovery point. Every required partition and dependent dataset needs a reconciled high-water mark.

## 3. Failure-domain declaration

Before a rehearsal, enumerate dependencies/shared failure domains across source database, storage/device, provider, network, credentials/identity, control plane, backup/replica, encryption/key custody, time source, verifier/oracle and evidence custody. Independence cannot be inferred from different filenames, buckets, accounts or labels. Shared credentials, control planes, regions, keys or failure domains must be disclosed.

The exact failure-domain boundary remains OPEN until an owner-approved environment contract and evidence establish it.

## 4. Restore state machine

Required states:
NOT_STARTED, POINT_SELECTED, MANIFEST_FROZEN, RESTORE_IN_PROGRESS, RESTORE_COMPLETE_UNVERIFIED, FENCED, RECONCILING, ORACLE_CHECK, READY, BLOCKED, FAILED and QUARANTINED.

READY requires exact recovery-point/manifest match; complete high-water marks and partition coverage; integrity checks and deterministic replay; policy, holds, authorization/revocation and trusted-time reconciliation; consistent checkpoint/seal/correction chain; correct distinction of T0 canonical and availability/recovery copies; CORE_LEDGER and AI_LEDGER separation/consistency; complete T3 reconstruction/reconciliation; advanced restore epoch and fenced pre-restore writers/leases; independent oracle confirmation and no unexplained residual; durable evidence with independent readback.

Any missing copy, unknown cursor, digest mismatch, stale writer, uncertain time, unresolved hold, missing audit record or oracle disagreement prevents READY and all writes.

## 5. Restore epoch and stale-writer fencing

Every restore increments a monotonic restore epoch/generation. Writer leases, checkpoints, adapter tokens and mutation intents bind the epoch. Pre-restore actors are rejected even if local lease/cache appears valid. Epoch advancement and writer fencing must be atomic or provably ordered with restore activation. If the backend cannot establish this, the restored environment remains BLOCKED and read-only.

## 6. Independent recovery oracle

The oracle must not share restore executor mutation credentials, writable path or sole evidence source. It independently reads restored state and compares exact manifest/object digests; per-partition high-water marks/cursors; checkpoint/seal/correction identities; ledger separation and balances/events; T3 replay/reconciliation invariants; holds, policy, authorization/revocation and governance evidence; restore epoch/stale-writer rejection; missing, extra, duplicate or unexplained objects/copies.

Oracle inputs, expected values, verifier version, evidence path and trust boundary are frozen before rehearsal. If independent evidence cannot establish the result, disposition is NOT_VERIFIED, never PASS.

## 7. Measurement contract

RPO measurement records the last acknowledged transaction within the declared failure boundary and compares it with the latest transaction recovered using frozen transaction IDs/digests and explicit snapshot time. Acknowledged-transaction RPO 0 is restricted to tested acknowledgement and failure semantics. Snapshot RPO is measured from frozen snapshot boundary to latest recovered source position, reported by partition and dependent dataset.

RTO start/stop events are explicit, independently evidenced and reproducible. Start is the declared failure/restore trigger; stop is when all READY criteria, including independent oracle and fencing, are satisfied—not when a process starts or a database accepts connections.

Each of three rehearsals has separate run identity, frozen inputs, evidence custody and measured results. Shared infrastructure/operator overlap is disclosed; independence is not presumed. No numeric result is asserted here.

## 8. Rehearsal evidence and status

Required package: authorization/scope; environment-equivalence manifest; failure-domain declaration; recovery-point manifest; source/target identities; exact software/backend/adapter versions; start/stop observations; per-partition recovered HWM; integrity/replay/oracle results; epoch/fencing evidence; ledger/T3 reconciliation; deviations/residuals; artifact hashes/provenance; rollback/containment plan; owner disposition.

A rehearsal requires separate explicit authorization. Stage B approval does not authorize provisioning, restoring, fault injection, data reads/writes, staging or production execution.

**Status: DOCUMENTARY CONTRACT COMPLETE; RESTORE / RECOVERY OPEN / BLOCKED / NOT VERIFIED.** No restore, rehearsal, provider selection, environment probe, backup/replica operation or runtime change occurred. RPO/RTO values remain planning targets only.
