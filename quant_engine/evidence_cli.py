"""Consolidate evidence while keeping observed parity and complete certification separate."""
import json,sys
from pathlib import Path
from .evidence_summary import summarize

def read(path):
    try:return json.loads(Path(path).read_text())
    except (OSError,ValueError,TypeError):return None

def main(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    market_path=root/"market-windows"/"market-coverage-report.json"
    market=read(market_path)
    if not market:
        market=read(root/"parity"/"parity-report.json")
    scenarios=read(root/"core-scenarios"/"scenario-parity-report.json")
    paper=read(root/"paper-dca-e2e-report.json")
    report=summarize(market,scenarios,paper)
    crash_results=[read(root/"crash-evidence"/stage/"result.json")
                   for stage in ("reservation","submit","confirmation")]
    crash_ok=all(isinstance(x,dict) and x.get("verified") is True and
                 x.get("exit_code")==47 and x.get("no_duplicate_reservation") is True
                 for x in crash_results)
    report["process_crash_recovery_verified"]=crash_ok
    report["crash_stages"]={stage:bool(x and x.get("verified")) for stage,x in
                           zip(("reservation","submit","confirmation"),crash_results)}
    if not crash_ok:report["certification_blockers"].append("PROCESS_CRASH_RECOVERY_NOT_VERIFIED")
    report["full_core_parity_certified"]=False
    # Make the primary parity report carry the same consolidated qualification.
    target=root/"core-evidence-report.json"
    target.write_text(json.dumps(report,indent=2)+"\n")
    primary=root/"parity"/"parity-report.json"
    primary.parent.mkdir(parents=True,exist_ok=True)
    original=read(primary) or {}
    original.update({key:report[key] for key in
        ("parity_verified","market_coverage_matrix","controlled_branch_parity_verified",
         "paper_dca_e2e_verified","process_crash_recovery_verified",
         "full_core_parity_certified","certification_blockers")})
    primary.write_text(json.dumps(original,indent=2)+"\n")
    print(target.read_text())
    return 0 if (report["parity_verified"] and
                 report["controlled_branch_parity_verified"] and
                 report["paper_dca_e2e_verified"] and crash_ok) else 1

if __name__=="__main__":sys.exit(main(sys.argv[1] if len(sys.argv)>1 else "artifacts"))
