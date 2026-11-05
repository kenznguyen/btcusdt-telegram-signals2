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


if __name__ == "__main__":
    unittest.main(verbosity=2)
