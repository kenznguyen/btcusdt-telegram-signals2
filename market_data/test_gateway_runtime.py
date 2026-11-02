"""Runtime contract tests for the T0 Single Writer Gateway.

All writes use disposable SQLite databases and synthetic candles. The test
suite must never point at a canonical database or contact an exchange.
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from dataclasses import replace
from market_data.feeder import LeaseStore
from market_data.store import Candle

try:
    from market_data.gateway import T0WriteGateway, GatewayWriteError
except ModuleNotFoundError as exc:
    if exc.name != "market_data.gateway":
        raise
    T0WriteGateway = GatewayWriteError = None

try:
    from paper_execution.writer_gate import PaperWriterGate
except ModuleNotFoundError as exc:
    if exc.name != "paper_execution.writer_gate":
        raise
    PaperWriterGate = None


class T0WriteGatewayRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db = self.root / "shadow.sqlite3"
        self.lease = LeaseStore(self.db)
        self.now = 1_800_000_000_000
        self.owner = "runtime-test-writer"
        self.lease_token = self.lease.acquire(self.owner, self.now, ttl_seconds=60)
        self.gateway = T0WriteGateway(db_path=self.db, lease_store=self.lease) if T0WriteGateway else None

    def tearDown(self):
        self.temp.cleanup()

    def candle(self, opened, close="100"):
        return Candle("15m", opened, "99", "101", "98", close, "1",
                      available_at_ms=opened + 900_000)

    def write(self, candles, token=None, now=None):
        return self.gateway.insert_batch(
            candles, lease_token=token or self.lease_token,
            now_ms=self.now if now is None else now,
        )

    def count(self):
        with sqlite3.connect(self.db) as connection:
            return connection.execute("SELECT COUNT(*) FROM candles").fetchone()[0]

    def test_gateway_contract_module_is_present(self):
        self.assertIsNotNone(T0WriteGateway,
            "CONTRACT RED: market_data.gateway module/API is not implemented")

    @unittest.skipIf(T0WriteGateway is None, "Gateway module absent; explicit contract RED assertion covers this")
    def test_valid_lease_commits_batch_atomically(self):
        candles = [self.candle(1_799_998_200_000), self.candle(1_799_999_100_000)]
        self.assertEqual(self.write(candles), 2)
        self.assertEqual(self.count(), 2)

    @unittest.skipIf(T0WriteGateway is None, "Gateway module absent; explicit contract RED assertion covers this")
    def test_missing_lease_is_rejected_without_mutation(self):
        with self.assertRaises(GatewayWriteError):
            self.gateway.insert_batch([self.candle(1_799_998_200_000)], lease_token=None, now_ms=self.now)
        self.assertEqual(self.count(), 0)

    @unittest.skipIf(T0WriteGateway is None, "Gateway module absent; explicit contract RED assertion covers this")
    def test_expired_lease_is_rejected_without_mutation(self):
        with self.assertRaises(GatewayWriteError):
            self.write([self.candle(1_799_998_200_000)], now=self.now + 60_001)
        self.assertEqual(self.count(), 0)

    @unittest.skipIf(T0WriteGateway is None, "Gateway module absent; explicit contract RED assertion covers this")
    def test_old_epoch_is_rejected_after_lease_takeover(self):
        old = self.lease_token
        newer = self.lease.acquire("new-writer", self.now + 60_001, ttl_seconds=60)
        with self.assertRaises(GatewayWriteError):
            self.write([self.candle(1_799_998_200_000)], token=old, now=self.now + 60_002)
        self.assertEqual(self.count(), 0)
        self.assertIsNotNone(newer)

    @unittest.skipIf(T0WriteGateway is None, "Gateway module absent; explicit contract RED assertion covers this")
    def test_failure_in_later_row_rolls_back_the_entire_batch(self):
        good = self.candle(1_799_998_200_000)
        conflict = self.candle(1_799_999_100_000, close="100")
        self.write([conflict])
        with self.assertRaises((GatewayWriteError, ValueError)):
            self.write([good, self.candle(1_799_999_100_000, close="102")])
        self.assertEqual(self.count(), 1)
        with sqlite3.connect(self.db) as connection:
            self.assertEqual(connection.execute(
                "SELECT open_time_ms FROM candles ORDER BY open_time_ms"
            ).fetchall(), [(1_799_999_100_000,)])

    @unittest.skipIf(T0WriteGateway is None, "Gateway module absent; explicit contract RED assertion covers this")
    def test_replaying_identical_batch_is_idempotent(self):
        batch = [self.candle(1_799_998_200_000)]
        self.assertEqual(self.write(batch), 1)
        self.assertEqual(self.write(batch), 0)
        self.assertEqual(self.count(), 1)

    @unittest.skipIf(T0WriteGateway is None, "Gateway module absent; explicit contract RED assertion covers this")
    def test_wrong_owner_or_generation_is_rejected(self):
        wrong = replace(self.lease_token, owner="forged-owner")
        with self.assertRaises(GatewayWriteError):
            self.write([self.candle(1_799_998_200_000)], token=wrong)
        self.assertEqual(self.count(), 0)

    @unittest.skipIf(T0WriteGateway is None, "Gateway module absent; explicit contract RED assertion covers this")
    def test_postgres_canonical_writer_is_disabled_by_default(self):
        with self.assertRaises(GatewayWriteError):
            T0WriteGateway(backend="postgres", allow_unfenced_postgres=False)

    @unittest.skipIf(T0WriteGateway is None, "Gateway module absent; explicit contract RED assertion covers this")
    def test_gateway_never_accepts_paper_writer_token(self):
        self.assertIsNotNone(PaperWriterGate, "Paper Writer Gate contract module is absent")
        paper_gate = PaperWriterGate(scope="paper_only")
        token = paper_gate.admit_writer()
        with self.assertRaises(GatewayWriteError):
            self.gateway.insert_batch([self.candle(1_799_998_200_000)],
                                      lease_token=token, now_ms=self.now)


if __name__ == "__main__":
    unittest.main()
