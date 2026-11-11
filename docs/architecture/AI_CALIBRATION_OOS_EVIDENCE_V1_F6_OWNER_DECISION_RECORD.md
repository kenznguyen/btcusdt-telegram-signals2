# OOS Evaluation Evidence v1 — F6 Owner Decision Record

Date: 2026-11-12 (Asia/Ho_Chi_Minh)
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/t0-centralized-data-feeder-p1-20261101
Decision authority: Owner explicit approval in conversation on 2026-11-12

## Decision

Owner approves the recommended design direction for all seven F6 items in `docs/architecture/AI_CALIBRATION_OOS_EVIDENCE_V1_F6_OWNER_DECISION_PACKAGE.md`, subject to the qualifications and non-authorizations below.

### Ratified design direction

| Item | Owner decision | Frozen boundary |
|---|---|---|
| F6.1 — Dataset lineage | **A: Canonical bundle lineage, read-only** | T0 remains the canonical market-data asset. A future verifier may consume independently verifiable bundle evidence only; it must not mutate T0 or establish authority from caller assertions alone. |
| F6.2 — Split protocol | **A: Fixed chronological holdout** | Train, calibration and evaluation partitions are strictly ordered. Embargo must cover the maximum forecast/label horizon and overlapping feature window. Exact split algorithm, identifiers/versioning, seed derivation and numerical reproducibility tolerance must be specified before provider/evaluation implementation. |
| F6.3 — Calibration metrics | **Approve the minimal probability-calibration set** | Brier score, Log Loss, reliability-bin evidence, sample counts, uncertainty intervals and a baseline over the same evaluation population. This approves the metric categories, not yet their complete mathematical definitions, binning, missing-value/imbalance handling, aggregation or acceptance thresholds; those must be frozen before a real evaluation. |
| F6.4 — Statistical policy | **A: Evidence-first; admission thresholds deferred** | OOS evidence is descriptive only. No C_min, minimum effective sample count, calibration duration, freshness/age threshold or metric acceptance threshold is approved. No admission based on OOS evidence until a separate policy decision. |
| F6.5 — Trusted time | **A: Defer trusted time** | Freshness remains UNKNOWN. Owner/GitHub attestation is not trusted-time proof. Any freshness-dependent AI admission remains fail-closed. |
| F6.6 — Detached evaluation signature | **A, conditional** | No additional detached evaluation signature if the provider independently verifies the signed manifest and exact evaluation-record bytes/digest binding. If that condition cannot be met, defer and keep OOS NOT_VERIFIED; do not silently substitute another trust mechanism. |
| F6.7 — Resource limits | **Approve the proposed ceilings as provisional design bounds for planning** | Candidate ceilings: record 256 KiB; JSON depth 8; 64 members/object; 128 items per metric/uncertainty/reliability collection; identifier length 128 ASCII characters. These are not yet measured provider runtime limits. Validate parser behavior and resource impact before implementation; provider CPU/time/memory profile and final enforcement details require a bounded implementation specification. |

## Global invariants

- Preserve frozen OOS Evidence v1 F1–F5 structure, manifest v1, transform v1 and the existing fail-closed decision boundary.
- The offline validator's digest match to a supplied binding is not manifest authenticity. It must continue to report manifest authenticity NOT_VERIFIED unless an authorized verifier establishes it.
- F4 sample-level partition disjointness, complete horizon embargo, future-feature exclusion and exclusion accountability require authoritative lineage verification; the offline validator does not establish them.
- OOS evidence status remains NOT_VERIFIED until an independently authorized provider verifies manifest authenticity, exact record bytes, dataset lineage, split/embargo, evaluator identity and reproducibility.
- AI admission remains fail-closed. No numerical admission thresholds or freshness claims are authorized by this decision.

## Explicit non-authorizations

This is a policy/design decision only. It does **not** authorize:
- implementation or deployment of a lineage provider/adapter, split pipeline, metric evaluator or OOS provider;
- real dataset inventory, sample-level lineage collection or real OOS evaluation;
- model training, calibration, production artifact generation or threshold tuning;
- production/test key generation, signing, trust-root enrollment, timestamp provider or registry event operations;
- changing F1–F5, manifest v1, transform v1, decision gate, T0/T1/T2, databases, ledgers, Shared Risk Engine, Kill Switch or trading paths;
- VPS/runtime changes, deployment, service activation, exchange access, live trading or real orders.

Any implementation/provider work requires a separate explicit approval of its exact scope, source changes, tests and evidence plan. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.

## Verification and disposition

- Decision source: explicit Owner approval in the conversation on 2026-11-12.
- This record is documentation only; no executable tests are applicable.
- OOS validator evidence remains tied to source SHA `0a3f73801cc5f1f5225658673b447ec658ac454d`, workflow run `43073542645`, job `130707512877`; OOS tests 13/13 PASS. The overall workflow failed in the separate AI/Dual Strategy RED suite (12 failures, 6 errors); this is not a full-system PASS.
- **Disposition: F6 DESIGN DIRECTIONS APPROVED WITH QUALIFICATIONS; PROVIDER/REAL OOS IMPLEMENTATION NOT AUTHORIZED; OOS NOT VERIFIED; AI ADMISSION FAIL-CLOSED.**
