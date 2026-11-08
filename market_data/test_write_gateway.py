"""Behavioral tests for the canonical T0 write gateways."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from market_data.feeder import LeaseStore
from market_data.store import Candle, CandleStore, INTERVAL_MS, read_window
from market_data.write_gateway import ShadowWriteGateway, SQLiteWriteGateway

NOW = 1_800_000_000_000


def candle(open_time_ms=NOW, high="101"):
    return Candle(
        timeframe="15m", open_time_ms=open_time_ms,
        open="100", high=high, low="99", close="100.5",
        volume="1", available_at_ms=open_time_ms + INTERVAL_MS["15m"],
    )


class SQLiteWriteGatewayTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = str(Path(self.temp.name) / "canonical.sqlite3")
        self.store = CandleStore(self.path)
        self.leases = LeaseStore(self.path)
        self.lease = self.leases.acquire("worker-A", NOW, 60)
        self.clock_values = iter((NOW + 1, NOW + 2))
        self.gateway = SQLiteWriteGateway(
            store=self.store,
            lease_store=self.leases,
            owner_id="worker-A",
            generation_provider=lambda: self.lease.generation,
            clock=lambda: next(self.clock_values),
        )

    def test_current_generation_commits_batch(self):
        self.assertEqual(self.gateway.write_batch([candle()]), 1)
        result = read_window(self.path, "BTCUSDT", "15m", NOW, NOW + INTERVAL_MS["15m"])
        self.assertEqual(result["coverage"]["returned"], 1)

    def test_stale_generation_is_rejected(self):
        self.leases.acquire("worker-B", NOW + 60_001, 60)
        with self.assertRaisesRegex(PermissionError, "lease is not current"):
            self.gateway.write_batch([candle()])
        result = read_window(self.path, "BTCUSDT", "15m", NOW, NOW + INTERVAL_MS["15m"])
        self.assertEqual(result["candles"], [])

    def test_lease_expiry_before_commit_rolls_back_batch(self):
        clock_values = iter((NOW + 1, NOW + 60_001))
        self.gateway.clock = lambda: next(clock_values)
        with self.assertRaisesRegex(PermissionError, "expired before commit"):
            self.gateway.write_batch([candle()])
        result = read_window(self.path, "BTCUSDT", "15m", NOW, NOW + INTERVAL_MS["15m"])
        self.assertEqual(result["candles"], [])

    def test_conflict_rolls_back_all_new_rows(self):
        self.gateway.write_batch([candle()])
        self.gateway.clock = lambda: NOW + 3
        conflicting = candle(high="102")
        with self.assertRaisesRegex(ValueError, "Conflicting closed candle"):
            self.gateway.write_batch([candle(NOW + INTERVAL_MS["15m"]), conflicting])
        result = read_window(
            self.path, "BTCUSDT", "15m", NOW,
            NOW + 2 * INTERVAL_MS["15m"],
        )
        self.assertEqual(result["coverage"]["returned"], 1)

    def test_committed_batch_survives_writer_process_crash_and_restart(self):
        import os
        import subprocess
        import sys
        script = r"""
