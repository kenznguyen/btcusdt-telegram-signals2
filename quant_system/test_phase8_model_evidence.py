"""Phase 8 strict native provenance tests (synthetic fixtures only)."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from quant_system.phase8_model_evidence import audit_native_model_evidence,booster_sha256

MODEL='chart-pro-okx-shadow-v1'
START=1777827600000
M15=900000

def sha(path):
    return 'sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()

def write(path,rows):
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)

def fixture(root):
    root=Path(root)
    (root/'native').mkdir()
    (root/'paper').mkdir()
    pred=root/'native/freqai-native-predictions.csv'
    rows=[]
    lineage=[]
    for i in range(8):
        ts=START+i*M15
        rows.append(dict(open_time=str(ts),model_identifier=MODEL,
            source='freqai-native-backtest',pair='BTC/USDT:USDT',
            do_predict='1',predicted_return='.01'))
        lineage.append(dict(open_time=str(ts),model_identifier=MODEL,
            model_sha256='sha256:'+'a'*64,fold_model_name='cb_btc_1777827600',
            training_end_ms=str(START),latest_train_feature_ms=str(START-M15),
            latest_observed_label_end_ms=str(START-M15),
            configured_label_horizon_candles='4',do_predict='1'))
    write(pred,rows)
    write(root/'native/freqai-native-model-lineage.csv',lineage)
    lineage_sha=sha(root/'native/freqai-native-model-lineage.csv')
    (root/'native/native-research-180.json').write_text(json.dumps(dict(
        freqai_native_runtime_succeeded=True,core_native_runtime_succeeded=True,
        prediction_capture_sha256=sha(pred),prediction_capture_accepted=8,
        phase8_model_lineage_sha256=lineage_sha,
        prediction_capture_rows=8,freqai_oos_verified=False,
        full_core_parity_certified=False)))
    (root/'paper/phase7-inferred-model-lineage.json').write_text(json.dumps(dict(
        research_lineage_consistent=True,per_prediction_model_verified=False,
        oos_certified=False,ready_for_360=False,accepted_forecasts=8,
        evidence_sha256=dict(predictions=sha(pred)))))
    return root

def update_manifest(root,path):
    native=root/'native/native-research-180.json'
    report=json.loads(native.read_text())
    report['phase8_model_lineage_sha256']=sha(path)
    native.write_text(json.dumps(report))

class Phase8Test(unittest.TestCase):
    def test_joined_native_rows_remain_noncertified(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=audit_native_model_evidence(fixture(tmp))
            self.assertTrue(result['native_model_lineage_verified'],result)
            self.assertEqual(result['matched_accepted_forecasts'],8)
            self.assertEqual(result['unique_model_fingerprints'],1)
            self.assertFalse(result['oos_certified'])
            self.assertFalse(result['purged_label_horizon_verified'])
            self.assertFalse(result['ready_for_360'])

    def test_missing_prediction_link_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=fixture(tmp);p=root/'native/freqai-native-model-lineage.csv'
            with p.open(newline='') as f: rows=list(csv.DictReader(f))
            write(p,rows[:-1])
            update_manifest(root,p)
            self.assertIn('MISSING_ACCEPTED_MODEL_LINEAGE',
                          audit_native_model_evidence(root)['errors'])

    def test_future_label_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=fixture(tmp);p=root/'native/freqai-native-model-lineage.csv'
            with p.open(newline='') as f: rows=list(csv.DictReader(f))
            rows[0]['latest_observed_label_end_ms']=str(START+M15)
            write(p,rows)
            update_manifest(root,p)
            self.assertIn('NONCAUSAL_MODEL_LABEL_BOUNDARY',
                          audit_native_model_evidence(root)['errors'])

    def test_duplicate_model_timestamp_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=fixture(tmp);p=root/'native/freqai-native-model-lineage.csv'
            with p.open(newline='') as f: rows=list(csv.DictReader(f))
            write(p,rows+[rows[0]])
            update_manifest(root,p)
            self.assertIn('DUPLICATE_MODEL_PREDICTION_TIME',
                          audit_native_model_evidence(root)['errors'])

    def test_invalid_hash_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=fixture(tmp);p=root/'native/freqai-native-model-lineage.csv'
            with p.open(newline='') as f: rows=list(csv.DictReader(f))
            rows[0]['model_sha256']='sha256:fake'
            write(p,rows)
            update_manifest(root,p)
            self.assertIn('INVALID_MODEL_FINGERPRINT',
                          audit_native_model_evidence(root)['errors'])

    def test_fingerprint_trace_sha_tamper_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=fixture(tmp)
            path=root/'native/freqai-native-model-lineage.csv'
            path.write_text(path.read_text()+'\\n')
            self.assertIn('NATIVE_MODEL_LINEAGE_SHA_MISMATCH',
                          audit_native_model_evidence(root)['errors'])

    def test_missing_model_trace_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=fixture(tmp)
            (root/'native/freqai-native-model-lineage.csv').unlink()
            self.assertFalse(audit_native_model_evidence(root)['native_model_lineage_verified'])

    def test_prediction_sha_tamper_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=fixture(tmp);p=root/'native/freqai-native-predictions.csv'
            p.write_text(p.read_text()+'\n')
            self.assertIn('NATIVE_PREDICTION_SHA_MISMATCH',
                          audit_native_model_evidence(root)['errors'])

    def test_booster_hash_deterministic(self):
        class Booster:
            def model_to_string(self):return 'serialized-lightgbm-model'
        class Model:
            booster_=Booster()
        expected='sha256:'+hashlib.sha256(b'serialized-lightgbm-model').hexdigest()
        self.assertEqual(booster_sha256(Model()),expected)

if __name__=='__main__':
    unittest.main()
