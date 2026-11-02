"""Read-only validation of the T0 production feeder configuration.

This audit never builds a runtime, creates a database, starts a feeder, or contacts
an exchange. Existing SQLite files are inspected through mode=ro only.
"""

import importlib.util
import json
import os
import sqlite3
import sys
from pathlib import Path
from urllib.parse import quote

from market_data.feeder import FeederConfig


def _resolve_path(value, label, errors):
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} is required")
        return None
    try:
        return Path(value.strip()).expanduser().resolve()
    except (OSError, RuntimeError, ValueError):
        errors.append(f"{label} is not a valid filesystem path")
        return None


def _inspect_existing_database(path, errors):
    result = {"state": "NOT_INITIALIZED", "integrity": "NOT_RUN"}
    if not path.exists():
        return result
    if not path.is_file():
        errors.append("MARKET_DATA_DB must point to a regular SQLite file")
        result["state"] = "INVALID"
        return result
    if not os.access(path, os.R_OK):
        errors.append("MARKET_DATA_DB file is not readable")
        result["state"] = "INVALID"
        return result
    if not os.access(path, os.W_OK):
        errors.append("MARKET_DATA_DB file is not writable by the feeder runtime")
        result["state"] = "INVALID"
        return result

    uri = path.as_uri() + "?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True, timeout=5)
        try:
            connection.execute("PRAGMA query_only=ON")
            integrity = connection.execute("PRAGMA integrity_check").fetchone()
            result["integrity"] = integrity[0] if integrity else "NO_RESULT"
            if result["integrity"] != "ok":
                errors.append("MARKET_DATA_DB SQLite integrity_check did not return ok")
            tables = {
                row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            missing = {"candles", "feeder_leases"} - tables
            if missing:
                errors.append(
                    "MARKET_DATA_DB is missing required table(s): "
                    + ", ".join(sorted(missing))
                )
                result["state"] = "INVALID"
            else:
                result["state"] = "EXISTING_SCHEMA_VALID"
            result["runtime_status_table"] = (
                "PRESENT" if "feeder_runtime_status" in tables else "NOT_YET_PUBLISHED"
            )
        finally:
            connection.close()
    except (OSError, sqlite3.Error, ValueError):
        errors.append("MARKET_DATA_DB could not be inspected in read-only mode")
        result["state"] = "INVALID"
    return result


def audit_runtime_config(environ=None, repo_root=None):
    values = os.environ if environ is None else environ
    errors = []
    checks = {
        "python_version": sys.version_info >= (3, 10),
        "ccxt_dependency": importlib.util.find_spec("ccxt") is not None,
        "backend": False,
        "canonical_path": False,
        "lease_path_alignment": False,
        "runtime_parameters": False,
        "database_parent": False,
    }
    if not checks["python_version"]:
        errors.append("Python 3.10 or newer is required")
    if not checks["ccxt_dependency"]:
        errors.append("ccxt dependency is not installed")

    backend = values.get("MARKET_DATA_BACKEND", "sqlite").strip().lower()
    checks["backend"] = backend == "sqlite"
    if not checks["backend"]:
        errors.append(
            "Production T0 feeder currently requires MARKET_DATA_BACKEND=sqlite"
        )

    candle_path = _resolve_path(values.get("MARKET_DATA_DB", ""), "MARKET_DATA_DB", errors)
    lease_value = values.get("T0_FEEDER_LEASE_DB", "").strip()
    lease_path = _resolve_path(
        lease_value or values.get("MARKET_DATA_DB", ""),
        "T0_FEEDER_LEASE_DB (defaults to MARKET_DATA_DB)",
        errors,
    )
    checks["canonical_path"] = candle_path is not None
    checks["lease_path_alignment"] = (
        candle_path is not None and lease_path is not None and candle_path == lease_path
    )
    if candle_path is not None and lease_path is not None and candle_path != lease_path:
        errors.append(
            "T0_FEEDER_LEASE_DB must resolve to the same file as MARKET_DATA_DB "
            "for atomic write fencing"
        )

    try:
        config = FeederConfig(
            poll_interval_seconds=int(values.get("T0_FEEDER_POLL_SECONDS", "5")),
            close_grace_seconds=int(values.get("T0_FEEDER_CLOSE_GRACE_SECONDS", "5")),
            retry_max_attempts=int(values.get("T0_FEEDER_RETRY_ATTEMPTS", "5")),
            lease_ttl_seconds=int(values.get("T0_FEEDER_LEASE_TTL_SECONDS", "60")),
            lease_heartbeat_seconds=int(
                values.get("T0_FEEDER_LEASE_HEARTBEAT_SECONDS", "15")
            ),
            timeframes=("15m", "1h"),
        )
        recovery_candles = int(values.get("T0_FEEDER_RECOVERY_CANDLES", "2000"))
        if not 1 <= recovery_candles <= 2000:
            raise ValueError("T0_FEEDER_RECOVERY_CANDLES must be between 1 and 2000")
        checks["runtime_parameters"] = True
        runtime_parameters = {
            "poll_interval_seconds": config.poll_interval_seconds,
            "close_grace_seconds": config.close_grace_seconds,
            "retry_max_attempts": config.retry_max_attempts,
            "lease_ttl_seconds": config.lease_ttl_seconds,
            "lease_heartbeat_seconds": config.lease_heartbeat_seconds,
            "recovery_lookback_candles": recovery_candles,
            "timeframes": list(config.timeframes),
            "owner_id": "EXPLICIT" if values.get("T0_FEEDER_OWNER_ID", "").strip() else "HOST_PID_FALLBACK",
        }
    except (TypeError, ValueError):
        errors.append("One or more T0 feeder numeric settings are invalid")
        runtime_parameters = {}

    database = {"state": "NOT_CHECKED", "integrity": "NOT_RUN"}
    if candle_path is not None:
        parent = candle_path.parent
        checks["database_parent"] = parent.is_dir() and os.access(parent, os.W_OK)
        if not checks["database_parent"]:
            errors.append(
                "MARKET_DATA_DB parent directory must already exist and be writable; "
                "the audit will not create it"
            )
        database = _inspect_existing_database(candle_path, errors)

    root = Path(repo_root).resolve() if repo_root is not None else Path.cwd().resolve()
    return {
        "ok": not errors and all(checks.values()),
        "scope": "read-only configuration and optional existing SQLite schema audit",
        "repository_root_available": root.is_dir(),
        "checks": checks,
        "runtime_parameters": runtime_parameters,
        "database": database,
        "errors": errors,
        "safety": {
            "database_created": False,
            "database_modified": False,
            "feeder_started": False,
            "exchange_contacted": False,
            "secret_values_emitted": False,
        },
    }


def render_report(report):
    result = dict(report)
    result["verdict"] = (
        "T0_FINAL_RUNTIME_CONFIGURATION=PASS"
        if report["ok"]
        else "T0_FINAL_RUNTIME_CONFIGURATION=FAIL"
    )
    return json.dumps(result, indent=2, sort_keys=True)


def main():
    report = audit_runtime_config()
    print(render_report(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
