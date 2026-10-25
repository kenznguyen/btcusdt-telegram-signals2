"""Static cross-language contract checks until Android unit tests are wired."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PARSER = ROOT / "android-app/app/src/main/java/com/kenznguyen/btclivealerts/analytics/BacktestAnalyticsReport.kt"


class AndroidReportContractTest(unittest.TestCase):
    def test_android_parser_declares_all_required_metrics(self):
        source = PARSER.read_text(encoding="utf-8")
        for key in ("net_profit_usdt", "win_rate_pct", "profit_factor",
                    "max_drawdown_pct", "total_fees_usdt"):
            with self.subTest(key=key):
                self.assertIn('metric("' + key + '")', source)

    def test_unverified_until_manual_parity_review(self):
        source = PARSER.read_text(encoding="utf-8")
        self.assertIn("verified = false", source)
        self.assertNotIn("createOrder", source)
        self.assertNotIn("StrategyEngine()", source)


if __name__ == "__main__":
    unittest.main()
