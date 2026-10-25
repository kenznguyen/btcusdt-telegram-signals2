import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compare_events import compare


def event():
    return {"timestamp_ms": 1700000000000, "symbol": "BTCUSDT", "kind": "ENTRY",
            "side": "LONG", "price": 50000.0, "quantity": 0.013,
            "avg_entry": 50000.0, "margin": 50.0, "roe_pct": 0.0,
            "balance": 100.0, "net_pnl": None, "fees": None}


class CompareEventsTest(unittest.TestCase):
    def test_matching_trace(self):
        self.assertTrue(compare([event()], [dict(event())])["passed"])

    def test_detects_price_difference(self):
        other = event()
        other["price"] = 50001.0
        result = compare([event()], [other])
        self.assertFalse(result["passed"])
        self.assertEqual(result["mismatches"][0]["field"], "price")

    def test_android_take_profit_alias_matches_canonical_tp(self):
        android = event()
        android["kind"] = "TAKE PROFIT"
        canonical = event()
        canonical["kind"] = "TP"
        self.assertTrue(compare([android], [canonical])["passed"])

    def test_android_emergency_stop_alias_matches_canonical(self):
        android = event()
        android["kind"] = "EMERGENCY SL"
        canonical = event()
        canonical["kind"] = "EMERGENCY_SL"
        self.assertTrue(compare([android], [canonical])["passed"])

    def test_unknown_kind_is_rejected(self):
        invalid = event()
        invalid["kind"] = "SOMETHING_ELSE"
        with self.assertRaises(ValueError):
            compare([invalid], [event()])

    def test_detects_missing_event(self):
        self.assertFalse(compare([event()], [])["passed"])

    def test_detects_kind_difference(self):
        other = event()
        other["kind"] = "DCA"
        self.assertFalse(compare([event()], [other])["passed"])

    def test_rejects_missing_field(self):
        incomplete = event()
        del incomplete["margin"]
        with self.assertRaises(ValueError):
            compare([incomplete], [event()])


if __name__ == "__main__":
    unittest.main()
