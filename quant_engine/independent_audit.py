"""Independent read-only audit of CORE artifacts. Never self-certifies automatically."""
import hashlib,json,sqlite3,sys
from pathlib import Path
from .canonical_csv import read_csv,digest
from .trace_gate import audit

def review(root):
 root=Path(root)
 failures=[]
 try:
  m15=read_csv(root/"m15.csv",900000);h1=read_csv(root/"h1.csv",3600000)
  k=json.loads((root/"kotlin-trace.json").read_text())
  p=json.loads((root/"python-trace.json").read_text())
  good,reason=audit(k,p)
  if not good:failures.append("PARITY_"+reason)
  sha=digest(m15,h1)
  if k.get("dataset_sha256")!=sha or p.get("dataset_sha256")!=sha:
   failures.append("DATASET_DIGEST_MISMATCH")
 except (OSError,ValueError,TypeError,KeyError) as e:
  failures.append("INCOMPLETE_EVIDENCE")
 kinds={e.get("kind") for e in k.get("events",[])} if not failures else set()
 for kind in ("LONG ENTRY","SHORT ENTRY","DCA","TAKE PROFIT","SOFT SL","EMERGENCY SL"):
  if kind not in kinds:failures.append("NOT_OBSERVED_"+kind.replace(" ","_"))
 # The independent audit additionally requires actual fill records and process
 # recovery reviews. Real M1/M5 data alone cannot prove exchange execution.
 failures.extend(["REAL_FILL_RECONCILIATION_NOT_CERTIFIED",
                  "INDEPENDENT_AUDITOR_SIGNOFF_REQUIRED"])
 return {"parity_verified":not any(x.startswith(("PARITY_","DATASET_","INCOMPLETE")) for x in failures),
         "full_core_parity_certified":False,"audit_status":"PENDING",
         "blockers":failures}

def main():
 root=Path(sys.argv[1] if len(sys.argv)>1 else "artifacts/history")
 result=review(root)
 (root/"independent-audit.json").write_text(json.dumps(result,indent=2)+"\n")
 print(json.dumps(result,indent=2))
 return 0 if result["parity_verified"] else 1
if __name__=="__main__":sys.exit(main())
