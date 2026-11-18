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
