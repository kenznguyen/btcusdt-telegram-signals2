# T0–T1–T2 Operational Readiness Review

Date: 2026-11-07 (Asia/Ho_Chi_Minh)
Review mode: READ-ONLY SOURCE / GITHUB EVIDENCE REVIEW
Verdict: **CONDITIONAL — COMPONENT CONTRACTS PARTIALLY VERIFIED; END-TO-END OPERATIONAL READINESS NOT CERTIFIED**

## 1. Scope and source identity

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Branch HEAD at review start: `0b1f68464ea5337dd3a44e0b4ad56ce55c0312a5`
- Last code/test verification SHA: `1b190ba7562b3843de75894ce68bd6f0ea99b321`
- GitHub compare: code SHA → HEAD is 7 commits ahead, 0 behind; the only changed paths are documentation:
  - `docs/PROJECT_SESSION_HANDOFF.md`
  - `docs/evidence/t0/T0_T2_COMPATIBILITY_AUDIT_2026-11-07.md`
  - `docs/evidence/t0/T0_T2_PAIRED_DATASET_ACQUISITION_READINESS_2026-11-07.md`
- Therefore, the verified code/test baseline has no source or test drift through the reviewed HEAD. This is a GitHub commit comparison, not a local PC worktree inspection.

Reviewed contracts/source:
- `market_data/README.md`, `market_data/store.py`, `market_data/storage.py`, T0 controlled-ingestion plan and compatibility audit.
- `futures_intelligence/README.md`, `futures_intelligence/import_collector.py`, `futures_intelligence/test_import_collector.py`.
- `freqai_bridge/README.md`, `freqai_bridge/context.py`, `freqai_bridge/exporter.py`, `freqai_bridge/config.research.json`, `freqai_bridge/ChartProFreqaiResearch.py`.
- `pipeline/decision.py` and current GitHub Actions workflow definitions.

No source code, tests, workflow, runtime configuration, database, or market data were changed or executed during the review.

## 2. Executive status

| Layer / gate | Contract and evidence | Operational verdict |
|---|---|---|
| T0 OHLCV foundation | SQLite store/read contract, closed-candle validation, coverage/gap checks, deterministic `datasetVersion`, single-writer/lease/health/restart tests | **PASS in isolated CI / NOT RUN on Canonical PC DB** |
| T0 public connectivity | User-provided PC probe: REST 5/5 and Binance USD-M WebSocket HTTP 101 with valid BTCUSDT M15 kline event | **PASS for one sample only; no SLA or ingestion proof** |
| T1 Futures Intelligence importer | Pinned collector CSV schema, strict importer, Decimal calculations, snapshot hash/provenance and fail-closed validation; synthetic/temp-file unit fixtures exist | **SOURCE CONTRACT PRESENT; LIVE CAPTURE NOT VERIFIED; T1 TESTS NOT IN CURRENT CI WORKFLOW** |
| T0 → T2 OHLCV consumer | Direct read-only T0 SQLite `read_window()`; M15 candle matching and prediction provenance checks; temporary SQLite immutability regression | **PASS in isolated fixtures for M15 only** |
| T2 Freqtrade/FreqAI runtime | Official Freqtrade/FreqAI 2026.9 image; strategy discovery/load smoke | **PASS for framework/strategy load only; training/inference/OOS NOT VERIFIED** |
| T0/T1/T2 integrated decision | `pipeline.decision.evaluate()` validates canonical M15, T1 observed trade flow, FreqAI prediction and Hummingbot order-book snapshot; errors return WAIT | **CONTRACT PRESENT; REAL END-TO-END INPUTS NOT VERIFIED** |
| Real Binance–OKX parity | Synthetic parity harness and deterministic difference report | **SYNTHETIC PASS; REAL DATA PARITY NOT RUN** |

## 3. T0 — data foundation

### Verified in source and isolated CI

- Canonical candle identity is Binance / USDT perpetual / BTCUSDT with timeframe and half-open UTC window.
- `read_window()` uses read-only SQLite access (`mode=ro`), refuses a missing database, validates candle/window identity and coverage, reports gaps, and computes deterministic `datasetVersion`.
- T0 write path is fenced through the single-writer gateway and lease contract; startup health/readiness and process restart/fencing tests are part of the T0 workflow.
- Controlled-ingestion acceptance was tested only against isolated temporary storage and synthetic exchange-compatible candles: expected 96 M15 + 24 H1 rows for a 24-hour window, idempotent second sync, stable dataset hash, API/hash parity, conflicting-batch rollback and isolation.
- PostgreSQL/TimescaleDB bootstrap and integration tests ran against disposable CI databases, not a production/canonical target.

