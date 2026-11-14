import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from paper_execution.account_equity import record_account_mark
from paper_execution.ledger import PaperLedger
from paper_execution.simulated_capital import DEFAULT_SIMULATED_CAPITAL_CONTRACT


class SimulatedOrderAdmissionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "simulated-order-admission.sqlite3"
        self.now = 1_800_000_000_000
        self.limits = {
            "maxDrawdownPct": "20",
            "maxDailyLossUsdt": "10",
            "maxExposureUsdt": "1000",
        }
        contract = json.dumps(
            DEFAULT_SIMULATED_CAPITAL_CONTRACT, separators=(",", ":")
        ).encode("utf-8")
        self.core = PaperLedger(
            self.path,
            max_position_base="1",
            fee_rate="0.001",
            strategy_id="STRATEGY_CORE",
            source_sha="a" * 40,
            risk_limits=self.limits,
            require_risk_limits=True,
            simulated_contract_bytes=contract,
            simulated_initialized_at_ms=self.now,
        )
        account_scope = PaperLedger(self.path)
        record_account_mark(
            account_scope,
            "100",
            self.now - 60_000,
            self.now,
            "sha256:" + "c" * 64,
        )

    def intent(self, intent_id, target):
        return {
            "intentId": intent_id,
            "symbol": "BTCUSDT",
            "exchange": "binance",
            "marketType": "USDT_PERPETUAL",
            "strategyVersion": "simulated-order-admission-v1",
            "modelVersion": "core-fixture",
            "datasetVersion": "sha256:" + "d" * 64,
            "targetPositionBase": target,
            "limitPrice": "100.1",
            "decisionAtMs": self.now - 100,
            "validUntilMs": self.now + 30_000,
            "inputSnapshotId": "fixture:" + intent_id,
            "mode": "PAPER",
        }

    def book(self):
        return {
            "source": "hummingbot",
            "connector": "binance_perpetual",
            "symbol": "BTCUSDT",
            "observedAtMs": self.now,
            "bids": [{"price": "100", "quantity": "1"}],
            "asks": [{"price": "100.1", "quantity": "1"}],
        }

    def test_simulated_core_entry_uses_shared_risk_without_funded_cutover(self):
        result = self.core.submit(
            self.intent("simulated-core-entry", "0.009"),
            self.book(),
            self.now,
            strategy_event="ENTRY",
        )

        self.assertEqual(result["status"], "FILLED", result)
        self.assertEqual(result["reason"], "VISIBLE_DEPTH_SIMULATION")
        with sqlite3.connect(self.path) as connection:
            cutovers = connection.execute(
                "SELECT COUNT(*) FROM paper_account_equity_cutovers"
            ).fetchone()[0]
            funding_events = connection.execute(
                "SELECT COUNT(*) FROM paper_funding_events"
            ).fetchone()[0]
            reservation = connection.execute(
                """SELECT reserved_margin_quote,reserved_notional_quote,
                          leverage,equity_basis_quote,status
                   FROM paper_risk_reservations WHERE intent_id=?""",
                ("simulated-core-entry",),
            ).fetchone()
            position = connection.execute(
                """SELECT position_base FROM paper_strategy_ledgers
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
            ).fetchone()[0]

        self.assertEqual(cutovers, 0)
        self.assertEqual(funding_events, 0)
        self.assertEqual(reservation, ("1", "1", "1", "100", "CONSUMED"))
        self.assertEqual(position, "0.009")

    def test_simulated_core_entry_above_one_percent_margin_is_rejected_atomically(self):
        result = self.core.submit(
            self.intent("simulated-core-over-budget", "0.011"),
            self.book(),
            self.now,
            strategy_event="ENTRY",
        )

        self.assertEqual(result["status"], "REJECTED", result)
        self.assertEqual(result["reason"], "MARGIN_RESERVATION_EXCEEDED")
        with sqlite3.connect(self.path) as connection:
            reservation_count = connection.execute(
                "SELECT COUNT(*) FROM paper_risk_reservations"
            ).fetchone()[0]
            position = connection.execute(
                """SELECT position_base FROM paper_strategy_ledgers
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
            ).fetchone()[0]
        self.assertEqual(reservation_count, 0)
        self.assertEqual(position, "0")


if __name__ == "__main__":
    unittest.main()
