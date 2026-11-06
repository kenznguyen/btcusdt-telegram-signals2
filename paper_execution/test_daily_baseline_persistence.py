"""Atomic daily baseline persistence contract (PAPER-only, temporary SQLite)."""
import sqlite3
import subprocess
import sys
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


    def _intent_at(self, intent_id, target, limit, snapshot_id, now_ms):
        intent = self.fixture.intent(intent_id, target, limit, snapshot_id)
        intent["decisionAtMs"] = now_ms - 100
        intent["validUntilMs"] = now_ms + 30_000
        return intent

    def test_writer_rejects_missing_immutable_audit_trigger_before_writing(self):
        with self._connection() as db:
            db.execute("DROP TRIGGER paper_daily_equity_baseline_audit_immutable_update")
            db.commit()
        with self.assertRaisesRegex(
            sqlite3.DatabaseError, "DAILY_BASELINE_IMMUTABLE_SCHEMA_INCOMPLETE"
        ):
            self.persist()
        with self._connection() as db:
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM paper_daily_equity_baselines"
            ).fetchone()[0], 0)
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM paper_daily_equity_baseline_audit"
            ).fetchone()[0], 0)

    def test_writer_rejects_missing_immutable_baseline_trigger_before_writing(self):
        with self._connection() as db:
            db.execute("DROP TRIGGER paper_daily_equity_baselines_immutable_delete")
            db.commit()
        with self.assertRaisesRegex(
            sqlite3.DatabaseError, "DAILY_BASELINE_IMMUTABLE_SCHEMA_INCOMPLETE"
        ):
            self.persist()
        with self._connection() as db:
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM paper_daily_equity_baselines"
            ).fetchone()[0], 0)

    def test_invalid_high_water_mark_fails_closed_without_partial_baseline(self):
        with self._connection() as db:
            db.execute(
                "UPDATE paper_account_risk_state SET high_water_mark_quote=NULL WHERE account_id=1"
            )
            db.commit()
        with self.assertRaisesRegex(
            sqlite3.DatabaseError, "DAILY_BASELINE_RISK_STATE_INVALID"
        ):
            self.persist()
        with self._connection() as db:
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM paper_daily_equity_baselines"
            ).fetchone()[0], 0)
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM paper_daily_equity_baseline_audit"
            ).fetchone()[0], 0)

    def test_os_process_kill_before_commit_rolls_back_baseline_audit_and_risk_state(self):
        script = r"""
import os
import sqlite3
import sys
from paper_execution.daily_baseline import persist_daily_equity_baseline

connection = sqlite3.connect(sys.argv[1], timeout=10)
connection.execute("PRAGMA foreign_keys=ON")
connection.create_function("hard_exit", 0, lambda: os._exit(73))
connection.execute("CREATE TRIGGER crash_before_daily_baseline_commit BEFORE UPDATE ON paper_account_risk_state BEGIN SELECT hard_exit(); END")
connection.commit()
persist_daily_equity_baseline(
    connection, utc_day_ms=int(sys.argv[2]), now_ms=int(sys.argv[3]),
    source_sha="b" * 40,
)
"""
        process = subprocess.run(
            [sys.executable, "-c", script, str(self.path),
             str(self.boundary), str(self.recorded)],
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(process.returncode, 73, process.stderr)
        with self._connection() as db:
            baseline_count = db.execute(
                "SELECT COUNT(*) FROM paper_daily_equity_baselines"
            ).fetchone()[0]
            audit_count = db.execute(
                "SELECT COUNT(*) FROM paper_daily_equity_baseline_audit"
            ).fetchone()[0]
            risk = db.execute(
                """SELECT daily_baseline_utc_day_ms,daily_baseline_equity_quote,
                          risk_ready FROM paper_account_risk_state WHERE account_id=1"""
            ).fetchone()
        self.assertEqual((baseline_count, audit_count), (0, 0))
        self.assertEqual(
            risk,
            (self.now // account_history.DAY_MS * account_history.DAY_MS, "100", 1),
        )

    def test_os_process_kill_after_commit_keeps_complete_state_and_retry_is_idempotent(self):
        script = r"""
import os
import sqlite3
import sys
from paper_execution.daily_baseline import persist_daily_equity_baseline

connection = sqlite3.connect(sys.argv[1], timeout=10)
connection.execute("PRAGMA foreign_keys=ON")
persist_daily_equity_baseline(
    connection, utc_day_ms=int(sys.argv[2]), now_ms=int(sys.argv[3]),
    source_sha="b" * 40,
)
os._exit(74)
"""
        process = subprocess.run(
            [sys.executable, "-c", script, str(self.path),
             str(self.boundary), str(self.recorded)],
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(process.returncode, 74, process.stderr)
        with self._connection() as db:
            baseline = db.execute(
                """SELECT baseline_id,baseline_equity_quote,replay_digest
                   FROM paper_daily_equity_baselines WHERE account_id=1"""
            ).fetchone()
            audit = db.execute(
                """SELECT baseline_id,replay_digest FROM paper_daily_equity_baseline_audit
                   WHERE account_id=1"""
            ).fetchone()
            risk = db.execute(
                """SELECT daily_baseline_utc_day_ms,daily_baseline_equity_quote,risk_ready
                   FROM paper_account_risk_state WHERE account_id=1"""
            ).fetchone()
        self.assertEqual(baseline[1], "100")
        self.assertEqual(audit, (baseline[0], baseline[2]))
        self.assertEqual(risk, (self.boundary, "100", 1))
        snapshot = read_account_risk_snapshot(self.path, now_ms=self.recorded)
        self.assertTrue(snapshot["riskReady"])
        retry = self.persist()
        self.assertTrue(retry["idempotent"])

    def test_missing_daily_baseline_blocks_new_exposure(self):
        self.persist()
        with self._connection() as db:
            db.execute(
                """UPDATE paper_account_risk_state
                   SET daily_baseline_utc_day_ms=NULL,daily_baseline_equity_quote=NULL
                   WHERE account_id=1"""
            )
            db.commit()
        order = self.fixture.core.submit(
            self._intent_at("missing-baseline-entry", "0.01", "100.1", "missing-baseline-book", self.recorded),
            self.fixture.book(self.recorded), self.recorded,
        )
        self.assertEqual(order["status"], "REJECTED")
        self.assertEqual(order["reason"], "RISK_INPUTS_STALE_OR_CORRUPT")

    def test_funding_coverage_gap_after_boundary_mark_observation_blocks_exposure(self):
        with self._connection() as db:
            db.execute("DROP TRIGGER paper_funding_coverage_immutable_update")
            db.execute("DROP TRIGGER paper_funding_coverage_immutable_delete")
            db.execute(
                """UPDATE paper_funding_coverage SET end_at_ms=?
                   WHERE coverage_id='fixture-funding-after-cutover'""",
                (self.boundary + 1,),
            )
            db.commit()
        self.persist()
        order = self.fixture.ai.submit(
            self._intent_at("funding-gap-entry", "-0.01", "100", "funding-gap-book", self.recorded),
            self.fixture.book(self.recorded), self.recorded,
        )
        self.assertEqual(order["status"], "REJECTED")
        self.assertEqual(order["reason"], "RISK_INPUTS_UNAVAILABLE")

    def test_kill_switch_still_blocks_new_exposure_after_daily_baseline(self):
        self.persist()
        self.fixture.core.set_killed(True, self.recorded, "ROLLOVER_KILL_SWITCH")
        order = self.fixture.core.submit(
            self._intent_at("rollover-kill-entry", "0.01", "100.1", "rollover-kill-book", self.recorded),
            self.fixture.book(self.recorded), self.recorded,
        )
        self.assertEqual(order["status"], "REJECTED")
        self.assertEqual(order["reason"], "KILL_SWITCH")

    def test_daily_loss_limit_latches_kill_after_baseline_rollover(self):
        self.persist()
        entry_now = self.recorded
        entry = self.fixture.core.submit(
            self._intent_at("daily-loss-seed-entry", "0.01", "100.1", "daily-loss-seed-book", entry_now),
            self.fixture.book(entry_now), entry_now,
        )
        self.assertEqual(entry["status"], "FILLED", entry)
        self.fixture.core.risk_limits["maxDailyLossUsdt"] = "0.05"
        with self._connection() as db:
            db.execute(
                """UPDATE paper_account_risk_state SET last_mark_price='90',
                   mark_observed_at_ms=?,mark_candle_close_ms=? WHERE account_id=1""",
                (self.recorded, self.boundary),
            )
            db.commit()
        order_now = self.recorded + 1
        rejected = self.fixture.core.submit(
            self._intent_at("daily-loss-trigger-entry", "0.02", "90", "daily-loss-trigger-book", order_now),
            self.fixture.book(order_now, bid="89.9", ask="90"), order_now,
        )
        self.assertEqual(rejected["status"], "REJECTED")
        self.assertEqual(rejected["reason"], "DAILY_LOSS_LIMIT")
        self.assertTrue(self.fixture.core.snapshot()["riskControl"]["killed"])

    def test_max_exposure_limit_still_applies_after_daily_baseline(self):
        self.persist()
        self.fixture.core.risk_limits["maxExposureUsdt"] = "0.5"
        order = self.fixture.core.submit(
            self._intent_at("rollover-exposure-entry", "0.01", "100.1", "rollover-exposure-book", self.recorded),
            self.fixture.book(self.recorded), self.recorded,
        )
        self.assertEqual(order["status"], "REJECTED")
        self.assertEqual(order["reason"], "MAX_EXPOSURE_LIMIT")

    def test_verified_daily_baseline_admits_core_and_ai_through_shared_risk_engine(self):
        self.persist()
        core_now = self.recorded
        core_order = self.fixture.core.submit(
            self._intent_at("rollover-core-entry", "0.01", "100.1", "core-boundary", core_now),
            self.fixture.book(core_now, bid="100", ask="100.1"), core_now,
        )
        ai_now = self.recorded + 1
        ai_order = self.fixture.ai.submit(
            self._intent_at("rollover-ai-entry", "-0.01", "100", "ai-boundary", ai_now),
            self.fixture.book(ai_now, bid="100", ask="100.2"), ai_now,
        )
        self.assertEqual(core_order["status"], "FILLED", core_order)
        self.assertEqual(ai_order["status"], "FILLED", ai_order)
        self.assertEqual(self.fixture.core.snapshot()["positionBase"], "0.01")
        self.assertEqual(self.fixture.ai.snapshot()["positionBase"], "-0.01")

    def test_wrong_day_baseline_blocks_new_exposure_after_rollover(self):
        self.persist()
        with self._connection() as db:
            db.execute(
                "UPDATE paper_account_risk_state SET daily_baseline_utc_day_ms=? WHERE account_id=1",
                (self.boundary - account_history.DAY_MS,),
            )
            db.commit()
        order = self.fixture.core.submit(
            self._intent_at("wrong-day-entry", "0.01", "100.1", "wrong-day-book", self.recorded),
            self.fixture.book(self.recorded), self.recorded,
        )
        self.assertEqual(order["status"], "REJECTED")
        self.assertEqual(order["reason"], "RISK_INPUTS_STALE_OR_CORRUPT")
        self.assertEqual(self.fixture.core.snapshot()["positionBase"], "0")

    def test_stale_boundary_mark_blocks_new_exposure_after_rollover(self):
        self.persist()
        with self._connection() as db:
            db.execute(
                "UPDATE paper_account_risk_state SET mark_observed_at_ms=? WHERE account_id=1",
                (self.recorded - 31 * 60_000,),
            )
            db.commit()
        order = self.fixture.ai.submit(
            self._intent_at("stale-mark-entry", "-0.01", "100", "stale-mark-book", self.recorded),
            self.fixture.book(self.recorded), self.recorded,
        )
        self.assertEqual(order["status"], "REJECTED")
        self.assertEqual(order["reason"], "RISK_INPUTS_STALE_OR_CORRUPT")
        self.assertEqual(self.fixture.ai.snapshot()["positionBase"], "0")

    def test_existing_position_can_reduce_when_daily_baseline_becomes_unavailable(self):
        self.persist()
        entry_now = self.recorded
        entry = self.fixture.core.submit(
            self._intent_at("reduce-after-rollover-entry", "0.01", "100.1", "reduce-entry-book", entry_now),
            self.fixture.book(entry_now), entry_now,
        )
        self.assertEqual(entry["status"], "FILLED", entry)
        with self._connection() as db:
            db.execute(
                "UPDATE paper_account_risk_state SET daily_baseline_utc_day_ms=NULL WHERE account_id=1"
            )
            db.commit()
        exit_now = self.recorded + 1
        exit_order = self.fixture.core.submit(
            self._intent_at("reduce-after-rollover-exit", "0", "100", "reduce-exit-book", exit_now),
            self.fixture.book(exit_now, bid="100", ask="100.1"), exit_now,
            strategy_event="EXIT",
        )
        self.assertEqual(exit_order["status"], "FILLED", exit_order)
        self.assertEqual(self.fixture.core.snapshot()["positionBase"], "0")

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
