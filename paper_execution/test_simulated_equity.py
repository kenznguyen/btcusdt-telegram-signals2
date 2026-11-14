import hashlib
import json
import sqlite3
import unittest

from paper_execution.simulated_capital import DEFAULT_SIMULATED_CAPITAL_CONTRACT
from paper_execution.simulated_equity import initialize_simulated_equity


class SimulatedEquityInitializationTest(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
            CREATE TABLE paper_accounts (
                account_id INTEGER PRIMARY KEY, mode TEXT NOT NULL,
                initial_capital TEXT NOT NULL, currency TEXT NOT NULL
            );
            CREATE TABLE paper_account_risk_state (
                account_id INTEGER PRIMARY KEY, high_water_mark_quote TEXT,
                daily_baseline_utc_day_ms INTEGER,
                daily_baseline_equity_quote TEXT, risk_ready INTEGER NOT NULL,
                unavailable_reason TEXT, updated_at_ms INTEGER NOT NULL,
                version INTEGER NOT NULL
            );
            CREATE TABLE paper_strategy_ledgers (
                account_id INTEGER NOT NULL, strategy_id TEXT NOT NULL,
                position_base TEXT NOT NULL, average_entry_price TEXT NOT NULL,
                realized_pnl_quote TEXT NOT NULL, fees_quote TEXT NOT NULL,
                funding_quote TEXT NOT NULL, initial_margin_quote TEXT NOT NULL
            );
            CREATE TABLE paper_account_adjustments (
                account_id INTEGER NOT NULL, adjustment_type TEXT NOT NULL,
                amount_quote TEXT NOT NULL
            );
            CREATE TABLE paper_orders (order_id TEXT PRIMARY KEY);
            CREATE TABLE paper_funding_events (event_id TEXT PRIMARY KEY);
            CREATE TABLE paper_funding_coverage (coverage_id TEXT PRIMARY KEY);
            CREATE TABLE paper_account_equity_cutovers (cutover_id TEXT PRIMARY KEY);
            CREATE TABLE paper_funding_reconciliations (reconciliation_id TEXT PRIMARY KEY);
        """)
        self.db.execute(
            "INSERT INTO paper_accounts VALUES (1,'PAPER','100','USDT')"
        )
        self.db.execute(
            "INSERT INTO paper_account_risk_state VALUES (1,NULL,NULL,NULL,0,'CUTOVER_REQUIRED',0,1)"
        )
        for strategy in ("STRATEGY_CORE", "AI_FREQAI", "LEGACY_UNATTRIBUTED"):
            self.db.execute(
                """INSERT INTO paper_strategy_ledgers VALUES
                   (1,?,'0','0','0','0','0','0')""", (strategy,)
            )
        self.contract = json.dumps(
            DEFAULT_SIMULATED_CAPITAL_CONTRACT, separators=(",", ":")
        ).encode("utf-8")
        self.now = 1_800_000_000_000

    def tearDown(self):
        self.db.close()

    def initialize(self):
        return initialize_simulated_equity(
            self.db, contract_bytes=self.contract, initialized_at_ms=self.now
        )

    def test_creates_simulated_equity_origin_seed_baseline_and_hwm(self):
        self.db.execute("BEGIN IMMEDIATE")
        result = self.initialize()
        self.db.commit()

        self.assertEqual(result["initialEquityQuote"], "100")
        self.assertEqual(result["highWaterMarkQuote"], "100")
        self.assertEqual(result["dailyBaselineEquityQuote"], "100")
        self.assertEqual(
            result["contractSha256"], hashlib.sha256(self.contract).hexdigest()
        )
        risk = self.db.execute(
            """SELECT high_water_mark_quote,daily_baseline_utc_day_ms,
                      daily_baseline_equity_quote,risk_ready,unavailable_reason
               FROM paper_account_risk_state WHERE account_id=1"""
        ).fetchone()
        self.assertEqual(risk, (
            "100", self.now // 86_400_000 * 86_400_000,
            "100", 0, "SIMULATED_INITIAL_MARK_REQUIRED"
        ))
        self.assertEqual(self.db.execute(
            "SELECT COUNT(*) FROM paper_simulated_capital_seed_events"
        ).fetchone()[0], 1)
        self.assertEqual(self.db.execute(
            "SELECT COUNT(*) FROM paper_funding_events"
        ).fetchone()[0], 0)
        self.assertEqual(self.db.execute(
            "SELECT COUNT(*) FROM paper_simulated_equity_origin"
        ).fetchone()[0], 1)

    def test_restart_is_idempotent_and_preserves_original_origin(self):
        self.db.execute("BEGIN IMMEDIATE")
        first = self.initialize()
        self.db.commit()
        self.db.execute("BEGIN IMMEDIATE")
        second = initialize_simulated_equity(
            self.db, contract_bytes=self.contract,
            initialized_at_ms=self.now + 90_000_000
        )
        self.db.commit()

        self.assertEqual(first, second)
        self.assertEqual(self.db.execute(
            "SELECT COUNT(*) FROM paper_simulated_equity_origin"
        ).fetchone()[0], 1)
        self.assertEqual(self.db.execute(
            "SELECT COUNT(*) FROM paper_simulated_capital_seed_events"
        ).fetchone()[0], 1)

    def test_funded_or_nonempty_account_is_rejected_without_mixing(self):
        self.db.execute("INSERT INTO paper_funding_events VALUES ('funded')")
        self.db.execute("BEGIN IMMEDIATE")
        with self.assertRaisesRegex(ValueError, "SIMULATED_ACCOUNT_NOT_PRISTINE"):
            self.initialize()
        self.db.rollback()
        self.assertEqual(self.db.execute(
            "SELECT COUNT(*) FROM paper_simulated_equity_origin"
        ).fetchone()[0] if self.db.execute(
            "SELECT 1 FROM sqlite_master WHERE name='paper_simulated_equity_origin'"
        ).fetchone() else 0, 0)

    def test_contract_mismatch_fails_closed(self):
        self.db.execute("BEGIN IMMEDIATE")
        self.initialize()
        self.db.commit()
        altered = json.dumps(
            {**DEFAULT_SIMULATED_CAPITAL_CONTRACT, "riskLimits": {
                **DEFAULT_SIMULATED_CAPITAL_CONTRACT["riskLimits"],
                "maxDailyLossUsdt": "3",
            }}, separators=(",", ":")
        ).encode()
        self.db.execute("BEGIN IMMEDIATE")
        with self.assertRaisesRegex(ValueError, "SIMULATED_ORIGIN_CONTRACT_MISMATCH"):
            initialize_simulated_equity(
                self.db, contract_bytes=altered, initialized_at_ms=self.now
            )
        self.db.rollback()

    def test_any_initialization_failure_rolls_back_account_origin_and_seed(self):
        self.db.execute("CREATE TRIGGER fail_equity_origin BEFORE INSERT ON paper_simulated_equity_origin "
                        "BEGIN SELECT RAISE(ABORT,'INJECTED_FAILURE'); END")
        self.db.execute("BEGIN IMMEDIATE")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "INJECTED_FAILURE"):
            self.initialize()
        self.db.rollback()
        for table in (
            "paper_simulated_capital_origin",
            "paper_simulated_capital_seed_events",
            "paper_simulated_equity_origin",
        ):
            exists = self.db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone()
            self.assertIsNone(exists)

    def test_origin_and_equity_records_are_immutable(self):
        self.db.execute("BEGIN IMMEDIATE")
        self.initialize()
        self.db.commit()
        with self.assertRaisesRegex(sqlite3.IntegrityError, "SIMULATED_EQUITY_ORIGIN_IMMUTABLE"):
            self.db.execute(
                "UPDATE paper_simulated_equity_origin SET initial_equity_quote='200'"
            )
        with self.assertRaisesRegex(sqlite3.IntegrityError, "SIMULATED_EQUITY_ORIGIN_IMMUTABLE"):
            self.db.execute("DELETE FROM paper_simulated_equity_origin")


if __name__ == "__main__":
    unittest.main()
