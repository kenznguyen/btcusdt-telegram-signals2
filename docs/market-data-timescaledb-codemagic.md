# Codemagic TimescaleDB integration gate

The workflow `market-data-timescaledb` uses a dedicated disposable TimescaleDB test database. It never provisions, migrates, or writes to production.

Before running it, create the Codemagic environment variable group `market_data_timescale_test` and add:
- `MARKET_DATA_TEST_DATABASE_URL`: secret PostgreSQL URI pointing to a dedicated TimescaleDB test database.

The test database must have the TimescaleDB extension available and the test role must be allowed to create the `market_data` schema, tables, and hypertable. Do not reuse production credentials or data. The integration suite writes temporary test candles into the database; use a dedicated database that can be reset.

The workflow sets `MARKET_DATA_REQUIRE_TIMESCALE=1`, so missing credentials, psycopg, or the extension fails the run rather than silently skipping the integration tests.

GitHub stores source. Codemagic executes the workflow. The workflow is manual until the dedicated test database and secret group have been configured.
