"""Regressions for OOS cross-timeframe OHLCV and historical prehistory seam."""
import copy
import unittest

from quant_system.phase17_oos_ohlcv import (
    OOSMarketIntegrityError,
    verify_oos_ohlcv_integrity,
)

START = 1793750400000
M5 = 300000
M15 = 900000
H1 = 3600000


def candles(start, count, step, volume):
    return [dict(open_time=start + i * step,
                 open=100., high=101., low=99., close=100.,
                 volume=float(volume), closed=True) for i in range(count)]


def valid_sets():
    warm15 = candles(START-128*M15,128,M15,3)
    warm1h = candles(START-100*H1,100,H1,12)
    m15 = candles(START,8,M15,3)
    h1 = candles(START,2,H1,12)
    fine = candles(START,24,M5,1)
    return warm1h,h1,warm15,m15,fine


class FrozenOOSOHLCVRegressions(unittest.TestCase):
    def test_consistent_holdout_and_warmup_pass(self):
        self.assertTrue(verify_oos_ohlcv_integrity(*valid_sets()))

    def test_holdout_5m_volume_drift_must_fail_even_when_prices_match(self):
        groups = list(valid_sets())
        groups[-1] = copy.deepcopy(groups[-1])
        groups[-1][0]['volume'] += 5
        with self.assertRaisesRegex(OOSMarketIntegrityError,
                                    'OOS_TIMEFRAME_OHLCV_INCONSISTENT'):
            verify_oos_ohlcv_integrity(*groups)

    def test_holdout_1h_volume_drift_must_fail_even_when_prices_match(self):
        groups = list(valid_sets())
        groups[1] = copy.deepcopy(groups[1])
        groups[1][0]['volume'] += 7
        with self.assertRaisesRegex(OOSMarketIntegrityError,
                                    'OOS_TIMEFRAME_OHLCV_INCONSISTENT'):
            verify_oos_ohlcv_integrity(*groups)

    def test_historical_h1_prebuffer_cannot_disagree_with_15m_on_prices(self):
        groups = list(valid_sets())
        groups[0] = copy.deepcopy(groups[0])
        groups[0][-1]['close'] = 101
        with self.assertRaisesRegex(OOSMarketIntegrityError,
                                    'OOS_PREHISTORY_H1_M15_INCONSISTENT'):
            verify_oos_ohlcv_integrity(*groups)

    def test_historical_h1_prebuffer_cannot_disagree_with_15m_on_volume(self):
        groups = list(valid_sets())
        groups[0] = copy.deepcopy(groups[0])
        groups[0][-2]['volume'] += 2
        with self.assertRaisesRegex(OOSMarketIntegrityError,
                                    'OOS_PREHISTORY_H1_M15_INCONSISTENT'):
            verify_oos_ohlcv_integrity(*groups)

    def test_bad_warmup_boundary_fails_closed(self):
        groups = list(valid_sets())
        groups[2] = copy.deepcopy(groups[2])
        groups[2][0]['open_time'] -= M15
        with self.assertRaisesRegex(OOSMarketIntegrityError,
                                    'OOS_PREHISTORY_H1_M15_INCONSISTENT'):
            verify_oos_ohlcv_integrity(*groups)

    def test_ratio_or_shape_mismatch_fails_closed(self):
        groups = list(valid_sets())
        groups[-1] = groups[-1][:-1]
        with self.assertRaisesRegex(OOSMarketIntegrityError,
                                    'OOS_TIMEFRAME_OHLCV_INCONSISTENT'):
            verify_oos_ohlcv_integrity(*groups)

if __name__ == '__main__':
    unittest.main()
