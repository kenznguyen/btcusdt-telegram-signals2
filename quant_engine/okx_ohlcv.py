"""Fetch observed, confirmed OKX BTC-USDT-SWAP candles. No synthetic fallback."""
import argparse,csv,json,math,os,time,urllib.parse,urllib.request
from pathlib import Path
from .canonical_csv import digest,read_csv

URL="https://www.okx.com/api/v5/market/history-candles"
FIELDS=("open","high","low","close","volume")

def parse_ohlcv_row(row, step_ms, now_ms):
    if len(row)<9: raise ValueError("truncated OHLCV response")
    if str(row[8])!="1": return None
    t=int(row[0])
    if t<0 or t%step_ms or t+step_ms>now_ms:raise ValueError("invalid confirmed timestamp")
    values=[float(row[i]) for i in (1,2,3,4,5)]
    if not all(math.isfinite(x) for x in values):raise ValueError("nonfinite candle")
    o,hi,lo,c,v=values
    if hi<max(o,c,lo) or lo>min(o,c,hi) or v<0 or min(o,c,hi,lo)<=0:
        raise ValueError("invalid OHLCV")
    return dict(open_time=t,open=o,high=hi,low=lo,close=c,volume=v,closed=True)

def api_page(bar,after):
    query={"instId":"BTC-USDT-SWAP","bar":bar,"limit":"100"}
    if after is not None:query["after"]=after
    req=urllib.request.Request(URL+"?"+urllib.parse.urlencode(query),
                               headers={"User-Agent":"ChartPro-Research-Parity/1.0"})
    with urllib.request.urlopen(req,timeout=25) as response:
        return json.load(response)

def fetch_closed(bar,step_ms,count,fetch_page=None,now_ms=None):
    if count<2:raise ValueError("insufficient requested bars")
    if now_ms is None:now_ms=int(time.time()*1000)
    if fetch_page is None:fetch_page=lambda after:api_page(bar,after)
    candles={};after=None
    for _ in range((count+99)//100+8):
        payload=fetch_page(after)
        if not isinstance(payload,dict) or payload.get("code")!="0" or not isinstance(payload.get("data"),list):
            raise ValueError("OKX_API_FAILURE")
        raw=payload["data"]
        if not raw:raise ValueError("OKX_EMPTY_PAGE")
        seen=[]
        for row in raw:
            c=parse_ohlcv_row(row,step_ms,now_ms)
            if c is None:continue
            t=c["open_time"];seen.append(t)
            if t in candles and candles[t]!=c:raise ValueError("CONFLICTING_DUPLICATE_CANDLE")
            candles[t]=c
        if len(candles)>=count:break
        if not seen:raise ValueError("NO_CONFIRMED_CANDLES")
        next_after=str(min(seen))
        if after is not None and int(next_after)>=int(after):raise ValueError("PAGINATION_STALLED")
        after=next_after
    if len(candles)<count:raise ValueError("INSUFFICIENT_CANDLES")
    rows=sorted(candles.values(),key=lambda c:c["open_time"])[-count:]
    if any(b["open_time"]-a["open_time"]!=step_ms for a,b in zip(rows,rows[1:])):
        raise ValueError("GAPPED_CANDLES")
    return rows

def write_dataset(folder,m15,h1,requested_at_ms):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    def write(path,rows):
        with path.open("w",newline="",encoding="utf-8") as stream:
            writer=csv.writer(stream,lineterminator="\n")
            writer.writerow(["open_time",*FIELDS,"closed"])
            for c in rows:writer.writerow([c["open_time"],*(format(c[k],".17g") for k in FIELDS),1])
    write(folder/"m15.csv",m15);write(folder/"h1.csv",h1)
    check_m=read_csv(folder/"m15.csv",900000)
    check_h=read_csv(folder/"h1.csv",3600000)
    metadata=dict(source="OKX_PUBLIC_HISTORY",instrument="BTC-USDT-SWAP",requested_at_ms=requested_at_ms,
                  m15_count=len(m15),h1_count=len(h1),dataset_sha256=digest(check_m,check_h),
                  confirmed_only=True,m15_first_open_ms=m15[0]["open_time"],m15_last_open_ms=m15[-1]["open_time"],
                  h1_first_open_ms=h1[0]["open_time"],h1_last_open_ms=h1[-1]["open_time"])
    (folder/"manifest.json").write_text(json.dumps(metadata,indent=2)+"\n")
    return metadata

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="parity-input");p.add_argument("--m15-count",type=int,default=600)
    p.add_argument("--h1-count",type=int,default=180)
    a=p.parse_args();now=int(time.time()*1000)
    m=fetch_closed("15m",900000,a.m15_count,now_ms=now)
    h=fetch_closed("1H",3600000,a.h1_count,now_ms=now)
    print(json.dumps(write_dataset(a.output,m,h,now),sort_keys=True))
if __name__=="__main__":main()
