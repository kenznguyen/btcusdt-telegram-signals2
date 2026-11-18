# Main documentation cleanup — 2026-11-18

## Work record

- Work ID: `MAIN-DOCUMENTATION-CLEANUP-2026-11-18`
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Target branch: `main`
- Owner approval: full documentation and obsolete-content cleanup; preserve Git history/evidence; keep source, T0, data and runtime unchanged; avoid branch divergence.
- Baseline main SHA: `ef5bdee41430a9f4acd86e104ad60f44a1386f69`
- Main SHA immediately before this report: `48177f7a73c0f11ae56a466958207809f0fff904`
- Date: 2026-11-18 (Asia/Ho_Chi_Minh)

## Scope executed

1. Preserve the previous root README verbatim in `docs/archive/README_TELEGRAM_LEGACY_2026-11-18.md`, with a notice that its operational instructions do not establish current deployment state.
2. Replace the root README with an evidence-bounded map of the current repository surfaces, operating boundaries, known main-side Core API defect, and links to current guidance.
3. Rewrite `docs/REPOSITORY_MAINTENANCE.md` to align branch, CI, T0, paper-only, Android release, evidence and documentation lifecycle rules.
4. Add `docs/README.md` as an index classifying active guidance, historical evidence, retired material and archive content.
5. Update `docs/PROJECT_SESSION_HANDOFF.md` with a dated current-main snapshot at the top while retaining the previous handoff body unchanged below it.
6. Preserve all historical evidence, source files, tests, workflows, branches, tags and Git history.

## Audit findings

- The old root README primarily described the Telegram/Render/OKX notification surface and did not give a balanced map of the current repository's Android, backtest, T0, pipeline and Core runtime paths.
- `.github/workflows/signal-scan.yml` is manual-only (`workflow_dispatch`); scheduled scanning is disabled.
- `docs/evidence/MAIN_CORE_API_QUALITY_SNAPSHOT_STATIC_REVIEW_2026-11-18.md` documents a critical static ordering defect in `main:pipeline/api.py` `quality_snapshot()`: local `core` is read before assignment. The cited review did not run the test; runtime failure remains NOT RUN.
- Core First branch `feature/core-operational-proof-20261112` remains separate and must not be described as merged or operational on `main`.
- SSH Preflight was retired on 2026-11-11. Historical reports were retained and classified as historical; no retired script/test/workflow was restored.
- No candidate file met all safe-deletion conditions. Files were either active source/configuration, workflows with extant triggers, decision/architecture records, or historical evidence. Accordingly, **zero files were deleted**. Obsolete instructions were superseded or archived instead.

## Commit sequence

| Commit | Change |
|---|---|
| `d8a5d036ee8fc4b456898f4824a561700140be5d` | Preserve previous root README in archive |
| `9fa3426a6d6c6e8576d3913ef6415c572f324bd5` | Refresh root README |
| `3f998b30fd7d9e54ecb70799c4b59001d275de53` | Modernize repository maintenance policy |
| `48177f7a73c0f11ae56a466958207809f0fff904` | Add documentation index |

The handoff update and this report are separate sequential commits on the same existing `main` branch. No branch was created.

## Validation and evidence

- Source scope: documentation-only.
- Source code, tests, workflows, runtime configuration, T0 data/database, VPS, credentials/secrets, exchange connectivity and trading: **UNCHANGED / NOT TOUCHED**.
- Git branch topology: no branch creation/deletion, merge, rebase, reset, cherry-pick, force-push or history rewrite.
- Test/build/workflow execution: **NOT RUN**; this scope changes documentation only and does not authorize unrelated CI workflows.
- Artifact: **NONE**; no workflow was dispatched and no artifact was produced.
- Markdown validation: GitHub readback and link-target existence checks are the applicable validation. Any runtime or behavior claim remains outside this cleanup's evidence.
- Independent review: **NOT PERFORMED**. This record is not an independent security or code audit.

## Final status

- Documentation refresh: **PASS**, subject to final exact-SHA GitHub readback.
- Historical evidence preservation: **PASS** by archive/readback and no deletion.
- Source/T0/data/runtime preservation: **PASS by scoped change set**, not a runtime inspection.
- Tests/CI/build: **NOT RUN**.
- Runtime/deployment/Core operational readiness: **NOT VERIFIED**.
- Branch divergence avoidance: **PASS** — all changes are sequential commits on the existing `main` branch only.
- No live trading or exchange action occurred.

