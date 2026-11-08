# Central Data Lifecycle Policy — Design

Date: 2026-11-08
Status: **DESIGN — proposed policy framework; not implemented or activated**

Related decisions and architecture:
- [Shared Data Foundation with Centralized Lifecycle Governance ADR](SHARED_DATA_FOUNDATION_LIFECYCLE_ADR_2026-11-08.md)
- [Shared Data Foundation](SHARED_DATA_FOUNDATION.md)
- [Dataset Consumer Contract](DATASET_CONSUMER_CONTRACT.md)
- [Data Deletion Safety Contract](DATA_DELETION_SAFETY_CONTRACT.md)

## 1. Purpose

This document defines the policy framework for governing the lifecycle of datasets shared across T0–T4. It translates the accepted decisions into reviewable policy rules:

- **Ownership: shared** at system level, with designated producer stewardship.
- **Raw data: demand-based**; retention follows declared dependencies and system obligations, not a delete-after-read rule.
- **Lifecycle governance: central**; one logical governance authority evaluates policy and authorizes lifecycle transitions.
- **Execution: least privilege and fail-closed**; a storage adapter may execute only a specifically authorized operation and cannot decide policy.

This is a policy design. It does not activate retention timers, archive jobs, compaction, vacuum, deletion, or any other data-changing operation.

## 2. Policy objectives and invariants

The policy must preserve, in priority order:

1. Data integrity and recoverability.
2. Reproducibility of backtests, model training/inference, signals, and investigations.
3. Auditability of producer, consumer, policy, and lifecycle decisions.
4. Availability for currently registered and reasonably foreseeable system dependencies.
5. Security, privacy, and applicable legal obligations.
6. Storage efficiency, only after the preceding obligations are satisfied.

Mandatory invariants:

- A read, download, successful job, or consumer ACK is never by itself a deletion trigger.
- No dataset is deleted solely because it is old, large, expensive, or has not recently been read.
- Absence of a heartbeat, missing consumer, or inaccessible registry is not proof that demand ended.
- Unresolved provenance, ownership, dependency, policy, hold, or execution state blocks destructive transitions.
- Retention periods are policy parameters, not guessed constants embedded in producers or storage adapters.
- A policy change cannot silently weaken an existing hold or invalidate a reproducibility obligation.
- Dataset payload and its evidence (manifest, lineage, audit event, tombstone) have separately governed lifecycles.
- T0 canonical data remains protected by its producer/fenced-writer boundary; lifecycle governance does not grant consumers direct write/delete access.
- No policy decision changes the paper-only boundary or enables live trading.

## 3. Lifecycle governance responsibilities

| Role | Responsibility | Prohibited authority |
|---|---|---|
| Central lifecycle authority | Owns policy versions, classification rules, dependency/hold evaluation, eligibility decisions, and audit requirements | Cannot bypass producer/storage safeguards or silently mutate payloads |
| Dataset steward / producer | Declares dataset purpose, classification, provenance, quality, dependencies, and correction history | Cannot unilaterally shorten system retention or delete shared datasets |
| Consumer owner | Registers purpose-specific dependencies and releases them when that purpose is complete | ACK cannot authorize archive or deletion |
| Hold owner | Requests and periodically reviews a scoped preservation hold with evidence and expiry/review date | Cannot silently apply an unbounded global hold |
| Storage adapter | Executes a narrowly scoped, approved archive or deletion operation and returns verifiable outcome | Cannot determine eligibility or initiate action from age/TTL alone |
| Auditor / reviewer | Reviews policy changes, exceptions, lifecycle decisions, and evidence | Read-only unless separately authorized |

The central lifecycle authority is a logical responsibility. This document does not choose its service, database, credential model, or deployment topology.

## 4. Dataset classification

Every registered dataset must have a steward, purpose, class, sensitivity classification, provenance, and lifecycle policy reference. Classification must describe the dataset's role, not merely its file format or storage location.

### 4.1 Functional classes

| Class | Meaning | Examples | Default lifecycle posture |
|---|---|---|---|
| Canonical operational | Authoritative records within a defined domain | T0 canonical candles; T3 paper execution state | Preserve while operational, audit, replay, recovery, or other declared obligations exist |
| Raw source observation | Source-level observations/captures used to build canonical or derived data | Exchange responses, raw event captures | Demand-based; retain while needed for validation, reprocessing, lineage, research, or audit |
| Derived analytical | Reproducible output from identified source versions and transformations | T1 intelligence metrics; T2 feature sets | Retain according to reproducibility, consumer, experiment, and audit obligations |
| Model and experiment | Training/evaluation inputs, model artifacts, inference lineage, experiment records | FreqAI datasets, model runs, evaluation outputs | Preserve enough lineage and artifacts to reproduce or explain material results |
| Signal and decision evidence | Signals, strategy decisions, risk evaluations, backtest results, reason codes | CORE_LEDGER and AI_LEDGER artifacts | Keep independently attributable; never merge the two ledgers for lifecycle convenience |
| Execution and reconciliation evidence | Paper/execution transitions, fills/observations, reconciliation results | T3 paper state and event records | Preserve while needed to reconcile, audit, investigate, or restore state |
| Governance evidence | Manifests, hashes, approvals, policy versions, dependency records, audit logs, tombstones | Dataset manifests and lifecycle audit records | Govern separately; deleting payload does not automatically remove evidence |
| Ephemeral/rebuildable | Temporary outputs with no independent canonical authority | Caches, scratch files, intermediate workspaces | Eligible for short-lived cleanup only under a separately approved, bounded cleanup contract |

