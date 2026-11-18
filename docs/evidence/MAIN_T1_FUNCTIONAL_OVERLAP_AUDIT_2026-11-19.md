# Main ↔ T1 Functional Overlap Audit — 2026-11-19

## Scope and exact source refs

Read-only static comparison of:
- Main application repository: `kenznguyen/btcusdt-telegram-signals2`, branch `main`, HEAD `719146bda589b567c5ff2784fe0ae31b7fb641b6`.
- T1 collector repository: `kenznguyen/binance-futures-collector`, branch `main`, HEAD `c91a8c22d3b6236c98ab9a4d4d69b25d47f7f738`.

No source, workflow, branch, runtime, collector, VPS, T0 database, exchange or trading state was changed or accessed.

## Executive result

**No exact duplicate source file or drop-in duplicate implementation was established.** One partial functional overlap exists at the Order Book/API presentation boundary, and there is a broader monitoring/quality-observability overlap. Their data sources, consumers, routes and trust contracts differ. Do not delete or replace a main file on the basis of filename or endpoint similarity alone.

## Functional comparison

| Main file / function | T1 file / function | Overlap classification | Finding |
|---|---|---|---|
| `pipeline/api.py`: `book_snapshot()`, `GET /v1/order-book` | `dashboard/backend/server.py`: `_current_book()`, `GET /api/orderbook/{symbol}` | **PARTIAL — same data domain** | Both expose an Order Book snapshot. Main obtains a normalized BTCUSDT snapshot from a server-configured Hummingbot bridge (`integrations.hummingbot_bridge`). T1 Capture Desk reconstructs a book from persisted CSV snapshot + depth-diff files, using float prices/quantities, for dashboard display. Different source, route, response shape, freshness/continuity trust and consumer. Not interchangeable. |
| `pipeline/api.py`: `quality_snapshot()`, `control_readiness()`, `GET /v1/quality`, `GET /health` | `dashboard/backend/server.py`: `/api/health`, `/api/streams`, `/api/coverage`, `/api/health/coverage`, `/api/gaps/{symbol}`, `/api/validate/{symbol}` | **PARTIAL — observability category** | Main quality/readiness aggregates T0 candles, intelligence/model/book and paper/Core readiness. T1 endpoints inspect raw collector process/CSV stream health, coverage, gaps and data invariants. Different layer and responsibility. |
| `pipeline/api.py`: `market_window()`, `context()`, `intelligence_snapshot()` | T1 `src/collectors/rest_collector.rs`, `src/websocket/message_handler.rs`, `src/collectors/orderbook_manager.rs` | **UPSTREAM/DOWNSTREAM — not duplicate** | T1 captures Binance raw trades, klines, depth, liquidations and derivatives metrics to CSV. Main API is designed to read canonical candles through the market-data store and optionally validate an imported intelligence report. A consumer of data is not a second collector. |
| `bot.py`: RSI/ADX indicators, Entry, TP, Smart DCA, stop/fill helpers | T1 Rust collector modules | **NO FUNCTIONAL DUPLICATE** | Main `bot.py` contains strategy rules only. T1 captures and persists market data; no RSI/ADX/Smart-DCA trade-signal engine was found in the inspected T1 collector paths. |
| `ci/test_strategy_rules.py` | T1 `scripts/verify_data.py`, dashboard validation routes/tests | **NO FUNCTIONAL DUPLICATE** | Main tests strategy math and decision rules. T1 validates raw captured dataset files, continuity and stream quality. |
| Main Android `StrategyMonitorService.kt` | T1 Capture Desk React/FastAPI dashboard | **NO FUNCTIONAL DUPLICATE** | Android service is a strategy-monitor/notification surface. T1 dashboard is a collector operations, coverage, validation, export and replay surface. |
| Main `backtest_rsi_percent_b_h1_adx.py` | T1 replay/export/validation | **NO FUNCTIONAL DUPLICATE** | Main script is a strategy research backtest; T1 replay reconstructs historical captured market state. Replay data is not a strategy backtest. |

## T1 Order Book Provider V1 status

