# Hệ thống 5 tầng — Internal Dependency Mapping, Second Pass

- Date: 2026-11-10
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact source baseline: `4063d289dbf5287d9685c628ef9386a13474a7d3`
- Method: read-only inspection of the exact branch Git tree and selected source/document blobs.
- Scope: only components belonging to Hệ thống 5 tầng (T0–T4). Android Chart/Scanner and Python bot/backtest are explicitly OUT OF SCOPE per owner correction.
- No tests, workflow dispatch, VPS/SSH, database, exchange, provider, runtime or deployment access was performed.

## 1. Five-layer source map

| Layer | In-scope source | Observed responsibility / data path | Classification |
|---|---|---|---|
| T0 — Data Foundation | `market_data/feeder_service.py`, `feeder.py`, `store.py`, `storage.py`, `write_gateway.py`, `sync.py`, `api.py` | Binance USD-M BTCUSDT M15/H1 canonical ingestion, fenced writer/lease, SQLite default and optional PostgreSQL adapter, bounded read-only Candle API | KEEP — canonical foundation |
| T1 — Futures Intelligence | `futures_intelligence/import_collector.py`, `connection_events.py`, `collector_sidecar_writer/` | Imports external collector CSV observations (trades/funding/OI/liquidations), validates and emits `OBSERVED_ONLY` snapshot; separate Rust connection-event sidecar reference | KEEP core importer; PARK sidecar/upstream integration qualification |
| T2 — Strategy and AI | `freqai_bridge/`, `pipeline/core_strategy.py`, `core_signal.py`, `decision.py`, `values.py` | Independent RSI/ADX/Smart-DCA Core and FreqAI prediction path; FreqAI bridge reads T0 through authenticated HTTP; versioned signal/intent validation | KEEP — strategy and AI paths |
| T3 — Risk / paper execution | `paper_execution/`, relevant parts of `pipeline/api.py` | Persistent dual-ledger, account/risk state, reservations, pause/kill latch and paper-only visible-depth simulation | KEEP — paper/risk domain; no live executor |
| T4 — Control plane | `control_dashboard/`, `pipeline/api.py` | React presentation client and common authenticated API for status, signals, data quality, paper state and paper controls | KEEP frontend/API; edge Gateway implementation remains NOT IMPLEMENTED / NOT VERIFIED |

## 2. Confirmed internal dependency edges

1. T0 Feeder composition: `feeder_service -> storage/store + lease + write_gateway + sync`; runtime recovery and scheduler use the selected canonical writer.
2. T0 read interface: `market_data.api` exposes bounded authenticated read-only `GET /v1/candles` (default development listener 8788).
3. T2 canonical HTTP path: `freqai_bridge.context -> CandleHttpClient -> GET /v1/candles`; strict contract validation, no local SQLite/cache/alternate-venue fallback. Exact runtime endpoint remains dependent on environment configuration.
4. T1 observation path: `futures_intelligence.import_collector` reads pinned-format collector CSVs, verifies file provenance and emits a bounded snapshot; `pipeline.api` loads it from `INTELLIGENCE_REPORT_PATH`.
5. T2 AI path: `ChartProFreqaiResearch -> canonical_context + actual FreqAI prediction/provenance -> FREQAI_REPORT_PATH`; native Freqtrade entries/exits remain disabled and `confirm_trade_entry` rejects.
6. Strategy Core path: `pipeline.api.core_decide -> pipeline.core_strategy.produce -> pipeline.core_signal.validate`; it reads M15/H1 windows and paper strategy state before producing/validating a paper intent.
7. T3 market microstructure input: `pipeline.api.book_snapshot -> integrations.hummingbot_bridge.fetch_snapshot -> Hummingbot /market-data/order-book`; adapter is GET-only and normalizes a snapshot.
8. T3 paper path: `pipeline.api /v1/paper/evaluate -> PaperLedger.submit`; AI and Core sources are tagged separately and submitted to the persistent paper ledger/risk controls.
9. T4 path: `control_dashboard React -> same-origin /v1/* -> pipeline.api:application`; tokens are held in frontend memory. The documented API Gateway is a separate target component, not an implemented edge service in this source baseline.

