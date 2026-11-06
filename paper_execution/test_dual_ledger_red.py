import tempfile
import unittest
from pathlib import Path

from paper_execution.ledger import PaperLedger


class DualLedgerRedTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "shared-account.sqlite3"
        self.now = 1_800_000_000_000
        bootstrap = PaperLedger(self.path, max_position_base="1", fee_rate="0.001")
        bootstrap.record_equity("100", self.now - 60_000, self.now, "sha256:dual-ledger-seed", "100")
        self.core = PaperLedger(self.path, max_position_base="1", fee_rate="0.001",
                                strategy_id="STRATEGY_CORE", source_sha="a" * 40)
        self.ai = PaperLedger(self.path, max_position_base="1", fee_rate="0.001",
                              strategy_id="AI_FREQAI", source_sha="a" * 40)

    def intent(self, intent_id, target, limit, snapshot_id):
        return {
            "intentId": intent_id,
            "symbol": "BTCUSDT",
            "exchange": "binance",
            "marketType": "USDT_PERPETUAL",
            "strategyVersion": "dual-ledger-red",
            "modelVersion": "red-test",
            "datasetVersion": "sha256:dual-ledger-fixture",
            "targetPositionBase": target,
            "limitPrice": limit,
            "decisionAtMs": self.now - 100,
            "validUntilMs": self.now + 30_000,
            "inputSnapshotId": snapshot_id,
            "mode": "PAPER",
        }

    def book(self, observed_at, bid="100", ask="100.1"):
        return {
            "source": "hummingbot",
            "connector": "binance_perpetual",
            "symbol": "BTCUSDT",
            "observedAtMs": observed_at,
            "bids": [{"price": bid, "quantity": "1"}],
            "asks": [{"price": ask, "quantity": "1"}],
        }

    def test_core_and_ai_hold_independent_positions_in_one_account_database(self):
        core_order = self.core.submit(
            self.intent("core-long", "0.1", "100.1", "core-book"),
            self.book(self.now),
            self.now,
        )
        ai_order = self.ai.submit(
            self.intent("ai-short", "-0.2", "100", "ai-book"),
            self.book(self.now + 1),
            self.now + 1,
        )

        self.assertEqual(core_order["status"], "FILLED")
        self.assertEqual(ai_order["status"], "FILLED")

        self.assertEqual(
            self.core.snapshot()["positionBase"], "0.1"
        )
        self.assertEqual(
            self.ai.snapshot()["positionBase"], "-0.2"
        )

        reopened_core = PaperLedger(self.path, max_position_base="1", strategy_id="STRATEGY_CORE", source_sha="a" * 40)
        reopened_ai = PaperLedger(self.path, max_position_base="1", strategy_id="AI_FREQAI", source_sha="a" * 40)
        self.assertEqual(
            reopened_core.snapshot()["positionBase"], "0.1"
        )
        self.assertEqual(
            reopened_ai.snapshot()["positionBase"], "-0.2"
        )


if __name__ == "__main__":
    unittest.main()
