# Dataset Consumer Contract — Design

Date: 2026-11-09
Status: **DESIGN — contract proposal; not implemented or activated**

Related architecture and policy:
- [Shared Data Foundation](SHARED_DATA_FOUNDATION.md)
- [Central Data Lifecycle Policy](CENTRAL_DATA_LIFECYCLE_POLICY.md)
- [Shared Data Foundation Lifecycle ADR](SHARED_DATA_FOUNDATION_LIFECYCLE_ADR_2026-11-08.md)

## 1. Purpose

Define the contract by which a producer publishes a dataset version and a consumer declares, uses, and releases a dependency on that exact version. The contract makes demand visible to central lifecycle governance without granting consumers ownership of shared payloads or lifecycle authority.

This is a logical contract only. It does not define an API, database schema, registry implementation, queue, scheduler, lease service, authentication mechanism, or runtime behavior.

## 2. Core invariants

1. A dependency identifies an immutable dataset version, not a moving alias such as `latest`.
2. Consumer registration is explicit, attributable, purpose-bound, and auditable.
3. A consumer can release only dependency records it owns or is explicitly delegated to manage.
4. ACK means only that the named consumer completed the named processing obligation. It is not archive or deletion authorization.
5. Releasing one dependency does not release another consumer's dependency, a legal/incident hold, a reproducibility obligation, or a producer obligation.
6. No dataset is lifecycle-eligible based solely on no recent reads, a missing heartbeat, a consumer timeout, or a successful job.
7. Missing, stale, conflicting, or unavailable dependency state blocks destructive lifecycle progression.
8. Producers retain stewardship of their datasets; consumers receive only the access needed for their declared purpose.
9. All state-changing contract operations are authenticated, idempotent, scoped, and auditable.
10. This contract does not change T0's canonical/fenced writer boundary or enable live trading.

## 3. Actors and authority

| Actor | May | May not |
|---|---|---|
| Producer / dataset steward | Publish a dataset version and its manifest; declare lineage and known producer-side obligations; correct data through its approved producer process | Release consumer-owned dependencies or unilaterally delete shared data |
| Consumer service | Resolve and read authorized dataset versions; register its own dependency; report processing outcome; release its own dependency | Modify canonical payloads, release another consumer's dependency, or authorize lifecycle action |
| Consumer owner / operator | Manage dependencies within an explicitly delegated consumer identity; reconcile abandoned registrations | Claim ownership of data produced by another layer |
| Central lifecycle authority | Validate registrations, evaluate all demand and holds, record policy decisions, and determine lifecycle eligibility | Treat ACK as deletion approval or bypass storage authorization |
| Storage adapter | Execute exact, separately authorized lifecycle operations | Infer consumer demand or make lifecycle policy decisions |
| Auditor | Inspect dependency and decision evidence | Mutate records without explicit delegated authority |

A human operator does not gain consumer-service authority merely by having dashboard access. Delegation must be explicit and auditable.

## 4. Dataset identity and version reference

A consumer dependency must refer to an immutable dataset version using a stable reference. The logical reference contains at least:

- `dataset_id`: stable identity of the dataset family;
- `dataset_version_id`: immutable version identity;
- `producer_id` and producer revision;
- schema/contract version;
- content digest or an equivalent integrity reference;
- source/lineage references where applicable;
- covered time range and availability/completion metadata where applicable;
- dataset classification and lifecycle policy reference.

These are conceptual fields, not an approved schema. A consumer must reject an unresolved reference, an ambiguous version, a digest mismatch, an incompatible schema, or a version that is not authorized for its identity. It must not silently substitute a newer version.

### 4.1 Version pinning

- Registration pins the exact version consumed.
- A producer publishing a new version does not mutate existing registrations.
- A consumer moving to a new version must register the new dependency, verify it, and then release the old dependency only after its own processing/reproducibility obligation is complete.
- A mutable alias may be used for discovery only; it is not sufficient for a durable dependency record.

## 5. Dependency record

A dependency record should capture the following logical information:

