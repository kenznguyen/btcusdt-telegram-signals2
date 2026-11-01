import hmac
import os
import threading
import time
from collections import deque

import requests
from flask import Flask, jsonify, request, send_from_directory

from integrations import codemagic_client as codemagic
from market_data.feeder import HealthEvaluator

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()


COMMANDS = {
    "/start": "help",
    "/help": "help",
    "/status": "status",
    "/position": "position",
    "/signal": "signal",
    "/backtest": "backtest",
    "/btstatus": "btstatus",
    "/btresult": "btresult",
}

# In-memory deduplication prevents Telegram retries from dispatching the same update twice.
_seen_updates = set()
_seen_order = deque(maxlen=2000)
_seen_lock = threading.Lock()


def telegram_send(message: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID environment variable")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    response = requests.post(
        url,
        json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "disable_web_page_preview": True},
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError("Telegram sendMessage returned ok=false")


def already_seen(update_id) -> bool:
    if update_id is None:
        return False
    key = str(update_id)
    with _seen_lock:
        if key in _seen_updates:
            return True
        if len(_seen_order) == _seen_order.maxlen:
            oldest = _seen_order[0]
            _seen_updates.discard(oldest)
        _seen_order.append(key)
        _seen_updates.add(key)
    return False


def dispatch_codemagic(command: str) -> str:
    return codemagic.start_build("telegram-command", {"TELEGRAM_COMMAND": command})


@app.get("/")
def index():
    return "BTCUSDT Telegram command bridge is running.", 200


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


# Keep both paths valid: /telegram-webhook is descriptive, /webhook is the short Render URL.
@app.post("/webhook")
@app.post("/telegram-webhook")
def telegram_webhook():
    if not TELEGRAM_WEBHOOK_SECRET:
        return jsonify({"ok": False, "error": "webhook not configured"}), 503

    supplied_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not hmac.compare_digest(supplied_secret, TELEGRAM_WEBHOOK_SECRET):
        return jsonify({"ok": False}), 403

    update = request.get_json(silent=True) or {}
    if already_seen(update.get("update_id")):
        return jsonify({"ok": True, "duplicate": True}), 200

    message = update.get("message") or update.get("edited_message")
    if not message:
        return jsonify({"ok": True, "ignored": True}), 200

    chat = message.get("chat") or {}
    sender_chat_id = str(chat.get("id", ""))
    if not TELEGRAM_CHAT_ID or sender_chat_id != TELEGRAM_CHAT_ID:
        # Silently ignore unauthorized chats; never expose whether the configured ID is valid.
        return jsonify({"ok": True, "ignored": True}), 200

    text = (message.get("text") or "").strip()
    if not text.startswith("/"):
        return jsonify({"ok": True, "ignored": True}), 200

    command_token = text.split()[0].split("@", 1)[0].lower()
    command = COMMANDS.get(command_token)
    if not command:
        telegram_send("Lệnh chưa hỗ trợ. Gõ /help để xem các lệnh có sẵn.")
        return jsonify({"ok": True, "unknown_command": True}), 200

    try:
        dispatch_codemagic(command)
        telegram_send(
            f"⏳ Đã nhận {command_token}. Codemagic đang xử lý; kết quả sẽ được gửi tại đây sau khi hoàn tất."
        )
    except Exception:
        app.logger.exception("Could not dispatch Telegram command")
        try:
            telegram_send(
                "⚠️ Không kích hoạt được Codemagic. Hãy kiểm tra cấu hình dịch vụ và thử lại."
            )
        except Exception:
            app.logger.exception("Could not send dispatch error to Telegram")

    return jsonify({"ok": True}), 200


# Dashboard API keeps its existing response shape while Codemagic owns compute.
@app.get("/api/dashboard/status")
def dashboard_status():
    if not codemagic.configured():
        return jsonify({"ok": False, "error": "Codemagic chưa được cấu hình."}), 503
    try:
        workflows = {key: [codemagic.normalize_build(build) for build in codemagic.list_builds(workflow, 5)]
                     for key, workflow in (("scanner", "signal-scan"), ("backtest", "dashboard-backtest"))}
        return jsonify({"ok": True, "source": "Codemagic API", "workflows": workflows}), 200
    except codemagic.CodemagicError:
        app.logger.warning("Could not read Codemagic build history")
        return jsonify({"ok": False, "error": "Chưa đọc được trạng thái Codemagic."}), 502


@app.get("/api/dashboard/backtest")
def dashboard_backtest():
    if not codemagic.configured():
        return jsonify({"ok": False, "error": "Codemagic chưa được cấu hình."}), 503
    try:
        return jsonify(codemagic.latest_report()), 200
    except codemagic.CodemagicError:
        app.logger.warning("Could not read Codemagic backtest artifacts")
        return jsonify({"ok": False, "error": "Chưa đọc được báo cáo backtest từ Codemagic."}), 502


@app.post("/api/dashboard/run-backtest")
def dashboard_run_backtest():
    if not codemagic.configured():
        return jsonify({"ok": False, "error": "Codemagic chưa được cấu hình."}), 503
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"ok": False, "error": "Cấu hình backtest không hợp lệ."}), 400
    try:
        raw_days = payload.get("days", 360)
        if isinstance(raw_days, bool) or float(raw_days) != int(raw_days):
            raise ValueError("Số ngày phải là số nguyên.")
        days = int(raw_days)
        capital = float(payload.get("initial_capital", 100))
        entry_margin_pct = float(payload.get("entry_margin_pct", 50))
        dca_margin_ratio = float(payload.get("dca_margin_ratio", 100))
        if not 1 <= days <= 365:
            raise ValueError("Số ngày phải từ 1 đến 365.")
        if not 1 <= capital <= 100000000:
            raise ValueError("Vốn ban đầu phải từ 1 đến 100.000.000 USDT.")
        if not 1 <= entry_margin_pct <= 100:
            raise ValueError("Margin lệnh đầu phải từ 1% đến 100% vốn hiện tại.")
        if not 0 <= dca_margin_ratio <= 500:
            raise ValueError("Margin DCA phải từ 0% đến 500% margin lệnh đầu.")
    except (TypeError, ValueError, OverflowError) as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    variables = {"BACKTEST_DAYS": str(days), "BACKTEST_INITIAL_CAPITAL": str(capital),
                 "ENTRY_MARGIN_PCT": str(entry_margin_pct), "DCA_MARGIN_RATIO": str(dca_margin_ratio)}
    try:
        build_id = codemagic.start_build("dashboard-backtest", variables)
        return jsonify({"ok": True, "message": "Đã gửi yêu cầu backtest tới Codemagic.", "build_id": build_id,
                        "parameters": {"days": days, "initial_capital": capital,
                                       "entry_margin_pct": entry_margin_pct, "dca_margin_ratio": dca_margin_ratio}}), 202
    except codemagic.CodemagicError:
        app.logger.warning("Could not start Codemagic dashboard backtest")
        return jsonify({"ok": False, "error": "Không thể gửi yêu cầu backtest tới Codemagic."}), 502
