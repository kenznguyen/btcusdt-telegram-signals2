# Shared Data Foundation — Architecture

Date: 2026-11-08
Status: **DESIGN — aligned with accepted ADR; not implemented**

Related decision: [Shared Data Foundation with Centralized Lifecycle Governance ADR](SHARED_DATA_FOUNDATION_LIFECYCLE_ADR_2026-11-08.md).

## 1. Purpose and scope

This document defines the logical data architecture shared by the five-layer system (T0–T4): what is shared, which layer produces or consumes each dataset, who may change it, and which boundaries must remain enforceable.

It translates the accepted decisions into an architecture:

- **Ownership: Shared.** System datasets are governed as assets of the five-layer system, not as an independently owned T0-only asset.
- **Raw data: Demand-based.** Data is retained according to declared system demand, reproducibility, audit, research, and recovery requirements. This document does not set numeric retention periods.
- **Lifecycle governance: Central.** A system-level governance authority defines dataset and lifecycle policy. Storage-specific components may execute only authorized operations.

This is a logical architecture, not a mandate to create a new database, data lake, service, API, or runtime process.

### In scope

- Logical ownership and stewardship.
- Dataset producer/consumer roles across T0–T4.
- Canonical versus derived data boundaries.
- Dataset identity, provenance, versioning, and dependency concepts.
- Read, write, and lifecycle authority boundaries.
- Trust boundaries and failure behavior.

### Out of scope

- Numeric retention periods, TTL values, archive tiers, and cost thresholds.
- Concrete consumer registry/API schema and runtime implementation (logical dependency and ACK/release semantics are defined in [Dataset Consumer Contract](DATASET_CONSUMER_CONTRACT.md)).
- Deletion execution implementation and operational runbooks (the governance and safety boundary is defined in [Data Deletion Safety Contract](DATA_DELETION_SAFETY_CONTRACT.md)).
- Database/provider selection, schema migration, API changes, deployment, and runtime activation.
- Trading/execution behavior or changes to Core/AI strategy logic.

Those topics require their own reviewed contracts and explicit implementation authorization.

## 2. Architecture model

The target model separates the **data plane** from the **governance control plane**.

### 2.1 Data plane

The data plane contains the actual datasets and the producers/consumers that read or derive them:

- T0 produces canonical market data.
- T1 consumes market data and produces versioned futures-intelligence datasets.
- T2 consumes canonical and intelligence datasets and produces strategy, model, inference, and backtest artifacts.
- T3 consumes approved strategy intents and market/execution context, and produces paper/execution-state records within its authority.
- T4 consumes read models and operational metadata for presentation; it is not a canonical data producer for market or strategy records.

Each producer is accountable for the correctness, schema, provenance, and version identity of datasets it publishes.

### 2.2 Governance control plane

The central governance control plane defines system-wide rules and metadata:

- dataset classification and ownership registry;
- producer and consumer identities;
- dataset version and lineage references;
- policy version and lifecycle state;
- dependency and hold state;
- authorization records for exceptional lifecycle operations;
- audit events and tombstones.

The control plane governs data without becoming an unrestricted writer to every dataset. It should not share credentials with T0's canonical writer, API reader, or trading/execution components.

Central governance is a logical authority. Its future implementation may be a service, a database-backed module, or another reviewed design. No such implementation is authorized by this document.

## 3. Shared ownership model

“Shared” means that datasets created for the system are managed under common system-level governance and can have multiple authorized consumers. It does **not** mean that every layer co-owns every row, may overwrite another producer's output, or has unrestricted access to the storage backend.

Use three distinct responsibilities:

| Responsibility | Meaning | Authority |
|---|---|---|
| System data governance | Defines common dataset identity, classification, access policy, lifecycle policy, and audit requirements | Central governance |
| Dataset stewardship | Accountable for the meaning, quality, schema, provenance, and publication of a dataset | Designated producer |
| Dataset consumption | Declares purpose and dependency; reads a permitted dataset version | Registered consumer |

The producer remains accountable for its published dataset. The system-level governance authority controls cross-layer policy. Consumers receive only the read and dependency-release capabilities required for their tasks.

