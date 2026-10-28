import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_signal_predicates import exit_reason, threshold_price


def decision(**changes):
    args = dict(side="LONG", low=99, high=101, candle_open=100,
                candle_close=99, previous_open=101, previous_close=100,
                h1_plus_di=15, h1_minus_di=25, h1_adx=36,
                avg_entry=100, rsi=80, roe_pct=6)
    args.update(changes)
    return exit_reason(**args)


class ExitPriorityTests(unittest.TestCase):
    def test_emergency_beats_soft_and_tp(self):
        self.assertEqual("EMERGENCY_SL", decision(low=90))

    def test_soft_beats_tp(self):
        self.assertEqual("SOFT_SL", decision(low=threshold_price("LONG", 100, -35)))

    def test_tp_when_no_stops(self):
        self.assertEqual("TP", decision())

    def test_missing_h1_disables_soft_but_not_tp(self):
        self.assertEqual("TP", decision(low=threshold_price("LONG", 100, -35),
                                        h1_plus_di=None, h1_minus_di=None, h1_adx=None))

    def test_emergency_works_without_rsi_or_h1(self):
        self.assertEqual("EMERGENCY_SL", decision(low=90, rsi=None,
                         h1_plus_di=None, h1_minus_di=None, h1_adx=None))

    def test_no_exit_when_thresholds_unmet(self):
        self.assertIsNone(decision(rsi=60, roe_pct=-1, h1_adx=20))


if __name__ == "__main__":
    unittest.main()
