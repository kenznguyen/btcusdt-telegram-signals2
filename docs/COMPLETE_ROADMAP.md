# BTCUSDT Quant System — Complete Roadmap

- Updated: 2026-11-11 (Asia/Ho_Chi_Minh)
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Working branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Default branch: `main`
- Document type: consolidated roadmap / read-only status reconciliation
- Scope: T0–T4, cross-cutting G0 assurance, GitHub governance, and future VPS acceptance
- Safety posture: personal research system; paper-only; `AI_EXECUTION_ENABLED=false`

> This document consolidates the roadmap and known evidence. It is not a production-readiness declaration, does not grant operational authority, and does not supersede a more specific Owner decision, contract, or evidence record. Statuses are evidence-bounded and must be refreshed against exact source SHAs and workflow runs before being promoted.

## 1. Owner invariants and governance

1. GitHub is the project source of truth. Continue on the existing working branch; do not create a parallel branch/PR or perform broad branch integration without a task-specific Owner decision.
2. T0 remains an independent canonical data foundation. Consumers use its approved read contract; they do not gain authority to mutate or delete canonical data.
3. Paper-only operation remains mandatory. No live trading, exchange execution, or real orders. Keep `AI_EXECUTION_ENABLED=false`.
4. T1 is NOT ACTIVATED. PostgreSQL/TimescaleDB remains PARKED / NOT CERTIFIED as the canonical backend. SQLite remains the selected T0 canonical backend.
5. No VPS provisioning, deployment, service start/restart, package/credential changes, exchange connection, market-data sync, model training, or runtime probe without the applicable explicit bounded approval.
6. No cleanup, archive, expiry, vacuum, compaction, deletion, or backup lifecycle action is authorized merely by this roadmap. Exact targets and effects require separate approval.
7. GitHub Actions is the preferred CI. Codemagic is fallback-only and requires a concrete GitHub Actions blocker plus explicit approval.
8. Every accepted CI result must record branch, PR head/base SHA, event, exact checked-out SHA, run URL, job conclusions, test counts, and artifact ID/name/digest/expiry. Distinguish PR head from synthetic merge SHA.
9. A CI PASS is not Owner authorization, deployment acceptance, or proof of production behavior.
10. Each G0 executable stage, workflow/permission change, real evidence adapter, provider/runtime operation, and destructive action requires separate exact-scope approval under D14-A.

## 2. Repository baseline and integration risk

- Working branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Default branch: `main`.
- G0.50 recorded baseline HEAD: `2b4e59a59faebb34b0d62a658d08fa95ece68ffa`. This is a historical workstream baseline, not asserted to be the current branch HEAD after subsequent commits.
- The prior repository comparison against `main` reported substantial divergence (3,204 commits ahead / 81 behind at the time queried). Re-run an exact compare before any integration decision.
- Numerous open Draft PRs and Issues exist. A complete PR-by-PR disposition has not yet been produced by this document.
- PR #139 (SSH passphrase preflight) is CLOSED / NOT MERGED per the controlling handoff. Do not reopen or merge without separate approval.
- Issue #138 / P1.42 remains a T1 review blocker (REQUEST CHANGES in the reviewed state).

**Disposition:** integration is BLOCKED pending a read-only branch/PR/commit topology inventory and an Owner-approved integration strategy. Do not rebase, merge, force-push, delete branches, or bulk-close PRs as part of roadmap maintenance.

## 3. Five-layer architecture and status

### T0 — Data Foundation

**Purpose:** canonical Binance USD-M BTCUSDT M15/H1 market-data ingestion, validation, persistence, provenance and bounded read-only delivery.

**Selected architecture**
- Binance USD-M public market data; no exchange API key required for the canonical candle path.
- SQLite is the selected canonical store and default backend.
- Single-writer/lease-fencing and guarded recovery boundary.
- Authenticated bounded read-only Candle API.
- T2 consumes through `CandleHttpClient`; no direct T2 SQLite access or fallback to synthetic/venue data.
- PostgreSQL adapters may exist in source but remain optional/PARKED and are not certified as canonical runtime.

