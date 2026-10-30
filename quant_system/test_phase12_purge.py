"""Phase12 regression: purge actual FreqAI train rows BEFORE feature/label fitting.

No pandas, sklearn, Freqtrade, external data or exchange required.
"""
import unittest
from datetime import datetime,timedelta,timezone
from types import SimpleNamespace
from quant_system.phase12_purge import purge_train_test_split, PurgeError

class Series:
    def __init__(self,values): self.data=list(values)
    def __len__(self): return len(self.data)
    def __getitem__(self,slice_): return Series(self.data[slice_])
    @property
    def iloc(self): return self
    def copy(self):return Series(self.data)
    @property
    def index(self):return [v[0] for v in self.data]

class Dates:
    def __init__(self,values):self.data=dict(values)
    @property
    def loc(self):return self
    def __getitem__(self,index):return self.data[index]

def setup(gap=0):
    t=datetime(2026,9,1,tzinfo=timezone.utc)
    indices=list(range(500,530))
    # 24 chronological train, 6 validation timestamps.
    # gap advances the TEST time while preserving sample order.
    dates=[(index,t+timedelta(minutes=15*(i+gap*(i>=24))))
           for i,index in enumerate(indices)]
    df=dict(train_features=Series((i,i*2) for i in indices[:24]),
            test_features=Series((i,i*2) for i in indices[24:]),
            train_labels=Series((i,i*.01) for i in indices[:24]),
            test_labels=Series((i,i*.01) for i in indices[24:]),
            train_weights=list(range(24)),
            test_weights=list(range(6)))
    dk=SimpleNamespace(train_dates=Dates(dates))
    return dk,df

class LabelPurgeTests(unittest.TestCase):
    def test_removes_exactly_four_leaking_train_rows_before_fit(self):
        dk,dd=setup()
        original_test=dd['test_features'].data.copy()
        actual=purge_train_test_split(dk,dd,horizon=4)
        self.assertIs(actual,dd)
        self.assertEqual(dd['train_features'].index,list(range(500,520)))
        self.assertEqual(dd['train_labels'].index,list(range(500,520)))
        self.assertEqual(dd['train_weights'],list(range(20)))
        self.assertEqual(dd['test_features'].data,original_test)
        self.assertEqual(dk._phase12_purged_train_source_indices,list(range(500,520)))
        self.assertEqual(dk._phase12_purge_meta['removed_train_rows'],4)
        self.assertEqual(dk._phase12_purge_meta['horizon_candles'],4)
    def test_gap_requires_only_two_purged_rows(self):
        dk,dd=setup(gap=2)
        purge_train_test_split(dk,dd,horizon=4)
        self.assertEqual(dk._phase12_purge_meta['removed_train_rows'],2)
        self.assertEqual(len(dd['train_features']),22)
    def test_six_candle_gap_requires_no_purge(self):
        dk,dd=setup(gap=6)
        purge_train_test_split(dk,dd,horizon=4)
        self.assertEqual(dk._phase12_purge_meta['removed_train_rows'],0)
        self.assertEqual(len(dd['train_features']),24)
    def test_model_training_labels_and_weights_must_remain_aligned(self):
        dk,dd=setup()
        dd['train_labels']=dd['train_labels'].iloc[:-1].copy()
        with self.assertRaisesRegex(PurgeError,'PHASE12_PREPURGE_SPLIT_IDENTITY_INVALID'):
            purge_train_test_split(dk,dd,horizon=4)
    def test_nonchronological_dataset_fails_closed(self):
        dk,dd=setup()
        dk.train_dates.data[501]=dk.train_dates.data[500]-timedelta(minutes=15)
        with self.assertRaisesRegex(PurgeError,'PHASE12_NONCHRONOLOGICAL_SPLIT'):
            purge_train_test_split(dk,dd,horizon=4)
    def test_horizon_must_equal_original_four_candles(self):
        for horizon in (0,3,5,True):
            dk,dd=setup()
            with self.subTest(horizon=horizon):
                with self.assertRaisesRegex(PurgeError,'PHASE12_UNAPPROVED_LABEL_HORIZON'):
                    purge_train_test_split(dk,dd,horizon=horizon)
    def test_does_not_purge_test_rows_or_reassign_them_as_train(self):
        dk,dd=setup()
        before=dd['test_labels'].data.copy()
        purge_train_test_split(dk,dd,horizon=4)
        self.assertEqual(dd['test_labels'].data,before)
        self.assertEqual(dd['test_weights'],list(range(6)))
        self.assertTrue(set(dd['train_features'].index).isdisjoint(dd['test_features'].index))

if __name__=='__main__':unittest.main()
