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


## Binance–OKX parity readiness audit (read-only source inspection)

### Confirmed source identities

- T0 canonical market-data source: Binance USD-M perpetual `BTC/USDT:USDT`, symbol key `BTCUSDT`, M15/H1; `market_data/sync.py` uses CCXT `binanceusdm`.
- Existing T2 bot/backtest source: OKX perpetual `BTC-USDT-SWAP`; `bot.py` calls `https://www.okx.com/api/v5/market/history-candles`, and `backtest.py` calls the same endpoint.
- T2's current OKX path is direct API fetch into pandas frames; it is not reading T0's Binance store. Preserve this source until parity review is complete.
- T2 `freqtrade_parity/dataset_io.py` consumes explicit closed-candle CSV files, checks continuity/alignment and emits a `CHARTPRO-OHLCV-V2` hash. T2 README explicitly says a signed shared OHLCV dataset and genuine paired traces are still missing.
- No committed paired Binance/OKX dataset or signed trace artifacts were found in the inspected branch tree. `.data/` is gitignored. No local operator dataset was accessed.

### Hash contract mismatch — do not compare hashes directly

- T0 `market_data.store.read_window()` `datasetVersion` is SHA-256 over a canonical JSON envelope including exchange/market identity, symbol, timeframe, UTC window, as-of value and decimal candle/provenance fields.
- T2 `freqtrade_parity.dataset_hash` hashes binary `CHARTPRO-OHLCV-V2` bytes: sorted M15/H1 closed rows, signed int64 UTC open milliseconds and five IEEE754 float64 values.
- These hashes intentionally represent different contracts and are NOT expected to match. A future parity package must retain the original T0 `datasetVersion` as source provenance and separately compute the T2 V2 hash from an explicitly specified decimal-to-float64 conversion. Never relabel one as the other.
- T0 stores normalized decimal strings; T2 V2 conversion to float64 can lose decimal precision. The conversion rule and resulting bytes must be explicit and tested against the shared Kotlin/Python V2 golden vector.

### Parity status and safe next step

**NOT RUN / BLOCKED BY MISSING PAIRED DATASET.** No real T0 Canonical database exists on PC, and no committed OKX dataset artifact is available for the same UTC window. Do not fetch/ingest into Canonical as a side effect of parity work.

Next bounded task: prepare a parity manifest/schema and offline comparison harness that accepts two operator-supplied, immutable closed-candle CSV exports (Binance and OKX), records independent source identity and T0 datasetVersion provenance, verifies M15/H1 UTC windows and coverage, computes per-source V2 hashes, and reports differences without expecting OHLCV equality. Keep the input files outside Git if they contain large market datasets; commit only manifests and compact evidence. Actual parity execution waits for paired data and explicit review.

No source switch, branch merge, canonical DB creation, ingestion, Feeder, VPS or execution.


## Offline parity harness implementation — PASS (2026-11-07)

### TDD evidence

- RED: run [42332542018](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42332542018), exact SHA `0fb76a394b62a87b1c014559ea6437a4156914ec`; parity test failed at expected missing module `market_data.t0_t2_parity`.
- Intermediate GREEN exposed two incorrect test expectations: report window included explicit UTC semantics, and the V2 golden vector must place M15 rows before the H1 section marker. Assertions were corrected to match the manifest/report contract and T2's canonical byte order.
- Final T0 workflow [42332748148](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42332748148): **SUCCESS**, exact source SHA `4664c28eaf0ae40f5e797b022284a378d2309c49`, all four jobs SUCCESS.
- Static Gateway: 270 tests PASS.
- Paper consumer: 52 tests PASS, including 7 new parity tests.
- Restricted provider bootstrap: PASS.
- Isolated TimescaleDB read-only integration: all 4 test groups PASS (10 atomic writer, 20 FeederRuntime, 6 lifecycle, 18 role privilege, 6 Timescale read-only tests).
- Consumer artifact `13558540383`, digest `sha256:0311b7e5b3b0264b6f2f5ac3e5442cb3e3061109b5ccc597177dcefcbc532673`.
- Static/Gateway artifact `13558003133`, digest `sha256:c50838261cd0fffcbf1a772f2b355334da3277a5c33440a96f779b3fbc5b739e`.
- Provider artifact `13558347616`, digest `sha256:f876d226d421801a453a887494dc89dddf59030a6991dda761058407e1df5129`.
- Timescale artifact `13557404226`, digest `sha256:9d0ec699740b570d2578071582b6a6a03561dcb5d4b864866381faf429401f7c`.