**Evidence-backed progress**
- Read-only Candle Contract v1 and T2 HTTP consumer contract/test work are present.
- Historical bounded T0→T2 loopback observations are recorded, but they are time-bounded and do not establish current runtime freshness or availability.
- G0.6 reconciliation records the former Scaleway VPS as deleted on 2026-11-11 and current T0/T2 deployment parity as NOT VERIFIED.
- T0 scope index identifies the canonical SQLite feeder/API chain and keeps optional PostgreSQL and separate research domains isolated.

**Remaining gates**
1. Reconcile current source and T0 active-scope index against all controlling owner decisions.
2. Complete minimum operational and evidence-lineage inventory with independently defined expected population.
3. Close remaining L4 assurance findings and exact artifact/readback requirements.
4. Verify the current source/build/runtime identity only after separate bounded deployment approval.
5. Complete T0→T2 API contract and failure-mode acceptance on an approved replacement host.
6. Preserve SQLite canonical data, lease/fencing, recovery and audit evidence; no lifecycle operation is implied.

**Status:** PARTIAL — source/contracts and historical tests exist; current runtime/deployment parity NOT VERIFIED.

### T1 — Futures Intelligence

**Purpose:** collect and normalize futures observations and publish versioned, provenance-bound intelligence datasets to approved consumers.

**Evidence-backed progress**
- Separate Rust collector repository and importer path exist.
- Contracts and tests cover raw stream handling, gaps/duplicates, funding/open-interest/trades/order-book areas.
- Reviewed CI evidence includes importer and Rust writer/contract jobs; historical PASS results apply only to the exact checked-out source and workflow run.
- T1 remains NOT ACTIVATED.

**Known blockers**
1. P1.42 / Issue #138 REQUEST CHANGES in the reviewed state.
2. F02-R24: source authenticity/traceability for fixture C02–C23 not accepted.
3. F07 filesystem behavior NOT VERIFIED.
4. Binance REST completeness and producer/consumer reconciliation remain unresolved.
5. T1 producer SHA / importer merge-base provenance mismatch must be reconciled.
6. BTCUSDT-only whitelist behavior and runtime capture have not been accepted.
7. Per-stream and total BTCUSDT storage growth has not been measured; no retention duration may be inferred.

**Remaining gates**
- Close P1.42 findings with exact evidence.
- Bind fixtures to authoritative source bytes and producer SHA.
- Prove bounded pagination/cursor continuity, gap handling, recovery and filesystem semantics.
- Verify BTCUSDT-only configuration and measured storage rate under separately approved synthetic or bounded capture tests.
- Register dataset identities, lineage and T2/T3 consumer dependencies.
- Obtain explicit activation approval before any runtime capture.

**Status:** BLOCKED for activation; contract/source progress does not establish operational readiness.

### T2 — Strategy Core and Independent AI Strategy

**Purpose:** preserve the established Core strategy while allowing a genuinely independent AI signal path. Both paths must pass the common risk authority before a paper trade is admitted.

**Strategy Core — preserved behavior**
- RSI + ADX + Smart DCA remains the Strategy Core.
- Core and AI decision paths and ledgers remain separately attributable.
- Core leverage policy is distinct from AI leverage policy.
- Shared risk admission is required for every new entry/DCA intent.

**Independent AI strategy — target architecture**
- AI may independently generate LONG/SHORT/WAIT, including when Strategy Core produces no signal.
- AI signal generation is not merely a confidence overlay or veto on Core.
- AI signals route to AI ledger; Core signals route to Core ledger.
- Both ledgers feed a common Shared Risk Engine and Kill Switch.
- No signal may bypass shared account exposure, margin, instrument, freshness, funding, or kill-switch controls.
- AI v1 DCA remains disabled unless separately specified and approved.

