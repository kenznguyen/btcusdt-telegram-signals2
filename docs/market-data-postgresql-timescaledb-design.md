# PostgreSQL / TimescaleDB design for canonical market data

## Status and scope

- Status: **Proposed — documentation only; not an implementation approval**.
- Scope: define a backward-compatible target for the existing `market_data/` SQLite store.
- This document does not authorize schema creation, dependency changes, repository refactors, data movement, database cutover, or production deployment.
- GitHub stores source and pull requests. Codemagic is the execution environment for future validation and migration workflows.

## Existing contract to preserve

The current canonical store is SQLite and serves Binance USDⓈ-M BTCUSDT linear perpetual candles at 15m and 1h. The exact persisted identity constants in `market_data/store.py` are `exchange='binance'`, `market_type='USDT_PERPETUAL'`, and `symbol='BTCUSDT'`; preserve these literal values. `linear perpetual` is the instrument description, not the stored `market_type` enum. Its externally visible contract includes:

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

Stores canonical instrument metadata keyed by exchange, market type, and symbol. The initial row is exactly `('binance', 'USDT_PERPETUAL', 'BTCUSDT')`, representing Binance USDⓈ-M linear perpetual. Do not normalize or rename the existing `USDT_PERPETUAL` value to `linear_perpetual`, and do not broaden supported instruments as part of this database migration.

### `market_data.candles`

The SQLite table physically persists only the identity fields, OHLCV decimal text, and `available_at_ms`. The current `Candle.as_dict()` adds `closeTimeMs`, `isClosed`, `availabilityKind`, `quality`, and `source` as deterministic projection fields; these are not separate SQLite columns. The PostgreSQL adapter must preserve that distinction and emit the same API projection.

Proposed physical columns:

| Column | Type | Contract |
| --- | --- | --- |
| `exchange` | `TEXT` | Exact current value: `binance` |
| `market_type` | `TEXT` | Exact current value: `USDT_PERPETUAL` |
| `symbol` | `TEXT` | Exact current value: `BTCUSDT` |
| `timeframe` | `TEXT` | `15m` or `1h` |
| `open_time_ms` | `BIGINT` | UTC Unix milliseconds; hypertable time dimension |
| `open/high/low/close/volume` | `NUMERIC` | Exact decimal values; validated in application |
| `available_at_ms` | `BIGINT` | First-observed system time; immutable on duplicate import |
| `ingestion_batch_id` | `UUID NULL` | New nullable provenance field; NULL for legacy rows |

The API projection remains:

- `closeTimeMs = openTimeMs + timeframe interval` (exclusive boundary).
- `isClosed = true` (only validated closed candles enter the canonical store).
- `availabilityKind = FIRST_OBSERVED`.
- `quality = VALIDATED`.
- `source = ccxt.binanceusdm`.

These values must not be described as migrated source columns or independently editable facts. If they are ever materialized in PostgreSQL for operational reasons, they must be constrained to these current deterministic values and must not alter the public projection.

Primary/unique identity is `(exchange, market_type, symbol, timeframe, open_time_ms)`. Since TimescaleDB requires unique indexes on a hypertable to include the partitioning dimension, `open_time_ms` remains part of the key.

Use `open_time_ms BIGINT` as the integer time dimension. The initial design proposes a 30-day chunk interval (`2592000000` milliseconds), subject to staging benchmark before production use. The table is converted to a hypertable only after the target schema and extension are available.

Required database constraints should mirror existing application validation:

- Exact identity vocabulary for this initial dataset: `exchange='binance'`, `market_type='USDT_PERPETUAL'`, `symbol='BTCUSDT'`.
- Supported timeframe and timestamp alignment: 900,000 ms for 15m; 3,600,000 ms for 1h.
- `is_closed = TRUE`.
- Positive OHLC prices; non-negative volume.
- OHLC consistency: high is not below open/close/low; low is not above open/close/high.
- `available_at_ms` cannot precede the exclusive candle close boundary.
- Required source/quality/availability fields are non-empty and from the supported vocabulary.

Keep Decimal digit/exponent bounds in Python as well; SQL constraints are defense in depth, not a replacement. Avoid a fixed NUMERIC precision/scale that could round legacy values.

### Normative initial DDL shape

The following is the proposed first-version table contract, not an instruction to execute it in this PR. It intentionally stores only source-persisted fields plus nullable ingestion provenance:

```sql
CREATE SCHEMA IF NOT EXISTS market_data;

CREATE TABLE market_data.candles (
    exchange TEXT NOT NULL CHECK (exchange = 'binance'),
    market_type TEXT NOT NULL CHECK (market_type = 'USDT_PERPETUAL'),
    symbol TEXT NOT NULL CHECK (symbol = 'BTCUSDT'),
    timeframe TEXT NOT NULL CHECK (timeframe IN ('15m', '1h')),
    open_time_ms BIGINT NOT NULL CHECK (open_time_ms >= 0),
    open NUMERIC NOT NULL CHECK (open > 0),
    high NUMERIC NOT NULL CHECK (high > 0),
    low NUMERIC NOT NULL CHECK (low > 0),
    close NUMERIC NOT NULL CHECK (close > 0),
    volume NUMERIC NOT NULL CHECK (volume >= 0),
    available_at_ms BIGINT NOT NULL,
    ingestion_batch_id UUID NULL,
    PRIMARY KEY (exchange, market_type, symbol, timeframe, open_time_ms),
    CHECK (
        open_time_ms <= 9223372036854775807 -
            CASE timeframe WHEN '15m' THEN 900000 ELSE 3600000 END
    ),
    CHECK (
        open_time_ms % CASE timeframe
            WHEN '15m' THEN 900000 ELSE 3600000
        END = 0
    ),
    CHECK (
        available_at_ms >= open_time_ms +
            CASE timeframe WHEN '15m' THEN 900000 ELSE 3600000 END
    ),
    CHECK (high >= GREATEST(open, low, close)),
    CHECK (low <= LEAST(open, high, close))
);

SELECT create_hypertable(
    'market_data.candles',
    'open_time_ms',
    chunk_time_interval => 2592000000,
    if_not_exists => TRUE
);
```

The table definition must be applied by a versioned migration in a later implementation PR after checking the target TimescaleDB version and staging behavior. The primary key includes the integer time partition column. No additional unique constraint may omit `open_time_ms`. Do not add indexes speculatively; benchmark the actual bounded `read_window` and `as_of_ms` query before adding any secondary index (and any hypertable unique index must still include the partitioning column).

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
