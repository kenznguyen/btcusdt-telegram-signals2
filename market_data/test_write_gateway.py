"""Behavioral tests for the canonical T0 write gateways."""
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
        self.gateway.clock = lambda: next(iter((NOW + 1, NOW + 60_001)))
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

    def test_gateway_rejects_separate_lease_database(self):
        other_path = str(Path(self.temp.name) / "other.sqlite3")
        other_lease = LeaseStore(other_path)
        with self.assertRaisesRegex(ValueError, "same SQLite database"):
            SQLiteWriteGateway(
                store=self.store, lease_store=other_lease,
                owner_id="worker-A", generation_provider=lambda: 1,
                clock=lambda: NOW,
            )


class ShadowWriteGatewayTest(unittest.TestCase):
    def test_shadow_gateway_counts_without_creating_a_database(self):
        gateway = ShadowWriteGateway()
        self.assertTrue(gateway.shadow_only)
        self.assertEqual(gateway.write_batch([candle(), candle(NOW + INTERVAL_MS["15m"])]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
