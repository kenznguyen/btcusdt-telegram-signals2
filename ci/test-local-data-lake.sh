#!/usr/bin/env bash
set -euo pipefail

: "${CM_BUILD_DIR:?Codemagic checkout is required}"
cd "$CM_BUILD_DIR"
exec > >(tee local-smoke-tests.log) 2>&1

# This job owns the managed Linux daemon, never an inherited remote context.
unset DOCKER_CONTEXT DOCKER_TLS DOCKER_TLS_VERIFY DOCKER_CERT_PATH COMPOSE_PROFILES
export DOCKER_HOST=unix:///var/run/docker.sock
lake_compose=(docker --host "$DOCKER_HOST" compose --project-name chart-lake-smoke \
  --env-file .data/local-lake.env -f deploy/data-lake/compose.yaml)

cleanup_local_lake() {
  lake_status=$?
  trap - EXIT
  if [ -f .data/local-lake.env ] && [ ! -L .data/local-lake.env ]; then
    if [ "$lake_status" -ne 0 ]; then
      # These processes emit fixed diagnostics; raw PostgreSQL logs are excluded.
      "${lake_compose[@]}" logs --no-color --tail 200 api bootstrap || true
    fi
    # Retain named volumes; the disposable CI machine owns their eventual cleanup.
    "${lake_compose[@]}" down --remove-orphans || true
  fi
  exit "$lake_status"
}
trap cleanup_local_lake EXIT

python3 --version
mkdir -p .data
# The launcher owns preflight, quiet configuration, build/start and readiness.
# Its stdout contract is safe JSON; progress and diagnostics go to stderr.
python3 -m data_lake.local_trial --project-name chart-lake-smoke \
  --port 8788 --wait-seconds 120 | tee .data/local-lake-status.json

"${lake_compose[@]}" ps --all --services > .data/local-lake-services.txt
python3 - <<'PY'
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, ProxyHandler, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


opener = build_opener(ProxyHandler({}), NoRedirect())

report = json.loads(Path('.data/local-lake-status.json').read_text())
assert report['ok'] is True
assert report['dataRequested'] is False, 'Smoke test must not request exchange data'
assert report['api']['service'] == 'canonical-data-lake'
assert report['api']['ready'] is True
assert report['api']['freshData'] is False, 'An empty local trial must not manufacture candles'
services = set(Path('.data/local-lake-services.txt').read_text().splitlines())
assert {'postgres', 'bootstrap', 'api'} <= services
assert 'collector' not in services, 'Smoke test must not start an exchange collector'
with opener.open('http://127.0.0.1:8788/health', timeout=5) as response:
    health = json.load(response)
assert health['ok'] is True and health['service'] == 'canonical-data-lake'
try:
    response = opener.open('http://127.0.0.1:8788/ready', timeout=5)
except HTTPError as error:
    try:
        assert error.code == 401
    finally:
        error.close()
else:
    response.close()
    raise AssertionError('Readiness endpoint must require authentication')
print('Local Docker smoke test passed: storage ready, empty data explicit, API authenticated, collector stopped.')
PY
