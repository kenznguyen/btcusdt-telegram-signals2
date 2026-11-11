# G0.8-B — T0 → T1 → T2 Data Contract Mapping (2026-11-11)

## Scope

Owner-approved read-only mapping of the implemented data paths and contracts across T0, T1 and T2. This is a source/documentation review only. No source, test, workflow, configuration, runtime, database, VPS, market-data, training or trading changes were made.

## Exact source identities

### T0/T2 repository
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Reviewed HEAD: `43ba5a917f162dd5060bfd49bc57a89a9f1d88d8`
- `market_data/api.py` blob: `81733c9b6de811cbebb2f5d472d41f37f337990c`
- `market_data/store.py` blob: `4e1b0c54bd56455abe5be0e5c7d0807e63e0bc78`
- `market_data/storage.py` blob: `13fe1ae01ebb5318b69e69eef3e512d207f74c49`
- `market_data/sync.py` blob: `e7ad4e6f2074225957b01f74abb0befe37675ea2`
- `freqai_bridge/context.py` blob: `9abe781340dc9b948c40c759d92f340da3e372c1`
- `freqai_bridge/http_candles.py` blob: `eb9aeccdf381e8a2ebc3450a7a31ae4e9da164ac`
- `freqai_bridge/exporter.py` blob: `3b707174316d0c6b464ac947cbbe2d2fbee73682`
- `futures_intelligence/import_collector.py` blob: `5effe6540b86edcb190456c95b6bb11456aec099`
- `pipeline/decision.py` blob: `e718756b415fc193a486900e7b84c2cf05e6a091`

### T1 repository
- Repository: `kenznguyen/binance-futures-collector`
- Branch: `feature/t1-connection-sidecar-integration-20261107`
- Reviewed HEAD: `f3bae0cfbc26aa694a4d6c9476965121818d3567`
- `config.example.toml` blob: `3436a8b75dc827a9299c083e9af783c8a74196c3`
- `src/config.rs` blob: `e07fd601986d7a8db18109e3179937579c425f98`
- `src/constants.rs` blob: `0bf50b5fe02f4f196b38481cde6ecab9e2adb941`
- `src/collectors/orderbook_manager.rs` blob: `5a28fbaff606d41c11264aad176113d41a1e33ae`
- `src/utils/csv_writer.rs` blob: `0a4455134de9b353b4a7c25ffc6f0a252ca2c5a0`
- `crates/connection-sidecar/README.md` blob: `43806ca013aa1b8b8784fd29805dac677729aa12`

## 1. T0 — canonical candle source and consumer boundary

T0 ingests Binance USD-M BTCUSDT perpetual OHLCV through CCXT (`binanceusdm`). Its canonical candle model supports only M15 and H1, stores closed candles with UTC millisecond open/close/availability timestamps, validated OHLCV decimal strings, `FIRST_OBSERVED` availability and `VALIDATED` quality.

SQLite is the default backend. PostgreSQL is opt-in and is not certified as the active canonical backend. T0 is an independent canonical source; no T1 write path into T0's canonical candle store was found in this mapping.

The T0 consumer API is GET-only `/v1/candles`, Bearer-authenticated, with aligned half-open `[startMs,endMs)` windows, optional `asOfMs`, BTCUSDT and M15/H1 support, and up to 2,000 expected candle slots per request. The response includes contract/schema version, candle records, volume unit `BTC_BASE_ASSET`, source `ccxt.binanceusdm`, coverage/gaps, a `datasetVersion` SHA-256 and freshness metadata.

Important limit: `datasetVersion` hashes the exact queried response/window. It is not a whole-dataset bundle manifest, a source-authenticity proof or training provenance. Repository source does not prove a live API endpoint, deployed source parity or current data freshness.

## 2. T1 — raw futures capture

T1 independently connects to public Binance USD-M market-data REST/WebSocket endpoints. Its documented capture types are:
- Order-book depth diffs and snapshots
- Aggregate trades
- 1-minute klines
- Liquidations
- Funding rates
- Open interest
- Long/short ratios
- Mark-price, index-price and premium-index klines
- Taker buy/sell ratios

CSV output is partitioned by data type, lowercase symbol and date. Depth rows include update IDs; trade rows include aggregate trade IDs, side, price and quantity; kline rows include OHLCV, quote volume, trade count and taker-buy volumes. These are T1-native CSV schemas, not the T0 Candle Contract v1 envelope.

