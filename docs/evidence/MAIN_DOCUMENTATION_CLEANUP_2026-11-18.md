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


## Follow-up workflow lifecycle audit — 2026-11-18

- Repository/branch: `kenznguyen/btcusdt-telegram-signals2:main`.
- Source baseline before this documentation increment: `95469069fdcf78c0567e3b5971e2eee8a440e94a`.
- Scope: read-only inventory of all 13 workflow files under `.github/workflows/`; inspect triggers, branch filters, key source references and whether named branches still exist. No workflow execution-history API data was available through the connected GitHub read surface; recent run frequency therefore remains NOT VERIFIED.
- KEEP — `android-live-chart-ci.yml`: manual branch selector; all three configured source branches were found. Android project paths are present in the repository.
- KEEP — `android-release-pair.yml`: manual exact-SHA paired APK release with paper-only/credential-empty checks and artifact verification. Its required branch `feature/p5-4-1-post-merge-validation-20261103` exists, and `ci/verify-android-release-pair.py` exists on that branch (blob `0f01375a41773af881a697404949be037c206728`).
- REVIEW — `android-release.yml`: older single-APK release workflow overlaps in purpose with the stricter paired release workflow, but it has different branch inputs and output contract. Configured branches still exist. No retirement/migration decision or evidence establishes it as redundant; do not delete.
- KEEP — `dashboard-backtest.yml`: manual backtest workflow; `backtest.py` exists on main (blob `1ad441dbfd18498adefea3776b60a0797ac3367a`).
- KEEP — `signal-scan.yml` and `telegram-command.yml`: manual/explicit trigger workflows; `bot.py` (blob `9151c61165d5ce9bcfd90f800b4f56f016347d6f`) and `telegram_commands.py` (blob `558af67f20c4191ad27d50031590beacaacd1c45a`) remain on main. The scanner is manual-only; telegram-command also has a push trigger on `.github/backtest-trigger.txt`.
- KEEP — `core-api-quality-regression.yml`: main push-path regression and manual dispatch; retain as the narrow main-side test boundary, not full Core integration proof.
- KEEP — `core-live-data-operational-proof.yml`: branch-filtered to `feature/core-operational-proof-20261112`; branch remains present. Do not interpret its presence on main as Core First merged or runnable on main.
- KEEP — `p1-8-synthetic-evidence.yml`: push-filtered to T0 branch; branch exists and `synthetic_evidence/test_generator.py` exists there (blob `4a0b677b0260d1a167d515ee82de928774149ab4`).
- KEEP / REVIEW — `paper-writer-isolation-red.yml`: push source branch and PR base branch both exist; test file exists on push branch (blob `89d6ff98e26339c398537e74a569c4b103af0a88`). No deletion.
- REVIEW — `p5-3-11-g2-integration-green.yml`: reusable via `workflow_call` and manual dispatch, but its test commands reference T0 implementation modules absent from main (for example `market_data/test_gateway_runtime.py`). Caller references and branch-side execution context were not fully established; preserve pending caller/dependency trace.
- REVIEW — `t0-signature-a2-2-stage-i.yml`: manual-only and requires `t0_signature_stage1/tests`, which was not found on main or confirmed on the inspected T0 branch. GitHub code search surfaced only the workflow itself. This is a potential orphan/stale workflow, not a deletion authorization; locate historical source/owner and check all refs before any retirement.
- KEEP / REVIEW — `t0-manual-validation.yml`: manual-only multi-gate workflow. Some gates reference T0 packages absent from main; intended execution ref/branch and the current authoritative T0 gate set need confirmation. Preserve T0 branch and workflow until that is reconciled.
- No workflow deleted or edited. No CI/test/workflow run was started. No runtime, database, Feeder, VPS, exchange, AI execution or live order accessed.
- Status: workflow inventory PASS for all 13 files; branch existence checks PASS for configured branches queried; workflow run recency/caller graph NOT VERIFIED; test/CI NOT RUN; artifact NONE.
- Next: inspect only the three REVIEW groups (`android-release.yml`, `p5-3-11-g2-integration-green.yml`, `t0-signature-a2-2-stage-i.yml`, plus T0 manual gate ref selection) with history/caller evidence. No deletion without separate explicit approval.


## Follow-up REVIEW workflow trace — 2026-11-18

