# Dual Ledger — Open Decision Proposal

**Status:** APPROVED — six design decisions accepted; implementation remains separately gated  
**Date:** 2026-11-06  
**Branch:** `feature/t0-centralized-data-feeder-p1-20261101`  
**Scope:** Resolve the six open design questions in `DUAL_LEDGER_SCHEMA_MIGRATION_PLAN.md`.

This proposal converts the existing fail-closed contract into explicit decision defaults. It does not authorize source changes, database migration, feature activation, backtests, merge, deployment or exchange connectivity.

## Decision 1 — Historical realized PnL and fees without strategy provenance

**Proposal**
- Preserve the exact known aggregate realized PnL and fees as account-level `LEGACY_UNATTRIBUTED` adjustments.
- Include known amounts once in account-level equity reconciliation; do not assign them to Core or AI performance, DCA or strategy statistics.
- Keep historical orders/audit immutable. Attribute an individual historical fill only when immutable evidence proves its strategy owner.
- If amount or sign cannot be reconciled, mark account equity NOT VERIFIED and block exposure increases. Do not allocate proportionally or infer from current strategy.

**Reason:** preserves account economics without fabricating strategy performance.

## Decision 2 — Historical and future funding

**Proposal**
- Never backfill missing historical funding as zero.
- If historical funding is known in amount but not strategy owner, preserve it as an account-level legacy funding adjustment. If the amount itself is unknown, account equity remains NOT VERIFIED and new exposure remains blocked until reconciled.
- Going forward, persist every modeled funding event with amount, timestamp, source/snapshot identity, payload hash and strategy attribution. If funding is intentionally disabled in a specific paper test, persist the explicit configuration/version proving that choice rather than silently assuming zero.
- Missing/stale funding inputs required by the active account model make risk admission fail-closed.

**Reason:** separates “not charged by configured model” from “unknown because evidence is missing.”

## Decision 3 — Account Equity cutover baseline

**Proposal**
- Do not seed the new aggregate baseline from a legacy single-position equity-history row unless its capital, mark, realized PnL, fees and funding provenance all reconcile.
- Compute cutover equity once from initial capital + reconciled account-level/strategy realized PnL + unrealized PnL for all migrated positions at one fresh mark − fees − funding, with no duplicated capital or adjustments.
- Seed account HWM and UTC daily baseline only from a verified cutover snapshot and known UTC day boundary.
- If any required input is missing or inconsistent, migration may preserve data in read-only legacy form, but account risk readiness stays false and no new exposure is admitted until an explicit reconciliation establishes the baseline. Valid reductions/closures remain allowed.

**Reason:** avoids manufacturing an equity curve or drawdown baseline from incompatible legacy history.

## Decision 4 — Meaning of 1% current-equity margin

**Proposal**
- Treat 1% of current Account Equity as the **fixed admission-time margin budget** for each new ENTRY or exposure-increasing DCA, not merely a loose ceiling.
- Calculate `reserved_margin = equity_at_admission × 0.01`; calculate target notional from the same admission-time leverage/config snapshot.
- Actual filled margin is `filled_notional / admitted_leverage`; it must not exceed the reservation. For partial fills, consume the corresponding fraction and retain only the unfilled remainder as reserved; release unused remainder on completion/cancel/expiry.
- Record equity basis and risk-config version. Never recalculate an existing order's reservation from later equity or leverage.
- The next independent ENTRY/DCA uses the then-current account equity and gets a fresh 1% budget.

**Reason:** directly implements the user-approved “margin mỗi lệnh 1% tài khoản” rule while preserving deterministic admission and partial-fill accounting.

## Decision 5 — Max Gross Exposure and pending reservations

**Proposal**
- Max Gross Exposure includes filled gross position notional **plus unfilled pending/reserved notional** across Core, AI and legacy.
- Count filled portions only in position exposure; count only remaining unfilled portions in reservations. Never double-count a partial fill.
- Use absolute notional per ledger; opposing LONG/SHORT positions never offset.
- Apply the same aggregate rule to concurrent admission inside the single account transaction.

**Reason:** a pending order consumes future exposure capacity even before fill; otherwise concurrent Core/AI orders could exceed the limit.

## Decision 6 — Legacy position with unknown owner

**Proposal**
- Migrate the full position, average entry and proven position-specific state to `LEGACY_UNATTRIBUTED`; never guess Core or AI.
- Block every new exposure-increasing Core/AI ENTRY or DCA account-wide while unattributed legacy exposure remains.
- Permit valid reduction/flatten of the legacy position through a dedicated reconciliation path, even while new exposure is blocked.
- Reassignment to Core or AI requires an explicit, auditable reconciliation backed by immutable source evidence and a separate user-approved operation. No automatic reassignment.
- If legacy position quantity/average or related state is corrupt, stop migration writes and preserve the original DB/backup for forward repair.

**Reason:** prevents hidden exposure and false strategy attribution.

## Combined behavior and acceptance tests

If approved, these six decisions become normative schema/runtime requirements. Add focused tests for:
1. Known but unowned PnL/fees affect account equity once, never Core/AI strategy stats.
2. Unknown historical funding blocks readiness; known unowned funding is counted once.
3. Cutover baseline requires a fresh mark and reconciled components; invalid history cannot seed HWM/daily baseline.
4. ENTRY and DCA reserve exactly 1% of admission-time equity; partial fill consumes and releases only the correct portions.
5. Max Gross Exposure includes only remaining pending reservations, without double-counting fills or netting opposite sides.
6. Unattributed legacy position blocks increases but allows dedicated reduction/closure; reassignment requires explicit evidence.

## Approval boundary

A user approval of this proposal would close the six **design decisions** and authorize updating the schema/migration plan and test specifications only. It would **not** authorize source implementation, DB migration, feature flag activation, backtests, merge/deployment or any live execution. Those require separate explicit approval.


## Approval record — 2026-11-06

The user explicitly approved all six decisions in this proposal. They are now normative design requirements for the schema/migration plan and test specifications. This approval authorizes documentation updates only. It does not authorize source implementation, database migration/data rewrite, feature activation, backtests, merge, deployment, exchange connectivity or live execution. A separate explicit approval is required before implementation.
