"""Canonical transition tests for DCA and EXIT accounting, no live trading."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_ohlc_replay import replay_ohlc, M15_MS
from android_state_replay import ReplayState
from android_signal_predicates import entry_position
from compare_events import validate_event, compare


def candle(i, *, close=100.0, low=None, high=None):
    return {"timestamp_ms": i * M15_MS, "open": close,
            "high": close + 1 if high is None else high,
            "low": close - 1 if low is None else low,
            "close": close, "closed": True}


def indicators(rsi=50.0, adx=30.0):
    return {"rsi": rsi, "adx": adx, "plus_di": 30.0, "minus_di": 10.0}


class ReplayAccountingTests(unittest.TestCase):
    def run_case(self, candles, state, points):
        with patch("android_ohlc_replay.indicator_series", side_effect=[
            points, []
        ]), patch("android_ohlc_replay.aligned_indicators", return_value={
            "h1_plus_di": 30.0, "h1_minus_di": 10.0, "h1_adx": 25.0
        }):
            return replay_ohlc(candles, [], initial_state=state)

    def test_dca_preserves_balance_and_reports_new_average(self):
        position = entry_position(100, "LONG", 100, 0)
        before = ReplayState(100.0, position)
        after, events = self.run_case(
            [candle(0), candle(1, close=98, low=97)],
            before, [indicators(rsi=24), indicators(rsi=25, adx=46)])
        self.assertEqual(1, len(events))
        event = events[0]
        self.assertEqual("DCA", event["kind"])
        self.assertEqual(100.0, event["balance"])
        self.assertEqual(100.0, event["margin"])
        self.assertEqual(after.position["avg_entry"], event["avg_entry"])
        self.assertEqual(after.position["qty"], event["quantity"])
        self.assertIsNone(event["net_pnl"])
        self.assertIsNone(event["fees"])
        validate_event(event)
        self.assertTrue(compare([event], [event])["passed"])

    def test_emergency_exit_uses_pre_exit_position(self):
        position = entry_position(100, "LONG", 100, 0)
        before = ReplayState(100.0, position)
        after, events = self.run_case(
            [candle(0), candle(1, close=95, low=90)],
            before, [indicators(), indicators()])
        self.assertEqual(1, len(events))
        event = events[0]
        self.assertEqual("EMERGENCY_SL", event["kind"])
        self.assertIsNone(after.position)
        self.assertEqual(position["qty"], event["quantity"])
        self.assertEqual(position["avg_entry"], event["avg_entry"])
        self.assertEqual(50.0, event["margin"])
        self.assertGreater(event["fees"], 0)
        self.assertAlmostEqual(100.0 + event["net_pnl"], event["balance"])
        validate_event(event)
        self.assertTrue(compare([event], [event])["passed"])


if __name__ == "__main__":
    unittest.main()
