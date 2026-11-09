# T4 RET-03 Owner Input Resolution — Dashboard, Read Models and Exports (2026-11-10)

## 1. Status and scope

**Stage A.5 documentary/source trace: COMPLETE.**  
**T4 RET-03: OPEN / FLOOR_NOT_ESTABLISHED.**  
**No numeric retention floor or TTL selected. No T4 object is deletion-eligible.**

Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Source baseline HEAD: `0052c7821f8e01379d4d6a69acad8d2340b044fb`

Scope is the five-layer React application under `control_dashboard/`, its common API read paths in `pipeline/api.py`, and relevant API Gateway design/evidence. Android Chart/Scanner and the legacy standalone `dashboard/index.html` backtest page are excluded; they are not the current five-layer T4 React dashboard. The legacy page's manual backtest JSON/CSV import is not treated as a T4 export pipeline.

This is a static repository analysis. It does not establish which build is deployed, whether the API is running, the actual configured report paths, the actual data files or their copies, browser/session behavior in a live deployment, or the complete runtime consumer graph.

No VPS/runtime/network/proxy, DB, report file, browser session, external provider, backup, replica, export destination or recipient was accessed. No tests, GitHub Actions, build, deployment, permission change, inventory command, source/config/schema/workflow change or destructive operation was performed.

## 2. Exact source records inspected

| Source | Blob SHA |
|---|---|
| `docs/evidence/T4_ROUTE_AUTH_CONTROL_DEPENDENCY_MAPPING_2026-11-10.md` | `536dbe3beb749afe41614d04e960a89508a2ce44` |
| `docs/architecture/T4_API_GATEWAY_ARCHITECTURE_DECISION_2026-11-08.md` | `58822c59cf2dd0f4c5d2afe47f09ced41d343d6e` |
| `control_dashboard/README.md` | `df8929a51dba2517b68080d529a4e8c6eba2afca` |
| `control_dashboard/package.json` | `b457cb2187bbd282d078bd719d4cedf78cc415eb` |
| `control_dashboard/src/App.jsx` | `f549fa442f23d39b0caec5a822dbd1ad3b25bc75` |
| `control_dashboard/src/api.js` | `38cb5a464b05acd77914c7f333d377d8ac0535ad` |
| `control_dashboard/src/useTerminal.js` | `3ed925e5b4c27d58ff94cdb1bbf0b64ac99fa28c` |
| `control_dashboard/src/CandleChart.jsx` | `ed454d6193459693ae81dc3a2808e6ea7c3fa8e5` |
| `control_dashboard/src/EquityChart.jsx` | `b8f690a86845e8fc8ed9c85dd5e81eaa39478306` |
| `control_dashboard/src/riskMetrics.js` | `2280b702db3d3bdd0eb007574c135aa4507da98d` |
| `control_dashboard/src/api.test.js` | `628084e7509f805a1c5248422f36fb75054bacda` |
| `control_dashboard/src/App.test.js` | `7eebfb65efacb16a67eb7df9dd4e54fb358abac2` |
| `control_dashboard/vite.config.js` | `fa29bc959a2ee764396fcf04d444dd6f2887dffd` |
| `pipeline/api.py` | `0540540462b3710a25788e4ff47a88272b7ee9c3` |
| `market_data/api.py` | `81733c9b6de811cbebb2f5d472d41f37f337990c` |
| `paper_execution/equity.py` | `40d6566294355c646839614c92f8fba6116b582c` |
| `paper_execution/ledger.py` | `0bc94ae0e704a69e253246a575991c1de436e0a4` |
| `futures_intelligence/import_collector.py` | `5effe6540b86edcb190456c95b6bb11456aec099` |

These are selected source anchors, not a complete repository/runtime inventory. The prior route/auth mapping document records a separate historical source baseline and the exact selected route/frontend anchors above.

## 3. T4 data flow and object classes

### 3.1 React application state and browser transport

- `useTerminal()` polls nine GET resources every five seconds while the page is visible: system, intelligence, decision, signals, paper, candles, equity, audit and quality.
- Responses are held in React component state. A connection change resets the displayed data; disconnect/reload clears the in-memory credentials/state. README states read/control tokens are not persisted to localStorage, sessionStorage, cookies or URLs.
- The browser request helper uses bearer headers, `credentials: omit`, `redirect: error`, `cache: no-store`, a 15-second timeout and a 2 MiB response cap. The API returns `Cache-Control: no-store`.
- The React charts derive SVG from the current candle/equity response in memory. The chart's displayed candle/equity point limit is a presentation bound, not an authoritative retention rule.
- No browser-side durable market-data, order, audit or equity database was found in the inspected frontend source. This is not proof that browser caches, screenshots, downloads, browser backups, operator captures or other copies do not exist.

