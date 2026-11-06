import hashlib
import json
import tempfile
import unittest
import uuid
from pathlib import Path

from synthetic_evidence.generator import (
    canonical_json,
    generate_fixture,
    hmac_stream,
    parse_json_strict,
    write_fixture,
    verify_local_replay,
    _stats,
)

SEED = "00" * 32
NAMESPACE = "2e4e8f6e-9a3c-5d72-9b4a-8a4f6b2d1c30"
SOURCE_SHA = "a" * 40
BASE_TIME = "2026-11-07T00:00:00.000Z"


class CanonicalJsonTests(unittest.TestCase):
    def test_sorts_keys_by_utf16_code_units_and_emits_compact_utf8(self):
        value = {"z": 1, "a": "é", "𝄞": True, "\ue000": None}
        encoded = canonical_json(value)
        self.assertEqual(encoded, '{"a":"é","z":1,"𝄞":true,"":null}'.encode())

    def test_rejects_floats_and_unsafe_integers(self):
        with self.assertRaises(ValueError):
            canonical_json({"amount": 1.25})
        with self.assertRaises(ValueError):
            canonical_json({"sequence": 2**53})

    def test_rejects_unpaired_surrogates(self):
        with self.assertRaises(ValueError):
            canonical_json({"bad": "\ud800"})

    def test_strict_parser_rejects_duplicate_keys(self):
        with self.assertRaises(ValueError):
            parse_json_strict('{"x":1,"x":2}')


class DeterministicPrfTests(unittest.TestCase):
    def test_fixed_seed_and_domain_are_reproducible(self):
        first = hmac_stream(SEED, "fixture/test/v1", "SYNTH-CORE-001", 1, "payload.value", 0, 48)
        second = hmac_stream(SEED, "fixture/test/v1", "SYNTH-CORE-001", 1, "payload.value", 0, 48)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 48)
        self.assertEqual(first.hex(), "295d276fe4dbf9151bcf5f2d2e9788ba95336bdafe41f199b5b550e9dcfc95b65db1576c334abaecf0411afae8f8977f")

    def test_rejects_invalid_seed_stream_and_sequence(self):
        for args in [("00", "fixture/test/v1", "SYNTH-CORE-001", 1),
                     (SEED, "fixture/test/v1", "bad stream", 1),
                     (SEED, "fixture/test/v1", "SYNTH-CORE-001", 0),
                     (SEED, "fixture/test/v1", "SYNTH-CORE-001", 2**64)]:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    hmac_stream(*args, "field", 0, 1)


