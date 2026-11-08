# T2 Dual Ledger Contract — RED Evidence

Date: 2026-11-08 (UTC)

## Scope

Define the first test-first contract for the Dual-Strategy Intelligence accounting boundary:

- CORE and AI own independent position, DCA, realized-PnL and equity state.
- Both ledgers may share one durable SQLite file but must be namespaced by strategy.
- Shared Risk Engine reads both snapshots and aggregates gross margin/exposure. Opposing LONG/SHORT positions must not net away gross exposure.
- Each accepted entry and DCA reserves 1% of account equity at admission time.
- No fixed position-count cap; admissions are constrained by shared risk budget and safety gates.
- Kill Switch blocks new entries and DCA/increases while allowing risk-reducing exits.
- Paper-only; no exchange execution, no canonical T0 database, no Feeder, no market-data sync.

The risk API receives account_equity explicitly. This keeps per-strategy ledger equity independent while allowing the caller to provide the correct equity basis for an isolated strategy backtest or combined portfolio test.

## Changes

1. Added `quant_system/test_dual_ledger_contract.py` with eight contract scenarios.
2. Added `.github/workflows/t2-dual-ledger-contract.yml` to run the contract on GitHub Actions for push and pull_request events.
3. No production implementation, existing CORE rules, FreqAI model, T0/T1 interface, or runtime configuration was changed.

## RED result

- Branch: `feature/dual-strategy-phase22-preholdout-attestation-20261031`
- PR: #95 (OPEN / DRAFT / NOT MERGED)
- Final source SHA: `068631d9c27bee6d83e529723b840ac7dc468c22`
- Test-only commit: `7c2b152fc390eb6ef628850c35fc2c9af023f90a`
- Workflow commit: `068631d9c27bee6d83e529723b840ac7dc468c22`
- GitHub Actions run: [42453885397](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42453885397)
- Event: `push`
- Workflow: `T2 Dual Ledger Contract`
- Checked-out SHA from job log: `068631d9c27bee6d83e529723b840ac7dc468c22`
- Job: `dual-ledger-contract`, conclusion `failure`
- Expected RED cause: `ModuleNotFoundError: No module named 'quant_system.dual_ledger'`
- Test loader stopped at module import; the eight behavioral test methods were not individually executed. Therefore this is a valid missing-contract/module RED, but not eight independently observed behavioral RED failures.
- Artifact: none produced by this workflow.

## Status

**RED — CONTRACT IMPLEMENTATION MISSING.**

This is not a GREEN result and does not certify independent ledgers or shared risk behavior.

## Next step

Implement `quant_system/dual_ledger.py` to the contract, then rerun the same GitHub Actions workflow. Preserve the existing Strategy Core RSI/ADX/Smart DCA rules and FreqAI provenance checks. Before GREEN, self-review the accounting semantics, transactional persistence, restart behavior, gross exposure aggregation, and the kill-switch reduction exception.

## Restrictions

- Keep `ai_execution_enabled=false`.
- Paper/research only; no real orders.
- Do not create or activate the canonical T0 database or Feeder.
- Do not connect to the exchange or synchronize market data.
- Do not change T0/T1 schemas or interfaces.
- Do not merge PR #95 or any other PR without explicit user approval.
