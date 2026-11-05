"""Runtime compatibility contracts for PostgreSQL's DB-clock lease authority.

These RED contracts ensure FeederRuntime's legacy now_ms arguments never become
PostgreSQL lease authority. The adapter must delegate expiry decisions to
PostgresLeaseStore, which uses clock_timestamp().
"""
import unittest
from unittest.mock import Mock

from market_data.feeder_service import PostgresRuntimeLeaseAdapter


class PostgresRuntimeLeaseAdapterContractTest(unittest.TestCase):
    def setUp(self):
        self.backend = Mock()
        self.adapter = PostgresRuntimeLeaseAdapter(self.backend)

    def test_acquire_ignores_runtime_clock_and_delegates_ttl(self):
        lease = object()
        self.backend.acquire.return_value = lease

        result = self.adapter.acquire(
            "worker-a", now_ms=1, ttl_seconds=37
        )

        self.assertIs(result, lease)
        self.backend.acquire.assert_called_once_with("worker-a", ttl_seconds=37)

    def test_heartbeat_ignores_runtime_clock_and_delegates_generation(self):
        self.backend.heartbeat.return_value = True

        result = self.adapter.heartbeat(
            "worker-a", 9, now_ms=1, ttl_seconds=41
        )

        self.assertTrue(result)
        self.backend.heartbeat.assert_called_once_with(
            "worker-a", 9, ttl_seconds=41
        )

    def test_current_and_write_authorization_use_database_clock(self):
        self.backend.is_current.return_value = True

        self.assertTrue(self.adapter.is_current(
            "worker-a", 9, now_ms=1
        ))
        self.assertTrue(self.adapter.authorize_write(
            "worker-a", 9, now_ms=2
        ))
        self.assertEqual(self.backend.is_current.call_args_list, [
            unittest.mock.call("worker-a", 9),
            unittest.mock.call("worker-a", 9),
        ])

    def test_release_remains_bound_to_exact_owner_and_generation(self):
        self.backend.release.return_value = True

        self.assertTrue(self.adapter.release("worker-a", 9))
        self.backend.release.assert_called_once_with("worker-a", 9)
