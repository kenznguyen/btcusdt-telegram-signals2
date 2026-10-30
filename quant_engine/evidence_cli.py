"""Read durable CI reports, always write consolidated evidence even if some missing."""
import json,sys
from pathlib import Path
from .evidence_summary import summarize
def read(path):
    try:return json.loads(Path(path).read_text())
    except (OSError,ValueError):return None
def main(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    report=summarize(read(root/"parity"/"parity-report.json"),
                     read(root/"core-scenarios"/"scenario-parity-report.json"),
                     read(root/"paper-dca-e2e-report.json"))
    target=root/"core-evidence-report.json"
    target.write_text(json.dumps(report,indent=2)+"\n")
    print(target.read_text())
    return 0 if (report["parity_verified"] and report["controlled_branch_parity_verified"] and
                 report["paper_dca_e2e_verified"]) else 1
if __name__=="__main__":sys.exit(main(sys.argv[1] if len(sys.argv)>1 else "artifacts"))
