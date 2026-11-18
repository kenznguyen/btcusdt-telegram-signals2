# BTCUSDT Quant System

Personal BTCUSDT Quant System repository. Current scope is research, strategy development and paper/simulated controls only.

**Repository state reviewed:** 2026-11-19  
**Default branch:** `main`  
**Safety boundary:** no live trading, real orders, exchange execution or production deployment is authorized by repository maintenance.

## Current repository map

| Area | Main paths | Status |
|---|---|---|
| Strategy Core reference rules | `bot.py` | Pure RSI/ADX/Smart-DCA indicators and rule helpers only; Telegram, scanner, state persistence and CLI entrypoint removed. |
| Independent research backtest | `backtest_rsi_percent_b_h1_adx.py`, `RSI_PERCENT_B_H1_ADX_BACKTEST.md` | Separate research implementation/specification; not the deleted legacy backtest engine. |
| Historical comparison plan | `BACKTEST_COMPARISON_180D.md` | Plan retained as historical research documentation; its former A-side runner is retired and must be revalidated before reuse. |
| Android application | `android-app/`, `.github/workflows/android-*.yml` | Android source and CI/release workflows remain. |
| T0 market data and Core API/runtime | `market_data/`, `pipeline/`, `core_runtime/` | Source and isolated contract workflows remain branch/repository scoped; source presence is not proof of deployment. |

## Retired legacy surfaces

The following legacy features have been removed from `main`: Telegram webhook/command bridge, Telegram signal notification scanner, Dashboard UI, Dashboard/Telegram backtest runner, and workflows used only by those surfaces. The historical instructions are retained in [docs/archive/README_TELEGRAM_LEGACY_2026-11-18.md](docs/archive/README_TELEGRAM_LEGACY_2026-11-18.md) for provenance only; they are retired and must not be used to deploy or reactivate the old services.

## Strategy and safety boundaries

- `bot.py` preserves the existing RSI + ADX + Smart-DCA indicator and decision helpers without Telegram/network/state side effects.
- The preserved helpers are a strategy reference, not the approved Core First runtime or proof of parity with the separate Core First branch.
- No live order placement is authorized. Keep `AI_EXECUTION_ENABLED=false` and paper/simulated execution boundaries.
- T0 remains an independent data asset. Do not open or mutate its canonical database, start a Feeder, connect to an exchange, or synchronize market data without separate explicit authorization.
- Core First work on `feature/core-operational-proof-20261112` remains separate from `main`; do not copy branch status or evidence into this branch.
- Dual-Strategy Intelligence / independent AI Strategy remains deferred until Core First closeout and separate approval.

## Documentation and evidence

- [Project Session Handoff](docs/PROJECT_SESSION_HANDOFF.md) — current state first, followed by preserved historical records.
- [Repository Maintenance](docs/REPOSITORY_MAINTENANCE.md) — branch, change, CI and safety rules.
- [Documentation index](docs/README.md) — active, historical and superseded document classification.
- [Evidence](docs/evidence/) — immutable historical test/review records; each result applies only to its stated source SHA and scope.
- [Archived Telegram legacy README](docs/archive/README_TELEGRAM_LEGACY_2026-11-18.md) — retired historical record; do not follow its deployment instructions.

## Working rules

1. Read `docs/PROJECT_SESSION_HANDOFF.md` before starting work.
2. Work on the existing authorized branch; do not create parallel branches or introduce branch divergence for the same task.
3. Before editing, record the exact base SHA, scope, protected paths and stop conditions.
4. Preserve T0 as an independent data asset. No T0 database, Feeder, exchange or market-data runtime action without separate explicit authorization.
5. Keep `AI_EXECUTION_ENABLED=false`; no live orders.
6. GitHub Actions is the default CI. Codemagic is fallback-only and requires a documented GitHub Actions blocker plus explicit approval.
7. Record exact source SHA, workflow/run ID and event, checked-out SHA, job results, artifact identity/digest and test summary. Missing evidence is **NOT VERIFIED**, not PASS.
8. Preserve Git history and historical evidence. Mark superseded material; do not rewrite history or delete evidence to make the repository appear current.
