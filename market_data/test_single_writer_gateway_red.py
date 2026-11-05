"""Static RED contracts for the T0 Single Writer Gateway.

These checks inspect source text only. They never open a database, start a
Feeder, contact an exchange, or mutate repository files.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def source(path):
    return (ROOT / path).read_text(encoding="utf-8")


class SingleWriterGatewayRedContracts(unittest.TestCase):
    def test_swg_a01_gateway_contract_exists(self):
        self.assertTrue(
            (ROOT / "market_data" / "write_gateway.py").is_file(),
            "SWG-A01: canonical write gateway module is not implemented",
        )

    def test_swg_a02_legacy_candle_insert_is_closed(self):
        text = source("market_data/store.py")
        self.assertNotIn(
            "def insert(self, candles",
            text,
            "SWG-A02: public unfenced CandleStore.insert remains available",
        )

    def test_swg_a03_sync_requires_write_authority(self):
        text = source("market_data/sync.py")
        self.assertIn(
            "write_gateway",
            text,
            "SWG-A03: sync module has no mandatory Gateway integration",
        )

    def test_swg_a04_cli_is_shadow_only(self):
        text = source("market_data/sync.py")
        self.assertIn(
            "shadow_only",
            text,
            "SWG-A04: CLI has no explicit Shadow-only write restriction",
        )

    def test_swg_b01_lease_validation_is_inside_gateway_transaction(self):
        gateway = ROOT / "market_data" / "write_gateway.py"
        self.assertTrue(
            gateway.is_file(),
            "SWG-B01: no Gateway transaction boundary exists",
        )
        text = gateway.read_text(encoding="utf-8")
        self.assertIn("BEGIN IMMEDIATE", text)
        self.assertIn("generation", text)
        self.assertIn("expires_at", text)

    def test_swg_c01_gateway_owns_atomic_batch_write(self):
        gateway = ROOT / "market_data" / "write_gateway.py"
        self.assertTrue(
            gateway.is_file(),
            "SWG-C01: atomic Gateway batch writer is not implemented",
        )
        text = gateway.read_text(encoding="utf-8")
        self.assertIn("write_batch", text)
        self.assertIn("ROLLBACK", text)

    def test_swg_d01_consumer_has_read_only_connection_contract(self):
        text = source("market_data/store.py")
        self.assertIn(
            "mode=ro",
            text,
            "SWG-D01: canonical consumer read-only URI contract is absent",
        )

    def test_swg_e01_sync_does_not_call_unfenced_insert(self):
        text = source("market_data/sync.py")
        self.assertNotIn(
            "store.insert(",
            text,
            "SWG-E01: sync path can still call the unfenced writer",
        )

    def test_swg_e02_recovery_is_gateway_only(self):
        text = source("market_data/feeder.py")
        self.assertIn(
            "write_gateway",
            text,
            "SWG-E02: recovery path has no Gateway-only write contract",
        )

    def test_swg_e03_postgres_canonical_writer_is_disabled(self):
        text = source("market_data/postgres.py")
        self.assertIn(
            "canonical_writes_disabled",
            text,
            "SWG-E03: PostgreSQL writer lacks an explicit canonical-write deny gate",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