**Classification:** React view state and SVG render output are transient presentation material only insofar as no separate capture/export/consumer exists. Do not apply a blanket class-level deletion rule until deployed browser/session, operator capture and downstream consumer/copy scope are established.

### 3.2 T0 candle read model

- Dashboard calls `/v1/candles` for a bounded closed M15 window. The common API delegates to the configured market-data store; the canonical candle API is read-only and has its own authenticated, bounded read path.
- T0 candles, coverage, dataset version and source provenance are T0-owned canonical/recovery data, not T4 cache ownership.
- The frontend only renders a bounded subset. That does not reduce the T0 canonical retention or recovery obligation.

**Classification:** T0 canonical records and their required recovery/evidence copies remain protected under T0 policy. T4 has no authority to delete or mutate them.

### 3.3 T1 intelligence snapshot

- Common API reads the configured `INTELLIGENCE_REPORT_PATH` JSON and validates it as an observation snapshot.
- T4 receives feed status, freshness, counts, snapshot ID, collector commit and quality fields. The source collector builds a bounded snapshot from CSV inputs and includes input-file provenance/hashes.
- The actual report file path, rotations, source CSV copies, report archive, consumer population and custody are environment/runtime facts not established by this repository trace.

**Classification:** T1 raw observations and their source/provenance obligations remain T1-owned. The T4 response is a derived view, not proof that source CSVs or report files may be deleted. Preserve any snapshot/report copy needed for lineage, replay, incident or audit until its owner establishes otherwise.

### 3.4 T2 FreqAI prediction and strategy views

- Common API reads `FREQAI_REPORT_PATH` and computes AI decision/signal views. Strategy Core signal is separately computed from canonical M15/H1 data and paper state.
- The dashboard displays AI/Core decision and signal snapshots; it does not own model training artifacts, model lifecycle or authoritative strategy execution.
- The inspected T2 analysis already records that the prediction JSON output is a replaceable latest-output slot, not a complete immutable prediction history. T4 polling cannot restore overwritten predictions or training provenance.
- Actual model/report path, historical prediction copies, consumers and model/evaluation artifact custody are NOT VERIFIED here.

**Classification:** T2 model, training, evaluation, prediction provenance and decision evidence remain T2-owned/protected according to the T2/T3 dependency graph. A T4-rendered decision snapshot is not a substitute for immutable T2/T3 evidence.

### 3.5 Hummingbot order-book snapshot and process cache

- The common API fetches a fixed BTCUSDT book snapshot from server-side Hummingbot credentials; the API code maintains an in-process cache for up to three seconds.
- This cache is a short-lived process optimization. It is not the authoritative order-book source and does not establish a durable historical book archive.
- Paper fill events refer to a book snapshot identity; the T3 report has already identified that an ID/digest alone does not prove source-byte custody or full upstream completeness.

**Classification:** the three-second in-memory cache may be a candidate transient object only after runtime process/copy scope and any event/replay references are proven. Any book snapshot bytes referenced by fills or needed to reconstruct paper decisions remain protected T3 evidence.

### 3.6 Paper state and audit views

- `/v1/paper` uses the ledger's read-only snapshot path and requires an existing DB; it does not initialize a new DB on that GET path.
- `/v1/audit?limit=50` reads the most recent bounded audit view. A display limit of 50 is not a retention limit and does not mean older audit records are disposable.
- T4 displays paper position/orders, risk state and audit entries. Authoritative paper orders, ledgers, risk controls, event journal and audit rows remain T3-owned.
- Control POSTs (evaluate, pause, cancel, kill and reset-kill) are separate state-changing operations protected by `CONTROL_TOKEN`. UI state is not the authorization boundary; backend enforcement remains authoritative.

**Classification:** CORE_LEDGER, AI_LEDGER, LEGACY_UNATTRIBUTED, paper orders, reservations, event/audit journals, risk controls and required T3 reconstruction evidence remain protected. T4 display copies are derivative; deleting the view state does not close the underlying T3 obligations.

### 3.7 Equity read path — persistent side effect

**T4-RET-01 — `GET /v1/equity` is not a pure read in the inspected implementation.**

