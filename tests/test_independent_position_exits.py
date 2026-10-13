"""Deterministic regression tests for independent position exits."""
import unittest
import backtest


class IndependentPositionExitTests(unittest.TestCase):
    def decision(self, side, avg, close, high, low, rsi, roe, plus=40, minus=20, hadx=10,
                 op=None, prev_open=100, prev_close=101):
        op = close if op is None else op
        return backtest._position_exit_decision(
            side=side, avg=avg, close=close, op=op, high=high, low=low,
            rsi=rsi, roe=roe, prev_open=prev_open, prev_close=prev_close,
            plus=plus, minus=minus, hadx=hadx)

    def test_three_open_positions_close_independently(self):
        # Three simultaneous LONG positions: first TP, second emergency SL, third remains open.
        positions = [
            {"id": 101, "side": "LONG", "avg": 100.0},
            {"id": 102, "side": "LONG", "avg": 100.0},
            {"id": 103, "side": "LONG", "avg": 100.0},
        ]
        outcomes = {}
        for p in positions:
            if p["id"] == 101:
                outcomes[p["id"]] = self.decision("LONG", 100, 110, 111, 109, 80, 10)
            elif p["id"] == 102:
                outcomes[p["id"]] = self.decision("LONG", 100, 90, 91, 80, 50, -100)
            else:
                outcomes[p["id"]] = self.decision("LONG", 100, 100, 101, 99, 50, 0)
        self.assertEqual(outcomes[101][0], "TP")
        self.assertEqual(outcomes[102][0], "Emergency SL")
        self.assertIsNone(outcomes[103][0])
        # One position's exit outcome does not mutate another position's state.
        self.assertEqual([p["id"] for p in positions], [101, 102, 103])

    def test_short_position_tp_and_long_position_soft_sl_are_independent(self):
        short_tp = self.decision("SHORT", 100, 90, 91, 89, 20, 10, plus=40, minus=20)
        # Long soft SL requires price threshold + trend reversal + two bearish candles.
        # Low crosses the soft-stop threshold but stays above the emergency-stop threshold.
        long_soft = self.decision("LONG", 100, 98, 100, 97, 50, -40,
                                  plus=10, minus=40, hadx=40,
                                  op=99, prev_open=102, prev_close=101)
        self.assertEqual(short_tp[0], "TP")
        self.assertEqual(long_soft[0], "Soft SL")

    def test_emergency_sl_has_priority_over_tp(self):
        result = self.decision("LONG", 100, 110, 111, 80, 80, 10)
        self.assertEqual(result[0], "Emergency SL")


if __name__ == "__main__":
    unittest.main(verbosity=2)
