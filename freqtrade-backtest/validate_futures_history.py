"""Check coverage of downloaded Freqtrade OKX perpetual OHLCV feather datasets."""
import argparse
import json
from pathlib import Path

from backtest_window import build_window, check_candle_window


def validate_files(data_dir, days):
    import pandas as pd
    window = build_window(days)
    checks = {}
    for timeframe in ("15m", "1h"):
        candidates = list(data_dir.rglob("BTC_USDT_USDT-" + timeframe + "-futures.feather"))
        if len(candidates) != 1:
            raise ValueError(f"Expected exactly one OKX futures {timeframe} Feather file: {candidates}")
        frame = pd.read_feather(candidates[0])
        if frame.empty or "date" not in frame:
            raise ValueError(f"Missing {timeframe} data")
        dates = pd.to_datetime(frame["date"], utc=True)
        if dates.duplicated().any() or not dates.is_monotonic_increasing:
            raise ValueError(f"Invalid {timeframe} order/duplicates")
        step = pd.Timedelta(minutes=15 if timeframe == "15m" else 60)
        if (dates.diff().dropna() > step).any():
            raise ValueError(f"{timeframe} contains missing historical bars")
        details = check_candle_window(dates.to_list(), window, timeframe)
        details["source_file"] = str(candidates[0])
        checks[timeframe] = details
    return {
        "source": "OKX BTC/USDT:USDT futures from Freqtrade download-data",
        "requested_days": days,
        "window_utc": window["timerange"],
        "complete": True,
        "timeframes": checks,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--days", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = validate_files(args.data_dir, args.days)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