### Implementation

- `market_data/t0_t2_parity.py`: stdlib-only offline parser/report engine; no exchange/network/database access.
- `market_data/test_t0_t2_parity.py`: 7 tests cover comparable report, T2 V2 byte contract, unclosed candles, gaps/duplicates/unaligned timestamps, invalid OHLC/non-finite values, source identity/volume units, mismatched windows and missing T0 provenance.
- `.github/workflows/t0-single-writer-gateway-red.yml` now includes the parity tests in paper consumer regressions.
- T2 Freqtrade 2026.9 strategy smoke also reran at the same exact SHA: [42332748141](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42332748141), SUCCESS; artifact `13557692507`, digest `sha256:a265665d029bdc0754de12fcdd7f43dd40b25a1eda609136366f8a4e736e3114`.

### Verification boundary

- Offline harness and T2 V2 hash compatibility: PASS on synthetic fixtures only.
- Real Binance–OKX parity: NOT RUN; no paired immutable source CSVs supplied.
- The harness strictly requires exact full-window M15/H1 coverage and closed rows; it rejects rather than fills gaps or filters rows.
- T0 JSON `datasetVersion` is retained separately from the T2 V2 binary digest. The harness does not claim the two hashes are equal.
- No PC Canonical DB, exchange API, market sync, ingestion, Feeder, VPS or live execution was used.


## Largest-difference evidence enhancement — PASS (2026-11-07)

- Gap found during spec review: aggregate per-field statistics existed, but the report did not yet list the largest-difference rows with source timestamps and both original values.
- TDD RED: valid synthetic fixture run [42333165249](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42333165249), exact test source SHA `7cdceb3978f1030a6ad8bdba862332dd33f110fc`; the new assertion failed with expected `KeyError: largest_differences`.
- One earlier attempt used an invalid fixture (close above high); corrected the fixture OHLC envelope before accepting the RED evidence.
- Implementation commit: `95932ec6cf9a6f5c061c2d7fbe0bafa740e9f313`.
- Final T0 workflow [42333240421](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42333240421): **SUCCESS**, exact source SHA `95932ec6cf9a6f5c061c2d7fbe0bafa740e9f313`, all 4 jobs SUCCESS.
- Static Gateway: 271 tests PASS; paper consumer: 53 tests PASS, including largest-difference test; provider bootstrap PASS; TimescaleDB integration PASS (10 writer, 20 FeederRuntime, 6 lifecycle, 18 role privilege, 6 read-only integration tests).
- Added deterministic top-5 rows for every M15/H1 OHLCV field, ordered by descending absolute difference then ascending timestamp. Each row records UTC open timestamp, original Binance/OKX decimal strings, absolute difference, and relative difference using OKX as denominator (n/a when OKX value is zero).
- Markdown report now includes a Largest difference rows section.
- T0 artifacts: consumer `13558188809` digest `sha256:f71425f026b20df1c2629d7ef820fcdbf696fa494fa02b3d603726c392198f70`; Gateway `13558248887` digest `sha256:41f391569c3eb4e9e06dcf45ad0ffdcc9696114f0b917a9be461a595bc127954`; provider `13557633648` digest `sha256:cdbd71b62ad677124211ffb4097146fa5ed773691ef2812069cb1c2c6da4eb97`; Timescale `13558471829` digest `sha256:f098ca773ee7757e2658d57a2f2e87fc78a06b2c8f996cc8c5f44054f2218186`.
- Freqtrade 2026.9 smoke [42333240406](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42333240406): SUCCESS at same exact SHA; strategy `ChartProFreqaiResearch` status OK; artifact `13557394964`, digest `sha256:951294815b964295675bb0d3996ad3c0685d5a1e04259bcdad572584fa7aa616`.
- Real Binance–OKX parity remains NOT RUN pending paired immutable CSVs. No network acquisition, Canonical DB access/write, ingestion, Feeder, VPS or execution.


## Current-HEAD read-only consumer review — 2026-11-07

