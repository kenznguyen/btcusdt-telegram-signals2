# Main Integration Review — bounded pass 1 — 2026-11-18

## Scope and exact refs

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Reviewed target branch: `feature/core-operational-proof-20261112`
- Branch HEAD at review: `5002814e7ee298db99eb9c1e0e63a2988e89054a`
- Main HEAD at review: `6bff2aff91657238297848ef644a0cb4112ab428`
- Merge base: `f5b74affb8777953fa66d241784965fbb0e577ba`
- Compare status: **DIVERGED**
- Branch ahead / behind: **4,582 / 85**
- Main-only range: 85 commits; compare from merge base to main reports 16 changed paths (14 added, 2 modified).
- Review type: read-only, bounded integration review. No source edits, merge simulation, rebase, reset, workflow dispatch or runtime access.

## Main-only history grouped by subject

The 85 main-side commits are not 85 distinct changed source files. The commit subjects cluster into:

1. PR #140 read-only SSH preflight work: contract tests, fail-closed probe behavior, evidence corrections, merge/closeout, then later retirement of the workflow/script/tests.
2. T0 signature / trust-policy A2.2 Stage I: decision and contract documentation, isolated workflow and parser/evidence fixes.
3. D01–D14 closure / S2 readiness audit documentation.
4. Two recent Common API changes:
   - `6a21c4183432634437b5014a48da4140fed861a2` — `refactor(core-api): align Core quality projection with Bundle v1`.
   - `2b0c043e3e336ca79d639c91cb9ecd7078c280c7` — `test(core-api): require ephemeral preview bundle without journal`.
5. `6bff2aff91657238297848ef644a0cb4112ab428` — exposes the Core First operational proof workflow from main.

## Material findings

### F-01 — Main Common API has a statically confirmed ordering defect

- Main `pipeline/api.py`, `quality_snapshot()`: `core` is read to derive `t1_evidence` before `core = core_runtime_preview(timestamp)` is assigned.
- Exact main lines: first read at line 328; assignment at line 351.
- With ordinary execution, this path raises `UnboundLocalError` before returning the quality projection.
- Main `core_runtime/test_api_facade.py` adds `test_quality_projection_uses_bundle_preview_and_t1_book_evidence`, which invokes this function and should expose the defect when executed.
- This review did not execute main's test suite; classify as **STATIC REVIEW FINDING — HIGH CONFIDENCE**, not a test-run result.
- The reviewed branch version assigns `core = core_runtime_preview(timestamp)` before reading `core.sourceEvidence` (branch line 384 before line 385), avoiding this specific defect.

### F-02 — Do not replace branch `pipeline/api.py` with main's file

- Main's file is 629 lines; branch's is 716 lines and has independent safety/architecture differences.
- Branch has a `paper_db_path()` boundary requiring an explicit Paper DB path and rejecting aliases with canonical T0 storage. Main's version does not contain that helper.
- Branch's `quality_snapshot()` ordering is correct for the T1 evidence projection.
- Branch's Core preview projection preserves the explicit `riskDecision` field; main's projection omits it. The intended display/API contract for preview-only `NOT_EVALUATED` risk status should be confirmed rather than silently changed.
- Main's file is not a safe wholesale replacement. Any selective port requires a focused diff, tests and exact-SHA CI.

### F-03 — Common API tests differ

- Both versions contain the ephemeral, non-persistent preview contract and quality projection coverage.
- Branch test file has additional local test coverage and differs from main around the preview projection contract.
- Main's newly added quality projection test is expected to fail against main's current `quality_snapshot()` ordering in F-01.
- No main test run was performed during this review.

### F-04 — Workflow changes are not a safe wholesale copy

- Main `.github/workflows/core-live-data-operational-proof.yml`: 430 lines.
- Branch version: 449 lines and includes explicit dual-ledger bootstrap / Kill Reset regression steps and additional path coverage.
- The exact tested branch workflow passed in run [44272495963](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/44272495963); that does not validate main's workflow.
- Main `.github/workflows/t0-signature-a2-2-stage-i.yml` and branch copy have identical blob SHA `5fa94939181af5f1f33686c3444bc6f8a0326962`.
- Main `.github/workflows/t0-manual-validation.yml` and branch copy differ substantially in size and content; they require a separate gate-by-gate workflow review before any integration decision.

### F-05 — T0 signature amendment contains a governance-text conflict

- Main and branch versions of `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A1_2026-11-11.md` differ.
- Main text describes VPS + GitHub custody as a proposed/draft alternative pending owner ratification.
- Branch text records the owner-approved addendum and explicitly retains the joint-rollback limitation.
- Do not resolve this by choosing a file based on branch age alone. Verify the controlling owner decision/addendum and reconcile the wording before any merge.

### F-06 — Main contains an additional D01–D14/S2 audit record

- Main has `docs/evidence/G0_52_D01_D14_CLOSURE_AUDIT_AND_S2_READINESS_2026-11-11.md`; the exact path was not found on the reviewed branch.
- It states S2 readiness is BLOCKED / NOT READY and explicitly grants no implementation authority.
- This is useful governance evidence, but its baseline is another branch/source snapshot and it is a documentary audit, not an independent security review or runtime acceptance. Preserve as a candidate for later evidence reconciliation; do not infer it authorizes implementation.

## Integration disposition

- Main's 85-commit history is bounded to 16 changed paths relative to the merge base, but it is not semantically safe to merge automatically.
- **F-01 is a concrete main-side code defect** in the quality projection.
- **F-02 is a data-isolation boundary difference**: keep the branch's explicit Paper/T0 separation unless a reviewed equivalent is proven.
- **F-05 is an owner-decision wording conflict** requiring evidence reconciliation.
- Main workflow and T0 manual workflow differences still need full gate-by-gate review.
- The main-side PR140 SSH preflight lifecycle includes later retirement; do not resurrect the retired workflow/script/tests merely because their historical commits are in the range.
- No blanket cherry-pick, merge, rebase, reset, force-push, source replacement or workflow replacement is recommended.

## Status

- Bounded main-history inventory: **PASS** (85 commits / 16 changed paths identified).
- Targeted Common API source review: **BLOCKED for integration** by F-01; branch variant avoids the identified defect.
- Paper/T0 isolation comparison: **REQUIRES PRESERVATION / FURTHER REVIEW**.
- T0 signature governance reconciliation: **BLOCKED / NOT VERIFIED** until controlling owner addendum is checked.
- Workflow parity review: **PARTIAL / NOT VERIFIED**.
- Full semantic review of all 85 commits and merged-tree validation: **NOT COMPLETE / NOT RUN**.
- Merge: **BLOCKED / NOT AUTHORIZED**.

## Next bounded actions

1. Verify the controlling owner-approved T0 custody addendum and reconcile the two A1 document versions.
2. Complete the gate-by-gate comparison of the two T0 manual validation workflows and Core operational proof workflows.
3. Reconcile the unique G0.52 D01–D14/S2 audit record with current handoff/evidence.
4. Only after those reviews, prepare a proposed integration map. Do not execute merge or alter source/runtime without separate approval.
