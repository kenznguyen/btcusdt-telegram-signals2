# Dual Ledger Schema and Migration Plan

**Status:** DESIGN APPROVED — six open decisions resolved; implementation and database changes remain unauthorized  
**Approval basis:** User approved `DUAL_LEDGER_CONTRACT.md` on 2026-11-06  
**Scope:** T1.2.1 follow-on design for the PAPER-only BTCUSDT Quant System  
**Branch:** `feature/t0-centralized-data-feeder-p1-20261101`

## 1. Design constraints and verified legacy schema

The current implementation is SQLite and stores one account-like paper position in:
- `paper_state(id, position, average, realized, fees, paused)`
- `paper_strategy_state(id, owner, dca_used, initial_margin_quote)`
- `paper_orders(intent_id, payload_hash, order_id, status, document)`
- `paper_books(book_id, used_at_ms)`
- `paper_audit(id, at_ms, kind, document)`
- `paper_risk_control(id, paused, killed, reason, updated_at_ms)`
- `paper_equity_history(... single-position equity snapshots ...)`
- `paper_daily_baselines(utc_day_ms, baseline_at_ms, baseline_equity, baseline_kind)`
- `paper_account_config(id, initial_capital)`

Important constraints found in source:
- `paper_orders` has one global `intent_id` primary key and does not expose a strategy column.
- `paper_books` marks an entire book snapshot consumed; it does not track per-price-level quantity reservations.
- `paper_equity_history` stores a single position, one realized PnL and one fee total per snapshot.
- `paper_account_config` stores initial capital once.
- Current `paper_strategy_state.owner` is one global owner, not a per-strategy state.
- Existing funding attribution is not represented in the inspected ledger/equity tables.
- The current source uses one SQLite transaction with `BEGIN IMMEDIATE` for submit; preserve this serialization boundary.

The old tables are migration inputs and audit evidence. Do not drop, rename, truncate or rewrite them during the initial migration.

## 2. Proposed additive schema

All monetary/quantity values remain canonical decimal strings in SQLite TEXT columns; timestamps are UTC epoch milliseconds. Foreign keys are enabled on every write connection. All rows below are scoped to the single paper account `account_id=1` unless otherwise stated.

### 2.1 Migration metadata

`paper_schema_migrations`
- `version INTEGER PRIMARY KEY`
- `name TEXT NOT NULL UNIQUE`
- `checksum TEXT NOT NULL`
- `applied_at_ms INTEGER NOT NULL`
- `source_sha TEXT NOT NULL`
- `status TEXT NOT NULL CHECK(status IN ('APPLIED'))`

A migration is applied exactly once. Checksum mismatch for an already-applied version is a hard stop. Do not rely on `PRAGMA user_version` alone because the migration record must include source and checksum evidence.

### 2.2 Account aggregate

`paper_accounts`
- `account_id INTEGER PRIMARY KEY CHECK(account_id=1)`
- `mode TEXT NOT NULL CHECK(mode='PAPER')`
- `initial_capital TEXT NOT NULL`
- `currency TEXT NOT NULL CHECK(currency='USDT')`
- `created_at_ms INTEGER NOT NULL`
- `migration_version INTEGER NOT NULL`

Exactly one row. Initial capital is copied once from legacy `paper_account_config`; if absent, migration does not invent it. Missing or invalid initial capital leaves account risk readiness false and blocks new exposure until explicitly configured through an approved account setup operation.

### 2.3 Strategy ledger state

`paper_strategy_ledgers`
- `account_id INTEGER NOT NULL REFERENCES paper_accounts(account_id)`
- `strategy_id TEXT NOT NULL CHECK(strategy_id IN ('STRATEGY_CORE','AI_FREQAI','LEGACY_UNATTRIBUTED'))`
- `position_base TEXT NOT NULL`
- `average_entry_price TEXT NOT NULL`
- `realized_pnl_quote TEXT NOT NULL`
- `fees_quote TEXT NOT NULL`
- `funding_quote TEXT NOT NULL`
- `dca_used INTEGER NOT NULL CHECK(dca_used IN (0,1))`
- `initial_margin_quote TEXT NOT NULL`
- `updated_at_ms INTEGER NOT NULL`
- `version INTEGER NOT NULL`
- Primary key: `(account_id,strategy_id)`

