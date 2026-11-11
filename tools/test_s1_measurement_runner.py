"""Focused tests for the deterministic, in-memory S1 preflight runner."""
import hashlib
import unittest

from tools.s1_measurement_harness import D10_TYPES, SCHEMA_VERSION, PURPOSE, measure_parser_input
from tools.s1_measurement_runner import (
    CASE_IDS,
    EXPECTED_FIXTURE_COUNT,
    build_recipe,
    prepare_preflight,
)

HARNESS_SOURCE = b"def frozen_harness():\n    return 'pure'\n"
RUNNER_SOURCE = b"def frozen_runner():\n    return 'pure'\n"
SOURCE_COMMIT = "a" * 40
HARNESS_SHA = hashlib.sha256(HARNESS_SOURCE).hexdigest()
RUNNER_SHA = hashlib.sha256(RUNNER_SOURCE).hexdigest()


class S1MeasurementRunnerTests(unittest.TestCase):
    def test_recipe_has_exact_22_unique_ids_and_ordered_case_inventory(self):
        recipe = build_recipe()
        self.assertEqual(len(recipe["ordered_ids"]), EXPECTED_FIXTURE_COUNT)
        self.assertEqual(len(set(recipe["ordered_ids"])), EXPECTED_FIXTURE_COUNT)
        self.assertEqual(list(recipe["parser_inputs"]), recipe["ordered_ids"])
        self.assertEqual(set(recipe["expected_case_ids"]), set(CASE_IDS))
        self.assertEqual(set(recipe["expected_fixture_types"]), set(D10_TYPES))
        self.assertEqual(set(recipe["manifest"]), set(recipe["ordered_ids"]))

    def test_all_eleven_d10_types_have_positive_syn01_control(self):
        recipe = build_recipe()
        positives = [
            record for record in recipe["manifest"].values()
            if record["case_id"] == "SYN-01"
        ]
        self.assertEqual(len(positives), len(D10_TYPES))
        self.assertEqual({record["fixture_type"] for record in positives}, set(D10_TYPES))
        self.assertTrue(all(value["expected_reason_code"] is None
                            for fid, value in recipe["oracle_records"].items()
                            if recipe["manifest"][fid]["case_id"] == "SYN-01"))

    def test_every_negative_case_has_predeclared_expected_reason(self):
        recipe = build_recipe()
        for fixture_id, record in recipe["manifest"].items():
            if record["case_id"] != "SYN-01":
                self.assertIsNotNone(recipe["oracle_records"][fixture_id]["expected_reason_code"])

    def test_duplicate_key_controls_include_top_level_and_nested(self):
        recipe = build_recipe()
        duplicate_inputs = [
            raw for fid, raw in recipe["parser_inputs"].items()
            if recipe["manifest"][fid]["case_id"] == "SYN-29"
            and recipe["oracle_records"][fid]["expected_reason_code"] == "PARSE_DUPLICATE_KEY"
        ]
        self.assertGreaterEqual(len(duplicate_inputs), 2)
        self.assertTrue(any(b'"fixture_id"' in raw for raw in duplicate_inputs))
        self.assertTrue(any(b'"outer"' in raw for raw in duplicate_inputs))

    def test_syn31_invalid_structural_probes_retain_nested_measurement_shape(self):
        recipe = build_recipe()
        probe_ids = [
            fid for fid in recipe["ordered_ids"]
            if recipe["manifest"][fid]["case_id"] == "SYN-31"
        ]
        self.assertEqual(len(probe_ids), 3)
        self.assertTrue(all(
            recipe["oracle_records"][fid]["expected_reason_code"] == "SCHEMA_FIELD_UNKNOWN"
            for fid in probe_ids
        ))
        measured = [measure_parser_input(recipe["parser_inputs"][fid]) for fid in probe_ids]
        self.assertTrue(all(row["raw_bytes"] == len(recipe["parser_inputs"][fid])
                            for row, fid in zip(measured, probe_ids)))
        self.assertGreaterEqual(max(row["max_depth"] for row in measured), 6)
        self.assertGreaterEqual(max(row["max_array_items"] for row in measured), 4)
        self.assertGreaterEqual(max(row["max_object_members"] for row in measured), 3)
        self.assertGreaterEqual(max(row["max_string_value_bytes"] for row in measured), 58)
        self.assertGreaterEqual(max(row["max_string_key_bytes"] for row in measured), 16)
        self.assertGreater(max(row["scalar_nodes"] for row in measured), 5)

    def test_oracle_is_separate_and_no_reserved_oracle_key_is_serialized(self):
        recipe = build_recipe()
        self.assertTrue(all(type(raw) is bytes for raw in recipe["parser_inputs"].values()))
        self.assertFalse(any(b'"expected"' in raw or b'"oracle"' in raw
                             for raw in recipe["parser_inputs"].values()))
        self.assertEqual(set(recipe["parser_inputs"]), set(recipe["oracle_records"]))

    def test_two_independent_recipe_builds_are_identical(self):
        first = build_recipe()
        second = build_recipe()
        self.assertEqual(first, second)
        self.assertIsNot(first["parser_inputs"], second["parser_inputs"])
        self.assertIsNot(first["oracle_records"], second["oracle_records"])

    def test_preflight_runs_all_thirteen_real_harness_assertions(self):
        result = prepare_preflight(
            harness_source_bytes=HARNESS_SOURCE,
            frozen_harness_sha256=HARNESS_SHA,
            runner_source_bytes=RUNNER_SOURCE,
            frozen_runner_sha256=RUNNER_SHA,
            source_commit=SOURCE_COMMIT,
           expected_source_commit=SOURCE_COMMIT,
            expected_source_commit=SOURCE_COMMIT,
            expected_source_commit=SOURCE_COMMIT,
            expected_source_commit=SOURCE_COMMIT,
            command="python -m unittest tools.test_s1_measurement_runner -v",
        )
        self.assertEqual(set(result["assertions"]), {f"A-{i:02d}" for i in range(1, 14)})
        self.assertTrue(all(result["assertions"].values()), result["assertions"])
        self.assertTrue(result["report_readback_valid"])
        self.assertEqual(result["fixture_count"], EXPECTED_FIXTURE_COUNT)
        self.assertEqual(result["runner_source_sha256"], RUNNER_SHA)

    def test_preflight_rejects_runner_source_digest_mismatch(self):
        with self.assertRaises(ValueError):
            prepare_preflight(
                harness_source_bytes=HARNESS_SOURCE,
                frozen_harness_sha256=HARNESS_SHA,
                runner_source_bytes=RUNNER_SOURCE,
                frozen_runner_sha256="0" * 64,
                source_commit=SOURCE_COMMIT,
                expected_source_commit=SOURCE_COMMIT,
                expected_source_commit=SOURCE_COMMIT,
                command="focused-tests",
            )

    def test_preflight_rejects_harness_source_digest_mismatch(self):
        with self.assertRaises(ValueError):
            prepare_preflight(
                harness_source_bytes=HARNESS_SOURCE + b"tampered",
                frozen_harness_sha256=HARNESS_SHA,
                runner_source_bytes=RUNNER_SOURCE,
                frozen_runner_sha256=RUNNER_SHA,
                source_commit=SOURCE_COMMIT,
                expected_source_commit=SOURCE_COMMIT,
                expected_source_commit=SOURCE_COMMIT,
                command="focused-tests",
            )

    def test_preflight_rejects_nonempty_oracle_in_parser_input(self):
        from tools.s1_measurement_runner import validate_recipe
        recipe = build_recipe()
        first = recipe["ordered_ids"][0]
        recipe["parser_inputs"][first] += b',"expected":{}'
        self.assertFalse(validate_recipe(recipe))

    def test_preflight_rejects_manifest_mutation(self):
        from tools.s1_measurement_runner import validate_recipe
        recipe = build_recipe()
        first = recipe["ordered_ids"][0]
        recipe["manifest"][first]["fixture_type"] = "NOT_D10"
        self.assertFalse(validate_recipe(recipe))

    def test_preflight_rejects_oracle_reason_mutation(self):
        from tools.s1_measurement_runner import validate_recipe
        recipe = build_recipe()
        first = recipe["ordered_ids"][0]
        recipe["oracle_records"][first]["expected_reason_code"] = "SCHEMA_FIELD_MISSING"
        self.assertFalse(validate_recipe(recipe))

    def test_preflight_rejects_execution_trace_with_any_event(self):
        from tools.s1_measurement_runner import validate_empty_execution_trace
        self.assertTrue(validate_empty_execution_trace({
            "payload_persistence_events": [], "external_access_events": []
        }))
        self.assertFalse(validate_empty_execution_trace({
            "payload_persistence_events": ["write"], "external_access_events": []
        }))
        self.assertFalse(validate_empty_execution_trace({
            "payload_persistence_events": [], "external_access_events": ["network"]
        }))

    def test_preflight_rejects_runner_source_with_file_or_network_capability(self):
        from tools.s1_measurement_runner import validate_runner_source
        file_source = b"def bad(path):\n    with open(path, 'wb') as f: f.write(b'x')\n"
        network_source = b"import socket\ndef bad(): return socket.socket()\n"
        self.assertFalse(validate_runner_source(file_source, hashlib.sha256(file_source).hexdigest()))
        self.assertFalse(validate_runner_source(network_source, hashlib.sha256(network_source).hexdigest()))

    def test_preflight_is_deterministic_across_two_measurement_passes(self):
        result = prepare_preflight(
            harness_source_bytes=HARNESS_SOURCE,
            frozen_harness_sha256=HARNESS_SHA,
            runner_source_bytes=RUNNER_SOURCE,
            frozen_runner_sha256=RUNNER_SHA,
            source_commit=SOURCE_COMMIT,
            expected_source_commit=SOURCE_COMMIT,
            expected_source_commit=SOURCE_COMMIT,
            command="focused-tests",
        )
        self.assertEqual(result["measurement_pass_1"], result["measurement_pass_2"])
        self.assertEqual(result["parser_input_digest"], result["measurement_pass_1"]["corpus_sha256"])

    def test_preflight_reports_no_payload_or_external_activity(self):
        result = prepare_preflight(
            harness_source_bytes=HARNESS_SOURCE,
            frozen_harness_sha256=HARNESS_SHA,
            runner_source_bytes=RUNNER_SOURCE,
            frozen_runner_sha256=RUNNER_SHA,
            source_commit=SOURCE_COMMIT,
            expected_source_commit=SOURCE_COMMIT,
            expected_source_commit=SOURCE_COMMIT,
            command="focused-tests",
        )
        self.assertEqual(result["execution_trace"], {
            "payload_persistence_events": [], "external_access_events": []
        })

    def test_preflight_does_not_change_frozen_harness_contract_constants(self):
        self.assertEqual(SCHEMA_VERSION, "synthetic-contract-fixture/v1")
        self.assertEqual(PURPOSE, "PARSER_CONTRACT_TEST_ONLY")
        self.assertEqual(len(D10_TYPES), 11)


