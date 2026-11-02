# T0 Data Integrity & Candle Continuity Gate

## Scope

This gate audits the canonical SQLite `candles` table for Binance USD-M BTCUSDT perpetual data on M15 (`15m`) and H1 (`1h`). It is independent of the Operational Contract Release Gate.

The audit is read-only. It opens the database with SQLite `mode=ro` and enables `PRAGMA query_only=ON`. It does not insert, update, delete, migrate, repair, vacuum, checkpoint, or otherwise modify canonical data.

## Checks

- Composite candle identity is unique by `exchange, market_type, symbol, timeframe, open_time_ms`, both as a schema constraint and in stored rows.
- Canonical market identity is `binance / USDT_PERPETUAL / BTCUSDT`; supported timeframes are M15 and H1.
- Open timestamps are nonnegative integer UTC epoch milliseconds aligned to the timeframe interval.
- Canonical reads are ordered by timeframe and open time; ingestion rejects duplicate or non-increasing timestamps within an exchange page. SQLite physical row insertion order is not treated as candle chronology, so legitimate historical gap backfills are not falsely rejected.
- OHLCV values are bounded finite decimal strings; prices are positive, volume is nonnegative, and OHLC bounds are internally consistent.
- `available_at_ms` is at or after candle close, and candle close is not later than the audit's `as_of_ms`.
- Missing candle slots are counted independently for M15 and H1. Gaps are reported only between the first and last observed candle; leading/trailing gaps are not inferred without an explicit expected audit window.
- SQLite `PRAGMA integrity_check` must return `ok`.

## Run against a canonical database

From the repository root, with the feeder stopped or with a stable SQLite snapshot:

```bash
python -m ci.t0_data_integrity --db "$MARKET_DATA_DB"
```

The command prints a JSON report and exits nonzero if any issue is found. To make a deterministic test run, pass `--as-of-ms <UTC epoch milliseconds>`.

A report containing `candle_gap` or `duplicate_candle_identity` is a failure. This gate never attempts gap recovery or repairs. Any remediation must be separately authorized and implemented through the canonical fenced writer.

## Codemagic boundary

Workflow: **T0 - Data Integrity & Candle Continuity Gate (read-only)**.

Codemagic runs the isolated unit tests against temporary SQLite fixtures and compiles the audit module. It does not receive or inspect a production/local canonical database, start the feeder, run synchronization, run T0 lifecycle/atomic-fencing/SIGKILL suites, or run Runtime Health Smoke. Therefore a Codemagic PASS proves the audit contract and test behavior, not the integrity of a user's actual database.

## Explicitly not certified

- Continuous production runtime operation or live feeder health.
- Leading/trailing coverage outside the observed candle range.
- Automatic gap recovery or any data mutation.
- T1-T4 read-only enforcement.
- Historical GREEN workflow execution evidence beyond the artifacts already supplied by the user.
