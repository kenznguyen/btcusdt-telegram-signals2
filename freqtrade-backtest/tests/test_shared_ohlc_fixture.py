"""Validate the shared Android/Python candle fixture without trading or network I/O."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from android_ohlc_replay import replay_ohlc


class SharedFixtureTests(unittest.TestCase):
    def test_python_replay_accepts_shared_fixture(self):
        fixture = json.loads((ROOT / "fixtures/android_python_ohlc_v1.json").read_text())
        self.assertEqual(1, fixture["schema_version"])
        state, events = replay_ohlc(
            fixture["candles_m15"], fixture["candles_h1"], symbol=fixture["symbol"])
        self.assertEqual(fixture["expected"]["event_count"], len(events))
        self.assertEqual(fixture["expected"]["final_balance"], state.balance)
        self.assertIsNone(state.position)

    def test_fixture_has_closed_aligned_candles(self):
        fixture = json.loads((ROOT / "fixtures/android_python_ohlc_v1.json").read_text())
        for key, step in (("candles_m15", 900000), ("candles_h1", 3600000)):
            rows = fixture[key]
            self.assertTrue(rows)
            self.assertTrue(all(row["closed"] for row in rows))
            self.assertTrue(all(row["timestamp_ms"] % step == 0 for row in rows))
            self.assertTrue(all(b["timestamp_ms"] - a["timestamp_ms"] == step
                                for a, b in zip(rows, rows[1:])))


if __name__ == "__main__":
    unittest.main()
