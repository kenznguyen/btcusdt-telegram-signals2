import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from android_ohlc_replay import replay_ohlc
from android_state_replay import ReplayState
from compare_events import validate_event


class SharedEmergencyExitFixtureTests(unittest.TestCase):
    def test_python_emergency_exit_from_seeded_position(self):
        fixture = json.loads((ROOT / "fixtures/android_python_emergency_exit_v1.json").read_text())
        state, events = replay_ohlc(
            fixture["candles_m15"], fixture["candles_h1"],
            ReplayState(fixture["initial_balance"], fixture["initial_position"]),
            symbol=fixture["symbol"])
        self.assertEqual(fixture["expected"]["event_count"], len(events))
        self.assertEqual(fixture["expected"]["kind"], events[0]["kind"])
        self.assertEqual(fixture["expected"]["side"], events[0]["side"])
        self.assertIsNone(state.position)
        self.assertAlmostEqual(fixture["initial_balance"] + events[0]["net_pnl"], state.balance)
        validate_event(events[0])


if __name__ == "__main__":
    unittest.main()
