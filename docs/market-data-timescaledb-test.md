# T0 PostgreSQL / TimescaleDB isolated acceptance

T0 supports SQLite as its default backend and PostgreSQL/TimescaleDB as an
explicit opt-in backend. This document describes the isolated integration-test
contract; it does not configure a hosted runner or authorize production
migration.

## Test database requirements

- Use a dedicated disposable TimescaleDB test database.
- The test role may create the `market_data` schema, tables and hypertable.
- Never reuse production credentials or production data.
- Test rows must be uniquely keyed and cleaned up after each test.
- Supply the DSN only through a masked local/CI environment variable:
  `MARKET_DATA_POSTGRES_DSN`.

## Runtime backend configuration

- Default: `MARKET_DATA_BACKEND=sqlite` and `MARKET_DATA_DB=/path/to/candles.sqlite3`.
- Opt-in PostgreSQL: `MARKET_DATA_BACKEND=postgres` and
  `MARKET_DATA_POSTGRES_DSN` supplied as a protected environment variable.
- An unknown backend or missing PostgreSQL DSN must fail closed; it must never
  silently fall back to SQLite.
- The API and ingestion CLI use the same storage factory and contract.

## Migration policy

Storage constructors, API startup, API reads and ingestion do not run DDL or
migrations. Provision PostgreSQL schema only through the explicit migration
runner after reviewing the target database:

```bash
MARKET_DATA_POSTGRES_DSN="$MARKET_DATA_POSTGRES_DSN" \
  python -c 'import os; from market_data.migrations import migrate; print(migrate(os.environ["MARKET_DATA_POSTGRES_DSN"]))'
```

Run this command only as a separately authorized maintenance action against
the intended database. Never point it at production as part of application
startup or routine CI.

## Acceptance evidence

Run the SQLite/factory/API/synchronization regression suites on every change.
Run PostgreSQL/TimescaleDB integration tests only when a dedicated disposable
database is explicitly available. Record the source SHA, test database class
(not its credentials), test results and any cleanup verification. Do not infer
production readiness from a successful isolated integration test.
