import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path

from market_data.initialize_sqlite import create_canonical_database
from market_data.store import INTERVAL_MS, read_window


class CanonicalDatabaseInitializationTest(unittest.TestCase):
    def test_creates_empty_canonical_schema_without_starting_feeder_or_ingesting(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".data" / "market-data.sqlite3"

            report = create_canonical_database(path)

            self.assertTrue(path.is_file())
            self.assertEqual(report["database"], str(path.resolve()))
            self.assertEqual(report["created"], True)
            self.assertEqual(report["candles"], 0)
            self.assertEqual(report["leases"], 0)
            with closing(sqlite3.connect(path)) as database:
                with database:
                    tables = {row[0] for row in database.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )}
                    self.assertEqual(tables, {"candles", "feeder_leases"})
                    self.assertEqual(database.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                    self.assertEqual(database.execute("SELECT COUNT(*) FROM candles").fetchone()[0], 0)
                    self.assertEqual(database.execute("SELECT COUNT(*) FROM feeder_leases").fetchone()[0], 0)
            result = read_window(path, "BTCUSDT", "15m", 0, INTERVAL_MS["15m"])
            self.assertFalse(result["coverage"]["complete"])
            self.assertEqual(result["coverage"]["returned"], 0)

    def test_refuses_to_overwrite_existing_file_without_changing_its_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "existing.sqlite3"
            path.write_bytes(b"preserve-existing-database")
            before = path.read_bytes()

            with self.assertRaises(FileExistsError):
                create_canonical_database(path)

            self.assertEqual(path.read_bytes(), before)

    def test_refuses_existing_directory_and_does_not_create_database_inside_it(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "already-a-directory"
            path.mkdir()

            with self.assertRaises(FileExistsError):
                create_canonical_database(path)

            self.assertTrue(path.is_dir())

    def test_failed_initialization_removes_only_the_new_database_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "new.sqlite3"
            sentinel = Path(directory) / "keep.txt"
            sentinel.write_text("keep", encoding="utf-8")

            with self.assertRaises((OSError, RuntimeError, sqlite3.Error, ValueError)):
                create_canonical_database(path, initializer=lambda _: (_ for _ in ()).throw(RuntimeError("injected")))

            self.assertFalse(path.exists())
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
