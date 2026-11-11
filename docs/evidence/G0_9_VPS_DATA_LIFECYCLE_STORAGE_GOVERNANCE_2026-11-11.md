# G0.9 — VPS Data Lifecycle and Storage Governance Design

Date: 2026-11-11  
Status: **DOCUMENTARY DESIGN — CONDITIONAL PASS; NOT IMPLEMENTED / NOT ACTIVE**

## 1. Scope and authority

This increment translates the already-ratified central lifecycle policy into a VPS storage-governance design for the planned single-host T0/T1/T2/FreqAI workload. It does not replace or weaken:

- `docs/architecture/CENTRAL_DATA_LIFECYCLE_POLICY.md`;
- `docs/architecture/DATASET_CONSUMER_CONTRACT.md`;
- `docs/architecture/DATA_DELETION_SAFETY_CONTRACT.md`;
- `docs/evidence/p1-8/P1.8.80-retention-and-eligibility-policy.md`;
- `docs/evidence/p1-8/P1.8.143-owner-retention-policy-ratification.md`;
- the 2026-11-11 handoff governance override.

The Option C blanket prohibition was revoked by the owner on 2026-11-11. That revocation is not an operation-specific authorization. Every concrete destructive operation still requires a separate explicit, bounded approval with exact target/data class, scope, preconditions, expected effect, dependency/hold checks, verification and recovery/rollback plan.

This is a design-only increment. The old Scaleway VPS was deleted on 2026-11-11; no replacement VPS exists in the current handoff. Consequently, no live file, process, database, volume, copy, consumer or storage usage was inventoried.

Paper-only remains mandatory. `AI_EXECUTION_ENABLED=false`. T0 remains an independent canonical data asset. No live trading or real orders.

## 2. Existing policy decisions that control this design

The owner-ratified RET-01 B and RET-02 B decisions remain controlling:

- T0 canonical data is protected by default; no routine or scheduled deletion path. A narrowly scoped binding legal/security exception requires competent review and a new explicit owner decision.
- Only four noncanonical groups may enter future read-only, exact-object/version eligibility assessment: (1) T4 deterministic caches/read models/materializations after rebuildability and dependency closure; (2) T2 ephemeral inference outputs after proving they did not underpin material decisions/claims/evidence; (3) T1 raw observations only after exact dependent outputs are reproducible from retained authoritative inputs and all obligations close; (4) individually identified noncanonical copies after copy-specific checks.
- Eligibility review is not deletion authorization. No class or object is currently authorized for deletion.
- CORE_LEDGER, AI_LEDGER, T3 reconstruction/reconciliation/audit evidence, governance approvals/history/tombstones, unknown/unclassified/orphaned/incompletely inventoried data remain outside ordinary class-wide deletion review.
- RET-03 through RET-10 remain open or not verified as recorded in P1.8.142/P1.8.143. No numeric retention floor, TTL, grace period, review cadence, authorization lifetime or evidence-freshness window is inferred here.

The earlier conversational suggestions of 24-hour cache, 7-day scratch, 14–30-day logs, or an 80% cleanup threshold are **not approved policy values** and are not adopted by this design.

## 3. VPS storage-domain mapping

The G0.8-C planning envelope remains 500 GB split across separate volumes: 80 GB OS/apps/logs, 20 GB T0 canonical, 300 GB T1 raw capture, and 100 GB T2 model artifacts/staging/scratch. This is a capacity plan only, not a provisioned layout or permission to dispose of data.

| Planned domain | Candidate contents | Lifecycle disposition at G0.9 | Key boundary |
|---|---|---|---|
| T0 volume (20 GB) | Canonical M15/H1 candles, source metadata, lease/fencing and recovery state | **PROTECTED** | No cleanup, rotation, compaction, vacuum, expiry or delete path in this scope |
| T1 raw volume (300 GB) | Raw trades, order book, funding, OI, liquidations and other exchange observations | **RETAIN_UNTIL_OBLIGATIONS_CLOSE / BLOCKED_UNKNOWN** | Producer provenance mismatch, incomplete importer contract and unknown BTCUSDT growth prevent deletion review |
| T2 model/data volume (100 GB) | Feature/label datasets, training inputs, model artifacts, inference outputs, staging and scratch | Mixed: model/training lineage protected; only specifically classified ephemeral inference output may enter future review | A directory name such as scratch/cache is not proof of rebuildability or disposability |
| OS/apps/logs volume (80 GB) | Packages, application state, runtime logs, temporary files, crash dumps and operational evidence | **BLOCKED_UNKNOWN until file-level classification** | Logs may contain incident, security, audit or reconstruction evidence; no blanket log rotation/deletion rule |
| Backups/exports/copies | Snapshots, archives, local exports and copies | **COPY_SPECIFIC_REVIEW only** | Separate identity and dependency/hold/recovery-chain checks; no cascade |
| Unknown paths | Unregistered files, orphaned directories, unclassified artifacts | **BLOCKED_UNKNOWN / PROTECTED** | Never default to ephemeral |

