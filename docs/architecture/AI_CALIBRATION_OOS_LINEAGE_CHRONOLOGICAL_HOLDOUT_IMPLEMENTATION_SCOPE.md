# OOS Evidence v1 — Canonical Bundle Lineage & Chronological Holdout Implementation Scope

Date: 2026-11-12 (Asia/Ho_Chi_Minh)
Repository: kenznguyen/btcusdt-telegram-signals2
Target branch: feature/t0-centralized-data-feeder-p1-20261101
Status: **IMPLEMENTATION SCOPE PROPOSAL ONLY — NO CODE OR DATA WORK AUTHORIZED**

## 1. Purpose

Translate the Owner-approved F6.1/F6.2 directions into a bounded, reviewable implementation plan for independently checking dataset lineage and chronological split declarations used by OOS Evaluation Evidence v1.

This proposal is downstream of:
- F1–F5 frozen OOS Evaluation Evidence v1 structural contract;
- the pure offline validator in `pipeline/oos_evaluation.py`;
- the F6 Owner decision record `docs/architecture/AI_CALIBRATION_OOS_EVIDENCE_V1_F6_OWNER_DECISION_RECORD.md`.

The proposal does not reopen those decisions and does not authorize implementation. A separate explicit approval of this exact scope is required before source/test changes.

## 2. Non-negotiable boundaries

- **T0 remains the independent canonical market-data asset.** All bundle and lineage reads are read-only. No T0 source, schema, storage, API, feeder, lease, data, or runtime changes.
- Do not make the registry, OOS evidence, evaluator, or bundle manifest a second canonical candle store.
- No network access, exchange access, provider service, VPS/runtime, database, or external trust dependency in the first implementation increment.
- No model training, calibrator fitting, threshold tuning, real OOS evaluation, or AI admission.
- No changes to frozen F1–F5, manifest v1, signature envelope v1, transform v1, or decision gate.
- Preserve `OOS NOT_VERIFIED`, `lineage NOT_VERIFIED`, `horizon_embargo NOT_VERIFIED`, `reproducibility NOT_VERIFIED`, and `ai_admission_eligible=false` until a separately authorized trust/provider layer proves the relevant claims.
- Keep `AI_EXECUTION_ENABLED=false`; no live orders or exchange execution.
- Work only on the existing branch; no branch creation, PR split, merge, rebase, cherry-pick, force push, VPS deployment, or runtime activation.

## 3. Proposed work packages

### WP0 — Contract and source inventory (read-only)

Before implementation, inspect the exact existing `T0_M15_H1_DATASET_BUNDLE_V1` contract and its producer/consumer references in the current branch. Record:
- authoritative bundle schema/version and canonical serialization rules, if already frozen;
- exact fields that identify source datasets, candle ranges/timeframes, sample identities, labels, feature windows, and transformations;
- which fields are independently recomputable from read-only T0 evidence versus merely asserted by a bundle producer;
- how the bundle digest is computed and where immutable bundle bytes are located;
- current split/label generation behavior and any leakage/overlap constraints.

Deliverable: a field-by-field compatibility matrix against OOS Evidence v1 and a list of unresolved contract gaps. Do not invent a new bundle format or silently reinterpret the existing one. If the current bundle contract cannot support sample-level lineage, stop and prepare a separate contract decision package.

### WP1 — Freeze the minimum lineage-verification contract

Subject to WP0 findings, specify a read-only verifier input/output contract. It must define:
- immutable bundle identity, schema version and exact-byte digest;
- source dataset identities/digests and timeframe/range coverage;
- deterministic sample identity and membership for train/calibration/evaluation;
- mapping from each sample to its feature window, forecast/label horizon and label definition;
- transformation lineage and deterministic ordering;
- duplicate, missing, excluded and invalid sample accounting;
- independent recomputation/readback requirements and what cannot be independently established;
- bounded input sizes and fail-closed error semantics.

A bundle digest or producer assertion alone is not proof of lineage. The verifier must compare immutable bytes to the declared digest and recompute all claims that can be independently derived from the canonical read-only source. Claims it cannot recompute must remain NOT_VERIFIED.

### WP2 — Freeze the fixed chronological holdout protocol

Specify the split as a deterministic, versioned temporal protocol. The protocol must:
- order train, calibration and evaluation strictly by event/availability time according to an explicitly selected timestamp semantic;
- prohibit sample identity overlap across partitions;
- ensure each sample's full label/forecast horizon remains inside its assigned partition;
- embargo across partition boundaries by at least the maximum forecast/label horizon and any overlapping feature-window span;
- prohibit feature construction from candles or information unavailable at the sample's decision time;
- define boundary inclusivity/exclusivity, missing/gap behavior, duplicate handling and exclusion reasons;
- bind split protocol ID/version, cutoff instants, maximum horizon, feature lookback/window semantics, deterministic seed derivation (if any), and exact implementation/evaluator commit;
- define deterministic output ordering and a reproducibility check.

No train/calibration/evaluation ratios, numeric dates, sample floor, metric acceptance thresholds, C_min, freshness or calibration duration are selected by this proposal. Split boundaries must be supplied by a frozen protocol/configuration, not tuned against the final evaluation results.

