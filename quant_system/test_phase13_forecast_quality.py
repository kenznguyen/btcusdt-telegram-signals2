"""Phase13 regression for model-SHA-tied forward label accounting."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from quant_system.phase13_forecast_quality import inspect_forecasts
from quant_system.phase13_oos_stability import WINDOW, sha

def fixture(root):
    for part in ("canonical", "native", "paper"):
        (root / part).mkdir(exist_ok=True)
    start=900000*9
    canonical=root/"canonical/15m.csv"
    with canonical.open("w",newline="") as f:
        w=csv.writer(f);w.writerow(("open_time","close","closed"))
        for i in range(6*WINDOW+4):
            w.writerow((start+i*900000, 30000+i*.1, 1))
    equity=root/"paper/portfolio-dual-equity.csv"
    with equity.open("w",newline="") as f:
        w=csv.writer(f);w.writerow(("candle_close_ms","equity_mtm_ex_funding_usdt"))
        for i in range(6*WINDOW):
            w.writerow((start+(i+1)*900000,100.0))
    predictions=root/"native/freqai-native-predictions.csv"
    models=root/"native/freqai-native-model-lineage.csv"
    with predictions.open("w",newline="") as fp, models.open("w",newline="") as fm:
        p=csv.writer(fp);m=csv.writer(fm)
        p.writerow(("open_time","close","predicted_return","do_predict",
                    "model_identifier","source","pair"))
        m.writerow(("open_time","model_sha256","training_end_ms",
                    "latest_observed_label_end_ms","model_identifier",
                    "configured_label_horizon_candles","do_predict"))
        for i in range(6*WINDOW):
            t=start+i*900000
            p.writerow((t,30000+i*.1,.001,1,"test-model",
                        "freqai-native-backtest","BTC/USDT:USDT"))
            m.writerow((t,"sha256:"+"a"*64,900000*8,900000*7,
                        "test-model",4,1))
    (root/"paper/phase12-native-fit-label-audit.json").write_text(json.dumps({
        "train_test_label_purge_verified":True,
        "actual_fit_sample_lineage_verified":True,
        "errors":[],
        "canonical_m15_sha256":sha(canonical)}))
    (root/"paper/phase8-native-model-evidence.json").write_text(json.dumps({
        "native_model_lineage_verified": True,
        "errors": [],
        "evidence_sha256": {
            "predictions": sha(predictions),
            "lineage": sha(models)
        }
    }))
    (root/"native/native-research-180.json").write_text(json.dumps({
        "prediction_capture_sha256":sha(predictions),
        "phase8_model_lineage_sha256":sha(models),
        "prediction_model_identifier":"test-model",
        "prediction_capture_accepted":6*WINDOW
    }))
    return predictions,models

class ForecastQualityTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.pred,self.models=fixture(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_real_four_candle_labels_accounted_without_oos_promotion(self):
        report=inspect_forecasts(self.root)
        self.assertEqual(report["errors"],[])
        self.assertTrue(report["retrospective_forecast_quality_verified"])
        self.assertEqual(report["labeled_forecasts"],6*WINDOW)
        self.assertEqual(report["right_edge_unlabeled_forecasts"],0)
        self.assertFalse(report["independent_oos_verified"])
        self.assertFalse(report["ready_for_360"])

    def test_prediction_tamper_without_native_sha_change_is_rejected(self):
        with self.pred.open("a") as f:f.write("tamper\n")
        report=inspect_forecasts(self.root)
        self.assertIn("PHASE13_FORECAST_EVIDENCE_SHA_MISMATCH",report["errors"])

    def test_retrained_after_prediction_is_rejected_even_with_matching_sha(self):
        rows=self.models.read_text().splitlines()
        values=rows[1].split(",")
        values[2]=str(900000*100)
        rows[1]=",".join(values)
        self.models.write_text("\n".join(rows)+"\n")
        p=self.root/"native/native-research-180.json"
        report=json.loads(p.read_text())
        report["phase8_model_lineage_sha256"]=sha(self.models)
        p.write_text(json.dumps(report))
        phase8_path=self.root/"paper/phase8-native-model-evidence.json"
        phase8=json.loads(phase8_path.read_text())
        phase8["evidence_sha256"]["lineage"]=sha(self.models)
        phase8_path.write_text(json.dumps(phase8))
        result=inspect_forecasts(self.root)
        self.assertIn("PHASE13_NONCAUSAL_MODEL_TRAINING_TIME",result["errors"])

if __name__=="__main__":
    unittest.main()