- The route calls `equity_snapshot()`, which calls `PaperLedger.record_equity()`.
- `record_equity()` persists `paper_equity_history` observations and `paper_daily_baselines`, including mark, position, average, realized PnL, fees, unrealized PnL, equity, HWM, drawdown, exposure and T0 dataset version.
- The frontend polls this endpoint every five seconds while visible. The equity history code uses a canonical snapshot hash and `INSERT OR IGNORE`; repeated equivalent snapshots may be idempotent, but this does not make the stored record a disposable cache.
- The same equity/risk state is used by the Shared Risk Engine and daily equity reconstruction. The equity history and baseline are therefore not T4-owned view cache; they are T3 paper account/risk/reconstruction records.
- The actual runtime polling rate, persisted row volume, database path and whether the route is currently deployed are NOT VERIFIED.

**Disposition:** keep equity history, daily baselines, cutover/replay dependencies and their required backup/evidence copies protected under T3. Do not solve the write-on-read design observation by deleting history or reducing retention. Any future endpoint separation/idempotency/polling change requires a separate design and implementation approval.

## 4. Export, cache and build-artifact findings

| Object | Source-level finding | RET-03 classification |
|---|---|---|
| React component state | In-memory view state; reset on disconnect/reconnect | Potential transient; exact deployed browser/capture scope NOT VERIFIED |
| SVG candle/equity chart | Derived from bounded API response; rendered in browser | Presentation output; no durable export path found in inspected T4 source |
| HTTP response cache | Frontend requests use no-store; API responses use Cache-Control no-store | Cache policy is source-confirmed; browser/proxy/service-worker/runtime copies NOT VERIFIED |
| Hummingbot book cache | In-process, up to three seconds | Candidate ephemeral process cache; protect any source bytes linked to T3 fills |
| T0 candle API response | Bounded canonical read | T0-owned source; no T4 retention authority |
| T1 intelligence JSON/report | File-backed upstream observation snapshot | T1-owned; actual copies/rotation NOT VERIFIED |
| T2 prediction JSON | File-backed latest prediction consumed by common API | T2-owned; overwrite means historical lineage remains a gap |
| Paper/audit API response | Read-only view over T3 records | T3-owned records remain protected |
| Equity API response | GET triggers persistent equity observation write | T3-owned risk/reconstruction record; not a disposable T4 cache |
| `control_dashboard/dist` build | Static app build from source and lockfile; no market/account data expected in build source | Build artifact lifecycle/copies/deployment NOT VERIFIED; no class-wide expiry |
| CSV/JSON export/download from current T4 | No explicit export/download function found in inspected T4 React source | NOT FOUND in selected source; external/manual captures and other paths NOT VERIFIED |
| Legacy `dashboard/index.html` | Standalone historical backtest-report file-import page | Explicitly excluded from current five-layer T4 scope; do not infer it is an approved current export path |

No T4-owned durable export archive or data warehouse was identified in the inspected source set. Absence from selected source files does not prove absence from deployment, operator workflows, connected apps or external copies.

## 5. Dependencies and retention ownership

T4 is a replaceable presentation layer, but the displayed objects retain the source-layer obligations:

1. T0 canonical candle store, dataset versions, coverage and required recovery/evidence copies remain T0 protected.
2. T1 raw observation files, CSV source evidence, intelligence snapshots and provenance remain T1 protected until T1 owner inputs and copy inventory are complete.
3. T2 training/model/evaluation artifacts, prediction provenance and decision lineage remain T2 protected.
4. T3 CORE_LEDGER, AI_LEDGER, LEGACY_UNATTRIBUTED, signal/risk/order/fill/reservation/funding/equity/audit/replay/reconciliation/correction evidence remain protected.
5. Gateway/API access and security evidence, credentials custody/rotation/revocation records, deployment/build provenance and incident evidence remain governed by their respective security/operational obligations.
6. Unknown, unclassified, orphaned, externally copied or incompletely inventoried objects remain protected under Option C.

A frontend polling interval, chart point limit, API query limit, cache TTL, request timeout, build output path or order validity window is not a retention floor or evidence that an underlying obligation ended.

## 6. RET-03 owner-input matrix for T4

