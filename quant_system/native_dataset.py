"""Import *exact* checksum-audited M15/H1/fine CSVs into native Freqtrade storage.

No downloading and no order submission. The same observed candles feed both
the offline Kotlin-parity exporter and the native Freqtrade research datahandler.
Only used after audit_history() succeeds and adequate FreqAI warmup exists.
"""
import argparse
import json
from pathlib import Path

from freqtrade_parity.dataset_io import read_closed_csv
from quant_system.intrabar_audit import DAY_MS, M15_MS, audit_history

PAIR = "BTC/USDT:USDT"


def training_window(m15_path, h1_path, *, days=360, warmup_days=35):
    if days not in (180, 360) or type(warmup_days) is not int or warmup_days < 35:
        raise ValueError("Invalid native research window")
    m15 = read_closed_csv(m15_path, M15_MS)
    h1 = read_closed_csv(h1_path, 3_600_000)
    # Use the same last jointly closed M15/H1 hour boundary as the
    # intrabar audit; do not start research from an incomplete H1 window.
    common_end = min(
        m15[-1]["open_time"] + M15_MS,
        h1[-1]["open_time"] + 3_600_000,
    )
    end = common_end - common_end % 3_600_000
    start = end - days * DAY_MS
    beginning = start - warmup_days * DAY_MS
    if beginning < 0 or m15[0]["open_time"] > beginning or h1[0]["open_time"] > beginning:
        raise ValueError("MISSING_FREQAI_TRAINING_PREHISTORY")
    if len(m15) < (days + warmup_days) * 96 or len(h1) < (days + warmup_days) * 24:
        raise ValueError("FREQAI_HISTORY_TOO_SHORT")
    return start, end


def import_to_freqtrade(m15_path, h1_path, detail_path, *, days=360,
                        detail_minutes=5, datadir, warmup_days=35):
    audited = audit_history(
        m15_path, h1_path, detail_path, days=days, detail_minutes=detail_minutes
    )
    if not audited["ohlcv_verified"]:
        raise ValueError("Canonical market data not verified")
    start, end = training_window(
        m15_path, h1_path, days=days, warmup_days=warmup_days
    )
    # Imported lazily so offline/audit unit tests run without native Freqtrade.
    import pandas as pd
    from freqtrade.data.history.datahandlers import get_datahandler
    from freqtrade.enums import CandleType

    target = Path(datadir).resolve()
    target.mkdir(parents=True, exist_ok=True)
    handler = get_datahandler(target, "feather")
    inputs = {
        "15m": read_closed_csv(m15_path, 900_000),
        "1h": read_closed_csv(h1_path, 3_600_000),
        f"{detail_minutes}m": read_closed_csv(detail_path, detail_minutes * 60_000),
    }
    if len(inputs) != 3:
        raise ValueError("Duplicate native timeframe mapping")
    for timeframe, rows in inputs.items():
        frame = pd.DataFrame({
            "date": pd.to_datetime([row["open_time"] for row in rows], unit="ms", utc=True),
            **{key: [row[key] for row in rows] for key in ("open", "high", "low", "close", "volume")},
        })
        handler.ohlcv_store(PAIR, timeframe, data=frame, candle_type=CandleType.FUTURES)
        loaded = handler.ohlcv_load(
            PAIR, timeframe, drop_incomplete=False, fill_missing=False,
            candle_type=CandleType.FUTURES,
        )
        if len(loaded) != len(rows):
            raise ValueError("NATIVE_DATA_COUNT_MISMATCH")
        for source, (_index, native) in zip(rows, loaded.iterrows()):
            if int(native["date"].timestamp() * 1000) != source["open_time"]:
                raise ValueError("NATIVE_CANDLE_TIMESTAMP_MISMATCH")
            for key in ("open", "high", "low", "close", "volume"):
                if abs(float(native[key]) - source[key]) > max(1e-8, abs(source[key]) * 1e-10):
                    raise ValueError("NATIVE_OHLCV_MISMATCH")
    return {
        "native_data_match": True, "native_orders_enabled": False,
        "backtest_start_ms": start, "backtest_end_ms": end,
        "data_dir": str(target),
        "dataset_sha256": audited["dataset_sha256"],
        "detail_sha256": audited["detail_sha256"],
        "data_timeframes": sorted(inputs),
        "freqai_training_completed": False,
        "native_trade_parity_verified": False,
        "full_core_parity_certified": False,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--m15", required=True)
    p.add_argument("--h1", required=True)
    p.add_argument("--detail", required=True)
    p.add_argument("--days", type=int, choices=(180, 360), required=True)
    p.add_argument("--detail-minutes", type=int, choices=(1, 5), default=5)
    p.add_argument("--datadir", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    result = import_to_freqtrade(
        a.m15, a.h1, a.detail, days=a.days,
        detail_minutes=a.detail_minutes, datadir=a.datadir,
    )
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    Path(a.output).write_text(json.dumps(result, sort_keys=True, indent=2), encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
