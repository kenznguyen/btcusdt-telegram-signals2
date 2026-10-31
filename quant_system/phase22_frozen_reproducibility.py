"""Phase22: verify Git-preserved frozen model bytes and provenance.

This gate never trains, tunes, reads holdout market rows, or unpickles a model.
The subsequent Phase14 audit performs the already-approved historical replay
and is responsible for hash-before-joblib-load enforcement.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

REGISTERED_BUNDLE_SHA = (
    "sha256:918dc4737ee432df8f7f9d2c3e561ac3983aaf56d8791a731a55624ab836b81f"
)
REGISTERED_METADATA_SHA = (
    "sha256:07e9c1b65df7a477de8ee14c51d47325932e6bf9a0732f3ea64e3118abcac3e5"
)
REGISTERED_PROTOCOL_SHA = (
    "sha256:b10d63c952a40fa70a3d4dfed2d952d676a888a0f72832734d3ff8d8c14c5b6e"
)
REGISTERED_SOURCE_COMMIT = "082edc082996425f61f48c952be41fb037564103"
REGISTERED_ATTESTATION_COMMIT = "f9591bcda1b11f15a549f397aa211259346ed3f9"
REGISTERED_FEATURE_COUNT = 20
HOLDOUT_START_UTC = "2026-11-04T00:00:00Z"
HOLDOUT_END_UTC = "2026-12-04T00:00:00Z"


class FrozenReproducibilityError(ValueError):
    """Raised when the preserved model or its provenance is not exact."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise FrozenReproducibilityError(code)


