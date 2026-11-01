"""P1.2 contract tests: graceful shutdown and restart recovery."""
import unittest
from unittest.mock import Mock

from market_data.feeder import FeederConfig, FeederRuntime

NOW = 1_800_000_000_000


class RuntimeLifecycleTest(unittest.TestCase):
    def test_stop_stops_scheduler_drains_work_then_releases_lease(self):
        events = []
        scheduler = Mock()
        scheduler.stop.side_effect = lambda: events.append("scheduler_stopped")
        scheduler.wait_for_idle.side_effect = lambda: events.append("work_drained")
        leases = Mock()
        leases.release.side_effect = lambda owner, generation: events.append("lease_released")
        runtime = FeederRuntime(
            config=FeederConfig(), scheduler=scheduler, lease_store=leases,
            owner_id="worker-A",
        )
        runtime.lease_generation = 4
        runtime.stop()
        self.assertEqual(events, ["scheduler_stopped", "work_drained", "lease_released"])
        leases.release.assert_called_once_with("worker-A", 4)

    def test_stop_is_idempotent(self):
        scheduler, leases = Mock(), Mock()
        runtime = FeederRuntime(
            config=FeederConfig(), scheduler=scheduler, lease_store=leases,
            owner_id="worker-A",
        )
        runtime.lease_generation = 4
        runtime.stop()
        runtime.stop()
        leases.release.assert_called_once_with("worker-A", 4)

    def test_start_acquires_lease_recovers_then_marks_ready(self):
        events = []
        scheduler, leases, recovery, health = Mock(), Mock(), Mock(), Mock()
        leases.acquire.side_effect = lambda *args, **kwargs: (
            events.append("lease_acquired") or Mock(generation=8)
        )
        recovery.recover_all.side_effect = lambda: (
            events.append("recovery_completed") or True
        )
        health.mark_ready.side_effect = lambda: events.append("ready")
        runtime = FeederRuntime(
            config=FeederConfig(), scheduler=scheduler, lease_store=leases,
            recovery=recovery, health=health, owner_id="worker-B",
            event_sink=events.append,
        )
        runtime.start(now_ms=NOW)
        self.assertLess(events.index("lease_acquired"), events.index("recovery_completed"))
        self.assertLess(events.index("recovery_completed"), events.index("ready"))
        scheduler.start.assert_called_once()

    def test_start_without_lease_does_not_recover_or_become_ready(self):
        scheduler, leases, recovery, health = Mock(), Mock(), Mock(), Mock()
        leases.acquire.return_value = None
        runtime = FeederRuntime(
            config=FeederConfig(), scheduler=scheduler, lease_store=leases,
            recovery=recovery, health=health, owner_id="worker-C",
        )
        runtime.start(now_ms=NOW)
        recovery.recover_all.assert_not_called()
        health.mark_ready.assert_not_called()
        scheduler.start.assert_not_called()

    def test_incomplete_restart_recovery_keeps_readiness_false(self):
        scheduler, leases, recovery, health = Mock(), Mock(), Mock(), Mock()
        leases.acquire.return_value = Mock(generation=9)
        recovery.recover_all.return_value = False
        runtime = FeederRuntime(
            config=FeederConfig(), scheduler=scheduler, lease_store=leases,
            recovery=recovery, health=health, owner_id="worker-D",
        )
        runtime.start(now_ms=NOW)
        health.mark_ready.assert_not_called()
        scheduler.start.assert_not_called()

    def test_recovery_exception_keeps_readiness_false_and_releases_lease(self):
        scheduler, leases, recovery, health = Mock(), Mock(), Mock(), Mock()
        leases.acquire.return_value = Mock(generation=10)
        recovery.recover_all.side_effect = OSError("storage unavailable")
        runtime = FeederRuntime(
            config=FeederConfig(), scheduler=scheduler, lease_store=leases,
            recovery=recovery, health=health, owner_id="worker-E",
        )
        with self.assertRaisesRegex(OSError, "storage unavailable"):
            runtime.start(now_ms=NOW)
        health.mark_ready.assert_not_called()
        scheduler.start.assert_not_called()
        leases.release.assert_called_once_with("worker-E", 10)

    def test_losing_lease_stops_scheduler_and_blocks_future_sync(self):
        scheduler, leases = Mock(), Mock()
        runtime = FeederRuntime(
            config=FeederConfig(), scheduler=scheduler, lease_store=leases,
            owner_id="worker-F",
        )
        runtime.lease_generation = 11
        runtime.on_lease_lost()
        scheduler.stop.assert_called_once()
        runtime.run_once()
        scheduler.run_due.assert_not_called()


if __name__ == "__main__":
    unittest.main()
