# OOS Evaluation Evidence v1 — Design Proposal

Date: 2026-11-12 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Status: **PROPOSAL ONLY — NOT FROZEN, NOT IMPLEMENTED**

## 1. Scope and invariants

This proposal defines the minimum immutable evidence object needed for the existing manifest fields `evaluation_record_id` and `evaluation_record_digest`. It is deliberately separate from the already frozen manifest v1 and signature-envelope v1.

It does not authorize or perform:
- changes to the 37-field manifest v1, envelope v1, transform v1, or decision gate;
- registry event-chain, promotion/ACTIVE/revocation, trusted-time, trust-root or production-key implementation;
- production OOS provider, dataset provider, model training, calibration fitting, or creation of real evaluation evidence;
- selection of numerical acceptance thresholds (including C_min, minimum sample count, metric limits, calibration age or interval);
- S2 verifier work, VPS/runtime/deployment, database/T0/T1/T2 changes, or live trading.

The production decision remains fail-closed unless every already-required server-side evidence state is independently established.

## 2. Object identity and byte contract

Proposed schema identifier: `ai-calibration-oos-evaluation/v1`.

The evaluation record is an immutable UTF-8 JSON object:
- UTF-8 without BOM; duplicate keys, invalid UTF-8, unknown/missing fields and noncanonical bytes are rejected.
- Canonical bytes use the same RFC 8785 JCS serialization primitive already selected for manifest v1. This is a proposed reuse of canonicalization only; it does not reuse T0 trust policy or signer authority.
- No JSON numeric values. Counts, durations, decimal metrics and timestamps are canonical strings with field-specific grammar. Boolean values are JSON booleans; arrays/objects have fixed schemas.
- The exact bytes are SHA-256 hashed. The manifest's existing `evaluation_record_id` and `evaluation_record_digest` bind that identity under its existing detached signature. The verifier/provider must fetch the record by immutable ID and compare exact bytes and digest; mutable branch names or URLs are not identity.
- The record is not self-authorizing. A matching digest proves byte identity only, not dataset truth, correct evaluation, leakage absence or statistical acceptability.

## 3. Proposed field inventory

| Field | Meaning |
|---|---|
| `schema` | Exact schema ID/version |
| `evaluation_id` | Immutable unique record ID; equals manifest `evaluation_record_id` |
| `evaluation_kind` | Fixed value `OUT_OF_SAMPLE_CALIBRATION_EVALUATION` |
| `model_id`, `model_version`, `model_artifact_digest` | Exact evaluated model identity |
| `strategy_id`, `strategy_version`, `strategy_source_commit` | Exact strategy identity and source |
| `training_dataset_id`, `training_dataset_digest`, `training_cutoff` | Training lineage and temporal cutoff |
| `calibration_dataset_id`, `calibration_dataset_digest`, `calibration_start`, `calibration_end` | Dataset used to fit the calibration mapping; distinct from evaluation data |
| `evaluation_dataset_id`, `evaluation_dataset_digest` | Held-out evaluation dataset identity and exact bytes |
| `label_definition_id`, `label_definition_digest` | Exact target/event semantics |
| `forecast_horizon_value`, `forecast_horizon_unit` | Exact forecast horizon |
| `split_protocol_id`, `split_protocol_version` | Versioned temporal split and embargo procedure |
| `evaluation_start`, `evaluation_end` | Evaluation observation interval |
| `eligible_sample_count`, `excluded_sample_count` | Counts after deterministic eligibility/exclusion |
| `exclusion_summary_digest` | Digest of row-level or partition-level exclusion evidence |
| `metrics` | Fixed-schema metrics and their aggregation definitions |
| `uncertainty` | Fixed-schema uncertainty estimates and procedure |
| `reliability_bins_digest` | Digest of the reliability-bin data used to inspect calibration behavior |
| `baseline_definition_id`, `baseline_metrics` | Named, reproducible comparison baseline |
| `evaluation_code_commit`, `evaluation_code_digest` | Exact evaluator source identity |
| `environment_lock_digest` | Dependency/environment lock identity |
| `reproduction_command_id` | Stable identifier for the bounded deterministic evaluation procedure |
| `created_at` | Producer timestamp only; not trusted time |

All digest fields should use the frozen lowercase `sha256:` plus 64-hex grammar. All timestamps should use the manifest v1 UTC representation. The exact field set, enum values, decimal grammar, metric object schema and size limits require a separate contract freeze before implementation.

## 4. Dataset separation and temporal leakage controls

The provider must establish three distinct roles:
1. training data used to fit model parameters;
2. calibration data used only to fit the score-to-probability mapping;
3. evaluation/OOS data used only to evaluate the already-fitted model and calibration mapping.

The evaluation dataset must not overlap training or calibration observations. Split checks must operate on underlying observation/label windows, not only nominal candle timestamps. For each sample, the complete target horizon must lie within its assigned partition. Samples whose feature/label windows cross a boundary must be excluded or embargoed according to the exact versioned split protocol.

The evidence should bind:
- source dataset digests and exact partition manifests;
- time boundaries and horizon-aware embargo;
- deterministic sample IDs or a digest of the ordered eligible sample set;
- exclusion counts and a digest of exclusion reasons;
- proof that evaluation results were not used to select the model, calibration mapping, thresholds or hyperparameters.

