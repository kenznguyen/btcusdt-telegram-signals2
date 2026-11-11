"""Build a bounded T2 inference window through the T0 read-only HTTP contract."""

import argparse
import os
import re
import time

from freqai_bridge.exporter import write_artifact
from freqai_bridge.http_candles import CandleHttpClient, CandleHttpConfig, CandleHttpError
from pipeline.values import stamp


_INTERVAL_MS = {"15m": 900_000, "1h": 3_600_000}


def _configured_client():
    """Load endpoint credentials from the process environment; never use local storage."""
    base_url = os.environ.get("T0_CANDLE_API_BASE_URL")
    token = os.environ.get("T0_CANDLE_API_TOKEN")
    raw_max_lag = os.environ.get("T0_CANDLE_MAX_LAG_MS")
    if not isinstance(raw_max_lag, str) or not re.fullmatch(r"[0-9]+", raw_max_lag):
        raise CandleHttpError("CONFIG_INVALID")
    try:
        max_lag_ms = int(raw_max_lag)
        config = CandleHttpConfig(base_url=base_url, token=token, max_lag_ms=max_lag_ms)
    except (TypeError, ValueError):
        raise CandleHttpError("CONFIG_INVALID") from None
    return CandleHttpClient(config)


def canonical_context(now_ms=None, bars=2, *, timeframe="15m", client=None):
    """Fetch a bounded closed M15/H1 window; fail closed on any error."""
    now = stamp(time.time_ns() // 1_000_000 if now_ms is None else now_ms)
    if timeframe not in _INTERVAL_MS:
        raise ValueError("Canonical context timeframe must be 15m or 1h")
    if type(bars) is not int or not 1 <= bars <= 3000:
        raise ValueError("Canonical context must contain 1 to 3000 bars")
    http_client = client if client is not None else _configured_client()
    interval = _INTERVAL_MS[timeframe]
    end = now // interval * interval
    start = end - bars * interval
    if timeframe == "15m":
        return http_client.fetch(start_ms=start, end_ms=end, as_of_ms=now)
    return http_client.fetch(start_ms=start, end_ms=end, as_of_ms=now, timeframe=timeframe)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=".data/canonical-window.json")
    parser.add_argument("--bars", type=int, default=2)
    args = parser.parse_args()
    try:
        window = canonical_context(bars=args.bars)
        write_artifact(args.output, window)
    except (CandleHttpError, OSError, ValueError, TypeError, OverflowError) as error:
        parser.exit(1, f"Canonical context unavailable ({type(error).__name__}).\n")
    print(window["datasetVersion"])


if __name__ == "__main__":
    main()
