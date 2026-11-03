"""P5.4.30 fixture-only Scheduler -> Gateway contract tests.

These tests compose build_runtime without starting FeederRuntime, touching a
database, connecting to an exchange, or enabling any production writer.
"""
import sys
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
        lease_store.authorize_write.return_value = True
        lease_store.is_current.return_value = True
        lease_store.lease_name = "binance-btcusdt-canonical"

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


    def test_scheduler_and_recovery_share_injected_gateway_and_current_fence(self):
        (
            runtime, gateway, _exchange, store, lease_store,
            lease_clock, _observation_clock, _initial_boundary, _interval,
        ) = self._build_runtime()

        coverage_reads = {"count": 0}

        def read_window(_symbol, _timeframe, start_ms, end_ms):
            coverage_reads["count"] += 1
            if coverage_reads["count"] == 1:
                return {
                    "startMs": start_ms,
                    "endMs": end_ms,
                    "coverage": {
                        "complete": False,
                        "gaps": [{"startMs": start_ms, "endMs": start_ms + INTERVAL_MS["15m"]}],
                    },
                }
            return {
                "startMs": start_ms,
                "endMs": end_ms,
                "coverage": {"complete": True, "gaps": []},
            }

        store.read_window.side_effect = read_window
        expected_fence = LeaseFence(
            "binance-btcusdt-canonical",
            "p5-4-30-scheduler-fixture",
            42,
        )

        with patch(
            "market_data.feeder_service.sync_window", side_effect=[7, 1]
        ) as sync_window:
            self.assertEqual(runtime.scheduler.run_due(), {"15m": 7})
            self.assertTrue(runtime.recovery.recover_all())

        self.assertEqual(sync_window.call_count, 2)
        for invocation in sync_window.call_args_list:
            self.assertIs(invocation.kwargs["gateway"], gateway)
            self.assertEqual(invocation.kwargs["lease_token"], expected_fence)
            self.assertIs(invocation.kwargs["lease_clock"], lease_clock)

        self.assertEqual(coverage_reads["count"], 2)
        self.assertEqual(lease_store.heartbeat.call_count, 2)
        lease_store.heartbeat.assert_has_calls([
            unittest.mock.call(
                "p5-4-30-scheduler-fixture",
                42,
                now_ms=lease_clock(),
                ttl_seconds=60,
            ),
            unittest.mock.call(
                "p5-4-30-scheduler-fixture",
                42,
                now_ms=lease_clock(),
                ttl_seconds=60,
            ),
        ])

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



class ProductionRuntimeDbIdentityContractTest(unittest.TestCase):
    """P5.4.32: production composition keeps all T0 SQLite roles on one file.

    These tests use only nonexistent temporary paths and a stub CCXT module.
    They never initialize/open a database or contact an exchange.
    """

    def test_production_factory_rejects_distinct_lease_database_before_composition(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import Mock, patch
        from market_data.feeder_service import build_production_runtime

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candle_path = root / "canonical.sqlite3"
            lease_path = root / "separate-lease.sqlite3"
            ccxt_stub = Mock()

            with patch.dict(sys.modules, {"ccxt": ccxt_stub}):
                with patch(
                    "market_data.feeder_service.build_runtime"
                ) as compose_runtime:
                    with self.assertRaisesRegex(
                        ValueError, "must resolve to the same file"
                    ):
                        build_production_runtime({
                            "MARKET_DATA_BACKEND": "sqlite",
                            "MARKET_DATA_DB": str(candle_path),
                            "T0_FEEDER_LEASE_DB": str(lease_path),
                        })

            ccxt_stub.binanceusdm.assert_not_called()
            compose_runtime.assert_not_called()
            self.assertFalse(candle_path.exists())
            self.assertFalse(lease_path.exists())

    def test_production_factory_composes_all_sqlite_roles_on_same_resolved_path(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import Mock, patch
        from market_data.feeder_service import build_production_runtime

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            canonical_path = root / "canonical.sqlite3"
            equivalent_lease_path = root / "unused" / ".." / "canonical.sqlite3"
            ccxt_stub = Mock()
            runtime_sentinel = object()

            with patch.dict(sys.modules, {"ccxt": ccxt_stub}):
                with patch(
                    "market_data.feeder_service.build_runtime",
                    return_value=runtime_sentinel,
                ) as compose_runtime:
                    result = build_production_runtime({
                        "MARKET_DATA_BACKEND": "sqlite",
                        "MARKET_DATA_DB": str(canonical_path),
                        "T0_FEEDER_LEASE_DB": str(equivalent_lease_path),
                        "T0_FEEDER_OWNER_ID": "p5-4-32-fixture-owner",
                    })

            self.assertIs(result, runtime_sentinel)
            ccxt_stub.binanceusdm.assert_called_once()
            kwargs = compose_runtime.call_args.kwargs
            resolved = canonical_path.resolve()
            self.assertEqual(Path(kwargs["store"].path).resolve(), resolved)
            self.assertEqual(Path(kwargs["gateway"]._db_path).resolve(), resolved)
            self.assertEqual(Path(kwargs["lease_store"].db_path).resolve(), resolved)
            self.assertEqual(Path(kwargs["status_store"].db_path).resolve(), resolved)
            self.assertFalse(canonical_path.exists())

    def test_production_factory_defaults_lease_database_to_canonical_database(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import Mock, patch
        from market_data.feeder_service import build_production_runtime

        with tempfile.TemporaryDirectory() as directory:
            canonical_path = Path(directory) / "canonical.sqlite3"
            ccxt_stub = Mock()
            with patch.dict(sys.modules, {"ccxt": ccxt_stub}):
                with patch(
                    "market_data.feeder_service.build_runtime",
                    return_value=object(),
                ) as compose_runtime:
                    build_production_runtime({
                        "MARKET_DATA_BACKEND": "sqlite",
                        "MARKET_DATA_DB": str(canonical_path),
                        "T0_FEEDER_OWNER_ID": "p5-4-32-default-lease-fixture",
                    })

            kwargs = compose_runtime.call_args.kwargs
            self.assertEqual(
                Path(kwargs["lease_store"].db_path).resolve(),
                canonical_path.resolve(),
            )
            self.assertFalse(canonical_path.exists())