T1 has `src/http/orderbook_v1.rs` (blob `1a17f60f3b0a960ac5cb67ddee1dafc57dd718b2`) and module exports in `src/http/mod.rs` / `src/lib.rs`. The publisher validates a BTCUSDT immutable snapshot, sequence watermark, generation, freshness, depth and canonical decimal levels.

However:
- T1's own contract document says **IMPLEMENTED IN PART / PAUSED — no HTTP route or collector runtime integration**.
- `src/main.rs` has no `OrderbookV1Publisher`, HTTP listener/server or provider route reference.
- `src/collectors/orderbook_manager.rs` has no publisher/read-fresh integration.
- The T1 Dashboard's `/api/orderbook/{symbol}` is a separate CSV-reconstruction route; it is not Provider V1.
- Do not add an endpoint, wire the provider, dispatch its workflow, deploy or change T0/T2 as part of this audit. Existing T1 commits remain untouched.

The Core First branch's intended consumer contract (`GET /internal/v1/orderbook/btcusdt`) is documented by T1 as a separate consumer. It must not be conflated with main's `GET /v1/order-book`, which calls the Hummingbot bridge.

## Main-side dependency caveat

The current main tree contains `pipeline/api.py`, but its imports include files not present in the inspected main tree, including:
- `market_data/api.py`, `market_data/storage.py`
- `futures_intelligence/import_collector.py`
- `integrations/hummingbot_bridge.py`
- `paper_execution/ledger.py`
- `pipeline/decision.py`, `pipeline/values.py`

Therefore the static API overlap above describes code intent only. Runtime availability of the main API and its Order Book route is **NOT VERIFIED** from this main snapshot. Missing imports are a separate dependency-integrity issue, not proof that the file duplicates T1 or permission to delete it.

## Evidence pointers

Main:
- `pipeline/api.py` blob `b6f017f603fecd242ba47a83fff387f8594bca2e`
- `bot.py` blob `d68d66fc39f49b5ac633ece8e4f5caf94f336b83`
- `StrategyMonitorService.kt` blob `4a3a1abea3d0fdf371f884867beed325a8b861b5`

T1:
- `src/collectors/orderbook_manager.rs` blob `d18d047c1f7cdddd03cea60b02de54b656ad4edf`
- `src/http/orderbook_v1.rs` blob `1a17f60f3b0a960ac5cb67ddee1dafc57dd718b2`
- `src/main.rs` blob `d3cde50a9fb761a1d6ef711a5a04cbbda359f3ed`
- `src/http/mod.rs` blob `8072db7b25198c8b9063e837aee775a5ecaf39a0`
- `src/lib.rs` blob `c16d25102a89f37e90db63b094504d615b6f566e`
- `dashboard/backend/server.py` blob `1bfc322d9868f5eda7a2d9152575fb22b547093d`
- `src/collectors/rest_collector.rs` blob `1a24b0b70737eee74f271bf39bc21a80d06d5cf5`
- `src/websocket/message_handler.rs` blob `7d7f221fbf4b31470049baea55584645352f61b7`
- `scripts/verify_data.py` blob `3ecd3306f46b9a40022cd5afbb2a4035e83cb888`
- `docs/T1_ORDERBOOK_HTTP_PROVIDER_V1_CONTRACT_AND_RED_PLAN.md` blob `fcf45baff1707aa839f6294493e963b1e774c6e8`

## Status and next step

- Targeted file inventory and functional comparison: **PASS (static)**.
- Exact duplicate files established: **NONE**.
- Partial overlap: main `pipeline/api.py` vs T1 Dashboard orderbook/health endpoints; separate data and trust contracts.
- Main API runtime/dependency completeness: **NOT VERIFIED** due absent imports listed above.
- T1 Provider runtime activation: **PAUSED / NOT INTEGRATED**.
- Tests, runtime parity, full dynamic caller scan and independent review: **NOT RUN / NOT VERIFIED**.
- No source/workflow/branch/runtime change. T1 repository is unchanged.

Recommendation: retain current main files for now. Do not delete `pipeline/api.py` or strategy helpers as duplicates. If a future integration is approved, define one explicit Order Book provider/consumer contract and assign a single owner for snapshot publication; keep T1 raw capture, T0 canonical candles and Strategy Core as distinct responsibilities.