- Scope: read-only inspection of workflow definitions, selected branch refs, PR history/diffs and reusable-workflow callers. No workflow was dispatched and no source/workflow was modified.
- `.github/workflows/android-release.yml` blob `a9db1582856cf730893bdb7e60f992775469fe81`: legacy manual single-APK build. Its configurable source branches remain present. Its output is one signed release APK.
- `.github/workflows/android-release-pair.yml` blob `b6f6b3deccc01f27fb3c00b0bb5657033508be5c`: separate manual workflow pinned to `feature/p5-4-1-post-merge-validation-20261103`, requires caller-supplied exact SHA equal to selected branch HEAD, builds regular host + parallel .paper APKs, verifies identity/signer parity and paper-only environment, and uploads paired evidence. The two release workflows have materially different source-selection and output contracts; classify both KEEP. No release workflow deletion is justified.
- `.github/workflows/p5-3-11-g2-integration-green.yml` blob `3b75fdbf34768a315e5ed025b2ba0015ce138b17`: supports both `workflow_call` and `workflow_dispatch`. Caller graph is confirmed by merged PR #127, whose P5.4.1 orchestrator invokes it as job `g2` via `uses: ./.github/workflows/p5-3-11-g2-integration-green.yml`. PR #127 merge commit: `135ef7b69e8314b0b78e68c7f6fd41af34ca99e3`; PR head `76fa59a5c3e0256e40e889d27f2b73f74aa89532`. It is not orphaned. Its test commands require T0 modules absent from main, so preserve it as a reusable branch-context gate; do not dispatch on main as if main contained those packages.
- `.github/workflows/t0-manual-validation.yml` blob `e4d5ecc712bf590d5b4f7587fa649cbc94d4f8e2`: manual-only gate selector; checkout is `github.sha`, therefore the selected dispatch ref determines which T0 implementation tree is tested. The current gates include final runtime config, P3 components, Kraken Spot and TimescaleDB. PR #126 documents the T0 CI migration and branch-context design. Keep; no evidence supports retirement. Main's missing T0 modules mean a main dispatch is not equivalent to a T0 implementation-branch validation.
- `.github/workflows/t0-signature-a2-2-stage-i.yml` blob `5fa94939181af5f1f33686c3444bc6f8a0326962`: PR #141 introduced the manual workflow (merged as `eed06ee653c5594f77caeb66156d30aae8ca5875`, source head `1bd498e69585bdaf7b831369cc0d2283e87a02a3`). Its review identified that `t0_signature_stage1/tests` is absent from the workflow's checked-out tree. PR #142 (merged as `8ed3be3707560bdb3930479c5e552d3e03a42fd4`, source head `a90ce5c6dabe88e9a5f9cc846f99c8df94e3ff77`) attempted to fix the unittest summary parser but the review identified another regex escaping defect. The package directory was also not found on the inspected fix branch. No Stage I workflow execution or successful artifact evidence was established. Classify BLOCKED / likely stale, not yet DELETE: package ownership/history and any intended external source ref must be confirmed before retirement.
- Status: caller trace PASS for G2; release workflow distinction PASS; T0 manual branch-selection semantics PASS; Stage I executable dependency NOT VERIFIED / BLOCKED. Workflow runs/history beyond the cited PR records NOT VERIFIED. Tests/CI NOT RUN; artifacts NONE. No T0 runtime/database/Feeder/VPS/exchange/trading access.
- Recommendation: KEEP both Android release workflows, G2 reusable workflow and T0 manual validation. Retain Stage I workflow temporarily as BLOCKED pending owner/source provenance confirmation; do not delete without separate explicit approval.


## Stage I provenance follow-up and review correction — 2026-11-18

