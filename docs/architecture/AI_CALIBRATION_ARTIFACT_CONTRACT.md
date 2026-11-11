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
| `calibration_transform` / `transform_parameters` | The approved mapping from raw model score to event probability (for example, method-specific parameters or a versioned calibration table) |
| `evaluation_summary_ref` | Immutable reference to OOS evaluation evidence, including reliability/calibration metrics and sample lineage |
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

A future trusted provider must bind two distinct objects: (a) the immutable calibration artifact, which defines the score-to-probability transform and its evaluation evidence; and (b) the per-inference prediction envelope, which contains the calibrated confidence produced by applying that exact transform to the raw score. The per-inference envelope must include the prediction/candle identity and calibration artifact ID, version and digest. The provider may construct an immutable admission evidence object containing:
- per-inference calibrated confidence and declared event semantics;
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


## 9. Recommended low-cost trust architecture — proposal only

For this personal, paper-first system, prefer a repository-backed append-only registry over introducing a separate database or paid registry service at this stage. This is a design recommendation, not an owner-approved provider selection.

1. **Registry record:** keep a versioned manifest and compact calibration artifact (transform parameters/table plus evaluation summary) in a dedicated repository path. Each promotion is a new immutable version/commit; do not overwrite a previously approved version. A manifest points to exact dataset/model/code identities and content digests.
2. **Independent publisher trust:** sign the canonical manifest digest with an offline Ed25519 private key. Keep the corresponding public key/key ID in a pinned trust configuration. The private key must not be stored in the repository, GitHub Actions secrets, CI variables, the VPS or runtime. CI and runtime only verify signatures. This recommendation does not depend on the previously discussed adapter implementation.
3. **Two checks, not one:** SHA-256 (or another explicitly versioned digest) verifies exact bytes; the signature verifies that an authorized key approved that manifest. Neither proves calibration quality or absence of leakage.
4. **Promotion gate:** a manifest can be registered as candidate, but only an explicit owner-approved promotion record may make it eligible for AI admission. Revoke/supersede by appending a new registry record; never rewrite old evidence. Key rotation/revocation must be explicit and auditable.
5. **Evidence lineage:** include exact model artifact digest, strategy/code commit, training dataset ID/hash and cutoff, calibration dataset ID/hash and time range, label definition, horizon, calibrator method/version, sample count, evaluation metrics, and OOS split boundaries. Calibration samples must be disjoint from training and must obey the forecast label horizon/embargo so labels cannot leak across the split.
6. **Storage boundary:** keep small manifest/transform/evaluation artifacts in the registry. Reference canonical T0-derived dataset bundles by immutable ID/hash; do not copy, mutate or make T0 subordinate to the registry. Large raw datasets need not be duplicated into Git.
7. **Verification path:** a future read-only provider resolves an approved manifest, verifies signature and digest, validates revocation and compatibility, loads only the exact referenced transform, then emits calibrated confidence bound to that artifact digest. It must not trust a confidence number supplied by an untrusted caller.

**Important semantic correction:** the calibration artifact is not itself one fixed `calibrated_confidence` value. It contains a transformation/evidence model. Each prediction receives its own calibrated confidence at inference, and that value must be cryptographically and structurally bound to the exact calibration artifact version.

**Remaining owner decisions:** confirm repository-backed registry; confirm offline Ed25519 signing/trust-root lifecycle; select manifest format/canonicalization; select calibration method and OOS evaluation protocol; select numerical `C_min`, sample, duration and freshness thresholds only after evidence. Until then G0-01/02/03 remain BLOCKED.


## 10. Owner-approved registry direction — 2026-11-11

**Owner decision: APPROVED (architecture direction only).**

The selected direction for the future calibration trust architecture is:
- a GitHub-backed append-only registry of versioned manifests and compact calibration artifacts/evaluation evidence;
- offline Ed25519 signing of the canonical manifest digest;
- pinned public-key verification by future read-only consumers;
- explicit append-only approval, revocation, supersession and key-lifecycle records;
- private signing key remains offline and must not be placed in the repository, GitHub Actions, CI variables, VPS or runtime.

This approval selects the architectural direction only. It does **not** approve registry path/schema, manifest canonicalization, key ceremony/rotation/revocation details, implementation, CI verification workflow, runtime provider, calibration training, numerical thresholds or AI activation. Those require separate design freeze and implementation gates.

Digest integrity, signer authorization and statistical/OOS validity remain three independent checks. G0-01/02/03 remain BLOCKED until the remaining trust, schema, provenance and evidence thresholds are resolved.


## 11. Manifest and key lifecycle design follow-up — 2026-11-11

The owner requested documentation-only completion of the manifest and Ed25519 lifecycle design. Two proposal contracts and one evidence report were added:
- `docs/architecture/AI_CALIBRATION_REGISTRY_MANIFEST_CONTRACT.md`: immutable manifest/evaluation/event/signature record model, provenance bindings, detached signature, canonicalization proposal, Git object evidence and T0 A2.2 separation.
- `docs/architecture/AI_CALIBRATION_ED25519_KEY_LIFECYCLE_CONTRACT.md`: offline ROOT/CALIBRATION_SIGNER/RECOVERY_AUTHORITY roles, key generation, custody, pinning, signing, rotation, revocation, compromise response and recovery.
- `docs/evidence/AI_CALIBRATION_MANIFEST_AND_KEY_LIFECYCLE_DESIGN_2026-11-11.md`: scope, design decisions, blockers and verification record.

These are proposals, not frozen implementation contracts. Exact schema/canonicalization, signature statement/domain bytes, trust bootstrap, key ceremony/tooling/custody, trusted-time and recovery topology remain owner decisions. The T0 A2.2 checkpoint-attestation protocol is a separate trust domain; no authority or production implementation is inherited. No keys, signatures, registry, code, tests, workflow or provider were created. G0-01/02/03 remain BLOCKED; GREEN-1..5 remain NOT AUTHORIZED.
