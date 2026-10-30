"""Fetch confirmed 1m/5m candles around observed stops, never fabricate fills."""
import csv,json,time
from pathlib import Path
from .okx_ohlcv import api_page,parse_ohlcv_row
from .intrabar_audit import inspect_stop

def collect(trace_path, output):
    trace=json.loads(Path(trace_path).read_text())
    stops=[e for e in trace.get("events",[]) if e.get("kind") in ("SOFT SL","EMERGENCY SL")]
    root=Path(output);root.mkdir(parents=True,exist_ok=True)
    evidence=[]
    for event in stops:
        t=int(event["candleTime"])
        for bar,step in (("1m",60000),("5m",300000)):
            try:
                response=api_page(bar,str(t+900000))
                if response.get("code")!="0":raise ValueError("OKX API failure")
                now=int(time.time()*1000)
                candles=[c for r in response["data"]
                         if (c:=parse_ohlcv_row(r,step,now)) is not None
                         and t<=c["open_time"]<t+900000]
                candles.sort(key=lambda r:r["open_time"])
                item=inspect_stop(event,candles,step)
                if item["verified"]:
                    filename=f'{t}-{bar}.csv'
                    with (root/filename).open("w",newline="") as f:
                        w=csv.writer(f);w.writerow(["open_time","open","high","low","close","volume","closed"])
                        for c in candles:
                            w.writerow([c["open_time"]]+[c[k] for k in ("open","high","low","close","volume")]+[1])
                    item["source_file"]=filename
            except Exception as exc:
                item=dict(verified=False,reason="UNAVAILABLE_OR_INVALID_INTRABAR_DATA",
                          expected_fill_price=event.get("price"),
                          actual_fill_price=None,fill_difference=None)
            item.update(candleTime=t,kind=event["kind"],bar=bar)
            evidence.append(item)
            time.sleep(.2)
    report=dict(stops_observed=len(stops),coverage=evidence,
                intrabar_data_verified=bool(stops) and all(x["verified"] for x in evidence),
                intrabar_execution_certified=False,full_core_parity_certified=False)
    (root/"intrabar-report.json").write_text(json.dumps(report,indent=2)+"\n")
    return report
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--trace",required=True);p.add_argument("--output",required=True)
    a=p.parse_args();print(json.dumps(collect(a.trace,a.output),indent=2))
