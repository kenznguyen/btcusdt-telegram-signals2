"""Phase19 RED: native historical model input and forecast byte lineage."""
import unittest
from quant_system.phase19_native_forecast_reconciliation import (
    NativeForecastMismatch, verify_native_row, validate_native_timestamps,
    check_original_prediction_map,
)

START=1793750400000
CUTOFF=1792965600000
M15=900000

def witness(flag=1,pred=.003):
    return dict(features=[1.,2.],x=[.2,.3],flag=flag,prediction=pred)

def native(flag=1,pred=".003"):
    return dict(x=[.2,.3],flag=flag,predicted_return=pred,
                source="freqai-native-backtest",
                pair="BTC/USDT:USDT",model_identifier="chart-pro-okx-shadow-v1")

class Phase19NativeForecastTests(unittest.TestCase):
    def test_exact_reconstruction_agrees(self):
        self.assertTrue(verify_native_row(witness(),native()))

    def test_recomputed_model_input_changed_fails(self):
        altered=native()
        altered["x"]=[.2,.301]
        with self.assertRaisesRegex(NativeForecastMismatch,
                                    "PHASE19_NATIVE_X_MISMATCH"):
            verify_native_row(witness(),altered)

    def test_native_flag_divergence_fails(self):
        with self.assertRaisesRegex(NativeForecastMismatch,
                                    "PHASE19_NATIVE_DO_PREDICT_MISMATCH"):
            verify_native_row(witness(),native(flag=0,pred=""))

    def test_model_forecast_divergence_fails(self):
        with self.assertRaisesRegex(NativeForecastMismatch,
                                    "PHASE19_NATIVE_FORECAST_MISMATCH"):
            verify_native_row(witness(),native(pred=".01"))

    def test_rejected_prediction_must_be_empty(self):
        self.assertTrue(verify_native_row(witness(flag=0,pred=None),
                                         native(flag=0,pred="")))
        with self.assertRaisesRegex(NativeForecastMismatch,
                                    "PHASE19_REJECTED_NATIVE_FORECAST_PRESENT"):
            verify_native_row(witness(flag=0,pred=None),
                              native(flag=0,pred=".001"))

    def test_reject_unapproved_provenance(self):
        altered=native()
        altered["source"]="freqai-frozen-oos"
        with self.assertRaisesRegex(NativeForecastMismatch,
                                    "PHASE19_WRONG_NATIVE_PROVENANCE"):
            verify_native_row(witness(),altered)

    def test_reject_future_or_overlap(self):
        with self.assertRaisesRegex(NativeForecastMismatch,
                                    "PHASE19_HOLDOUT_OR_TRAINING_OVERLAP"):
            validate_native_timestamps([CUTOFF-M15,CUTOFF],CUTOFF,START)
        with self.assertRaisesRegex(NativeForecastMismatch,
                                    "PHASE19_HOLDOUT_OR_TRAINING_OVERLAP"):
            validate_native_timestamps([CUTOFF,START],CUTOFF,START)

    def test_reject_duplicate_and_gapped_index(self):
        with self.assertRaisesRegex(NativeForecastMismatch,
                                    "PHASE19_DUPLICATE_OR_REVERSED_TIME"):
            validate_native_timestamps([CUTOFF,CUTOFF],CUTOFF,START)
        # Sparse but increasing original PREDICT timestamps remain allowed.
        self.assertEqual(validate_native_timestamps(
            [CUTOFF,CUTOFF+2*M15],CUTOFF,START),2)

    def test_prediction_map_rejects_orphans_and_duplicate_source(self):
        t=[CUTOFF,CUTOFF+M15]
        good=[{"open_time":str(t[0])},{"open_time":str(t[1])}]
        self.assertEqual(len(check_original_prediction_map(t,good)),2)
        with self.assertRaisesRegex(NativeForecastMismatch,
                                    "PHASE19_MISSING_NATIVE_PREDICTION"):
            check_original_prediction_map(t,good[:1])
        with self.assertRaisesRegex(NativeForecastMismatch,
                                    "PHASE19_DUPLICATE_NATIVE_PREDICTION"):
            check_original_prediction_map(t,good+[good[-1]])

    def test_missing_model_columns_fails(self):
        item=native()
        item["x"]=[.2]
        with self.assertRaisesRegex(NativeForecastMismatch,
                                    "PHASE19_NATIVE_X_MISMATCH"):
            verify_native_row(witness(),item)

if __name__=="__main__":
    unittest.main()
