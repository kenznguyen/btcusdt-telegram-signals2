"""Historical OHLC backtest for the isolated BTCUSDT M5 scalping prototype.

Uses confirmed OKX candles, closed M15 + H1 trend filters, one position at a time,
no DCA, fee/slippage estimates, and conservative stop-first intrabar handling.
"""
import argparse
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

BASE = "https://www.okx.com/api/v5/market/history-candles"
INST = "BTC-USDT-SWAP"
RSI_LEN = 14
DMI_LEN = 14
ADX_SMOOTH = 14


def fetch_history(bar, days, page_limit=300):
    duration = {"5m": pd.Timedelta(minutes=5), "15m": pd.Timedelta(minutes=15),
                "1H": pd.Timedelta(hours=1)}[bar]
    start_ms = int((pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=days)).timestamp() * 1000)
    rows, after = [], None
    session = requests.Session()
    while True:
        params = {"instId": INST, "bar": bar, "limit": str(page_limit)}
        if after is not None:
            params["after"] = after
        resp = session.get(BASE, params=params, timeout=25)
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("code") != "0":
            raise RuntimeError(f"OKX API error: {payload.get('msg')}")
        batch = payload.get("data", [])
        if not batch:
            break
        rows.extend(batch)
        oldest = int(batch[-1][0])
        if oldest <= start_ms or len(batch) < 2:
            break
        if after == str(oldest):
            break
        after = str(oldest)
        time.sleep(0.08)

    if not rows:
        raise RuntimeError(f"No candles returned for {bar}")
    unique = {int(r[0]): r for r in rows}
    df = pd.DataFrame(sorted(unique.values(), key=lambda r: int(r[0])),
                      columns=["open_time", "open", "high", "low", "close",
                               "vol_ccy", "volume", "vol_quote", "confirm"])
    df["open_time"] = pd.to_datetime(pd.to_numeric(df["open_time"]), unit="ms", utc=True)
    for c in ("open", "high", "low", "close"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["close_time"] = df["open_time"] + duration
    now = pd.Timestamp.now(tz="UTC")
    df = df[(df["confirm"].astype(str) == "1") & (df["close_time"] <= now)]
    df = df[df["open_time"] >= pd.Timestamp(start_ms, unit="ms", tz="UTC") - pd.Timedelta(hours=2)]
    return df.drop_duplicates("open_time").sort_values("open_time").reset_index(drop=True)


def rma(s, n):
    x = pd.Series(s, dtype=float)
    out = pd.Series(np.nan, index=x.index, dtype=float)
    valid = x.dropna()
    if len(valid) < n:
        return out
    first = valid.index[n - 1]
    seed = x.loc[valid.index[:n]].mean()
    prev = np.nan
    started = False
    for i in x.index:
        v = x.loc[i]
        if i == first:
            prev, started, out.loc[i] = seed, True, seed
        elif started:
            if pd.notna(v):
                prev = (prev * (n - 1) + v) / n
            out.loc[i] = prev
    return out


def add_indicators(df):
    d = df.copy()
    delta = d.close.diff()
    ag, al = rma(delta.clip(lower=0), RSI_LEN), rma(-delta.clip(upper=0), RSI_LEN)
    rs = ag / al.replace(0, np.nan)
    d["rsi"] = 100 - 100 / (1 + rs)
    d.loc[(al == 0) & (ag > 0), "rsi"] = 100
    d.loc[(al == 0) & (ag == 0), "rsi"] = 50
    up, down = d.high.diff(), -d.low.diff()
    pdm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=d.index)
    mdm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=d.index)
    pc = d.close.shift(1)
    tr = pd.concat([d.high - d.low, (d.high - pc).abs(), (d.low - pc).abs()], axis=1).max(axis=1)
    d["atr"] = rma(tr, DMI_LEN)
    d["plus_di"] = 100 * rma(pdm, DMI_LEN) / d.atr.replace(0, np.nan)
    d["minus_di"] = 100 * rma(mdm, DMI_LEN) / d.atr.replace(0, np.nan)
    denom = (d.plus_di + d.minus_di).replace(0, np.nan)
    d["adx"] = rma(100 * (d.plus_di - d.minus_di).abs() / denom, ADX_SMOOTH)
    return d