- Read-only refs inspected: `main`, `chore/t0-signature-stage-i-workflow-main`, `fix/t0-stage-i-unittest-summary-parser`, and `feature/t0-centralized-data-feeder-p1-20261101`.
- PR #141 changed only the workflow file; its head `1bd498e69585bdaf7b831369cc0d2283e87a02a3`, merge `eed06ee653c5594f77caeb66156d30aae8ca5875`. The workflow-only branch does not contain `t0_signature_stage1/__init__.py` or `t0_signature_stage1/tests/test_stage_i.py`.
- PR #142 changed only the workflow file; its head `a90ce5c6dabe88e9a5f9cc846f99c8df94e3ff77`, merge `8ed3be3707560bdb3930479c5e552d3e03a42fd4`. The parser regex in the merged workflow contains the expected single regex escape for each token (`\\d` and `\\.` in source representation); direct source inspection confirms the pattern accepts both timed unittest summaries and singular/plural test counts. The earlier characterization that the merged regex itself still had a doubled-escape defect was incorrect and is withdrawn. The review comment's concern is not reproduced by the merged file as fetched.
- The required Stage I package/test file was not found on `main`, the workflow-introduction branch, the parser-fix branch, or the inspected T0 centralized-data branch. Repository-wide history search for `t0_signature_stage1` returned no commits; this search is not a proof that no unindexed or deleted historical source exists.
- Commit-associated workflow-run lookup for the two PR merge commits returned no PR-triggered runs. This API view is limited to PR-triggered runs and does not establish whether manual dispatch runs ever occurred. No manual run history/artifact was verified.
- Updated assessment: workflow is **BLOCKED by missing executable package dependency** on the inspected refs. Parser correction in PR #142 is **PASS by static source inspection only**. Runtime execution, test count, artifact production and manual run history remain **NOT VERIFIED**.
- Recommendation: do not delete yet. The workflow is currently unusable on the inspected refs, but first confirm whether the intended Stage I package exists in another repository/ref or was intentionally retired. No source/workflow deletion or edits authorized/performed. T0 runtime/data/VPS/Feeder/exchange/trading untouched.


## Stage I provenance correction — 2026-11-18 (supersedes prior missing-package finding)

- A follow-up read-only inspection corrected a path-selection error in the prior audit. The earlier check looked for `t0_signature_stage1/tests/test_stage_i.py`, but the actual test modules are `test_primitives.py` and `test_verdicts.py`; the workflow uses the broader `test_*.py` discovery pattern.
- Confirmed on current branch ref `feature/t0-centralized-data-feeder-p1-20261101`, exact HEAD `eb91528bab2b994f283dbe34cd7b0bcbfe406cb5` (branch commit page readback). The earlier Stage I handoff commit is `e7273e918f254bd17a3ce997bb722e8d4e36d029`; all listed Stage I blobs were fetched using the current branch ref:
  - `t0_signature_stage1/__init__.py`: blob `de3841295124c36cd366a4ff138c42ada303b688`.
  - `t0_signature_stage1/primitives.py`: blob `91496d70a67d12525b8399b46aeb1318693b17ee`.
  - `t0_signature_stage1/verdicts.py`: blob `600c49865279e03ef28466f267a6bf0b57176aa1`.
  - `t0_signature_stage1/tests/__init__.py`: blob `4beea581f1e3cd514e6a085290f7f4dffb47aea9`.
  - `t0_signature_stage1/tests/test_primitives.py`: blob `8e47af0bb98cae6e8501c609c97259ebc5e0c78f`.
  - `t0_signature_stage1/tests/test_verdicts.py`: blob `d37ab48b0455d788bd5c87398281420a7aa121d8`.
- Provenance: source/test addition commit `40b338336fcad59f058fac320bffe6182b4485f8`; post-amendment self-review document blob `e44273248ef7ee68898a90e1fdfb1cd6a0a6c6dc`. The self-review records 23 primitive test methods + 11 fixture/verdict test methods = 34, but explicitly states the exact repository suite and compile check were NOT RUN after the latest source change; Python 3.12 parity NOT VERIFIED; independent review NOT PERFORMED; G3 NOT ESTABLISHED.
- Workflow `.github/workflows/t0-signature-a2-2-stage-i.yml` is present on both `main` and the T0 branch with blob `5fa94939181af5f1f33686c3444bc6f8a0326962`. It compiles `t0_signature_stage1`, discovers `test_*.py` under `t0_signature_stage1/tests`, checks empty DB/exchange credentials and `AI_EXECUTION_ENABLED=false`, and uploads a Stage I evidence artifact. The actual run/dispatch history and artifacts remain NOT VERIFIED.
- Corrected status: package/test dependency provenance on the inspected T0 branch **PASS (static GitHub readback)**; workflow path compatibility **PASS (static inspection)**; test execution, compile execution, Python 3.12 parity, manual dispatch history and artifact production **NOT VERIFIED**. The previous claim that the package was absent from the inspected T0 branch is withdrawn.
- Scope remained read-only: no workflow dispatch, test/build execution, source/workflow edit or deletion, branch mutation, T0 runtime/database/Feeder/VPS/exchange/trading access.
- Recommendation: retain the Stage I workflow as a valid manual branch-context gate, not an orphan. Do not dispatch without separate owner approval; if approved later, select the exact T0 branch ref and record the checked-out SHA, run, job results and artifact identity.


