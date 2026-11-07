# T0–T2 Compatibility Audit — 2026-11-07

## Scope

Read-only source audit of:
- T0 branch: `feature/t0-centralized-data-feeder-p1-20261101`
- T0 source HEAD before this documentation update: `b1a3daec797ab92280a95bee54aacede7cc40a57`
- T2 branch: `feature/freqtrade-strategy-parity-20261029`
- T2 source HEAD inspected: `4c039411542e11e073615a52d5a50d4ca605b49a`

No branch merge, code modification, workflow execution, database creation/opening, schema migration, ingestion, exchange connection, Feeder startup, VPS provisioning, or execution was performed.

## Source inventory

T0:
- `market_data/store.py`, blob `2b47b7a29b2407651515a3cabfda6045ff4386b4`.

T2:
- `market_data/store.py`, blob `5bc0543e3074fd66b9025289b34864e23612c702`.
- `freqai_bridge/README.md`, blob `9cbe44a60a880e7a5ccd10266c2353a5dbf409e0`.
- `freqai_bridge/config.research.json`, blob `a777e018f457628150647064119435ce75dc3e29`.
- `freqai_bridge/context.py`, blob `6df3606df8ab34366bfe3abdb77a83574b76e7b1`.
- `freqai_bridge/exporter.py`, blob `3b707174316d0c6b464ac947cbbe2d2fbee73682`.
- `freqai_bridge/ChartProFreqaiResearch.py`, blob `c24a1d75523c907fde08cfe6cfe509312593e849`.
- `freqai_bridge/test_exporter.py`, blob `81fcd9bb3823899be50e20f671696ea9812fcfe7`.
- `pipeline/decision.py`, blob `66f94d96604a31979e8cec0a983f840aea63cbe4`.
- `pipeline/test_decision.py`, blob `38e158584befd48aed95cc780fc7c8e43cd30ab3`.

## Findings

### 1. Read contract and schema

**CONDITIONAL PASS — source-level compatibility.**

Both store implementations use the same `candles` table columns and primary key:
`exchange, market_type, symbol, timeframe, open_time_ms`; OHLCV and availability timestamps are stored as decimal/text and integer UTC milliseconds respectively. The T0 and T2 readers agree on the BTCUSDT Binance USD-M market identity, M15/H1 interval mapping, half-open time windows, closed-candle validation and deterministic dataset hash structure.

The `read_window()` implementation in both branches opens SQLite with URI `mode=ro`. T2's `canonical_context()` calls only `read_window()`, checks complete coverage and verifies `availableAtMs <= now`. The T2 prediction exporter compares actual FreqAI dataframe candle times and OHLCV against the canonical window. The decision pipeline independently validates canonical coverage and recomputes the dataset identity.

This is a source-code inspection result, not a runtime proof against a real canonical database.

### 2. Writer/API divergence

**BLOCKED — existing T2 test fixtures are not directly compatible with the T0 branch.**

T2's `market_data/store.py` contains `CandleStore.insert()`; the T0 version no longer exposes that method. T2 tests `freqai_bridge.test_exporter` and `pipeline.test_decision` currently construct temporary data by calling `CandleStore(path).insert(...)`. Running those fixtures unchanged with T0's store module will fail before testing the consumer contract.

Do not restore a direct writer to T0 merely to satisfy T2 tests. Adapt tests to use an isolated test-only fixture writer or the T0 single-writer gateway against a temporary database. The production consumer must retain read-only access.

### 3. Consumer write boundary

**CONDITIONAL PASS — source-level only.**

- T2 context reads through T0 `read_window()`; no store initialization or insert call is made by this path.
- T2 decision evaluation is an in-memory validation/decision function.
- T2 exporter writes an atomic JSON prediction artifact to its configured output path; this is not a write to the T0 database.
- The Freqtrade strategy calls `self.freqai.start()` and publishes the JSON artifact in dry-run mode. The strategy sets native entry/exit flags to zero and `confirm_trade_entry()` returns false.