class G040BRegressionTests(unittest.TestCase):
    def _actual_sources(self):
        from pathlib import Path
        root = Path(__file__).resolve().parent
        return (
            (root / "s1_measurement_harness.py").read_bytes(),
            (root / "s1_measurement_runner.py").read_bytes(),
        )

    def test_preflight_uses_actual_checked_out_source_bytes_and_commit(self):
        import os
        harness_bytes, runner_bytes = self._actual_sources()
        checkout = os.environ.get("G0_SOURCE_COMMIT", SOURCE_COMMIT)
        result = prepare_preflight(
            harness_source_bytes=harness_bytes,
            frozen_harness_sha256=hashlib.sha256(harness_bytes).hexdigest(),
            runner_source_bytes=runner_bytes,
            frozen_runner_sha256=hashlib.sha256(runner_bytes).hexdigest(),
            source_commit=checkout,
            expected_source_commit=checkout,
            command="python -m unittest tools.test_s1_measurement_runner -v",
        )
        self.assertEqual(result["harness_source_sha256"], hashlib.sha256(harness_bytes).hexdigest())
        self.assertEqual(result["runner_source_sha256"], hashlib.sha256(runner_bytes).hexdigest())
        self.assertEqual(result["source_commit"], checkout)

    def test_preflight_rejects_source_commit_not_equal_to_verified_checkout(self):
        harness_bytes, runner_bytes = self._actual_sources()
        with self.assertRaises(ValueError):
            prepare_preflight(
                harness_source_bytes=harness_bytes,
                frozen_harness_sha256=hashlib.sha256(harness_bytes).hexdigest(),
                runner_source_bytes=runner_bytes,
                frozen_runner_sha256=hashlib.sha256(runner_bytes).hexdigest(),
                source_commit="a" * 40,
                expected_source_commit="b" * 40,
                command="focused-tests",
            )

    def test_capability_policy_rejects_aliased_io_open(self):
        from tools.s1_measurement_harness import validate_capability_boundary
        source = b"from io import open as file_open\ndef f(path): return file_open(path)\n"
        self.assertFalse(validate_capability_boundary(source, "persistence"))

    def test_capability_policy_rejects_archive_extraction(self):
        from tools.s1_measurement_harness import validate_capability_boundary
        for source in (
            b"import zipfile\ndef f(z, p): z.extractall(p)\n",
            b"import tarfile\ndef f(t, p): t.extractall(p)\n",
        ):
            self.assertFalse(validate_capability_boundary(source, "persistence"))

    def test_capability_policy_rejects_smtplib_external_access(self):
        from tools.s1_measurement_harness import validate_capability_boundary
        source = b"import smtplib\ndef f(): return smtplib.SMTP('example.invalid')\n"
        self.assertFalse(validate_capability_boundary(source, "external"))

    def _valid_report(self):
        import json
        from tools.s1_measurement_harness import measure_corpus, build_report
        recipe = build_recipe()
        measurement = measure_corpus(recipe["parser_inputs"], recipe["ordered_ids"])
        assertions = {f"A-{i:02d}": True for i in range(1, 14)}
        provenance = {
            "corpus_revision": "synthetic-test",
            "source_commit": SOURCE_COMMIT,
            "source_blob_sha256": HARNESS_SHA,
            "command": "focused-tests",
            "python_version": "test",
            "platform": "test",
            "measurement_definition_revision": "S1-MEASUREMENTS-V1",
        }
        report_bytes = build_report("synthetic-test", measurement, assertions, provenance)
        return json.loads(report_bytes), recipe

    def test_report_readback_rejects_duplicate_fixture_ids(self):
        import json
        from tools.s1_measurement_harness import validate_report_readback
        report, recipe = self._valid_report()
        report["measurement"]["rows"][1]["fixture_id"] = report["measurement"]["rows"][0]["fixture_id"]
        raw = json.dumps(report, separators=(",", ":")).encode()
        self.assertFalse(validate_report_readback(raw, recipe["parser_inputs"], recipe["ordered_ids"]))

    def test_report_readback_rejects_reordered_fixture_rows(self):
        import json
        from tools.s1_measurement_harness import validate_report_readback
        report, recipe = self._valid_report()
        report["measurement"]["rows"].reverse()
        raw = json.dumps(report, separators=(",", ":")).encode()
        self.assertFalse(validate_report_readback(raw, recipe["parser_inputs"], recipe["ordered_ids"]))

    def test_report_readback_rejects_missing_or_extra_rows(self):
        import json
        from tools.s1_measurement_harness import validate_report_readback
        for operation in ("missing", "extra"):
            report, recipe = self._valid_report()
            if operation == "missing":
                report["measurement"]["rows"].pop()
            else:
                report["measurement"]["rows"].append(dict(report["measurement"]["rows"][0]))
                report["measurement"]["aggregates"]["fixture_count"] += 1
            raw = json.dumps(report, separators=(",", ":")).encode()
            self.assertFalse(validate_report_readback(raw, recipe["parser_inputs"], recipe["ordered_ids"]))

    def test_report_readback_rejects_modified_raw_byte_count(self):
        import json
        from tools.s1_measurement_harness import validate_report_readback
        report, recipe = self._valid_report()
        report["measurement"]["rows"][0]["raw_bytes"] += 1
        report["measurement"]["aggregates"]["total_raw_bytes"] += 1
        raw = json.dumps(report, separators=(",", ":")).encode()
        self.assertFalse(validate_report_readback(raw, recipe["parser_inputs"], recipe["ordered_ids"]))

    def test_report_readback_rejects_altered_corpus_digest(self):
        import json
        from tools.s1_measurement_harness import validate_report_readback
        report, recipe = self._valid_report()
        report["measurement"]["corpus_sha256"] = "0" * 64
        raw = json.dumps(report, separators=(",", ":")).encode()
        self.assertFalse(validate_report_readback(raw, recipe["parser_inputs"], recipe["ordered_ids"]))


if __name__ == "__main__":
    unittest.main()
