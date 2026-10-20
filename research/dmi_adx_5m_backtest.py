#!/usr/bin/env python3
"""Leakage-aware Binance BTCUSDT 5m DMI/ADX paper backtest. No order execution."""
from __future__ import annotations
import argparse, csv, json, math, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://api.binance.com/api/v3/klines"
INTERVAL_MS = 5 * 60 * 1000

def get_json(url: str):
    req = Request(url, headers={"User-Agent": "dmi-adx-paper-backtest/1.0"})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def fetch_klines(days: int):
    end = int(datetime.now(timezone.utc).timestamp() * 1000)
    end = end // INTERVAL_MS * INTERVAL_MS
    start = end - days * 24 * 60 * 60 * 1000
    rows, cursor = [], start
    while cursor < end:
        params = urlencode({"symbol":"BTCUSDT","interval":"5m","startTime":cursor,"endTime":end-1,"limit":1000})
        data = get_json(BASE + "?" + params)
        if not data:
            break
        rows.extend(data)
        last_open = int(data[-1][0])
        next_cursor = last_open + INTERVAL_MS
        if next_cursor <= cursor:
            raise RuntimeError("Binance pagination stalled; aborting rather than producing a partial report.")
        cursor = next_cursor
        if len(data) < 1000:
            break
        time.sleep(0.08)
    # Only candles whose close time has passed; dedupe by open time.
    dedup = {int(r[0]): r for r in rows if int(r[6]) < end}
    out = []
    for t in sorted(dedup):
        r = dedup[t]
        out.append({"open_time": int(r[0]), "open": float(r[1]), "high": float(r[2]),
                    "low": float(r[3]), "close": float(r[4]), "volume": float(r[5]),
                    "close_time": int(r[6])})
    expected = days * 24 * 12
    if len(out) < expected * 0.98:
        raise RuntimeError(f"Incomplete Binance data: got {len(out)} closed candles; expected about {expected}. No performance report generated.")
    return out

def wilder(values, period):
    out = [None] * len(values)
    if len(values) < period:
        return out
    first = [x for x in values[:period] if x is not None]
    if len(first) < period:
        return out
    prev = sum(first) / period
    out[period-1] = prev
    for i in range(period, len(values)):
        if values[i] is None:
            continue
        prev = ((prev * (period - 1)) + values[i]) / period
        out[i] = prev
    return out

def add_dmi(candles, period=14):
    n = len(candles)
    tr, plus_dm, minus_dm = [None]*n, [None]*n, [None]*n
    for i in range(1,n):
        cur, prev = candles[i], candles[i-1]
        up = cur["high"] - prev["high"]
        down = prev["low"] - cur["low"]
        plus_dm[i] = up if up > down and up > 0 else 0.0
        minus_dm[i] = down if down > up and down > 0 else 0.0
        tr[i] = max(cur["high"]-cur["low"], abs(cur["high"]-prev["close"]), abs(cur["low"]-prev["close"]))
    # Wilder averages seeded only after 14 valid observations (index 14).
    def wilder_from_index1(values):
        out = [None]*n
        if n <= period: return out
        seed = values[1:period+1]
        if any(v is None for v in seed): return out
        prev = sum(seed)/period
        out[period] = prev
        for j in range(period+1,n):
            prev = ((prev*(period-1)) + values[j])/period
            out[j] = prev
        return out
    atr, pavg, mavg = (wilder_from_index1(x) for x in (tr,plus_dm,minus_dm))
    pdi, mdi, dx = [None]*n, [None]*n, [None]*n
    for i in range(n):
        if atr[i] is None or atr[i] == 0 or pavg[i] is None or mavg[i] is None: continue
        pdi[i] = 100*pavg[i]/atr[i]; mdi[i] = 100*mavg[i]/atr[i]
        denom = pdi[i]+mdi[i]
        dx[i] = 100*abs(pdi[i]-mdi[i])/denom if denom else 0.0
    adx = [None]*n
    valid_dx = [i for i,x in enumerate(dx) if x is not None]
    if len(valid_dx) >= period:
        seed_idx = valid_dx[period-1]
        # Require consecutive DX values to avoid silently compressing missing bars.
        if valid_dx[:period] == list(range(seed_idx-period+1, seed_idx+1)):
            prev = sum(dx[j] for j in valid_dx[:period])/period
            adx[seed_idx] = prev
            for i in range(seed_idx+1,n):
                if dx[i] is not None:
                    prev = ((prev*(period-1))+dx[i])/period
                    adx[i] = prev
    return pdi, mdi, adx

