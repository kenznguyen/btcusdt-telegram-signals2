# VPS PAPER Ledger and Config Creation — 2026-11-14

## Scope and approval

- Owner explicitly approved creation of a new independent PAPER config and Ledger on the replacement VPS.
- Virtual capital confirmed by owner as 100 USDT of simulated capital, not an exchange balance or real trade.
- Scope: create the dedicated Ledger and minimal preflight config only; preserve all existing data.
- No Bootstrap, Decision Cycle, One-shot, Continuous Runner, service/autostart, T0 access, exchange connectivity, AI execution, live trading or real orders.

## Source and contract identity

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Active branch: `feature/core-operational-proof-20261112`
- Owner-reported VPS source SHA: `b92bb75b00b6f91c39c1b78fafab5cd1c77d8fde`
- Simulated capital contract: `paper_execution/contracts/simulated_capital_v1.json`
- Contract SHA-256: `101120eb159248201a45a71b4485ce1de5f9aa0e05ab85cd2713266572ce16c2`

## Pre-creation isolation checks

Owner-pasted VPS output confirmed:

- `PAPER_DB=UNSET`
- `PAPER_TRADING_DB=UNSET`
- Target `/home/ubuntu/btcusdt-telegram-signals2/.data/paper-ledger.sqlite3`
- T0 reference `/home/ubuntu/t0/app/.data/market-data.sqlite3` did not exist on that host at inspection time.
- Prior checks at the same reported source SHA showed exchange credential variables unset, `AI_EXECUTION_ENABLED=UNSET`, and both target files absent before creation.
- The creation command included explicit source SHA, branch, target-absence, credential, AI flag, contract digest and path-isolation guards.

These are owner-pasted terminal results, not independently observed through SSH by the assistant.

## Creation result

Owner-pasted command output reported:

- `CREATION_STATUS=PASS`
- Ledger: `/home/ubuntu/btcusdt-telegram-signals2/.data/paper-ledger.sqlite3`
- Config: `/home/ubuntu/btcusdt-telegram-signals2/core_runtime/config.paper.json`
- `SQLITE_INTEGRITY=ok`
- Simulated account: `PAPER / 100 USDT`
- Strategy ledger scopes: `STRATEGY_CORE`, `AI_FREQAI`, `LEGACY_UNATTRIBUTED`
- `AI_EXECUTION_ENABLED=False`
- `LIVE_TRADING_SUPPORTED=False`

The AI_FREQAI row is an empty schema/ledger scope created by the dual-ledger schema. It does not mean the AI strategy is implemented, admitted or executing.

## Risk and runtime disposition

- `RISK_READY=False`
- Reason: `SIMULATED_INITIAL_MARK_REQUIRED`
- No market mark was fabricated or recorded.
- Decision Cycle: `NOT_RUN`
- One-shot: `NOT_RUN`
- Bootstrap: `NOT_RUN`
- Continuous Runner: `NOT_RUN`
- No GitHub Actions workflow or artifact was generated for this owner-run VPS creation.
- The terminal output was pasted by the owner; no independent SSH observation or remote artifact readback is claimed.

## Status

- Independent PAPER Ledger and minimal config creation: **PASS (owner-reported VPS output)**.
- SQLite integrity and simulated-origin verification: **PASS (owner-reported command output)**.
- Risk readiness: **BLOCKED / NOT READY**, intentionally fail-closed pending a valid market mark.
- Persistent PAPER runtime readiness: **NOT VERIFIED / BLOCKED**.
- Overall VPS operational readiness: **NOT VERIFIED / BLOCKED**.
- AI Strategy: **NOT IMPLEMENTED**; AI execution remains disabled.
- Live trading / real orders: **NOT AUTHORIZED**.

## Next step and restrictions

Next bounded step: review the exact generated config and the Ledger's risk snapshot read-only, then determine the authorized source and freshness requirements for a valid market mark. Do not ingest a mark or change risk readiness until a separate bounded approval specifies the permitted read-only market-data source and exact operation.

Do not run `--ledger-preflight`, Bootstrap, Decision Cycle, One-shot or Runner as part of this evidence record. Do not modify/delete the Ledger, config, existing untracked VPS file, or T0 data. Do not enable AI or live execution.
