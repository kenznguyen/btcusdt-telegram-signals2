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

## Manual live collector acceptance

The manual workflow `market-data-live-collector-acceptance` is separate from the disposable migration/parity test workflow. It fetches real public BTCUSDT USD-M candles from Binance for a bounded 24-hour window on M15 and H1, writes them to a dedicated PostgreSQL staging database, repeats the exact same sync to prove idempotency, then reads the persisted rows through the read-only `/v1/candles` WSGI application in a fresh Python process.

Before running it, create the Codemagic environment variable group `market_data_live_acceptance` with:

- `MARKET_DATA_ACCEPTANCE_DATABASE_URL`: PostgreSQL/TimescaleDB DSN for a dedicated staging database. The database name must contain `staging`, `acceptance`, or `test`; the runner refuses other database names.
- The database must have TimescaleDB installed and grant the workflow role permission to create the `market_data` schema, tables, and hypertable.

Do not reuse the `market_data_timescale_test` database, production credentials, or production data. This workflow explicitly applies the reviewed migrations to the dedicated acceptance database. It retains its uniquely timestamped acceptance candles for inspection; repeated runs use a new completed 24-hour window. No API keys or trading credentials are used, and no orders are submitted.

The workflow has no push trigger. Start it manually against the intended feature/integration branch after reviewing the source SHA. Acceptance requires complete coverage for both timeframes, zero inserts on the repeat sync, identical dataset hashes, and successful API reads whose hashes match the collector output. Artifacts are `ci-source-sha.txt`, `market-data-live-acceptance.log`, and `market-data-live-acceptance.json`.

This proves live public exchange ingestion into the isolated staging database and process-restart read durability within the acceptance run. It does not certify production deployment, long-term uptime, backup/restore, or production cutover.