The checked-in example configuration still has `symbols = []`, which means all discovered USDT-M perpetuals. A non-empty whitelist restricts collection but bypasses discovery/delisting detection. No BTCUSDT-only runtime configuration has been applied or verified.

The Connection Sidecar remains a standalone offline library, not integrated into the upstream Collector. Its event manifest cannot certify market-data completeness.

## 3. Existing T1 → T2 file-import path

A concrete T1-to-T2 path exists in `futures_intelligence/import_collector.py`. It accepts BTCUSDT CSVs for four streams only:
- trades
- funding rates
- open interest
- liquidations

It validates exact CSV headers, Binance futures/BTCUSDT identity, UTC millisecond timestamps, bounded files/rows/windows, selected-row ranges, file stability during read and SHA-256 for each input file. It creates a bounded, at-most-one-day `OBSERVED_ONLY` intelligence snapshot with per-stream coverage and a content-derived `snapshotId`.

This is a file import, not a direct T1 service/API connection. It does not import T1 order-book data, klines, long/short ratios, mark/index/premium klines or taker ratio into this intelligence snapshot.

The importer deliberately does not claim completeness:
- Each stream has `complete=false`.
- Connection state is `UNVERIFIABLE` because the pinned CSV schema has no connection-evidence fields.
- Trade-ID gaps can be counted, but zero observed gaps does not prove full capture from Binance.
- Liquidations have no event ID in the accepted schema and are not deduplicated by a fabricated ID.

### Critical provenance mismatch

The importer hardcodes:
- `SOURCE_COMMIT = bc4f0ef633fbeee4a49defd72827f17162693805`
- `source = binance-futures-collector@bc4f0ef633fbeee4a49defd72827f17162693805`

That is the T1 branch's recorded merge-base commit, not the reviewed T1 feature branch HEAD `f3bae0cfbc26aa694a4d6c9476965121818d3567`. The accepted CSV headers do not carry a producer commit or signed source identity, so the importer cannot independently prove that supplied CSVs were produced by the pinned source revision.

Disposition: the importer is implemented, but provenance of CSVs generated by the current T1 feature branch is **NOT VERIFIED**. Do not treat the T1 → T2 path as production-ready or source-pinned until this discrepancy is resolved through a separately approved contract change and tests.

## 4. Existing T0 → T2 candle path

T2's `freqai_bridge/context.py` obtains canonical candles through the T0 HTTP API client. The client:
- Supports BTCUSDT M15 only (not H1), 1–32 bars per request.
- Uses Bearer auth; HTTPS is required except loopback HTTP.
- Rejects redirects, bounds response size to 256 KiB, uses 3s connect / 5s read timeouts and at most 3 attempts.
- Retries bounded transient failures and fails closed on other errors.
- Validates exact envelope/candle fields, source and market identity, closed candles, no gaps, timestamps, OHLCV, dataset hash and freshness/ingestion lag.
- Has no SQLite, local-cache, synthetic-data or exchange fallback.

The bridge therefore consumes only a bounded M15 inference window, even though T0's API and canonical store support both M15 and H1. `canonical_context` defaults to two M15 bars and allows at most 32.

The FreqAI exporter binds actual FreqAI dataframe OHLCV rows to the canonical T0 window and requires trainer-supplied training dataset version, model/strategy version, `trainedThroughMs` and completion time. Its artifact contains `predictedReturn` and `doPredict`; it is not itself a standalone LONG/SHORT signal contract or a proof that a scheduled training pipeline has run.

## 5. T2 paper decision path and additional input mismatch

`pipeline/decision.py` accepts four separate inputs: T0 canonical M15 candles, the T1-derived observed intelligence snapshot, a prediction artifact, and an order-book snapshot.

The decision code:
- Fails closed to WAIT if any input is missing or invalid.
- Requires a prediction threshold and agreement between forecast direction and observed taker flow.
- Requires the order-book input to identify source `hummingbot` / connector `binance_perpetual`; it does not consume the T1 CSV order-book output in this function.
- Emits BUY/SELL with a bounded PAPER target-position intent, or WAIT.

This shows a partial paper decision pipeline, not proof of live strategy operation. The inspected decision function uses a default fixed `target_base=0.001` BTC and does not establish that the shared 1%-of-equity margin risk engine, leverage controls, kill switch, or independent Core/AI ledgers are enforced on this path. Those risk gates must be separately traced before this pipeline can be treated as compliant with the Dual-Strategy Intelligence architecture.

