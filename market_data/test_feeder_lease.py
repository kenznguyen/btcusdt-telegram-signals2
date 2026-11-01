"""P1.2 contract tests: durable singleton lease and fencing."""
import tempfile
import unittest
from pathlib import Path
from market_data.feeder import LeaseStore

NOW = 1_800_000_000_000


class LeaseContractTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = LeaseStore(str(Path(self.temp.name) / "lease.sqlite3"),
                                lease_name="binance-btcusdt-canonical")

    def test_only_one_process_can_hold_an_unexpired_lease(self):
        first = self.store.acquire("process-A", now_ms=NOW, ttl_seconds=60)
        second = self.store.acquire("process-B", now_ms=NOW + 1_000, ttl_seconds=60)
        self.assertIsNotNone(first)
        self.assertIsNone(second)

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

    def test_fencing_rejects_stale_writer_after_takeover(self):
        old = self.store.acquire("process-A", now_ms=NOW, ttl_seconds=60)
        new = self.store.acquire("process-B", now_ms=NOW + 60_001, ttl_seconds=60)
        self.assertFalse(self.store.authorize_write(
            "process-A", old.generation, now_ms=NOW + 60_002))
        self.assertTrue(self.store.authorize_write(
            "process-B", new.generation, now_ms=NOW + 60_002))


if __name__ == "__main__":
    unittest.main()