**Evidence-backed progress**
- AI strategy contract and research/evaluation contract are present.
- Separate AI/Core ledger routing and independent signal source paths have source-level and CI evidence.
- Strategy load smoke and focused tests have passed in recorded workflows.
- DS-03 Core sizing implementation has a separate evidence record.
- AI research R0/R1 and D1 bundle work have dedicated gates and reports.

**Known blockers**
1. AI leverage policy (target 1x–3x) is not yet proven end-to-end on the paper decision path.
2. Calibrated confidence and calibration provenance are not accepted as production inputs.
3. AI equity-based sizing and account-wide risk admission require exact-path verification; a fixed `PAPER_TARGET_BASE` path was identified and must not be mistaken for equity-based sizing.
4. D1 `T0_M15_H1_DATASET_BUNDLE_V1` has not been established as a verified, complete training bundle in the reviewed evidence.
5. R1 research contract/freeze remains a prerequisite; R2 offline experiment is not authorized until its own gates are satisfied.
6. Full shared risk enforcement, including the 1% account-equity margin cap, leverage, and Kill Switch, is NOT VERIFIED on every paper decision path.
7. No live execution or real order path is permitted.

**Remaining gates**
- Freeze R1 research protocol, labels, horizons, purge/embargo, features and evaluation rules.
- Verify the exact D1 source bundle, completeness, provenance and M15/H1 coverage.
- Complete calibration contract and out-of-sample calibration evidence.
- Implement and test AI sizing/leverage only after exact Owner approval; fail closed for missing, stale, uncalibrated or out-of-range inputs.
- Prove both Core and AI independently create signals and both are admitted/rejected by the same risk engine.
- Verify ledger attribution, duplicate/idempotent handling, Kill Switch and paper-only boundaries.
- Obtain separate approval before R2 training/experiment or scheduled FreqAI operation.

**Status:** PARTIAL — independent signal architecture/source work exists; AI research, calibrated sizing and full risk-path acceptance remain BLOCKED / NOT VERIFIED.

### T3 — Paper Execution and Portfolio Risk

**Purpose:** paper-only order lifecycle, separate ledgers, account equity, reconciliation and shared risk enforcement.

**Evidence-backed progress**
- CORE_LEDGER and AI_LEDGER are separate.
- Paper order lifecycle and account/equity concepts exist.
- Shared Risk Engine and Kill Switch are represented in source/contracts.
- CI evidence includes paper execution and ledger test jobs; recorded results are scoped to their exact source/run.

**Remaining gates**
1. Complete all applicable Dual Ledger contract gates and record per-gate evidence.
2. Verify persistent account state and migration/cutover plan without touching real funds.
3. Verify account equity, realized/unrealized PnL, funding, fees and reconciliation.
4. Prove risk reservations, concurrent admission, crash recovery and idempotency.
5. Prove global Kill Switch blocks both Core and AI admission.
6. Verify margin cap and leverage calculations on exact Core and AI paths.
7. Keep all execution paper-only; no exchange order submission.

**Status:** PARTIAL — code and test evidence exist; full account/runtime acceptance NOT VERIFIED.

### T4 — Dashboard, API Gateway and Android

**Purpose:** present system health, data quality, Core/AI signals, risk, equity and audit state through controlled interfaces.

**Evidence-backed progress**
- React dashboard/control surfaces and Android application source exist.
- Signal Board, Risk Management and audit/equity concepts are represented.
- API gateway architecture decision specifies a gateway/front door rather than having the frontend call multiple internal service ports directly.

**Remaining gates**
1. Reconcile dashboard components and API contracts with the current active branch source.
2. Verify authentication, authorization and read-only boundaries.
3. Verify gateway routing, timeouts, error handling and service isolation.
4. Run production-like React build and browser runtime tests under an approved test scope.
5. Verify Android build identity, package/version and paper-only behavior.
6. Complete end-to-end UI/API acceptance for independent Core and AI signals, separate ledgers and shared risk status.

