# T0 → T2 OHLCV adapter plan — 2026-11-07

## Purpose

Define a safe, independently testable read-only adapter from T0 SQLite Canonical market data to the T2 Freqtrade/FreqAI research pipeline. This is a design and implementation plan only. It does not authorize canonical database creation, schema migration, ingestion, Feeder startup, changing T2's current OKX source, or live execution.

## Current verified boundary

- T0 store supports Binance USD-M BTCUSDT perpetual OHLCV at 15m and 1h.
- Candle records contain UTC open/close timestamps, decimal-string OHLCV, first-observed availability timestamp, source and quality metadata.
- Read API exposes coverage/gaps and a deterministic `datasetVersion`.
- Missing intervals are not silently forward-filled; API can return HTTP 200 with `coverage.complete=false`.
- SQLite is the approved canonical backend for the current PC-first phase, but the user confirmed the canonical SQLite file does not yet exist.
- Isolated temporary SQLite tests are permitted. No canonical file or production data may be created or written in this work item.
- T0 acceptance evidence: source SHA `1aac449b96c4079004e1cab882280b923e33342c`; GitHub Actions run [42329799499](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42329799499) SUCCESS. This proves isolated acceptance behavior, not a live canonical dataset.

## Adapter boundary

The future adapter must:

1. Open the configured T0 SQLite file in read-only mode (or call the authenticated read-only T0 API); it must never initialize schema or invoke a writer.
2. Request one explicit symbol/timeframe/UTC half-open window `[startMs,endMs)`.
3. Validate response identity: exchange Binance, market type USDT perpetual, symbol BTCUSDT, requested timeframe and exact requested window.
4. Require `coverage.complete=true`, expected candle count equal returned count, no gaps, strictly increasing unique open timestamps, and every candle marked closed and validated.
5. Preserve source provenance and datasetVersion in a sidecar manifest. Do not inject provenance columns into Freqtrade's OHLCV frame unless T2 explicitly defines them.
6. Convert decimal strings to numeric values only at the export boundary, using deterministic Decimal conversion and rejecting non-finite/overflow values.
7. Export to a staging path, verify the exported row count and timestamp range, then atomically publish the output. Never overwrite an existing dataset silently.
8. Keep T2's current OKX source and backtest configuration unchanged until parity acceptance is approved.
9. Have no network access to an exchange, no credential handling, no order/execution capability, and no write access to T0.

## Freqtrade compatibility must be established before implementation

Do not guess Freqtrade's filename, pair naming, timeframe encoding, futures suffix, or storage format. First pin the exact Freqtrade version and configuration used by this repository's T2 research workflow. Then add a compatibility fixture generated or validated by that exact version.

The adapter should initially support only BTCUSDT and the already supported 15m/1h timeframes. Additional pairs/timeframes require a separate contract change.

## Required tests (TDD)

### Unit tests
- Reject incomplete coverage, gaps, duplicate or out-of-order timestamps.
- Reject wrong exchange, market type, symbol, timeframe, or window boundaries.
- Reject unclosed, invalid-quality, malformed decimal, non-finite and invalid OHLCV values.
- Preserve exact timestamp semantics and source metadata in the manifest.
- Produce deterministic output for the same input and pinned exporter version.
- Refuse overwrite and clean up failed staging output.

### Integration tests
- Use a fresh temporary SQLite database only.
- Prove the adapter opens the source read-only: source hash/schema/row count unchanged before and after export.
- Verify exact exported row count, first/last timestamps and OHLCV values against the source.
- Validate output with the pinned Freqtrade version, not a hand-written approximation.
- Compare a bounded identical time window against the current OKX T2 dataset. Differences must be reported; do not silently normalize exchange differences.
- Keep missing intervals as a hard failure; no forward-fill or synthetic candles.

### Acceptance gates
- T0 source remains unchanged and read-only.
- T2 existing source/config remains unchanged.
- Export is reproducible and manifest records T0 datasetVersion, source identity, time window, timeframe, exporter version and output hash.
- Exact Freqtrade compatibility test passes.
- Source parity report exists and explicitly classifies differences.
- GitHub Actions passes on the exact source SHA.
- No live exchange, canonical DB, Feeder, VPS or execution is involved.

