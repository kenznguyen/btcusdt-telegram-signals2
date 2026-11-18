# Core First Independent Review — 2026-11-18

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Review branch: `feature/core-operational-proof-20261112`
- Reviewed branch HEAD: `ff74d10aba0bdd60c14bebbe07746452571213fb`
- Code/test SHA with successful operational CI: `50d6f775ff3c1cd9fe5a20144874f4ee5f4c2b95`
- CI run: [44256822798](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/44256822798)
- Artifact: `14405604108`
- Artifact SHA-256: `e0a0ef6bc491e63bc1886383c3983680532d06b2e416fbcf30c02578e0337367`
- Review type: static source review of selected Core, API, ledger, runtime recovery, and CI files; no source/test execution performed during this review.
- Verdict: **REQUEST CHANGES / MERGE BLOCKED**. The CI run remains valid evidence for its exact checked-out SHA, but it is not an independent approval of the branch for merge.

## 1. Review scope

Inspected:
- `pipeline/core_strategy.py`
- `pipeline/core_signal.py`
- `pipeline/api.py`
- `pipeline/decision.py`
- `pipeline/test_api.py`
- `pipeline/test_core_strategy.py`
- `paper_execution/ledger.py`
- `paper_execution/risk_control.py`
- `paper_execution/test_core_first_operational.py`
- `paper_execution/test_core_short_lifecycle.py`
- `paper_execution/test_partial_fill_process_crash.py`
- `paper_execution/test_account_risk_snapshot_read_only.py`
- `paper_execution/test_core_runner_ledger_integration.py`
- `core_runtime/continuous_runner.py`
- `core_runtime/paper_ledger_preflight.py`
- `core_runtime/api_facade.py`
- `.github/workflows/core-live-market-data-operational-proof.yml` (actual path: `.github/workflows/core-live-data-operational-proof.yml`)
- Core-First architecture and readiness documents.

## 2. Findings

### BLOCKER B1 — Branch history is not merge-ready

GitHub compare at review time:
- `main`: `6bff2aff91657238297848ef644a0cb4112ab428`
- Core branch: `ff74d10aba0bdd60c14bebbe07746452571213fb`
- Merge base: `f5b74affb8777953fa66d241784965fbb0e577ba`
- Compare reports branch **4,560 commits ahead and 85 commits behind** `main`.
- Compare response exposes at most 300 file entries for this very large history; this review did not establish a complete, line-by-line review of the entire proposed merge.
- No open PR targets `main` from this Core branch.

Impact:
- A merge would combine a very large divergent history and cannot be treated as a small Core-First increment.
- The Core code is not present on `main` (for example, `pipeline/core_strategy.py`, `pipeline/core_signal.py`, `paper_execution/ledger.py` and Core runtime modules are absent there).
- This is a merge-process blocker, not evidence that the Core code itself is incorrect.

Required:
- Do not merge, rebase, reset, force-push, or create a replacement branch in this review.
- First produce a reviewed, owner-approved integration plan that preserves the existing branch and accounts for the 85 commits on `main`; establish a bounded, auditable diff before any merge proposal.

### BLOCKER B2 — Core-First AI deferral is not enforced at the API boundary

Architecture decision `docs/architecture/CORE_FIRST_ARCHITECTURE_DECISION_2026-11-12.md` says AI Strategy is offline-research-only and must not participate in the paper-submit path while deferred.

Source inspection found:
- `pipeline/api.py:591-626`: `POST /v1/paper/evaluate` defaults an empty payload to source `AI`; the AI branch evaluates the AI decision and retains a call to `strategy_ledger.submit(..., strategy_id="AI_FREQAI")`.
- `pipeline/api.py:598-601`: if the Dual Ledger is not active, the code selects the legacy `ledger()` path rather than rejecting AI paper evaluation outright.
- `paper_execution/ledger.py:2473+`: the legacy writer accepts `AI_FREQAI` as a strategy owner when the Dual Ledger migration is not active.
- `pipeline/decision.py:217-219`: the current `decide()` call does not supply an `admission_context`, so the present evaluator returns WAIT with `AI_CALIBRATION_ADMISSION_CONTEXT_UNAVAILABLE` rather than generating an intent. This is a current fail-closed condition, not a permanent architectural boundary.
- `pipeline/test_api.py:372-394` still exercises independent Core/AI signal presentation; `pipeline/test_api.py:487-496` mocks a valid AI decision to test Kill Switch rejection.

