"""Materialize adjacent fixed-size market windows without changing observed candles."""
import csv,json
from pathlib import Path
from .canonical_csv import read_csv,digest

def windows(source,output,span=600):
 source=Path(source);output=Path(output)
 m15=read_csv(source/"m15.csv",900000);h1=read_csv(source/"h1.csv",3600000)
 if len(m15)<2*span or len(h1)<180:raise ValueError("insufficient market history")
 result=[]
 for idx in range(2):
  m=m15[idx*span:(idx+1)*span]
  # Full confirmed H1 input is shared: each M15 only selects H1 candles strictly before its bucket.
  h=h1
  folder=output/f"window-{idx+1}";folder.mkdir(parents=True,exist_ok=True)
  for file,rows in (("m15.csv",m),("h1.csv",h)):
   with (folder/file).open("w",newline="") as f:
    writer=csv.writer(f);writer.writerow(["open_time","open","high","low","close","volume","closed"])
    for x in rows:writer.writerow([x["open_time"]]+[format(x[k],".17g") for k in ("open","high","low","close","volume")]+[1])
  meta=dict(window_id=idx+1,source="OKX_PUBLIC_HISTORY",dataset_sha256=digest(m,h),
            first_m15_ms=m[0]["open_time"],last_m15_ms=m[-1]["open_time"])
  (folder/"window-manifest.json").write_text(json.dumps(meta,indent=2)+"\n")
  result.append(meta)
 return result

if __name__=="__main__":
 import argparse
 p=argparse.ArgumentParser();p.add_argument("--input",default="parity-input");p.add_argument("--output",default="artifacts/market-windows")
 args=p.parse_args();print(json.dumps(windows(args.input,args.output),indent=2))
