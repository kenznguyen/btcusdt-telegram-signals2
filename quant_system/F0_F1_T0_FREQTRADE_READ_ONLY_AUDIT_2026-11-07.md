# F0/F1 — T0 to Freqtrade Read-Only Integration Audit

Date: 2026-11-07 (Asia/Ho_Chi_Minh)

## Scope and safety

F0 is a read-only source/configuration audit. F1 is an offline snapshot adapter only.

- No T0 database was opened or created.
- No T0 Feeder, scheduler, API server, exchange connection, market-data sync, or runtime service was started.
- No Freqtrade backtest, model training, tuning, OOS evaluation, or strategy execution was run.
- No existing backtest artifact, frozen model, Strategy Core rule, or risk parameter was modified.
- Native Freqtrade entry flags remain disabled; `confirm_trade_entry` remains false.
- `AI_EXECUTION_ENABLED=false`; no live or paper order execution was enabled.

## F0 — observed Freqtrade state

Repository: `kenznguyen/btcusdt-telegram-signals2`

Relevant source line:
- Phase22 frozen-model PR #94: `feature/dual-strategy-phase22-frozen-reproducibility-20261031`, head `b8f120fa0975225e5b7ff6243bd374cbde80b158`.
- Phase22 attestation PR #95: `feature/dual-strategy-phase22-preholdout-attestation-20261031`, current head at this report `b9582b3fd3c225c090a74d0a3147fc67f1e69f3a`, base `b8f120fa0975225e5b7ff6243bd374cbde80b158`.
- Both PRs remain Draft; neither is merged.

Observed pinned runtime and model provenance:
- `requirements-freqai.txt` pins `freqtrade[freqai]==2026.9`.
- FreqAI strategy is `ChartProFreqaiResearch`, timeframe M15, pair `BTC/USDT:USDT`; native `enter_long/enter_short` are zero and `confirm_trade_entry` returns false.
- Core parity strategy is `ChartProParityDryRun`, M15 with H1 informative data, futures research mode, 13x maximum leverage, native entry flags zero and `confirm_trade_entry` false.
- Frozen model identifier: `chart-pro-okx-shadow-v1`.
- Frozen bundle SHA-256: `918dc4737ee432df8f7f9d2c3e561ac3983aaf56d8791a731a55624ab836b81f`.
- Original source commit bound by model metadata: `082edc082996425f61f48c952be41fb037564103`.
- Frozen model metadata config hash: `c253091852b704c00fa33bd6fceb69fb4d480630da1645e3e35ebea13888bb72`.
- Frozen model metadata FreqAI config hash: `a716c80fbb78b8d4bc8b436136912e93e6988a8cdf8d7d1945e8f512bcd6d852`.
- Feature schema: 20 ordered columns.
- Frozen prospective holdout protocol: 2026-11-04T00:00:00Z through 2026-12-04T00:00:00Z. Phase22 keeps retraining, tuning, OOS certification, AI promotion and live orders disabled.

Configuration evidence limitation:
- The frozen-model metadata preserves hashes for the original Freqtrade and FreqAI configs, but the corresponding complete config files were not found at the expected tracked paths in the inspected Phase22 branch.
- Therefore the exact current effective exchange, data directory, pairlist, candle source, fee/funding settings and runtime overrides are **NOT VERIFIED**. A config digest is not a substitute for inspecting the configuration bytes.

## F0 — T0 comparison

T0 canonical contract (from `market_data/README.md` and `market_data/store.py`):
- Binance USD-M perpetual BTCUSDT.
- M15 and H1 only.
- Read contract returns decimal strings, closed-candle state, first-observed availability timestamp, validated quality, source `ccxt.binanceusdm`, coverage/gaps and `datasetVersion`.
- T0 API is read-only; it does not create a missing database, collect data during a request, or call the exchange.
- The T0 documentation explicitly states that it has not replaced the existing OKX source used by the Python bot/backtest.

Critical incompatibility:
- T0 canonical venue is Binance USD-M.
- The preserved Phase22 model is explicitly named and registered as an OKX shadow model.
- A Binance T0 dataset must not be substituted into the existing OKX model/backtest, nor may the existing OKX dataset be relabeled as Binance.
- A new Binance export may be inspected as a separate Freqtrade dataset, but model compatibility remains false until independently established. No retraining or parameter changes are part of this task.

Data availability:
- T0 remains PAUSED.
- No canonical T0 database or actual T0 candle snapshot was opened or supplied during this audit.
- Consequently, real candle-by-candle parity, row counts, actual gap coverage, dataset hashes and timestamp availability against T0 are **NOT VERIFIED**. This report compares the published data contract and model provenance only.

## F1 — implementation

