# Architecture Simplification Audit — Personal Quant Baseline

- Date: 2026-11-12 (Asia/Ho_Chi_Minh)
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Active branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Main-repository source baseline: `e90b539378e100cf87d1e3d0e0e072bd16ad3510`
- T1 repository: `kenznguyen/binance-futures-collector`
- T1 branch/source baseline: `feature/t1-connection-sidecar-integration-20261107` / `9d9d9f29a8b2d801d2c2d7b3fa45121cd1320599`
- Review type: read-only architecture/source/document inventory; no implementation.
- Overall disposition: **PARTIAL — useful simplification boundaries identified; no deletion/refactor is justified by this pass.**

## 1. Executive conclusion

The five-layer architecture is not inherently excessive for a personal BTCUSDT quant system. The existing architecture document already says that five layers are logical responsibilities, not five repositories or five separately deployed services; it also says that an MVP does not need an event bus or a new orchestration framework.

The main over-complexity risk is therefore **operational and integration duplication**, not the existence of five logical layers.

Recommended direction:

- Keep the five logical layers and their trust/risk boundaries.
- Implement them as a small **modular monolith plus independent data producers**, not as a microservice fleet.
- Keep T0 and T1 as independent data assets. T1 must not feed T0; T2 consumes T0 and T1 through separate adapters.
- Keep Core, AI, Shared Risk Engine, Kill Switch and separate Core/AI ledgers.
- Freeze new infrastructure and assurance-framework expansion unless a current acceptance gate requires it.
- Do not delete code, reduce tests, change schemas, or alter the active T1 producer-conformance work.

## 2. Repository inventory — context, not runtime size

At source baseline `e90b539...`, the recursive Git tree contains:

| Inventory | Count | Interpretation |
|---|---:|---|
| Tracked files | 918 | Includes documentation, evidence bundles and historical records |
| Documentation files | 615 | Not runtime components |
| Code/config files outside docs | 253 | Includes Android, CI, tests and application code |
| Test files | 89 | Preserve existing regression coverage |
| GitHub Actions workflows | 21 | Includes core CI and separate assurance/evidence workflows |

The large documentation/evidence footprint is a maintenance burden, but it must not be confused with deployed-system complexity. Historical evidence, audit records and frozen decisions should be preserved rather than deleted to make the repository appear smaller.

The active branch is substantially divergent from `main`: comparison at review time reported **3,382 commits ahead and 82 behind**. This is a repository integration/governance risk, not a reason to rebase, merge or create another branch during this audit. Keep work on the existing branch and do not create a parallel PR.

## 3. Findings by layer

### T0 — canonical data foundation

The prior T0 scope-minimization and dependency reviews already establish the correct boundary:

- Active canonical path: Binance USD-M BTCUSDT M15/H1, SQLite, fenced Feeder/writer/recovery and bounded read-only Candle API.
- PostgreSQL/TimescaleDB: optional and PARKED; SQLite remains the selected default.
- Kraken Spot: separate research domain, not canonical BTCUSDT Futures data.
- Connectivity probe: support-only.
- G0/L4 evidence and lifecycle assurance: separate assurance workstreams, not prerequisites for ordinary SQLite ingestion.

Those reviews found no safe source-retirement candidate. PostgreSQL requirements splitting was separately reassessed and PARKED because the extra package/workflow branching was not shown to reduce total complexity.

**Disposition: KEEP the current T0 active path. Do not simplify lease fencing, recovery, writer ownership, canonical validation, read-only boundaries or regression tests. Do not repeat the already-rejected PostgreSQL packaging split in this increment.**

Existing references:
- `docs/T0_ACTIVE_SCOPE_INDEX.md`
- `docs/evidence/T0_SCOPE_MINIMIZATION_REVIEW_2026-11-10.md`
- `docs/evidence/T0_SIMPLIFICATION_DEPENDENCY_REVIEW_SECOND_PASS_2026-11-10.md`
- `docs/evidence/T0_SIMPLIFICATION_POSTGRES_PACKAGING_REASSESSMENT_2026-11-10.md`
- `docs/evidence/T0_SIMPLIFICATION_ACTIVE_SQLITE_STARTUP_CONFIGURATION_REVIEW_2026-11-10.md`

### T1 — independent Futures producer

The current frozen boundary is clear:

- T0 and T1 are independent producers and independent data assets.
- No T1-to-T0 adapter, canonicalization or write path.
- T2 is intended to consume T0 and T1 through separate adapters.
- T1 CSV compatibility profile/schema v1.0.0 is frozen; producer conformance and immutable manifest publication are not yet complete.
- Existing T1 CSV importer is pull/CLI driven; the connection sidecar is an offline reference and is not integrated into the upstream collector or decision path.

