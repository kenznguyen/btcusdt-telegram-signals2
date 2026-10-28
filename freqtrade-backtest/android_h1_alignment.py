"""Timestamp-safe prior-H1 alignment for Android M15 offline replay.

Android StrategyEngine selects an H1 candle with openTime strictly earlier
than the M15 hour bucket, never the currently forming H1 candle.
"""
from bisect import bisect_left


HOUR_MS = 3_600_000


def prior_h1_for_m15(m15_open_ms, closed_h1):
    """Return most recent prior CLOSED H1 record, or None.

    Input must be sorted ascending by timestamp_ms. H1 records at the same
    hour bucket as M15 are excluded, regardless of their closed flag.
    """
    if not isinstance(m15_open_ms, int) or m15_open_ms < 0:
        raise ValueError("Invalid M15 timestamp")
    previous = -1
    times = []
    for candle in closed_h1:
        timestamp = candle["timestamp_ms"]
        if not isinstance(timestamp, int) or timestamp <= previous:
            raise ValueError("H1 timestamps must be strictly increasing")
        if timestamp % HOUR_MS:
            raise ValueError("H1 timestamp must align to hour")
        if not candle.get("closed", False):
            raise ValueError("H1 input contains an unclosed candle")
        previous = timestamp
        times.append(timestamp)
    bucket = m15_open_ms - m15_open_ms % HOUR_MS
    index = bisect_left(times, bucket) - 1
    return closed_h1[index] if index >= 0 else None


def aligned_indicators(m15_open_ms, closed_h1):
    hour = prior_h1_for_m15(m15_open_ms, closed_h1)
    if hour is None:
        return {"h1_plus_di": None, "h1_minus_di": None, "h1_adx": None}
    return {
        "h1_plus_di": hour.get("plus_di"),
        "h1_minus_di": hour.get("minus_di"),
        "h1_adx": hour.get("adx"),
    }