**Status:** PARTIAL — source and architecture exist; integrated browser/API/Android acceptance NOT VERIFIED.

## 4. Cross-cutting G0 assurance

G0 is a separate assurance workstream. A policy decision or synthetic test PASS does not imply production verifier implementation or authorize S2.

### Owner-decided policy

- **D06:** initial phase uses manual Owner attestation; autonomous issuer authenticity is deferred.
- **D07-A:** inventory completeness requires independently defined expected population, deterministic enumeration and full expected/observed reconciliation. Producer manifest or Owner attestation alone cannot establish completeness.
- **D08-A:** no global freshness/latestness claim in the initial phase. Permitted claims are `INTEGRITY_ONLY` or `AS_OF_SNAPSHOT`; freshness-dependent decisions fail closed when freshness is unknown.
- **D09-A:** an authenticated Owner-controlled GitHub action/commit may be described as `PLATFORM_ATTRIBUTED_OWNER_ACTION`, not as a cryptographic signature or proof of factual truth.
- **D12-A:** append-only logical audit history in the approved GitHub repository/commit history; GitHub-domain custody only, not independent backup/DR/WORM. Exact artifact bytes must be read back and digest-checked before custody/readability claims. Corrections are linked events, not silent rewrites.
- **D13-A:** target is an immutable/versioned verifier-created envelope bound to exact subject, source, evidence digests, claim/scope, policy, verifier build/contract and evaluation set. No caller-controlled generic trusted boolean and no execution authority.
- **D14-A:** strict per-increment Owner approval. Every executable stage and operational/destructive action requires separate exact-scope approval. CI PASS does not substitute for authorization or acceptance.

### G0 progress and next gates

- G0.49: D07-A/D08-A/D09-A recorded; S2 implementation NOT AUTHORIZED.
- G0.51: D12-A/D13-A/D14-A recorded; S2 implementation and operational/destructive actions NOT AUTHORIZED.
- G0.52: D01–D14 closure audit PASS; S2 synthetic verifier BLOCKED / NOT READY.
- G0.53: S2 synthetic-verifier contract package prepared; requested decisions and exact implementation gate remain outstanding in the reviewed handoff.
- S1 synthetic parser has recorded focused test PASS; this does not establish production trust verification.

**Next:** reconcile the current G0.53 owner decision package and any later decision record; then prepare the next exact owner decision package only. Do not infer approval, begin S2, create keys/trust roots, connect providers, or run a verifier implementation.

**Status:** policy decisions recorded; S2 technical readiness BLOCKED / NOT AUTHORIZED.

## 5. Data lifecycle and storage governance

Controlling policy documents include:
- `docs/architecture/SHARED_DATA_FOUNDATION_LIFECYCLE_ADR_2026-11-08.md`
- `docs/architecture/CENTRAL_DATA_LIFECYCLE_POLICY.md`
- `docs/architecture/DATA_DELETION_SAFETY_CONTRACT.md`
- `docs/architecture/DATA_COPY_BACKUP_REPLICA_LIFECYCLE_CONTRACT.md`
- `docs/architecture/DATASET_CONSUMER_CONTRACT.md`

**Core rules**
- Demand-based retention is not delete-after-read.
- Read/download/job completion/consumer ACK, elapsed time, storage pressure, heartbeat loss or lack of recent access is never by itself a deletion trigger.
- T0 canonical candles remain protected; consumers do not receive direct mutation/deletion authority.
- CORE_LEDGER, AI_LEDGER, T3 reconstruction/reconciliation/audit evidence, governance approvals/history/tombstones and unknown/unclassified/orphaned data are excluded from ordinary class-wide deletion.
- Eligibility review is not deletion authorization.
- No numeric retention floor, TTL, grace period, review cadence or evidence-freshness window is approved unless a later exact Owner decision says so.
- The former Scaleway VPS was deleted on 2026-11-11; no replacement host exists in the reviewed handoff. G0.9 is documentary design only and no live filesystem inventory has been performed.
- Storage-pressure monitoring may alert/report only; it must never invoke cleanup or bypass protected-data rules.

