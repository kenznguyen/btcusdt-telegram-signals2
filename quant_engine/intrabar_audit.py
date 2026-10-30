"""Stop intrabar diagnostics. Estimates only; never claim exchange fills."""
import csv,json,sys
from pathlib import Path

def inspect_stop(event, rows, step_ms):
    if event.get("kind") not in ("SOFT SL","EMERGENCY SL"):
        raise ValueError("not a stop")
    t=int(event["candleTime"])
    selected=[r for r in rows if t<=r["open_time"]<t+900000]
    expected=900000//step_ms
    if len(selected)!=expected or any(r["open_time"]!=t+i*step_ms for i,r in enumerate(selected)):
        return dict(verified=False,reason="MISSING_INTRABAR_CANDLES",
                    expected_fill_price=event.get("price"),actual_fill_price=None,fill_difference=None)
    side=event["side"]
    expected_fill=event.get("price")
    if expected_fill is None:raise ValueError("missing modeled fill")
    # Soft SL is only confirmed at M15 close. Emergency can breach intrabar,
    # but without actual order book/slippage no execution price is knowable.
    first=selected[0]["open"]
    worst=min(r["low"] for r in selected) if side=="LONG" else max(r["high"] for r in selected)
    return dict(verified=True,kind=event["kind"],timeframe_ms=step_ms,
                estimated_gap_open=first,intrabar_extreme=worst,
                expected_fill_price=expected_fill,actual_fill_price=None,
                fill_difference=None,execution_verified=False,
                reason="NO_EXCHANGE_FILL_JOURNAL")

def main():
    import argparse
    from .canonical_csv import read_csv
    p=argparse.ArgumentParser();p.add_argument("--trace",required=True)
    p.add_argument("--m1");p.add_argument("--m5");p.add_argument("--output",required=True)
    a=p.parse_args()
    events=json.loads(Path(a.trace).read_text()).get("events",[])
    output=[]
    for key,step in (("m1",60000),("m5",300000)):
        path=getattr(a,key)
        if not path:continue
        rows=read_csv(path,step)
        output.extend(inspect_stop(e,rows,step) for e in events if e.get("kind") in ("SOFT SL","EMERGENCY SL"))
    result=dict(intrabar_diagnostics=output,intrabar_execution_certified=False,
                full_core_parity_certified=False)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+"\n")
if __name__=="__main__":main()
