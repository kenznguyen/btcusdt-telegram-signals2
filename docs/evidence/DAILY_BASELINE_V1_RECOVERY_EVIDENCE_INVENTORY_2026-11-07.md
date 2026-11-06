# Daily Baseline v1 Recovery — Repository Evidence Inventory

**Inspection status:** READ-ONLY SOURCE/SCHEMA INVENTORY  
**Result:** BLOCKED for v1-to-v2 historical recovery using repository-retained evidence alone.  
**No account database was opened. No migration, backfill, or data mutation was performed.**

## Exact source inspected

Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Branch HEAD at inspection start: `ae9ee62b27cb67de2df755dc1f524ae1558c93e5`

| File | Blob SHA | Relevant evidence |
|---|---|---|
| `paper_execution/account_history.py` | `6163065798b2386e1c466650048e40b7eab0d2eb` | v6 event journal, coverage and mark history; v7 per-ledger cutover snapshots; v9 immutable baseline audit |
| `paper_execution/ledger.py` | `0bc94ae0e704a69e253246a575991c1de436e0a4` | mutable current risk-state row; mutable order/audit tables; event journal writes |
| `paper_execution/funding.py` | `575758eb3223b4341ac37bad56d58e52539305c0` | immutable funding events/coverage; immutable cutover; cutover HWM snapshot; mutable risk-state refreshes |
| `paper_execution/equity.py` | `40d6566294355c646839614c92f8fba6116b582c` | legacy single-strategy equity history and first-observed daily baselines |
| `paper_execution/risk_control.py` | `3c76e462b0b4d924c2418842d95ed74285e2315d` | shared kill/pause latch; no historical account risk-state snapshots |

## Findings

### 1. Immutable evidence that exists

- v6 `paper_account_event_journal` is append-only and records event time, recorded time, strategy owner, order/intent/source IDs, signed fill/adjustment data, fee amount/currency (v8), source snapshot, payload hash and canonical payload.
- v6 `paper_account_history_coverage` is append-only and can attest VERIFIED/UNKNOWN execution and market-mark intervals independently for Core, AI and Legacy.
- v6 `paper_market_mark_history` is append-only, has a unique mark per effective timestamp, and records exact boundary mark, candle close, source snapshot, dataset version, hash and quality status.
- v7 `paper_account_cutover_ledger_snapshots` is append-only and stores Core/AI/Legacy positions, average entry, realized PnL, fees, funding and provenance at the one verified cutover.
- v4 funding events and funding coverage are append-only with source/recorded timestamps, coverage status, source snapshot and hash. Legacy events are marked `LEGACY_UNVERIFIED`; they cannot be treated as verified.
- v5 `paper_account_equity_cutovers` is append-only and stores cutover equity, mark, funding interval, HWM and daily baseline at cutover.
- v9 `paper_daily_equity_baselines` and `paper_daily_equity_baseline_audit` have immutable UPDATE/DELETE triggers. A v1 audit payload remains immutable, but it does not contain the v2 `riskState` snapshot.

These sources can support replay of some historical economics when complete coverage and provenance exist. Their presence does not prove the risk state at a later historical daily-baseline commit.

### 2. Required historical risk evidence is absent

- `paper_account_risk_state` is a single mutable row. Its HWM, daily baseline, last equity/mark, readiness, timestamp and version are overwritten as activity proceeds.
- No immutable per-day or per-version risk-state history table was found in the inspected `paper_execution` schema.
- The v7 per-ledger snapshots exist only at the cutover; they are not repeated at every daily baseline.
- `paper_account_equity_cutovers` preserves HWM/readiness inputs at the cutover only. It cannot establish HWM, readiness or `version` at a later daily baseline timestamp.
- The code increments the mutable risk-state version during fills/reductions and funding/equity refreshes, but those mutations do not create an immutable before/after risk-state snapshot.
- Therefore the historical `high_water_mark_quote`, `version` and `risk_ready` required by the v2 audit cannot be independently proven for a v1 baseline from these tables alone.

### 3. Other historical evidence limits

