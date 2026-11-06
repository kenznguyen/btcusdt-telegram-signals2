from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import sqlite3
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
        limits = {"maxDrawdownPct": "50", "maxDailyLossUsdt": "50", "maxExposureUsdt": "1000"}
        self.core = PaperLedger(self.path, max_position_base="1", fee_rate="0.001",
                                strategy_id="STRATEGY_CORE", source_sha="a" * 40,
                                risk_limits=limits, require_risk_limits=True)
        self.ai = PaperLedger(self.path, max_position_base="1", fee_rate="0.001",
                              strategy_id="AI_FREQAI", source_sha="a" * 40,
                              risk_limits=limits, require_risk_limits=True)
        with sqlite3.connect(self.path) as connection:
            day = self.now // 86_400_000 * 86_400_000
            connection.execute(
                """UPDATE paper_account_risk_state SET high_water_mark_quote='100',
                   daily_baseline_utc_day_ms=?,daily_baseline_equity_quote='100',
                   last_equity_quote='100',last_mark_price='100',mark_observed_at_ms=?,
                   mark_candle_close_ms=?,dataset_version='sha256:dual-ledger-seed',
                   risk_ready=1,unavailable_reason=NULL,updated_at_ms=? WHERE account_id=1""",
                (day, self.now, self.now-60_000, self.now),
            )

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
            self.intent("ai-short", "-0.1", "100", "ai-book"),
            self.book(self.now + 1),
            self.now + 1,
        )

        self.assertEqual(core_order["status"], "FILLED", core_order)
        self.assertEqual(ai_order["status"], "FILLED", ai_order)

        self.assertEqual(
            self.core.snapshot()["positionBase"], "0.1"
        )
        self.assertEqual(
            self.ai.snapshot()["positionBase"], "-0.1"
        )

        reopened_core = PaperLedger(self.path, max_position_base="1", strategy_id="STRATEGY_CORE", source_sha="a" * 40)
        reopened_ai = PaperLedger(self.path, max_position_base="1", strategy_id="AI_FREQAI", source_sha="a" * 40)
        self.assertEqual(
            reopened_core.snapshot()["positionBase"], "0.1"
        )
        self.assertEqual(
            reopened_ai.snapshot()["positionBase"], "-0.1"
        )

    def test_entry_and_dca_reserve_one_percent_of_admission_time_equity_per_ledger(self):
        entry = self.core.submit(
            self.intent("core-entry", "0.1", "100.1", "core-entry"),
            self.book(self.now), self.now,
        )
        self.assertEqual(entry["status"], "FILLED", entry)
        dca = self.core.submit(
            self.intent("core-dca", "0.2", "100.1", "core-dca"),
            self.book(self.now+1), self.now+1, strategy_event="DCA",
        )
        self.assertEqual(dca["status"], "FILLED", dca)
        self.assertTrue(self.core.strategy_state()["dcaUsed"])
        self.assertFalse(self.ai.strategy_state()["dcaUsed"])

        with sqlite3.connect(self.path) as connection:
            rows = connection.execute(
                """SELECT reservation_kind,equity_basis_quote,reserved_margin_quote,
                          reserved_notional_quote,status
                   FROM paper_risk_reservations WHERE strategy_id='STRATEGY_CORE'
                   ORDER BY created_at_ms"""
            ).fetchall()
        self.assertEqual([row[0] for row in rows], ["ENTRY", "DCA"])
        for _, basis, margin, notional, status in rows:
            self.assertEqual(Decimal(margin), Decimal(basis)*Decimal("0.01"))
            self.assertEqual(Decimal(notional), Decimal(margin)*Decimal("13"))
            self.assertEqual(status, "CONSUMED")

        repeated_dca = self.core.submit(
            self.intent("core-dca-again", "0.3", "100.1", "core-dca-again"),
            self.book(self.now+2), self.now+2, strategy_event="DCA",
        )
        self.assertEqual(repeated_dca["reason"], "DCA_ALREADY_USED")

    def test_opposite_positions_are_counted_as_gross_exposure_without_netting(self):
        self.core.risk_limits["maxExposureUsdt"] = "15"
        self.ai.risk_limits["maxExposureUsdt"] = "15"
        core = self.core.submit(
            self.intent("gross-core", "0.1", "100.1", "gross-core"),
            self.book(self.now), self.now,
        )
        ai = self.ai.submit(
            self.intent("gross-ai", "-0.1", "100", "gross-ai"),
            self.book(self.now+1), self.now+1,
        )
        self.assertEqual(core["status"], "FILLED", core)
        self.assertEqual(ai["reason"], "MAX_EXPOSURE_LIMIT", ai)
        self.assertEqual(self.core.snapshot()["positionBase"], "0.1")
        self.assertEqual(self.ai.snapshot()["positionBase"], "0")

    def test_missing_account_risk_inputs_fail_closed(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "UPDATE paper_account_risk_state SET risk_ready=0,unavailable_reason='TEST_MISSING' WHERE account_id=1"
            )
        order = self.core.submit(
            self.intent("risk-not-ready", "0.1", "100.1", "risk-not-ready"),
            self.book(self.now), self.now,
        )
        self.assertEqual(order["status"], "REJECTED")
        self.assertEqual(order["reason"], "RISK_INPUTS_UNAVAILABLE")
        self.assertEqual(self.core.snapshot()["positionBase"], "0")

    def test_kill_switch_blocks_increase_but_allows_strategy_scoped_reduction(self):
        opened = self.core.submit(
            self.intent("kill-open", "0.1", "100.1", "kill-open"),
            self.book(self.now), self.now,
        )
        self.assertEqual(opened["status"], "FILLED", opened)
        self.core.set_killed(True, self.now+1, "TEST_KILL")
        reduced = self.core.submit(
            self.intent("kill-reduce", "0.05", "100", "kill-reduce"),
            self.book(self.now+2), self.now+2, strategy_event="EXIT",
        )
        self.assertEqual(reduced["status"], "FILLED", reduced)
        self.assertEqual(self.core.snapshot()["positionBase"], "0.05")
        blocked = self.core.submit(
            self.intent("kill-increase", "0.08", "100.1", "kill-increase"),
            self.book(self.now+3), self.now+3, strategy_event="DCA",
        )
        self.assertEqual(blocked["reason"], "KILL_SWITCH")

    def test_shared_book_depth_is_reserved_across_core_and_ai(self):
        shared_book = self.book(self.now)
        shared_book["asks"] = [{"price": "100.1", "quantity": "0.15"}]
        core = self.core.submit(
            self.intent("book-core", "0.1", "100.1", "book-core"),
            shared_book, self.now,
        )
        ai = self.ai.submit(
            self.intent("book-ai", "0.1", "100.1", "book-ai"),
            shared_book, self.now,
        )
        self.assertEqual(core["filledBase"], "0.1")
        self.assertEqual(ai["status"], "PARTIALLY_FILLED", ai)
        self.assertEqual(ai["filledBase"], "0.05")
        self.assertEqual(self.ai.snapshot()["positionBase"], "0.05")
        with sqlite3.connect(self.path) as connection:
            used = connection.execute(
                """SELECT SUM(CAST(reserved_quantity AS REAL))
                   FROM paper_book_level_reservations WHERE book_id=? AND side='BUY'
                     AND price='100.1' AND status IN ('ACTIVE','CONSUMED')""",
                (connection.execute(
                    "SELECT book_id FROM paper_book_level_reservations LIMIT 1"
                ).fetchone()[0],),
            ).fetchone()[0]
        self.assertAlmostEqual(used, 0.15)

    def test_concurrent_core_ai_admissions_cannot_breach_gross_exposure(self):
        self.core.risk_limits["maxExposureUsdt"] = "15"
        self.ai.risk_limits["maxExposureUsdt"] = "15"
        def core_submit():
            return self.core.submit(
                self.intent("concurrent-core", "0.1", "100.1", "concurrent-core"),
                self.book(self.now), self.now,
            )
        def ai_submit():
            return self.ai.submit(
                self.intent("concurrent-ai", "0.1", "100.1", "concurrent-ai"),
                self.book(self.now+1), self.now+1,
            )
        with ThreadPoolExecutor(max_workers=2) as pool:
            core_future = pool.submit(core_submit)
            ai_future = pool.submit(ai_submit)
            results = [core_future.result(), ai_future.result()]
        self.assertCountEqual([result["status"] for result in results], ["FILLED", "REJECTED"])
        with sqlite3.connect(self.path) as connection:
            positions = connection.execute(
                "SELECT position_base FROM paper_strategy_ledgers WHERE account_id=1"
            ).fetchall()
        gross = sum((abs(Decimal(row[0]))*Decimal("100") for row in positions), Decimal(0))
        self.assertLessEqual(gross, Decimal("15"))


if __name__ == "__main__":
    unittest.main()
