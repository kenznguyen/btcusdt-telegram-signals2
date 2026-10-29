import hashlib
import math

def kotlin_double(value):
    value=float(value)
    if not math.isfinite(value):
        raise ValueError("OHLCV must be finite")
    if value==0.0:
        return "-0.0" if math.copysign(1.0,value)<0 else "0.0"
    # Python repr has the same shortest-roundtrip numeric value as Java Double.toString
    # for typical market prices; formatting edge cases require cross-runtime golden tests.
    rendered=repr(value)
    return rendered.replace("e+", "E").replace("e-", "E-")

def canonical_rows(candles,label):
    closed=sorted((c for c in candles if c["closed"]),key=lambda c:c["open_time"])
    return "\n".join(",".join([label,str(int(c["open_time"])),
        *(kotlin_double(c[k]) for k in ("open","high","low","close","volume"))]) for c in closed)

def dataset_hash(m15,h1):
    payload=canonical_rows(m15,"15m")+"\n"+canonical_rows(h1,"1h")
    return "sha256:"+hashlib.sha256(payload.encode("utf-8")).hexdigest()

import struct

def canonical_bytes(m15,h1):
    output=bytearray(b"CHARTPRO-OHLCV-V2"+bytes([0]))
    for label,candles in ((b"M15",m15),(b"H1",h1)):
        output.extend(label+bytes([0]))
        rows=sorted((c for c in candles if c["closed"]),key=lambda c:c["open_time"])
        for row in rows:
            values=[float(row[k]) for k in ("open","high","low","close","volume")]
            if not all(math.isfinite(value) for value in values):
                raise ValueError("OHLCV must be finite")
            output.extend(struct.pack(">q5d",int(row["open_time"]),*values))
    return bytes(output)

def dataset_hash(m15,h1):
    return "sha256:"+hashlib.sha256(canonical_bytes(m15,h1)).hexdigest()
