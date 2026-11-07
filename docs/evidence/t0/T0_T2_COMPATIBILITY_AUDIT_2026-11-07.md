# T0–T2 Compatibility Audit — 2026-11-07 (corrected with runtime consumer tests)

## Scope and exact source

Repository: `kenznguyen/btcusdt-telegram-signals2`

- T0 working branch: `feature/t0-centralized-data-feeder-p1-20261101`
- T0 source audited before documentation corrections: `b1a3daec797ab92280a95bee54aacede7cc40a57`
- T0 integration-test source: `0464b70a8a0b012730f675239f67abcb589a2ca5`
- T2 branch inspected for comparison: `feature/freqtrade-strategy-parity-20261029`, HEAD `4c039411542e11e073615a52d5a50d4ca605b49a`

Important correction: the earlier audit compared older T2 branch files and found its legacy `CandleStore.insert()` test-fixture API. The active T0 branch already contains the ported FreqAI bridge and consumer tests using `market_data.test_support.seed_candles()`. Therefore the old fixture blocker does NOT block tests on the active T0 branch. The T2 branch remains a separate historical source and has not been merged.

No canonical DB creation, DB access outside isolated test fixtures, migration, live market collection, ingestion, Feeder startup, VPS provisioning, exchange credentials, order execution, or branch merge occurred.

## Source findings

1. T0 and T2 candle store schema/read contract are compatible at source level: candle identity columns, OHLCV decimal strings, UTC millisecond timestamps, Binance USD-M BTCUSDT M15/H1 identity, bounded windows and deterministic dataset hash.
2. Active T0 branch's `read_window()` opens SQLite in URI `mode=ro`; T0's FreqAI `canonical_context()` uses that reader.
3. FreqAI exporter verifies dataframe timestamps and OHLCV against the canonical window. Prediction artifact is atomically written as a separate JSON file, not to T0 SQLite.
4. T0 active branch test fixtures initialize a temporary SQLite DB and seed it through explicitly test-only `market_data.test_support.seed_candles()`. Production `CandleStore` does not expose the legacy T2 `insert()` API. Do not restore a direct writer to production.
5. T2 documents Freqtrade/FreqAI 2026.9 and `dry_run=true`; installed version and real strategy-load remain NOT VERIFIED.
6. Binance-vs-OKX parity remains NOT RUN. Existing T2 OKX research/backtest source is not replaced.

## New read-only regression

Added `test_t0_context_and_prediction_export_leave_canonical_sqlite_unchanged` to `freqai_bridge/test_exporter.py`.

The test snapshots SHA-256 of the temporary database and its WAL/SHM sidecars, runs T0 canonical context read, makes a FreqAI prediction from the actual fixture dataframe, writes a separate JSON artifact, then asserts:
- canonical DB path identity is unchanged;
- database/WAL/SHM file hashes and presence are unchanged;
- JSON artifact exists and reads back correctly.

The test uses only a temporary isolated SQLite fixture and does not touch a Canonical PC database.

## GitHub Actions verification

- Workflow: `.github/workflows/t0-single-writer-gateway-red.yml`
- Workflow run: [42331669847](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42331669847)
- Exact head SHA: `0464b70a8a0b012730f675239f67abcb589a2ca5`
- Paper consumer job ID: `128279379624`
- Paper consumer tests: **45 passed**, including:
  - `pipeline.test_decision`
  - `pipeline.test_api`
  - `freqai_bridge.test_exporter`
  - new canonical SQLite immutability regression.
- Paper consumer artifact: [13557379289](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42331669847/artifacts/13557379289)
- Artifact digest: `sha256:1c47deb2e00eca992edc2cd466368fed438d6e575190d1aa7931069c5321e01e`
- Static Gateway contract job ID `128279379462`: SUCCESS, including full `market_data` regression suite.
- At report time, restricted provider bootstrap and isolated TimescaleDB jobs were still running; overall workflow conclusion remains pending until all jobs complete.

Workflow path filters were expanded so changes under `freqai_bridge/**`, `pipeline/**` and `requirements-web.txt` trigger the consumer regression workflow on the active branch.

## Acceptance matrix

| Gate | Result | Evidence |
|---|---|---|
| T0/T2 schema and read contract | CONDITIONAL PASS | Static source comparison |
| Active T0 consumer reads via read_window | PASS | Source inspection + 45-test CI job |
| Canonical SQLite immutability during context/export | PASS in isolated fixture | New hash/identity regression |
| T2 decision + API regressions | PASS | 45-test consumer job |
| T2 legacy test fixtures on T0 source | Not applicable to active branch | Active T0 branch has test-only fixture seeding |
| Freqtrade/FreqAI 2026.9 installed | NOT VERIFIED | Docs/config only |
| Real Freqtrade strategy-load smoke test | NOT RUN | No framework runtime invocation |
| Binance/OKX parity | NOT RUN | No paired bounded dataset/report |
| Canonical SQLite on PC | NOT CREATED | User-confirmed |
| Canonical ingestion | NOT RUN | Not authorized |
| Feeder | STOPPED | Not authorized |
| VPS | NOT PROVISIONED | No decision to provision |
| Live execution | DISABLED | `ai_execution_enabled=false` |

## Next steps

