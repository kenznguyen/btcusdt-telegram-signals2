# ADR — Shared Data Foundation with Centralized Lifecycle Governance

Date: 2026-11-08 (Asia/Ho_Chi_Minh)
Status: **DECISION ACCEPTED — DESIGN ONLY; NOT IMPLEMENTED**

## 1. Decision

The five-layer system adopts the following data-governance model:

| Decision axis | Accepted choice |
|---|---|
| Data ownership | **Shared** — datasets are governed as system-wide assets across T0–T4, not as an independently owned T0-only asset |
| Raw-data retention | **Demand-based** — retain according to declared consumer demand, reproducibility, audit and research requirements; no assumption of permanent retention |
| Lifecycle governance | **Central** — one system-level policy authority defines lifecycle rules and authorizes state transitions; storage-specific adapters may execute approved operations |

Architecture name: **Shared Data Foundation with Centralized Lifecycle Governance**.

This decision changes logical ownership and lifecycle governance. It does not change physical storage, database selection, writer authority, API behavior, or runtime deployment.

## 2. Context

The existing architecture describes T0 as an independent data asset. That boundary is no longer the desired system model because T1–T4 consume, derive, evaluate, and present data whose value and retention requirements extend beyond T0.

A consumer reading a dataset does not prove that the dataset is no longer needed. Data may remain necessary for:
- reproducing Core or AI signals and their input state;
- FreqAI training, inference lineage, and model evaluation;
- independent Core/AI backtests and strategy comparisons;
- data-quality investigations, incident analysis, and audit;
- rebuilding derived datasets when transformations change.

The system therefore needs shared logical ownership while preserving strict write and execution boundaries.

## 3. Architectural principles

### 3.1 Shared ownership is not shared write authority

- T0 remains the canonical market-data foundation and is accountable for ingestion, normalization, data quality, provenance, canonical persistence, and its read contract.
- The system-wide data governance authority owns dataset classification and lifecycle policy.
- T1–T4 may consume approved datasets and publish derived datasets under their own producer identity.
- Consumers do not receive direct permission to mutate or delete canonical T0 data.
- Canonical writes remain behind the existing fenced writer authority. Sharing data does not create shared database credentials or unrestricted write access.

### 3.2 Demand-based retention is not delete-after-read

A successful read or consumer ACK is evidence of a completed read/task only. It is not deletion authorization.

A dataset remains retained while at least one of the following applies:
- an active registered consumer dependency exists;
- a running or reproducible experiment references it;
- training, inference, backtest, or signal audit requires it;
- an approved replay/recovery requirement applies;
- an explicit legal, security, or incident hold applies;
- its declared retention window has not elapsed.

When none applies, the dataset may become eligible for review. Eligibility is not the same as permission to delete.

### 3.3 Central policy, distributed execution

- A central lifecycle authority defines classification, retention policy versions, dependency rules, archive/expiry criteria, grace periods, and deletion authorization.
- Storage adapters may execute approved archive or deletion operations for their storage backend.
- Adapters must not invent or override policy.
- The central authority must be able to fail closed: if policy, dependency, identity, or authorization state cannot be verified, destructive operations do not proceed.

## 4. Data classes and initial policy intent

No numeric retention periods are approved by this ADR.

| Data class | Initial lifecycle intent |
|---|---|
| Raw market events / raw captures | Demand-based; preserve when required for reconstruction, research, or source-level audit |
| Canonical candles | Shared canonical dataset; retain according to downstream dependencies and reproducibility requirements |
| Derived features / intelligence datasets | Versioned; may have shorter retention when reproducible from retained inputs and transformation versions |
| Inference inputs and prediction lineage | Preserve sufficient input identity and provenance to audit model outputs |
| Training datasets / model artifacts | Versioned and linked to source dataset manifests; retain according to research and model-audit needs |
| Backtest / experiment outputs | Retain with strategy/model version, source SHA, dataset identity/version, parameters, and result manifest |
| Core and AI signals / paper ledgers | Preserve separately by strategy origin and lifecycle; never conflate CORE_LEDGER and AI_LEDGER |
| Cache / temporary intermediates | Candidate for short TTL and automatic expiry after dependency checks |
| Audit records / manifests / tombstones | Retain independently from the payload lifecycle; payload deletion must not erase the evidence that it existed or was processed |

Policy durations, storage tiers, cost thresholds, and archive mechanics require a separate policy specification and evidence-based review.

## 5. Dataset identity and consumer contract

Before lifecycle automation is designed, each managed dataset must have a stable identity and enough metadata to make safe decisions. The minimum proposed metadata is:

- dataset ID and logical dataset type;
- producer/layer identity;
- schema and dataset version;
- source identity and source time range;
- source commit SHA or producer build identity where applicable;
- content checksum or manifest digest where feasible;
- creation/availability timestamps;
- quality/completeness state;
- registered consumer references;
- retention policy ID/version;
- lifecycle state and hold/reason metadata.

Consumers must declare dependencies against dataset identity/version, not only a mutable path or table name. Completion ACKs should identify the consumer, task/run, dataset version, and completed operation. An ACK may release that consumer's dependency only; it cannot authorize deletion while other dependencies or holds remain.

## 6. Lifecycle state model

The target lifecycle state machine is:

`ACTIVE → RETAINED → ARCHIVE_ELIGIBLE → PENDING_DELETION → DELETION_AUTHORIZED → DELETED`

