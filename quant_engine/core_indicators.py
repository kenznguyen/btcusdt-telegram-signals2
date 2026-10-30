"""Wilder RSI, DMI and ADX from Android StrategyEngine.kt (PR #32).
Closed candles only. Fails on malformed OHLCV.
"""
def rma(values, length):
    if length < 1: raise ValueError("invalid length")
    out = [None] * len(values)
    valid = [i for i,v in enumerate(values) if v is not None]
    if len(valid) < length: return out
    first = valid[length-1]
    prev = sum(values[i] for i in valid[:length])/length
    out[first] = prev
    for i in range(first+1,len(values)):
        if values[i] is not None: prev = (prev*(length-1)+values[i])/length
        out[i] = prev
    return out

def indicator_series(candles, rsi_length=14, dmi_length=14, adx_smoothing=14):
    n = len(candles)
    if not n: return []
    delta = [None]+[candles[i]["close"]-candles[i-1]["close"] for i in range(1,n)]
    gain = [None if x is None else max(x,0.0) for x in delta]
    loss = [None if x is None else max(-x,0.0) for x in delta]
    ag, al = rma(gain,rsi_length),rma(loss,rsi_length)
    rsi = [None if g is None or l is None else
           (100.0 if g>0 else 50.0) if l==0 else 100.0-100.0/(1.0+g/l)
           for g,l in zip(ag,al)]
    tr=[]; pdm=[]; mdm=[]
    for i,c in enumerate(candles):
        if i==0:
            tr.append(c["high"]-c["low"]);pdm.append(0.0);mdm.append(0.0)
        else:
            p=candles[i-1]
            tr.append(max(c["high"]-c["low"],abs(c["high"]-p["close"]),abs(c["low"]-p["close"])))
            up=c["high"]-p["high"]; down=p["low"]-c["low"]
            pdm.append(up if up>down and up>0 else 0.0)
            mdm.append(down if down>up and down>0 else 0.0)
    atr,sp,sm = rma(tr,dmi_length),rma(pdm,dmi_length),rma(mdm,dmi_length)
    plus=[None if a is None or x is None or a==0 else 100*x/a for a,x in zip(atr,sp)]
    minus=[None if a is None or x is None or a==0 else 100*x/a for a,x in zip(atr,sm)]
    dx=[None if p is None or m is None or p+m==0 else 100*abs(p-m)/(p+m) for p,m in zip(plus,minus)]
    adx=rma(dx,adx_smoothing)
    return [dict(rsi=rsi[i],adx=adx[i],plus_di=plus[i],minus_di=minus[i]) for i in range(n)]
