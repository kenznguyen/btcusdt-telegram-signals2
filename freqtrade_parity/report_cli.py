"""Report entry point: schema comparison is not proof of independent runtime origin."""
import argparse
import json
from pathlib import Path
from .reconciliation import reconcile_trace_envelopes

def generate_report(kotlin_path,freqtrade_path,output_path):
    output_path=Path(output_path)
    try:
        if not Path(kotlin_path).is_file() or not Path(freqtrade_path).is_file():
            report={"parity_verified":False,"reason":"MISSING_TRACE_FILE","trades":[]}
        else:
            kotlin=json.loads(Path(kotlin_path).read_text(encoding="utf-8"))
            freqtrade=json.loads(Path(freqtrade_path).read_text(encoding="utf-8"))
            hash_value=kotlin.get("dataset_sha256")
            comparison=reconcile_trace_envelopes(kotlin,freqtrade,hash_value)
            # No independent runtime attestation or input-byte checksum verification yet.
            report={**comparison,"parity_verified":False,"reason":
                    "UNVERIFIED_TRACE_ORIGIN" if comparison["reason"]=="MATCH" else comparison["reason"]}
    except (OSError,ValueError,TypeError,KeyError) as e:
        report={"parity_verified":False,"reason":"INVALID_TRACE_INPUT","trades":[]}
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    return bool(report["parity_verified"])

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--kotlin",required=True)
    parser.add_argument("--freqtrade",required=True)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    success=generate_report(args.kotlin,args.freqtrade,args.output)
    raise SystemExit(0 if success else 1)
