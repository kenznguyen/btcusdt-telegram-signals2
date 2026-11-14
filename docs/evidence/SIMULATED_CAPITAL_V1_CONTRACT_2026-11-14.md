# SIMULATED_CAPITAL_V1 — PAPER capital contract

Date: 2026-11-14
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/core-operational-proof-20261112`

## Decision

The owner approved a simulated starting balance of **100 USDT** and the following shared risk limits:

| Limit | Approved value | Contract meaning |
|---|---:|---|
| Maximum drawdown | 10% | Account-level drawdown ceiling |
| Maximum daily loss | 2 USDT | UTC-day loss ceiling |
| Maximum order margin | 1% of current portfolio equity | Per-new-order margin budget |
| Maximum exposure | 10 USDT | Shared portfolio exposure ceiling |

Core and AI signals share the same portfolio-level risk scope. Smart DCA additions consume the same per-order margin budget and remain subject to the shared exposure and loss limits. Neither strategy receives a separate risk allowance.

## Immutable capital rules

- `capitalMode=SIMULATED`, `tradingMode=PAPER`, denomination `USDT`.
- Initial capital is exactly 100 USDT.
- Restart must not reset capital, equity, PnL, daily baseline or risk state.
- No automatic top-up and no implicit account reset.
- Capital initialization is a one-time account-creation event; a later reset requires a separately reviewed lifecycle operation and is not part of this contract.
- `liveTradingSupported=false` and `aiExecutionEnabled=false`.
- No exchange credentials, exchange requests, real orders, or live execution.

## Shared risk behavior

- The 10% drawdown, 2 USDT daily loss and 10 USDT exposure ceilings apply across Core and AI together, not independently per strategy.
- A breach of a loss ceiling must block new entries and DCA additions through the shared risk control / Kill Switch.
- The 1% order-margin ceiling is measured against the latest accepted portfolio equity snapshot. Missing, stale or invalid equity must fail closed.
- Exposure and order-margin are different quantities. The contract records both; implementation must not silently substitute one for the other.
- Risk is evaluated again at the atomic order-intent boundary. A signal is not an authorization to trade.

## Implementation boundary and known gap

This increment adds a machine-readable contract and a strict pure-Python validator with synthetic tests. It does **not** wire these values into account bootstrap, persisted risk-state migrations, ledger order admission, Core/AI runners, or runtime configuration. Existing Bootstrap still requires its current funding evidence, equity cutover and owner-attestation package. Do not fabricate account-funding evidence to represent simulated capital.

Before runtime use, a separate implementation increment must reconcile the existing `PaperLedger` risk-limit semantics, add persistent capital provenance/immutability, enforce the 1% margin calculation at the atomic order boundary, and prove cross-strategy Kill Switch behavior. Then run full relevant regression suites and CI.

## Status

- Owner decision: **APPROVED**.
- Contract schema + validator: **IMPLEMENTED**.
- Synthetic contract tests: **CI pending**.
- Existing Bootstrap compatibility: **BLOCKED / NOT IMPLEMENTED**.
- PAPER Ledger readiness: **BLOCKED / NOT VERIFIED**.
- Bootstrap and Runner: **NOT AUTHORIZED**.