def run_backtest(days=90, leverage=13.0, fee_rate=0.0005, slippage_bps=5.0,
                 m15_adx_min=20.0, m5_adx_min=18.0, tp_roe=3.0,
                 hard_sl_roe=-90.0, soft_sl_roe=-35.0, start_balance=100.0):
    m5 = add_indicators(fetch_history("5m", days))
    m15 = add_indicators(fetch_history("15m", days))
    h1 = add_indicators(fetch_history("1H", days))
    if len(m5) < 100 or len(m15) < 100 or len(h1) < 50:
        raise RuntimeError(f"Not enough data: M5={len(m5)}, M15={len(m15)}, H1={len(h1)}")

    # Map only fully closed M15/H1 candles to each closed M5 candle.
    trend15 = m15[["close_time", "rsi", "adx", "plus_di", "minus_di"]].rename(
        columns={"rsi": "rsi15", "adx": "adx15", "plus_di": "plus15", "minus_di": "minus15"})
    trend1h = h1[["close_time", "rsi", "adx", "plus_di", "minus_di"]].rename(
        columns={"rsi": "rsi1h", "adx": "adx1h", "plus_di": "plus1h", "minus_di": "minus1h"})
    d = pd.merge_asof(m5.sort_values("close_time"), trend15.sort_values("close_time"),
                      on="close_time", direction="backward", allow_exact_matches=True)
    d = pd.merge_asof(d.sort_values("close_time"), trend1h.sort_values("close_time"),
                      on="close_time", direction="backward", allow_exact_matches=True)
    d = d.reset_index(drop=True)

    balance = float(start_balance)
    equity_peak = balance
    max_dd_abs = 0.0
    max_dd_pct = 0.0
    side = None
    entry = stop = entry_fee = 0.0
    entry_time = None
    cooldown_index = -1
    trades = []
    equity_curve = []
    slippage = slippage_bps / 10000.0

    def fill_price(raw, action_side):
        # action_side is the position direction: conservative adverse fill.
        return raw * (1 + slippage) if action_side == "LONG" else raw * (1 - slippage)

    for i in range(2, len(d)):
        r, p, p2 = d.iloc[i], d.iloc[i - 1], d.iloc[i - 2]
        vals = [r.rsi, r.adx, r.atr, r.rsi15, r.adx15, r.plus15, r.minus15,
                r.rsi1h, r.adx1h, r.plus1h, r.minus1h, r.plus_di, r.minus_di]
        if not np.isfinite(np.array(vals, dtype=float)).all():
            equity_curve.append({"time": r.close_time.isoformat(), "equity": balance})
            continue
        price = float(r.close)
        m15_long = r.adx15 > m15_adx_min and r.plus15 > r.minus15 and r.rsi15 > 50
        m15_short = r.adx15 > m15_adx_min and r.minus15 > r.plus15 and r.rsi15 < 50
        h1_long = r.adx1h > m15_adx_min and r.plus1h > r.minus1h and r.rsi1h > 50
        h1_short = r.adx1h > m15_adx_min and r.minus1h > r.plus1h and r.rsi1h < 50
        trend_long = m15_long and h1_long
        trend_short = m15_short and h1_short
        trend_reverse = (side == "LONG" and m15_short and h1_short) or (
            side == "SHORT" and m15_long and h1_long)
        exit_reason, exit_raw = None, price

        if side:
            gross_roe_close = ((price - entry) / entry if side == "LONG" else (entry - price) / entry) * leverage * 100
            # Hard SL uses the -90% gross ROE threshold, checked against candle extremes.
            adverse_move = abs(hard_sl_roe) / (leverage * 100)
            hard_stop_price = entry * (1 - adverse_move) if side == "LONG" else entry * (1 + adverse_move)
            hard_stop_hit = float(r.low) <= hard_stop_price if side == "LONG" else float(r.high) >= hard_stop_price
            if hard_stop_hit:
                exit_reason = "HARD_SL_ROE_MINUS_90"
                exit_raw = min(float(r.open), hard_stop_price) if side == "LONG" else max(float(r.open), hard_stop_price)
            elif gross_roe_close >= tp_roe and ((side == "LONG" and r.rsi >= 70) or (side == "SHORT" and r.rsi <= 30)):
                exit_reason = "TAKE_PROFIT"
            else:
                # Soft SL requires two consecutive CLOSED M5 candles to confirm reversal.
                opposite_now = (side == "LONG" and price < float(p.low) and r.rsi < 50) or (
                    side == "SHORT" and price > float(p.high) and r.rsi > 50)
                prev_close = float(p.close)
                opposite_prev = (side == "LONG" and prev_close < float(p2.low) and float(p.rsi) < 50) or (
                    side == "SHORT" and prev_close > float(p2.high) and float(p.rsi) > 50)
                if gross_roe_close <= soft_sl_roe and trend_reverse and opposite_now and opposite_prev:
                    exit_reason = "SOFT_SL_ROE_MINUS_35_M15_H1_REVERSAL_2X_M5"
            if exit_reason:
                exit_fill = fill_price(exit_raw, "SHORT" if side == "LONG" else "LONG")
                qty = 1.0 / entry if entry else 0.0  # normalized notional; PnL in account-currency units below
                # Fixed notional equals starting capital x leverage for reproducible comparable ROE.
                notional = start_balance * leverage
                move = (exit_fill - entry) / entry if side == "LONG" else (entry - exit_fill) / entry
                gross = notional * move
                exit_fee = notional * abs(exit_fill / entry) * fee_rate
                net = gross - entry_fee - exit_fee
                balance += net
                trades.append({
                    "trade_id": len(trades) + 1, "side": side, "entry_time": entry_time.isoformat(),
                    "exit_time": r.close_time.isoformat(), "entry_price": round(entry, 4),
                    "exit_price": round(exit_fill, 4), "gross_pnl": round(gross, 4),
                    "entry_fee": round(entry_fee, 4), "exit_fee": round(exit_fee, 4),
                    "net_pnl": round(net, 4), "net_return_on_start_pct": round(net / start_balance * 100, 4),
                    "gross_roe_at_close_pct": round(gross_roe_close, 4), "exit_reason": exit_reason
                })
                side, entry, stop, entry_fee, entry_time = None, 0.0, 0.0, 0.0, None
                cooldown_index = i
        elif i > cooldown_index + 1 and float(r.adx) > m5_adx_min:
            long_entry = (trend_long and 40 <= float(p.rsi) <= 50 and float(r.rsi) > 50
                          and float(r.plus_di) > float(r.minus_di) and price > float(p.high))
            short_entry = (trend_short and 50 <= float(p.rsi) <= 60 and float(r.rsi) < 50
                           and float(r.minus_di) > float(r.plus_di) and price < float(p.low))
            if long_entry or short_entry:
                side = "LONG" if long_entry else "SHORT"
                entry = fill_price(price, side)
                stop = None  # Hard SL is calculated from the -90% ROE threshold.
                entry_time = r.close_time
                notional = start_balance * leverage
                entry_fee = notional * fee_rate

        # Close-to-close equity only; no mark-to-market unrealized PnL while a position is open.
        equity_peak = max(equity_peak, balance)
        dd = equity_peak - balance
        max_dd_abs = max(max_dd_abs, dd)
        max_dd_pct = max(max_dd_pct, (dd / equity_peak * 100) if equity_peak else 0.0)
        equity_curve.append({"time": r.close_time.isoformat(), "equity": round(balance, 6),
                             "drawdown": round(dd, 6), "drawdown_pct": round((dd / equity_peak * 100) if equity_peak else 0, 6)})

    wins = sum(t["net_pnl"] > 0 for t in trades)
    losses = sum(t["net_pnl"] < 0 for t in trades)
    gross_profit = sum(max(0, t["net_pnl"]) for t in trades)
    gross_loss = abs(sum(min(0, t["net_pnl"]) for t in trades))
    total_net = sum(t["net_pnl"] for t in trades)
    result = {
        "symbol": "BTCUSDT (OKX BTC-USDT-SWAP candles)", "strategy": "M5 entry with closed M15 + H1 trend filters; Soft SL needs 2 closed M5 confirmations",
        "period_days_requested": days, "data_start_utc": m5.open_time.iloc[0].isoformat(),
        "data_end_utc": m5.close_time.iloc[-1].isoformat(), "m5_candles": int(len(m5)),
        "m15_candles": int(len(m15)), "h1_candles": int(len(h1)), "starting_balance": start_balance,
        "ending_balance_realized_only": round(start_balance + total_net, 4),
        "net_pnl": round(total_net, 4), "net_return_pct": round(total_net / start_balance * 100, 4),
        "trades": len(trades), "wins": wins, "losses": losses,
        "win_rate_pct": round(wins / len(trades) * 100, 4) if trades else 0.0,
        "profit_factor": round(gross_profit / gross_loss, 4) if gross_loss else (None if gross_profit == 0 else "infinity"),
        "max_drawdown_close_to_close_usd": round(max_dd_abs, 4),
        "max_drawdown_close_to_close_pct": round(max_dd_pct, 4),
        "leverage_estimate": leverage, "fee_rate_per_side": fee_rate,
        "slippage_bps_per_side": slippage_bps, "dca": "disabled",
        "open_position_at_end": side, "hard_sl_roe": hard_sl_roe, "soft_sl_roe": soft_sl_roe, "warning": "Approximate OHLC backtest; M5 entries require both latest fully closed M15 and H1 trends; Soft SL requires trend reversal on both timeframes plus two consecutive closed M5 reversal candles. Hard SL uses -90% gross ROE and candle high/low, but gap fills may be worse. No funding/liquidation/tick data; unrealized PnL excluded from equity curve; not a profit guarantee.",
        "trade_list": trades
    }
    Path("backtest_m5_90d_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    pd.DataFrame(trades).to_csv("backtest_m5_90d_trades.csv", index=False)
    pd.DataFrame(equity_curve).to_csv("backtest_m5_90d_equity.csv", index=False)
    summary = {k: v for k, v in result.items() if k != "trade_list"}
    print(json.dumps(summary, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--leverage", type=float, default=13)
    parser.add_argument("--fee-rate", type=float, default=0.0005)
    parser.add_argument("--slippage-bps", type=float, default=5)
    parser.add_argument("--start-balance", type=float, default=100)
    args = parser.parse_args()
    run_backtest(days=args.days, leverage=args.leverage, fee_rate=args.fee_rate,
                 slippage_bps=args.slippage_bps, start_balance=args.start_balance)
