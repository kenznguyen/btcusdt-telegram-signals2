"""ENTRY-only Freqtrade DataFrame bridge for diagnostic backtesting.

Uses the exact Android RSI/DMI/ADX calculations in android_indicators and
previous CLOSED H1 values. No orders, exits or account simulation here.
"""
import pandas as pd

from android_indicators import indicator_series
from android_signal_predicates import entry_side


def _as_candles(frame):
    required = ("date", "open", "high", "low", "close", "volume")
    if any(key not in frame.columns for key in required):
        raise ValueError("Missing OHLCV column")
    if frame["date"].isna().any() or frame["date"].duplicated().any():
        raise ValueError("Invalid or duplicate candle timestamp")
    if not frame["date"].is_monotonic_increasing:
        raise ValueError("Candles must be chronological")
    return [
        {
            "timestamp_ms": int(pd.Timestamp(row.date).value // 1_000_000),
            "open": float(row.open), "high": float(row.high),
            "low": float(row.low), "close": float(row.close),
            "volume": float(row.volume), "closed": True,
        }
        for row in frame.itertuples(index=False)
    ]


def entry_diagnostics(m15, h1):
    """Return diagnostic columns on the original M15 rows, never future H1.

    In Freqtrade both dataframes have OPEN timestamps. An H1 row starting 12:00
    becomes usable at 13:00, not at 12:15 or 12:45.
    """
    m15 = m15.copy()
    h1 = h1.copy()
    if m15.empty:
        for col in ("android_entry_long", "android_entry_short",
                    "android_rsi", "android_h1_adx"):
            m15[col] = pd.Series(dtype=float)
        return m15
    left = _as_candles(m15)
    right = _as_candles(h1) if not h1.empty else []
    for candles, step, label in ((left, 900_000, "M15"), (right, 3_600_000, "H1")):
        times = [c["timestamp_ms"] for c in candles]
        if any(t % step for t in times):
            raise ValueError(f"Misaligned {label} timestamp")
        if any(b - a != step for a, b in zip(times, times[1:])):
            raise ValueError(f"Missing {label} candle")
    m15_ind = indicator_series(left)
    h1_ind = indicator_series(right)
    indexed_h1 = [
        {"available_ms": candle["timestamp_ms"] + 3_600_000, **indicator}
        for candle, indicator in zip(right, h1_ind)
    ]
    hidx = 0
    long_flags, short_flags, rsi_values, h1_adx_values = [], [], [], []
    for i, candle in enumerate(left):
        # Advance only after the corresponding H1 candle is fully closed.
        while hidx < len(indexed_h1) and indexed_h1[hidx]["available_ms"] <= candle["timestamp_ms"]:
            hidx += 1
        prior = indexed_h1[hidx - 1] if hidx else {}
        point = m15_ind[i]
        side = entry_side(
            m15_ind[i - 1]["rsi"] if i else None,
            point["rsi"], prior.get("plus_di"),
            prior.get("minus_di"), prior.get("adx")
        )
        long_flags.append(int(side == "LONG"))
        short_flags.append(int(side == "SHORT"))
        rsi_values.append(point["rsi"])
        h1_adx_values.append(prior.get("adx"))
    m15["android_entry_long"] = long_flags
    m15["android_entry_short"] = short_flags
    m15["android_rsi"] = rsi_values
    m15["android_h1_adx"] = h1_adx_values
    return m15
