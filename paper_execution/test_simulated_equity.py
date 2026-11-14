import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from paper_execution.simulated_capital import DEFAULT_SIMULATED_CAPITAL_CONTRACT
from paper_execution.simulated_equity import initialize_simulated_equity
from paper_execution.ledger import PaperLedger, read_account_risk_snapshot
from paper_execution.account_equity import record_account_mark


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
                adjustment_id TEXT PRIMARY KEY, account_id INTEGER NOT NULL,
                strategy_id TEXT NOT NULL, adjustment_type TEXT NOT NULL,
                amount_quote TEXT NOT NULL, source_table TEXT NOT NULL,
                source_hash TEXT NOT NULL, created_at_ms INTEGER NOT NULL
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
        for adjustment_type in ("LEGACY_REALIZED_PNL", "LEGACY_FEES"):
            self.db.execute(
                """INSERT INTO paper_account_adjustments VALUES
                   (?,?,?,?,'0','paper_state',?,?)""",
                ("legacy-v1:" + adjustment_type, 1, "LEGACY_UNATTRIBUTED",
                 adjustment_type, "a" * 64, 0),
            )
        self.contract = json.dumps(
            DEFAULT_SIMULATED_CAPITAL_CONTRACT, separators=(",", ":")
        ).encode("utf-8")
        self.now = 1_800_000_000_000
        self.db.commit()  # Finish fixture setup before explicit BEGIN IMMEDIATE tests.

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

    def test_restart_does_not_reset_risk_state_after_initialization(self):
        self.db.execute("BEGIN IMMEDIATE")
        self.initialize()
        self.db.commit()
        self.db.execute(
            """UPDATE paper_account_risk_state
               SET high_water_mark_quote='125',daily_baseline_equity_quote='98',
                   daily_baseline_utc_day_ms=?,risk_ready=0,
                   unavailable_reason='SIMULATED_INITIAL_MARK_REQUIRED'
               WHERE account_id=1""",
            (self.now // 86_400_000 * 86_400_000,),
        )
        self.db.commit()
        before = self.db.execute(
            """SELECT high_water_mark_quote,daily_baseline_equity_quote,
                      daily_baseline_utc_day_ms,version
               FROM paper_account_risk_state WHERE account_id=1"""
        ).fetchone()
        self.db.execute("BEGIN IMMEDIATE")
        self.initialize()
        self.db.commit()
        after = self.db.execute(
            """SELECT high_water_mark_quote,daily_baseline_equity_quote,
                      daily_baseline_utc_day_ms,version
               FROM paper_account_risk_state WHERE account_id=1"""
        ).fetchone()
        self.assertEqual(after, before)

    def test_funded_or_nonempty_account_is_rejected_without_mixing(self):
        self.db.execute("INSERT INTO paper_funding_events VALUES ('funded')")
        self.db.commit()
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
            DEFAULT_SIMULATED_CAPITAL_CONTRACT, indent=2
        ).encode("utf-8")
        self.db.execute("BEGIN IMMEDIATE")
        with self.assertRaisesRegex(ValueError, "SIMULATED_ORIGIN_CONTRACT_MISMATCH"):
            initialize_simulated_equity(
                self.db, contract_bytes=altered, initialized_at_ms=self.now
            )
        self.db.rollback()

    def test_any_initialization_failure_rolls_back_account_origin_and_seed(self):
        self.db.execute("CREATE TRIGGER fail_equity_origin BEFORE UPDATE ON paper_account_risk_state "
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


    def test_paperledger_initializes_new_simulated_account_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "simulated.sqlite3"
            PaperLedger(
                path,
                strategy_id="STRATEGY_CORE",
                source_sha="a" * 40,
                simulated_contract_bytes=self.contract,
                simulated_initialized_at_ms=self.now,
            )
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute(
                    "SELECT initial_capital FROM paper_account_config WHERE id=1"
                ).fetchone(), ("100",))
                self.assertEqual(db.execute(
                    "SELECT initial_capital,currency FROM paper_accounts WHERE account_id=1"
                ).fetchone(), ("100", "USDT"))
                self.assertEqual(db.execute(
                    """SELECT high_water_mark_quote,daily_baseline_utc_day_ms,
                              daily_baseline_equity_quote,risk_ready
                       FROM paper_account_risk_state WHERE account_id=1"""
                ).fetchone(), (
                    "100", self.now // 86_400_000 * 86_400_000, "100", 0
                ))
                self.assertEqual(db.execute(
                    "SELECT COUNT(*) FROM paper_simulated_capital_seed_events"
                ).fetchone()[0], 1)
                self.assertEqual(db.execute(
                    "SELECT COUNT(*) FROM paper_funding_events"
                ).fetchone()[0], 0)

    def test_paperledger_refuses_to_reclassify_existing_legacy_account_as_simulated(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy.sqlite3"
            PaperLedger(path)
            with sqlite3.connect(path) as db:
                db.execute(
                    "INSERT INTO paper_account_config VALUES (1,'100')"
                )
            with self.assertRaisesRegex(ValueError, "SIMULATED_ACCOUNT_ALREADY_EXISTS"):
                PaperLedger(
                    path,
                    strategy_id="STRATEGY_CORE",
                    source_sha="a" * 40,
                    simulated_contract_bytes=self.contract,
                    simulated_initialized_at_ms=self.now,
                )
            with sqlite3.connect(path) as db:
                self.assertIsNone(db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='paper_accounts'"
                ).fetchone())
                self.assertIsNone(db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='paper_simulated_capital_origin'"
                ).fetchone())


    def test_simulated_first_mark_establishes_readiness_without_funding_cutover(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "simulated.sqlite3"
            PaperLedger(
                path,
                strategy_id="STRATEGY_CORE",
                source_sha="a" * 40,
                simulated_contract_bytes=self.contract,
                simulated_initialized_at_ms=self.now,
            )
            account_scope = PaperLedger(path)
            result = record_account_mark(
                account_scope, "100", self.now - 60_000, self.now,
                "sha256:" + "c" * 64,
            )
            self.assertTrue(result["riskReady"])
            self.assertEqual(result["accountEquityQuote"], "100")
            snapshot = read_account_risk_snapshot(path, now_ms=self.now)
            self.assertTrue(snapshot["riskReady"])
            self.assertIsNone(snapshot["unavailableReason"])
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute(
                    "SELECT COUNT(*) FROM paper_account_equity_cutovers"
                ).fetchone()[0], 0)
                self.assertEqual(db.execute(
                    "SELECT COUNT(*) FROM paper_funding_events"
                ).fetchone()[0], 0)
                self.assertEqual(db.execute(
                    "SELECT risk_ready FROM paper_account_risk_state WHERE account_id=1"
                ).fetchone(), (1,))

    def test_simulated_mark_fails_closed_after_utc_day_without_new_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "simulated.sqlite3"
            PaperLedger(
                path,
                strategy_id="STRATEGY_CORE",
                source_sha="a" * 40,
                simulated_contract_bytes=self.contract,
                simulated_initialized_at_ms=self.now,
            )
            account_scope = PaperLedger(path)
            record_account_mark(
                account_scope, "100", self.now - 60_000, self.now,
                "sha256:" + "c" * 64,
            )
            with self.assertRaisesRegex(ValueError, "ACCOUNT_RISK_DAILY_BASELINE_UNAVAILABLE"):
                record_account_mark(
                    account_scope, "101", self.now + 86_400_000 - 60_000,
                    self.now + 86_400_000, "sha256:" + "d" * 64,
                )
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute(
                    """SELECT daily_baseline_utc_day_ms,last_mark_price,mark_observed_at_ms
                       FROM paper_account_risk_state WHERE account_id=1"""
                ).fetchone(), (
                    self.now // 86_400_000 * 86_400_000,
                    "100", self.now,
                ))


    def test_simulated_daily_baseline_rolls_over_from_previous_confirmed_equity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "simulated.sqlite3"
            PaperLedger(
                path, strategy_id="STRATEGY_CORE", source_sha="a" * 40,
                simulated_contract_bytes=self.contract,
                simulated_initialized_at_ms=self.now,
            )
            account_scope = PaperLedger(path)
            first = record_account_mark(
                account_scope, "100", self.now - 60_000, self.now,
                "sha256:" + "c" * 64,
            )
            next_day = self.now // 86_400_000 * 86_400_000 + 86_400_000
            second = record_account_mark(
                account_scope, "101", next_day, next_day + 1_000,
                "sha256:" + "d" * 64,
            )
            self.assertTrue(first["riskReady"])
            self.assertTrue(second["riskReady"])
            self.assertEqual(second["dailyBaselineUtcDayMs"], next_day)
            self.assertEqual(second["dailyPnlUsdt"], "0")
            self.assertEqual(second["highWaterMarkQuote"], "100")
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute(
                    """SELECT daily_baseline_utc_day_ms,daily_baseline_equity_quote,
                              high_water_mark_quote,risk_ready
                       FROM paper_account_risk_state WHERE account_id=1"""
                ).fetchone(), (next_day, "100", "100", 1))
                event = db.execute(
                    """SELECT utc_day_ms,baseline_equity_quote,previous_utc_day_ms,
                              previous_equity_quote,previous_mark_observed_at_ms,
                              previous_dataset_version,previous_event_hash,event_hash
                       FROM paper_simulated_daily_baseline_events WHERE account_id=1"""
                ).fetchone()
                self.assertEqual(event[:6], (
                    next_day, "100", self.now // 86_400_000 * 86_400_000,
                    "100", self.now, "sha256:" + "c" * 64,
                ))
                self.assertEqual(len(event[6]), 64)
                self.assertEqual(len(event[7]), 64)

    def test_simulated_daily_baseline_rejects_skipped_utc_day_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "simulated.sqlite3"
            PaperLedger(
                path, strategy_id="STRATEGY_CORE", source_sha="a" * 40,
                simulated_contract_bytes=self.contract,
                simulated_initialized_at_ms=self.now,
            )
            account_scope = PaperLedger(path)
            record_account_mark(
                account_scope, "100", self.now - 60_000, self.now,
                "sha256:" + "c" * 64,
            )
            day0 = self.now // 86_400_000 * 86_400_000
            skipped_day = day0 + 2 * 86_400_000
            with self.assertRaisesRegex(ValueError, "ACCOUNT_RISK_DAILY_BASELINE_UNAVAILABLE"):
                record_account_mark(
                    account_scope, "101", skipped_day, skipped_day + 1_000,
                    "sha256:" + "d" * 64,
                )
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute(
                    """SELECT daily_baseline_utc_day_ms,last_equity_quote,
                              last_mark_price,mark_observed_at_ms,risk_ready
                       FROM paper_account_risk_state WHERE account_id=1"""
                ).fetchone(), (day0, "100", "100", self.now, 1))
                self.assertEqual(db.execute(
                    "SELECT COUNT(*) FROM paper_simulated_daily_baseline_events"
                ).fetchone()[0], 0)

    def test_simulated_daily_baseline_rollover_rolls_back_event_and_state_together(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "simulated.sqlite3"
            PaperLedger(
                path, strategy_id="STRATEGY_CORE", source_sha="a" * 40,
                simulated_contract_bytes=self.contract,
                simulated_initialized_at_ms=self.now,
            )
            account_scope = PaperLedger(path)
            record_account_mark(
                account_scope, "100", self.now - 60_000, self.now,
                "sha256:" + "c" * 64,
            )
            with sqlite3.connect(path) as db:
                db.execute(
                    """CREATE TRIGGER fail_simulated_rollover
                       BEFORE UPDATE OF daily_baseline_utc_day_ms ON paper_account_risk_state
                       WHEN NEW.daily_baseline_utc_day_ms != OLD.daily_baseline_utc_day_ms
                       BEGIN SELECT RAISE(ABORT,'INJECTED_ROLLOVER_FAILURE'); END"""
                )
            next_day = self.now // 86_400_000 * 86_400_000 + 86_400_000
            with self.assertRaisesRegex(sqlite3.IntegrityError, "INJECTED_ROLLOVER_FAILURE"):
                record_account_mark(
                    account_scope, "101", next_day, next_day + 1_000,
                    "sha256:" + "d" * 64,
                )
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute(
                    "SELECT COUNT(*) FROM paper_simulated_daily_baseline_events"
                ).fetchone()[0], 0)
                self.assertEqual(db.execute(
                    "SELECT daily_baseline_utc_day_ms FROM paper_account_risk_state WHERE account_id=1"
                ).fetchone()[0], self.now // 86_400_000 * 86_400_000)

    def test_simulated_daily_baseline_provenance_tampering_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "simulated.sqlite3"
            PaperLedger(
                path, strategy_id="STRATEGY_CORE", source_sha="a" * 40,
                simulated_contract_bytes=self.contract,
                simulated_initialized_at_ms=self.now,
            )
            account_scope = PaperLedger(path)
            record_account_mark(
                account_scope, "100", self.now - 60_000, self.now,
                "sha256:" + "c" * 64,
            )
            next_day = self.now // 86_400_000 * 86_400_000 + 86_400_000
            record_account_mark(
                account_scope, "101", next_day, next_day + 1_000,
                "sha256:" + "d" * 64,
            )
            with sqlite3.connect(path) as db:
                db.execute(
                    "UPDATE paper_simulated_daily_baseline_events SET baseline_equity_quote='99'"
                )
            with self.assertRaisesRegex(sqlite3.DatabaseError, "SIMULATED_DAILY_BASELINE_PROVENANCE_INVALID"):
                read_account_risk_snapshot(path, now_ms=next_day + 2_000)

if __name__ == "__main__":
    unittest.main()
