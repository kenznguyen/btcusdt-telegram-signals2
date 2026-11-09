# T0 Lifecycle Residual Dependency and Acceptance Plan

Date: 2026-11-10
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Type: documentation-only dependency analysis; no implementation authorization

## 1. Controlling decisions and source baseline

- Lifecycle owner decision: `docs/decisions/D-2026-11-10-LIFECYCLE-INDEPENDENT-REVIEW-WAIVER.md`, blob `555951e36f6365012cb5b9e48ba24e455b775d16`.
- L4-Minimum acceptance matrix: `docs/evidence/p1-8/L4-MINIMUM-PROVENANCE-ACCEPTANCE-MATRIX.md`, blob `2ba85af550fb7e369ea39ade6d73878d78dbf6bc`.
- P1.8.152 lifecycle reconciliation: `docs/evidence/p1-8/P1.8.152-retention-and-lifecycle-residual-finding-reconciliation.md`, blob `e1a4d95af216e94a58fa5528850fcd0c1ff465f8`.
- F-01–F-09 / P1.8.152–153 crosswalk, including prospective waiver addendum: `docs/evidence/T0_L4_F01_F09_P1_8_152_153_RECONCILIATION_2026-11-10.md`, updated blob `3d084c04cd9712ed05d790ce5c431e988b64ce32`.

The lifecycle independent-human-review requirement is OWNER-WAIVED / NOT MANDATORY. P1.8.153 is OWNER-WAIVED / NOT REQUIRED, NOT EXECUTED, and not PASS. An owner assessment may be recorded, but is not independent assurance. Technical/environmental separation of verification remains required where specified.

## 2. Current residual status — no promotion

| Item | Current status | Acceptance gap |
|---|---|---|
| RET-03 numeric minimum retention floors | OPEN | No approved class-specific numeric floors, TTLs or end-duration rules |
| RET-04 archive | NON-EXECUTABLE | Option C prohibits archive/irreversible transition |
| RET-05 approval/authority separation | Owner policy approved; technical enforcement NOT VERIFIED | No verified enforcement at mutation boundary |
| RET-06 grace/cancellation/authorization lifetime/freshness | OPEN | No approved values; trusted-time and mutation-boundary dependencies unresolved |
| RET-07 tombstone/audit/evidence retention | OPEN | No approved expiry values or class-specific disposition rules |
| RET-08 emergency/legal requests | OPEN | No qualified authority/decision protocol or approved exception; no break-glass path |
| RET-09 consumer/copy/restore inventory | NOT VERIFIED | No complete runtime/provider/backup/replica/export/cache/recipient inventory |
| RET-10 adapter and verifier | OPEN / NOT VERIFIED | No adapter qualification or demonstrated technically separate verifier |
| V07 trusted-time/revocation | BLOCKED | Trust profile, protocol, revocation/freshness semantics and provider evidence absent |
| V08 durable checkpoint/seal ordering | OPEN / BLOCKED | Durable ordering token, watermark/lateness and replay/correction proof absent |
| Restore/recovery | OPEN / BLOCKED | HWM completeness, provider/database semantics, independent oracle and measured failure-domain evidence absent |
| LDA-05 mutation fencing | NOT VERIFIED | No qualified adapter proving atomic/ordered policy/hold/authorization revision binding |
| LDA-06 consumer/copy inventory | NOT VERIFIED | Actual consumers and all copy classes un-inventoried |
| LDA-07 negative vectors | NOT RUN | 87 specified vectors have not been executed |
| LDA-08 Option C technical enforcement | HOLD / NOT VERIFIED | Effective GitHub/workflow/runner/credential/OIDC/provider permissions unverified; inventory paused |
| F-07–F-09 lineage | NOT VERIFIED | Authoritative originating records and closure criteria not identified |

These statuses are inherited from P1.8.152 and the current reconciliation. This plan does not close, pass, or reclassify them.

## 3. Dependency order

The sequence below is a planning dependency, not authorization to perform the work.

### Stage A — Documentary class and policy inputs

1. **RET-03 / RET-07:** enumerate only already-authorized data classes and state the retention question for each class. For each proposed floor, require a documented purpose, source of obligation, minimum duration, start/end event, clock basis, hold interaction, dependencies, evidence needed to prove compliance, and owner approval. Do not invent numeric values where the owner has not supplied the legal/operational basis.
2. **RET-06:** specify grace, cancellation, authorization lifetime and evidence freshness only after the class/floor semantics and trusted-time model are explicit.
3. **RET-08:** define an authority/evidence decision protocol on paper only. No legal/security exception, break-glass route or destructive request is pre-approved.
4. Keep RET-04 non-executable. Any archive proposal remains a policy description only and cannot override Option C.

