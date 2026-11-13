"""Deterministic M15 cadence and cycle identity helpers for Continuous Core."""

import math

from core_runtime.input_bundle import validate_bundle


M15_INTERVAL_MS = 15 * 60 * 1000


def _timestamp(value, field):
    if type(value) is not int or value < 0:
        raise ValueError(f"CONTINUOUS_{field.upper()}_INVALID")
    return value


def latest_eligible_m15_open_ms(now_ms, *, settlement_ms):
    """Return the newest M15 open time whose close+settlement has elapsed."""
    now_ms = _timestamp(now_ms, "now_ms")
    settlement_ms = _timestamp(settlement_ms, "settlement_ms")
    eligible_close = ((now_ms - settlement_ms) // M15_INTERVAL_MS) * M15_INTERVAL_MS
    if eligible_close < M15_INTERVAL_MS:
        raise ValueError("CONTINUOUS_NO_ELIGIBLE_M15_CANDLE")
    return eligible_close - M15_INTERVAL_MS


def next_m15_deadline_ms(now_ms, *, settlement_ms):
    """Return the next strictly-future M15 close boundary plus settlement."""
    now_ms = _timestamp(now_ms, "now_ms")
    settlement_ms = _timestamp(settlement_ms, "settlement_ms")
    next_close = ((now_ms // M15_INTERVAL_MS) + 1) * M15_INTERVAL_MS
    return next_close + settlement_ms


def cycle_key_for_bundle(bundle, *, max_book_age_ms=5_000):
    """Validate Bundle v1 and derive the unique Core cycle from its last M15 candle."""
    validate_bundle(bundle, max_book_age_ms=max_book_age_ms)
    market = bundle["market"]
    candles = bundle["marketData"]["m15"]["candles"]
    if not candles:
        raise ValueError("CONTINUOUS_M15_CANDLES_REQUIRED")
    candle_open = _timestamp(candles[-1]["openTimeMs"], "candle_open_ms")
    if bundle.get("strategyId") != "STRATEGY_CORE":
        raise ValueError("CONTINUOUS_STRATEGY_SCOPE_INVALID")
    return (
        f'{market["exchange"]}:{market["marketType"]}:{market["symbol"]}:'
        f'15m:{candle_open}:STRATEGY_CORE'
    )


def wait_until_deadline(
    *,
    deadline_ms,
    wall_now_ms,
    monotonic,
    sleep,
    stop_requested,
    max_sleep_seconds=1.0,
):
    """Wait against one monotonic deadline; wall-clock changes cannot reset the wait."""
    deadline_ms = _timestamp(deadline_ms, "deadline_ms")
    wall_now_ms = _timestamp(wall_now_ms, "wall_now_ms")
    if not callable(monotonic) or not callable(sleep) or not callable(stop_requested):
        raise ValueError("CONTINUOUS_WAIT_CALLBACK_INVALID")
    if (isinstance(max_sleep_seconds, bool)
            or not isinstance(max_sleep_seconds, (int, float))
            or not math.isfinite(max_sleep_seconds)
            or max_sleep_seconds <= 0):
        raise ValueError("CONTINUOUS_MAX_SLEEP_INVALID")

    monotonic_deadline = monotonic() + max(0, deadline_ms - wall_now_ms) / 1000
    while True:
        if stop_requested():
            return False
        remaining = monotonic_deadline - monotonic()
        if remaining <= 0:
            return True
        sleep(min(remaining, float(max_sleep_seconds)))