This table maps planned storage domains, not actual runtime objects. The actual VPS filesystem and mount points do not exist for inspection.

## 4. Proposed non-destructive lifecycle workflow

The implementation-independent workflow is:

1. **Inventory:** enumerate exact object/path identity, owning layer, data class, steward, source/version, size, timestamps, digest availability, mount/domain, and known copies. Inventory itself must be read-only and separately approved for a future host.
2. **Classify:** map each object to the ratified functional class and policy version. Missing or conflicting metadata becomes `BLOCKED_UNKNOWN`.
3. **Register dependencies and obligations:** capture exact consumers, runs/models/experiments, replay/recovery, audit/incident/security/legal holds and copy-chain relationships. Missing registry evidence is protective, not evidence of no demand.
4. **Verify rebuildability where relevant:** demonstrate exact retained inputs, code/configuration, transformation/model version, schema and integrity equivalence. Assertion or successful read is insufficient.
5. **Evaluate:** emit a read-only disposition such as `PROTECTED`, `RETAIN_UNTIL_REVIEW`, `REVIEWABLE_NONCANONICAL`, `COPY_SPECIFIC_REVIEW` or `BLOCKED_UNKNOWN`. Do not collapse dependency state, eligibility and authorization into one state.
6. **Dry-run report:** list exact candidates, reasons, policy version, blockers, estimated bytes that might be affected, and the evidence supporting each conclusion. Dry-run must not rename, move, truncate, compress, chmod, unlink, expire, vacuum or otherwise mutate payload or metadata.
7. **Separate approval:** any actual operation must be proposed and approved independently for exact objects, with a bounded execution window, expected effect, rollback/recovery, and independent verification.
8. **Post-operation reconciliation:** only after a separately approved operation, reconcile exact object outcomes and preserve required manifests, audit events and tombstones independently of payload.

A read, download, successful job, consumer ACK, model training completion, elapsed time, heartbeat loss, storage pressure or missing recent access is never a deletion trigger.

## 5. Fail-closed controls required before any future implementation

- Immutable object/version manifest with stable identity, source lineage, policy version, content digest and size; secrets and credentials must never enter manifests.
- Exact-path allowlist and explicit denylist for protected domains. Unknown paths are denied by default.
- Consumer/reference inventory must be authoritative and consistent; unavailable, stale, contradictory or incomplete registry state blocks review.
- Holds and source/copy lineage must be checked independently. No implicit source-to-copy or copy-to-derived cascade.
- Candidate must be closed to active writers/processes and have no unresolved file handles, locks, jobs or mount ownership. Process absence alone does not prove no dependency.
- Quarantine, if later designed, is a separate data-moving operation and is not automatically authorized by this report. No quarantine duration is set.
- Audit and tombstone storage must be independent of the payload being assessed; audit write failure blocks progression.
- Dry-run output must be deterministic, idempotent, reviewable and incapable of invoking a storage mutation API.
- Any mismatch in hash, size, manifest, ownership, policy version, path resolution, dependency state or postcondition must fail closed.
- No routine SQLite `VACUUM`, WAL truncation, volume resize, snapshot expiry or provider lifecycle operation is included. Each requires separate technical assessment and bounded approval.
- Monitoring should report per-volume bytes, inode usage, growth rate, I/O wait and free-space trends. Alert thresholds may be proposed separately; storage-pressure alerts must never invoke deletion or weaken protected-data rules.

## 6. Current blockers and evidence-based disposition