Create the three strategy rows at migration time. Zero position must have zero average; nonzero position must have positive average. `LEGACY_UNATTRIBUTED` is not a signal-producing strategy and accepts only explicit reconciliation/reduction operations.

### 2.4 Orders and idempotency

Keep `paper_orders` as the compatibility/history table during transition. Add nullable columns using additive `ALTER TABLE`:
- `account_id INTEGER`
- `strategy_id TEXT`
- `strategy_event TEXT`
- `reservation_id TEXT`
- `created_schema_version INTEGER`

New writes require non-null account and strategy identity at application validation; historical rows remain NULL when ownership cannot be proven. Add indexes on `(account_id,strategy_id,status)` and `reservation_id` after a duplicate/null audit.

Do not add a second independent order table with a competing idempotency key. Existing `intent_id` remains the account-wide idempotency key. Canonical payload digest must include account, strategy ID, strategy event, intent body and relevant immutable execution/risk config version. Reuse with any mismatch is a conflict.

### 2.5 Account risk snapshot and reservations

`paper_account_risk_state`
- `account_id INTEGER PRIMARY KEY REFERENCES paper_accounts(account_id)`
- `high_water_mark_quote TEXT`
- `daily_baseline_utc_day_ms INTEGER`
- `daily_baseline_equity_quote TEXT`
- `last_equity_quote TEXT`
- `last_mark_price TEXT`
- `mark_observed_at_ms INTEGER`
- `mark_candle_close_ms INTEGER`
- `dataset_version TEXT`
- `risk_ready INTEGER NOT NULL CHECK(risk_ready IN (0,1))`
- `unavailable_reason TEXT`
- `updated_at_ms INTEGER NOT NULL`
- `version INTEGER NOT NULL`

`paper_risk_reservations`
- `reservation_id TEXT PRIMARY KEY`
- `account_id INTEGER NOT NULL REFERENCES paper_accounts(account_id)`
- `intent_id TEXT NOT NULL UNIQUE REFERENCES paper_orders(intent_id)`
- `strategy_id TEXT NOT NULL`
- `reservation_kind TEXT NOT NULL CHECK(reservation_kind IN ('ENTRY','DCA','PENDING','BOOK_DEPTH'))`
- `status TEXT NOT NULL CHECK(status IN ('ACTIVE','PARTIAL','RELEASED','CONSUMED','EXPIRED'))`
- `reserved_margin_quote TEXT NOT NULL`
- `reserved_notional_quote TEXT NOT NULL`
- `leverage TEXT NOT NULL`
- `equity_basis_quote TEXT NOT NULL`
- `risk_config_version TEXT NOT NULL`
- `created_at_ms INTEGER NOT NULL`
- `updated_at_ms INTEGER NOT NULL`

Reservation values are immutable evidence of admission-time inputs; status/remaining amounts may advance under transaction. A reservation cannot be silently recomputed using a later equity or leverage value.

### 2.6 Book-level liquidity reservations

`paper_book_level_reservations`
- `reservation_id TEXT NOT NULL REFERENCES paper_risk_reservations(reservation_id)`
- `book_id TEXT NOT NULL`
- `side TEXT NOT NULL CHECK(side IN ('BUY','SELL'))`
- `price TEXT NOT NULL`
- `reserved_quantity TEXT NOT NULL`
- `remaining_quantity TEXT NOT NULL`
- `status TEXT NOT NULL CHECK(status IN ('ACTIVE','RELEASED','CONSUMED'))`
- Primary key: `(reservation_id,book_id,side,price)`

Add an index on `(book_id,side,price,status)`. Under the same account write transaction, sum active remaining reservations at each level and reject any reservation that would exceed captured visible quantity. Snapshot identity is retained, but a snapshot is not considered entirely consumed merely because one strategy used part of it.

### 2.7 Strategy funding and audit attribution

`paper_funding_events`
- `funding_event_id TEXT PRIMARY KEY`
- `account_id INTEGER NOT NULL REFERENCES paper_accounts(account_id)`
- `strategy_id TEXT NOT NULL`
- `amount_quote TEXT NOT NULL`
- `event_at_ms INTEGER NOT NULL`
- `source_snapshot_id TEXT NOT NULL`
- `payload_hash TEXT NOT NULL UNIQUE`

No historical funding amount is inferred. Existing history without funding attribution is retained as unknown/unattributed; risk readiness must reflect the absence of required current-period inputs if funding is required by the configured account model.

