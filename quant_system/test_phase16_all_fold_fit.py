"""Phase16 RED: 26-fold original native matrix contract, no new LightGBM fit."""
import unittest
from quant_system.phase16_all_fold_fit import FoldEvidenceError, index_folds

SHA="sha256:"+"a"*64

def item(name,stage,count=9):
    return {"fold_model_name":name,"stage":stage,"model_sha256":SHA,
            "n_rows":count,"n_features":20,
            "training_end_ms":1792965600000,"label_horizon_candles":4,
            "columns":["x"+str(i) for i in range(20)]}
def sample(name,kind,t):
    return {"fold_model_name":name,"model_sha256":SHA,
            "model_identifier":"chart-pro-okx-shadow-v1",
            "row_kind":kind,"feature_open_ms":str(t*900000),
            "label_end_ms":str((t+4)*900000),
            "training_end_ms":str(30*900000),
            "observed_raw_label":".01","expected_recomputed_label":".01"}

class All26Tests(unittest.TestCase):
    def fixture(self,n=2):
        events=[];rows=[]
        for i in range(n):
            name="cb_btc_"+str(100+i)
            for stage in ("FIT_TRAIN","FIT_TEST","PREDICT"):
                event=item(name,stage,8 if stage=="FIT_TRAIN" else 1)
                event["training_end_ms"]=30*900000
                events.append(event)
            for t in range(1,9):
                rows.append(sample(name,"TRAIN",t))
            rows.append(sample(name,"TEST",20))
        return events,rows

    def test_two_folds_explicit_size_fixture(self):
        e,s=self.fixture()
        self.assertEqual(len(index_folds(e,s,expected_fold_count=2)),2)

    def test_missing_fold_fails_closed(self):
        e,s=self.fixture()
        with self.assertRaisesRegex(FoldEvidenceError,"PHASE16_FOLD_COUNT_MISMATCH"):
            index_folds(e,s,expected_fold_count=26)

    def test_duplicate_fit_event_fails_closed(self):
        e,s=self.fixture()
        e.append(dict(e[0]))
        with self.assertRaisesRegex(FoldEvidenceError,"PHASE16_DUPLICATE_FIT_STAGE"):
            index_folds(e,s,expected_fold_count=2)

    def test_wrong_row_count_fails_closed(self):
        e,s=self.fixture()
        s.pop()
        with self.assertRaisesRegex(FoldEvidenceError,"PHASE16_NATIVE_SOURCE_ROW_COUNT_MISMATCH"):
            index_folds(e,s,expected_fold_count=2)

    def test_missing_prediction_provenance_fails_closed(self):
        e,s=self.fixture()
        e.pop()
        with self.assertRaisesRegex(FoldEvidenceError,"PHASE16_INCOMPLETE_ORIGINAL_FOLD"):
            index_folds(e,s,expected_fold_count=2)

    def test_test_label_after_cutoff_fails_closed(self):
        e,s=self.fixture()
        s[-1]["label_end_ms"]=str(31*900000)
        with self.assertRaisesRegex(FoldEvidenceError,"PHASE16_FOLD_TEMPORAL_PROVENANCE_FAILED"):
            index_folds(e,s,expected_fold_count=2)

if __name__=="__main__":
    unittest.main()