- `paper_audit` is created as a normal table without immutable UPDATE/DELETE triggers. It records order, funding and cutover events, but is not a tamper-resistant risk-state history.
- `paper_orders` stores aggregate order/fill state and is updated for lifecycle changes. It is not a complete immutable per-fill source for older history.
- `paper_equity_history` and `paper_daily_baselines` are legacy single-strategy history. The former is not protected by immutable triggers; the latter can be updated when an earlier observation arrives. Neither certifies the dual-ledger account HWM/version at a v1 baseline.
- v8 intentionally leaves historical fee currency unknown rather than guessing. Any pre-v8 journal row without explicit USDT currency blocks a complete fee reconciliation.
- Source payload hashes in local tables are syntax/provenance fields; repository code does not retrieve original external payload bytes and independently rehash them. The evidence manifest's raw-byte rehash attestation cannot be inferred from a stored hash string.

## Manifest assessment

| Manifest requirement | Repository-only result |
|---|---|
| Baseline row + immutable v1 audit pair | Schema supports it; actual persistent rows not inspected |
| Replay inputs, per-ledger cutover snapshots | Schema supports these sources; historical interval completeness not proven here |
| Continuous execution/funding coverage | Schema and validators support proof; actual persistent coverage not inspected |
| Exact boundary mark | Schema supports it; actual persistent mark not inspected |
| Independently verified historical risk snapshot at v1 baseline time | **NOT FOUND** |
| Original source payload bytes rehashed | **NOT AVAILABLE from repository schema/code alone** |

**Overall:** `BLOCKED`. The pure manifest assessor must not be given `risk_state.independently_verified=true` or raw-byte rehash attestations unless independently retained evidence is actually produced and verified. A current mutable risk row, cutover-only snapshot, audit digest, or legacy equity history cannot substitute for missing historical risk state.

## Safe handling

1. Keep v1 rows immutable and fail-closed.
2. Do not synthesize historical HWM, version, readiness, mark provenance, fee currency, or missing events.
3. Do not infer authenticity from stored hash syntax.
4. If independent external evidence is later found, assemble the manifest and assess it read-only; a positive result permits manual review only.
5. Any conversion/reconciliation transaction requires a separate explicit approval and its own RED/GREEN tests.

## Scope limits

This was a source/schema inspection only. It did not inspect a persistent account DB, enumerate real v1 rows, verify live data availability, migrate, backfill, deploy, connect to an exchange, or place orders. T0 remains paused; paper-only execution and `ai_execution_enabled=false` remain unchanged.


## 2026-11-07 — Independent archive/checkpoint repository scan

A second read-only inventory was performed against the recursive Git tree at branch commit 2eb17051dd93a9c36b1e9be45333168793546702 after the Dual Reconstruction contract was committed.

- Git tree contained 279 paths and was not truncated.
- No tracked files with database, SQLite, JSONL/NDJSON, CSV, Parquet, Arrow, archive, binary payload, checksum-manifest, or equivalent raw event/checkpoint data extensions were found.
- The evidence directory contains documentation reports/manifests, not a retained raw event archive or independent account checkpoint.
- The tree contains source code for the event journal, funding, ledger and baseline logic; source code is not a second evidence root.
- The scan does not enumerate or download GitHub Actions artifact payloads, private Project attachments, local PC/Android files, or any separately retained external archive. Those sources remain NOT INSPECTED.
- The prior immutable event journal/coverage/mark tables and cutover snapshots described above are schema capabilities. Because the persistent account DB was not opened, their actual rows, completeness, raw source bytes, and independence from a second checkpoint remain NOT VERIFIED.

**Result:** INDEPENDENT_SECOND_ROOT_NOT_FOUND_IN_TRACKED_GIT_TREE. The repository alone currently provides no discoverable separately retained event archive/checkpoint suitable for Reconstruction B. This does not prove that no such evidence exists outside the tracked Git tree. Do not treat a pair of computations over the mutable account DB as independent verification. Keep the candidate BLOCKED unless an external retained evidence root is identified and byte-verified.

No account DB was opened; no artifacts were downloaded; no source, schema, tests, workflow, migration, or data were changed.
