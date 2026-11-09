# T0 Dependency Mapping — first-pass static inventory

- Date: 2026-11-10
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact inspected branch HEAD: `cf0b66580cadfda54945e6c327f75b4cfb075bc4`
- Method: read-only Git tree, exact-branch blob inspection for selected T0 source/tests/workflows, plus static import/call-site inspection.
- Scope: no source edits, no test execution, no workflow dispatch, no runtime/VPS/database/provider access.
- Status: FIRST-PASS STATIC MAP; NOT A COMPLETE REPOSITORY-WIDE CALL GRAPH.

## 1. Runtime path established from exact-branch source

1. `market_data.feeder_service` is the process entry point: module `__main__` calls `main()`, which calls `build_production_runtime()`.
2. `build_production_runtime()` selects the configured backend through `create_store_from_env()` and constructs the runtime.
3. `build_runtime()` composes the Feeder, lease implementation, write gateway and scheduler/recovery path.
4. SQLite path uses `SQLiteWriteGateway`; PostgreSQL path uses `PostgresWriteGateway`, `PostgresLeaseStore` and `PostgresStore`. The selected gateway instance is passed to `sync_window` and retained as the runtime's canonical write gateway.
5. `market_data.sync.sync_window` is shared ingestion logic. The module also exposes a standalone CLI described by `market_data/README.md`; that one-shot sync path is distinct from the always-on Feeder service.
6. `market_data.api` is the separate WSGI read-only Candle API. It creates the selected read store from environment and only serves bounded GET reads.
7. `freqai_bridge/context.py` imports `CandleHttpClient` from `freqai_bridge.http_candles`; this confirms an HTTP consumer boundary rather than direct import of T0 SQLite storage in that consumer.

## 2. Component disposition

| Component | Exact-branch evidence | Classification | Decision |
|---|---|---|---|
| `market_data/feeder.py` | Feeder and lease primitives; imported by feeder_service and T0 tests | Core runtime | KEEP |
| `market_data/feeder_service.py` | Owns runtime composition and executable module entry point | Core runtime | KEEP |
| `market_data/store.py` | Candle contract, validation and SQLite read/storage primitives; imported by core modules | Core data contract | KEEP |
| `market_data/storage.py` | SQLite default and explicit opt-in PostgreSQL adapter selection | Core abstraction with optional backend | KEEP; PostgreSQL remains PARK operationally |
| `market_data/write_gateway.py` | SQLiteWriteGateway used by feeder_service; ShadowWriteGateway used by sync/tests | Core write boundary | KEEP |
| `market_data/sync.py` | Shared sync_window called by feeder_service; standalone one-shot CLI documented | Core ingestion logic | KEEP |
| `market_data/api.py` | Bounded authenticated read-only WSGI endpoint | Core consumer boundary | KEEP |
| `market_data/initialize_sqlite.py`, `migrations.py` | Schema/bootstrap support referenced by storage/runtime/test paths | Core support | KEEP |
| `market_data/binance_connectivity_probe.py` | Dedicated probe module and dedicated workflow/test | Diagnostic support, not ingestion runtime | PARK as optional diagnostic |
| `market_data/postgres.py` and PostgreSQL migrations/tests | Directly imported by feeder_service and storage; separate PG workflow/test coverage exists; runtime backend can select PostgreSQL | Implemented optional backend, not dead code | PARK provider activation/qualification; KEEP source and tests |
| `market_data/kraken_spot.py`, `kraken_spot_store.py`, `kraken_spot_api.py` | Isolated Kraken Spot identity/storage/API; dedicated tests and manual-validation gates; separate SQLite file requirement | Separate research domain | PARK outside canonical T0 |
| `market_data/t0_t2_parity.py` | Referenced by T0/T2 consumer test command in workflow | Cross-layer contract test/support | KEEP while T2 consumes T0 |
| `synthetic_evidence/t0_checkpoint_contract.py` and tests | Isolated synthetic-only checkpoint oracle and dedicated G2 workflow | Evidence workstream, not T0 runtime | PARK feature expansion; preserve current G2/G3 blockers and artifacts |

