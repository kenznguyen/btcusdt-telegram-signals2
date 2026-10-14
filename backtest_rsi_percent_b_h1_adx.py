#!/usr/bin/env python3
"""Independent M15 RSI-%b / closed-H1 ADX backtest for Binance USDⓈ-M Futures.

This is a research backtest, separate from the live Telegram bot and its state.
Signals are evaluated on closed M15 candles; H1 filters use only fully closed H1 candles.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

BASE_URL = os.getenv("BINANCE_FUTURES_BASE_URL", "https://fapi.binance.com")
SYMBOL = os.getenv("BACKTEST_SYMBOL", "BTCUSDT").upper()
OUT = Path(os.getenv("RSIB_OUTPUT_DIR", "rsi_percent_b_backtest"))
FEE_RATE = float(os.getenv("TAKER_FEE_RATE", "0.0005"))
SLIPPAGE_TICKS = int(os.getenv("SLIPPAGE_TICKS", "2"))
TICK_SIZE = float(os.getenv("TICK_SIZE", "0.1"))


def fetch_klines(interval: str, start_ms: int, end_ms: int) -> pd.DataFrame:
    rows: list[list] = []
    cursor = start_ms
    session = requests.Session()
    while cursor < end_ms:
        response = session.get(
            f"{BASE_URL}/fapi/v1/klines",
            params={"symbol": SYMBOL, "interval": interval, "startTime": cursor,
                    "endTime": end_ms, "limit": 1500},
            timeout=30,
        )
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break
        rows.extend(batch)
        next_cursor = int(batch[-1][0]) + 1
        if next_cursor <= cursor:
            raise RuntimeError("Binance klines pagination did not advance.")
        cursor = next_cursor
        if len(batch) < 1500:
            break
        time.sleep(0.12)
    if not rows:
        raise RuntimeError(f"No {interval} candles returned for {SYMBOL}.")
    columns = ["open_ms", "open", "high", "low", "close", "volume", "close_ms",
               "quote_volume", "trades", "taker_base", "taker_quote", "ignore"]
    df = pd.DataFrame(rows, columns=columns)
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["open_time"] = pd.to_datetime(pd.to_numeric(df["open_ms"]), unit="ms", utc=True)
    df["close_time"] = pd.to_datetime(pd.to_numeric(df["close_ms"]), unit="ms", utc=True)
    df = df.drop_duplicates("open_time").sort_values("open_time")
    # Do not use a currently unfinished candle.
    now = pd.Timestamp.now(tz="UTC")
    return df.loc[df["close_time"] < now].reset_index(drop=True)


def rma(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()


def add_rsi_percent_b(df: pd.DataFrame, rsi_len=14, ema_len=28, bb_len=80, mult=3.0) -> pd.DataFrame:
    out = df.copy()
    delta = out["close"].diff()
    gain = rma(delta.clip(lower=0), rsi_len)
    loss = rma((-delta).clip(lower=0), rsi_len)
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)
    rsi = rsi.where(loss.ne(0), 100)
    out["rsi"] = rsi
    out["osc"] = out["rsi"].ewm(span=ema_len, adjust=False, min_periods=ema_len).mean()
    out["bb_basis"] = out["osc"].rolling(bb_len, min_periods=bb_len).mean()
    out["bb_dev"] = out["osc"].rolling(bb_len, min_periods=bb_len).std(ddof=0) * mult
    upper = out["bb_basis"] + out["bb_dev"]
    lower = out["bb_basis"] - out["bb_dev"]
    width = upper - lower
    out["percent_b"] = ((out["osc"] - lower) / width.replace(0, np.nan))
    return out


def add_dmi_adx(df: pd.DataFrame, length=14) -> pd.DataFrame:
    out = df.copy()
    high, low, close = out["high"], out["low"], out["close"]
    up = high.diff()
    down = -low.diff()
    plus_dm = up.where((up > down) & (up > 0), 0.0)
    minus_dm = down.where((down > up) & (down > 0), 0.0)
    prev_close = close.shift()
    tr = pd.concat([high - low, (high - prev_close).abs(),
                    (low - prev_close).abs()], axis=1).max(axis=1)
    atr = rma(tr, length)
    out["plus_di"] = 100 * rma(plus_dm, length) / atr.replace(0, np.nan)
    out["minus_di"] = 100 * rma(minus_dm, length) / atr.replace(0, np.nan)
    dx = 100 * (out["plus_di"] - out["minus_di"]).abs() / (
        out["plus_di"] + out["minus_di"]).replace(0, np.nan)
    out["adx"] = rma(dx, length)
    return out


def run(days: int, initial_capital: float, margin_pct: float, leverage: float,
        adx_len: int, adx_min: float, fee_rate: float, slippage_ticks: int) -> dict:
    if not 1 <= days <= 365:
        raise ValueError("days must be between 1 and 365")
    if initial_capital <= 0 or not 0 < margin_pct <= 100 or leverage <= 0:
        raise ValueError("Invalid capital, margin percentage, or leverage.")
    end = pd.Timestamp.now(tz="UTC").floor("15min")
    start = end - pd.Timedelta(days=days)
    warm_start = start - pd.Timedelta(days=20)
    m15 = fetch_klines("15m", int(warm_start.timestamp()*1000), int(end.timestamp()*1000))
    h1 = fetch_klines("1h", int(warm_start.timestamp()*1000), int(end.timestamp()*1000))
    m15 = add_rsi_percent_b(m15)
    h1 = add_dmi_adx(h1, adx_len)
    # Merge only H1 bars that have fully closed by the M15 candle close.
    h1_filter = h1[["close_time", "adx", "plus_di", "minus_di"]].sort_values("close_time")
    m15 = pd.merge_asof(
        m15.sort_values("close_time"), h1_filter,
        left_on="close_time", right_on="close_time", direction="backward",
        allow_exact_matches=True,
    )
    m15 = m15[(m15["open_time"] >= start) & (m15["close_time"] <= end)].reset_index(drop=True)
    if len(m15) < 100:
        raise RuntimeError(f"Not enough M15 candles for test: {len(m15)}")

    pb = m15["percent_b"]
    m15["long_cross"] = (pb > 0.2) & (pb.shift(1) <= 0.2)
    m15["short_cross"] = (pb < 0.8) & (pb.shift(1) >= 0.8)
    m15["long_exit"] = (pb > 0.8) & (pb.shift(1) <= 0.8)
    m15["short_exit"] = (pb < 0.2) & (pb.shift(1) >= 0.2)
    m15["h1_long"] = (m15["adx"] >= adx_min) & (m15["plus_di"] > m15["minus_di"])
    m15["h1_short"] = (m15["adx"] >= adx_min) & (m15["minus_di"] > m15["plus_di"])

    balance = float(initial_capital)
    position = None
    trades = []
    curve = []
    peak = balance
    max_dd = 0.0
    slip = slippage_ticks * TICK_SIZE

    def close_position(ts, raw_price, reason):
        nonlocal balance, position
        side = position["side"]
        exit_price = raw_price - slip if side == "LONG" else raw_price + slip
        gross = ((exit_price - position["entry_price"]) if side == "LONG"
                 else (position["entry_price"] - exit_price)) * position["qty"]
        exit_fee = abs(exit_price * position["qty"]) * fee_rate
        net = gross - position["entry_fee"] - exit_fee
        # Entry fee was deducted at entry; add only gross PnL less exit fee here.
        balance += gross - exit_fee
        trades.append({
            "side": side, "entry_time": position["entry_time"].isoformat(),
            "exit_time": ts.isoformat(), "entry_price": position["entry_price"],
            "exit_price": exit_price, "qty": position["qty"],
            "margin_used": position["margin"], "gross_pnl": gross,
            "entry_fee": position["entry_fee"], "exit_fee": exit_fee,
            "net_pnl": net, "return_on_margin_pct": net / position["margin"] * 100,
            "reason": reason, "balance_after": balance,
        })
        position = None

    for row in m15.itertuples(index=False):
        ts, price = row.close_time, float(row.close)
        # Equity curve marks open positions to market and estimates exit fee.
        unrealized = 0.0
        if position:
            unrealized = ((price - position["entry_price"]) if position["side"] == "LONG"
                          else (position["entry_price"] - price)) * position["qty"]
            unrealized -= abs(price * position["qty"]) * fee_rate
        equity = balance + unrealized
        peak = max(peak, equity)
        dd = peak - equity
        max_dd = max(max_dd, dd)
        curve.append({"time": ts.isoformat(), "close": price, "balance": balance,
                      "unrealized_pnl": unrealized, "equity": equity,
                      "drawdown_usdt": dd, "drawdown_pct": (dd / peak * 100 if peak else 0),
                      "position": position["side"] if position else "FLAT"})

        if position:
            should_exit = (position["side"] == "LONG" and bool(row.long_exit)) or (
                position["side"] == "SHORT" and bool(row.short_exit))
            if should_exit:
                close_position(ts, price, "RSI %b exit")
        if position is None:
            want_long = bool(row.long_cross) and bool(row.h1_long)
            want_short = bool(row.short_cross) and bool(row.h1_short)
            if want_long or want_short:
                side = "LONG" if want_long else "SHORT"
                entry_price = price + slip if side == "LONG" else price - slip
                margin = balance * margin_pct / 100
                notional = margin * leverage
                qty = notional / entry_price
                entry_fee = abs(entry_price * qty) * fee_rate
                balance -= entry_fee
                position = {"side": side, "entry_time": ts, "entry_price": entry_price,
                            "qty": qty, "margin": margin, "entry_fee": entry_fee}
    if position and len(m15):
        last = m15.iloc[-1]
        close_position(last["close_time"], float(last["close"]), "End of test")
    total_net = balance - initial_capital
    gross_wins = sum(max(0, t["net_pnl"]) for t in trades)
    gross_losses = -sum(min(0, t["net_pnl"]) for t in trades)
    wins = sum(t["net_pnl"] > 0 for t in trades)
    result = {
        "status": "success", "symbol": SYMBOL, "market": "Binance USDⓈ-M Futures",
        "timeframe_entry": "15m", "timeframe_trend_filter": "1h closed candles",
        "start_utc": m15.iloc[0]["open_time"].isoformat(),
        "end_utc": m15.iloc[-1]["close_time"].isoformat(), "requested_days": days,
        "candles_m15": len(m15), "initial_capital": initial_capital,
        "final_balance": balance, "net_profit_usdt": total_net,
        "net_profit_pct": total_net / initial_capital * 100,
        "max_drawdown_usdt": max_dd,
        "max_drawdown_pct_of_peak_equity": max((x["drawdown_pct"] for x in curve), default=0),
        "total_trades": len(trades), "winning_trades": wins,
        "win_rate_pct": wins / len(trades) * 100 if trades else 0,
        "profit_factor": gross_wins / gross_losses if gross_losses else (None if gross_wins == 0 else "Infinity"),
        "fees_usdt": sum(t["entry_fee"] + t["exit_fee"] for t in trades),
        "fee_rate_per_side": fee_rate, "slippage_ticks_each_side": slippage_ticks,
        "tick_size_assumption": TICK_SIZE, "margin_pct_of_balance": margin_pct,
        "leverage": leverage, "h1_adx_length": adx_len, "h1_adx_min": adx_min,
        "signal_definition": {
            "long_entry": "M15 RSI %b crosses above 0.2 AND last closed H1 ADX >= threshold AND +DI > -DI",
            "short_entry": "M15 RSI %b crosses below 0.8 AND last closed H1 ADX >= threshold AND -DI > +DI",
            "long_exit": "M15 RSI %b crosses above 0.8",
            "short_exit": "M15 RSI %b crosses below 0.2",
            "indicator_parameters": {"rsi": 14, "ema_smoothing": 28, "bb_length": 80, "bb_multiplier": 3},
        },
        "limitations": [
            "Research simulation only; not investment advice.",
            "Uses close-based signals, one position at a time, no funding payments or liquidation model.",
            "Fees and slippage are configurable assumptions, not a claim about the user's actual account.",
            "Indicator warm-up and exchange candle history can affect exact results.",
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(trades).to_csv(OUT / "trades.csv", index=False)
    pd.DataFrame(curve).to_csv(OUT / "equity_curve_m15.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=int(os.getenv("BACKTEST_DAYS", "180")))
    parser.add_argument("--capital", type=float, default=float(os.getenv("INITIAL_CAPITAL", "1000")))
    parser.add_argument("--margin-pct", type=float, default=float(os.getenv("MARGIN_PCT", "10")))
    parser.add_argument("--leverage", type=float, default=float(os.getenv("LEVERAGE", "1")))
    parser.add_argument("--adx-length", type=int, default=int(os.getenv("H1_ADX_LENGTH", "14")))
    parser.add_argument("--adx-min", type=float, default=float(os.getenv("H1_ADX_MIN", "20")))
    parser.add_argument("--fee-rate", type=float, default=FEE_RATE)
    parser.add_argument("--slippage-ticks", type=int, default=SLIPPAGE_TICKS)
    args = parser.parse_args()
    result = run(args.days, args.capital, args.margin_pct, args.leverage,
                 args.adx_length, args.adx_min, args.fee_rate, args.slippage_ticks)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
