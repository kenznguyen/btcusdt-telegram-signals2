# T0 RET-03 / RET-07 Retention-Floor Input Gap Analysis

Date: 2026-11-10
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/t0-centralized-data-feeder-p1-20261101
Work type: documentation-only source reconciliation and owner-input gap analysis
Baseline HEAD before this document: 9c93e0c4f5ab211df660feb6a538cc27bf6b83da
Status: **DOCUMENTARY ANALYSIS COMPLETE — RET-03 / RET-07 OPEN — NO NUMERIC FLOOR OR EXPIRY RULE APPROVED**

## 1. Purpose and boundaries

This record performs Stage A from the Lifecycle Residual Dependency and Acceptance Plan. It identifies the class boundaries and the missing owner/legal/operational inputs needed before RET-03 (numeric minimum retention floors) or RET-07 (tombstone/audit/evidence retention) can be decided.

This is a documentary interpretation of repository records only. It does not inspect runtime datasets, consumers, copies, databases, backups, providers, external recipients, personnel, permissions or legal sources. It does not make a legal determination, infer an obligation, select a retention period, or authorize inventory or implementation.

Controlling boundaries remain:
- RET-01 B / RET-02 B as ratified by P1.8.143.
- Option C — No Destructive Authority.
- T0 canonical data and its availability/recovery copies remain protected.
- CORE_LEDGER, AI_LEDGER and required T3 reconstruction/audit records remain protected and separate.
- Unknown, unclassified, orphaned or incompletely inventoried data remains BLOCKED_UNKNOWN / protected.
- Lifecycle independent-human-review waiver applies only to the reviewer gate. It does not waive substantive evidence, technical, authority, inventory, or fail-closed requirements. Owner assessment is not independent assurance.
- No archive, expiry, cleanup, compaction, vacuum, backup/replica removal, export mutation or deletion is authorized.

## 2. Source baseline inspected

| Source | Blob SHA | Relevance |
|---|---|---|
| P1.8.80 Retention and Eligibility Policy | a38710c9d01e5409ce989cc73f791c94bc73773f | Initial T0–T4/evidence/copy taxonomy and unresolved RET-03/RET-07 |
| P1.8.141 Holistic Lifecycle Design Closure Assessment | c20616d79f6dcedde08128f589a5c0e04d6257f1 | LDA-01 and lifecycle residual baseline |
| P1.8.142 Owner Retention and Data-Class Disposition Decision Package | a8b6027c5ff25192ebba82dadc52c70dd1983c82 | Proposed class posture, no-delete-after-read, no numeric assumptions |
| P1.8.143 Owner Retention Policy Ratification | 6f4451f1eb193e763970581bcd6d8a782508acfd | Ratified RET-01 B and RET-02 B |
| P1.8.144 Retention Floor Evidence Contract | f3002ba709f874936ca434c883ef855d2f11784a | Obligation evidence and candidate-floor rule |
| P1.8.145 Static Review of P1.8.144 | 59c6bef4ef971a8376d3383d6689ba0ed47c4891 | Initial contract gaps |
| P1.8.146 Obligation Completeness / Typed End-State / Copy-Graph Clarification | 5efb0ae86d88ede5627ed7b77322463c39fb737e | Source manifest, terminal states, recurring/indefinite duties and copy graph |
| P1.8.147 Static Review of P1.8.146 | 4bc99b2886fce32efd54fe2294732655fc63253 | IR147-01 status before later waiver |
| P1.8.148 Reviewer Independence / Conflict-Control Clarification | baea1eb363a06ea7e804fe986777b31e9b693513 | Historical reviewer-control contract; reviewer gate later waived by owner |
| P1.8.149 Static Review of P1.8.148 | cce7aa0bf9c7b6048b61ef5c436433e3ac0c01c4 | Historical review finding |
| P1.8.150 Conflicted Contributor / Reviewer Clarification | f23fbcfdc85c82b95271d835a1e452e4a9863db2 | Historical reviewer-control clarification |
| P1.8.151 Static Review of P1.8.150 | 64902f09d0f5576a47da44dbb194a56e18d727c2 | IR149-01 documentary closure only |
| P1.8.152 Lifecycle Residual Reconciliation | e1a4d95af216e94a58fa5528850fcd0c1ff465f8 | Current RET-03/RET-07 residual status |
| Lifecycle dependency/acceptance plan | bfbd3ae5ec49e644632c72a1865745628ef574f3 | Stage A scope and sequencing |
| Lifecycle reviewer-waiver decision | 555951e36f6365012cb5b9e48ba24e455b775d16 | Current reviewer-gate authority |