## Implementation sequence

1. Inventory the active T2 strategy/config/workflow and pin the exact Freqtrade version and data format.
2. Add failing tests for the adapter contract (RED).
3. Implement a minimal read-only exporter (GREEN).
4. Run focused adapter tests, then relevant T0 and T2 regression suites.
5. Add GitHub Actions workflow using synthetic temporary SQLite fixtures only.
6. Review exact-SHA CI results and record artifacts, source/output hashes and limitations.
7. Only after parity acceptance, propose a separate approval to use T0 as an additional T2 research input. Do not replace OKX by implication.

## Current status

- Adapter design: READY FOR IMPLEMENTATION.
- Exact T2 runtime/version/config inventory: NOT VERIFIED.
- Freqtrade output format compatibility: NOT VERIFIED.
- Adapter code/tests: NOT STARTED.
- T0 Canonical SQLite file: NOT CREATED (user-confirmed).
- Canonical ingestion: NOT RUN.
- Feeder: STOPPED.
- VPS: NOT PROVISIONED.
- Live execution: DISABLED (`ai_execution_enabled=false`).

## Next action

Inspect the active branch's T2 strategy, FreqAI config, dependency pins and GitHub Actions workflow. Record exact version and data-format evidence before writing adapter code. If these assets are not present on this branch, stop and identify the authoritative T2 branch/revision rather than implementing against assumptions.


## Architecture correction — existing T2 bridge discovered (2026-11-07)

The initial proposal to build a separate OHLCV export adapter is superseded by inspection of the existing T2 branch `feature/freqtrade-strategy-parity-20261029`.

Verified files on that branch:
- `freqai_bridge/README.md` (blob `9cbe44a60a880e7a5ccd10266c2353a5dbf409e0`): documents Freqtrade/FreqAI **2026.9**, direct canonical SQLite consumption and the existing verification commands.
- `freqai_bridge/config.research.json` (blob `a777e018f457628150647064119435ce75dc3e29`): points `canonical_db_path` to `.data/market-data.sqlite3`, timeframe 15m, BTC/USDT:USDT, dry_run true.
- `freqai_bridge/context.py` (blob `6df3606df8ab34366bfe3abdb77a83574b76e7b1`): calls T0 `market_data.store.read_window()`, requires complete canonical coverage and checks availability time.
- `freqai_bridge/exporter.py` (blob `3b707174316d0c6b464ac947cbbe2d2fbee73682`): binds actual FreqAI dataframe timestamps and OHLCV to the canonical window, validates prediction/provenance, and emits an atomic JSON artifact.
- `freqai_bridge/test_exporter.py` (blob `81fcd9bb3823899be50e20f671696ea9812fcfe7`): uses temporary SQLite and pandas fixtures to test real dataframe/canonical matching.

Therefore, do NOT build a duplicate CSV/Feather/Parquet adapter. The next task is an integration/parity verification, not a new data exporter.

## Revised next work item

1. Compare the T0 branch's current `market_data.store` contract and schema with the T2 branch's assumptions. Confirm table/column names, timeframe semantics, UTC timestamps, decimal values, source identity and read-only access.
2. Confirm the T2 consumer opens SQLite without initializing or writing to it. Add a regression proving source schema/hash/row count are unchanged by T2 context and prediction export.
3. Run the existing `freqai_bridge.test_exporter` and `pipeline.test_decision` suites against the exact compatible source tree using temporary SQLite only.
4. Validate the exact Freqtrade 2026.9 strategy-load smoke test in its pinned environment; do not infer compatibility solely from pandas tests.
5. Build a bounded parity report against the existing OKX T2 dataset. Binance and OKX candles are different market sources; report timestamp/price/volume differences, do not expect exact equality or silently replace OKX.
6. Keep the existing OKX source and all live-execution guards unchanged. Any future T0 source enablement in T2 requires separate acceptance.

Branch boundary: the T2 implementation inspected above is on `feature/freqtrade-strategy-parity-20261029`; the current T0 development branch remains `feature/t0-centralized-data-feeder-p1-20261101`. Do not assume the two branches are merged or that the T2 code has passed tests against the latest T0 source. Cross-branch compatibility remains NOT VERIFIED.

