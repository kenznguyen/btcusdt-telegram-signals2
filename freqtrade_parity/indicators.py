"""Wilder RSI / DMI / ADX port matching StrategyEngine.kt seed and null behavior.

Input is an already ordered OHLCV sequence; no exchange I/O.
"""
def kotlin_rma(values, length):
    if length < 1: raise ValueError("length")
    out=[None]*len(values)
    valid=[i for i,x in enumerate(values) if x is not None]
    if len(valid)<length: return out
    first=valid[length-1]
    prev=sum(values[i] for i in valid[:length])/length
    out[first]=prev
    for i in range(first+1,len(values)):
        if values[i] is not None:
            prev=(prev*(length-1)+values[i])/length
        out[i]=prev
    return out

def prior_closed_h1_index(m15_open_time, h1):
    bucket=m15_open_time-m15_open_time%3600000
    found=None
    for i,h in enumerate(h1):
        if h["closed"] and h["open_time"]<bucket:
            found=i
    return found

def indicator_series(candles, rsi_length=14,dmi_length=14,adx_smoothing=14):
    candles=sorted((r for r in candles if r["closed"]),key=lambda r:r["open_time"])
    n=len(candles)
    if not n:return []
    delta=[None]+[candles[i]["close"]-candles[i-1]["close"] for i in range(1,n)]
    gain=[None if d is None else max(d,0.) for d in delta]
    loss=[None if d is None else max(-d,0.) for d in delta]
    ag=kotlin_rma(gain,rsi_length); al=kotlin_rma(loss,rsi_length)
    rsi=[]
    for g,l in zip(ag,al):
        if g is None or l is None:rsi.append(None)
        elif l==0:rsi.append(100. if g>0 else 50.)
        else:rsi.append(100.-100./(1.+g/l))
    tr=[]; plus=[]; minus=[]
    for i,c in enumerate(candles):
        if i==0:
            tr.append(c["high"]-c["low"]); plus.append(0.);minus.append(0.)
        else:
            prev=candles[i-1]
            tr.append(max(c["high"]-c["low"],abs(c["high"]-prev["close"]),abs(c["low"]-prev["close"])))
            up=c["high"]-prev["high"];down=prev["low"]-c["low"]
            plus.append(up if up>down and up>0 else 0.)
            minus.append(down if down>up and down>0 else 0.)
    atr=kotlin_rma(tr,dmi_length); sp=kotlin_rma(plus,dmi_length);sm=kotlin_rma(minus,dmi_length)
    pdi=[None if a is None or p is None or a==0 else 100.*p/a for a,p in zip(atr,sp)]
    mdi=[None if a is None or m is None or a==0 else 100.*m/a for a,m in zip(atr,sm)]
    dx=[None if p is None or m is None or p+m==0 else 100.*abs(p-m)/(p+m) for p,m in zip(pdi,mdi)]
    adx=kotlin_rma(dx,adx_smoothing)
    return [{"open_time":candles[i]["open_time"],"rsi":rsi[i],"adx":adx[i],
             "plus_di":pdi[i],"minus_di":mdi[i]} for i in range(n)]