### 4.2 Orthogonal sensitivity classification

Functional class does not replace sensitivity classification. A dataset may additionally be classified as public, internal, confidential, or restricted according to the eventual security policy. The exact taxonomy and handling controls remain to be approved. Secrets, API keys, credentials, and personal data must not be copied into manifests or ordinary audit logs.

### 4.3 Classification uncertainty

If a dataset is unclassified, has conflicting stewards, or lacks sufficient provenance, it is treated as **protected / lifecycle action blocked** until reviewed. It must not default to ephemeral or disposable.

## 5. Demand model

“Demand” means a documented, attributable reason the system still needs a particular dataset version. Demand is evaluated per dataset/version and purpose; a generic “dataset is used by the system” flag is insufficient.

Recognized demand categories include:

- active operational reads or downstream jobs;
- registered consumer dependencies and scheduled processing;
- backtest, replay, model training, model evaluation, and inference reproducibility;
- signal and risk-decision explanation;
- data-quality validation, source parity, and correction/reprocessing;
- incident investigation, security review, and recovery;
- regulatory, contractual, or other legal preservation obligations where applicable;
- approved research or benchmark commitments with a named owner and review date.

Demand records should identify the owner, purpose, exact dataset/version, related run/model/experiment/incident, created time, review/expiry time where appropriate, and evidence. The exact registry schema is deferred to the consumer contract.

### 5.1 Demand release

A consumer may release only its own dependency for the exact dataset/version and purpose it registered. Release must be idempotent and auditable.

A release:
- removes only that dependency;
- does not release dependencies owned by other consumers;
- does not cancel an independent hold or reproducibility obligation;
- does not make a dataset immediately archive- or deletion-eligible;
- requires central reevaluation of all remaining demand and policy constraints.

No read-based reference counting or delete-after-ACK behavior is permitted.

### 5.2 Stale or unavailable demand records

A missed heartbeat or expired lease may indicate an abandoned registration, not that the underlying data is no longer needed. Stale dependency handling is defined in [Dataset Consumer Contract](DATASET_CONSUMER_CONTRACT.md). Review deadlines and any separately approved grace/escalation windows trigger owner resolution and auditable reconciliation only; they never auto-release the dependency or remove its protective effect. Until an authorized owner release or governed adjudication resolves the record, stale or ambiguous demand blocks destructive action.

## 6. Lifecycle states

Dataset lifecycle, per-consumer dependency, and deletion request/execution are three separate state domains. Their states must not be collapsed into one shared enum. The consumer contract defines dependency states; the deletion safety contract defines request/execution stages. Cross-domain guards are: Released dependencies do not imply dataset eligibility; Deletion review does not imply authorization; and the dataset may become Deleted/tombstoned only after exact-scope execution is independently verified and reconciled.

The following logical states define policy review. They are not a runtime state machine or an approved database enum.

| State | Meaning | Permitted actions |
|---|---|---|
| Registered | Dataset identity, steward, class, and policy reference recorded | Validate metadata; no automatic retention action |
| Active | At least one current operational or declared demand exists | Read according to access contract; publish new versions through steward |
| Retention review | A review is due or demand may have changed | Reconcile dependencies, holds, lineage, policy, and evidence |
| Archive eligible | All archive prerequisites are met and an approved archive plan exists | Archive only after explicit authorization and verified restore plan |
| Archived | Payload is in an approved archive location with integrity and restore metadata | Restore/read through approved process; no implicit deletion |
| Deletion review | Candidate has no known demand and is undergoing a separate deletion safety review | Non-destructive verification only |
| Deletion authorized | A scoped, time-bounded authorization passed all required approvals and final checks | Storage adapter may execute the exact approved operation |
| Deleted / tombstoned | Authorized deletion completed and outcome reconciled | Preserve required tombstone and audit evidence |
| Hold | Preservation restriction overrides ordinary lifecycle progress | No archive or deletion while the hold applies |

A hold is an orthogonal restriction and may apply to a dataset in any pre-deletion state. State transitions must be monotonic only where appropriate; for example, restored archived data returns to an available state with a recorded event, not by erasing archive history.