Updated status:
- Duplicate export adapter: NOT REQUIRED based on existing implementation.
- Existing T2 direct SQLite bridge: PRESENT on T2 branch; exact compatibility with current T0 branch NOT VERIFIED.
- Freqtrade/FreqAI target: 2026.9 documented; installed runtime and strategy-load test NOT VERIFIED in this session.
- T0 Canonical SQLite file: NOT CREATED.
- T0 canonical ingestion: NOT RUN; Feeder STOPPED; `ai_execution_enabled=false`.



## T0–T2 Compatibility Audit — corrected runtime consumer result (2026-11-07)

- Full corrected report: `docs/evidence/t0/T0_T2_COMPATIBILITY_AUDIT_2026-11-07.md`.
- Correction: earlier audit identified a legacy `CandleStore.insert()` fixture in the separate T2 branch. The active T0 branch already carries the FreqAI bridge and adapted tests using test-only `market_data.test_support.seed_candles()`; the fixture issue does not block the active branch's test run.
- Added `test_t0_context_and_prediction_export_leave_canonical_sqlite_unchanged`: snapshots SQLite/WAL/SHM hashes and DB identity around canonical context read, prediction generation and separate JSON export.
- GitHub Actions run 42331669847, exact head SHA `0464b70a8a0b012730f675239f67abcb589a2ca5`.
- Paper consumer job 128279379624: 45 tests PASS (`pipeline.test_decision`, `pipeline.test_api`, `freqai_bridge.test_exporter`), including DB immutability regression.
- Artifact 13557379289, digest `sha256:1c47deb2e00eca992edc2cd466368fed438d6e575190d1aa7931069c5321e01e`.
- Static Gateway job 128279379462: SUCCESS; complete `market_data` regression passed.
- Other provider/Timescale jobs were still running when this note was recorded; final overall run status must be checked separately.
- Freqtrade/FreqAI 2026.9 actual runtime and strategy-load: NOT VERIFIED. Binance/OKX parity: NOT RUN.
- Canonical DB remains NOT CREATED; ingestion NOT RUN; Feeder STOPPED; no merge/source switch; `ai_execution_enabled=false`.
- Next: record final workflow conclusion, then verify pinned Freqtrade 2026.9 in isolated mode and prepare bounded Binance/OKX parity evidence.


## T0 CI final result and Freqtrade runtime smoke (2026-11-07)

- T0 integration workflow `42331669847` final **SUCCESS**, exact SHA `0464b70a8a0b012730f675239f67abcb589a2ca5`, all four jobs PASS including isolated TimescaleDB read-only integration.
- Timescale artifact `13558195472`, digest `sha256:0edb675178596ddc11c2d3b09ceb5a54890d0663bf25586ee059a2637c6307e0`.
- Added official Freqtrade 2026.9 FreqAI Docker strategy-load smoke workflow. First run `42331884189` verified version `freqtrade 2026.9` but used unsupported `--print-json`; corrected workflow commit `8e5a815c8c729e832ab6c705b9e175b935081f5e`.
- Corrected run `42331960788` pending. No claim of strategy-load success until run concludes.
- Next: confirm strategy discovery result, then build Binance/OKX bounded parity report using paired timestamp windows and source provenance. Existing OKX data remains authoritative for current T2 backtests.
- Safety unchanged: no canonical DB creation, ingestion, Feeder, VPS or execution.


## Freqtrade 2026.9 strategy-load smoke — PASS (2026-11-07)

- Workflow `42332039353`: SUCCESS; exact source SHA `c15fff327bb5da25a571a8ae654c728a7d22a2b4`.
- Official image `freqtradeorg/freqtrade:2026.9_freqai` reports `freqtrade 2026.9`.
- `freqtrade list-strategies` discovered `ChartProFreqaiResearch` with status **OK**.
- Artifact `13558216419`; digest `sha256:87c364ae3937aae1b9769029753bac22fa8b3733c27a4fda9430a7c278f4d263`.
- The smoke only validates framework import and strategy discovery, not FreqAI training, prediction quality/provenance, database availability, or market parity.
- Next: read-only inspect T2's authoritative OKX dataset provenance and T0 Binance sample windows; define a bounded, like-for-like parity report without changing the current OKX source.
- Safety unchanged: Canonical SQLite NOT CREATED; ingestion NOT RUN; Feeder STOPPED; no source switch or live execution.


