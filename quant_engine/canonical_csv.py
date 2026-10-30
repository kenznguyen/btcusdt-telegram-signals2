"""Canonical CSV / Kotlin binary dataset SHA-256 compatibility."""
import csv, hashlib, math, struct
from pathlib import Path

def read_csv(path, step):
    with Path(path).open(newline="",encoding="utf-8") as f:
        reader=csv.DictReader(f)
        if reader.fieldnames != ["open_time","open","high","low","close","volume","closed"]:
            raise ValueError("CSV header mismatch")
        rows=[]
        for row in reader:
            if row["closed"].strip() not in ("1","true","True"): raise ValueError("unclosed candle")
            t=int(row["open_time"])
            if t<0 or t%step: raise ValueError("unaligned candle")
            vals={k:float(row[k]) for k in ("open","high","low","close","volume")}
            if not all(map(math.isfinite,vals.values())):raise ValueError("nonfinite candle")
            if vals["high"]<max(vals["open"],vals["close"],vals["low"]) or vals["low"]>min(vals["open"],vals["close"],vals["high"]) or vals["volume"]<0:raise ValueError("invalid OHLCV")
            rows.append(dict(open_time=t,**vals,closed=True))
    if not rows or any(b["open_time"]-a["open_time"]!=step for a,b in zip(rows,rows[1:])):raise ValueError("empty/unsorted/gapped candles")
    return rows

def digest(m15,h1):
    buf=bytearray(b"CHARTPRO-OHLCV-V2\0")
    for label,rows in ((b"M15",m15),(b"H1",h1)):
        buf.extend(label+b"\0")
        for c in rows:
            buf.extend(struct.pack(">q",c["open_time"]))
            for key in ("open","high","low","close","volume"):buf.extend(struct.pack(">d",c[key]))
    return "sha256:"+hashlib.sha256(buf).hexdigest()
