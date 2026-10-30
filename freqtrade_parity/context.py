"""Closed M15 indicator context with strict previous-closed-hour join; offline-only."""
from .indicators import indicator_series,prior_closed_h1_index

def enrich_closed_m15(m15,h1):
    m15=sorted((dict(r) for r in m15 if r["closed"]),key=lambda r:r["open_time"])
    h1=sorted((dict(r) for r in h1 if r["closed"]),key=lambda r:r["open_time"])
    if not m15:return []
    mi=indicator_series(m15)
    hi=indicator_series(h1)
    out=[]
    for i,c in enumerate(m15):
        point=mi[i]
        hour=prior_closed_h1_index(c["open_time"],h1)
        hp=hi[hour] if hour is not None else {}
        prior=mi[i-1] if i else {}
        previous=m15[i-1] if i else {}
        out.append({**c,"rsi":point["rsi"],"adx":point["adx"],
                    "previous_rsi":prior.get("rsi"),
                    "previous_open":previous.get("open"),"previous_close":previous.get("close"),
                    "h1_plus":hp.get("plus_di"),"h1_minus":hp.get("minus_di"),
                    "h1_adx":hp.get("adx"),
                    "h1_source_open_time":h1[hour]["open_time"] if hour is not None else None})
    return out
