"""Isolated A/B backtest for BTCUSDT perpetual; never touches live state or Telegram outputs.

A uses the current project's M15 RSI + last fully closed H1 directional ADX strategy
with Smart DCA and risk exits. B implements the exact user-supplied RSI %b Pine rules
on H1 by default. Both use the same OKX BTC-USDT-SWAP candles, $200 starting balance,
$50 initial margin, $50 DCA margin for A, $50 standardized entry margin for B,
13x leverage, 0.04% fee per side and 5 bps adverse slippage.
Funding, maintenance-margin tiers and liquidation are not modeled.
"""
import csv
import json
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
import requests

import bot

OUT = Path(os.getenv("COMPARE_OUT_DIR", "comparison_results"))
DAYS = int(os.getenv("COMPARE_DAYS", "180"))
START_BALANCE = float(os.getenv("COMPARE_INITIAL_CAPITAL", "200"))
ENTRY_MARGIN = float(os.getenv("COMPARE_ENTRY_MARGIN", "50"))
DCA_MARGIN = float(os.getenv("COMPARE_DCA_MARGIN", "50"))
LEVERAGE = float(os.getenv("COMPARE_LEVERAGE", "13"))
FEE = float(os.getenv("COMPARE_FEE_RATE", "0.0004"))
SLIPPAGE_BPS = float(os.getenv("COMPARE_SLIPPAGE_BPS", "5"))
OKX_URL = "https://www.okx.com/api/v5/market/history-candles"
INSTRUMENT = "BTC-USDT-SWAP"


