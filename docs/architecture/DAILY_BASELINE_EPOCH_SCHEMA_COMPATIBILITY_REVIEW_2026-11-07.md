# Daily Baseline Epoch — Schema Compatibility Review (2026-11-07)

## Status

**DESIGN REVIEW ONLY — NOT APPROVED FOR IMPLEMENTATION.**

This review turns the proposed epoch concept into a compatibility-oriented schema direction. It does not modify source, migrations, tests, workflows, or any database.

## Existing schema constraints observed

Current source defines:
- Migration v6: immutable account-history streams, market marks/coverage and `paper_daily_equity_baselines`.
- Migration v7: immutable `paper_account_cutover_ledger_snapshots`, one row per `cutover_id + strategy_id`.
- Migration v8: explicit fee currency provenance.
- Migration v9: immutable `paper_daily_equity_baseline_audit`.
- Daily baseline key: `UNIQUE(account_id, utc_day_ms)`.
- Baseline foreign key: `starting_cutover_id -> paper_account_equity_cutovers(cutover_id)`.
- Audit key: `UNIQUE(account_id, utc_day_ms, event_type)`; audit row references the baseline row.
- Current writer validates the predecessor baseline and uses the account's single cutover identity.

These constraints make retrofitting an epoch ID into the existing tables risky: SQLite table rebuilds can affect foreign keys, immutable triggers, migration checksums, and historical row identity. Existing v1/v2 rows must not be rewritten to infer an epoch.

## Recommended compatibility strategy: additive parallel epoch tables

Do not rebuild or alter the existing v6/v9 baseline and audit tables in the first epoch migration. Leave the existing writer and strict predecessor validation unchanged for the legacy chain.

Introduce a separate epoch-scoped namespace, with its own writer and reader:

### 1. `paper_account_baseline_epochs` (immutable)

Suggested fields:
- `epoch_id` primary key
- `account_id` foreign key
- `prior_epoch_id` nullable self-reference (first epoch has no predecessor)
- `prior_legacy_cutover_id` reference to the original cutover, for provenance only
- `start_boundary_ms` with UTC-day alignment check
- `reason_code` constrained to an enumerated recovery reason
- `policy_version`
- `opening_equity_quote`, `opening_hwm_quote`
- `source_statement_id`, `source_statement_sha256`
- `mark_id`, `dataset_version`
- `approval_reference`
- `recorded_at_ms`, `source_sha`, canonical payload and payload digest

Require unique `(account_id, epoch_id)` and unique `(account_id, start_boundary_ms)` unless an explicit product decision allows multiple reviewed candidates at the same boundary. A candidate epoch is not active merely because its row exists.

### 2. `paper_account_epoch_ledger_anchors` (immutable)

One row per epoch and exactly one of Core, AI, Legacy:
- `epoch_id`, `strategy_id`
- signed position and average entry
- realized PnL, fees and funding with explicit quote currency
- margin attribution
- open-order and reservation inventory digest/references
- source snapshot ID, source payload hash, canonical payload, recorded time

Primary key `(epoch_id, strategy_id)`. Activation requires exactly three valid snapshots and reconciled aggregate totals.

### 3. `paper_epoch_daily_baselines` and `paper_epoch_daily_baseline_audit` (immutable)

Use a new table rather than rebuilding `paper_daily_equity_baselines`:
- baseline primary key is epoch-qualified;
- unique `(account_id, epoch_id, utc_day_ms)`;
- epoch FK plus mark FK;
- replay digest, algorithm version, source SHA, recorded timestamp;
- audit row references the epoch baseline and includes canonical payload/digest;
- immutable UPDATE/DELETE triggers on both tables.

The first baseline at `epoch.start_boundary_ms` is the epoch opening equity. Subsequent days must chain to the immediately preceding verified baseline **within the same epoch**. There is no implicit fallback to the legacy baseline table.

### 4. Append-only activation events; no mutable active pointer

Use `paper_account_epoch_events` with event types such as `EPOCH_CANDIDATE_CREATED`, `EPOCH_ACTIVATED`, `EPOCH_SUSPENDED`. Rows are immutable and carry actor/approval reference, timestamp, source digest and canonical payload.

