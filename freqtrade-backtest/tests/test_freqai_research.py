"""FreqAI research guardrails and no future leak in independent validation."""
import ast
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from freqai_research_metrics import build_samples


class ResearchTest(unittest.TestCase):
    def test_config_is_keyless_and_research_only(self):
        conf = json.loads((ROOT / "config.freqai-research.json").read_text())
        self.assertTrue(conf["dry_run"])
        self.assertEqual("futures", conf["trading_mode"])
        self.assertEqual("okx", conf["exchange"]["name"])
        self.assertEqual("", conf["exchange"]["key"])
        self.assertEqual("", conf["exchange"]["secret"])
        self.assertEqual(["15m", "1h"], conf["freqai"]["feature_parameters"]["include_timeframes"])
        self.assertFalse(conf["freqai"]["data_split_parameters"]["shuffle"])

    def test_adapter_no_entry_or_exit_orders(self):
        path = ROOT / "strategies" / "BtcFreqaiResearch.py"
        tree = ast.parse(path.read_text())
        strategy = next(node for node in tree.body if isinstance(node, ast.ClassDef))
        for name in ("populate_entry_trend", "populate_exit_trend"):
            method = next(node for node in strategy.body if isinstance(node, ast.FunctionDef) and node.name == name)
            source = ast.get_source_segment(path.read_text(), method)
            self.assertIn('= 0', source)
        self.assertIn("RunMode.BACKTEST", path.read_text())
        self.assertIn("self.freqai.start", path.read_text())

    def test_closed_h1_and_forward_target(self):
        import pandas as pd
        dates15 = pd.date_range("2026-01-01", periods=220, freq="15min", tz="UTC")
        dates1h = pd.date_range("2026-01-01", periods=60, freq="1h", tz="UTC")
        m15 = pd.DataFrame({"date":dates15, "open":range(220),
                            "high":[float(i)+1 for i in range(220)],
                            "low":[float(i)+0.1 for i in range(220)],
                            "close":[float(i)+0.5 for i in range(220)],
                            "volume":[float(i)+100 for i in range(220)]})
        h1 = pd.DataFrame({"date":dates1h, "close":[float(i)+100 for i in range(60)],
                           "volume":[100.0]*60})
        original, features = build_samples(m15, h1)
        self.assertEqual(original.loc[0,"h1_close"], float(100))
        self.assertEqual(original.loc[3,"h1_close"], float(100))
        self.assertEqual(original.loc[4,"h1_close"], float(101))
        self.assertEqual(original.loc[0,"label_available"],
                         pd.Timestamp("2026-01-01 01:15", tz="UTC"))
        self.assertAlmostEqual(original.loc[40,"target"], (44.5/40.5)-1)
        self.assertIn("h1_distance", features)


if __name__ == "__main__":
    unittest.main()
