import json
import tempfile
import unittest
from pathlib import Path
from freqtrade_parity.freqtrade_trace import export_freqtrade_trade_trace

class RuntimeTraceTest(unittest.TestCase):
    def test_rejects_absent_and_empty_native_trade_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"native.json";out=Path(tmp)/"out.json"
            with self.assertRaises(ValueError):
                export_freqtrade_trade_trace(p,out,"sha256:"+"a"*64)
            p.write_text(json.dumps({"strategy":{"ChartProParityDryRun":{"trades":[]}}}))
            with self.assertRaises(ValueError):
                export_freqtrade_trade_trace(p,out,"sha256:"+"a"*64)
            self.assertFalse(out.exists())
    def test_exported_trade_requires_actual_fill_and_event_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"native.json";out=Path(tmp)/"out.json"
            p.write_text(json.dumps({"strategy":{"ChartProParityDryRun":{"trades":[{
                "trade_id":"7","open_date":"2026-10-20 12:00:00+00:00",
                "open_rate":100.0,"exit_reason":"roi","close_rate":101.0
            }]}}}))
            with self.assertRaises(ValueError):
                export_freqtrade_trade_trace(p,out,"sha256:"+"a"*64)
            self.assertFalse(out.exists())

if __name__=="__main__":unittest.main()
