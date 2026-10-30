"""Codemagic manual fail-closed trace audit. No trace fabrication."""
import json
import pathlib
import sys
from quant_engine.parity_gate import verify_bundle

def main(directory):
    root=pathlib.Path(directory)
    verdict={"parity_verified":False,"reason":"MISSING_TRACE_BUNDLE","compared_events":0}
    try:
        kotlin=json.loads((root/"kotlin-trace.json").read_text())
        python=json.loads((root/"python-trace.json").read_text())
        verdict=verify_bundle(kotlin,python)
    except (OSError,ValueError,TypeError) as exc:
        verdict["reason"]="MISSING_OR_INVALID_TRACE"
    root.mkdir(parents=True,exist_ok=True)
    (root/"parity-report.json").write_text(json.dumps(verdict,indent=2)+"\n")
    print(json.dumps(verdict))
    return 0 if verdict["parity_verified"] else 1

if __name__=="__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv)>1 else "artifacts/parity"))