## 3. Material boundary findings

### F5-01 — Two candle-serving paths; common API bypasses the T0 HTTP service boundary

- Evidence: `freqai_bridge/context.py` imports `CandleHttpClient`; `pipeline/api.py` imports `market_data.storage.create_store_from_env` and its `market_window()` calls `create_store_from_env().read_window()` directly. Its own `/v1/candles`, Core, equity and quality paths use this direct store access.
- T0 also has the separate `market_data.api:application` read-only API.
- Impact: T2's FreqAI context has an explicit HTTP boundary, but the common paper API/Strategy Core path is coupled to the configured storage adapter and does not consume the T0 HTTP endpoint. A single uniform T0 consumer boundary is therefore NOT ESTABLISHED.
- Status: SOURCE-CONFIRMED; intended deployment topology and whether this co-location is an accepted trusted boundary remain NOT VERIFIED.
- No recommendation to refactor in this mapping; design a separate boundary decision first.

### F5-02 — T0 candle store and T3 paper ledger share a configured SQLite path

- Evidence: `pipeline.api.market_window()` reads canonical candles from `create_store_from_env()`; `ledger()`, paper snapshot, Core state, audit and equity paths use `MARKET_DATA_DB`; `paper_execution/README.md` describes paper tables added to the same SQLite database without replacing candle tables.
- Impact: logical tables/domains are distinct, but physical storage/failure/backup/permission boundary is not independent in the SQLite configuration. This is narrower than claiming separate databases.
- Status: SOURCE-CONFIRMED for code path; actual configured path/backend and deployed physical topology NOT VERIFIED.
- Preserve existing data and schema. No split/migration is authorized.

### F5-03 — T1 CSV importer and connection sidecar are separate evidence/data paths

- Evidence: importer pins external collector commit `bc4f0ef633fbeee4a49defd72827f17162693805`, reads bounded CSV streams and emits `OBSERVED_ONLY` snapshots; the repository inventory identifies the Rust sidecar as a reference writer not integrated into the upstream collector.
- Impact: CSV observations do not prove complete exchange coverage or connection continuity; sidecar existence does not prove it is receiving live collector events. T1 readiness cannot be inferred from importer code or T0 candle readiness alone.
- Status: source-defined importer PASS; actual input files, active collector, sidecar integration and runtime snapshot NOT VERIFIED.
- Keep sidecar separate from the canonical T0 candle dataset.

### F5-04 — T3 is currently paper simulation, not Hummingbot order execution

- Evidence: `integrations/hummingbot_bridge.py` only accepts GET and calls `/market-data/order-book`; `paper_execution/README.md` says there is no HTTP client, exchange API key or real order function; ledger simulates fills from visible book depth.
- Impact: Hummingbot is currently a read-only book source for paper simulation. T3 order placement, exchange fill reconciliation and live execution adapter are not implemented by these files.
- Status: SOURCE-CONFIRMED; live execution remains explicitly unsupported/not authorized.
- Do not label a simulated fill as an exchange fill.

### F5-05 — T4 Gateway decision exists, but no deployed/implemented edge Gateway is established

- Evidence: `docs/architecture/T4_API_GATEWAY_ARCHITECTURE_DECISION_2026-11-08.md` says Gateway and T4 are separate and implementation/deployment are not authorized/not verified; `control_dashboard` calls same-origin `/v1/*`; `pipeline.api` binds to loopback in its development entry point.
- Impact: frontend-to-common-API contract exists in source; external edge routing, TLS termination, route isolation and deployed Gateway are not proven.
- Status: architecture DECIDED; implementation/runtime NOT VERIFIED. No proxy choice or deployment inferred.

### F5-06 — Strategy Core source defaults conflict with the approved conservative leverage/margin direction

