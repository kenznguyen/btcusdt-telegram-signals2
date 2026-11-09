import unittest

from synthetic_evidence.root_b_checkpoint import (
    RootBJournal,
    SimulatedCrash,
    RootBIntegrityError,
)


class RootBDuplicateAckAndCheckpointCrashTests(unittest.TestCase):
    def setUp(self):
        self.journal = RootBJournal(required_observers={"observer-a", "observer-b"})
        self.journal.append_event("evt-1", b'{"event_id":"evt-1","value":1}')
        self.journal.append_event("evt-2", b'{"event_id":"evt-2","value":2}')

    def _ack_all(self, event_id, digest):
        self.journal.acknowledge(event_id, "observer-a", digest)
        self.journal.acknowledge(event_id, "observer-b", digest)

    def test_duplicate_identical_ack_is_idempotent_and_does_not_inflate_count(self):
        digest = self.journal.event_digest("evt-1")
        first = self.journal.acknowledge("evt-1", "observer-a", digest)
        duplicate = self.journal.acknowledge("evt-1", "observer-a", digest)

        self.assertEqual(first, "ACK_RECORDED")
        self.assertEqual(duplicate, "ACK_DUPLICATE")
        self.assertEqual(self.journal.ack_count("evt-1"), 1)
        self.assertTrue(self.journal.all_observers_acked("evt-1"))

    def test_same_observer_ack_with_changed_digest_is_integrity_failure(self):
        digest = self.journal.event_digest("evt-1")
        self.journal.acknowledge("evt-1", "observer-a", digest)

        with self.assertRaises(RootBIntegrityError):
            self.journal.acknowledge("evt-1", "observer-a", "0" * 64)

    def test_ack_for_unknown_event_or_observer_is_rejected(self):
        with self.assertRaises(RootBIntegrityError):
            self.journal.acknowledge("missing", "observer-a", "0" * 64)
        with self.assertRaises(RootBIntegrityError):
            self.journal.acknowledge("evt-1", "unregistered", self.journal.event_digest("evt-1"))

    def test_checkpoint_cannot_commit_until_all_required_observers_ack(self):
        digest = self.journal.event_digest("evt-1")
        self.journal.acknowledge("evt-1", "observer-a", digest)

        with self.assertRaises(RootBIntegrityError):
            self.journal.commit_checkpoint("cp-1", through_sequence=1)

        self.assertIsNone(self.journal.recover_checkpoint())

    def test_crash_before_checkpoint_write_leaves_previous_checkpoint_unchanged(self):
        for event_id in ("evt-1", "evt-2"):
            self._ack_all(event_id, self.journal.event_digest(event_id))
        self.journal.commit_checkpoint("cp-1", through_sequence=1)

        with self.assertRaises(SimulatedCrash):
            self.journal.commit_checkpoint(
                "cp-2", through_sequence=2, crash_at="before_durable_write"
            )

        recovered = self.journal.recover_checkpoint()
        self.assertEqual(recovered["checkpoint_id"], "cp-1")
        self.assertEqual(recovered["through_sequence"], 1)

    def test_crash_after_durable_write_before_ack_recovers_committed_checkpoint(self):
        for event_id in ("evt-1", "evt-2"):
            self._ack_all(event_id, self.journal.event_digest(event_id))

        with self.assertRaises(SimulatedCrash):
            self.journal.commit_checkpoint(
                "cp-2", through_sequence=2, crash_at="after_durable_write"
            )

        recovered = self.journal.recover_checkpoint()
        self.assertEqual(recovered["checkpoint_id"], "cp-2")
        self.assertEqual(recovered["through_sequence"], 2)
        self.assertTrue(self.journal.checkpoint_is_valid(recovered))

    def test_crash_after_checkpoint_ack_is_idempotently_recoverable(self):
        for event_id in ("evt-1", "evt-2"):
            self._ack_all(event_id, self.journal.event_digest(event_id))

        with self.assertRaises(SimulatedCrash):
            self.journal.commit_checkpoint(
                "cp-2", through_sequence=2, crash_at="after_ack"
            )

        recovered = self.journal.recover_checkpoint()
        self.assertEqual(recovered["checkpoint_id"], "cp-2")
        self.assertEqual(self.journal.checkpoint_ack_count("cp-2"), 1)

        self.assertEqual(
            self.journal.commit_checkpoint("cp-2", through_sequence=2),
            "CHECKPOINT_ALREADY_COMMITTED",
        )
        self.assertEqual(self.journal.checkpoint_ack_count("cp-2"), 1)

    def test_recovery_rejects_checkpoint_when_committed_event_bytes_change(self):
        digest = self.journal.event_digest("evt-1")
        self._ack_all("evt-1", digest)
        self.journal.commit_checkpoint("cp-1", through_sequence=1)

        self.journal.corrupt_event_for_test("evt-1", b'{"event_id":"evt-1","value":999}')

        with self.assertRaises(RootBIntegrityError):
            self.journal.recover_checkpoint()

    def test_checkpoint_cannot_skip_a_sequence_or_include_unacknowledged_event(self):
        self._ack_all("evt-1", self.journal.event_digest("evt-1"))
        self._ack_all("evt-2", self.journal.event_digest("evt-2"))

        with self.assertRaises(RootBIntegrityError):
            self.journal.commit_checkpoint("cp-gap", through_sequence=3)

        self.journal.acknowledge("evt-2", "observer-b", "f" * 64) if False else None
        self.assertEqual(self.journal.commit_checkpoint("cp-2", through_sequence=2), "CHECKPOINT_COMMITTED")


if __name__ == "__main__":
    unittest.main()
