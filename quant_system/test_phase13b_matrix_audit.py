"""Independent Phase13B matrix reconciliation regression tests."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from quant_system.phase13b_matrix import record_matrix, append_event, matrix_digest
from quant_system.phase13b_matrix_audit import audit_matrices

class MatrixAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        (self.root/"native").mkdir()
        (self.root/"paper").mkdir()
        self.sha="sha256:"+"b"*64
        self.fold="fold1"
        self.native=self.root/"native"
        self.events=self.native/"phase13b-native-matrix-events.jsonl"
        x=pd.DataFrame({"%-a":[.2,.4], "%-b":[.7,.8]})
        for stage,times in (("FIT_TRAIN",[900000,1800000]),
                            ("FIT_TEST",[6300000,7200000]),
                            ("PREDICT",[13500000,14400000])):
            e=record_matrix(self.native,stage=stage,fold=self.fold,
                model_sha=self.sha,features=x,timestamps=times,
                labels=[.01,.02] if stage!="PREDICT" else None,
                weights=[1.,1.] if stage!="PREDICT" else None,
                flags=[1,0] if stage=="PREDICT" else None)
            e["training_end_ms"]=12600000
            e["label_horizon_candles"]=4
            append_event(self.events,e)
        train_file=self.native/"freqai-native-training-samples.csv"
        with train_file.open("w",newline="") as file:
            writer=csv.DictWriter(file,fieldnames=(
                "fold_model_name","model_sha256","row_kind","feature_open_ms"))
            writer.writeheader()
            for kind,ts in (("TRAIN",[900000,1800000]),
                            ("TEST",[6300000,7200000])):
                for t in ts:
                    writer.writerow(dict(fold_model_name=self.fold,
                        model_sha256=self.sha,row_kind=kind,feature_open_ms=t))
        lineage=self.native/"freqai-native-model-lineage.csv"
        with lineage.open("w",newline="") as file:
            writer=csv.DictWriter(file,fieldnames=(
                "fold_model_name","model_sha256","open_time","do_predict",
                "model_identifier"))
            writer.writeheader()
            for t,flag in ((13500000,1),(14400000,0)):
                writer.writerow(dict(fold_model_name=self.fold,
                    model_sha256=self.sha,open_time=t,do_predict=flag,
                    model_identifier="test-model"))
        (self.root/"paper/phase12-native-fit-label-audit.json").write_text(json.dumps({
            "actual_fit_sample_lineage_verified":True,
            "train_test_label_purge_verified":True,
            "train_rows":2,"test_rows":2,"errors":[]}))
        (self.root/"paper/phase8-native-model-evidence.json").write_text(json.dumps({
            "native_model_lineage_verified":True,"errors":[],
            "emitted_lineage_rows":2,
            "matched_accepted_forecasts":1}))
        # The FreqAI-exported CSV includes pre-training neutral rows that
        # have never entered LightGBM.predict(). The model witness must
        # reconcile to Phase8 lineage, NOT demand equality with these rows.
        self.predictions=self.native/"freqai-native-predictions.csv"
        with self.predictions.open("w",newline="") as file:
            writer=csv.DictWriter(file,fieldnames=(
                "open_time","do_predict","predicted_return",
                "model_identifier","source","pair"))
            writer.writeheader()
            for t,flag,forecast in (
                (2700000,0,""),(3600000,0,""),
                (13500000,1,"0.025"),(14400000,0,"")
            ):
                writer.writerow(dict(open_time=t,do_predict=flag,
                    predicted_return=forecast,model_identifier="test-model",
                    source="freqai-native-backtest",pair="BTC/USDT:USDT"))
        bundle=self.native/"phase13b-unsealed-model-candidate.joblib"
        bundle.write_bytes(b"trusted test-only candidate")
        meta=self.native/"phase13b-unsealed-model-candidate.json"
        meta.write_text(json.dumps({
            "fold_model_name":self.fold,"model_sha256":self.sha,
            "training_end_ms":12600000,"ordered_feature_columns":["%-a","%-b"],
            "candidate_sha256":matrix_digest(bundle),
            "sealed_in_git":False
        }))
        self.report=self.native/"native-research-180.json"
        self.report.write_text(json.dumps({
            "phase13b_candidate_sha256":matrix_digest(bundle),
            "phase13b_candidate_metadata_sha256":matrix_digest(meta),
            "phase13b_matrix_events_sha256":matrix_digest(self.events),
            "phase12_training_samples_sha256":matrix_digest(train_file),
            "phase8_model_lineage_sha256":matrix_digest(lineage),
            "core_native_runtime_succeeded":True,
            "freqai_native_runtime_succeeded":True,
            "prediction_model_identifier":"test-model",
            "prediction_capture_rows":4,
            "prediction_capture_accepted":1,
            "prediction_capture_sha256":matrix_digest(self.predictions)}))

    def tearDown(self):
        self.tmp.cleanup()

    def test_reconstruct_and_link_exact_fitted_and_predicted_rows(self):
        result=audit_matrices(self.root)
        self.assertEqual(result["errors"],[])
        self.assertTrue(result["actual_fit_predict_matrices_verified"])
        self.assertEqual(result["model_fold_count"],1)
        self.assertEqual(result["fit_train_rows"],2)
        self.assertEqual(result["predict_rows"],2)
        self.assertFalse(result["independent_oos_verified"])
        self.assertFalse(result["full_model_pipeline_causality_verified"])

    def test_pretraining_neutral_csv_rows_are_accounted_not_lightgbm_calls(self):
        result=audit_matrices(self.root)
        self.assertEqual(result["errors"],[])
        self.assertTrue(result["actual_fit_predict_matrices_verified"])
        self.assertEqual(result["predict_rows"],2)
        self.assertEqual(result["exported_prediction_rows"],4)
        self.assertEqual(result["unmodeled_neutral_rows"],2)
        self.assertEqual(result["modeled_prediction_rows"],2)
        self.assertEqual(result["modeled_accepted_rows"],1)

    def test_one_adjacent_trailing_neutral_candle_is_accounted(self):
        # FreqAI may export the next closed candle after the last actual
        # LightGBM.predict window. This cannot be called training warmup.
        lines=self.predictions.read_text().splitlines()
        lines.append("15300000,0,,test-model,freqai-native-backtest,BTC/USDT:USDT")
        self.predictions.write_text("\n".join(lines)+"\n")
        report=json.loads(self.report.read_text())
        report["prediction_capture_sha256"]=matrix_digest(self.predictions)
        report["prediction_capture_rows"]=5
        self.report.write_text(json.dumps(report))
        output=audit_matrices(self.root)
        self.assertEqual(output["errors"],[])
        self.assertTrue(output["actual_fit_predict_matrices_verified"])
        self.assertEqual(output["unmodeled_neutral_rows"],3)
        self.assertEqual(output["unmodeled_warmup_rows"],2)
        self.assertEqual(output["unmodeled_trailing_rows"],1)
        self.assertEqual(output["modeled_prediction_rows"],2)

    def test_untraced_neutral_inside_model_time_range_is_denied(self):
        from quant_system.phase13b_matrix_audit import reconcile_exported_predictions
        from quant_system.phase13b_matrix import MatrixEvidenceError
        # Make a synthetic model lineage with a hole at 14,400,000.
        self.predictions.write_text(
            "open_time,do_predict,predicted_return,model_identifier,source,pair\n"
            "13500000,1,0.025,test-model,freqai-native-backtest,BTC/USDT:USDT\n"
            "14400000,0,,test-model,freqai-native-backtest,BTC/USDT:USDT\n"
            "15300000,0,,test-model,freqai-native-backtest,BTC/USDT:USDT\n")
        report={"prediction_capture_sha256":matrix_digest(self.predictions),
                "prediction_capture_rows":3,
                "prediction_capture_accepted":1,
                "prediction_model_identifier":"test-model"}
        phase8={"matched_accepted_forecasts":1,"emitted_lineage_rows":2}
        lineage={(self.fold,self.sha):[(13500000,1),(15300000,0)]}
        with self.assertRaisesRegex(MatrixEvidenceError,
                "PHASE13B_UNMODELED_ROW_INSIDE_INFERENCE_WINDOW") as failure:
            reconcile_exported_predictions(self.native,report,phase8,lineage)
        self.assertEqual(failure.exception.row_diagnostics["open_time_ms"],
                         14400000)
        self.assertEqual(failure.exception.row_diagnostics["last_model_open_ms"],
                         15300000)

    def test_nonadjacent_trailing_neutral_candle_is_denied(self):
        lines=self.predictions.read_text().splitlines()
        lines.append("16200000,0,,test-model,freqai-native-backtest,BTC/USDT:USDT")
        self.predictions.write_text("\n".join(lines)+"\n")
        report=json.loads(self.report.read_text())
        report["prediction_capture_sha256"]=matrix_digest(self.predictions)
        report["prediction_capture_rows"]=5
        self.report.write_text(json.dumps(report))
        outcome=audit_matrices(self.root)
        self.assertFalse(outcome["actual_fit_predict_matrices_verified"])
        self.assertIn("PHASE13B_UNEXPLAINED_POSTMODEL_NEUTRAL_ROW",outcome["errors"])
        self.assertEqual(outcome["failing_unmodeled_row"]["open_time_ms"],
                         16200000)
        self.assertEqual(outcome["failing_unmodeled_row"]["last_model_open_ms"],
                         14400000)

    def test_untraced_accepted_forecast_after_last_model_is_denied(self):
        lines=self.predictions.read_text().splitlines()
        lines.append("15300000,1,0.025,test-model,freqai-native-backtest,BTC/USDT:USDT")
        self.predictions.write_text("\n".join(lines)+"\n")
        report=json.loads(self.report.read_text())
        report["prediction_capture_sha256"]=matrix_digest(self.predictions)
        report["prediction_capture_rows"]=5
        report["prediction_capture_accepted"]=2
        self.report.write_text(json.dumps(report))
        outcome=audit_matrices(self.root)
        self.assertFalse(outcome["actual_fit_predict_matrices_verified"])
        self.assertIn("PHASE13B_ACCEPTED_FORECAST_WITHOUT_MODEL_MATRIX",
                      outcome["errors"])

    def test_unmodeled_accepted_forecast_is_never_exempted(self):
        lines=self.predictions.read_text().splitlines()
        lines[1]=lines[1].replace(",0,,",",1,0.123,")
        self.predictions.write_text("\n".join(lines)+"\n")
        report=json.loads(self.report.read_text())
        report["prediction_capture_sha256"]=matrix_digest(self.predictions)
        report["prediction_capture_accepted"]=2
        self.report.write_text(json.dumps(report))
        output=audit_matrices(self.root)
        self.assertFalse(output["actual_fit_predict_matrices_verified"])
        self.assertIn("PHASE13B_ACCEPTED_FORECAST_WITHOUT_MODEL_MATRIX",output["errors"])

    def test_untraced_forecast_value_on_neutral_row_denied(self):
        lines=self.predictions.read_text().splitlines()
        lines[1]=lines[1].replace(",0,,",",0,0.123,")
        self.predictions.write_text("\n".join(lines)+"\n")
        report=json.loads(self.report.read_text())
        report["prediction_capture_sha256"]=matrix_digest(self.predictions)
        self.report.write_text(json.dumps(report))
        output=audit_matrices(self.root)
        self.assertFalse(output["actual_fit_predict_matrices_verified"])
        self.assertIn("PHASE13B_NONMODEL_ROW_NOT_NEUTRAL",output["errors"])

    def test_traced_prediction_flag_mismatch_denied(self):
        lines=self.predictions.read_text().splitlines()
        lines[3]=lines[3].replace(",1,0.025,",",0,,")
        self.predictions.write_text("\n".join(lines)+"\n")
        report=json.loads(self.report.read_text())
        report["prediction_capture_sha256"]=matrix_digest(self.predictions)
        report["prediction_capture_accepted"]=0
        self.report.write_text(json.dumps(report))
        output=audit_matrices(self.root)
        self.assertFalse(output["actual_fit_predict_matrices_verified"])
        self.assertIn("PHASE13B_EXPORTED_PREDICTION_MODEL_FLAG_MISMATCH",output["errors"])

    def test_candidate_must_be_same_latest_model_and_schema(self):
        meta_path=self.native/"phase13b-unsealed-model-candidate.json"
        meta=json.loads(meta_path.read_text())
        meta["model_sha256"]="sha256:"+"c"*64
        meta_path.write_text(json.dumps(meta))
        report=json.loads(self.report.read_text())
        report["phase13b_candidate_metadata_sha256"]=matrix_digest(meta_path)
        self.report.write_text(json.dumps(report))
        outcome=audit_matrices(self.root)
        self.assertFalse(outcome["actual_fit_predict_matrices_verified"])
        self.assertIn("PHASE13B_CANDIDATE_NOT_LAST_VERIFIED_MODEL",outcome["errors"])

    def test_tampered_npz_detected(self):
        events=[json.loads(x) for x in self.events.read_text().splitlines()]
        file=self.native/events[0]["path"]
        with file.open("ab") as f:f.write(b"corrupt")
        result=audit_matrices(self.root)
        self.assertFalse(result["actual_fit_predict_matrices_verified"])
        self.assertIn("MATRIX_SHA_MISMATCH",result["errors"])

    def test_mismatched_source_row_denied(self):
        source=self.native/"freqai-native-training-samples.csv"
        lines=source.read_text().splitlines()
        lines[1]=lines[1].replace("900000","2700000")
        source.write_text("\n".join(lines)+"\n")
        meta=json.loads(self.report.read_text())
        meta["phase12_training_samples_sha256"]=matrix_digest(source)
        self.report.write_text(json.dumps(meta))
        result=audit_matrices(self.root)
        self.assertFalse(result["actual_fit_predict_matrices_verified"])
        self.assertIn("PHASE13B_FITTED_SOURCE_TIMESTAMPS_MISMATCH",result["errors"])

if __name__=="__main__":unittest.main()
