"""Synthetic-only shared admission gate for CORE and AI intents.

This module is a deterministic reference model. It has no runtime, database,
exchange, network, or order-execution integration.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
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
        return json.dumps(
            intent, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ValueError("intent must contain canonical JSON data") from exc


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
    """One admission boundary for every strategy source in the synthetic model."""

    def __init__(self, policy: RiskPolicy, portfolio: PortfolioSnapshot) -> None:
        self._policy = policy
        self._exposure = _decimal(portfolio.current_exposure, "current_exposure")
        self._open_positions = portfolio.open_positions
        self._daily_loss = _decimal(portfolio.daily_loss, "daily_loss")
        self._seen: dict[str, tuple[bytes, dict[str, Any]]] = {}
        self._reservations: dict[str, dict[str, str]] = {}

    @property
    def reservation_count(self) -> int:
        return len(self._reservations)

    def admit(self, intent: dict[str, Any]) -> dict[str, Any]:
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

        source = intent.get("source")
        side = intent.get("side")
        try:
            notional = _decimal(intent.get("notional"), "notional", allow_zero=False)
        except ValueError:
            return self._remember(intent_id, encoded, self._reject("INVALID_NOTIONAL"))

        if source not in ("CORE", "AI"):
            return self._remember(intent_id, encoded, self._reject("INVALID_SOURCE"))
        if side not in ("LONG", "SHORT"):
            return self._remember(intent_id, encoded, self._reject("INVALID_SIDE"))

        if self._policy.kill_switch:
            return self._remember(intent_id, encoded, self._reject("KILL_SWITCH_ACTIVE"))
        if self._daily_loss >= _decimal(self._policy.max_daily_loss, "max_daily_loss", allow_zero=False):
            return self._remember(intent_id, encoded, self._reject("DAILY_LOSS_LIMIT"))
        if self._open_positions >= self._policy.max_open_positions:
            return self._remember(intent_id, encoded, self._reject("MAX_OPEN_POSITIONS"))
        if self._exposure + notional > _decimal(self._policy.max_total_exposure, "max_total_exposure", allow_zero=False):
            return self._remember(intent_id, encoded, self._reject("MAX_TOTAL_EXPOSURE"))

        reservation_id = f"reservation:{intent_id}"
        self._reservations[reservation_id] = {
            "intent_id": intent_id,
            "source": source,
            "side": side,
            "notional": format(notional, "f"),
        }
        self._exposure += notional
        self._open_positions += 1
        result = {
            "intent_id": intent_id,
            "source": source,
            "status": "ACCEPTED",
            "reason": "RISK_ADMITTED",
            "risk_gate": "SHARED",
            "reservation_id": reservation_id,
        }
        return self._remember(intent_id, encoded, result)

    def admit_batch(
        self,
        *,
        core_intents: Iterable[dict[str, Any]],
        ai_intents: Iterable[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        # The two strategy feeds are merged here and have no separate reservation path.
        return [self.admit(item) for item in (*tuple(core_intents), *tuple(ai_intents))]

    def _reject(self, reason: str) -> dict[str, Any]:
        return {
            "status": "REJECTED",
            "reason": reason,
            "risk_gate": "SHARED",
            "reservation_id": None,
        }

    def _remember(self, intent_id: str, encoded: bytes, result: dict[str, Any]) -> dict[str, Any]:
        decision = {"intent_id": intent_id, **result}
        self._seen[intent_id] = (encoded, decision)
        return dict(decision)
