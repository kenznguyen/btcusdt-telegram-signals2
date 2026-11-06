# Dual-Strategy Ledger Contract

**Status:** DESIGN CONTRACT — implementation not started  
**Scope:** T1.2.1 for the PAPER-only BTCUSDT Quant System  
**Canonical branch:** `feature/t0-centralized-data-feeder-p1-20261101`

## 1. Non-negotiable architecture

- `CORE_LEDGER` and `AI_LEDGER` are separate strategy-owned accounting domains in one account database.
- The two ledgers have independent positions, average entry, realized PnL attribution, fees/funding attribution, DCA state, margin attribution, order history and strategy audit state.
- Both ledgers submit intents through one account-scoped Shared Risk Engine and one atomic account transaction boundary.
- Shared controls remain account-scoped: Max Gross Exposure, Max Drawdown, Daily Loss and Kill Switch. No fixed position-count limit is introduced.
- Every new ENTRY and every exposure-increasing DCA reserves margin equal to **1% of current Account Equity** at admission time. Notional is derived from the strategy leverage; the reservation must use the same leverage/config snapshot later used to simulate the order.
- Risk admission is fail-closed if account equity, risk limits, mark/freshness inputs, strategy identity or reservation state are missing, stale, corrupt or inconsistent.
- Risk-reducing operations (partial reduction, flatten) remain admissible while Kill Switch or a risk latch blocks new/increased exposure, subject to valid execution/book constraints.
- PAPER-only. No exchange API credentials, live orders, deployment, or production execution.

## 2. Ownership and ledger isolation

Allowed strategy identifiers:
- `STRATEGY_CORE`
- `AI_FREQAI`
- `LEGACY_UNATTRIBUTED` for pre-migration exposure whose owner cannot be proven.

Each strategy ledger owns:
- signed position quantity and average entry;
- realized PnL, fees and funding attribution;
- DCA-used/state and strategy-specific initial/current margin attribution;
- its own pending intent/order lifecycle and idempotency records;
- strategy-scoped audit references and read snapshot.

A Core event must never mutate AI position/DCA/PnL state, and vice versa. A reversal closes/reduces only the submitting strategy's position. Any opposite-side residual opening is a separate exposure-increasing leg and must pass Shared Risk Engine admission. A strategy cannot close or reverse another strategy's position.

No strategy-scoped API may silently return the whole account position as though it belonged to that strategy. Read APIs must make account aggregate and strategy-specific views explicit.

## 3. Account aggregate and equity contract

Account Equity is computed once:
`initial capital + Core realized/unrealized PnL + AI realized/unrealized PnL + attributable legacy PnL - fees - funding`.

- Initial capital is stored once at account scope; it is never duplicated per strategy.
- Account-level high-water mark, drawdown and UTC daily baseline are computed from aggregate account equity.
- Gross Exposure is `abs(Core notional) + abs(AI notional) + abs(legacy notional) + reserved/pending exposure`. Opposing LONG/SHORT positions do not offset.
- Total used/reserved margin is aggregated across both ledgers and outstanding reservations.
- Per-strategy equity/PnL attribution is reporting data; it must reconcile exactly to account totals and must not create separate capital pools.
- Missing mark price, stale mark, incomplete ledger attribution, unavailable equity history or invalid account configuration => reject new exposure with an explicit fail-closed reason.

## 4. Shared admission and atomicity

A single SQLite write transaction (or equivalent serializable transaction for a future database adapter) must perform, in order:

1. Validate strategy identity, intent schema, mode, expiry and idempotency key.
2. Return the prior result for an identical `intentId`; reject reuse with a different canonical payload or strategy identity.
3. Load/validate all strategy ledger rows, legacy exposure, active pending orders and reservations.
4. Calculate current aggregate account equity and gross exposure from a consistent snapshot.
5. Classify the intent as reduction-only, neutral, or exposure-increasing. A reversal must be split into a close/reduce leg and a separately admitted opening leg.
6. For each exposure-increasing ENTRY/DCA, reserve `current_account_equity * 0.01` margin and corresponding notional using the strategy's leverage. DCA is not exempt.
7. Enforce shared Max Gross Exposure, Max Drawdown, Daily Loss, Kill Switch, margin availability and configured liquidity constraints. Never use net exposure to pass admission.
8. Reserve order-book liquidity at price-level granularity before fill simulation. Two strategies must not consume the same displayed quantity twice.
9. Persist the reservation, order/intent state, risk decision and audit event atomically.
10. On fill/cancel/expiry/rejection, atomically reconcile or release unused reservations and update only the owning strategy ledger plus account aggregates.

