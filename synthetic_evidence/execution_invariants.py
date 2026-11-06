"""Synthetic-only position transition invariants; disconnected from any execution runtime."""
from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable


def _positive_quantity(value: Any, field: str) -> Decimal:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an exact decimal string")
    try:
        quantity = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field} must be a valid decimal string") from exc
    if not quantity.is_finite() or quantity <= 0:
        raise ValueError(f"{field} must be positive and finite")
    return quantity


def _event_bytes(event: dict[str, Any]) -> bytes:
    try:
        return json.dumps(
            event, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ValueError("position event must contain canonical JSON data") from exc


def replay_position_transitions(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Replay explicit open/reduce/close/reversal transitions with idempotent delivery.

    A reversal is admitted only after the immediately preceding active position has
    been explicitly closed to zero, and must reference that last closed position.
    This is a deterministic synthetic reference model, not an execution adapter.
    """
    positions: dict[str, dict[str, Any]] = {}
    seen: dict[str, bytes] = {}
    active_position_id: str | None = None
    last_closed_position_id: str | None = None

    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get("event_id"), str) or not event["event_id"]:
            raise ValueError("each position event requires a non-empty string event_id")
        event_id = event["event_id"]
        encoded = _event_bytes(event)
        if event_id in seen:
            if seen[event_id] != encoded:
                raise ValueError("same event ID delivered with changed bytes")
            continue
        seen[event_id] = encoded

        event_type = event.get("type")
        position_id = event.get("position_id")
        if not isinstance(position_id, str) or not position_id:
            raise ValueError("position event requires a non-empty position_id")

        if event_type in ("POSITION_OPENED", "REVERSAL_OPENED"):
            if active_position_id is not None:
                if event_type == "REVERSAL_OPENED":
                    raise ValueError("prior position must be closed before reversal")
                raise ValueError("cannot open a position while another is active")
            if position_id in positions:
                raise ValueError("position_id must be unique")
            side = event.get("side")
            if side not in ("LONG", "SHORT"):
                raise ValueError("position side must be LONG or SHORT")
            quantity = _positive_quantity(event.get("quantity"), "quantity")

            if event_type == "REVERSAL_OPENED":
                if last_closed_position_id is None or event.get("reversal_of") != last_closed_position_id:
                    raise ValueError("reversal must reference the last closed position")
                previous_side = positions[last_closed_position_id]["side"]
                if side == previous_side:
                    raise ValueError("reversal must use the opposite side")
            elif "reversal_of" in event:
                raise ValueError("initial position cannot declare reversal_of")

            positions[position_id] = {
                "side": side,
                "original_quantity": quantity,
                "remaining_quantity": quantity,
                "status": "OPEN",
            }
            active_position_id = position_id
            continue

        if event_type in ("POSITION_REDUCED", "POSITION_CLOSED"):
            if active_position_id is None or position_id != active_position_id:
                raise ValueError("transition requires the active position")
            position = positions[position_id]
            quantity = _positive_quantity(event.get("quantity"), "quantity")
            remaining = position["remaining_quantity"]

            if event_type == "POSITION_REDUCED":
                if quantity >= remaining:
                    raise ValueError("reduction must be smaller than remaining quantity; use close")
                position["remaining_quantity"] = remaining - quantity
                position["status"] = "REDUCED"
            else:
                if quantity != remaining:
                    raise ValueError("close quantity must equal the exact remaining quantity")
                position["remaining_quantity"] = Decimal(0)
                position["status"] = "CLOSED"
                active_position_id = None
                last_closed_position_id = position_id
            continue

        raise ValueError(f"unsupported position transition: {event_type}")

    return {
        "active_position_id": active_position_id,
        "last_closed_position_id": last_closed_position_id,
        "positions": {
            position_id: {
                "side": position["side"],
                "original_quantity": format(position["original_quantity"], "f"),
                "remaining_quantity": format(position["remaining_quantity"], "f"),
                "status": position["status"],
            }
            for position_id, position in sorted(positions.items())
        },
    }