### Operational limitations

- Canonical SQLite file/absolute target identity is still not established or created. The user's later decision deferred initialization; this supersedes the earlier architecture/initializer approval.
- No canonical ingestion has run. Feeder remains STOPPED. Windows host preflight is deferred.
- One successful public connectivity sample does not establish sustained connection, capture completeness, recovery behavior on the PC, or persisted data quality.
- T0 Controlled First Run remains NOT AUTHORIZED; backup/restore preflight and exact UTC first-run window remain unresolved.

Verdict: **T0 software/isolated acceptance PASS; PC operational readiness BLOCKED / NOT VERIFIED.**

## 4. T1 — Futures Intelligence

### Verified in source

- Importer accepts real CSV files for Binance futures BTCUSDT and four feed types: aggregate trades, funding rates, open interest, and liquidations.
- Collector schema is pinned to commit `bc4f0ef633fbeee4a49defd72827f17162693805`.
- Snapshot records source commit, input-file SHA-256/size/row counts, a deterministic `snapshotId`, time window and feed coverage.
- Missing feeds remain null rather than fabricated zeroes. Trade duplicates/conflicts and ID gaps are surfaced; invalid market identity, timestamps and numeric fields fail closed.
- Connection continuity is explicitly `UNVERIFIABLE` because the pinned CSV schema has no heartbeat/disconnect events. No observed trade-ID gap is not proof of uninterrupted capture.
- Funding/OI/liquidation are published as context; current decision code uses validated fresh aggregate trade flow as the T1 directional input.

### Evidence gaps

- Unit tests exist in `futures_intelligence/test_import_collector.py` and use temporary CSV fixtures; they do not prove the external collector was running or that live data was captured.
- The current `t0-single-writer-gateway-red.yml` workflow does not invoke `futures_intelligence.test_import_collector`. The reviewed workflow directory has no dedicated T1 importer/live-capture workflow.
- No immutable live capture bundle, collector heartbeat/reconnect evidence, or independently verified T1 snapshot from the PC was found in the reviewed handoff/evidence set.
- Liquidation feed continuity and event deduplication remain explicitly unverified due to source schema limitations.
- T1 is not currently an OHLCV consumer of T0. It imports microstructure/futures feeds from the separate pinned collector. Its snapshot has its own `snapshotId`; the decision intent records both T0 `datasetVersion` and T1 `inputSnapshotId`, but no live cross-source dataset has been accepted.

Verdict: **Importer design/source contract present; live T1 operational readiness NOT VERIFIED.**

## 5. T2 — Freqtrade/FreqAI and T0 bridge

### Verified

- T2 bridge reads T0 directly; a second OHLCV exporter is unnecessary.
- T0 context read is read-only and validates exact market, M15 timeframe, complete closed-candle coverage, timestamps and source `datasetVersion`.
- Prediction publication checks actual FreqAI dataframe timestamps/OHLCV against the T0 context, `do_predict == 1`, model/strategy/training provenance, and dataset hash. JSON publication is atomic and separate from the T0 database.
- A regression test checks database path and SQLite/WAL/SHM hashes remain unchanged across T0 context read and prediction export in temporary fixtures.
- Current FreqAI strategy/config uses M15 only (`timeframe=15m`, `include_timeframes=["15m"]`). H1 is available in T0 but is not consumed by this bridge.
- T2's existing OKX research/backtest source has not been replaced by T0/Binance.

### CI evidence

- T0 workflow [42338141750](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42338141750): SUCCESS, branch `feature/t0-centralized-data-feeder-p1-20261101`, exact head SHA `1b190ba7562b3843de75894ce68bd6f0ea99b321`, all four jobs SUCCESS.
  - Static Gateway job: complete `market_data` suite ran 276 tests, 42 skipped; Health/Readiness and restart/fencing commands are included.
  - Paper consumer job: 53 tests PASS, including `pipeline.test_decision`, `pipeline.test_api`, `freqai_bridge.test_exporter`, and synthetic T0/T2 parity.
  - Artifacts:
    - Static/Gateway: ID `13559494829`, digest `sha256:8836bac802bb8eb869f66c0339f2b23fae1025cb96edd15877a87212ea098cba`.
    - Paper consumer: ID `13560313069`, digest `sha256:894df1eae176be762a1e4d60cc4ac0752ecccc931e3a7d2544a0511a23bbe219`.
    - Provider bootstrap: ID `13560458082`, digest `sha256:616a6d44f94ef4147f4223752e5e0983453ff031166df33780aadd3749ffe29a`.
    - Disposable TimescaleDB: ID `13560042410`, digest `sha256:94bc46427341d6d0517ce3d268b031c03682723e3186ed15ce5a4ce4a6269416`.
