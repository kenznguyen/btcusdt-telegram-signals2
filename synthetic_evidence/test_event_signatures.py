import unittest
from datetime import datetime, timezone

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from synthetic_evidence.event_signatures import (
    KeyRecord,
    SignatureVerificationError,
    verify_event_signature,
)


NOW = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)


def make_key_record(private_key, **overrides):
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    values = {
        "public_key": public_key,
        "status": "ACTIVE",
        "valid_from": datetime(2026, 11, 1, tzinfo=timezone.utc),
        "valid_until": datetime(2026, 12, 1, tzinfo=timezone.utc),
        "revocation_status": "CLEAR",
        "revocation_evidence_verified": True,
    }
    values.update(overrides)
    return KeyRecord(**values)


class EventSignatureTests(unittest.TestCase):
    def setUp(self):
        self.private_key = Ed25519PrivateKey.generate()
        self.message = b'{"event_id":"synthetic-event-001","sequence":1}'
        self.signature = self.private_key.sign(self.message)
        self.record = make_key_record(self.private_key)
        self.registry = {"test-key-1": self.record}

    def test_accepts_valid_ed25519_signature_for_exact_event_bytes(self):
        self.assertTrue(
            verify_event_signature(
                self.message, self.signature, "test-key-1", self.registry, at_time=NOW
            )
        )

    def test_rejects_invalid_signature(self):
        with self.assertRaises(SignatureVerificationError) as caught:
            verify_event_signature(
                self.message, b"\\x00" * 64, "test-key-1", self.registry, at_time=NOW
            )
        self.assertEqual(caught.exception.code, "REJECT_SIGNATURE")

    def test_rejects_event_bytes_changed_after_signing(self):
        with self.assertRaises(SignatureVerificationError) as caught:
            verify_event_signature(
                self.message + b" ", self.signature, "test-key-1", self.registry, at_time=NOW
            )
        self.assertEqual(caught.exception.code, "REJECT_SIGNATURE")

    def test_rejects_malformed_signature_length(self):
        with self.assertRaises(SignatureVerificationError) as caught:
            verify_event_signature(
                self.message, b"short", "test-key-1", self.registry, at_time=NOW
            )
        self.assertEqual(caught.exception.code, "REJECT_SIGNATURE_FORMAT")

    def test_rejects_unknown_key_id(self):
        with self.assertRaises(SignatureVerificationError) as caught:
            verify_event_signature(
                self.message, self.signature, "unknown-key", self.registry, at_time=NOW
            )
        self.assertEqual(caught.exception.code, "REJECT_UNKNOWN_KEY")

    def test_rejects_invalid_public_key_length(self):
        registry = {"bad-key": KeyRecord(
            public_key=b"bad", status="ACTIVE",
            valid_from=datetime(2026, 11, 1, tzinfo=timezone.utc),
            valid_until=datetime(2026, 12, 1, tzinfo=timezone.utc),
            revocation_status="CLEAR", revocation_evidence_verified=True,
        )}
        with self.assertRaises(SignatureVerificationError) as caught:
            verify_event_signature(
                self.message, self.signature, "bad-key", registry, at_time=NOW
            )
        self.assertEqual(caught.exception.code, "REJECT_PUBLIC_KEY")

    def test_rejects_key_before_validity_window(self):
        record = make_key_record(
            self.private_key, valid_from=datetime(2026, 11, 10, tzinfo=timezone.utc)
        )
        with self.assertRaises(SignatureVerificationError) as caught:
            verify_event_signature(
                self.message, self.signature, "test-key-1",
                {"test-key-1": record}, at_time=NOW
            )
        self.assertEqual(caught.exception.code, "REJECT_KEY_NOT_YET_VALID")

    def test_rejects_key_after_validity_window(self):
        record = make_key_record(
            self.private_key, valid_until=datetime(2026, 11, 8, tzinfo=timezone.utc)
        )
        with self.assertRaises(SignatureVerificationError) as caught:
            verify_event_signature(
                self.message, self.signature, "test-key-1",
                {"test-key-1": record}, at_time=NOW
            )
        self.assertEqual(caught.exception.code, "REJECT_KEY_EXPIRED")

    def test_rejects_revoked_key(self):
        record = make_key_record(
            self.private_key, status="REVOKED", revocation_status="REVOKED"
        )
        with self.assertRaises(SignatureVerificationError) as caught:
            verify_event_signature(
                self.message, self.signature, "test-key-1",
                {"test-key-1": record}, at_time=NOW
            )
        self.assertEqual(caught.exception.code, "REJECT_REVOKED_KEY")

    def test_fails_closed_when_revocation_state_is_unknown(self):
        record = make_key_record(
            self.private_key, revocation_status="UNKNOWN",
            revocation_evidence_verified=False
        )
        with self.assertRaises(SignatureVerificationError) as caught:
            verify_event_signature(
                self.message, self.signature, "test-key-1",
                {"test-key-1": record}, at_time=NOW
            )
        self.assertEqual(caught.exception.code, "REJECT_REVOCATION_UNKNOWN")

    def test_fails_closed_when_revocation_evidence_is_unverified(self):
        record = make_key_record(
            self.private_key, revocation_status="CLEAR",
            revocation_evidence_verified=False
        )
        with self.assertRaises(SignatureVerificationError) as caught:
            verify_event_signature(
                self.message, self.signature, "test-key-1",
                {"test-key-1": record}, at_time=NOW
            )
        self.assertEqual(caught.exception.code, "REJECT_REVOCATION_UNVERIFIED")

    def test_rotation_accepts_new_key_and_rejects_old_key_after_boundary(self):
        new_private_key = Ed25519PrivateKey.generate()
        old_record = make_key_record(
            self.private_key, valid_until=datetime(2026, 11, 9, 11, 59, tzinfo=timezone.utc)
        )
        new_record = make_key_record(
            new_private_key, valid_from=datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)
        )
        new_signature = new_private_key.sign(self.message)
        registry = {"old-key": old_record, "new-key": new_record}

        with self.assertRaises(SignatureVerificationError) as caught:
            verify_event_signature(
                self.message, self.signature, "old-key", registry, at_time=NOW
            )
        self.assertEqual(caught.exception.code, "REJECT_KEY_EXPIRED")
        self.assertTrue(
            verify_event_signature(
                self.message, new_signature, "new-key", registry, at_time=NOW
            )
        )


if __name__ == "__main__":
    unittest.main()
