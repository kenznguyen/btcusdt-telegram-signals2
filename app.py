import hmac
import json
import os
import tempfile
import threading
from collections import deque

import requests
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY", "kenznguyen/btcusdt-telegram-signals2").strip()
GITHUB_REF = os.getenv("GITHUB_REF", "main").strip()
GITHUB_WORKFLOW_FILE = os.getenv("GITHUB_WORKFLOW_FILE", "telegram-command.yml").strip()

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

# Persist webhook update IDs so Render restarts do not forget recent deliveries.
BOT_STATE_DIR = os.getenv("BOT_STATE_DIR", ".")
TELEGRAM_UPDATE_STATE_FILE = os.path.join(BOT_STATE_DIR, "telegram_seen_updates.json")
_seen_updates = set()
_seen_order = deque(maxlen=2000)
_seen_lock = threading.Lock()


def _persist_seen_updates(keys):
    os.makedirs(BOT_STATE_DIR, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".telegram-updates-", suffix=".tmp", dir=BOT_STATE_DIR)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(list(keys)[-2000:], f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, TELEGRAM_UPDATE_STATE_FILE)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


try:
    if os.path.exists(TELEGRAM_UPDATE_STATE_FILE):
        with open(TELEGRAM_UPDATE_STATE_FILE, "r", encoding="utf-8") as f:
            _saved_updates = json.load(f)
        if not isinstance(_saved_updates, list):
            raise ValueError("telegram_seen_updates.json must contain a JSON list")
        for _saved_id in _saved_updates[-2000:]:
            _key = str(_saved_id)
            _seen_order.append(_key)
            _seen_updates.add(_key)
except Exception as _state_error:
    # Do not silently discard the dedupe ledger; fail service startup to avoid replaying commands.
    raise RuntimeError("Cannot safely restore Telegram webhook dedupe state") from _state_error


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
        return key in _seen_updates


def mark_seen(update_id) -> None:
    if update_id is None:
        return
    key = str(update_id)
    with _seen_lock:
        if key in _seen_updates:
            return
        next_order = list(_seen_order)
        next_order.append(key)
        next_order = next_order[-2000:]
        # Persist first; only acknowledge the update once the dedupe ledger is durable.
        _persist_seen_updates(next_order)
        _seen_order.clear()
        _seen_order.extend(next_order)
        _seen_updates.clear()
        _seen_updates.update(next_order)


def dispatch_github(command: str) -> None:
    if not GITHUB_TOKEN:
        raise RuntimeError("GitHub dispatch token is not configured")
    url = (
        f"https://api.github.com/repos/{GITHUB_REPOSITORY}"
        f"/actions/workflows/{GITHUB_WORKFLOW_FILE}/dispatches"
    )
    response = requests.post(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"ref": GITHUB_REF, "inputs": {"command": command}},
        timeout=10,
    )
    if response.status_code != 204:
        # Log GitHub validation detail without exposing request headers or credentials.
        detail = (response.text or "").replace("\n", " ")[:500]
        raise RuntimeError(f"GitHub API returned HTTP {response.status_code}: {detail}")


@app.get("/")
def index():
    return "BTCUSDT Telegram command bridge is running.", 200


@app.get("/dashboard")
def dashboard_page():
    return send_from_directory(os.path.join(os.path.dirname(__file__), "dashboard"), "index.html")


@app.get("/health")
def health():
    return jsonify({"ok": True}), 200


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

    update_id = update.get("update_id")
    message = update.get("message") or update.get("edited_message")
    if not message:
        mark_seen(update_id)
        return jsonify({"ok": True, "ignored": True}), 200

    chat = message.get("chat") or {}
    sender_chat_id = str(chat.get("id", ""))
    if not TELEGRAM_CHAT_ID or sender_chat_id != TELEGRAM_CHAT_ID:
        # Silently ignore unauthorized chats; never expose whether the configured ID is valid.
        mark_seen(update_id)
        return jsonify({"ok": True, "ignored": True}), 200

    text = (message.get("text") or "").strip()
    if not text.startswith("/"):
        mark_seen(update_id)
        return jsonify({"ok": True, "ignored": True}), 200

    command_token = text.split()[0].split("@", 1)[0].lower()
    command = COMMANDS.get(command_token)
    if not command:
        telegram_send("Lệnh chưa hỗ trợ. Gõ /help để xem các lệnh có sẵn.")
        mark_seen(update_id)
        return jsonify({"ok": True, "unknown_command": True}), 200

    try:
        dispatch_github(command)
    except Exception:
        app.logger.exception("Could not dispatch Telegram command")
        try:
            telegram_send(
                "⚠️ Không kích hoạt được GitHub Actions. Lệnh sẽ được Telegram thử gửi lại; kiểm tra workflow và secret GITHUB_TOKEN."
            )
        except Exception:
            app.logger.exception("Could not send dispatch error to Telegram")
        # Do not mark the update as handled; Telegram can retry after a transient failure.
        return jsonify({"ok": False, "error": "workflow dispatch failed"}), 503

    # Dispatch succeeded; persist dedupe before sending the optional acknowledgement.
    mark_seen(update_id)
    try:
        telegram_send(
            f"⏳ Đã nhận {command_token}. GitHub Actions đang xử lý; kết quả sẽ được gửi tại đây sau khi hoàn tất."
        )
    except Exception:
        app.logger.exception("Command dispatched but Telegram acknowledgement failed")
    return jsonify({"ok": True}), 200