**G0.9 disposition:** DOCUMENTARY DESIGN — CONDITIONAL PASS; NOT IMPLEMENTED / NOT ACTIVE. No object or class is currently authorized for deletion.

## 6. VPS capacity and deployment readiness

- G0.8-C is a capacity-planning document, not a provisioning approval.
- Planned envelope: one research host with separate logical/volume boundaries for OS/apps/logs, T0 canonical data, T1 raw capture, and T2 model/training/scratch data.
- Capacity figures are provisional estimates; T1 bytes/day, model footprint, training duration and runtime RSS/CPU/I/O behavior require measurement.
- A single host remains one physical failure domain even when volumes are separate.
- The old VPS was deleted on 2026-11-11; current runtime parity is NOT VERIFIED.
- No replacement VPS, volume, IP, package, service, deployment or exchange connection is authorized by this roadmap.

**Deployment gate:** first obtain a separate bounded provisioning/deployment approval; then validate T0, T1 and T2 in sequence, with paper-only safeguards and explicit Owner acceptance at each gate.

## 7. Dependency order and execution roadmap

| Order | Work package | Entry condition | Exit evidence | Current disposition |
|---:|---|---|---|---|
| 0 | GitHub governance and source topology | Existing branch preserved | Exact branch/PR/commit map; reconciled handoff and roadmap | BLOCKED / IN PROGRESS |
| 1 | T0 contracts and assurance | Scope and Owner invariants frozen | Inventory closure, exact-source evidence, read contract and recovery gates | PARTIAL |
| 2 | T1 provenance and contracts | T0 read contract stable; T1 remains isolated | P1.42 closure, fixture provenance, importer/producer reconciliation | BLOCKED |
| 3 | T2 Core/AI contracts and research | T0/T1 data contracts stable | R1 freeze, D1 bundle, calibration, sizing and shared risk tests | BLOCKED / PARTIAL |
| 4 | T3 paper execution and ledgers | T2 signal/risk contracts stable | Dual Ledger gates, account reconciliation, crash/idempotency tests | PARTIAL |
| 5 | T4 dashboard/API/Android | T0–T3 interfaces stable | Browser/API/Android acceptance and permission evidence | PARTIAL |
| 6 | Replacement VPS provisioning | GitHub contracts/CI and exact deployment scope approved | Provisioning evidence, security baseline, no-autostart until approved | NOT AUTHORIZED |
| 7 | Layered deployment validation | Replacement host and per-layer approval | T0→T1→T2→T3→T4 exact runtime evidence | NOT STARTED |
| 8 | End-to-end operational acceptance | All layer gates individually PASS | Reproducible paper-only E2E evidence and Owner acceptance | NOT STARTED |

## 8. GitHub completion process for every increment

For every completed work item:
1. Record exact scope and paths before editing.
2. Preserve existing decisions and evidence; do not rewrite historical facts.
3. Run only the tests authorized by the increment.
4. Record exact source SHA, workflow run/attempt, checked-out SHA, jobs, test counts and artifact details.
5. Mark each item PASS / PARTIAL / BLOCKED / NOT VERIFIED with the scope and time boundary.
6. Record next step, unresolved limitations and actions explicitly not authorized.
7. Commit on the existing working branch. Avoid unnecessary branch divergence and parallel PRs.
8. Re-read the changed file and verify the commit SHA after write.

## 9. Immediate next actions

