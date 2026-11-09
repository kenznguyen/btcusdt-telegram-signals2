# T0 Active Scope Index

- Date: 2026-11-10
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Source baseline before this documentation change: `3811277f746a4cc4a777b25da68e8e56b63b5229`
- Basis: T0 scope minimization review and T0 simplification dependency review second pass.
- Purpose: distinguish the selected canonical T0 runtime from optional, research, support and assurance workstreams. This index does not certify production readiness.

## 1. Scope at a glance

| Workstream | Classification | Current disposition | Counts as active canonical T0 runtime? |
|---|---|---|---|
| Binance USD-M BTCUSDT M15/H1 + SQLite + Feeder + read-only Candle API | Canonical runtime | ACTIVE / KEEP | Yes |
| PostgreSQL backend, migrations and qualification | Optional backend | PARKED; SQLite remains selected default | No |
| Kraken Spot modules, store, API and tests | Separate research domain | PRESERVE / ISOLATED | No |
| Binance connectivity probe | Manual support diagnostic | SUPPORT-ONLY; explicit invocation | No |
| Evidence Object / Checkpoint G0–G3 | Separate assurance workstream | PRESERVE EXISTING RECORDS; freeze feature expansion | No |

## 2. Canonical active runtime — KEEP

The minimum active T0 responsibility is limited to:

1. Acquire canonical Binance USD-M perpetual BTCUSDT M15/H1 candles through the existing CCXT public-data path; no exchange API key is required.
2. Validate market identity, timeframe, timestamps, closed-candle state and OHLCV.
3. Persist canonical candles through the SQLite single-writer/lease fencing path, with guarded recovery and fail-closed behavior.
4. Expose the bounded, authenticated, read-only Candle API for authorized consumers.
5. Preserve canonical data and recovery copies; no automatic deletion, TTL, archive, cleanup, compaction, vacuum or backup expiry.
6. Retain regression coverage for the writer, lease, recovery, integrity, API contract and consumer compatibility.

The inspected active dependency chain is:

```text
feeder_service
  -> production runtime composition
  -> SQLite storage factory (selected default)
  -> FeederRuntime / Scheduler / RecoveryCoordinator
  -> sync_window
  -> SQLiteWriteGateway + LeaseStore (same database fencing boundary)
  -> SQLite WAL keeper
  -> bounded read-only market_data.api
  -> T2 CandleHttpClient -> GET /v1/candles
```

Keep the following components together unless a future behavior-preserving refactor is separately reviewed: `market_data/feeder.py`, `feeder_service.py`, `store.py`, `sync.py`, `write_gateway.py` SQLite writer/WAL components, `storage.py` SQLite facade, `api.py`, explicit SQLite initialization/migrations and T0 regression tests.

## 3. Parked optional backend — PostgreSQL

- PostgreSQL support exists as an optional backend path; it is not the selected canonical runtime.
- It is not fully isolated at import/package level: PostgreSQL modules are imported by shared composition/storage code and `requirements-market-data.txt` currently installs psycopg unconditionally.
- Disposition: PARK. Do not remove PostgreSQL adapters, migrations, tests or driver in this scope pass.
- A future packaging/lazy-import proposal must first map all import paths, test commands, workflow jobs and opt-in qualification paths. No implementation or dependency change is authorized by this index.

## 4. Separate research domain — Kraken Spot

- Kraken Spot uses a separate market identity, store, API and dedicated tests.
- It is not canonical Binance USD-M BTCUSDT data, a failover source, or a proven input to Futures strategy/paper execution.
- Disposition: PRESERVE AS AN ISOLATED RESEARCH DOMAIN; exclude it from the active canonical T0 readiness denominator.
- Do not merge it into the canonical schema/Feeder/API or delete it based only on its exclusion from active T0.

## 5. Support-only diagnostic — Binance connectivity probe

- The connectivity probe is an explicitly invoked diagnostic for public REST/WebSocket reachability.
- It does not start the Feeder, write canonical storage or substitute for runtime ingestion acceptance.
- Disposition: KEEP AS SUPPORT-ONLY; exclude from the always-on runtime dependency graph.
- Do not invoke it as part of this documentation-only work.

## 6. Separate assurance workstream — Evidence Object / Checkpoint G0–G3

- Checkpoint evidence and its synthetic reference tests/workflow are not prerequisites for basic SQLite ingestion or read-only API operation.
- Preserve their contracts, evidence and blocker history in their own assurance scope; do not inflate minimum T0 runtime acceptance with TSA, WORM, Root A/Root B or L4-Extended requirements.
- Current assurance status remains: G2 exact-SHA CI execution NOT VERIFIED; G3 independent review PENDING / NOT VERIFIED; L4-Minimum operational acceptance BLOCKED / NOT VERIFIED.
- This index does not close or waive any assurance gate and does not authorize additional feature expansion, staging or production execution.

## 7. Cross-cutting restrictions

- Option C — No Destructive Authority — remains in force. Reading, using, consuming, verifying or ACKing data does not authorize deletion.
- No default TTL, deletion-after-use, cleanup, archive, compaction, vacuum, backup expiry or replica removal.
- No changes to canonical data, database, Feeder, VPS, provider, keys, permissions, runtime or live consumers.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- No workflow path narrowing, test-denominator reduction, source retirement or dependency removal is approved by this index.
- Android Chart/Scanner and the separate Python bot/backtest are outside the 5-layer system and are not T0 dependencies.

## 8. Evidence and limitations

- T0 scope classification: `docs/evidence/T0_SCOPE_MINIMIZATION_REVIEW_2026-11-10.md`.
- Dependency/retirement review: `docs/evidence/T0_SIMPLIFICATION_DEPENDENCY_REVIEW_SECOND_PASS_2026-11-10.md`.
- Selected active SQLite source/workflow mapping: PASS for inspected paths.
- Full repository call graph, all workflow jobs, branch protection, deployed package/runtime and live consumer inventory: NOT VERIFIED.
- Tests and GitHub Actions: NOT RUN / NOT DISPATCHED for this index.
- Independent review: NOT PERFORMED.
- No source, test, workflow, package, schema, runtime, VPS, database, provider, key, permission or data changes.

## 9. Next safe step

Perform a separate documentation cross-reference review to decide whether this index should be linked from `market_data/README.md` or another maintained navigation document. Do not modify source, package dependencies, workflow triggers or acceptance denominators as part of that review.
