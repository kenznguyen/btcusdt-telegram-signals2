# Bounded Main Integration Map — 2026-11-18

## Exact comparison state

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Target branch: `feature/core-operational-proof-20261112`
- Branch HEAD before this map: `4b0d045fcbf67060612f2dd67269061609fc9963`
- Main HEAD: `6bff2aff91657238297848ef644a0cb4112ab428`
- Merge base: `f5b74affb8777953fa66d241784965fbb0e577ba`
- Divergence: branch 4,591 ahead / 85 behind.
- Main-side delta from merge base: 85 commits, 16 changed paths (14 added, 2 modified).
- Review basis: bounded static source/workflow/document comparison recorded in integration passes 1–3. This is not a full semantic review of all 85 commits and not a merge-tree simulation.

## Integration map by path

| Main-side path | Classification | Required disposition |
|---|---|---|
| `.github/workflows/core-live-data-operational-proof.yml` | **PRESERVE BRANCH VERSION** | Branch workflow has 37 steps and explicit Dual Ledger bootstrap + Kill Reset regression gates; main has 35. Do not replace branch with main. Keep exact-SHA CI evidence tied to its tested SHA. |
| `.github/workflows/t0-manual-validation.yml` | **PRESERVE, THEN CORRECT UNDER APPROVAL** | Branch has richer T0 automatic gates and manual choices. Do not replace with main's manual-only version. Resolve F-07 skipped-job dependency chain, F-08 missing PR trigger/branch intent, and F-10 manual-only P3/Kraken coverage before relying on it as integrated CI. |
| `.github/workflows/t0-signature-a2-2-stage-i.yml` | **IDENTICAL / NO CONTENT MERGE** | Main and branch blob are identical: `5fa94939181af5f1f33686c3444bc6f8a0326962`. Owner decision allows Stage I synthetic offline harness only; it explicitly says CI/workflow execution is not authorized without separate approval. Do not dispatch it based on file presence. |
| `core_runtime/test_api_facade.py` | **PRESERVE BRANCH VERSION; SELECTIVELY RECONCILE TEST INTENT** | Both sides independently added this path after merge base. Main quality-projection test reaches a statically defective main `pipeline/api.py` ordering. Branch test suite/version and its API contract must be preserved; do not import the main file/test changes blindly. |
| `docs/PROJECT_CONTRIBUTION_EFFORT_LEDGER.md` | **OPTIONAL SUPPLEMENTARY RECORD** | Initial 2026-11-09 baseline only; exact cumulative hours and full history inventory explicitly NOT VERIFIED. If retained, update with evidence-backed current milestones; do not treat as a complete effort/time audit. |
| `docs/PROJECT_SESSION_HANDOFF.md` | **PRESERVE BRANCH HANDOFF; RECONCILE FACTS ONLY** | Branch handoff is current and now includes exact Core First proof, bounded integration findings and latest branch commits. Never replace it wholesale with main's handoff; selectively import only unique, verified facts with source/date/baseline. |
| `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A1_2026-11-11.md` | **PRESERVE BRANCH VERSION** | Main A1 text is stale against the formal owner-approved VPS + GitHub custody addendum in the controlling v1 contract. The addendum controls; retain joint-rollback limitation and NOT VERIFIED technical controls. |
| `docs/evidence/G0_52_D01_D14_CLOSURE_AUDIT_AND_S2_READINESS_2026-11-11.md` | **OPTIONAL SUPPLEMENTARY / DUPLICATIVE** | Same 2026-11-11 baseline and S2 BLOCKED verdict as branch G0.52 record. No new decision or authority. Branch G0.53 is the later package and remains NOT RATIFIED. See G0.52 reconciliation report. |
| `docs/evidence/P1_SSH_PREFLIGHT_CONTRACT_RUN_42793921622.md` | **HISTORICAL EVIDENCE ONLY** | Exact historical contract-only run; no authenticated SSH/VPS probe. Keep only as historical traceability; do not infer current VPS state. |
| `docs/evidence/PR140_FAIL_CLOSED_PROBE_FIX_20261110.md` | **HISTORICAL EVIDENCE ONLY** | Historical PR #140 source/fix notes. SSH Preflight was later retired; do not restore retired source/workflow/tests. |
| `docs/evidence/PR140_SOURCE_REVIEW_20261110.md` | **HISTORICAL REVIEW ONLY** | Review findings and exact historical SHAs remain provenance. PR #140 lifecycle later closed/merged and feature retired; do not use old blockers as current source status. |
| `docs/evidence/SSH_PREFLIGHT_RETIREMENT_2026-11-11.md` | **PRESERVE AS RETIREMENT AUTHORITY/EVIDENCE** | Records owner-approved retirement and deletion of SSH Preflight across scoped branches while preserving history. Do not resurrect script, tests, inputs or jobs. |
| `docs/evidence/T0_SIGNATURE_CONTRACT_FINAL_CONSISTENCY_REVIEW_2026-11-11.md` | **SUPPLEMENTARY REVIEW EVIDENCE ONLY** | Static same-session consistency review at exact historical blobs; explicitly not independent review and implementation remains blocked. It does not replace the controlling contract/addendum or qualify as independent assurance. |
| `docs/evidence/T0_T2_DEPLOYMENT_PARITY_EVIDENCE_RECONCILIATION_2026-11-10.md` | **HISTORICAL RUNTIME EVIDENCE ONLY** | Reconciles operator-provided 2026-11-09 evidence. Current deployed checkout/process/listener/config/freshness remain NOT VERIFIED. No new VPS probe authorized or performed. |
| `docs/reviews/t1/P1_38_SECOND_PASS_ADVERSARIAL_REVIEW_P137_2026-11-09.md` | **HISTORICAL SELF-REVIEW ONLY** | Explicitly same-session, not independent. Keep provenance; do not describe as third-party review or implementation acceptance. |
| `pipeline/api.py` | **DO NOT REPLACE BRANCH FILE** | Main quality_snapshot reads `core.sourceEvidence` before assigning `core`, causing likely `UnboundLocalError`. Branch version orders assignment before use and retains explicit Paper/T0 DB separation. Any selective feature port requires focused design, tests and exact-SHA CI. |

