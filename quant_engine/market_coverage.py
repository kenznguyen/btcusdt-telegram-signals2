"""Combine real market window parity, keeping missing events visible."""
import json,sys
from pathlib import Path
from .trace_gate import audit
from .evidence_summary import REQUIRED

def aggregate(root):
 root=Path(root);datasets=[];counts={name:0 for name in REQUIRED};errors=[]
 for folder in sorted(root.glob("window-*")):
  try:
   k=json.loads((folder/"kotlin-trace.json").read_text())
   p=json.loads((folder/"python-trace.json").read_text())
   ok,why=audit(k,p)
   if not ok:errors.append(f"{folder.name}:{why}")
   if ok:
    for event in k["events"]:
     if event["kind"] in counts:counts[event["kind"]]+=1
   datasets.append(dict(window=folder.name,parity_verified=ok,reason=why,
                        dataset_sha256=k.get("dataset_sha256")))
  except (OSError,ValueError,TypeError) as error:
   errors.append(f"{folder.name}:MISSING_OR_INVALID_TRACE")
 if len(datasets)!=2:errors.append("MISSING_MARKET_WINDOWS")
 matched=not errors
 return dict(parity_verified=matched,reason="MATCH" if matched else "WINDOW_PARITY_FAILED",
             windows=datasets,
             coverage_matrix={name:dict(observed=count,matched=bool(matched and count))
                              for name,count in counts.items()},
             full_core_parity_certified=False,errors=errors)

def main(root):
 root=Path(root);root.mkdir(parents=True,exist_ok=True)
 report=aggregate(root)
 (root/"market-coverage-report.json").write_text(json.dumps(report,indent=2)+"\n")
 print(json.dumps(report,indent=2))
 return 0 if report["parity_verified"] else 1
if __name__=="__main__":sys.exit(main(sys.argv[1] if len(sys.argv)>1 else "artifacts/market-windows"))
