#!/usr/bin/env bash
set -euo pipefail

: "${CM_BUILD_DIR:?Codemagic checkout is required}"
: "${CI_PYTHON:?Run ci/setup-python.sh first}"
: "${MARKET_DATA_TEST_DATABASE_URL:?Configure the dedicated TimescaleDB test database in Codemagic}"
cd "$CM_BUILD_DIR"
export MARKET_DATA_REQUIRE_TIMESCALE=1
export MARKET_DATA_BACKEND=postgres
export MARKET_DATA_POSTGRES_DSN="$MARKET_DATA_TEST_DATABASE_URL"
"$CI_PYTHON" -c 'import psycopg'
"$CI_PYTHON" -m unittest market_data.test_store market_data.test_storage market_data.test_sync market_data.test_api market_data.test_timescaledb -v 2>&1 | tee timescaledb-tests.log
"$CI_PYTHON" -m compileall -q market_data