## Main-only commit clusters and dispositions

1. **Contribution ledger and handoff edits** — documentary. Retain only verified facts; preserve the current branch handoff.
2. **P1.38 review and T0→T2 parity reconciliation** — historical evidence with explicit non-independent/current-state limits.
3. **PR #140 SSH Preflight work, corrections, merge and retirement** — lifecycle is complete and feature retired. Preserve history/evidence; do not resurrect retired code or workflows.
4. **T0 signature contract/A2.2 Stage I documentation and workflow** — preserve the controlling owner-approved contract/addendum. The A2.2 Stage I workflow blob is identical on both sides; no execution is authorized by the Stage I decision absent separate approval.
5. **G0.52 D01–D14/S2 audit** — supplementary duplicate; branch G0.52/G0.53 records are the current documentary chain. S2 remains blocked.
6. **Common API quality projection change and test** — main-side code has the ordering defect; branch implementation is the safer baseline for this interface.

## Proposed integration order — not execution authority

1. Keep branch Core First implementation and exact-SHA proof as the candidate baseline.
2. Preserve branch Common API/Paper-T0 isolation; do not copy main `pipeline/api.py`.
3. Preserve branch Core workflow additions (Dual Ledger bootstrap and Kill Reset).
4. Keep branch T0 workflow as the richer candidate, but do not rely on it as complete until F-07/F-08/F-10 are addressed through an approved minimal change and exact-SHA validation.
5. Keep branch A1 and the formal owner-approved v1 contract addendum; reject stale main A1 wording.
6. Reconcile unique documentary records individually; retain historical SSH/T0-T2/P1.38 evidence with explicit provenance, not as current runtime/independent-review proof.
7. Re-run targeted tests and exact-HEAD CI only after approved source/workflow changes. Then perform a fresh merged-tree review and validation before any merge decision.

## Non-authorizations and status

- This map authorizes no merge, rebase, reset, cherry-pick, force-push, source replacement, workflow edit/dispatch, default-branch change, VPS/T0/runtime/database/provider/key access, AI execution, deployment, exchange connection or real order.
- Core First exact tested source SHA remains `ea8dc9159782a3da83cab2b84409698922bd281d` from workflow run #44272495963; the later evidence/handoff commits are documentation-only and are not represented as tested by that run.
- Workflow integration review: **PARTIAL — material findings identified**.
- Bounded main integration map: **PASS WITH CONDITIONS**.
- Full semantic review of all 85 main-side commits: **NOT COMPLETE**.
- Merged-tree validation: **NOT RUN**.
- Merge: **BLOCKED / NOT AUTHORIZED**.
- Dual-Strategy Intelligence / AI Strategy implementation: **DEFERRED**.