def _digest(path: Path) -> str:
    _require(path.is_file() and not path.is_symlink(),
             "PHASE22_REQUIRED_FILE_MISSING_OR_UNSAFE")
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _json_object(path: Path, code: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FrozenReproducibilityError(code) from exc
    _require(isinstance(value, dict), code)
    return value


def _utc_ms(value: str) -> int:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        _require(parsed.tzinfo is not None, "PHASE22_INVALID_HOLDOUT_TIMESTAMP")
        return int(parsed.astimezone(timezone.utc).timestamp() * 1000)
    except (TypeError, ValueError, OverflowError) as exc:
        if isinstance(exc, FrozenReproducibilityError):
            raise
        raise FrozenReproducibilityError(
            "PHASE22_INVALID_HOLDOUT_TIMESTAMP"
        ) from exc


def verify_preserved_snapshot(bundle, original_bundle, metadata, protocol, seal,
                              attestation=None, github_commit_proof=None):
    """Verify byte identity with Phase14 source and immutable pre-holdout seal.

    All paths are read-only. No pickle/joblib loader is imported or called.
    """
    bundle, original_bundle, metadata, protocol, seal = map(
        Path, (bundle, original_bundle, metadata, protocol, seal)
    )
    bundle_sha = _digest(bundle)
    original_sha = _digest(original_bundle)
    metadata_sha = _digest(metadata)
    protocol_sha = _digest(protocol)

    _require(bundle_sha == REGISTERED_BUNDLE_SHA,
             "PHASE22_BUNDLE_SHA_MISMATCH")
    _require(original_sha == REGISTERED_BUNDLE_SHA and
             bundle.read_bytes() == original_bundle.read_bytes(),
             "PHASE22_ORIGINAL_BYTES_MISMATCH")
    _require(metadata_sha == REGISTERED_METADATA_SHA,
             "PHASE22_METADATA_SHA_MISMATCH")
    _require(protocol_sha == REGISTERED_PROTOCOL_SHA,
             "PHASE22_PROTOCOL_SHA_MISMATCH")

    candidate = _json_object(metadata, "PHASE22_INVALID_METADATA")
    registered_protocol = _json_object(protocol, "PHASE22_INVALID_PROTOCOL")
    declaration = _json_object(seal, "PHASE22_INVALID_SEAL")

    _require(declaration.get("type") == "PHASE13B_PRE_HOLDOUT_SHA256_SEAL" and
             candidate.get("schemaVersion") == 1 and
             candidate.get("candidate_sha256") == bundle_sha and
             candidate.get("model_sha256") == declaration.get("model_booster_sha256") and
             declaration.get("candidate_bundle_sha256") == bundle_sha and
             declaration.get("candidate_metadata_sha256") == metadata_sha and
             declaration.get("protocol_sha256") == protocol_sha,
             "PHASE22_SEAL_DIGEST_MISMATCH")

    source = candidate.get("source_commit_sha")
    model_id = candidate.get("model_identifier")
    feature_columns = candidate.get("ordered_feature_columns")
    training_end = candidate.get("training_end_ms")
    _require(source == REGISTERED_SOURCE_COMMIT and
             source == declaration.get("source_commit_sha"),
             "PHASE22_SOURCE_COMMIT_MISMATCH")
    _require(isinstance(model_id, str) and model_id and
             model_id == declaration.get("model_identifier") ==
             registered_protocol.get("model_identifier"),
             "PHASE22_MODEL_IDENTITY_MISMATCH")
    _require(isinstance(feature_columns, list) and
             len(feature_columns) == REGISTERED_FEATURE_COUNT and
             len(set(feature_columns)) == REGISTERED_FEATURE_COUNT and
             all(isinstance(name, str) and name for name in feature_columns) and
             declaration.get("feature_column_count") == REGISTERED_FEATURE_COUNT,
             "PHASE22_INVALID_FEATURE_SCHEMA")
    _require(isinstance(training_end, int) and
             training_end == declaration.get("training_end_ms") and
             training_end < _utc_ms(HOLDOUT_START_UTC) and
             candidate.get("latest_observed_label_end_ms", 0) <
             _utc_ms(HOLDOUT_START_UTC),
             "PHASE22_TRAINING_WINDOW_CROSSES_HOLDOUT")

    _require(registered_protocol.get("protocol") ==
             "PHASE13B_PROSPECTIVE_FROZEN_MODEL_OOS" and
             registered_protocol.get("holdout_start_utc") == HOLDOUT_START_UTC ==
             declaration.get("holdout_start_utc") and
             registered_protocol.get("holdout_end_utc") == HOLDOUT_END_UTC ==
             declaration.get("holdout_end_utc") and
             registered_protocol.get("holdout_days") == 30,
             "PHASE22_HOLDOUT_PROTOCOL_MISMATCH")

    policy = registered_protocol.get("frozen_model_policy", {})
    data = registered_protocol.get("data", {})
    evaluation = registered_protocol.get("evaluation", {})
    certification = registered_protocol.get("certification", {})
    _require(policy.get("retrain_inside_holdout") is False and
             policy.get("tune_parameters_using_holdout") is False and
             policy.get("change_strategy_or_features_after_seal") is False and
             policy.get("reuse_existing_trained_model_with_fitted_datasieve_and_label_pipeline") is True and
             policy.get("all_training_labels_end_before_holdout_start") is True and
             policy.get("freeze_all_feature_scalers_and_outlier_transformers") is True and
             data.get("only_closed_candles") is True and
             data.get("exact_holdout_15m_rows") == 2880 and
             data.get("no_backfill_of_missing_holdout_candles") is True and
             data.get("no_use_of_holdout_rows_for_training_or_scalers") is True and
             evaluation.get("no_real_orders") is True and
             evaluation.get("automatic_promotion_allowed") is False and
             declaration.get("holdout_retraining_allowed") is False and
             declaration.get("holdout_tuning_allowed") is False,
             "PHASE22_HOLDOUT_POLICY_MISMATCH")

    safety_flags = (
        declaration.get("independent_oos_verified"),
        declaration.get("oos_certified"),
        declaration.get("ai_promotion_eligible"),
        declaration.get("live_orders_enabled"),
        certification.get("independent_oos_verified"),
        certification.get("oos_certified"),
        certification.get("ai_promotion_eligible"),
        certification.get("live_orders_enabled"),
        candidate.get("oos_certified"),
    )
    _require(all(flag is False for flag in safety_flags),
             "PHASE22_UNSAFE_SEAL")

    return {
        "schemaVersion": 1,
        "audit": "PHASE22_GIT_PRESERVED_FROZEN_MODEL_REPRODUCIBILITY",
        "exact_original_bundle_bytes_verified": True,
        "candidate_bundle_sha256": bundle_sha,
        "candidate_metadata_sha256": metadata_sha,
        "protocol_sha256": protocol_sha,
        "pre_holdout_attestation_verified": False,
        "source_commit_sha": source,
        "model_identifier": model_id,
        "training_end_ms": training_end,
        "feature_column_count": len(feature_columns),
        "holdout_start_utc": HOLDOUT_START_UTC,
        "holdout_end_utc": HOLDOUT_END_UTC,
        "historical_replay_delegated_to_phase14": True,
        "retrained": False,
        "holdout_rows_read": False,
        "independent_oos_verified": False,
        "oos_certified": False,
        "ai_promotion_eligible": False,
        "live_orders_enabled": False,
        "errors": [],
    }


def _verify_github_server_proof(proof_path, expected_path, error_code):
    proof = _json_object(Path(proof_path), error_code)
    server = proof.get("server_evidence", {})
    sha = proof.get("sha")
    created_at = server.get("created_at") if isinstance(server, dict) else None
    _require(
        proof.get("proof_source") == "github_actions_run"
        and isinstance(sha, str) and len(sha) == 40
        and all(char in "0123456789abcdef" for char in sha.lower())
        and isinstance(server, dict)
        and server.get("provider") == "GitHub Actions"
        and isinstance(server.get("run_id"), int) and server["run_id"] > 0
        and server.get("head_sha") == sha
        and isinstance(created_at, str)
        and any(isinstance(item, dict) and item.get("filename") == expected_path
                for item in proof.get("files", [])),
        error_code,
    )
    try:
        timestamp = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        _require(timestamp.tzinfo is not None, error_code)
    except (TypeError, ValueError) as exc:
        raise FrozenReproducibilityError(error_code) from exc
    _require(
        timestamp.astimezone(timezone.utc) <
        datetime.fromisoformat(HOLDOUT_START_UTC.replace("Z", "+00:00")),
        "PHASE22_ATTESTATION_NOT_PRE_HOLDOUT",
    )
    return proof, created_at


def verify_oos_eligibility(bundle, original_bundle, metadata,
                           historical_protocol, historical_seal,
                           oos_protocol, attestation,
                           attestation_commit_proof,
                           oos_protocol_commit_proof):
    """Check a separately sealed OOS protocol without rewriting history.

    The historical protocol and historical seal are verified byte-for-byte by
    verify_preserved_snapshot. The prospective OOS protocol has its own hash,
    attestation, Git commit and GitHub Actions server-time evidence.
    """
    historical = verify_preserved_snapshot(
        bundle, original_bundle, metadata, historical_protocol, historical_seal
    )
    oos_path = Path(oos_protocol)
    oos = _json_object(oos_path, "PHASE22_INVALID_OOS_PROTOCOL")
    oos_sha = _digest(oos_path)
    _require(oos.get("protocol") == "PHASE13B_PROSPECTIVE_FROZEN_MODEL_OOS"
             and oos.get("status") == "SEALED_BY_EXTERNAL_ATTESTATION",
             "PHASE22_PROTOCOL_NOT_SEALED")
    hashes = (
        oos.get("source_commit_sha"),
        oos.get("frozen_model_bundle_sha256"),
        oos.get("frozen_model_metadata_sha256"),
    )
    _require(all(isinstance(value, str) and value.strip() for value in hashes),
             "PHASE22_PROTOCOL_PROVENANCE_MISSING")
    _require(hashes == (
        REGISTERED_SOURCE_COMMIT,
        REGISTERED_BUNDLE_SHA.removeprefix("sha256:"),
        REGISTERED_METADATA_SHA.removeprefix("sha256:"),
    ), "PHASE22_PROTOCOL_PROVENANCE_MISMATCH")
    policy = oos.get("frozen_model_policy", {})
    data = oos.get("data", {})
    evaluation = oos.get("evaluation", {})
    certification = oos.get("certification", {})
    _require(
        oos.get("holdout_start_utc") == HOLDOUT_START_UTC
        and oos.get("holdout_end_utc") == HOLDOUT_END_UTC
        and oos.get("holdout_days") == 30
        and policy.get("retrain_inside_holdout") is False
        and policy.get("tune_parameters_using_holdout") is False
        and policy.get("change_strategy_or_features_after_seal") is False
        and policy.get("all_training_labels_end_before_holdout_start") is True
        and policy.get("freeze_all_feature_scalers_and_outlier_transformers") is True
        and data.get("only_closed_candles") is True
        and data.get("exact_holdout_15m_rows") == 2880
        and data.get("no_backfill_of_missing_holdout_candles") is True
        and data.get("no_use_of_holdout_rows_for_training_or_scalers") is True
        and evaluation.get("no_real_orders") is True
        and evaluation.get("automatic_promotion_allowed") is False
        and all(certification.get(flag) is False for flag in (
            "independent_oos_verified", "oos_certified",
            "ai_promotion_eligible", "ready_for_360", "live_orders_enabled")),
        "PHASE22_OOS_PROTOCOL_POLICY_MISMATCH",
    )
    _require(oos.get("sealed_in_git") is True
             and isinstance(oos.get("seal_git_commit"), str)
             and len(oos["seal_git_commit"]) == 40,
             "PHASE22_PROTOCOL_COMMIT_EVIDENCE_MISSING")
    oos_commit_path = (
        "research_evidence/frozen-model/phase13b-20261104/oos-protocol.json"
    )
    oos_proof, oos_created_at = _verify_github_server_proof(
        oos_protocol_commit_proof, oos_commit_path,
        "PHASE22_OOS_PROTOCOL_SERVER_PROOF_MISSING",
    )
    _require(oos_proof["sha"] == oos["seal_git_commit"],
             "PHASE22_OOS_PROTOCOL_COMMIT_MISMATCH")

    attested = _json_object(Path(attestation), "PHASE22_INVALID_ATTESTATION")
    expected_attestation_path = (
        "research_evidence/frozen-model/phase13b-20261104/pre-holdout-attestation.json"
    )
    attestation_proof, attestation_created_at = _verify_github_server_proof(
        attestation_commit_proof, expected_attestation_path,
        "PHASE22_GITHUB_COMMIT_PROOF_MISSING",
    )
    _require(attestation_proof.get("sha") == REGISTERED_ATTESTATION_COMMIT,
             "PHASE22_GITHUB_COMMIT_PROOF_MISSING")
    _require(
        attested.get("attestation_type") ==
            "PHASE13B_PRE_HOLDOUT_EXTERNAL_ATTESTATION"
        and attested.get("source_commit_sha") == REGISTERED_SOURCE_COMMIT
        and attested.get("model_bundle_sha256") ==
            REGISTERED_BUNDLE_SHA.removeprefix("sha256:")
        and attested.get("model_metadata_sha256") ==
            REGISTERED_METADATA_SHA.removeprefix("sha256:")
        and attested.get("historical_protocol_sha256") ==
            REGISTERED_PROTOCOL_SHA.removeprefix("sha256:")
        and attested.get("oos_protocol_sha256") ==
            oos_sha.removeprefix("sha256:")
        and attested.get("holdout_start_utc") == HOLDOUT_START_UTC
        and attested.get("holdout_end_utc") == HOLDOUT_END_UTC
        and attested.get("holdout_retraining_allowed") is False
        and attested.get("holdout_tuning_allowed") is False
        and attested.get("independent_oos_verified") is False
        and attested.get("oos_certified") is False
        and attested.get("ai_promotion_eligible") is False
        and attested.get("live_orders_enabled") is False,
        "PHASE22_ATTESTATION_PROVENANCE_MISMATCH",
    )
    result = dict(historical)
    result.update({
        "audit": "PHASE22_SEPARATE_OOS_PROTOCOL_ELIGIBILITY_GATE",
        "historical_protocol_unchanged": True,
        "historical_protocol_sha256": historical["protocol_sha256"],
        "oos_protocol_sha256": oos_sha,
        "oos_protocol_commit_sha": oos_proof["sha"],
        "oos_protocol_server_created_at_utc": oos_created_at,
        "attestation_commit_sha": attestation_proof["sha"],
        "attestation_server_created_at_utc": attestation_created_at,
        "pre_holdout_attestation_verified": True,
        "independent_oos_verified": False,
        "oos_certified": False,
        "ai_promotion_eligible": False,
        "live_orders_enabled": False,
    })
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--original-bundle", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--seal", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    report = verify_preserved_snapshot(
        args.bundle, args.original_bundle, args.metadata, args.protocol, args.seal
    )
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True),
                      encoding="utf8")
    print("PHASE22_EXACT_FROZEN_BUNDLE_REPRODUCIBILITY_VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
