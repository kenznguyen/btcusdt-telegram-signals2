import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compare_events import compare


def event():
    return {"timestamp_ms": 1700000000000, "symbol": "BTCUSDT", "kind": "ENTRY",
            "side": "LONG", "price": 50000.0, "quantity": 0.013,
            "avg_entry": 50000.0, "margin": 50.0, "roe_pct": 0.0}


class CompareEventsTest(unittest.TestCase):
    def test_matching_trace(self):
        self.assertTrue(compare([event()], [dict(event())])["passed"])

    def test_detects_price_difference(self):
        other = event()
        other["price"] = 50001.0
        result = compare([event()], [other])
        self.assertFalse(result["passed"])
        self.assertEqual(result["mismatches"][0]["field"], "price")

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