The implementation may refine these states, but must preserve these semantics:

1. **ACTIVE / RETAINED:** data is available to registered consumers under the read contract.
2. **ARCHIVE_ELIGIBLE:** no active hot-path requirement is known; archival may be considered without deleting the logical dataset.
3. **PENDING_DELETION:** all declared dependencies appear released; a grace period and final dependency/hold recheck are required.
4. **DELETION_AUTHORIZED:** a central policy decision explicitly authorizes a bounded dataset/version/scope.
5. **DELETED:** payload removal is confirmed by the storage adapter; a tombstone and audit event remain.

A newly registered dependency or hold before deletion execution must cancel or suspend the pending transition. Deletion commands must be idempotent and narrowly scoped. A failure or ambiguous outcome must be reported as unknown/blocked, not as successful deletion.

## 7. Safety invariants

- No delete-after-read behavior.
- No deletion based solely on a TTL, a single ACK, or lack of recent access.
- No deletion while a registered dependency, active job, audit hold, or recovery hold exists.
- No deletion when dataset identity, version, manifest, policy version, or storage target is ambiguous.
- No consumer can bypass central authorization through a direct storage call.
- No mutation of canonical T0 candles by T1–T4 consumers.
- No lifecycle operation may weaken T0 writer fencing or read-only API credentials.
- Deletion must preserve tombstone/audit metadata and record actor, policy version, target scope, reason, timestamp, and adapter result.
- Retention-policy changes are versioned and auditable; retroactive destructive effects require a separate review and explicit authorization.
- The lifecycle manager must not share credentials with the Feeder writer or read-only API.

## 8. Responsibilities by layer

| Layer | Data responsibility under this ADR |
|---|---|
| T0 | Canonical market-data producer, quality/provenance authority, fenced canonical writes, read API |
| T1 | Register raw-feed/derived intelligence dependencies and publish versioned derived datasets |
| T2 | Register training, inference, backtest, replay, and signal-audit dependencies; preserve separate Core and AI ledgers |
| T3 | Register execution-intelligence and paper-state dependencies where applicable |
| T4 | Read and display lifecycle/quality state; no direct deletion authority |
| Central governance | Own dataset classification, consumer registry rules, retention policy, holds, expiry review, deletion authorization, and audit trail |

## 9. Compatibility and migration constraints

This ADR does not authorize or require:
- a database or schema migration;
- a PostgreSQL/TimescaleDB provider or hosting decision;
- a change to T0 Candle API contract or its current bind address;
- a T2 HTTP API/FreqAI consumer migration;
- a change to Feeder, writer fencing, lease, WAL keeper, or systemd behavior;
- a retention scheduler, archive job, vacuum, or deletion execution;
- VPS provisioning/deployment, exchange connectivity, or market-data synchronization;
- live trading or changes to `ai_execution_enabled=false`.

Existing storage and API behavior remain unchanged until separately designed, tested, reviewed, and explicitly authorized.

## 10. Required follow-on design documents

1. `docs/architecture/SHARED_DATA_FOUNDATION.md` — ownership, dataset boundaries, producer/consumer roles, and trust boundaries.
2. `docs/architecture/CENTRAL_DATA_LIFECYCLE_POLICY.md` — classifications, demand definitions, policy versioning, archive/expiry, grace periods, and unresolved retention values.
3. `docs/architecture/DATASET_CONSUMER_CONTRACT.md` — dataset identity/version, consumer registration, dependency release, ACK/checkpoint semantics.
4. `docs/architecture/DATA_DELETION_SAFETY_CONTRACT.md` — fail-closed authorization, final recheck, idempotency, tombstones, audit, and recovery from ambiguous outcomes.

After those designs are reviewed, reconcile:
- `docs/FIVE_LAYER_ARCHITECTURE.md`;
- `docs/FIVE_LAYER_PAPER_RUNBOOK.md`;
- `docs/T0_POSTGRESQL_LIFECYCLE_ACCEPTANCE_MATRIX.md` (keep runtime lifecycle distinct from data retention lifecycle);
- `docs/architecture/T0_POSTGRESQL_ATOMIC_WRITER_P0_2026-11-05.md`;
- `docs/PROJECT_SESSION_HANDOFF.md`.

## 11. Acceptance gates before implementation

Before any retention or deletion implementation:
1. inventory existing data stores, datasets, producers, consumers, and current retention behavior;
2. define dataset identity and consumer dependency semantics;
3. approve data-class-specific retention policy values and holds;
4. specify deletion authorization and grace-period behavior;
5. add RED tests for dependency/hold checks, cancellation, idempotency, and fail-closed behavior;
6. validate against disposable synthetic data only;
7. run GitHub Actions on the exact source SHA and preserve artifacts/evidence;
8. obtain separate explicit approval before any real data archive/deletion or runtime activation.

## 12. Decision status

| Item | Status |
|---|---|
| Shared logical ownership | ACCEPTED |
| Demand-based raw-data retention | ACCEPTED |
| Central lifecycle governance | ACCEPTED |
| Numeric retention periods | OPEN |
| Dataset/consumer contract | DESIGN REQUIRED |
| Deletion authorization contract | DESIGN REQUIRED |
| Existing source/runtime changes | NOT AUTHORIZED |
| Real data deletion/archive | NOT AUTHORIZED |
| Lifecycle automation | NOT AUTHORIZED |
