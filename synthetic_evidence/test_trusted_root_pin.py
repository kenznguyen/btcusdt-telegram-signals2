import hashlib
import unittest

from synthetic_evidence.trust_anchor import verify_trusted_root
from synthetic_evidence.trusted_root_pin import TRUSTED_ROOT_SHA256


class TrustedRootPinTests(unittest.TestCase):
    def setUp(self):
        self.root_bytes = (
            b'{"mediaType":"application/vnd.dev.sigstore.trustedroot+json;version=0.1"}\n'
            b'{"mediaType":"application/vnd.dev.sigstore.trustedroot+json;version=0.1","source":"second"}\n'
        )
        self.pin = hashlib.sha256(self.root_bytes).hexdigest()

    def test_reviewed_pin_is_a_sha256_digest(self):
        self.assertRegex(TRUSTED_ROOT_SHA256, r"^[0-9a-f]{64}$")

    def test_accepts_exact_pinned_jsonl_trusted_root(self):
        self.assertEqual(verify_trusted_root(self.root_bytes, self.pin), self.pin)

    def test_rejects_modified_trusted_root_bytes(self):
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            verify_trusted_root(self.root_bytes + b" ", self.pin)

    def test_rejects_wrong_pin(self):
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            verify_trusted_root(self.root_bytes, "0" * 64)

    def test_rejects_empty_trusted_root(self):
        with self.assertRaisesRegex(ValueError, "empty trusted root"):
            verify_trusted_root(b"", self.pin)

    def test_rejects_malformed_jsonl(self):
        malformed = b'{"valid":true}\nnot-json\n'
        with self.assertRaisesRegex(ValueError, "invalid JSONL"):
            verify_trusted_root(malformed, hashlib.sha256(malformed).hexdigest())

    def test_rejects_non_object_jsonl_record(self):
        malformed = b'[]\n'
        with self.assertRaisesRegex(ValueError, "JSON object"):
            verify_trusted_root(malformed, hashlib.sha256(malformed).hexdigest())

    def test_rejects_malformed_pin(self):
        with self.assertRaisesRegex(ValueError, "invalid trusted-root pin"):
            verify_trusted_root(self.root_bytes, "not-a-sha256")


if __name__ == "__main__":
    unittest.main()
