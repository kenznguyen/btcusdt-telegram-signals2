"""P5.3.11.5 G2 RED contracts for mandatory Gateway writer routing.

All tests use an in-memory exchange double and disposable objects. They never
resolve MARKET_DATA_DB, open a canonical database, contact an exchange, or
start FeederRuntime. The expected RED baseline is the unfenced G1-era routing.
"""
import ast
import inspect
import textwrap
import unittest
from unittest.mock import Mock

from market_data import feeder, feeder_service, sync
from market_data.feeder import RecoveryCoordinator
from market_data.gateway import (
    CandleBatchRejected,
    LeaseFence,
    LeaseRejected,
)
from market_data.store import INTERVAL_MS
from market_data.sync import sync_window


START = 1_800_000_000_000
STEP = INTERVAL_MS["15m"]
SYMBOL = "BTC/USDT:USDT"
LEASE = LeaseFence("binance-btcusdt-canonical", "g2-test-owner", 7)


def candle_row(opened):
    return [opened, 100.01, 103.5, 99.0, 102.25, 1.25]


class ExchangeDouble:
    id = "binanceusdm"

    def __init__(self, pages):
        self.pages = list(pages)
        self.calls = []
        self.server_time = START + 3000 * STEP
        self.market = {
            "symbol": SYMBOL, "id": "BTCUSDT", "base": "BTC",
            "quote": "USDT", "settle": "USDT", "active": True,
            "swap": True, "linear": True, "spot": False,
        }

    def load_markets(self):
        return {SYMBOL: self.market}

    def fetch_time(self):
        return self.server_time

    def fetch_ohlcv(self, symbol, timeframe, since, limit, params):
        self.calls.append((symbol, timeframe, since, limit, params))
        page = self.pages.pop(0)
        if isinstance(page, Exception):
            raise page
        return page


class GatewayDouble:
    def __init__(self, result=None, error=None, error_at_call=None):
        self.result = result
        self.error = error
        self.error_at_call = error_at_call
        self.calls = []

    def insert_batch(self, candles, *, lease_token, now_ms):
        batch = tuple(candles)
        self.calls.append((batch, lease_token, now_ms))
        if (self.error is not None
                and (self.error_at_call is None or len(self.calls) == self.error_at_call)):
            raise self.error
        if self.result is not None:
            return self.result
        return len(batch)


