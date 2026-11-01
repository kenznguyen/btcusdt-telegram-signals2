#!/usr/bin/env bash
set -euo pipefail

: "${CM_BUILD_DIR:?Codemagic checkout directory is required}"
: "${CI_PYTHON:?Run ci/setup-python.sh first}"
: "${MARKET_DATA_ACCEPTANCE_DATABASE_URL:?Configure the dedicated staging database in market_data_live_acceptance}"

cd "$CM_BUILD_DIR"
export MARKET_DATA_BACKEND=postgres
export MARKET_DATA_POSTGRES_DSN="$MARKET_DATA_ACCEPTANCE_DATABASE_URL"
export MARKET_DATA_TOKEN=market-data-live-acceptance-read-only

# Refuse databases whose name does not clearly identify an isolated test/staging target.
"$CI_PYTHON" - <<'PY'
import os
from urllib.parse import unquote, urlparse

dsn = os.environ["MARKET_DATA_ACCEPTANCE_DATABASE_URL"]
parsed = urlparse(dsn)
database = unquote(parsed.path.lstrip("/")).lower()
if parsed.scheme not in {"postgres", "postgresql"}:
    raise SystemExit("Acceptance DSN must use PostgreSQL")
if not any(marker in database for marker in ("staging", "acceptance", "test")):
    raise SystemExit("Refusing database name without staging/acceptance/test marker")
PY

# End one full hour behind the current hour so all requested bars are closed.
read -r START_MS END_MS < <("$CI_PYTHON" - <<'PY'
import time
hour = 3_600_000
end_ms = (time.time_ns() // 1_000_000 // hour - 1) * hour
print(end_ms - 24 * hour, end_ms)
PY
)

LOG=market-data-live-acceptance.log
REPORT=market-data-live-acceptance.json
: > "$LOG"
exec > >(tee -a "$LOG") 2>&1

echo "source_sha=$(git rev-parse HEAD)"
echo "market=BTCUSDT exchange=Binance USD-M timeframes=15m,1h"
echo "window_start_ms=$START_MS window_end_ms=$END_MS"

echo "Applying explicit migrations to the dedicated acceptance database"
"$CI_PYTHON" - <<'PY'
import os
from market_data.migrations import migrate
applied, total = migrate(os.environ["MARKET_DATA_POSTGRES_DSN"])
print(f"migrations_applied={applied} migrations_total={total}")
if applied != total:
    raise SystemExit("Migration set is incomplete")
PY

declare -A FIRST_HASH
for timeframe in 15m 1h; do
  echo "Collecting real Binance USD-M $timeframe candles"
  first=$("$CI_PYTHON" -m market_data.sync --backend postgres --timeframe "$timeframe" --start-ms "$START_MS" --end-ms "$END_MS")
  printf 'first_sync_%s=%s\n' "$timeframe" "$first"
  second=$("$CI_PYTHON" -m market_data.sync --backend postgres --timeframe "$timeframe" --start-ms "$START_MS" --end-ms "$END_MS")
  printf 'repeat_sync_%s=%s\n' "$timeframe" "$second"

  FIRST_HASH["$timeframe"]=$(printf '%s' "$first" | "$CI_PYTHON" -c 'import json,sys; print(json.load(sys.stdin)["datasetVersion"])')
  "$CI_PYTHON" - "$first" "$second" "$timeframe" <<'PY'
import json
import sys
first, second, timeframe = map(json.loads, sys.argv[1:]) if False else (json.loads(sys.argv[1]), json.loads(sys.argv[2]), sys.argv[3])
if not first["coverage"]["complete"]:
    raise SystemExit(f"{timeframe}: first sync has missing candles")
if second["inserted"] != 0:
    raise SystemExit(f"{timeframe}: repeat sync was not idempotent")
if first["datasetVersion"] != second["datasetVersion"]:
    raise SystemExit(f"{timeframe}: dataset hash changed on repeat sync")
print(f"{timeframe}_idempotency=PASS inserted_on_repeat=0")
PY
done

# A new Python process exercises the read-only API against the persisted database.
"$CI_PYTHON" - "$START_MS" "$END_MS" "${FIRST_HASH[15m]}" "${FIRST_HASH[1h]}" <<'PY'
import json
import os
import sys
from urllib.parse import urlencode
from market_data.api import application

start, end, hash_15m, hash_1h = sys.argv[1:]
for timeframe, expected_hash in (("15m", hash_15m), ("1h", hash_1h)):
    query = urlencode({"symbol": "BTCUSDT", "timeframe": timeframe, "startMs": start, "endMs": end})
    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/v1/candles",
        "QUERY_STRING": query,
        "HTTP_AUTHORIZATION": "Bearer " + os.environ["MARKET_DATA_TOKEN"],
    }
    status = []
    body = b"".join(application(environ, lambda value, headers: status.append(value)))
    if not status or status[0].split()[0] != "200":
        raise SystemExit(f"{timeframe}: API read failed ({status[0] if status else 'no response'})")
    result = json.loads(body)
    coverage = result["coverage"]
    if not coverage["complete"] or coverage["returned"] != coverage["expected"]:
        raise SystemExit(f"{timeframe}: persisted API window is incomplete")
    if result["datasetVersion"] != expected_hash:
        raise SystemExit(f"{timeframe}: API dataset hash differs from collector output")
    print(f"{timeframe}_api_read=PASS returned={coverage['returned']} hash={result['datasetVersion']}")
PY

"$CI_PYTHON" - "$START_MS" "$END_MS" "${FIRST_HASH[15m]}" "${FIRST_HASH[1h]}" "$REPORT" <<'PY'
import json
import os
import subprocess
import sys
start, end, hash_15m, hash_1h, report = sys.argv[1:]
payload = {
    "sourceSha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "exchange": "binance",
    "market": "BTCUSDT",
    "marketType": "USDT_PERPETUAL",
    "window": {"startMs": int(start), "endMs": int(end)},
    "timeframes": {
        "15m": {"datasetVersion": hash_15m, "apiRead": "PASS", "repeatSyncInserted": 0},
        "1h": {"datasetVersion": hash_1h, "apiRead": "PASS", "repeatSyncInserted": 0},
    },
    "storageBackend": "postgres",
    "target": "dedicated-staging-acceptance-database",
}
with open(report, "w", encoding="utf-8") as stream:
    json.dump(payload, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(f"acceptance_report={report}")
PY

echo "LIVE_COLLECTOR_ACCEPTANCE=PASS"