### WP3 — Implement pure offline verifier and deterministic tests

After WP0/WP1/WP2 contracts are frozen and separately approved:
- implement a pure offline, read-only verifier with no network or database writes;
- verify bundle bytes/digest, schema, dataset references, sample membership, time ordering, partition disjointness, full horizon embargo, feature-window overlap and exclusion reconciliation to the extent supported by source evidence;
- produce a structured report that distinguishes VERIFIED, INVALID and NOT_VERIFIED per claim; never collapse missing authority into PASS;
- integrate only as an independent evidence-validation step; do not grant it authority to mark the signed manifest authentic or to set OOS evidence VERIFIED.

Test-first coverage must include:
1. canonical valid bundle and deterministic valid split;
2. altered bytes/digest mismatch;
3. unknown/missing fields, duplicate JSON keys, invalid UTF-8 and noncanonical serialization;
4. duplicate sample IDs and cross-partition overlap;
5. out-of-order or overlapping time partitions;
6. label/forecast horizon crossing a partition boundary;
7. feature window crossing embargo or using future information;
8. missing candles/gaps and incomplete source coverage;
9. excluded-sample count/reason reconciliation failures;
10. malformed or unsupported bundle version;
11. oversized/deep/many-member inputs at the approved provisional ceilings;
12. absent/unverifiable source evidence returning NOT_VERIFIED rather than VERIFIED;
13. deterministic repeated execution producing byte-identical reports.

No fixture may be described as real OOS evidence. Synthetic fixtures are test-only and must be clearly labelled.

### WP4 — CI and evidence capture

- Add focused compile/unit tests to the existing GitHub Actions workflow without replacing or weakening existing gates.
- Preserve a separate focused result for lineage/split tests and the existing OOS validator tests.
- Capture exact source SHA, workflow run/job IDs, test counts, artifact ID/name/digest and overall workflow status.
- If the broader AI/Dual Strategy RED suite fails, report its failure separately; do not describe the full workflow as PASS.
- Update `docs/PROJECT_SESSION_HANDOFF.md` after the increment with scope, exact evidence, status and next gates.

## 4. Candidate code surface (not yet authorized)

Likely minimal additions, subject to WP0 repository inventory:
- a dedicated pure module for bundle lineage and split verification under `pipeline/`;
- a focused deterministic test module under `pipeline/`;
- a narrowly scoped update to the existing AI Strategy contract workflow;
- this architecture scope and the session handoff.

Do not modify `market_data/`, T0 API/feeder/storage, `freqai_bridge/context.py`, registry manifest/transform/decision contracts, database schemas, or runtime configuration unless a separate Owner decision explicitly changes scope.

## 5. Acceptance criteria for a future implementation

The implementation may be marked **PASS** only if:
- existing bundle contract compatibility is demonstrated, with no silent schema reinterpretation;
- all lineage and split rules are explicit, versioned and deterministic;
- tests prove invalid/overlapping/leaking inputs are rejected;
- missing authoritative evidence remains NOT_VERIFIED;
- verifier performs no network, exchange, DB write, T0 mutation, model training or trading action;
- all focused tests and compile checks pass at the exact recorded SHA;
- workflow artifacts and full workflow status are recorded accurately;
- independent code review findings within the approved scope are resolved or explicitly dispositioned.

Even if all implementation tests pass, the result is only **offline structural/lineage-verification capability**. It does not by itself authenticate the manifest, establish trusted time, establish statistical acceptability, set `oosEvidenceStatus=VERIFIED`, or make AI admission eligible.

## 6. Explicit unresolved items before coding

WP0 must establish whether the existing bundle contract already defines:
- canonical bytes and digest domain;
- sample identity and deterministic ordering;
- timestamp semantics (event time vs availability time);
- feature-window and label-horizon representation;
- split boundaries and exclusions;
- authoritative source references and independently reproducible derivations.

If any are absent or ambiguous, pause and submit the exact missing contract decisions to Owner. Do not guess values or silently extend a frozen contract.

The provisional F6.7 ceilings (256 KiB record, depth 8, 64 members/object, 128 metric/uncertainty/reliability items, 128-character ASCII identifiers) are planning bounds only. WP0/WP1 must verify compatibility and WP3 must test enforcement. Provider CPU/time/memory limits are outside this offline increment.

## 7. Approval gate

This document requests approval for a bounded implementation package, not authorization to start it. Before coding, Owner must explicitly approve:
1. WP0 inventory result and any compatibility gaps;
2. the exact WP1 lineage contract;
3. the exact WP2 split protocol semantics and version;
4. the final file/change list and focused test plan.

Until that approval:
- no source code, tests, workflow, dependency, dataset, bundle, or runtime changes;
- no real dataset inventory or sample-level lineage collection;
- no real OOS evaluation;
- OOS remains NOT_VERIFIED and AI admission remains fail-closed.

**Disposition: IMPLEMENTATION SCOPE PREPARED; CODE IMPLEMENTATION NOT AUTHORIZED; OOS NOT VERIFIED; AI ADMISSION FAIL-CLOSED.**
