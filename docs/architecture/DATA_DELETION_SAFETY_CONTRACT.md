# Data Deletion Safety Contract — Design

Date: 2026-11-09
Status: **DESIGN — safety contract proposal; not implemented, approved for execution, or activated**

Related documents:
- [Shared Data Foundation](SHARED_DATA_FOUNDATION.md)
- [Central Data Lifecycle Policy](CENTRAL_DATA_LIFECYCLE_POLICY.md)
- [Dataset Consumer Contract](DATASET_CONSUMER_CONTRACT.md)
- [Shared Data Foundation Lifecycle ADR](SHARED_DATA_FOUNDATION_LIFECYCLE_ADR_2026-11-08.md)

## 1. Purpose and strict scope

This contract defines the minimum governance and safety boundary that would be required before any shared dataset could be deleted. It separates a deletion request, eligibility review, independent approval, execution authorization, storage execution, and post-operation verification.

This is a design-only document. It does **not** grant permission to delete any dataset, raw data, derived data, expired data, cache, archive, database row, file, backup, or object. It does not create an executor or authorize a dry-run against real storage. Any future implementation and any first real-data operation require separate review and explicit approval.

## 2. Non-negotiable safety invariants

1. **No automatic deletion.** Age, TTL expiry, low storage, lack of recent reads, job completion, ACK, dependency release, or archive completion cannot independently trigger deletion.
2. **Eligibility is not authorization.** A candidate may pass an eligibility review and still must not be deleted until a separate approval and exact-scope execution authorization exist.
3. **Fail closed.** Missing, stale, contradictory, unavailable, or unverifiable evidence blocks the request or execution.
4. **Exact immutable scope.** Authorization names exact dataset IDs, immutable version IDs, and storage-object identities. Wildcards, mutable aliases, prefixes, table-wide predicates, and “all old data” are prohibited unless a future contract explicitly constrains and proves their expansion before approval.
5. **Independent review.** Requester cannot be the sole reviewer and executor. The same identity must not both request and approve a destructive action.
6. **No inferred consent.** Silence, timeout, missing heartbeat, service decommission, or failed notification is not approval.
7. **No cross-domain authority.** Consumer, dashboard, producer, and storage-adapter roles do not acquire deletion authority through ordinary access.
8. **Preserve evidence.** Required manifests, lineage, policy versions, approvals, audit records, and tombstones survive payload deletion according to separately approved policy.
9. **No cascading deletion.** Deleting one dataset version does not implicitly delete source versions, derived outputs, model artifacts, ledger records, replicas, backups, or evidence.
10. **Reversibility before execution.** Before execution starts, authorization can be cancelled. After execution starts, rollback is not assumed; recovery depends on separately verified backups or replicas.
11. **No partial success presented as success.** Partial, ambiguous, or unverified outcomes remain unresolved and block subsequent destructive actions on the affected scope.
12. **Paper-only system boundary remains.** This contract does not enable live trading or alter `ai_execution_enabled=false`.

## 3. Roles and separation of duties

| Role | Responsibility | Restrictions |
|---|---|---|
| Requester | Proposes deletion of a stated dataset/version with purpose, evidence, and reason | Cannot approve own request or execute deletion |
| Dataset steward / producer owner | Confirms identity, provenance, class, dependencies, producer obligations, and impact | Cannot unilaterally approve deletion of shared data |
| Consumer owners | Confirm or dispute their own dependency records and reproducibility obligations | Cannot approve deletion for other consumers |
| Lifecycle reviewer | Evaluates policy, demand, holds, lineage, archive status, and eligibility evidence | Cannot alter source evidence to force eligibility |
| Independent approver | Reviews the complete evidence package and authorizes or rejects the exact request | Must be independent of requester; approval is not a general-purpose delete permission |
| Execution authority | Issues a narrow, time-bounded execution authorization after final rechecks | Cannot widen approved scope or bypass policy |
| Storage executor / adapter | Performs only the exact authorized operation and returns evidence | Cannot decide eligibility, approve, expand scope, or retry ambiguously without reconciliation |
| Auditor | Reviews the full chain of events and evidence | Read-only unless separately delegated |

