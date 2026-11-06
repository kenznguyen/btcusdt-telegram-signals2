"""Synthetic-only shared admission gate with thread-safe reservation lifecycle.

This deterministic reference model is process-local and intentionally has no
runtime, database, exchange, network, or order-execution integration.
"""
from __future__ import annotations

import base64
import hashlib
import json
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable


def _decimal(value: Any, field: str, *, allow_zero: bool = True) -> Decimal:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an exact decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field} must be a valid decimal string") from exc
    if not parsed.is_finite() or parsed < 0 or (not allow_zero and parsed == 0):
        raise ValueError(f"{field} must be finite and {'non-negative' if allow_zero else 'positive'}")
    return parsed


def _canonical_intent(intent: dict[str, Any]) -> bytes:
    try:
        return json.dumps(intent, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ValueError("intent must contain canonical JSON data") from exc


def _utc(value: datetime | None) -> datetime:
    result = value or datetime.now(timezone.utc)
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return result.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


@dataclass(frozen=True)
class RiskPolicy:
    kill_switch: bool
    max_total_exposure: str
    max_open_positions: int
    max_daily_loss: str

    def __post_init__(self) -> None:
        if not isinstance(self.kill_switch, bool):
            raise ValueError("kill_switch must be boolean")
        _decimal(self.max_total_exposure, "max_total_exposure", allow_zero=False)
        _decimal(self.max_daily_loss, "max_daily_loss", allow_zero=False)
        if isinstance(self.max_open_positions, bool) or not isinstance(self.max_open_positions, int) or self.max_open_positions < 1:
            raise ValueError("max_open_positions must be a positive integer")


@dataclass(frozen=True)
class PortfolioSnapshot:
    current_exposure: str
    open_positions: int
    daily_loss: str

    def __post_init__(self) -> None:
        _decimal(self.current_exposure, "current_exposure")
        _decimal(self.daily_loss, "daily_loss")
        if isinstance(self.open_positions, bool) or not isinstance(self.open_positions, int) or self.open_positions < 0:
            raise ValueError("open_positions must be a non-negative integer")


class SharedRiskAdmission:
    """One serialized admission boundary for all strategies in this process."""

    SNAPSHOT_VERSION = 1

    def __init__(self, policy: RiskPolicy, portfolio: PortfolioSnapshot) -> None:
        self._policy = policy
        self._base_exposure = _decimal(portfolio.current_exposure, "current_exposure")
        self._base_open_positions = portfolio.open_positions
        self._daily_loss = _decimal(portfolio.daily_loss, "daily_loss")
        self._seen: dict[str, tuple[bytes, dict[str, Any]]] = {}
        self._reservations: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()

    @property
    def reservation_count(self) -> int:
        with self._lock:
            return len(self._reservations)

    @property
    def reserved_exposure(self) -> str:
        with self._lock:
            total = sum((Decimal(item["notional"]) for item in self._reservations.values() if item["status"] == "ACTIVE"), Decimal("0"))
            return format(total, "f")

    @property
    def open_reservation_count(self) -> int:
        with self._lock:
            return sum(item["status"] == "ACTIVE" for item in self._reservations.values())

    def admit(
        self,
        intent: dict[str, Any],
        *,
        now_utc: datetime | None = None,
        reservation_ttl_seconds: int = 300,
    ) -> dict[str, Any]:
        with self._lock:
            if not isinstance(intent, dict):
                raise ValueError("intent must be an object")
            intent_id = intent.get("intent_id")
            if not isinstance(intent_id, str) or not intent_id:
                raise ValueError("intent requires a non-empty intent_id")
            encoded = _canonical_intent(intent)

            previous = self._seen.get(intent_id)
            if previous is not None:
                if previous[0] != encoded:
                    raise ValueError("same intent ID delivered with changed bytes")
                return dict(previous[1])

            source, side = intent.get("source"), intent.get("side")
            try:
                notional = _decimal(intent.get("notional"), "notional", allow_zero=False)
            except ValueError:
                return self._remember(intent_id, encoded, self._reject("INVALID_NOTIONAL"))
            if source not in ("CORE", "AI"):
                return self._remember(intent_id, encoded, self._reject("INVALID_SOURCE"))
            if side not in ("LONG", "SHORT"):
                return self._remember(intent_id, encoded, self._reject("INVALID_SIDE"))
            if isinstance(reservation_ttl_seconds, bool) or not isinstance(reservation_ttl_seconds, int) or reservation_ttl_seconds <= 0:
                raise ValueError("reservation_ttl_seconds must be a positive integer")

            if self._policy.kill_switch:
                return self._remember(intent_id, encoded, self._reject("KILL_SWITCH_ACTIVE"))
            if self._daily_loss >= _decimal(self._policy.max_daily_loss, "max_daily_loss", allow_zero=False):
                return self._remember(intent_id, encoded, self._reject("DAILY_LOSS_LIMIT"))

            active = [item for item in self._reservations.values() if item["status"] == "ACTIVE"]
            exposure = self._base_exposure + sum((Decimal(item["notional"]) for item in active), Decimal("0"))
            open_positions = self._base_open_positions + len(active)
            if open_positions >= self._policy.max_open_positions:
                return self._remember(intent_id, encoded, self._reject("MAX_OPEN_POSITIONS"))
            if exposure + notional > _decimal(self._policy.max_total_exposure, "max_total_exposure", allow_zero=False):
                return self._remember(intent_id, encoded, self._reject("MAX_TOTAL_EXPOSURE"))

            created = _utc(now_utc)
            reservation_id = f"reservation:{intent_id}"
            self._reservations[reservation_id] = {
                "intent_id": intent_id, "source": source, "side": side,
                "notional": format(notional, "f"), "status": "ACTIVE",
                "created_at_utc": _iso(created),
                "expires_at_utc": _iso(created + timedelta(seconds=reservation_ttl_seconds)),
            }
            result = {
                "intent_id": intent_id, "source": source, "status": "ACCEPTED",
                "reason": "RISK_ADMITTED", "risk_gate": "SHARED",
                "reservation_id": reservation_id,
            }
            return self._remember(intent_id, encoded, result)

    def release_reservation(self, reservation_id: str) -> bool:
        with self._lock:
            reservation = self._reservations.get(reservation_id)
            if reservation is None or reservation["status"] != "ACTIVE":
                return False
            reservation["status"] = "RELEASED"
            return True

    def expire_reservations(self, now_utc: datetime) -> list[str]:
        now = _utc(now_utc)
        with self._lock:
            expired = []
            for reservation_id, reservation in self._reservations.items():
                if reservation["status"] == "ACTIVE":
                    deadline = datetime.fromisoformat(reservation["expires_at_utc"].replace("Z", "+00:00"))
                    if deadline <= now:
                        reservation["status"] = "EXPIRED"
                        expired.append(reservation_id)
            return sorted(expired)

    def reservation_status(self, reservation_id: str) -> str | None:
        with self._lock:
            item = self._reservations.get(reservation_id)
            return item["status"] if item else None

    def export_state(self) -> dict[str, Any]:
        with self._lock:
            payload = {
                "version": self.SNAPSHOT_VERSION,
                "policy": {
                    "kill_switch": self._policy.kill_switch,
                    "max_total_exposure": self._policy.max_total_exposure,
                    "max_open_positions": self._policy.max_open_positions,
                    "max_daily_loss": self._policy.max_daily_loss,
                },
                "portfolio": {
                    "current_exposure": format(self._base_exposure, "f"),
                    "open_positions": self._base_open_positions,
                    "daily_loss": format(self._daily_loss, "f"),
                },
                "reservations": {key: dict(value) for key, value in sorted(self._reservations.items())},
                "seen": {
                    key: {"encoded": base64.b64encode(value[0]).decode("ascii"), "decision": dict(value[1])}
                    for key, value in sorted(self._seen.items())
                },
            }
            canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
            return {**payload, "integrity_sha256": hashlib.sha256(canonical).hexdigest()}

    @classmethod
    def restore_state(cls, snapshot: dict[str, Any]) -> "SharedRiskAdmission":
        if not isinstance(snapshot, dict) or "integrity_sha256" not in snapshot:
            raise ValueError("snapshot integrity metadata missing")
        payload = {key: value for key, value in snapshot.items() if key != "integrity_sha256"}
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
        if not hashlib.sha256(canonical).hexdigest() == snapshot["integrity_sha256"]:
            raise ValueError("snapshot integrity check failed")
        if payload.get("version") != cls.SNAPSHOT_VERSION:
            raise ValueError("unsupported snapshot version")
        try:
            policy = RiskPolicy(**payload["policy"])
            portfolio = PortfolioSnapshot(**payload["portfolio"])
            restored = cls(policy, portfolio)
            reservations = payload["reservations"]
            seen = payload["seen"]
            if not isinstance(reservations, dict) or not isinstance(seen, dict):
                raise ValueError("invalid snapshot collections")
            for reservation_id, item in reservations.items():
                if reservation_id != f"reservation:{item['intent_id']}" or item["status"] not in ("ACTIVE", "RELEASED", "EXPIRED"):
                    raise ValueError("invalid reservation record")
                _decimal(item["notional"], "reservation notional", allow_zero=False)
                datetime.fromisoformat(item["created_at_utc"].replace("Z", "+00:00"))
                datetime.fromisoformat(item["expires_at_utc"].replace("Z", "+00:00"))
                restored._reservations[reservation_id] = dict(item)
            for intent_id, item in seen.items():
                encoded = base64.b64decode(item["encoded"], validate=True)
                decision = item["decision"]
                if decision.get("intent_id") != intent_id:
                    raise ValueError("intent ledger mismatch")
                restored._seen[intent_id] = (encoded, dict(decision))
            for reservation_id, reservation in restored._reservations.items():
                intent_id = reservation["intent_id"]
                if intent_id not in restored._seen or restored._seen[intent_id][1].get("reservation_id") != reservation_id:
                    raise ValueError("reservation ledger mismatch")
            active = [item for item in restored._reservations.values() if item["status"] == "ACTIVE"]
            exposure = restored._base_exposure + sum((Decimal(item["notional"]) for item in active), Decimal("0"))
            positions = restored._base_open_positions + len(active)
            if exposure > _decimal(policy.max_total_exposure, "max_total_exposure", allow_zero=False) or positions > policy.max_open_positions:
                raise ValueError("snapshot integrity violates risk limits")
            return restored
        except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
            if isinstance(exc, ValueError) and "snapshot integrity" in str(exc):
                raise
            raise ValueError("snapshot integrity validation failed") from exc

    def admit_batch(self, *, core_intents: Iterable[dict[str, Any]], ai_intents: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.admit(item) for item in (*tuple(core_intents), *tuple(ai_intents))]

    def _reject(self, reason: str) -> dict[str, Any]:
        return {"status": "REJECTED", "reason": reason, "risk_gate": "SHARED", "reservation_id": None}

    def _remember(self, intent_id: str, encoded: bytes, result: dict[str, Any]) -> dict[str, Any]:
        decision = {"intent_id": intent_id, **result}
        self._seen[intent_id] = (encoded, decision)
        return dict(decision)
