"""Create three non-overlapping chronological 120-day OOS periods for 360d."""
import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


def make_windows(end_utc, days=360):
    if days != 360 or end_utc.tzinfo is None:
        raise ValueError("Walk-forward requires a timezone-aware 360-day period")
    end_day = end_utc.astimezone(timezone.utc).date()
    start_day = end_day - timedelta(days=360)
    windows = []
    for index in range(3):
        start = start_day + timedelta(days=index * 120)
        end = start + timedelta(days=120)
        windows.append({
            "index": index + 1, "days": 120,
            "start_utc": start.isoformat(), "end_exclusive_utc": end.isoformat(),
            "timerange": start.strftime("%Y%m%d") + "-" + end.strftime("%Y%m%d"),
            "training_or_reoptimization": False,
            "parity_verified": False,
        })
    return windows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    periods = make_windows(datetime.now(timezone.utc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(periods, indent=2) + "\n", encoding="utf-8")
    for window in periods:
        print(window["index"], window["timerange"])


if __name__ == "__main__":
    main()
