# Architecture Decision Addendum — Dual-Strategy Intelligence

Date: 2026-11-06 (Asia/Ho_Chi_Minh)

This addendum is part of the durable project handoff for `kenznguyen/btcusdt-telegram-signals2`. It records the owner's latest architecture decisions. It is documentation only; it does not claim that the corresponding runtime, backtest, risk, ledger, or execution code has been implemented.

## 1. Decision status and scope

- Status: **OWNER-APPROVED ARCHITECTURE BASELINE**.
- Applies to: BTCUSDT Quant System / five-layer project.
- Does not apply to the separately maintained BTC Chart Pro repository.
- This decision supersedes older planning assumptions that capped open positions at five or used a 10% account-margin allocation per order.
- Existing paper-only and no-live-execution constraints remain in force.

## 2. Dual-Strategy Intelligence

Two independent strategy producers operate side by side:

### Strategy Core
- Preserve the existing RSI + ADX + Smart DCA strategy and its approved parameters/behavior.
- Core independently generates its own LONG/SHORT intents.
- Core owns and manages its own orders, positions, lifecycle state, and trade history.
- Do not modify Core logic or tune its parameters merely to improve historical results without separate owner approval.

### AI Strategy
- AI is a standalone signal-producing strategy, not merely a validator or filter for Core signals.
- AI may independently generate LONG/SHORT intents even when Strategy Core produces no signal.
- AI owns and manages its own orders, positions, lifecycle state, and trade history.
- AI must not borrow, mutate, close, or net Core position state as an implicit side effect.

## 3. Independent order and position domains

- Core and AI maintain separate order streams and position books.
- Every intent, order, fill, position, DCA action, TP/SL action, and close event must retain an unambiguous strategy-source identity.
- IDs and reconciliation must prevent cross-strategy accidental updates, closes, or netting.
- Account-level risk remains shared. Independent strategy books do not create independent account risk budgets.

## 4. Independent backtests and reporting

Two separate backtest pipelines are required:

1. **Core Backtest** evaluates Strategy Core only.
2. **AI Backtest** evaluates AI Strategy only.

Each report must be independently reproducible and must not use the other strategy's trades or outcomes as a substitute. At minimum, each reports:
- trade count and LONG/SHORT breakdown;
- realized and unrealized PnL;
- fees and funding;
- win/loss statistics;
- equity curve and maximum drawdown;
- margin and exposure;
- DCA, TP, SL, and liquidation events;
- fill assumptions, slippage, and data/source provenance.

A combined portfolio report may be provided as an additional view, but it must not replace either independent report. Comparisons must use clearly disclosed common data windows and cost/fill assumptions.

## 5. Position sizing and portfolio limits

- Initial margin allocation per new order: **1% of total account capital at the time of sizing**.
- There is **no hard-coded maximum count of open positions**.
- The removal of a position-count cap does not remove account-level controls.
- Shared portfolio controls must continue to enforce configured limits for total exposure, aggregate margin, leverage, drawdown, daily loss, available collateral, and any other approved risk constraints.
- Do not silently relax any account-level limit to make a signal pass.
- Reject or defer an intent when the shared risk budget, available margin, or safety state does not permit it.
- Sizing must define the account-capital basis, rounding, minimum notional, leverage interaction, and insufficient-margin behavior explicitly before implementation.

## 6. Shared Risk Engine and Kill Switch

- Both Core and AI submit strategy-tagged intents to the same Shared Risk Engine.
- Every intent must pass shared risk validation before it can create or increase paper exposure.
- The Kill Switch is account-wide and must be able to block both strategy streams.
- Risk decisions and rejections must be auditable and attributable to the originating strategy.
- Strategy independence must never bypass shared account-level controls.

## 7. Execution boundary

- Paper Trading and signal generation only.
- No live trading, real exchange orders, or production execution.
- Keep `ai_execution_enabled = false`.
- Any future execution-mode change requires explicit owner approval and a separately reviewed safety decision.

## 8. Development and evidence rules

- GitHub is the source-of-truth repository for source, architecture decisions, handoff, and evidence.
- Preserve the repository's currently recorded workflow/runner policy; this addendum does not authorize a CI-provider migration or a workflow change.
- Continue PC-first development. VPS deployment is deferred until the relevant acceptance gates pass.
- Apply test-first development for behavior changes. After each feature increment, run focused tests and the required regression suite.
- Verify branch, exact source SHA, workflow run, job conclusions, and artifacts before declaring PASS.
- Distinguish implemented, tested, accepted, and production-enabled states. This architecture approval alone does not prove implementation or acceptance.
- Do not merge a PR without explicit owner approval.

## 9. Required implementation and acceptance checklist

Before calling this architecture implemented:
- [ ] Remove any hard-coded open-position count cap across configuration, validation, API, UI, tests, and documentation; retain all account-level risk limits.
- [ ] Implement and test 1%-of-account sizing at the documented sizing timestamp, including rounding, minimum notional, leverage, and insufficient-margin cases.
- [ ] Enforce strategy-source isolation across intents, order IDs, fills, positions, DCA, TP/SL, close events, and reconciliation.
- [ ] Prove Core cannot mutate AI state and AI cannot mutate Core state.
- [ ] Route both strategy streams through the same Shared Risk Engine and account-wide Kill Switch.
- [ ] Build and run Core Backtest independently from AI Backtest.
- [ ] Verify each backtest's fees, funding, slippage/fills, liquidation, equity, drawdown, exposure, and event accounting.
- [ ] Keep combined reporting supplementary and prove it does not contaminate either independent result.
- [ ] Verify paper-only invariants and `ai_execution_enabled = false` across configuration, tests, and runtime boundaries.

## 10. Current implementation status

At the time this addendum is recorded:
- The decisions above are approved as architecture requirements.
- No source-code implementation, test run, backtest run, runtime activation, or production acceptance is asserted by this document.
- Existing PRs and historical backtest artifacts must be re-audited against this baseline; their titles or prior descriptions alone do not prove compliance.
- In particular, historical Core/AI replay results must not be treated as proof that the new independent order books and independent backtest pipelines satisfy this decision.

## 11. Handoff instruction

At the next session, read this addendum together with `docs/PROJECT_SESSION_HANDOFF.md`. Treat this addendum as the authoritative owner-approved baseline for Dual-Strategy Intelligence, order/position separation, per-order margin sizing, and independent backtests. Preserve all other handoff safety boundaries unless the owner explicitly changes them.
