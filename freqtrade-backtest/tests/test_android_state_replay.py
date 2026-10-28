import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_state_replay import ReplayState, step
from android_signal_predicates import entry_position


def candle(**changes):
    result = {"timestamp_ms": 900000, "open": 100, "high": 101,
              "low": 99, "close": 100, "closed": True}
    result.update(changes)
    return result


class ReplayStepTests(unittest.TestCase):
    def test_entry_from_closed_candle(self):
        state, event = step(ReplayState(), candle(), candle(),
            {"previous_rsi": 30, "rsi": 31, "adx": 35,
             "h1_plus_di": 25, "h1_minus_di": 15, "h1_adx": 21})
        self.assertEqual("ENTRY", event["kind"])
        self.assertEqual("LONG", state.position["side"])
        self.assertEqual(100, state.balance)

    def test_forming_candle_is_ignored(self):
        initial = ReplayState()
        result, event = step(initial, candle(closed=False), candle(), {})
        self.assertEqual(initial, result)
        self.assertIsNone(event)

    def test_emergency_exit_uses_preclose_position_and_net_pnl(self):
        position = entry_position(100, "LONG", 100, 0)
        state, event = step(ReplayState(100, position), candle(low=90), candle(), {})
        self.assertEqual("EMERGENCY_SL", event["kind"])
        self.assertIsNone(state.position)
        self.assertAlmostEqual(100 + event["net_pnl"], state.balance)

    def test_dca_changes_position_not_balance(self):
        position = entry_position(100, "LONG", 100, 0)
        state, event = step(ReplayState(100, position), candle(close=98, low=97),
                            candle(), {"adx": 46, "rsi": 25, "previous_rsi": 24})
        self.assertEqual("DCA", event["kind"])
        self.assertTrue(state.position["dca_used"])
        self.assertEqual(100, state.balance)


if __name__ == "__main__":
    unittest.main()
