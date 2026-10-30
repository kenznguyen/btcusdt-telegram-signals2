"""Strict reader for native Freqtrade backtest exports.

Native summary trade rows are NOT full ENTRY/DCA/SL callback traces. Refuse
certification until event-level executions with reliable fill provenance exist.
"""
import json
from pathlib import Path

def export_freqtrade_trade_trace(native_result_path,output_path,dataset_sha256):
    path=Path(native_result_path)
    if not path.is_file():
        raise ValueError("Native Freqtrade result missing")
    data=json.loads(path.read_text(encoding="utf-8"))
    strategies=data.get("strategy",{})
    trades=strategies.get("ChartProParityDryRun",{}).get("trades",[])
    if not isinstance(trades,list) or not trades:
        raise ValueError("No native trades; disabled ENTRY is not parity")
    required=("trade_id","event_kind","candleTime","actual_fill_price",
              "filled_at_ms","source_order_id")
    if any(not isinstance(t,dict) or any(t.get(k) is None for k in required) for t in trades):
        raise ValueError("Native summary lacks event-level fill/confirmation provenance")
    # No output until independently authenticated runtime event provenance is wired.
    raise ValueError("Native event trace attestation not implemented; parity unverified")
