# AI Calibration Artifact Contract

**Status:** DESIGN CONTRACT PROPOSAL — GREEN-0 DOCUMENTATION ONLY  
**Date:** 2026-11-11  
**Applies to:** independent AI Strategy admission; not Strategy Core  
**Authority:** owner-approved AI Strategy Contract and AI Strategy API Contract Proposal

## 1. Purpose and non-goals

Define the evidence required before a raw model prediction may be interpreted as calibrated confidence for an AI LONG/SHORT ENTRY decision.

This document does not implement a calibration pipeline, registry, loader, signature verifier, model, training job, inference path or execution path. It does not choose `C_min`, sample-count, calibration-duration or age thresholds. It does not enable AI trading.

## 2. Trust boundary

The prediction exporter is not the calibration authority. A prediction report may reference a calibration artifact, but it cannot self-assert trust merely by supplying a confidence number or hash.

A future admission provider must obtain the artifact from an owner-approved trusted registry/manifest and verify:
- the artifact's exact bytes against a trusted digest (and, if the selected registry supports it, an authenticated publisher/signature);
- registry identity, immutable artifact/version identity and revocation/status;
- that the artifact is approved for the exact model, strategy, training dataset, label definition and forecast horizon;
- that the calibration evidence is temporally out-of-sample relative to model training and the prediction being admitted;
- that all policy-required freshness, sample and calibration-period conditions are met.

A digest proves byte identity, not publisher authority or calibration quality. Registry trust and digest verification are separate requirements. No registry/provider is selected in this document.

## 3. Logical artifact contract

The following is a logical field inventory, not a frozen serialization format. Exact schema/version and canonicalization must be decided with the registry owner before implementation.

| Field | Required meaning |
|---|---|
| `artifact_schema_version` | Immutable schema identifier/version |
| `calibration_id` / `calibration_version` | Registry-issued immutable identity |
| `artifact_digest` / `digest_algorithm` | Digest of exact canonical artifact bytes |
| `registry_id` / `registry_record_id` | Trusted registry provenance |
| `publisher_identity` | Authenticated artifact producer identity |
| `model_id` / `model_version` | Exact model compatibility |
| `strategy_id` / `strategy_version` | Exact strategy compatibility |
| `training_dataset_id` / `training_dataset_hash` | Exact model-training dataset identity |
| `calibration_dataset_id` / `calibration_dataset_hash` | Separate calibration dataset identity |
| `label_definition` | Exact target/label semantics |
| `forecast_horizon` | Exact prediction horizon and unit |
| `calibration_method` / `method_version` | Method and implementation version |
| `calibration_started_at` / `calibration_completed_at` | Calibration evidence interval |
| `calibrated_at` | Artifact creation/approval time |
| `sample_count` | Count of eligible calibration observations |
| `calibrated_confidence` | Calibrated probability/confidence in [0,1] for the declared event |
| `evaluation_summary_ref` | Immutable reference to OOS evaluation evidence |
| `status` | Registry-controlled approved/revoked/superseded state |

Fields may be represented in a signed manifest or registry record rather than duplicated in the artifact. The future adapter must preserve an auditable binding between the exact artifact digest and all compatibility metadata.

## 4. Compatibility and temporal rules

Admission must fail closed when any required identity is absent or mismatched:
- prediction model/version versus calibration model/version;
- strategy/version;
- training dataset identity/hash;
- label definition;
- forecast horizon;
- calibration artifact schema/version;
- trusted registry record and exact digest.

Temporal OOS validation must establish, using trusted timestamps and dataset ranges, that calibration observations are not used to train the model being calibrated and do not overlap with prohibited training or inference periods. Timestamp ordering alone is insufficient if dataset ranges or lineage indicate leakage.

The contract must distinguish:
- model training interval/cutoff;
- calibration dataset interval;
- calibration artifact approval/creation time;
- prediction candle/dataset time;
- artifact observation/retrieval time.

No calibration window or maximum-age value is selected here. Missing or unverifiable temporal lineage blocks admission.

## 5. Confidence and policy validation

A future decision boundary must:
- accept only a finite numeric decimal in [0,1]; reject booleans, NaN, infinity, strings and out-of-range values;
- bind the value to the exact approved calibration artifact and prediction identity;
- require a versioned owner-approved policy containing `C_min`, minimum sample count, minimum calibration duration and maximum artifact age;
- require calibrated confidence >= the policy's `C_min`;
- reject absent, stale, revoked, superseded, incompatible or digest-mismatched artifacts.

No numeric value for `C_min`, sample count, duration or maximum age is authorized by this document. Test fixtures must be explicitly marked as fixtures and never become production defaults.

## 6. Runtime/admission output

A future trusted provider may construct an immutable admission evidence object containing:
- calibrated confidence and declared event semantics;
- artifact and registry IDs/versions/digests;
- model/strategy/training/calibration dataset identities;
- label/horizon compatibility;
- calibration method/version and OOS evidence reference;
- sample count and calibration time interval;
- policy version and the evaluated freshness result.

The pure decision function must consume this server-constructed object; it must not fetch arbitrary artifact paths, trust caller-supplied confidence or access the registry itself.

## 7. Failure behavior

Missing provider/configuration, registry outage, failed digest, invalid signature where required, unknown/revoked status, provenance mismatch, leakage uncertainty, stale artifact, invalid confidence or unmet policy threshold => **no AI trade intent**. Do not fall back to raw predicted return, FreqAI `do_predict`, generic confidence, cached unverified artifacts or Core signals.

AI Strategy remains independent of Strategy Core, but the shared risk engine remains the final admission authority for any future valid AI intent. AI DCA remains disabled in v1; this contract covers ENTRY confidence only.

## 8. Open decisions and approval gates

Still unresolved:
1. Trusted registry/manifest product and owner.
2. Authentication/signature model and trust-root lifecycle.
3. Exact schema and canonical serialization/digest algorithm.
4. Calibration method and event/probability semantics.
5. Dataset lineage and temporal OOS verification provider.
6. Numerical `C_min`, minimum sample count, minimum duration and maximum age, supported by OOS evidence.
7. Artifact revocation and rollback policy.

**Disposition:** design proposal only. G0-01/G0-02/G0-03 remain BLOCKED. Implementation, calibration training, model changes, OOS acceptance, feature activation and trading are not authorized.