def fetch_candles(bar, start, end):
    """Download confirmed candles in the requested UTC window plus warm-up."""
    rows, after = [], None
    start_ms, end_ms = int(start.timestamp() * 1000), int(end.timestamp() * 1000)
    while True:
        params = {"instId": INSTRUMENT, "bar": bar, "limit": "300"}
        if after is not None:
            params["after"] = after
        response = requests.get(OKX_URL, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") != "0":
            raise RuntimeError(f"OKX API error: {payload.get('msg')}")
        batch = payload.get("data", [])
        if not batch:
            break
        rows.extend(x for x in batch if start_ms <= int(x[0]) < end_ms and str(x[8]) == "1")
        oldest = int(batch[-1][0])
        if oldest <= start_ms or len(batch) < 2:
            break
        if after == str(oldest):
            raise RuntimeError("OKX pagination stopped advancing.")
        after = str(oldest)
    if not rows:
        raise RuntimeError(f"No confirmed candles returned for {bar}.")
    rows = sorted({int(x[0]): x for x in rows}.values(), key=lambda x: int(x[0]))
    df = pd.DataFrame(rows, columns=["open_time","open","high","low","close",
        "volume_contracts","volume","quote_volume","confirm"])
    df["open_time"] = pd.to_datetime(pd.to_numeric(df["open_time"]), unit="ms", utc=True)
    for col in ("open", "high", "low", "close"):
        df[col] = pd.to_numeric(df[col], errors="raise")
    delta = pd.Timedelta(minutes=15 if bar == "15m" else 60)
    df["close_time"] = df["open_time"] + delta
    return df.reset_index(drop=True)


def add_b_indicators(df):
    """Pine ta.rsi -> ta.ema -> ta.bb approximation with population stdev."""
    d = df.copy()
    # Reuse the project's Wilder RSI calculation, with its configured RSI length.
    d["rsi_raw"] = bot.add_indicators(d)["rsi"]
    d["rsi_smoothed"] = d["rsi_raw"].ewm(span=28, adjust=False, min_periods=28).mean()
    basis = d["rsi_smoothed"].rolling(80, min_periods=80).mean()
    stdev = d["rsi_smoothed"].rolling(80, min_periods=80).std(ddof=0)
    upper, lower = basis + 3.0 * stdev, basis - 3.0 * stdev
    width = upper - lower
    d["pb"] = (d["rsi_smoothed"] - lower) / width.replace(0, np.nan)
    d["pb_prev"] = d["pb"].shift(1)
    return d


def fill_price(price, action):
    slip = SLIPPAGE_BPS / 10000.0
    return price * (1 + slip if action == "BUY" else 1 - slip)


def pnl(side, avg, price, qty):
    return (price - avg) * qty if side == "LONG" else (avg - price) * qty


def run_strategy_a(m15, h1, test_start):
    """A: mirror current bot/backtest exit and DCA rules, with explicit fixed margins."""
    d = bot.add_indicators(m15).reset_index(drop=True)
    h = bot.add_indicators(h1).set_index("open_time")
    balance, pos, trades, curve = START_BALANCE, None, [], []
    counts = {"DCA": 0, "TP": 0, "Soft SL": 0, "Emergency SL": 0, "DCA skipped insufficient margin": 0}
    for i, row in d.iterrows():
        ts = row.open_time
        if ts < test_start:
            continue
        close, op, high, low = map(float, (row.close, row.open, row.high, row.low))
        prior = d.iloc[i-1] if i else None
        available_h = h.loc[h.index < ts.floor("h")]
        if available_h.empty or prior is None:
            continue
        hr = available_h.iloc[-1]
        if any(pd.isna(x) for x in (row.rsi, row.adx, prior.rsi, hr.plus_di, hr.minus_di, hr.adx)):
            continue
        rsi, adx, prev_rsi = float(row.rsi), float(row.adx), float(prior.rsi)
        hp, hm, ha = float(hr.plus_di), float(hr.minus_di), float(hr.adx)
        go_long = hp > hm and ha > 20 and prev_rsi <= 30 and rsi > 30
        go_short = hm > hp and ha > 20 and prev_rsi >= 70 and rsi < 70
        exited = False
        if pos:
            side, avg, qty = pos["side"], pos["avg"], pos["qty"]
            roe = pnl(side, avg, close, qty) / pos["margin"] * 100
            emergency_level = avg * (1 - 0.90 / LEVERAGE) if side == "LONG" else avg * (1 + 0.90 / LEVERAGE)
            soft_level = avg * (1 - 0.35 / LEVERAGE) if side == "LONG" else avg * (1 + 0.35 / LEVERAGE)
            emergency = low <= emergency_level if side == "LONG" else high >= emergency_level
            reversal = (hm > hp if side == "LONG" else hp > hm) and ha > 35
            two_bear = close < op and float(prior.close) < float(prior.open)
            two_bull = close > op and float(prior.close) > float(prior.open)
            soft = ((low <= soft_level and reversal and two_bear) if side == "LONG"
                    else (high >= soft_level and reversal and two_bull))
            tp = ((rsi >= 76 if side == "LONG" else rsi <= 24) and roe >= 5)
            reason, exit_price = None, close
            if emergency:
                reason = "Emergency SL"
                trigger = emergency_level
                exit_price = min(op, trigger) if side == "LONG" and op < trigger else max(op, trigger) if side == "SHORT" and op > trigger else trigger
                exit_price = fill_price(exit_price, "SELL" if side == "LONG" else "BUY")
            elif soft:
                reason = "Soft SL"
                trigger = soft_level
                exit_price = min(op, trigger) if side == "LONG" and op < trigger else max(op, trigger) if side == "SHORT" and op > trigger else trigger
                exit_price = fill_price(exit_price, "SELL" if side == "LONG" else "BUY")
            elif tp:
                reason = "TP"
                exit_price = fill_price(close, "SELL" if side == "LONG" else "BUY")
            if reason:
                gross = pnl(side, avg, exit_price, qty)
                fees = (pos["notional"] + exit_price * qty) * FEE
                net = gross - fees
                balance += net
                trades.append({"strategy":"A","side":side,"entry_time":pos["time"].isoformat(),
                    "exit_time":ts.isoformat(),"avg_entry":avg,"exit_price":exit_price,"qty":qty,
                    "gross_pnl_usdt":gross,"fees_usdt":fees,"net_pnl_usdt":net,"reason":reason,
                    "dca_used":pos["dca"],"margin_used_usdt":pos["margin"]})
                counts[reason] += 1
                pos, exited = None, True
            elif not pos["dca"]:
                dca = roe <= -25 and adx > 45 and (
                    (rsi > 20 and rsi > prev_rsi) if side == "LONG"
                    else (rsi < 80 and rsi < prev_rsi))
                if dca and balance - pos["margin"] >= DCA_MARGIN - 1e-9:
                    add_qty = DCA_MARGIN * LEVERAGE / close
                    new_qty = qty + add_qty
                    pos["avg"] = (avg * qty + close * add_qty) / new_qty
                    pos["qty"] = new_qty
                    pos["margin"] += DCA_MARGIN
                    pos["notional"] += close * add_qty
                    pos["dca"] = True
                    counts["DCA"] += 1
                elif dca:
                    counts["DCA skipped insufficient margin"] += 1
        if pos is None and not exited and balance > 0 and (go_long or go_short):
            side = "LONG" if go_long else "SHORT"
            qty = ENTRY_MARGIN * LEVERAGE / close
            pos = {"side":side,"time":ts,"avg":close,"qty":qty,"margin":ENTRY_MARGIN,
                   "notional":close*qty,"dca":False}
        if pos:
            mark = pnl(pos["side"], pos["avg"], close, pos["qty"])
            exit_fee_est = close * pos["qty"] * FEE
            equity = balance + mark - pos["notional"] * FEE - exit_fee_est
            curve.append({"timestamp_utc":ts.isoformat(),"strategy":"A","mark_price":close,
                "balance_usdt":balance,"unrealized_pnl_usdt":mark,"equity_usdt":equity,
                "drawdown_usdt":0.0,"drawdown_pct":0.0,"position_side":pos["side"],
                "position_margin_usdt":pos["margin"]})
        else:
            curve.append({"timestamp_utc":ts.isoformat(),"strategy":"A","mark_price":close,
                "balance_usdt":balance,"unrealized_pnl_usdt":0.0,"equity_usdt":balance,
                "drawdown_usdt":0.0,"drawdown_pct":0.0,"position_side":"","position_margin_usdt":0.0})
    if pos:
        row = d.iloc[-1]
        exit_price = fill_price(float(row.close), "SELL" if pos["side"] == "LONG" else "BUY")
        gross = pnl(pos["side"], pos["avg"], exit_price, pos["qty"])
        fees = (pos["notional"] + exit_price * pos["qty"]) * FEE
        net = gross - fees
        trades.append({"strategy":"A","side":pos["side"],"entry_time":pos["time"].isoformat(),
            "exit_time":row.open_time.isoformat(),"avg_entry":pos["avg"],"exit_price":exit_price,
            "qty":pos["qty"],"gross_pnl_usdt":gross,"fees_usdt":fees,"net_pnl_usdt":net,
            "reason":"End of test (marked/closed for ledger)","dca_used":pos["dca"],"margin_used_usdt":pos["margin"]})
        balance += net
    return trades, curve, counts, balance


def run_strategy_b(h1, test_start):
    """B: exact supplied Pine threshold crossings; next-open fills per default Pine strategy semantics."""
    d = add_b_indicators(h1).reset_index(drop=True)
    balance, pos, trades, curve = START_BALANCE, None, [], []
    for i, row in d.iterrows():
        ts = row.open_time
        if ts < test_start:
            continue
        op, close = float(row.open), float(row.close)
        prev_pb, pb = row.pb_prev, row.pb
        long_signal = pd.notna(prev_pb) and pd.notna(pb) and prev_pb < 0.2 and pb > 0.2
        short_signal = pd.notna(prev_pb) and pd.notna(pb) and prev_pb > 0.8 and pb < 0.8
        exit_signal = pd.notna(prev_pb) and pd.notna(pb) and (
            (prev_pb > 0.2 and pb < 0.2) or (prev_pb < 0.8 and pb > 0.8))
        # Signal from previous bar is filled at this bar open (default Pine behavior).
        if i > 0:
            prev = d.iloc[i-1]
            prev_ts = prev.open_time
            prev_prev_pb, prev_close_pb = prev.pb_prev, prev.pb
            prev_long = pd.notna(prev_prev_pb) and pd.notna(prev_close_pb) and prev_prev_pb < 0.2 and prev_close_pb > 0.2
            prev_short = pd.notna(prev_prev_pb) and pd.notna(prev_close_pb) and prev_prev_pb > 0.8 and prev_close_pb < 0.8
            prev_exit = pd.notna(prev_prev_pb) and pd.notna(prev_close_pb) and (
                (prev_prev_pb > 0.2 and prev_close_pb < 0.2) or (prev_prev_pb < 0.8 and prev_close_pb > 0.8))
            if pos and prev_exit:
                side, avg, qty = pos["side"], pos["avg"], pos["qty"]
                exit_price = fill_price(op, "SELL" if side == "LONG" else "BUY")
                gross = pnl(side, avg, exit_price, qty)
                fees = (pos["notional"] + exit_price * qty) * FEE
                net = gross - fees
                balance += net
                trades.append({"strategy":"B","side":side,"entry_time":pos["time"].isoformat(),
                    "exit_time":ts.isoformat(),"avg_entry":avg,"exit_price":exit_price,"qty":qty,
                    "gross_pnl_usdt":gross,"fees_usdt":fees,"net_pnl_usdt":net,"reason":"Pine exit",
                    "dca_used":False,"margin_used_usdt":ENTRY_MARGIN})
                pos = None
            # Opposing entry reverses the position by default in Pine strategy.entry.
            if prev_long or prev_short:
                target = "LONG" if prev_long else "SHORT"
                if pos and pos["side"] != target:
                    side, avg, qty = pos["side"], pos["avg"], pos["qty"]
                    exit_price = fill_price(op, "SELL" if side == "LONG" else "BUY")
                    gross = pnl(side, avg, exit_price, qty)
                    fees = (pos["notional"] + exit_price * qty) * FEE
                    net = gross - fees
                    balance += net
                    trades.append({"strategy":"B","side":side,"entry_time":pos["time"].isoformat(),
                        "exit_time":ts.isoformat(),"avg_entry":avg,"exit_price":exit_price,"qty":qty,
                        "gross_pnl_usdt":gross,"fees_usdt":fees,"net_pnl_usdt":net,"reason":"Reversal",
                        "dca_used":False,"margin_used_usdt":ENTRY_MARGIN})
                    pos = None
                if pos is None and balance > 0:
                    qty = ENTRY_MARGIN * LEVERAGE / op
                    pos = {"side":target,"time":ts,"avg":fill_price(op,"BUY" if target=="LONG" else "SELL"),
                            "qty":qty,"notional":op*qty}
        # At each H1 close, mark equity. A new signal at this close isn't filled until next open.
        mark = pnl(pos["side"], pos["avg"], close, pos["qty"]) if pos else 0.0
        fees_est = ((pos["notional"] + close * pos["qty"]) * FEE) if pos else 0.0
        curve.append({"timestamp_utc":row.close_time.isoformat(),"strategy":"B","mark_price":close,
            "balance_usdt":balance,"unrealized_pnl_usdt":mark,"equity_usdt":balance+mark-fees_est,
            "drawdown_usdt":0.0,"drawdown_pct":0.0,"position_side":pos["side"] if pos else "",
            "position_margin_usdt":ENTRY_MARGIN if pos else 0.0})
    if pos:
        row = d.iloc[-1]
        exit_price = fill_price(float(row.close), "SELL" if pos["side"] == "LONG" else "BUY")
        gross = pnl(pos["side"], pos["avg"], exit_price, pos["qty"])
        fees = (pos["notional"] + exit_price * pos["qty"]) * FEE
        net = gross - fees
        trades.append({"strategy":"B","side":pos["side"],"entry_time":pos["time"].isoformat(),
            "exit_time":row.close_time.isoformat(),"avg_entry":pos["avg"],"exit_price":exit_price,
            "qty":pos["qty"],"gross_pnl_usdt":gross,"fees_usdt":fees,"net_pnl_usdt":net,
            "reason":"End of test (marked/closed for ledger)","dca_used":False,"margin_used_usdt":ENTRY_MARGIN})
        balance += net
    return trades, curve, {}, balance


def metrics(name, trades, curve, final_balance):
    pnl_values = [float(t["net_pnl_usdt"]) for t in trades]
    wins = [x for x in pnl_values if x > 0]
    losses = [x for x in pnl_values if x < 0]
    profit_factor = sum(wins) / abs(sum(losses)) if losses else (math.inf if wins else None)
    equity_values = [float(x["equity_usdt"]) for x in curve]
    peak, max_dd, max_dd_pct = START_BALANCE, 0.0, 0.0
    for equity in equity_values:
        peak = max(peak, equity)
        dd = max(0.0, peak-equity)
        dd_pct = dd / peak * 100 if peak > 0 else 0.0
        max_dd, max_dd_pct = max(max_dd, dd), max(max_dd_pct, dd_pct)
    return {"strategy":name,"starting_balance_usdt":START_BALANCE,"ending_balance_usdt":final_balance,
        "net_profit_usdt":final_balance-START_BALANCE,"return_pct":(final_balance/START_BALANCE-1)*100,
        "trade_count_including_end_mark":len(trades),"winning_trade_count":len(wins),"losing_trade_count":len(losses),
        "win_rate_pct":len(wins)/len(pnl_values)*100 if pnl_values else 0.0,
        "profit_factor":None if profit_factor is None or not math.isfinite(profit_factor) else profit_factor,
        "profit_factor_unbounded":bool(math.isinf(profit_factor)),"average_trade_net_usdt":sum(pnl_values)/len(pnl_values) if pnl_values else 0,
        "fees_usdt":sum(float(t["fees_usdt"]) for t in trades),"max_drawdown_usdt":max_dd,
        "max_drawdown_pct":max_dd_pct,"dca_count":sum(1 for t in trades if t.get("dca_used")),
        "funding_modeled":False,"slippage_bps_per_side":SLIPPAGE_BPS}


def main():
    if DAYS != 180:
        raise ValueError("This comparison workflow is fixed to 180 days; set COMPARE_DAYS=180.")
    if START_BALANCE <= 0 or ENTRY_MARGIN <= 0 or DCA_MARGIN < 0 or LEVERAGE <= 0:
        raise ValueError("Balance/margin/leverage settings must be positive.")
    OUT.mkdir(parents=True, exist_ok=True)
    end = pd.Timestamp.now(tz="UTC").floor("15min")
    start = end - pd.Timedelta(days=DAYS)
    warm = start - pd.Timedelta(days=20)
    m15 = fetch_candles("15m", warm, end)
    h1 = fetch_candles("1H", warm, end)
    # Verify full test-window M15 coverage; do not publish partial results.
    test_m15 = m15[(m15.open_time >= start) & (m15.open_time < end)]
    expected = DAYS * 96
    if len(test_m15) < expected - 4:
        raise RuntimeError(f"Incomplete M15 coverage: got {len(test_m15)}, expected about {expected}.")
    gaps = test_m15.open_time.diff().dropna()
    if not gaps.eq(pd.Timedelta(minutes=15)).all():
        raise RuntimeError("M15 candles contain gaps or duplicate timestamps; aborting report.")
    # Strategy A operates on M15; B's Pine source is H1 and must be evaluated on H1.
    a_m15 = m15[(m15.open_time >= start) & (m15.open_time < end)].reset_index(drop=True)
    a_h1 = h1[h1.open_time < end].reset_index(drop=True)
    b_h1 = h1[(h1.open_time >= start - pd.Timedelta(days=20)) & (h1.open_time < end)].reset_index(drop=True)
    if len(a_h1) < 100 or len(b_h1) < 100:
        raise RuntimeError("Insufficient H1 warm-up coverage.")
    # Keep warm-up candles for indicators, but do not allow trades before test_start.
    trades_a, curve_a, counts_a, balance_a = run_strategy_a(m15, a_h1, start)
    trades_b, curve_b, counts_b, balance_b = run_strategy_b(b_h1, start)
    summary = {
        "status":"completed","symbol":INSTRUMENT,"exchange":"OKX swap historical candles",
        "period_days":DAYS,"start_utc":start.isoformat(),"end_utc":end.isoformat(),
        "starting_balance_usdt":START_BALANCE,"entry_margin_usdt":ENTRY_MARGIN,"dca_margin_usdt":DCA_MARGIN,
        "leverage":LEVERAGE,"fee_rate_per_side":FEE,"slippage_bps_per_side":SLIPPAGE_BPS,
        "funding_modeled":False,"maintenance_margin_or_liquidation_modeled":False,
        "strategy_A":metrics("A_M15_RSI_H1_ADX_DCA",trades_a,curve_a,balance_a),
        "strategy_B":metrics("B_H1_RSI_percent_b",trades_b,curve_b,balance_b),
        "notes":["A rules follow the current bot.py thresholds; A entry margin is fixed $50 and one DCA add is fixed $50.",
                 "B follows supplied Pine %b crossings; because Pine strategy has no sizing, B uses standardized $50 margin x 13 leverage.",
                 "B uses H1 as its Pine source contains no timeframe override. Pine default market entries/exits fill at next bar open.",
                 "Fees and slippage are estimated; funding, liquidation and maintenance-margin tiers are excluded.",
                 "B's RSI calculation is approximated using the repository's Wilder RSI and EMA initialization; verify parity against TradingView before treating results as final."]
    }
    all_trades = trades_a + trades_b
    for fname, rows in (("trades_A.csv",trades_a),("trades_B.csv",trades_b)):
        fields = sorted({k for r in rows for k in r}) if rows else ["strategy","side","entry_time","exit_time","net_pnl_usdt"]
        with (OUT/fname).open("w",newline="",encoding="utf-8-sig") as f:
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    for curve in (curve_a, curve_b):
        peak = START_BALANCE
        for point in curve:
            equity = float(point["equity_usdt"])
            peak = max(peak, equity)
            dd = max(0.0, peak - equity)
            point["drawdown_usdt"] = dd
            point["drawdown_pct"] = dd / peak * 100 if peak > 0 else 0.0
    curve_rows = curve_a + curve_b
    with (OUT/"equity_curve_m15.csv").open("w",newline="",encoding="utf-8-sig") as f:
        fields=["timestamp_utc","strategy","mark_price","balance_usdt","unrealized_pnl_usdt","equity_usdt","drawdown_usdt","drawdown_pct","position_side","position_margin_usdt"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(curve_rows)
    with (OUT/"comparison_summary.json").open("w",encoding="utf-8") as f:
        json.dump(summary,f,indent=2,ensure_ascii=False)
    with (OUT/"comparison_summary.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=["strategy","starting_balance_usdt","ending_balance_usdt","net_profit_usdt","return_pct","trade_count_including_end_mark","win_rate_pct","profit_factor","max_drawdown_usdt","max_drawdown_pct","fees_usdt","dca_count","funding_modeled","slippage_bps_per_side"])
        w.writeheader(); w.writerow(summary["strategy_A"]); w.writerow(summary["strategy_B"])
    (OUT/"README_RESULTS.md").write_text("# BTCUSDT A/B 180-day comparison\n\n" + json.dumps(summary,indent=2,ensure_ascii=False) + "\n",encoding="utf-8")
    print(json.dumps({"status":"completed","period_days":DAYS,"start_utc":summary["start_utc"],"end_utc":summary["end_utc"],"outputs":str(OUT),"strategy_A":summary["strategy_A"],"strategy_B":summary["strategy_B"]},indent=2))


if __name__ == "__main__":
    main()
