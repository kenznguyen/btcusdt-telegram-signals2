"""Common read API and explicitly authorized, local paper controls."""

import hmac
import json
import mimetypes
import os
from pathlib import Path
import sqlite3
import threading
import time
from urllib.parse import parse_qs, unquote

from market_data.api import candle_query
from market_data.store import read_window
from pipeline.values import stamp

ROOT = Path(__file__).resolve().parents[1]
_book_lock = threading.Lock()
_book_cache = None
_book_loaded_at = 0


def now_ms():
    return time.time_ns() // 1_000_000


def control_root():
    return Path(os.environ.get("CONTROL_DIST_PATH") or ROOT / "control_dashboard/dist").resolve()


def load_report(variable):
    path = os.environ.get(variable)
    if not path:
        return None
    with open(path, "rb") as source:
        raw = source.read(1_048_577)
    if len(raw) > 1_048_576:
        raise ValueError("Oversized report")
    try:
        report = json.loads(raw)
    except RecursionError as error:
        raise ValueError("Invalid report nesting") from error
    if not isinstance(report, dict):
        raise ValueError("Invalid report")
    return report


def intelligence_snapshot(timestamp):
    from futures_intelligence.import_collector import validate_snapshot
    report = load_report("INTELLIGENCE_REPORT_PATH")
    return validate_snapshot(report, timestamp) if report is not None else None


def book_snapshot(timestamp):
    global _book_cache, _book_loaded_at
    from integrations.hummingbot_bridge import fetch_snapshot, normalize_snapshot
    # Server-only credentials and fixed symbol. No user-supplied URL or connector.
    if not all(os.environ.get(key) for key in ("HB_API_URL", "HB_API_USER", "HB_API_PASSWORD")):
        return None
    with _book_lock:
        if _book_loaded_at and 0 <= now_ms() - _book_loaded_at < 3_000:
            return _book_cache
        try:
            result = normalize_snapshot(fetch_snapshot("BTCUSDT"), "BTCUSDT", now_ms())
        except Exception:
            _book_cache, _book_loaded_at = None, now_ms()
            return None
        _book_cache, _book_loaded_at = result, now_ms()
        return result


def ledger():
    from paper_execution.ledger import PaperLedger
    path = os.environ.get("MARKET_DATA_DB")
    if not path:
        raise ValueError("Unconfigured store")
    return PaperLedger(path, max_position_base=os.environ.get("PAPER_MAX_POSITION_BASE", "0.01"),
                       fee_rate=os.environ.get("PAPER_FEE_RATE", "0.0005"),
                       max_spread_bps=os.environ.get("PAPER_MAX_SPREAD_BPS", "50"))