- Audited current branch HEAD `237cd06e7973d5d9c95944ad7f023b142191c167` and compared it with code-verification SHA `95932ec6cf9a6f5c061c2d7fbe0bafa740e9f313`. The compare reports 9 commits ahead and only documentation files changed; no production or test code changed after the verified code SHA.
- `market_data.store.read_window()` resolves the configured SQLite path, refuses a missing file, and opens SQLite with URI `mode=ro`. It selects the exact Binance/USDT-perpetual/BTCUSDT/timeframe/window identity, orders by open time, derives closed/validated candle metadata, computes gaps and a deterministic `datasetVersion`.
- `freqai_bridge.context.canonical_context()` requests a bounded M15 window ending at the latest closed 15-minute boundary, requires complete coverage, and rejects candles whose first-observed availability is later than the decision clock.
- `freqai_bridge.exporter.make_prediction()` requires training provenance, validates FreqAI dataframe timestamps and OHLCV against every canonical context row, requires `do_predict == 1`, binds the inference `datasetVersion` to the canonical window, and preserves the independent training dataset hash.
- `write_artifact()` publishes a bounded JSON file atomically outside the SQLite store. The existing regression snapshots DB/WAL/SHM hashes and database path identity around context read and prediction publication; this was verified in isolated temporary SQLite fixtures, not a PC Canonical database.
- Important scope clarification: current `freqai_bridge/config.research.json` and `ChartProFreqaiResearch` configure only `15m`; FreqAI `include_timeframes` is also `["15m"]`. H1 is not consumed by this T2 bridge today. Therefore M15 bridge PASS must not be represented as M15+H1 consumer acceptance. H1 remains available in the T0 store and parity harness but requires a separately specified T2 consumer change if needed.
- No code defect requiring a duplicate adapter was found in this bounded review. Do not create a second CSV/Parquet exporter or modify the existing OKX backtest source.
- Evidence remains: T0 consumer regression run `42331669847` SUCCESS at `0464b70a8a0b012730f675239f67abcb589a2ca5`; offline parity and largest-difference workflow `42333240421` SUCCESS at `95932ec6cf9a6f5c061c2d7fbe0bafa740e9f313`; Freqtrade 2026.9 strategy discovery run `42333240406` SUCCESS at the same code SHA. These prove isolated consumer immutability, synthetic parity harness and strategy import/discovery only.
- Current acceptance: read-only M15 source integration PASS in isolated fixtures; H1 T2 consumption NOT IMPLEMENTED / NOT VERIFIED; real Binance–OKX parity NOT RUN; actual FreqAI training/prediction provenance NOT RUN.
- Safety unchanged: Canonical SQLite NOT CREATED; no canonical DB access/write; ingestion NOT RUN; Feeder STOPPED; T2 OKX source unchanged; no merge; VPS NOT PROVISIONED; `ai_execution_enabled=false`.

### Next bounded step

Before any real parity conclusion, obtain paired immutable Binance USD-M and OKX CSVs for the same fresh 30-day UTC window and genuine T0 `read_window()` datasetVersion values for the exact Binance M15/H1 windows. If genuine provenance cannot be produced through an isolated temporary store without Canonical SQLite, stop as BLOCKED. Do not fabricate provenance, access/create Canonical SQLite, start Feeder, or change T2 source.


## Canonical SQLite empty initializer — implementation and test evidence (2026-11-07)

- User explicitly approved creation of the T0 Canonical DB. Scope for this increment is schema initialization only: no Binance fetch, candle ingestion, lease acquisition, Feeder startup, or T2 source change.
- Added `market_data/initialize_sqlite.py` and `market_data/test_initialize_sqlite.py`.
- Initializer default path: `.data/market-data.sqlite3`; creates a new file exclusively with restrictive mode `0600` where supported; refuses any existing file/directory/symlink target rather than overwriting it.
- Creates only the current SQLite `candles` and `feeder_leases` tables, sets schema `user_version=1`, runs `PRAGMA integrity_check`, and verifies both tables contain zero rows. It does not start a Feeder or contact an exchange.
- TDD RED evidence: run `42337706098`, exact test-only SHA `a83e8ee30dae890eb2ff849c05977eef5a567b22`, Static Gateway full market_data suite failed as expected with `ModuleNotFoundError: market_data.initialize_sqlite`; artifact `13559648818`, digest `sha256:3cc6d730fcb2435621ce42f5a1c6a73ff79bfeebafaff60a55525e4d62c6c124`.
- Implementation commit sequence: `b289d7c1168e7bb7cfeca403966d5647800dc43a`, `1d7a5a8c80939acb60fe12c5d36c3c16e5105b3f`, final tested code SHA `28ef9da578118190f8bb3033d02a58da8b40ec7f`.
- Final workflow `42337762615` at exact SHA `28ef9da578118190f8bb3033d02a58da8b40ec7f`: Static Gateway contract job SUCCESS, including full `market_data` regression suite; paper consumer regression job SUCCESS. Restricted provider bootstrap and isolated TimescaleDB jobs were still in progress at the time of this record; overall workflow conclusion therefore remains NOT VERIFIED.
- PC Canonical DB creation has NOT been executed from this ChatGPT session because the PC filesystem is not accessible here. The GitHub Actions runner is intentionally not used as the Canonical data host.
- After the code is available on the PC, the exact operator command is: `python -m market_data.initialize_sqlite --db .data/market-data.sqlite3 --confirm-create`. This command is intentionally fail-closed if the target already exists.
- Required post-creation evidence from the PC: command JSON output; file path/size/permissions; `PRAGMA integrity_check=ok`; tables exactly `candles, feeder_leases`; zero candle rows and zero lease rows; no WAL/SHM integrity issue; computed SHA-256 of the DB file. Do not upload the DB itself to GitHub; record only hashes and non-sensitive metadata.
- Status: initializer implementation and static/full market_data regression PASS on isolated GitHub runner; provider/Timescale full workflow NOT VERIFIED; PC Canonical DB NOT CREATED; ingestion NOT RUN; Feeder STOPPED; live execution disabled.


