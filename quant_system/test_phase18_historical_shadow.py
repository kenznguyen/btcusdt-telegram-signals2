"""Phase18 RED regressions: historical frozen inference is strictly pre-OOS."""
import unittest
from quant_system.phase18_historical_shadow import (
    HistoricalShadowError, select_historical_witnesses,
    compare_shadow_predictions,
)
M15 = 900000
START = 1793750400000

def times(n=600):
    return [START - n*M15 + i*M15 for i in range(n)]

def snap(feature=1., x=.25, flag=1, prediction=.007):
    return dict(features=[feature, 4.], x=[x, .1],
                flag=flag, prediction=prediction)

class HistoricalFrozenShadowTests(unittest.TestCase):
    def test_picks_only_closed_historical_after_model_cutoff(self):
        t=times()
        sample=select_historical_witnesses(t, t[420], max_count=24)
        self.assertEqual(len(sample),24)
        self.assertTrue(all(320<=i<len(t)-3 and t[i]>=t[420]
                            and t[i]+M15<=START for i in sample))
        self.assertEqual(sample,sorted(set(sample)))

    def test_nonmonotonic_candle_source_rejected(self):
        t=times()
        t[400]=t[399]
        with self.assertRaisesRegex(HistoricalShadowError,
                                    'SHADOW_INVALID_HISTORICAL_TIMEBASE'):
            select_historical_witnesses(t,t[420])

    def test_holdout_intrusion_rejected(self):
        t=times()
        t.append(START)  # contiguous but the candle itself is in holdout
        with self.assertRaisesRegex(HistoricalShadowError,
                                    'SHADOW_HOLDOUT_DATA_FORBIDDEN'):
            select_historical_witnesses(t,t[420])

    def test_insufficient_post_training_samples_rejected(self):
        t=times()
        with self.assertRaisesRegex(HistoricalShadowError,
                                    'SHADOW_NOT_ENOUGH_POST_TRAIN_WITNESSES'):
            select_historical_witnesses(t,t[-6])

    def test_prefix_and_future_mutations_invariant(self):
        self.assertTrue(compare_shadow_predictions(
            snap(),snap(),snap(),snap(),positive_raw_feature_changed=True))

    def test_prediction_drift_rejected(self):
        with self.assertRaisesRegex(HistoricalShadowError,
                                    'SHADOW_FROZEN_PREDICTION_DRIFT'):
            compare_shadow_predictions(
                snap(),snap(prediction=.04),snap(),snap(),True)

    def test_fitted_x_or_flag_drift_rejected(self):
        with self.assertRaisesRegex(HistoricalShadowError,
                                    'SHADOW_FROZEN_X_OR_FLAG_DRIFT'):
            compare_shadow_predictions(
                snap(),snap(x=.4),snap(),snap(),True)
        with self.assertRaisesRegex(HistoricalShadowError,
                                    'SHADOW_FROZEN_X_OR_FLAG_DRIFT'):
            compare_shadow_predictions(
                snap(),snap(flag=0,prediction=None),snap(),snap(),True)

    def test_raw_feature_leakage_rejected(self):
        with self.assertRaisesRegex(HistoricalShadowError,
                                    'SHADOW_FUTURE_DEPENDENT_RAW_FEATURES'):
            compare_shadow_predictions(
                snap(),snap(),snap(feature=2.),snap(),True)

    def test_positive_control_required(self):
        with self.assertRaisesRegex(HistoricalShadowError,
                                    'SHADOW_INEFFECTIVE_CURRENT_CANDLE_CONTROL'):
            compare_shadow_predictions(
                snap(),snap(),snap(),snap(),False)

    def test_rejected_predictions_must_remain_rejected(self):
        q=snap(flag=0,prediction=None)
        self.assertTrue(compare_shadow_predictions(q,q,q,q,True))
        with self.assertRaisesRegex(HistoricalShadowError,
                                    'SHADOW_INVALID_REJECTION_OR_FORECAST'):
            compare_shadow_predictions(snap(flag=0),q,q,q,True)

if __name__ == '__main__':
    unittest.main()