1. **Complete repository topology inventory:** exact current branch HEAD, main comparison, open PR list, PR head/base SHAs, issue status, workflow runs and branch protections. Do this read-only; do not integrate branches.
2. **Reconcile controlling documents:** handoff, active scope index, architecture, runbook, lifecycle records and G0.53+ decisions. Correct only demonstrably stale status statements in a separately scoped documentation increment.
3. **Close T1 P1.42 blocker:** address fixture source traceability, producer SHA mismatch and filesystem/REST completeness evidence.
4. **Complete T2 AI research gate:** reconcile R1 freeze, D1 bundle evidence, calibrated confidence, equity sizing/leverage and common risk admission. No R2 or training without separate approval.
5. **Complete T3/T4 acceptance plans:** enumerate contract gates and exact evidence requirements before implementation or runtime work.
6. **Prepare replacement VPS decision package only after GitHub readiness:** capacity plan is not provisioning authority.

## 10. Explicit non-authorizations and limitations

This roadmap does NOT authorize:
- branch rebase/merge/force-push, branch deletion, bulk PR closure, or broad source refactoring;
- S2 implementation, key/trust-root/provider creation, or trust-verifier runtime;
- T1 activation or live capture;
- PostgreSQL/TimescaleDB canonical migration;
- AI R2 experiments, model training, scheduled FreqAI operation or signal publication outside paper scope;
- changes to risk limits, leverage, strategy behavior, ledger semantics or execution;
- replacement VPS provisioning, SSH/network/service changes, deployment or runtime probes;
- data cleanup, retention expiry, archive, vacuum, compaction, backup expiry or deletion;
- live trading, real orders, or enabling `AI_EXECUTION_ENABLED`.

## 11. Evidence index

Use these records as the starting evidence set; each result remains bounded to its exact scope and source:

- `docs/PROJECT_SESSION_HANDOFF.md` — controlling session handoff and current owner decisions.
- `docs/T0_ACTIVE_SCOPE_INDEX.md` — canonical T0 scope and parked backend boundaries.
- `docs/architecture/T0_READ_ONLY_CANDLE_CONTRACT_V1_2026-11-08.md` — T0 consumer contract (verify exact path before linking).
- `docs/architecture/T0_T1_T2_DATA_CONSUMPTION_ARCHITECTURE_2026-11-08.md` — data delivery architecture.
- `docs/architecture/DUAL_LEDGER_CONTRACT.md` — separate ledger contract.
- `docs/architecture/AI_STRATEGY_CONTRACT.md` — independent AI strategy contract.
- `docs/architecture/CENTRAL_DATA_LIFECYCLE_POLICY.md` — lifecycle governance.
- `docs/evidence/G0_6_T0_T2_DEPLOYMENT_PARITY_RECONCILIATION_2026-11-11.md` — current deployment parity disposition.
- `docs/evidence/G0_8_C_SCALEWAY_VPS_CAPACITY_PLAN_2026-11-11.md` — capacity plan only.
- `docs/evidence/G0_9_VPS_DATA_LIFECYCLE_STORAGE_GOVERNANCE_2026-11-11.md` — storage governance design only.
- `docs/evidence/G0_49_D07_D08_D09_OWNER_DECISION_RECORD_2026-11-11.md` — D07/D08/D09 decisions.
- `docs/evidence/G0_51_D12_D13_D14_OWNER_DECISION_RECORD_2026-11-11.md` — D12/D13/D14 decisions.
- `docs/evidence/G0_52_D01_D14_S2_READINESS_AUDIT_RECORD_2026-11-11.md` — S2 readiness audit.
- `docs/evidence/G0_53_S2_SYNTHETIC_VERIFIER_CONTRACT_OWNER_DECISION_PACKAGE_2026-11-11.md` — latest package referenced by the reviewed handoff.
- Issue #138 — T1 P1.42 review blocker.
- PR #92 — dashboard/shared-risk integration workstream; Draft status in the reviewed snapshot.

**Maintenance rule:** update this roadmap only when new source/evidence/Owner decisions are verified. Never promote a historical PASS to current PASS without a new exact-source check.