Impact:
- The current production decision function does not issue an AI intent without trusted admission context, but the API and legacy-ledger submit path remain wired for AI paper submission.
- A future change that supplies admission context could activate AI paper submission without first changing the Core-First policy boundary or obtaining a separate owner decision.
- Empty evaluate requests currently select AI rather than Strategy Core, which is inconsistent with Core being the sole active paper strategy.

Required before Core-First merge:
- Make the API fail closed for AI paper evaluation while Core-First deferral is active; do not fall back to the legacy writer for AI.
- Make Core the only accepted/default paper evaluation source in this phase, or require an explicit Core source and reject AI/unknown sources.
- Retain AI offline research artifacts and tests as appropriate, but ensure no API/ledger route can create AI paper orders.
- Add regression tests proving AI paper evaluation is rejected even when a valid AI intent is injected/mocked, both with and without a ready Dual Ledger.
- Do not implement Dual-Strategy Intelligence as part of this correction.

### REQUIRED R3 — Core-First decision/readiness documents are stale

- `CORE_FIRST_ARCHITECTURE_DECISION_2026-11-12.md` still identifies a different active branch and says implementation was not started.
- `CORE_FIRST_READINESS_PLAN_2026-11-12.md` reports Core CI, Risk/Ledger CI, and Core-to-Risk integration as NOT RUN / NOT VERIFIED at its inspected SHA.
- Later exact-SHA evidence now exists at `50d6f775ff3c1cd9fe5a20144874f4ee5f4c2b95` and workflow run `44256822798`.

Required:
- Update these documents with the new evidence and explicit distinctions between deterministic fixture/CI PASS, real-market OOS NOT VERIFIED, operational runtime NOT AUTHORIZED, and live trading NOT AUTHORIZED.
- Keep synthetic funding/equity/owner-attestation fixture data clearly labeled as synthetic.

### REVIEW NOTE R4 — Workflow copies differ

- Branch workflow blob: `0c2d86d76d4d3281e3d7ffb9904a820cf30df547`.
- Main workflow blob: `1c0d9e7b6c8355264aa509342175d72931b64cc4`.
- Branch workflow includes the shared fixture path filters and focused three-test Kill Reset regression; main copy does not.
- Run `44256822798` was executed against the branch and is valid for the branch workflow/source SHA recorded in its logs.
- The workflow copy difference must be explicitly reviewed in any future bounded integration proposal; do not infer that main already contains the latest branch workflow.

## 3. Positive review observations

- Core producer uses closed, complete M15/H1 windows and emits no intent when the execution book is unavailable/invalid.
- Core entry sizing derives a 1% margin budget from account equity and the shared leverage policy; ledger admission independently enforces risk and exposure constraints.
- Dual Ledger readiness is checked before strategy-scoped Core/AI ledger construction.
- Kill Switch state is read inside the ledger write transaction; the risk latch blocks exposure increases while preserving permitted reductions.
- Continuous Runner validates immutable bundle provenance, claims cycles idempotently, records intent before execution, and uses reconciliation states after ambiguous failures.
- Partial-fill crash and concurrency tests are present in the reviewed test suite.
- These are static source observations, not market profitability or production-runtime evidence.

## 4. Verification boundary

- Existing exact-SHA GitHub Actions run `44256822798`: **PASS** as recorded in the handoff.
- This review session: no local checkout was available and no tests were executed here.
- Independent static review: **PARTIAL / REQUEST CHANGES** due to B1 and B2; not a merge approval.
- Real-market OOS profitability: **NOT VERIFIED**.
- VPS/runtime deployment: **NOT AUTHORIZED**.
- Live trading/real orders: **NOT AUTHORIZED**.
- Dual-Strategy implementation: **DEFERRED** pending Core-First closure and separate approval.

## 5. Next actions

1. Preserve the current branch; do not merge or rewrite history.
2. Obtain owner approval for the narrowly scoped API hardening in B2.
3. Implement regression-first on this same branch, retaining all fail-closed behavior.
4. Update the stale Core-First architecture/readiness documents with exact-SHA evidence.
5. Re-run the operational workflow on the final code SHA and record the artifact digest.
6. Reassess branch integration only after a bounded diff and independent review of the main divergence.
