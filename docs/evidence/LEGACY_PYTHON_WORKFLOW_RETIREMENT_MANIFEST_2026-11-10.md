# Legacy Python and workflow retirement manifest — 2026-11-10

## Scope and source baseline

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact source baseline inspected: `3838b452ac96f5d82c6071f2ae826ff954d9c4bc`
- Operation: remove the three specifically authorized Python entry points and the workflow/bridge code that exists only to execute or report those tasks.
- This is a source-tree change only. It does not delete the repository, other branches, Git history, Actions/Codemagic run history, artifacts, caches, external repositories, secrets, account settings, Android modules, or market data.

## Discovery correction

At the inspected branch SHA, the paths `.github/workflows/signal-scan.yml`, `.github/workflows/telegram-command.yml`, and `.github/workflows/dashboard-backtest.yml` do **not** exist. Their archived GitHub Actions copies exist under `ci/archive/github-actions/`; the active legacy workflow IDs also exist as blocks in `codemagic.yaml`. The three archived copies and the three Codemagic workflow blocks are the actual workflow definitions removed in this change. The other 14 active `.github/workflows/*.yml` files are preserved.

## Deleted tracked files

| Path | Baseline blob SHA | Reason |
| --- | --- | --- |
| `bot.py` | `9151c61165d5ce9bcfd90f800b4f56f016347d6f` | Legacy Telegram signal/scanner entry point |
| `backtest.py` | `390edc02180da66c85616314d7b1baa295d54c90` | Legacy shared bot backtest engine |
| `telegram_commands.py` | `bd42ca09358127040fce2de353b20f820115399f` | Legacy Telegram command handler |
| `ci/run-legacy.py` | `2537a750beacea99a8aedd9981b466af99f8da7e` | Wrapper that invoked the three legacy tasks |
| `ci/test_legacy_runner.py` | `f535c257dd0883f7e41c11e514b191397ee568f0` | Tests for the removed wrapper |
| `integrations/codemagic_client.py` | `9e590de9d302be976c9c8b2826d3262b701ba9a2` | Codemagic dispatch/history/artifact adapter used by legacy app routes |
| `integrations/test_codemagic_client.py` | `c1068f19d9a52352a982d2f1ab43ae3cc7c06c53` | Tests for the removed legacy adapter |
| `ci/archive/github-actions/signal-scan.yml` | `724d0e7a37c72e2db10d477c7ed7da0d890ea19f` | Archived scanner workflow |
| `ci/archive/github-actions/telegram-command.yml` | `b8f006edc5b716efc03ed0a16573bef4a83d19ef` | Archived Telegram command/backtest workflow |
| `ci/archive/github-actions/dashboard-backtest.yml` | `d2df64c5a3d356db85b2a120514a54e24a80578b` | Archived dashboard backtest workflow |
| `.github/backtest-trigger.txt` | `80ce1fed445b9806d7727594f14edd2131cd498d` | Trigger marker used only by the retired backtest workflow |

## Updated dependency boundaries

- `app.py`: remove Telegram webhook, command dispatch, Codemagic client and dashboard workflow/artifact APIs; preserve T0 health endpoints and the static manual report-viewer route.
- `codemagic.yaml`: remove only `telegram-command`, `dashboard-backtest`, and `signal-scan`; remove deleted Python files from the canonical-market-data path filter and compileall command. Preserve all other workflows.
- `dashboard/index.html`: convert the retained report viewer to manual JSON/CSV loading only; remove workflow polling, external API fetches and the backtest dispatch form.
- `ci/test_ci_policy.py`: remove the obsolete expectation that the retired workflow IDs exist and add a guard for the retirement boundary while retaining checks for Android and five-layer workflows.
- `README.md`, `docs/CODEMAGIC_SETUP.md`, `docs/REPOSITORY_MAINTENANCE.md`, `integrations/README.md`: remove active operating instructions for the retired service and document the new boundary.
- `docs/PROJECT_SESSION_HANDOFF.md`: record exact baseline, scope, evidence state and next verification gate.

## Explicitly retained

- All T0–T4 source, tests, data stores, migrations, APIs, paper ledgers, risk controls and active GitHub Actions workflows.
- Android Paper client and Android/Chart Pro source; no Android module or signing identity was modified.
- `backtest_rsi_percent_b_h1_adx.py`: a separate standalone research script, outside this exact deletion authorization.
- `dashboard/index.html`: retained as a manual JSON/CSV report viewer; it no longer starts or polls workflows.
- `requirements.txt`: retained because the separately retained research script imports NumPy, pandas and requests.
- `requirements-web.txt`, `requirements-market-data.txt`, `requirements-freqai.txt`, `requirements-ci.txt` and the other dependency/test files.
- Other Codemagic workflow definitions and all 14 active `.github/workflows/*.yml` files.

## Data, credentials and external state

- No tracked `state.json` was found in the inspected branch tree.
- No Actions cache or artifact, Codemagic artifact/build, external Telegram state, Render deployment, secret, token, external repository, VPS file, database or canonical T0 data was accessed or deleted.
- Existing Git history continues to contain the deleted blobs; this is ordinary Git commit deletion, not history rewriting or secure erasure.

## Verification status

- Source/path inventory at baseline: PASS for the listed paths and direct dependencies.
- Post-change read-back: pending commit creation.
- Unit/integration tests: NOT RUN in this environment.
- GitHub Actions: NOT DISPATCHED; no run or artifact is claimed.
- External Codemagic account/workflow state: NOT VERIFIED; source configuration only was changed.
- Independent review: NOT PERFORMED.
- T0–T4 runtime/data/acceptance status: unchanged; no new PASS claim.
- Next step: inspect the resulting commit/tree, then run the focused retirement and T0/API regression tests in GitHub Actions after a separately authorized validation step.
