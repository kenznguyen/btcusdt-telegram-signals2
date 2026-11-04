"""T0 feeder health HTTP API.

The legacy Telegram webhook and backtest dashboard runtime are intentionally
kept outside this repository's T0 application boundary.
"""

import os
import time

from flask import Flask, jsonify

from market_data.feeder import HealthEvaluator
from market_data.feeder_status import FeederRuntimeStatusStore

app = Flask(__name__)


def _feeder_health_result():
    clock = app.config.get("T0_HEALTH_CLOCK")
    try:
        now_ms = clock() if callable(clock) else time.time_ns() // 1_000_000
    except Exception:
        now_ms = time.time_ns() // 1_000_000

    provider = app.config.get("T0_HEALTH_SNAPSHOT_PROVIDER")
    try:
        if callable(provider):
            snapshot = provider()
        else:
            db_path = (
                app.config.get("T0_HEALTH_RUNTIME_STATUS_DB")
                or os.getenv("MARKET_DATA_DB", "").strip()
            )
            if not db_path:
                snapshot = {
                    "process_running": True,
                    "startup_complete": False,
                    "storage_readable": False,
                    "storage_writable": False,
                    "lease_valid": False,
                    "fatal_error": False,
                }
            else:
                snapshot = FeederRuntimeStatusStore(db_path).snapshot(now_ms)
                if snapshot is None:
                    snapshot = {
                        "process_running": True,
                        "startup_complete": False,
                        "storage_readable": True,
                        "storage_writable": True,
                        "lease_valid": False,
                        "fatal_error": False,
                        "runtime_state": "STARTING",
                    }
    except Exception:
        app.logger.exception("T0 health runtime status read failed")
        snapshot = {
            "process_running": True,
            "startup_complete": False,
            "storage_readable": False,
            "storage_writable": False,
            "lease_valid": False,
            "fatal_error": True,
            "runtime_state": "FAILED",
        }

    try:
        result = HealthEvaluator().evaluate(snapshot, now_ms=now_ms)
    except Exception:
        app.logger.exception("T0 health evaluation failed")
        result = HealthEvaluator().evaluate(
            {
                "process_running": True,
                "startup_complete": False,
                "storage_readable": False,
                "storage_writable": False,
                "lease_valid": False,
                "fatal_error": True,
            },
            now_ms=time.time_ns() // 1_000_000,
        )

    runtime_state = snapshot.get("runtime_state") if isinstance(snapshot, dict) else None
    state = (
        runtime_state
        if runtime_state in ("STARTING", "LEASE_LOST", "FAILED", "STOPPED")
        else result.state
    )
    timeframes = {
        timeframe: {
            "state": item.state,
            "latest_closed_candle_close_ms": item.latest_closed_candle_close_ms,
            "last_successful_sync_ms": item.last_successful_sync_ms,
            "unresolved_gap_count": item.unresolved_gap_count,
            "sync_error": item.sync_error,
            "age_ms": item.age_ms,
        }
        for timeframe, item in result.timeframes.items()
    }
    return result, {
        "state": state,
        "live": result.live,
        "ready": result.ready and state == "HEALTHY",
        "timeframes": timeframes,
    }


@app.get("/health/live")
def health_live():
    result, body = _feeder_health_result()
    return jsonify(body), (200 if result.live else 503)


@app.get("/health/ready")
def health_ready():
    result, body = _feeder_health_result()
    return jsonify(body), (200 if result.ready else 503)


@app.get("/health/data")
def health_data():
    result, body = _feeder_health_result()
    storage_available = (
        app.config.get("T0_HEALTH_SNAPSHOT_PROVIDER") is not None
        or bool(
            app.config.get("T0_HEALTH_RUNTIME_STATUS_DB")
            or os.getenv("MARKET_DATA_DB", "").strip()
        )
    )
    data_healthy = (
        storage_available
        and bool(result.timeframes)
        and result.state not in ("FAILED", "STOPPED")
        and all(item.state == "HEALTHY" for item in result.timeframes.values())
    )
    return jsonify(body), (200 if data_healthy else 503)


@app.get("/health")
def health():
    result, body = _feeder_health_result()
    return jsonify(body), (200 if result.ready else 503)