## Binance–OKX parity readiness — source audit (2026-11-07)

- T0 source confirmed: Binance USD-M perpetual via `ccxt.binanceusdm`, BTCUSDT M15/H1.
- Existing T2 bot/backtest confirmed: OKX `BTC-USDT-SWAP` through `https://www.okx.com/api/v5/market/history-candles`. This source remains unchanged.
- T2 offline parity input contract: closed-candle CSV, continuous aligned timestamps, `CHARTPRO-OHLCV-V2` binary hash. README says signed shared dataset and independent traces remain absent.
- No paired Binance/OKX dataset artifacts were found in tracked branch files; `.data/` is gitignored. No local PC files were accessed.
- Hash formats differ by design: T0 datasetVersion hashes JSON envelope/provenance and decimal candles; T2 V2 hashes M15/H1 closed candle rows as int64 timestamp + float64 OHLCV. Do not compare these digests directly. Preserve T0 source hash and compute a separate V2 digest using an explicit tested conversion.
- Actual parity remains NOT RUN / BLOCKED pending paired immutable datasets.
- Next: design offline parity manifest/harness for two externally supplied closed-candle CSVs; verify UTC windows/coverage and report differences, never assume Binance and OKX OHLCV should match. No Canonical DB creation or ingestion.


## Binance–OKX parity manifest specification prepared (2026-11-07)

- Spec: docs/evidence/t0/T0_T2_BINANCE_OKX_PARITY_MANIFEST_SPEC_2026-11-07.md
- Commit: 868276d01fc291b58bca2905d3d47d4cf8c9ed36
- Defines source identity, independent file/T0/V2 hashes, UTC window, closed-candle and continuity gates, volume-unit mapping, explicit decimal→float64 conversion, and per-field difference outputs.
- T0 source is Binance USD-M BTC/USDT:USDT; existing T2 bot/backtest source is OKX BTC-USDT-SWAP. OKX volume must use volCcy (BTC base volume), not contract-count vol.
- T0 JSON datasetVersion and T2 CHARTPRO-OHLCV-V2 binary hash are different contracts; never compare them directly.
- No paired dataset is present in tracked source; parity remains NOT RUN pending immutable input exports.
- No data acquisition, Canonical DB creation, ingestion, Feeder, VPS or execution.


## Offline Binance–OKX parity harness — implementation PASS (2026-11-07)

- Added `market_data/t0_t2_parity.py` and `market_data/test_t0_t2_parity.py`.
- TDD RED run `42332542018` at SHA `0fb76a394b62a87b1c014559ea6437a4156914ec`: expected ModuleNotFoundError for the missing harness.
- Final T0 workflow `42332748148` SUCCESS at exact SHA `4664c28eaf0ae40f5e797b022284a378d2309c49`; Static Gateway 270 tests PASS, consumer 52 tests PASS, provider bootstrap PASS, TimescaleDB integration PASS.
- New parity tests: 7 PASS, including a V2 binary golden-layout assertion against the T2 contract and fail-closed CSV/window/source validations.
- T2 2026.9 smoke at the same SHA: run `42332748141` SUCCESS; strategy discovery PASS; artifact `13557692507`, digest `sha256:a265665d029bdc0754de12fcdd7f43dd40b25a1eda609136366f8a4e736e3114`.
- The tool reads operator-supplied CSVs offline, requires exact M15/H1 UTC window coverage and closed candles, checks source identity/volume unit, records raw file hashes and T0 datasetVersion provenance, computes separate T2 V2 hashes and per-field difference metrics.
- Real Binance/OKX comparison remains NOT RUN pending paired immutable CSV exports. No external data fetch was performed. Current T2 OKX source remains unchanged.
- No Canonical SQLite creation/access/write, ingestion, Feeder, VPS, exchange execution or live orders.