At review time, T1 PR #1 remained OPEN/DRAFT/UNMERGED. Exact-head workflows `43162239707` (push) and `43162245242` (pull_request), both for source `9d9d9f29...`, were still IN_PROGRESS. The handoff identifies the in-flight `spawn_blocking` operation barrier as the producer-quiescence blocker.

**Disposition: DO NOT TOUCH T1 in this architecture pass.** No T1 source, schema, manifest, writer, workflow, runtime or PR changes. Do not begin T1→T2 adapter implementation until the existing producer-conformance gate and separately approved consumer contract permit it.

References:
- `docs/evidence/T1_T2_SCHEMA_FREEZE_V1_2026-11-12.md`
- `docs/evidence/T1_T2_INDEPENDENT_INGESTION_CONTRACT_PROPOSAL_2026-11-12.md`
- `docs/evidence/T1_PRODUCER_TO_CONSUMER_DEPENDENCY_TRACE_2026-11-10.md`

### T2 — Strategy Core and independent AI

The codebase has a native RSI/ADX/Smart-DCA Core path and a separate FreqAI decision path. The existing read-only AI-path audit confirms that Core WAIT does not inherently suppress an independent AI signal at source level.

The same audit records unresolved AI-specific requirements: bounded 1x–3x leverage, calibrated confidence/provenance and account-equity-based AI sizing. These must remain explicit gates; they are not reasons to add more AI frameworks or services.

FreqAI training/research is a separate process/job. The paper API consumes a published prediction artifact; paper-evaluation requests do not start training.

**Disposition: KEEP one Core producer and one independent AI producer. Do not add additional model services or duplicate inference frameworks before the existing AI calibration/sizing gates are resolved and real out-of-sample evidence exists.**

Reference: `docs/evidence/DUAL_STRATEGY_AI_PATH_READ_ONLY_AUDIT_2026-11-11.md`.

### T3 — Paper execution and risk

The paper system deliberately contains more accounting safeguards than a simple signal bot: idempotent intent handling, partial fills, Decimal accounting, reservations, separate strategy ledgers, account-level risk state, audit, funding/equity history and restart recovery.

Two source files are notably large:
- `paper_execution/ledger.py`: 112,445 bytes.
- `pipeline/api.py`: 32,105 bytes.

The Paper Ledger also imports account-history, funding, replay-input, equity and risk-control modules. This is a concentrated maintenance surface, but the behaviors protect accounting and risk invariants. File size alone is not evidence that these responsibilities are redundant.

The Paper Ledger currently uses the same SQLite file as canonical candles and adds `paper_*` tables. Paper writes use SQLite transactions (`BEGIN IMMEDIATE`). This reduces database/service count but couples T0 ingestion and T3 accounting through SQLite's single-writer lock. No contention failure was measured in this audit.

**Disposition: KEEP the risk/accounting behavior. Do not split the database or refactor the ledger without a separate design, contention evidence and full regression plan.** Treat database separation as a trade-off to measure, not an automatic simplification.

### T4 — control surface

The repository contains:
- React control dashboard under `control_dashboard/`, served by `pipeline.api` at `/control`.
- Android Paper client in `android-app/`.
- Root `dashboard/index.html`, documented as a manual JSON/CSV report viewer.
- Root `app.py`, a separate Flask health/dashboard entry point whose active use was not established in this bounded review.

The React dashboard is the documented five-layer control plane. The Android Paper client can remain an optional mobile client; it should not become a second independent decision/risk engine. The root report viewer and `app.py` should remain classified as support/legacy candidates until their callers, workflows and runtime use are verified.

**Disposition: Keep React as the primary control plane; avoid adding new dashboard surfaces. Do not delete Android Paper, root dashboard or `app.py` based on this audit.**

## 4. Cross-layer duplication and coupling

### ARCH-01 — two Candle API access paths (HIGH, design decision required)

- `market_data.api` exposes the bounded authenticated T0 read-only Candle API.
- `pipeline.api` also exposes `GET /v1/candles` and imports the same query parser, but its `market_window()` calls `create_store_from_env().read_window()` directly.
- `freqai_bridge` uses the T0 `CandleHttpClient` over HTTP.

This creates two access paths to the same canonical candles: HTTP contract consumption in the FreqAI bridge and direct storage access in the common paper API. It is not proven that both paths are wrong, but the ownership/interface rule should be explicit.

**Next design question:** should all T2 consumers use the T0 HTTP contract, or is the direct in-process store read an intentionally approved same-host optimization? Do not change code until the decision and compatibility tests are explicit.

### ARCH-02 — shared SQLite write-lock domain (MEDIUM, measure first)

