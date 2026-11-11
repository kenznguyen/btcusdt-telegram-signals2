import hashlib
import unittest

from t0_signature_stage1.primitives import (
    StageIError,
    anchor_object_digest,
    b64url_decode,
    b64url_encode,
    canonicalize,
    evidence_object_digest,
    parse_canonical_json,
    parse_u64,
    signature_envelope_digest,
    trust_policy_body_digest,
    u64be,
)


class StrictJsonTests(unittest.TestCase):
    def test_canonicalizes_object_keys_by_utf16_code_units(self):
        value = {"z": 1, "a": "é", "😀": True}
        self.assertEqual(canonicalize(value), '{"a":"é","z":1,"😀":true}'.encode())

    def test_rejects_duplicate_object_keys(self):
        with self.assertRaisesRegex(StageIError, "NONCANONICAL_STATEMENT"):
            parse_canonical_json(b'{"a":1,"a":2}')

    def test_rejects_utf8_bom(self):
        with self.assertRaisesRegex(StageIError, "NONCANONICAL_STATEMENT"):
            parse_canonical_json(b'\xef\xbb\xbf{}')

    def test_rejects_invalid_utf8(self):
        with self.assertRaisesRegex(StageIError, "NONCANONICAL_STATEMENT"):
            parse_canonical_json(b'{"x":"\xff"}')

    def test_rejects_non_finite_and_unsupported_float_tokens(self):
        for raw in (b'{"x":NaN}', b'{"x":Infinity}', b'{"x":1.25}', b'{"x":1e2}'):
            with self.subTest(raw=raw), self.assertRaisesRegex(StageIError, "NONCANONICAL_STATEMENT"):
                parse_canonical_json(raw)

    def test_rejects_noncanonical_whitespace_and_key_order(self):
        for raw in (b'{ "a":1}', b'{"z":1,"a":2}'):
            with self.subTest(raw=raw), self.assertRaisesRegex(StageIError, "NONCANONICAL_STATEMENT"):
                parse_canonical_json(raw)

    def test_sorts_supplementary_key_by_utf16_not_unicode_scalar_value(self):
        value = {"\ue000": 1, "😀": 2}
        self.assertEqual(canonicalize(value), '{"😀":2,"\ue000":1}'.encode())

    def test_rejects_json_integer_outside_safe_integer_range(self):
        with self.assertRaisesRegex(StageIError, "NONCANONICAL_STATEMENT"):
            parse_canonical_json(b'{"n":9007199254740992}')

    def test_rejects_unpaired_surrogate(self):
        with self.assertRaisesRegex(StageIError, "NONCANONICAL_STATEMENT"):
            canonicalize({"x": "\ud800"})

    def test_accepts_exact_canonical_bytes(self):
        raw = b'{"a":true,"b":[0,"x",null]}'
        self.assertEqual(parse_canonical_json(raw), {"a": True, "b": [0, "x", None]})


class U64Tests(unittest.TestCase):
    def test_canonical_u64_vectors(self):
        vectors = {
            "0": "0000000000000000",
            "1": "0000000000000001",
            "18446744073709551615": "ffffffffffffffff",
        }
        for decimal, expected_hex in vectors.items():
            with self.subTest(decimal=decimal):
                value = parse_u64(decimal)
                self.assertEqual(u64be(value).hex(), expected_hex)

    def test_rejects_noncanonical_u64(self):
        for value in ("", "00", "01", "+1", "-1", "1.0", "1e0", " 1", "１"):
            with self.subTest(value=value), self.assertRaisesRegex(StageIError, "U64_NONCANONICAL"):
                parse_u64(value)

    def test_rejects_u64_overflow(self):
        for value in ("18446744073709551616", "9" * 5000):
            with self.subTest(value_length=len(value)), self.assertRaisesRegex(StageIError, "U64_OVERFLOW"):
                parse_u64(value)

    def test_u64be_rejects_out_of_range_values(self):
        for value in (-1, 1 << 64):
            with self.subTest(value=value), self.assertRaisesRegex(StageIError, "U64_OVERFLOW"):
                u64be(value)


class Base64UrlTests(unittest.TestCase):
    def test_canonical_unpadded_vectors(self):
        self.assertEqual(b64url_encode(b"\x00"), "AA")
        self.assertEqual(b64url_encode(b"\xff"), "_w")
        self.assertEqual(b64url_encode(b"\xfb"), "-w")
        self.assertEqual(b64url_decode("AA"), b"\x00")
        self.assertEqual(b64url_decode("_w"), b"\xff")
        self.assertEqual(b64url_decode("-w"), b"\xfb")

    def test_rejects_padding_standard_alphabet_whitespace_and_bad_pad_bits(self):
        for value in ("AA==", "+w", "/w", "A A", "A", "AB"):
            with self.subTest(value=value), self.assertRaisesRegex(StageIError, "BASE64URL_NONCANONICAL"):
                b64url_decode(value)

    def test_empty_value_requires_explicit_permission(self):
        with self.assertRaisesRegex(StageIError, "BASE64URL_NONCANONICAL"):
            b64url_decode("")
        self.assertEqual(b64url_decode("", allow_empty=True), b"")


class DigestTests(unittest.TestCase):
    def test_evidence_object_digest_matches_independent_oracle(self):
        payload = b'{"a":1}'
        expected = hashlib.sha256(b"T0-EVIDENCE-OBJECT-V1\x00" + len(payload).to_bytes(8, "big") + payload).hexdigest()
        self.assertEqual(evidence_object_digest(payload), expected)

    def test_trust_policy_digest_fails_closed_on_ambiguous_domain_escape(self):
        with self.assertRaisesRegex(StageIError, "DOMAIN_SEPARATOR_ENCODING_UNRESOLVED"):
            trust_policy_body_digest(b'{"policy_id":"synthetic"}')

    def test_anchor_envelope_digest_fails_closed_on_ambiguous_domain_escape(self):
        with self.assertRaisesRegex(StageIError, "DOMAIN_SEPARATOR_ENCODING_UNRESOLVED"):
            anchor_object_digest(b'{"anchor_type":"synthetic"}')

    def test_signature_envelope_digest_fails_closed_on_ambiguous_domain_escape(self):
        with self.assertRaisesRegex(StageIError, "DOMAIN_SEPARATOR_ENCODING_UNRESOLVED"):
            signature_envelope_digest(b'{"signature":"mock"}')
