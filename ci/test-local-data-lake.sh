#!/usr/bin/env bash
set -euo pipefail

: "${CM_BUILD_DIR:?Codemagic checkout is required}"
cd "$CM_BUILD_DIR"
exec > >(tee local-smoke-tests.log) 2>&1

python3 --version
docker compose version
command -v timeout >/dev/null
python3 -m data_lake.local_setup --port 8788
lake_compose=(docker compose --project-name chart-lake-smoke \
  --env-file .data/local-lake.env -f deploy/data-lake/compose.yaml)
# Quiet validation never renders the resolved environment or its generated secrets.
"${lake_compose[@]}" config --quiet

cleanup_local_lake() {
  lake_status=$?
  trap - EXIT
  if [ "$lake_status" -ne 0 ]; then
    # These processes emit fixed diagnostics; raw PostgreSQL logs are excluded.
    "${lake_compose[@]}" logs --no-color --tail 200 api bootstrap || true
  fi
  # Retain named volumes; the disposable CI machine owns their eventual cleanup.
  "${lake_compose[@]}" down --remove-orphans || true
  exit "$lake_status"
}
trap cleanup_local_lake EXIT

"${lake_compose[@]}" up -d --build
lake_ready=0
lake_deadline=$((SECONDS + 120))
while (( SECONDS < lake_deadline )); do
  lake_remaining=$((lake_deadline - SECONDS))
  if timeout "$lake_remaining" python3 -m data_lake.local_setup --check > .data/local-lake-status.json; then
    lake_ready=1
    break
  fi
  lake_remaining=$((lake_deadline - SECONDS))
  if (( lake_remaining > 0 )); then
    sleep "$((lake_remaining < 2 ? lake_remaining : 2))"
  fi
done
if [ "$lake_ready" -ne 1 ]; then
  printf '%s\n' 'Local API did not become ready within 120 seconds.' >&2
  exit 1
fi

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
assert report['service'] == 'canonical-data-lake'
assert report['ready'] is True
assert report['freshData'] is False, 'An empty local trial must not manufacture candles'
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