No component is classified CANDIDATE FOR RETIREMENT in this pass. The evidence is insufficient to prove global non-use or safely retire any file.

## 3. Workflow dependency map

Exact branch tree contains these relevant workflows:

- `.github/workflows/t0-single-writer-gateway-red.yml`: runs gateway, fenced-store, store, sync, storage, Feeder lifecycle/health/restart, broad market_data suite, paper consumer parity, and separate PostgreSQL writer/runtime/role/TimescaleDB test steps. This workflow couples several validation domains; it is not safe to remove merely because PostgreSQL is parked.
- `.github/workflows/t0-manual-validation.yml`: contains explicit `kraken-adapter`, `kraken-spot-sqlite`, `kraken-spot-read-api`, component, TimescaleDB and SSH preflight gates. Kraken is manually gated, not part of the default canonical ingestion path.
- `.github/workflows/t0-binance-connectivity-probe.yml`: diagnostic connectivity probe.
- `.github/workflows/t0-postgres16-grantor-repro.yml`: PostgreSQL privilege/grantor reproduction.
- `.github/workflows/t0-sqlite-readonly-sandbox.yml`: SQLite read-only sandbox.
- `.github/workflows/t0-systemd-feeder-api-integration.yml`: Feeder/API deployment integration; operational scope must be reviewed separately before any retirement.
- `.github/workflows/t0-evidence-contract-g2.yml`: synthetic-only checkpoint contract; G2 exact-SHA execution remains NOT VERIFIED.
- `.github/workflows/t2-http-consumer-red.yml`: T2 HTTP consumer contract dependency.

The workflow names and their configured test commands establish repository CI/test references, not proof that a workflow is currently scheduled, successful, or required by branch protection. No workflow was run or modified.

## 4. Evidence anchors

Exact branch HEAD: `cf0b66580cadfda54945e6c327f75b4cfb075bc4`.

Key source blobs:
- `market_data/feeder.py`: `935d295ef42c94482a48ce6ccdc927ebfa4c7e22`
- `market_data/feeder_service.py`: `bdcecf6bc98a2ff070f83098d2c50154a160c99c`
- `market_data/store.py`: `4e1b0c54bd56455abe5be0e5c7d0807e63e0bc78`
- `market_data/storage.py`: `13fe1ae01ebb5318b69e69eef3e512d207f74c49`
- `market_data/write_gateway.py`: `b2029d9db15fe39dcbe575acfeb6df1b16e16acd`
- `market_data/sync.py`: `e7ad4e6f2074225957b01f74abb0befe37675ea2`
- `market_data/api.py`: `81733c9b6de811cbebb2f5d472d41f37f337990c`
- `market_data/postgres.py`: `2fe27fe2d066dda0c192a381b72d27404487b800`
- `market_data/kraken_spot.py`: `d8191606d27617f964f23736e07fb7fe7458dc39`
- `market_data/kraken_spot_store.py`: `1736935cf143c11f0789651b5ef80a1821aabbb8`
- `market_data/kraken_spot_api.py`: `5d8679f74fe5d4b70d89ba796f83550c6e1f2c58`
- `freqai_bridge/context.py`: `9abe781340dc9b948c40c759d92f340da3e372c1`

Workflow blobs:
- T0 single-writer: `2d836c6c835f414efa62137abf7b97b7bcd6d5ec`
- T0 manual validation: `395ae93274a9202f14ab63d528be5cd582c30149`
- T0 Binance probe: `42050b37282d81c21149d3a25d0eb3ba6d99771b`
- T0 PostgreSQL grantor: `c7bc589ca8240edb25a9c33cce5b9a76e6193271`
- T0 SQLite sandbox: `a41e63cc7581606c6fb1bea264c1340d6448355d`
- T0 systemd integration: `64476a3dd281eb69b92d29f3783570107c4ab48e`
- T0 Evidence G2: `5e22648c38fd3c6e631f912010de1489bb78f9b5`
- T2 HTTP consumer: `7690780e076c317345879dcef081951e78cf2c6a`