### Stage B — Technical contracts before implementation

5. **V07 / RET-10:** define trust profile, timestamp semantics, revocation/freshness behavior, failure behavior and the technically separate verifier contract. Provider selection/contact, key enrollment and trust-root changes are out of scope.
6. **V08:** define the durable checkpoint/seal ordering token, partition progress, watermark/lateness, uncertainty and correction/replay semantics. Do not assert durable ordering without a concrete storage contract.
7. **RET-05 / LDA-05:** specify the mutation-fence state machine and adapter contract. The required invariant is that policy revision, object identity/version, dependency/hold state, authorization and trusted-time revision are bound atomically or provably ordered with any side effect. No side effect is authorized by this plan.
8. **Restore:** specify the restore oracle, high-water-mark completeness, failure-domain assumptions, evidence chain and proposed RPO/RTO measurement method. RPO/RTO remain planning targets, not measured SLOs.

### Stage C — Inventory and enforcement evidence (separate authorization required)

9. **RET-09 / LDA-06:** only after explicit bounded authorization, inventory consumers, dependencies, canonical and noncanonical copies, backups, replicas, exports, caches, derived artifacts, recipients and provider-side copies. Until then, inventory completeness is NOT VERIFIED and no “all copies known” claim is allowed.
10. **LDA-08:** effective GitHub/workflow/runner/credential/OIDC/provider permissions remain paused. Requires a separate owner-approved read-only scope and least-privilege evidence. No permission changes or secret access.
11. **LDA-07:** the 87 negative vectors require a deterministic isolated runner, test fixture/object set, independent oracle, concurrency model, expected fail-closed outcomes and artifact provenance. Execution requires separate approval. No production data or live lifecycle operations.

### Stage D — Owner assessment and disposition

12. Freeze exact source versions and evidence artifacts into an immutable baseline manifest with object digests and provenance.
13. Record an **OWNER ASSESSMENT** per criterion: PASS only with evidence; otherwise OPEN / BLOCKED / NOT VERIFIED / NOT RUN. Explicitly distinguish policy approval, technical design, test evidence, operational evidence and execution authority.
14. Owner disposition references the exact baseline ID/digest. Do not claim independent review, third-party assurance, certification or reviewer-confirmed closure.

## 4. Acceptance rules

- A waived reviewer gate is not a PASS for the underlying requirement.
- No unknown, unclassified, orphaned or incompletely inventoried object can become eligible for class-wide disposition.
- No retention floor is accepted without a class-specific basis, event semantics, clock basis, dependency/hold treatment and owner approval.
- No technical enforcement claim without a mutation-boundary test and evidence tied to the exact adapter/backend version.
- No restore claim without a measured rehearsal and independent oracle; planning targets are not measured capability.
- No completeness claim for consumers/copies without bounded inventory evidence and reconciliation.
- No negative-test PASS without all applicable vectors executed with deterministic expected outcomes and retained artifacts.
- Option C remains controlling. No archive, cleanup, expiry, compaction, vacuum, backup/replica removal, export mutation, deletion or irreversible transition is authorized.
- T0 canonical data, availability/recovery copies, CORE_LEDGER, AI_LEDGER, required T3 reconstruction/audit records, governance history/evidence and unknown/unclassified/orphaned/incompletely inventoried data remain excluded from ordinary class-wide deletion review.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.

## 5. Immediate next bounded task

The next safe task is **Stage A documentary clarification**, beginning with RET-03 and RET-07 class-specific floor-input requirements. It must identify missing owner inputs and evidence definitions without selecting arbitrary numeric retention values. If the existing source documents do not define a class taxonomy or obligation basis sufficiently, record that as a blocking input and stop; do not infer classes or legal requirements.

## 6. Execution and verification boundary

- This plan is documentation-only.
- Tests: NOT RUN.
- GitHub Actions: NOT DISPATCHED; no run/artifact.
- Runtime/VPS/database/storage/provider/permission/consumer/copy inventory: NOT PERFORMED.
- Staging, restore, fault injection and provider/key/TSA operations: NOT AUTHORIZED / NOT PERFORMED.
- Archive, cleanup, expiry, compaction, vacuum, backup/replica removal, export mutation and deletion: NOT AUTHORIZED / NOT EXECUTED.
- No source, schema, API, adapter, scheduler, workflow, secret, key, permission or data changes.
- Option C unchanged; T0 remains independent; ledgers remain separate.

**Plan status: DOCUMENTARY DEPENDENCY MAP COMPLETE — IMPLEMENTATION NOT AUTHORIZED — ALL SUBSTANTIVE RESIDUAL STATUSES PRESERVED.**
