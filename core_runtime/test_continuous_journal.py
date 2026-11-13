"""RED-first tests for the durable Continuous Core cycle journal."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import sqlite3
import os
import unittest
from unittest.mock import patch

from core_runtime.continuous_journal import (
    ContinuousJournal,
    CycleConflict,
    JournalError,
)


class ContinuousJournalClaimTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "continuous-journal.sqlite3"

    def claim(self, journal, *, bundle_id="bundle-a", digest="sha256:" + "a" * 64):
        return journal.claim_cycle(
            cycle_key="binance:USDT_PERPETUAL:BTCUSDT:15m:1800000000000:STRATEGY_CORE",
            bundle_id=bundle_id,
            bundle_sha256=digest,
            bundle_path="/immutable/bundles/bundle-a.json",
            source_sha="source-sha",
            config_sha256="config-sha256",
            claimed_at_ms=1_800_000_001_000,
        )

    def test_first_claim_is_persisted_and_readable(self):
        journal = ContinuousJournal(self.db)
        self.assertTrue(self.claim(journal))
        cycle = journal.get_cycle(
            "binance:USDT_PERPETUAL:BTCUSDT:15m:1800000000000:STRATEGY_CORE"
        )
        self.assertEqual(cycle["bundleId"], "bundle-a")
        self.assertEqual(cycle["status"], "CLAIMED")
        self.assertEqual(cycle["sourceSha"], "source-sha")

    def test_same_cycle_and_same_bundle_is_idempotent(self):
        journal = ContinuousJournal(self.db)
        self.assertTrue(self.claim(journal))
        self.assertFalse(self.claim(journal))
        self.assertEqual(len(journal.list_cycles()), 1)



    def test_journal_refuses_t0_canonical_database_path(self):
        with tempfile.TemporaryDirectory() as directory:
            t0_path = Path(directory) / "market-data.sqlite3"
            with patch.dict(os.environ, {"MARKET_DATA_DB": str(t0_path)}, clear=False):
                with self.assertRaises(JournalError):
                    ContinuousJournal(t0_path)
            self.assertFalse(t0_path.exists())

    def test_schema_version_mismatch_fails_closed_without_reset(self):
        with sqlite3.connect(self.db) as connection:
            connection.execute(
                "CREATE TABLE journal_meta(singleton INTEGER PRIMARY KEY, schema_version INTEGER NOT NULL)"
            )
            connection.execute(
                "INSERT INTO journal_meta(singleton,schema_version) VALUES (1,999)"
            )
        with self.assertRaises(JournalError):
            ContinuousJournal(self.db)
        with sqlite3.connect(self.db) as connection:
            version = connection.execute(
                "SELECT schema_version FROM journal_meta WHERE singleton=1"
            ).fetchone()[0]
        self.assertEqual(version, 999)

    def test_same_cycle_with_different_bundle_fails_closed(self):
        journal = ContinuousJournal(self.db)
        self.assertTrue(self.claim(journal))
        with self.assertRaises(CycleConflict):
            self.claim(journal, bundle_id="bundle-b", digest="sha256:" + "b" * 64)
        self.assertEqual(journal.get_cycle(
            "binance:USDT_PERPETUAL:BTCUSDT:15m:1800000000000:STRATEGY_CORE"
        )["bundleId"], "bundle-a")

    def test_concurrent_claimers_produce_exactly_one_winner(self):
        def contender(_):
            return self.claim(ContinuousJournal(self.db))

        with ThreadPoolExecutor(max_workers=8) as pool:
            outcomes = list(pool.map(contender, range(8)))
        self.assertEqual(outcomes.count(True), 1)
        self.assertEqual(outcomes.count(False), 7)
        self.assertEqual(len(ContinuousJournal(self.db).list_cycles()), 1)


    def test_cycle_state_transition_persists_intent_and_terminal_result(self):
        journal = ContinuousJournal(self.db)
        self.claim(journal)
        cycle_key = "binance:USDT_PERPETUAL:BTCUSDT:15m:1800000000000:STRATEGY_CORE"
        self.assertTrue(journal.transition_cycle(
            cycle_key,
            expected_status="CLAIMED",
            status="EXECUTING",
            updated_at_ms=1_800_000_002_000,
            run_id="core-run:fixture",
            intent_id="intent:fixture",
        ))
        executing = journal.get_cycle(cycle_key)
        self.assertEqual(executing["status"], "EXECUTING")
        self.assertEqual(executing["intentId"], "intent:fixture")
        self.assertTrue(journal.transition_cycle(
            cycle_key,
            expected_status="EXECUTING",
            status="PAPER_ACCEPTED",
            updated_at_ms=1_800_000_003_000,
            order_id="paper:fixture",
            terminal_result="PAPER_ACCEPTED",
        ))
        terminal = journal.get_cycle(cycle_key)
        self.assertEqual(terminal["status"], "PAPER_ACCEPTED")
        self.assertEqual(terminal["orderId"], "paper:fixture")
        self.assertEqual(terminal["terminalResult"], "PAPER_ACCEPTED")



    def test_checkpoint_advances_only_after_reconciled_terminal_outcome(self):
        journal = ContinuousJournal(self.db)
        cycle_key = "binance:USDT_PERPETUAL:BTCUSDT:15m:1800000000000:STRATEGY_CORE"
        stream_key = "binance:USDT_PERPETUAL:BTCUSDT:15m:STRATEGY_CORE"
        self.claim(journal)
        journal.transition_cycle(
            cycle_key, expected_status="CLAIMED", status="EXECUTING",
            updated_at_ms=1_800_000_002_000,
        )
        self.assertIsNone(journal.get_checkpoint(stream_key))
        journal.transition_cycle(
            cycle_key, expected_status="EXECUTING",
            status="UNKNOWN_REQUIRES_RECONCILIATION",
            updated_at_ms=1_800_000_003_000,
            terminal_result="SUBMIT_OUTCOME_UNKNOWN",
        )
        self.assertIsNone(journal.get_checkpoint(stream_key))
        journal.transition_cycle(
            cycle_key, expected_status="UNKNOWN_REQUIRES_RECONCILIATION",
            status="NO_SIGNAL", updated_at_ms=1_800_000_004_000,
            terminal_result="NO_SIGNAL",
        )
        checkpoint = journal.get_checkpoint(stream_key)
        self.assertEqual(checkpoint["cycleKey"], cycle_key)
        self.assertEqual(checkpoint["candleOpenTimeMs"], 1_800_000_000_000)

    def test_checkpoint_never_regresses_when_an_older_cycle_finishes_late(self):
        journal = ContinuousJournal(self.db)
        stream_key = "binance:USDT_PERPETUAL:BTCUSDT:15m:STRATEGY_CORE"
        later_key = "binance:USDT_PERPETUAL:BTCUSDT:15m:1800000900000:STRATEGY_CORE"
        earlier_key = "binance:USDT_PERPETUAL:BTCUSDT:15m:1800000000000:STRATEGY_CORE"

        def claim_key(key, bundle_id, at_ms):
            return journal.claim_cycle(
                cycle_key=key, bundle_id=bundle_id,
                bundle_sha256="sha256:" + ("a" if bundle_id == "later" else "b") * 64,
                bundle_path="/immutable/" + bundle_id + ".json",
                source_sha="source-sha", config_sha256="config-sha256",
                claimed_at_ms=at_ms,
            )

        for key, bundle_id, at_ms in (
            (later_key, "later", 1_800_000_901_000),
            (earlier_key, "earlier", 1_800_000_001_000),
        ):
            claim_key(key, bundle_id, at_ms)
            journal.transition_cycle(
                key, expected_status="CLAIMED", status="EXECUTING",
                updated_at_ms=at_ms + 1,
            )
            journal.transition_cycle(
                key, expected_status="EXECUTING", status="PAPER_ACCEPTED",
                updated_at_ms=at_ms + 2, terminal_result="PAPER_ACCEPTED",
            )

        checkpoint = journal.get_checkpoint(stream_key)
        self.assertEqual(checkpoint["cycleKey"], later_key)
        self.assertEqual(checkpoint["candleOpenTimeMs"], 1_800_000_900_000)

    def test_reopened_journal_preserves_cycle_claim_and_checkpoint(self):
        journal = ContinuousJournal(self.db)
        self.claim(journal)
        cycle_key = "binance:USDT_PERPETUAL:BTCUSDT:15m:1800000000000:STRATEGY_CORE"
        journal.transition_cycle(
            cycle_key, expected_status="CLAIMED", status="EXECUTING",
            updated_at_ms=1_800_000_002_000,
        )
        journal.transition_cycle(
            cycle_key, expected_status="EXECUTING", status="NO_SIGNAL",
            updated_at_ms=1_800_000_003_000, terminal_result="NO_SIGNAL",
        )
        reopened = ContinuousJournal(self.db)
        self.assertEqual(reopened.get_cycle(cycle_key)["status"], "NO_SIGNAL")
        self.assertEqual(len(reopened.list_cycles()), 1)
        self.assertEqual(
            reopened.get_checkpoint(
                "binance:USDT_PERPETUAL:BTCUSDT:15m:STRATEGY_CORE"
            )["cycleKey"],
            cycle_key,
        )

    def test_pre_submit_intent_persistence_is_idempotent_and_conflict_safe(self):
        journal = ContinuousJournal(self.db)
        self.claim(journal)
        cycle_key = "binance:USDT_PERPETUAL:BTCUSDT:15m:1800000000000:STRATEGY_CORE"
        journal.transition_cycle(
            cycle_key,
            expected_status="CLAIMED",
            status="EXECUTING",
            updated_at_ms=1_800_000_002_000,
        )
        self.assertTrue(journal.record_intent(
            cycle_key, "intent:stable", updated_at_ms=1_800_000_002_100
        ))
        self.assertFalse(journal.record_intent(
            cycle_key, "intent:stable", updated_at_ms=1_800_000_002_200
        ))
        self.assertEqual(journal.get_cycle(cycle_key)["intentId"], "intent:stable")
        with self.assertRaises(CycleConflict):
            journal.record_intent(
                cycle_key, "intent:changed", updated_at_ms=1_800_000_002_300
            )

    def test_cycle_transition_uses_compare_and_swap_and_rejects_terminal_replay(self):
        journal = ContinuousJournal(self.db)
        self.claim(journal)
        cycle_key = "binance:USDT_PERPETUAL:BTCUSDT:15m:1800000000000:STRATEGY_CORE"
        with self.assertRaises(CycleConflict):
            journal.transition_cycle(
                cycle_key,
                expected_status="EXECUTING",
                status="PAPER_ACCEPTED",
                updated_at_ms=1_800_000_002_000,
                terminal_result="PAPER_ACCEPTED",
            )
        journal.transition_cycle(
            cycle_key,
            expected_status="CLAIMED",
            status="EXECUTING",
            updated_at_ms=1_800_000_002_000,
        )
        journal.transition_cycle(
            cycle_key,
            expected_status="EXECUTING",
            status="NO_SIGNAL",
            updated_at_ms=1_800_000_003_000,
            terminal_result="NO_SIGNAL",
        )
        with self.assertRaises(CycleConflict):
            journal.transition_cycle(
                cycle_key,
                expected_status="NO_SIGNAL",
                status="EXECUTING",
                updated_at_ms=1_800_000_003_000,
            )



if __name__ == "__main__":
    unittest.main()