Added on the existing Freqtrade Phase22 attestation branch, without changing T0 source:
- `quant_system/t0_freqtrade_adapter.py`
- `quant_system/test_t0_freqtrade_adapter.py`
- `.github/workflows/f1-t0-freqtrade-adapter.yml`

Adapter behavior:
1. Reads a saved T0 `/v1/candles` JSON response from a local file only.
2. Validates Binance / USDT_PERPETUAL / BTCUSDT identity and M15/H1 timeframe.
3. Recomputes and verifies T0 `datasetVersion`.
4. Requires complete coverage, no gaps/overlaps, contiguous closed candles, validated quality, first-observed availability and optional `asOfMs` compliance.
5. Validates decimal OHLCV and OHLC bounds before conversion to Freqtrade float64 JSON rows.
6. Writes into a new dataset-specific directory and refuses to overwrite an existing export.
7. Writes a provenance manifest with source payload hash, T0 dataset version, output hash, row count, time range and the float64 conversion boundary.
8. Explicitly records `existing_okx_shadow_model_compatible=false`, `strategy_core_modified=false`, `native_orders_enabled=false`, `ai_execution_enabled=false` and `runtime_integration=false`.

The adapter does not make HTTP requests, import/open a T0 database, modify Freqtrade config, replace existing market data, or start a strategy. Pair-to-filename conversion and futures subdirectory placement were checked against the pinned upstream Freqtrade 2026.9 `IDataHandler`, `JsonDataHandler` and `misc.pair_to_filename` implementations.

## Verification status

| Item | Status | Evidence / limitation |
|---|---|---|
| F0 pinned Freqtrade version and strategy source inspection | PARTIAL PASS | Version pin and strategy source inspected on the Phase22 branch |
| Frozen model identity and hashes | PASS — metadata scope only | Exact hashes and model ID read from preserved metadata; no model bytes loaded |
| Full effective Freqtrade/FreqAI config | NOT VERIFIED | Config files absent from inspected tracked paths; only digests available |
| T0 published schema and read-only semantics | PASS — documentation/source scope | T0 README, store and API inspected on T0 branch |
| Actual T0 candle comparison | BLOCKED | T0 remains PAUSED; no DB or snapshot opened |
| F1 offline exporter implementation | IMPLEMENTED / NOT TEST VERIFIED | Source and tests committed; no runtime invocation |
| GitHub Actions F1 workflow | ADDED / NOT VERIFIED | Workflow file committed; no matching workflow run ID, checked-out SHA, job result or artifact evidence was retrieved |
| Existing backtest/model preservation | NOT MODIFIED | No backtest, model, strategy, config or existing evidence file changed in this increment |
| Runtime integration | NOT AUTHORIZED / NOT RUN | T0 remains PAUSED; adapter is offline only |

## Exact source and commits

Branch: `feature/dual-strategy-phase22-preholdout-attestation-20261031`

- Initial RED contract test: `4e6d3a255b47027cb98e8ef7025b3e5f98370028`.
- F1 GitHub Actions workflow: `c33bb8f89e830ad09dac2edaa1b769363e2882d6`.
- Adapter implementation: `468569f49120db87223e78e7723bcd857b5f7979`.
- Adapter create-race safety fix: `a316a7f7b86dc81d19d82a826ab4e2b816d92227`.
- Current branch head when this report was updated: `4ed5209a723029b59bd2f6593991fbf1a379009e`.

No GitHub Actions run ID or artifact is claimed. Upstream format references: [Freqtrade 2026.9 IDataHandler](https://github.com/freqtrade/freqtrade/blob/2026.9/freqtrade/data/history/datahandlers/idatahandler.py), [JsonDataHandler](https://github.com/freqtrade/freqtrade/blob/2026.9/freqtrade/data/history/datahandlers/jsondatahandler.py), and [pair_to_filename](https://github.com/freqtrade/freqtrade/blob/2026.9/freqtrade/misc.py). The source is not ready for acceptance until exact-head Actions evidence is retrieved and the adapter is tested against a real, user-authorized T0 export.

## Next permitted steps

1. Obtain the exact effective Freqtrade/FreqAI config bytes from the preserved historical research environment or its archived evidence; inspect without changing them.
2. When T0 is explicitly resumed and a canonical snapshot is made available, export a bounded M15/H1 window and run the adapter offline. Do not start T0 merely to satisfy this audit.
3. Verify source payload hash, datasetVersion, row counts, full coverage, output hash and Freqtrade JSON parsing on the exact source SHA.
4. Keep Binance export isolated from the existing OKX frozen-model research path.
5. Only after these gates pass, separately propose any runtime read-only integration. No strategy, model, T1, risk, paper execution or live-order changes are implied.
