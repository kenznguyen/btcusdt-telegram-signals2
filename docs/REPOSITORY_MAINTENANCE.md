# Repository maintenance and safety rules

Last reviewed: 2026-11-18  
Repository: `kenznguyen/btcusdt-telegram-signals2`

## Protected assets and product surfaces

- T0 is an independent data asset. Preserve its canonical data, storage contracts, provenance and evidence.
- Strategy Core and paper/simulated execution: preserve RSI + ADX + Smart DCA behavior unless a separately approved implementation scope says otherwise.
- Core API/runtime, risk controls, ledgers and account/risk contracts.
- Telegram scanner/command bridge and Python backtest/dashboard.
- Android application source, signing configuration and release compatibility.
- Git history, tags, workflow evidence, test artifacts and audit reports.

Repository source or workflow presence is not proof of deployment or runtime readiness.

## Safety boundaries

- Paper/simulated operation only. No live order placement, live exchange execution or real trading.
- Keep `AI_EXECUTION_ENABLED=false`.
- Do not connect to an exchange, open or mutate the canonical T0 database, start a Feeder, synchronize market data, deploy services or change VPS/runtime configuration without separate explicit approval.
- Do not expose, rotate, delete or rewrite credentials/secrets as part of documentation cleanup.
- Preserve T0 independently; do not combine its lifecycle with ordinary repository/documentation cleanup.

## Branch and history policy

- `main` is the repository default branch. Make only scoped, reviewed, fast-forward changes based on its freshly read HEAD.
- Continue work on the existing authorized branch for an active workstream. Do not create parallel branches/PRs for the same task or introduce branch divergence.
- `feature/core-operational-proof-20261112` is a separate Core First workstream and is not to be treated as merged into `main`. Do not merge, reset, rebase, cherry-pick, force-push or reconcile its divergent history without a separately approved plan.
- Preserve all branch refs, tags and Git history during routine cleanup. No branch deletion or history rewrite.
- Backup/restore refs are protected and must never be deleted as routine maintenance.

## CI and evidence rules

- GitHub Actions is the default CI. Codemagic is fallback-only; use it only after recording a concrete GitHub Actions blocker and receiving explicit approval.
- Before changing a workflow, inspect its current triggers, jobs, permissions, concurrency, environment and artifact behavior.
- Before dispatching a workflow, obtain approval for the exact workflow, ref, gate and side effects. A documentation-only task does not authorize unrelated workflows.
- Record exact source SHA, workflow/run ID and event, checked-out SHA, job conclusions, test summary, and artifact ID/name/digest where present.
- A result applies only to the exact source and execution context demonstrated by evidence. If identity, test execution or artifact readback is missing, record **NOT RUN** or **NOT VERIFIED**, not PASS.
- Never claim runtime, deployment, Android installation, exchange connectivity or live-trading readiness from unit tests or static review.

## Documentation lifecycle

- Root README describes the repository as it exists on `main`, not an unmerged feature branch or an assumed deployment.
- `docs/PROJECT_SESSION_HANDOFF.md` is the restart point. Put the current main-branch snapshot at the top; preserve historical entries below it.
- `docs/README.md` is the document index. Mark documents ACTIVE, HISTORICAL, SUPERSEDED or NOT VERIFIED as appropriate.
- Preserve evidence reports and historical handoffs. Prefer an explicit supersession notice or archive copy over deletion.
- Remove a file only when its content is demonstrably obsolete, no source/workflow/docs/tests link to it, it is not evidence or a decision record, and the removal is within the approved scope. This cleanup found no file that met all deletion conditions.
- Do not edit source code, tests, workflows, runtime configuration, T0 data or credentials during documentation-only maintenance.

## Release gate — Android

1. Inspect the exact candidate source and feature parity: scanner, symbol switcher, M15/H1, indicators, alerts and Strategy Monitor.
2. Run the required Android unit tests and debug build on the selected source branch.
3. Use the existing signed release workflow and verify the exact checked-out source SHA.
4. Confirm release build, signing alias, applicationId/versionCode compatibility and artifact.
5. Verify install-over-existing-app before claiming release readiness.
6. Never assume `main` is the release source merely because it is the default branch; inspect the workflow's selected source branch and current feature parity.

## Known repository state at review

- Signal Scanner workflow is manual-only (`workflow_dispatch`); scheduled scanning is disabled.
- Core API quality snapshot on `main` has a critical statically confirmed local-variable ordering defect. See `docs/evidence/MAIN_CORE_API_QUALITY_SNAPSHOT_STATIC_REVIEW_2026-11-18.md`. No runtime test was run by that review.
- Core First work on `feature/core-operational-proof-20261112` is separate from `main`; branch status must not be copied into main's handoff.
- SSH Preflight was retired on 2026-11-11. Its source/test/workflow removal and historical reports remain part of Git history/evidence. Do not restore it as routine maintenance.

## Cleanup disposition

The 2026-11-18 documentation cleanup preserved source, workflows, branches, tags, evidence, history, T0, data and runtime. The previous root Telegram README was copied to `docs/archive/README_TELEGRAM_LEGACY_2026-11-18.md` before the root README was refreshed. No source, workflow, evidence or branch was deleted.
