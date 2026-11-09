import os
import time

from flask import Flask, jsonify, send_from_directory

from market_data.feeder import HealthEvaluator

app = Flask(__name__)

@app.get("/dashboard")
def dashboard_page():
    return send_from_directory(os.path.join(os.path.dirname(__file__), "dashboard"), "index.html")

def _feeder_health_result():
    provider = app.config.get("T0_HEALTH_SNAPSHOT_PROVIDER")
    if not callable(provider):
        snapshot = {
            "process_running": True,
            "startup_complete": True,
            "storage_readable": False,
            "storage_writable": False,
            "lease_valid": False,
            "fatal_error": False,
        }
    else:
        try:
            snapshot = provider()
        except Exception:
            app.logger.exception("T0 health snapshot provider failed")
            snapshot = {
                "process_running": True,
                "startup_complete": True,
                "storage_readable": False,
                "storage_writable": False,
                "lease_valid": False,
                "fatal_error": True,
            }

    clock = app.config.get("T0_HEALTH_CLOCK")
    try:
        now_ms = clock() if callable(clock) else time.time_ns() // 1_000_000
        result = HealthEvaluator().evaluate(snapshot, now_ms=now_ms)
    except Exception:
        app.logger.exception("T0 health evaluation failed")
        result = HealthEvaluator().evaluate({
            "process_running": True,
            "startup_complete": True,
            "storage_readable": False,
            "storage_writable": False,
            "lease_valid": False,
            "fatal_error": True,
        }, now_ms=time.time_ns() // 1_000_000)

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
        "state": result.state,
        "live": result.live,
        "ready": result.ready,
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
    storage_available = app.config.get("T0_HEALTH_SNAPSHOT_PROVIDER") is not None
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
