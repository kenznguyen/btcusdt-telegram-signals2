# Data Copy, Backup, Replica, and Export Lifecycle Contract

Date: 2026-11-09
Status: **DESIGN ONLY — NOT IMPLEMENTED / NOT ACTIVE**

## 1. Purpose

Define governance and safety requirements for copies of shared datasets and operational state, including backups, replicas, exports, snapshots, local copies, caches, and recovery copies.

This contract closes the backup/replica governance gap identified by CC-09 in `SHARED_DATA_LIFECYCLE_CROSS_CONTRACT_REVIEW_2026-11-09.md`.

It is subordinate to:
- `SHARED_DATA_FOUNDATION.md`;
- `CENTRAL_DATA_LIFECYCLE_POLICY.md`;
- `DATASET_CONSUMER_CONTRACT.md`;
- `DATA_DELETION_SAFETY_CONTRACT.md`;
- `ENVIRONMENT_EVIDENCE_BOUNDARY.md`.

This document defines no storage implementation, API, schema, scheduler, retention duration, backup product, provider, or executable operation.

## 2. Scope and terminology

A **copy** is any separately addressable representation of source data or operational state, regardless of whether it is complete, partial, transformed, compressed, encrypted, online, offline, or temporary.

Copy classes include:

| Class | Meaning | Examples |
|---|---|---|
| Replica | Continuously or periodically maintained copy intended to serve reads or provide availability | hot standby, read replica, mirrored object |
| Backup | Recovery-oriented point-in-time or bounded copy | database backup, WAL/archive chain, filesystem snapshot |
| Export | Copy produced for transfer, analysis, interoperability, or external use | CSV, Parquet, JSON, object-store export |
| Local/working copy | Copy held by a consumer or operator outside the authoritative store | downloaded dataset, research workspace, temporary checkout |
| Cache/materialization | Reconstructible or derived copy used to improve access | feature cache, query materialization, dashboard read model |
| Evidence copy | Copy retained to prove a test, operation, lineage, or integrity claim | manifest, checksum inventory, CI artifact |

A copy is not automatically disposable because it is called a cache, temporary file, backup, or export. Its actual content, dependencies, recovery role, and obligations determine its governance.

## 3. Authority and ownership

1. Shared data ownership remains shared; the producer remains responsible for source identity, provenance, and publication integrity.
2. Central lifecycle governance owns classification, dependency reconciliation, holds, policy decisions, and authorization for destructive disposition of governed copies.
3. A storage operator or executor may perform only the exact operation covered by a valid authorization. Operational access does not confer lifecycle authority.
4. A consumer may create or hold copies only within its approved purpose and access scope. It may not independently expire or destroy a copy that is subject to a hold, active dependency, recovery obligation, or central restriction.
5. T0 writer fencing governs canonical writes. It does not grant authority to delete canonical data or any backup/replica/export.
6. Destructive disposition of a copy must not be used to bypass the central deletion governance required for its source dataset/version.

## 4. Identity, lineage, and inventory requirements

Every governed copy should have a stable copy identity and a recorded relationship to its source. Before a lifecycle decision can be made, the inventory must capture, where applicable:

- copy ID and copy class;
- source dataset ID and immutable dataset/version identity;
- source content/query fingerprint or manifest reference;
- source commit/schema/format version where relevant;
- copy creation time and last verified time;
- location/provider/environment class, with secrets excluded;
- producer, custodian, and responsible consumer;
- completeness scope: full, incremental, partitioned, filtered, transformed, or unknown;
- parent/child copy relationships and backup-chain dependencies;
- encryption/key dependency metadata without recording key material;
- restore procedure and last successful restore verification;
- consistency point, WAL/log sequence, watermark, or equivalent recovery position;
- legal, security, operational, research, and incident holds;
- active consumers, recovery obligations, and downstream copies;
- integrity evidence and known gaps.

Unknown identity, lineage, completeness, consistency, or ownership is a blocking condition for destructive disposition. A checksum alone proves neither semantic correctness nor recoverability.

