# D07.5 — PAPER Position Projection from Cutover and Execution History

Date: 2026-11-14  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/core-operational-proof-20261112`  
Disposition: **PURE PROJECTION + CI PASS / DATABASE ADAPTER NOT IMPLEMENTED**

## Scope

Added a pure, fail-closed projection that converts immutable per-strategy cutover snapshots, execution-journal FILL events and declared VERIFIED EXECUTION coverage into as-of position snapshots at funding settlement times. Output matches the position input contract consumed by `funding_model.py`.

No database is opened or mutated by this pure function. No VPS, T0, production database, exchange credentials, real account data, network access, orders or runtime scheduler are used.

## Contract

Added:
- `paper_execution/funding_position_projection.py`
- `paper_execution/test_funding_position_projection.py`

The projector:
- requires exactly one cutover snapshot for each of `STRATEGY_CORE`, `AI_FREQAI`, and `LEGACY_UNATTRIBUTED`, all from the same cutover and timestamp;
- validates the cutover snapshot canonical payload against its stored fields;
- validates execution event canonical JSON and recomputes each event SHA-256;
- replays only FILL events strictly before each settlement; unsupported event types fail closed;
- requires contiguous, non-overlapping, declared VERIFIED EXECUTION coverage from the cutover timestamp through settlement+1ms;
- rejects late events, events recorded beyond the coverage watermark, invalid fee currency, missing coverage, gaps, future evidence and fills exactly at settlement (ambiguous ordering);
- derives deterministic position snapshot IDs from cutover, included event hashes and coverage evidence;
- returns signed position quantities as of each settlement, suitable for the PAPER funding model.

The change to `account_history.replay_ledger_events` is backward-compatible: UTC-day alignment remains required by default; the projector explicitly opts out because funding settlements occur at intraday timestamps.

## Exact-source CI evidence

- TDD RED: run [43522055968](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43522055968), source `42c0a266f46ebb7de4cfa4a2b9354a3aacccccfb`, failed because the projector implementation had not yet been added.
- Final GREEN: run [43522246798](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43522246798), SUCCESS, source SHA `5348e42f508c4864c7629121a4b5356cc68be855`.
- Focused position projection tests: **19/19 PASS**.
- Funding model tests: **19/19 PASS**.
- Binance public funding parser tests: **19/19 PASS**.
- D07.2 provenance tests: **17/17 PASS**.
- Full PaperLedger regression: **540/540 PASS** in 140.597s.
- Artifact `14084001315`, name `dual-ledger-bootstrap-proof-5348e42f508c4864c7629121a4b5356cc68be855`, 16,012 bytes, GitHub ZIP digest `sha256:c8852603a60fede650961ced447f7e2cdec2f1d4911e2234c4520a6e521c48e4`, expires 2026-11-20T22:48:24Z.

## Limitations and next gates

- The pure projector currently accepts caller-supplied cutover/event/coverage rows; a read-only SQLite adapter that loads these exact rows from the PAPER ledger has not been implemented.
- The function replays event history for each settlement independently. Before using large populations, refactor to incremental multi-settlement replay to avoid repeated work.
- `VERIFIED` coverage and payload hashes are validated as declared ledger evidence; this does not independently prove that every execution event was captured.
- No end-to-end workflow yet joins D07.2 byte readback, public page parser, SQLite position projection, expected funding population, independently generated observed ledger events, persisted reconciliation and VERIFIED funding coverage.

D07.5 pure projection and CI: **PASS**. D07 overall: **PARTIAL**.