| Required input | Evidence available | Missing input | Status |
|---|---|---|---|
| Purpose | Display system/market/intelligence/strategy/paper/equity/audit/quality state | Owner-approved purpose and obligations for each response/build/capture class | PARTIAL |
| Owner / custodian | T4 React and common API code paths identified | Accountable owner/custodian for deployed builds, browser captures, report files, proxy caches, exports and recipients | NOT PROVIDED |
| Exact object scope | Source paths, API routes, payload classes and some file-backed report paths | Exact deployed dist hash, runtime files, browser copies, proxy/CDN/service-worker caches, screenshots/downloads/exports and DB rows | NOT VERIFIED |
| Source ownership | T0/T1/T2/T3 source paths traced | Signed owner mapping and complete upstream source/copy registry | PARTIAL |
| Start event | API observation and dataset timestamps exist | Owner-approved start event for each display/capture/build/evidence object | OPEN |
| Terminal event | React disconnect/reload and request completion exist; cache code has three-second expiry | Positive closure event for operator captures, incidents, audits, T3 reconstruction, model/data lineage and security obligations | OPEN |
| Duration / numeric floor | No T4-specific approved floor found | Authoritative source-backed duration for each independently owned object class | NOT PROVIDED |
| Consumer closure | Nine API reads and paper control paths traced | Complete browser, API, automation, operator, monitoring, downstream and external recipient inventory | NOT VERIFIED |
| Copy graph | Source code documents no browser storage and no-store requests | Actual browser/network/proxy caches, backups, CDN, logs, screenshots, downloads, exports and recipient copies | NOT VERIFIED |
| Build provenance | package manifest, lockfile and Vite build configuration exist | Exact build input/output hashes, CI artifact retention, deployed build and rollback copies | NOT VERIFIED |
| Holds / incidents | No T4-specific hold registry in inspected files | Competent hold authority, scope, release evidence and reopen/successor rules | NOT PROVIDED |
| Security evidence | Read/control tokens separated; API/Gateway controls documented | Actual secret custody, access population, rotation/revocation, proxy exposure and security log lifecycle | NOT VERIFIED |
| Owner disposition | No T4 retention-floor decision found | Explicit owner disposition tied to exact immutable object/version and authoritative basis | NOT PROVIDED |

No duration is inferred from the three-second in-memory book cache, five-second UI polling, 15-second request timeout, 50-row audit view, 240-point chart display, API response size cap or build tooling.

## 7. Required owner inputs before finite-floor assessment

1. Confirm T4 ownership boundary and name custodians for React build, deployed static files, operator captures and any downstream dashboard data products.
2. Identify exact deployed build hashes and every serving/storage location, including rollback artifacts and CI artifacts.
3. Inventory actual browser, reverse-proxy, CDN, service-worker, network, log, monitoring, screenshot, clipboard, download and manual export copies.
4. Confirm actual configured T0/T1/T2 report paths and all upstream consumers/copy destinations.
5. Classify each API response as transient presentation, source-layer data, T3 accounting/risk evidence, security/governance evidence or separately persisted T4 artifact.
6. Resolve the `GET /v1/equity` persistent write behavior as a separately approved design question; do not delete or shorten equity history to mask it.
7. Confirm whether any export/download workflow exists outside the inspected T4 React source and identify recipients and downstream dependencies.
8. Define owner-approved start/terminal events and duration basis per class, including incidents, audits, disputes, recovery, rollback and security investigations.
9. Establish complete consumer/copy/hold inventory and positive release evidence before any individual object can be assessed as a candidate.
10. Keep unknown or unclassified objects protected; if an authoritative duration basis is absent, leave the floor open.

## 8. Stage A.5 result and controls

- **T4 React/source/API data-flow map:** DOCUMENTED.
- **T4 presentation/cache/export classification:** DOCUMENTED at selected source level.
- **Persistent equity side effect:** SOURCE-CONFIRMED; runtime invocation frequency and deployment NOT VERIFIED.
- **T4 RET-03:** OPEN / FLOOR_NOT_ESTABLISHED.
- **Numeric retention floor / TTL:** NONE SELECTED.
- **Deletion eligibility:** NONE.
- **Tests:** NOT RUN; documentation-only increment.
- **GitHub Actions:** NOT DISPATCHED; no workflow run or artifact claimed.
- **Build/deployment/runtime/browser/proxy/consumer/copy inventory:** NOT PERFORMED.
- **Legal/contractual determination:** NOT PERFORMED.
- **Source, schema, config, workflow, permission, runtime and data:** UNCHANGED.
- **Archive, expiry, cleanup, compaction, vacuum, backup/replica removal, export mutation and deletion:** NOT AUTHORIZED / NOT EXECUTED.

Option C — No Destructive Authority — remains in force. The lifecycle independent-review waiver removes only the human reviewer gate; it does not waive owner authority, substantive evidence, technical separation, inventory, exact-object/version binding, fail-closed requirements or destructive-operation prohibitions. T0 independence, separate CORE_LEDGER/AI_LEDGER, required T3 reconstruction/audit evidence, paper-only mode and `AI_EXECUTION_ENABLED=false` remain unchanged.

**Final status: STAGE A.5 DOCUMENTARY TRACE COMPLETE — T4 RET-03 OPEN — NO NUMERIC FLOOR — NO DELETE-AFTER-USE AUTHORITY.**
