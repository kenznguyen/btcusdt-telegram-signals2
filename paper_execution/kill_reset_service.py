"""Separate-process Kill Switch reset authority and local IPC transport.

Run as a dedicated OS user. The API process must not be able to read the
signing key; it receives only access to the Unix socket and IPC token. No
market/readiness evidence is accepted over the socket: this process obtains
it from trusted data providers.
"""
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import socket
import socketserver
import sqlite3
import stat
import threading

from pipeline.values import stamp

KILL_RESET_SIGNING_KEY_PATH = Path("/etc/btcquant/kill-reset-signing.key")
_RESET_EVIDENCE = {}
_RESET_EVIDENCE_LOCK = threading.Lock()
_RESET_EVIDENCE_TTL_MS = 5_000
_RESET_CHECKS = {"closedCandles", "orderBook", "noPendingPaperOrders", "accountRiskReady"}
_MAX_IPC_MESSAGE = 65_536


def _load_signing_key():
    try:
        metadata = KILL_RESET_SIGNING_KEY_PATH.stat()
        mode = stat.S_IMODE(metadata.st_mode)
        if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.geteuid()
                or mode & 0o077):
            raise ValueError("KILL_RESET_SIGNING_KEY_PERMISSIONS_INVALID")
        key = KILL_RESET_SIGNING_KEY_PATH.read_bytes()
    except OSError as error:
        raise ValueError("KILL_RESET_SIGNING_KEY_UNAVAILABLE") from error
    if len(key) < 32:
        raise ValueError("KILL_RESET_SIGNING_KEY_INVALID")
    return key


def _issue_kill_reset_evidence(*, checked_at_ms, checks, candle_evidence, book_evidence):
    """Issue one-use evidence only in the isolated process holding the signing key."""
    key = _load_signing_key()
    checked = stamp(checked_at_ms)
    if not isinstance(checks, dict) or set(checks) != _RESET_CHECKS or any(
        value is not True for value in checks.values()
    ):
        raise ValueError("KILL_RESET_READINESS_INCOMPLETE")
    if not isinstance(candle_evidence, dict) or set(candle_evidence) != {
        "datasetVersion", "closeTimeMs", "availableAtMs",
    }:
        raise ValueError("KILL_RESET_CANDLE_EVIDENCE_INVALID")
    dataset = candle_evidence["datasetVersion"]
    close_at = stamp(candle_evidence["closeTimeMs"])
    available_at = stamp(candle_evidence["availableAtMs"])
    if not isinstance(dataset, str) or not dataset.strip() or close_at > available_at or available_at > checked:
        raise ValueError("KILL_RESET_CANDLE_EVIDENCE_INVALID")
    if not isinstance(book_evidence, dict) or set(book_evidence) != {"snapshotDigest", "observedAtMs"}:
        raise ValueError("KILL_RESET_BOOK_EVIDENCE_INVALID")
    digest = book_evidence["snapshotDigest"]
    observed = stamp(book_evidence["observedAtMs"])
    if (not isinstance(digest, str) or len(digest) != 71 or not digest.startswith("sha256:")
            or any(c not in "0123456789abcdef" for c in digest[7:])
            or not -5_000 <= checked-observed <= 30_000):
        raise ValueError("KILL_RESET_BOOK_EVIDENCE_INVALID")
    token = secrets.token_urlsafe(32)
    signature = hmac.new(key, token.encode("ascii"), hashlib.sha256).hexdigest()
    with _RESET_EVIDENCE_LOCK:
        for old in [item for item, value in _RESET_EVIDENCE.items()
                    if checked-value["checkedAtMs"] > _RESET_EVIDENCE_TTL_MS]:
            _RESET_EVIDENCE.pop(old, None)
        if len(_RESET_EVIDENCE) >= 256:
            oldest = min(_RESET_EVIDENCE, key=lambda item: _RESET_EVIDENCE[item]["checkedAtMs"])
            _RESET_EVIDENCE.pop(oldest, None)
        _RESET_EVIDENCE[token] = {
            "checkedAtMs": checked, "signature": signature,
            "checks": dict(checks), "candleEvidence": dict(candle_evidence),
            "bookEvidence": dict(book_evidence),
        }
    return {"token": token, "checkedAtMs": checked, "signature": signature}


