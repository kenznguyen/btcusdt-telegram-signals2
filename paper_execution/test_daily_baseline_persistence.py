"""Atomic daily baseline persistence contract (PAPER-only, temporary SQLite)."""
import sqlite3
import unittest

from paper_execution import account_history
from paper_execution.test_dual_ledger_red import DualLedgerRedTest
from paper_execution.daily_baseline import persist_daily_equity_baseline
from paper_execution.ledger import read_account_risk_snapshot


class DailyBaselinePersistenceContractTest(unittest.TestCase):
    def setUp(self):
        self.fixture = DualLedgerRedTest(
            "test_core_and_ai_hold_independent_positions_in_one_account_database"
        )
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.path = self.fixture.path
        self.now = self.fixture.now
        self.boundary = (self.now // account_history.DAY_MS + 1) * account_history.DAY_MS
        self.recorded = self.boundary + 60_000
        source_sha = "b" * 40

        for strategy_id in sorted(account_history.STRATEGIES):
            account_history.record_account_history_coverage(
                self.path, coverage_id=f"exec:{strategy_id}",
                stream_type="EXECUTION", strategy_id=strategy_id,
                start_at_ms=self.now, end_at_ms=self.boundary + 1,
                status="VERIFIED", source="FIXTURE_EXECUTION_HISTORY",
                source_snapshot_id=f"fixture:execution:{strategy_id}",
                payload_hash="sha256:" + "c" * 64, recorded_at_ms=self.recorded,
            )
        account_history.record_account_history_coverage(
            self.path, coverage_id="market:boundary",
            stream_type="MARKET_MARK", strategy_id=None,
            start_at_ms=self.now, end_at_ms=self.boundary + 1,
            status="VERIFIED", source="FIXTURE_MARK_HISTORY",
            source_snapshot_id="fixture:market",
            payload_hash="sha256:" + "d" * 64, recorded_at_ms=self.recorded,
        )
        from paper_execution import ledger
        ledger.record_funding_coverage(
            self.path, coverage_id="fixture-funding-after-cutover",
            start_at_ms=self.now, end_at_ms=self.recorded,
            status="VERIFIED", source="FIXTURE_FUNDING_HISTORY",
            source_snapshot_id="fixture:funding-after-cutover",
            payload_hash="sha256:" + "e" * 64,
            config_version="fixture-funding-v2", recorded_at_ms=self.recorded,
        )
        account_history.record_market_mark_history(
            self.path, mark_id="fixture-boundary-mark",
            effective_at_ms=self.boundary, observed_at_ms=self.recorded,
            mark_price="100", candle_close_ms=self.boundary,
            source="FIXTURE_MARK_HISTORY", source_snapshot_id="fixture:market",
            dataset_version="sha256:dual-ledger-seed",
            payload_hash="sha256:" + "f" * 64, quality_status="VERIFIED",
            recorded_at_ms=self.recorded,
        )

    def persist(self):
        connection = self._connection()
        try:
            return persist_daily_equity_baseline(
                connection, utc_day_ms=self.boundary,
                now_ms=self.recorded, source_sha="b" * 40,
            )
        finally:
            connection.close()

    def _connection(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def test_persists_one_immutable_baseline_audit_and_daily_risk_state_atomically(self):
        result = self.persist()
        self.assertFalse(result["idempotent"])
        self.assertEqual(result["baseline_equity_quote"], "100")
        with self._connection() as db:
            baseline = db.execute(
                """SELECT utc_day_ms,baseline_equity_quote,mark_id,
                          starting_cutover_id,replay_digest
                   FROM paper_daily_equity_baselines WHERE account_id=1"""
            ).fetchone()
            audit = db.execute(
                """SELECT baseline_id,replay_digest,event_type
                   FROM paper_daily_equity_baseline_audit WHERE account_id=1"""
            ).fetchone()
            risk = db.execute(
                """SELECT daily_baseline_utc_day_ms,daily_baseline_equity_quote,
                          risk_ready,last_equity_quote,last_mark_price,mark_observed_at_ms,
                          mark_candle_close_ms,dataset_version
                   FROM paper_account_risk_state WHERE account_id=1"""
            ).fetchone()
        self.assertEqual(baseline[:4], (
            self.boundary, "100", "fixture-boundary-mark", "fixture-account-cutover"
        ))
        self.assertEqual(baseline[4], result["replay_digest"])
        self.assertEqual(audit, (result["baseline_id"], result["replay_digest"], "DAILY_BASELINE_CREATED"))
        self.assertEqual(risk, (self.boundary, "100", 1, "100", "100", self.recorded, self.boundary, "sha256:dual-ledger-seed"))


    def test_baseline_is_consumed_by_shared_risk_snapshot_at_boundary_mark(self):
        self.persist()
        snapshot = read_account_risk_snapshot(self.path, now_ms=self.recorded)
        self.assertTrue(snapshot['available'])
        self.assertTrue(snapshot['riskReady'])
        self.assertEqual(snapshot['dailyBaselineUtcDayMs'], self.boundary)
        self.assertEqual(snapshot['accountEquityQuote'], '100')
        self.assertEqual(snapshot['markObservedAtMs'], self.recorded)

    def test_identical_retry_is_idempotent_and_does_not_duplicate_audit(self):
        first = self.persist()
        second = self.persist()
        self.assertFalse(first["idempotent"])
        self.assertTrue(second["idempotent"])
        self.assertEqual(first["replay_digest"], second["replay_digest"])
        with self._connection() as db:
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM paper_daily_equity_baselines"
            ).fetchone()[0], 1)
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM paper_daily_equity_baseline_audit"
            ).fetchone()[0], 1)

    def test_conflicting_existing_replay_digest_is_rejected_without_state_change(self):
        with self._connection() as db:
            db.execute(
                """INSERT INTO paper_daily_equity_baselines
                   (baseline_id,account_id,utc_day_ms,baseline_equity_quote,mark_id,
                    starting_cutover_id,replay_digest,algorithm_version,source_sha,recorded_at_ms)
                   VALUES (?,1,?,'100','fixture-boundary-mark','fixture-account-cutover',
                           'sha256:conflict','daily-equity-replay-v1',?,?)""",
                (f"daily-equity-baseline:1:{self.boundary}", self.boundary,
                 "b" * 40, self.recorded),
            )
            db.commit()
        with self.assertRaisesRegex(ValueError, "DAILY_BASELINE_REPLAY_CONFLICT"):
            self.persist()
        with self._connection() as db:
            self.assertEqual(db.execute(
                "SELECT replay_digest FROM paper_daily_equity_baselines WHERE account_id=1"
            ).fetchone()[0], "sha256:conflict")
            self.assertEqual(db.execute(
                "SELECT daily_baseline_utc_day_ms FROM paper_account_risk_state WHERE account_id=1"
            ).fetchone()[0], self.now // account_history.DAY_MS * account_history.DAY_MS)

    def test_failure_during_risk_state_update_rolls_back_baseline_and_audit(self):
        with self._connection() as db:
            db.execute("""CREATE TRIGGER fail_daily_baseline_risk_update
                BEFORE UPDATE ON paper_account_risk_state
                BEGIN SELECT RAISE(ABORT,'INJECTED_RISK_STATE_FAILURE'); END""")
            db.commit()
        with self.assertRaises(sqlite3.IntegrityError):
            self.persist()
        with self._connection() as db:
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM paper_daily_equity_baselines"
            ).fetchone()[0], 0)
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM paper_daily_equity_baseline_audit"
            ).fetchone()[0], 0)
            risk = db.execute(
                "SELECT daily_baseline_utc_day_ms,risk_ready FROM paper_account_risk_state WHERE account_id=1"
            ).fetchone()
        self.assertEqual(risk[0], self.now // account_history.DAY_MS * account_history.DAY_MS)
        self.assertEqual(risk[1], 1)

    def test_baseline_reconstruction_does_not_promote_an_unready_account(self):
        with self._connection() as db:
            db.execute(
                """UPDATE paper_account_risk_state SET risk_ready=0,
                   unavailable_reason='PREEXISTING_RISK_GATE' WHERE account_id=1"""
            )
            db.commit()
        result = self.persist()
        self.assertFalse(result["risk_ready"])
        with self._connection() as db:
            state = db.execute(
                "SELECT risk_ready,unavailable_reason,daily_baseline_utc_day_ms "
                "FROM paper_account_risk_state WHERE account_id=1"
            ).fetchone()
        self.assertEqual(state, (0, "PREEXISTING_RISK_GATE", self.boundary))

    def test_baseline_and_audit_rows_reject_update_and_delete(self):
        self.persist()
        with self._connection() as db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute(
                    "UPDATE paper_daily_equity_baselines SET baseline_equity_quote='999' WHERE account_id=1"
                )
            db.rollback()
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("DELETE FROM paper_daily_equity_baseline_audit")
            db.rollback()


if __name__ == "__main__":
    unittest.main()
