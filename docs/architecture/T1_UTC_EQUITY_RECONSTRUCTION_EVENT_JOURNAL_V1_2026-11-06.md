# T1 UTC Equity Reconstruction — Account History Journal v1

Status: DESIGN CONTRACT / NOT IMPLEMENTED  
Date: 2026-11-06  
Scope: PAPER-only Dual Ledger account history required to reconstruct the account equity baseline at exactly 00:00:00 UTC.

## 1. Safety invariants

- This is an additive T1 design. Existing tables and legacy single-strategy history remain unchanged.
- No production/persistent account database is to be opened, migrated, or backfilled in this increment.
- No live exchange order, exchange credential, market-data network client, deployment, or backtest is introduced.
- Missing, stale, conflicting, unattributed, or unverifiable history is UNKNOWN, never zero. A failed reconstruction must leave the prior baseline unchanged and block all new exposure. Pure reductions/flattening remain available.
- Account history is account-wide and includes STRATEGY_CORE, AI_FREQAI, and LEGACY_UNATTRIBUTED. It must never merge strategy accounting ownership.
- Funding remains sourced from immutable `paper_funding_events` and `paper_funding_coverage`; the new execution journal must reference funding event IDs when needed, not duplicate funding amounts.

## 2. UTC boundary semantics

For a requested UTC day boundary `B = utc_day_ms`:

- Replay every accepted economic event with `event_at_ms < B`.
- Events with `event_at_ms == B` belong to the new UTC day and are excluded from the baseline.
- The market valuation is the verified mark whose `effective_at_ms == B` and whose documented source convention explicitly represents the instant at B. A nearby/latest mark is not a substitute.
- The baseline key is unique on `(account_id, utc_day_ms)`.
- Replay order is deterministic: `event_at_ms, strategy_id, event_id`; duplicate IDs with different canonical payloads are conflicts.
- A late-arriving event recorded after B with `event_at_ms < B` invalidates the completeness certificate for that day. It cannot silently mutate a committed baseline. Reconciliation must create a separately audited revision and keep exposure blocked until resolved.

## 3. Additive schema proposal (migration v6)

### 3.1 `paper_account_event_journal`

Append-only canonical economic event journal. Minimum columns:

- `event_id TEXT PRIMARY KEY`, `account_id`, `strategy_id` constrained to Core/AI/Legacy.
- `event_type` constrained to `FILL` or `LEDGER_ADJUSTMENT`.
- `event_at_ms`, `recorded_at_ms`, `order_id`, `intent_id`, `source_event_id`.
- For FILL: signed `quantity_delta_base`, positive `fill_price`, nonnegative `fee_quote`; one row per actual partial fill / consumed execution level, not one aggregate order.
- For LEDGER_ADJUSTMENT: explicit signed `position_delta_base`, explicit post-adjustment `average_entry_price`, signed `realized_pnl_delta_quote`, signed `fee_delta_quote`; all adjustment dimensions must be supplied and provenance-backed. An adjustment cannot be inferred from a changed aggregate ledger row.
- `source`, `source_snapshot_id`, `payload_hash`, `canonical_payload`, and `created_at_ms`.
- Idempotency: same `event_id` + identical canonical payload returns the prior result; same ID + changed payload raises a conflict and changes no state.
- UPDATE and DELETE triggers reject mutation. A payload hash is validated as SHA-256 syntax; external source-byte authenticity remains a separately verified concern.

A FILL changes its owning strategy's position/average entry, realized PnL (derived deterministically from prior position and fill), and fees. Funding is excluded from FILL and comes only from the existing funding ledger. A partial order must append a separate journal event for every individual fill.

### 3.2 `paper_account_history_coverage`

Completeness watermarks are evidence, not inferred row counts. Minimum columns:

- `coverage_id`, `account_id`, `stream_type` (`EXECUTION` or `MARKET_MARK`), nullable `strategy_id` (required for EXECUTION; null for MARKET_MARK).
- Half-open interval `[start_at_ms, end_at_ms)`, `status` (`VERIFIED` or `UNKNOWN`), `source`, `source_snapshot_id`, `payload_hash`, `recorded_at_ms`.
- Overlapping intervals are rejected; adjacent intervals are valid. Only contiguous VERIFIED coverage from the verified starting cutover through B can certify a replay.
- EXECUTION coverage must be supplied independently for Core, AI, and Legacy, including streams with zero events. A zero-event interval requires an explicit verified empty-stream statement.
- Late-arrival/correction signals invalidate the relevant verified coverage and force reconciliation; a coverage record cannot be silently overwritten.

### 3.3 `paper_market_mark_history`

Immutable account valuation observations:

- `mark_id`, `account_id`, `effective_at_ms`, `observed_at_ms`, `mark_price`, `candle_close_ms`.
- `source`, `source_snapshot_id`, `dataset_version`, `payload_hash`, `quality_status`.
- Unique source identity for an effective boundary mark; conflicting marks at B make reconstruction unavailable.
- For v1, only an explicit boundary mark with `effective_at_ms = B` and `candle_close_ms = B` is eligible. If the selected source cannot provide this convention, it must be reported as unsupported/UNKNOWN; do not interpolate or use the last observation without a separately approved deterministic policy.
- UPDATE/DELETE triggers reject mutation.