## 7. Retention decision framework

No numeric retention duration is approved in this document. The policy must not insert arbitrary day counts, TTLs, or age-based cleanup defaults.

For each dataset class, the eventual policy must define:

- minimum preservation floor, if any, and the authority for that floor;
- active-demand rules and dependency sources;
- reproducibility and lineage obligations;
- audit, incident, recovery, and legal-hold requirements;
- review cadence and owner;
- archive eligibility and restore requirements;
- deletion review prerequisites and approvals;
- evidence that must survive payload removal.

Retention end is not a single timestamp if multiple obligations apply. The effective end condition is the latest unresolved obligation across all applicable purposes and holds. If any obligation has no defined end, the dataset remains protected pending explicit review rather than receiving an invented expiry.

### 7.1 Class-specific decision guidance

| Dataset class | Retention decision inputs | Must not be discarded while |
|---|---|---|
| Canonical operational | Operational need, recovery, source validation, consumer dependencies, correction history | Required by active system operation, reconciliation, or recovery |
| Raw source observation | Downstream lineage, reprocessing, source disputes, data-quality validation, research commitments | A dependent canonical/derived result cannot otherwise be validated or reproduced to the required standard |
| Derived analytical | Source versions, transformation version, consumers, experiment and backtest lineage | Needed to reproduce a material output or satisfy a registered dependency |
| Model and experiment | Model version, training inputs, feature/label definitions, evaluation, inference lineage | Needed to explain or reproduce a model result or approved experiment |
| Signal and decision evidence | Ledger identity, strategy/model version, risk result, audit and backtest needs | Needed to reconstruct a signal, risk decision, or historical paper result |
| Execution/reconciliation | State transitions, incident and recovery needs, audit | Needed to reconcile or restore the execution state |
| Governance evidence | Policy, authorization, lineage, integrity, audit, tombstone obligations | Required to prove what data existed and why/how a lifecycle action occurred |
| Ephemeral/rebuildable | Rebuildability proof, active process lock, bounded workspace contract | In use, not safely reproducible, or its classification is uncertain |

These are decision criteria, not automatic retention durations or deletion permissions.

## 8. Archive policy

Archive is a storage-tier transition, not deletion and not proof that data is no longer valuable. Consumer dependencies must declare the availability/latency requirement they rely on; archive is blocked when the requirement is unknown or incompatible with the proposed archive/restore service. This compatibility requirement remains a design gap until the consumer contract is extended and approved.

Before a dataset can be marked archive eligible, the reviewer must establish:

1. Dataset identity, version, steward, class, and content integrity are known.
2. No active dependency requires the online copy or an online service-level guarantee.
3. No hold or unresolved audit, incident, legal, recovery, or reproducibility obligation prohibits the transition.
4. The archive destination and access controls are approved for the sensitivity class.
5. A restore path, expected restore behavior, and integrity verification method are documented and tested with non-production evidence.
6. Required manifests, source lineage, policy references, and tombstones remain discoverable.
7. The archive operation is idempotent or safely reconcilable after interruption.
8. Central authorization is explicit, scoped to exact dataset versions, and time-bounded.

Archive must fail closed if any prerequisite cannot be verified. No archive tier, vendor, price, restore-time objective, or automated archive schedule is selected here.

## 9. Deletion eligibility is not deletion authorization

A dataset that appears to have no remaining demand may enter **Deletion review** only. It must not be deleted automatically when a retention timer expires or all known consumers ACK.

These requirements are detailed in the separate [Data Deletion Safety Contract](DATA_DELETION_SAFETY_CONTRACT.md), which defines requester/reviewer/approver/executor separation, exact dataset/version/object scope, dependency and hold rechecks, cancellation, authorization, idempotency, reconciliation, tombstones, and post-operation verification.

This policy document does not authorize any deletion, including raw-data, derived-data, expired-data, or ephemeral-data deletion. Even ephemeral cleanup requires the same explicit governance and safety review; no cleanup exception is implied.

## 10. Policy versioning and change control

Every lifecycle policy must have an immutable version identity and record:

- policy ID and version;
- status (draft, reviewed, approved, active, superseded, or withdrawn);
- author, reviewers, approver, and approval evidence;
- effective time and superseded version;
- affected dataset classes and scopes;
- parameter changes and rationale;
- compatibility and migration impact;
- rollback/suspension procedure;
- audit reference.

Policy changes must be prospective by default. A change that shortens retention, relaxes a hold, or changes deletion eligibility must not silently apply to previously registered datasets. It requires explicit impact analysis and approval. Where policy versions conflict or cannot be resolved, the more protective applicable rule governs until reviewed.

A policy version cannot be edited in place after approval; publish a new version and retain the old version for audit. Producers and storage adapters must not embed private copies of retention values that can drift from central policy.

## 11. Exceptions and holds

