"""Fail closed if actual independent Kotlin and Python traces are absent or unequal."""
import json,sys
from pathlib import Path

KEYS=("id","kind","candleTime","side","price","confirmed_at_ms","fees","net_pnl")
def audit(k,p):
    if not isinstance(k,dict) or not isinstance(p,dict):return False,"MISSING_TRACE"
    if k.get("engine")!="kotlin" or p.get("engine")!="python":return False,"INVALID_PRODUCER"
    kd=k.get("dataset_sha256")
    if not isinstance(kd,str) or not kd.startswith("sha256:") or len(kd)!=71 or kd!=p.get("dataset_sha256"):return False,"DATASET_MISMATCH"
    a,b=k.get("events"),p.get("events")
    if not isinstance(a,list) or not isinstance(b,list):return False,"MISSING_EVENTS"
    # Both real runners may legitimately produce zero events. Compare datasets only
    # after runner exit status and independent provenance are checked by CI.
    if len(a)!=len(b):return False,"COUNT_MISMATCH"
    for i,(left,right) in enumerate(zip(a,b)):
        if not isinstance(left,dict) or not isinstance(right,dict):return False,f"INVALID_EVENT:{i}"
        if any(key not in left or key not in right for key in KEYS):return False,f"MISSING_FIELDS:{i}"
        for key in KEYS:
            x,y=left[key],right[key]
            if x is None or y is None:
                if x is not None or y is not None:return False,f"EVENT_MISMATCH:{i}:{key}"
            elif key in ("price","fees","net_pnl") and type(x) in (float,int) and type(y) in (float,int):
                if abs(x-y)>1e-7*max(1,abs(x),abs(y)):return False,f"EVENT_MISMATCH:{i}:{key}"
            elif x!=y:return False,f"EVENT_MISMATCH:{i}:{key}"
    return True,"MATCH"

def main(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    try:
        k=json.loads((root/"kotlin-trace.json").read_text())
        p=json.loads((root/"python-trace.json").read_text())
        ok,reason=audit(k,p)
    except (OSError,ValueError,TypeError) as e:
        ok,reason=False,"MISSING_OR_INVALID_TRACE"
    result={"parity_verified":ok,"reason":reason}
    (root/"parity-report.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))
    return 0 if ok else 1
if __name__=="__main__":sys.exit(main(sys.argv[1] if len(sys.argv)>1 else "artifacts/parity"))