A producer cannot use shared ownership to bypass central policy. Central governance cannot silently rewrite producer-owned payloads. Any correction to a canonical or derived dataset must follow the producer's versioned correction/republication contract. T0 maintenance/correction authority is not deletion approval. Destructive removal of a published shared dataset/version must pass central lifecycle review, independent approval, exact-scope execution authorization, and post-operation verification under [Data Deletion Safety Contract](DATA_DELETION_SAFETY_CONTRACT.md).

## 4. Dataset domains and stewardship

The following is a logical responsibility map. It does not claim that every listed dataset or service is currently implemented.

| Domain | Primary producer / steward | Authorized consumers | Canonical boundary |
|---|---|---|---|
| Raw market captures and exchange observations | T0 or designated source collector | T0 validation; T1 and approved research consumers | Source observations retain source identity, event/observation times, and coverage limitations |
| Canonical market candles | T0 | T1, T2, T3, T4 through approved read interfaces | T0 is the only canonical writer under fenced writer authority |
| Market-quality and completeness metadata | T0 for canonical candles; T1 for its own feeds | All layers as needed | Quality claims are scoped to source, feed, interval, and validation method |
| Futures-intelligence datasets (funding, OI, trades, observed liquidations, derived metrics) | T1 | T2, T3, T4 | T1 owns schema/provenance of its published datasets; observations must not be represented as complete exchange tape without evidence |
| Strategy inputs, feature sets, model training datasets and inference lineage | T2 | T2; selected read-only outputs to T3/T4 | Versioned with source dataset references, feature/label definitions, model and code provenance |
| Core and AI signals, strategy state and backtest outputs | T2 | T2; authorized paper/execution boundary and read-only T4 views | CORE_LEDGER and AI_LEDGER remain logically and operationally separate |
| Paper execution state and execution observations | T3 | T2 for reconciliation; T4 for display; T3 for state transitions | T3 is authoritative for its paper/execution state; a UI view is not a write authority |
| Dashboard/read models and presentation cache | T4 or designated API/read-model producer | T4 clients and approved read-only consumers | Derived and rebuildable; must not become a hidden source of canonical truth |
| Lifecycle registry, policy and audit metadata | Central governance | Authorized governance components; read-only status to other layers | Central authority controls policy transitions; payload access remains separately authorized |

Where the actual implementation differs, record the observed producer and consumer rather than assuming this target table describes deployed behavior.

## 5. Canonical data and derived data

Every dataset must be explicitly classified as one of:

1. **Canonical:** authoritative within a defined domain and produced by its designated steward. Examples: T0 canonical candles; T3 paper execution state.
2. **Derived:** computed from one or more source datasets by a versioned transformation. Examples: T1 intelligence metrics; T2 feature matrices and model outputs; T4 read models.
3. **Evidence:** manifests, checksums, test outputs, audit events, lineage records, and tombstones that support verification of other datasets.
4. **Ephemeral:** cache, temporary work files, and intermediate artifacts that are rebuildable and have no independent canonical authority.

A derived dataset must not silently replace its source dataset or claim the source's canonical status. It must identify its inputs and transformation. If source completeness is limited, the derived dataset must preserve that limitation rather than manufacture certainty.

Evidence metadata has a lifecycle distinct from the payload it describes. Deleting a payload must not silently delete its manifest, audit event, or tombstone where policy requires that evidence to remain.

## 6. Dataset identity and lineage requirements

A consumer must identify the exact dataset version it used. A mutable file path, table name, latest-row query, or branch name alone is not a sufficient reproducibility reference.

The minimum logical dataset descriptor is:

| Field | Purpose |
|---|---|
| dataset_id | Stable logical identity across versions |
| dataset_type | Canonical, derived, evidence, or ephemeral plus domain subtype |
| producer_id | Layer/service identity accountable for publication |
| dataset_version | Immutable version or snapshot identity |
| schema_version | Interpretation of the dataset structure |
| source_refs | Exact upstream dataset IDs and versions |
| time_range | Covered event/source interval, where applicable |
| available_at | When the dataset became available to consumers |
| quality_state | Completeness, validation, and known limitations |
| content_digest | Integrity reference where feasible |
| producer_revision | Source SHA, build, model, or transformation identity where applicable |
| policy_ref | Applicable governance policy version |
| lifecycle_state | Current governed lifecycle state |