No runtime filesystem observation or before/after SQLite hash/schema/row-count test has been run. Therefore the actual read-only property remains NOT VERIFIED at runtime.

### 4. Freqtrade/FreqAI runtime

**NOT VERIFIED.**

T2 README and configuration document target version Freqtrade/FreqAI 2026.9 and set `dry_run=true`, pair `BTC/USDT:USDT`, timeframe `15m`, and canonical DB path `.data/market-data.sqlite3`. This is a documented target, not evidence that 2026.9 is installed or that strategy loading succeeds in the current environment.

The configured path is an operator setting/example. It does not prove that a canonical SQLite file exists. User has confirmed that the canonical file is NOT CREATED.

### 5. Binance versus OKX parity

**NOT RUN / NOT VERIFIED.**

The inspected FreqAI research config explicitly selects Binance USD-M. No identical, bounded Binance/OKX dataset pair or parity artifact was inspected in this audit. Exchange candles are not expected to be identical. No source switch, normalization, or OKX replacement is approved.

### 6. CI status

No GitHub Actions workflow was run in this audit. The T2 branch contains a `codemagic.yaml` change in its current head; this is not authorization to use Codemagic. Future verification must use GitHub Actions, consistent with the project rule. Workflow availability and exact-head test coverage still need a dedicated inspection before execution.

## Acceptance matrix

| Gate | Result | Evidence boundary |
|---|---|---|
| T0/T2 candle table schema | CONDITIONAL PASS | Static source comparison |
| Market/timeframe/timestamp contract | CONDITIONAL PASS | Static source comparison |
| T2 uses T0 read_window | PASS (source inspection) | No runtime DB access |
| T2 DB writes absent from consumer path | CONDITIONAL PASS | JSON artifact write is separate; runtime DB immutability not tested |
| Existing T2 tests on exact combined source | NOT RUN | Fixture writer API mismatch found |
| Test fixture compatibility | BLOCKED | T2 tests call removed T0 `CandleStore.insert()` |
| Freqtrade/FreqAI 2026.9 installed | NOT VERIFIED | Documentation/config only |
| Freqtrade strategy-load smoke test | NOT RUN | No runtime invocation |
| Binance/OKX parity | NOT RUN | No paired dataset/report |
| Canonical SQLite file | NOT CREATED | User-confirmed |
| Canonical ingestion / Feeder | NOT RUN / STOPPED | Not authorized |
| Live execution | DISABLED | `ai_execution_enabled=false` |

## Required next steps

1. Add a temporary-database fixture path compatible with the T0 single-writer design; do not add a production writer to the T0 consumer API.
2. Add a regression that snapshots the temporary DB's schema, row count and file/database identity before and after T2 context + exporter execution, proving no T0 mutation.
3. Run `freqai_bridge.test_exporter` and `pipeline.test_decision` against a combined source checkout pinned to both exact branch SHAs. Use only temporary SQLite fixtures.
4. Inspect GitHub Actions workflow inventory and add/extend a GitHub Actions-only exact-SHA job if required. Do not use Codemagic absent a documented GitHub Actions blocker and explicit authorization.
5. Verify Freqtrade/FreqAI 2026.9 in an isolated environment and run strategy-load smoke test without exchange sync, credentials, or orders.
6. Build a bounded Binance-vs-OKX parity report only after both datasets and their provenance are available.

## Safety and disposition

- T0 remains the owner of canonical data and the single-writer boundary.
- T2 remains a read-only consumer of T0.
- Existing OKX research/backtest source remains unchanged.
- No merge or source switch.
- Canonical SQLite remains NOT CREATED; ingestion NOT RUN; Feeder STOPPED; VPS NOT PROVISIONED.
- `ai_execution_enabled=false`; no live orders or exchange execution.
- Overall audit verdict: **CONDITIONAL / BLOCKED FOR RUNTIME ACCEPTANCE**.
