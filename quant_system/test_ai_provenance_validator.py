"""Signed AI OOS provenance validator contracts; all artifacts are synthetic fixtures."""
import base64
import hashlib
import json
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from quant_system.ai_provenance_validator import verify_signed_provenance
from quant_system.ai_calibration_evaluator import (
    CalibrationEvaluator,
    CalibrationObservation,
    approved_calibration_gate_policy,
)


ROLES = ("model", "dataset", "predictions", "split_protocol", "calibration_report")



def make_t0_snapshot(timeframe, count):
    interval = {"15m": 900_000, "1h": 3_600_000}[timeframe]
    anchor = 1_700_000_000_000
    start = (anchor // interval) * interval
    candles = []
    for index in range(count):
        opened = start + index * interval
        candles.append({
            "exchange": "binance", "marketType": "USDT_PERPETUAL",
            "symbol": "BTCUSDT", "timeframe": timeframe,
            "openTimeMs": opened, "closeTimeMs": opened + interval,
            "open": "65000.10", "high": "65100.20", "low": "64900.05",
            "close": "65050.25", "volume": "12.345", "isClosed": True,
            "availableAtMs": opened + interval + 1000,
            "availabilityKind": "FIRST_OBSERVED", "quality": "VALIDATED",
            "source": "ccxt.binanceusdm",
        })
    payload = {
        "exchange": "binance", "marketType": "USDT_PERPETUAL",
        "symbol": "BTCUSDT", "timeframe": timeframe,
        "startMs": candles[0]["openTimeMs"],
        "endMs": candles[-1]["closeTimeMs"], "asOfMs": None,
        "candles": candles,
    }
    identity = {key: payload[key] for key in (
        "exchange", "marketType", "symbol", "timeframe",
        "startMs", "endMs", "asOfMs", "candles",
    )}
    payload["datasetVersion"] = "sha256:" + hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    payload["coverage"] = {
        "expected": count, "returned": count, "complete": True, "gaps": [],
    }
    payload["generatedAtMs"] = candles[-1]["availableAtMs"] + 1
    return payload


def make_m15_h1_bundle():
    snapshots = {
        "15m": make_t0_snapshot("15m", 24),
        "1h": make_t0_snapshot("1h", 6),
    }
    identity = {
        "schema_version": 1,
        "format": "T0_M15_H1_DATASET_BUNDLE_V1",
        "source": "T0_CANONICAL_BINANCE_USDT_PERPETUAL",
        "exchange": "binance", "marketType": "USDT_PERPETUAL",
        "symbol": "BTCUSDT",
        "snapshotVersions": {
            key: snapshots[key]["datasetVersion"] for key in ("15m", "1h")
        },
    }
    bundle = {
        "schema_version": 1,
        "format": "T0_M15_H1_DATASET_BUNDLE_V1",
        "source": "T0_CANONICAL_BINANCE_USDT_PERPETUAL",
        "exchange": "binance", "marketType": "USDT_PERPETUAL",
        "symbol": "BTCUSDT", "snapshots": snapshots,
        "datasetVersion": "sha256:" + hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }
    return bundle


def bundle_bytes(bundle):
    return json.dumps(
        bundle, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


class AIProvenanceValidatorTests(unittest.TestCase):
    def setUp(self):
        self.private_key = Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        self.dataset_bundle = make_m15_h1_bundle()
        self.dataset_version = self.dataset_bundle["datasetVersion"]
        self.artifacts = {role: (f"synthetic-{role}-bytes").encode() for role in ROLES}
        self.artifacts["dataset"] = bundle_bytes(self.dataset_bundle)
        prediction_rows = []
        observations = []
        for index in range(1000):
            timestamp = 1_700_003_700_100 + index * 1000
            outcome = (index // 2) % 2
            side = "LONG" if index % 2 == 0 else "SHORT"
            confidence = "0.975" if outcome else "0.025"
            row = {
                "prediction_timestamp_ms": timestamp,
                "outcome_available_at_ms": timestamp + 500,
                "outcome": outcome,
                "confidence": confidence,
                "side": side,
                "regime": "TREND",
                "model_version": "model-sha-test-v1",
                "dataset_version": self.dataset_version,
                "feature_cutoffs": {
                    timeframe: {
                        "open_time_ms": candle["openTimeMs"],
                        "close_time_ms": candle["closeTimeMs"],
                        "available_at_ms": candle["availableAtMs"],
                    }
                    for timeframe in ("15m", "1h")
                    for candle in [max(
                        (item for item in self.dataset_bundle["snapshots"][timeframe]["candles"]
                         if item["availableAtMs"] <= timestamp),
                        key=lambda item: item["openTimeMs"],
                    )]
                },
            }
            prediction_rows.append(json.dumps(row, sort_keys=True, separators=(",", ":")))
            observations.append(CalibrationObservation(
                outcome=outcome, confidence=confidence, side=side,
                regime="TREND", out_of_sample=True,
            ))
        self.artifacts["predictions"] = ("\n".join(prediction_rows) + "\n").encode()
        policy = approved_calibration_gate_policy(ece_bins=10, required_regimes=("TREND",))
        evaluation = CalibrationEvaluator().evaluate(observations, policy)
        self.assertTrue(evaluation.accepted)
        policy_payload = {
            "max_ece": "0.05", "min_total_samples": 1000,
            "min_group_samples": 200, "ece_bins": 10,
            "required_regimes": ["TREND"],
        }
        report = {
            "schema_version": 1, "policy": policy_payload,
            "accepted": evaluation.accepted, "reasons": list(evaluation.reasons),
            "sample_count": evaluation.sample_count, "group_count": evaluation.group_count,
            "metrics": evaluation.metrics, "input_sha256": evaluation.input_sha256,
            "report_sha256": evaluation.report_sha256,
            "trade_authorized": False, "attestation_issued": False,
        }
        self.artifacts["calibration_report"] = json.dumps(
            report, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
        self.now_ms = 1_800_000_000_000
        self.manifest = {
            "schema_version": 1,
            "key_id": "offline-test-root-1",
            "model_version": "model-sha-test-v1",
            "strategy_version": "dual-ai-v1",
            "dataset_version": self.dataset_version,
            "issued_at_ms": self.now_ms - 1000,
            "expires_at_ms": self.now_ms + 60_000,
            "temporal_split": {
                "train_end_ms": 1_700_000_000_000,
                "oos_start_ms": 1_700_000_000_001,
                "oos_end_ms": 1_710_000_000_000,
            },
            "artifacts": {
                role: {
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "size_bytes": len(data),
                }
                for role, data in self.artifacts.items()
            },
        }

    def signed_envelope(self, manifest=None):
        manifest = self.manifest if manifest is None else manifest
        canonical = json.dumps(
            manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode()
        return {
            "manifest": manifest,
            "signature": base64.b64encode(self.private_key.sign(canonical)).decode(),
        }

    def verify(self, envelope=None, artifacts=None, keys=None, now_ms=None):
        return verify_signed_provenance(
            self.signed_envelope() if envelope is None else envelope,
            self.artifacts if artifacts is None else artifacts,
            {"offline-test-root-1": self.public_key} if keys is None else keys,
            now_ms=self.now_ms if now_ms is None else now_ms,
        )

    def test_valid_signature_hashes_and_temporal_split_are_accepted(self):
        result = self.verify()
        self.assertTrue(result.accepted)
        self.assertEqual(result.reasons, ())
        self.assertEqual(set(result.verified_artifacts), set(ROLES))
        self.assertEqual(len(result.manifest_sha256), 64)
        self.assertFalse(result.attestation_issued)

    def test_rejects_unknown_signing_key(self):
        result = self.verify(keys={})
        self.assertFalse(result.accepted)
        self.assertIn("SIGNING_KEY_UNTRUSTED", result.reasons)

    def test_rejects_tampered_manifest_signature(self):
        envelope = self.signed_envelope()
        envelope["manifest"]["strategy_version"] = "tampered"
        result = self.verify(envelope=envelope)
        self.assertFalse(result.accepted)
        self.assertIn("SIGNATURE_INVALID", result.reasons)

    def test_rejects_tampered_artifact_bytes(self):
        artifacts = dict(self.artifacts)
        artifacts["model"] = b"X" + artifacts["model"][1:]
        result = self.verify(artifacts=artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("ARTIFACT_HASH_MISMATCH:model", result.reasons)

    def test_rejects_missing_artifact(self):
        artifacts = dict(self.artifacts)
        del artifacts["predictions"]
        result = self.verify(artifacts=artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("ARTIFACT_MISSING:predictions", result.reasons)

    def test_rejects_extra_artifact_role(self):
        artifacts = dict(self.artifacts, credentials=b"must-not-be-accepted")
        result = self.verify(artifacts=artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("ARTIFACT_ROLE_SET_MISMATCH", result.reasons)

    def test_rejects_artifact_size_mismatch(self):
        manifest = json.loads(json.dumps(self.manifest))
        manifest["artifacts"]["dataset"]["size_bytes"] += 1
        result = self.verify(envelope=self.signed_envelope(manifest))
        self.assertFalse(result.accepted)
        self.assertIn("ARTIFACT_SIZE_MISMATCH:dataset", result.reasons)

    def test_rejects_training_window_overlapping_oos(self):
        manifest = json.loads(json.dumps(self.manifest))
        manifest["temporal_split"]["train_end_ms"] = manifest["temporal_split"]["oos_start_ms"]
        result = self.verify(envelope=self.signed_envelope(manifest))
        self.assertFalse(result.accepted)
        self.assertIn("TEMPORAL_SPLIT_INVALID", result.reasons)

    def test_rejects_invalid_oos_window(self):
        manifest = json.loads(json.dumps(self.manifest))
        manifest["temporal_split"]["oos_end_ms"] = manifest["temporal_split"]["oos_start_ms"] - 1
        result = self.verify(envelope=self.signed_envelope(manifest))
        self.assertFalse(result.accepted)
        self.assertIn("TEMPORAL_SPLIT_INVALID", result.reasons)

    def test_rejects_expired_manifest(self):
        result = self.verify(now_ms=self.manifest["expires_at_ms"])
        self.assertFalse(result.accepted)
        self.assertIn("MANIFEST_EXPIRED", result.reasons)

    def test_rejects_manifest_issued_in_the_future(self):
        result = self.verify(now_ms=self.manifest["issued_at_ms"] - 1)
        self.assertFalse(result.accepted)
        self.assertIn("MANIFEST_TIME_INVALID", result.reasons)

    def test_rejects_duplicate_json_keys(self):
        raw = b'{"manifest":{"schema_version":1,"schema_version":1},"signature":"AA=="}'
        result = self.verify(envelope=raw)
        self.assertFalse(result.accepted)
        self.assertIn("ENVELOPE_INVALID", result.reasons)

    def test_rejects_noncanonical_unknown_manifest_fields(self):
        manifest = dict(self.manifest, caller_says_oos=True)
        result = self.verify(envelope=self.signed_envelope(manifest))
        self.assertFalse(result.accepted)
        self.assertIn("MANIFEST_SCHEMA_INVALID", result.reasons)

    def test_rejects_invalid_signature_encoding(self):
        envelope = self.signed_envelope()
        envelope["signature"] = "not-base64!"
        result = self.verify(envelope=envelope)
        self.assertFalse(result.accepted)
        self.assertIn("SIGNATURE_ENCODING_INVALID", result.reasons)



    def verify_rehashed_predictions(self, artifacts):
        manifest = json.loads(json.dumps(self.manifest))
        for role, data in artifacts.items():
            manifest["artifacts"][role] = {
                "sha256": hashlib.sha256(data).hexdigest(),
                "size_bytes": len(data),
            }
        return self.verify(envelope=self.signed_envelope(manifest), artifacts=artifacts)

    def test_rejects_prediction_timestamp_before_oos_window(self):
        artifacts = dict(self.artifacts)
        artifacts["predictions"] = artifacts["predictions"].replace(
            b'"prediction_timestamp_ms":1700000000100',
            b'"prediction_timestamp_ms":1699999999000',
        )
        result = self.verify_rehashed_predictions(artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("PREDICTION_TIMESTAMP_OUTSIDE_OOS", result.reasons)

    def test_rejects_prediction_timestamp_after_oos_window(self):
        artifacts = dict(self.artifacts)
        artifacts["predictions"] = artifacts["predictions"].replace(
            b'"prediction_timestamp_ms":1700000000100',
            b'"prediction_timestamp_ms":1710000000001',
        )
        result = self.verify_rehashed_predictions(artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("PREDICTION_TIMESTAMP_OUTSIDE_OOS", result.reasons)

    def test_rejects_outcome_available_before_prediction(self):
        artifacts = dict(self.artifacts)
        artifacts["predictions"] = artifacts["predictions"].replace(
            b'"outcome_available_at_ms":1700000000600',
            b'"outcome_available_at_ms":1700000000000',
        )
        result = self.verify_rehashed_predictions(artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("OUTCOME_TIMESTAMP_INVALID", result.reasons)

    def test_rejects_outcome_available_after_oos_window(self):
        artifacts = dict(self.artifacts)
        artifacts["predictions"] = artifacts["predictions"].replace(
            b'"outcome_available_at_ms":1700000000600',
            b'"outcome_available_at_ms":1710000000001',
        )
        result = self.verify_rehashed_predictions(artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("OUTCOME_TIMESTAMP_INVALID", result.reasons)

    def test_rejects_prediction_model_version_mismatch(self):
        artifacts = dict(self.artifacts)
        artifacts["predictions"] = artifacts["predictions"].replace(
            b'"model_version":"model-sha-test-v1"',
            b'"model_version":"different-model"',
        )
        result = self.verify_rehashed_predictions(artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("PREDICTION_MODEL_VERSION_MISMATCH", result.reasons)

    def test_rejects_prediction_dataset_version_mismatch(self):
        artifacts = dict(self.artifacts)
        artifacts["predictions"] = artifacts["predictions"].replace(
            f'"dataset_version":"{self.dataset_version}"'.encode(),
            b'"dataset_version":"different-dataset"',
        )
        result = self.verify_rehashed_predictions(artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("PREDICTION_DATASET_VERSION_MISMATCH", result.reasons)

    def test_rejects_empty_predictions_artifact(self):
        artifacts = dict(self.artifacts)
        artifacts["predictions"] = b""
        result = self.verify_rehashed_predictions(artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("PREDICTIONS_EMPTY", result.reasons)

    def test_rejects_malformed_prediction_jsonl(self):
        artifacts = dict(self.artifacts)
        artifacts["predictions"] = b'{"prediction_timestamp_ms":'
        result = self.verify_rehashed_predictions(artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("PREDICTION_ROW_INVALID", result.reasons)


    def test_rejects_prediction_rows_when_signed_split_is_malformed(self):
        manifest = json.loads(json.dumps(self.manifest))
        manifest["temporal_split"] = {"train_end_ms": 1_700_000_000_000}
        result = self.verify(envelope=self.signed_envelope(manifest))
        self.assertFalse(result.accepted)
        self.assertIn("TEMPORAL_SPLIT_INVALID", result.reasons)




    def test_rejects_dataset_bundle_version_not_bound_to_manifest(self):
        manifest = json.loads(json.dumps(self.manifest))
        manifest["dataset_version"] = "sha256:" + "f" * 64
        artifacts = dict(self.artifacts)
        rows = artifacts["predictions"].decode().splitlines()
        for index, line in enumerate(rows):
            row = json.loads(line)
            row["dataset_version"] = manifest["dataset_version"]
            rows[index] = json.dumps(row, sort_keys=True, separators=(",", ":"))
        artifacts["predictions"] = ("\n".join(rows) + "\n").encode()
        for role, data in artifacts.items():
            manifest["artifacts"][role] = {
                "sha256": hashlib.sha256(data).hexdigest(),
                "size_bytes": len(data),
            }
        result = self.verify(
            envelope=self.signed_envelope(manifest), artifacts=artifacts
        )
        self.assertFalse(result.accepted)
        self.assertIn("DATASET_MANIFEST_VERSION_MISMATCH", result.reasons)

    def test_rejects_duplicate_json_keys_in_dataset_bundle(self):
        artifacts = dict(self.artifacts)
        artifacts["dataset"] = b'{"schema_version":1,"schema_version":1}'
        result = self.verify_rehashed_predictions(artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("DATASET_BUNDLE_INVALID", result.reasons)

    def test_rejects_dataset_bundle_missing_h1_snapshot(self):
        bundle = json.loads(self.artifacts["dataset"])
        del bundle["snapshots"]["1h"]
        artifacts = dict(self.artifacts, dataset=bundle_bytes(bundle))
        result = self.verify_rehashed_predictions(artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("DATASET_BUNDLE_SCHEMA_INVALID", result.reasons)

    def test_rejects_dataset_bundle_with_snapshot_under_wrong_timeframe(self):
        bundle = json.loads(self.artifacts["dataset"])
        bundle["snapshots"]["1h"] = bundle["snapshots"]["15m"]
        artifacts = dict(self.artifacts, dataset=bundle_bytes(bundle))
        result = self.verify_rehashed_predictions(artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("DATASET_SNAPSHOT_INVALID:1h", result.reasons)

    def test_rejects_dataset_bundle_with_tampered_aggregate_fingerprint(self):
        bundle = json.loads(self.artifacts["dataset"])
        bundle["datasetVersion"] = "sha256:" + "0" * 64
        artifacts = dict(self.artifacts, dataset=bundle_bytes(bundle))
        result = self.verify_rehashed_predictions(artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("DATASET_BUNDLE_VERSION_MISMATCH", result.reasons)

    def test_rejects_prediction_timestamp_outside_both_timeframe_coverage(self):
        artifacts = dict(self.artifacts)
        rows = artifacts["predictions"].decode().splitlines()
        row = json.loads(rows[0])
        h1_end = self.dataset_bundle["snapshots"]["1h"]["endMs"]
        row["prediction_timestamp_ms"] = h1_end + 1000
        row["outcome_available_at_ms"] = h1_end + 1500
        rows[0] = json.dumps(row, sort_keys=True, separators=(",", ":"))
        artifacts["predictions"] = ("\n".join(rows) + "\n").encode()
        result = self.verify_rehashed_predictions(artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("PREDICTION_OUTSIDE_DATASET_COVERAGE", result.reasons)

    def test_rejects_outcome_resolution_after_m15_dataset_coverage(self):
        artifacts = dict(self.artifacts)
        rows = artifacts["predictions"].decode().splitlines()
        row = json.loads(rows[0])
        row["outcome_available_at_ms"] = self.dataset_bundle["snapshots"]["15m"]["endMs"] + 1
        rows[0] = json.dumps(row, sort_keys=True, separators=(",", ":"))
        artifacts["predictions"] = ("\n".join(rows) + "\n").encode()
        result = self.verify_rehashed_predictions(artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("OUTCOME_OUTSIDE_M15_DATASET_COVERAGE", result.reasons)


    def _prediction_with_feature_cutoffs(self, *, m15_available_offset=0, h1_available_offset=0):
        artifacts = dict(self.artifacts)
        rows = artifacts["predictions"].decode().splitlines()
        row = json.loads(rows[0])
        timestamp = row["prediction_timestamp_ms"]
        cutoffs = {}
        for timeframe, offset in (("15m", m15_available_offset), ("1h", h1_available_offset)):
            candles = self.dataset_bundle["snapshots"][timeframe]["candles"]
            eligible = [c for c in candles if c["availableAtMs"] <= timestamp]
            candle = eligible[-1] if eligible else candles[0]
            cutoffs[timeframe] = {
                "open_time_ms": candle["openTimeMs"],
                "close_time_ms": candle["closeTimeMs"],
                "available_at_ms": candle["availableAtMs"] + offset,
            }
        row["feature_cutoffs"] = cutoffs
        rows[0] = json.dumps(row, sort_keys=True, separators=(",", ":"))
        artifacts["predictions"] = ("\n".join(rows) + "\n").encode()
        return artifacts

    def test_rejects_prediction_without_declared_m15_h1_feature_cutoffs(self):
        artifacts = dict(self.artifacts)
        result = self.verify_rehashed_predictions(artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("FEATURE_CUTOFFS_INVALID", result.reasons)

    def test_rejects_feature_candle_available_after_prediction_decision(self):
        artifacts = self._prediction_with_feature_cutoffs(m15_available_offset=1)
        result = self.verify_rehashed_predictions(artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("FEATURE_CANDLE_NOT_AVAILABLE_AT_DECISION:15m", result.reasons)

    def test_rejects_feature_cutoff_that_does_not_match_dataset_candle(self):
        artifacts = self._prediction_with_feature_cutoffs()
        rows = artifacts["predictions"].decode().splitlines()
        row = json.loads(rows[0])
        row["feature_cutoffs"]["1h"]["open_time_ms"] += 3_600_000
        rows[0] = json.dumps(row, sort_keys=True, separators=(",", ":"))
        artifacts["predictions"] = ("\n".join(rows) + "\n").encode()
        result = self.verify_rehashed_predictions(artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("FEATURE_CANDLE_REFERENCE_INVALID:1h", result.reasons)

    def test_rejects_calibration_report_with_wrong_input_fingerprint(self):
        artifacts = dict(self.artifacts)
        report = json.loads(artifacts["calibration_report"])
        report["input_sha256"] = "0" * 64
        artifacts["calibration_report"] = json.dumps(
            report, sort_keys=True, separators=(",", ":")
        ).encode()
        result = self.verify_rehashed_predictions(artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("CALIBRATION_REPORT_MISMATCH", result.reasons)

    def test_rejects_calibration_report_with_wrong_report_digest(self):
        artifacts = dict(self.artifacts)
        report = json.loads(artifacts["calibration_report"])
        report["report_sha256"] = "0" * 64
        artifacts["calibration_report"] = json.dumps(
            report, sort_keys=True, separators=(",", ":")
        ).encode()
        result = self.verify_rehashed_predictions(artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("CALIBRATION_REPORT_MISMATCH", result.reasons)

    def test_rejects_calibration_report_that_weakens_approved_policy(self):
        artifacts = dict(self.artifacts)
        report = json.loads(artifacts["calibration_report"])
        report["policy"]["max_ece"] = "0.10"
        artifacts["calibration_report"] = json.dumps(
            report, sort_keys=True, separators=(",", ":")
        ).encode()
        result = self.verify_rehashed_predictions(artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("CALIBRATION_POLICY_NOT_APPROVED", result.reasons)

    def test_rejects_calibration_report_metrics_not_recomputed_from_predictions(self):
        artifacts = dict(self.artifacts)
        report = json.loads(artifacts["calibration_report"])
        report["metrics"]["overall"]["ece"] = 0.0
        artifacts["calibration_report"] = json.dumps(
            report, sort_keys=True, separators=(",", ":")
        ).encode()
        result = self.verify_rehashed_predictions(artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("CALIBRATION_REPORT_MISMATCH", result.reasons)

    def test_rejects_malformed_calibration_report(self):
        artifacts = dict(self.artifacts)
        artifacts["calibration_report"] = b'{"schema_version":'
        result = self.verify_rehashed_predictions(artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("CALIBRATION_REPORT_INVALID", result.reasons)

if __name__ == "__main__":
    unittest.main()