## 5. Gaps and limits

- The repository tree was read at exact branch HEAD, but the source call-site inspection covered selected T0 modules, tests and workflows, not every source file in the repository.
- GitHub code-search connector searches the repository default branch, not this feature branch; its results were not treated as proof of exact-branch references.
- No live process/service manager, VPS filesystem, systemd state, cron/scheduler, deployed configuration, database contents, or consumer traffic was inspected.
- No branch-protection/ruleset requirement was inferred from workflow presence.
- PostgreSQL runtime selection exists in code, but current operational backend selection/deployment is NOT VERIFIED.
- Kraken Spot has dedicated tests/manual gates; global consumer/runtime use outside the selected files is NOT VERIFIED.
- Write-gateway is not a retirement candidate: feeder_service imports it directly, and SQLiteWriteGateway is used in the core runtime path.
- No tests, py_compile, CI, runtime probes, provider calls or integration execution occurred.

## 6. Next safe increment

1. Extend exact-branch consumer reference inventory across all repository source and deployment/config files.
2. Inspect every T0 workflow's triggers, required status/check dependencies and artifact retention before proposing workflow consolidation.
3. Reconcile actual runtime/deployment evidence only with separately authorized read-only access.
4. Produce a separate retirement proposal with dependency closure, replacement path, rollback and test impact.
5. Do not delete or disable any module/workflow, alter schemas, change backend selection, or modify runtime without explicit approval.

## 7. Status

