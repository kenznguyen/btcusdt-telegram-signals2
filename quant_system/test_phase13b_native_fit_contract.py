"""Pinned FreqAI 2026.9 and LightGBM actual fit/predict interception contract."""
import inspect
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd

from lightgbm import LGBMRegressor
from freqtrade.freqai.base_models.BaseRegressionModel import BaseRegressionModel
from freqtrade.freqai.prediction_models.LightGBMRegressor import LightGBMRegressor

class PinnedModelCallContractTests(unittest.TestCase):
    def test_pinned_model_passes_transformed_data_dictionary_into_sklearn_fit(self):
        fit=inspect.getsource(LightGBMRegressor.fit)
        self.assertIn('data_dictionary["train_features"]',fit)
        self.assertIn('data_dictionary["train_labels"]',fit)
        self.assertIn('data_dictionary["train_weights"]',fit)
        self.assertIn("model.fit(",fit)
        self.assertIn("eval_set=eval_set",fit)
        predict=inspect.getsource(BaseRegressionModel.predict)
        self.assertIn('self.model.predict(dk.data_dictionary["prediction_features"])',
                      predict)
        self.assertIn("dk.feature_pipeline.transform(",predict)

    def test_actual_lightgbm_model_fit_and_predict_calls_are_witnessed(self):
        source=pd.DataFrame({"%-price":np.linspace(.1,.2,90),
                             "%-volume":np.linspace(.7,1.0,90)})
        targets=np.linspace(-.1,.1,90)
        real=LGBMRegressor.fit
        events=[]
        def witness(self,*args,**kwargs):
            events.append((kwargs["X"].copy(),np.asarray(kwargs["y"]).copy()))
            return real(self,*args,**kwargs)
        model=LGBMRegressor(n_estimators=3,verbosity=-1)
        with patch.object(LGBMRegressor,"fit",witness):
            model.fit(X=source,y=targets)
        self.assertEqual(len(events),1)
        pd.testing.assert_frame_equal(events[0][0],source)
        np.testing.assert_array_equal(events[0][1],targets)
        watched=[]
        saved=model.predict
        def pred_hook(x,*a,**kw):
            watched.append(x.copy())
            return saved(x,*a,**kw)
        with patch.object(model,"predict",pred_hook):
            predictions=model.predict(source.iloc[-5:])
        self.assertEqual(len(watched),1)
        self.assertEqual(len(predictions),5)
        pd.testing.assert_frame_equal(watched[0],source.iloc[-5:])

if __name__=="__main__":unittest.main()
