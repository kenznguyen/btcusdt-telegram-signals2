"""RED contract tests for independent CORE/AI ledgers and shared risk.

The implementation module is intentionally absent in this RED increment.
This contract preserves independent strategy accounting while the shared risk
engine evaluates gross exposure across both ledgers.
"""
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest

from quant_system.dual_ledger import SharedRiskEngine, StrategyLedger


class DualLedgerContractTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "dual-ledger.sqlite3"
        self.core = StrategyLedger(self.db, strategy_id="CORE", initial_equity="10000")
        self.ai = StrategyLedger(self.db, strategy_id="AI", initial_equity="10000")
        self.risk = SharedRiskEngine()

    def test_core_and_ai_positions_are_isolated_in_one_persistent_store(self):
        self.core.record_entry("core-1", side="LONG", quantity="0.01",
                               entry_price="100000", margin_used="100")
        self.ai.record_entry("ai-1", side="SHORT", quantity="0.02",
                             entry_price="100000", margin_used="100")

        core = self.core.snapshot()
        ai = self.ai.snapshot()
        self.assertEqual([p.position_id for p in core.positions], ["core-1"])
        self.assertEqual([p.position_id for p in ai.positions], ["ai-1"])
        self.assertEqual(core.positions[0].side, "LONG")
        self.assertEqual(ai.positions[0].side, "SHORT")

    def test_dca_state_is_independent_between_strategies(self):
        self.core.record_entry("core-1", side="LONG", quantity="0.01",
                               entry_price="100000", margin_used="100")
        self.ai.record_entry("ai-1", side="SHORT", quantity="0.01",
                             entry_price="100000", margin_used="100")
        self.core.record_dca("core-1", quantity="0.01", price="99000",
                             margin_used="100")

        self.assertEqual(self.core.snapshot().positions[0].dca_count, 1)
        self.assertEqual(self.ai.snapshot().positions[0].dca_count, 0)

    def test_equity_and_realized_pnl_are_independent(self):
        self.core.apply_realized_pnl(pnl="250", fees="5")
        self.assertEqual(self.core.snapshot().equity, Decimal("10245"))
        self.assertEqual(self.ai.snapshot().equity, Decimal("10000"))

    def test_ledger_state_survives_reopening_without_cross_contamination(self):
        self.core.record_entry("core-1", side="LONG", quantity="0.01",
                               entry_price="100000", margin_used="100")
        self.ai.record_entry("ai-1", side="SHORT", quantity="0.01",
                             entry_price="100000", margin_used="100")

        core_reopened = StrategyLedger(self.db, strategy_id="CORE", initial_equity="10000")
        ai_reopened = StrategyLedger(self.db, strategy_id="AI", initial_equity="10000")
        self.assertEqual(core_reopened.snapshot(), self.core.snapshot())
        self.assertEqual(ai_reopened.snapshot(), self.ai.snapshot())

    def test_each_entry_and_dca_reserves_one_percent_of_equity_at_admission(self):
        empty_core = self.core.snapshot()
        empty_ai = self.ai.snapshot()
        entry = self.risk.admit_entry(
            account_equity="10000", core_snapshot=empty_core,
            ai_snapshot=empty_ai, data_fresh=True, state_reconciled=True,
        )
        self.assertTrue(entry.accepted)
        self.assertEqual(entry.required_margin, Decimal("100"))

        self.core.record_entry("core-1", side="LONG", quantity="0.01",
                               entry_price="100000", margin_used=str(entry.required_margin))
        dca = self.risk.admit_dca(
            account_equity="11000", position_id="core-1",
            core_snapshot=self.core.snapshot(), ai_snapshot=self.ai.snapshot(),
            data_fresh=True, state_reconciled=True,
        )
        self.assertTrue(dca.accepted)
        self.assertEqual(dca.required_margin, Decimal("110"))

    def test_shared_risk_counts_gross_margin_without_offsetting_opposite_sides(self):
        self.core.record_entry("core-long", side="LONG", quantity="0.01",
                               entry_price="100000", margin_used="100")
        self.ai.record_entry("ai-short", side="SHORT", quantity="0.01",
                             entry_price="100000", margin_used="100")
        decision = self.risk.admit_entry(
            account_equity="10000", core_snapshot=self.core.snapshot(),
            ai_snapshot=self.ai.snapshot(), data_fresh=True, state_reconciled=True,
        )
        self.assertEqual(decision.gross_margin_used, Decimal("200"))
        self.assertEqual(decision.required_margin, Decimal("100"))
        self.assertTrue(decision.accepted)

    def test_no_fixed_position_count_cap_when_shared_risk_budget_allows_entries(self):
        for index in range(12):
            decision = self.risk.admit_entry(
                account_equity="10000", core_snapshot=self.core.snapshot(),
                ai_snapshot=self.ai.snapshot(), data_fresh=True, state_reconciled=True,
            )
            self.assertTrue(decision.accepted, f"entry {index} unexpectedly blocked")
            self.core.record_entry(
                f"core-{index}", side="LONG", quantity="0.001",
                entry_price="100000", margin_used=str(decision.required_margin),
            )
        self.assertEqual(len(self.core.snapshot().positions), 12)

    def test_kill_switch_blocks_entries_and_dca_but_allows_reductions(self):
        entry = self.risk.admit_entry(
            account_equity="10000", core_snapshot=self.core.snapshot(),
            ai_snapshot=self.ai.snapshot(), data_fresh=True,
            state_reconciled=True, kill_switch=True,
        )
        self.assertFalse(entry.accepted)
        self.assertEqual(entry.reason, "KILL_SWITCH_ACTIVE")

        self.core.record_entry("core-1", side="LONG", quantity="0.01",
                               entry_price="100000", margin_used="100")
        dca = self.risk.admit_dca(
            account_equity="10000", position_id="core-1",
            core_snapshot=self.core.snapshot(), ai_snapshot=self.ai.snapshot(),
            data_fresh=True, state_reconciled=True, kill_switch=True,
        )
        self.assertFalse(dca.accepted)
        reduction = self.risk.admit_reduction(
            strategy_id="CORE", position_id="core-1", quantity="0.005",
            core_snapshot=self.core.snapshot(), ai_snapshot=self.ai.snapshot(),
            kill_switch=True,
        )
        self.assertTrue(reduction.accepted)


if __name__ == "__main__":
    unittest.main()
