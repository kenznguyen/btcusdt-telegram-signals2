# T0 Single Writer Gateway — Implementation and Verification

Date: 2026-11-05 (UTC)

## Scope

Implemented the SQLite canonical write Gateway on the existing PR #134 branch. This increment centralizes Binance USD-M candle writes behind a lease-fenced batch API and removes the legacy unfenced writer entrypoints.

- Branch: `feature/t0-atomic-write-fencing-20261105`
- PR: https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/134
- Exact source SHA validated by push workflow: `dbfc402fe41772952d9a7ad718eace124af388ab`
- Gateway: `market_data/write_gateway.py`
- Workflow: `.github/workflows/t0-single-writer-gateway-red.yml`

## Changes

1. Added `SQLiteWriteGateway.write_batch()`. It validates the owner/generation/expiry lease inside the same SQLite `BEGIN IMMEDIATE` transaction as the candle batch, rechecks lease validity immediately before commit, and rolls back the complete batch on any error.
2. Added `ShadowWriteGateway`, a non-persistent sink for manual Shadow inspection.
3. Routed `sync_window()` through `write_batch()`; it no longer calls an unfenced `store.insert()`.
4. Routed Feeder scheduler and recovery composition through `SQLiteWriteGateway`; removed the legacy `FencedCandleWriter` adapter.
5. Removed `CandleStore.insert()`, `CandleStore.insert_fenced()`, and write methods from the canonical storage facades.
6. Disabled PostgreSQL canonical writes. PostgreSQL remains a read-only adapter until same-transaction lease fencing is independently implemented and accepted.
7. Made the standalone sync CLI require explicit `--shadow-only`; it reports candidates and never persists them.
8. Updated canonical store, API, sync, storage, Gateway, and Feeder regression fixtures to use the Gateway. Kraken Spot's isolated store remains separate and unchanged.

## GitHub Actions evidence

- Run ID: `41976841830`
- URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41976841830
- Event: `push`
- Exact branch source and checkout SHA: `dbfc402fe41772952d9a7ad718eace124af388ab`
- Conclusion: `success`
- Job ID: `127077555829`; all steps completed successfully.
- Shadow-only environment preflight: PASS; Python compile: PASS.
- Static Gateway contracts: 10 tests, PASS.
- Gateway + canonical store + sync + storage + Feeder lifecycle regression: 52 tests, PASS.
- Complete `market_data` suite: 173 tests, PASS; 8 skipped.
- Final full-suite output: `Ran 173 tests ... OK (skipped=8)`.

Artifact:
- ID: `13392126852`
- URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41976841830/artifacts/13392331551
- Size: 7,596 bytes
- GitHub digest: `sha256:42d85c6bd30520a22ddaff8eeb3a03089d78d29fcc5e5245eec4cc9d50f34707`
- Artifact payload checksum has not been independently recomputed.

## Status

- Gateway static acceptance contracts: PASS.
- Atomic SQLite lease fencing and batch rollback tests: PASS.
- Takeover serialization test: PASS.
- Sync, API, storage and Feeder lifecycle regression: PASS.
- Concrete composition test: scheduler and recovery use the same Gateway instance and lease database; PASS.
- Complete `market_data` suite: PASS with 8 skipped TimescaleDB integration tests.
- PostgreSQL canonical write API: DISABLED; TimescaleDB integration remains NOT VERIFIED.
- Kraken Spot isolated storage: unchanged and not part of this Gateway.
- Full process-level crash/restart and independent Paper Writer Gate acceptance: NOT VERIFIED.
- T0 production readiness / canonical ingestion authorization: NOT GRANTED.
- PR #134: OPEN / DRAFT / NOT MERGED.

## Safety boundary

GitHub Actions ran temporary-directory SQLite unit tests and local API/Feeder tests only. No production database, configured exchange credentials, live Feeder process, exchange write endpoint, market-data collector, migration, or order execution was used. No strategy, AI signal, Shared Risk Engine, or live-trading behavior changed. `ai_execution_enabled=false` remains unchanged.

## Next step

Add concrete Feeder composition tests that prove scheduler and startup recovery use the Gateway with the same lease database, then separately verify Paper Writer Gate and process crash/restart semantics. Keep PostgreSQL writes disabled until a separately approved, equivalent same-transaction fencing implementation and integration evidence exist. Do not merge without explicit user approval.