P1.8.142–P1.8.151 are historical records and are not rewritten by this analysis. P1.8.152 remains unchanged.

## 3. Confirmed class boundary

### 3.1 Classes that may enter a future read-only exact-object/version assessment

Only the following ratified RET-02 B groups may be considered, and only after all exact-object gates are evidenced:

| Class | Existing documentary basis | Missing class-specific retention inputs |
|---|---|---|
| T1 raw exchange observations | P1.8.142 §4; P1.8.143 RET-02 B; P1.8.144 §6.2; P1.8.80 §4 | Authoritative purpose/obligation sources; exact consumer and replay/correction obligations; source-dispute and reproducibility duties; event that closes each duty; applicable legal/contract scope; exact source/copy graph |
| T2 ephemeral inference outputs | P1.8.142 §4; P1.8.143 RET-02 B; P1.8.144 §6.3; P1.8.80 §4 | Evidence distinguishing genuinely non-material ephemeral output from output used in signal/risk/ledger/model evaluation/audit; downstream decision-reconstruction duties; approved end events; model/input/configuration lineage; applicable holds and obligations |
| T4 deterministic caches, read models and materializations | P1.8.142 §4; P1.8.143 RET-02 B; P1.8.144 §6.5; P1.8.80 §4 | Exact rebuild contract and successful rebuild evidence; authoritative source availability; consumer availability/release obligations; transformation/version identity; evidence of no independent evidentiary value, export dependency or recovery role |
| Individually identified noncanonical copies | P1.8.142 §4.2; P1.8.143 RET-02 B; P1.8.144 §6.6; P1.8.146 §§4–5 | Copy-specific owner/custodian and location; source/version lineage; object/edge/chain/restore-set obligations; holds; recovery role; external recipient duties; proof that copy is noncanonical and not protecting T0 |

This is only a permission to consider a future read-only assessment. It is not a retention-period decision, deletion eligibility, approval or execution authority.

### 3.2 Protected and excluded classes

The following are not candidates for ordinary class-wide deletion review under the current ratified baseline:
- T0 canonical BTCUSDT market data, source metadata and canonical lineage.
- T0 availability/recovery copies, including any copy whose purpose is to preserve T0 availability, integrity, lineage or recovery.
- CORE_LEDGER and AI_LEDGER.
- T3 event, signal, decision, fill, funding, reconciliation and audit records while needed for paper-outcome reconstruction.
- Governance approvals, policy versions/history, manifests, dependency/hold records, tombstones and lifecycle evidence while needed to prove authority, lineage, process and outcome.
- Unknown, unclassified, orphaned, or incompletely inventoried data and copies.

No class label, age, redundancy, successful read, consumer ACK, completed job, model completion, provider expiry, storage pressure or theoretical rebuildability changes these boundaries.

## 4. RET-03 — minimum retention floor inputs

### 4.1 What is already specified

P1.8.144 defines an evidence-only candidate floor for an exact object/version/copy as the latest proven end among all applicable minimum-retention obligations. P1.8.146 requires a bounded source manifest, source authority/coverage/accessibility, typed obligation states, recurring/rolling/indefinite treatment, exact end/successor evidence, and complete copy/backup/restore graph semantics.

A finite candidate floor cannot be established if the source manifest is incomplete, any obligation is ACTIVE/INDEFINITE/UNKNOWN, a recurring cycle or successor is unresolved, a hold/dependency remains, copy/restore graph closure is incomplete, or time/order evidence is uncertain. The required outcome is FLOOR_NOT_ESTABLISHED / RETAIN / BLOCKED.

P1.8.144 explicitly says a floor is not a deletion date, deletion eligibility or authorization.

### 4.2 Missing inputs that prevent numeric selection

No reviewed source supplies an approved numeric minimum duration, TTL, or finite terminal duration for any eligible class. For each class and each applicable obligation, the owner still needs a source-backed decision record containing:

