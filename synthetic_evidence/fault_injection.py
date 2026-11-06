"""Synthetic-only fault models; deliberately disconnected from T0/T1 runtime."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable


class IncompleteEquityError(ValueError):
    """Required fee/funding facts are unknown; equity cannot be certified."""


class MarkNotReadyError(ValueError):
    """A mark price is missing, stale, or has an unsafe source clock."""


def calculate_equity(realized_pnl: Decimal, *, fee: Decimal | None,
                     funding: Decimal | None) -> Decimal:
    """Return equity delta only when every required financial input is known."""
    if fee is None or funding is None:
        raise IncompleteEquityError("fee and funding must be known; UNKNOWN is not zero")
    values = (realized_pnl, fee, funding)
    if any(not isinstance(value, Decimal) or not value.is_finite() for value in values):
        raise IncompleteEquityError("equity inputs must be finite Decimal values")
    return realized_pnl - fee + funding


def _aware(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")


def validate_mark(mark_price: Decimal | None, observed_at: datetime | None,
                  now: datetime, max_age: timedelta, *,
                  clock_uncertainty: timedelta = timedelta(0)) -> Decimal:
    """Accept only positive finite marks within age and clock-uncertainty bounds."""
    _aware(now, "now")
    if observed_at is None or mark_price is None:
        raise MarkNotReadyError("mark price or source timestamp is missing")
    _aware(observed_at, "observed_at")
    if not isinstance(mark_price, Decimal) or not mark_price.is_finite() or mark_price <= 0:
        raise MarkNotReadyError("mark price must be a positive finite Decimal")
    if max_age < timedelta(0) or clock_uncertainty < timedelta(0):
        raise ValueError("age and clock uncertainty bounds must be non-negative")
    if clock_uncertainty > max_age:
        raise MarkNotReadyError("clock uncertainty exceeds the allowed mark age")
    age = now - observed_at
    if age < -clock_uncertainty:
        raise MarkNotReadyError("mark timestamp is in the future beyond clock uncertainty")
    if age + clock_uncertainty > max_age:
        raise MarkNotReadyError("mark is stale after accounting for clock uncertainty")
    return mark_price


def checkpoint_is_valid(events: Iterable[dict[str, Any]], boundary_at: datetime,
                        checkpoint_sealed_at: datetime) -> bool:
    """Invalidate a checkpoint if a late commit belongs before its event-time boundary."""
    _aware(boundary_at, "boundary_at")
    _aware(checkpoint_sealed_at, "checkpoint_sealed_at")
    for event in events:
        occurred_at, committed_at = event.get("occurred_at"), event.get("committed_at")
        _aware(occurred_at, "event.occurred_at")
        _aware(committed_at, "event.committed_at")
        if occurred_at <= boundary_at and committed_at > checkpoint_sealed_at:
            return False
    return True


def _quantity(value: Any, field: str) -> Decimal:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an exact decimal string")
    try:
        quantity = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field} must be a valid decimal string") from exc
    if not quantity.is_finite() or quantity <= 0:
        raise ValueError(f"{field} must be positive and finite")
    return quantity


def replay_order_lifecycle(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Replay a synthetic accepted/partial/cancel/replace/fill stream idempotently."""
    orders: dict[str, dict[str, Decimal | str]] = {}
    seen: dict[str, bytes] = {}
    active_order_id: str | None = None

    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get("event_id"), str):
            raise ValueError("each lifecycle event requires a string event_id")
        event_id = event["event_id"]
        try:
            encoded = json.dumps(event, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        except (TypeError, ValueError, UnicodeEncodeError) as exc:
            raise ValueError("lifecycle event must be canonical JSON data") from exc
        if event_id in seen:
            if seen[event_id] != encoded:
                raise ValueError("same event ID delivered with changed bytes")
            continue
        seen[event_id] = encoded

        event_type = event.get("type")
        order_id = event.get("order_id")
        if not isinstance(order_id, str) or not order_id:
            raise ValueError("lifecycle event requires order_id")

        if event_type == "ORDER_ACCEPTED":
            if active_order_id is not None or order_id in orders:
                raise ValueError("cannot accept an order while another order is active")
            quantity = _quantity(event.get("quantity"), "quantity")
            orders[order_id] = {"original": quantity, "filled": Decimal(0), "status": "OPEN"}
            active_order_id = order_id
            continue

        if event_type == "ORDER_REPLACED":
            old_id = event.get("replaces")
            if old_id not in orders or orders[old_id]["status"] != "CANCELLED":
                raise ValueError("replacement requires a cancelled predecessor")
            if active_order_id is not None or order_id in orders:
                raise ValueError("replacement order ID is not available")
            old = orders[old_id]
            remaining = old["original"] - old["filled"]
            quantity = _quantity(event.get("quantity"), "quantity")
            if quantity != remaining:
                raise ValueError("replacement quantity must equal predecessor remainder")
            orders[order_id] = {"original": quantity, "filled": Decimal(0), "status": "OPEN"}
            active_order_id = order_id
            continue

        if order_id not in orders or order_id != active_order_id:
            raise ValueError("event targets an inactive order")
        order = orders[order_id]

        if event_type == "ORDER_PARTIAL_FILL":
            quantity = _quantity(event.get("quantity"), "quantity")
            remaining = order["original"] - order["filled"]
            if quantity >= remaining:
                raise ValueError("partial fill must be smaller than remaining quantity")
            order["filled"] += quantity
            order["status"] = "PARTIAL"
        elif event_type == "ORDER_CANCELLED":
            order["status"] = "CANCELLED"
            active_order_id = None
        elif event_type == "ORDER_FILLED":
            quantity = _quantity(event.get("quantity"), "quantity")
            remaining = order["original"] - order["filled"]
            if quantity != remaining:
                raise ValueError("final fill must equal remaining quantity")
            order["filled"] += quantity
            order["status"] = "FILLED"
            active_order_id = None
        else:
            raise ValueError(f"unsupported lifecycle event type: {event_type}")

    filled_total = sum((order["filled"] for order in orders.values()), Decimal(0))
    remaining_total = Decimal(0)
    if active_order_id is not None:
        active = orders[active_order_id]
        remaining_total = active["original"] - active["filled"]
    status = orders[active_order_id]["status"] if active_order_id is not None else (
        orders[next(reversed(orders))]["status"] if orders else "EMPTY"
    )
    return {
        "active_order_id": active_order_id,
        "filled_quantity": format(filled_total, "f"),
        "remaining_quantity": format(remaining_total, "f"),
        "status": status,
        "orders": {
            order_id: {
                "original_quantity": format(order["original"], "f"),
                "filled_quantity": format(order["filled"], "f"),
                "status": order["status"],
            }
            for order_id, order in sorted(orders.items())
        },
    }
