"""P5.4.30 fixture-only Scheduler -> Gateway contract tests.

These tests compose build_runtime without starting FeederRuntime, touching a
database, connecting to an exchange, or enabling any production writer.
"""
import unittest
from unittest.mock import Mock, patch

from market_data.feeder import FeederConfig
from market_data.feeder_service import build_runtime
from market_data.gateway import LeaseFence, T0WriteGateway
from market_data.store import INTERVAL_MS

INITIAL_NOW = 1_800_000_000_000


class SchedulerGatewayContractTest(unittest.TestCase):
    def _build_runtime(self, *, heartbeat=True):
        interval = INTERVAL_MS["15m"]
        initial_boundary = INITIAL_NOW - (INITIAL_NOW % interval)
        lease_now = [INITIAL_NOW]
        observation_now = [INITIAL_NOW + 123]
        gateway = T0WriteGateway("/fixture-only/not-created/canonical.sqlite3")
        exchange, store, lease_store = Mock(), Mock(), Mock()
        lease_store.heartbeat.return_value = heartbeat

        def lease_clock():
            return lease_now[0]

        def observation_clock():
            return observation_now[0]

        runtime = build_runtime(
            config=FeederConfig(timeframes=("15m",)),
            owner_id="p5-4-30-scheduler-fixture",
            exchange=exchange,
            store=store,
            gateway=gateway,
            lease_store=lease_store,
            lease_clock=lease_clock,
            observation_clock=observation_clock,
        )
        runtime.lease_generation = 42
        lease_now[0] = initial_boundary + interval + 5_000
        return (
            runtime, gateway, exchange, store, lease_store,
            lease_clock, observation_clock, initial_boundary, interval,
        )

    def test_scheduler_callback_routes_through_injected_gateway_and_current_fence(self):
        (
            runtime, gateway, exchange, _store, lease_store,
            lease_clock, observation_clock, initial_boundary, interval,
        ) = self._build_runtime()

        with patch(
            "market_data.feeder_service.sync_window", return_value=7
        ) as sync_window:
            completed = runtime.scheduler.run_due()

        self.assertEqual(completed, {"15m": 7})
        self.assertEqual(
            sync_window.call_args.args,
            (exchange, "15m", initial_boundary, initial_boundary + interval),
        )
        kwargs = sync_window.call_args.kwargs
        self.assertIs(kwargs["gateway"], gateway)
        self.assertEqual(
            kwargs["lease_token"],
            LeaseFence(
                "binance-btcusdt-canonical",
                "p5-4-30-scheduler-fixture",
                42,
            ),
        )
        self.assertIs(kwargs["now_ms"], observation_clock)
        self.assertIs(kwargs["lease_clock"], lease_clock)
        lease_store.heartbeat.assert_called_once_with(
            "p5-4-30-scheduler-fixture",
            42,
            now_ms=lease_clock(),
            ttl_seconds=60,
        )
        self.assertEqual(
            runtime.scheduler.last_completed_end_ms["15m"],
            initial_boundary + interval,
        )

    def test_scheduler_callback_fails_closed_when_lease_heartbeat_is_rejected(self):
        (
            runtime, _gateway, _exchange, _store, lease_store,
            lease_clock, _observation_clock, initial_boundary, _interval,
        ) = self._build_runtime(heartbeat=False)

        with patch(
            "market_data.feeder_service.sync_window"
        ) as sync_window:
            with self.assertRaises(Exception) as raised:
                runtime.scheduler.run_due()

        self.assertEqual(type(raised.exception).__name__, "SchedulerExecutionError")
        self.assertIn("15m", raised.exception.failures)
        self.assertIsInstance(raised.exception.failures["15m"], PermissionError)
        sync_window.assert_not_called()
        lease_store.heartbeat.assert_called_once_with(
            "p5-4-30-scheduler-fixture",
            42,
            now_ms=lease_clock(),
            ttl_seconds=60,
        )
        self.assertEqual(
            runtime.scheduler.last_completed_end_ms["15m"], initial_boundary
        )
        self.assertEqual(runtime.scheduler.running_timeframes, frozenset())


if __name__ == "__main__":
    unittest.main()
