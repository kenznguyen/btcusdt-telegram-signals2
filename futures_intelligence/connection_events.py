"""Validate an append-only JSONL sidecar of collector WebSocket lifecycle events.

This module is deliberately separate from the legacy CSV importer. It validates
captured evidence only; it never opens a socket, starts a collector, or changes
the importer connectionStatus contract.
"""

import hashlib
import json
import re
from pathlib import Path

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
ROUTES = {"public", "market"}
EVENT_TYPES = {
    "CONNECTED", "PING_SENT", "PONG_RECEIVED", "DISCONNECTED",
    "RECONNECT_SCHEDULED",
}
DISCONNECT_REASONS = {
    "REMOTE_CLOSE", "TRANSPORT_ERROR", "HEARTBEAT_TIMEOUT", "SHUTDOWN", "UNKNOWN",
}
MAX_EVENT_BYTES = 16 * 1024
MAX_EVENTS = 1_000_000
MAX_RECONNECT_DELAY_MS = 60_000


def _required_text(event, key, maximum=128):
    value = event.get(key)
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ValueError("Invalid connection event field: " + key)
    return value


def _required_int(event, key, minimum=0, maximum=2**63 - 1):
    value = event.get(key)
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError("Invalid connection event integer: " + key)
    return value


def _parse_event(event):
    if not isinstance(event, dict) or event.get("schemaVersion") != 1:
        raise ValueError("Unsupported connection event schema")
    event_id = _required_text(event, "eventId")
    source = _required_text(event, "sourceCommit", 40)
    if not COMMIT_RE.fullmatch(source):
        raise ValueError("Invalid collector source commit")
    session = _required_text(event, "sessionId")
    connection = _required_text(event, "connectionId")
    batch = _required_int(event, "batchId", 0, 100_000)
    route = _required_text(event, "route", 16)
    if route not in ROUTES:
        raise ValueError("Unsupported WebSocket route")
    event_type = _required_text(event, "eventType", 32)
    if event_type not in EVENT_TYPES:
        raise ValueError("Unsupported connection event type")
    at = _required_int(event, "eventAtMs")
    parsed = {
        "eventId": event_id, "sourceCommit": source, "sessionId": session,
        "connectionId": connection, "batchId": batch, "route": route,
        "eventType": event_type, "eventAtMs": at,
    }
    if event_type in {"PING_SENT", "PONG_RECEIVED"}:
        parsed["heartbeatId"] = _required_text(event, "heartbeatId")
    if event_type == "DISCONNECTED":
        reason = _required_text(event, "reason", 64)
        if reason not in DISCONNECT_REASONS:
            raise ValueError("Unsupported disconnect reason")
        parsed["reason"] = reason
    if event_type == "RECONNECT_SCHEDULED":
        parsed["attempt"] = _required_int(event, "attempt", 1, 1_000_000)
        parsed["delayMs"] = _required_int(event, "delayMs", 1, MAX_RECONNECT_DELAY_MS)
    return parsed


