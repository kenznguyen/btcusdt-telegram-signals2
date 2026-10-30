"""Export native Freqtrade OHLCV into a single checksum-pinned Kotlin/Python CSV bundle.

Only runs after the operator downloads validated BTCUSDT perpetual futures
candles from an explicitly named exchange. No keys or order APIs.
"""
import argparse
import csv
import json
import hashlib
import math
import time
from pathlib import Path

from freqtrade_parity.dataset_io import read_closed_csv
from quant_system.intrabar_audit import audit_history
from quant_system.native_dataset import training_window

PAIR = "BTC/USDT:USDT"
INTERVALS = {"15m": 900_000, "1h": 3_600_000, "5m": 300_000, "1m": 60_000}


def export_native_bundle(datadir, output_dir, *, detail_minutes=5, audit_days=360,
                         observed_at_ms=None, exchange="binance"):
    if exchange not in ("okx", "binance") or type(exchange) is not str:
        raise ValueError("INVALID_SOURCE_EXCHANGE")
    if type(detail_minutes) is not int or detail_minutes not in (1, 5):
        raise ValueError("INVALID_DETAIL_TIMEFRAME")
    if audit_days not in (180, 360):
        raise ValueError("INVALID_AUDIT_DAYS")
    # Native imports happen only in the separately provisioned Codemagic runtime.
    from freqtrade.data.history.datahandlers import get_datahandler
    from freqtrade.enums import CandleType

    clock = int(time.time() * 1000) if observed_at_ms is None else observed_at_ms
    if type(clock) is not int or clock <= 0:
        raise ValueError("INVALID_AS_OF_MS")
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    handler = get_datahandler(Path(datadir).resolve(), "feather")
    files = {}
    for timeframe in ("15m", "1h", f"{detail_minutes}m"):
        width = INTERVALS[timeframe]
        frame = handler.ohlcv_load(
            PAIR, timeframe, drop_incomplete=False, fill_missing=False,
            candle_type=CandleType.FUTURES,
        )
        if frame is None or frame.empty:
            raise ValueError(f"NO_NATIVE_{timeframe.upper()}_CANDLES")
        destination = target / (f"{timeframe}.csv")
        seen = set()
        with destination.open("w", newline="", encoding="utf-8") as source:
            writer = csv.writer(source)
            writer.writerow(["open_time", "open", "high", "low", "close", "volume", "closed"])
            for _, bar in frame.iterrows():
                date = bar["date"]
                if getattr(date, "tzinfo", None) is None:
                    raise ValueError("NAIVE_NATIVE_CANDLE_TIMESTAMP")
                opening = int(date.timestamp() * 1000)
                if opening + width > clock:
                    continue
                if opening in seen:
                    raise ValueError("DUPLICATE_NATIVE_CANDLE")
                seen.add(opening)
                prices = [float(bar[key]) for key in ("open", "high", "low", "close", "volume")]
                if not all(math.isfinite(p) for p in prices):
                    raise ValueError("NONFINITE_NATIVE_CANDLE")
                writer.writerow([opening, *(format(x, ".17g") for x in prices), 1])
        read_closed_csv(destination, width)
        files[timeframe] = destination

    m15, h1, fine = files["15m"], files["1h"], files[f"{detail_minutes}m"]
    report = audit_history(m15, h1, fine, days=audit_days, detail_minutes=detail_minutes)
    training_window(m15, h1, days=audit_days, warmup_days=35)
    provenance = {
        "exchange": exchange, "symbol": "BTC/USDT:USDT",
        "marketType": "USDT_PERPETUAL",
        "dataset_sha256": report["dataset_sha256"],
        "detail_sha256": report["detail_sha256"],
    }
    provenance_digest = "sha256:" + hashlib.sha256(json.dumps(
        provenance, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    report.update({
        "exchange": exchange,
        "marketType": "USDT_PERPETUAL",
        "symbol": PAIR,
        "provenance_sha256": provenance_digest,
        "funding_mark_full_coverage_verified": False,
        "origin_claim": f"freqtrade-2026.9-{exchange}-futures-datadir",
        "origin_independently_attested": False,
        "native_store_path": str(Path(datadir).resolve()),
        "dataset_paths": {tf: str(file) for tf, file in files.items()},
        "as_of_ms": clock,
    })
    (target / "native-export-report.json").write_text(
        json.dumps(report, sort_keys=True, indent=2, allow_nan=False), encoding="utf-8"
    )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datadir", required=True)
    parser.add_argument("--exchange", choices=("binance", "okx"), required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--detail-minutes", type=int, choices=(1, 5), default=5)
    parser.add_argument("--days", type=int, choices=(180, 360), default=360)
    args = parser.parse_args()
    result = export_native_bundle(
        args.datadir, args.output_dir,
        detail_minutes=args.detail_minutes, audit_days=args.days,
        exchange=args.exchange,
    )
    print(json.dumps({
        "exchange": result["exchange"],
        "ohlcv_verified": result["ohlcv_verified"],
        "funding_mark_full_coverage_verified": False,
        "dataset_sha256": result["dataset_sha256"],
        "m15_count": result["m15_count"],
        "detail_count": result["detail_count"],
        "full_core_parity_certified": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
