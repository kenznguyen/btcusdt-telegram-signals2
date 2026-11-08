# Cross-Contract Consistency Review — Shared Data Lifecycle

Date: 2026-11-09
Status: **DOCUMENTATION REVIEW COMPLETE — FINDINGS RECORDED; NO IMPLEMENTATION AUTHORIZED**

## 1. Scope and evidence

Reviewed the following four design documents on branch `feature/t0-centralized-data-feeder-p1-20261101`:

| Document | Blob SHA | Characters |
|---|---|---:|
| [Shared Data Foundation](SHARED_DATA_FOUNDATION.md) | fe18d3eef7f2789a06905affc78d039589798bd5 | 18432 |
| [Central Data Lifecycle Policy](CENTRAL_DATA_LIFECYCLE_POLICY.md) | 599319ce3f1a774139144e3afb6b021c1bb7a359 | 21744 |
| [Dataset Consumer Contract](DATASET_CONSUMER_CONTRACT.md) | 5f614992db2694b00c446924a84b56c1963d81dd | 20477 |
| [Data Deletion Safety Contract](DATA_DELETION_SAFETY_CONTRACT.md) | d265b90ab632dce424854c1f6ce22bd22f904f0e | 25005 |

Review was limited to documentation semantics, authority boundaries, lifecycle states, dependency/ACK/release behavior, archive/deletion gates, and T0–T4 compatibility. No source code, tests, workflow, schema, API, database, VPS, Feeder, registry, scheduler, archive, vacuum, or deletion behavior was inspected or changed.

## 2. Overall assessment

The four documents share the same core safety position:
- system-level shared governance with producer stewardship;
- demand is evaluated per immutable dataset version and purpose;
- ACK is not release or deletion authorization;
- uncertain dependency/hold/policy state blocks destructive progression;
- archive and deletion require separate safeguards;
- T0 canonical writer fencing and paper-only execution boundaries remain intact.

No direct contradiction was found that grants an executable deletion path today. However, two authority/semantics ambiguities and several cross-document gaps should be resolved before implementation or numeric retention decisions.

## 3. Findings

### CC-01 — CONFLICT / MUST RESOLVE: Stale dependency review vs bounded grace

**Observation:** CENTRAL_DATA_LIFECYCLE_POLICY.md §5.2 says stale handling must include bounded grace/review. DATASET_CONSUMER_CONTRACT.md §10 says no grace duration is set and unresolved dependencies remain protective. These can coexist only if bounded review/escalation time never auto-releases or removes protection.

**Recommended resolution:** Define review_due/escalation separately from dependency release. At review deadline, keep dependency protective and escalate; only authenticated owner release or an explicitly approved central adjudication may resolve it. No timeout-based release.

### CC-02 — CONTRACT GAP: Lifecycle state vocabulary is not normalized

**Observation:** Policy uses Registered, Active, Retention review, Archive eligible, Archived, Deletion review, Deletion authorized, Deleted/tombstoned, Hold. Consumer contract has Requested, Active, Release pending, Released, Rejected, Under review. Deletion contract uses Proposed, Eligibility review, Eligible for approval, Approved, Awaiting execution authorization, Execution authorized, Executing, Reconciliation required, Verified complete, Cancelled/rejected/expired. They are different state machines but no shared mapping or statement that they are orthogonal.

**Recommended resolution:** Declare three separate state domains: dataset lifecycle, per-consumer dependency, and deletion request/execution. Define cross-domain guards, not a single merged enum. Map deletion verified-complete to dataset Deleted/tombstoned only after independent reconciliation.

### CC-03 — CONTRACT GAP: Archive and dependency scope

**Observation:** Policy archive eligibility asks whether any dependency requires the online copy/online SLA. Consumer contract dependencies protect an exact dataset version but do not distinguish online-read demand from archive-compatible demand.

**Recommended resolution:** Add dependency access/availability requirement (online, low-latency, restore-acceptable, metadata-only) and prohibit archive only when the registered requirement conflicts with archive service guarantees. Until specified, treat unknown requirement as blocking archive.

### CC-04 — CONFLICT / MUST RESOLVE: T0 maintenance authority vs centralized deletion authority

**Observation:** SHARED_DATA_FOUNDATION.md §7 allows T0 correction/delete through reviewed T0 maintenance authority, while deletion contract requires central eligibility, independent approval, final authorization, and exact-scope executor. Without an explicit precedence rule, T0 maintenance could be misread as a parallel delete path.

**Recommended resolution:** Clarify that T0 maintenance authority covers producer-scoped correction/republication and non-destructive maintenance only. Any destructive removal of a published shared dataset/version must pass central deletion safety contract; T0 writer fencing remains an independent prerequisite, not deletion approval.

### CC-05 — DOC ALIGNMENT: Foundation document says consumer contract is future/out of scope

**Observation:** SHARED_DATA_FOUNDATION.md §§1, 8, 13, 15 still describe consumer ACK/dependency details as out of scope/future and list heartbeat/expiry as unresolved, although the dedicated consumer contract now exists.

**Recommended resolution:** Update foundation references to mark the dedicated contract as the normative detailed contract; replace ambiguous heartbeat/expiry language with review-only signals and no automatic release. Keep schema/API/runtime explicitly out of scope.

### CC-06 — DOC ALIGNMENT: Policy still calls deletion contract a future document

**Observation:** CENTRAL_DATA_LIFECYCLE_POLICY.md §§9 and 16 describe deletion safety contract as future work, but it now exists.

**Recommended resolution:** Update references/status to identify DATA_DELETION_SAFETY_CONTRACT.md as the separate normative execution-safety design, while retaining explicit no-implementation/no-authorization status.

### CC-07 — CONTRACT GAP: Approval vs authorization and actor separation

