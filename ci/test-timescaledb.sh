#!/usr/bin/env bash
set -euo pipefail

CI_PYTHON="${CI_PYTHON:-python3}"
: "${MARKET_DATA_TEST_DATABASE_URL:?Configure the dedicated disposable TimescaleDB test database as GitHub Actions secret MARKET_DATA_TEST_DATABASE_URL}"

# Require an exact, separately configured SHA-256 fingerprint before any DB connection.
"$CI_PYTHON" -m ci.t0_test_database_url --check-environment

export MARKET_DATA_REQUIRE_TIMESCALE=1
export MARKET_DATA_BACKEND=postgres
export MARKET_DATA_POSTGRES_DSN="$MARKET_DATA_TEST_DATABASE_URL"

"$CI_PYTHON" -c 'import psycopg'
"$CI_PYTHON" -m unittest market_data.test_store market_data.test_storage market_data.test_sync market_data.test_api market_data.test_timescaledb -v 2>&1 | tee timescaledb-tests.log
"$CI_PYTHON" -m compileall -q market_data
