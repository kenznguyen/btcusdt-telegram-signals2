"""Finalize long-history artifacts without weakening parity or fabricating certification."""
import json
from pathlib import Path

def _read(path):
    try:
        data=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,ValueError) as exc:
        raise ValueError(f"Missing or invalid evidence: {path}") from exc
    if not isinstance(data,dict):
        raise ValueError(f"Invalid evidence object: {path}")
    return data

def finalize(root):
    root=Path(root)
    target=root/"parity-report.json"
    report=_read(target)
    independent=_read(root/"independent-audit.json")
    intrabar=_read(root/"intrabar"/"intrabar-report.json")
    report["full_core_parity_certified"]=False
    report["independent_audit_status"]=independent.get("audit_status","PENDING")
    report["independent_audit_blockers"]=independent.get("blockers",[])
    report["intrabar_data_verified"]=intrabar.get("intrabar_data_verified") is True
    report["intrabar_fill_verified"]=intrabar.get("intrabar_execution_certified") is True
    report["certification_blockers"]=list(dict.fromkeys(
        report.get("certification_blockers",[])+report["independent_audit_blockers"]))
    target.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report

if __name__=="__main__":
    import sys
    print(json.dumps(finalize(sys.argv[1] if len(sys.argv)>1 else "artifacts/history"),indent=2))
