"""Synthetic Phase 7 evidence tests; does not simulate genuine FreqAI OOS."""
import csv
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from quant_system.phase7_model_lineage import inspect_lineage

DAY = 86_400_000
M15 = 900_000
START = 1_800_000_000_000
MODEL = 'chart-pro-okx-shadow-v1'

def sha(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()

def utc(ms):
    return datetime.fromtimestamp(ms/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

def fixture(root):
    root = Path(root)
    (root/'paper').mkdir()
    (root/'native').mkdir()
    ends = [START, START+7*DAY]
    lines = [f'INFO Training BTC/USDT:USDT, 1/1 pairs from {utc(end-30*DAY)} to {utc(end)}, {i+1}/2 trains'
             for i,end in enumerate(ends)]
    (root/'native/freqai-native-180.log').write_text('\n'.join(lines)+'\n')
    pred = root/'native/freqai-native-predictions.csv'
    cols = ['open_time','open','high','low','close','volume','predicted_return',
            'do_predict','model_identifier','source','pair']
    rows = [dict(open_time=str(t),open='100',high='102',low='99',close='101',
            volume='12',predicted_return='0.004',do_predict='1',
            model_identifier=MODEL,source='freqai-native-backtest',
            pair='BTC/USDT:USDT')
            for t in (START,START+M15,START+5*M15,START+7*DAY,START+7*DAY+5*M15)]
    with pred.open('w',newline='') as file:
        w=csv.DictWriter(file,fieldnames=cols);w.writeheader();w.writerows(rows)
    native = dict(core_native_runtime_succeeded=True,
        freqai_native_runtime_succeeded=True,prediction_capture_verified=True,
        prediction_capture_rows=len(rows),prediction_capture_accepted=len(rows),
        prediction_capture_sha256=sha(pred),prediction_model_identifier=MODEL,
        full_core_parity_certified=False,freqai_oos_verified=False)
    (root/'native/native-research-180.json').write_text(json.dumps(native))
    (root/'paper/phase6-research-readiness.json').write_text(json.dumps(dict(
        research_report_verified=True,oos_certified=False,ready_for_360=False,
        full_core_parity_certified=False,
        freqai=dict(training_windows_observed=2,accepted_forecasts=len(rows)))))
    config=root/'freqai-config.json'
    config.write_text(json.dumps(dict(freqai=dict(enabled=True,identifier=MODEL,
        train_period_days=30,backtest_period_days=7,
        feature_parameters=dict(label_period_candles=4)))))
    return root,config

class Phase7ModelLineageTest(unittest.TestCase):
    def test_tentative_folds_not_model_certificate(self):
        with tempfile.TemporaryDirectory() as temp:
            root,config=fixture(temp)
            result=inspect_lineage(root,config)
            self.assertTrue(result['research_lineage_consistent'],result)
            self.assertEqual(result['accepted_forecasts'],5)
            self.assertEqual(result['tentative_fold_counts'],[3,2])
            self.assertEqual(result['boundary_horizon_forecasts'],3)
            self.assertFalse(result['per_prediction_model_verified'])
            self.assertFalse(result['purged_label_horizon_verified'])
            self.assertFalse(result['oos_certified'])
            self.assertFalse(result['ready_for_360'])

    def test_prediction_sha_tamper_is_fatal(self):
        with tempfile.TemporaryDirectory() as temp:
            root,config=fixture(temp)
            path=root/'native/freqai-native-predictions.csv'
            path.write_text(path.read_text()+'\n')
            self.assertIn('NATIVE_PREDICTION_SHA_MISMATCH',
                          inspect_lineage(root,config)['errors'])

    def test_accepted_before_first_model_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root,config=fixture(temp)
            path=root/'native/freqai-native-predictions.csv'
            path.write_text(path.read_text().replace(str(START),str(START-M15),1))
            native=root/'native/native-research-180.json'
            report=json.loads(native.read_text())
            report['prediction_capture_sha256']=sha(path)
            native.write_text(json.dumps(report))
            self.assertIn('ACCEPTED_BEFORE_FIRST_TRAIN_CUTOFF',
                          inspect_lineage(root,config)['errors'])

    def test_duplicate_accepted_time_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root,config=fixture(temp)
            path=root/'native/freqai-native-predictions.csv'
            lines=path.read_text().splitlines()
            path.write_text('\n'.join(lines+[lines[1]])+'\n')
            native=root/'native/native-research-180.json'
            report=json.loads(native.read_text())
            report.update(prediction_capture_sha256=sha(path),
                          prediction_capture_rows=6,prediction_capture_accepted=6)
            native.write_text(json.dumps(report))
            self.assertIn('DUPLICATE_NATIVE_PREDICTION_TIME',
                          inspect_lineage(root,config)['errors'])

    def test_wrong_model_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root,config=fixture(temp)
            path=root/'native/freqai-native-predictions.csv'
            path.write_text(path.read_text().replace(MODEL,'foreign'))
            native=root/'native/native-research-180.json'
            report=json.loads(native.read_text())
            report['prediction_capture_sha256']=sha(path)
            native.write_text(json.dumps(report))
            self.assertIn('PREDICTION_MODEL_IDENTIFIER_MISMATCH',
                          inspect_lineage(root,config)['errors'])

    def test_zero_label_horizon_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root,config=fixture(temp)
            settings=json.loads(config.read_text())
            settings['freqai']['feature_parameters']['label_period_candles']=0
            config.write_text(json.dumps(settings))
            self.assertIn('INVALID_LABEL_HORIZON',
                          inspect_lineage(root,config)['errors'])

    def test_missing_phase6_artifact_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root,config=fixture(temp)
            (root/'paper/phase6-research-readiness.json').unlink()
            self.assertFalse(inspect_lineage(root,config)['research_lineage_consistent'])

if __name__=='__main__':
    unittest.main()