| Field | Purpose |
|---|---|
| dependency_id | Stable idempotency and audit identity |
| consumer_id | Authenticated consumer identity |
| owner_id | Accountable service/team/operator owner |
| dataset_id + dataset_version_id | Exact dataset/version reference |
| purpose | Why this consumer needs this version |
| required_access | Read/metadata access scope needed |
| state | Requested, active, release-pending, released, rejected, or under-review |
| created_at / updated_at | Audit ordering |
| expected_completion or review_at | Review trigger, not automatic release time |
| source_job/run/model/experiment | Optional trace to the consuming activity |
| registration_idempotency_key | Deduplicates retries |
| evidence_refs | References to processing, validation, or approval evidence |
| policy_ref | Policy version evaluated at registration |

The final schema, required/optional fields, and indexes must be established separately through API/data-contract review.

## 6. Registration protocol

The conceptual registration sequence is:

1. Authenticate the consumer and resolve its declared owner/delegation.
2. Resolve the exact dataset/version reference.
3. Validate that the dataset exists, is published, is readable by this consumer, and has compatible classification and schema.
4. Validate purpose and access scope against the consumer's approved role.
5. Submit a registration with a stable idempotency key.
6. Central governance records the dependency and returns a durable dependency identifier and state.
7. Consumer verifies the returned reference before beginning work.

Registration must be fail-closed. If the central registry, authorization service, policy reference, or dataset metadata cannot be verified, the consumer must not assume registration succeeded and must not start work that relies on an unprotected dependency.

Retries with the same idempotency key and same logical payload must resolve to the same dependency result. Reuse of a key with a different consumer, dataset version, or purpose must be rejected as a conflict.

### 6.1 Registration timing

A consumer should register before relying on the dataset version. If a workflow cannot register before discovery/read, it must use a separately approved short-lived acquisition protocol; it must not create an untracked retention gap. No such acquisition protocol is approved by this document.

## 7. Processing and ACK semantics

ACK is a consumer processing statement, not a lifecycle command. It must be scoped to a dependency ID and the processing obligation represented by that dependency.

An ACK may report:
- processing completed successfully;
- processing completed with warnings;
- processing failed;
- processing was intentionally abandoned and requires owner review.

An ACK should include the consumer identity, dependency ID, job/run reference, result, completion timestamp, and evidence reference where available.

Rules:

- ACK cannot change the dataset payload or producer manifest.
- ACK cannot release dependencies owned by other consumers.
- ACK cannot override holds, retention floors, lineage, audit, recovery, or reproducibility requirements.
- A successful ACK does not automatically release the dependency unless a separate consumer policy explicitly defines that behavior and the consumer performs an authenticated release operation.
- Failure ACK does not release the dependency.
- Duplicate ACK with the same idempotency key and same result is harmless; conflicting duplicate ACK is rejected or placed under review.
- ACK received after release is retained as late evidence but does not silently reactivate or rewrite the dependency. Reacquisition requires a new registration.

## 8. Release protocol

Release is the consumer's declaration that it no longer requires that specific dependency for the declared purpose. It is not a global statement that the dataset is no longer needed.

Conceptual sequence:

1. Consumer confirms its own processing, retry, replay, and local reproducibility obligations are complete or separately preserved.
2. Consumer submits release for its dependency ID with an idempotency key and reason/evidence.
3. Governance authenticates ownership/delegation and verifies the dependency is in a releasable state.
4. Governance records the release event and returns the resulting dependency state.
5. Consumer verifies the durable result; uncertain outcomes are reconciled by querying the same dependency, not by creating a different release blindly.

Release must be scoped to one dependency. Bulk release requires an explicit, reviewable list of dependency IDs and must not be inferred from a wildcard dataset or consumer selector.

A released dependency is terminal for that registration. If the consumer needs the version again, it creates a new registration. Reopening a released record is not the normal retry path.

## 9. State model and transitions

The following states are conceptual contract states, not implementation enums:

| State | Meaning | Allowed next states |
|---|---|---|
| Requested | Registration received but not yet fully validated | Active, Rejected, Under review |
| Active | Dependency is recorded and protects the exact dataset version for the declared purpose | Release pending, Under review |
| Release pending | Consumer requested release; ownership and evidence are being checked | Released, Active, Under review |
| Released | This dependency no longer contributes active demand | Terminal; reacquisition uses a new dependency |
| Rejected | Registration was not accepted | Terminal; corrected request uses a new idempotency key |
| Under review | Ownership, identity, conflict, stale state, or evidence needs resolution | Active, Release pending, Released, Rejected only after authorized review |

