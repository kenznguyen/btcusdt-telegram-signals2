"""Native FreqAI forecast capture boundary, using only stdlib test doubles."""
import csv
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from quant_system.native_prediction_capture import capture_predictions


class FakeFrame:
    def __init__(self, rows):
        self.rows=rows
        self.columns=set(rows[0]) if rows else set()
    def iterrows(self):
        return iter(enumerate(self.rows))
    def without(self,column):
        return FakeFrame([{k:v for k,v in r.items() if k!=column} for r in self.rows])


class NativeCaptureTest(unittest.TestCase):
    def sample(self,flag=1):
        return FakeFrame([dict(date=datetime(2026,6,1,12,0,tzinfo=timezone.utc),
            open=100.,high=102.,low=99.,close=101.,volume=8.,
            **{'&-future_return':.006 if flag==1 else float('nan'),
               'do_predict':flag})])

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

    def test_rejected_minus_one_never_fabricates_forecast(self):
        with tempfile.TemporaryDirectory() as d:
            destination=Path(d)/'pred.csv'
            capture_predictions(self.sample(-1),destination,'chart-pro-okx-shadow-v1')
            with destination.open() as f: actual=list(csv.DictReader(f))
            self.assertEqual(actual[0]['do_predict'],'-1')
            self.assertEqual(actual[0]['predicted_return'],'')

    def test_nan_warmup_do_predict_is_abstention_without_fabricated_signal(self):
        with tempfile.TemporaryDirectory() as d:
            destination=Path(d)/'pred.csv'
            capture_predictions(self.sample(float('nan')),destination,'chart-pro-okx-shadow-v1')
            with destination.open() as handle:
                rows=list(csv.DictReader(handle))
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]['do_predict'],'0')
            self.assertEqual(rows[0]['predicted_return'],'')

    def test_fails_if_real_prediction_column_absent(self):
        with tempfile.TemporaryDirectory() as d:
            frame=self.sample().without('&-future_return')
            with self.assertRaisesRegex(ValueError,'MISSING_NATIVE_FREQAI_PREDICTIONS'):
                capture_predictions(frame,Path(d)/'pred.csv','chart-pro-okx-shadow-v1')

if __name__=='__main__': unittest.main()