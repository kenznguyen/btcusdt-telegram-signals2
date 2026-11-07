"""Read-only Binance USD-M connectivity probe.

This module never imports the T0 store/Feeder, never persists exchange data, and
never uses API credentials. Network access occurs only through the explicit
CLI --confirm-network switch. REST requests deliberately ignore proxy environment
variables; WebSocket connects directly with verified TLS.
"""
import argparse
import base64
import hashlib
import json
import math
import os
import secrets
import socket
import ssl
import struct
import time
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


REST_BASE = "https://fapi.binance.com"
WS_HOST = "fstream.binance.com"
WS_PATH = "/ws/btcusdt@kline_15m"
WS_PORT = 443
INTERVAL_MS = 900_000
MAX_WS_FRAME = 1_048_576


def classify_http_status(status):
    """Map HTTP outcomes without conflating rate limits and network policy."""
    if status == 200:
        return "REACHABLE"
    if status == 451:
        return "NETWORK_POLICY_BLOCKED"
    if status == 429:
        return "RATE_LIMITED"
    if status in (401, 403):
        return "AUTH_OR_PERMISSION_ERROR"
    if 500 <= status <= 599:
        return "REMOTE_SERVER_ERROR"
    if 400 <= status <= 499:
        return "HTTP_CLIENT_ERROR"
    return "UNEXPECTED_HTTP_STATUS"


def validate_server_time(payload):
    return (
        isinstance(payload, dict)
        and type(payload.get("serverTime")) is int
        and 0 < payload["serverTime"] < 4_102_444_800_000
    )


def validate_exchange_info(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("symbols"), list):
        return False
    for market in payload["symbols"]:
        if not isinstance(market, dict) or market.get("symbol") != "BTCUSDT":
            continue
        return all(market.get(key) == value for key, value in {
            "status": "TRADING",
            "contractType": "PERPETUAL",
            "baseAsset": "BTC",
            "quoteAsset": "USDT",
            "marginAsset": "USDT",
        }.items())
    return False


def _decimal(value):
    if not isinstance(value, (str, int, float)) or isinstance(value, bool):
        raise ValueError("invalid decimal type")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("invalid decimal value") from None
    if not number.is_finite():
        raise ValueError("non-finite decimal")
    return number


def validate_klines(rows, *, now_ms, interval_ms=INTERVAL_MS):
    if not isinstance(rows, list) or type(now_ms) is not int or type(interval_ms) is not int:
        return False
    if interval_ms <= 0 or not rows:
        return False
    valid_closed = False
    previous_open = None
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) != 12:
            return False
        opened, close_time = row[0], row[6]
        if type(opened) is not int or type(close_time) is not int:
            return False
        if opened < 0 or opened % interval_ms or close_time != opened + interval_ms - 1:
            return False
        if previous_open is not None and opened <= previous_open:
            return False
        previous_open = opened
        try:
            open_price, high, low, close, volume = (_decimal(value) for value in row[1:6])
            quote_volume = _decimal(row[7])
            taker_base = _decimal(row[9])
            taker_quote = _decimal(row[10])
        except ValueError:
            return False
        if min(open_price, high, low, close) <= 0 or volume < 0 or quote_volume < 0 or taker_base < 0 or taker_quote < 0:
            return False
        if high < max(open_price, close, low) or low > min(open_price, close, high):
            return False
        if close_time < now_ms:
            valid_closed = True
    return valid_closed


