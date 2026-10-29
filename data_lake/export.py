"""Export API-only canonical OHLCV for Freqtrade 2026.9 research consumers.

The manifest is the commit marker. A directory without manifest.json is incomplete.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time

from data_lake.client import (DataLakeClient, DataLakeError, QUERY_FIELDS,
                              _require, _stamp, _window)
from market_data.store import EXCHANGE, MARKET_TYPE, MAX_CANDLES, PRICE_FIELDS, SYMBOL


MAX_EXPORT_BARS = 100_000
PRECISION_NOTE = ("Canonical JSON preserves exact decimal strings and FIRST_OBSERVED availability. "
                  "Feather converts OHLCV to float64 at the consumer boundary and may lose decimal precision. "
                  "Historical OHLCV does not prove point-in-time availability before sourceAsOfMs.")


def _json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _digest(data):
    return "sha256:"+hashlib.sha256(data).hexdigest()


def _write_feather(candles, path):
    # Official 2026.9 schema/dtypes and filename rules:
    # https://github.com/freqtrade/freqtrade/blob/2026.9/freqtrade/candle_columns.py
    # https://github.com/freqtrade/freqtrade/blob/2026.9/freqtrade/data/history/datahandlers/idatahandler.py
    # https://github.com/freqtrade/freqtrade/blob/2026.9/freqtrade/data/history/datahandlers/featherdatahandler.py
    try:
        import pandas as pd
        import pyarrow  # noqa: F401 - fail before publishing if the optional engine is absent
    except ImportError:
        raise DataLakeError("FEATHER_DEPENDENCIES_REQUIRED") from None
    frame = pd.DataFrame({"date": pd.to_datetime([c["openTimeMs"] for c in candles], unit="ms", utc=True),
                          **{field: [float(c[field]) for c in candles] for field in PRICE_FIELDS}})
    frame = frame.astype({field: "float64" for field in PRICE_FIELDS})
    frame.to_feather(path, compression_level=9, compression="lz4")


def export_freqtrade(client, timeframe, start_ms, end_ms, output_dir, *, as_of_ms=None):
    """Read <=100k bars in <=2000-bar pages; publish manifest last, never overwrite.

    output_dir is a new Freqtrade datadir containing futures/*.feather plus the exact
    canonical.json and manifest.json. Only a completed manifest makes it consumable.
    """
    start, end, step = _window(timeframe, start_ms, end_ms, MAX_EXPORT_BARS)
    now = time.time_ns() // 1_000_000
    cutoff = now if as_of_ms is None else _stamp(as_of_ms)
    _require(end <= cutoff <= now, "INVALID_EXPORT_AS_OF")
    destination = Path(output_dir)
    # Exclusive reservation is portable on Codemagic macOS and Linux. No existing
    # file, directory or symlink is reused; manifest.json is the atomic commit.
    destination.mkdir()
    published = []
    try:
        with tempfile.TemporaryDirectory(prefix=".staging-", dir=destination) as staging_name:
            staging = Path(staging_name)
            candles, pages = [], []
            for opening in range(start, end, MAX_CANDLES*step):
                closing = min(end, opening+MAX_CANDLES*step)
                page = client.read_candles(timeframe, opening, closing, as_of_ms=cutoff)
                _require(page["coverage"]["complete"] is True, "INCOMPLETE_EXPORT_PAGE")
                candles.extend(page["candles"])
                pages.append({"startMs": opening, "endMs": closing, "datasetVersion": page["datasetVersion"],
                              "rows": page["coverage"]["returned"]})
            _require(len(candles) == (end-start)//step, "INCOMPLETE_EXPORT")
            canonical = dict(exchange=EXCHANGE, marketType=MARKET_TYPE, symbol=SYMBOL, timeframe=timeframe,
                             startMs=start, endMs=end, asOfMs=cutoff, candles=candles)
            version = _digest(_json_bytes({key: canonical[key] for key in QUERY_FIELDS}))
            canonical.update(datasetVersion=version, coverage={"expected": len(candles), "returned": len(candles),
                                                             "complete": True, "gaps": []})
            (staging/"canonical.json").write_bytes(_json_bytes(canonical))
            feather_relative = f"futures/BTC_USDT_USDT-{timeframe}-futures.feather"
            (staging/"futures").mkdir()
            _write_feather(candles, staging/feather_relative)
            files = {}
            for relative in ("canonical.json", feather_relative):
                data = (staging/relative).read_bytes()
                files[relative] = {"sha256": _digest(data), "bytes": len(data)}
            manifest = {"schemaVersion": 1, "source": "data-lake-api", "exchange": EXCHANGE,
                        "marketType": MARKET_TYPE, "symbol": SYMBOL, "timeframe": timeframe,
                        "startMs": start, "endMs": end, "sourceAsOfMs": cutoff,
                        "bars": len(candles), "datasetVersion": version, "pages": pages,
                        "format": "FREQTRADE_2026_9_OHLCV_FEATHER", "precisionNote": PRECISION_NOTE,
                        "files": files}
            (staging/"manifest.json").write_bytes(_json_bytes(manifest))
            (destination/"futures").mkdir()
            # Hard links publish each fully written file exclusively on the same
            # filesystem. The final link atomically installs the commit marker.
            for relative in (*files, "manifest.json"):
                os.link(staging/relative, destination/relative)
                published.append(destination/relative)
        return manifest
    except BaseException:
        for path in reversed(published):
            path.unlink(missing_ok=True)
        try:
            (destination/"futures").rmdir()
        except OSError:
            pass
        try:
            destination.rmdir()
        except OSError:
            pass
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description="Export canonical API OHLCV; consume only after manifest.json exists")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--timeframe", required=True, choices=("15m", "1h"))
    parser.add_argument("--start-ms", required=True, type=int)
    parser.add_argument("--end-ms", required=True, type=int)
    parser.add_argument("--as-of-ms", type=int)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    try:
        client = DataLakeClient(args.base_url, os.environ.get("MARKET_DATA_TOKEN", ""))
        manifest = export_freqtrade(client, args.timeframe, args.start_ms, args.end_ms,
                                    args.output_dir, as_of_ms=args.as_of_ms)
    except (OSError, ValueError, ImportError):
        print("EXPORT_FAILED", file=sys.stderr)
        return 1
    print(json.dumps({"bars": manifest["bars"], "datasetVersion": manifest["datasetVersion"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
