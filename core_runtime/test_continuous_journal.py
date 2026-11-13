"""RED-first tests for the durable Continuous Core cycle journal."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest

from core_runtime.continuous_journal import (
    ContinuousJournal,
    CycleConflict,
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
