# G0.17 — Owner Ratification of Sensitivity Classification Policy (2026-11-11)

Date: 2026-11-11  
Status: **OWNER-RATIFIED — POLICY/DOCUMENTATION ONLY**  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Decision package: `docs/evidence/G0_16_OWNER_SENSITIVITY_CLASSIFICATION_DECISION_PACKAGE_2026-11-11.md`  
Decision-package blob at ratification: `95cc2a1a36b05e35e15348d870a147282d659851`  
Starting HEAD: `3826b4a483dd78b911473e3c4fcc80ad75501a7f`

## 1. Owner decision

On 2026-11-11, the owner explicitly approved all six decisions presented in G0.16, without amendment. This record captures that approval. It does not authorize implementation or runtime classification.

## 2. Ratified sensitivity vocabulary

The ordered sensitivity labels are:

`PUBLIC < INTERNAL < CONFIDENTIAL < RESTRICTED`

The following are classification states, not sensitivity labels:

- `UNCLASSIFIED`
- `CONFLICTED`
- `PENDING_OWNER_DECISION`

Unknown, stale, contradictory or unauthenticated classification evidence must fail closed. Preserve the object and apply the protective handling posture; do not silently default to PUBLIC or INTERNAL.

## 3. Ratified minimum class mapping

The owner ratifies the G0.16 §3 mapping as the minimum default:

| Data class / domain | Ratified minimum |
|---|---|
| T0 canonical candles, source versions, correction lineage | `RESTRICTED` |
| T0 lease, fencing, writer and recovery state | `RESTRICTED` |
| T1 raw exchange observations and capture manifests | `CONFIDENTIAL` |
| T1 sidecar/session integrity, gap and provenance evidence | `RESTRICTED` |
| T2 canonical input snapshots, features, labels, training datasets | `CONFIDENTIAL` |
| T2 model artifacts, evaluation reports and model provenance | `CONFIDENTIAL` |
| T2 ephemeral inference outputs | `CONFIDENTIAL` |
| T3 CORE_LEDGER, AI_LEDGER, account/equity, reservations, risk state | `RESTRICTED` |
| T3 signals, decisions, paper events, fills, funding, reconciliation and audit records | `RESTRICTED` |
| T4 deterministic caches, read models and materializations | `INTERNAL` |
| Governance approvals, policy history, custody/trust records, manifests, holds, tombstones and lifecycle evidence | `RESTRICTED` |
| Wholly synthetic fixtures and CI reports meeting G0.16 constraints | `INTERNAL` |
| Noncanonical copies, backups, replicas and exports | Inherit source sensitivity; never lower by default |
| Unknown, unclassified, orphaned or incompletely inventoried data | `UNCLASSIFIED`; handle as `RESTRICTED` pending resolution |

These are minimum defaults, not a blanket classification of every physical object. Exact content, lineage, embedded fields, aggregation and recipient context may require a higher sensitivity.

## 4. Ratified inheritance and declassification rules

1. Effective sensitivity is the most restrictive of class default, source/parent, embedded content, applicable policy/hold and recipient/export-context requirements.
2. Copies, backups, replicas, caches, features, reports and exports inherit the highest sensitivity of their inputs unless an approved transformation-specific assessment establishes otherwise.
3. Aggregation does not lower sensitivity. Derived outputs may be raised where they reveal restricted information or enable reconstruction.
4. Downgrade/declassification requires a separate explicit owner-approved decision for the exact scope, supported by evidence. Consumption, rebuildability, ACK, age or copying does not lower a label.
5. Public release is a separate explicit decision. Repository visibility or artifact expiry does not make an object PUBLIC.
6. Credentials, private keys, tokens, signing material and trust-root secrets are always `RESTRICTED`; secret values must not be embedded in ordinary evidence reports or CI artifacts.

## 5. Relationship to lifecycle policy and authority

- Sensitivity classification is separate from lifecycle disposition and retention.
- RET-01 B remains unchanged: T0 canonical data is protected by default; no routine or scheduled automatic deletion.
- RET-02 B remains unchanged: only its four specified noncanonical groups may enter exact-object/version read-only eligibility assessment after all predicates are proven.
- A sensitivity label does not establish lifecycle eligibility, retention-floor completion, archive/deletion approval, or execution authority.
- `RESTRICTED` does not mean permanent retention; `INTERNAL` does not mean disposable; `PUBLIC` does not imply deletion eligibility.
- No numeric retention floor, TTL, grace period, review cadence or trusted-time freshness value is created.
- Each concrete destructive operation still requires separate explicit bounded approval.
- T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.

## 6. Status and remaining gates

- Owner ratification of all six G0.16 decisions: **PASS**.
- Sensitivity vocabulary and minimum class mapping: **OWNER-RATIFIED**.
- G0.15 R4 policy-definition gap: **CLOSED AT DOCUMENTARY OWNER-POLICY LEVEL**.
- Evaluator/schema/registry integration: **NOT IMPLEMENTED** and requires separate bounded approval.
- Evaluator source validation/authentication of supplied sensitivity facts: **NOT ESTABLISHED**.
- Independent review: **NOT RUN**.
- Tests: **NOT RUN**.
- GitHub Actions: **NOT DISPATCHED**; no run/artifact.
- Runtime inventory or classification: **NOT PERFORMED / NOT VERIFIED**.
- TEST-01–07: no status promotion; prior 0/87 executed remains.
- Destructive authority: **NOT GRANTED**.

## 7. Explicit non-actions

No source code, tests, fixtures, schema, API, registry, adapter, runner, oracle, workflow, scheduler, service, permission, credential, database, storage, VPS, market data, model, ledger or runtime changes. No production inventory, file/secret scan, network/provider/database access, workflow dispatch, archive, quarantine, cleanup, expiry, compaction, vacuum or deletion.

## 8. Next gate

The next candidate is a separately bounded implementation plan for propagating and validating the ratified sensitivity field in the pure lifecycle evaluator and its in-memory synthetic tests. That plan must preserve the five-disposition contract, specify canonical field/type/unknown/conflict behavior, and avoid treating labels as deletion authorization. No implementation, CI dispatch, broader TEST-01–07 harness, runtime inventory or destructive operation is authorized by this ratification.

**Final status: SIX SENSITIVITY POLICY DECISIONS OWNER-RATIFIED — POLICY ONLY — NO IMPLEMENTATION OR DESTRUCTIVE AUTHORITY.**