def load_and_validate_connection_events(
    path,
    *,
    expected_sha256,
    expected_source_commit,
    expected_session_id,
    window_start_ms,
    window_end_ms,
    max_heartbeat_gap_ms,
    expected_connections=None,
):
    """Validate a JSONL sidecar and derive conservative per-connection status.

    A connection is VERIFIED_CONNECTED only when it was opened before the
    half-open window, has paired Pong evidence spanning both window boundaries,
    has no excessive Pong gap, and has no disconnect inside the window.
    """
    if not isinstance(expected_sha256, str) or not SHA256_RE.fullmatch(expected_sha256):
        raise ValueError("Expected a lowercase SHA-256 digest")
    if not isinstance(expected_source_commit, str) or not COMMIT_RE.fullmatch(expected_source_commit):
        raise ValueError("Expected a pinned collector source commit")
    if not isinstance(expected_session_id, str) or not expected_session_id:
        raise ValueError("Expected collector session identity")
    if type(window_start_ms) is not int or type(window_end_ms) is not int or not 0 <= window_start_ms < window_end_ms:
        raise ValueError("Invalid half-open connection evidence window")
    if type(max_heartbeat_gap_ms) is not int or max_heartbeat_gap_ms <= 0:
        raise ValueError("Invalid heartbeat gap policy")

    raw = Path(path).read_bytes()
    if not raw or len(raw) > MAX_EVENTS * MAX_EVENT_BYTES:
        raise ValueError("Connection event sidecar is empty or too large")
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("Connection event sidecar checksum mismatch")

    events = []
    event_ids = set()
    previous_global_at = -1
    for line in raw.splitlines():
        if not line or len(line) > MAX_EVENT_BYTES:
            raise ValueError("Blank or oversized connection event line")
        try:
            item = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Invalid connection event JSONL") from exc
        event = _parse_event(item)
        if event["eventId"] in event_ids:
            raise ValueError("Duplicate connection event identity")
        event_ids.add(event["eventId"])
        if event["sourceCommit"] != expected_source_commit or event["sessionId"] != expected_session_id:
            raise ValueError("Connection event source/session identity mismatch")
        if event["eventAtMs"] < previous_global_at:
            raise ValueError("Connection event file is not append-time ordered")
        previous_global_at = event["eventAtMs"]
        events.append(event)
        if len(events) > MAX_EVENTS:
            raise ValueError("Too many connection events")
    if not events:
        raise ValueError("Connection event sidecar contains no records")

    grouped = {}
    for event in events:
        key = event["connectionId"]
        identity = (event["batchId"], event["route"])
        group = grouped.setdefault(key, {"identity": identity, "events": []})
        if group["identity"] != identity:
            raise ValueError("Connection ID reused across batch or route")
        group["events"].append(event)

    results = []
    for connection_id, group in grouped.items():
        items = group["events"]
        opened = []
        disconnected = []
        pending = {}
        pongs = []
        reconnect = None
        state = "NEW"
        previous_at = -1
        for event in items:
            at, kind = event["eventAtMs"], event["eventType"]
            if at < previous_at:
                raise ValueError("Per-connection events are out of order")
            previous_at = at
            if kind == "CONNECTED":
                if state != "NEW":
                    raise ValueError("Connection opened more than once")
                state = "CONNECTED"
                opened.append(at)
            elif kind == "PING_SENT":
                if state != "CONNECTED":
                    raise ValueError("Ping sent while connection is not open")
                heartbeat_id = event["heartbeatId"]
                if heartbeat_id in pending:
                    raise ValueError("Duplicate outstanding heartbeat identity")
                pending[heartbeat_id] = at
            elif kind == "PONG_RECEIVED":
                heartbeat_id = event["heartbeatId"]
                if state != "CONNECTED" or heartbeat_id not in pending:
                    raise ValueError("Unmatched Pong response")
                sent_at = pending.pop(heartbeat_id)
                if at < sent_at or at - sent_at > max_heartbeat_gap_ms:
                    raise ValueError("Pong response exceeded heartbeat deadline")
                pongs.append(at)
            elif kind == "DISCONNECTED":
                if state != "CONNECTED":
                    raise ValueError("Disconnect without an open connection")
                state = "DISCONNECTED"
                disconnected.append(event)
            elif kind == "RECONNECT_SCHEDULED":
                if state != "DISCONNECTED" or reconnect is not None:
                    raise ValueError("Reconnect schedule without one preceding disconnect")
                reconnect = event

        opened_at = opened[0] if opened else None
        disconnect = disconnected[0] if disconnected else None
        in_window_disconnect = disconnect and window_start_ms <= disconnect["eventAtMs"] < window_end_ms
        window_pongs = [at for at in pongs if window_start_ms - max_heartbeat_gap_ms <= at < window_end_ms + max_heartbeat_gap_ms]
        status = "UNVERIFIABLE"
        if in_window_disconnect:
            status = "DISCONNECTED"
        elif opened_at is not None and opened_at <= window_start_ms and window_pongs:
            window_pongs.sort()
            boundary_ok = (
                window_pongs[0] <= window_start_ms + max_heartbeat_gap_ms
                and window_pongs[-1] >= window_end_ms - max_heartbeat_gap_ms
            )
            gaps_ok = all(
                right - left <= max_heartbeat_gap_ms
                for left, right in zip(window_pongs, window_pongs[1:])
            )
            if not boundary_ok or not gaps_ok:
                status = "HEARTBEAT_GAP"
            elif disconnect is None or disconnect["eventAtMs"] >= window_end_ms:
                status = "VERIFIED_CONNECTED"

        result = {
            "connectionId": connection_id,
            "batchId": group["identity"][0],
            "route": group["identity"][1],
            "connectionStatus": status,
            "connectedAtMs": opened_at,
            "disconnectedAtMs": disconnect["eventAtMs"] if disconnect else None,
            "disconnectReason": disconnect["reason"] if disconnect else None,
            "reconnectAttempt": reconnect["attempt"] if reconnect else None,
            "reconnectDelayMs": reconnect["delayMs"] if reconnect else None,
            "pongCountInEvidence": len(pongs),
        }
        results.append(result)

    results.sort(key=lambda item: (item["batchId"], item["route"], item["connectionId"]))
    if expected_connections is not None:
        expected = set()
        for item in expected_connections:
            if not isinstance(item, dict) or type(item.get("batchId")) is not int or item.get("route") not in ROUTES:
                raise ValueError("Invalid expected connection identity")
            expected.add((item["batchId"], item["route"]))
        observed = {(item["batchId"], item["route"]) for item in results}
        for batch_id, route in sorted(expected - observed):
            results.append({
                "connectionId": None, "batchId": batch_id, "route": route,
                "connectionStatus": "UNVERIFIABLE", "connectedAtMs": None,
                "disconnectedAtMs": None, "disconnectReason": None,
                "reconnectAttempt": None, "reconnectDelayMs": None,
                "pongCountInEvidence": 0,
            })
        results.sort(key=lambda item: (item["batchId"], item["route"], item["connectionId"] or ""))

    statuses = {item["connectionStatus"] for item in results}
    if "DISCONNECTED" in statuses:
        overall = "DISCONNECTED"
    elif "HEARTBEAT_GAP" in statuses:
        overall = "HEARTBEAT_GAP"
    elif not results or statuses != {"VERIFIED_CONNECTED"}:
        overall = "UNVERIFIABLE"
    else:
        overall = "VERIFIED_CONNECTED"

    return {
        "schemaVersion": 1,
        "sourceCommit": expected_source_commit,
        "sessionId": expected_session_id,
        "windowStartMs": window_start_ms,
        "windowEndMs": window_end_ms,
        "sidecarSha256": expected_sha256,
        "connectionStatus": overall,
        "verifiedConnections": sum(item["connectionStatus"] == "VERIFIED_CONNECTED" for item in results),
        "connections": results,
    }