## 30-day T0 provenance read-window bound — 2026-11-07

- The approved 30-calendar-day M15 parity window contains 2,880 candles, exceeding the prior `read_window()` bound of 2,000. The old bound would reject the requested single-window M15 `datasetVersion`; chunking and inventing a composite provenance value is not acceptable.
- Added a distinct read-side bound `MAX_READ_CANDLES=3000` to support the exact 2,880-row M15 snapshot with a bounded 120-row margin. Preserved `MAX_CANDLES=2000` as the existing ingestion/sync bound; `sync_window()` write-side behavior remains unchanged.
- Regression test inserts 2,880 closed M15 fixture candles through the existing test gateway and requires a complete 30-day read, exact first/last timestamps and a SHA-256 datasetVersion. The over-limit read rejection now uses `MAX_READ_CANDLES+1`.
- TDD RED evidence: workflow `42338026283` at test-only SHA `2c54ee6a5e1857f2c51850644ec65f9fffbe282f` failed on the expected 2,000-row read bound. Artifact `13560825276`, digest `sha256:a215fc0315ee54c75c712feefa00534ffde49dc3aa0b9202e06c2928639fce18`.
- An intermediate implementation at SHA `4fd8e3f096a29e9d36067e1684830c781bd0100f` exposed an unintended coupling: increasing the shared constant also widened `sync_window()` ingestion limits and caused its invalid-range test to call the exchange. This was corrected by separating read and sync limits; the write-side cap remains 2,000.
- Final current code SHA: `1b190ba7562b3843de75894ce68bd6f0ea99b321`. Workflow `42338141750`: Static Gateway full contract/market_data suite PASS; Paper consumer regressions PASS. Fresh-cluster provider bootstrap and isolated TimescaleDB jobs were still running when this note was recorded, so overall workflow conclusion remains NOT VERIFIED. T2 Freqtrade smoke `42338141694` is associated with the same SHA and was pending at record time.
- Artifact evidence at current SHA: Static Gateway `13559494829`, digest `sha256:8836bac802bb8eb869f66c0339f2b23fae1025cb96edd15877a87212ea098cba`; paper consumer `13560313069`, digest `sha256:894df1eae176be762a1e4d60cc4ac0752ecccc931e3a7d2544a0511a23bbe219`.
- The change only increases the bounded read-window ceiling; it does not create a database, ingest market data, or change the T0 write gateway. Canonical DB creation remains deferred at the user's request.


## Workflow reconciliation and next acquisition design — 2026-11-07