Derive the active epoch from the latest valid activation/suspension event inside a transaction. Enforce at most one active epoch per account through a transactional admission check and a unique/partial index only if the supported SQLite version is pinned and verified. Do not rely on an application-only check without a database constraint or serialized transaction.

An epoch candidate must not affect risk readiness. Activation must be a separate, explicit operation and audit event.

### 5. Risk-state integration

Do not add a nullable `epoch_id` to the existing risk row and silently backfill it. Do not reset existing HWM or daily baseline in place.

A future implementation must choose one of two explicit strategies:
- **Preferred:** introduce an epoch-scoped immutable risk reference table and make the risk snapshot resolver select the active epoch, while retaining legacy risk state as historical/read-only evidence; or
- **Alternative:** add a new epoch-aware risk-state table and transactionally activate it while keeping the old row untouched.

Either strategy requires a dedicated compatibility design for all readers/writers. Until then, the legacy risk snapshot must remain not-ready and exposure increases blocked. A separate epoch baseline table alone is insufficient to authorize increases.

## Migration sequencing (proposed only)

- v10: additive epoch, ledger-anchor, epoch daily baseline/audit, and epoch event tables; immutable triggers; strict schema/checksum verification. No backfill of legacy rows.
- v11 (only after separate review): epoch-aware read-only risk snapshot resolver and invariant checker.
- v12 (only after separate approval): atomic epoch activation and epoch-scoped baseline writer, including risk admission integration.

Do not bundle all versions into one large migration. Each version needs its own RED/GREEN contract, checksum, idempotent re-entry, partial-schema detection, rollback test, and GitHub Actions evidence. Exact migration numbers must be rechecked against the branch at implementation time.

## Compatibility invariants

1. Existing v1/v2 baseline and audit rows remain byte-for-byte unchanged.
2. Existing v6/v7/v8/v9 migration checksums and immutable triggers remain unchanged.
3. Legacy writer continues to fail closed for an unresolved v1 predecessor.
4. An inactive epoch candidate cannot change current risk state or admit exposure.
5. Epoch activation is atomic with anchor validation, exactly three ledger snapshots, opening baseline, audit, and risk-state selection.
6. Duplicate identical activation is idempotent; conflicting source digest or approval reference is rejected without mutation.
7. A crash at any point yields either no activation or one fully committed activation; never partial activation.
8. Missing/late/unknown execution, fee, funding, market mark, order reservation or source evidence blocks activation.
9. Old legacy cutover is referenced for provenance only; it is not rewritten or re-used as the new epoch anchor.
10. The new HWM is explicitly labeled epoch HWM and never represented as historical HWM continuity.

## Required tests before implementation can be considered

- Migration on fresh fixture and on a fixture with v6-v9 already applied.
- Migration re-entry, checksum mismatch, partial table/trigger detection, and rollback.
- Verify exact old baseline/audit row bytes and triggers before/after migration.
- Verify all existing v1 retry and predecessor rollover fail-closed tests remain green.
- Missing/duplicate Core, AI, or Legacy anchor rejection.
- Incomplete orders/reservations and unattributed Legacy rejection.
- Fee/funding unknown, late, overlapping, missing coverage and bad source-hash rejection.
- Inactive candidate has no effect on risk snapshot.
- Epoch activation atomicity, idempotency, conflict, crash/reopen and process-kill recovery.
- Exactly one active epoch per account under concurrent activation attempts.
- Risk increase blocked before activation and after any activation validation failure.
- Epoch HWM/daily-loss reporting clearly separates new period from unrecovered history.

## Approval gates

This document does not approve:
- choosing Option B as product/risk policy;
- adding migrations or source code;
- opening or migrating the persistent account DB;
- importing/backfilling account statement or exchange data;
- activating an epoch or resetting HWM;
- running a production backtest, connecting to an exchange, deploying, merging, or placing orders.

Before any implementation, obtain separate approval for the epoch policy, the exact schema strategy, the external evidence source, and persistent DB access/activation. The current operational state remains Option A: strict chain, unresolved v1, no exposure increases.