This is a design-level descriptor, not an approved API payload or database schema. The concrete contract must define required/optional fields, serialization, immutability, and compatibility rules.

For strategy and model outputs, lineage should be sufficient to reconstruct the decision context: source dataset versions, feature/label definitions, strategy or model version, relevant parameters, decision timestamp, and result manifest. This supports separate Core and AI evaluation without merging their ledgers.

## 7. Access and mutation boundaries

The architecture follows least privilege and producer-scoped writes.

| Actor | Read | Publish/write | Correct/delete |
|---|---|---|---|
| T0 canonical writer | Required source inputs | Canonical T0 datasets under fenced lease | Producer-scoped correction/republication under T0 controls; destructive removal of a published shared dataset/version must pass central deletion governance and the separate deletion safety contract |
| T1 producer | Approved T0/source datasets | T1-owned intelligence datasets | Only T1-owned outputs under versioned producer contract |
| T2 producer | Approved T0/T1 datasets | T2-owned features, model/inference and strategy artifacts | Only T2-owned outputs under versioned producer contract |
| T3 producer | Approved strategy and market context | T3-owned paper/execution state | Only through T3 state-transition rules |
| T4 client/read model | Approved read models and status | Rebuildable T4-owned presentation artifacts only, if applicable | No authority over canonical T0–T3 records |
| Central governance | Metadata needed for policy decisions | Registry, policy, hold, authorization, and audit metadata | May authorize lifecycle actions; cannot bypass storage adapter safeguards |
| Storage adapter | Narrowly scoped target | Executes authorized archive/delete operation | No independent policy decision |

Important invariants:

- Shared ownership does not imply shared database credentials.
- T1–T4 cannot write directly into T0 canonical tables/files.
- A consumer cannot mutate a producer's dataset.
- T4 UI controls cannot directly change canonical data or lifecycle state.
- Central governance does not use the Feeder writer identity.
- Read-only API access remains read-only.
- Any correction or replacement creates an auditable version transition; it does not silently rewrite historical evidence.

## 8. Consumer dependency model

A consumer registers a dependency against a specific dataset identity/version and declares why it is needed. The dependency may represent an active process, scheduled job, experiment, model, backtest, replay, audit, or recovery obligation.

A dependency release means only that the named consumer/task no longer requires that specific version for that declared purpose. It does not prove that all consumers are finished.

The detailed logical contract is defined in [Dataset Consumer Contract](DATASET_CONSUMER_CONTRACT.md). It covers consumer identity, exact dataset/version pinning, purpose, registration, ACK, release, idempotency, stale-consumer review, retries, and reconciliation. The contract does not define an implementation schema or API.

A missing heartbeat or overdue review date is only a review/escalation signal. It never releases a dependency or removes its protective effect. No dependency registry, ACK endpoint, TTL, or automatic cleanup is implemented or authorized by this architecture document.

## 9. Failure and consistency rules

The architecture prefers correctness and explicit uncertainty over availability of an unverified dataset.

- If dataset identity/version cannot be resolved, the consumer must not silently substitute “latest”.
- If provenance, checksum, or quality metadata required by a consumer is missing or inconsistent, the consumer must report unavailable/blocked according to its contract.
- If a source feed has gaps or observation-only coverage, downstream datasets preserve those limitations.
- If central policy or dependency state cannot be read, destructive lifecycle actions fail closed.
- If a producer republishes corrected data, consumers must be able to distinguish the old and new versions.
- If a consumer is offline or its dependency state is ambiguous, the central lifecycle authority must not infer that the dependency has ended merely from lack of recent reads.
- If a storage adapter reports an ambiguous delete/archive result, the lifecycle state remains unknown/blocked pending reconciliation.

This document does not define cross-database transactions or strong consistency guarantees. Those depend on the eventual storage and service design.

## 10. Relationship to current T0 interfaces

T0 remains the canonical market-data foundation. Its current read interface, fenced writer boundary, lease behavior, and persistence implementation are not changed by this document.

- Consumers should continue using the currently approved T0 read interface and its existing contract.
- No T2 HTTP client migration is implied.
- No new dataset registry endpoint or lifecycle API is implied.
- No new write path to canonical T0 data is permitted.
- Dataset metadata requirements are design targets; any addition to API responses or persisted schema requires a separate compatibility review.