- Evidence: `pipeline/core_strategy.py` defines `LEVERAGE` default 13 and `ENTRY_MARGIN_PCT` default 0.50; `pipeline/api.py` constructs the general ledger with `LEVERAGE` default 13. The dual-ledger scoped admission path separately caps each increase using 1% of equity as admission margin multiplied by the configured leverage.
- Impact: the producer's default target sizing and the ledger's per-increase admission sizing are different stages and must not be treated as one effective risk cap. The 13x default is inconsistent with the previously recorded no-fixed-13x Core direction; actual environment overrides and which ledger path is selected require verification.
- Status: SOURCE-CONFIRMED defaults; effective deployed values and exact risk-path selection NOT VERIFIED.
- No strategy/risk code changed. This finding requires a separate risk-contract reconciliation before any execution-path change.


### F5-07 — Common API ledger factory is not visibly strategy-scoped after dual-ledger migration

- Evidence: `pipeline/api.py.ledger()` constructs `PaperLedger(...)` without a `strategy_id` argument, so the constructor default is `MANUAL`. The same API later calls `ledger().submit(..., strategy_id="STRATEGY_CORE"|"AI_FREQAI")`.
- In `paper_execution/ledger.py`, `DUAL_STRATEGIES = {"STRATEGY_CORE", "AI_FREQAI"}`; `PaperLedger.submit()` enters the scoped path only when `self.strategy_id` is one of those values. For a MANUAL instance, the method checks whether dual-ledger migration is active and raises `DUAL_LEDGER_MIGRATION_ACTIVE_MANUAL_WRITE_BLOCKED` before the legacy write path.
- Impact: the statically traced common API evaluate path appears inconsistent with the dual-ledger scoped-write requirement. This may block Core/AI paper submissions through the common API after dual-ledger migration. This is a source-level call-path finding, not a claim that a deployed request was attempted or failed.
- Status: SOURCE-CONFIRMED CALL-PATH MISMATCH; runtime behavior NOT VERIFIED. Needs targeted unit/integration test and code-owner review before any fix.
- No source/test/runtime changes made.

## 4. KEEP / PARK / OUT-OF-SCOPE disposition

### KEEP
- T0 canonical Binance USD-M BTCUSDT M15/H1 Feeder, storage contract, fenced writer/lease, recovery, bounded read API and regression tests.
- T1 CSV importer/validator and bounded observed intelligence snapshot; keep the raw-source provenance distinction.
- T2 FreqAI HTTP consumer, prediction provenance, Strategy Core RSI/ADX/Smart-DCA logic, independent Core/AI signal interfaces and validation.
- T3 dual paper ledgers, account risk state, reservations, persistent kill/pause, paper fill simulation and tests.
- T4 React dashboard and common authenticated API contracts.

### PARK / NOT VERIFIED
- T1 upstream collector integration and Rust connection-event sidecar activation.
- T0 optional PostgreSQL/TimescaleDB activation and qualification.
- T0/T2 uniform API boundary for the common paper API/Core path (F5-01).
- Physical separation of canonical T0 data and paper ledger storage (F5-02).
- Hummingbot order execution/reconciliation beyond read-only book snapshots (F5-04).
- T4 edge Gateway/proxy implementation and deployment (F5-05).
- Strategy Core leverage/margin defaults and exact shared risk admission path reconciliation (F5-06).
- Runtime data paths, environment variables, active files, service listeners and actual backend selection.

### OUT OF SCOPE
- Android Chart/Scanner and Python bot/backtest, per owner scope correction recorded in the first-pass audit and handoff.
- Legacy Telegram/Codemagic scanner/backtest automation and unrelated archived Android/legacy workflows unless a separate in-scope dependency is proven. Their presence in the repository tree alone does not make them T0–T4 runtime dependencies.

No in-scope module is classified CANDIDATE FOR RETIREMENT in this second pass. No deletion, disabling, schema change, source change, API migration, database split, proxy deployment or runtime operation is proposed or performed.