Keep `paper_audit` append-only. Add nullable `account_id`, `strategy_id`, `intent_id`, `event_version` columns for new structured events. Existing audit rows remain untouched and may be returned as legacy account-level events, not falsely attributed to either strategy.

## 3. Account math and risk calculation

At a single consistent transaction snapshot:

- Account equity = one-time initial capital + sum(strategy realized PnL) + sum(strategy unrealized PnL at one fresh mark) - sum(strategy fees) - sum(strategy funding costs).
- Gross position notional = sum(abs(strategy position quantity) * mark price) for Core, AI and unattributed legacy.
- Gross exposure for admission additionally includes active pending-order notional and active notional reservations not already represented by filled positions. Avoid double-counting filled portions.
- Used margin = sum of strategy margin attribution for open positions; reserved margin = sum active unfilled reservations. Available margin must be derived from account equity and configured risk/leverage rules, not from net positions.
- HWM and UTC daily baseline are account-level and never duplicated per strategy.
- All risk comparisons use decimal arithmetic and the same mark/risk-config snapshot used to make the admission decision.
- If current account equity or mark is missing/stale, legacy reconciliation is incomplete, risk config is absent, or any ledger/reservation row is corrupt, return a stable fail-closed reason and reject exposure increases. Reductions may proceed through the separate reduction-only path if valid execution data exists.

## 4. Transaction protocol

All submit/cancel/expire/fill/reconcile operations acquire the account write boundary using `BEGIN IMMEDIATE` on SQLite.

### Submit

1. Validate PAPER mode, strategy identity, event type, intent timestamps and canonical payload.
2. Look up account-wide `intent_id`; return prior order for identical hash; conflict on mismatch.
3. Read all strategy states, risk state, active orders/reservations, mark and config under the transaction.
4. Validate migration completion and risk readiness.
5. Calculate aggregate equity and gross exposure without netting.
6. Classify reduction vs exposure increase. For reversal, first simulate a close of only the submitting ledger; separately evaluate residual opening exposure as a new risk admission.
7. For each ENTRY/DCA increase, reserve exactly 1% of current account equity as margin; record equity basis, leverage and risk-config version.
8. Reserve required visible book quantity by price level after subtracting active reservations.
9. Insert/update order, reservation, strategy ledger, risk snapshot and audit rows atomically.
10. On any error, rollback all writes. Do not leave an order without its reservation or a reservation without its owning order.

### Fill / partial fill

- Apply fills only to the owning strategy ledger.
- Update realized PnL, average price, fees and remaining reservation using fill-level prices.
- Convert consumed book reservation to consumed quantity; release unused level quantity only when order completes/cancels/expires.
- Recompute account aggregates and reconcile all ledger sums before commit.

### Cancel / expiry / recovery

- Cancel/expiry releases remaining margin/notional/book reservations in the same transaction.
- Restart recovery loads active orders and reservations and validates referential consistency. It must not recreate or duplicate reservations.
- Any orphan order/reservation or mismatched quantity causes risk readiness false and blocks new exposure pending repair; no silent cleanup.

## 5. Migration plan

Migration is additive, one-time, restart-safe, and PAPER-only.

### Phase A — Preflight, read-only

1. Verify exact source SHA and branch; stop if branch changes during migration.
2. Open DB read-only; validate integrity (`PRAGMA integrity_check`), foreign key state and every legacy row.
3. Record counts and canonical hashes for all legacy tables and account config.
4. Build a report for position, average, realized PnL, fees, pause/kill state, orders by status, audit count, books, equity history, daily baselines and initial capital.
5. Determine ownership only from an explicit valid legacy owner plus consistent state. If owner is absent, `MANUAL`, conflicting or unsupported while a position exists, classify position as `LEGACY_UNATTRIBUTED`.
6. If any required value is corrupt or reconciliation cannot be explained, stop without writes.

### Phase B — Backup and transactional migration

