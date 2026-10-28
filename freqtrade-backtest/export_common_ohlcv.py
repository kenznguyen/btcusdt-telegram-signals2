"""Export exchange OHLCV as immutable, shared Android/Freqtrade input.

Outputs canonical UTC CSV+SHA256. Android ingestion is a separate step;
a common source alone does NOT prove identical entry/exit decisions.
"""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path


def export_common(data_dir, output):
    import pandas as pd
    output.mkdir(parents=True, exist_ok=True)
    manifest = {"source": "OKX BTC/USDT:USDT futures", "timezone": "UTC",
                "price_unit": "USDT", "android_import_verified": False,
                "freqtrade_android_parity_verified": False, "datasets": {}}
    for timeframe in ("5m", "15m", "1h"):
        files = list(data_dir.rglob("BTC_USDT_USDT-" + timeframe + "-futures.feather"))
        if len(files) != 1:
            raise ValueError(f"Required single futures {timeframe} file: {files}")
        frame = pd.read_feather(files[0])
        columns = ("date", "open", "high", "low", "close", "volume")
        if any(c not in frame.columns for c in columns):
            raise ValueError(f"Invalid OHLCV {timeframe}")
        frame = frame.loc[:, columns].copy()
        frame["date"] = pd.to_datetime(frame["date"], utc=True)
        if frame["date"].isna().any() or frame["date"].duplicated().any():
            raise ValueError(f"Bad timestamps {timeframe}")
        frame = frame.sort_values("date")
        name = f"btc-usdt-okx-futures-{timeframe}-utc.csv.gz"
        file = output / name
        with gzip.open(file, "wt", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(("timestamp_ms", "open", "high", "low", "close", "volume"))
            for row in frame.itertuples(index=False, name=None):
                date, *values = row
                writer.writerow((int(date.timestamp() * 1000), *values))
        digest = hashlib.sha256(file.read_bytes()).hexdigest()
        manifest["datasets"][timeframe] = {
            "file": name, "sha256": digest, "rows": len(frame),
            "first_open_utc": frame["date"].iloc[0].isoformat(),
            "last_open_utc": frame["date"].iloc[-1].isoformat(),
        }
    (output / "shared-ohlcv-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datadir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export_common(args.datadir, args.output), indent=2))


if __name__ == "__main__":
    main()
