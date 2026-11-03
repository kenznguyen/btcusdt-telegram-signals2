"""Fail-closed T0 CI database isolation contracts."""
import tempfile
import unittest
from pathlib import Path

from ci.t0_test_isolation import TestIsolationError, validate_test_database_path


class T0TestIsolationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.db = self.root / "shadow.sqlite3"
        self.env = {
            "CI": "true",
            "T0_TEST_MODE": "1",
            "T0_TEST_ROOT": str(self.root),
            "T0_TEST_DB": str(self.db),
            "MARKET_DATA_DB": "",
            "T0_FEEDER_LEASE_DB": "",
            "PAPER_DB": "",
            "PAPER_TRADING_DB": "",
        }

    def check(self, path=None, env=None):
        selected = self.db if path is None else path
        return validate_test_database_path(selected, self.env if env is None else env)

    def test_iso_01_missing_test_mode_fails(self):
        env = dict(self.env, T0_TEST_MODE="")
        with self.assertRaises(TestIsolationError):
            self.check(env=env)

    def test_iso_02_invalid_test_mode_fails(self):
        env = dict(self.env, T0_TEST_MODE="yes")
        with self.assertRaises(TestIsolationError):
            self.check(env=env)

    def test_iso_03_missing_root_fails(self):
        env = dict(self.env, T0_TEST_ROOT="")
        with self.assertRaises(TestIsolationError):
            self.check(env=env)

    def test_iso_04_missing_root_directory_fails(self):
        env = dict(self.env, T0_TEST_ROOT=str(self.root / "missing"))
        with self.assertRaises(FileNotFoundError):
            self.check(env=env)

    def test_iso_05_root_file_fails(self):
        root_file = self.root / "not-a-directory"
        root_file.write_text("x", encoding="utf-8")
        env = dict(self.env, T0_TEST_ROOT=str(root_file))
        with self.assertRaises(TestIsolationError):
            self.check(env=env)

    def test_iso_06_missing_database_path_fails(self):
        with self.assertRaises(TestIsolationError):
            self.check(path="")

    def test_iso_07_database_inside_root_passes(self):
        self.assertEqual(self.check(), self.db)

    def test_iso_08_database_outside_root_fails(self):
        with self.assertRaises(TestIsolationError):
            self.check(path=self.root.parent / "outside.sqlite3")

    def test_iso_09_parent_traversal_fails(self):
        with self.assertRaises(TestIsolationError):
            self.check(path=self.root / ".." / "outside.sqlite3")

    def test_iso_10_symlink_escape_fails(self):
        outside = self.root.parent / (self.root.name + "-outside.sqlite3")
        link = self.root / "escape.sqlite3"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is unavailable")
        with self.assertRaises(TestIsolationError):
            self.check(path=link)

    def test_iso_11_nested_symlink_escape_fails(self):
        outside_dir = self.root.parent / (self.root.name + "-outside")
        outside_dir.mkdir()
        link = self.root / "nested"
        try:
            link.symlink_to(outside_dir, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is unavailable")
        with self.assertRaises(TestIsolationError):
            self.check(path=link / "db.sqlite3")

    def test_iso_12_configured_database_alias_outside_root_fails(self):
        env = dict(self.env, MARKET_DATA_DB=str(self.root.parent / "canonical.sqlite3"))
        with self.assertRaises(TestIsolationError):
            self.check(env=env)

    def test_iso_13_market_data_production_path_fails(self):
        env = dict(self.env, MARKET_DATA_DB="/var/lib/t0/canonical.sqlite3")
        with self.assertRaises(TestIsolationError):
            self.check(env=env)

    def test_iso_14_lease_production_path_fails(self):
        env = dict(self.env, T0_FEEDER_LEASE_DB="/var/lib/t0/canonical.sqlite3")
        with self.assertRaises(TestIsolationError):
            self.check(env=env)

    def test_iso_15_paper_database_production_paths_fail(self):
        for key in ("PAPER_DB", "PAPER_TRADING_DB"):
            with self.subTest(key=key):
                env = dict(self.env, **{key: "/var/lib/paper/paper.sqlite3"})
                with self.assertRaises(TestIsolationError):
                    self.check(env=env)

    def test_iso_16_sqlite_uri_outside_root_fails(self):
        uri = "file:" + str(self.root.parent / "outside.sqlite3") + "?mode=ro"
        with self.assertRaises(TestIsolationError):
            self.check(path=uri)


if __name__ == "__main__":
    unittest.main()
