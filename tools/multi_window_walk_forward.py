"""Fixed-parameter rolling walk-forward validation: six adjacent 30-day OOS windows.

Each OOS window is preceded by a 180-day IS diagnostic window. IS results are
reported, not used to optimize parameters. One common OKX candle snapshot is used.
Paper/backtest only; no orders are submitted.
"""
import csv
import json
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import bot
import backtest

OUT = Path(os.getenv("VALIDATION_OUTPUT_DIR", "multi_window_validation_report"))
OUT.mkdir(parents=True, exist_ok=True)
NOW = pd.Timestamp.now(tz="UTC").floor("15min")
IS_DAYS = int(os.getenv("IS_DAYS", "180"))
OOS_DAYS = int(os.getenv("OOS_DAYS", "30"))
WINDOWS = int(os.getenv("WF_WINDOWS", "6"))
if IS_DAYS < 90 or OOS_DAYS < 30 or not 2 <= WINDOWS <= 8:
    raise ValueError("Require IS >=90 days, OOS >=30 days and 2-8 windows.")
TOTAL_DAYS = IS_DAYS + OOS_DAYS * WINDOWS
if TOTAL_DAYS > 365:
    raise ValueError("IS + all adjacent OOS windows must fit within 365 days.")

# A single shared snapshot ensures variants/windows do not use separately fetched data.
start = NOW - pd.Timedelta(days=TOTAL_DAYS + 10)
end_ms = int(NOW.timestamp() * 1000)
cache = {}
for key, bar, limit in (
    ("15m", "15m", TOTAL_DAYS * 96 + 1400),
    ("1h", "1H", TOTAL_DAYS * 24 + 450),
):
    df = backtest._candles(bar, int(start.timestamp() * 1000), end_ms, limit)
    cache[key] = df.copy()
    print(f"Snapshot {key}: {len(df)} confirmed candles; "
          f"{df['open_time'].iloc[0]} .. {df['open_time'].iloc[-1]}", flush=True)

def cached_candles(bar, start_ms, end_ms, limit):
    key = "15m" if bar == "15m" else "1h"
    df = cache[key]
    ms = df["open_time"].astype("int64") // 1_000_000
    return df[(ms >= start_ms) & (ms < end_ms)].tail(limit).reset_index(drop=True)

backtest._candles = cached_candles
original_end = os.environ.get("BACKTEST_END_UTC")
original_outputs = {k: getattr(backtest, k) for k in ("STATUS","RESULT","TRADES_CSV","EQUITY_CSV","CURVE_CSV")}
original_run_id = getattr(backtest, "RUN_ID", "")
rows = []
params = {
    "DCA_ROE": bot.DCA_ROE, "DCA_ADX": bot.DCA_ADX,
    "SOFT_SL_ROE": bot.SOFT_SL_ROE, "TP_ROE": bot.TP_ROE,
    "SLIPPAGE_BPS": bot.SLIPPAGE_BPS, "FEE_RATE": bot.FEE_RATE,
}
try:
    for n in range(WINDOWS):
        # Chronological, adjacent, non-overlapping OOS windows.
        oos_end = NOW - pd.Timedelta(days=OOS_DAYS * (WINDOWS - 1 - n))
        oos_start = oos_end - pd.Timedelta(days=OOS_DAYS)
        for split, days, window_end in (
            ("IS", IS_DAYS, oos_start),
            ("OOS", OOS_DAYS, oos_end),
        ):
            name = f"wf{n+1:02d}_{split.lower()}"
            os.environ["BACKTEST_END_UTC"] = window_end.isoformat()
            os.environ["BACKTEST_RUN_ID"] = name
            backtest.RUN_ID = name
            for attr, suffix in (
                ("STATUS", "status.json"), ("RESULT", "result.json"),
                ("TRADES_CSV", "trades.csv"), ("EQUITY_CSV", "equity.csv"),
                ("CURVE_CSV", "curve.csv"),
            ):
                setattr(backtest, attr, OUT / f"{name}_{suffix}")
            report = backtest.run_backtest(days)
            rows.append({
                "window": n+1, "split": split, "run": name,
                "is_days": IS_DAYS, "oos_days": OOS_DAYS,
                "start_utc": report.get("start"), "end_utc": report.get("end"),
                "trades": report.get("trade_count"),
                "win_rate_pct": report.get("win_rate_pct"),
                "net_profit_usdt": report.get("net_profit_usdt"),
                "return_pct": report.get("return_pct"),
                "profit_factor": report.get("profit_factor"),
                "expectancy_usdt": report.get("expectancy_per_trade_usdt"),
                "max_dd_close_usdt": report.get("max_drawdown_close_usdt"),
                "max_dd_close_pct": report.get("max_drawdown_close_pct"),
                "max_dd_intrabar_usdt": report.get("max_intrabar_drawdown_usdt"),
                "max_dd_intrabar_pct": report.get("max_intrabar_drawdown_pct"),
                "fees_usdt": report.get("fees_usdt"),
                "dca_count": report.get("dca_count"),
                "tp_count": report.get("tp_count"),
                "soft_sl_count": report.get("soft_sl_count"),
                "emergency_sl_count": report.get("emergency_sl_count"),
                "end_of_test_close_count": report.get("end_of_test_close_count"),
                "parameters_json": json.dumps(params, sort_keys=True),
            })
            print(f"{name}: net={report.get('net_profit_usdt')}; "
                  f"trades={report.get('trade_count')}; "
                  f"intrabarDD={report.get('max_intrabar_drawdown_pct')}", flush=True)
finally:
    if original_end is None:
        os.environ.pop("BACKTEST_END_UTC", None)
    else:
        os.environ["BACKTEST_END_UTC"] = original_end
    os.environ.pop("BACKTEST_RUN_ID", None)
    for k,v in original_outputs.items():
        setattr(backtest, k, v)
    backtest.RUN_ID = original_run_id

with (OUT / "walk_forward_windows.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

oos = [r for r in rows if r["split"] == "OOS"]
summary = {
    "status": "completed",
    "symbol": "BTCUSDT perpetual (OKX BTC-USDT-SWAP candles)",
    "generated_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
    "is_days": IS_DAYS, "oos_days": OOS_DAYS, "windows": WINDOWS,
    "oos_windows_are_adjacent_non_overlapping": True,
    "parameters_held_fixed": params,
    "data_snapshot": {k: {"candles": len(v), "first": v["open_time"].iloc[0].isoformat(),
                          "last": v["open_time"].iloc[-1].isoformat()} for k,v in cache.items()},
    "oos_aggregate": {
        "windows_positive": sum(float(r["net_profit_usdt"] or 0) > 0 for r in oos),
        "windows_total": len(oos),
        "net_profit_sum_usdt": sum(float(r["net_profit_usdt"] or 0) for r in oos),
        "trades_sum": sum(int(r["trades"] or 0) for r in oos),
        "max_window_intrabar_dd_pct": max((float(r["max_dd_intrabar_pct"] or 0) for r in oos), default=None),
    },
    "windows": rows,
    "caveats": [
        "IS windows are diagnostic only; parameters are not tuned from these results.",
        "Adjacent OOS windows do not overlap; all use the same confirmed candle snapshot.",
        "OHLC simulation cannot resolve intrabar event ordering exactly.",
        "Maintenance margin, exact liquidation mechanics and funding may not be fully modeled.",
        "Six windows are still a limited sample and do not guarantee future performance."
    ],
}
(OUT / "walk_forward_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
print(f"Walk-forward report written to {OUT.resolve()}", flush=True)
