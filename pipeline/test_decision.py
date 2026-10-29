import copy
import csv
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from market_data.store import Candle, CandleStore, read_window
from pipeline.decision import evaluate
from pipeline.values import identity
from futures_intelligence.import_collector import HEADERS, build_snapshot


class DecisionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        opening, interval = 1_800_000_000_000, 900_000
        self.now = opening + interval + 5_000
        path = Path(self.temp.name) / "data.sqlite3"
        CandleStore(path).insert([Candle("15m", opening, "100", "102", "99", "101", "3", opening+interval+1000)])
        self.window = read_window(path, "BTCUSDT", "15m", opening, opening+interval)
        self.prediction = {"schemaVersion": 1, "exchange": "binance", "marketType": "USDT_PERPETUAL",
            "symbol": "BTCUSDT", "timeframe": "15m", "candleOpenTimeMs": opening,
            "candleCloseTimeMs": opening+interval, "availableAtMs": self.now-2000,
            "trainedThroughMs": opening, "modelVersion": "model-1", "strategyVersion": "strategy-1",
            "trainingCompletedAtMs": opening+1000, "trainingDatasetVersion": "sha256:"+"a"*64,
            "predictedReturn": "0.004", "doPredict": 1, "datasetVersion": self.window["datasetVersion"]}
        self.intelligence = {"schemaVersion": 1, "exchange": "binance", "marketType": "USDT_PERPETUAL",
            "symbol": "BTCUSDT", "windowStartMs": self.now-301_000, "windowEndMs": self.now-1000,
            "availableAtMs": self.now-500, "quality": "OBSERVED_ONLY", "source": "collector",
            "takerBuyQuote": "120", "takerSellQuote": "80", "netTakerQuote": "40",
            "coverage": {"trades": {"status": "OBSERVED", "rows": 3, "tradeIdGaps": 0,
                                     "lastEventAtMs": self.now-1500}}}
        self.rehash()
        self.book = {"source": "hummingbot", "connector": "binance_perpetual", "symbol": "BTCUSDT",
            "observedAtMs": self.now-100, "bids": [{"price": "100", "quantity": "2"}],
            "asks": [{"price": "101", "quantity": "2"}]}

    def rehash(self):
        payload = {k: v for k, v in self.intelligence.items() if k != "snapshotId"}
        self.intelligence["snapshotId"] = identity("intelligence:", payload)

    def evaluate(self, **changes):
        values = dict(candle_window=self.window, intelligence=self.intelligence,
                      prediction=self.prediction, book=self.book, now_ms=self.now)
        values.update(changes)
        return evaluate(**values)

    def test_real_model_output_and_aligned_flow_create_stable_paper_intent(self):
        result = self.evaluate()
        self.assertEqual(result["action"], "BUY")
        intent = result["intent"]
        self.assertEqual(intent["targetPositionBase"], "0.001")
        self.assertEqual(intent["limitPrice"], "101")
        self.assertEqual(intent["mode"], "PAPER")
        self.assertEqual(self.evaluate(now_ms=self.now+1000)["intent"], intent)
        self.assertEqual(intent["inputSnapshotId"], self.intelligence["snapshotId"])

    def test_negative_forecast_requires_actual_sell_flow(self):
        self.prediction["predictedReturn"] = "-0.004"
        self.assertEqual(self.evaluate()["action"], "WAIT")
        self.intelligence.update(takerBuyQuote="80", takerSellQuote="120", netTakerQuote="-40")
        self.rehash()
        result = self.evaluate()
        self.assertEqual(result["action"], "SELL")
        self.assertEqual(result["intent"]["targetPositionBase"], "-0.001")
        self.assertEqual(result["intent"]["limitPrice"], "100")

    def test_decision_time_includes_the_quote_used_to_choose_the_limit(self):
        result = self.evaluate()
        self.assertEqual(result["action"], "BUY")
        expected = max(self.prediction["availableAtMs"], self.intelligence["availableAtMs"],
                       self.book["observedAtMs"])
        self.assertEqual(result["intent"]["decisionAtMs"], expected)
        self.assertEqual(self.evaluate(now_ms=self.now+1000)["intent"], result["intent"])
        refreshed = self.evaluate(book=self.book | {"observedAtMs": self.now})
        self.assertEqual(refreshed["intent"]["decisionAtMs"], self.now)
        self.assertNotEqual(refreshed["intent"]["intentId"], result["intent"]["intentId"])

    def test_high_precision_collector_flow_is_not_rounded_into_a_mismatch(self):
        path = Path(self.temp.name) / "precise-trades.csv"
        rows = []
        for offset, side, price, quantity in (
            (298000, "buy", "1234567890123456.123456789012", "1.000000000001"),
            (299000, "sell", "1", "0.000000000001"),
        ):
            timestamp = self.intelligence["windowStartMs"]+offset
            trade_id = offset//1000
            rows.append({"exchange": "binance", "market": "futures", "datatype": "trades",
                         "timestamp_ms": str(timestamp), "datetime_utc": datetime.fromtimestamp(
                             timestamp/1000, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                         "symbol": "btcusdt", "trade_id": str(trade_id), "side": side,
                         "price": price, "quantity": quantity, "is_buyer_maker": "0" if side == "buy" else "1",
                         "first_update_id": str(trade_id), "last_update_id": str(trade_id)})
        with path.open("w", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=HEADERS["trades"].split(","))
            writer.writeheader()
            writer.writerows(rows)
        snapshot = build_snapshot(self.intelligence["windowStartMs"], self.intelligence["windowEndMs"],
                                  self.intelligence["availableAtMs"], trades=path)
        self.assertEqual(snapshot["netTakerQuote"], "1234567890124690.691346912467123456789012")
        result = self.evaluate(intelligence=snapshot)
        self.assertEqual(result["action"], "BUY", result["reason"])

    def test_fresh_window_and_import_time_do_not_make_old_trade_events_fresh(self):
        for timestamp in (self.now-297_000, self.intelligence["windowEndMs"], True, None):
            self.intelligence["coverage"]["trades"]["lastEventAtMs"] = timestamp
            self.rehash()
            with self.subTest(last_event=timestamp):
                result = self.evaluate()
                self.assertEqual(result["action"], "WAIT", result["reason"])
                self.assertIsNone(result["intent"])

    def test_missing_inputs_never_invent_a_prediction_or_an_order(self):
        for name in ("candle_window", "intelligence", "prediction", "book"):
            with self.subTest(name=name):
                self.assertEqual(self.evaluate(**{name: None})["action"], "WAIT")
                self.assertIsNone(self.evaluate(**{name: None})["intent"])

    def test_future_stale_outlier_and_model_dataset_mismatches_wait(self):
        mutations = ({"availableAtMs": self.now+1}, {"availableAtMs": self.now-31_000},
                     {"doPredict": 0}, {"doPredict": True}, {"doPredict": 2},
                     {"trainedThroughMs": self.prediction["candleOpenTimeMs"]+1},
                     {"datasetVersion": "sha256:"+"0"*64}, {"predictedReturn": "NaN"},
                     {"candleOpenTimeMs": self.prediction["candleOpenTimeMs"]-900_000},
                     {"modelVersion": ""})
        for changes in mutations:
            with self.subTest(changes=changes):
                self.assertEqual(self.evaluate(prediction=self.prediction | changes)["action"], "WAIT")

    def test_corrupt_or_incomplete_canonical_data_waits(self):
        for mutation in ({"datasetVersion": "sha256:"+"0"*64},
                         {"coverage": {"complete": False}}, {"candles": []}):
            with self.subTest(mutation=mutation):
                self.assertEqual(self.evaluate(candle_window=self.window | mutation)["action"], "WAIT")
        window = copy.deepcopy(self.window)
        window["candles"][0]["isClosed"] = False
        self.assertEqual(self.evaluate(candle_window=window)["action"], "WAIT")

    def test_prediction_requires_training_completion_and_dataset_lineage(self):
        for field in ("trainingCompletedAtMs", "trainingDatasetVersion"):
            prediction = {key: value for key, value in self.prediction.items() if key != field}
            with self.subTest(missing=field):
                self.assertEqual(self.evaluate(prediction=prediction)["action"], "WAIT")
        for changes in ({"trainingCompletedAtMs": self.now+1},
                        {"trainingCompletedAtMs": self.prediction["trainedThroughMs"]-1},
                        {"trainingCompletedAtMs": True}, {"trainingDatasetVersion": "sha256:invalid"},
                        {"trainingDatasetVersion": None}):
            with self.subTest(changes=changes):
                self.assertEqual(self.evaluate(prediction=self.prediction | changes)["action"], "WAIT")

    def test_trade_gaps_missing_flow_wrong_market_and_hash_tampering_wait(self):
        for field, value in (("netTakerQuote", None), ("windowEndMs", self.now-61_000),
                             ("availableAtMs", self.now+1), ("symbol", "ETHUSDT")):
            original = self.intelligence
            self.intelligence = original | {field: value}
            self.rehash()
            with self.subTest(field=field):
                self.assertEqual(self.evaluate()["action"], "WAIT")
            self.intelligence = original
        self.intelligence["coverage"]["trades"]["tradeIdGaps"] = 1
        self.rehash()
        self.assertEqual(self.evaluate()["action"], "WAIT")
        self.intelligence["coverage"]["trades"]["tradeIdGaps"] = 0
        self.rehash()
        self.intelligence["netTakerQuote"] = "999"
        self.assertEqual(self.evaluate()["action"], "WAIT")

    def test_invalid_crossed_stale_future_and_nonfinite_books_wait(self):
        for changes in ({"connector": "binance"}, {"symbol": "ETHUSDT"},
                        {"observedAtMs": self.now-30_001}, {"observedAtMs": self.now+1},
                        {"bids": []}, {"bids": [{"price": "101", "quantity": "1"}]},
                        {"asks": [{"price": "NaN", "quantity": "1"}]}):
            with self.subTest(changes=changes):
                self.assertEqual(self.evaluate(book=self.book | changes)["action"], "WAIT")

    def test_expiry_and_input_bounds_fail_closed(self):
        self.assertEqual(self.evaluate(now_ms=self.now+60_000)["action"], "WAIT")
        for changes in ({"target_base": "0"}, {"threshold": "-1"}, {"max_input_age_ms": True}, {"now_ms": True}):
            with self.subTest(changes=changes):
                self.assertEqual(self.evaluate(**changes)["action"], "WAIT")


if __name__ == "__main__":
    unittest.main()
