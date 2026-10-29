import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from futures_intelligence.import_collector import build_snapshot
from market_data import archive
from market_data.store import CandleStore, StoreUnavailable


class SnapshotArchiveTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "data.sqlite3"
        archive.init_archive(self.path)

    def snapshot(self, available=1200, end=1000, threshold="1000000"):
        return build_snapshot(end - 1000, end, available, large_trade_threshold=threshold)

    def test_snapshot_is_durable_idempotent_and_ordered_by_availability_then_id(self):
        snapshots = [self.snapshot(threshold="2"), self.snapshot(threshold="1"), self.snapshot(available=1300)]
        for snapshot in reversed(snapshots):
            self.assertTrue(archive.archive_snapshot(self.path, snapshot, 1500))
            self.assertFalse(archive.archive_snapshot(self.path, snapshot, 1500))
        archive.init_archive(self.path)
        self.assertEqual(archive.read_snapshots(self.path, 0, 1500, 1500),
                         sorted(snapshots, key=lambda row: (row["availableAtMs"], row["snapshotId"])))

    def test_queries_filter_first_observation_without_backdating(self):
        earlier, later = self.snapshot(available=1200), self.snapshot(available=1400)
        archive.archive_snapshot(self.path, earlier, 1500)
        archive.archive_snapshot(self.path, later, 1500)
        self.assertEqual(archive.read_snapshots(self.path, 0, 1500, 1300), [earlier])
        self.assertEqual(archive.read_snapshots(self.path, 1201, 1500, 1500), [later])
        self.assertEqual(archive.read_snapshots(self.path, 1400, 1400, 1400), [later])
        self.assertEqual(archive.read_snapshots(self.path, 1401, 1500, 1200), [])

    def test_reads_never_create_missing_database_or_schema(self):
        missing = self.path.parent / "missing.sqlite3"
        with self.assertRaises(StoreUnavailable):
            archive.read_snapshots(missing, 0, 1500, 1500)
        self.assertFalse(missing.exists())
        candles = self.path.parent / "candles-only.sqlite3"
        CandleStore(candles)
        with self.assertRaises(StoreUnavailable):
            archive.read_snapshots(candles, 0, 1500, 1500)
        with sqlite3.connect(candles) as connection:
            self.assertIsNone(connection.execute("SELECT name FROM sqlite_master WHERE name='intelligence_snapshots'").fetchone())

    def test_invalid_future_and_tampered_snapshots_are_not_inserted(self):
        sample = self.snapshot()
        for value in ({**sample, "netTakerQuote": "12"}, {**sample, "symbol": "ETHUSDT"}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                archive.archive_snapshot(self.path, value, 1500)
        with self.assertRaises(ValueError):
            archive.archive_snapshot(self.path, self.snapshot(available=1600), 1500)
        self.assertEqual(archive.read_snapshots(self.path, 0, 1500, 1500), [])

    def test_corrupt_stored_hash_or_metadata_is_not_served(self):
        sample = self.snapshot()
        archive.archive_snapshot(self.path, sample, 1500)
        with sqlite3.connect(self.path) as connection:
            connection.execute("UPDATE intelligence_snapshots SET document=?", (json.dumps({**sample, "symbol": "ETHUSDT"}),))
        with self.assertRaises(ValueError):
            archive.read_snapshots(self.path, 0, 1500, 1500)
        with sqlite3.connect(self.path) as connection:
            connection.execute("UPDATE intelligence_snapshots SET document=?, available_at_ms=1199", (json.dumps(sample),))
        with self.assertRaises(ValueError):
            archive.read_snapshots(self.path, 0, 1500, 1500)

    def test_conflicting_existing_id_cannot_be_silently_replaced(self):
        sample = self.snapshot()
        archive.archive_snapshot(self.path, sample, 1500)
        with sqlite3.connect(self.path) as connection:
            connection.execute("UPDATE intelligence_snapshots SET document='corrupt'")
        with self.assertRaises(ValueError):
            archive.archive_snapshot(self.path, sample, 1500)

    def test_single_snapshot_limit_is_checked_before_writing(self):
        sample = self.snapshot()
        sample["padding"] = "x" * 65536
        with self.assertRaises(ValueError):
            archive.archive_snapshot(self.path, sample, 1500)
        self.assertEqual(archive.read_snapshots(self.path, 0, 1500, 1500), [])

    def test_record_count_limit_is_checked_before_fetching_or_parsing_documents(self):
        with sqlite3.connect(self.path) as connection:
            connection.executemany("INSERT INTO intelligence_snapshots VALUES (?,?,?,?)",
                                   ((f"row-{index}", 1200, 1000, "not JSON") for index in range(10001)))
        with patch.object(archive.json, "loads", side_effect=AssertionError("Must not parse oversized query")):
            with self.assertRaises(ValueError):
                archive.read_snapshots(self.path, 0, 1500, 1500)

    def test_utf8_total_byte_limit_is_checked_before_parsing(self):
        document = "é" * 32768  # 64 KiB UTF-8, rather than 32 KiB codepoints.
        with sqlite3.connect(self.path) as connection:
            connection.executemany("INSERT INTO intelligence_snapshots VALUES (?,?,?,?)",
                                   ((f"row-{index}", 1200, 1000, document) for index in range(129)))
        with patch.object(archive.json, "loads", side_effect=AssertionError("Must not parse oversized query")):
            with self.assertRaises(ValueError):
                archive.read_snapshots(self.path, 0, 1500, 1500)

    def test_stored_oversized_document_is_rejected_before_parsing(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute("INSERT INTO intelligence_snapshots VALUES (?,?,?,?)", ("oversized", 1200, 1000, "x" * 65537))
        with patch.object(archive.json, "loads", side_effect=AssertionError("Must not parse oversized row")):
            with self.assertRaises(ValueError):
                archive.read_snapshots(self.path, 0, 1500, 1500)

    def test_query_timestamps_are_bounded_integers(self):
        for start, end, asof in ((True, 1500, 1500), (-1, 1500, 1500), (1501, 1500, 1500),
                                 (0, 1500, None), (0, 1500, 2**63)):
            with self.subTest(start=start, end=end, asof=asof), self.assertRaises(ValueError):
                archive.read_snapshots(self.path, start, end, asof)

    def test_deeply_nested_invalid_stored_json_is_a_validation_error(self):
        document = "[" * 1500 + "0" + "]" * 1500
        with sqlite3.connect(self.path) as connection:
            connection.execute("INSERT INTO intelligence_snapshots VALUES (?,?,?,?)", ("nested", 1200, 1000, document))
        with self.assertRaises(ValueError):
            archive.read_snapshots(self.path, 0, 1500, 1500)


if __name__ == "__main__":
    unittest.main()