1. Create and verify a consistent SQLite backup while no other writer is active; record backup SHA-256 and database identity.
2. Begin `BEGIN IMMEDIATE`.
3. Create new tables and migration metadata; add nullable compatibility columns to old tables.
4. Copy initial capital once, preserving exact decimal text.
5. Create Core, AI and Legacy ledger rows with zero defaults.
6. Transfer the single legacy position only to its proven owner; otherwise transfer it to Legacy. Preserve average entry exactly.
7. Attribute existing realized PnL/fees only when source provenance proves strategy ownership. Otherwise preserve them as account-level legacy adjustments, not arbitrary Core/AI PnL. Record exact reconciliation mapping and hashes.
8. Preserve legacy orders/audit/history as-is; populate new strategy/account columns only where ownership is proven from immutable evidence. Otherwise leave NULL and treat as unattributed historical records.
9. Copy pause/kill latch and risk config without weakening it.
10. Seed account HWM/daily baseline from the latest valid legacy equity point only if its source/account configuration is consistent. If not, set risk readiness false until a new valid account-level equity baseline is observed; never fabricate a baseline.
11. Validate row counts, hashes and decimal reconciliation; insert migration record and commit only if every required invariant passes.
12. On any failure, rollback. Keep backup unchanged.

### Phase C — Post-migration read-only reconciliation

Compare pre/post:
- initial capital (exactly one copy);
- position quantity and average entry;
- realized PnL, fees and funding/unattributed adjustments;
- active/pending orders and idempotency keys;
- audit row count and content hashes;
- pause/kill state;
- equity history and UTC daily baselines;
- used/reserved margin and gross exposure;
- account equity at the migration cutover (or explicit NOT VERIFIED when historical data lacks required mark/funding provenance).

Any unexplained difference => migration NOT VERIFIED, no new exposure, preserve backup and use forward repair. No destructive downgrade.

### Phase D — Runtime compatibility window

- New strategy-scoped writes target new ledger tables and account risk/reservation tables only.
- Old tables remain read-only compatibility evidence until all read paths are migrated and regression tests pass.
- A single feature flag controls schema read/write cutover; default OFF until migration and tests pass.
- No dual-write to old and new position states.
- Rollback means disable new write path and restore from verified backup/forward-repair; do not replay writes into the old single-owner state without a reconciled reverse mapping.

## 6. API/read-model shape after migration

The implementation should expose distinct methods, not overload the existing ambiguous snapshot:
- `strategy_snapshot(strategy_id)` → one strategy's position, PnL, fees/funding, DCA, margin and owned orders.
- `account_snapshot(now_ms)` → aggregate equity, gross exposure, active reservations, margin, HWM, drawdown, UTC daily loss, kill/pause and readiness reasons.
- `account_reservations()` → account-wide pending margin/notional and book-level reservations for diagnostics.
- `submit(..., strategy_id, strategy_event)` → explicit strategy ownership, account-wide idempotency and atomic admission.
- Existing `snapshot()` remains temporarily as a deprecated legacy/account compatibility view; it must not silently claim a global position belongs to the caller. Deprecation behavior must be explicit and tested.

Stable errors include `ACCOUNT_NOT_READY`, `LEGACY_RECONCILIATION_REQUIRED`, `EQUITY_UNAVAILABLE`, `MARK_STALE`, `RISK_LIMITS_UNCONFIGURED`, `GROSS_EXPOSURE_LIMIT`, `MARGIN_RESERVATION_FAILED`, `BOOK_DEPTH_RESERVED`, `INTENT_ID_CONFLICT` and `LEDGER_STATE_CORRUPT`.

## 7. Test plan mapped to schema and migration

| Gate | Required proof |
|---|---|
| Schema init | Fresh DB creates all tables/indexes, version/checksum idempotently |
| RED 1 coexistence | Core LONG + AI SHORT fill, isolated snapshots and reopen persistence |
| Isolation | Core/AI DCA, close, reverse and audit attribution cannot cross-write |
| Aggregate math | Equity, gross exposure, margin and PnL reconcile exactly |
| Reservation | Current-equity 1% for every ENTRY/DCA, no double spend |
| Concurrency | Concurrent Core/AI submissions serialize; one cannot over-reserve |
| Kill/reduction | Kill blocks increases, valid reductions still work |
| Pending | Partial fill/cancel/expiry releases only remaining reservation |
| Book depth | Same snapshot price-level quantity cannot be consumed twice |
| Idempotency | Same intent returns same result; altered strategy/payload conflicts |
| Fail-closed | Missing/stale/corrupt mark/equity/config/legacy state blocks increases |
| Migration | Owner proven vs unknown, exact PnL/fee/position preservation |
| Recovery | Restart and interrupted migration do not duplicate/lose state |
| Rollback | Backup restore/forward repair preserves all post-cutover evidence |

