# OOS Evaluation Evidence v1 — F6 Owner Decision Package

Date: 2026-11-12  
Branch: feature/t0-centralized-data-feeder-p1-20261101  
Status: **PROPOSAL ONLY — NO F6 POLICY OR PROVIDER DECISION IS RATIFIED**

## Purpose and boundary

F1-F5 structural contract is frozen. The offline validator and deterministic tests are implemented; OOS contract tests pass 13/13 on source SHA `0a3f73801cc5f1f5225658673b447ec658ac454d`. This package presents the remaining F6 decisions needed before any trusted OOS provider or real evaluation is implemented.

No option below is selected by this document. No source authority, threshold, trusted-time anchor, key, provider, data collection, model training, or AI admission is authorized. Until the applicable decisions and a separate implementation gate are approved, `oosEvidenceStatus` remains NOT_VERIFIED and AI admission remains fail-closed.

## Decision F6.1 — authoritative dataset lineage

**Question:** Which evidence source independently establishes the identity and sample membership of training, calibration, and evaluation partitions?

| Option | Definition | Limitation |
|---|---|---|
| A — Canonical bundle lineage (recommended candidate) | A versioned dataset-bundle manifest records source dataset IDs/digests, candle range, timeframe, sample identities, label horizon and transformation lineage. A read-only verifier recomputes digests and checks partition membership against the bundle. | Requires a separately frozen bundle-lineage contract and evidence that the manifest is generated from the canonical source, not caller assertions. |
| B — Evaluator-produced lineage | The evaluation pipeline emits sample-level lineage and partition manifests alongside the record. | Evaluator cannot be its own sole authority; independent readback/recomputation is still required. |
| C — External lineage provider | A separate provider supplies signed/attested dataset membership and partition evidence. | Introduces external trust, availability, custody and provider-specific controls. |

**Proposed boundary:** T0 remains the canonical market-data asset and is not modified by this decision. A lineage adapter may consume read-only evidence; it must not silently become a second canonical data store.

Owner decision required: A / B / C / defer.

## Decision F6.2 — split protocol and reproducibility

**Question:** Which exact temporal split and embargo protocol binds `split_protocol_id/version`?

| Option | Definition | Limitation |
|---|---|---|
| A — Fixed chronological holdout (recommended candidate for first OOS) | Train, calibration and evaluation partitions are strictly ordered; embargo is at least the maximum label/forecast horizon and any overlapping feature window. One frozen split version per evaluation. | A single holdout provides limited sensitivity to regime changes. |
| B — Purged walk-forward | Multiple chronological folds; purge overlapping labels/features and embargo boundaries; aggregate metrics using a separately specified rule. | More complex reproducibility and aggregation contract. |
| C — Defer protocol | Keep provider and real OOS evaluation blocked until the algorithm is specified. | Slower, but avoids silently choosing a methodology. |

Reproduction must bind exact code commit, environment lock, deterministic seed derivation and command. Numerical reproducibility tolerance must be explicitly specified; no tolerance is inferred here.

Owner decision required: A / B / C, plus whether a later walk-forward extension is planned.

## Decision F6.3 — metric catalogue and label suitability

**Question:** Which metrics are mandatory for the first calibration evaluation?

Suggested minimal candidate set:
- Brier score — probability calibration / squared error.
- Log loss — penalizes confident incorrect probabilities.
- Reliability-bin evidence — calibration curve data and bin counts.
- Sample count and uncertainty interval for each metric.
- A baseline using the same evaluation population.

This is a candidate list, not an acceptance policy. Directional accuracy, AUC, trading PnL, Sharpe, drawdown and execution metrics should not be treated as calibration-quality substitutes. Metric definitions, missing-value handling, class imbalance treatment and aggregation must be frozen before a real evaluation.

Owner decision required: approve the minimal set, modify it, or defer metric policy.

## Decision F6.4 — statistical acceptance and interaction with C_min

**Question:** What evidence is sufficient to admit a calibrated model?

