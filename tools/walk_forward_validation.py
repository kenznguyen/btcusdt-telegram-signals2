"""Deterministic walk-forward and one-factor sensitivity report for the BTCUSDT strategy.

Downloads the 360-day M15/H1 candle window once, then replays fixed in-sample,
out-of-sample and parameter-perturbation runs against that same candle snapshot.
No live orders are submitted. Strategy defaults are not changed in production.
"""
import csv
import json
import os
from pathlib import Path

import pandas as pd
import bot
import backtest

OUT = Path(os.getenv("VALIDATION_OUTPUT_DIR", "strategy_validation_report"))
OUT.mkdir(parents=True, exist_ok=True)
NOW = pd.Timestamp.now(tz="UTC").floor("15min")
OOS_DAYS = int(os.getenv("OOS_DAYS", "90"))
IS_DAYS = int(os.getenv("IS_DAYS", "270"))
TOTAL_DAYS = IS_DAYS + OOS_DAYS
if OOS_DAYS < 30 or IS_DAYS < 90 or TOTAL_DAYS > 365:
    raise ValueError("Require OOS >=30 days, IS >=90 days, and combined window <=365 days.")

# Fetch one common market-data snapshot. The backtest's indicator warm-up adds 10 days.
overall_start = NOW - pd.Timedelta(days=TOTAL_DAYS + 10)
overall_end_ms = int(NOW.timestamp() * 1000)
cache = {}
for interval, bar, limit in (
    ("15m", "15m", TOTAL_DAYS * 96 + 1300),
    ("1h", "1H", TOTAL_DAYS * 24 + 400),
):
    df = backtest._candles(bar, int(overall_start.timestamp() * 1000), overall_end_ms, limit)
    cache[interval] = df.copy()
    print(f"Downloaded {interval}: {len(df)} confirmed candles", flush=True)

