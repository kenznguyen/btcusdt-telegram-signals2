import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from parity_suite import compare_case


def event(kind="ENTRY", price=100.0):
    return {
        "timestamp_ms": 900000, "symbol": "BTCUSDT", "kind": kind,
        "side": "LONG", "price": price, "quantity": 6.5,
        "avg_entry": 100.0, "margin": 50.0, "roe_pct": 0.0,
        "balance": 100.0, "net_pnl": None, "fees": None,
    }


class ParitySuiteTest(unittest.TestCase):
    def test_identical_required_event_passes(self):
        self.assertTrue(compare_case("entry", [event()], [event()])["passed"])

    def test_empty_traces_never_pass(self):
        report = compare_case("entry", [], [])
        self.assertFalse(report["passed"])
        self.assertIn("empty_trace", [m["field"] for m in report["mismatches"]])

    def test_detects_price_discrepancy(self):
        report = compare_case("entry", [event()], [event(price=101.0)])
        self.assertFalse(report["passed"])
        self.assertIn("price", [m["field"] for m in report["mismatches"]])

    def test_wrong_event_kind_does_not_pass(self):
        report = compare_case("tp", [event()], [event()])
        self.assertFalse(report["passed"])
        self.assertIn("required_event_kind", [m["field"] for m in report["mismatches"]])

    def test_android_alias_normalizes_kind(self):
        self.assertTrue(compare_case("tp", [event("TAKE PROFIT")], [event("TP")])["passed"])

    def test_unequal_event_counts_fail(self):
        self.assertFalse(compare_case("entry", [event()], [event(), event()])["passed"])


if __name__ == "__main__":
    unittest.main()
