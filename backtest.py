"""90-day historical candle backtest; deliberately does not read/write live state.json."""
import csv
import json
import os
import uuid
from pathlib import Path

import pandas as pd
import requests
import bot

STATUS = Path("backtest_status.json")
RESULT = Path("backtest_last_result.json")
TRADES_CSV = Path("backtest_trades.csv")
EQUITY_CSV = Path("backtest_equity.csv")
CURVE_CSV = Path("backtest_equity_m15.csv")
FEE = float(os.getenv("TAKER_FEE_RATE", "0.0005"))
INITIAL_CAPITAL = float(os.getenv("BACKTEST_INITIAL_CAPITAL", "100"))
# Workflow/dashboard inputs use percentages (50, 100); legacy env values may use fractions (0.50, 1.00).
_entry_margin_raw = float(os.getenv("ENTRY_MARGIN_PCT", "0.50"))
ENTRY_MARGIN_PCT = _entry_margin_raw / 100.0 if _entry_margin_raw > 1.0 else _entry_margin_raw
_dca_margin_raw = float(os.getenv("DCA_MARGIN_RATIO", "1.00"))
DCA_MARGIN_RATIO = _dca_margin_raw / 100.0 if _dca_margin_raw > 5.0 else _dca_margin_raw
URL = "https://www.okx.com/api/v5/market/history-candles"
SYMBOL = os.getenv("BACKTEST_SYMBOL", "BTCUSDT").strip().upper()
OKX_INSTRUMENTS = {
    "BTCUSDT": "BTC-USDT-SWAP",
    "ETHUSDT": "ETH-USDT-SWAP",
    "SOLUSDT": "SOL-USDT-SWAP",
    "BNBUSDT": "BNB-USDT-SWAP",
    "XRPUSDT": "XRP-USDT-SWAP",
    "DOGEUSDT": "DOGE-USDT-SWAP",
    "ADAUSDT": "ADA-USDT-SWAP",
    "LINKUSDT": "LINK-USDT-SWAP",
}
if SYMBOL not in OKX_INSTRUMENTS:
    raise ValueError(f"Symbol không được hỗ trợ: {SYMBOL}")
RUN_ID = os.getenv("BACKTEST_RUN_ID", "").strip() or uuid.uuid4().hex
GENERATED_AT_UTC = None


def _status(value, **extra):
    payload = {"status": value, "run_id": RUN_ID,
               "generated_at_utc": GENERATED_AT_UTC, **extra}
    STATUS.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def get_backtest_status():
    # Prefer live GitHub Actions status so this command can see a backtest running in another job.
    token = os.getenv("ACTIONS_GITHUB_TOKEN", "").strip()
    repository = os.getenv("GITHUB_REPOSITORY", "").strip()
    if token and repository:
        try:
            response = requests.get(
                f"https://api.github.com/repos/{repository}/actions/workflows/telegram-command.yml/runs",
                params={"status": "in_progress", "per_page": 100},
                headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}"},
                timeout=10,
            )
            response.raise_for_status()
            for run in response.json().get("workflow_runs", []):
                title = str(run.get("display_title") or run.get("name") or "")
                if title.strip().lower() == "telegram command: backtest":
                    return "\n".join([
                        "🧪 BACKTEST STATUS",
                        "Trạng thái: RUNNING",
                        f"Run ID: {run.get('id', 'N/A')}",
                        f"Bắt đầu: {run.get('run_started_at', 'N/A')}",
                        f"Chi tiết: {run.get('html_url', '')}",
                    ])
        except Exception as exc:
            print(f"Could not query live GitHub Actions status: {exc}")
    try:
        s = json.loads(STATUS.read_text(encoding="utf-8"))
        return "\n".join(["🧪 BACKTEST STATUS", f"Trạng thái: {s.get('status')}",
                           f"Bắt đầu: {s.get('started_at', 'N/A')}",
                           f"Kết thúc: {s.get('finished_at', 'N/A')}",
                           f"Thông tin: {s.get('message', '')}"])
    except (OSError, ValueError):
        return "Chưa có trạng thái backtest. Gửi /backtest để chạy."


