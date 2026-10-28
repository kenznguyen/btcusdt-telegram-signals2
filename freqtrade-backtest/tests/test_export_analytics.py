import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from export_analytics import convert


class ExportTest(unittest.TestCase):
    def test_unverified_and_percent_conversion(self):
        raw = {"strategy": {"Sample": {"profit_total_abs": 12.5, "winrate": 0.5, "profit_factor": 1.2, "max_drawdown_account": 0.08}}}
        report = convert(raw, symbol="BTC/USDT:USDT", days=90, commit="abc123")
        self.assertFalse(report["verified"])
        self.assertEqual(report["metrics"]["win_rate_pct"], 50)
        self.assertEqual(report["metrics"]["max_drawdown_pct"], 8)

    def test_reject_multiple_strategies(self):
        with self.assertRaises(ValueError):
            convert({"strategy": {"A": {}, "B": {}}}, symbol="BTC/USDT:USDT", days=90, commit="abc")

    def test_unknown_metrics_are_not_fabricated(self):
        report = convert({"strategy": {"A": {}}}, symbol="BTC/USDT:USDT", days=90, commit="abc")
        self.assertIsNone(report["metrics"]["total_fees_usdt"])
        self.assertIsNone(report["metrics"]["net_profit_usdt"])


if __name__ == "__main__":
    unittest.main()
