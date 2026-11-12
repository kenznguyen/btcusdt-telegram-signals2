# AI Evaluate — Owner Authorization and Execution Boundary

Date: 2026-11-12 (Asia/Ho_Chi_Minh)
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/t0-centralized-data-feeder-p1-20261101
Authorization source: explicit owner approval in conversation on 2026-11-12 — “Phê duyệt triển khai cả ba nhóm.”
Baseline source HEAD: 945a263788bc92f712bc80f7aba3fa2185d75561

## Approved work packages

Owner authorizes implementation across all three previously identified groups:

1. OOS lineage/provider, real dataset collection and OOS evaluation.
2. Registry ACTIVE/revocation lifecycle, trusted-time provider, and trust-root/key creation and enrollment.
3. AI admission/leverage policy, including C_min, minimum sample count, freshness threshold and confidence-to-leverage mapping within the existing 1x–3x AI leverage domain.

This approval supersedes the earlier F6/GREEN-0 non-authorization for these three work-package categories, but does not waive their technical contracts, verification gates, evidence requirements or fail-closed behavior.

## Invariants and exclusions

- Work on the existing branch only; no parallel branch or PR.
- GitHub Actions first. No VPS creation, provisioning, runtime deployment or service activation under this authorization.
- No changes to T0, T1, T2 data/runtime contracts, Strategy Core, or completed AI Ledger CANCEL behavior.
- No database migration or canonical data mutation.
- Paper-only; no exchange execution, live trading or real orders. Keep AI_EXECUTION_ENABLED=false.
- Reuse the existing Shared Risk Engine and Kill Switch; preserve the 1% account-equity margin budget and 1x–3x AI leverage bounds.
- Do not treat fixtures, GitHub timestamps, self-asserted registry states or unsigned caller data as trusted evidence.
- Production private keys must not be committed, placed in GitHub artifacts, or generated into an unapproved custody location. Test keys remain ephemeral and test-only.
- Numerical policy values must be derived from verified evidence and exposed for owner review; this authorization does not permit inventing unsupported thresholds or claiming statistical validity without real OOS evidence.
- No new dataset schema may be inferred from the missing T0_M15_H1_DATASET_BUNDLE_V1 bundle. If no canonical producer/contract/payload can be verified, stop that sub-workstream and report the exact contract decision required.

## Baseline inventory at authorization

- Exact branch HEAD: 945a263788bc92f712bc80f7aba3fa2185d75561.
- Recursive Git tree: 992 entries, not truncated.
- Candidate T0_M15_H1_DATASET_BUNDLE_V1 schema, payload and producer: not identified in tracked tree; prior WP0 inventory reports the same gap at earlier HEAD f012305b9c13d0deb7ec1bdfeda22a2affb7a5d2.
- Existing pipeline/oos_evaluation.py is a pure structural validator; it explicitly does not establish authoritative lineage, sample-level embargo, reproducibility, trusted time, statistical acceptability or admission.
- Existing pipeline/calibration_registry.py verifies exact manifest bytes, Ed25519 signature against a pinned public key and artifact bytes; it does not establish registry promotion/revocation, trusted time, OOS quality or admission.
- Existing pipeline/test_oos_evaluation.py and pipeline/test_ai_calibration_registry.py are present.
- Existing .github/workflows/ai-strategy-contract-red.yml supports workflow_dispatch and exact-branch push triggers; it isolates paper-only environment and runs OOS, registry, decision and AI strategy contracts.
- risk_policy.py currently defines Core leverage 13x and shared order margin budget 1%; no versioned AI confidence-to-leverage policy is defined.
- Existing GREEN-0 inventory identifies no authoritative BTCUSDT tick/lot/min-notional provider and no AI DCA trigger contract. AI DCA must remain disabled unless separately specified and verified.

## Initial disposition

- Authorization: APPROVED for all three groups.
- OOS implementation: BLOCKED at canonical dataset contract/payload discovery; no substitute schema or synthetic evidence permitted.
- Registry/trusted-time/key lifecycle: implementation authorized, but provider selection, custody boundary, trust-root enrollment evidence and operational secrets boundary must be established before any production key or external trust operation.
- AI numerical policy: implementation authorized; policy interface and evidence-driven evaluation may proceed, but numerical admission thresholds cannot be asserted until valid OOS evidence and an explicit owner policy disposition exist.
- Runtime/VPS: NOT AUTHORIZED by this approval; no VPS required for initial GitHub Actions work.

## Evidence discipline

For each implementation increment record source commit SHA, exact workflow run and checked-out SHA, job conclusions, test counts, artifact ID/name/digest/expiry, and whether artifact payload bytes were independently downloaded and re-hashed. Use PASS, CONDITIONAL PASS, BLOCKED, NOT RUN and NOT VERIFIED precisely. Preserve prior evidence; do not promote structural checks to trusted admission.
