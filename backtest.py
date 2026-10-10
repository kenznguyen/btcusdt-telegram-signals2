"""90-day historical candle backtest; deliberately does not read/write live state.json."""
import csv
import json
import os
from pathlib import Path

import pandas as pd
import requests
import bot

STATUS = Path("backtest_status.json")
RESULT = Path("backtest_last_result.json")
TRADES_CSV = Path("backtest_trades.csv")
EQUITY_CSV = Path("backtest_equity.csv")
FEE = float(os.getenv("TAKER_FEE_RATE", "0.0005"))
URL = "https://www.okx.com/api/v5/market/history-candles"


def _status(value, **extra):
    STATUS.write_text(json.dumps({"status": value, **extra}, indent=2), encoding="utf-8")


def get_backtest_status():
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
                if title.strip().lower() in ("telegram command backtest", "telegram command: backtest"):
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
        params = {"instId": "BTC-USDT-SWAP", "bar": bar, "limit": "300"}
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


def _write_csv(path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_backtest(days=90):
    days = int(days)
    if not 1 <= days <= 365:
        raise ValueError("Số ngày phải từ 1 đến 365.")
    now = pd.Timestamp.now(tz="UTC")
    started = now.strftime("%Y-%m-%d %H:%M UTC")
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
        if len(m15) < 100 or len(h1) < 100:
            raise RuntimeError("Không đủ dữ liệu nến đã đóng.")

        pos, trades = None, []
        counts = {"DCA":0, "TP":0, "Soft SL":0, "Emergency SL":0}
        equity = peak = max_dd = 0.0
        equity_rows = []
        for i, row in m15.iterrows():
            if i == 0 or pd.isna(row["rsi"]) or pd.isna(row["adx"]):
                continue
            ts = row["open_time"]
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
                roe = bot.roe_for(side, avg, close) or 0.0
                # Track intrabar favorable/adverse excursion using OHLC extremes.
                if side == "LONG":
                    favorable = (high / avg - 1) * bot.LEVERAGE * 100
                    adverse = (low / avg - 1) * bot.LEVERAGE * 100
                else:
                    favorable = (avg / low - 1) * bot.LEVERAGE * 100 if low else 0.0
                    adverse = (avg / high - 1) * bot.LEVERAGE * 100 if high else 0.0
                pos["max_favorable_roe_pct"] = max(pos["max_favorable_roe_pct"], favorable)
                pos["max_adverse_roe_pct"] = min(pos["max_adverse_roe_pct"], adverse)

                unrealized = ((close-avg) if side=="LONG" else (avg-close))*qty
                estimated_fees = (pos["notional"] + abs(close*qty))*FEE
                mark_equity = equity + unrealized - estimated_fees
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
                    reason, exit_price = "Emergency SL", emergency_price
                elif soft:
                    reason, exit_price = "Soft SL", soft_price
                elif tp:
                    target_move = bot.TP_ROE / (100.0 * bot.LEVERAGE)
                    exit_price = avg * (1.0 + target_move) if side == "LONG" else avg * (1.0 - target_move)
                    reason = "TP"
                if reason:
                    gross = ((exit_price-avg) if side=="LONG" else (avg-exit_price))*qty
                    fees = (pos["notional"] + abs(exit_price*qty))*FEE
                    net = gross-fees
                    held = max(0.0, (ts - pos["time"]).total_seconds()/60)
                    trades.append({
                        "trade_id": len(trades)+1, "side":side,
                        "entry_time":pos["time"].isoformat(), "exit_time":ts.isoformat(),
                        "hold_minutes":round(held,2), "initial_entry_price":pos["initial_entry"],
                        "dca_time":pos["dca_time"].isoformat() if pos["dca_time"] is not None else "",
                        "dca_price":pos["dca_price"], "avg_entry":avg, "exit_price":exit_price,
                        "initial_qty":pos["initial_qty"], "dca_qty":pos["dca_qty"], "qty_total":qty,
                        "margin_used_usdt":pos["margin"], "leverage":bot.LEVERAGE,
                        "gross_pnl_usdt":gross, "entry_exit_fees_usdt":fees, "net_pnl_usdt":net,
                        "net_return_on_margin_pct":(net/pos["margin"]*100) if pos["margin"] else 0,
                        "roe_at_exit_pct":roe, "max_favorable_roe_pct":pos["max_favorable_roe_pct"],
                        "max_adverse_roe_pct":pos["max_adverse_roe_pct"],
                        "exit_reason":reason, "dca_used":bool(pos["dca"])
                    })
                    equity += net
                    peak = max(peak, equity)
                    max_dd = max(max_dd, peak-equity)
                    counts[reason] += 1
                    pos = None
                    equity_rows.append({"time":ts.isoformat(),"realized_equity_usdt":equity,
                                        "mark_to_market_equity_usdt":equity,"drawdown_usdt":max(0,peak-equity),
                                        "position_side":"","close_price":close})
                    continue
                if not pos["dca"]:
                    dca = roe <= bot.DCA_ROE and adx > bot.DCA_ADX
                    dca = dca and ((rsi > bot.LONG_DCA_RSI and rsi > prsi) if side=="LONG"
                                   else (rsi < bot.SHORT_DCA_RSI and rsi < prsi))
                    if dca:
                        add = bot.DCA_MARGIN*bot.LEVERAGE/close
                        pos["dca_time"] = ts
                        pos["dca_price"] = close
                        pos["dca_qty"] = add
                        new_qty = qty+add
                        pos["avg"] = (avg*qty+close*add)/new_qty
                        pos["qty"] = new_qty
                        pos["margin"] += bot.DCA_MARGIN
                        pos["dca"] = True
                        pos["notional"] += close*add
                        counts["DCA"] += 1
                equity_rows.append({"time":ts.isoformat(),"realized_equity_usdt":equity,
                                    "mark_to_market_equity_usdt":mark_equity,
                                    "drawdown_usdt":max(0,peak-mark_equity),
                                    "position_side":pos["side"] if pos else "",
                                    "close_price":close})
                continue

            if go_long or go_short:
                side = "LONG" if go_long else "SHORT"
                qty = bot.INITIAL_MARGIN*bot.LEVERAGE/close
                pos = {"side":side,"time":ts,"avg":close,"qty":qty,"margin":bot.INITIAL_MARGIN,
                       "dca":False,"notional":close*qty,"initial_entry":close,"initial_qty":qty,
                       "dca_time":None,"dca_price":"","dca_qty":0.0,
                       "max_favorable_roe_pct":0.0,"max_adverse_roe_pct":0.0}
            equity_rows.append({"time":ts.isoformat(),"realized_equity_usdt":equity,
                                "mark_to_market_equity_usdt":equity,
                                "drawdown_usdt":max(0,peak-equity),
                                "position_side":pos["side"] if pos else "",
                                "close_price":close})

        if pos:
            row = m15.iloc[-1]
            side, avg, qty = pos["side"], pos["avg"], pos["qty"]
            exit_price = float(row["close"])
            gross = ((exit_price-avg) if side=="LONG" else (avg-exit_price))*qty
            fees = (pos["notional"]+abs(exit_price*qty))*FEE
            net = gross-fees
            ts = row["open_time"]
            trades.append({
                "trade_id":len(trades)+1,"side":side,"entry_time":pos["time"].isoformat(),
                "exit_time":ts.isoformat(),"hold_minutes":max(0.0,(ts-pos["time"]).total_seconds()/60),
                "initial_entry_price":pos["initial_entry"],
                "dca_time":pos["dca_time"].isoformat() if pos["dca_time"] is not None else "",
                "dca_price":pos["dca_price"],"avg_entry":avg,"exit_price":exit_price,
                "initial_qty":pos["initial_qty"],"dca_qty":pos["dca_qty"],"qty_total":qty,
                "margin_used_usdt":pos["margin"],"leverage":bot.LEVERAGE,
                "gross_pnl_usdt":gross,"entry_exit_fees_usdt":fees,"net_pnl_usdt":net,
                "net_return_on_margin_pct":(net/pos["margin"]*100) if pos["margin"] else 0,
                "roe_at_exit_pct":bot.roe_for(side,avg,exit_price) or 0,
                "max_favorable_roe_pct":pos["max_favorable_roe_pct"],
                "max_adverse_roe_pct":pos["max_adverse_roe_pct"],
                "exit_reason":"End of test","dca_used":bool(pos["dca"])
            })
            equity += net
            equity_rows.append({"time":ts.isoformat(),"realized_equity_usdt":equity,
                                "mark_to_market_equity_usdt":equity,"drawdown_usdt":max(0,peak-equity),
                                "position_side":"","close_price":exit_price})

        trade_fields = ["trade_id","side","entry_time","exit_time","hold_minutes",
            "initial_entry_price","dca_time","dca_price","avg_entry","exit_price",
            "initial_qty","dca_qty","qty_total","margin_used_usdt","leverage",
            "gross_pnl_usdt","entry_exit_fees_usdt","net_pnl_usdt","net_return_on_margin_pct",
            "roe_at_exit_pct","max_favorable_roe_pct","max_adverse_roe_pct","exit_reason","dca_used"]
        _write_csv(TRADES_CSV, trades, trade_fields)
        _write_csv(EQUITY_CSV, equity_rows, ["time","realized_equity_usdt",
            "mark_to_market_equity_usdt","drawdown_usdt","position_side","close_price"])

        wins = [t for t in trades if t["net_pnl_usdt"] > 0]
        losses = [t for t in trades if t["net_pnl_usdt"] <= 0]
        gp, gl = sum(t["net_pnl_usdt"] for t in wins), abs(sum(t["net_pnl_usdt"] for t in losses))
        pf = gp/gl if gl else (999.0 if gp else None)
        report = {"symbol":"BTCUSDT perpetual (OKX BTC-USDT-SWAP candles)",
          "timeframe":"M15 entry / closed H1 trend filter","period_days":days,
          "start":m15.iloc[0]["open_time"].isoformat(),"end":m15.iloc[-1]["open_time"].isoformat(),
          "candle_count":len(m15),"trade_count":len(trades),
          "win_rate_pct":len(wins)/len(trades)*100 if trades else 0,
          "net_profit_usdt":sum(t["net_pnl_usdt"] for t in trades),
          "gross_profit_usdt":gp,"gross_loss_usdt":gl,"profit_factor":pf,
          "max_drawdown_usdt":max_dd,"fees_usdt":sum(t["entry_exit_fees_usdt"] for t in trades),
          "dca_count":counts["DCA"],"tp_count":counts["TP"],"soft_sl_count":counts["Soft SL"],
          "emergency_sl_count":counts["Emergency SL"],"fee_rate_per_side":FEE,
          "trades":trades,"trade_csv":str(TRADES_CSV),"equity_csv":str(EQUITY_CSV)}
        RESULT.write_text(json.dumps(report,indent=2),encoding="utf-8")
        _status("completed",started_at=started,finished_at=pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d %H:%M UTC"),
                message=f"Hoàn tất {days} ngày; {len(trades)} giao dịch. Đã xuất CSV chi tiết.")
        return report
    except Exception as exc:
        _status("failed",started_at=started,finished_at=pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d %H:%M UTC"),
                message=str(exc)[:300])
        raise


def format_report(r):
    pf = r.get("profit_factor")
    pf_text = "∞" if pf == 999.0 else (f"{pf:.2f}" if isinstance(pf,(int,float)) else "N/A")
    return "\n".join(["📊 BTCUSDT — BACKTEST",
        f"Khung: {r['timeframe']} | Giai đoạn: {r['period_days']} ngày",
        f"Nến: {r['candle_count']} | Giao dịch: {r['trade_count']}",
        f"Net Profit sau phí: {r['net_profit_usdt']:+.2f} USDT",
        f"Win Rate: {r['win_rate_pct']:.2f}%","Profit Factor: "+pf_text,
        f"Max Drawdown (mark-to-market, close-to-close): {r['max_drawdown_usdt']:.2f} USDT",
        f"Phí ước tính: {r['fees_usdt']:.2f} USDT ({r['fee_rate_per_side']*100:.03f}%/chiều)",
        f"DCA: {r['dca_count']} | TP: {r['tp_count']} | Soft SL: {r['soft_sl_count']} | Emergency SL: {r['emergency_sl_count']}",
        f"Khoảng thời gian: {r['start'][:16]} — {r['end'][:16]} UTC",
        "Chi tiết: backtest_trades.csv và backtest_equity.csv (GitHub Actions artifact).",
        "Mô phỏng OHLC với phí ước tính; không phải khớp lệnh thực tế."])
