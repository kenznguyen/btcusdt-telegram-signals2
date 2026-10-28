import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common_dataset_parity import compare_events

class CommonDatasetParityTest(unittest.TestCase):
    def test_matching_events(self):
        e = [{"timestamp_ms": 1000, "side": "LONG", "type": "ENTRY", "price": 100.0}]
        self.assertTrue(compare_events(e, e)["all_events_match"])

    def test_missing_events_not_parity(self):
        e = [{"timestamp_ms": 1000, "side": "LONG", "type": "ENTRY", "price": 100.0}]
        self.assertFalse(compare_events(e, [])["all_events_match"])

    def test_price_mismatch_detected(self):
        a = [{"timestamp_ms": 1000, "side": "SHORT", "type": "SOFT_SL", "price": 102.0}]
        b = [{"timestamp_ms": 1000, "side": "SHORT", "type": "SOFT_SL", "price": 101.0}]
        self.assertEqual("price_disagreement", compare_events(a, b)["events"][0]["status"])

if __name__ == "__main__":
    unittest.main()