## 5. Copy-specific safety invariants

### 5.1 Replicas

- A replica may be serving active consumers or failover duties even when it appears idle.
- Replica lag, consistency position, failover role, and rebuildability must be known before changing or removing it.
- Removing a replica must not silently remove the last recoverable copy or violate an availability/recovery commitment.
- Promotion, failover, resynchronization, and replica deletion are separate operations with separate authorization requirements.

### 5.2 Backups and recovery chains

- A backup is useful only in the context of its required base, incremental, log/WAL, metadata, encryption, and restore dependencies.
- A backup-chain member must not be expired independently if doing so makes a retained recovery point unusable.
- Retention eligibility must be evaluated per recoverable recovery point and complete dependency chain, not by file age alone.
- A successful backup job or object upload does not prove that restoration is possible.
- Restore verification must identify the exact source point, chain, environment, procedure, and observed result.
- Backup expiry and destructive removal remain out of scope until a dedicated inventory and policy decision exist.

### 5.3 Exports and local copies

- Exports and local copies retain source classification and applicable restrictions unless an approved transformation demonstrably changes their classification.
- Consumer ACK, download completion, or transfer success does not prove that all derived/local copies have been removed.
- External recipients and unmanaged destinations must be recorded where known; unknown distribution blocks claims of complete disposition.
- Revoking access and deleting a copy are distinct actions and must be evidenced separately.
- Credentials, private keys, tokens, and unrestricted account data must not be copied into lifecycle evidence.

### 5.4 Caches and materializations

- A copy may be considered reconstructible only when the authoritative source, transformation version, required inputs, and reproducible procedure are available and verified.
- A cache label or TTL does not itself authorize deletion.
- A derived copy with independent consumer value, audit obligations, or non-reproducible information must be governed as a dataset, not assumed disposable.

### 5.5 Hold inheritance across source and copies

- A hold on a source dataset/version is a protective constraint for every known copy that contains, represents, or derives from the held scope.
- A copy must not be treated as unheld merely because its copy record has no local hold entry. The source-hold relationship must be resolved during copy inventory and disposition review.
- A hold may be excluded from a particular copy only when the authoritative hold owner or authorized governance reviewer explicitly establishes that the hold's scope does not apply to that copy, records the rationale and evidence, and binds the decision to the exact source and copy identities.
- A copy may also carry an independent copy-specific hold even when no source hold applies.
- Releasing a source hold removes only that hold constraint after an authenticated, auditable release. It does not itself authorize copy disposition; all other dependencies, holds, recovery obligations, and disposition gates still apply.
- If lineage is incomplete, the source hold cannot be reliably mapped, or applicability is disputed, the copy remains protected and disposition is blocked.

### 5.6 Evidence copies

- Evidence required to substantiate an acceptance, incident, financial reconstruction, or audit claim must be protected from deletion while that obligation remains active.
- GitHub source history and CI artifacts are not substitutes for operational account-event storage or independently verified backups.
- Artifact metadata, payload retrievability, payload integrity, and semantic validity are separate evidence claims.

## 6. Separate state domains

Do not merge copy state into the dataset lifecycle, consumer dependency, or deletion-request state machines.

Maintain conceptually separate domains:

1. **Source dataset lifecycle** — governed by the Central Data Lifecycle Policy.
2. **Consumer dependency** — governed by the Dataset Consumer Contract.
3. **Copy lifecycle** — proposed states:
   - Discovered;
   - Registered;
   - Active;
   - Verification due;
   - Restore/rebuild review;
   - Disposition review;
   - Disposition eligible;
   - Disposition authorized;
   - Disposition executing;
   - Reconciliation required;
   - Verified disposed;
   - Held / blocked;
   - Unknown / unverified.
4. **Deletion request/execution** — governed by the Data Deletion Safety Contract.

These domains are related but not interchangeable. A source dataset may remain Active while one obsolete replica is retired. A consumer may release a dependency while a backup remains protected for recovery. A copy may be disposition-eligible without being authorized or executed.