| Option | Definition | Limitation |
|---|---|---|
| A — Evidence-first, thresholds deferred (recommended initial policy) | Produce descriptive OOS metrics and uncertainty only. No model admission based on the record until thresholds, minimum effective sample count, calibration duration, freshness and C_min interaction are approved. | No automatic AI admission yet. |
| B — Owner-approved fixed policy | Freeze per-metric thresholds, sample floor, interval requirements, calibration duration, maximum evidence age and C_min interaction before evaluation. | Requires numerical decisions and validation evidence now. |
| C — Empirical policy after shadow evaluation | First collect non-executing shadow evaluation evidence; propose thresholds from distributions, then require a separate Owner ratification before admission. | Shadow evidence itself remains non-authoritative until lineage/provider gates close. |

**Proposed invariant:** no threshold may be optimized against the same evaluation set used to report final OOS performance. Any threshold selection needs a separate development/calibration partition and independent evaluation.

Owner decision required: A / B / C. If B, numeric values must be supplied or separately prepared for approval.

## Decision F6.5 — trusted time and freshness

**Question:** What anchors evidence creation time and freshness?

| Option | Definition | Limitation |
|---|---|---|
| A — Defer trusted time (recommended now) | Keep evidence freshness UNKNOWN; do not claim current/latest/non-revoked. Any freshness-dependent AI admission remains blocked. | No freshness-based admission. |
| B — External trusted timestamp | Bind the evaluation/manifest digest to a named trusted timestamp authority and verify its token, policy and certificate chain. | External provider, trust and availability must be selected and approved. |
| C — Owner attestation only | Owner records an as-of statement through GitHub. | Platform attribution is not cryptographic time proof and cannot establish freshness. |

Owner decision required: A / B / C. Existing Owner-attestation policy must not be upgraded into trusted-time assurance.

## Decision F6.6 — detached evaluation signature

**Question:** Is an extra signature over the evaluation record required in addition to the signed manifest binding its exact digest?

- A — No additional signature (recommended candidate): signed manifest authenticates the record digest; provider independently verifies manifest signature and exact record bytes.
- B — Detached evaluation signature: add a separately signed statement over the evaluation record with a frozen domain-separated schema and key policy.
- C — Defer signature semantics and keep OOS NOT_VERIFIED.

No production/test key operation is authorized by selecting a direction; a separate implementation package would still be required.

Owner decision required: A / B / C.

## Decision F6.7 — provider resource limits

**Question:** What hard limits apply to the record parser and future lineage provider?

Candidate starting ceilings for Owner review only:
- OOS record: 256 KiB maximum UTF-8 bytes.
- JSON nesting depth: 8.
- Members per object: 64.
- Items per metric/uncertainty/reliability collection: 128.
- Identifier length: retain manifest v1 limit of 128 ASCII characters.
- Fail closed on size/depth/count overflow; do not echo raw evidence or secrets in errors/logs.

These values are proposals, not measured or ratified. Provider CPU/time/memory limits require a separate bounded execution profile; the offline validator currently has no provider execution or external I/O.

Owner decision required: approve these ceilings, supply alternatives, or defer resource policy.

## Recommended decision sequence

For the smallest safe first provider increment, consider:
1. F6.1 A — read-only canonical bundle lineage, only after a precise bundle evidence contract is frozen.
2. F6.2 A — fixed chronological holdout with explicit maximum-horizon/feature-window embargo.
3. F6.3 approve the minimal probability-calibration metric set, subject to exact definitions.
4. F6.4 A — descriptive evidence only; no admission thresholds yet.
5. F6.5 A — freshness UNKNOWN; fail closed where freshness is required.
6. F6.6 A — rely on the already signed manifest digest, provided the provider independently verifies the manifest; otherwise defer.
7. F6.7 ratify measured limits before provider implementation.

This recommendation is not an Owner decision. Each item remains open until explicitly approved.

## Non-authorizations

This package does not authorize:
- provider, adapter, schema, split algorithm or metric implementation;
- real OOS evaluation, dataset inventory or sample-level lineage collection;
- model training, calibration artifact creation or threshold tuning;
- production/test key generation, signature, trust-root or timestamp-provider operation;
- changes to the frozen F1-F5 contract, manifest v1, transform v1 or decision gate;
- changes to T0/T1/T2, VPS/runtime, databases, ledgers, Shared Risk Engine, Kill Switch or trading execution;
- live exchange access or real orders.

**Disposition: F6 DECISION PACKAGE PREPARED; OWNER DECISIONS REQUIRED; NO PROVIDER IMPLEMENTATION AUTHORIZED.**
