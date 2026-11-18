"""Persistent server-side risk latch shared by every paper signal source.

All state lives in the same SQLite database as the paper ledger. Call
risk_block_reason() inside the ledger write transaction so a concurrent kill
cannot race an order submission.
"""
import secrets
import sqlite3
import threading

from pipeline.values import stamp


def ensure(connection):
    connection.execute("""CREATE TABLE IF NOT EXISTS paper_risk_control (
        id INTEGER PRIMARY KEY CHECK(id=1),
        paused INTEGER NOT NULL CHECK(paused IN (0,1)),
        killed INTEGER NOT NULL CHECK(killed IN (0,1)),
        reason TEXT,
        updated_at_ms INTEGER NOT NULL
    )""")
    connection.execute(
        "INSERT OR IGNORE INTO paper_risk_control VALUES (1,0,0,NULL,0)"
    )


def _read_state(connection):
    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='paper_risk_control'"
    ).fetchone()
    if not exists:
        raise sqlite3.DatabaseError("RISK_CONTROL_STATE_MISSING")
    row = connection.execute(
        "SELECT paused,killed,reason,updated_at_ms FROM paper_risk_control WHERE id=1"
    ).fetchone()
    if row is None:
        raise sqlite3.DatabaseError("RISK_CONTROL_STATE_MISSING")
    paused, killed, reason, updated_at_ms = row
    if (
        type(paused) is not int or paused not in (0, 1)
        or type(killed) is not int or killed not in (0, 1)
        or (reason is not None and not isinstance(reason, str))
        or type(updated_at_ms) is not int or updated_at_ms < 0
    ):
        raise sqlite3.DatabaseError("RISK_CONTROL_STATE_CORRUPT")
    return paused, killed, reason, updated_at_ms


def snapshot(connection):
    paused, killed, reason, updated_at_ms = _read_state(connection)
    return {"paused": bool(paused), "killed": bool(killed), "reason": reason,
            "updatedAtMs": updated_at_ms, "mode": "PAPER",
            "liveTradingSupported": False}


def risk_block_reason(connection):
    paused, killed, _, _ = _read_state(connection)
    if killed == 1:
        return "KILL_SWITCH"
    if paused == 1:
        return "RISK_PAUSED"
    return None

def set_kill(connection, enabled, at_ms, reason="OPERATOR_KILL_SWITCH"):
    if type(enabled) is not bool:
        raise ValueError("enabled must be boolean")
    at = stamp(at_ms)
    if enabled:
        connection.execute(
            "UPDATE paper_risk_control SET killed=1,reason=?,updated_at_ms=? WHERE id=1",
            (str(reason)[:160], at),
        )
    else:
        # A kill latch is intentionally not cleared by a generic resume call.
        # Explicit acknowledgement is required after readiness checks.
        raise ValueError("Kill switch requires explicit acknowledged reset")


_RESET_EVIDENCE = {}
_RESET_EVIDENCE_LOCK = threading.Lock()
_RESET_EVIDENCE_TTL_MS = 5_000
_RESET_CHECKS = {"closedCandles", "orderBook", "noPendingPaperOrders", "accountRiskReady"}


def issue_kill_reset_evidence(*, checked_at_ms, checks, candle_evidence, book_evidence):
    """Issue a one-use, process-local capability after the API readiness preflight."""
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
    with _RESET_EVIDENCE_LOCK:
        for key in [key for key, item in _RESET_EVIDENCE.items()
                    if checked-item["checkedAtMs"] > _RESET_EVIDENCE_TTL_MS]:
            _RESET_EVIDENCE.pop(key, None)
        if len(_RESET_EVIDENCE) >= 256:
            oldest = min(_RESET_EVIDENCE, key=lambda key: _RESET_EVIDENCE[key]["checkedAtMs"])
            _RESET_EVIDENCE.pop(oldest, None)
        _RESET_EVIDENCE[token] = {
            "checkedAtMs": checked, "checks": dict(checks),
            "candleEvidence": dict(candle_evidence), "bookEvidence": dict(book_evidence),
        }
    return {"token": token, "checkedAtMs": checked}


def _consume_kill_reset_evidence(evidence, at_ms):
    if not isinstance(evidence, dict) or set(evidence) != {"token", "checkedAtMs"}:
        return False
    token = evidence["token"]
    if not isinstance(token, str) or not 40 <= len(token) <= 128:
        return False
    try:
        checked, now = stamp(evidence["checkedAtMs"]), stamp(at_ms)
    except (TypeError, ValueError):
        return False
    with _RESET_EVIDENCE_LOCK:
        issued = _RESET_EVIDENCE.pop(token, None)
    return bool(issued is not None and issued["checkedAtMs"] == checked
                and 0 <= now-checked <= _RESET_EVIDENCE_TTL_MS)


def reset_kill(connection, acknowledge, readiness_evidence, at_ms):
    if acknowledge is not True:
        raise ValueError("Kill reset requires explicit acknowledgement")
    if not _consume_kill_reset_evidence(readiness_evidence, at_ms):
        raise ValueError("Kill reset requires fresh server-issued readiness evidence")
    at = stamp(at_ms)
    connection.execute(
        "UPDATE paper_risk_control SET killed=0,reason=NULL,updated_at_ms=? WHERE id=1",
        (at,),
    )


def set_paused(connection, paused, at_ms):
    if type(paused) is not bool:
        raise ValueError("paused must be boolean")
    at = stamp(at_ms)
    connection.execute(
        "UPDATE paper_risk_control SET paused=?,reason=?,updated_at_ms=? WHERE id=1",
        (int(paused), "OPERATOR_PAUSE" if paused else None, at),
    )