1. Wait for and record the final result of workflow run 42331669847 and its remaining provider/Timescale jobs.
2. Inspect T0/T2 exact source diff and decide whether any code synchronization is actually needed; do not merge branches merely to align them.
3. Verify Freqtrade/FreqAI 2026.9 in an isolated environment and run a strategy-load smoke test without exchange sync, credentials, or orders.
4. Build a bounded Binance-vs-OKX parity report with provenance and explicit differences. Keep existing OKX backtest data unchanged until acceptance.

## Safety disposition

- T0 remains canonical data owner and single-writer boundary.
- T2 consumer access remains read-only.
- Test-only fixture writes are confined to temporary databases.
- No merge, source switch, canonical DB creation, migration, ingestion, Feeder startup, VPS provisioning, or live execution.
- Overall: **PASS for isolated T0→T2 consumer/read-only regression; NOT VERIFIED for Freqtrade runtime and exchange parity.**


## Final verification — T0 integration workflow completed (2026-11-07)

- Re-checked workflow run [42331669847](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42331669847): final status **SUCCESS**, exact head SHA `0464b70a8a0b012730f675239f67abcb589a2ca5`.
- All four jobs SUCCESS: Static Gateway, Paper consumer, restricted provider bootstrap, isolated TimescaleDB read-only integration.
- Artifacts:
  - Paper consumer `13557379289`, digest `sha256:1c47deb2e00eca992edc2cd466368fed438d6e575190d1aa7931069c5321e01e`.
  - TimescaleDB read-only `13558195472`, digest `sha256:0edb675178596ddc11c2d3b09ceb5a54890d0663bf25586ee059a2637c6307e0`.
  - Static/Gateway `13557860731`, digest `sha256:f25b883eb7492a5f490a9990a0ff6486b7c2b35a15b2037bfcf123580ab7acc6`.
  - Provider bootstrap `13557462607`, digest `sha256:07ed38b3c578ff36b698bdf13d488dd45714f03fbe5e8fc8aed9fa44fd9cb869`.
- These are isolated test databases and fixtures; no PC Canonical DB, production ingestion or Feeder was used.

## Pinned Freqtrade runtime smoke — in progress

- Added `.github/workflows/t2-freqtrade-2026-9-strategy-smoke.yml`, commit `c9344633c0fc78bb08015e546475afcf432804d8`.
- First run `42331884189` confirmed official image version `freqtrade 2026.9`, but failed because the workflow passed unsupported CLI flag `--print-json` to `list-strategies`. This was a workflow invocation error, not a strategy failure.
- Removed the unsupported flag in commit `8e5a815c8c729e832ab6c705b9e175b935081f5e`.
- Corrected run `42331960788` is in progress; exact head SHA `8e5a815c8c729e832ab6c705b9e175b935081f5e`. Final strategy-load result must be recorded after completion.
- The smoke job checks dry-run and disabled entry/exit guards, has empty exchange credentials, mounts source read-only, and runs only strategy discovery; no exchange sync, DB, model training or order execution.

## Updated disposition

- T0→T2 consumer regression and T0 isolated storage/provider/Timescale CI: PASS.
- Freqtrade 2026.9 image version: VERIFIED.
- Freqtrade strategy-load: PENDING corrected run.
- Binance/OKX parity: NOT RUN.
- Canonical SQLite PC: NOT CREATED; canonical ingestion NOT RUN; Feeder STOPPED; VPS NOT PROVISIONED; `ai_execution_enabled=false`.


## Freqtrade/FreqAI 2026.9 runtime strategy-load — PASS

- Workflow: [42332039353](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42332039353), final **SUCCESS**.
- Exact workflow/source SHA: `c15fff327bb5da25a571a8ae654c728a7d22a2b4`.
- Official image: `freqtradeorg/freqtrade:2026.9_freqai`; runtime output confirms `freqtrade 2026.9`.
- Strategy discovery output: `ChartProFreqaiResearch`, status **OK**.
- Artifact: `13558216419`; digest `sha256:87c364ae3937aae1b9769029753bac22fa8b3733c27a4fda9430a7c278f4d263`.
- First smoke attempt exposed two harness issues (unsupported `--print-json`; read-only bind mount placed at Freqtrade's default writable user-data directory). Both were corrected in the workflow. The final run mounts source at `/workspace:ro` and uses isolated `/tmp/freqtrade-userdata`.
- The smoke proves the pinned framework imports and discovers the strategy. It does NOT prove a FreqAI training run, prediction quality, model provenance, actual canonical DB availability, exchange parity, or trading behavior.
- No exchange sync, credentials, canonical DB mount, DB writes, model training or orders were used.

## Updated acceptance

| Gate | Result |
|---|---|
| T0→T2 consumer regression | PASS |
| T0 static Gateway + SQLite contracts | PASS |
| Disposable PostgreSQL provider bootstrap | PASS |
| Disposable TimescaleDB read-only integration | PASS |
| Freqtrade/FreqAI 2026.9 image | PASS |
| ChartProFreqaiResearch strategy discovery | PASS |
| FreqAI training/model provenance | NOT RUN |
| Binance/OKX parity | NOT RUN |
| Canonical SQLite PC | NOT CREATED |
| Canonical ingestion / Feeder | NOT RUN / STOPPED |
| Live execution | DISABLED |

Overall: **PASS for T0 isolated consumer/storage integration and Freqtrade 2026.9 strategy discovery. NOT VERIFIED for FreqAI training/prediction and Binance–OKX data parity.**