- Exact branch tree and selected-blob identity: PASS.
- Core Feeder/runtime composition mapping: PASS for inspected source.
- T0 workflow/test references: PARTIAL.
- Repository-wide source consumer/call graph: NOT VERIFIED.
- Live runtime/deployment consumer inventory: NOT VERIFIED.
- KEEP/PARK first-pass classification: PASS with stated limitations.
- CANDIDATE FOR RETIREMENT: NONE.
- Source/runtime/database/VPS/workflow mutation: NONE.
- T0 L4-Minimum operational acceptance: remains BLOCKED / NOT VERIFIED.
- G2 exact-SHA execution: NOT VERIFIED; G3 independent review: PENDING.
- Option C remains in force; no automatic delete-after-use, TTL, archive, cleanup, vacuum, compaction, backup expiry or replica removal. `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.


## 8. Supplemental repository-wide consumer findings (same frozen source baseline)

Additional exact-branch Android source inspection found an important boundary not captured in the initial Python-only path:

- `android-app/.../MarketEngine.kt` blob `ed921c7278ce3397c85c49c9706c2b5550fc5012` directly builds HTTP requests to Binance Futures and opens Binance Futures WebSocket streams. Its `fetchCandles()` is consumed by `ChartMarketSession.kt` (blob `bfbf52e58358afa9f0c610aaa2496ed81f4cd8ac`) and `ScannerMarketFeed.kt` (blob `413f50b0996c219f0ebdcd185dcc835632539d2c`). Thus the Android market/chart/scanner path is not proven to consume T0 canonical Candle API.
- `FiveLayerApi.kt` blob `91c9ce61a14dc54a2e2bf1b47285d5645b3f119e` exposes a distinct configurable `baseUrl` API client with a `candles` route and other five-layer service routes. Its candle decoder enforces a canonical-looking Binance BTCUSDT contract, but the exact deployment URL/server route mapping was not established here. Do not assume this endpoint is `market_data.api /v1/candles`.
- `freqai_bridge/http_candles.py` blob `eb9aeccdf381e8a2ebc3450a7a31ae4e9da164ac` calls `/v1/candles`; `freqai_bridge/context.py` uses `CandleHttpClient`. This is the confirmed Python T2 HTTP consumer path.
- `market_data/README.md` blob `660a2f0f4f88c0de4fa8c1be3c4af96df282de0e` explicitly states the initial T0 store/API has not replaced the direct OKX source of the existing Python bot/backtest or the direct APK source. This matches the Android source inspection.

### Supplemental disposition

| Consumer | Current observed source | Relationship to T0 | Decision |
|---|---|---|---|
| FreqAI bridge | `CandleHttpClient -> /v1/candles` | Confirmed T0 HTTP consumer boundary; deployment runtime still unverified | KEEP |
| Android chart/scanner | `MarketEngine -> Binance Futures REST/WebSocket` | Direct exchange path, not T0 canonical API | PARK migration; do not silently switch |
| Android FiveLayer API | Configurable `baseUrl`, `candles` route | Separate service API; server mapping to T0 not verified | NOT VERIFIED; keep separate |
| Existing Python bot/backtest | README says OKX source remains | Not migrated to T0 in documented baseline | PARK migration; preserve current behavior |

This is a significant architecture gap for any future claim that T0 is the sole canonical source for all app/strategy consumers. Do not alter Android or Python bot source as part of this mapping.

### Scope update

- Repository-wide search is still not complete: static inspection now covers selected Python T0 source, selected workflow files, Android market engine/API consumers, and T0 README declarations.
- The new Android direct-Binance path is positive evidence that at least one app market-data path bypasses T0, not evidence of a defect in T0 itself.
- Runtime endpoint/configuration mapping and live consumers remain NOT VERIFIED.


## Owner-directed retirement candidates — 2026-11-10

The owner has directed that the following legacy consumer paths be placed on the **RETIREMENT CANDIDATE** list for the target architecture. This is a planning/disposition decision only; it does not authorize immediate deletion, disabling, migration, or runtime changes.

| Candidate | Current path evidenced | Target disposition | Preconditions before retirement |
|---|---|---|---|
| Android Chart/Scanner direct market feed | `MarketEngine.fetchCandles()` uses Binance Futures REST; MarketEngine also opens Binance Futures WebSocket streams; `ChartMarketSession` and `ScannerMarketFeed` consume this path | Retire the direct-exchange market-data path and route Chart/Scanner through the approved T0 consumer/API boundary | Map FiveLayer API baseUrl and server route ownership; establish T0 endpoint contract and availability; verify M15/H1 parity, pagination/gaps/as-of semantics, reconnect/background/recovery behavior, scanner/chart regression and rollback |
| Python bot/backtest legacy market-data source | T0 README records that the existing Python bot/backtest still uses OKX directly | Retire the legacy OKX source path and migrate consumers to T0 canonical data | Complete exact-branch call-site/config inventory; identify all bot/backtest entry points and timeframe/symbol assumptions; establish T0 contract mapping; verify historical parity, indicator/signal/backtest reproducibility, failure behavior and rollback |

### Retirement boundaries

- The target is the **legacy consumer/source path**, not blanket deletion of the Android application, Chart/Scanner features, Python bot, backtesting engine, or their unrelated modules.
- Preserve current behavior until replacement paths pass the required tests and receive a separate migration/retirement approval.
- Do not infer that Android FiveLayer API is already routed to `market_data.api /v1/candles`; that deployment mapping remains NOT VERIFIED.
- Do not infer that every Python bot/backtest call site has been inventoried; the OKX dependency is documented, but the repository-wide call graph remains NOT VERIFIED.
- No files, workflows, configuration, runtime, VPS, database, exchange access, or consumer behavior were changed by this decision.

### Status

- Owner direction to list both paths as retirement candidates: RECORDED.
- Dependency closure and replacement design: NOT VERIFIED / OPEN.
- Migration and regression evidence: NOT RUN.
- Actual retirement/deletion: NOT AUTHORIZED by this record.
