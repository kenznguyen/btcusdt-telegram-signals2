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
- Phase22 attestation PR #95: `feature/dual-strategy-phase22-preholdout-attestation-20261031`, current head at this follow-up `7a61c651ff59ea13e48413cabad94953742aafff`, base `b8f120fa0975225e5b7ff6243bd374cbde80b158`.
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

Configuration evidence and provenance reconciliation:
- Historical source commit `082edc082996425f61f48c952be41fb037564103` was inspected through its complete Git tree. It contains:
  - `freqai_bridge/config.okx-research.json`, Git blob `bbccccb8fd6688c8b5b27fa6160b8068f3103f35`, 1,890 bytes. It specifies OKX USDT perpetual, isolated futures, M15, BTC/USDT:USDT, `dry_run=true`, stake 10 USDT, dry-run wallet 1,000 USDT, max_open_trades=1, FreqAI identifier `chart-pro-okx-shadow-v1`, `force_entry_enable=false`, and `initial_state=running`.
  - `freqai_bridge/config.research.json`, Git blob `a777e018f457628150647064119435ce75dc3e29`, 1,730 bytes. It specifies Binance and identifier `chart-pro-shadow-v1`; it is not the config path passed by the Phase13B native research workflow.
- The Phase13B Codemagic workflow at the same source commit explicitly passes `--config-path freqai_bridge/config.okx-research.json` to `quant_system.native_research`. That module allowlists and reads this exact file. This is strong source-level evidence that the OKX candidate config was intended for the frozen-model research job; the workflow/source alone does not prove the actual historical job's runtime-resolved config.
- Important hash semantics: `quant_system/phase13b_freeze.py::_canonical_sha()` hashes canonical JSON objects, not raw config-file bytes. `freqai_bridge/ChartProAuditLightGBMRegressor.py::_capture_phase13b_predict()` constructs the recorded snapshot from the effective Freqtrade `self.config` subset: `freqai`, exchange name, timeframe, `dry_run`, and `force_entry_enable`. The frozen metadata's `config_sha256=c253091852b704c00fa33bd6fceb69fb4d480630da1645e3e35ebea13888bb72` and `freqai_config_sha256=a716c80fbb78b8d4bc8b436136912e93e6988a8cdf8d7d1945e8f512bcd6d852` are therefore effective-runtime-object hashes, not raw file SHA-256 values.
- Raw file SHA-256 inventory (exact retrieved bytes): OKX config `81229b2321adc1345735e476051dec3e9df6065944b2cff6d5cb8dbad8a41e7d`; Binance config `3e2aa8a4f131b21b54ff7e7019666b7f054434b10465e53c95f983c62c53cef6`. These values are not directly comparable to the metadata's canonical runtime-object hashes.
- Reconstructing the metadata hashes requires the pinned Freqtrade 2026.9 configuration loader and the effective `self.config` object (or the original run's captured config evidence). That runtime reconstruction has not been performed. The effective runtime config hash is **NOT VERIFIED**.
- `requirements-freqai.txt` at the same source commit pins `freqtrade[freqai]==2026.9`. The historical OKX candidate contains `live_retrain_hours=1` and `initial_state=running`; do not start this config or a FreqAI process as part of F0/F1. No configuration was executed or modified.
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
6. Writes into a new dataset-specific directory using the Freqtrade 2026.9 futures layout `futures/BTC_USDT_USDT-<timeframe>-futures.json`; refuses to overwrite existing exports and rejects symlinked output roots.
7. Writes a provenance manifest with source payload hash, T0 dataset version, output hash, row count, time range and the float64 conversion boundary.
8. Explicitly records `existing_okx_shadow_model_compatible=false`, `strategy_core_modified=false`, `native_orders_enabled=false`, `ai_execution_enabled=false` and `runtime_integration=false`.

The adapter does not make HTTP requests, import/open a T0 database, modify Freqtrade config, replace existing market data, or start a strategy. Pair-to-filename conversion and futures subdirectory placement were checked against the pinned upstream Freqtrade 2026.9 `IDataHandler`, `JsonDataHandler` and `misc.pair_to_filename` implementations.

## F1 — pinned Freqtrade 2026.9 loader source verification

Pinned upstream source was inspected read-only at tag `2026.9`:
- `freqtrade/data/history/datahandlers/jsondatahandler.py`, blob `baed3e9d9e6bef1be6f1337d22735e31cf20a039`: `JsonDataHandler._ohlcv_load()` uses the same `_pair_data_filename()` lookup, reads positional JSON rows with `pandas.read_json(..., orient="values")`, normalizes positional columns, applies candle dtypes and converts the first field from Unix milliseconds to UTC dates.
- `freqtrade/data/history/datahandlers/idatahandler.py`, blob `e5429c04d4f5f7963e558c2aea15f029edc52376`: non-spot candle types resolve below the `futures/` directory and use the `-{candle_type}` filename suffix.
- `freqtrade/misc.py`, blob `065321bafefec14780aa3549831a30a95bf9662b`: `pair_to_filename()` replaces slash and colon with underscores; `BTC/USDT:USDT` therefore maps to `BTC_USDT_USDT`.
- This confirms the adapter's intended six-value OHLCV row layout and `futures/BTC_USDT_USDT-15m-futures.json` / `...-1h-futures.json` naming against the pinned source implementation.
- Boundary: this is source-level compatibility verification only. The Freqtrade package was not installed or invoked, and no `list-data` or `JsonDataHandler` runtime test was run. Actual T0 export remains blocked while T0 is PAUSED.

## Verification status

| Item | Status | Evidence / limitation |
|---|---|---|
| F0 pinned Freqtrade version and strategy source inspection | PARTIAL PASS | Version pin and strategy source inspected on the Phase22 branch |
| Frozen model identity and hashes | PASS — metadata scope only | Exact hashes and model ID read from preserved metadata; no model bytes loaded |
| Historical config path | SOURCE-VERIFIED CANDIDATE | Phase13B workflow passes `freqai_bridge/config.okx-research.json` to native research at source SHA `082edc0`; actual runtime config object hash not reproduced |
| Effective frozen Freqtrade/FreqAI config hash | NOT VERIFIED | Metadata hashes canonicalized effective `self.config`; pinned Freqtrade loader/runtime object not reconstructed |
| T0 published schema and read-only semantics | PASS — documentation/source scope | T0 README, store and API inspected on T0 branch |
| Actual T0 candle comparison | BLOCKED | T0 remains PAUSED; no DB or snapshot opened |
| F1 offline exporter contract | PASS — exact PR head | Run `42310673116`, job `128211020242`; checked-out SHA equals PR head `d43b34348225629eb6b783f7c4c655301e108a72`; compile PASS; 10/10 tests PASS |
| GitHub Actions F1 workflow | PASS — exact PR head | Run `42310673116`; preflight PASS; artifact `13548780012`, SHA-256 `35a1a7fda37ead44cf440d819471242c39caa96807d63c94abb2fc4b2e22cf8d`; downloaded ZIP hash independently matched GitHub metadata |
| Existing backtest/model preservation | NOT MODIFIED | No backtest, model, strategy, config or existing evidence file changed in this increment |
| Runtime integration | NOT AUTHORIZED / NOT RUN | T0 remains PAUSED; adapter is offline only |

## Exact source and commits

Branch: `feature/dual-strategy-phase22-preholdout-attestation-20261031`

- Initial contract-test scaffold (added before adapter implementation): `4e6d3a255b47027cb98e8ef7025b3e5f98370028`.
- F1 GitHub Actions workflow: `c33bb8f89e830ad09dac2edaa1b769363e2882d6`.
- Adapter implementation: `468569f49120db87223e78e7723bcd857b5f7979`.
- Adapter create-race safety fix: `a316a7f7b86dc81d19d82a826ab4e2b816d92227`.
- F1 Freqtrade futures-layout correction: `ddcbd5a2e746066f2fd3c0550f36829b5eb6ca04`.
- F1 strict source/output validation: `debdc05d9085e59697bc4671b3bad6e0b3c0b5ce`.
- F1 symlink-output regression: `4ed5209a723029b59bd2f6593991fbf1a379009e`.
- F1 exact-head verification source: `d43b34348225629eb6b783f7c4c655301e108a72` (run `42310673116`).
- F0/F1 audit report commit: `bf244e34137321adc98ae510e4a6d298d4eabcb3` (initial report; follow-up config reconciliation recorded in this update).

Earlier run `42310599932` tested the synthetic merge SHA `18a31f6bfd0d7703995334cb0e20fd6fc26c2470` and is not treated as direct-head evidence. The later run `42310673116` explicitly checked out the PR head SHA. Its artifact ZIP was downloaded and independently hashed; local SHA-256 matched the GitHub artifact digest. No live T0 data or Freqtrade runtime was involved. Upstream format references: [Freqtrade 2026.9 IDataHandler](https://github.com/freqtrade/freqtrade/blob/2026.9/freqtrade/data/history/datahandlers/idatahandler.py), [JsonDataHandler](https://github.com/freqtrade/freqtrade/blob/2026.9/freqtrade/data/history/datahandlers/jsondatahandler.py), and [pair_to_filename](https://github.com/freqtrade/freqtrade/blob/2026.9/freqtrade/misc.py). The source has exact-head Actions contract evidence. Data acceptance remains blocked until the adapter is tested against a real, user-authorized T0 export and Freqtrade's installed 2026.9 JSON loader.

## Next permitted steps

1. Recover original run evidence containing the effective Freqtrade `self.config` snapshot, if available, and independently recompute both metadata hashes.
2. Otherwise obtain explicit approval to add an isolated GitHub Actions job that installs only the pinned `freqtrade[freqai]==2026.9` package, loads the historical OKX config without connecting to an exchange or starting a strategy, and records the effective config hashes.
3. Use that same disposable CI environment to validate an adapter-generated synthetic fixture through the actual Freqtrade 2026.9 JSON loader / `list-data`; no T0 database or Feeder access is needed for this synthetic format test.
4. When T0 is explicitly resumed and a canonical snapshot is made available, export a bounded M15/H1 window and run the adapter offline. Do not start T0 merely to satisfy this audit.
5. Verify source payload hash, datasetVersion, row counts, full coverage, output hash and Freqtrade JSON parsing on the exact source SHA.
6. Keep Binance export isolated from the existing OKX frozen-model research path.
7. Only after these gates pass, separately propose any runtime read-only integration. No strategy, model, T1, risk, paper execution or live-order changes are implied.