T0 candle ingestion and T3 paper ledger mutations use the same SQLite file. This is operationally simple but couples independent responsibilities through SQLite's single-writer behavior.

**Next design question:** retain one file for the personal paper-first deployment, or isolate paper state in a separate SQLite file if measured contention or recovery isolation justifies the extra configuration. No DB/schema/runtime change is authorized by this audit.

### ARCH-03 — multiple server/UI entry points (MEDIUM, dependency mapping required)

The documented active services are T0 Candle API and the common `pipeline.api`; `app.py` is an additional Flask entry point with no active caller established here. React, Android Paper and the root static report viewer are different client/support surfaces.

**Next step:** trace imports, workflow references and operator entry points before classifying `app.py` or any UI as unused. No deletion now.

### ARCH-04 — order-book data has two distinct roles (LOW, preserve separation)

T1 captures raw Futures market observations, while the Paper Ledger consumes a Hummingbot normalized order-book snapshot for paper fill simulation. These are not automatically duplicates: research capture and execution simulation have different provenance and quality requirements. Keep the distinction explicit; do not merge the feeds without a validated contract.

### ARCH-05 — assurance workflows are not runtime services (MEDIUM, governance)

The 21 GitHub Actions workflows include T0 contracts, T2 smoke/consumer checks, Paper Writer/Dual Ledger tests and separate G0/L4 assurance work. They should not all be counted as five-layer runtime dependencies. GitHub Actions remains the preferred CI; Codemagic remains retained/fallback/legacy according to the existing governance.

Freeze further assurance-framework expansion outside already approved gates. Preserve current workflow/test denominators and historical evidence.

## 5. Recommended personal-use topology

Keep five logical responsibilities but use a small deployment topology:

1. **T0 service group:** one Feeder process and its bounded read-only Candle API, backed by selected SQLite storage.
2. **T1 producer group:** independent collector and its own raw output/manifest path; activate only after producer conformance passes.
3. **Quant/Paper service group:** one common `pipeline.api` process hosting Core/AI decision adapters, Shared Risk Engine, Paper Ledger, audit/quality endpoints and the React static UI.
4. **On-demand research job:** FreqAI training/research/prediction publication; do not make training a request-time API action.
5. **Optional external dependency:** Hummingbot only where its order-book snapshot is needed for paper fill simulation.

This is a **modular monolith plus independent producers**, not five microservices. No event bus, Kubernetes, public API gateway, multi-tenant layer or additional database is justified by the current personal-use scope.

This is a target topology only. The current handoff says the previous VPS was deleted and no replacement host is established; no deployment/runtime readiness is claimed.

## 6. Prioritized follow-up

| Priority | Work | Type | Boundary |
|---|---|---|---|
| P0 | Preserve T1 producer conformance work | Existing gate | No changes from this audit |
| P1 | Decide the canonical T0 candle read path for `pipeline.api` | Design-only | No code/API/schema change |
| P2 | Measure SQLite write contention between T0 and Paper Ledger | Evidence-only | Disposable/synthetic evidence only; no canonical DB |
| P3 | Trace `app.py` and root dashboard callers/workflows | Read-only | No deletion or retirement |
| P4 | Keep React primary and Android Paper optional | Scope decision | No UI changes |
| P5 | Revisit modular extraction only after tests are green and a concrete maintenance problem is demonstrated | Future refactor | TDD, one module at a time |

## 7. Evidence, limitations and status

- Main repository branch/HEAD read from GitHub: **PASS** — `feature/t0-centralized-data-feeder-p1-20261101`, `e90b539378e100cf87d1e3d0e0e072bd16ad3510`.
- T1 branch/PR head read from GitHub: **PASS** — `9d9d9f29a8b2d801d2c2d7b3fa45121cd1320599`.
- Static source/document inventory for the files listed in this report: **PASS**.
- Full repository call graph, every workflow consumer, active process inventory and deployed runtime: **NOT VERIFIED**.
- Tests/builds: **NOT RUN** by this audit.
- GitHub Actions: **NOT DISPATCHED** by this audit. T1 exact-head push/PR workflows were IN_PROGRESS at the recorded observation; see Section 2.
- Artifacts produced by this audit: **NONE**.
- Source code, T0/T1 schemas, package files, workflows, database, runtime, VPS, credentials, exchange connectivity and trading state: **UNCHANGED**.
- Paper-only remains mandatory; `AI_EXECUTION_ENABLED=false`; no live orders.

## 8. Next permitted step

Complete a design-only review of ARCH-01 (canonical candle read path) and ARCH-02 (shared SQLite write-lock domain), using synthetic/disposable evidence only where measurement is needed. Do not start implementation, change schemas, activate T1, deploy a VPS, or alter trading/risk behavior under this report.
