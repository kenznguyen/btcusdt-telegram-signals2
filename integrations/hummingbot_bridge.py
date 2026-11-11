"""Read-only Hummingbot API adapter; exchange credentials stay on the server."""

import base64
import hmac
import http.client
import json
import math
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request


MAX_BYTES = 1024 * 1024
CONNECTOR = "binance_perpetual"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward Hummingbot's Basic credentials to a redirected host.
        return None


OPENER = urllib.request.build_opener(NoRedirect())


def number(value):
    if isinstance(value, bool):
        raise ValueError("Invalid number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Non-finite number")
    return result


def normalize_snapshot(raw, symbol, now_ms):
    if not isinstance(raw, dict) or raw.get("trading_pair") != symbol[:-4] + "-USDT":
        raise ValueError("Wrong trading pair")
    observed_at = round(number(raw["timestamp"]) * 1000)
    if not -5000 <= now_ms - observed_at <= 30000:
        raise ValueError("Invalid snapshot time")

    def levels(side, reverse):
        rows = raw[side]
        if not isinstance(rows, list) or not 1 <= len(rows) <= 20:
            raise ValueError("Invalid depth")
        result = []
        for row in rows:
            price, quantity = number(row["price"]), number(row["amount"])
            if price <= 0 or quantity <= 0:
                raise ValueError("Invalid level")
            result.append({"price": price, "quantity": quantity})
        if len({row["price"] for row in result}) != len(result):
            raise ValueError("Duplicate price")
        return sorted(result, key=lambda row: row["price"], reverse=reverse)

    bids, asks = levels("bids", True), levels("asks", False)
    if bids[0]["price"] >= asks[0]["price"]:
        raise ValueError("Crossed order book")
    return {"source": "hummingbot", "symbol": symbol, "connector": CONNECTOR,
            "observedAtMs": observed_at, "bids": bids, "asks": asks}


def fetch_snapshot(symbol):
    base = os.environ["HB_API_URL"].rstrip("/")
    parsed = urllib.parse.urlsplit(base)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Invalid configured URL")
    user, password = os.environ["HB_API_USER"], os.environ["HB_API_PASSWORD"]
    credentials = base64.b64encode((user + ":" + password).encode()).decode()
    payload = {"connector_name": CONNECTOR, "trading_pair": symbol[:-4] + "-USDT", "depth": 20}
    request = urllib.request.Request(base + "/market-data/order-book", data=json.dumps(payload).encode(),
                                     headers={"Authorization": "Basic " + credentials,
                                              "Content-Type": "application/json", "Accept": "application/json"})
    with OPENER.open(request, timeout=8) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Response too large")
    return json.loads(data)


def application(environ, start_response):
    def reply(status, body):
        data = json.dumps(body, allow_nan=False).encode()
        start_response(status, [("Content-Type", "application/json; charset=utf-8"),
                                ("Content-Length", str(len(data))), ("Cache-Control", "no-store")])
        return [data]

    if environ.get("REQUEST_METHOD") != "GET":
        return reply("405 Method Not Allowed", {"error": "METHOD_NOT_ALLOWED"})
    path = environ.get("PATH_INFO", "")
    if path == "/health":
        return reply("200 OK", {"ok": True, "service": "hummingbot-read-only-bridge"})
    if path != "/v1/order-book":
        return reply("404 Not Found", {"error": "NOT_FOUND"})
    token = os.environ.get("HB_BRIDGE_TOKEN", "")
    if not token or not all(os.environ.get(key) for key in ("HB_API_URL", "HB_API_USER", "HB_API_PASSWORD")):
        return reply("503 Service Unavailable", {"error": "UNCONFIGURED"})
    auth = environ.get("HTTP_AUTHORIZATION", "")
    if not hmac.compare_digest(auth.encode(), ("Bearer " + token).encode()):
        return reply("401 Unauthorized", {"error": "UNAUTHORIZED"})
    query = urllib.parse.parse_qs(environ.get("QUERY_STRING", ""), keep_blank_values=True)
    symbols = {item.strip() for item in os.environ.get("HB_SYMBOLS", "BTCUSDT,ETHUSDT").split(",")}
    selected = query.get("symbol", [])
    if len(selected) != 1 or not re.fullmatch(r"[A-Z0-9]{2,16}USDT", selected[0]) or selected[0] not in symbols:
        return reply("400 Bad Request", {"error": "INVALID_SYMBOL"})
    try:
        snapshot = fetch_snapshot(selected[0])
        normalized = normalize_snapshot(snapshot, selected[0], round(time.time() * 1000))
        return reply("200 OK", normalized)
    except (ValueError, TypeError, KeyError, OverflowError):
        return reply("502 Bad Gateway", {"error": "INVALID_SNAPSHOT"})
    except (OSError, http.client.HTTPException):
        # Do not return exception text, request URLs, or credentials to the APK.
        return reply("502 Bad Gateway", {"error": "UPSTREAM_UNAVAILABLE"})


if __name__ == "__main__":
    from wsgiref.simple_server import make_server

    # Local development only. Put the production bridge behind HTTPS.
    with make_server("127.0.0.1", int(os.environ.get("PORT", "8787")), application) as server:
        server.serve_forever()
