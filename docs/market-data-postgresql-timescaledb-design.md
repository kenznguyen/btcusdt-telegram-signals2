# PostgreSQL / TimescaleDB design for canonical market data

## Status and scope

- Status: **Proposed — documentation only; not an implementation approval**.
- Scope: define a backward-compatible target for the existing `market_data/` SQLite store.
- This document does not authorize schema creation, dependency changes, repository refactors, data movement, database cutover, or production deployment.
- GitHub stores source and pull requests. Codemagic is the execution environment for future validation and migration workflows.

## Existing contract to preserve

The current canonical store is SQLite and serves Binance USDⓈ-M linear perpetual BTCUSDT candles at 15m and 1h. Its externally visible contract includes:

- Candle identity: `exchange`, `market_type`, `symbol`, `timeframe`, `open_time_ms`.
- OHLCV values are persisted as decimal text, validated with Python `Decimal`; do not introduce binary-float persistence or silent rounding.
- Closed-candle semantics and UTC millisecond timestamps.
- `available_at_ms` records when the system first observed the row. Historical imports must not fabricate earlier availability.
- `read_window(start_ms, end_ms, as_of_ms=...)` uses a half-open time range and point-in-time availability filtering.
- Gaps, duplicate idempotency, conflicting duplicate rejection, deterministic ordering, and `datasetVersion` SHA-256 semantics.
- Read API remains read-only, authenticated, bounded, and must not create a missing database.

The current `MARKET_DATA_DB` SQLite file is also used by the paper ledger. `paper_execution/ledger.py` owns paper state/order/book/audit/strategy-state and risk/equity history tables; `pipeline/api.py` reads both market data and paper state. Therefore, changing `MARKET_DATA_DB` to a PostgreSQL DSN is not backward-compatible and is explicitly out of scope.

## Proposed architecture

Introduce a repository boundary without changing callers' domain contract:

- `SQLiteRepository`: retain the current SQLite implementation and remain the default/rollback path.
- `PostgresRepository`: a separate adapter for canonical market data only.
- Shared domain types and validation: Candle, Decimal validation, query bounds, coverage/gaps, duplicate/conflict rules, and canonical serialization.
- Configuration remains explicit:
  - `MARKET_DATA_DB`: existing SQLite file path; retain its current meaning during transition.
  - `MARKET_DATA_DATABASE_URL`: optional PostgreSQL/TimescaleDB connection for market data only.
  - `PAPER_DB_PATH`: explicit future paper-ledger SQLite path after a separately reviewed configuration split.
  - `MARKET_DATA_TOKEN`: read API authentication; unchanged semantics.

No dual-write to two independent databases is proposed as a correctness mechanism: there is no distributed atomic transaction. Any mirror/shadow stage must be replayable and reconcile from the SQLite source of truth.

## Target PostgreSQL / TimescaleDB schema

Use a dedicated `market_data` schema. PostgreSQL `NUMERIC` without a fixed precision/scale is proposed for OHLCV to avoid database-side scale rounding. Application-level Decimal validation limits remain authoritative.

### `market_data.schema_migrations`

Tracks ordered, immutable migration identifiers, checksums, and application timestamps. A migration identifier may be applied once; a changed checksum for an already-applied identifier is a hard error.

### `market_data.instruments`

Stores canonical instrument metadata keyed by exchange, market type, and symbol. The initial supported instrument remains Binance USDⓈ-M linear perpetual BTCUSDT. Do not broaden supported instruments as part of this database migration.

### `market_data.candles`

Proposed columns:

| Column | Type | Contract |
| --- | --- | --- |
| `exchange` | `TEXT` | Canonical exchange identifier |
| `market_type` | `TEXT` | `linear_perpetual` for the current dataset |
| `symbol` | `TEXT` | Canonical symbol, initially `BTCUSDT` |
| `timeframe` | `TEXT` | `15m` or `1h` |
| `open_time_ms` | `BIGINT` | UTC Unix milliseconds; hypertable time dimension |
| `close_time_ms` | `BIGINT` | Exclusive candle boundary |
| `open/high/low/close/volume` | `NUMERIC` | Exact decimal values; validated in application |
| `is_closed` | `BOOLEAN` | Must be true for canonical rows |
| `available_at_ms` | `BIGINT` | First-observed system time; immutable on duplicate import |
| `availability_kind` | `TEXT` | Existing availability classification |
| `quality` | `TEXT` | Existing validation quality classification |
| `source` | `TEXT` | Existing source identifier |
| `ingestion_batch_id` | `UUID NULL` | Nullable for legacy rows with no batch provenance |

