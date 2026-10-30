"""Controlled scenarios with actual indicators and initial position, no mocked signals."""
import json,csv
from dataclasses import asdict
from pathlib import Path
from .core_strategy import Position,State,replay
from .canonical_csv import read_csv,digest

NAMES=("DCA","SOFT SL","EMERGENCY SL")
def candles(step, count, fn):
    out=[]
    for i in range(count):
        price=fn(i)
        out.append(dict(open_time=i*step,open=price,high=price+.15,low=price-.15,close=price,volume=10.,closed=True))
    return out

def write_csv(path, rows):
    with path.open("w",newline="") as f:
        w=csv.writer(f);w.writerow(["open_time","open","high","low","close","volume","closed"])
        for r in rows:w.writerow([r[k] for k in ("open_time","open","high","low","close","volume")]+[1])

def write_scenarios(root):
    root=Path(root)
    for name in NAMES:
        folder=root/name;folder.mkdir(parents=True,exist_ok=True)
        if name=="DCA":
            m=candles(900000,160,lambda i:110-.085*i if i<=154 else 110-.085*154+.22*(i-154))
            h=candles(3600000,45,lambda i:100.+.2*i)
            last=m[-1]["close"]
            avg=last/0.98
            initial=State(100.,Position("LONG",1.,avg,50.,0.,avg,0),m[157]["open_time"])
        elif name=="SOFT SL":
            m=candles(900000,160,lambda i:110.-.08*i)
            h=candles(3600000,45,lambda i:110.-.25*i)
            for i in (158,159):
                m[i]["open"]=m[i]["close"]+.1
                m[i]["high"]=m[i]["open"]+.15
            last=m[-1]["close"]
            avg=last/0.97
            initial=State(100.,Position("LONG",1.,avg,50.,0.,avg,0),m[158]["open_time"])
        else:
            m=candles(900000,160,lambda i:100.)
            h=candles(3600000,45,lambda i:100.)
            m[-1]["low"]=90.
            initial=State(100.,Position("LONG",1.,100.,50.,0.,100.,0),m[158]["open_time"])
        write_csv(folder/"m15.csv",m);write_csv(folder/"h1.csv",h)
        (folder/"initial-state.json").write_text(json.dumps({"balance":initial.balance,
            "lastProcessedOpenTime":initial.last_processed_open_time,
            "position":{"side":initial.position.side,"qty":initial.position.qty,
                "avgEntry":initial.position.avg_entry,"initialMargin":initial.position.initial_margin,
                "dcaMargin":initial.position.dca_margin,"entryNotional":initial.position.entry_notional,
                "entryTime":initial.position.entry_time,"dcaUsed":False}},indent=2)+"\n")

def replay_scenarios(root):
    output={}
    for name in NAMES:
        folder=Path(root)/name
        m=read_csv(folder/"m15.csv",900000);h=read_csv(folder/"h1.csv",3600000)
        j=json.loads((folder/"initial-state.json").read_text());p=j["position"]
        state=State(j["balance"],Position(p["side"],p["qty"],p["avgEntry"],p["initialMargin"],
            p["dcaMargin"],p["entryNotional"],p["entryTime"],p["dcaUsed"]),j["lastProcessedOpenTime"])
        final,events=replay(m,h,state)
        rows=[dict(id=f'{e["side"]}:{e["candleTime"]}',kind=e["kind"],candleTime=e["candleTime"],
                   side=e["side"],price=e["price"],
                   confirmed_at_ms=e["candleTime"] if e["kind"]=="EMERGENCY SL" else e["candleTime"]+900000,
                   fees=e.get("fees"),net_pnl=e.get("netPnl")) for e in events]
        trace=dict(engine="python",source="quant_engine.core_strategy.replay",dataset_sha256=digest(m,h),
                   data_class="CONTROLLED_SYNTHETIC",events=rows,parity_verified=False)
        (folder/"python-trace.json").write_text(json.dumps(trace,indent=2)+"\n")
        output[name]=dict(events=[e["kind"] for e in events],dca_used=bool(final.position and final.position.dca_used),
                          data_class="CONTROLLED_SYNTHETIC")
    return output

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--output",default="artifacts/core-scenarios");a=p.parse_args()
    write_scenarios(a.output)
    print(json.dumps(replay_scenarios(a.output),indent=2))
if __name__=="__main__":main()