def _consume_kill_reset_evidence(evidence, at_ms):
    if not isinstance(evidence, dict) or set(evidence) != {"token", "checkedAtMs", "signature"}:
        return False
    token, signature = evidence["token"], evidence["signature"]
    if (not isinstance(token, str) or not 40 <= len(token) <= 128
            or not isinstance(signature, str) or len(signature) != 64):
        return False
    try:
        key = _load_signing_key()
        checked, now = stamp(evidence["checkedAtMs"]), stamp(at_ms)
    except (TypeError, ValueError):
        return False
    expected = hmac.new(key, token.encode("ascii"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return False
    with _RESET_EVIDENCE_LOCK:
        issued = _RESET_EVIDENCE.pop(token, None)
    return bool(issued is not None and issued["checkedAtMs"] == checked
                and hmac.compare_digest(issued["signature"], signature)
                and 0 <= now-checked <= _RESET_EVIDENCE_TTL_MS)


def _perform_reset():
    from pipeline import api

    timestamp = api.now_ms()
    try:
        readiness = api.control_readiness(timestamp)
    except (OSError, ValueError, sqlite3.Error):
        return 409, {"error": "SYSTEM_NOT_READY", "checks": {}}
    if not readiness.get("ready"):
        return 409, {"error": "SYSTEM_NOT_READY", "checks": readiness.get("checks", {})}
    try:
        result = api.ledger().reset_kill(True, readiness.get("evidence"), timestamp)
    except (ValueError, OSError, sqlite3.Error):
        return 409, {"error": "SYSTEM_NOT_READY", "checks": readiness.get("checks", {})}
    return 200, result


class _KillResetHandler(socketserver.StreamRequestHandler):
    def handle(self):
        raw = self.rfile.readline(_MAX_IPC_MESSAGE + 1)
        if not raw or len(raw) > _MAX_IPC_MESSAGE or not raw.endswith(b"\n"):
            response = {"status": 400, "body": {"error": "INVALID_CONTROL_REQUEST"}}
        else:
            try:
                payload = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError):
                payload = None
            token = getattr(self.server, "control_token", "")
            if (not isinstance(payload, dict) or set(payload) != {"acknowledge", "token"}
                    or payload.get("acknowledge") is not True
                    or not isinstance(payload.get("token"), str)
                    or not hmac.compare_digest(payload["token"], token)):
                response = {"status": 401, "body": {"error": "CONTROL_SERVICE_UNAUTHORIZED"}}
            else:
                try:
                    status, body = _perform_reset()
                except Exception:
                    status, body = 503, {"error": "KILL_RESET_CONTROL_FAILED"}
                response = {"status": status, "body": body}
        self.wfile.write(json.dumps(response, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n")


class _KillResetServer(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True
    allow_reuse_address = True


def request_kill_reset(socket_path, control_token, timeout=2.0):
    if not isinstance(socket_path, str) or not socket_path or not Path(socket_path).is_absolute():
        raise ValueError("KILL_RESET_CONTROL_SOCKET_INVALID")
    if not isinstance(control_token, str) or len(control_token) < 32:
        raise ValueError("KILL_RESET_CONTROL_TOKEN_UNAVAILABLE")
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.settimeout(timeout)
    try:
        client.connect(socket_path)
        payload = {"acknowledge": True, "token": control_token}
        client.sendall(json.dumps(payload, separators=(",", ":")).encode("utf-8") + b"\n")
        data = bytearray()
        while len(data) <= _MAX_IPC_MESSAGE:
            chunk = client.recv(4096)
            if not chunk:
                break
            data.extend(chunk)
            if b"\n" in chunk:
                break
    finally:
        client.close()
    if not data or len(data) > _MAX_IPC_MESSAGE or b"\n" not in data:
        raise ValueError("KILL_RESET_CONTROL_RESPONSE_INVALID")
    try:
        result = json.loads(bytes(data).split(b"\n", 1)[0])
        status, body = result["status"], result["body"]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        raise ValueError("KILL_RESET_CONTROL_RESPONSE_INVALID") from None
    if type(status) is not int or not isinstance(body, dict):
        raise ValueError("KILL_RESET_CONTROL_RESPONSE_INVALID")
    return status, body


def serve(socket_path=None, ready_event=None):
    _load_signing_key()
    control_token = os.environ.get("KILL_RESET_CONTROL_TOKEN", "")
    if len(control_token) < 32:
        raise RuntimeError("KILL_RESET_CONTROL_TOKEN must contain at least 32 characters")
    configured_path = socket_path or os.environ.get("KILL_RESET_CONTROL_SOCKET", "")
    if not configured_path or not Path(configured_path).is_absolute():
        raise RuntimeError("KILL_RESET_CONTROL_SOCKET must be an absolute path")
    path = Path(configured_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        if not stat.S_ISSOCK(path.lstat().st_mode):
            raise RuntimeError("Refusing to replace a non-socket control path")
        path.unlink()
    server = _KillResetServer(str(path), _KillResetHandler)
    server.control_token = control_token
    os.chmod(path, 0o660)
    if ready_event is not None:
        ready_event.set()
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        server.server_close()
        path.unlink(missing_ok=True)


if __name__ == "__main__":
    serve()
