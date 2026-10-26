import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from android_ohlc_replay import replay_ohlc
from android_state_replay import ReplayState


class SharedHoldPositionFixtureTests(unittest.TestCase):
    def test_python_does_not_close_without_exit_signal(self):
        fixture = json.loads((ROOT / "fixtures/android_python_hold_position_v1.json").read_text())
        state, events = replay_ohlc(
            fixture["candles_m15"], fixture["candles_h1"],
            ReplayState(fixture["initial_balance"], fixture["initial_position"]),
            symbol=fixture["symbol"])
        self.assertEqual(0, len(events))
        self.assertIsNotNone(state.position)
        self.assertEqual(fixture["initial_position"]["qty"], state.position["qty"])
        self.assertEqual(fixture["initial_balance"], state.balance)


if __name__ == "__main__":
    unittest.main()