**Observation:** Policy says central lifecycle authority authorizes scoped operations; deletion contract splits lifecycle reviewer, independent approver, execution authority, and storage executor. The relationship between central authority and these distinct actors is not yet formalized.

**Recommended resolution:** Define central lifecycle authority as governance function, not one unrestricted principal. Require distinct permission scopes and prohibit requester=approver; execution authority issues narrow token only after independent approval and fresh rechecks.

### CC-08 — CONTRACT GAP: Raw-data demand model lacks an inventory/evidence baseline

**Observation:** Shared foundation and policy rely on demand, reproducibility, lineage, recovery and research obligations, but the four contracts do not define a verified inventory of actual datasets/consumers or evidence quality needed before numeric retention decisions.

**Recommended resolution:** Before any retention values or implementation, create a read-only dataset/consumer inventory and evidence matrix (dataset/version/class/steward/consumers/lineage/rebuildability/holds/storage copies). Unknown classification or ownership remains protected.

### CC-09 — CONTRACT GAP: Backup/replica scope is not yet fully governed

**Observation:** Deletion contract explicitly excludes implicit cascading and requires per-copy disposition; policy mentions restore requirements, but no separate backup/replica lifecycle contract or authoritative inventory exists.

**Recommended resolution:** Keep backup expiry and replica deletion out of scope. Design a separate copy/backup lifecycle contract and inventory before any such operation.

### CC-10 — OPEN DECISION: Canonical T0 deletion default

**Observation:** Deletion contract asks whether canonical T0 data is non-deletable by default or has narrow exceptions. Policy protects T0 canonical data but does not decide an absolute prohibition or exception path.

**Recommended resolution:** No deletion eligibility for T0 canonical data until an explicit policy decision and legal/operational evidence are approved. Do not infer permission from generic deletion workflow.

## 4. Normalized conceptual model recommended

Do not merge all statuses into one lifecycle enum. Maintain three logically separate state domains:

1. **Dataset lifecycle state** — registered, active, retention review, archive eligible, archived, deletion review, deletion authorized, deleted/tombstoned, with holds as orthogonal restrictions.
2. **Consumer dependency state** — requested, active, release pending, released, rejected, under review.
3. **Deletion request/execution state** — proposed, eligibility review, eligible for approval, approved, awaiting execution authorization, execution authorized, executing, reconciliation required, verified complete, cancelled/rejected/expired.

Cross-domain safety rules:
- A dependency can be Released while dataset lifecycle remains Active because other demands/holds exist.
- Archive eligibility requires that every active dependency's availability requirement is compatible with archive service guarantees.
- Deletion review is possible only after all demand and hold evidence is reconciled; it is not authorization.
- Dataset state becomes Deleted/tombstoned only after the exact authorized operation is independently verified and reconciled.
- Review deadlines trigger review/escalation only. They never release dependencies or trigger archive/deletion.
- T0 writer fencing protects canonical writes; it does not replace central deletion approval.

## 5. Required documentation corrections

Before implementation, align the documents as follows:

1. Update Shared Data Foundation to reference the dedicated Consumer Contract and Deletion Safety Contract as the detailed normative designs; remove stale wording that presents them as future documents.
2. Clarify T0's correction/maintenance authority so destructive removal of a published shared dataset cannot bypass central deletion governance.
3. Clarify that stale-consumer review/grace is an escalation mechanism only, never an auto-release timer.
4. Add dependency availability requirements relevant to archive (online/latency/restore-compatible).
5. Update Central Data Lifecycle Policy to reference the existing deletion safety contract.
6. Normalize state domains and their transition guards without creating an implementation schema.
7. Keep numeric retention, grace, evidence-freshness, restore objectives, and approval quorum unresolved until evidence and separate approval exist.

These are documentation-only corrections. They do not approve a registry, API, schema, scheduler, retention timer, archive, vacuum, or deletion executor.

## 6. Required evidence before retention policy can be quantified

A read-only inventory is needed before assigning numeric retention values:
- dataset ID/version and functional/sensitivity class;
- actual producer/steward and deployed storage locations;
- known consumers and exact purposes;
- source/derived lineage and reproducibility evidence;
- backtest/model/replay/audit/recovery obligations;
- holds and policy obligations;
- replicas, backups, exports, caches, and local copies;
- rebuild/restore evidence and limitations.

Unknown owner, classification, dependency, or copy inventory must be treated as unresolved/protected. Do not infer “unused” from no reads or missing heartbeat.

## 7. Decisions still requiring explicit approval

- Whether T0 canonical market data is absolutely non-deletable or has narrowly scoped exceptions.
- Which data classes may be archived and under what restore guarantees.
- Whether any dataset classes may ever be deleted and the legal/policy basis.
- Independent approver model and separation of duties.
- Review/escalation cadence (separate from dependency release).
- Evidence freshness rules and authoritative consistency guarantees.
- Backup/replica/export lifecycle and restore-chain requirements.
- Numeric retention floors, grace periods, and tombstone/audit retention.

No values or defaults are selected by this review.

## 8. Acceptance and status

- [x] Four design documents reviewed.
- [x] Core invariants compared across documents.
- [x] Authority and state-model ambiguities identified.
- [x] Required documentation corrections listed.
- [x] Evidence prerequisites and unresolved approvals recorded.
- [x] No implementation or real-data operation authorized.

**Status: REVIEW COMPLETE — CORRECTIONS RECOMMENDED — NOT IMPLEMENTED / NOT ACTIVE.**

Next: apply the documentation-only corrections in §5 on the existing branch, then repeat read-back and cross-contract review. Do not proceed to source/schema/API/runtime work, retention values, archive, vacuum, or deletion without separate approval.
