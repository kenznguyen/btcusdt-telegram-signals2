# BTCUSDT Quant System

Repository for the personal BTCUSDT Quant System. It contains several generations and surfaces of the project; their presence in `main` does not mean every service is deployed or operational.

**Repository state reviewed:** 2026-11-18  
**Default branch:** `main`  
**Operating boundary:** research, alerts, backtesting and paper/simulated execution only. Do not infer permission for live orders, exchange execution, or production deployment from repository code or CI.

## Current repository map

| Area | Main paths | What is established |
|---|---|---|
| Telegram signal scanner and command bridge | `bot.py`, `app.py`, `telegram_commands.py`, `.github/workflows/signal-scan.yml`, `.github/workflows/telegram-command.yml` | Legacy notification/command surface remains in source. Signal Scanner is manual-only (`workflow_dispatch`); scheduled scanning is disabled. |
| Backtesting and dashboard | `backtest.py`, `backtest_rsi_percent_b_h1_adx.py`, `dashboard/` | Research and backtest tooling; dashboard consumes user-selected backtest artifacts. |
| Android application | `android-app/`, `.github/workflows/android-*.yml` | Android source and CI/release workflows remain in the repository. Release source selection and signing/install compatibility must be verified before any release. |
| T0 market data and Core API/runtime | `market_data/`, `pipeline/`, `core_runtime/` | Source and isolated contract workflows are present. Source presence is not proof of an operational deployment. |

## Current verified constraints and known limits

- No live order placement is authorized by this repository maintenance state.
- `signal-scan.yml` has only `workflow_dispatch`; it has no active cron schedule.
- The Core API quality projection on `main` has a critical statically confirmed ordering defect documented in [MAIN_CORE_API_QUALITY_SNAPSHOT_STATIC_REVIEW_2026-11-18.md](docs/evidence/MAIN_CORE_API_QUALITY_SNAPSHOT_STATIC_REVIEW_2026-11-18.md): `quality_snapshot()` reads local `core` before assigning it. The review did not execute tests; runtime failure is **NOT RUN**, while the control-flow defect is **CONFIRMED STATICALLY**.
- Core First work on `feature/core-operational-proof-20261112` is not represented as merged or operational on `main`. Do not copy branch status or branch-only evidence into main's current status.
- No claim is made here about VPS, Feeder, canonical database, exchange connectivity, deployment, Android installation, or live runtime readiness.

## Documentation and evidence

- [Project Session Handoff](docs/PROJECT_SESSION_HANDOFF.md) — current state first, followed by preserved historical records.
- [Repository Maintenance](docs/REPOSITORY_MAINTENANCE.md) — branch, change, CI and safety rules.
- [Documentation index](docs/README.md) — active, historical and superseded document classification.
- [Evidence](docs/evidence/) — immutable historical test/review records; a historical PASS applies only to its stated source SHA and scope.
- [Archived Telegram README](docs/archive/README_TELEGRAM_LEGACY_2026-11-18.md) — full previous root README retained for historical operational context. Its deployment instructions are not current deployment evidence.

## Working rules

1. Read `docs/PROJECT_SESSION_HANDOFF.md` before starting work.
2. Work on the existing authorized branch; do not create parallel branches or introduce branch divergence for the same task.
3. Before editing, record the exact base SHA, scope, protected paths and stop conditions.
4. Preserve T0 as an independent data asset. Do not open or mutate its canonical database, start a Feeder, connect to an exchange, or synchronize market data without separate explicit authorization.
5. Keep `AI_EXECUTION_ENABLED=false` and paper/simulated execution boundaries. No live orders.
6. Use GitHub Actions as the default CI. Codemagic is fallback-only and requires a documented GitHub Actions blocker plus explicit approval.
7. Record exact source SHA, workflow/run ID and event, checked-out SHA, job results, artifact identity/digest, and test summary. Missing evidence is **NOT VERIFIED**, not PASS.
8. Preserve Git history and historical evidence. Mark superseded material; do not rewrite history or delete evidence to make the repository appear current.

## Historical Telegram instructions

The prior README contained detailed Render, Telegram webhook, token and manual operation instructions. They have been preserved verbatim in [docs/archive/README_TELEGRAM_LEGACY_2026-11-18.md](docs/archive/README_TELEGRAM_LEGACY_2026-11-18.md), with a notice that those instructions do not establish current deployment state. Use that file only when explicitly working on the legacy Telegram surface, and verify all configuration against current source before acting.
