"""Deterministic, fail-closed UTC date window for actual Freqtrade futures backtests."""
import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

SUPPORTED_DAYS = (90, 180, 360)
WARMUP_DAYS = 7


def build_window(days, now=None):
    if type(days) is not int or days not in SUPPORTED_DAYS:
        raise ValueError("Unsupported backtest days; choose 90, 180 or 360")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("UTC-aware clock required")
    now = now.astimezone(timezone.utc)
    end = (now + timedelta(days=1)).date()
    start_time = now - timedelta(days=days)
    return {
        "days": days, "download_days": days + WARMUP_DAYS,
        "start": start_time.strftime("%Y%m%d"),
        "end_exclusive": end.strftime("%Y%m%d"),
        "timerange": start_time.strftime("%Y%m%d") + "-" + end.strftime("%Y%m%d"),
        "start_time": start_time, "now": now,
    }


def check_candle_window(dates, window, timeframe):
    if timeframe not in ("15m", "1h"):
        raise ValueError("Unsupported timeframe")
    ordered = sorted(dates)
    if not ordered:
        raise ValueError("insufficient historical candles: empty dataset")
    if any(d.tzinfo is None for d in ordered):
        raise ValueError("Naive timestamps")
    required_first = window["start_time"] - timedelta(days=WARMUP_DAYS - 1)
    # Allow up to 12h of exchange/server clock drift at the start.
    if ordered[0] > required_first + timedelta(hours=12):
        raise ValueError("insufficient warmup/history for requested window")
    max_age = timedelta(hours=3) if timeframe == "1h" else timedelta(hours=1)
    if ordered[-1] < window["now"] - max_age:
        raise ValueError("stale end-of-history candles")
    return {
        "timeframe": timeframe, "days_requested": window["days"],
        "first": ordered[0].isoformat(), "last": ordered[-1].isoformat(),
        "coverage_ok": True, "candle_count": len(ordered),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    w = build_window(args.days)
    report = {k: v.isoformat() if isinstance(v, datetime) else v for k, v in w.items()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
