import json
import unittest

from pipeline.synthetic_contract import (
    D10_TYPES, MAX_ARRAY_ITEMS, MAX_DEPTH, MAX_INPUT_BYTES,
    MAX_OBJECT_MEMBERS, MAX_SCALAR_NODES, MAX_STRING_KEY_BYTES,
    MAX_STRING_VALUE_BYTES, PURPOSE, SCHEMA_VERSION, parse_fixture,
)


def fixture(**changes):
    value = {
        "schema_version": SCHEMA_VERSION,
        "fixture_id": "syn-fixture-001",
        "case_id": "SYN-01",
        "fixture_type": "SYNTHETIC_OBJECT",
        "subject": {
            "object_id": "syn-object-001",
            "version_id": "syn-version-001",
            "namespace": "syn-namespace-001",
        },
        "purpose": PURPOSE,
        "claims": {},
    }
    value.update(changes)
    return value


def encode(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("utf-8")


class SyntheticContractTests(unittest.TestCase):
    def test_valid_fixture_is_deterministic_and_has_no_authority(self):
        raw = encode(fixture())
        first = parse_fixture(raw)
        self.assertEqual(first, parse_fixture(raw))
        self.assertIsNone(first.reason_code)
        self.assertFalse(first.trusted)
        self.assertFalse(first.execution_authorized)

    def test_accepts_all_ratified_d10_values(self):
        for fixture_type in D10_TYPES:
            with self.subTest(fixture_type=fixture_type):
                self.assertIsNone(parse_fixture(encode(fixture(fixture_type=fixture_type))).reason_code)

    def test_rejects_unknown_d10_value(self):
        self.assertEqual(parse_fixture(encode(fixture(fixture_type="REAL_EVIDENCE"))).reason_code,
                         "SCHEMA_VALUE_OUT_OF_RANGE")

    def test_rejects_unsupported_schema_and_purpose(self):
        self.assertEqual(parse_fixture(encode(fixture(schema_version="v2"))).reason_code,
                         "SCHEMA_VERSION_UNSUPPORTED")
        self.assertEqual(parse_fixture(encode(fixture(purpose="PRODUCTION"))).reason_code,
                         "SCHEMA_PURPOSE_UNSUPPORTED")

    def test_rejects_unknown_missing_and_oracle_fields(self):
        self.assertEqual(parse_fixture(encode(fixture(extra=1))).reason_code, "SCHEMA_FIELD_UNKNOWN")
        self.assertEqual(parse_fixture(encode(fixture(expected={"expected_reason_code": None}))).reason_code,
                         "SCHEMA_FIELD_UNKNOWN")
        missing = fixture()
        del missing["purpose"]
        self.assertEqual(parse_fixture(encode(missing)).reason_code, "SCHEMA_FIELD_MISSING")

    def test_rejects_unknown_and_missing_subject_fields(self):
        unknown = fixture()
        unknown["subject"]["extra"] = "syn-extra"
        missing = fixture()
        del missing["subject"]["namespace"]
        self.assertEqual(parse_fixture(encode(unknown)).reason_code, "SCHEMA_FIELD_UNKNOWN")
        self.assertEqual(parse_fixture(encode(missing)).reason_code, "SCHEMA_FIELD_MISSING")

    def test_rejects_wrong_types_without_coercion_and_nonempty_claims(self):
        cases = (
            ("fixture_id", 1, "SCHEMA_TYPE_MISMATCH"),
            ("case_id", True, "SCHEMA_TYPE_MISMATCH"),
            ("claims", [], "SCHEMA_TYPE_MISMATCH"),
            ("notes", None, "SCHEMA_TYPE_MISMATCH"),
            ("notes", "real-person-note", "SCHEMA_SYNTHETIC_ID_INVALID"),
            ("subject", [], "SCHEMA_TYPE_MISMATCH"),
            ("claims", {"claim": "syn-value"}, "SCHEMA_TYPE_MISMATCH"),
        )
        for key, value, expected in cases:
            with self.subTest(key=key, value=value):
                self.assertEqual(parse_fixture(encode(fixture(**{key: value}))).reason_code, expected)

    def test_accepts_synthetic_notes(self):
        self.assertIsNone(parse_fixture(encode(fixture(notes="syn-note-001"))).reason_code)

    def test_rejects_non_synthetic_identifiers(self):
        self.assertEqual(parse_fixture(encode(fixture(fixture_id="real-id"))).reason_code,
                         "SCHEMA_SYNTHETIC_ID_INVALID")
        subject = {"object_id": "real-id", "version_id": "syn-v1", "namespace": "syn-ns"}
        self.assertEqual(parse_fixture(encode(fixture(subject=subject))).reason_code,
                         "SCHEMA_SYNTHETIC_ID_INVALID")

    def test_rejects_non_bytes_and_oversized_raw_input(self):
        self.assertEqual(parse_fixture(bytearray(b"{}")).reason_code, "INPUT_NOT_BYTES")
        self.assertEqual(parse_fixture(b" " * (MAX_INPUT_BYTES + 1)).reason_code, "LIMIT_RAW_BYTES")

    def test_rejects_invalid_utf8_json_non_json_whitespace_and_trailing_content(self):
        cases = (
            (b"\xff", "PARSE_INVALID_UTF8"),
            (b"{", "PARSE_INVALID_JSON"),
            (b"\xc2\xa0{}", "PARSE_INVALID_JSON"),
            (encode(fixture()) + b" {}", "PARSE_TRAILING_CONTENT"),
        )
        for raw, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(parse_fixture(raw).reason_code, expected)

    def test_rejects_nonfinite_numbers_and_invalid_unicode_scalars(self):
        self.assertEqual(parse_fixture(b'{"value":NaN}').reason_code, "PARSE_NONFINITE_NUMBER")
        self.assertEqual(parse_fixture(b'{"value":1e999}').reason_code, "PARSE_NONFINITE_NUMBER")
        self.assertEqual(parse_fixture(b'{"value":"\\ud800"}').reason_code, "PARSE_INVALID_UNICODE")

    def test_rejects_duplicate_keys_at_top_level_and_nested_depth(self):
        self.assertEqual(parse_fixture(b'{"a":1,"a":2}').reason_code, "PARSE_DUPLICATE_KEY")
        self.assertEqual(parse_fixture(b'{"a":{"x":1,"x":2}}').reason_code, "PARSE_DUPLICATE_KEY")

    def test_accepts_exact_raw_byte_limit_and_rejects_one_over(self):
        base = encode(fixture())
        exact = base + b" " * (MAX_INPUT_BYTES - len(base))
        self.assertIsNone(parse_fixture(exact).reason_code)
        self.assertEqual(parse_fixture(exact + b" ").reason_code, "LIMIT_RAW_BYTES")

    def test_accepts_exact_depth_and_rejects_one_over(self):
        def nested(depth):
            value = 0
            for _ in range(depth):
                value = [value]
            return encode(value)

        self.assertEqual(parse_fixture(nested(MAX_DEPTH)).reason_code, "SCHEMA_TYPE_MISMATCH")
        self.assertEqual(parse_fixture(nested(MAX_DEPTH + 1)).reason_code, "LIMIT_DEPTH")

    def test_accepts_exact_object_members_and_rejects_one_over(self):
        exact = {str(index): index for index in range(MAX_OBJECT_MEMBERS)}
        over = {str(index): index for index in range(MAX_OBJECT_MEMBERS + 1)}
        self.assertEqual(parse_fixture(encode(exact)).reason_code, "SCHEMA_FIELD_UNKNOWN")
        self.assertEqual(parse_fixture(encode(over)).reason_code, "LIMIT_OBJECT_MEMBERS")

    def test_accepts_exact_array_items_and_rejects_one_over(self):
        self.assertEqual(parse_fixture(encode([0] * MAX_ARRAY_ITEMS)).reason_code, "SCHEMA_TYPE_MISMATCH")
        self.assertEqual(parse_fixture(encode([0] * (MAX_ARRAY_ITEMS + 1))).reason_code, "LIMIT_ARRAY_ITEMS")

    def test_enforces_string_value_limit_in_utf8_bytes(self):
        self.assertEqual(parse_fixture(encode("a" * MAX_STRING_VALUE_BYTES)).reason_code,
                         "SCHEMA_TYPE_MISMATCH")
        self.assertEqual(parse_fixture(encode("é" * (MAX_STRING_VALUE_BYTES // 2 + 1))).reason_code,
                         "LIMIT_STRING_VALUE_BYTES")

    def test_enforces_string_key_limit_in_utf8_bytes(self):
        self.assertEqual(parse_fixture(encode({"a" * MAX_STRING_KEY_BYTES: 1})).reason_code,
                         "SCHEMA_FIELD_UNKNOWN")
        self.assertEqual(parse_fixture(encode({"a" * (MAX_STRING_KEY_BYTES + 1): 1})).reason_code,
                         "LIMIT_STRING_KEY_BYTES")
        self.assertEqual(parse_fixture(encode({"é" * (MAX_STRING_KEY_BYTES // 2 + 1): 1})).reason_code,
                         "LIMIT_STRING_KEY_BYTES")

    def test_enforces_scalar_node_limit(self):
        exact = {key: [0] * 64 for key in ("a", "b", "c", "d")}
        over = dict(exact, e=[0])
        self.assertEqual(parse_fixture(encode(exact)).reason_code, "SCHEMA_FIELD_UNKNOWN")
        self.assertEqual(parse_fixture(encode(over)).reason_code, "LIMIT_SCALAR_NODES")

    def test_returns_one_fixed_reason_without_echo_or_authority(self):
        result = parse_fixture(b'{"token":"do-not-echo","unknown":true}')
        self.assertIsInstance(result.reason_code, str)
        self.assertNotIn("do-not-echo", repr(result))
        self.assertFalse(result.trusted)
        self.assertFalse(result.execution_authorized)

    def test_does_not_mutate_input_bytes(self):
        raw = encode(fixture())
        original = bytes(raw)
        parse_fixture(raw)
        self.assertEqual(raw, original)


if __name__ == "__main__":
    unittest.main()
