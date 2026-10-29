import copy
import csv
from datetime import datetime, timedelta, timezone
from decimal import Decimal, localcontext
from pathlib import Path
import tempfile
import unittest

from data_lake.analytics import CROSS_ANALYSIS_DELAY_MS, MAX_SNAPSHOTS, build_cross_analysis, build_features
from futures_intelligence.import_collector import HEADERS, build_snapshot
from market_data.store import Candle, CandleStore, INTERVAL_MS, read_window
from pipeline.values import identity


class AnalyticsTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.counter = 0
        self.step = INTERVAL_MS["15m"]

    def path(self, suffix):
        self.counter += 1
        return Path(self.directory.name, str(self.counter)+suffix)

    def window(self, prices, *, slots=None, availability=None, as_of_ms=None, ranges=None):
        slots = list(range(len(prices))) if slots is None else slots
        availability = availability or {}
        ranges = ranges or {}
        path = self.path(".sqlite3")
        store = CandleStore(path)
        store.insert([Candle("15m", slot*self.step, str(price), str(ranges.get(slot, (price, price))[0]),
                             str(ranges.get(slot, (price, price))[1]), str(price), "1",
                             availability.get(slot, (slot+1)*self.step)) for slot, price in zip(slots, prices)])
        return read_window(path, "BTCUSDT", "15m", 0, (max(slots)+1)*self.step, as_of_ms)

    def csv(self, stream, rows):
        path = self.path(".csv")
        with path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=HEADERS[stream].split(","))
            writer.writeheader()
            writer.writerows(rows)
        return path

    def snapshot(self, closed, net="1", *, funding=None, published=None, event=None, gaps=False, missing=False):
        end = closed+CROSS_ANALYSIS_DELAY_MS-1000
        event = closed+CROSS_ANALYSIS_DELAY_MS-2000 if event is None else event
        start = min(end-30_000, event-1000)
        published = end if published is None else published
        if missing:
            return build_snapshot(start, end, published)
        common = {"exchange": "binance", "market": "futures", "timestamp_ms": str(event),
                  "datetime_utc": (datetime(1970, 1, 1, tzinfo=timezone.utc)+timedelta(milliseconds=event))
                                  .isoformat(timespec="milliseconds").replace("+00:00", "Z"), "symbol": "btcusdt"}
        side = "buy" if Decimal(net) > 0 else "sell"
        rows = [{**common, "datatype": "trades", "trade_id": "1", "side": side, "price": "1",
                 "quantity": str(abs(Decimal(net))), "is_buyer_maker": "0" if side == "buy" else "1",
                 "first_update_id": "1", "last_update_id": "1"}]
        if gaps:
            rows.append({**rows[0], "trade_id": "3"})
        inputs = {"trades": self.csv("trades", rows)}
        if funding is not None:
            inputs["funding"] = self.csv("funding", [{**common, "datatype": "funding_rates", "funding_rate": funding,
                                                       "next_funding_time": str(end+28_800_000)}])
        return build_snapshot(start, end, published, **inputs)

    def test_feature_warmup_population_volatility_and_fixed_version(self):
        window = self.window(list(range(1, 22)))
        result = build_features(window)
        rows = result["rows"]
        self.assertEqual(result["datasetVersion"], window["datasetVersion"])
        self.assertEqual(result["featureVersion"], "causal-v2")
        self.assertIsNone(rows[0]["return1"])
        self.assertIsNone(rows[18]["sma20"])
        self.assertEqual(rows[19]["sma20"], "10.5")
        self.assertIsNone(rows[19]["volatility20"])
        self.assertEqual(rows[20]["sma20"], "11.5")
        self.assertIsNone(rows[13]["rsi14"])
        self.assertEqual(rows[14]["rsi14"], "100")
        with localcontext() as context:
            context.prec = 100
            returns = [Decimal(1)/value for value in range(1, 21)]
            mean = sum(returns)/20
            expected = (sum((value-mean)**2 for value in returns)/20).sqrt()
            self.assertLess(abs(Decimal(rows[20]["volatility20"])-expected), Decimal("1e-98"))

    def test_wilder_rsi_seed_and_recursion_and_flat_series(self):
        prices = [100+(slot % 2) for slot in range(16)]
        rows = build_features(self.window(prices))["rows"]
        self.assertEqual(rows[14]["rsi14"], "50")
        with localcontext() as context:
            context.prec = 100
            expected = 100-100/(1+Decimal("7.5")/Decimal("6.5"))
            self.assertEqual(Decimal(rows[15]["rsi14"]), expected)
        flat = build_features(self.window([100]*21))["rows"][-1]
        self.assertEqual(flat["return1"], "0")
        self.assertEqual(flat["volatility20"], "0")
        self.assertIsNone(flat["rsi14"])
        self.assertEqual(flat["unavailableReasons"]["rsi14"], "ZERO_GAIN_AND_LOSS")

    def test_wilder_dmi_adx_known_trend_seed_and_reversal(self):
        prices = list(range(100, 128))+[126, 125, 124]
        ranges = {slot: (price+1, price-1) for slot, price in enumerate(prices)}
        rows = build_features(self.window(prices, ranges=ranges))["rows"]
        self.assertIsNone(rows[13]["plusDi14"])
        self.assertEqual(rows[14]["plusDi14"], "50")
        self.assertEqual(rows[14]["minusDi14"], "0")
        self.assertIsNone(rows[26]["adx14"])
        self.assertEqual(rows[27]["adx14"], "100")
        # Independent Wilder sums after reversal: TR=28, +DM=13, -DM=1.
        with localcontext() as context:
            context.prec = 100
            expected = {28: Decimal(4850)/49, 29: Decimal(33300)/343, 30: Decimal(453525)/4802}
            for slot, adx in expected.items():
                self.assertLess(abs(Decimal(rows[slot]["adx14"])-adx), Decimal("1e-95"))
            self.assertEqual(Decimal(rows[28]["plusDi14"]), Decimal(1300)/28)
            self.assertEqual(Decimal(rows[28]["minusDi14"]), Decimal(100)/28)
        falling = list(range(100, 72, -1))
        ranges = {slot: (price+1, price-1) for slot, price in enumerate(falling)}
        last = build_features(self.window(falling, ranges=ranges))["rows"][-1]
        self.assertEqual(last["plusDi14"], "0")
        self.assertEqual(last["minusDi14"], "50")
        self.assertEqual(last["adx14"], "100")

    def test_dmi_zero_range_directional_ties_and_consecutive_dx_warmup(self):
        flat = build_features(self.window([100]*30))["rows"][-1]
        for feature in ("plusDi14", "minusDi14", "adx14"):
            self.assertIsNone(flat[feature])
            self.assertEqual(flat["unavailableReasons"][feature], "ZERO_TRUE_RANGE")
        ranges = {slot: (101+slot, 99-slot) for slot in range(15)}
        tied = build_features(self.window([100]*15, ranges=ranges))["rows"][-1]
        self.assertEqual(tied["plusDi14"], "0")
        self.assertEqual(tied["minusDi14"], "0")
        self.assertIsNone(tied["adx14"])
        self.assertEqual(tied["unavailableReasons"]["adx14"], "ZERO_DIRECTIONAL_MOVEMENT")
        prices = [100]*20+list(range(101, 115))
        ranges = {slot: (price+1, price-1) for slot, price in enumerate(prices)}
        rows = build_features(self.window(prices, ranges=ranges))["rows"]
        self.assertEqual(rows[19]["unavailableReasons"]["adx14"], "ZERO_DIRECTIONAL_MOVEMENT")
        self.assertIsNone(rows[32]["adx14"])
        self.assertEqual(rows[32]["unavailableReasons"]["adx14"], "INSUFFICIENT_CONSECUTIVE_DX_VALUES")
        self.assertEqual(rows[33]["adx14"], "100")

    def test_adx_dmi_reset_at_gaps(self):
        slots = list(range(30))+list(range(31, 61))
        rows = build_features(self.window([100+slot for slot in slots], slots=slots))["rows"]
        self.assertEqual(rows[27]["adx14"], "100")
        self.assertTrue(all(rows[30][name] is None for name in ("plusDi14", "minusDi14", "adx14")))
        self.assertIsNone(rows[43]["plusDi14"])
        self.assertEqual(rows[44]["plusDi14"], "100")
        self.assertIsNone(rows[56]["adx14"])
        self.assertEqual(rows[57]["adx14"], "100")

    def test_gaps_reset_all_state_and_do_not_interpolate_rows(self):
        slots = list(range(21))+list(range(22, 43))
        result = build_features(self.window([100+slot for slot in slots], slots=slots))
        rows = result["rows"]
        self.assertFalse(result["coverage"]["complete"])
        self.assertEqual(len(rows), 42)
        self.assertEqual(rows[21]["candleOpenTimeMs"], 22*self.step)
        self.assertTrue(all(rows[21][name] is None for name in ("return1", "sma20", "volatility20", "rsi14")))
        self.assertIsNone(rows[40]["volatility20"])
        self.assertIsNotNone(rows[41]["volatility20"])

    def test_preserves_high_precision_and_actual_rsi_dependency_availability(self):
        before = "100.123456789012345678901234567890"
        after = "100.123456789012345678901234567891"
        rows = build_features(self.window([before, after]))["rows"]
        with localcontext() as context:
            context.prec = 100
            self.assertEqual(Decimal(rows[-1]["return1"]), Decimal(after)/Decimal(before)-1)
            self.assertGreater(Decimal(rows[-1]["return1"]), 0)
        late = 100*self.step
        window = self.window(list(range(100, 125)), availability={0: late}, as_of_ms=late)
        result = build_features(window)
        self.assertEqual(result["rows"][-1]["featureAvailableAtMs"], late)
        self.assertGreater(late, result["rows"][-1]["candleCloseTimeMs"])

    def test_revalidates_dataset_hash_closed_market_coverage_and_as_of(self):
        window = self.window([100, 101])
        for mutate in (
            lambda value: value.update(datasetVersion="sha256:"+"0"*64),
            lambda value: value["candles"][0].update(isClosed=False),
            lambda value: value["candles"][0].update(symbol="ETHUSDT"),
            lambda value: value["coverage"].update(returned=0),
            lambda value: value.update(asOfMs=0),
            lambda value: value.pop("asOfMs"),
            lambda value: value["candles"].reverse(),
        ):
            changed = copy.deepcopy(window)
            mutate(changed)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                build_features(changed)
        empty = copy.deepcopy(window)
        empty["candles"] = []
        empty["coverage"] = {"expected": 2, "returned": 0, "complete": False,
                             "gaps": [{"startMs": 0, "endMs": 2*self.step}]}
        empty["datasetVersion"] = identity("sha256:", {key: empty[key] for key in
            ("exchange", "marketType", "symbol", "timeframe", "startMs", "endMs", "asOfMs", "candles")})
        self.assertEqual(build_features(empty)["rows"], [])

    def test_actual_csv_snapshots_join_with_independent_metric_sample_counts(self):
        window = self.window([100, 110, 132, "171.6"])
        reports = [self.snapshot((slot+1)*self.step, str(slot), funding=str(Decimal(slot)/1000)) for slot in (1, 2, 3)]
        result = build_cross_analysis(window, list(reversed(reports)), as_of_ms=4*self.step+CROSS_ANALYSIS_DELAY_MS)
        self.assertTrue(result["descriptiveOnly"])
        for name in ("return1VsNetTakerQuote", "return1VsFundingRate"):
            correlation = result["correlations"][name]
            self.assertEqual(correlation["value"], "1")
            self.assertEqual(correlation["sampleCount"], 3)
            self.assertIsNone(correlation["reason"])
        self.assertEqual(result["rows"][1]["snapshotId"], reports[0]["snapshotId"])
        self.assertEqual(result["rows"][1]["snapshotQuality"], "OBSERVED_ONLY")
        missing = self.snapshot(4*self.step, "3")
        partial = build_cross_analysis(window, reports[:2]+[missing], as_of_ms=4*self.step+CROSS_ANALYSIS_DELAY_MS)
        self.assertEqual(partial["rows"][-1]["joinReason"], "MATCHED_OBSERVED_ONLY")
        self.assertIsNone(partial["rows"][-1]["fundingRate"])
        self.assertEqual(partial["rows"][-1]["metricReasons"]["fundingRate"], "FUNDING_MISSING")
        self.assertEqual(partial["correlations"]["return1VsFundingRate"]["sampleCount"], 2)
        self.assertEqual(partial["correlations"]["return1VsFundingRate"]["reason"], "INSUFFICIENT_SAMPLES")

    def test_late_publication_and_backfilled_features_are_not_historical_knowledge(self):
        window = self.window([100, 110, 132])
        late = self.snapshot(2*self.step, published=2*self.step+CROSS_ANALYSIS_DELAY_MS+1)
        result = build_cross_analysis(window, [late], as_of_ms=4*self.step)
        self.assertEqual(result["rows"][1]["joinReason"], "SNAPSHOT_NOT_YET_AVAILABLE")
        self.assertIsNone(result["rows"][1]["netTakerQuote"])
        self.assertEqual(result["rows"][2]["joinReason"], "STALE_SNAPSHOT")
        backfilled = self.window([100, 110], availability={0: 3*self.step}, as_of_ms=3*self.step)
        result = build_cross_analysis(backfilled, [self.snapshot(2*self.step)])
        self.assertEqual(result["rows"][-1]["netTakerQuote"], "1")
        self.assertFalse(result["rows"][-1]["pointInTimeEligible"])
        self.assertEqual(result["rows"][-1]["analysisReason"], "FEATURE_NOT_AVAILABLE_AT_ANALYSIS_TIME")
        self.assertEqual(result["correlations"]["return1VsNetTakerQuote"]["sampleCount"], 0)

    def test_fixed_analysis_clock_accepts_normal_observation_and_marks_pending(self):
        closed = 2*self.step
        analysis = closed+CROSS_ANALYSIS_DELAY_MS
        window = self.window([100, 110], availability={0: self.step+10, 1: closed+10})
        report = self.snapshot(closed, event=closed)
        result = build_cross_analysis(window, [report], as_of_ms=analysis)
        row = result["rows"][-1]
        self.assertEqual(result["alignmentDelayMs"], 60_000)
        self.assertIn("not predictions", result["descriptiveNotPrediction"])
        self.assertEqual(row["analysisAtMs"], analysis)
        self.assertTrue(row["pointInTimeEligible"])
        self.assertEqual(row["joinReason"], "MATCHED_OBSERVED_ONLY")
        pending = build_cross_analysis(window, [report], as_of_ms=analysis-1)["rows"][-1]
        self.assertEqual(pending["analysisReason"], "ANALYSIS_TIME_NOT_REACHED")
        self.assertFalse(pending["pointInTimeEligible"])
        self.assertIsNone(pending["netTakerQuote"])
        # A later request cannot move the fixed clock forward to admit backfill.
        backfill = self.window([100, 110], availability={1: analysis+1})
        late = build_cross_analysis(backfill, [report], as_of_ms=analysis+1000)["rows"][-1]
        self.assertEqual(late["analysisAtMs"], analysis)
        self.assertEqual(late["analysisReason"], "FEATURE_NOT_AVAILABLE_AT_ANALYSIS_TIME")
        self.assertFalse(late["pointInTimeEligible"])

    def test_adx_funding_correlation_has_independent_warmup_sample_count(self):
        prices = list(range(100, 128))+[126, 125, 124]
        ranges = {slot: (price+1, price-1) for slot, price in enumerate(prices)}
        window = self.window(prices, ranges=ranges)
        reports = [self.snapshot((slot+1)*self.step, str(slot), funding=str(Decimal(slot-28)/1000))
                   for slot in range(26, 31)]
        result = build_cross_analysis(window, reports, as_of_ms=31*self.step+CROSS_ANALYSIS_DELAY_MS)
        correlation = result["correlations"]["adx14VsFundingRate"]
        self.assertEqual(correlation["sampleCount"], 4)
        self.assertIsNone(correlation["reason"])
        self.assertLess(Decimal(correlation["value"]), Decimal("-0.97"))
        self.assertEqual(result["correlations"]["return1VsFundingRate"]["sampleCount"], 5)

    def test_stale_events_id_gaps_missing_stream_and_latest_missing_metric(self):
        window = self.window([100, 110])
        closed = 2*self.step
        for report, reason in (
            (self.snapshot(closed, event=closed+CROSS_ANALYSIS_DELAY_MS-60_001), "STALE_TRADE_EVENTS"),
            (self.snapshot(closed, gaps=True), "TRADE_ID_GAPS"),
            (self.snapshot(closed, missing=True), "NO_OBSERVED_TRADES"),
        ):
            with self.subTest(reason=reason):
                row = build_cross_analysis(window, [report], as_of_ms=closed+CROSS_ANALYSIS_DELAY_MS)["rows"][-1]
                self.assertEqual(row["joinReason"], reason)
                self.assertIsNone(row["netTakerQuote"])
                self.assertFalse(row["pointInTimeEligible"])
        older = self.snapshot(closed, funding="0.001", published=closed+CROSS_ANALYSIS_DELAY_MS-500)
        newer = self.snapshot(closed, "2", published=closed+CROSS_ANALYSIS_DELAY_MS-100)
        row = build_cross_analysis(window, [newer, older], as_of_ms=closed+CROSS_ANALYSIS_DELAY_MS)["rows"][-1]
        self.assertEqual(row["snapshotId"], newer["snapshotId"])
        self.assertIsNone(row["fundingRate"])

    def test_constant_series_bounds_future_snapshots_and_tampering(self):
        window = self.window([100, 100, 100, 100])
        reports = [self.snapshot((slot+1)*self.step) for slot in (1, 2, 3)]
        result = build_cross_analysis(window, reports, as_of_ms=4*self.step+CROSS_ANALYSIS_DELAY_MS)
        correlation = result["correlations"]["return1VsNetTakerQuote"]
        self.assertIsNone(correlation["value"])
        self.assertEqual(correlation["sampleCount"], 3)
        self.assertEqual(correlation["reason"], "ZERO_VARIANCE")
        with self.assertRaises(ValueError):
            build_cross_analysis(window, reports, as_of_ms=0)
        with self.assertRaises(ValueError):
            build_cross_analysis(window, [reports[0]]*(MAX_SNAPSHOTS+1))
        changed = copy.deepcopy(reports[-1])
        changed["netTakerQuote"] = "2"
        with self.assertRaises(ValueError):
            build_cross_analysis(window, [changed])
        future = self.snapshot(4*self.step, published=5*self.step)
        with self.assertRaises(ValueError):
            build_cross_analysis(window, [future], as_of_ms=4*self.step)


if __name__ == "__main__":
    unittest.main()
