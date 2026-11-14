# VPS PAPER Ledger Read-Only State Inspection — 2026-11-14

## Scope and source identity

Owner approved a bounded read-only inspection of the generated PAPER config and independent Ledger risk state. No preflight, migration, bootstrap, Decision Cycle, One-shot, Runner or service was executed.

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/core-operational-proof-20261112`
- Owner-reported VPS source SHA: `b92bb75b00b6f91c39c1b78fafab5cd1c77d8fde`
- Config: `/home/ubuntu/btcusdt-telegram-signals2/core_runtime/config.paper.json`
- Config SHA-256: `211a29985c6c3b211f50edea87c4371acf69ee339ad513ae722ad289b5ea9bb6`
- Ledger: `/home/ubuntu/btcusdt-telegram-signals2/.data/paper-ledger.sqlite3`

Evidence is terminal output pasted by the owner. No independent SSH observation or CI workflow/artifact is claimed.

## Owner-reported read-only results

- `READ_ONLY_INSPECTION=PASS`
- `SQLITE_INTEGRITY=ok`
- `SIMULATED_ORIGIN_VALID=True`
- Account: `PAPER`, initial capital `100 USDT`
- Config: mode `PAPER`, `ai_execution_enabled=false`
- AI execution environment variable: `UNSET`; config explicitly disables AI execution.
- Exchange credential variables: absent.
- Strategy ledgers present: `AI_FREQAI`, `LEGACY_UNATTRIBUTED`, `STRATEGY_CORE`.
- All three strategy positions, average entry, PnL, fees, funding and initial margin are zero; DCA-used flags are zero.
- Orders query returned no rows.
- Schema migrations versions 1 through 11 all report `APPLIED`.

## Risk state and disposition

Owner-reported persisted account risk state:

- `high_water_mark_quote=100`
- `daily_baseline_equity_quote=100`
- `last_equity_quote=null`
- `last_mark_price=null`
- `mark_observed_at_ms=null`
- `mark_candle_close_ms=null`
- `dataset_version=null`
- `risk_ready=0`
- `unavailable_reason=SIMULATED_INITIAL_MARK_REQUIRED`

Kill Switch state:

- `paused=0`
- `killed=0`
- `reason=null`

The Kill Switch is not armed. This inspection did not change it. The missing initial market mark and `risk_ready=0` remain a separate fail-closed readiness blocker. Do not describe this as runtime-ready.

## Status

- Config and Ledger read-only inspection: **PASS (owner-reported terminal output)**.
- SQLite integrity and simulated origin: **PASS (owner-reported)**.
- Schema migration state: **PASS (11/11 applied, owner-reported)**.
- Risk readiness: **BLOCKED / NOT READY**, reason `SIMULATED_INITIAL_MARK_REQUIRED`.
- Kill Switch: **NOT ARMED** (`killed=0`, `paused=0`); no mutation authorized or performed.
- Persistent PAPER runtime readiness: **NOT VERIFIED / BLOCKED**.
- AI Strategy: **NOT IMPLEMENTED**; AI execution disabled by config.
- Live trading / real orders: **NOT AUTHORIZED**.

## Next step and restrictions

Next bounded design decision: specify the permitted read-only market-data source, candle timeframe, freshness limit, dataset-version provenance and exact mark-ingestion operation needed to establish the first valid simulated account mark. Any write to the Ledger, Kill Switch change, preflight, Bootstrap, Decision Cycle, One-shot or Runner requires separate explicit approval.

Preserve the Ledger, config, existing untracked VPS file and all T0 data. Do not enable AI execution or live trading.