# Dashboard API: workflow metadata only; no exchange execution/fill claims.
@app.get("/api/dashboard/status")
def dashboard_status():
    if not GITHUB_TOKEN:
        return jsonify({"ok": False, "error": "GITHUB_TOKEN is not configured"}), 503
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        result = {}
        for key, workflow in (("scanner", "signal-scan.yml"), ("backtest", "dashboard-backtest.yml")):
            response = requests.get(
                f"https://api.github.com/repos/{GITHUB_REPOSITORY}/actions/workflows/{workflow}/runs",
                headers=headers, params={"per_page": 5, "branch": "main"}, timeout=12,
            )
            response.raise_for_status()
            result[key] = [
                {
                    "id": run.get("id"),
                    "name": run.get("name"),
                    "display_title": run.get("display_title"),
                    "status": run.get("status"),
                    "conclusion": run.get("conclusion"),
                    "created_at": run.get("created_at"),
                    "updated_at": run.get("updated_at"),
                    "html_url": run.get("html_url"),
                }
                for run in response.json().get("workflow_runs", [])
            ]
        return jsonify({"ok": True, "source": "GitHub Actions API", "workflows": result}), 200
    except requests.RequestException:
        app.logger.exception("Could not read GitHub Actions dashboard status")
        return jsonify({"ok": False, "error": "Unable to read GitHub Actions. Check GITHUB_TOKEN Actions read permission."}), 502


@app.get("/api/dashboard/backtest")
def dashboard_backtest():
    if not GITHUB_TOKEN:
        return jsonify({"ok": False, "error": "GITHUB_TOKEN is not configured"}), 503
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        runs_response = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPOSITORY}/actions/workflows/dashboard-backtest.yml/runs",
            headers=headers, params={"per_page": 15, "branch": "main"}, timeout=12,
        )
        runs_response.raise_for_status()
        runs = runs_response.json().get("workflow_runs", [])
        for run in runs:
            title = (run.get("display_title") or run.get("name") or "").lower()
            is_backtest = "backtest" in title
            if not is_backtest or run.get("status") != "completed":
                continue
            artifacts_response = requests.get(
                f"https://api.github.com/repos/{GITHUB_REPOSITORY}/actions/runs/{run['id']}/artifacts",
                headers=headers, params={"per_page": 30}, timeout=12,
            )
            artifacts_response.raise_for_status()
            artifacts = artifacts_response.json().get("artifacts", [])
            artifact = next((a for a in artifacts if a.get("name") == "dashboard-backtest-report" and not a.get("expired")), None)
            if not artifact:
                continue
            download = requests.get(artifact["archive_download_url"], headers=headers, timeout=30, allow_redirects=True)
            download.raise_for_status()
            import io
            import zipfile
            from pathlib import PurePosixPath
            files = {}
            with zipfile.ZipFile(io.BytesIO(download.content)) as archive:
                allowed = {
                    "dashboard_backtest_last_result.json", "dashboard_backtest_status.json",
                    "dashboard_backtest_trades.csv", "dashboard_backtest_equity.csv", "dashboard_backtest_equity_m15.csv",
                }
                for member in archive.namelist():
                    name = PurePosixPath(member).name
                    if name in allowed:
                        files[name.replace("dashboard_backtest_", "backtest_")] = archive.read(member).decode("utf-8-sig", errors="replace")
            return jsonify({
                "ok": True,
                "available": True,
                "run": {
                    "id": run.get("id"), "name": run.get("name"),
                    "status": run.get("status"), "conclusion": run.get("conclusion"),
                    "created_at": run.get("created_at"), "html_url": run.get("html_url"),
                },
                "artifact": {"name": artifact.get("name"), "created_at": artifact.get("created_at")},
                "files": files,
            }), 200
        return jsonify({"ok": True, "available": False, "message": "Chưa tìm thấy artifact backtest hợp lệ trong các lần chạy gần đây."}), 200
    except requests.RequestException:
        app.logger.exception("Could not read backtest artifact from GitHub Actions")
        return jsonify({"ok": False, "error": "Không đọc được artifact. Kiểm tra quyền Actions: read của GITHUB_TOKEN."}), 502
    except (ValueError, KeyError):
        app.logger.exception("Invalid backtest artifact response")
        return jsonify({"ok": False, "error": "Artifact backtest không đúng định dạng mong đợi."}), 502


@app.post("/api/dashboard/run-backtest")
def dashboard_run_backtest():
    if not GITHUB_TOKEN:
        return jsonify({"ok": False, "error": "GITHUB_TOKEN is not configured"}), 503
    payload = request.get_json(silent=True) or {}
    try:
        days = int(payload.get("days", 360))
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
    except (TypeError, ValueError) as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/actions/workflows/dashboard-backtest.yml/dispatches"
    inputs = {
        "backtest_days": str(days),
        "initial_capital": str(capital),
        "entry_margin_pct": str(entry_margin_pct),
        "dca_margin_ratio": str(dca_margin_ratio),
    }
    try:
        response = requests.post(url, headers=headers, json={"ref": GITHUB_REF, "inputs": inputs}, timeout=15)
        if response.status_code != 204:
            detail = (response.text or "").replace("\\n", " ")[:300]
            app.logger.error("GitHub workflow dispatch failed: HTTP %s %s", response.status_code, detail)
            return jsonify({"ok": False, "error": f"GitHub không nhận workflow dispatch (HTTP {response.status_code}). Kiểm tra quyền Actions: write và tên branch."}), 502
        return jsonify({
            "ok": True,
            "message": "Đã gửi yêu cầu backtest tới GitHub Actions.",
            "parameters": {
                "days": days, "initial_capital": capital,
                "entry_margin_pct": entry_margin_pct, "dca_margin_ratio": dca_margin_ratio,
            },
        }), 202
    except requests.RequestException:
        app.logger.exception("Could not dispatch dashboard backtest")
        return jsonify({"ok": False, "error": "Không thể kết nối GitHub Actions."}), 502