Primary/unique identity is `(exchange, market_type, symbol, timeframe, open_time_ms)`. Since TimescaleDB requires unique indexes on a hypertable to include the partitioning dimension, `open_time_ms` remains part of the key.

Use `open_time_ms BIGINT` as the integer time dimension. The initial design proposes a 30-day chunk interval (`2592000000` milliseconds), subject to staging benchmark before production use. The table is converted to a hypertable only after the target schema and extension are available.

Required database constraints should mirror existing application validation:

- Supported timeframe and timestamp alignment: 900,000 ms for 15m; 3,600,000 ms for 1h.
- `is_closed = TRUE`.
- Positive OHLC prices; non-negative volume.
- OHLC consistency: high is not below open/close/low; low is not above open/close/high.
- `available_at_ms` cannot precede the exclusive candle close boundary.
- Required source/quality/availability fields are non-empty and from the supported vocabulary.

Keep Decimal digit/exponent bounds in Python as well; SQL constraints are defense in depth, not a replacement. Avoid a fixed NUMERIC precision/scale that could round legacy values.

### Supporting tables (future-compatible, not required for the first cutover)

- `market_data.ingestion_batches`: source, requested window, observed server time, status, row counts, and source artifact hashes.
- `market_data.dataset_snapshots`: immutable dataset-window manifest and canonical dataset hash.

Do not fabricate batch identifiers or provenance for legacy SQLite rows. Leave `ingestion_batch_id` NULL when the source does not contain that evidence.

Do not add cross-table foreign keys from the hypertable to regular tables without confirming the exact TimescaleDB version and its constraints. Validate instrument identity at the repository/application boundary in the first version.

## Compatibility and parity requirements

Both adapters must expose the same logical operations and results. Preserve the existing public API and response schema; no caller should need to know which adapter served a query.

Important parity rule: PostgreSQL `NUMERIC` values must be converted to the same canonical decimal strings used by SQLite before JSON serialization and dataset hashing. The same logical window and `as_of_ms` must produce identical candle values, gaps, ordering, and `datasetVersion`.

SQLite remains the rollback source until PostgreSQL parity is demonstrated. The paper ledger remains on SQLite in this phase; its schema and transaction semantics are not migrated by this design.

## Migration sequence (future PRs only)

1. **Baseline and backup:** use SQLite's consistent backup API; run `PRAGMA integrity_check`; record table counts, key ranges, gap reports, decimal samples, and canonical dataset hashes. Separately inventory paper-ledger tables and state.
2. **Provision staging:** create a dedicated PostgreSQL/TimescaleDB staging database, extension, least-privilege roles, migration history, and target schema.
3. **Copy snapshot:** import a consistent SQLite snapshot in bounded batches. Preserve all key fields, Decimal values, `available_at_ms`, quality/source metadata, and NULL legacy batch provenance.
4. **Verify:** compare row counts, unique keys, timestamp ranges, OHLCV values, availability, gaps, and canonical dataset hashes for multiple windows and `as_of_ms` cutoffs.
5. **Shadow read:** SQLite remains authoritative. Compare read responses from both adapters using the same query set; record mismatches and do not silently prefer PostgreSQL.
6. **Controlled cutover:** pause ingestion, apply a final delta, rerun parity checks, then switch only the market-data repository configuration. Keep the SQLite backup and rollback route intact.
7. **Post-cutover observation:** retain SQLite until an explicit retention/retirement review. Do not enable automatic retention, compression, or columnstore in the initial migration.

Each executable stage requires its own implementation PR and Codemagic run. This design PR does not run migration or provision infrastructure.

## Explicit non-goals

- Migrating the paper ledger or its risk/equity history.
- Changing RSI/ADX/Smart DCA, Core/AI signal logic, risk limits, position sizing, OOS protocol, model artifacts, or strategy parameters.
- Changing market source, symbol, timeframe, candle semantics, or API response fields.
- Adding live exchange orders, credentials, or automatic trading.
- Deleting, rewriting, backfilling, or fabricating historical candle provenance.
- Enabling retention, compression, continuous aggregates, or production cutover.
- Modifying Codemagic workflows in this documentation-only phase.
