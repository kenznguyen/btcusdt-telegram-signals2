#!/usr/bin/env bash
# Read-only Scaleway VPS preflight. Install root-owned and bind as an authorized_keys forced command.
set -euo pipefail
readonly APP_DIR="/home/ubuntu/t0/app"
readonly DB_PATH="/home/ubuntu/t0/app/.data/market-data.sqlite3"
readonly API_PORT="8788"

printf '%s\n' "P1_SSH_PREFLIGHT_VERSION=1"
printf 'HOSTNAME=%s\n' "$(hostname -s 2>/dev/null | tr -cd 'A-Za-z0-9._-')"
printf 'SSH_USER=%s\n' "$(id -un | tr -cd 'A-Za-z0-9._-')"

if SOURCE_SHA="$(git -C "$APP_DIR" rev-parse --verify HEAD 2>/dev/null)" && [[ "$SOURCE_SHA" =~ ^[0-9a-f]{40}$ ]]; then
  printf 'SOURCE_SHA=%s\n' "$SOURCE_SHA"
else
  printf '%s\n' "SOURCE_SHA=NOT_VERIFIED"
fi

feeder_pids=()
for proc in /proc/[0-9]*; do
  [[ -r "$proc/cmdline" ]] || continue
  if tr '\0' ' ' < "$proc/cmdline" 2>/dev/null | grep -Eq '(^|[ /])market_data\.(feeder|feeder_service)([ /]|$)'; then
    feeder_pids+=("${proc##*/}")
  fi
done
if (("${#feeder_pids[@]}" > 0)); then
  printf 'FEEDER_PIDS=%s\n' "$(IFS=,; printf '%s' "${feeder_pids[*]}")"
else
  printf '%s\n' "FEEDER_PIDS=NONE"
fi

listener_endpoints="$(ss -H -ltn "sport = :$API_PORT" 2>/dev/null | awk '{print $4}' | tr '\n' ',' | sed 's/,$//')"
if [[ -z "$listener_endpoints" ]]; then
  printf '%s\n' "API_8788=NOT_LISTENING"
else
  printf 'API_8788_ENDPOINTS=%s\n' "$(printf '%s' "$listener_endpoints" | tr -cd 'A-Za-z0-9.:,_[]-')"
  if awk -v value="$listener_endpoints" 'BEGIN { n=split(value,a,","); for(i=1;i<=n;i++) if(a[i] !~ /^(127\.[0-9]+\.[0-9]+\.[0-9]+|\[::1\]|::1):8788$/) exit 1; }'; then
    printf '%s\n' "API_8788=LOOPBACK_ONLY"
  else
    printf '%s\n' "API_8788=NON_LOOPBACK_LISTENER"
  fi
fi

if [[ -r "$DB_PATH" ]]; then
  db_result="$(python3 - "$DB_PATH" <<'PY'
import sqlite3
import sys
path = sys.argv[1]
try:
    uri = "file:" + path + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=5)
    try:
        connection.execute("PRAGMA query_only=ON")
        result = connection.execute("PRAGMA integrity_check").fetchone()[0]
        print("PASS" if result == "ok" else "FAIL")
    finally:
        connection.close()
except Exception:
    print("ERROR")
PY
)"
  printf 'SQLITE_INTEGRITY=%s\n' "$db_result"
else
  printf '%s\n' "SQLITE_INTEGRITY=NOT_READABLE_OR_MISSING"
fi
printf '%s\n' "P1_SSH_PREFLIGHT_END=1"