| Item | Finding | Status |
|---|---|---|
| T0 canonical data | Protected by RET-01 B and handoff invariants | **PROTECTED** |
| T1 raw data | Importer marks streams incomplete/unverifiable; producer SHA mismatch; BTCUSDT-only runtime capture and measured growth absent | **BLOCKED — no deletion review** |
| T2 training scratch | No authoritative runtime inventory, exact artifact contract or proven rebuildability | **NOT VERIFIED — no cleanup rule** |
| T2 ephemeral inference | No runtime object inventory or proof of non-use in material decisions/claims | **NOT VERIFIED — no eligibility claim** |
| T4 caches/read models | No verified runtime inventory or deterministic rebuild proof in current host | **NOT VERIFIED — no eligibility claim** |
| Runtime logs | No log taxonomy, evidence classification or owner-approved retention floor | **BLOCKED_UNKNOWN** |
| Backups/copies | No replacement-host inventory or copy-chain/restore proof | **NOT VERIFIED** |
| Disk-growth assumptions | 0.5–2.0 GB/day T1 is a planning estimate only, not a measurement | **NOT VERIFIED** |
| Cleanup/quarantine implementation | No implementation or test evidence in this increment | **NOT IMPLEMENTED** |
| Replacement VPS | None exists | **NOT VERIFIED / NOT PROVISIONED** |

## 7. Dry-run acceptance matrix for a future separately approved test

These are required test cases for a future non-production, synthetic-only implementation. They were **not executed** in G0.9.

| Case | Synthetic condition | Required expected result |
|---|---|---|
| DRY-01 | Fully identified synthetic disposable fixture with complete manifest and no dependencies | Candidate may be reported; payload unchanged |
| DRY-02 | T0 canonical path or protected ledger/evidence class | Excluded; explicit protected reason |
| DRY-03 | Unknown/unclassified path or missing steward | `BLOCKED_UNKNOWN`; no candidate |
| DRY-04 | Missing/stale/contradictory consumer registry | Blocked; preserve protective state |
| DRY-05 | Active dependency, hold, incident or recovery obligation | Protected; no candidate |
| DRY-06 | Hash/size/manifest mismatch | Integrity failure; blocked |
| DRY-07 | Open writer/process/lock or active training job | Blocked; no candidate |
| DRY-08 | Source/copy lineage incomplete or backup chain unresolved | Blocked; no cascade |
| DRY-09 | Dry-run output destination unavailable or audit write fails | Fail closed; no mutation |
| DRY-10 | Repeat identical dry-run | Same candidate set and deterministic reasons; source payload unchanged |
| DRY-11 | Attempt to pass a dry-run result directly to an executor | Rejected; no implicit authorization path |
| DRY-12 | Storage pressure crosses a configured alert boundary | Alert/report only; no deletion or policy bypass |

A future test must prove source immutability before/after using synthetic disposable fixtures and hashes. It must not mount, open, copy or mutate T0 canonical production data or any real VPS data.

## 8. G0.9 verdict

- Alignment with existing central lifecycle policy and owner-ratified RET-01/RET-02: **PASS — documentary mapping**.
- Planned VPS storage-domain classification: **CONDITIONAL PASS — static plan only**.
- T0 protection: **PASS — policy boundary preserved**.
- T1 deletion eligibility: **BLOCKED**.
- T2/T4 disposable-object eligibility: **NOT VERIFIED**.
- Runtime inventory, dependency/copy completeness and rebuildability: **NOT VERIFIED**.
- Numeric retention/TTL/alert thresholds: **OPEN — none approved here**.
- Dry-run implementation and synthetic tests: **NOT IMPLEMENTED / NOT RUN**.
- GitHub Actions: **NOT DISPATCHED**; no workflow run or artifact.
- VPS provisioning/runtime/cleanup/deletion: **NOT AUTHORIZED / NOT PERFORMED**.

## 9. Non-actions and next step

No source code, schema, API, registry, workflow, scheduler, service, permission, credential, database, storage volume, VPS, market data, model, ledger or runtime was changed. No test, workflow dispatch, inventory read against a live host, archive, quarantine, cleanup, expiry, compaction, vacuum, deletion or provider operation was performed.

Next bounded increment: prepare a **synthetic-only dry-run contract and test implementation plan** on GitHub. Before implementing or dispatching tests, separately confirm the exact synthetic fixture paths, test-only allowlist, proof of no production-data access, and CI workflow scope. No destructive executor is part of that next increment.

T0 remains independent. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.
