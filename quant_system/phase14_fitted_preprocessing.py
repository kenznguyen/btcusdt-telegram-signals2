"""Phase14: offline causal interventions on an already FITTED FreqAI pipeline.

Fail-closed. Joblib may ONLY be loaded after matching the pre-holdout Git
seal's candidate SHA. This is a limited prefix-invariance test, not proof
of training-time fit causality or independent OOS.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from quant_system.phase13b_matrix import matrix_digest, read_matrix
from quant_system.phase13_feature_causality import canonical_frame, feature_matrix

M15_MS = 900000


class PipelineCausalityError(ValueError):
    pass


def require(ok, code):
    if not ok:
        raise PipelineCausalityError(code)


def verify_model_bundle_seal(bundle, metadata, protocol, seal):
    """Check exact candidate bytes against an already committed Git manifest.

    The caller separately verifies the Git commit timestamp and immutable
    commit identity BEFORE this routine is used. Never blindly trust a local
    self-declared manifest or unpickle before checking these hashes.
    """
    bundle, metadata, protocol, seal = map(
        Path, (bundle, metadata, protocol, seal))
    try:
        declaration = json.loads(seal.read_text(encoding="utf8"))
        candidate = json.loads(metadata.read_text(encoding="utf8"))
        registered_protocol = json.loads(protocol.read_text(encoding="utf8"))
        require(isinstance(declaration, dict) and
                isinstance(candidate, dict) and
                isinstance(registered_protocol, dict),
                "PHASE14_INVALID_SEAL_METADATA")
        require(bundle.is_file() and not bundle.is_symlink() and
                matrix_digest(bundle) == declaration.get("candidate_bundle_sha256") ==
                candidate.get("candidate_sha256"),
                "PHASE14_BUNDLE_SHA_MISMATCH")
        require(matrix_digest(metadata) ==
                declaration.get("candidate_metadata_sha256"),
                "PHASE14_METADATA_SHA_MISMATCH")
        require(matrix_digest(protocol) ==
                declaration.get("protocol_sha256"),
                "PHASE14_PROTOCOL_SHA_MISMATCH")
        require(candidate.get("source_commit_sha") ==
                declaration.get("source_commit_sha") and
                candidate.get("model_sha256") ==
                declaration.get("model_booster_sha256") and
                candidate.get("model_identifier") ==
                declaration.get("model_identifier") ==
                registered_protocol.get("model_identifier"),
                "PHASE14_SEAL_MODEL_IDENTITY_MISMATCH")
        require(registered_protocol.get("holdout_start_utc") ==
                declaration.get("holdout_start_utc") and
                registered_protocol.get("holdout_end_utc") ==
                declaration.get("holdout_end_utc") and
                candidate.get("training_end_ms") ==
                declaration.get("training_end_ms") and
                candidate.get("training_end_ms") <
                1793750400000,  # 2026-11-04T00:00:00Z
                "PHASE14_SEAL_TIMEBOUND_MISMATCH")
        require(declaration.get("live_orders_enabled") is False and
                declaration.get("independent_oos_verified") is False and
                declaration.get("oos_certified") is False,
                "PHASE14_UNSAFE_SEAL")
        return True
    except (OSError, UnicodeError, ValueError, TypeError, KeyError,
            OverflowError, json.JSONDecodeError) as exc:
        if isinstance(exc, PipelineCausalityError):
            raise
        raise PipelineCausalityError("PHASE14_INVALID_SEAL_METADATA") from exc


def _transform_fitted(feature_pipeline, raw):
    output = copy.deepcopy(feature_pipeline).transform(
        raw.reset_index(drop=True).copy(deep=True), outlier_check=True)
    require(isinstance(output, tuple) and len(output) == 3,
            "PHASE14_UNEXPECTED_DATASIEVE_TRANSFORM_RETURN")
    x, flags, _ = output
    require(isinstance(x, pd.DataFrame) and len(x) == len(raw) and
            len(flags) == len(raw),
            "PHASE14_FITTED_TRANSFORM_ROW_LOSS")
    return x, np.asarray(flags)


def _inverse_fitted(label_pipeline, samples):
    x = pd.DataFrame({"&-future_return": samples})
    output = copy.deepcopy(label_pipeline).inverse_transform(x)
    require(isinstance(output, tuple) and len(output) == 3 and
            isinstance(output[0], pd.DataFrame),
            "PHASE14_UNEXPECTED_DATASIEVE_LABEL_RETURN")
    return float(output[0].iloc[0, 0])


def verify_fitted_row_invariance(feature_pipeline, label_pipeline,
                                 row, future, native_x, native_flag):
    """One actual inference-row witness and adversarial FUTURE suffix.

    Independently cloned, ALREADY FITTED transforms must not learn
    from or read later inference rows. Compare exactly the model input
    and native reject/accept flag, not merely a DataFrame column list.
    """
    require(isinstance(row, pd.DataFrame) and len(row) == 1 and
            isinstance(future, pd.DataFrame) and len(future) >= 2 and
            list(row.columns) == list(future.columns),
            "PHASE14_INVALID_INTERVENTION_INPUT")
    require([name for name, _ in feature_pipeline.steps] ==
            ["const", "scaler", "di"] and
            [name for name, _ in label_pipeline.steps] == ["scaler"],
            "PHASE14_UNAPPROVED_FITTED_PIPELINE")
    one_x, one_flags = _transform_fitted(feature_pipeline, row)
    require(list(one_x.columns) == list(row.columns) and
            len(native_x) == len(one_x.columns),
            "PHASE14_FEATURE_SCHEMA_MISMATCH")
    one = one_x.iloc[0].to_numpy(dtype=np.float64)
    expected = np.asarray(native_x, dtype=np.float64)
    require(bool(np.isfinite(one).all()) and
            bool(np.isfinite(expected).all()) and
            bool(np.allclose(one, expected, rtol=1e-9, atol=1e-10)),
            "PHASE14_FITTED_X_NATIVE_MISMATCH")
    require(int(one_flags[0]) == int(native_flag),
            "PHASE14_FITTED_NATIVE_FLAG_MISMATCH")
    # Disturb every future feature with values far outside the fitted
    # training range while preserving the audited current candle.
    disturbed = future.copy(deep=True).reset_index(drop=True)
    for index, column in enumerate(disturbed.columns):
        disturbed[column] = (disturbed[column].astype(float) +
                             10000.0 + 101.0 * (index + 1))
    amended = pd.concat([row.reset_index(drop=True), disturbed],
                        ignore_index=True)
    altered_x, altered_flags = _transform_fitted(feature_pipeline, amended)
    require(list(altered_x.columns) == list(one_x.columns) and
            np.allclose(one, altered_x.iloc[0].to_numpy(dtype=float),
                        rtol=1e-9, atol=1e-10) and
            int(altered_flags[0]) == int(one_flags[0]),
            "PHASE14_FUTURE_DEPENDENT_FEATURE_PIPELINE")
    # The fitted label scaler must also be row-independent. Never refit
    # it using the unseen holdout or this deliberately altered suffix.
    original_y = _inverse_fitted(label_pipeline, [0.123])
    changed_y = _inverse_fitted(label_pipeline, [0.123, 5000.0])
    require(math.isfinite(original_y) and math.isfinite(changed_y) and
            math.isclose(original_y, changed_y, rel_tol=1e-10, abs_tol=1e-10),
            "PHASE14_FUTURE_DEPENDENT_LABEL_PIPELINE")
    return {"feature_comparisons": 2, "label_comparisons": 1}


def inspect_frozen_candidate(artifacts_root, bundle, metadata,
                             protocol, seal):
    """Reproduce actual last-fold LightGBM X using a frozen fitted pipeline.

    All inputs must be from SAME historical run as the sealed candidate.
    No fresh FreqAI rolling train, no new order signals, no OOS assertions.
    """
    report = dict(schemaVersion=1,
        audit="PHASE14_FROZEN_FITTED_DATASIEVE_INTERVENTIONS",
        fitted_preprocessing_prefix_invariance_verified=False,
        full_model_pipeline_causality_verified=False,
        independent_oos_verified=False, oos_certified=False,
        ai_promotion_eligible=False, ready_for_360=False,
        full_core_parity_certified=False, live_orders_enabled=False,
        errors=[], blockers=[
            "TRAINING_TIME_PIPELINE_FIT_PREFIX_CAUSALITY_NOT_CERTIFIED",
            "PROSPECTIVE_FROZEN_INFERENCE_NOT_EVALUATED",
            "VENUE_FUNDING_LIQUIDATION_AND_KOTLIN_PARITY_PENDING"])
    try:
        root = Path(artifacts_root)
        require(verify_model_bundle_seal(bundle, metadata, protocol, seal),
                "PHASE14_SEAL_NOT_VERIFIED")
        meta = json.loads(Path(metadata).read_text(encoding="utf8"))
        phase13b = json.loads((root / "paper/phase13b-native-matrix-audit.json").read_text())
        native = json.loads((root / "native/native-research-180.json").read_text())
        require(phase13b.get("actual_fit_predict_matrices_verified") is True and
                phase13b.get("errors") == [] and
                native.get("phase13b_candidate_sha256") ==
                meta.get("candidate_sha256") and
                native.get("phase13b_candidate_metadata_sha256") ==
                matrix_digest(metadata),
                "PHASE14_PHASE13B_EVIDENCE_MISMATCH")
        # Unpickle ONLY after the independently committed SHA is checked.
        import joblib
        from quant_system.phase8_model_evidence import booster_sha256
        payload = joblib.load(bundle)
        require(isinstance(payload, dict) and
                payload.get("source_commit_sha") == meta["source_commit_sha"] and
                payload.get("model_sha256") == meta["model_sha256"] and
                payload.get("training_end_ms") == meta["training_end_ms"] and
                payload.get("ordered_features") ==
                meta["ordered_feature_columns"] and
                booster_sha256(payload["model"]) == meta["model_sha256"],
                "PHASE14_LOADED_MODEL_NOT_SEALED")
        feature_pipe = payload["feature_pipeline"]
        label_pipe = payload["label_pipeline"]
        events_path = root / "native/phase13b-native-matrix-events.jsonl"
        require(matrix_digest(events_path) ==
                native.get("phase13b_matrix_events_sha256"),
                "PHASE14_MATRIX_LEDGER_SHA_MISMATCH")
        matching = []
        for line in events_path.read_text(encoding="utf8").splitlines():
            event = json.loads(line)
            if event["stage"] == "PREDICT" and \
               event["fold_model_name"] == meta["fold_model_name"] and \
               event["model_sha256"] == meta["model_sha256"]:
                matching.append(read_matrix(root / "native", event))
        require(bool(matching), "PHASE14_SEALED_MODEL_MISSING_PREDICT_MATRIX")
        stamps, feature_rows, native_flags = [], [], []
        for block in matching:
            require(block["columns"] == meta["ordered_feature_columns"],
                    "PHASE14_SEALED_MATRIX_SCHEMA_MISMATCH")
            stamps.extend(block["timestamps"])
            feature_rows.extend(block["values"].tolist())
            native_flags.extend(block["flags"])
        require(len(stamps) >= 64 and len(stamps) == len(set(stamps)) and
                all(a < b for a, b in zip(stamps, stamps[1:])),
                "PHASE14_INVALID_SEALED_MODEL_TIMESTAMPS")
        from freqai_bridge.ChartProFreqaiResearch import ChartProFreqaiResearch
        closed = canonical_frame(root / "canonical/15m.csv")
        base = feature_matrix(closed, ChartProFreqaiResearch)
        mapped = {c: (c if c in ("%-day-of-week", "%-hour-of-day")
                       else c + "_BTC/USDTUSDT_15m") for c in base.columns}
        base = base.rename(columns=mapped)
        require(set(base.columns) == set(meta["ordered_feature_columns"]),
                "PHASE14_UNAPPROVED_SOURCE_FEATURE_SCHEMA")
        base = base.loc[:, meta["ordered_feature_columns"]]
        opened = list(closed["open_time"].astype(int))
        positions = {t: i for i, t in enumerate(opened)}
        choose = sorted({8, len(stamps)//4, len(stamps)//2,
                         len(stamps)*3//4, len(stamps)-8})
        witnesses = []
        for cut in choose:
            time = stamps[cut]
            require(time >= meta["training_end_ms"] and
                    time in positions and positions[time] + 3 < len(base),
                    "PHASE14_NONCAUSAL_OR_MISSING_SOURCE_CANDLE")
            offset = positions[time]
            current = base.iloc[[offset]].copy()
            future = base.iloc[offset+1:offset+4].copy()
            require(bool(current.notna().all().all()) and
                    bool(future.notna().all().all()),
                    "PHASE14_NONFINITE_SOURCE_FEATURE")
            actual = verify_fitted_row_invariance(
                feature_pipe, label_pipe, current, future,
                feature_rows[cut], native_flags[cut])
            witnesses.append({"open_time_ms": time,
                              "model_flag": int(native_flags[cut]),
                              **actual})
        report.update(fitted_preprocessing_prefix_invariance_verified=True,
            observed_model_sha256=meta["model_sha256"],
            observed_candidate_sha256=meta["candidate_sha256"],
            original_source_commit_sha=meta["source_commit_sha"],
            native_predict_rows=len(stamps),
            intervention_row_count=len(witnesses),
            interventions=witnesses,
            feature_intervention_comparisons=sum(
                w["feature_comparisons"] for w in witnesses),
            label_intervention_comparisons=sum(
                w["label_comparisons"] for w in witnesses),
            source_canonical_sha256=matrix_digest(root / "canonical/15m.csv"),
            matrix_ledger_sha256=matrix_digest(events_path))
    except PipelineCausalityError as exc:
        report["errors"].append(str(exc))
    except (OSError, KeyError, TypeError, ValueError, ImportError,
            AttributeError, OverflowError, json.JSONDecodeError) as exc:
        report["errors"].append("PHASE14_PREPROCESSING_AUDIT_FAILED")
        report["error_type"] = type(exc).__name__
    return report


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--artifacts-root", required=True)
    cli.add_argument("--bundle", required=True)
    cli.add_argument("--candidate-metadata", required=True)
    cli.add_argument("--protocol", required=True)
    cli.add_argument("--seal", required=True)
    cli.add_argument("--out", required=True)
    args = cli.parse_args()
    result = inspect_frozen_candidate(
        args.artifacts_root, args.bundle, args.candidate_metadata,
        args.protocol, args.seal)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                  allow_nan=False)+"\n", encoding="utf8")
    print(json.dumps({k: result[k] for k in (
        "fitted_preprocessing_prefix_invariance_verified",
        "intervention_row_count", "full_model_pipeline_causality_verified",
        "independent_oos_verified", "errors") if k in result}))
    return 0 if result["fitted_preprocessing_prefix_invariance_verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