def get_last_report():
    try:
        return json.loads(RESULT.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _candles(bar, start_ms, end_ms, limit):
    rows, after = [], None
    while len(rows) < limit:
        params = {"instId": OKX_INSTRUMENTS[SYMBOL], "bar": bar, "limit": "300"}
        if after is not None:
            params["after"] = after
        r = requests.get(URL, params=params, timeout=30)
        r.raise_for_status()
        p = r.json()
        if p.get("code") != "0":
            raise RuntimeError("OKX candle API error: " + str(p.get("msg", "")))
        batch = p.get("data", [])
        if not batch:
            break
        rows.extend(x for x in batch if start_ms <= int(x[0]) < end_ms)
        oldest = int(batch[-1][0])
        if oldest <= start_ms or len(batch) < 2:
            break
        after = str(oldest)
    if not rows:
        raise RuntimeError("Không tải được nến lịch sử.")
    rows = sorted({str(x[0]): x for x in rows}.values(), key=lambda x: int(x[0]))
    df = pd.DataFrame(rows, columns=["open_time","open","high","low","close",
        "volume_contracts","volume","quote_volume","confirm"])
    for c in ("open","high","low","close","volume","quote_volume"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["open_time"] = pd.to_datetime(pd.to_numeric(df["open_time"]), unit="ms", utc=True)
    return df[df["confirm"].astype(str) == "1"].reset_index(drop=True)


def run_backtest(days=None):
    global RUN_ID, GENERATED_AT_UTC
    days = int(days if days is not None else os.getenv("BACKTEST_DAYS", "360"))
    if not 1 <= days <= 365:
        raise ValueError("Số ngày phải từ 1 đến 365.")
    if INITIAL_CAPITAL <= 0:
        raise ValueError("Vốn ban đầu phải lớn hơn 0.")
    if not 0 < ENTRY_MARGIN_PCT <= 1:
        raise ValueError("ENTRY_MARGIN_PCT phải nằm trong (0, 1], dạng tỷ lệ hoặc phần trăm.")
    if not 0 <= DCA_MARGIN_RATIO <= 5:
        raise ValueError("DCA_MARGIN_RATIO phải từ 0% đến 500%.")
    RUN_ID = os.getenv("BACKTEST_RUN_ID", "").strip() or uuid.uuid4().hex
    now = pd.Timestamp.now(tz="UTC")
    GENERATED_AT_UTC = now.isoformat()
    started = now.strftime("%Y-%m-%d %H:%M UTC")
    # Clear old outputs first so a failed run cannot publish stale results as current.
    for output in (RESULT, TRADES_CSV, EQUITY_CSV, CURVE_CSV):
        try:
            output.unlink()
        except FileNotFoundError:
            pass
    _status("running", started_at=started, message=f"Đang tải và mô phỏng {days} ngày.")
    try:
        start = now - pd.Timedelta(days=days)
        warm = start - pd.Timedelta(days=10)
        end_ms = int(now.timestamp() * 1000)
        m15 = _candles("15m", int(warm.timestamp()*1000), end_ms, days*96+1100)
        h1 = _candles("1H", int(warm.timestamp()*1000), end_ms, days*24+300)
        m15["close_time"] = m15["open_time"] + pd.Timedelta(minutes=15)
        h1["close_time"] = h1["open_time"] + pd.Timedelta(hours=1)
        m15 = bot.add_indicators(m15).reset_index(drop=True)
        h1 = bot.add_indicators(h1).reset_index(drop=True)
        m15 = m15[m15["open_time"] >= start].reset_index(drop=True)
        # M15 is trimmed to the requested test window, so a 1-day test has
        # at most 96 candles. Keep the minimum proportional for short smoke tests.
        min_m15 = min(100, max(30, int(days * 96 * 0.75)))
        if len(m15) < min_m15 or len(h1) < 100:
            raise RuntimeError(
                f"Không đủ dữ liệu nến đã đóng: M15={len(m15)} (cần >= {min_m15}), "
                f"H1={len(h1)} (cần >= 100), symbol={SYMBOL}, days={days}."
            )

        pos, trades = None, []
        counts = {"DCA":0, "TP":0, "Soft SL":0, "Emergency SL":0}
        balance = INITIAL_CAPITAL
        equity = 0.0  # cumulative realized net PnL, excluding initial capital
        peak = INITIAL_CAPITAL
        max_dd = 0.0  # close-to-close drawdown, retained for backward compatibility
        max_intrabar_dd = 0.0
        max_intrabar_dd_pct = 0.0
        max_intrabar_dd_details = None
        equity_curve = []
        max_dd_details = None
        peak_time_utc = m15.iloc[0]["open_time"].isoformat() if len(m15) else None

        def _refresh_last_equity(ts, mark_price):
            nonlocal peak, max_dd, max_dd_details, peak_time_utc
            side_now = pos["side"] if pos else ""
            unrealized_now = 0.0
            estimated_fees_now = 0.0
            if pos:
                unrealized_now = ((mark_price - pos["avg"]) if side_now == "LONG"
                                  else (pos["avg"] - mark_price)) * pos["qty"]
                estimated_fees_now = (pos["notional"] + abs(mark_price * pos["qty"])) * FEE
            mark_equity_now = balance + unrealized_now - estimated_fees_now
            if mark_equity_now > peak:
                peak = mark_equity_now
                peak_time_utc = ts.isoformat()
            drawdown_now = max(0.0, peak - mark_equity_now)
            drawdown_pct_now = drawdown_now / peak * 100.0 if peak > 0 else 0.0
            snapshot = {
                "run_id": RUN_ID, "generated_at_utc": GENERATED_AT_UTC,
                "timestamp_utc": ts.isoformat(), "mark_price": mark_price,
                "account_balance_usdt": balance, "unrealized_pnl_gross_usdt": unrealized_now,
                "estimated_entry_exit_fees_usdt": estimated_fees_now, "equity_usdt": mark_equity_now,
                "peak_equity_usdt": peak, "drawdown_usdt": drawdown_now, "drawdown_pct": drawdown_pct_now,
                "position_trade_id": pos.get("trade_id", "") if pos else "",
                "position_side": side_now, "position_entry_time_utc": pos["time"].isoformat() if pos else "",
                "avg_entry_price": pos["avg"] if pos else "", "position_qty": pos["qty"] if pos else "",
                "position_margin_usdt": pos["margin"] if pos else "", "dca_used": pos["dca"] if pos else False
            }
            if equity_curve and equity_curve[-1]["timestamp_utc"] == ts.isoformat():
                equity_curve[-1] = snapshot
            else:
                equity_curve.append(snapshot)
            if drawdown_now > max_dd:
                max_dd = drawdown_now
                max_dd_details = {**snapshot, "max_drawdown_usdt": drawdown_now,
                                  "peak_time_utc": peak_time_utc, "trough_time_utc": ts.isoformat()}

        for i, row in m15.iterrows():
            ts = row["open_time"]
            mark_price = float(row["close"])
            # Per-candle mark-to-market snapshot of the position carried into this candle.
            side_now = pos["side"] if pos else ""
            unrealized_now = 0.0
            estimated_fees_now = 0.0
            if pos:
                unrealized_now = ((mark_price - pos["avg"]) if side_now == "LONG" else (pos["avg"] - mark_price)) * pos["qty"]
                estimated_fees_now = (pos["notional"] + abs(mark_price * pos["qty"])) * FEE
            mark_equity_now = balance + unrealized_now - estimated_fees_now
            if mark_equity_now > peak:
                peak = mark_equity_now
                peak_time_utc = ts.isoformat()
            drawdown_now = max(0.0, peak - mark_equity_now)
            drawdown_pct_now = drawdown_now / peak * 100.0 if peak > 0 else 0.0
            equity_curve.append({
                "run_id": RUN_ID, "generated_at_utc": GENERATED_AT_UTC,
                "timestamp_utc": ts.isoformat(), "mark_price": mark_price,
                "account_balance_usdt": balance, "unrealized_pnl_gross_usdt": unrealized_now,
                "estimated_entry_exit_fees_usdt": estimated_fees_now, "equity_usdt": mark_equity_now,
                "peak_equity_usdt": peak, "drawdown_usdt": drawdown_now, "drawdown_pct": drawdown_pct_now,
                "position_trade_id": pos.get("trade_id", "") if pos else "",
                "position_side": side_now, "position_entry_time_utc": pos["time"].isoformat() if pos else "",
                "avg_entry_price": pos["avg"] if pos else "", "position_qty": pos["qty"] if pos else "",
                "position_margin_usdt": pos["margin"] if pos else "", "dca_used": pos["dca"] if pos else False
            })
            if drawdown_now > max_dd:
                max_dd = drawdown_now
                max_dd_details = {**equity_curve[-1], "max_drawdown_usdt": drawdown_now,
                                  "peak_time_utc": peak_time_utc, "trough_time_utc": ts.isoformat()}

            # Intrabar adverse equity estimate for the position carried into this candle.
            # OHLC cannot reveal whether the favorable or adverse extreme happened first;
            # this deliberately compares the adverse extreme with the previously observed equity peak.
            intrabar_adverse_price = None
            intrabar_equity = mark_equity_now
            if pos:
                intrabar_adverse_price = float(row["low"] if pos["side"] == "LONG" else row["high"])
                intrabar_unrealized = ((intrabar_adverse_price - pos["avg"]) if pos["side"] == "LONG"
                                       else (pos["avg"] - intrabar_adverse_price)) * pos["qty"]
                intrabar_fees = (pos["notional"] + abs(intrabar_adverse_price * pos["qty"])) * FEE
                intrabar_equity = balance + intrabar_unrealized - intrabar_fees
            intrabar_dd = max(0.0, peak - intrabar_equity)
            intrabar_dd_pct = intrabar_dd / peak * 100.0 if peak > 0 else 0.0
            equity_curve[-1]["intrabar_adverse_price"] = intrabar_adverse_price if pos else ""
            equity_curve[-1]["intrabar_adverse_equity_usdt"] = intrabar_equity
            equity_curve[-1]["intrabar_drawdown_usdt"] = intrabar_dd
            equity_curve[-1]["intrabar_drawdown_pct"] = intrabar_dd_pct
            if intrabar_dd > max_intrabar_dd:
                max_intrabar_dd = intrabar_dd
                max_intrabar_dd_pct = intrabar_dd_pct
                max_intrabar_dd_details = {
                    "timestamp_utc": ts.isoformat(),
                    "adverse_price": intrabar_adverse_price,
                    "adverse_equity_usdt": intrabar_equity,
                    "peak_equity_usdt": peak,
                    "drawdown_usdt": intrabar_dd,
                    "drawdown_pct": intrabar_dd_pct,
                    "position_side": pos["side"] if pos else "",
                    "position_trade_id": pos.get("trade_id", "") if pos else "",
                    "method": "OHLC adverse extreme vs observed equity peak; intrabar order unknown"
                }
            if i == 0 or pd.isna(row["rsi"]) or pd.isna(row["adx"]):
                continue
            # Match bot.py: latest H1 candle whose open is before this M15 hour.
            # This intentionally excludes the current forming H1 candle.
            candidates = h1[h1["open_time"] < ts.floor("h")]
            if candidates.empty:
                continue
            hr, prev = candidates.iloc[-1], m15.iloc[i-1]
            if any(pd.isna(x) for x in [hr["plus_di"],hr["minus_di"],hr["adx"],prev["rsi"]]):
                continue
            op, high, low, close = [float(row[k]) for k in ("open","high","low","close")]
            rsi, adx, prsi = float(row["rsi"]), float(row["adx"]), float(prev["rsi"])
            plus, minus, hadx = float(hr["plus_di"]), float(hr["minus_di"]), float(hr["adx"])
            bull = plus > minus and hadx > bot.H1_ADX_ENTRY
            bear = minus > plus and hadx > bot.H1_ADX_ENTRY
            go_long = bull and prsi <= bot.LONG_RSI_ENTRY and rsi > bot.LONG_RSI_ENTRY
            go_short = bear and prsi >= bot.SHORT_RSI_ENTRY and rsi < bot.SHORT_RSI_ENTRY

            if pos:
                side, avg, qty = pos["side"], pos["avg"], pos["qty"]
                margin = pos["margin"]
                # Match bot.py ROE semantics: price move multiplied by configured leverage.
                roe = bot.roe_for(side, avg, close) or 0.0
                # Close-to-close mark-to-market drawdown, including estimated entry + exit fees.
                unrealized = ((close-avg) if side=="LONG" else (avg-close))*qty
                estimated_fees = (pos["notional"] + abs(close*qty))*FEE
                mark_equity = balance + unrealized - estimated_fees
                peak = max(peak, mark_equity)
                max_dd = max(max_dd, peak-mark_equity)
                emergency_price = bot.threshold_price(side, avg, abs(bot.EMERGENCY_SL_ROE))
                soft_price = bot.threshold_price(side, avg, abs(bot.SOFT_SL_ROE))
                emergency = low <= emergency_price if side=="LONG" else high >= emergency_price
                reversal = (minus > plus if side=="LONG" else plus > minus) and hadx > bot.SOFT_SL_ADX
                two_bear = op > close and float(prev["close"]) < float(prev["open"])
                two_bull = close > op and float(prev["close"]) > float(prev["open"])
                soft = ((low <= soft_price and reversal and two_bear) if side=="LONG"
                        else (high >= soft_price and reversal and two_bull))
                tp = ((rsi >= bot.LONG_RSI_TP) if side=="LONG" else (rsi <= bot.SHORT_RSI_TP)) and roe >= bot.TP_ROE
                reason, exit_price = None, close
                if emergency:
                    reason, exit_price = "Emergency SL", bot.stop_fill_price(side, emergency_price, op)
                elif soft:
                    reason, exit_price = "Soft SL", bot.stop_fill_price(side, soft_price, op)
                elif tp:
                    # TP's RSI condition is known only after candle close; do not backfill at an earlier theoretical threshold.
                    # Match bot.py: simulate a market fill from the signal candle close with adverse slippage.
                    exit_price = bot.execution_fill_price(close, "SELL" if side == "LONG" else "BUY")
                    reason = "TP"
                if reason:
                    gross = ((exit_price-avg) if side=="LONG" else (avg-exit_price))*qty
                    fees = (pos["notional"] + abs(exit_price*qty))*FEE
                    net = gross-fees
                    trades.append({"side":side,"entry_time":pos["time"].isoformat(),"exit_time":ts.isoformat(),
                        "avg_entry":avg,"exit_price":exit_price,"qty":qty,"gross_pnl":gross,
                        "fees":fees,"net_pnl":net,"reason":reason,"dca_used":pos["dca"],
                        "initial_margin_usdt":pos["initial_margin"],
                        "dca_margin_usdt":pos["initial_margin"]*DCA_MARGIN_RATIO if pos["dca"] else 0.0})
                    equity += net
                    balance += net
                    peak = max(peak, balance)
                    max_dd = max(max_dd, peak-balance)
                    counts[reason] += 1
                    pos = None
                    _refresh_last_equity(ts, mark_price)
                    continue
                if not pos["dca"]:
                    dca = roe <= bot.DCA_ROE and adx > bot.DCA_ADX
                    dca = dca and ((rsi > bot.LONG_DCA_RSI and rsi > prsi) if side=="LONG"
                                   else (rsi < bot.SHORT_DCA_RSI and rsi < prsi))
                    if dca:
                        dca_margin = pos["initial_margin"] * DCA_MARGIN_RATIO
                        add = dca_margin*bot.LEVERAGE/close
                        new_qty = qty+add
                        pos["avg"] = (avg*qty+close*add)/new_qty
                        pos["qty"] = new_qty
                        pos["margin"] += dca_margin
                        pos["dca"] = True
                        pos["notional"] += close*add
                        counts["DCA"] += 1
                        _refresh_last_equity(ts, mark_price)
                continue

            if (go_long or go_short) and balance > 0:
                side = "LONG" if go_long else "SHORT"
                initial_margin = balance * ENTRY_MARGIN_PCT
                qty = initial_margin*bot.LEVERAGE/close
                pos = {"side":side,"time":ts,"avg":close,"qty":qty,"margin":initial_margin,
                       "initial_margin":initial_margin,"dca":False,"notional":close*qty,
                       "trade_id":len(trades)+1}
                _refresh_last_equity(ts, mark_price)

        if pos:
            row = m15.iloc[-1]
            side, avg, qty = pos["side"], pos["avg"], pos["qty"]
            exit_price = float(row["close"])
            gross = ((exit_price-avg) if side=="LONG" else (avg-exit_price))*qty
            fees = (pos["notional"]+abs(exit_price*qty))*FEE
            net = gross-fees
            trades.append({"side":side,"entry_time":pos["time"].isoformat(),"exit_time":row["open_time"].isoformat(),
                "avg_entry":avg,"exit_price":exit_price,"qty":qty,"gross_pnl":gross,"fees":fees,
                "net_pnl":net,"reason":"End of test","dca_used":pos["dca"],
                "initial_margin_usdt":pos["initial_margin"],
                "dca_margin_usdt":pos["initial_margin"]*DCA_MARGIN_RATIO if pos["dca"] else 0.0})
            equity += net
            balance += net
            peak = max(peak, balance)
            max_dd = max(max_dd, peak-balance)
            _refresh_last_equity(row["open_time"], exit_price)

        # KPI definitions are based on closed-trade net PnL after estimated fees.
        wins = [t for t in trades if float(t["net_pnl"]) > 0]
        losses = [t for t in trades if float(t["net_pnl"]) < 0]
        breakeven = [t for t in trades if float(t["net_pnl"]) == 0]
        net_profit = sum(float(t["net_pnl"]) for t in trades)
        winning_net_pnl = sum(float(t["net_pnl"]) for t in wins)
        losing_net_pnl = abs(sum(float(t["net_pnl"]) for t in losses))
        pf = winning_net_pnl / losing_net_pnl if losing_net_pnl > 0 else (float("inf") if winning_net_pnl > 0 else None)
        avg_win = winning_net_pnl / len(wins) if wins else 0.0
        avg_loss = -losing_net_pnl / len(losses) if losses else 0.0
        expectancy = net_profit / len(trades) if trades else 0.0
        return_pct = net_profit / INITIAL_CAPITAL * 100.0 if INITIAL_CAPITAL > 0 else 0.0
        curve_peak = max(equity_curve, key=lambda x: float(x["drawdown_usdt"])) if equity_curve else None
        curve_max_dd = float(curve_peak["drawdown_usdt"]) if curve_peak else 0.0
        curve_max_dd_pct = float(curve_peak["drawdown_pct"]) if curve_peak else 0.0
        reason_counts = {reason: sum(1 for t in trades if t["reason"] == reason)
                         for reason in ("TP", "Soft SL", "Emergency SL", "End of test")}
        # Export every trade and the realized cumulative PnL curve.
        trade_fields = ["run_id","generated_at_utc","trade_id","side","entry_time","exit_time","avg_entry","exit_price","qty",
            "gross_pnl","fees","net_pnl","reason","dca_used","initial_margin_usdt","dca_margin_usdt"]
        with TRADES_CSV.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=trade_fields, extrasaction="ignore")
            writer.writeheader()
            for idx, trade in enumerate(trades, 1):
                writer.writerow({"run_id":RUN_ID, "generated_at_utc":GENERATED_AT_UTC, "trade_id":idx, **trade})
        running_equity = 0.0
        running_balance = INITIAL_CAPITAL
        with EQUITY_CSV.open("w", newline="", encoding="utf-8-sig") as f:
            fields = ["run_id","generated_at_utc","trade_id","exit_time","side","exit_reason","trade_net_pnl_usdt","cumulative_net_pnl_usdt","account_balance_usdt","initial_margin_usdt","dca_margin_usdt"]
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for idx, trade in enumerate(trades, 1):
                running_equity += float(trade["net_pnl"])
                running_balance += float(trade["net_pnl"])
                writer.writerow({"run_id":RUN_ID,"generated_at_utc":GENERATED_AT_UTC,"trade_id":idx,"exit_time":trade["exit_time"],"side":trade["side"],
                    "exit_reason":trade["reason"],"trade_net_pnl_usdt":trade["net_pnl"],
                    "cumulative_net_pnl_usdt":running_equity,"account_balance_usdt":running_balance,
                    "initial_margin_usdt":trade.get("initial_margin_usdt"),"dca_margin_usdt":trade.get("dca_margin_usdt",0.0)})
        curve_fields = ["run_id","generated_at_utc","timestamp_utc","mark_price","account_balance_usdt","unrealized_pnl_gross_usdt",
            "estimated_entry_exit_fees_usdt","equity_usdt","peak_equity_usdt","drawdown_usdt","drawdown_pct",
            "intrabar_adverse_price","intrabar_adverse_equity_usdt","intrabar_drawdown_usdt","intrabar_drawdown_pct",
            "position_trade_id","position_side","position_entry_time_utc","avg_entry_price","position_qty",
            "position_margin_usdt","dca_used"]
        with CURVE_CSV.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=curve_fields)
            writer.writeheader()
            writer.writerows(equity_curve)

        report = {"run_id":RUN_ID,"generated_at_utc":GENERATED_AT_UTC,"status":"completed",
          "symbol":f"{SYMBOL} perpetual (OKX {OKX_INSTRUMENTS[SYMBOL]} candles)",
          "timeframe":"M15 entry / closed H1 trend filter","period_days":days,
          "start":m15.iloc[0]["open_time"].isoformat(),"end":m15.iloc[-1]["open_time"].isoformat(),
          "candle_count":len(m15),"trade_count":len(trades),"closed_trade_count":len(trades),
          "winning_trade_count":len(wins),"losing_trade_count":len(losses),"breakeven_trade_count":len(breakeven),
          "win_rate_pct":len(wins)/len(trades)*100 if trades else 0.0,
          "initial_capital_usdt":INITIAL_CAPITAL,"final_balance_usdt":INITIAL_CAPITAL+net_profit,
          "entry_margin_pct_of_current_balance":ENTRY_MARGIN_PCT,"dca_margin_ratio_of_initial_order":DCA_MARGIN_RATIO,
          "net_profit_usdt":net_profit,"return_pct":return_pct,
          "winning_net_pnl_usdt":winning_net_pnl,"losing_net_pnl_usdt":losing_net_pnl,
          # Legacy aliases retained for consumers of older reports; these are net PnL, not gross PnL.
          "gross_profit_usdt":winning_net_pnl,"gross_loss_usdt":losing_net_pnl,
          "profit_factor":pf,"average_win_usdt":avg_win,"average_loss_usdt":avg_loss,
          "expectancy_per_trade_usdt":expectancy,
          "max_drawdown_usdt":curve_max_dd,"max_drawdown_pct":curve_max_dd_pct,
          "max_drawdown_details":curve_peak,
          "max_drawdown_close_usdt":curve_max_dd,"max_drawdown_close_pct":curve_max_dd_pct,
          "max_intrabar_drawdown_usdt":max_intrabar_dd,
          "max_intrabar_drawdown_pct":max_intrabar_dd_pct,
          "max_intrabar_drawdown_details":max_intrabar_dd_details,
          "max_drawdown_method":"Close-to-close and conservative OHLC intrabar adverse estimate; intrabar high/low order is unknown",
          "equity_curve_candle_count":len(equity_curve),"fees_usdt":sum(float(t["fees"]) for t in trades),
          "dca_count":counts["DCA"],"tp_count":reason_counts["TP"],"soft_sl_count":reason_counts["Soft SL"],
          "emergency_sl_count":reason_counts["Emergency SL"],"end_of_test_close_count":reason_counts["End of test"],
          "fee_rate_per_side":FEE,"trades":trades,"trade_csv":str(TRADES_CSV),"equity_csv":str(EQUITY_CSV),
          "equity_curve_csv":str(CURVE_CSV)}
        finished = pd.Timestamp.now(tz="UTC")
        report["finished_at_utc"] = finished.isoformat()
        RESULT.write_text(json.dumps(report,indent=2),encoding="utf-8")
        _status("completed",started_at=started,finished_at=finished.strftime("%Y-%m-%d %H:%M UTC"),
                finished_at_utc=finished.isoformat(), message=f"Hoàn tất {days} ngày; {len(trades)} giao dịch.")
        return report
    except Exception as exc:
        finished = pd.Timestamp.now(tz="UTC")
        _status("failed",started_at=started,finished_at=finished.strftime("%Y-%m-%d %H:%M UTC"),
                finished_at_utc=finished.isoformat(), message=str(exc)[:300])
        RESULT.write_text(json.dumps({
            "run_id": RUN_ID, "generated_at_utc": GENERATED_AT_UTC,
            "status": "failed", "error": str(exc)[:300]
        }, indent=2), encoding="utf-8")
        raise


