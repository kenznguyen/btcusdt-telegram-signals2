"""Atomic SQLite lease fencing contracts for canonical candle writes."""
import tempfile
import unittest
from pathlib import Path

from market_data.feeder import LeaseStore
from market_data.store import Candle, CandleStore, INTERVAL_MS, read_window
from market_data.sync import sync_window


NOW = 1_800_000_000_000
STEP = INTERVAL_MS["15m"]
SYMBOL = "BTC/USDT:USDT"


def candle(slot=0):
    return Candle(
        timeframe="15m",
        open_time_ms=NOW + slot * STEP,
        open="100",
        high="102",
        low="99",
        close="101",
        volume="5",
        available_at_ms=NOW + (slot + 1) * STEP + 100,
    )


class Exchange:
    id = "binanceusdm"

    def __init__(self, rows):
        self.rows = rows
        self.market = {
            "symbol": SYMBOL, "id": "BTCUSDT", "base": "BTC", "quote": "USDT",
            "settle": "USDT", "active": True, "swap": True,
            "linear": True, "spot": False,
        }

    def load_markets(self):
        return {SYMBOL: self.market}

    def fetch_time(self):
        return NOW + 10 * STEP

    def fetch_ohlcv(self, *args, **kwargs):
        return self.rows


def row(slot=0):
    return [NOW + slot * STEP, 100, 102, 99, 101, 5]


class AtomicWriteFencingTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "canonical.sqlite3"
        self.candles = CandleStore(self.path)
        self.leases = LeaseStore(str(self.path))
        self.lease = self.leases.acquire("writer-A", now_ms=NOW, ttl_seconds=60)

    def read(self, count=2):
        return read_window(self.path, "BTCUSDT", "15m", NOW, NOW + count * STEP)

    def test_current_generation_can_commit_candles_with_lease_check(self):
        inserted = self.candles.insert_fenced(
            [candle()],
            owner="writer-A",
            generation=self.lease.generation,
            now_ms=lambda: NOW + 1,
        )
        self.assertEqual(inserted, 1)
        self.assertEqual(self.read(1)["coverage"]["returned"], 1)

    def test_stale_generation_is_rejected_without_writing_any_candle(self):
        replacement = self.leases.acquire(
            "writer-B", now_ms=NOW + 60_001, ttl_seconds=60
        )
        with self.assertRaises(PermissionError):
            self.candles.insert_fenced(
                [candle()],
                owner="writer-A",
                generation=self.lease.generation,
                now_ms=lambda: NOW + 60_002,
            )
        self.assertEqual(self.read(1)["candles"], [])
        self.assertTrue(self.leases.is_current(
            replacement.owner, replacement.generation, NOW + 60_002
        ))

    def test_expired_lease_is_rejected_even_when_generation_matches(self):
        with self.assertRaises(PermissionError):
            self.candles.insert_fenced(
                [candle()],
                owner="writer-A",
                generation=self.lease.generation,
                now_ms=lambda: NOW + 60_000,
            )
        self.assertEqual(self.read(1)["candles"], [])

    def test_lease_validation_and_batch_insert_share_one_atomic_transaction(self):
        with self.assertRaises(PermissionError):
            self.candles.insert_fenced(
                [candle(0), candle(1)],
                owner="writer-A",
                generation=self.lease.generation + 1,
                now_ms=lambda: NOW + 1,
            )
        self.assertEqual(self.read(2)["candles"], [])

    def test_sync_window_requires_fenced_store_write_when_fence_is_supplied(self):
        fence = {
            "owner": "writer-A",
            "generation": self.lease.generation,
            "now_ms": lambda: NOW + 2,
        }
        inserted = sync_window(
            Exchange([row()]),
            self.candles,
            "15m",
            NOW,
            NOW + STEP,
            now_ms=lambda: NOW + 2 * STEP,
            write_fence=fence,
        )
        self.assertEqual(inserted, 1)
        self.assertEqual(self.read(1)["coverage"]["returned"], 1)

    def test_missing_lease_record_fails_closed(self):
        with self.assertRaises(PermissionError):
            self.candles.insert_fenced(
                [candle()],
                owner="unknown-writer",
                generation=1,
                now_ms=lambda: NOW + 1,
            )
        self.assertEqual(self.read(1)["candles"], [])

    def test_lease_expiring_during_batch_rolls_back_all_candles(self):
        clock_values = iter((NOW + 1, NOW + 60_000))
        with self.assertRaises(PermissionError):
            self.candles.insert_fenced(
                [candle(0), candle(1)],
                owner="writer-A",
                generation=self.lease.generation,
                now_ms=lambda: next(clock_values),
            )
        self.assertEqual(self.read(2)["candles"], [])


    def test_lease_takeover_waits_for_inflight_canonical_write_transaction(self):
        import threading
        from unittest.mock import patch

        writer_entered = threading.Event()
        allow_writer_commit = threading.Event()
        takeover_started = threading.Event()
        takeover_finished = threading.Event()
        errors = []
        original_insert_batch = CandleStore._insert_batch

        def paused_insert_batch(connection, batch):
            writer_entered.set()
            if not allow_writer_commit.wait(2):
                raise TimeoutError("test did not release canonical writer")
            return original_insert_batch(connection, batch)

        def write_batch():
            try:
                with patch.object(CandleStore, "_insert_batch", side_effect=paused_insert_batch):
                    self.candles.insert_fenced(
                        [candle()], owner="writer-A", generation=self.lease.generation,
                        now_ms=lambda: NOW + 1,
                    )
            except Exception as error:
                errors.append(error)

        replacement = {}
        def take_over():
            takeover_started.set()
            try:
                replacement["lease"] = self.leases.acquire(
                    "writer-B", now_ms=NOW + 60_001, ttl_seconds=60
                )
            except Exception as error:
                errors.append(error)
            finally:
                takeover_finished.set()

        writer = threading.Thread(target=write_batch)
        writer.start()
        self.assertTrue(writer_entered.wait(1))
        takeover = threading.Thread(target=take_over)
        takeover.start()
        self.assertTrue(takeover_started.wait(1))
        self.assertFalse(takeover_finished.wait(0.05))

        allow_writer_commit.set()
        writer.join(2)
        takeover.join(2)

        self.assertFalse(writer.is_alive())
        self.assertFalse(takeover.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(self.read(1)["coverage"]["returned"], 1)
        self.assertEqual(replacement["lease"].generation, self.lease.generation + 1)

    def test_recovery_fills_multiple_gaps_through_fenced_canonical_sync(self):
        from market_data.feeder import RecoveryCoordinator

        self.candles.insert([candle(0), candle(2), candle(4)])

        class GapExchange(Exchange):
            def fetch_ohlcv(self, symbol, timeframe, since, limit, params):
                slot = (since - NOW) // STEP
                return [row(slot)] if slot in (1, 3) else []

        exchange = GapExchange([])
        fence = {
            "owner": "writer-A",
            "generation": self.lease.generation,
            "now_ms": lambda: NOW + 1,
        }
        coordinator = RecoveryCoordinator(
            sync_callback=lambda timeframe, start_ms, end_ms: sync_window(
                exchange, self.candles, timeframe, start_ms, end_ms,
                now_ms=lambda: NOW + 10 * STEP, write_fence=fence,
            ),
            coverage_reader=lambda timeframe, start_ms, end_ms: read_window(
                self.path, "BTCUSDT", timeframe, start_ms, end_ms
            ),
        )

        result = coordinator.recover("15m", NOW, NOW + 5 * STEP)

        self.assertTrue(result.complete)
        self.assertEqual(result.recovered_windows, (
            (NOW + STEP, NOW + 2 * STEP),
            (NOW + 3 * STEP, NOW + 4 * STEP),
        ))
        final = self.read(5)
        self.assertEqual(final["coverage"]["returned"], 5)
        self.assertTrue(final["coverage"]["complete"])


if __name__ == "__main__":
    unittest.main()