def pct(x): return None if x is None else round(x*100, 4)

def evaluate(candles, pdi, mdi, adx, threshold, split):
    records = []
    for i in range(len(candles)-1):
        if pdi[i] is None or mdi[i] is None or adx[i] is None or adx[i] < threshold:
            continue
        pred = "UP" if pdi[i] > mdi[i] else ("DOWN" if mdi[i] > pdi[i] else "SKIP")
        if pred == "SKIP": continue
        delta = candles[i+1]["close"] - candles[i]["close"]
        actual = "UP" if delta > 0 else ("DOWN" if delta < 0 else "FLAT")
        correct = pred == actual
        split_name = "test_oos" if i >= split else "train"
        records.append({
            "signal_time_utc": datetime.fromtimestamp(candles[i]["close_time"]/1000,timezone.utc).isoformat(),
            "entry_reference_close": candles[i]["close"],
            "target_close_time_utc": datetime.fromtimestamp(candles[i+1]["close_time"]/1000,timezone.utc).isoformat(),
            "target_close": candles[i+1]["close"], "plus_di": round(pdi[i],6),
            "minus_di": round(mdi[i],6), "adx": round(adx[i],6), "threshold": threshold,
            "prediction": pred, "actual": actual, "correct": correct, "split": split_name,
            "return_pct_reference": round(delta/candles[i]["close"]*100,6),
        })
    return records

def metrics(rows):
    n=len(rows)
    if not n: return {"signals":0,"accuracy_including_flat_as_loss_pct":None,"directional_accuracy_excluding_flat_pct":None,"flat_outcomes":0}
    nonflat=[r for r in rows if r["actual"]!="FLAT"]
    wins=sum(r["correct"] for r in rows)
    nw=sum(r["correct"] for r in nonflat)
    return {"signals":n,"correct":wins,"accuracy_including_flat_as_loss_pct":round(100*wins/n,3),
            "directional_accuracy_excluding_flat_pct":round(100*nw/len(nonflat),3) if nonflat else None,
            "flat_outcomes":n-len(nonflat),"coverage_pct":None}