A dataset hash alone is insufficient. The provider must independently reconstruct or verify partition membership and lineage from authoritative source evidence. Any missing lineage, ambiguous overlap, duplicate sample, future-data dependency or unexplained exclusion yields `UNVERIFIED`, not a warning.

## 5. Metrics and uncertainty — no thresholds selected

The record should preserve enough information to assess both discrimination and probability quality without declaring acceptance thresholds in this proposal.

Proposed metric families, subject to method/label suitability:
- probability quality: Brier score and log loss;
- reliability: fixed-bin observed frequency versus predicted probability, with per-bin sample counts and confidence intervals;
- discrimination: ROC-AUC and/or PR-AUC where mathematically meaningful;
- operational context: class prevalence, eligible sample count, coverage and abstention/out-of-range rate;
- baseline comparison: same metrics computed under a named, reproducible baseline.

Every metric definition must specify target semantics, direction, weighting, treatment of missing values and aggregation. Uncertainty must identify its method, resampling unit, interval level and deterministic seed or reproducible seed derivation. Do not infer that a metric is acceptable merely because it is present. Numeric acceptance limits and minimum effective sample counts remain Owner decisions.

## 6. Proposed verification result vocabulary

A future provider may return separate, non-interchangeable results:
- `BYTES_VERIFIED`: exact record bytes match the digest in the signed manifest.
- `IDENTITY_MATCHED`: model, strategy, dataset, label, horizon and calibration IDs match the signed manifest and source lineage.
- `SPLIT_LINEAGE_VERIFIED`: train/calibration/evaluation partitions and horizon embargo are independently established.
- `EVALUATION_REPRODUCED`: the declared evaluator and environment reproduce the recorded metrics within a separately frozen deterministic/tolerance contract.
- `OOS_EVIDENCE_VERIFIED`: all required structural and lineage checks pass.

These are proposed provider-internal statuses, not additions to the frozen manifest verifier output. The decision boundary's existing `oosEvidenceStatus=VERIFIED` must be asserted only after all required subchecks and a separately Owner-approved statistical policy pass. A digest match alone must never produce VERIFIED.

## 7. Provider boundary and trust separation

The future provider should accept immutable manifest/evaluation bytes plus independently obtained dataset-lineage evidence. It must not accept a client-supplied `oosEvidenceStatus`, confidence, metric verdict or registry status as authoritative.

The provider should return a server-constructed evidence object bound to:
- manifest ID and digest;
- evaluation ID and digest;
- model/strategy/dataset/label/horizon identities;
- split protocol and evaluator identities;
- verification timestamp from a separately approved trusted-time source;
- policy version and explicit result/reason.

This proposal does not define the registry event chain, trusted-time anchor, production trust configuration or the final statistical policy. Those remain separate gates. It does not authorize implementing this provider.

## 8. Contract test matrix to implement after schema freeze

The following are required deterministic contract tests, not claims of tests already run:

1. Canonical valid record: exact JCS bytes and digest accepted.
2. Reject BOM, invalid UTF-8, duplicate keys, unknown/missing fields, JSON numbers and noncanonical serialization.
3. Reject mismatched evaluation ID or digest against the signed manifest reference.
4. Reject model, strategy, source commit, training/calibration dataset, label or horizon mismatch.
5. Reject evaluation dataset equal to training or calibration dataset.
6. Reject overlapping sample IDs and temporal/label windows crossing split boundaries.
7. Reject missing or incorrect horizon embargo and future-feature leakage.
8. Reject inconsistent eligible/excluded counts and unexplained exclusions.
9. Reject invalid metric grammar, non-finite values, missing required metric metadata and malformed uncertainty definitions.
10. Reject missing evaluator commit, environment digest or reproducibility procedure.
11. Ensure metric presence alone never creates `OOS_EVIDENCE_VERIFIED`; policy thresholds must be separately supplied and version-bound.
12. Ensure any failed/missing subcheck returns a non-verified result and cannot produce an admission-eligible decision context.
13. Ensure a fully valid test fixture is clearly test-only and cannot be loaded as production trust/evidence.

Test fixtures must be synthetic and explicitly marked test-only. They must never be represented as actual OOS performance or production evidence.

## 9. Open decisions required before freezing v1

1. Whether the evaluation record uses the exact field inventory above or a narrower metric-neutral core plus separately hashed metric payload.
2. Exact metric set and per-metric schema for the selected prediction/label semantics.
3. Split protocol, sample identity, horizon embargo and reproducibility/tolerance rules.
4. Authoritative source and independent method for verifying dataset partition lineage.
5. Whether evaluation artifacts require their own detached signature or are sufficiently bound by the signed manifest digest plus separately trusted provider.
6. Statistical acceptance policy: minimum effective sample count, metric thresholds, uncertainty requirements, calibration freshness and C_min interaction.
7. Trusted-time source and how evaluation validity/freshness is established.
8. Maximum record/artifact sizes and deterministic resource bounds.

## 10. Disposition

**Design proposal prepared under explicit Owner approval.** No schema freeze, code implementation, contract tests, production provider, real dataset/evaluation, key, registry event, trust bootstrap, model training, calibration artifact or AI admission was created. Frozen manifest/envelope/transform v1 and current fail-closed decision boundary remain unchanged.

Next permitted increment: Owner review of the proposed field inventory, dataset split/lineage rules and metric families; only after those choices are explicitly frozen may implementation and executable contract tests be considered.