- Re-checked active branch: `feature/t0-centralized-data-feeder-p1-20261101`, HEAD at reconciliation time `8537763d8efe543dd702978954b5341700b32c35`.
- Compared tested code SHA `1b190ba7562b3843de75894ce68bd6f0ea99b321` to HEAD: 3 commits ahead; changed paths were documentation only. No code/test drift after the verified code SHA.
- T0 workflow [42338141750](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42338141750): **SUCCESS**, exact head SHA `1b190ba7562b3843de75894ce68bd6f0ea99b321`; all four jobs SUCCESS: Static Gateway, Paper consumer, restricted provider bootstrap, isolated TimescaleDB read-only integration.
  - Static/Gateway artifact `13559494829`, digest `sha256:8836bac802bb8eb869f66c0339f2b23fae1025cb96edd15877a87212ea098cba`.
  - Paper consumer artifact `13560313069`, digest `sha256:894df1eae176be762a1e4d60cc4ac0752ecccc931e3a7d2544a0511a23bbe219`.
  - Provider bootstrap artifact `13560458082`, digest `sha256:616a6d44f94ef4147f4223752e5e0983453ff031166df33780aadd3749ffe29a`.
  - Timescale read-only artifact `13560042410`, digest `sha256:94bc46427341d6d0517ce3d268b031c03682723e3186ed15ce5a4ce4a6269416`.
- T2 Freqtrade 2026.9 smoke [42338141694](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42338141694): **SUCCESS**, exact head SHA `1b190ba7562b3843de75894ce68bd6f0ea99b321`; pinned Freqtrade 2026.9 FreqAI image and strategy-load job `128299761176` SUCCESS; artifact `13560551806`, digest `sha256:6103de121988540315d5f54ab30b74243499f9921ef3bd00a42e202883af20bd`.
- These runs verify code SHA `1b190ba...`; current branch HEAD is later documentation-only SHA `8537763...`. Do not relabel the tested code SHA as HEAD.

### Proposed isolated acquisition path — not implemented / not run

- The previously approved one-shot public-read-only 30-day Binance USD-M / OKX export remains unexecuted. This approval does not authorize Canonical SQLite creation/access, Feeder startup, VPS, source switching, or trading.
- A genuine T0 Binance provenance path is technically available without Canonical SQLite: create a uniquely named temporary runner-only SQLite file; initialize only that disposable file with the existing T0 `CandleStore` and `LeaseStore`; use the existing lease-fenced `SQLiteWriteGateway` and `market_data.sync.sync_window()` for the Binance USD-M BTC/USDT:USDT data; then call `market_data.store.read_window()` on that exact temporary file to capture M15/H1 `datasetVersion` values and export the corresponding returned candles. Do not start `FeederRuntime` or `feeder_service`.
- Respect `sync_window()`'s 2,000-candle maximum per invocation: the 30-day M15 window (2,880 rows) must be split into adjacent bounded calls (2,000 + 880); H1 is 720 rows. The read side supports the complete 2,880-row M15 snapshot with `MAX_READ_CANDLES=3000`.
- The current T0 CCXT path converts parsed OHLCV values to strings after CCXT parsing; the README explicitly notes this cannot recover precision already lost by an upstream float parser. Preserve the exact T0 read-window values in the Binance CSV and disclose this source precision limitation; do not describe them as raw exchange decimal strings.
- Fetch OKX public `/api/v5/market/history-candles` for `BTC-USDT-SWAP`; require `confirm=1`; use response `volCcy` (index 6, base-asset BTC) and never contract-count `vol` (index 5). Paginate with the documented maximum 300 rows/request and remain below the public rate limit.
- Binance public USD-M `/fapi/v1/klines` supports bounded `startTime`/`endTime` and a maximum 1,500 rows/request. The actual T0 provenance must still be generated by the isolated T0 store path above, not by substituting the raw CSV hash.
- Network boundary for the future one-shot runner: public endpoints only; no API keys, no proxy/VPN, disable inherited proxy environment; strict timeouts/status/schema checks; fixed BTCUSDT instrument/timeframes; temporary directory only; upload only CSV/manifest/report/log artifacts; cleanup the temporary DB and raw response files at job end.
- Recompute the 30-day half-open UTC window at execution time from the latest fully closed H1 boundary. At this reconciliation time (2026-11-07 04:25Z), the candidate window is [`1791432000000`, `1794024000000`) = 2026-10-08 04:00Z through 2026-11-07 04:00Z; do not reuse it if the actual run starts later.
- Before acquisition is enabled, implement and test the runner's pagination, source identity, closed-candle, rate-limit, no-proxy, temporary-DB isolation, provenance equality, and cleanup contracts. Then run the one-shot GitHub Actions job and preserve exact SHA/run/artifact hashes.
- Current status: T0 CI PASS; T2 Freqtrade 2026.9 strategy-load PASS; acquisition runner NOT IMPLEMENTED; paired real exports NOT AVAILABLE; real parity NOT RUN; Canonical SQLite NOT CREATED; Feeder STOPPED; T2 OKX source unchanged; `ai_execution_enabled=false`.