No timeout automatically transitions Active to Released. A dependency with uncertain ownership or state remains protective until reconciled.

## 10. Stale consumer and abandoned dependency handling

A stale dependency is a governance review condition, not evidence that the dataset can be deleted.

Possible signals include:
- consumer heartbeat absent;
- owner identity no longer resolves;
- job/run appears abandoned;
- review date passed;
- service identity was rotated or decommissioned;
- repeated processing failures.

Required handling:

1. Mark the record for review without removing its protective effect.
2. Preserve the exact dataset/version reference and audit history.
3. Notify or route to the accountable owner through a separately approved mechanism.
4. Allow owner or authorized operator to confirm continued need, release, or transfer ownership.
5. If owner cannot be reached, require a documented central governance review and evidence-based decision.
6. Retain the dependency as unresolved if evidence is insufficient.

No grace duration, notification channel, escalation SLA, or automatic orphan cleanup is set here. Those are open policy parameters. Expired review dates must not silently release dependencies.

### 10.1 Consumer decommissioning

Before decommissioning a consumer identity, its owner must inventory all active dependencies and explicitly release, transfer, or preserve each one. Deleting a service account must not erase dependency records or their audit evidence.

## 11. Conflicts, duplicates, and concurrency

- **Duplicate registration:** Same idempotency key and same logical request returns the existing result.
- **Idempotency conflict:** Same key with different semantic content is rejected and audited.
- **Concurrent release:** Only one durable release outcome is recorded; retries return that outcome.
- **Concurrent ACK and release:** Both events remain auditable. Release eligibility is evaluated using the full ordered event history; an ACK cannot authorize release.
- **Version replacement:** New version registration and old version release are separate operations.
- **Ownership transfer:** Requires explicit authorization, a durable transfer event, and continuity of dependency protection; no delete/recreate gap.
- **Registry partition/unavailability:** No new dependency is assumed registered and no destructive lifecycle progression is allowed.
- **Inconsistent replica/read model:** Consumers and governance must use an authoritative consistency contract; stale read models cannot be used to prove absence of dependencies.

The exact concurrency model, consistency level, and conflict-resolution mechanics require API and storage design.

## 12. Access and security boundaries

- Consumers receive read-only access to approved dataset versions and metadata required for their purpose.
- Dependency records are writable only by the owning consumer identity or an explicitly delegated operator.
- Consumer identities must be distinct from producer and lifecycle-authority identities.
- Dataset payload write, correction, archive, and deletion permissions are not implied by dependency registration.
- Credentials and secrets must not appear in dependency records, ACKs, evidence payloads, or ordinary logs.
- Authorization checks must be applied to both registration and release; knowledge of a dependency ID is not sufficient authority.
- Audit records must identify the authenticated actor, delegated principal if any, action, exact scope, timestamp, idempotency key, and outcome.

No authentication technology, token format, network boundary, or secret store is selected here.

## 13. T0–T4 consumer expectations

| Layer | Expected dependency behavior | Explicit boundary |
|---|---|---|
| T0 Data Foundation | Registers internal dependencies for its own validation/recovery workflows where needed; publishes canonical dataset identity/version/lineage | Remains canonical producer and fenced writer; consumers do not gain T0 write/delete access |
| T1 Futures Intelligence | Pins exact T0 source versions and registers demand for source data needed by intelligence outputs and replay | Cannot release another consumer's dependency or delete T0 source data |
| T2 Strategy / FreqAI | Pins source, feature, label, model, experiment, and backtest versions needed to reproduce results | CORE_LEDGER and AI_LEDGER remain independent; no cross-ledger release or state merging |
| T3 Paper / execution | Registers exact signal, risk, and market-data versions required for paper-state reconstruction and reconciliation | Paper-only boundary remains; no live order authority |
| T4 Dashboard | Uses read-only views; any durable export/report job registers its own dependency | Dashboard viewing or UI dismissal is not a release or lifecycle command |

This table defines intended contract behavior, not proof that each layer currently implements it.

## 14. Observability and reconciliation

