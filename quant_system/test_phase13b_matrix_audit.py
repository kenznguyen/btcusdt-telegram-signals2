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
                "fold_model_name","model_sha256","open_time","do_predict"))
            writer.writeheader()
            for t,flag in ((13500000,1),(14400000,0)):
                writer.writerow(dict(fold_model_name=self.fold,
                    model_sha256=self.sha,open_time=t,do_predict=flag))
        (self.root/"paper/phase12-native-fit-label-audit.json").write_text(json.dumps({
            "actual_fit_sample_lineage_verified":True,
            "train_test_label_purge_verified":True,
            "train_rows":2,"test_rows":2,"errors":[]}))
        (self.root/"paper/phase8-native-model-evidence.json").write_text(json.dumps({
            "native_model_lineage_verified":True,"errors":[]}))
        self.report=self.native/"native-research-180.json"
        self.report.write_text(json.dumps({
            "phase13b_matrix_events_sha256":matrix_digest(self.events),
            "phase12_training_samples_sha256":matrix_digest(train_file),
            "phase8_model_lineage_sha256":matrix_digest(lineage),
            "core_native_runtime_succeeded":True,
            "freqai_native_runtime_succeeded":True,
            "prediction_capture_rows":2}))

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