For a small personal system where full organizational separation is not available, the minimum acceptable alternative must be explicitly designed and approved; it must not silently collapse requester and approver into one identity. A second-person approval is the safer default for shared canonical or non-rebuildable data.

## 4. Deletion lifecycle and gates

The following stages are logical governance states, not implementation enums or an enabled workflow.

| Stage | Meaning | Gate to proceed |
|---|---|---|
| Proposed | Request submitted for exact dataset/version scope | Required request metadata and authenticated requester |
| Eligibility review | Evidence is gathered and reconciled | Identity, classification, demand, holds, lineage, recovery, policy, and archive checks |
| Eligible for approval | Review finds no known blocker | Complete, current evidence package; no automatic execution |
| Approved | Independent approver accepts the exact request | Approval records scope, rationale, policy version, evidence digest, and conditions |
| Awaiting execution authorization | Final checks occur immediately before execution | Fresh dependency/hold/policy checks and exact storage-object resolution |
| Execution authorized | Narrow, time-bounded authorization issued | Authorized actor, operation, exact objects, idempotency key, and expiry are bound |
| Executing | Storage adapter performs authorized work | Adapter verifies authorization and exact scope before each operation |
| Reconciliation required | Outcome is partial, interrupted, or ambiguous | No further destructive action until authoritative state is reconciled |
| Verified complete | Exact requested objects are confirmed removed and evidence retained | Independent post-operation verification |
| Cancelled / rejected / expired | Request did not execute | Terminal audit record; a new request is required for changed scope |

An authorization expiry must not cause deletion to run automatically. It invalidates the authorization. A new final check and authorization are required.

## 5. Request requirements

A deletion request must be explicit, attributable, and limited to a reviewable scope. It should include:

- request ID and idempotency key;
- requester identity and accountable owner;
- exact dataset ID and immutable version ID;
- exact object or record manifest to be affected;
- producer/steward and functional/sensitivity classifications;
- reason for deletion and business/system purpose;
- policy ID/version claimed to permit review;
- evidence references for dependency, lineage, hold, recovery, and archive checks;
- known replicas, exports, caches, derived data, backups, and downstream references;
- proposed operation type and storage domain;
- requested execution window and cancellation contact, if applicable;
- declaration of whether data is rebuildable and the evidence supporting that claim.

A request with unresolved identity, broad selector, unknown replicas, missing steward, or incomplete object manifest is rejected or returned for clarification. The system must not “best effort” expand an ambiguous scope.

## 6. Eligibility review checklist

Eligibility review is read-only. It must not mutate payloads, remove dependencies, alter retention policy, compact tables, vacuum storage, or stage deletion.

### 6.1 Identity and integrity

- Resolve dataset ID and immutable version ID from the authoritative registry.
- Verify producer, steward, classification, schema/contract version, lineage, and content digest.
- Resolve the exact storage objects associated with the version.
- Confirm the object manifest is complete and immutable for the review.
- Detect duplicate, shared, referenced, or aliased storage objects.
- If identity or object mapping cannot be proven, stop.

### 6.2 Demand and consumer dependencies

- Read authoritative dependency state, not a dashboard/read-model snapshot alone.
- Confirm each consumer dependency for the exact version is released or otherwise resolved by its owner and governed review.
- Reconcile stale, orphaned, disputed, transferred, and decommissioned consumer identities.
- Check non-consumer obligations: reproducibility, backtest/replay, model training/evaluation/inference, source parity, correction/reprocessing, operational recovery, and approved research.
- A consumer ACK or absence of recent reads is not sufficient.
- If registry consistency or owner state is unavailable, stop.

### 6.3 Holds and obligations

- Check legal, privacy, security, incident, investigation, audit, contractual, and recovery holds where applicable.
- Check policy minimums and any class-specific preservation floor.
- Check open incidents, unresolved integrity issues, and producer correction obligations.
- Check whether governance evidence must be retained after payload removal.
- Any active or ambiguous hold blocks eligibility.

### 6.4 Recovery and rebuildability

