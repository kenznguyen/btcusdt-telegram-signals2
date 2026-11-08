"""RED contract tests for independent CORE/AI ledgers and shared risk.

The implementation module is intentionally absent in this RED increment.
This contract preserves independent strategy accounting while the shared risk
engine evaluates gross exposure across both ledgers.
"""
from concurrent.futures import ThreadPoolExecutor
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
        self.core.restore_position("core-1", side="LONG", quantity="0.01",
                               entry_price="100000", margin_used="100")
        self.ai.restore_position("ai-1", side="SHORT", quantity="0.02",
                             entry_price="100000", margin_used="100")

        core = self.core.snapshot()
        ai = self.ai.snapshot()
        self.assertEqual([p.position_id for p in core.positions], ["core-1"])
        self.assertEqual([p.position_id for p in ai.positions], ["ai-1"])
        self.assertEqual(core.positions[0].side, "LONG")
        self.assertEqual(ai.positions[0].side, "SHORT")

    def test_dca_state_is_independent_between_strategies(self):
        self.core.restore_position("core-1", side="LONG", quantity="0.01",
                               entry_price="100000", margin_used="100")
        self.ai.restore_position("ai-1", side="SHORT", quantity="0.01",
                             entry_price="100000", margin_used="100")
        self.core.restore_dca("core-1", quantity="0.01", price="99000",
                             margin_used="100")

        self.assertEqual(self.core.snapshot().positions[0].dca_count, 1)
        self.assertEqual(self.ai.snapshot().positions[0].dca_count, 0)

    def test_equity_and_realized_pnl_are_independent(self):
        self.core.apply_realized_pnl(pnl="250", fees="5")
        self.assertEqual(self.core.snapshot().equity, Decimal("10245"))
        self.assertEqual(self.ai.snapshot().equity, Decimal("10000"))

    def test_ledger_state_survives_reopening_without_cross_contamination(self):
        self.core.restore_position("core-1", side="LONG", quantity="0.01",
                               entry_price="100000", margin_used="100")
        self.ai.restore_position("ai-1", side="SHORT", quantity="0.01",
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

        self.core.restore_position("core-1", side="LONG", quantity="0.01",
                               entry_price="100000", margin_used=str(entry.required_margin))
        dca = self.risk.admit_dca(
            account_equity="11000", position_id="core-1",
            core_snapshot=self.core.snapshot(), ai_snapshot=self.ai.snapshot(),
            data_fresh=True, state_reconciled=True,
        )
        self.assertTrue(dca.accepted)
        self.assertEqual(dca.required_margin, Decimal("110"))

    def test_shared_risk_counts_gross_margin_without_offsetting_opposite_sides(self):
        self.core.restore_position("core-long", side="LONG", quantity="0.01",
                               entry_price="100000", margin_used="100")
        self.ai.restore_position("ai-short", side="SHORT", quantity="0.01",
                             entry_price="100000", margin_used="100")
        decision = self.risk.admit_entry(
            account_equity="10000", core_snapshot=self.core.snapshot(),
            ai_snapshot=self.ai.snapshot(), data_fresh=True, state_reconciled=True,
        )
        self.assertEqual(decision.gross_margin_used, Decimal("200"))
        self.assertEqual(decision.gross_exposure, Decimal("2000"))
        self.assertEqual(decision.required_margin, Decimal("100"))
        self.assertTrue(decision.accepted)

    def test_no_fixed_position_count_cap_when_shared_risk_budget_allows_entries(self):
        for index in range(12):
            decision = self.risk.admit_entry(
                account_equity="10000", core_snapshot=self.core.snapshot(),
                ai_snapshot=self.ai.snapshot(), data_fresh=True, state_reconciled=True,
            )
            self.assertTrue(decision.accepted, f"entry {index} unexpectedly blocked")
            self.core.restore_position(
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

        self.core.restore_position("core-1", side="LONG", quantity="0.01",
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


    def test_stale_data_and_unreconciled_state_fail_closed(self):
        stale = self.risk.admit_entry(
            account_equity="10000", core_snapshot=self.core.snapshot(),
            ai_snapshot=self.ai.snapshot(), data_fresh=False, state_reconciled=True,
        )
        unreconciled = self.risk.admit_entry(
            account_equity="10000", core_snapshot=self.core.snapshot(),
            ai_snapshot=self.ai.snapshot(), data_fresh=True, state_reconciled=False,
        )
        self.assertFalse(stale.accepted)
        self.assertEqual(stale.reason, "STALE_DATA")
        self.assertFalse(unreconciled.accepted)
        self.assertEqual(unreconciled.reason, "UNRECONCILED_STATE")

    def test_shared_gross_margin_must_leave_one_percent_for_next_admission(self):
        self.core.restore_position("core-heavy", side="LONG", quantity="1",
                               entry_price="100000", margin_used="9950")
        decision = self.risk.admit_entry(
            account_equity="10000", core_snapshot=self.core.snapshot(),
            ai_snapshot=self.ai.snapshot(), data_fresh=True, state_reconciled=True,
        )
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "INSUFFICIENT_MARGIN")
        self.assertEqual(decision.gross_margin_used, Decimal("9950"))
        self.assertEqual(decision.required_margin, Decimal("100"))

    def test_dca_rejects_missing_or_ambiguous_position_identity(self):
        missing = self.risk.admit_dca(
            account_equity="10000", position_id="missing",
            core_snapshot=self.core.snapshot(), ai_snapshot=self.ai.snapshot(),
            data_fresh=True, state_reconciled=True,
        )
        self.assertFalse(missing.accepted)
        self.assertEqual(missing.reason, "POSITION_NOT_UNIQUELY_FOUND")

        self.core.restore_position("shared-id", side="LONG", quantity="0.01",
                               entry_price="100000", margin_used="100")
        self.ai.restore_position("shared-id", side="SHORT", quantity="0.01",
                             entry_price="100000", margin_used="100")
        ambiguous = self.risk.admit_dca(
            account_equity="10000", position_id="shared-id",
            core_snapshot=self.core.snapshot(), ai_snapshot=self.ai.snapshot(),
            data_fresh=True, state_reconciled=True,
        )
        self.assertFalse(ambiguous.accepted)
        self.assertEqual(ambiguous.reason, "POSITION_NOT_UNIQUELY_FOUND")


    def test_competing_core_and_ai_reservations_are_serialized_against_shared_collateral(self):
        self.core.restore_position("core-heavy", side="LONG", quantity="1",
                               entry_price="100000", margin_used="9850")
        core_engine = SharedRiskEngine(self.db)
        ai_engine = SharedRiskEngine(self.db)

        def reserve(engine, strategy_id, reservation_id):
            return engine.reserve_entry(
                reservation_id=reservation_id, strategy_id=strategy_id,
                position_id=f"{strategy_id.lower()}-new", account_equity="10000",
                notional_exposure="1000", data_fresh=True, state_reconciled=True,
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(reserve, core_engine, "CORE", "reserve-core"),
                pool.submit(reserve, ai_engine, "AI", "reserve-ai"),
            ]
            decisions = [future.result() for future in futures]

        self.assertEqual(sum(decision.accepted for decision in decisions), 1)
        rejected = next(decision for decision in decisions if not decision.accepted)
        self.assertEqual(rejected.reason, "INSUFFICIENT_MARGIN")

    def test_reserved_entry_is_consumed_once_by_its_own_ledger(self):
        engine = SharedRiskEngine(self.db)
        decision = engine.reserve_entry(
            reservation_id="entry-core-1", strategy_id="CORE",
            position_id="core-reserved-1", account_equity="10000",
            notional_exposure="1000", data_fresh=True, state_reconciled=True,
        )
        self.assertTrue(decision.accepted)
        self.core.record_reserved_entry(
            reservation_id="entry-core-1", position_id="core-reserved-1",
            side="LONG", quantity="0.01", entry_price="100000",
        )
        position = self.core.snapshot().positions[0]
        self.assertEqual(position.margin_used, Decimal("100"))
        with self.assertRaises(ValueError):
            self.core.record_reserved_entry(
                reservation_id="entry-core-1", position_id="core-reserved-1",
                side="LONG", quantity="0.01", entry_price="100000",
            )

    def test_reserved_dca_is_consumed_once_and_updates_only_target_ledger(self):
        self.core.restore_position("core-1", side="LONG", quantity="0.01",
                               entry_price="100000", margin_used="100")
        self.ai.restore_position("ai-1", side="SHORT", quantity="0.01",
                             entry_price="100000", margin_used="100")
        engine = SharedRiskEngine(self.db)
        decision = engine.reserve_dca(
            reservation_id="dca-core-1", strategy_id="CORE",
            position_id="core-1", account_equity="10000",
            notional_exposure="1000", data_fresh=True, state_reconciled=True,
        )
        self.assertTrue(decision.accepted)
        self.core.record_reserved_dca(
            reservation_id="dca-core-1", position_id="core-1",
            quantity="0.01", price="99000",
        )
        self.assertEqual(self.core.snapshot().positions[0].dca_count, 1)
        self.assertEqual(self.core.snapshot().positions[0].margin_used, Decimal("200"))
        self.assertEqual(self.ai.snapshot().positions[0].dca_count, 0)
        with self.assertRaises(ValueError):
            self.core.record_reserved_dca(
                reservation_id="dca-core-1", position_id="core-1",
                quantity="0.01", price="99000",
            )

    def test_duplicate_reservation_id_cannot_be_reused_by_other_strategy(self):
        engine = SharedRiskEngine(self.db)
        first = engine.reserve_entry(
            reservation_id="duplicate-id", strategy_id="CORE",
            position_id="core-1", account_equity="10000",
            notional_exposure="1000", data_fresh=True, state_reconciled=True,
        )
        second = engine.reserve_entry(
            reservation_id="duplicate-id", strategy_id="AI",
            position_id="ai-1", account_equity="10000",
            notional_exposure="1000", data_fresh=True, state_reconciled=True,
        )
        self.assertTrue(first.accepted)
        self.assertFalse(second.accepted)
        self.assertEqual(second.reason, "DUPLICATE_RESERVATION")


if __name__ == "__main__":
    unittest.main()
