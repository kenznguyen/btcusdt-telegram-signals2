# Codemagic TimescaleDB integration gate

The workflow `market-data-timescaledb` uses a dedicated disposable TimescaleDB test database. It never provisions, migrates, or writes to production.

## Codemagic test secret

Create the environment variable group `market_data_timescale_test` and add:

- `MARKET_DATA_TEST_DATABASE_URL`: secret PostgreSQL URI pointing to a dedicated TimescaleDB test database.

The test database must have the TimescaleDB extension available and the test role must be allowed to create the `market_data` schema, tables, and hypertable. Do not reuse production credentials or data. Integration tests write uniquely keyed temporary test candles and remove those rows after each test.

The workflow maps the secret to `MARKET_DATA_POSTGRES_DSN` only inside the Codemagic shell process. It does not print the DSN or write it into GitHub, artifacts, or source files.

## Runtime backend configuration

- Default: `MARKET_DATA_BACKEND=sqlite` and `MARKET_DATA_DB=/path/to/candles.sqlite3`. Existing deployments remain on SQLite without configuration changes.
- Opt-in PostgreSQL: `MARKET_DATA_BACKEND=postgres` and `MARKET_DATA_POSTGRES_DSN` supplied as a masked runtime secret.
- An unknown backend or missing PostgreSQL DSN fails closed. It never silently falls back to SQLite.
- The API and ingestion CLI use the same factory and storage contract.

## Migration policy

Storage constructors, API startup, API reads, and ingestion do not run DDL or migrations. Provision the PostgreSQL schema only through the explicit migration runner after reviewing the target database:

```bash
MARKET_DATA_POSTGRES_DSN="$MARKET_DATA_POSTGRES_DSN" \
  python -c 'import os; from market_data.migrations import migrate; print(migrate(os.environ["MARKET_DATA_POSTGRES_DSN"]))'
```

Run that command as a separately authorized maintenance action against the intended database. Never point it at production as part of an application startup or routine Codemagic test.

## Codemagic validation

The branch-triggered `market-data-timescaledb` workflow sets `MARKET_DATA_REQUIRE_TIMESCALE=1`, maps the test secret to the runtime DSN variable, and runs:

- SQLite storage and API regression tests.
- Factory selection, missing configuration, and fail-closed tests.
- Ingestion/sync tests.
- TimescaleDB API read and connection-error tests.
- PostgreSQL ingestion tests and SQLite/PostgreSQL parity tests.
- Python compile checks.

The `canonical-market-data` workflow runs the SQLite/factory/API regression suite on pushes to the integration branch.

GitHub stores source. Codemagic executes the workflows. Verify the Codemagic source SHA against the PR head SHA before accepting the validation result.
