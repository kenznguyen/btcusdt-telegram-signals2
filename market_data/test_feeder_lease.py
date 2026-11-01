"""P1.2 contract tests: durable singleton lease and fencing."""
import tempfile
import threading
import unittest
from pathlib import Path

from market_data.feeder import LeaseStore

NOW = 1_800_000_000_000


class LeaseContractTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = str(Path(self.temp.name) / "lease.sqlite3")
        self.store = LeaseStore(self.path, lease_name="binance-btcusdt-canonical")

    def test_only_one_process_can_hold_an_unexpired_lease(self):
        first = self.store.acquire("process-A", now_ms=NOW, ttl_seconds=60)
        second = self.store.acquire("process-B", now_ms=NOW + 1_000, ttl_seconds=60)
        self.assertIsNotNone(first)
        self.assertIsNone(second)

    def test_two_store_instances_cannot_both_win_the_same_lease(self):
        stores = [self.store, LeaseStore(
            self.path, lease_name="binance-btcusdt-canonical")]
        barrier = threading.Barrier(2)
        results = []
        errors = []

        def acquire(index):
            try:
                barrier.wait()
                results.append(stores[index].acquire(
                    f"process-{index}", now_ms=NOW, ttl_seconds=60))
            except Exception as error:
                errors.append(error)

        threads = [threading.Thread(target=acquire, args=(i,)) for i in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)

        self.assertEqual(errors, [])
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(sum(result is not None for result in results), 1)

    def test_expired_lease_takeover_increments_fencing_generation(self):
        first = self.store.acquire("process-A", now_ms=NOW, ttl_seconds=60)
        second = self.store.acquire("process-B", now_ms=NOW + 60_001, ttl_seconds=60)
        self.assertGreater(second.generation, first.generation)

    def test_old_owner_cannot_renew_or_release_new_lease(self):
        old = self.store.acquire("process-A", now_ms=NOW, ttl_seconds=60)
        new = self.store.acquire("process-B", now_ms=NOW + 60_001, ttl_seconds=60)
        self.assertFalse(self.store.heartbeat(
            "process-A", old.generation, now_ms=NOW + 61_000, ttl_seconds=60))
        self.assertFalse(self.store.release("process-A", old.generation))
        self.assertTrue(self.store.is_current(
            "process-B", new.generation, now_ms=NOW + 61_000))

    def test_heartbeat_requires_matching_owner_and_generation(self):
        lease = self.store.acquire("process-A", now_ms=NOW, ttl_seconds=60)
        self.assertFalse(self.store.heartbeat(
            "process-A", lease.generation + 1, now_ms=NOW + 15_000, ttl_seconds=60))
        self.assertTrue(self.store.heartbeat(
            "process-A", lease.generation, now_ms=NOW + 15_000, ttl_seconds=60))

    def test_expired_owner_cannot_authorize_a_write(self):
        lease = self.store.acquire("process-A", now_ms=NOW, ttl_seconds=60)
        self.assertFalse(self.store.authorize_write(
            "process-A", lease.generation, now_ms=NOW + 60_001))

    def test_fencing_rejects_stale_writer_after_takeover(self):
        old = self.store.acquire("process-A", now_ms=NOW, ttl_seconds=60)
        new = self.store.acquire("process-B", now_ms=NOW + 60_001, ttl_seconds=60)
        self.assertFalse(self.store.authorize_write(
            "process-A", old.generation, now_ms=NOW + 60_002))
        self.assertTrue(self.store.authorize_write(
            "process-B", new.generation, now_ms=NOW + 60_002))


if __name__ == "__main__":
    unittest.main()
