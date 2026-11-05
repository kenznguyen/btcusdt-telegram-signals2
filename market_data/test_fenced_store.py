"""Atomic SQLite fencing tests for canonical candle writes."""
import tempfile
import threading
import unittest
from pathlib import Path

from market_data.feeder import LeaseStore
from market_data.store import Candle, CandleStore, INTERVAL_MS, read_window

NOW = 1_800_000_000_000


def candle(open_time_ms=NOW):
    return Candle(
        timeframe="15m",
        open_time_ms=open_time_ms,
        open="100", high="101", low="99", close="100.5",
        volume="1", available_at_ms=open_time_ms + INTERVAL_MS["15m"],
    )


class FencedCandleStoreTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = str(Path(self.temp.name) / "canonical.sqlite3")
        self.store = CandleStore(self.path)
        self.leases = LeaseStore(self.path)

    def test_current_generation_can_commit_candle(self):
        lease = self.leases.acquire("worker-A", NOW, 60)
        inserted = self.store.insert_fenced(
            [candle()], owner="worker-A", generation=lease.generation,
            now_ms=lambda: NOW + 1,
        )
        self.assertEqual(inserted, 1)

    def test_expired_generation_is_rejected_inside_write_transaction(self):
        lease = self.leases.acquire("worker-A", NOW, 60)
        with self.assertRaisesRegex(PermissionError, "lease is not current"):
            self.store.insert_fenced(
                [candle()], owner="worker-A", generation=lease.generation,
                now_ms=lambda: NOW + 60_001,
            )
        self.assertEqual(read_window(self.path, "BTCUSDT", "15m", NOW, NOW + INTERVAL_MS["15m"])["candles"], [])

    def test_lease_takeover_waits_until_fenced_batch_commits(self):
        lease = self.leases.acquire("worker-A", NOW, 60)
        takeover_started = threading.Event()
        takeover_done = threading.Event()
        takeover_result = []

        def takeover():
            takeover_started.set()
            takeover_result.append(
                self.leases.acquire("worker-B", NOW + 60_001, 60)
            )
            takeover_done.set()

        takeover_thread = None

        def clock_during_write():
            nonlocal takeover_thread
            takeover_thread = threading.Thread(target=takeover)
            takeover_thread.start()
            self.assertTrue(takeover_started.wait(1))
            self.assertFalse(takeover_done.wait(0.05))
            return NOW + 1

        inserted = self.store.insert_fenced(
            [candle()], owner="worker-A", generation=lease.generation,
            now_ms=clock_during_write,
        )
        self.assertEqual(inserted, 1)
        self.assertTrue(takeover_done.wait(1))
        takeover_thread.join(1)
        self.assertFalse(takeover_thread.is_alive())
        self.assertGreater(takeover_result[0].generation, lease.generation)

    def test_lease_expiring_during_batch_is_rechecked_before_commit(self):
        lease = self.leases.acquire("worker-A", NOW, 60)
        clock_values = iter((NOW + 1, NOW + 60_001))
        with self.assertRaisesRegex(PermissionError, "expired before commit"):
            self.store.insert_fenced(
                [candle()], owner="worker-A", generation=lease.generation,
                now_ms=lambda: next(clock_values),
            )
        self.assertEqual(
            read_window(self.path, "BTCUSDT", "15m", NOW, NOW + INTERVAL_MS["15m"])["candles"],
            [],
        )

    def test_stale_generation_cannot_write_after_takeover(self):
        old = self.leases.acquire("worker-A", NOW, 60)
        new = self.leases.acquire("worker-B", NOW + 60_001, 60)
        self.assertGreater(new.generation, old.generation)
        with self.assertRaisesRegex(PermissionError, "lease is not current"):
            self.store.insert_fenced(
                [candle()], owner="worker-A", generation=old.generation,
                now_ms=lambda: NOW + 60_002,
            )
        inserted = self.store.insert_fenced(
            [candle()], owner="worker-B", generation=new.generation,
            now_ms=lambda: NOW + 60_003,
        )
        self.assertEqual(inserted, 1)

    def test_conflicting_candle_rolls_back_entire_fenced_batch(self):
        lease = self.leases.acquire("worker-A", NOW, 60)
        self.store.insert_fenced(
            [candle()], owner="worker-A", generation=lease.generation,
            now_ms=lambda: NOW + 1,
        )
        conflicting = Candle(
            timeframe="15m", open_time_ms=NOW,
            open="100", high="102", low="99", close="100.5",
            volume="1", available_at_ms=NOW + INTERVAL_MS["15m"],
        )
        with self.assertRaisesRegex(ValueError, "Conflicting closed candle"):
            self.store.insert_fenced(
                [candle(NOW + INTERVAL_MS["15m"]), conflicting],
                owner="worker-A", generation=lease.generation,
                now_ms=lambda: NOW + 2,
            )
        self.assertEqual(read_window(self.path, "BTCUSDT", "15m", NOW, NOW + 2 * INTERVAL_MS["15m"])["coverage"]["returned"], 1)


if __name__ == "__main__":
    unittest.main()
