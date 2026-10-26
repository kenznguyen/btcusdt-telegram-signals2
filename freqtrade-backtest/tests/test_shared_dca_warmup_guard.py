import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from android_ohlc_replay import replay_ohlc
from android_state_replay import ReplayState


class SharedDcaWarmupGuardTests(unittest.TestCase):
    def test_no_dca_without_warmed_up_indicators(self):
        fixture = json.loads((ROOT / "fixtures/android_python_dca_warmup_guard_v1.json").read_text())
        before = fixture["initial_position"]
        after, events = replay_ohlc(
            fixture["candles_m15"], fixture["candles_h1"],
            ReplayState(fixture["initial_balance"], before),
            symbol=fixture["symbol"])
        self.assertEqual(0, len(events))
        self.assertFalse(after.position["dca_used"])
        self.assertEqual(before["qty"], after.position["qty"])
        self.assertEqual(before["avg_entry"], after.position["avg_entry"])
        self.assertEqual(fixture["initial_balance"], after.balance)


if __name__ == "__main__":
    unittest.main()