## Remaining limits and next step

- The main-side Core API static defect remains open and is not repaired by this documentation task.
- Do not merge or copy the separate Core First branch into `main` as part of cleanup.
- Next step: perform final GitHub readback of the cleanup files and verify the exact final `main` SHA. Any source repair, workflow dispatch, branch reconciliation or runtime action requires its own explicit scope and approval.


## Final GitHub readback — 2026-11-18

- Main HEAD read back before this final evidence update: `b9fecd23e06f1e122da7e98949fc76d670c8c2ab`.
- Compare from baseline `ef5bdee41430a9f4acd86e104ad60f44a1386f69`: **6 commits ahead / 0 behind**; exactly six changed paths:
  - `README.md` (modified)
  - `docs/PROJECT_SESSION_HANDOFF.md` (modified)
  - `docs/README.md` (added)
  - `docs/REPOSITORY_MAINTENANCE.md` (modified)
  - `docs/archive/README_TELEGRAM_LEGACY_2026-11-18.md` (added)
  - `docs/evidence/MAIN_DOCUMENTATION_CLEANUP_2026-11-18.md` (added)
- Archive integrity: archived README content after its preservation notice matches the baseline root README exactly.
- Handoff integrity: the entire original `docs/PROJECT_SESSION_HANDOFF.md` body is an exact unchanged suffix after the new current-main snapshot.
- All six documented link targets exist on `main`.
- No source, test, workflow, T0, runtime, credential, branch, tag or historical evidence path was changed or deleted.
- Final documentation readback: **PASS**. Tests/build/workflow remain **NOT RUN**; no artifact exists.
- The final handoff update is committed immediately after this evidence update; its exact commit becomes the final main HEAD and is recorded in the conversation result.


## Follow-up bounded cleanup audit — 2026-11-18

- Audit target: `main`; source HEAD at audit start: `82412ec5c887598c2dac5e775f3ee46ecddcc26c`.
- Read-only scope: verify the immediately preceding one-file removal, re-check candidate workflows and their branch-side dependencies, and classify remaining obvious cleanup candidates.
- Removed from main in the preceding approved increment: `market_data/test_write_gateway.py`; deletion commit `82412ec5c887598c2dac5e775f3ee46ecddcc26c`. The T0 branch copy remains at blob `131880b9110f5bb5780b411d348eae19acb6e14e`.
- Correction to the earlier dependency inventory: its statement that main contains `market_data/test_write_gateway.py` is historical and no longer current after the deletion. Main no longer contains that test or the T0 implementation package; do not interpret its absence as permission to remove T0 branch content.
- `.github/workflows/paper-writer-isolation-red.yml`: KEEP / REVIEW. Its target branch `feature/t0-paper-writer-isolation-red-20261102` exists and contains `paper_execution/test_writer_isolation_red.py` (blob `89d6ff98e26339c398537e74a569c4b103af0a88`). The target test is absent on main and on the workflow's separately named PR base branch; retain pending branch/PR lifecycle review.
- `.github/workflows/core-live-data-operational-proof.yml`: KEEP. It is the Core First workflow; its corresponding implementation/tests exist on `feature/core-operational-proof-20261112`. Main's copy is not evidence that Core First is merged or operational on main.
- `.github/workflows/core-api-quality-regression.yml` and `ci/test_core_api_quality_snapshot.py`: KEEP. They provide the intentionally narrow main-side regression boundary; they do not prove full Core/T0 integration.
- `.github/workflows/signal-scan.yml` and `.github/workflows/telegram-command.yml`: KEEP / LEGACY ACTIVE. Manual scanning and Telegram/backtest command paths remain explicitly documented in the current README; workflow triggers still exist. No retirement authorization or migration evidence found in this audit.
- Historical reports, architecture decisions, archive content, active Android/backtest sources and other workflows: KEEP pending a separate dependency/ownership audit.
- Result: no additional DELETE candidate met the required conditions. No further files were deleted or modified in this audit. No tests, builds, workflows, runtime, T0 database, Feeder, VPS, exchange or trading paths were executed or accessed.
- Status: read-only inventory PASS for the inspected paths; full repository-wide dependency audit NOT VERIFIED. CI/tests NOT RUN; artifact NONE.
- Next: only continue with a bounded candidate review where ownership, branch/PR triggers, references and replacement/migration evidence can all be established. Any further deletion requires a separate explicit approval.
