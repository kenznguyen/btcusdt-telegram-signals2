"""90-day historical candle backtest; deliberately does not read/write live state.json."""
import json
import os
from pathlib import Path

import pandas as pd
import requests
import bot

STATUS = Path("backtest_status.json")
RESULT = Path("backtest_last_result.json")
FEE = float(os.getenv("TAKER_FEE_RATE", "0.0005"))
URL = "https://www.okx.com/api/v5/market/history-candles"


def _status(value, **extra):
    STATUS.write_text(json.dumps({"status": value, **extra}, indent=2), encoding="utf-8")


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
        for i, row in m15.iterrows():
            if i == 0 or pd.isna(row["rsi"]) or pd.isna(row["adx"]):
                continue
            ts = row["open_time"]
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
                    # TP moves in the profitable direction, unlike stop-loss thresholds.
                    target_move = bot.TP_ROE / (100.0 * bot.LEVERAGE)
                    exit_price = avg * (1.0 + target_move) if side == "LONG" else avg * (1.0 - target_move)
                    reason = "TP"
                if reason:
                    gross = ((exit_price-avg) if side=="LONG" else (avg-exit_price))*qty
                    fees = (pos["notional"] + abs(exit_price*qty))*FEE
                    net = gross-fees
                    trades.append({"side":side,"entry_time":pos["time"].isoformat(),"exit_time":ts.isoformat(),
                        "avg_entry":avg,"exit_price":exit_price,"qty":qty,"gross_pnl":gross,
                        "fees":fees,"net_pnl":net,"reason":reason,"dca_used":pos["dca"]})
                    equity += net
                    peak = max(peak, equity)
                    max_dd = max(max_dd, peak-equity)
                    counts[reason] += 1
                    pos = None
                    continue
                if not pos["dca"]:
                    dca = roe <= bot.DCA_ROE and adx > bot.DCA_ADX
                    dca = dca and ((rsi > bot.LONG_DCA_RSI and rsi > prsi) if side=="LONG"
                                   else (rsi < bot.SHORT_DCA_RSI and rsi < prsi))
                    if dca:
                        add = bot.DCA_MARGIN*bot.LEVERAGE/close
                        new_qty = qty+add
                        pos["avg"] = (avg*qty+close*add)/new_qty
                        pos["qty"] = new_qty
                        pos["margin"] += bot.DCA_MARGIN
                        pos["dca"] = True
                        pos["notional"] += close*add
                        counts["DCA"] += 1
                continue

            if go_long or go_short:
                side = "LONG" if go_long else "SHORT"
                qty = bot.INITIAL_MARGIN*bot.LEVERAGE/close
                pos = {"side":side,"time":ts,"avg":close,"qty":qty,"margin":bot.INITIAL_MARGIN,
                       "dca":False,"notional":close*qty}

        if pos:
            row = m15.iloc[-1]
            side, avg, qty = pos["side"], pos["avg"], pos["qty"]
            exit_price = float(row["close"])
            gross = ((exit_price-avg) if side=="LONG" else (avg-exit_price))*qty
            fees = (pos["notional"]+abs(exit_price*qty))*FEE
            net = gross-fees
            trades.append({"side":side,"entry_time":pos["time"].isoformat(),"exit_time":row["open_time"].isoformat(),
                "avg_entry":avg,"exit_price":exit_price,"qty":qty,"gross_pnl":gross,"fees":fees,
                "net_pnl":net,"reason":"End of test","dca_used":pos["dca"]})
            equity += net

        wins = [t for t in trades if t["net_pnl"] > 0]
        losses = [t for t in trades if t["net_pnl"] <= 0]
        gp, gl = sum(t["net_pnl"] for t in wins), abs(sum(t["net_pnl"] for t in losses))
        pf = gp/gl if gl else (999.0 if gp else None)
        report = {"symbol":"BTCUSDT perpetual (OKX BTC-USDT-SWAP candles)",
          "timeframe":"M15 entry / closed H1 trend filter","period_days":days,
          "start":m15.iloc[0]["open_time"].isoformat(),"end":m15.iloc[-1]["open_time"].isoformat(),
          "candle_count":len(m15),"trade_count":len(trades),"win_rate_pct":len(wins)/len(trades)*100 if trades else 0,
          "net_profit_usdt":sum(t["net_pnl"] for t in trades),"gross_profit_usdt":gp,"gross_loss_usdt":gl,
          "profit_factor":pf,"max_drawdown_usdt":max_dd,"fees_usdt":sum(t["fees"] for t in trades),
          "dca_count":counts["DCA"],"tp_count":counts["TP"],"soft_sl_count":counts["Soft SL"],
          "emergency_sl_count":counts["Emergency SL"],"fee_rate_per_side":FEE,"trades":trades[-500:]}
        RESULT.write_text(json.dumps(report,indent=2),encoding="utf-8")
        _status("completed",started_at=started,finished_at=pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d %H:%M UTC"),
                message=f"Hoàn tất {days} ngày; {len(trades)} giao dịch.")
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
        "Mô phỏng OHLC với phí ước tính; không phải khớp lệnh thực tế."])
