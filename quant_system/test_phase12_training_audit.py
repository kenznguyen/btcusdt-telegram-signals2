"""Synthetic Phase12 label and TRAIN/TEST purge tests; no Freqtrade required."""
import csv,hashlib,json,tempfile,unittest
from pathlib import Path
from quant_system.phase12_training_audit import audit_training_samples,ROWS

M15=900000
T=1800000000000
FOLD='cb_btc_1800000000'
MODEL='sha256:'+'a'*64

def save(path,records,cols):
    with path.open('w',newline='',encoding='utf8') as f:
        writer=csv.DictWriter(f,fieldnames=cols)
        writer.writeheader();writer.writerows(records)

def sha(path):
    return 'sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()

def setup(root,train=(1,2),test=(7,8)):
    root=Path(root)
    for sub in ('paper','native','canonical'):(root/sub).mkdir()
    prices={T+i*M15:100+i for i in range(17)}
    candles=[dict(open_time=k,close=v,closed=True) for k,v in prices.items()]
    save(root/'canonical/15m.csv',candles,list(candles[0]))
    rows=[];cutoff=T+16*M15
    for kind,indices in (('TRAIN',train),('TEST',test)):
        for i in indices:
            start=T+i*M15;end=start+4*M15
            rows.append(dict(fold_model_name=FOLD,model_identifier='id',
                model_sha256=MODEL,row_kind=kind,feature_open_ms=start,
                label_end_ms=end,observed_raw_label=prices[end]/prices[start]-1,
                expected_recomputed_label=prices[end]/prices[start]-1,
                feature_close=prices[start],future_close=prices[end],
                training_end_ms=cutoff,horizon_candles=4))
    samples=root/'native/freqai-native-training-samples.csv'
    save(samples,rows,ROWS)
    lineage=root/'native/freqai-native-model-lineage.csv'
    tr=[dict(fold_model_name=FOLD,model_sha256=MODEL,model_identifier='id',
             training_end_ms=cutoff,open_time=cutoff,
             configured_label_horizon_candles=4)]
    save(lineage,tr,list(tr[0]))
    pred=root/'native/freqai-native-predictions.csv'
    pred.write_text('synthetic prediction capture fixture\n')
    native=root/'native/native-research-180.json'
    native.write_text(json.dumps(dict(core_native_runtime_succeeded=True,
        freqai_native_runtime_succeeded=True,freqai_oos_verified=False,
        full_core_parity_certified=False,
        phase12_training_samples_sha256=sha(samples),
        phase12_observer_failure_count=0,
        phase8_model_lineage_sha256=sha(lineage),
        prediction_capture_sha256=sha(pred))))
    (root/'paper/phase8-native-model-evidence.json').write_text(json.dumps(dict(
        native_model_lineage_verified=True,errors=[],
        evidence_sha256=dict(lineage=sha(lineage),predictions=sha(pred)))))
    (root/'paper/portfolio-180-conflict-reconciliation.json').write_text(
        json.dumps(dict(source_conflict_reconciliation_verified=True,errors=[])))
    return root,samples

