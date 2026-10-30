"""Emit Python replay trace with Kotlin StrategyTraceExporter schema."""
import argparse,json,os
from pathlib import Path
from .canonical_csv import read_csv,digest
from .core_strategy import replay

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--m15",required=True);p.add_argument("--h1",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    m15=read_csv(a.m15,900000);h1=read_csv(a.h1,3600000)
    _,events=replay(m15,h1)
    rows=[]
    for e in events:
        t=e["candleTime"];kind=e["kind"];side=e["side"]
        rows.append(dict(id=f"{side}:{t}",kind=kind,candleTime=t,side=side,price=e["price"],
                         confirmed_at_ms=t if kind=="EMERGENCY SL" else t+900000,
                         fees=e.get("fees"),net_pnl=e.get("netPnl")))
    result=dict(engine="python",dataset_sha256=digest(m15,h1),events=rows,
                source="quant_engine.core_strategy.replay",parity_verified=False)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n")
if __name__=="__main__":main()