## 5. Evidence anchors

Exact source baseline: `4063d289dbf5287d9685c628ef9386a13474a7d3`.

Selected blobs:
- `market_data/feeder_service.py`: `bdcecf6bc98a2ff070f83098d2c50154a160c99c`
- `market_data/api.py`: `81733c9b6de811cbebb2f5d472d41f37f337990c`
- `freqai_bridge/context.py`: `9abe781340dc9b948c40c759d92f340da3e372c1`
- `freqai_bridge/http_candles.py`: `eb9aeccdf381e8a2ebc3450a7a31ae4e9da164ac`
- `freqai_bridge/ChartProFreqaiResearch.py`: `a7722f1148cf105c853deedaacb88edd14e671be`
- `futures_intelligence/import_collector.py`: `5effe6540b86edcb190456c95b6bb11456aec099`
- `pipeline/api.py`: `0540540462b3710a25788e4ff47a88272b7ee9c3`
- `pipeline/core_strategy.py`: `b4266fc05ea41355ba9dcf6f15cb7b5a6d3800b0`
- `pipeline/core_signal.py`: `df5fbb59611bdd4fbb8224665f79655dd4433455`
- `paper_execution/ledger.py`: `0bc94ae0e704a69e253246a575991c1de436e0a4`
- `paper_execution/risk_control.py`: `3c76e462b0b4d924c2418842d95ed74285e2315d`
- `integrations/hummingbot_bridge.py`: `aa9db7522ffb7ce911c7fbbdc73a7f9b47401331`
- `control_dashboard/src/api.js`: `38cb5a464b05acd77914c7f333d377d8ac0535ad`
- `docs/FIVE_LAYER_ARCHITECTURE.md`: `74b2fbed86d1921e9c620ee7aa694f463afa3fc9`
- `docs/architecture/T4_API_GATEWAY_ARCHITECTURE_DECISION_2026-11-08.md`: `58822c59cf2dd0f4c5d2afe47f09ced41d343d6e`
- `docs/architecture/DATASET_CONSUMER_INVENTORY_BASELINE_2026-11-09.md`: `9183b94bcb959a999029d9698d129af9b9f39b20`

## 6. Limitations and status

- Exact branch tree identity and selected source/blob identities: PASS.
- Static T0–T4 component and selected dependency mapping: PARTIAL; not a full call graph.
- T0/T2 HTTP path: SOURCE-CONFIRMED for FreqAI bridge.
- Common API direct storage path: SOURCE-CONFIRMED.
- T1 active collector/CSV/snapshot/sidecar runtime: NOT VERIFIED.
- T3 paper-only boundary: SOURCE-CONFIRMED.
- T4 edge Gateway/deployment: NOT VERIFIED.
- Effective risk/leverage configuration and active dual-ledger path: NOT VERIFIED.
- Runtime/VPS/database/service/process/consumer inventory: NOT PERFORMED.
- Tests and GitHub Actions: NOT RUN / NOT DISPATCHED.
- L4-Minimum operational acceptance: remains BLOCKED / NOT VERIFIED.
- G2 exact-SHA CI execution and G3 independent review: remain NOT VERIFIED / PENDING.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Option C — No Destructive Authority — remains unchanged. No TTL, auto-delete, cleanup, archive, vacuum, compaction, backup expiry or replica removal.

## 7. Next safe increment

1. Reconcile F5-01/F5-02 as a documentation/design-only decision package: decide whether common API is intentionally co-located/trusted or must consume T0 HTTP, and whether shared physical SQLite is an accepted personal-use tradeoff or requires later isolation.
2. Reconcile F5-06 against the approved risk policy using exact source/config paths; do not edit sizing or leverage before the risk contract is approved.
3. Complete T1 producer-to-importer/sidecar static integration trace; no collector activation.
4. Continue source-only route/dependency mapping for T4 and service boundaries. No runtime inspection unless separately authorized.
