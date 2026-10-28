"""Fail-closed Kotlin/Freqtrade parity on the same verified OHLCV; trade-level differences."""
import argparse
import csv
import json
from pathlib import Path
from common_dataset_parity import verify_manifest

FIVE = {"ENTRY","DCA","TP","SOFT_SL","EMERGENCY_SL"}
ALLOWED = FIVE | {"LIQUIDATION","OTHER_EXIT"}

def trades_from_events(events):
    ordered = sorted(events, key=lambda e: (int(e["timestamp_ms"]), e["type"] != "ENTRY"))
    trades, active = [], None
    for event in ordered:
        if event["type"] not in ALLOWED:
            raise ValueError("Unknown event type: " + event["type"])
        for field in ("timestamp_ms","side","type","price","quantity"):
            if field not in event:
                raise ValueError("Event missing " + field)
        if event["type"] == "ENTRY":
            if active is not None:
                raise ValueError("Overlapping positions unsupported")
            active = [event]
        elif event["type"] == "DCA":
            if active is None or active[0]["side"] != event["side"]:
                raise ValueError("DCA without same-side entry")
            active.append(event)
        else:
            if active is None:
                raise ValueError("Exit without entry")
            active.append(event)
            trades.append(active)
            active = None
    if active is not None:
        trades.append(active) # open position at end of export
    return trades

def pair_trade_events(android_events, freqtrade_events):
    if not android_events or not freqtrade_events:
        return {"parity_verified":False,"reason":"missing_or_empty_trace",
                "android_events":len(android_events),"freqtrade_events":len(freqtrade_events),
                "trades":[],"matched_trade_indices":[]}
    android = trades_from_events(android_events)
    freqtrade = trades_from_events(freqtrade_events)
    comparisons, matched = [], []
    for i in range(max(len(android),len(freqtrade))):
        a = android[i] if i < len(android) else []
        f = freqtrade[i] if i < len(freqtrade) else []
        differences = []
        if not a or not f:
            differences.append({"field":"trade_present","android":bool(a),"freqtrade":bool(f)})
        for j in range(max(len(a),len(f))):
            ea = a[j] if j < len(a) else None
            ef = f[j] if j < len(f) else None
            if ea is None or ef is None:
                differences.append({"event_index":j,"field":"event_present",
                                    "android":ea,"freqtrade":ef})
                continue
            for field in ("type","side","timestamp_ms","price","quantity"):
                av, fv = ea[field], ef[field]
                same = (abs(float(av)-float(fv)) <= (1e-8 if field=="price" else 1e-10)
                        if field in ("price","quantity") else str(av)==str(fv))
                if not same:
                    differences.append({"event_index":j,"field":field,
                                        "android":av,"freqtrade":fv,
                                        "difference":float(fv)-float(av) if field in ("timestamp_ms","price","quantity") else None})
        good = bool(a and f and not differences)
        if good: matched.append(i+1)
        comparisons.append({"trade_index":i+1,"android_side":a[0]["side"] if a else None,
                            "freqtrade_side":f[0]["side"] if f else None,
                            "android_event_count":len(a),"freqtrade_event_count":len(f),
                            "matched":good,"differences":differences})
    return {"parity_verified":bool(comparisons) and len(matched)==len(comparisons),
            "android_events":len(android_events),"freqtrade_events":len(freqtrade_events),
            "android_trade_count":len(android),"freqtrade_trade_count":len(freqtrade),
            "trades":comparisons,"matched_trade_indices":matched,
            "reason":"all_trade_events_match" if len(matched)==len(comparisons) and comparisons else "trade_event_discrepancies"}

def main():
    p=argparse.ArgumentParser()
    for name in ("ohlcv","android","freqtrade","output","csv"):
        p.add_argument("--"+name,required=name in ("ohlcv","output","csv"),type=Path)
    args=p.parse_args()
    report={"parity_verified":False,"reason":"missing_trace","trades":[],"matched_trade_indices":[]}
    try:
        report["shared_ohlcv_sha256"]=verify_manifest(args.ohlcv)
        if args.android and args.freqtrade and args.android.is_file() and args.freqtrade.is_file():
            result=pair_trade_events(json.loads(args.android.read_text()),
                                     json.loads(args.freqtrade.read_text()))
            report.update(result)
        else:
            report["trace_paths_present"]={"android":bool(args.android and args.android.is_file()),
                                          "freqtrade":bool(args.freqtrade and args.freqtrade.is_file())}
    except (ValueError,KeyError,TypeError,FileNotFoundError,json.JSONDecodeError) as e:
        report["parity_verified"]=False
        report["reason"]="invalid_trace_or_dataset: "+str(e)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.csv.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    with args.csv.open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=["trade_index","matched","android_side","freqtrade_side","android_event_count","freqtrade_event_count","differences_json"])
        writer.writeheader()
        for trade in report.get("trades",[]):
            writer.writerow({k:(json.dumps(trade["differences"],ensure_ascii=False) if k=="differences_json" else trade.get(k))
                for k in writer.fieldnames})
    print("parity_verified:",report["parity_verified"],"reason:",report.get("reason"))
    return 0 if report["parity_verified"] else 1

if __name__=="__main__":
    raise SystemExit(main())