The eventual implementation should support audit-friendly queries for:
- active dependencies by dataset/version;
- dependencies by consumer, owner, purpose, and source run;
- pending releases and release outcomes;
- stale and under-review dependencies;
- duplicate/idempotency conflicts;
- dependencies affected by policy or classification changes;
- ownership transfers and consumer decommissioning;
- unresolved registration/release outcomes.

Reconciliation must compare authoritative dependency records with consumer-side job/run state and preserve both evidence sets. It must not silently delete unmatched records. Any mismatch that could understate demand blocks destructive lifecycle progression until resolved.

## 15. Failure behavior

| Failure | Required safe behavior |
|---|---|
| Registry unavailable during registration | Fail closed; do not assume dependency is protected or begin dependent work |
| Registry unavailable during release | Do not assume release succeeded; preserve dependency and reconcile later |
| Authorization unavailable | Reject or defer mutation; no permissive fallback |
| Dataset/version metadata missing | Reject registration |
| Digest/schema mismatch | Reject use and raise integrity/compatibility review |
| Duplicate request retry | Return durable prior result if semantically identical |
| Conflicting idempotency key | Reject and audit |
| Consumer heartbeat lost | Mark for review; keep dependency protective |
| Owner unavailable | Keep unresolved dependency; require governed review |
| ACK delivery lost | Query/retry idempotently; do not infer release |
| Stale dashboard/read model | Do not use it as proof that no dependency exists |
| Partial persistence or ambiguous outcome | Preserve protective state and reconcile before further action |

## 16. Relationship to lifecycle policy and deletion safety

This contract supplies evidence of declared consumer demand. The central lifecycle policy combines that evidence with producer obligations, lineage/reproducibility needs, holds, audit/recovery obligations, and class-specific retention rules.

Even when every known consumer dependency is Released:
- dataset may still be Active due to non-consumer obligations;
- archive eligibility requires a separate policy evaluation and archive safeguards;
- deletion review requires a separate safety contract;
- deletion authorization requires explicit, scoped approval and a separate execution path.

The consumer contract never grants permission to archive or delete.

## 17. Open decisions

The following remain unresolved and must be decided before implementation:

1. Canonical dataset/version identifier format and digest algorithm.
2. Required metadata and schema evolution/compatibility rules.
3. Authoritative registry and consistency guarantees.
4. Consumer identity, owner/delegation, and authentication model.
5. Idempotency-key scope, lifetime, and conflict response.
6. ACK result taxonomy and evidence requirements.
7. Whether any consumer class may auto-release after a separately defined completion condition.
8. Stale-consumer review cadence, grace periods, escalation, and ownerless dependency process.
9. Ownership transfer and decommissioning workflow.
10. Read model freshness guarantees and reconciliation frequency.
11. Operational availability targets and registry recovery procedure.
12. API shape, schema, audit storage, and migration strategy.

No default timeout or automatic release behavior should be introduced until these decisions are supported by operational evidence and approved.

## 18. Acceptance criteria for this design

- [x] Dependency is pinned to an immutable dataset version.
- [x] Registration is explicit, authenticated, purpose-bound, and idempotent.
- [x] ACK semantics are separated from release and lifecycle authorization.
- [x] Consumer can release only its own dependency.
- [x] Release is exact-scope and auditable.
- [x] Stale consumer/owner loss does not auto-release demand.
- [x] Duplicate, concurrent, conflicting, and unavailable-registry cases fail safely.
- [x] T0–T4 boundaries are documented without claiming current implementation.
- [x] No API/schema/service/runtime behavior is specified as already implemented.
- [x] Deletion remains outside this contract and requires separate authorization.

## 19. Status and next step

**Status: CONSUMER CONTRACT DESIGN COMPLETE — NOT IMPLEMENTED / NOT ACTIVE.**

Next: design `DATA_DELETION_SAFETY_CONTRACT.md` as a separate contract for deletion request, review, approval, grace/cancellation, exact-scope execution, idempotency, tombstones, audit, and post-operation verification. That document must not authorize actual deletion or activate an executor.

No source code, tests, workflow, database/schema, API, VPS, Feeder, registry, scheduler, retention timer, archive, vacuum, or deletion operation is changed or activated by this document. Real-data lifecycle operations remain unauthorized without separate review and explicit approval.
