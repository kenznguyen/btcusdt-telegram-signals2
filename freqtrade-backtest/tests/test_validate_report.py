import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from validate_report import validate_report


def sample():
    return {
        "schema_version": "1.0", "engine": "freqtrade", "symbol": "BTC/USDT:USDT",
        "timeframe": "15m", "period_days": 90, "strategy_commit": "test-commit",
        "verified": False, "metrics": {
            "net_profit_usdt": None, "win_rate_pct": None,
            "profit_factor": None, "max_drawdown_pct": None, "total_fees_usdt": None
        }, "trades": []
    }


class ReportValidationTest(unittest.TestCase):
    def test_unverified_empty_report(self):
        self.assertFalse(validate_report(sample())["verified"])

    def test_reject_invalid_period(self):
        report = sample()
        report["period_days"] = 91
        with self.assertRaises(ValueError):
            validate_report(report)

    def test_reject_nonfinite_metrics(self):
        report = sample()
        report["metrics"]["net_profit_usdt"] = float("nan")
        with self.assertRaises(ValueError):
            validate_report(report)

    def test_reject_missing_provenance(self):
        report = sample()
        report["strategy_commit"] = ""
        with self.assertRaises(ValueError):
            validate_report(report)


if __name__ == "__main__":
    unittest.main()