1. **Purpose and obligation basis:** the precise operational, research, reproducibility, contractual, legal, audit, security, incident or recovery purpose; the authoritative policy/contract/source; its version and scope. A legal or regulatory basis must be supplied/attributed by a competent authority for the applicable jurisdiction; this analysis does not infer one.
2. **Accountability:** named accountable role/owner and custodian, their authority to attest to the obligation, and the authoritative system/source from which it can be established.
3. **Exact scope:** class, object/version/copy, applicable systems, consumers, recipients and jurisdictions; explicit exclusions and completeness boundary.
4. **Start event:** the event that starts the obligation, its exact semantics, source, timestamp domain, precision and provenance. Creation time or ingestion time must not be assumed to be the correct start.
5. **Terminal event:** a positive, attributable event/decision that closes the obligation, exact affected scope, evidence source and authority. Consumer ACK, job completion, elapsed age or last access is not a terminal event by itself.
6. **Duration rule:** the minimum duration, if any, and the authoritative reason for that value; whether it is a fixed interval, event-relative period, recurring obligation, rolling window or indefinite duty. No numeric value is selected in this record.
7. **Clock and ordering:** event-time / trusted receipt-time / durable commit-time / legal-effective-time semantics; UTC/timezone, precision, uncertainty, ordering and evidence requirements under V07/V08. These dependencies remain unresolved.
8. **Dependencies and holds:** replay, corrections, model/training/evaluation, backtest, signals/risk/ledger reconstruction, consumers, incidents, legal/security/audit holds, recovery and copy/backup/restore-chain interactions.
9. **Copy graph:** source/copy/replica/export/backup/restore-set identities, lineage, completeness, custody and affected-scope calculation; no cascade or shared floor assumption.
10. **Evidence of compliance:** immutable source manifest, obligation register, exact end-event proof, provenance/integrity verification, reconciliation and freshness basis.
11. **Owner disposition:** explicit approval of the class-specific policy semantics and any numeric value, tied to the exact policy version. Recommendations or technical defaults are not owner approval.

### 4.3 Class-specific questions still unanswered

- **T1:** Which authoritative operational/research/replay/source-dispute obligations actually apply to each observation type? What evidence proves that all derived outputs remain reproducible from retained authoritative inputs? What exact event closes correction, dispute, consumer and recovery duties?
- **T2:** Which output types are demonstrably non-material and ephemeral? Which signals, risk decisions, model evaluations, ledger events, investigations or claims consume them? What exact event closes decision-reconstruction and model-provenance obligations?
- **T4:** What authoritative consumer contract defines availability and release? What exact versioned rebuild test and source-availability proof is accepted? What event closes each consumer/export/recovery dependency?
- **Noncanonical copies:** What is the exact copy identity and purpose? Which obligations are object-local, edge-level, chain-level, restore-set-level, shared-resource or scope-wide? Who can attest to closure and what proves the complete affected set?

Until those answers are supported, RET-03 remains OPEN and no numeric floor can be calculated.

## 5. RET-07 — tombstone, audit and evidence retention inputs

### 5.1 Evidence groups must remain distinct

The source documents identify several evidence groups, but do not establish a finite expiry policy for them. Future documentary decisions must not collapse them into one generic “audit log” class:

| Evidence group | Why it exists / protected function | Missing end/retention inputs |
|---|---|---|
| Policy versions and owner approvals | Prove which policy and authority applied to a decision | Policy supersession semantics; claims/decisions still relying on each version; competent end authority |
| Assessment and eligibility manifests | Bind exact class/object/version/copy, scope, source inventory and evidence used | Whether later assessments supersede but must preserve prior decision history; closure of all dependent claims |
| Dependency and hold records | Prove consumer release, hold scope/revision and release authority | Authoritative release event, successor/recurrence rules, stale/unknown reconciliation and clock basis |
| Tombstones and lifecycle state transitions | Preserve identity, prior state, requested/approved scope and transition/reconciliation history | Required fields and evidence purpose; terminality and correction semantics; successor links; authority for any future expiry |
| Audit, security and incident evidence | Prove access, decisions, exceptions, investigations and response | Applicable authority/source, incident/audit closure, appeal/reopen window if any, legal/contract scope and release authority |
| Copy lineage, backup and restore evidence | Prove copy graph, recovery chain, restore point and reconstruction | Complete chain/restore-set closure, measured recovery obligations, successor proof and trusted-time semantics |
| Verification and acceptance artifacts | Support technical, security, policy and lifecycle claims | Which claims depend on each artifact; historical re-verification needs; evidence-store authority and integrity requirements |
| External recipient/export evidence | Prove transfer, custody, recipient and onward-copy disposition | Recipient/source-of-truth inventory, onward-copy completeness, competent attestation and exact closure proof |

These groups are not all necessarily subject to the same obligation or retention basis. No shared TTL or automatic expiry rule is justified by the inspected documents.

### 5.2 Missing inputs for any finite evidence-retention rule

For each evidence group and exact record/version, the owner needs:
- the claim, decision, process or obligation the record proves;
- the authoritative policy/contract/legal/security/operational source and applicable scope;
- accountable evidence owner/custodian and competent release authority;
- the start event and exact terminal event (including whether obligations recur, reopen or are indefinite);
- any minimum period and its source-backed rationale, if a finite period is appropriate;
- clock domain, trusted-time/ordering semantics and uncertainty;
- links to decisions, objects, copies, holds, incidents, audit findings, restores and claims still relying on the evidence;
- successor/supersession semantics without deleting historical proof of the prior decision;
- completeness and integrity evidence for the relevant record set;
- explicit owner approval of the resulting class-specific rule.