The code's BUY/SELL intent vocabulary also needs an explicit mapping to the project's desired LONG/SHORT signal contract. Do not silently equate BUY/SELL with an approved AI LONG/SHORT strategy event.

## 6. End-to-end contract map

| Path | Implemented source boundary | Data scope | What is proved by source review | What remains unproved |
|---|---|---|---|---|
| Binance → T0 | CCXT USD-M sync → canonical store | BTCUSDT M15/H1 candles | Source code supports closed validated candles and coverage/gap reporting | Live source/runtime, deployed parity, current freshness |
| T0 → T2 | Bearer GET /v1/candles → strict HTTP client | M15 only, 1–32 bars | Client validates identity, coverage, quality, freshness and hash | Live endpoint and runtime parity |
| Binance → T1 | REST/WS Collector → CSV | Raw BTCUSDT if explicitly whitelisted; otherwise all discovered USDT-M symbols | Collector code/docs define streams and CSV schemas | BTCUSDT-only runtime, disk rate, sustained capture |
| T1 → T2 | Four CSV streams → importer → observed snapshot | Trades, funding, OI, liquidations | Bounded import, file hashes and observed-only metrics | Current branch producer provenance, stream completeness, live path |
| T1 order book → T2 | No matching path in inspected decision function | T1 depth CSV vs Hummingbot order-book snapshot | T2 expects Hummingbot book identity | T1 order-book substitution/adapter and sequence contract |
| T1 klines → T0/T2 | No matching canonical adapter found | T1 1m vs T0/T2 M15 | Timeframe mismatch identified | Aggregation rules, provenance and canonical ownership |

## 7. Consolidated blockers before VPS sizing

1. Resolve T1 importer producer provenance: the importer pins the merge-base SHA while current T1 branch is a later feature SHA; CSVs do not attest producer SHA.
2. Decide whether T1 remains an auxiliary intelligence source only, or whether any T1 data should feed T0 canonical candles. Preserve T0 independence unless an explicit contract decision changes it.
3. Define the accepted T1 BTCUSDT-only configuration and its delisting/discovery trade-off; measure actual per-stream disk growth before sizing retention/storage.
4. Decide whether T2 should consume H1 as well as M15; current bridge is M15-only.
5. Decide whether T1's order-book stream is to remain separate from the Hummingbot book input or whether a new adapter/contract is needed.
6. Trace and prove Shared Risk Engine, 1% equity margin cap, leverage, Kill Switch and separate Core/AI ledgers on every paper intent path before treating any signal as risk-approved.
7. Freeze FreqAI training data/manifest and training provenance before scheduling training. The candidate immutable `T0_M15_H1_DATASET_BUNDLE_V1` remains NOT VERIFIED; the existing T0 API response hash is not a bundle manifest.

## Review verdict

- Source-level T0/T1/T2 contract mapping: **PASS**.
- T0 canonical source remains independent; no T1→T0 canonical write contract identified.
- T0→T2 read-only M15 HTTP client: **IMPLEMENTED IN SOURCE / LIVE NOT VERIFIED**.
- T1→T2 four-stream CSV import: **IMPLEMENTED IN SOURCE / CURRENT PRODUCER PROVENANCE NOT VERIFIED**.
- T1 sidecar live integration: **NOT IMPLEMENTED**.
- T1→T2 order-book integration: **NOT IDENTIFIED**; T2 expects Hummingbot source.
- H1 consumption by current FreqAI bridge: **NOT IMPLEMENTED IN INSPECTED CLIENT**.
- Shared Risk Engine enforcement on this paper decision path: **NOT VERIFIED**.
- FreqAI scheduled training and immutable training bundle: **NOT VERIFIED / NOT FROZEN**.
- End-to-end T0/T1/T2 runtime: **NOT VERIFIED**.
- Tests/workflows: **NOT RUN** for this read-only mapping.

## Next step

G0.8-C may now size the replacement VPS only after declaring an explicit workload envelope. Use BTCUSDT-only as a planning scenario, not as an applied runtime config. Separate storage budgets for T0 canonical M15/H1, T1 trades/orderbook/other raw streams, T2 model artifacts and logs, and FreqAI training scratch. Treat all disk-rate, RAM and training-time values as estimates until a bounded benchmark is separately approved.

## Non-actions

No code/config/test/workflow change, workflow dispatch, data read/export/copy, API request, token use, SQLite access, exchange connection, VPS provisioning, service start, AI training, strategy activation, order or destructive operation occurred. T0 remains independent. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.