Concurrent Core and AI submissions must serialize at the account boundary. Two simultaneous requests may not both spend the same remaining exposure, margin or visible book depth. A transaction failure must leave no partial reservation, fill, ledger update or audit inconsistency.

## 5. Pending orders and order-book reservations

- Pending order uniqueness is account-wide for risk and resource reservation, while lifecycle ownership remains strategy-scoped.
- A pending order reserves its maximum remaining exposure/margin until filled, canceled, expired or rejected.
- Shared order-book liquidity is reserved by immutable book snapshot identity, side and price level. Reservation quantity is cumulative across strategies and cannot exceed captured visible quantity.
- Reuse of a snapshot is not automatically forbidden if there is unconsumed quantity; however, the same visible units must never be filled twice.
- Stale/invalid/crossed snapshots or insufficient reserved depth must not be treated as executable liquidity.
- Reservations must be idempotent by intent/order ID and recoverable after process restart.

## 6. Migration and legacy safety

- Migration must be additive, versioned, transactional and restart-safe.
- Existing `paper_state` and `paper_strategy_state` must be preserved as migration inputs until verified reconciliation succeeds.
- If existing owner is reliable, migrate the existing position, average, realized PnL, fees, DCA and margin into that strategy ledger without changing economic values.
- If owner is missing, conflicting or cannot be proven, migrate exposure to `LEGACY_UNATTRIBUTED`; never guess Core or AI.
- While unattributed legacy exposure exists, block new exposure-increasing orders until it is explicitly reconciled. Risk-reducing closure remains allowed under a dedicated legacy-reconciliation path.
- Preserve all historical orders, intent hashes, audit records, kill/pause state, equity history, initial capital and daily baselines.
- Do not duplicate initial capital, fees, funding, realized PnL or equity history during migration.
- Provide a read-only pre/post migration reconciliation report: position, average, realized PnL, fees, funding, margin, pending orders, reservations, account equity and gross exposure.
- Migration rollback must not discard post-migration events. Use a tested backup/restore or forward-repair plan; no destructive downgrade.

## 7. Required public behavior / read models

The ledger API must support:
- submit an intent with explicit strategy ID and event type;
- fetch one strategy snapshot;
- fetch an account aggregate risk/equity snapshot;
- fetch account-wide pending/reservation state for risk diagnostics;
- read strategy and account audit trails without cross-owner mutation.

Strategy snapshot includes strategy ID, position, average entry, realized/unrealized PnL attribution, fees/funding, DCA state, margin, owned orders and update cursor.

Account snapshot includes total equity, gross exposure, reserved exposure, total margin used/reserved, high-water mark, Max DD, UTC daily loss, Kill Switch, risk readiness and explicit unavailable reasons.

## 8. Required test gates before GREEN

1. Core LONG and AI SHORT coexist in one database; each snapshot and reopened instance sees only its own state.
2. Core and AI same-side positions coexist without accidental netting.
3. Core DCA does not mutate AI DCA state and vice versa.
4. Strategy-scoped reduction/reversal cannot mutate the other ledger.
5. Account equity and gross exposure reconcile across both strategies and legacy state.
6. Two simultaneous entries cannot over-reserve margin or Max Gross Exposure.
7. Each ENTRY and DCA reserves exactly 1% of current account equity at admission; subsequent admission uses updated equity.
8. Kill Switch / Max DD / Daily Loss block increases but permit valid reductions.
9. Missing/stale/corrupt equity or risk input fails closed.
10. Identical intent retry is idempotent; changed payload/strategy reuse is rejected.
11. Pending and partial fills reserve and release capacity correctly across both strategies.
12. Shared book-level reservations prevent double consumption of displayed depth across Core and AI.
13. Restart/reopen preserves all ledgers, reservations, idempotency, audit and risk state.
14. Legacy ownership ambiguity remains unattributed and blocks new exposure.
15. Migration reconciliation and rollback/recovery tests preserve all economic totals.

RED 1 currently covers only item 1's initial coexistence assertion and is intentionally incomplete. Its observed failure occurs before its snapshot/persistence assertions, so those assertions remain unverified.

## 9. Implementation sequence and stop conditions

- T1.2.1: approve/freeze this contract and define migration/schema plan.
- T1.2.2: implement strategy ledger storage plus account-level atomic Shared Risk Engine and reservations, driven by focused RED tests.
- T1.2.3: integrate Paper Execution and strategy-scoped read models.
- T1.2.4: run concurrency, migration, recovery, risk and full regression tests.
- T1.3: only then build independent Core and AI backtests using the same market data window and shared account assumptions, with separate trade ledgers/results.

No implementation, schema migration, backtest, merge or live execution is authorized by this design document. Any ambiguity in legacy attribution or account equity is a hard stop, not an invitation to infer ownership.
