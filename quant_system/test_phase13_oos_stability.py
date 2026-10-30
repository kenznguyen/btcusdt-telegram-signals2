"""Phase13 risk-stability tests: missing/tampered reports must fail closed."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from quant_system.phase13_oos_stability import inspect_stability, WINDOW

def sha(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

def setup(root):
    for sub in ("canonical", "paper", "native"):
        (root / sub).mkdir(exist_ok=True)
    canonical = root / "canonical/15m.csv"
    canonical.write_text("open_time,close,closed\n900000,40000,1\n", encoding="utf8")
    dataset_sha = "sha256:" + "1"*64
    detail_sha = "sha256:" + "2"*64
    (root / "paper/phase12-native-fit-label-audit.json").write_text(json.dumps({
        "actual_fit_sample_lineage_verified": True,
        "label_reconstruction_verified": True,
        "train_test_label_purge_verified": True,
        "errors": [],
        "canonical_m15_sha256": sha(canonical)
    }))
    (root / "native/native-research-180.json").write_text(json.dumps({
        "core_native_runtime_succeeded": True,
        "freqai_native_runtime_succeeded": True,
        "dataset_sha256": dataset_sha,
        "detail_sha256": detail_sha
    }))
    pins = {}
    for mode in ("core-only", "ai-only", "dual"):
        path = root / ("paper/portfolio-" + mode + "-equity.csv")
        with path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(("candle_close_ms", "equity_mtm_ex_funding_usdt"))
            for i in range(6 * WINDOW):
                writer.writerow((900000 * (i + 1), 100.0 + (i+1) * .001))
        end = 100.0 + (6 * WINDOW) * .001
        (root / ("paper/portfolio-" + mode + "-report.json")).write_text(
            json.dumps({
                "mode": mode.replace("-", "_").upper(),
                "dataset_sha256": dataset_sha,
                "detail_sha256": detail_sha,
                "starting_capital_usdt": 100.0,
                "freqai_oos_verified": False,
                "live_orders_enabled": False,
                "equity_mtm_ex_funding_usdt": end,
                "max_drawdown_ex_funding_usdt": 0.0
            }))
        report_path = root / ("paper/portfolio-" + mode + "-report.json")
        pins[path.name] = sha(path)
        pins[report_path.name] = sha(report_path)
    (root / "paper/portfolio-180-independent-audit.json").write_text(json.dumps({
        "paper_portfolio_integrity_verified": True,
        "errors": [],
        "artifact_sha256": pins
    }))

class Phase13StabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        setup(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_valid_retrospective_does_not_claim_independent_oos(self):
        outcome = inspect_stability(self.root)
        self.assertEqual(outcome["errors"], [])
        self.assertTrue(outcome["retrospective_stability_verified"])
        self.assertFalse(outcome["independent_oos_verified"])
        self.assertFalse(outcome["oos_certified"])
        self.assertFalse(outcome["ready_for_360"])
        self.assertEqual(outcome["modes"]["DUAL"]["negative_30d_segments"], 0)

    def test_tampered_canonical_sha_denied(self):
        (self.root / "canonical/15m.csv").write_text("altered")
        outcome = inspect_stability(self.root)
        self.assertIn("PHASE13_CANONICAL_SHA_MISMATCH", outcome["errors"])

    def test_missing_candle_denied(self):
        path = self.root / "paper/portfolio-dual-equity.csv"
        content = path.read_text().splitlines()
        path.write_text("\n".join(content[:300] + content[301:]) + "\n")
        outcome = inspect_stability(self.root)
        self.assertIn("PHASE13_PORTFOLIO_PHASE9_SHA_MISMATCH", outcome["errors"])

    def test_report_drawdown_forgery_denied(self):
        path = self.root / "paper/portfolio-ai-only-report.json"
        report = json.loads(path.read_text())
        report["max_drawdown_ex_funding_usdt"] = 1.0
        path.write_text(json.dumps(report))
        phase9_path = self.root / "paper/portfolio-180-independent-audit.json"
        phase9 = json.loads(phase9_path.read_text())
        phase9["artifact_sha256"][path.name] = sha(path)
        phase9_path.write_text(json.dumps(phase9))
        outcome = inspect_stability(self.root)
        self.assertIn("PHASE13_FULL_DRAWDOWN_MISMATCH", outcome["errors"])

    def test_model_development_history_can_never_self_certify_oos(self):
        for name in ("core-only", "ai-only", "dual"):
            p = self.root / ("paper/portfolio-" + name + "-report.json")
            report = json.loads(p.read_text())
            report["freqai_oos_verified"] = True
            p.write_text(json.dumps(report))
        outcome = inspect_stability(self.root)
        self.assertFalse(outcome["retrospective_stability_verified"])
        self.assertIn("PHASE13_PORTFOLIO_PHASE9_SHA_MISMATCH", outcome["errors"])

if __name__ == "__main__":
    unittest.main()