class Phase12Test(unittest.TestCase):
    def test_purged_label_horizon_passes_but_no_oos_certification(self):
        with tempfile.TemporaryDirectory() as d:
            root,_=setup(d)
            r=audit_training_samples(root)
            self.assertTrue(r['actual_fit_sample_lineage_verified'],r)
            self.assertTrue(r['label_reconstruction_verified'])
            self.assertTrue(r['train_test_label_purge_verified'])
            self.assertFalse(r['oos_certified'])
            self.assertEqual((r['train_rows'],r['test_rows']),(2,2))
    def test_no_four_candle_purge_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root,_=setup(d,train=(1,4),test=(7,8))
            r=audit_training_samples(root)
            self.assertTrue(r['actual_fit_sample_lineage_verified'],r)
            self.assertFalse(r['train_test_label_purge_verified'])
            self.assertIn('TRAIN_TEST_LABEL_HORIZON_NOT_PURGED',r['errors'])
    def test_sample_file_tamper_fails_sha(self):
        with tempfile.TemporaryDirectory() as d:
            root,path=setup(d)
            path.write_text(path.read_text()+'\n')
            self.assertIn('PHASE12_TRAINING_SAMPLES_SHA_MISMATCH',
                audit_training_samples(root)['errors'])
    def test_malicious_label_value_is_rejected_with_rehashed_sample_file(self):
        with tempfile.TemporaryDirectory() as d:
            root,path=setup(d)
            with path.open() as f:records=list(csv.DictReader(f))
            records[0]['observed_raw_label']='1234'
            save(path,records,ROWS)
            report=root/'native/native-research-180.json'
            obj=json.loads(report.read_text())
            obj['phase12_training_samples_sha256']=sha(path)
            report.write_text(json.dumps(obj))
            self.assertIn('NATIVE_FIT_LABEL_VALUE_MISMATCH',
                audit_training_samples(root)['errors'])
    def test_fitted_training_boundary_is_checked(self):
        with tempfile.TemporaryDirectory() as d:
            root,path=setup(d)
            with path.open() as f:records=list(csv.DictReader(f))
            records[0]['training_end_ms']=str(T+4*M15)
            save(path,records,ROWS)
            report=root/'native/native-research-180.json'
            obj=json.loads(report.read_text())
            obj['phase12_training_samples_sha256']=sha(path)
            report.write_text(json.dumps(obj))
            self.assertIn('INVALID_FIT_SAMPLE_METADATA',
                audit_training_samples(root)['errors'])
    def test_observer_failures_keep_training_audit_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root,_=setup(d)
            report=root/'native/native-research-180.json'
            obj=json.loads(report.read_text())
            obj['phase12_observer_failure_count']=2
            report.write_text(json.dumps(obj))
            actual=audit_training_samples(root)
            self.assertFalse(actual['actual_fit_sample_lineage_verified'])
            self.assertFalse(actual['train_test_label_purge_verified'])
            self.assertIn('PHASE12_FIT_OBSERVER_REPORTED_ERROR',actual['errors'])

    def test_observer_errors_expose_fold_details_but_remain_unverified(self):
        with tempfile.TemporaryDirectory() as d:
            root,_=setup(d)
            report=root/'native/native-research-180.json'
            obj=json.loads(report.read_text())
            obj['phase12_observer_failure_count']=2
            obj['phase12_observer_failure_examples']=[
                dict(fold_model_name='sub-train-BTC_1',
                     error_type='EvidenceError',
                     error_code='PHASE12_FIT_INDEX_IDENTITY_UNVERIFIED'),
                dict(fold_model_name='sub-train-BTC_2',
                     error_type='ValueError',
                     error_code='PHASE12_RAW_LABEL_MISMATCH')]
            report.write_text(json.dumps(obj))
            actual=audit_training_samples(root)
            self.assertFalse(actual['actual_fit_sample_lineage_verified'])
            self.assertFalse(actual['ready_for_360'])
            self.assertFalse(actual['oos_certified'])
            self.assertIn('PHASE12_FIT_OBSERVER_REPORTED_ERROR',actual['errors'])
            self.assertEqual(actual['phase12_observer_failure_count'],2)
            self.assertEqual(len(actual['phase12_observer_failure_examples']),2)
            self.assertEqual(actual['phase12_observer_failure_examples'][0]['error_code'],
                             'PHASE12_FIT_INDEX_IDENTITY_UNVERIFIED')

    def test_train_test_timestamp_overlap_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root,_=setup(d,train=(1,7),test=(7,8))
            self.assertIn('TRAIN_TEST_ROW_OVERLAP',
                audit_training_samples(root)['errors'])

if __name__=='__main__':
    unittest.main()