The lifecycle reviewer waiver does not supply any of these missing inputs and does not authorize the evidence to expire. The reviewer-dependent portion of LDA-09/IR147-01 was waived only as a human reviewer gate; substantive documentary alignment and all technical/evidence criteria remain.

### 5.3 Fail-closed treatment

Until a competent, source-backed end condition and exact-scope owner rule exist:
- preserve the evidence and its lineage;
- treat an unresolved, recurring or indefinite obligation as non-terminal;
- do not infer expiry from the age of a record, supersession of a policy, completion of a job, provider artifact expiry or the closure of one incident;
- do not infer that a tombstone can expire merely because the associated payload is no longer used;
- do not cascade payload disposition into tombstone, approval, manifest, audit or verification evidence;
- return OPEN / RETAIN / BLOCKED where source coverage, clock, successor, authority or dependency is unknown.

No numeric RET-07 expiry value or finite retention rule is approved by this analysis.

## 6. Decision and evidence gap register

| Gap | Required owner/source input | Current status |
|---|---|---|
| No approved numeric floor by eligible class | Class-specific purpose, authoritative obligation basis, start/end event, duration rationale and owner approval | OPEN |
| Legal/contractual scope absent from inspected repository evidence | Competent authority's scoped determination and source/version; no legal inference by system | NOT PROVIDED / NOT VERIFIED |
| Operational obligations not evidenced per object | Authoritative consumer/replay/research/recovery contracts and accountable owners | NOT VERIFIED |
| Trusted time/order not ready | V07/V08 source/provider semantics and proof | BLOCKED / OPEN |
| Copy/restore graph incomplete | Separately authorized inventory and complete source/copy/backup/restore evidence | NOT VERIFIED; inventory not authorized here |
| RET-07 terminal semantics absent | Per-evidence-group purpose, terminal/reopen/successor rules, authority and evidence | OPEN |
| Evidence-store/custody policy absent | Owner-approved evidence authority, integrity, availability and custody requirements | OPEN |
| Reviewer gate waived | Owner waiver controls reviewer gate only | OWNER-WAIVED; substantive criteria remain OPEN |

## 7. Stage A conclusion

**RET-03: OPEN — no numeric minimum retention floor or TTL selected.**

**RET-07: OPEN — no tombstone/audit/evidence expiry value or finite deletion rule selected.**

The source set provides a conservative class taxonomy, read-only review boundary, evidence-only floor method, typed obligation states and copy-graph semantics. It does not provide the class-specific obligation sources, numeric duration bases, exact start/end events, trusted-time evidence, complete operational inventories or evidence-retention terminal rules needed to calculate or approve a floor.

The next safe action is to obtain owner-supplied documentary inputs for the identified questions, one class/evidence group at a time. If an authoritative source or competent determination is absent, record the gap and stop. No legal rule, numeric value, or class eligibility may be inferred.

## 8. Verification and authorization record

- Source branch HEAD before this document: 9c93e0c4f5ab211df660feb6a538cc27bf6b83da.
- Source records: exact blob SHAs listed in §2.
- Work performed: GitHub repository document retrieval and static documentary comparison only.
- Tests: **NOT RUN**.
- GitHub Actions: **NOT DISPATCHED**; no workflow run or artifact.
- Runtime/VPS/database/storage/provider/consumer/copy/restore inventory: **NOT PERFORMED**.
- Legal/contractual research or determination: **NOT PERFORMED**.
- Permissions, credentials, workflow, source, schema, API, adapter, runtime or data: **UNCHANGED**.
- Staging, restore, fault injection, provider/key/TSA operations: **NOT AUTHORIZED / NOT PERFORMED**.
- Archive, cleanup, expiry, compaction, vacuum, backup/replica removal, export mutation and deletion: **NOT AUTHORIZED / NOT EXECUTED**.
- AI_EXECUTION_ENABLED=false; paper-only; no live orders.
- Option C remains in force; T0 remains independent; CORE_LEDGER and AI_LEDGER remain separate.

**Final status: STAGE A DOCUMENTARY CLARIFICATION COMPLETE — RET-03 / RET-07 OPEN — NO NUMERIC FLOOR OR EXPIRY RULE APPROVED — NO IMPLEMENTATION OR DESTRUCTIVE AUTHORITY.**