## 7. Disposition gates

No copy may be destructively disposed of until all applicable checks pass:

1. Exact copy identity, source identity, scope, and location are established.
2. The copy's class, completeness, lineage, and dependency chain are known.
3. Active consumer dependencies and access/availability requirements are reconciled.
4. Holds, legal obligations, incident requirements, and evidence obligations are checked.
5. Recovery objectives and required restore points remain satisfied by verified alternatives.
6. Rebuildability is demonstrated, not assumed.
7. Source dataset lifecycle and deletion policy permit the proposed disposition.
8. Independent review and approval are complete with separation of duties.
9. Final execution authorization is narrow, time-bounded, idempotent, and bound to exact copy identities and operation scope.
10. Post-operation reconciliation independently verifies the intended result and checks that protected copies and recovery chains remain intact.

Any unknown, stale, contradictory, or unavailable evidence fails closed.

## 8. Review, expiry, and stale inventory

- Review deadlines may trigger investigation and escalation only.
- No TTL, age threshold, missing heartbeat, ACK, failed contact, or stale inventory entry may automatically release a dependency or authorize copy deletion.
- Unknown copies must be treated as protected until identified and adjudicated.
- Inventory freshness and evidence freshness are separate from authorization validity.
- A previously approved action must be rechecked against current dependencies, holds, recovery requirements, and exact copy identity before execution.

## 9. Failure and reconciliation

- Partial failure must be recorded per copy and per operation; never infer global success from a process exit code.
- Retries must be idempotent and remain within the original exact scope.
- If copy identity or operation outcome becomes ambiguous, stop further destructive actions and enter Reconciliation required.
- Preserve logs, manifests, and authorization evidence needed to determine what changed.
- Do not automatically cascade disposition to child copies, replicas, exports, or backups.
- A verified disposition claim requires independent post-operation evidence and an updated inventory.

## 10. Explicit non-goals and prohibitions

This contract does not:
- select retention durations, grace periods, RPO/RTO, evidence freshness windows, or approval quorum;
- designate a backup provider, object store, replica topology, or official T0 environment;
- implement a registry, API, schema, scheduler, retention timer, archive, vacuum, cleanup, or deletion executor;
- authorize backup expiry, replica removal, export revocation/deletion, local-copy cleanup, or cache eviction;
- authorize creation or modification of a canonical database, Feeder, or production runtime;
- convert experimental VPS observations or synthetic CI evidence into official-environment acceptance.

No destructive copy lifecycle operation is authorized by this design document.

## 11. Open decisions requiring evidence and separate approval

- Required copy classes and minimum inventory coverage for each layer T0–T4.
- Authoritative copy registry and accountable custodian model.
- Recovery-point selection, RPO/RTO, and restore-test requirements.
- Hold inheritance is protective by default under §5.6; any exception requires exact-scope, evidence-backed adjudication. Detailed hold taxonomy and jurisdiction-specific application remain open.
- External export tracking and recipient attestation requirements.
- Cryptographic key lifecycle and recoverability evidence.
- Independent approval and execution-authority separation.
- Numeric retention floors, review cadence, and evidence freshness.
- Policy for canonical T0 source data and its recovery copies.
- Official environment designation and provider-specific controls.

These decisions must be evidence-led. No default values are inferred.

## 12. Acceptance checklist

- [x] Copy classes and scope are defined.
- [x] Copy identity, lineage, and inventory requirements are specified.
- [x] Replica, backup-chain, export, local-copy, cache, and evidence-copy risks are separated.
- [x] Copy lifecycle is distinct from dataset, consumer, and deletion state domains.
- [x] Destructive disposition requires exact scope, independent approval, recovery checks, and post-operation reconciliation.
- [x] Stale inventory and TTL cannot authorize automatic disposition.
- [x] No implementation or destructive operation is authorized.

**Status: DESIGN COMPLETE — IMPLEMENTATION NOT APPROVED — INVENTORY AND POLICY DECISIONS PENDING.**
