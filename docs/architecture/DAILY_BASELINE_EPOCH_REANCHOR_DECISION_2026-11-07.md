# Daily Baseline Epoch Re-anchor — Architecture Decision (2026-11-07)

## Status

**PROPOSED — architecture only. Not approved for implementation or activation.**

This document evaluates a safe way to resume daily baseline progression when an immutable historical v1 baseline cannot be independently recovered. It does not authorize source changes, schema migration, persistent database access, backfill, or risk-state mutation.

## Current verified constraints

- The current daily baseline chain is sequential: the writer requires the immediately preceding UTC-day baseline to be verified.
- A v1 baseline without the v2 `riskState` evidence is rejected by risk snapshot validation, retry, and next-day rollover.
- The baseline table has a unique key on `(account_id, utc_day_ms)`; the current baseline identity is account/day-based, not epoch-based.
- Baselines reference the original immutable account cutover.
- The account risk state is a mutable current row; there is no independently retained immutable HWM/version/readiness history for every historical day.
- Repository-only inspection found no evidence sufficient to reconstruct those missing historical risk-state values.
- No persistent account database was opened or inspected for this decision.

## Options

### A. Preserve the strict chain indefinitely

Keep v1 unresolved and block all future baseline progression for the account.

Advantages:
- No reset or reinterpretation of drawdown history.
- No additional schema semantics.
- No risk of presenting a new HWM as the historical HWM.

Disadvantages:
- Daily baseline progression remains unavailable for this account.
- Existing v1 evidence gap remains operationally blocking.

This is the safest default until an independently verifiable new anchor is available.

### B. Start a separately identified baseline epoch

Create a new, immutable account-level anchor at a precise UTC boundary. The new epoch is a new risk-measurement period, not a repair or conversion of v1 history.

The old v1 baseline and audit remain unchanged and permanently unresolved. The new epoch must carry an explicit link to the prior epoch and a reason code such as `HISTORICAL_RISK_STATE_UNRECOVERABLE`.

A new epoch must not reuse or overwrite the original cutover. It needs a distinct anchor record and epoch identifier. Daily baseline identity/uniqueness must become epoch-aware (for example, unique `account_id, epoch_id, utc_day_ms`), while preserving all existing v1/v2 rows and their original identities.

## Minimum anchor evidence

The anchor is eligible for manual review only when all of the following are independently available:

1. **Account statement:** authoritative account-level statement or export with account identity, quote currency, equity, wallet balance, liabilities, and observation timestamp.
2. **Positions:** complete open-position inventory at the same boundary, including strategy/owner attribution, signed quantity, average entry, margin, unrealized PnL, and instrument identity. Unattributed positions must remain Legacy and block exposure increases until reconciled.
3. **Orders and reservations:** open/pending orders, remaining quantities and reservations, cancellations, and exchange/provider identifiers; no pending exposure may be omitted.
4. **Fees and funding:** complete fee and funding amounts through the anchor boundary, explicit quote currency, source identifiers, coverage interval, and raw source evidence. Unknown amounts are not zero.
5. **Market mark:** exact-boundary verified mark, closed-candle identity, dataset version, source, observation time, and independently checked source payload/hash.
6. **Ledger reconciliation:** Core, AI, and Legacy position/PnL/fee/funding totals reconcile to the authoritative statement with explicit tolerances and a deterministic reconciliation report.
7. **Risk-policy authorization:** explicit approval to begin a new measurement period and to reset the *new epoch's* HWM reference. This is a policy reset, not a claim about the missing historical HWM.

A screenshot or a displayed balance alone is insufficient if positions, liabilities, pending orders, fees, or funding are not fully represented.

## HWM and Daily Loss semantics

If a new epoch is explicitly approved and anchored at exactly 00:00:00 UTC:

- The anchor equity is the epoch's opening equity.
- The epoch HWM starts at that verified opening equity. It is a **new epoch HWM**, not a reconstructed historical HWM.
- The first daily-loss baseline equals the verified epoch opening equity at that UTC boundary.
- Events with `event_at_ms < boundary_ms` belong to the prior history; events at or after the boundary belong to the new epoch.
- Daily loss is measured against the immutable baseline for the current UTC day. It must not silently inherit an unknown v1 daily baseline.
- Drawdown is measured from the new epoch HWM. Reports must label the epoch start and disclose that historical drawdown continuity is unavailable.
- If the anchor is not exactly at a UTC boundary, do not admit exposure under a daily-loss policy until the next UTC boundary has a complete, verified replay from the anchor. Do not interpolate or invent the missing boundary value.

This explicitly creates a new risk reference frame. It does not erase or certify the old one.

## Proposed data model (not implemented)

- `paper_account_baseline_epochs`: immutable epoch ID, account ID, prior epoch ID, start boundary, reason code, policy version, source statement ID/hash, mark ID, dataset identity, opening equity, opening HWM, approval reference, recorded timestamp, source SHA.
- `paper_account_epoch_ledger_anchors`: one immutable Core/AI/Legacy anchor snapshot per epoch, with positions, average entry, realized PnL, fees, funding, reservations/open-order references, source IDs and payload hashes.
- Daily baselines and audit rows become epoch-scoped, with immutable uniqueness on account + epoch + UTC day. Existing v1/v2 records are not rewritten.
- Risk state stores the active epoch ID and epoch-specific HWM/daily baseline. Every epoch activation is an append-only audited transition.
- Replay coverage and event streams are scoped to the epoch's start boundary; any event arriving late with economic time before a boundary invalidates completeness and blocks increases pending audited reconciliation.

The exact FK and migration strategy requires a separate schema design and compatibility review. Do not add nullable epoch IDs to old records and silently infer their epoch.

## Admission and recovery rules

- Before activation, all Core/AI/Legacy positions, open orders and reservations must be accounted for.
- Epoch creation, anchor snapshots, initial daily baseline, risk-state activation, and audit event must commit atomically.
- Idempotency key includes account ID + epoch ID + anchor boundary + source statement digest. Same evidence is idempotent; conflicting evidence is rejected.
- Any missing or contradictory source, mark, funding, fee, position, or risk-policy evidence leaves the epoch inactive and risk unready.
- Kill Switch blocks exposure increases during review and activation. Only risk-reducing operations may be considered, subject to existing controls.
- No automatic conversion of v1 to v2 and no mutation/deletion of old rows.
- A new epoch does not automatically authorize trading or production readiness. It only establishes a separately defined risk-measurement anchor for subsequent PAPER validation.

## Decision recommendation

Use **Option A as the current operational state**: keep the account blocked and v1 immutable.

Design Option B only as a future, separately approved capability. Do not implement or activate it until an authoritative account statement and complete position/order/fee/funding/mark evidence can be obtained and independently reconciled. If those sources are unavailable, retain the block; do not fabricate continuity.

## Verification required before any implementation approval

1. Independent source inventory and byte-level authenticity checks.
2. Reconciliation of account equity and every Core/AI/Legacy position at one exact UTC boundary.
3. Explicit treatment of pending orders, partial fills, reservations, fees, funding, and unattributed Legacy state.
4. Migration compatibility proof preserving all old rows and immutable triggers.
5. Atomic crash/reopen, retry, conflict, and rollback tests.
6. Fail-closed tests for missing/stale/late/contradictory evidence and Kill Switch.
7. Separate user approval for schema changes, persistent DB access, and epoch activation.

## Restrictions

No persistent account DB opening or migration, no backfill, no production backtest, no exchange connection, no deployment, no merge, and no live orders are authorized by this document. T0 remains paused. PAPER-only; `ai_execution_enabled=false`.
