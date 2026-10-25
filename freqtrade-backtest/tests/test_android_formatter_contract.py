import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
FILE = ROOT / "android-app/app/src/main/java/com/kenznguyen/btclivealerts/analytics/AnalyticsSummaryFormatter.kt"


class AndroidFormatterContractTest(unittest.TestCase):
    def test_read_only_kpi_fields(self):
        text = FILE.read_text(encoding="utf-8")
        for field in ("netProfitUsdt", "winRatePct", "profitFactor",
                      "maxDrawdownPct", "totalFeesUsdt"):
            self.assertIn("report." + field, text)
        self.assertIn('"N/A"', text)

    def test_does_not_claim_verified_or_place_orders(self):
        text = FILE.read_text(encoding="utf-8")
        self.assertIn("Chưa xác minh", text)
        for forbidden in ("createOrder", "placeOrder", "StrategyEngine()"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