def parse_http_upgrade(response, websocket_key):
    """Return (accepted, status_code, bytes_after_headers) for an RFC6455 response."""
    marker = response.find(b"\r\n\r\n")
    if marker < 0:
        return False, None, b""
    header_bytes, remainder = response[:marker], response[marker + 4:]
    lines = header_bytes.decode("iso-8859-1").split("\r\n")
    parts = lines[0].split()
    try:
        status = int(parts[1])
    except (IndexError, ValueError):
        return False, None, remainder
    headers = {}
    for line in lines[1:]:
        if ":" in line:
            name, value = line.split(":", 1)
            headers[name.strip().lower()] = value.strip()
    expected = base64.b64encode(hashlib.sha1(
        (websocket_key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")
    ).digest()).decode("ascii")
    connection_tokens = {token.strip().lower() for token in headers.get("connection", "").split(",")}
    accepted = (
        status == 101
        and headers.get("upgrade", "").lower() == "websocket"
        and "upgrade" in connection_tokens
        and headers.get("sec-websocket-accept") == expected
    )
    return accepted, status, remainder


def parse_server_frame(data):
    """Decode one complete, unmasked, final server frame; reject unsafe frames."""
    if len(data) < 2:
        raise ValueError("incomplete WebSocket frame")
    first, second = data[0], data[1]
    if first & 0x70 or not first & 0x80:
        raise ValueError("fragmented or reserved WebSocket frame")
    opcode = first & 0x0F
    if opcode not in (1, 8, 9, 10):
        raise ValueError("unsupported WebSocket opcode")
    if second & 0x80:
        raise ValueError("server frame must not be masked")
    length = second & 0x7F
    offset = 2
    if length == 126:
        if len(data) < 4:
            raise ValueError("incomplete WebSocket frame")
        length = struct.unpack("!H", data[2:4])[0]
        offset = 4
    elif length == 127:
        if len(data) < 10:
            raise ValueError("incomplete WebSocket frame")
        length = struct.unpack("!Q", data[2:10])[0]
        offset = 10
    if opcode in (8, 9, 10) and length > 125:
        raise ValueError("WebSocket control frame exceeds 125-byte limit")
    if length > MAX_WS_FRAME:
        raise ValueError("WebSocket frame exceeds safety limit")
    if len(data) < offset + length:
        raise ValueError("incomplete WebSocket frame")
    return opcode, data[offset:offset + length], offset + length


def _build_client_frame(opcode, payload):
    """Build a masked client control frame as required by RFC 6455."""
    if opcode not in (8, 10):
        raise ValueError("unsupported client control opcode")
    if len(payload) > 125:
        raise ValueError("WebSocket control frame exceeds 125-byte limit")
    mask = secrets.token_bytes(4)
    masked = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
    return bytes((0x80 | opcode, 0x80 | len(payload))) + mask + masked


def _receive_kline_event(sock, initial_data=b""):
    """Read until a text event arrives, answering Ping and ignoring Pong frames."""
    buffer = initial_data
    while True:
        try:
            opcode, payload, consumed = parse_server_frame(buffer)
        except ValueError as error:
            if str(error) != "incomplete WebSocket frame":
                raise
            chunk = sock.recv(4096)
            if not chunk:
                raise ConnectionError("WebSocket closed before first event")
            buffer += chunk
            continue

        buffer = buffer[consumed:]
        if opcode == 9:
            sock.sendall(_build_client_frame(10, payload))
            continue
        if opcode == 10:
            continue
        if opcode == 8:
            raise ConnectionError("WebSocket closed before first event")
        if opcode == 1:
            return payload

def validate_kline_event(event):
    return (
        isinstance(event, dict)
        and event.get("e") == "kline"
        and event.get("s") == "BTCUSDT"
        and isinstance(event.get("k"), dict)
        and event["k"].get("s") == "BTCUSDT"
        and event["k"].get("i") == "15m"
    )


def _network_error_kind(error):
    if isinstance(error, socket.gaierror):
        return "DNS_ERROR"
    if isinstance(error, ssl.SSLError):
        return "TLS_ERROR"
    if isinstance(error, (TimeoutError, socket.timeout)):
        return "TIMEOUT"
    if isinstance(error, URLError):
        reason = error.reason
        if isinstance(reason, socket.gaierror):
            return "DNS_ERROR"
        if isinstance(reason, ssl.SSLError):
            return "TLS_ERROR"
        if isinstance(reason, (TimeoutError, socket.timeout)):
            return "TIMEOUT"
    return "CONNECTION_ERROR"


def _rest_request(opener, name, path, timeout):
    started = time.monotonic()
    request = Request(REST_BASE + path, headers={"Accept": "application/json", "User-Agent": "T0-read-only-connectivity-probe/1.0"})
    try:
        with opener.open(request, timeout=timeout) as response:
            status = response.status
            body = response.read(8_000_001)
        elapsed = round((time.monotonic() - started) * 1000, 2)
        if len(body) > 8_000_000:
            return {"name": name, "status": status, "classification": "RESPONSE_TOO_LARGE", "latency_ms": elapsed, "schema_valid": False}, None
        try:
            payload = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            payload = None
        return {"name": name, "status": status, "classification": classify_http_status(status), "latency_ms": elapsed}, payload
    except HTTPError as error:
        return {"name": name, "status": error.code, "classification": classify_http_status(error.code), "latency_ms": round((time.monotonic() - started) * 1000, 2)}, None
    except Exception as error:
        reason = error.reason if isinstance(error, URLError) else error
        detail = " ".join(str(reason).split())[:240]
        return {
            "name": name,
            "status": None,
            "classification": _network_error_kind(error),
            "error_type": type(error).__name__,
            "error_reason_type": type(reason).__name__,
            "error_detail": detail,
            "latency_ms": round((time.monotonic() - started) * 1000, 2),
        }, None


def probe_rest(timeout=8):
    """Probe public REST endpoints directly; no credentials, DB, or proxy."""
    opener = build_opener(ProxyHandler({}))
    checks = []
    time_payload = None
    endpoints = (
        ("ping", "/fapi/v1/ping"),
        ("time", "/fapi/v1/time"),
        ("exchange_info", "/fapi/v1/exchangeInfo"),
        ("closed_m15_kline", "/fapi/v1/klines?symbol=BTCUSDT&interval=15m&limit=2"),
        ("closed_h1_kline", "/fapi/v1/klines?symbol=BTCUSDT&interval=1h&limit=2"),
    )
    for name, path in endpoints:
        result, payload = _rest_request(opener, name, path, timeout)
        schema_valid = False
        if name == "time":
            schema_valid = validate_server_time(payload)
            if schema_valid:
                time_payload = payload
        elif name == "exchange_info":
            schema_valid = validate_exchange_info(payload)
        elif name == "closed_m15_kline" and time_payload:
            schema_valid = validate_klines(payload, now_ms=time_payload["serverTime"], interval_ms=900_000)
        elif name == "closed_h1_kline" and time_payload:
            schema_valid = validate_klines(payload, now_ms=time_payload["serverTime"], interval_ms=3_600_000)
        elif name == "ping":
            schema_valid = payload == {}
        result["schema_valid"] = schema_valid
        checks.append(result)
    return {"checks": checks, "passed": all(
        item.get("status") == 200 and item.get("schema_valid") is True for item in checks
    )}


def _recv_until(sock, buffer, marker, max_bytes=65536):
    while marker not in buffer:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("WebSocket closed before handshake completed")
        buffer += chunk
        if len(buffer) > max_bytes:
            raise ValueError("WebSocket handshake headers exceed safety limit")
    return buffer


def probe_websocket(timeout=8):
    """Perform direct TLS WebSocket upgrade and receive one BTCUSDT kline event."""
    key = base64.b64encode(secrets.token_bytes(16)).decode("ascii")
    request = (
        f"GET {WS_PATH} HTTP/1.1\r\n"
        f"Host: {WS_HOST}\r\n"
        "Upgrade: websocket\r\nConnection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "User-Agent: T0-read-only-connectivity-probe/1.0\r\n\r\n"
    ).encode("ascii")
    started = time.monotonic()
    stage = "TCP_CONNECT"
    status = None
    try:
        raw = socket.create_connection((WS_HOST, WS_PORT), timeout=timeout)
        stage = "TLS_HANDSHAKE"
        with raw:
            raw.settimeout(timeout)
            with ssl.create_default_context().wrap_socket(raw, server_hostname=WS_HOST) as secure:
                stage = "HTTP_UPGRADE"
                secure.sendall(request)
                received = _recv_until(secure, b"", b"\\r\\n\\r\\n")
                accepted, status, remainder = parse_http_upgrade(received, key)
                if not accepted:
                    return {
                        "status": status,
                        "stage": stage,
                        "classification": classify_http_status(status) if status else "INVALID_HANDSHAKE",
                        "latency_ms": round((time.monotonic() - started) * 1000, 2),
                        "event_valid": False,
                    }
                status = 101
                stage = "WAITING_FOR_KLINE_EVENT"
                payload = _receive_kline_event(secure, remainder)
                event = json.loads(payload)
                event_valid = validate_kline_event(event)
                return {
                    "status": 101,
                    "stage": "KLINE_EVENT_RECEIVED",
                    "classification": "REACHABLE",
                    "latency_ms": round((time.monotonic() - started) * 1000, 2),
                    "event_valid": event_valid,
                }
    except Exception as error:
        timed_out_waiting_for_event = (
            stage == "WAITING_FOR_KLINE_EVENT"
            and isinstance(error, (TimeoutError, socket.timeout))
        )
        return {
            "status": status,
            "stage": stage,
            "classification": "EVENT_TIMEOUT" if timed_out_waiting_for_event else _network_error_kind(error),
            "error_type": type(error).__name__,
            "error_detail": " ".join(str(error).split())[:240],
            "latency_ms": round((time.monotonic() - started) * 1000, 2),
            "event_valid": False,
        }


def run_probe(timeout=8):
    rest = probe_rest(timeout=timeout)
    websocket = probe_websocket(timeout=timeout)
    return {
        "scope": "READ_ONLY_PUBLIC_CONNECTIVITY",
        "exchange": "BINANCE_USDM",
        "credentials_used": False,
        "proxy_used": False,
        "database_accessed": False,
        "feeder_started": False,
        "market_data_persisted": False,
        "ai_execution_enabled": False,
        "rest": rest,
        "websocket": websocket,
        "passed": rest["passed"] and websocket.get("status") == 101 and websocket.get("event_valid") is True,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only Binance USD-M REST/WebSocket connectivity probe")
    parser.add_argument("--confirm-network", action="store_true", required=True,
                        help="Explicitly allow direct public Binance network requests")
    parser.add_argument("--timeout", type=float, default=8, help="Per-request timeout (1-30 seconds)")
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout) or not 1 <= args.timeout <= 30:
        parser.error("--timeout must be between 1 and 30 seconds")
    report = run_probe(timeout=args.timeout)
    report["observed_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print(json.dumps(report, sort_keys=True, indent=2, allow_nan=False))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
