"""Regression: audit artifacts must remain strict JSON after finalization."""
import json
import tempfile
import unittest
from pathlib import Path
from quant_engine.history_finalize import finalize


class HistoryFinalizeTests(unittest.TestCase):
    def test_preserves_parity_and_writes_parseable_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"parity-report.json").write_text(json.dumps({
                "parity_verified":True,"coverage_matrix":{"DCA":{"observed":2,"matched":True}},
                "full_core_parity_certified":False
            }))
            (root/"independent-audit.json").write_text(json.dumps({
                "audit_status":"PENDING","full_core_parity_certified":False,
                "blockers":["NOT_OBSERVED_EMERGENCY_SL"]
            }))
            (root/"intrabar").mkdir()
            (root/"intrabar"/"intrabar-report.json").write_text(json.dumps({
                "intrabar_data_verified":True,"intrabar_execution_certified":False
            }))
            finalize(root)
            raw=(root/"parity-report.json").read_text()
            result=json.loads(raw)
            self.assertTrue(result["parity_verified"])
            self.assertFalse(result["full_core_parity_certified"])
            self.assertEqual(result["independent_audit_status"],"PENDING")
            self.assertTrue(result["intrabar_data_verified"])
            self.assertFalse(result["intrabar_fill_verified"])
            self.assertFalse(raw.endswith("\\n"))

    def test_invalid_json_never_gets_silently_fixed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"parity-report.json").write_text('{"parity_verified":true}\\n')
            with self.assertRaises(ValueError):
                finalize(root)

    def test_missing_independent_evidence_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"parity-report.json").write_text('{"parity_verified":true}')
            with self.assertRaises((ValueError,FileNotFoundError)):
                finalize(root)


if __name__=="__main__":
    unittest.main()
