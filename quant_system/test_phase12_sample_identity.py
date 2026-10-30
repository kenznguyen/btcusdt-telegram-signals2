"""Phase12 native row-identity tests emulating DataSieve's reset index.

No Freqtrade, DataSieve, or pandas dependency in the unit runner.
"""
import unittest
from types import SimpleNamespace
from quant_system.phase12_sample_identity import resolve_fit_row_ids, RowIdentityError

class Col:
    def __init__(self,values):
        self.values=values
    def __len__(self):
        return len(self.values)
    def __getitem__(self,i):
        return self.values[i]
    @property
    def iloc(self):
        return self

class Date:
    def __init__(self,idx):
        self.index=idx
    def __len__(self):
        return len(self.index)

class Frame:
    def __init__(self,rows):
        self.rows=rows
        # Deliberate identity loss: model labels use RangeIndex 0..N-1.
        self.index=list(range(len(rows)))
    def __len__(self):
        return len(self.rows)
    @property
    def iloc(self):
        return Col(self.rows)

class IdentityLabelPipeline:
    steps=[('scaler',object())]
    def inverse_transform(self,frame):
        return (frame,None,None)

def fixture(di_mask=(1,1),train_labels=(.01,.02,.03,.04,.05,.06,.07,.08),test_labels=(.09,.10)):
    # Chronological original indexed FreqAI dates, then overwritten by
    # reset-index DataSieve features/labels at the fitted model boundary.
    indices=[100+i for i in range(10)]
    dk=SimpleNamespace(train_dates=Date(indices),
                       label_pipeline=IdentityLabelPipeline(),
                       feature_pipeline=SimpleNamespace(
                           steps=[('const',object()),('scaler',object()),('di',object())],
                           __getitem__=lambda x:None))
    di=SimpleNamespace(di_values=[0.0 if x else 9.0 for x in di_mask],di_threshold=.9)
    class Pipeline:
        steps=[('const',object()),('scaler',object()),('di',di)]
        def __getitem__(self,key):
            return di if key=='di' else None
    dk.feature_pipeline=Pipeline()
    selected=[v for v,mask in zip(test_labels,di_mask) if mask]
    dd=dict(train_features=Frame(list(range(8))),
            test_features=Frame(list(range(len(selected)))),
            train_labels=Frame([[v] for v in train_labels]),
            test_labels=Frame([[v] for v in selected]),
            train_weights=[1.0]*8,test_weights=[1.0]*len(selected))
    raw=dict(zip(indices,train_labels+test_labels))
    return dk,dd,raw

class FitRowIdentityTest(unittest.TestCase):
    def test_restores_original_rows_even_when_datasieve_resets_indices(self):
        dk,dd,raw=fixture()
        train,test=resolve_fit_row_ids(dk,dd,raw,split_fraction=.2)
        self.assertEqual(train,[100,101,102,103,104,105,106,107])
        self.assertEqual(test,[108,109])
    def test_di_validation_row_removal_is_proven_by_mask_and_label_inverse(self):
        dk,dd,raw=fixture(di_mask=(1,0))
        train,test=resolve_fit_row_ids(dk,dd,raw,split_fraction=.2)
        self.assertEqual(train,list(range(100,108)))
        self.assertEqual(test,[108])
    def test_model_label_reorder_is_not_misrepresented_as_lineage(self):
        dk,dd,raw=fixture()
        dd['train_labels']=Frame([[.02],[.01],[.03],[.04],[.05],[.06],[.07],[.08]])
        with self.assertRaisesRegex(RowIdentityError,'PHASE12_FIT_LABEL_ORDER_MISMATCH'):
            resolve_fit_row_ids(dk,dd,raw,split_fraction=.2)
    def test_outlier_mask_mismatch_fails_closed(self):
        dk,dd,raw=fixture(di_mask=(1,0))
        dk.feature_pipeline['di'].di_values=[0.0]
        with self.assertRaisesRegex(RowIdentityError,'PHASE12_DI_MASK_IDENTITY_UNVERIFIED'):
            resolve_fit_row_ids(dk,dd,raw,split_fraction=.2)
    def test_unsupported_reordering_pipeline_fails_closed(self):
        dk,dd,raw=fixture()
        dk.feature_pipeline.steps.append(('svm',object()))
        with self.assertRaisesRegex(RowIdentityError,'PHASE12_UNAPPROVED_FEATURE_PIPELINE'):
            resolve_fit_row_ids(dk,dd,raw,split_fraction=.2)
    def test_no_unknown_extra_or_missing_rows(self):
        dk,dd,raw=fixture()
        dd['train_features']=Frame(range(7))
        with self.assertRaisesRegex(RowIdentityError,'PHASE12_FIT_SAMPLE_COUNT_MISMATCH'):
            resolve_fit_row_ids(dk,dd,raw,split_fraction=.2)
    def test_incorrect_fraction_not_accepted(self):
        dk,dd,raw=fixture()
        for fraction in (0,.3,1,True):
            with self.subTest(fraction=fraction):
                with self.assertRaises(RowIdentityError):
                    resolve_fit_row_ids(dk,dd,raw,split_fraction=fraction)