## Cross-branch functional overlap audit — 2026-11-18

- Scope: read-only static comparison of selected same-purpose application surfaces on `main` and `feature/t0-centralized-data-feeder-p1-20261101`. This is a targeted overlap pass, not a complete repository-wide symbol/dependency graph.
- Refs: main HEAD at audit start `fb26b5cb8c7184c735a170e139bf0935367ce337`; T0 branch current HEAD readback `eb91528bab2b994f283dbe34cd7b0bcbfe406cb5`. The branch compare reports a heavily diverged history (main 122 commits behind; branch 3,437 commits ahead relative to this compare base); do not merge, rebase or bulk-delete based on path overlap.
- **Confirmed functional overlap — Strategy Core logic:**
  - Main `bot.py`, blob `9151c61165d5ce9bcfd90f800b4f56f016347d6f`, contains RSI/ADX indicators, M15 RSI-cross + closed-H1 ADX directional entry rules, TP, DCA and soft-stop logic; it is a signal-only Telegram bot surface.
  - T0 branch `pipeline/core_strategy.py`, blob `c14e76f2cecb9f8aca54db263ded1ff17881cb24`, explicitly states that its rules mirror the signal-only `bot.py` implementation and implements RSI/ADX/Smart-DCA as a native Strategy Core producer.
  - Assessment: strategy rule logic is duplicated/migrated across the two refs, but the files are not drop-in replacements. `bot.py` also owns legacy Telegram/reporting and signal delivery behavior; `core_strategy.py` emits a versioned strategy intent under the paper architecture. **Candidate for future consolidation only after Core First acceptance and parity evidence. Do not delete or rewrite either file in this cleanup.**
- **Confirmed functional overlap — common API server:**
  - Main `pipeline/api.py`, blob `b6f017f603fecd242ba47a83fff387f8594bca2e`, and branch `pipeline/api.py`, blob `d0217944bbfa9b864b0f259e0091daf9a989d180`, both implement the common read API and paper controls and expose overlapping route families including `/v1/system`, `/v1/candles`, `/v1/order-book`, `/v1/intelligence`, `/v1/decision`, `/v1/signals`, and paper endpoints. The branch variant imports/uses the dedicated `pipeline.core_signal` adapter and has different signal/paper event handling.
  - Assessment: same module and service responsibility with divergent implementation state, not two independent files within one checkout. Keep branch-specific implementation and main-specific implementation isolated; no file replacement or cherry-pick implied.
- **Same filename, different responsibility — not a duplicate:**
  - Main `app.py`, blob `198c373b1008a2a53e74dd43d7c2c3f8f6343c83`, is the Telegram webhook/dashboard and GitHub Actions backtest-dispatch surface.
  - Branch `app.py`, blob `760d6d8e8a8680160df97f030931fda256205072`, is a T0 feeder health/dashboard surface using `HealthEvaluator`. Do not treat these as interchangeable or delete one because the paths match.
- **Related research/backtest, not proven duplicate:**
  - Main `backtest.py`, blob `1ad441dbfd18498adefea3776b60a0797ac3367a`, imports `bot.py` and simulates its RSI/ADX/Smart-DCA entry, TP and DCA rules.
  - Branch `backtest_rsi_percent_b_h1_adx.py`, blob `4765c53c358b1091a6619cad6d2b37a3f1751520`, is an independent RSI-%b / closed-H1 ADX research backtest with different entry/exit definitions and assumptions. It is not a drop-in duplicate of main `backtest.py`.