def cached_candles(bar, start_ms, end_ms, limit):
    interval = "15m" if bar == "15m" else "1h"
    df = cache[interval]
    times_ms = (df["open_time"].astype("int64") // 1_000_000)
    selected = df[(times_ms >= start_ms) & (times_ms < end_ms)]
    return selected.tail(limit).reset_index(drop=True)

backtest._candles = cached_candles

PARAMS = {
    "DCA_ROE": bot.DCA_ROE,
    "DCA_ADX": bot.DCA_ADX,
    "SOFT_SL_ROE": bot.SOFT_SL_ROE,
    "TP_ROE": bot.TP_ROE,
    "SLIPPAGE_BPS": bot.SLIPPAGE_BPS,
    "FEE_RATE": bot.FEE_RATE,
}
BASE = dict(PARAMS)
BASE["FEE_RATE"] = backtest.FEE

scenarios = [
    ("in_sample_270d", IS_DAYS, "IS", {}),
    ("out_of_sample_baseline_90d", OOS_DAYS, "OOS", {}),
    ("oos_dca_roe_minus15", OOS_DAYS, "OOS_sensitivity", {"DCA_ROE": -15.0}),
    ("oos_dca_roe_minus25", OOS_DAYS, "OOS_sensitivity", {"DCA_ROE": -25.0}),
    ("oos_dca_adx_40", OOS_DAYS, "OOS_sensitivity", {"DCA_ADX": 40.0}),
    ("oos_dca_adx_50", OOS_DAYS, "OOS_sensitivity", {"DCA_ADX": 50.0}),
    ("oos_soft_sl_minus30", OOS_DAYS, "OOS_sensitivity", {"SOFT_SL_ROE": -30.0}),
    ("oos_soft_sl_minus40", OOS_DAYS, "OOS_sensitivity", {"SOFT_SL_ROE": -40.0}),
    ("oos_tp_roe_4", OOS_DAYS, "OOS_sensitivity", {"TP_ROE": 4.0}),
    ("oos_tp_roe_6", OOS_DAYS, "OOS_sensitivity", {"TP_ROE": 6.0}),
    ("oos_slippage_2_5bps", OOS_DAYS, "OOS_sensitivity", {"SLIPPAGE_BPS": 2.5}),
    ("oos_slippage_10bps", OOS_DAYS, "OOS_sensitivity", {"SLIPPAGE_BPS": 10.0}),
    ("oos_fee_0_04pct", OOS_DAYS, "OOS_sensitivity", {"FEE_RATE": 0.0004}),
    ("oos_fee_0_08pct", OOS_DAYS, "OOS_sensitivity", {"FEE_RATE": 0.0008}),
]

rows = []
details = {}
original = {name: getattr(bot, name) for name in (
    "DCA_ROE", "DCA_ADX", "SOFT_SL_ROE", "TP_ROE", "SLIPPAGE_BPS", "FEE_RATE")}
original_backtest_fee = backtest.FEE
original_end = os.environ.get("BACKTEST_END_UTC")
try:
    for run_name, days, split, changes in scenarios:
        # Baseline params are restored before every independent run.
        for name, value in original.items():
            setattr(bot, name, value)
        backtest.FEE = original_backtest_fee
        for name, value in changes.items():
            if name == "FEE_RATE":
                bot.FEE_RATE = value
                backtest.FEE = value
            else:
                setattr(bot, name, value)

        end = NOW - pd.Timedelta(days=OOS_DAYS) if split == "IS" else NOW
        os.environ["BACKTEST_END_UTC"] = end.isoformat()
        backtest.STATUS = OUT / f"{run_name}_status.json"
        backtest.RESULT = OUT / f"{run_name}_result.json"
        backtest.TRADES_CSV = OUT / f"{run_name}_trades.csv"
        backtest.EQUITY_CSV = OUT / f"{run_name}_equity.csv"
        backtest.CURVE_CSV = OUT / f"{run_name}_curve.csv"
        backtest.RUN_ID = run_name
        report = backtest.run_backtest(days)
        details[run_name] = {
            "split": split, "days": days, "end_exclusive_utc": end.isoformat(),
            "parameter_overrides": changes, "report": report,
        }
        rows.append({
            "run": run_name, "split": split, "days": days,
            "start_utc": report.get("start"), "end_utc": report.get("end"),
            "trades": report.get("trade_count"), "win_rate_pct": report.get("win_rate_pct"),
            "net_profit_usdt": report.get("net_profit_usdt"), "return_pct": report.get("return_pct"),
            "profit_factor": report.get("profit_factor"), "expectancy_usdt": report.get("expectancy_per_trade_usdt"),
            "max_dd_close_usdt": report.get("max_drawdown_close_usdt"),
            "max_dd_close_pct": report.get("max_drawdown_close_pct"),
            "max_dd_intrabar_usdt": report.get("max_intrabar_drawdown_usdt"),
            "max_dd_intrabar_pct": report.get("max_intrabar_drawdown_pct"),
            "fees_usdt": report.get("fees_usdt"), "dca_count": report.get("dca_count"),
            "tp_count": report.get("tp_count"), "soft_sl_count": report.get("soft_sl_count"),
            "emergency_sl_count": report.get("emergency_sl_count"),
            "end_of_test_close_count": report.get("end_of_test_close_count"),
            "parameter_overrides_json": json.dumps(changes, sort_keys=True),
        })
        print(f"Completed {run_name}: net={report.get('net_profit_usdt')} trades={report.get('trade_count')}", flush=True)
finally:
    for name, value in original.items():
        setattr(bot, name, value)
    backtest.FEE = original_backtest_fee
    if original_end is None:
        os.environ.pop("BACKTEST_END_UTC", None)
    else:
        os.environ["BACKTEST_END_UTC"] = original_end

with (OUT / "summary.csv").open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

base = next(r for r in rows if r["run"] == "out_of_sample_baseline_90d")
for row in rows:
    row["delta_net_vs_oos_baseline_usdt"] = (
        float(row["net_profit_usdt"]) - float(base["net_profit_usdt"])
        if row["split"] == "OOS_sensitivity" else None)
    row["delta_max_intrabar_dd_vs_oos_baseline_usdt"] = (
        float(row["max_dd_intrabar_usdt"]) - float(base["max_dd_intrabar_usdt"])
        if row["split"] == "OOS_sensitivity" else None)

with (OUT / "summary.csv").open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

final = {
    "status": "completed", "symbol": "BTCUSDT perpetual (OKX BTC-USDT-SWAP candles)",
    "generated_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
    "in_sample_days": IS_DAYS, "out_of_sample_days": OOS_DAYS,
    "oos_start_utc": (NOW - pd.Timedelta(days=OOS_DAYS)).isoformat(),
    "oos_end_exclusive_utc": NOW.isoformat(),
    "data_snapshot": {k: {"candles": len(v), "first": v["open_time"].iloc[0].isoformat(),
                          "last": v["open_time"].iloc[-1].isoformat()} for k, v in cache.items()},
    "baseline_parameters": BASE, "results": rows, "runs": details,
    "caveats": [
        "Single walk-forward split; OOS is not repeatedly optimized. Sensitivity runs are one-factor-at-a-time on the same OOS period.",
        "OHLC bar simulation cannot know intrabar event ordering; intrabar drawdown is a conservative adverse-extreme estimate.",
        "Margin model does not simulate exchange maintenance margin, funding payments or exact liquidation mechanics.",
        "Fees and slippage are assumptions, not observed execution costs. End-of-test open positions are force-closed.",
        "Historical OOS is not a guarantee of future performance; compare trade count and drawdown, not just net return.",
    ],
}
(OUT / "summary.json").write_text(json.dumps(final, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
print(f"Report written to {OUT.resolve()}", flush=True)