### 3.4 `paper_daily_equity_baselines`

Immutable daily reconstruction result:

- Unique `(account_id, utc_day_ms)`, baseline equity, mark ID, starting cutover ID, replay start/end, per-stream coverage IDs, event count, funding event count, reconstructed per-ledger positions/average entries/realized PnL/fees/funding, reconciliation digest, algorithm version, source SHA, and `recorded_at_ms`.
- Persist a canonical replay digest over ordered event IDs/payload hashes, funding IDs/payload hashes, exact mark ID/hash, starting cutover, coverage evidence, and algorithm version.
- Identical retry returns the existing baseline. A different digest for the same UTC day is rejected; no UPDATE/DELETE.
- Baseline insert, audit event, and readiness transition occur in one `BEGIN IMMEDIATE` transaction.

## 4. Reconstruction algorithm contract

1. Validate current migration checksums and the one-time account equity cutover.
2. Require a prior verified starting state at or before B. The starting state must provide all three ledger positions, average entries, realized PnL, fees, funding totals, initial capital, legacy adjustments, and provenance.
3. Require contiguous VERIFIED EXECUTION coverage for Core, AI, and Legacy from the starting state through B; require contiguous VERIFIED MARKET_MARK coverage and one exact eligible mark at B.
4. Require contiguous VERIFIED funding coverage through B using the existing funding provenance validator. Include funding events with `event_at_ms < B`; exclude events at B. All amounts and owner attribution must reconcile to ledger funding totals at the replay endpoint.
5. Replay each strategy's fills independently in deterministic order. Apply reductions/reversals using signed quantities and deterministic average-cost accounting; calculate realized PnL and fees from individual fill records. Apply only explicitly evidenced ledger adjustments. Do not import current aggregate state as replay evidence.
6. Value each final signed position at the exact boundary mark; calculate account equity from initial capital + all realized PnL + all unrealized PnL - fees - funding, with account-level legacy adjustments included exactly once.
7. Reconcile the replay result against independently persisted account/ledger statements and expected totals. Any mismatch, gap, duplicate conflict, unknown event, missing fee, unsupported adjustment, invalid provenance, stale/future timestamp, or nonfinite amount fails closed.
8. Atomically persist exactly one immutable baseline for B and the audit record. Keep HWM and prior daily baseline unchanged if any step fails. Only a verified baseline for the current UTC day can make daily-loss input available for new exposure.

## 5. API contract (proposed; not implemented)

- `record_account_history_event(db_path, **event)`: validates and appends one immutable execution/adjustment event transactionally. Identical retry is idempotent; conflicting retry fails.
- `record_account_history_coverage(db_path, **coverage)`: appends non-overlapping VERIFIED/UNKNOWN stream coverage.
- `record_market_mark_history(db_path, **mark)`: appends one immutable mark observation.
- `reconstruct_daily_equity_baseline(db_path, *, utc_day_ms, now_ms, source_sha)`: validates all evidence, replays, reconciles, and atomically inserts the daily baseline. It never mutates source events or silently repairs missing history.

These names are provisional until the RED contract is reviewed against the existing transaction boundaries. Implementations must write the journal row in the same SQLite transaction as the corresponding ledger/order/audit mutation; a separate post-commit journal writer is prohibited.

## 6. Backfill and migration

- Existing `paper_orders` aggregate fills and mutable `paper_audit` are not sufficient proof for historical per-fill fees or immutable event completeness.
- Backfill is allowed only where original execution-level evidence and fee policy are independently verified. Do not synthesize individual fills from `averagePrice`, estimate fee from current configuration, or assume empty intervals.
- Unprovable historical periods remain UNKNOWN. The system may begin a new verified history epoch only from a separately approved, fully reconciled cutover; this does not retroactively certify earlier dates.
- Migration v6 is additive, versioned, checksum-verified, transactional, restart-safe, and must preserve all existing rows and source tables. No persistent DB migration is authorized by this document.

## 7. Required RED test matrix

- missing execution coverage for any of Core/AI/Legacy blocks reconstruction;
- UNKNOWN/gapped/overlapping coverage blocks reconstruction; adjacent verified intervals are accepted;
- one partial fill per journal event reconstructs quantity, average entry, realized PnL, and fees;
- long-to-short and short-to-long reversals replay correctly without cross-ledger mutation;
- event exactly at B is excluded; event immediately before B is included;
- funding immediately before B is included; funding exactly at B is excluded;
- missing/conflicting/stale/non-boundary mark blocks reconstruction;
- identical event/baseline retry is idempotent; conflicting same-ID payload is rejected;
- late-arriving pre-B event invalidates coverage and blocks exposure pending reconciliation;
- UPDATE/DELETE attempts against journal, marks, coverage evidence, and baselines are rejected;
- failure at any stage rolls back baseline/audit/readiness changes and preserves the prior baseline;
- source DB byte-level immutability is proven for read-only inspection.

## 8. Explicit non-goals

No live trading, no exchange integration, no backtest certification, no persistent account DB migration, no deployment, no PR/merge, no T0 changes, and no change to Core RSI+ADX+Smart DCA parameters or independent Core/AI ledgers.
