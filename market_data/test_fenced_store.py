"""Concurrency test for lease takeover serialization through the Gateway."""
import tempfile
import threading
import unittest
from pathlib import Path

from market_data.feeder import LeaseStore
from market_data.store import Candle, CandleStore, INTERVAL_MS
from market_data.write_gateway import SQLiteWriteGateway

NOW = 1_800_000_000_000


class GatewayTakeoverSerializationTest(unittest.TestCase):
    def test_takeover_waits_until_gateway_batch_commits(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "canonical.sqlite3")
            store = CandleStore(path)
            leases = LeaseStore(path)
            lease = leases.acquire("worker-A", NOW, 60)
            started = threading.Event()
            done = threading.Event()
            results = []

            def takeover():
                started.set()
                results.append(leases.acquire("worker-B", NOW + 60_001, 60))
                done.set()

            calls = {"count": 0}

            def clock():
                calls["count"] += 1
                if calls["count"] == 1:
                    thread = threading.Thread(target=takeover)
                    thread.start()
                    self.assertTrue(started.wait(1))
                    self.assertFalse(done.wait(0.05))
                return NOW + calls["count"]

            gateway = SQLiteWriteGateway(
                store=store, lease_store=leases, owner_id="worker-A",
                generation_provider=lambda: lease.generation, clock=clock,
            )
            value = Candle(
                "15m", NOW, "100", "101", "99", "100.5", "1",
                NOW + INTERVAL_MS["15m"],
            )
            self.assertEqual(gateway.write_batch([value]), 1)
            self.assertTrue(done.wait(1))
            self.assertGreater(results[0].generation, lease.generation)


    def test_expiry_during_gateway_transaction_rolls_back_before_takeover(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "isolated-expiry.sqlite3")
            store = CandleStore(path)
            leases = LeaseStore(path)
            lease = leases.acquire("worker-A", NOW, 60)
            takeover_started = threading.Event()
            takeover_done = threading.Event()
            takeover_results = []

            def takeover():
                takeover_started.set()
                takeover_results.append(
                    leases.acquire("worker-B", NOW + 60_001, 60)
                )
                takeover_done.set()

            clock_calls = {"count": 0}
            takeover_thread = None

            def clock():
                nonlocal takeover_thread
                clock_calls["count"] += 1
                if clock_calls["count"] == 1:
                    takeover_thread = threading.Thread(target=takeover)
                    takeover_thread.start()
                    if not takeover_started.wait(1):
                        raise AssertionError("takeover thread did not start")
                    if takeover_done.wait(0.05):
                        raise AssertionError(
                            "lease takeover must wait while the Gateway transaction is open"
                        )
                    return NOW + 1
                if clock_calls["count"] == 2:
                    return NOW + 60_001
                raise AssertionError("unexpected Gateway clock read")

            gateway = SQLiteWriteGateway(
                store=store, lease_store=leases, owner_id="worker-A",
                generation_provider=lambda: lease.generation, clock=clock,
            )
            value = Candle(
                "15m", NOW, "100", "101", "99", "100.5", "1",
                NOW + INTERVAL_MS["15m"],
            )

            with self.assertRaisesRegex(PermissionError, "expired before commit"):
                gateway.write_batch([value])

            self.assertTrue(takeover_done.wait(1))
            takeover_thread.join(timeout=1)
            self.assertFalse(takeover_thread.is_alive())
            self.assertEqual(len(takeover_results), 1)
            replacement = takeover_results[0]
            self.assertIsNotNone(replacement)
            self.assertGreater(replacement.generation, lease.generation)

            rows = read_window(
                path, "BTCUSDT", "15m", NOW, NOW + INTERVAL_MS["15m"]
            )
            self.assertEqual(rows["candles"], [])
            self.assertTrue(leases.is_current(
                "worker-B", replacement.generation, NOW + 60_002
            ))
            self.assertFalse(leases.is_current(
                "worker-A", lease.generation, NOW + 60_002
            ))


if __name__ == "__main__":
    unittest.main(verbosity=2)
