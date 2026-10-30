"""CI parity artifact gate. Missing Kotlin/Freqtrade outputs must never pass."""
import json
from pathlib import Path
import sys
from freqtrade_parity.report_cli import generate_report

def main(root):
    root=Path(root)
    kotlin=root/"kotlin-trace.json"
    freqtrade=root/"freqtrade-trace.json"
    result=root/"parity-report.json"
    verified=generate_report(kotlin,freqtrade,result)
    print(result.read_text(encoding="utf-8"))
    return 0 if verified else 1

if __name__=="__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv)>1 else "artifacts/parity"))
