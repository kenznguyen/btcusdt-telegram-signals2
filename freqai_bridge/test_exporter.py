import copy
import json
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from freqai_bridge.exporter import TARGET, make_prediction, read_context, write_artifact
from freqai_bridge.context import canonical_context
from market_data.store import Candle, CandleStore, read_window


class FreqaiExporterTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.opened = 1_800_000_000_000
        self.now = self.opened+900_000+3000
        database = self.path / "candles.sqlite3"
        CandleStore(database).insert([Candle("15m", self.opened, "100", "102", "99", "101", "3", self.now-1000)])
        self.window = read_window(database, "BTCUSDT", "15m", self.opened, self.opened+900_000)
        self.frame = pd.DataFrame({"date": [pd.Timestamp(self.opened, unit="ms", tz="UTC")],
            "open": [100.0], "high": [102.0], "low": [99.0], "close": [101.0], "volume": [3.0],
            TARGET: [0.004], "do_predict": [1]})
        self.provenance = {"modelVersion": "model-actual-1", "strategyVersion": "chart-pro-shadow-v1",
            "trainedThroughMs": self.opened, "trainingCompletedAtMs": self.opened+1000,
            "trainingDatasetVersion": "sha256:"+"a"*64}

    def test_exports_real_dataframe_prediction_and_preserves_provenance(self):
        result = make_prediction(self.frame, self.window, self.provenance, self.now)
        self.assertEqual(result["predictedReturn"], "0.004")
        self.assertEqual(result["availableAtMs"], self.now)
        self.assertEqual(result["trainedThroughMs"], self.opened)
        self.assertEqual(result["datasetVersion"], self.window["datasetVersion"])
        self.assertEqual(result["modelVersion"], "model-actual-1")
        self.assertEqual(result["trainingDatasetVersion"], "sha256:"+"a"*64)

    def test_rejects_missing_outlier_nonfinite_and_mismatched_actual_model_rows(self):
        frames = [self.frame.drop(columns=[TARGET]), self.frame.assign(do_predict=0),
                  self.frame.assign(do_predict=True), self.frame.assign(**{TARGET: float("nan")}),
                  self.frame.assign(close=100.0), self.frame.assign(date=[pd.Timestamp(self.opened, unit="ms")])]
        for frame in frames:
            with self.subTest(columns=list(frame.columns)), self.assertRaises((ValueError, TypeError)):
                make_prediction(frame, self.window, self.provenance, self.now)

    def test_cannot_invent_training_dates_or_rebind_prediction_to_another_dataset(self):
        for change in ({"trainedThroughMs": self.opened+1}, {"trainingCompletedAtMs": self.now+1},
                       {"datasetVersion": "sha256:"+"0"*64}, {"trainingDatasetVersion": ""}, {"modelVersion": ""}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                make_prediction(self.frame, self.window, self.provenance | change, self.now)
        missing = copy.deepcopy(self.provenance)
        missing.pop("trainedThroughMs")
        with self.assertRaises(KeyError):
            make_prediction(self.frame, self.window, missing, self.now)

    def test_atomic_json_artifact_does_not_load_or_pickle_models(self):
        output = self.path / "prediction.json"
        result = make_prediction(self.frame, self.window, self.provenance, self.now)
        write_artifact(output, result)
        self.assertEqual(read_context(output), result)
        self.assertEqual(list(self.path.glob(".freqai-*")), [])
        with self.assertRaises(ValueError):
            write_artifact(output, {"return": float("nan")})
        self.assertEqual(json.loads(output.read_text()), result)
        with self.assertRaises(ValueError):
            write_artifact(self.path / "model.pkl", result)

    def test_context_hash_matches_api_without_query_time_drift(self):
        database = self.path / "candles.sqlite3"
        first = canonical_context(database, self.now, bars=1)
        later = canonical_context(database, self.now+1000, bars=1)
        self.assertEqual(first, self.window)
        self.assertIsNone(first["asOfMs"])
        self.assertEqual(first["datasetVersion"], later["datasetVersion"])
        with self.assertRaises(ValueError):
            canonical_context(database, self.now, bars=2)


if __name__ == "__main__":
    unittest.main()
