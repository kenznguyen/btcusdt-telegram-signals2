"""Build a bounded T2 inference window through the T0 read-only HTTP contract."""

import argparse
import os
import re
import time

from freqai_bridge.exporter import write_artifact
from freqai_bridge.http_candles import CandleHttpClient, CandleHttpConfig, CandleHttpError
from pipeline.values import stamp


_M15_INTERVAL_MS = 900_000


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


def canonical_context(now_ms=None, bars=2, *, client=None):
    """Fetch exactly the latest requested closed M15 window; fail closed on any error."""
    now = stamp(time.time_ns() // 1_000_000 if now_ms is None else now_ms)
    if type(bars) is not int or not 1 <= bars <= 32:
        raise ValueError("Canonical context must contain 1 to 32 bars")
    http_client = client if client is not None else _configured_client()
    end = now // _M15_INTERVAL_MS * _M15_INTERVAL_MS
    start = end - bars * _M15_INTERVAL_MS
    return http_client.fetch(start_ms=start, end_ms=end, as_of_ms=now)


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
