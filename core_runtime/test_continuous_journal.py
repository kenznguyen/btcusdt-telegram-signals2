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


if __name__ == "__main__":
    unittest.main()
