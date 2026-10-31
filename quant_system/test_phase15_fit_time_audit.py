"""Phase15 strict historical fit eligibility and native X/y/w contract tests."""
import unittest
import numpy as np
import pandas as pd

from quant_system.phase15_fit_time_audit import (
    FitCausalityError, eligible_rows, verify_fitted_outputs
)


def sample(i, cutoff, kind):
    return dict(feature_open_ms=str(i*900000),
        label_end_ms=str((i+4)*900000),
        training_end_ms=str(cutoff), row_kind=kind,
        observed_raw_label="0.015",
        expected_recomputed_label="0.015")


class Phase15FittingTests(unittest.TestCase):
    def setUp(self):
        self.end=30*900000
        self.train=[sample(i,self.end,"TRAIN") for i in range(1,11)]
        self.test=[sample(i,self.end,"TEST") for i in range(16,25)]

    def test_fit_rows_temporally_purged(self):
        train,test=eligible_rows(self.train,self.test,self.end)
        self.assertEqual((len(train),len(test)),(10,9))

    def test_train_label_overlapping_test_is_denied(self):
        self.train[-1]=sample(13,self.end,"TRAIN")
        with self.assertRaisesRegex(FitCausalityError,
                                    "PHASE15_FIT_LABEL_PURGE_OR_TEMPORAL_LEAK"):
            eligible_rows(self.train,self.test,self.end)

    def test_validation_target_after_training_cutoff_is_denied(self):
        self.test[-1]=sample(27,self.end,"TEST")
        with self.assertRaisesRegex(FitCausalityError,
                                    "PHASE15_FIT_LABEL_PURGE_OR_TEMPORAL_LEAK"):
            eligible_rows(self.train,self.test,self.end)

    def test_forged_label_is_denied(self):
        self.train[0]["observed_raw_label"]="0.9"
        with self.assertRaisesRegex(FitCausalityError,
                                    "PHASE15_UNTRUSTED_FIT_ROW_PROVENANCE"):
            eligible_rows(self.train,self.test,self.end)

    def test_exact_native_lightgbm_x_y_w(self):
        x=pd.DataFrame({"%a":[.1,.3],"%b":[-1.,1.]})
        native=dict(columns=["%a","%b"],
            values=np.array([[.1,-1.],[.3,1.]]),
            labels=[.4,.6],weights=[1.,1.],
            timestamps=[900000,1800000])
        self.assertEqual(verify_fitted_outputs(
            native,x,[.4,.6],[1.,1.],[900000,1800000]),2)
        x.iloc[0,0]+=.01
        with self.assertRaisesRegex(FitCausalityError,
                    "PHASE15_REPLAYED_FIT_NOT_NATIVE_LIGHTGBM_X_Y_W"):
            verify_fitted_outputs(native,x,[.4,.6],[1.,1.],
                                  [900000,1800000])
        x.iloc[0,0]=.1
        with self.assertRaisesRegex(FitCausalityError,
                    "PHASE15_REPLAYED_FIT_NOT_NATIVE_LIGHTGBM_X_Y_W"):
            verify_fitted_outputs(native,x,[.4,.6],[1.,2.],
                                  [900000,1800000])
        with self.assertRaisesRegex(FitCausalityError,
                    "PHASE15_REPLAY_FIT_SHAPE_OR_ORDER_MISMATCH"):
            verify_fitted_outputs(native,x,[.4,.6],[1.,1.],
                                  [1800000,900000])


if __name__=="__main__":
    unittest.main()