All gates run through GitHub Actions on exact source SHAs, using isolated temporary SQLite databases and no secrets or external exchange connections.

## 8. Resolved design decisions — normative requirements

All six decisions below were explicitly approved by the user on 2026-11-06. They are mandatory requirements for implementation and acceptance tests; they are not optional defaults.

1. **Historical realized PnL and fees without strategy provenance:** preserve exact known aggregates as account-level `LEGACY_UNATTRIBUTED` adjustments and include them once in account equity. Never assign them to Core/AI statistics or infer ownership. Attribute individual fills only with immutable evidence. If amount or sign cannot be reconciled, equity is NOT VERIFIED and all exposure increases fail closed.
2. **Historical and future funding:** never backfill missing historical funding as zero. Known amount with unknown owner remains an account-level legacy adjustment; unknown amount makes account equity NOT VERIFIED and blocks increases. Persist future modeled funding with amount, timestamp, source/snapshot identity, payload hash and strategy attribution. If funding is intentionally disabled for a paper test, persist explicit configuration/version evidence. Missing or stale funding required by the active model fails closed.
3. **Account Equity cutover:** do not seed aggregate equity from legacy single-position history unless capital, mark, realized PnL, fees and funding provenance reconcile. Compute once from initial capital + reconciled realized PnL + unrealized PnL for all migrated positions at one fresh mark − fees − funding. Seed HWM and UTC daily baseline only from a verified cutover snapshot and known UTC boundary. Otherwise preserve legacy data read-only, mark readiness false and block increases; valid reductions/closures remain allowed.
4. **1% current-equity margin:** each new ENTRY or exposure-increasing DCA receives a fixed admission-time margin reservation equal to 1% of current Account Equity. Store the equity basis, admitted leverage and risk-config version. Filled margin is filled notional divided by admitted leverage and cannot exceed the reservation. Partial fills consume proportionately; unfilled remainder stays reserved until completion/cancel/expiry, when unused reservation is released. Later equity changes do not recalculate an existing reservation; each later ENTRY/DCA uses then-current equity.
5. **Max Gross Exposure:** include filled gross position notional plus only remaining unfilled pending/reserved notional across Core, AI and legacy. Filled portions count only in position exposure; remaining unfilled portions count in reservations. Use absolute notional; never net opposing positions. Serialize concurrent admission within the same account transaction.
6. **Unknown-owner legacy position:** migrate the complete proven position/average/state to `LEGACY_UNATTRIBUTED`, never guess ownership. Block all new Core/AI ENTRY/DCA exposure account-wide while unattributed legacy exposure remains. Permit valid reduction/flatten through a dedicated reconciliation path. Reassignment requires immutable evidence and a separate user-approved auditable operation. Corrupt legacy state stops migration writes and preserves the original DB/backup for forward repair.

### Required acceptance tests added by approval

- Known unowned PnL/fees affect account equity exactly once and never Core/AI strategy statistics.
- Unknown historical funding blocks readiness; known unowned funding is counted once; future events require provenance; explicit disabled-funding configuration is auditable.
- Cutover requires a fresh mark and reconciled components; invalid legacy history cannot seed HWM/daily baseline.
- Every ENTRY/DCA reserves exactly 1% of admission-time equity; partial fills consume/release only the correct portions; later equity changes do not mutate existing reservations.
- Max Gross Exposure includes remaining pending reservations, without double-counting filled quantity or netting opposite sides; concurrent admission cannot over-reserve.
- Unattributed legacy positions block increases but allow dedicated reductions/closure; reassignment requires explicit immutable evidence and separate approval.

No unresolved design question remains among these six items. Any newly discovered ambiguity or unreconcilable evidence remains a hard stop and must fail closed; do not invent data.


## 9. Authorization boundary

The user has approved the Dual Ledger architecture contract and all six design decisions. This authorizes the documentation/schema/migration/test-specification design to be treated as approved. It does **not** authorize:
- source-code implementation;
- database migration or data rewrite;
- enabling the feature flag;
- paper backtests or performance claims;
- merge/deploy;
- exchange connectivity or live execution.

A separate explicit user approval is required before source implementation begins. All activity remains PAPER-only and `ai_execution_enabled=false`.
