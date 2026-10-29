import hashlib
import math

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
