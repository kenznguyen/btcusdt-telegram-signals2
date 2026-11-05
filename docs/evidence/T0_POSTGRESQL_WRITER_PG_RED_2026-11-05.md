# T0 PostgreSQL writer PG-RED evidence — 2026-11-05

## Scope

Define the required PostgreSQL/TimescaleDB lease-fenced canonical writer contract before implementation. This is an intentional RED baseline, not a production failure or a passing acceptance result.

No PostgreSQL writer, lease table migration, runtime routing, or production configuration was implemented. Existing SQLite behavior was not changed. The TimescaleDB service was a disposable local GitHub Actions service using synthetic test candles only.

## Source identity

- Branch: `feature/t0-atomic-write-fencing-20261105`
- Exact tested head SHA: `b9111a022d3e66f7a17032e40f9597bc7e24e38f`
- Workflow: T0 Single Writer Gateway Contracts
- Run: [#42019166710](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42019166710)
- Event: push
- Static job: `127217729954` — SUCCESS
- TimescaleDB service job: `127217896416` — FAILURE at intentional RED step

## Contract tests

Added `market_data/test_postgres_write_gateway.py` with seven contracts:

1. Current owner and generation commit a complete batch with decimal precision preserved.
2. Wrong owner and stale generation are rejected without rows.
3. Expired lease is rejected using database time.
4. Identical duplicate is idempotent; conflicting candle rejects and rolls back the whole batch.
5. Invalid candle rejected by PostgreSQL constraints rolls back the whole batch.
6. Concurrent takeover waits for the writer's lease-row transaction; expiry causes old batch rollback; replacement generation fences old writer.
7. Heartbeat and release are bound to exact owner/generation.

The suite fails at the expected missing public API: `PostgresLeaseStore` does not yet exist in `market_data.postgres`. The run reports 7 tests, 7 errors, all at setup/import. This confirms the PostgreSQL lease/writer interface is not implemented; it does not yet validate deeper transaction semantics.

## CI evidence

Exact-head run #42019166710:

- Static Gateway contract verification: SUCCESS.
- Existing Gateway/Feeder behavior, health/readiness, process restart, and full `market_data` static suite: SUCCESS.
- PostgreSQL writer RED contracts: expected failure, 7 errors due to missing `PostgresLeaseStore`.
- Existing read-only TimescaleDB integration step: SKIPPED because the preceding RED step failed under `set -e`; it was not represented as PASS for this run.

Artifacts:
- Static evidence ID `13410937055`; SHA-256 `544b8b77603727cc2261935830ca24259b689ff4f78f84e30446b944dfede5ae`.
- Timescale service evidence ID `13410853344`; SHA-256 `5098c1703998bce6275a5be3c2dfe29c1b54e1dc1e9059b873e717ee1d83ab10`.

A preceding workflow run #42018870960 also observed the same missing API, but its source preceded the final test-fixture hardening. The authoritative RED baseline for this record is run #42019166710 on exact head `b9111a0...`.

## Status

- Contract test source: RECORDED.
- Expected RED condition: CONFIRMED.
- PostgreSQL lease store: NOT IMPLEMENTED.
- PostgreSQL write gateway: NOT IMPLEMENTED.
- Atomic lease/candle transaction semantics: NOT VERIFIED.
- PostgreSQL writer acceptance: BLOCKED pending implementation.
- Existing SQLite regression suite: PASS in exact-head static job.
- Read-only TimescaleDB integration: NOT RUN in this run because the intentional RED step stopped the job.
- Production DB, VPS, Binance connection, Feeder activation, and live trading: NOT USED / NOT AUTHORIZED.

## Next increment — PG-GREEN

Implement the minimum PostgreSQL lease lifecycle and write gateway to satisfy these tests, with:
- one PostgreSQL transaction for lease row lock, owner/generation/expiry validation, candle batch, final expiry check, and commit;
- database-clock expiry checks using `clock_timestamp()`;
- atomic generation increment on takeover;
- whole-batch rollback for lease loss, invalid candle, and conflicting duplicates;
- explicit migration for the lease table, applied only in disposable test setup;
- no automatic migrations at runtime and no fallback to unfenced writes.

Then run the PostgreSQL writer contracts and the existing read-only TimescaleDB integration in the same isolated CI job. Keep SQLite implementation unchanged. No canonical database creation, VPS provisioning, real Binance connection, production Feeder, or PR merge.