- Determine whether the data is canonical, unique, derived, or reproducible.
- Verify the authoritative source versions and transformation/model versions needed to rebuild it.
- Confirm required inputs remain available and themselves protected.
- For data claimed to be rebuildable, require evidence of a successful controlled rebuild and integrity comparison; a statement that “the pipeline can regenerate it” is insufficient.
- Confirm recovery/backup requirements and restore evidence independently.
- If data is canonical, non-reproducible, or recovery evidence is missing, deletion is blocked pending explicit policy decision.

### 6.5 Archive and alternative action

- Determine whether archive, tiering, or access restriction meets the storage objective without deletion.
- Verify archive restore and integrity evidence if archive is proposed.
- Record why archive or no-op is insufficient if deletion is still requested.
- Archive status does not imply deletion eligibility; archived data remains protected until separately reviewed.

### 6.6 Evidence freshness

Every evidence item must identify its source, scope, timestamp, and authoritative revision. Evidence must be refreshed before execution authorization. If the policy does not define an acceptable freshness window, the review cannot invent one; the open policy parameter must be resolved first.

## 7. Approval requirements

The approval package must contain:

1. Exact dataset/version/object manifest and a digest of that manifest.
2. Requester identity, reason, and accountable owner.
3. Dataset steward's assessment.
4. Consumer dependency reconciliation results.
5. Central lifecycle policy version and eligibility decision.
6. Hold, audit, legal, incident, and recovery checks.
7. Rebuildability or archive assessment and supporting evidence.
8. Replica/backup/export impact analysis and scope disposition.
9. Expected impact, failure modes, and recovery limitations.
10. Proposed operation, execution constraints, and cancellation procedure.

The independent approver must approve or reject the complete package. Any material change to scope, object manifest, policy version, evidence, or operation invalidates the approval and requires a new review. Approval of one dataset version does not authorize another version.

No quorum, approver count, or approval SLA is fixed here. Those are unresolved governance decisions. Until resolved and explicitly approved for the relevant dataset class, deletion remains disabled.

## 8. Final execution authorization

Approval alone does not authorize a storage operation. Immediately before execution, the execution authority must recheck:

- request remains approved and not cancelled or expired;
- exact manifest digest is unchanged;
- dataset/version identity still resolves to the same objects;
- dependency and hold state has not changed;
- policy version remains applicable and has not been withdrawn or superseded in a blocking way;
- no new incident, recovery, or legal obligation has appeared;
- required evidence and audit sink are available;
- destination/target storage identity is correct;
- operation is supported, bounded, and idempotent or safely reconcilable;
- executor identity has only the required narrow permission.

The authorization must bind at least:
- authorization ID;
- request ID;
- exact dataset/version and object-manifest digest;
- exact operation and storage domain;
- policy version and approval evidence;
- authorized executor identity;
- not-before and expiry conditions, if used;
- unique idempotency/replay-protection key;
- permitted retry/reconciliation behavior.

If any recheck fails, the authorization is not issued. If the state changes after authorization but before the first destructive write, the executor must revalidate and stop if authorization is no longer valid.

## 9. Execution contract

The storage executor must:

- accept only a valid, unexpired authorization from the trusted authority;
- verify the authorization signature/identity and exact manifest digest;
- reject wildcard, prefix, mutable-alias, or unbounded query scopes;
- operate only on the listed objects;
- avoid cascading to related data unless each related object has its own approved scope;
- record per-object outcomes and durable operation IDs;
- use idempotent semantics where supported;
- stop on unexpected object, permission, digest, or state mismatch;
- avoid retrying ambiguous destructive operations until reconciliation establishes the prior outcome;
- preserve required manifests, audit records, lineage, policy and approval evidence, and tombstones;
- report success only after post-operation verification.

The executor must not perform retention decisions, infer expiry, release dependencies, create approvals, or widen a request. Database-specific operations such as row deletion, partition drop, truncate, vacuum, object lifecycle expiration, and backup expiration require separate adapter-specific safety review. This document authorizes none of them.

## 10. Cancellation, grace, and expiry

A request may be cancelled by its requester or authorized governance actor before execution begins, subject to a durable cancellation event. An approver may revoke approval before execution authorization. The execution authority may revoke an authorization before the executor starts.

