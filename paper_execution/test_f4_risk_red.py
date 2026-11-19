import sqlite3
import tempfile
import unittest
from pathlib import Path

from paper_execution.ledger import PaperLedger
from paper_execution import risk_control


class F4RiskContractRedTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "account.sqlite3"
        self.now = 1_800_000_000_000

    def test_core_and_ai_cannot_supply_conflicting_limits_for_one_account(self):
        PaperLedger(self.path, max_position_base="1")
        core_limits = {
            "maxDrawdownPct": "20",
            "maxDailyLossUsdt": "10",
            "maxExposureUsdt": "1000",
        }
        ai_limits = {
            "maxDrawdownPct": "30",
            "maxDailyLossUsdt": "15",
            "maxExposureUsdt": "1200",
        }
        PaperLedger(
            self.path, strategy_id="STRATEGY_CORE", source_sha="a" * 40,
            risk_limits=core_limits, require_risk_limits=True,
        )
        with self.assertRaisesRegex(
            (ValueError, sqlite3.DatabaseError), "ACCOUNT_RISK_CONTRACT"
        ):
            PaperLedger(
                self.path, strategy_id="AI_FREQAI", source_sha="a" * 40,
                leverage="2", risk_limits=ai_limits, require_risk_limits=True,
            )


class F4KillSwitchFailClosedRedTest(unittest.TestCase):
    def test_missing_kill_switch_table_is_not_treated_as_unlatched(self):
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)

        with self.assertRaisesRegex(
            sqlite3.DatabaseError, "RISK_CONTROL_STATE_UNAVAILABLE"
        ):
            risk_control.risk_block_reason(connection)

    def test_malformed_unlatched_row_is_rejected(self):
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        connection.execute("""
            CREATE TABLE paper_risk_control (
                id INTEGER PRIMARY KEY,
                paused,
                killed,
                reason TEXT,
                updated_at_ms
            )
        """)
        connection.execute(
            "INSERT INTO paper_risk_control VALUES (1, 0, 0, NULL, 'not-a-timestamp')"
        )

        with self.assertRaisesRegex(
            sqlite3.DatabaseError, "RISK_CONTROL_STATE_INVALID"
        ):
            risk_control.risk_block_reason(connection)


class F4KillResetAtomicReadinessRedTest(unittest.TestCase):
    def test_caller_supplied_ready_true_cannot_clear_kill_without_account_readiness(self):
        ledger = PaperLedger(self.path_for_test())
        ledger.set_killed(True, 1_800_000_000_000, "TEST_KILL")

        with self.assertRaisesRegex(
            (ValueError, sqlite3.DatabaseError), "ACCOUNT_RISK_NOT_READY"
        ):
            ledger.reset_kill(True, True, 1_800_000_000_001)

        self.assertTrue(ledger.snapshot()["riskControl"]["killed"])

    def path_for_test(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        return Path(self.temp.name) / "reset.sqlite3"


if __name__ == "__main__":
    unittest.main()
