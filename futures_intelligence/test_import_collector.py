import copy
import csv
import hashlib
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from futures_intelligence.import_collector import build_snapshot, feed_quality, validate_snapshot, write_snapshot
from pipeline.values import identity


COMMON = ["exchange", "market", "datatype", "timestamp_ms", "datetime_utc", "symbol"]
HEADERS = {
    "trades": COMMON + ["trade_id", "side", "price", "quantity", "is_buyer_maker", "first_update_id", "last_update_id"],
    "funding_rates": COMMON + ["funding_rate", "next_funding_time"],
    "open_interest": COMMON + ["mark_price", "open_interest", "oi_value"],
    "liquidations": COMMON + ["side", "price", "quantity", "value"],
}


class IntelligenceImportTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.start = 1_700_000_000_000
        self.end = self.start + 300_000
        self.now = self.end + 100

    def row(self, datatype, offset=1000, **values):
        timestamp = self.start + offset
        return {"exchange": "binance", "market": "futures", "datatype": datatype,
                "symbol": "btcusdt", "timestamp_ms": str(timestamp),
                "datetime_utc": datetime.fromtimestamp(timestamp/1000, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                **values}

    def trade(self, trade_id=42, side="buy", **values):
        return self.row("trades", trade_id=str(trade_id), side=side, price="100", quantity="2",
                        is_buyer_maker="0" if side == "buy" else "1", first_update_id="100", last_update_id="101", **values)

    def csv(self, datatype, rows, name=None):
        path = Path(self.directory.name, name or datatype + ".csv")
        with path.open("w", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=HEADERS[datatype])
            writer.writeheader()
            writer.writerows(rows)
        return path

    def build(self, **inputs):
        return build_snapshot(self.start, self.end, self.now, **inputs)

    def test_imports_exact_headers_and_preserves_distinct_feed_meanings(self):
        buy = self.trade()
        sell = {**self.trade(43, "sell"), "price": "110", "quantity": "1"}
        trades = self.csv("trades", [buy, sell])
        funding = self.csv("funding_rates", [self.row("funding_rates", funding_rate="-0.0002", next_funding_time=str(self.end+28_800_000))])
        interest = self.csv("open_interest", [self.row("open_interest", mark_price="100", open_interest="10", oi_value="1000"),
                                                 self.row("open_interest", 2000, mark_price="100", open_interest="11", oi_value="1100")])
        liquidations = self.csv("liquidations", [self.row("liquidations", side="sell", price="100", quantity="2", value="200"),
                                                   self.row("liquidations", side="buy", price="110", quantity="3", value="330")])
        result = self.build(trades=trades, funding=funding, open_interest=interest, liquidations=liquidations, large_trade_threshold="150")
        self.assertEqual(result["takerBuyQuote"], "200")
        self.assertEqual(result["takerSellQuote"], "110")
        self.assertEqual(result["netTakerQuote"], "90")
        self.assertEqual(result["largeTradeQuote"], "200")
        self.assertEqual(result["fundingRate"], "-0.0002")
        self.assertEqual(result["openInterestBase"], "11")
        self.assertEqual(result["openInterestChangeBase"], "1")
        self.assertEqual(result["observedLiquidationSellQuote"], "200")
        self.assertEqual(result["observedLiquidationBuyQuote"], "330")
        self.assertEqual(result["availableAtMs"], self.now)
        self.assertTrue(all(not c["complete"] for c in result["coverage"].values()))
        self.assertEqual(validate_snapshot(result, self.now+10_000_000), result)

    def test_absent_empty_and_single_sample_never_become_fake_zeroes(self):
        missing = self.build()
        self.assertIsNone(missing["netTakerQuote"])
        self.assertIsNone(missing["observedLiquidationSellQuote"])
        self.assertEqual(missing["coverage"]["trades"]["status"], "MISSING")
        empty = self.build(trades=self.csv("trades", []))
        self.assertEqual(empty["coverage"]["trades"]["status"], "NO_ROWS")
        self.assertIsNone(empty["takerBuyQuote"])
        interest = self.csv("open_interest", [self.row("open_interest", mark_price="100", open_interest="10", oi_value="1000")])
        self.assertIsNone(self.build(open_interest=interest)["openInterestChangeBase"])

    def test_deduplicates_aggregate_ids_detects_conflicts_and_exposes_gaps(self):
        first, other = self.trade(42), self.trade(45)
        path = self.csv("trades", [first, other, first])
        result = self.build(trades=path)
        self.assertEqual(result["takerBuyQuote"], "400")
        self.assertEqual(result["coverage"]["trades"]["duplicateRows"], 1)
        self.assertEqual(result["coverage"]["trades"]["tradeIdGaps"], 2)
        self.assertEqual(feed_quality(result, self.now)[0]["integrityStatus"], "DUPLICATES_PRESENT")
        conflicting = self.csv("trades", [first, {**first, "quantity": "3"}], "conflict.csv")
        with self.assertRaises(ValueError):
            self.build(trades=conflicting)
        same_notional = self.csv("trades", [first, {**first, "price": "200", "quantity": "1"}], "same-quote.csv")
        with self.assertRaises(ValueError):
            self.build(trades=same_notional)

    def test_snapshot_pins_input_file_checksums_and_declares_unknown_continuity(self):
        path = self.csv("trades", [self.trade()])
        result = self.build(trades=path)
        provenance = result["inputFiles"]["trades"][0]
        self.assertEqual(provenance["name"], path.name)
        self.assertEqual(provenance["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(provenance["sizeBytes"], path.stat().st_size)
        self.assertEqual(provenance["rowsRead"], 1)
        self.assertEqual(provenance["selectedRows"], 1)
        self.assertEqual(result["collectorCommit"], "bc4f0ef633fbeee4a49defd72827f17162693805")
        self.assertEqual(result["coverage"]["trades"]["continuityStatus"], "UNVERIFIED")

    def test_rejects_capture_file_changed_while_its_snapshot_is_built(self):
        path = self.csv("trades", [self.trade()])
        from futures_intelligence import import_collector

        original_hash = import_collector._file_sha256

        def mutate_before_hash(source):
            with Path(source).open("a", encoding="utf-8") as output:
                output.write("\\n")
            return original_hash(source)

        with patch("futures_intelligence.import_collector._file_sha256", side_effect=mutate_before_hash):
            with self.assertRaisesRegex(ValueError, "changed during import"):
                self.build(trades=path)

    def test_trade_id_gaps_are_explicitly_a_continuity_warning(self):
        path = self.csv("trades", [self.trade(42), self.trade(45)])
        result = self.build(trades=path)
        self.assertEqual(result["coverage"]["trades"]["tradeIdGaps"], 2)
        self.assertEqual(result["coverage"]["trades"]["continuityStatus"], "GAPS_DETECTED")

    def test_freshness_uses_collector_cadence_and_never_infers_liquidation_disconnect(self):
        funding = self.csv("funding_rates", [self.row("funding_rates", funding_rate="0.0001", next_funding_time=str(self.end+28_800_000))])
        interest = self.csv("open_interest", [self.row("open_interest", mark_price="100", open_interest="10", oi_value="1000")])
        liquidations = self.csv("liquidations", [self.row("liquidations", side="sell", price="100", quantity="1", value="100")])
        snapshot = self.build(funding=funding, open_interest=interest, liquidations=liquidations)
        feeds = {feed["name"]: feed for feed in feed_quality(snapshot, self.end+1_500_000)}
        self.assertEqual(feeds["funding"]["freshness"], "STALE")
        self.assertEqual(feeds["openInterest"]["freshness"], "STALE")
        self.assertEqual(feeds["liquidations"]["freshness"], "UNVERIFIABLE")
        self.assertEqual(feeds["liquidations"]["integrityStatus"], "UNVERIFIABLE")
        self.assertEqual(feeds["liquidations"]["deduplicationStatus"], "NO_EVENT_ID")
        self.assertGreater(feeds["liquidations"]["ageMs"], 0)
        self.assertEqual(feeds["liquidations"]["continuityStatus"], "UNVERIFIED")

    def test_rejects_market_time_numeric_and_aggressor_inconsistencies(self):
        base = self.trade()
        mutations = [dict(exchange="other"), dict(market="spot"), dict(symbol="ethusdt"), dict(datatype="liquidations"),
                     dict(price="NaN"), dict(price="0"), dict(quantity="-1"), dict(is_buyer_maker="1"),
                     dict(datetime_utc="2023-11-14T22:13:21.001Z"), dict(last_update_id="99")]
        for index, fields in enumerate(mutations):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                self.build(trades=self.csv("trades", [{**base, **fields}], f"bad-{index}.csv"))
        with self.assertRaises(ValueError):
            build_snapshot(self.start, self.end, self.end-1)

    def test_window_is_half_open_and_all_selected_rows_are_bounded(self):
        before = self.row("trades", -1000, **{k: v for k, v in self.trade().items() if k not in COMMON})
        at_end = self.row("trades", 300_000, **{k: v for k, v in self.trade(44).items() if k not in COMMON})
        path = self.csv("trades", [before, self.trade(), at_end])
        result = self.build(trades=path)
        self.assertEqual(result["coverage"]["trades"]["rows"], 1)
        with patch("futures_intelligence.import_collector.MAX_ROWS", 1), self.assertRaises(ValueError):
            self.build(trades=path)

    def test_artifact_hash_semantics_and_atomic_replacement(self):
        result = self.build(trades=self.csv("trades", [self.trade()]))
        output = Path(self.directory.name, "nested", "intelligence.json")
        write_snapshot(output, result)
        self.assertEqual(json.loads(output.read_text()), result)
        original = output.read_bytes()
        bad = {**result, "netTakerQuote": "999"}
        with self.assertRaises(ValueError):
            write_snapshot(output, bad)
        self.assertEqual(output.read_bytes(), original)
        changed = copy.deepcopy(result)
        changed["netTakerQuote"] = "999"
        changed["snapshotId"] = identity("intelligence:", {k: v for k, v in changed.items() if k != "snapshotId"})
        with self.assertRaises(ValueError):
            validate_snapshot(changed, self.now)
        with self.assertRaises(ValueError):
            validate_snapshot(result, self.end)
        unsupported = copy.deepcopy(result)
        unsupported["coverage"]["trades"]["status"] = []
        unsupported["snapshotId"] = identity("intelligence:", {k: v for k, v in unsupported.items() if k != "snapshotId"})
        with self.assertRaises(ValueError):
            validate_snapshot(unsupported, self.now)


if __name__ == "__main__":
    unittest.main()
