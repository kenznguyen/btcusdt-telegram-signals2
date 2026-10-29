"""Verify recent closed BTCUSDT 15m/1h windows through the local read-only API."""

import argparse
import json
from pathlib import Path
import time

from data_lake.client import DataLakeClient, DataLakeError
from data_lake.local_setup import DEFAULT_CONFIG, read_configuration
from market_data.store import INTERVAL_MS, MAX_CANDLES, MAX_TIMESTAMP


_READ_ERRORS = frozenset((
    "INVALID_TIMESTAMP", "FUTURE_AS_OF", "INVALID_RESPONSE", "INVALID_RESPONSE_SCHEMA",
    "MARKET_MISMATCH", "QUERY_MISMATCH", "FUTURE_RESPONSE", "INVALID_CANDLES", "INVALID_CANDLE",
    "INVALID_CANDLE_PROVENANCE", "INVALID_CANDLE_TIME", "INVALID_COVERAGE", "DATASET_HASH_MISMATCH",
    "DATA_LAKE_HTTP_FAILURE", "INVALID_CONTENT_TYPE", "INVALID_CONTENT_ENCODING", "RESPONSE_TOO_LARGE",
    "TRUNCATED_RESPONSE", "DUPLICATE_JSON_FIELD", "INVALID_JSON_NUMBER", "DATA_LAKE_UNAVAILABLE_OR_INVALID",
))


def verify_windows(client, bars=20, now_ms=None):
    """Read both aligned closed windows at one cutoff; never infer missing candles."""
    if type(bars) is not int or not 1 <= bars <= MAX_CANDLES:
        raise ValueError("INVALID_VERIFY_BARS")
    current = time.time_ns() // 1_000_000
    cutoff = current if now_ms is None else now_ms
    if (type(cutoff) is not int or not 0 <= cutoff <= min(current, MAX_TIMESTAMP)
            or any(cutoff // step < bars for step in INTERVAL_MS.values())):
        raise ValueError("INVALID_VERIFY_TIME")
    timeframes = {}
    for timeframe, step in INTERVAL_MS.items():
        summary = {"expected": bars, "returned": None, "complete": False, "datasetVersion": None,
                   "latestCloseTimeMs": None, "latestClose": None, "reason": "READ_FAILED"}
        end = cutoff // step * step
        try:
            report = client.read_candles(timeframe, end-bars*step, end, as_of_ms=cutoff)
            latest = report["candles"][-1] if report["candles"] else None
            summary.update(returned=report["coverage"]["returned"], complete=report["coverage"]["complete"],
                           datasetVersion=report["datasetVersion"],
                           latestCloseTimeMs=latest["closeTimeMs"] if latest else None,
                           latestClose=latest["close"] if latest else None,
                           reason="VERIFIED" if report["coverage"]["complete"] else "INCOMPLETE_WINDOW")
        except DataLakeError as error:
            summary["reason"] = str(error) if str(error) in _READ_ERRORS else "READ_FAILED"
        except Exception:
            # A failed dependency must not turn its exception text into a diagnostic.
            pass
        timeframes[timeframe] = summary
    return {"verified": all(summary["complete"] for summary in timeframes.values()), "timeframes": timeframes}


def verify_local(config_path=DEFAULT_CONFIG, bars=20, now_ms=None):
    """Use the existing private local configuration without creating or changing it."""
    try:
        settings = read_configuration(config_path)
    except (OSError, ValueError, TypeError, UnicodeError):
        raise ValueError("LOCAL_CONFIG_UNAVAILABLE_OR_INVALID") from None
    client = DataLakeClient("http://127.0.0.1:" + settings["LAKE_API_PORT"], settings["LAKE_READ_TOKEN"])
    return verify_windows(client, bars=bars, now_ms=now_ms)


class _Arguments(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError("INVALID_VERIFY_ARGUMENTS")


def main(argv=None):
    parser = _Arguments(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--bars", default="20")
    try:
        args = parser.parse_args(argv)
        if not args.bars.isascii() or not args.bars.isdigit() or len(args.bars) > 4:
            raise ValueError("INVALID_VERIFY_BARS")
        result = verify_local(args.config, bars=int(args.bars))
    except (OSError, ValueError, UnicodeError) as error:
        reason = str(error)
        if reason not in ("INVALID_VERIFY_BARS", "INVALID_VERIFY_TIME", "INVALID_VERIFY_ARGUMENTS"):
            reason = "LOCAL_CONFIG_UNAVAILABLE_OR_INVALID"
        result = {"verified": False, "reason": reason}
    print(json.dumps(result))
    return 0 if result["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
