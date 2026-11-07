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
