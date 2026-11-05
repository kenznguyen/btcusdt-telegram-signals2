"""Negative acceptance tests for the independent T0 and Paper write authorities.

The Paper implementation is loaded from this branch. T0 modules are imported
from the separately checked-out, exact source revision identified below.
All databases are disposable temporary SQLite files; no external services.
"""
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

T0_SOURCE_SHA = "a569eb6248cd53252fcf32065482921fc4c8ffcd"
T0_SOURCE_ROOT = os.environ.get("T0_SOURCE_ROOT")
if not T0_SOURCE_ROOT:
    raise RuntimeError("T0_SOURCE_ROOT must point to the exact T0 source checkout")
T0_SOURCE_ROOT = str(Path(T0_SOURCE_ROOT).resolve())
if not Path(T0_SOURCE_ROOT, "market_data", "write_gateway.py").is_file():
    raise RuntimeError("T0_SOURCE_ROOT does not contain the T0 write gateway")
sys.path.insert(0, T0_SOURCE_ROOT)

from market_data.feeder import LeaseStore
from market_data.store import Candle, CandleStore, INTERVAL_MS, read_window
from market_data.write_gateway import SQLiteWriteGateway
from paper_execution.writer_gate import (
    PaperWriterGate,
    WriterTokenInvalid,
)

NOW = 1_800_000_000_000


def _candle(open_time_ms):
    return Candle(
        timeframe="15m",
        open_time_ms=open_time_ms,
        open="100",
        high="101",
        low="99",
        close="100.5",
        volume="1",
        available_at_ms=open_time_ms + INTERVAL_MS["15m"],
    )


class CrossDomainWriterIsolationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.paper_db = root / "paper" / "paper.sqlite3"
        self.market_db = root / "market" / "market.sqlite3"
        self.paper_db.parent.mkdir(parents=True)
        with sqlite3.connect(self.paper_db) as connection:
            connection.execute(
                "CREATE TABLE paper_probe (value TEXT NOT NULL)"
            )

        self.store = CandleStore(str(self.market_db))
        self.lease_store = LeaseStore(str(self.market_db))
        self.t0_lease = self.lease_store.acquire("t0-worker", NOW, 60)
        self.assertIsNotNone(self.t0_lease)

        self.paper_gate = PaperWriterGate.initialize(
            paper_db_path=str(self.paper_db)
        )
        self.paper_token = self.paper_gate.admit_writer()
        self.addCleanup(self.paper_gate.release_writer, self.paper_token)

        self.assertNotEqual(
            self.paper_db.resolve(), self.market_db.resolve()
        )
        self.assertFalse(os.path.samefile(self.paper_db, self.market_db))

    def _paper_probe_rows(self):
        with sqlite3.connect(self.paper_db) as connection:
            return connection.execute(
                "SELECT value FROM paper_probe ORDER BY rowid"
            ).fetchall()

    def test_paper_writer_token_cannot_authorize_t0_candle_writes(self):
        self.assertEqual(self.paper_gate.paper_db_path, self.paper_db.resolve())
        self.assertEqual(
            Path(self.store.path).resolve(), self.market_db.resolve()
        )

        authority = {"generation": self.t0_lease.generation}
        gateway = SQLiteWriteGateway(
            store=self.store,
            lease_store=self.lease_store,
            owner_id=self.t0_lease.owner,
            generation_provider=lambda: authority["generation"],
            clock=lambda: NOW + 1,
        )

        # Positive control: the actual T0 lease generation can write T0.
        self.assertEqual(gateway.write_batch([_candle(NOW)]), 1)

        # A Paper capability is not a T0 generation and must fail closed.
        authority["generation"] = self.paper_token
        with self.assertRaisesRegex(
            PermissionError, "Feeder lease is unavailable"
        ):
            gateway.write_batch([_candle(NOW + INTERVAL_MS["15m"])])

        result = read_window(
            str(self.market_db),
            "BTCUSDT",
            "15m",
            NOW,
            NOW + 2 * INTERVAL_MS["15m"],
        )
        self.assertEqual(
            [item["openTimeMs"] for item in result["candles"]], [NOW]
        )
        self.assertEqual(self._paper_probe_rows(), [])

    def test_t0_lease_capability_cannot_authorize_paper_writer_gate(self):
        self.assertEqual(
            self.paper_gate.paper_db_path, self.paper_db.resolve()
        )
        self.assertTrue(self.lease_store.is_current(
            self.t0_lease.owner, self.t0_lease.generation, NOW + 1
        ))

        # Positive control: a Paper-owned token is accepted and can write PAPER_DB.
        self.paper_gate.validate_writer_token(self.paper_token)
        with self.paper_gate.writer_transaction(
            paper_db_path=str(self.paper_db)
        ) as connection:
            connection.execute(
                "INSERT INTO paper_probe(value) VALUES (?)",
                ("paper-control",),
            )

        # A real, current T0 Lease object is not a Paper WriterToken.
        with self.assertRaises(WriterTokenInvalid):
            self.paper_gate.validate_writer_token(self.t0_lease)

        self.assertEqual(
            self._paper_probe_rows(), [("paper-control",)]
        )
        result = read_window(
            str(self.market_db),
            "BTCUSDT",
            "15m",
            NOW,
            NOW + INTERVAL_MS["15m"],
        )
        self.assertEqual(result["candles"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
