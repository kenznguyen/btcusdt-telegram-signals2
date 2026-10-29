import json
import tempfile
import unittest
from pathlib import Path
from freqtrade_parity.report_cli import generate_report

class ReportCliTest(unittest.TestCase):
    def test_missing_trace_creates_failed_report(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/"report.json"
            ok=generate_report(Path(directory)/"kotlin.json",Path(directory)/"freqtrade.json",out)
            self.assertFalse(ok)
            report=json.loads(out.read_text())
            self.assertFalse(report["parity_verified"])
            self.assertEqual("MISSING_TRACE_FILE",report["reason"])
    def test_unverified_input_is_not_certified(self):
        with tempfile.TemporaryDirectory() as directory:
            d=Path(directory)
            checksum="sha256:"+"a"*64
            events=[{"id":"p1","kind":"DCA","candleTime":900000,"price":100.,
                     "confirmed_at_ms":1800000}]
            for engine in ("kotlin","freqtrade"):
                (d/(engine+".json")).write_text(json.dumps(
                    {"engine":engine,"dataset_sha256":checksum,"events":events}))
            out=d/"report.json"
            self.assertFalse(generate_report(d/"kotlin.json",d/"freqtrade.json",out))
            self.assertEqual("UNVERIFIED_TRACE_ORIGIN",json.loads(out.read_text())["reason"])

if __name__=="__main__":
    unittest.main()
