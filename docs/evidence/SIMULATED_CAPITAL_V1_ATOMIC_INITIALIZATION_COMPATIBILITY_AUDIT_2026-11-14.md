# SIMULATED_CAPITAL_V1 atomic initialization compatibility audit — 2026-11-14

## Scope

Read-only inspection of the active branch `feature/core-operational-proof-20261112` at source HEAD `f51dc3f72687ebfa8267edc9fa07627360c85759`. The audit evaluates the next owner-authorized task: composing account creation, immutable simulated origin, distinct seed, UTC daily baseline and HWM in one atomic initialization transaction.

No source code, schema, workflow, database, Bootstrap, Runner, VPS/T0, exchange or runtime was changed. No test or CI run was performed in this audit increment.

## Exact source reviewed

| Path | Git blob SHA |
|---|---|
| `paper_execution/ledger.py` | `03c76bcd3bab370c49d898fc1ba995073be995b1` |
| `paper_execution/simulated_origin.py` | `6c5dd0452021b42a01189ecb09b0a2f8043dd7ef` |
| `paper_execution/daily_baseline.py` | `747808d9a68a70e9c2aa6f71f00aeeffb6682145` |
| `paper_execution/funding.py` | reviewed current branch; exact content inspected |
| `paper_execution/account_history.py` | `6163065798b2386e1c466650048e40b7eab0d2eb` |
| `paper_execution/bootstrap.py` | `2a75724d0071ecc340617bfc52f4198c09926c92` |
| `paper_execution/risk_control.py` | `2309e1b31872cbbbc99ee2aade79d4f73ea42ace` |

## Findings

1. `PaperLedger.__init__` creates the legacy ledger tables and, for a dual strategy, runs the dual-ledger, funding, cutover, account-history, and daily-baseline-audit migrations inside its own SQLite connection context. The dual-ledger migration creates `paper_accounts`, the three strategy ledgers, and `paper_account_risk_state`. A migrated legacy account starts explicitly not risk-ready; its HWM and daily baseline are NULL until a separate equity cutover.
2. `initialize_simulated_origin` can participate in a caller-owned transaction through a SAVEPOINT, but its current public call after `PaperLedger` construction would be a separate transaction. It requires an existing `paper_accounts` row and does not create the account or risk state.
3. `record_account_equity_cutover` opens its own SQLite connection and `BEGIN IMMEDIATE`. It requires funding coverage/reconciliation and verifies funding events against each strategy ledger's funding total. This is the funded-account evidence path and must not be weakened or supplied with fabricated funding to represent the synthetic seed.
4. `persist_daily_equity_baseline` also opens its own transaction and requires an applied audit migration, a verified equity cutover, replay inputs, a market mark and immutable baseline/audit records. It is not composable as-is inside the account-creation transaction.
5. Therefore, simply calling the existing three helpers in sequence cannot satisfy the approved single-transaction requirement. The current code commits the account/schema migration before origin creation, while cutover and daily-baseline functions independently acquire and commit their own transactions.

## Compatibility boundary

The existing funded-account Bootstrap/cutover path must remain unchanged. The simulated seed must remain separate from `paper_funding_events` and must not masquerade as a deposit, funding coverage, or funding reconciliation.

To create a simulated account that can safely carry a daily baseline and HWM without fabricating funded-account evidence, the design needs an explicit simulation-only equity-origin/cutover path, with its own immutable provenance and clearly separated readiness validation. This likely requires an additive schema/contract boundary and a transaction-aware initialization seam in the ledger migration path. That is a change to persisted schema/risk-state semantics and is not currently specified by the four approved freeze decisions.

## Disposition

- Existing origin/seed primitive: **PASS WITHIN ISOLATED TEST SCOPE** (prior evidence: run `43602607051`, source `d7be89a09c660a4a43b3de0a739d67558b65152a`, 12/12 tests).
- Single atomic account + origin + seed + UTC baseline + HWM initialization: **BLOCKED — existing APIs are transactionally non-composable**.
- Funded-account Bootstrap/cutover preservation: **NOT VERIFIED by an integration test**, but the audited path is distinct and must remain unchanged.
- Runtime/PAPER Ledger readiness: **BLOCKED / NOT VERIFIED**.

## Next decision required

Before writing the integration test or changing schema/risk semantics, obtain owner approval for a narrowly scoped, additive SIMULATED-only equity initialization/cutover record and readiness path. It must:
- bind the exact approved contract SHA-256 and immutable origin/seed;
- establish initial equity = 100 USDT and HWM = 100 USDT without creating a funding event;
- establish the UTC-day baseline and audit record from the simulated origin, with no fabricated funding coverage/reconciliation;
- be created atomically with the account and seed under one `BEGIN IMMEDIATE`;
- fail closed on restart mismatch, partial/orphan state, corrupt provenance or mixed SIMULATED/funded-account identity;
- leave the existing funded-account Bootstrap, funding reconciliation and cutover path unchanged.

No implementation should proceed until this additional boundary is approved. The prior authorization still prohibits operational DB access/mutation, migration, Bootstrap activation, Runner, VPS/T0, exchange access, AI execution, live trading and real orders.
