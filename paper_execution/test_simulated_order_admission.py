import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from paper_execution.account_equity import record_account_mark
from paper_execution.ledger import PaperLedger
from paper_execution import risk_control
from paper_execution.simulated_capital import DEFAULT_SIMULATED_CAPITAL_CONTRACT


class SimulatedOrderAdmissionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "simulated-order-admission.sqlite3"
        self.now = 1_800_000_000_000
        self.contract = json.dumps(
            DEFAULT_SIMULATED_CAPITAL_CONTRACT, separators=(",", ":")
        ).encode("utf-8")
        self.core = PaperLedger(
            self.path,
            max_position_base="1",
            fee_rate="0.001",
            strategy_id="STRATEGY_CORE",
            source_sha="a" * 40,
            simulated_contract_bytes=self.contract,
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


    def test_simulated_core_dca_uses_same_shared_admission_without_funding(self):
        entry = self.core.submit(
            self.intent("simulated-core-entry-before-dca", "0.009"),
            self.book(),
            self.now,
            strategy_event="ENTRY",
        )
        self.assertEqual(entry["status"], "FILLED", entry)

        dca = self.core.submit(
            self.intent("simulated-core-dca", "0.018"),
            self.book(),
            self.now,
            strategy_event="DCA",
        )
        self.assertEqual(dca["status"], "FILLED", dca)
        with sqlite3.connect(self.path) as connection:
            state = connection.execute(
                """SELECT position_base,dca_used FROM paper_strategy_ledgers
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
            ).fetchone()
            self.assertEqual(state, ("0.018", 1))
            self.assertEqual(connection.execute(
                "SELECT COUNT(*) FROM paper_funding_events"
            ).fetchone()[0], 0)

    def test_simulated_core_entry_is_blocked_by_shared_kill_switch(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            risk_control.set_kill(connection, True, self.now, "TEST_KILL_SWITCH")

        result = self.core.submit(
            self.intent("simulated-core-kill-switch", "0.009"),
            self.book(),
            self.now,
            strategy_event="ENTRY",
        )
        self.assertEqual(result["status"], "REJECTED", result)
        self.assertIn("KILL", result["reason"])
        with sqlite3.connect(self.path) as connection:
            self.assertEqual(connection.execute(
                """SELECT position_base FROM paper_strategy_ledgers
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
            ).fetchone()[0], "0")
            self.assertEqual(connection.execute(
                "SELECT COUNT(*) FROM paper_risk_reservations"
            ).fetchone()[0], 0)


    def test_simulated_core_entry_at_exact_one_percent_margin_boundary_is_accepted(self):
        intent = self.intent("simulated-core-exact-margin-boundary", "0.01")
        intent["limitPrice"] = "100"
        book = self.book()
        book["bids"] = [{"price": "99.9", "quantity": "1"}]
        book["asks"] = [{"price": "100", "quantity": "1"}]

        result = self.core.submit(
            intent, book, self.now, strategy_event="ENTRY",
        )

        self.assertEqual(result["status"], "FILLED", result)
        with sqlite3.connect(self.path) as connection:
            reservation = connection.execute(
                """SELECT reserved_margin_quote,reserved_notional_quote,
                          leverage,equity_basis_quote,status
                   FROM paper_risk_reservations WHERE intent_id=?""",
                ("simulated-core-exact-margin-boundary",),
            ).fetchone()
            position = connection.execute(
                """SELECT position_base FROM paper_strategy_ledgers
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
            ).fetchone()[0]
        self.assertEqual(reservation, ("1", "1", "1", "100", "CONSUMED"))
        self.assertEqual(position, "0.01")

    def test_simulated_daily_loss_boundary_latches_shared_kill_switch(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """UPDATE paper_strategy_ledgers
                   SET position_base='0.1',average_entry_price='100'
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
            )
        account_scope = PaperLedger(self.path)
        record_account_mark(
            account_scope, "80", self.now - 60_000, self.now,
            "sha256:" + "e" * 64,
        )

        result = self.core.submit(
            self.intent("simulated-core-daily-loss-boundary", "0.11"),
            self.book(), self.now, strategy_event="DCA",
        )

        self.assertEqual(result["status"], "REJECTED", result)
        self.assertEqual(result["reason"], "DAILY_LOSS_LIMIT")
        with sqlite3.connect(self.path) as connection:
            latch = connection.execute(
                "SELECT paused,killed,reason FROM paper_risk_control WHERE id=1"
            ).fetchone()
            order = connection.execute(
                "SELECT status,document FROM paper_orders WHERE intent_id=?",
                ("simulated-core-daily-loss-boundary",),
            ).fetchone()
            reservation_count = connection.execute(
                "SELECT COUNT(*) FROM paper_risk_reservations WHERE intent_id=?",
                ("simulated-core-daily-loss-boundary",),
            ).fetchone()[0]
            fill_count = connection.execute(
                """SELECT COUNT(*) FROM paper_account_event_journal
                   WHERE intent_id=? AND event_type='FILL'""",
                ("simulated-core-daily-loss-boundary",),
            ).fetchone()[0]
            position = connection.execute(
                """SELECT position_base FROM paper_strategy_ledgers
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
            ).fetchone()[0]
        self.assertEqual(latch, (0, 1, "DAILY_LOSS_LIMIT"))
        self.assertIsNotNone(order)
        self.assertEqual(order[0], "REJECTED")
        self.assertEqual(json.loads(order[1])["reason"], "DAILY_LOSS_LIMIT")
        self.assertEqual(reservation_count, 0)
        self.assertEqual(fill_count, 0)
        self.assertEqual(position, "0.1")

    def test_simulated_drawdown_boundary_latches_shared_kill_switch(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """UPDATE paper_strategy_ledgers
                   SET position_base='1',average_entry_price='100'
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
            )
        account_scope = PaperLedger(self.path)
        record_account_mark(
            account_scope, "90", self.now - 60_000, self.now,
            "sha256:" + "f" * 64,
        )

        result = self.core.submit(
            self.intent("simulated-core-drawdown-boundary", "1.001"),
            self.book(), self.now, strategy_event="DCA",
        )

        self.assertEqual(result["status"], "REJECTED", result)
        self.assertEqual(result["reason"], "MAX_DRAWDOWN_LIMIT")
        with sqlite3.connect(self.path) as connection:
            latch = connection.execute(
                "SELECT paused,killed,reason FROM paper_risk_control WHERE id=1"
            ).fetchone()
            order = connection.execute(
                "SELECT status,document FROM paper_orders WHERE intent_id=?",
                ("simulated-core-drawdown-boundary",),
            ).fetchone()
            reservation_count = connection.execute(
                "SELECT COUNT(*) FROM paper_risk_reservations WHERE intent_id=?",
                ("simulated-core-drawdown-boundary",),
            ).fetchone()[0]
            fill_count = connection.execute(
                """SELECT COUNT(*) FROM paper_account_event_journal
                   WHERE intent_id=? AND event_type='FILL'""",
                ("simulated-core-drawdown-boundary",),
            ).fetchone()[0]
            position = connection.execute(
                """SELECT position_base FROM paper_strategy_ledgers
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
            ).fetchone()[0]
        self.assertEqual(latch, (0, 1, "MAX_DRAWDOWN_LIMIT"))
        self.assertIsNotNone(order)
        self.assertEqual(order[0], "REJECTED")
        self.assertEqual(json.loads(order[1])["reason"], "MAX_DRAWDOWN_LIMIT")
        self.assertEqual(reservation_count, 0)
        self.assertEqual(fill_count, 0)
        self.assertEqual(position, "1")


    def test_simulated_ledger_rejects_independent_risk_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "override.sqlite3"
            with self.assertRaisesRegex(
                ValueError, "SIMULATED_RISK_LIMITS_OVERRIDE_FORBIDDEN"
            ):
                PaperLedger(
                    path,
                    strategy_id="STRATEGY_CORE",
                    source_sha="b" * 40,
                    risk_limits={
                        "maxDrawdownPct": "1",
                        "maxDailyLossUsdt": "0.1",
                        "maxExposureUsdt": "1",
                    },
                    simulated_contract_bytes=self.contract,
                    simulated_initialized_at_ms=self.now,
                )

    def test_existing_simulated_core_ledger_requires_validated_contract(self):
        with self.assertRaisesRegex(
            ValueError, "SIMULATED_RISK_CONTRACT_REQUIRED"
        ):
            PaperLedger(
                self.path,
                strategy_id="STRATEGY_CORE",
                source_sha="c" * 40,
            )


    def test_simulated_ai_ledger_uses_same_contract_limits_and_its_leverage(self):
        ai = PaperLedger(
            self.path,
            max_position_base="1",
            fee_rate="0.001",
            strategy_id="AI_FREQAI",
            source_sha="a" * 40,
            leverage="3",
            simulated_contract_bytes=self.contract,
        )
        self.assertEqual(dict(ai.risk_limits), {
            "maxDrawdownPct": "10",
            "maxDailyLossUsdt": "2",
            "maxExposureUsdt": "10",
            "maxOrderMarginPct": "1",
        })
        result = ai.submit(
            self.intent("simulated-ai-contract-entry", "0.0299"),
            self.book(),
            self.now,
            strategy_event="ENTRY",
        )
        self.assertEqual(result["status"], "FILLED", result)
        with sqlite3.connect(self.path) as connection:
            reservation = connection.execute(
                """SELECT reserved_margin_quote,reserved_notional_quote,
                          leverage,equity_basis_quote,status
                   FROM paper_risk_reservations WHERE intent_id=?""",
                ("simulated-ai-contract-entry",),
            ).fetchone()
        self.assertEqual(reservation[2:], ("3", "100", "CONSUMED"))
        self.assertLessEqual(float(reservation[0]), 1.0)

    def test_simulated_risk_limits_are_immutable_after_contract_binding(self):
        with self.assertRaises(TypeError):
            self.core.risk_limits["maxExposureUsdt"] = "1000"

    def test_simulated_reopen_rejects_contract_bytes_with_different_digest(self):
        contract = json.loads(self.contract)
        different_encoding = json.dumps(contract, indent=2).encode("utf-8")
        with self.assertRaisesRegex(
            ValueError, "SIMULATED_RISK_CONTRACT_MISMATCH"
        ):
            PaperLedger(
                self.path,
                strategy_id="STRATEGY_CORE",
                source_sha="d" * 40,
                simulated_contract_bytes=different_encoding,
            )


if __name__ == "__main__":
    unittest.main()
