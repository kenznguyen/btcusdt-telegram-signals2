import unittest

from synthetic_evidence.trust_anchor import verify_attestation_result


class TrustAnchorPolicyTests(unittest.TestCase):
    def _valid(self):
        return [{
            "verificationResult": {
                "statement": {
                    "predicateType": "https://slsa.dev/provenance/v1",
                    "subject": [{"name": "synthetic-evidence-bundle.zip",
                                 "digest": {"sha256": "a" * 64}}],
                },
                "verifiedTimestamps": [{"kind": "transparency-log", "timestamp": "2026-11-07T00:00:00Z"}],
                "signature": {"certificate": {"issuer": "https://token.actions.githubusercontent.com"}},
            }
        }]

    def test_accepts_verified_subject_with_signed_transparency_timestamp(self):
        self.assertTrue(verify_attestation_result(
            self._valid(), expected_subject_sha256="a" * 64,
            expected_source_sha="b" * 40,
        ))

    def test_rejects_empty_verification_result(self):
        with self.assertRaisesRegex(ValueError, "no verified attestations"):
            verify_attestation_result([], expected_subject_sha256="a" * 64,
                                      expected_source_sha="b" * 40)

    def test_rejects_subject_digest_substitution(self):
        with self.assertRaisesRegex(ValueError, "subject digest"):
            verify_attestation_result(self._valid(), expected_subject_sha256="c" * 64,
                                      expected_source_sha="b" * 40)

    def test_rejects_missing_transparency_timestamp(self):
        result = self._valid()
        result[0]["verificationResult"]["verifiedTimestamps"] = []
        with self.assertRaisesRegex(ValueError, "transparency timestamp"):
            verify_attestation_result(result, expected_subject_sha256="a" * 64,
                                      expected_source_sha="b" * 40)

    def test_rejects_wrong_predicate_type(self):
        result = self._valid()
        result[0]["verificationResult"]["statement"]["predicateType"] = "https://example.invalid"
        with self.assertRaisesRegex(ValueError, "predicate type"):
            verify_attestation_result(result, expected_subject_sha256="a" * 64,
                                      expected_source_sha="b" * 40)

    def test_rejects_malformed_verification_shape(self):
        with self.assertRaisesRegex(ValueError, "verification result"):
            verify_attestation_result({"not": "an array"}, expected_subject_sha256="a" * 64,
                                      expected_source_sha="b" * 40)


if __name__ == "__main__":
    unittest.main()