Once destructive execution begins, cancellation cannot be represented as rollback. The executor must stop at a safe boundary where possible, report completed and remaining objects, and move the request to reconciliation. Already removed objects may require restore from a verified backup; restoration must be a separate controlled operation.

A grace period, minimum waiting interval, authorization lifetime, and evidence freshness window are policy parameters and are deliberately unspecified. No numeric values are approved. No default timer may initiate execution.

## 11. Idempotency, retries, and partial failure

- A duplicate request with the same idempotency key and same semantic payload resolves to the original request.
- Reuse of a key with different scope or reason is rejected and audited.
- An approval is bound to one immutable manifest digest; changing the manifest invalidates approval.
- An execution retry must use the same authorization and operation identity only when the adapter can prove safe idempotent replay.
- If the outcome is unknown, do not blindly retry. Query authoritative storage state and reconcile per object.
- Partial completion is recorded per object; it is never reported as full success.
- A failed object does not authorize widening the scope or skipping failed checks.
- A new or changed scope requires a new request and approval.

## 12. Replicas, backups, exports, and derived data

Deletion scope must explicitly account for data copies and relationships:

- primary storage object;
- replicas and read copies;
- archives and object-store versions;
- snapshots and backups;
- exports and local copies;
- derived datasets, features, labels, and model artifacts;
- backtest, signal, risk, and execution evidence;
- manifests, lineage, audit logs, and tombstones.

The default is **no cascading deletion**. A primary-payload deletion request does not imply deletion of backups, replicas, exports, or derived outputs. Each copy has its own owner, policy, dependency, and authorization. Where a copy cannot be located or its lifecycle cannot be governed, the request must disclose the limitation and remain blocked if the copy creates an unresolved preservation or privacy obligation.

Backup expiration and destruction must be a separate contract, including restore-chain integrity and evidence retention. Do not remove a backup needed to recover a dataset while its recovery obligation remains active.

## 13. Tombstones and retained evidence

After verified deletion, the governance system should preserve a tombstone sufficient to prove what was deleted, under which authority, and with what outcome. It should include:

- dataset ID and immutable version ID;
- deleted object-manifest digest and storage domain;
- request, approval, and authorization IDs;
- policy version and decision evidence references;
- requester, reviewer, approver, executor identities;
- timestamps for request, approval, authorization, execution, and verification;
- per-object outcome and adapter operation reference;
- reason and final status;
- known exclusions (for example, backups intentionally retained under separate policy).

Tombstones and audit records must not contain deleted payload contents, credentials, secrets, or unnecessary sensitive data. Their own retention and access controls are governed separately. A tombstone is not a substitute for an audit trail or proof that every replica was deleted.

## 14. Post-operation verification and reconciliation

Verification must be independent of the executor's success response where technically possible. It should confirm:

1. Every authorized object is absent or in the exact approved terminal state.
2. No object outside the approved manifest was changed.
3. Required manifests, lineage, tombstones, approvals, and audit records remain readable and integrity-verifiable.
4. Replicas/backups/exports have the disposition recorded in the approval package.
5. Storage accounting and authoritative metadata are reconciled.
6. Partial failures and residual references are identified and assigned.
7. Final outcome is recorded as Verified complete, Partial, Failed, or Unknown.

An adapter return code alone is not sufficient evidence. If independent verification is unavailable, status remains NOT VERIFIED and the system must not claim successful deletion.

## 15. Emergency and legal requests

Emergency requests do not bypass identity, exact-scope, audit, or authorization checks. Any emergency path must be separately designed, narrowly scoped, time-bounded, independently reviewable after the event, and explicitly approved before implementation.

A valid legal or privacy requirement may impose deletion or preservation obligations that differ from ordinary lifecycle policy. Such cases require competent review, documented legal basis, exact scope, and evidence of the controlling instruction. This document does not interpret legal requirements or authorize an operator to act on an unverified request.

## 16. T0–T4 boundaries

