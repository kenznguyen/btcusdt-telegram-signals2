#!/usr/bin/env bash
# P1 Scaleway preflight: bounded, read-only evidence collection.
# Install as /usr/local/sbin/t0-readonly-preflight and force it from authorized_keys.
set -u
umask 077

readonly T0_APP_DIR="/home/ubuntu/t0/app"
readonly T0_DB_PATH="/home/ubuntu/t0/app/.data/market-data.sqlite3"
readonly API_PORT="8788"

emit() {
  printf '%s=%s\n' "$1" "$2"
}

printf '%s\n' "P1_SSH_PREFLIGHT_VERSION=1"

emit "HOSTNAME" "$(hostname 2>/dev/null || printf 'UNAVAILABLE')"
emit "SSH_USER" "$(id -un 2>/dev/null || printf 'UNAVAILABLE')"

source_sha="UNKNOWN"
if source_sha="$(git -C "$T0_APP_DIR" rev-parse --verify HEAD 2>/dev/null)" &&
   [[ "$source_sha" =~ ^[0-9a-f]{40}$ ]]; then
  emit "SOURCE_SHA" "$source_sha"
else
  emit "SOURCE_SHA" "UNKNOWN"
fi

feeder_pids="NONE"
if command -v pgrep >/dev/null 2>&1; then
  detected_pids="$(pgrep -f '[m]arket_data\.feeder' 2>/dev/null || true)"
  if [[ -n "$detected_pids" ]]; then
    feeder_pids="$(printf '%s' "$detected_pids" | tr '\n' ' ' | sed 's/[[:space:]]*$//')"
  fi
fi
emit "FEEDER_PIDS" "$feeder_pids"

api_state="NOT_LISTENING"
if command -v ss >/dev/null 2>&1; then
  listeners="$(ss -H -ltn "sport = :$API_PORT" 2>/dev/null || true)"
  if [[ -n "$listeners" ]]; then
    if printf '%s\n' "$listeners" | awk '{print $4}' | grep -Ev '^127\.0\.0\.1:' >/dev/null; then
      api_state="NON_LOOPBACK_LISTENER"
    else
      api_state="LOOPBACK_LISTENER"
    fi
  fi
fi
emit "API_8788" "$api_state"

sqlite_state="FAIL"
if [[ -r "$T0_DB_PATH" ]] && command -v python3 >/dev/null 2>&1; then
  if python3 - "$T0_DB_PATH" <<'PY'
import sqlite3
import sys

path = sys.argv[1]
try:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5)
    try:
        connection.execute("PRAGMA query_only=ON")
        result = connection.execute("PRAGMA integrity_check").fetchone()
        if result is None or result[0] != "ok":
            raise RuntimeError("integrity check did not return ok")
    finally:
        connection.close()
except Exception:
    raise SystemExit(1)
PY
  then
    sqlite_state="PASS"
  fi
fi
emit "SQLITE_INTEGRITY" "$sqlite_state"

printf '%s\n' "P1_SSH_PREFLIGHT_END=1"

# A preflight is successful only when the evidence is complete and safe.
[[ "$source_sha" =~ ^[0-9a-f]{40}$ ]] || exit 1
[[ "$sqlite_state" == "PASS" ]] || exit 1
[[ "$api_state" != "NON_LOOPBACK_LISTENER" ]] || exit 1
exit 0