def control_permit(timestamp):
    """A small shared SQLite budget for paper writes across API workers."""
    from contextlib import closing
    path = os.environ.get("MARKET_DATA_DB")
    if not path or not Path(path).is_file():
        return False
    with closing(sqlite3.connect(path, timeout=5)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("CREATE TABLE IF NOT EXISTS paper_control_budget (minute INTEGER PRIMARY KEY, used INTEGER NOT NULL)")
        minute = timestamp // 60_000
        connection.execute("DELETE FROM paper_control_budget WHERE minute<?", (minute-1,))
        connection.execute("INSERT OR IGNORE INTO paper_control_budget VALUES (?,0)", (minute,))
        used = connection.execute("SELECT used FROM paper_control_budget WHERE minute=?", (minute,)).fetchone()[0]
        if used >= 30:
            return False
        connection.execute("UPDATE paper_control_budget SET used=used+1 WHERE minute=?", (minute,))
        return True


def context(timestamp):
    """Resolve inputs on the server; callers cannot substitute model/book data."""
    stamp(timestamp)
    end = timestamp // 900_000 * 900_000
    data = {}
    errors = {}
    try:
        data["candles"] = read_window(os.environ.get("MARKET_DATA_DB", ""), "BTCUSDT", "15m",
                                      end - 1_800_000, end)
    except (ValueError, OSError, sqlite3.Error):
        data["candles"], errors["candles"] = None, "CANDLES_UNAVAILABLE"
    try:
        data["intelligence"] = intelligence_snapshot(timestamp)
    except (ValueError, OSError, TypeError, KeyError):
        data["intelligence"], errors["intelligence"] = None, "INTELLIGENCE_UNAVAILABLE"
    try:
        data["prediction"] = load_report("FREQAI_REPORT_PATH")
    except (ValueError, OSError):
        data["prediction"], errors["prediction"] = None, "PREDICTION_UNAVAILABLE"
    data["book"] = book_snapshot(timestamp)
    data["errors"] = errors
    return data


def decide(data, timestamp):
    from pipeline.decision import evaluate
    return evaluate(data["candles"], data["intelligence"], data["prediction"], data["book"], timestamp,
                    target_base=os.environ.get("PAPER_TARGET_BASE", "0.001"))


def core_decide(timestamp):
    from pipeline.core_signal import validate
    try:
        report = load_report("STRATEGY_CORE_REPORT_PATH")
    except (ValueError, OSError):
        report = None
    return validate(report, timestamp)


def signal_snapshot(timestamp):
    data = context(timestamp)
    ai = decide(data, timestamp)
    ai["source"] = "AI_FREQAI"
    return {"strategyCore": core_decide(timestamp), "aiStrategy": ai,
            "mode": "PAPER", "liveTradingSupported": False}


def control_readiness(timestamp):
    data = context(timestamp)
    candles = data.get("candles")
    candle_ready = bool(candles and candles.get("coverage", {}).get("complete") is True)
    book_ready = data.get("book") is not None
    paper = ledger().snapshot()
    no_pending = not any(order.get("status") in ("OPEN", "PARTIALLY_FILLED")
                         for order in paper.get("orders", []))
    return {"ready": candle_ready and book_ready and no_pending,
            "checks": {"closedCandles": candle_ready, "orderBook": book_ready,
                       "noPendingPaperOrders": no_pending}}


def _body(environ):
    try:
        length = int(environ.get("CONTENT_LENGTH", "0"))
    except (TypeError, ValueError) as error:
        raise ValueError("Invalid body size") from error
    if not 0 < length <= 4096:
        raise ValueError("Invalid body size")
    raw = environ["wsgi.input"].read(length)
    if len(raw) != length:
        raise ValueError("Incomplete request")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    try:
        value = json.loads(raw, object_pairs_hook=unique)
    except RecursionError as error:
        raise ValueError("Invalid body nesting") from error
    if not isinstance(value, dict):
        raise ValueError("Expected JSON object")
    return value


def application(environ, start_response):
    headers = [("Cache-Control", "no-store"), ("X-Content-Type-Options", "nosniff"),
               ("X-Frame-Options", "DENY"), ("Referrer-Policy", "no-referrer")]

    def response(status, value):
        data = json.dumps(value, allow_nan=False, separators=(",", ":")).encode()
        start_response(status, headers + [("Content-Type", "application/json; charset=utf-8"),
                                         ("Content-Length", str(len(data)))])
        return [data]

    method, path = environ.get("REQUEST_METHOD", ""), environ.get("PATH_INFO", "")
    if method == "GET" and path == "/health":
        return response("200 OK", {"ok": True, "service": "five-layer-paper", "liveTradingSupported": False})
    if method == "GET" and (path == "/control" or path.startswith("/control/")):
        root = control_root()
        name = unquote(path.removeprefix("/control")).lstrip("/") or "index.html"
        target = (root / name).resolve()
        public_asset = name == "index.html" or (name.startswith("assets/") and target.suffix in {".js", ".css", ".svg", ".png", ".ico", ".woff", ".woff2"})
        if not public_asset or not target.is_relative_to(root) or any(part.startswith(".") for part in Path(name).parts) or not target.is_file():
            return response("404 Not Found", {"error": "DASHBOARD_NOT_BUILT"})
        data = target.read_bytes()
        static_headers = headers + [("Content-Type", mimetypes.guess_type(str(target))[0] or "application/octet-stream"),
                                    ("Content-Length", str(len(data))),
                                    ("Content-Security-Policy", "default-src 'self'; connect-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'")]
        start_response("200 OK", static_headers)
        return [data]
    routes = {"/v1/system", "/v1/candles", "/v1/order-book", "/v1/intelligence", "/v1/decision", "/v1/signals", "/v1/paper",
              "/v1/paper/evaluate", "/v1/paper/pause", "/v1/paper/cancel", "/v1/paper/kill", "/v1/paper/reset-kill"}
    if path not in routes:
        return response("404 Not Found", {"error": "NOT_FOUND"})
    expected = "POST" if path in {"/v1/paper/evaluate", "/v1/paper/pause", "/v1/paper/cancel", "/v1/paper/kill", "/v1/paper/reset-kill"} else "GET"
    if method != expected:
        return response("405 Method Not Allowed", {"error": "METHOD_NOT_ALLOWED"})
    token = os.environ.get("CONTROL_TOKEN" if method == "POST" else "MARKET_DATA_TOKEN", "")
    if not token:
        return response("503 Service Unavailable", {"error": "UNCONFIGURED"})
    if not hmac.compare_digest(environ.get("HTTP_AUTHORIZATION", "").encode(), ("Bearer " + token).encode()):
        return response("401 Unauthorized", {"error": "UNAUTHORIZED"})
    if method == "POST" and token == os.environ.get("MARKET_DATA_TOKEN"):
        return response("503 Service Unavailable", {"error": "CONTROL_TOKEN_MUST_BE_DISTINCT"})
    timestamp = now_ms()
    try:
        if method == "POST":
            payload = _body(environ)
            if not os.environ.get("MARKET_DATA_DB") or not Path(os.environ["MARKET_DATA_DB"]).is_file():
                return response("503 Service Unavailable", {"error": "STORE_UNAVAILABLE"})
            if not control_permit(timestamp):
                return response("429 Too Many Requests", {"error": "CONTROL_RATE_LIMIT"})
            if path == "/v1/paper/pause" and set(payload) == {"paused"} and type(payload["paused"]) is bool:
                result = ledger().set_paused(payload["paused"], timestamp)
            elif path == "/v1/paper/cancel" and set(payload) == {"orderId"} and isinstance(payload["orderId"], str) and 0 < len(payload["orderId"]) <= 100:
                result = ledger().cancel(payload["orderId"], timestamp)
            elif path == "/v1/paper/kill" and set(payload) == {"enabled"} and payload["enabled"] is True:
                result = ledger().set_killed(True, timestamp, "OPERATOR_KILL_SWITCH")
            elif path == "/v1/paper/reset-kill" and set(payload) == {"acknowledge"} and payload["acknowledge"] is True:
                readiness = control_readiness(timestamp)
                if not readiness["ready"]:
                    return response("409 Conflict", {"error": "SYSTEM_NOT_READY", "checks": readiness["checks"]})
                result = ledger().reset_kill(True, True, timestamp)
            elif path == "/v1/paper/evaluate" and (not payload or payload in ({"source": "AI"}, {"source": "CORE"})):
                source = payload.get("source", "AI")
                if source == "CORE":
                    decision = core_decide(timestamp)
                    data = {"book": book_snapshot(timestamp)}
                else:
                    data = context(timestamp)
                    decision = decide(data, timestamp)
                    decision["source"] = "AI_FREQAI"
                timestamp = now_ms()
                order = ledger().submit(decision["intent"], data["book"], timestamp) if decision.get("intent") else None
                result = {"decision": decision, "order": order}
            else:
                raise ValueError("Invalid control payload")
        elif path == "/v1/candles":
            query = candle_query(environ.get("QUERY_STRING", ""))
            try:
                result = read_window(os.environ.get("MARKET_DATA_DB", ""), **query)
            except (ValueError, OSError, sqlite3.Error):
                return response("503 Service Unavailable", {"error": "STORE_UNAVAILABLE"})
        elif path == "/v1/paper":
            from paper_execution.ledger import read_snapshot
            if not os.environ.get("MARKET_DATA_DB"):
                return response("503 Service Unavailable", {"error": "UNCONFIGURED"})
            result = read_snapshot(os.environ["MARKET_DATA_DB"])
        elif path == "/v1/order-book":
            query = parse_qs(environ.get("QUERY_STRING", ""), max_num_fields=1)
            if query != {"symbol": ["BTCUSDT"]}:
                raise ValueError("Invalid symbol")
            result = book_snapshot(timestamp)
            if result is None:
                return response("503 Service Unavailable", {"error": "ORDER_BOOK_UNAVAILABLE"})
        elif path == "/v1/intelligence":
            try:
                snapshot = intelligence_snapshot(timestamp)
            except (ValueError, KeyError, TypeError):
                return response("503 Service Unavailable", {"error": "INTELLIGENCE_INVALID"})
            result = snapshot if snapshot is not None else {"available": False, "reason": "INTELLIGENCE_UNAVAILABLE"}
        elif path == "/v1/decision":
            data = context(timestamp)
            result = decide(data, now_ms())
        elif path == "/v1/signals":
            result = signal_snapshot(timestamp)
        else:
            end = timestamp // 900_000 * 900_000
            try:
                candles = read_window(os.environ.get("MARKET_DATA_DB", ""), "BTCUSDT", "15m", end-1_800_000, end)
                candle_ready = candles["coverage"]["complete"] and all(c["availableAtMs"] <= timestamp for c in candles["candles"])
            except (ValueError, OSError, sqlite3.Error):
                candle_ready = False
            try:
                intelligence = intelligence_snapshot(timestamp)
                intel_ready = intelligence is not None and 0 <= timestamp-intelligence["windowEndMs"] <= 60_000 and any(
                    stream.get("status") == "OBSERVED" for stream in intelligence["coverage"].values())
            except (ValueError, OSError, KeyError, TypeError):
                intel_ready = False
            try:
                prediction = load_report("FREQAI_REPORT_PATH")
                model_ready = prediction is not None and prediction.get("doPredict") == 1 and 0 <= timestamp-stamp(prediction.get("availableAtMs")) <= 30_000
            except (ValueError, OSError, TypeError):
                model_ready = False
            hb_ready = all(os.environ.get(k) for k in ("HB_API_URL", "HB_API_USER", "HB_API_PASSWORD"))
            result = {"mode": "PAPER", "liveTradingSupported": False, "layers": [
                {"level": 0, "name": "Kho nến chuẩn", "status": "READY" if candle_ready else "WAIT", "detail": "Cửa sổ M15 · API kho cũng hỗ trợ H1"},
                {"level": 1, "name": "Trinh sát futures", "status": "OBSERVED" if intel_ready else "WAIT", "detail": "Dữ liệu quan sát; từng feed có coverage riêng"},
                {"level": 2, "name": "Freqtrade + FreqAI", "status": "ARTIFACT_AVAILABLE" if model_ready else "WAIT", "detail": "Dự báo phải qua kiểm tra provenance khi ra quyết định"},
                {"level": 3, "name": "Hummingbot / paper", "status": "CONFIGURED" if hb_ready else "WAIT", "detail": "Snapshot chỉ phục vụ mô phỏng, chưa xác nhận kết nối thật"},
                {"level": 4, "name": "React + API", "status": "READY" if (control_root() / "index.html").is_file() else "API_ONLY", "detail": "Quyền đọc và điều khiển paper tách riêng; React cần build dist"}]}
        return response("200 OK", result)
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return response("400 Bad Request", {"error": "INVALID_INPUT"})
    except (OSError, sqlite3.Error):
        return response("503 Service Unavailable", {"error": "DATA_UNAVAILABLE"})


if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    with make_server("127.0.0.1", int(os.environ.get("PORT", "8789")), application) as server:
        server.serve_forever()