class FixtureTests(unittest.TestCase):
    def build(self, count=120):
        return generate_fixture(
            seed_hex=SEED,
            namespace=NAMESPACE,
            base_time_utc=BASE_TIME,
            event_count=count,
            source_sha=SOURCE_SHA,
            segment_event_cap=7,
            segment_byte_cap=65536,
        )

    def test_same_descriptor_produces_identical_events_segments_and_manifests(self):
        a = self.build()
        b = self.build()
        self.assertEqual(a["events_jsonl"], b["events_jsonl"])
        self.assertEqual(a["segments"], b["segments"])
        self.assertEqual(a["manifests_jsonl"], b["manifests_jsonl"])
        self.assertEqual(a["descriptor"], b["descriptor"])

    def test_event_ids_sequences_hash_chain_and_causality_are_valid(self):
        fixture = self.build()
        seen = {}
        for event in fixture["events"]:
            core = event["event_core"]
            stream = core["stream_id"]
            sequence = int(core["sequence"])
            self.assertEqual(len(core["sequence"]), 20)
            self.assertEqual(sequence, len(seen.setdefault(stream, [])) + 1)
            expected_id = str(uuid.uuid5(uuid.UUID(NAMESPACE), f"{stream}:{sequence:020d}"))
            self.assertEqual(core["event_id"], expected_id)
            previous = seen[stream][-1]["integrity"]["event_hash"] if seen[stream] else "GENESIS"
            self.assertEqual(core["previous_event_hash"], previous)
            if core["causality"]["causation_event_ids"]:
                self.assertEqual(core["causality"]["causation_event_ids"][-1], seen[stream][-1]["event_core"]["event_id"])
            raw = canonical_json(core)
            expected_hash = hashlib.sha256(b"BTCUSDT-PAPER-EVENT-V1\n" + raw).hexdigest()
            self.assertEqual(event["integrity"]["event_hash"], expected_hash)
            seen[stream].append(event)

    def test_clean_fixture_has_core_ai_and_legacy_streams_and_no_private_keys(self):
        fixture = self.build()
        streams = {e["event_core"]["stream_id"] for e in fixture["events"]}
        self.assertEqual(streams, {"SYNTH-CORE-001", "SYNTH-AI-001", "SYNTH-LEGACY-001"})
        self.assertEqual(len(fixture["events"]), 120)
        self.assertGreaterEqual(len(fixture["negative_vectors"]), 10)
        self.assertTrue(all(not vector["clean_volume_denominator"] for vector in fixture["negative_vectors"]))
        self.assertIn("UNKNOWN_FEE_FUNDING", {vector["name"] for vector in fixture["negative_vectors"]})
        self.assertTrue({"config", "intent_signal", "risk_decision", "reservation", "order_lifecycle", "position_transition", "fee_adjustment", "funding", "mark_valuation", "baseline_risk", "recovery_audit"}.issubset(fixture["measurements"]["event_counts_by_class"]))
        serialized = json.dumps(fixture["descriptor"], sort_keys=True)
        self.assertNotIn("private_key", serialized)
        self.assertNotIn("seed_hex", serialized)
        self.assertIn("hash_signature_profile", fixture["descriptor"])
        self.assertIn("cpu_count", fixture["descriptor"]["environment"])
        self.assertEqual(fixture["descriptor"]["environment"]["storage_medium"], "NOT_MEASURED")

    def test_segments_are_single_stream_contiguous_and_within_byte_cap(self):
        fixture = self.build()
        for segment in fixture["segments"]:
            self.assertLessEqual(segment["byte_length"], 65536)
            self.assertEqual(segment["first_sequence"] + segment["event_count"] - 1, segment["last_sequence"])
            self.assertTrue(all(e["event_core"]["stream_id"] == segment["stream_id"] for e in segment["events"]))
            manifest_core = segment["manifest"]["manifest_core"]
            expected_manifest_hash = hashlib.sha256(b"BTCUSDT-PAPER-MANIFEST-V1\n" + canonical_json(manifest_core)).hexdigest()
            self.assertEqual(segment["manifest"]["integrity"]["manifest_hash"], expected_manifest_hash)
            self.assertEqual(hashlib.sha256(segment["data"]).hexdigest(), manifest_core["segment_sha256"])

    def test_nearest_rank_quantiles_use_exact_ceiling_rule(self):
        stats = _stats([1, 2, 3, 4, 5])
        self.assertEqual(stats["mean"], "3")
        self.assertEqual(stats["p50"], 3)
        self.assertEqual(stats["p90"], 5)
        self.assertEqual(stats["p95"], 5)
        self.assertEqual(stats["p99"], 5)

    def test_measurements_include_mean_and_nearest_rank_quantiles(self):
        fixture = self.build()
        stats = fixture["measurements"]["event_core_bytes"]["overall"]
        self.assertEqual(stats["sample_count"], 120)
        self.assertIn("mean", stats)
        self.assertIn("p95", stats)
        self.assertEqual(sum(fixture["measurements"]["event_class_target_counts_normalized"].values()), 120)
        self.assertEqual(fixture["measurements"]["event_class_target_weight_sum"], 94)

    def test_segments_close_at_exact_byte_cap_and_reject_one_byte_too_small(self):
        roomy = generate_fixture(seed_hex=SEED, namespace=NAMESPACE, base_time_utc=BASE_TIME,
                                 event_count=3, source_sha=SOURCE_SHA,
                                 segment_event_cap=10, segment_byte_cap=65536)
        one_event_bytes = max(len(segment["data"]) for segment in roomy["segments"])
        exact = generate_fixture(seed_hex=SEED, namespace=NAMESPACE, base_time_utc=BASE_TIME,
                                  event_count=3, source_sha=SOURCE_SHA,
                                  segment_event_cap=10, segment_byte_cap=one_event_bytes)
        self.assertTrue(all(segment["byte_length"] <= one_event_bytes for segment in exact["segments"]))
        with self.assertRaisesRegex(ValueError, "single event exceeds"):
            generate_fixture(seed_hex=SEED, namespace=NAMESPACE, base_time_utc=BASE_TIME,
                             event_count=3, source_sha=SOURCE_SHA,
                             segment_event_cap=10, segment_byte_cap=one_event_bytes - 1)

    def test_local_replay_detects_tampering_and_labels_assurance(self):
        fixture = self.build()
        result = verify_local_replay(fixture["events"])
        self.assertEqual(result["assurance"], "LOCAL_REPLAY_SIMULATION")
        corrupted = [dict(event) for event in fixture["events"]]
        corrupted[0] = {"event_core": dict(corrupted[0]["event_core"]), "integrity": dict(corrupted[0]["integrity"])}
        corrupted[0]["event_core"]["payload"] = dict(corrupted[0]["event_core"]["payload"])
        corrupted[0]["event_core"]["payload"]["amount"] = "999.9999"
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            verify_local_replay(corrupted)

    def test_local_replay_treats_identical_duplicate_delivery_as_idempotent(self):
        fixture = self.build()
        events = list(fixture["events"])
        events.insert(1, events[0])
        result = verify_local_replay(events)
        self.assertEqual(result["duplicate_deliveries_ignored"], 1)
        self.assertEqual(result["events_verified"], 120)

    def test_local_replay_rejects_same_event_id_with_changed_bytes(self):
        fixture = self.build()
        events = list(fixture["events"])
        changed = json.loads(json.dumps(events[0]))
        changed["event_core"]["payload"]["amount"] = "9.9999"
        events.insert(1, changed)
        with self.assertRaisesRegex(ValueError, "same event ID delivered with changed bytes"):
            verify_local_replay(events)

    def test_local_replay_rejects_sequence_gap_and_wrong_previous_hash(self):
        fixture = self.build()
        by_stream = {}
        for event in fixture["events"]:
            by_stream.setdefault(event["event_core"]["stream_id"], []).append(event)
        stream = "SYNTH-CORE-001"
        gap = [event for event in fixture["events"] if event["event_core"]["stream_id"] != stream]
        gap.extend(by_stream[stream][0:1] + by_stream[stream][2:])
        gap.sort(key=lambda event: (event["event_core"]["time"]["committed_at"], event["event_core"]["stream_id"], event["event_core"]["sequence"]))
        with self.assertRaisesRegex(ValueError, "sequence gap or reorder"):
            verify_local_replay(gap)
        wrong = json.loads(json.dumps(fixture["events"]))
        target = next(event for event in wrong if event["event_core"]["stream_id"] == stream and event["event_core"]["sequence"] == "00000000000000000002")
        target["event_core"]["previous_event_hash"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "previous hash mismatch"):
            verify_local_replay(wrong)

    def test_fixture_writer_refuses_to_overwrite_existing_directory(self):
        fixture = self.build()
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "out"
            write_fixture(fixture, target)
            with self.assertRaises(FileExistsError):
                write_fixture(fixture, target)

    def test_writer_creates_only_local_synthetic_outputs(self):
        fixture = self.build()
        with tempfile.TemporaryDirectory() as tmp:
            output = write_fixture(fixture, Path(tmp) / "out")
            self.assertTrue((output / "run_descriptor.json").is_file())
            self.assertTrue((output / "events.jsonl").is_file())
            self.assertTrue((output / "manifests.jsonl").is_file())
            self.assertTrue((output / "measurements.json").is_file())
            self.assertTrue((output / "negative_vectors.json").is_file())
            self.assertTrue((output / "fixture.sha256").is_file())


if __name__ == "__main__":
    unittest.main()
