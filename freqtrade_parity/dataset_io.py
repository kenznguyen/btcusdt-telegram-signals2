"""Strict shared closed-candle CSV input for offline parity, never exchange orders."""
import csv
import math
from pathlib import Path
from .dataset_hash import dataset_hash

def read_closed_csv(path,step_ms):
    rows=[]
    with Path(path).open(newline="",encoding="utf-8") as source:
        reader=csv.DictReader(source)
        if not {"open_time","open","high","low","close","volume","closed"}.issubset(reader.fieldnames or []):
            raise ValueError("Missing required columns")
        for row in reader:
            if str(row["closed"]).strip() not in ("1","true","True"):
                raise ValueError("Candle is not confirmed closed")
            time=int(row["open_time"])
            if time<0 or time%step_ms:raise ValueError("Unaligned candle")
            values={key:float(row[key]) for key in ("open","high","low","close","volume")}
            if not all(math.isfinite(v) for v in values.values()):raise ValueError("Non-finite OHLCV")
            rows.append({"open_time":time,**values,"closed":True})
    if not rows:raise ValueError("Empty dataset")
    times=[row["open_time"] for row in rows]
    if len(set(times))!=len(times) or any(b-a!=step_ms for a,b in zip(times,times[1:])):
        raise ValueError("Duplicate, unsorted or missing candle")
    return rows

def generate_manifest(m15_path,h1_path):
    m15=read_closed_csv(m15_path,900000)
    h1=read_closed_csv(h1_path,3600000)
    return {"format":"CHARTPRO-OHLCV-V2","dataset_sha256":dataset_hash(m15,h1),
            "m15_count":len(m15),"h1_count":len(h1),
            "m15_first_open_ms":m15[0]["open_time"],"m15_last_open_ms":m15[-1]["open_time"],
            "h1_first_open_ms":h1[0]["open_time"],"h1_last_open_ms":h1[-1]["open_time"]}
