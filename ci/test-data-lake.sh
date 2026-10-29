#!/usr/bin/env bash
set -euo pipefail

: "${CM_BUILD_DIR:?Codemagic checkout is required}"
: "${CI_PYTHON:?Run ci/setup-python.sh first}"
cd "$CM_BUILD_DIR"
lake_phase="dependency imports"
trap 'printf "Data-lake CI failed during: %s\n" "$lake_phase" >&2' ERR
"$CI_PYTHON" -c 'import psycopg, pyarrow, pandas, fastapi, httpx'
lake_phase="PostgreSQL installation"
if ! brew list --versions postgresql@17 >/dev/null 2>&1; then
  brew install postgresql@17
fi
lake_pg_bin="$(brew --prefix postgresql@17)/bin"
lake_pg_dir="$(mktemp -d /tmp/chart-lake-pg.XXXXXX)"
cleanup_lake_postgres() {
  "$lake_pg_bin/pg_ctl" -D "$lake_pg_dir/data" -m fast -w stop >/dev/null 2>&1 || true
  if [ -f "$lake_pg_dir/server.log" ]; then
    cp "$lake_pg_dir/server.log" "$CM_BUILD_DIR/postgres-server.log" || true
  fi
  rm -rf "$lake_pg_dir"
}
trap cleanup_lake_postgres EXIT
# Isolated, disposable localhost-only CI database; no production credentials.
lake_phase="PostgreSQL initialization"
"$lake_pg_bin/initdb" -D "$lake_pg_dir/data" -U data_lake_ci --no-locale --encoding=UTF8 --auth=trust >/dev/null
lake_phase="PostgreSQL startup"
"$lake_pg_bin/pg_ctl" -D "$lake_pg_dir/data" -l "$lake_pg_dir/server.log" \
  -o "-F -p 55439 -h 127.0.0.1 -k $lake_pg_dir" -w start
lake_phase="test database creation"
"$lake_pg_bin/createdb" -h 127.0.0.1 -p 55439 -U data_lake_ci data_lake_test
export DATA_LAKE_TEST_POSTGRES="postgresql://data_lake_ci@127.0.0.1:55439/data_lake_test"
export DATA_LAKE_REQUIRE_POSTGRES=1
lake_phase="PostgreSQL integration tests"
"$CI_PYTHON" -m unittest market_data.test_postgres -v 2>&1 | tee postgres-tests.log
lake_phase="API and Feather export tests"
"$CI_PYTHON" -m unittest discover -s data_lake -p 'test_*.py' -v 2>&1 | tee data-lake-tests.log
lake_phase="CLI and syntax checks"
"$CI_PYTHON" -m data_lake --help
"$CI_PYTHON" -m data_lake.export --help
"$CI_PYTHON" -m data_lake.refresh --help
"$CI_PYTHON" -m compileall -q data_lake market_data pipeline freqai_bridge