- **No same-path T0 package duplication on main in the checked paths:** `market_data/api.py`, `market_data/storage.py`, `market_data/feeder.py`, `pipeline/core_strategy.py`, `pipeline/core_signal.py`, `pipeline/decision.py`, `paper_execution/risk_control.py` and `paper_execution/ledger.py` were not found on main at the checked ref, while their branch versions exist. This is absence on main, not authorization to copy or delete branch content.
- Disposition:
  - KEEP: both `app.py` files (different responsibilities); both backtest surfaces (different strategy definitions); branch T0 package and paper execution modules.
  - REVIEW / consolidation candidate: `bot.py` Strategy Core rules versus `pipeline/core_strategy.py`; `pipeline/api.py` cross-ref implementation divergence.
  - No file deleted, edited, renamed or moved. No tests, build, CI, workflow, runtime, T0 DB/Feeder/VPS, exchange or trading action performed.
- Status: targeted static overlap inspection **PASS**; complete repository-wide functional duplicate detection **NOT VERIFIED**; runtime/test parity **NOT VERIFIED**.
- Next: if a broader cleanup is approved, inventory remaining same-purpose modules by subsystem (signal, API, backtest, Android/dashboard, CI) and trace callers/tests before proposing any exact file retirement. Preserve Core First sequencing and do not merge the T0 branch wholesale.


## 2026-11-19 — Telegram, Dashboard and legacy backtest retirement

- Repository/base: `kenznguyen/btcusdt-telegram-signals2`; branch `main`; exact pre-change HEAD `e0880d4144b0d81ca1ff3e2e9e97a72ee408eedf`.
- Owner-approved scope: remove the complete legacy Telegram bridge/notification scanner, Dashboard UI, and legacy Dashboard/Telegram backtest engine including `backtest.py`. Preserve the independent RSI-%b research backtest and preserve RSI/ADX/Smart-DCA strategy rules.
- Removed paths: `app.py`, `telegram_commands.py`, `backtest.py`, `dashboard/index.html`, `.github/backtest-trigger.txt`, `.github/workflows/telegram-command.yml`, `.github/workflows/signal-scan.yml`, and `.github/workflows/dashboard-backtest.yml`.
- `requirements-web.txt` was retained after dependency tracing showed it is still consumed by `.github/workflows/core-api-quality-regression.yml` and `.github/workflows/core-live-data-operational-proof.yml`; deleting it would break unrelated CI. Its presence does not mean the Telegram bridge remains.
- Refactored `bot.py` into a side-effect-free strategy reference: retained Wilder RMA, RSI/ADX indicator construction, RSI-cross entry, TP, Smart-DCA, Soft SL, Emergency SL, threshold and conservative fill helpers; removed Telegram messaging/reporting, OKX candle fetching, state persistence and scanner entrypoint.
- Added `ci/test_strategy_rules.py` covering indicators and the retained strategy rule helpers. Test execution is **NOT RUN** in this change; no test/CI workflow was dispatched.
- Updated root README to describe active repository state; marked archived Telegram README RETIRED while preserving it as historical provenance.
- Independent research files `backtest_rsi_percent_b_h1_adx.py`, `RSI_PERCENT_B_H1_ADX_BACKTEST.md`, and `BACKTEST_COMPARISON_180D.md` were retained. The comparison plan is now historical/inactive because its legacy A-side runner was removed.
- Historical git objects and prior commits are preserved; no history rewrite, branch deletion, T0 change, Core First branch change, VPS/runtime/deployment, exchange, AI execution or live-order action.
- Static dependency scope: the deleted legacy backtest was the only inspected source importing `bot`; after removal, `bot.py` is retained as a pure strategy module and has no Telegram/scanner entrypoint. Full repository-wide dynamic import/caller scan is **NOT VERIFIED**.
- Post-commit GitHub readback: branch `main` resolves to `de4a3e84c38507b76ff561cddb71a7b14a970933`; targeted tree inspection confirms all nine retired source/workflow paths are absent and the independent RSI-%b research backtest remains. `bot.py` readback confirms only the intended strategy functions remain and no `main`, Telegram sender, state persistence or candle-fetch entrypoint exists.
- Status: source/docs commit and targeted tree/readback **PASS**. Tests, workflow execution, artifact production and independent review: **NOT VERIFIED**.
- Next: run `python -m unittest ci.test_strategy_rules -v` and the repository's relevant safe CI on the exact commit; inspect full test discovery and verify no remaining runtime/deployment references to retired surfaces. Do not deploy or reactivate legacy services.