- Freqtrade smoke [42338141694](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42338141694): SUCCESS at the same exact SHA; job `128299761176` loaded official Freqtrade/FreqAI 2026.9 and found `ChartProFreqaiResearch` status OK. Artifact ID `13560551806`, digest `sha256:6103de121988540315d5f54ab30b74243499f9921ef3bd00a42e202883af20bd`.

### Not proven

- Freqtrade strategy load is not model training, actual inference, prediction quality, backtest profitability or OOS certification.
- Actual FreqAI training sidecar/provenance is not present as accepted live evidence.
- M15 consumer fixtures do not certify H1 T2 consumption.
- Real Binance–OKX paired data parity remains NOT RUN; no accepted paired immutable CSVs and matching genuine T0 `datasetVersion` provenance.
- Current OKX source remains unchanged.

Verdict: **M15 T0 bridge/consumer fixtures PASS; T2 research runtime smoke PASS; production prediction and real-source parity NOT VERIFIED.**

## 6. Cross-layer decision contract and integration gaps

The current decision function requires all four inputs:
1. T0 canonical M15 candle window with complete coverage and matching `datasetVersion`.
2. T1 intelligence snapshot with fresh observed aggregate trades, no trade-ID gaps and no duplicates.
3. T2 FreqAI prediction with `doPredict=1`, matching T0 dataset hash, candle timestamps and training provenance.
4. T3 Hummingbot order-book snapshot with correct Binance perpetual/BTCUSDT identity, valid bid/ask depth and freshness.

The function returns `WAIT` if any input is missing or fails validation. A valid paper intent records T0 dataset hash and T1 snapshot ID. The Hummingbot snapshot timestamp is retrieval time; code explicitly does not claim exchange sequence verification.

This means the three-layer readiness review cannot be promoted to end-to-end operational readiness while T1 live capture and T2 real prediction provenance are absent; the decision path also has a T3 data dependency.

## 7. Ordered gaps and next work

| Priority | Gap | Required next evidence | Constraint |
|---|---|---|---|
| 1 | T1 importer test suite not in current CI | Add a dedicated offline GitHub Actions test step/job for `futures_intelligence.test_import_collector`; exact-SHA test artifact | No live capture or API calls in this test step |
| 2 | T1 live capture/continuity | Separate read-only capture acceptance with immutable input files, hashes, pinned collector identity, heartbeat/reconnect evidence or explicit UNVERIFIABLE status | Do not fabricate continuity; no secrets/proxy/VPN |
| 3 | T2 model provenance and inference | Actual FreqAI training/prediction artifact, immutable model/strategy/dataset provenance, matching T0 window and prediction timestamps | Research/paper only; no order execution |
| 4 | T0 canonical target/first run | Resolve target identity and host-local preflight, backup/restore proof, bounded window, then a separate explicit first-run authorization | Currently deferred/not authorized; do not initialize or ingest |
| 5 | T2 H1 consumer requirement | Decide whether T2 actually needs H1 input; if yes, specify and test it separately | Do not imply current M15 bridge already consumes H1 |
| 6 | Real Binance–OKX parity | Paired immutable M15/H1 exports plus genuine T0 provenance and deterministic report | Isolated Paired Dataset Acquisition Runner remains PAUSED; do not resume implicitly |
| 7 | Full decision path | Verify T0/T1/T2 artifacts together with a T3 order-book snapshot and explicit paper-risk gate | Paper-only; `ai_execution_enabled=false` |

Recommended next bounded implementation task: **add the existing T1 importer unit suite to GitHub Actions as an offline-only CI gate**, then verify the exact source SHA and artifact. This does not require Canonical SQLite, Windows preflight, exchange access, or Feeder startup.

## 8. Explicit safety and deferred states

- Canonical SQLite: **NOT CREATED / CREATION DEFERRED**.
- Canonical ingestion: **NOT RUN**.
- Controlled First Run: **NOT AUTHORIZED**.
- Feeder: **STOPPED**.
- Windows Feeder preflight: **DEFERRED / NOT RUN**.
- Isolated Paired Dataset Acquisition Runner: **PAUSED / NOT IMPLEMENTED**.
- Real Binance–OKX parity: **NOT RUN**.
- T2 OKX research source: **UNCHANGED**.
- VPS: **NOT PROVISIONED**.
- Live orders/exchange execution: **DISABLED**.
- `ai_execution_enabled=false`.

This report is a source/evidence review only. It does not authorize database creation, ingestion, Feeder startup, exchange data acquisition, source switching, VPS provisioning, merging, or live execution.