class G2WriterRoutingRedTests(unittest.TestCase):
    def setUp(self):
        self.observed_at = START + 100 * STEP
        self.lease_now = START + 100 * STEP + 123

    def _assert_routing_api(self):
        parameters = inspect.signature(sync_window).parameters
        self.assertTrue(
            {"gateway", "lease_token", "lease_clock"}.issubset(parameters),
            "CONTRACT RED: sync_window must require Gateway, LeaseFence and lease_clock",
        )

    def _sync(self, exchange, gateway, **overrides):
        self._assert_routing_api()
        arguments = {
            "now_ms": lambda: self.observed_at,
            "lease_token": LEASE,
            "lease_clock": lambda: self.lease_now,
        }
        arguments.update(overrides)
        return sync_window(
            exchange, gateway, "15m", START, START + STEP, **arguments
        )

    def test_g2_01_missing_gateway_fails_closed(self):
        exchange = ExchangeDouble([[candle_row(START)]])
        with self.assertRaises((TypeError, ValueError)):
            self._sync(exchange, None)

    def test_g2_02_missing_lease_fence_fails_closed(self):
        exchange = ExchangeDouble([[candle_row(START)]])
        gateway = GatewayDouble()
        with self.assertRaises((TypeError, ValueError, LeaseRejected)):
            self._sync(exchange, gateway, lease_token=None)
        self.assertEqual(gateway.calls, [])

    def test_g2_03_missing_lease_clock_fails_closed(self):
        exchange = ExchangeDouble([[candle_row(START)]])
        gateway = GatewayDouble()
        with self.assertRaises((TypeError, ValueError, LeaseRejected)):
            self._sync(exchange, gateway, lease_clock=None)
        self.assertEqual(gateway.calls, [])

    def test_g2_04_wrong_gateway_interface_is_rejected(self):
        exchange = ExchangeDouble([[candle_row(START)]])
        with self.assertRaises((TypeError, ValueError)):
            self._sync(exchange, object())

    def test_g2_05_feeder_runtime_routes_a_typed_fence_to_sync_callback(self):
        source = textwrap.dedent(inspect.getsource(feeder.FeederRuntime))
        self.assertIn("LeaseFence", source)
        self.assertIn("lease_generation", source)
        self.assertIn("sync_callback", source)
        runtime_builder = textwrap.dedent(inspect.getsource(feeder_service.build_runtime))
        self.assertIn("T0WriteGateway", runtime_builder)
        self.assertIn("LeaseFence", runtime_builder)

    def test_g2_06_stale_generation_rejection_is_not_bypassed(self):
        exchange = ExchangeDouble([[candle_row(START)]])
        stale = LeaseFence(LEASE.lease_name, LEASE.owner_id, LEASE.generation - 1)
        gateway = GatewayDouble(error=LeaseRejected("stale generation"))
        with self.assertRaises(LeaseRejected):
            self._sync(exchange, gateway, lease_token=stale)
        self.assertEqual(len(gateway.calls), 1)
        self.assertIs(gateway.calls[0][1], stale)

    def test_g2_07_lease_expiry_error_propagates_without_legacy_fallback(self):
        exchange = ExchangeDouble([[candle_row(START)]])
        gateway = GatewayDouble(error=LeaseRejected("expired at admission"))
        legacy = Mock()
        legacy.insert.return_value = 1
        legacy.insert_fenced.return_value = 1
        with self.assertRaises(LeaseRejected):
            self._sync(exchange, gateway)
        legacy.insert.assert_not_called()
        legacy.insert_fenced.assert_not_called()

    def test_g2_08_recovery_uses_the_same_gateway_backed_sync_callback(self):
        self._assert_routing_api()
        exchange = ExchangeDouble([[candle_row(START)]])
        gateway = GatewayDouble()
        read = Mock(side_effect=[
            {"startMs": START, "endMs": START + STEP,
             "coverage": {"complete": False, "gaps": [
                 {"startMs": START, "endMs": START + STEP}]}},
            {"startMs": START, "endMs": START + STEP,
             "coverage": {"complete": True, "gaps": []}},
        ])

        def canonical_callback(frame, start, end):
            return sync_window(
                exchange, gateway, frame, start, end,
                now_ms=lambda: self.observed_at,
                lease_token=LEASE,
                lease_clock=lambda: self.lease_now,
            )

        result = RecoveryCoordinator(canonical_callback, read).recover(
            "15m", START, START + STEP
        )
        self.assertTrue(result.complete)
        self.assertEqual(len(gateway.calls), 1)
        self.assertIs(gateway.calls[0][1], LEASE)

    def test_g2_09_cli_cannot_invoke_sync_without_explicit_capability(self):
        tree = ast.parse(inspect.getsource(sync.main))
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "sync_window"
        ]
        self.assertTrue(calls, "CLI must retain an explicit ingestion entrypoint")
        for call in calls:
            keywords = {item.arg for item in call.keywords}
            self.assertIn("lease_token", keywords)
            self.assertIn("lease_clock", keywords)

    def test_g2_10_legacy_store_insert_is_not_a_canonical_writer_route(self):
        self._assert_routing_api()
        class LegacyStore:
            def __init__(self):
                self.insert_calls = 0

            def insert(self, candles):
                self.insert_calls += 1
                return len(candles)

        legacy = LegacyStore()
        exchange = ExchangeDouble([[candle_row(START)]])
        with self.assertRaises((TypeError, ValueError)):
            sync_window(
                exchange, legacy, "15m", START, START + STEP,
                now_ms=lambda: self.observed_at,
                lease_token=LEASE,
                lease_clock=lambda: self.lease_now,
            )
        self.assertEqual(legacy.insert_calls, 0)

    def test_g2_11_legacy_insert_fenced_is_not_an_alternate_route(self):
        self._assert_routing_api()
        class LegacyFencedStore:
            def __init__(self):
                self.calls = 0

            def insert_fenced(self, candles, **kwargs):
                self.calls += 1
                return len(candles)

        legacy = LegacyFencedStore()
        exchange = ExchangeDouble([[candle_row(START)]])
        with self.assertRaises((TypeError, ValueError)):
            sync_window(
                exchange, legacy, "15m", START, START + STEP,
                now_ms=lambda: self.observed_at,
                lease_token=LEASE,
                lease_clock=lambda: self.lease_now,
            )
        self.assertEqual(legacy.calls, 0)

    def test_g2_12_runtime_lease_path_does_not_create_schema(self):
        source = textwrap.dedent(inspect.getsource(feeder.LeaseStore._transaction))
        normalized = " ".join(source.upper().split())
        self.assertNotIn("CREATE TABLE", normalized)
        self.assertNotIn("CREATE INDEX", normalized)

    def test_g2_13_gateway_conflict_rejection_propagates(self):
        exchange = ExchangeDouble([[candle_row(START)]])
        gateway = GatewayDouble(error=CandleBatchRejected("conflicting candle"))
        with self.assertRaises(CandleBatchRejected):
            self._sync(exchange, gateway)
        self.assertEqual(len(gateway.calls), 1)

    def test_g2_14_identical_duplicate_is_idempotent(self):
        exchange = ExchangeDouble([[candle_row(START)]])
        gateway = GatewayDouble(result=0)
        self.assertEqual(self._sync(exchange, gateway), 0)
        self.assertEqual(len(gateway.calls), 1)

    def test_g2_15_empty_exchange_page_is_a_gateway_noop(self):
        exchange = ExchangeDouble([[]])
        gateway = GatewayDouble()
        self.assertEqual(self._sync(exchange, gateway), 0)
        self.assertEqual(gateway.calls, [])

    def test_g2_16_pagination_preserves_per_page_commit_boundary(self):
        self._assert_routing_api()
        first = [candle_row(START + i * STEP) for i in range(1000)]
        second = [candle_row(START + 1000 * STEP)]
        exchange = ExchangeDouble([first, second])
        end = START + 1001 * STEP
        gateway = GatewayDouble(
            error=RuntimeError("second page rejected"), error_at_call=2
        )
        with self.assertRaisesRegex(RuntimeError, "second page rejected"):
            sync_window(
                exchange, gateway, "15m", START, end,
                now_ms=lambda: START + 2000 * STEP,
                lease_token=LEASE,
                lease_clock=lambda: self.lease_now,
            )
        self.assertEqual(len(gateway.calls), 2)
        self.assertEqual(len(gateway.calls[0][0]), 1000)
        self.assertEqual(len(gateway.calls[1][0]), 1)

    def test_g2_17_available_at_uses_observation_clock_not_lease_clock(self):
        exchange = ExchangeDouble([[candle_row(START)]])
        gateway = GatewayDouble()
        self._sync(exchange, gateway)
        stored_candidate = gateway.calls[0][0][0]
        self.assertEqual(stored_candidate.available_at_ms, self.observed_at)
        self.assertTrue(callable(gateway.calls[0][2]))
        self.assertNotEqual(stored_candidate.available_at_ms, self.lease_now)

    def test_g2_18_postgres_store_cannot_bypass_gateway_for_canonical_sync(self):
        self._assert_routing_api()
        class PostgresLikeStore:
            def insert(self, candles):
                return len(candles)

        postgres = PostgresLikeStore()
        exchange = ExchangeDouble([[candle_row(START)]])
        with self.assertRaises((TypeError, ValueError)):
            sync_window(
                exchange, postgres, "15m", START, START + STEP,
                now_ms=lambda: self.observed_at,
                lease_token=LEASE,
                lease_clock=lambda: self.lease_now,
            )
        self.assertFalse(hasattr(postgres, "insert_batch"))


if __name__ == "__main__":
    unittest.main()
