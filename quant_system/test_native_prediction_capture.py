import csv
from pathlib import Path
import tempfile
import unittest
import pandas as pd

from quant_system.native_prediction_capture import capture_predictions


class NativeCaptureTest(unittest.TestCase):
    def sample(self):
        return pd.DataFrame([dict(date=pd.Timestamp('2026-06-01T12:00:00Z'),
            open=100.,high=102.,low=99.,close=101.,volume=8.,
            **{'&-future_return':.006,'do_predict':1})])

    def test_writes_real_model_output_only_with_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            destination=Path(d)/'pred.csv'
            result=capture_predictions(self.sample(),destination,'chart-pro-okx-shadow-v1')
            self.assertEqual(result,1)
            with destination.open() as f: actual=list(csv.DictReader(f))
            self.assertEqual(len(actual),1)
            self.assertAlmostEqual(float(actual[0]['predicted_return']),0.006)
            self.assertEqual(actual[0]['do_predict'],'1')
            self.assertEqual(actual[0]['source'],'freqai-native-backtest')

    def test_fails_if_real_prediction_column_absent(self):
        with tempfile.TemporaryDirectory() as d:
            frame=self.sample().drop(columns=['&-future_return'])
            with self.assertRaisesRegex(ValueError,'MISSING_NATIVE_FREQAI_PREDICTIONS'):
                capture_predictions(frame,Path(d)/'pred.csv','chart-pro-okx-shadow-v1')

if __name__=='__main__': unittest.main()