def format_report(r):
    pf = r.get("profit_factor")
    pf_text = ("∞" if pf is not None and isinstance(pf,(int,float)) and pf == float("inf")
               else f"{pf:.2f}" if isinstance(pf,(int,float)) else "N/A")
    return "\n".join([f"📊 {r.get('symbol', 'Perpetual')} — BACKTEST",
        f"Khung: {r['timeframe']} | Giai đoạn: {r['period_days']} ngày",
        f"Nến: {r['candle_count']} | Lệnh đóng: {r.get('closed_trade_count', r['trade_count'])}",
        f"Vốn đầu/cuối: {r.get('initial_capital_usdt',100):.2f} → {r.get('final_balance_usdt',100+r['net_profit_usdt']):.2f} USDT",
        f"Net Profit sau phí: {r['net_profit_usdt']:+.2f} USDT ({r.get('return_pct',0.0):+.2f}%)",
        f"Win Rate: {r['win_rate_pct']:.2f}% ({r.get('winning_trade_count',0)} thắng / {r.get('losing_trade_count',0)} thua / {r.get('breakeven_trade_count',0)} hòa)",
        "Profit Factor: "+pf_text+" (lãi ròng lệnh thắng / trị tuyệt đối lỗ ròng lệnh thua)",
        f"Expectancy/lệnh: {r.get('expectancy_per_trade_usdt',0.0):+.3f} USDT | TB thắng: {r.get('average_win_usdt',0.0):+.3f} | TB thua: {r.get('average_loss_usdt',0.0):+.3f}",
        f"Max DD (đóng nến): {r.get('max_drawdown_close_usdt', r['max_drawdown_usdt']):.2f} USDT ({r.get('max_drawdown_close_pct', r.get('max_drawdown_pct',0.0)):.2f}%)",
        f"Max DD (intrabar ước tính): {r.get('max_intrabar_drawdown_usdt', r['max_drawdown_usdt']):.2f} USDT ({r.get('max_intrabar_drawdown_pct', r.get('max_drawdown_pct',0.0)):.2f}%)",
        f"Phí ước tính: {r['fees_usdt']:.2f} USDT ({r['fee_rate_per_side']*100:.03f}%/chiều)",
        f"DCA: {r['dca_count']} | TP: {r['tp_count']} | Soft SL: {r['soft_sl_count']} | Emergency SL: {r['emergency_sl_count']} | Đóng cuối kỳ: {r.get('end_of_test_close_count',0)}",
        f"Khoảng thời gian: {r['start'][:16]} — {r['end'][:16]} UTC",
        "Mọi KPI PnL dùng net PnL sau phí ước tính; lệnh đóng cuối kỳ được tính vào tổng lệnh nhưng không thuộc TP/SL.",
        "Mô phỏng OHLC; không phải khớp lệnh thực tế."])

if __name__ == "__main__":
    # The runner is a standalone CLI as well as an importable module.
    # Without this guard Python exits successfully without producing a report.
    result = run_backtest()
    print(json.dumps({
        "symbol": SYMBOL,
        "status": result.get("status"),
        "period_days": result.get("period_days"),
        "trade_count": result.get("trade_count"),
        "net_profit_usdt": result.get("net_profit_usdt"),
        "result_file": str(RESULT),
    }, ensure_ascii=False), flush=True)