import os, sys
from market_data.feeder import LeaseStore
from market_data.store import Candle, CandleStore, INTERVAL_MS
from market_data.write_gateway import SQLiteWriteGateway
path, generation = sys.argv[1], int(sys.argv[2])
store = CandleStore(path)
leases = LeaseStore(path)
gateway = SQLiteWriteGateway(
    store=store, lease_store=leases, owner_id="worker-A",
    generation_provider=lambda: generation, clock=lambda: 1_800_000_000_001,
)
gateway.write_batch([Candle(
    timeframe="15m", open_time_ms=1_800_000_000_000,
    open="100", high="101", low="99", close="100.5",
    volume="1", available_at_ms=1_800_000_900_000,
)])
os._exit(0)
"""
        result = subprocess.run(
            [sys.executable, "-c", script, self.path, str(self.lease.generation)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        persisted = read_window(
            self.path, "BTCUSDT", "15m", NOW, NOW + INTERVAL_MS["15m"],
        )
        self.assertEqual(persisted["coverage"]["returned"], 1)

        restarted = SQLiteWriteGateway(
            store=self.store, lease_store=self.leases, owner_id="worker-A",
            generation_provider=lambda: self.lease.generation,
            clock=lambda: NOW + 3,
        )
        self.assertEqual(
            restarted.write_batch([candle(NOW + INTERVAL_MS["15m"])]), 1,
        )
        after_restart = read_window(
            self.path, "BTCUSDT", "15m", NOW,
            NOW + 2 * INTERVAL_MS["15m"],
        )
        self.assertEqual(after_restart["coverage"]["returned"], 2)

    def test_gateway_rejects_separate_lease_database(self):
        other_path = str(Path(self.temp.name) / "other.sqlite3")
        other_lease = LeaseStore(other_path)
        with self.assertRaisesRegex(ValueError, "same SQLite database"):
            SQLiteWriteGateway(
                store=self.store, lease_store=other_lease,
                owner_id="worker-A", generation_provider=lambda: 1,
                clock=lambda: NOW,
            )

    def test_gateway_rejects_existing_database_without_canonical_schema(self):
        empty = Path(self.temp.name) / "empty.sqlite3"
        sqlite3.connect(empty).close()
        fake_store = type("StoreRef", (), {"path": empty})()
        fake_lease = type("LeaseRef", (), {
            "db_path": str(empty),
            "lease_name": "binance-btcusdt-canonical",
        })()

        with self.assertRaisesRegex(ValueError, "canonical SQLite schema"):
            SQLiteWriteGateway(
                store=fake_store, lease_store=fake_lease,
                owner_id="worker-A", generation_provider=lambda: 1,
                clock=lambda: NOW,
            )

        connection = sqlite3.connect(empty)
        try:
            tables = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        finally:
            connection.close()
        self.assertEqual(tables, [])

    def test_gateway_rejects_missing_database_without_creating_it(self):
        missing = Path(self.temp.name) / "missing.sqlite3"
        fake_store = type("StoreRef", (), {"path": missing})()
        fake_lease = type("LeaseRef", (), {
            "db_path": str(missing),
            "lease_name": "binance-btcusdt-canonical",
        })()
        with self.assertRaisesRegex(FileNotFoundError, "must already exist"):
            SQLiteWriteGateway(
                store=fake_store, lease_store=fake_lease,
                owner_id="worker-A", generation_provider=lambda: 1,
                clock=lambda: NOW,
            )
        self.assertFalse(missing.exists())


    def test_wal_keeper_preserves_sidecars_across_short_lived_writer_and_heartbeat(self):
        from market_data.write_gateway import SQLiteWalKeeper

        keeper = SQLiteWalKeeper(self.path)
        self.assertTrue(keeper.open())
        wal_path = Path(self.path + "-wal")
        shm_path = Path(self.path + "-shm")
        self.assertTrue(wal_path.is_file())
        self.assertTrue(shm_path.is_file())

        self.assertEqual(self.gateway.write_batch([candle()]), 1)
        self.assertTrue(self.leases.heartbeat(
            "worker-A", self.lease.generation, now_ms=NOW + 3, ttl_seconds=60,
        ))
        self.assertTrue(wal_path.is_file())
        self.assertTrue(shm_path.is_file())
        result = read_window(
            self.path, "BTCUSDT", "15m", NOW, NOW + INTERVAL_MS["15m"],
        )
        self.assertEqual(result["coverage"]["returned"], 1)

        self.assertTrue(keeper.close())
        self.assertFalse(keeper.is_open)
        self.assertFalse(wal_path.exists())
        self.assertFalse(shm_path.exists())

    def test_wal_keeper_fails_closed_for_missing_database(self):
        from market_data.write_gateway import SQLiteWalKeeper

        missing = Path(self.temp.name) / "not-created.sqlite3"
        with self.assertRaisesRegex(FileNotFoundError, "must already exist"):
            SQLiteWalKeeper(missing)
        self.assertFalse(missing.exists())


class ShadowWriteGatewayTest(unittest.TestCase):
    def test_shadow_gateway_counts_without_creating_a_database(self):
        gateway = ShadowWriteGateway()
        self.assertTrue(gateway.shadow_only)
        self.assertEqual(gateway.write_batch([candle(), candle(NOW + INTERVAL_MS["15m"])]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