| Layer | Deletion-safety boundary |
|---|---|
| T0 Data Foundation | Canonical market data is protected by default; deletion requires explicit dataset/version-level governance and cannot bypass the fenced-writer boundary |
| T1 Futures Intelligence | May request review of its own derived outputs; cannot delete T0 source versions or other consumers' data |
| T2 Strategy / FreqAI | Must preserve model, feature, training, inference, backtest, and decision lineage; CORE_LEDGER and AI_LEDGER remain distinct |
| T3 Paper / execution | Paper-state and reconciliation evidence cannot be removed while required to reconstruct or audit paper outcomes |
| T4 Dashboard | Read-only; UI actions cannot request, approve, or execute deletion |
| Central governance | Evaluates eligibility and issues scoped approvals/authorizations under separately approved policy |
| Storage adapter | Executes only exact authorized objects; no policy judgment or cascading action |

These are target boundaries, not claims about deployed capabilities. No current layer is authorized to delete data through this document.

## 17. Security and operational controls

Before implementation, the design must specify:
- separate identities and least-privilege credentials for requester, approver, authorization service, and executor;
- tamper-evident audit and approval records;
- replay protection and authorization revocation;
- safe behavior during network partition, registry outage, audit sink outage, clock uncertainty, and failover;
- prevention of shell/SQL/object-store injection through untrusted selectors;
- rate and blast-radius limits at the adapter boundary;
- operator confirmation and incident escalation for unexpected object counts;
- secret redaction and access logging;
- recovery and restore tests for any data class that claims recoverability.

If the authoritative policy or audit system is unavailable, destructive execution is blocked. No break-glass mode is enabled by this design.

## 18. Open decisions — require separate approval

1. Which dataset classes, if any, may ever be deleted and under what legal/policy basis.
2. Whether canonical T0 data is non-deletable by default or subject to narrowly defined exceptions.
3. Required independent approver count and separation-of-duties model.
4. Grace period, cancellation deadline, authorization lifetime, and evidence freshness window.
5. Exact identity, signing, replay-protection, and credential mechanisms.
6. Authoritative registry and audit-store consistency/availability requirements.
7. Object-manifest format, digest algorithm, and storage adapter contracts.
8. How to inventory and govern replicas, backups, snapshots, exports, and local copies.
9. Rebuildability proof standard and required restore-test evidence by class.
10. Tombstone/audit retention and privacy constraints.
11. Emergency/legal request governance.
12. Adapter-specific safeguards for PostgreSQL, SQLite, object storage, backups, and archives.
13. Independent verification method and acceptable residual state.
14. Who can approve the first controlled test, and what non-production evidence is required.

Until these are decided, reviewed, and explicitly approved, deletion remains disabled. No numeric timing defaults are introduced.

## 19. Acceptance criteria for this design

- [x] Separates request, eligibility, approval, execution authorization, execution, and verification.
- [x] Requires exact immutable dataset/version/object scope.
- [x] Separates requester, reviewer, approver, execution authority, and executor.
- [x] Defines fail-closed checks for identity, dependencies, holds, lineage, recovery, policy, and audit.
- [x] States that ACK, timeout, age, and missing heartbeat never authorize deletion.
- [x] Prohibits implicit cascading to replicas, backups, exports, and derived data.
- [x] Defines cancellation, expiry, idempotency, retry, partial-failure, and reconciliation behavior.
- [x] Requires retained tombstone/audit evidence and independent post-operation verification.
- [x] Preserves T0–T4 boundaries and paper-only execution constraints.
- [x] Leaves numeric timing values and implementation choices unresolved.
- [x] Explicitly states that no deletion is authorized or activated.

## 20. Status and next step

**Status: DELETION SAFETY CONTRACT DESIGN COMPLETE — NOT IMPLEMENTED / NOT APPROVED FOR EXECUTION / NOT ACTIVE.**

Next: conduct a documentation-only cross-contract consistency review across the Shared Data Foundation, Central Data Lifecycle Policy, Dataset Consumer Contract, and this Deletion Safety Contract. Identify contradictions, missing decisions, and approval gates. Do not implement an executor, API, schema, registry, scheduler, archive, vacuum, cleanup, or deletion operation as part of that review.

No source code, tests, workflow, database/schema, API, VPS, Feeder, registry, scheduler, retention timer, archive, vacuum, backup expiry, or deletion operation is changed or activated by this document. Real-data lifecycle operations remain unauthorized without separate review and explicit approval.
