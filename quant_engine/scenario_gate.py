"""Audit three independent Kotlin/Python controlled branch traces."""
import json,sys
from pathlib import Path
from .trace_gate import audit

REQUIRED=("DCA","SOFT SL","EMERGENCY SL")
def main(root):
    root=Path(root)
    cases={}
    for name in REQUIRED:
        folder=root/name
        try:
            kotlin=json.loads((folder/"kotlin-trace.json").read_text())
            python=json.loads((folder/"python-trace.json").read_text())
            matched,reason=audit(kotlin,python)
            kinds=[e.get("kind") for e in kotlin.get("events",[])]
            expected=(kinds==[name] and [e.get("kind") for e in python.get("events",[])]==[name])
            passed=matched and expected
            if not expected:reason="REQUIRED_EVENT_NOT_OBSERVED"
        except (OSError,ValueError,TypeError) as error:
            passed=False;reason="MISSING_OR_INVALID_BRANCH_TRACE"
        cases[name]=dict(passed=passed,reason=reason,scenario_type="CONTROLLED_SYNTHETIC")
    report={"controlled_branch_parity_verified":all(v["passed"] for v in cases.values()),
            "cases":cases,"full_core_parity_certified":False,
            "remaining_evidence":"real market branch coverage and paper lifecycle verification"}
    root.mkdir(parents=True,exist_ok=True)
    (root/"scenario-parity-report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    return 0 if report["controlled_branch_parity_verified"] else 1
if __name__=="__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv)>1 else "artifacts/core-scenarios"))