The PostgreSQL/Feeder runtime lifecycle (process start/stop, lease, writer fencing, WAL keeper, migrations) remains separate from system-wide dataset retention and lifecycle governance.

## 11. Cross-layer data flow

The intended logical flow is:

T0 canonical market data → T1 intelligence datasets → T2 strategy/model datasets and signals → T3 paper/execution state → T4 read models and presentation

This is not a mandatory linear pipeline. T2 may consume T0 directly where its strategy contract requires canonical candles; T1 may independently publish feed datasets; T4 may read authorized status from multiple layers through an API. Each edge must identify the dataset, version, access contract, and producer.

No layer should rely on undocumented filesystem sharing or direct database access across trust boundaries. Existing local implementation details remain unchanged until an integration contract explicitly replaces them.

## 12. Security and operational boundaries

- Credentials are scoped by component and operation; no shared superuser credential across layers.
- Canonical writes, lifecycle policy changes, and deletion execution use distinct identities.
- Secret material is not included in dataset manifests or audit logs.
- Dataset metadata exposed to T4 is read-only and must not reveal credentials or sensitive infrastructure details.
- Lifecycle state transitions are auditable and policy-versioned.
- Manual exceptions require actor, scope, reason, expiry/review point, and evidence.
- The system remains paper-only; this document does not enable live orders or change ai_execution_enabled=false.

## 13. Open design decisions

The following remain unresolved and must not be guessed during implementation:

1. Concrete dataset ID/version format and canonical manifest serialization.
2. Concrete registry/API implementation, storage, and ownership.
3. Operational review cadence and escalation for stale consumers; the logical contract prohibits timeout-based auto-release.
4. Dataset classification details and numeric retention periods.
5. Archive storage classes and restore service levels.
6. Deletion authorization roles, grace period, and final recheck semantics.
7. Exact audit/tombstone retention and integrity guarantees.
8. Cross-layer API contracts and compatibility migration sequence.
9. Mapping of currently deployed files, tables, services, and jobs to this target model.

## 14. Acceptance criteria for this architecture document

- [x] Shared ownership is distinguished from unrestricted shared write access.
- [x] T0 remains the canonical market-data producer and fenced writer boundary.
- [x] T1–T4 producer/consumer responsibilities are explicit and scoped.
- [x] Canonical, derived, evidence, and ephemeral datasets are distinguished.
- [x] Dataset identity, version, lineage, and quality requirements are documented.
- [x] Consumer dependency and ACK semantics do not authorize delete-after-read.
- [x] Central governance and storage adapter responsibilities are separated.
- [x] Existing T0 runtime/API/database behavior is explicitly unchanged.
- [x] Open questions and non-authorized implementation scope are recorded.

## 15. Status and next step

**Status: DESIGN DOCUMENT COMPLETE — NOT IMPLEMENTED.**

Detailed follow-on designs now exist: [Central Data Lifecycle Policy](CENTRAL_DATA_LIFECYCLE_POLICY.md), [Dataset Consumer Contract](DATASET_CONSUMER_CONTRACT.md), and [Data Deletion Safety Contract](DATA_DELETION_SAFETY_CONTRACT.md). The cross-contract review is recorded in [Shared Data Lifecycle Cross-Contract Review](SHARED_DATA_LIFECYCLE_CROSS_CONTRACT_REVIEW_2026-11-09.md). The repository-level static inventory is recorded in [Dataset Consumer Inventory Baseline](DATASET_CONSUMER_INVENTORY_BASELINE_2026-11-09.md). The current experimental VPS is explicitly excluded from all inspection, including read-only inspection. The official environment is NOT DESIGNATED; any future runtime inventory requires a separately designated official environment and explicit scope approval. See [Environment and Evidence Boundary](ENVIRONMENT_EVIDENCE_BOUNDARY.md). Do not infer live datasets, consumers, lineage, or copies from source-only evidence.

No source code, test, workflow, database/schema, API, VPS, Feeder, scheduler, archive, vacuum, or deletion operation is changed or activated by this document. Any such work requires separate review and explicit authorization.
