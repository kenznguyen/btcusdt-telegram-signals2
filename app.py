import hmac
import os
import threading
from collections import deque

import requests
from flask import Flask, jsonify, request

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
        dispatch_github(command)
        telegram_send(
            f"⏳ Đã nhận {command_token}. GitHub Actions đang xử lý; kết quả sẽ được gửi tại đây sau khi hoàn tất."
        )
    except Exception:
        app.logger.exception("Could not dispatch Telegram command")
        try:
            telegram_send(
                "⚠️ Không kích hoạt được GitHub Actions. Hãy kiểm tra workflow và secret GITHUB_TOKEN trong dịch vụ bridge."
            )
        except Exception:
            app.logger.exception("Could not send dispatch error to Telegram")

    return jsonify({"ok": True}), 200