def payout_sensitivity(rows):
    # Net profit per losing stake = -1; on win = +net profit ratio; tie = 0 (push).
    out={}
    for ratio in (0.5,0.8,1.0):
        pnl=0.0
        for r in rows:
            if r["actual"]=="FLAT": continue
            pnl += ratio if r["correct"] else -1.0
        out[str(ratio)]={"assumed_net_profit_per_win_per_1_stake":ratio,
                         "paper_net_units_per_1_unit_each_signal":round(pnl,3),
                         "breakeven_accuracy_pct":round(100/(1+ratio),3),
                         "warning":"Illustrative only; not a Binance payout quote. Excludes contract-specific fees/taxes/slippage."}
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--days",type=int,default=180)
    ap.add_argument("--period",type=int,default=14)
    ap.add_argument("--thresholds",default="20,25,30")
    ap.add_argument("--out",default="dmi-adx-backtest-results")
    args=ap.parse_args()
    thresholds=[float(x.strip()) for x in args.thresholds.split(",")]
    outdir=Path(args.out); outdir.mkdir(parents=True,exist_ok=True)
    candles=fetch_klines(args.days)
    # Verify continuous 5m bars: no hidden missing intervals in target series.
    gaps=[i for i in range(1,len(candles)) if candles[i]["open_time"]-candles[i-1]["open_time"] != INTERVAL_MS]
    if gaps: raise RuntimeError(f"Detected {len(gaps)} missing 5m intervals. Refusing to score across a gapped series.")
    pdi,mdi,adx=add_dmi(candles,args.period)
    split=int(len(candles)*0.70)
    all_predictions=[]
    summary={"symbol":"BTCUSDT","source":"Binance Spot public klines API","interval":"5m",
             "requested_days":args.days,"actual_first_open_utc":datetime.fromtimestamp(candles[0]["open_time"]/1000,timezone.utc).isoformat(),
             "actual_last_closed_utc":datetime.fromtimestamp(candles[-1]["close_time"]/1000,timezone.utc).isoformat(),
             "candles":len(candles),"dmi_adx_period":args.period,"thresholds":thresholds,
             "split":{"method":"chronological 70% train / 30% untouched out-of-sample test",
                      "train_candles":split,"test_candles":len(candles)-split,
                      "note":"Thresholds are prespecified, not selected using the OOS results. Indicator at candle i predicts close-to-close move from close i to close i+1."},
             "leakage_controls":["Only closed candles are used","DMI/ADX at index i uses data no later than candle i","Prediction is scored against next candle close","Chronological split; no random shuffle","Gapped data aborts the run"],
             "costs":{"exchange_trading_fees":"Not applicable to directional forecast itself; no exchange order is simulated.",
                      "payout":"Unknown without the exact contract/product; sensitivity table is illustrative, not an actual Binance payout."},
             "results":{}}
    for th in thresholds:
        rows=evaluate(candles,pdi,mdi,adx,th,split)
        all_predictions.extend(rows)
        train=[r for r in rows if r["split"]=="train"]
        test=[r for r in rows if r["split"]=="test_oos"]
        summary["results"][str(th)]={"train":metrics(train),"test_oos":metrics(test),
            "test_oos_payout_sensitivity":payout_sensitivity(test),
            "interpretation":"Accuracy is not expected value unless actual payout, tie settlement and all costs are known."}
    with (outdir/"predictions.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(all_predictions[0].keys()) if all_predictions else ["signal_time_utc"])
        writer.writeheader(); writer.writerows(all_predictions)
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    lines=["# BTCUSDT DMI + ADX 5-minute paper backtest","",
      f"- Data source: Binance Spot public klines, BTCUSDT 5m",
      f"- Actual candles: {len(candles)}; requested period: {args.days} days",
      f"- Range: {summary['actual_first_open_utc']} through {summary['actual_last_closed_utc']}",
      f"- DMI/ADX period: {args.period}; thresholds: {', '.join(map(str,thresholds))}",
      "- Split: first 70% chronological train, last 30% untouched OOS",
      "- No orders placed. No exchange trading fees applied to forecast-only scoring.",
      "- Payout sensitivities assume net win profit ratios 0.5/0.8/1.0 per 1-unit stake; these are examples, not verified product terms.","",
      "| ADX threshold | Train signals | Train accuracy* | OOS signals | OOS accuracy* | OOS directional accuracy** |",
      "|---:|---:|---:|---:|---:|---:|"]
    for th in thresholds:
        r=summary["results"][str(th)]; tr=r["train"]; te=r["test_oos"]
        fmt=lambda x: "n/a" if x is None else f"{x:.3f}%"
        lines.append(f"| {th:g} | {tr['signals']} | {fmt(tr['accuracy_including_flat_as_loss_pct'])} | {te['signals']} | {fmt(te['accuracy_including_flat_as_loss_pct'])} | {fmt(te['directional_accuracy_excluding_flat_pct'])} |")
    lines += ["","* Flat outcomes count as incorrect in the primary accuracy column.",
              "** Directional accuracy excludes exact ties, which are reported separately.",
              "","## Leakage and limitations","",
              "Signals are generated from the completed candle's DMI/ADX and evaluated on the next 5-minute close. This tests a close-to-close forecast, not a tradable fill price. Exact 5-minute UP/DOWN products may use a different price oracle, boundary convention, payout and tie rule. No profitability claim should be made until the exact product settlement and payout are confirmed.",""]
    (outdir/"report.md").write_text("\n".join(lines),encoding="utf-8")
    print((outdir/"report.md").read_text(encoding="utf-8"))

if __name__=="__main__":
    main()