An exception or hold must be scoped to exact dataset IDs/versions or a clearly bounded class/time range. The record must include:

- requester and accountable owner;
- reason and supporting evidence;
- scope and affected obligations;
- start time and expiry/review date;
- approver and policy basis;
- review outcome, release actor, and release evidence.

No silent indefinite exception is permitted. If a hold's expiry/review date passes without an authorized review, the safe outcome is to keep the hold active and flag it for review, not auto-release it.

## 12. Monitoring and audit requirements

The eventual governance implementation should expose auditable, non-secret status for:

- datasets missing steward, class, provenance, or policy reference;
- unresolved or stale consumer dependencies;
- active holds and overdue hold reviews;
- datasets entering retention review;
- archive candidates, approvals, results, and restore verification;
- deletion-review candidates, approvals, cancellations, and outcomes;
- policy version changes and exceptions;
- failed, partial, or ambiguous storage operations.

Audit events should record actor, action, exact scope, policy version, decision inputs, evidence references, timestamps, and outcome. Sensitive payloads and credentials must not be copied into audit records.

A missing audit trail, inconsistent state, or unverifiable storage result blocks further destructive progression.

## 13. Compatibility and layer responsibilities

- **T0:** remains canonical market-data producer and fenced writer. This policy does not alter the current Candle API, Feeder, PostgreSQL/SQLite lifecycle, or writer implementation.
- **T1:** declares provenance and dependencies for its own futures-intelligence outputs; it cannot delete T0 inputs.
- **T2:** preserves source dataset/version lineage for features, training, inference, backtests, and strategy decisions. CORE_LEDGER and AI_LEDGER remain distinct.
- **T3:** remains authoritative for its paper/execution-state domain; lifecycle rules cannot remove state needed for reconciliation or recovery.
- **T4:** may display read-only lifecycle status; it cannot approve or execute lifecycle actions through dashboard controls.
- **Central governance:** owns policy and decision records; it does not take over producer payload stewardship.
- **Storage adapters:** execute only explicitly authorized, exact-scope operations.

No new endpoint, schema, service, registry, scheduler, credential, migration, or deployment is implied. Existing consumers continue using currently approved interfaces until separately reviewed contracts authorize a change.

## 14. Open decisions — intentionally unresolved

The following require evidence and separate approval; do not fill them with assumptions:

1. Numeric retention floors and review intervals for each dataset class.
2. Exact meaning and proof standard for “reproducible” for each T0–T4 dataset.
3. Consumer dependency schema, heartbeat/grace behavior, and owner escalation.
4. Legal/privacy obligations and jurisdiction-specific retention requirements.
5. Sensitivity taxonomy and archive encryption/access requirements.
6. Archive provider, storage class, restore objectives, and restore cost.
7. Deletion roles, approval quorum, grace period, and final-check window.
8. Evidence/tombstone retention and integrity guarantees.
9. Policy enforcement topology and failover behavior.
10. Mapping of currently deployed datasets and jobs to the proposed classes.

No numeric value should be chosen until dataset inventory, consumer map, reproducibility requirements, and cost/restore evidence are available.

## 15. Acceptance criteria for this policy design

- [x] Shared ownership and central lifecycle governance are reflected.
- [x] Demand is defined per dataset/version/purpose.
- [x] Consumer ACK/release is explicitly not deletion authorization.
- [x] Dataset functional classes and sensitivity separation are defined.
- [x] Lifecycle states distinguish archive eligibility, deletion review, and deletion authorization.
- [x] Retention decisions account for active demand, lineage, reproducibility, audit, recovery, and holds.
- [x] No arbitrary numeric retention periods are introduced.
- [x] Archive requires restore and integrity safeguards.
- [x] Policy versioning, exceptions, holds, and audit requirements are documented.
- [x] T0–T4 boundaries and current-interface compatibility are preserved.
- [x] Open decisions and non-authorized operations are explicit.

## 16. Status and next step

**Status: POLICY FRAMEWORK DESIGN COMPLETE — NOT IMPLEMENTED / NOT ACTIVE.**

The detailed [Dataset Consumer Contract](DATASET_CONSUMER_CONTRACT.md) and [Data Deletion Safety Contract](DATA_DELETION_SAFETY_CONTRACT.md) are now documented separately. The cross-contract review and required corrections are recorded in [Shared Data Lifecycle Cross-Contract Review](SHARED_DATA_LIFECYCLE_CROSS_CONTRACT_REVIEW_2026-11-09.md). Next: build a read-only inventory of actual datasets, consumers, lineage, holds, and storage copies before considering numeric retention values.

No source code, tests, workflow, database/schema, API, VPS, Feeder, policy engine, retention timer, archive, vacuum, or deletion operation is changed or activated by this document. Real-data lifecycle operations remain unauthorized without separate review and explicit approval.
