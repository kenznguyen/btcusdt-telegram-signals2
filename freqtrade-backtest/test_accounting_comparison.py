"""Regression tests for optional financial accounting trace comparison."""
import unittest
from compare_events import compare


def event(**updates):
    result = {
        "timestamp_ms": 900000, "symbol": "BTCUSDT", "kind": "TP",
        "side": "LONG", "price": 100.0, "quantity": 1.0,
        "avg_entry": 90.0, "margin": 50.0, "roe_pct": 10.0,
        "balance": 110.0, "net_pnl": 10.0, "fees": 0.2,
    }
    result.update(updates)
    return result


class AccountingComparisonTests(unittest.TestCase):
    def test_equal_accounting_passes(self):
        self.assertTrue(compare([event()], [event()])["passed"])

    def test_balance_difference_fails(self):
        report = compare([event()], [event(balance=109.0)])
        self.assertIn("balance", [item["field"] for item in report["mismatches"]])

    def test_fees_difference_fails(self):
        report = compare([event()], [event(fees=0.3)])
        self.assertIn("fees", [item["field"] for item in report["mismatches"]])

    def test_missing_accounting_field_fails(self):
        right = event()
        del right["net_pnl"]
        report = compare([event()], [right])
        self.assertIn("net_pnl", [item["field"] for item in report["mismatches"]])

    def test_matching_null_fees_passes(self):
        self.assertTrue(compare([event(fees=None)], [event(fees=None)])["passed"])

    def test_invalid_nan_accounting_is_rejected(self):
        with self.assertRaises(ValueError):
            compare([event(balance=float("nan"))], [event()])


if __name__ == "__main__":
    unittest.main()
