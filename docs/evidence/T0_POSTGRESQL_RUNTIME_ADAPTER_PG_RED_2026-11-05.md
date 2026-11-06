# T0 PostgreSQL runtime adapter PG-RED — 2026-11-05

## Scope
Specify the FeederRuntime-to-PostgreSQL lease adapter boundary before changing runtime composition. PostgreSQL lease expiry must remain authoritative on the database clock; the legacy FeederRuntime `now_ms` argument must not be forwarded as expiry authority.

## RED contract
Added `market_data/test_postgres_feeder_runtime.py` with four contracts:
- acquire ignores runtime `now_ms` and delegates TTL;
- heartbeat ignores runtime `now_ms` and delegates owner/generation/TTL;
- current-state and write authorization use the PostgreSQL database-clock API;
- release remains bound to exact owner and generation.

The tests import the not-yet-implemented `PostgresRuntimeLeaseAdapter`. This intentionally fails before implementation.

## Exact evidence
- Test source commit: `66157193bbaf7c3960ef52736a3f4dbadcac9e0c`.
- Workflow: [T0 Single Writer Gateway Contracts run #42023493409](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42023493409).
- Static job: failure at full-suite discovery, as expected, because `PostgresRuntimeLeaseAdapter` does not yet exist.
- Prior static steps: compile, Gateway RED contracts, Gateway/Feeder regression, Health/Readiness, and process-level SIGKILL restart all succeeded.
- Full-suite result: 188 discovered; 1 import error; 13 skipped.
- TimescaleDB job: skipped because the static job failed.
- Artifact ID: `13412547723`; SHA-256: `80068b0f3f1352244bd35a7b66362666d0b442028ce5c46be1a582234de7c886`.
- This is expected RED evidence, not a green acceptance run.

## Implementation boundary
A proposed runtime implementation update was blocked by the repository write interface safety gate; no runtime source code was changed. No claim of adapter implementation or integration is made.

## Status
- Runtime adapter contract: RED confirmed / implementation pending.
- PostgreSQL runtime composition: NOT IMPLEMENTED.
- Scheduler and recovery shared Gateway identity: NOT VERIFIED for PostgreSQL.
- PostgreSQL heartbeat/readiness/lease-loss/shutdown/restart: NOT VERIFIED.
- SQLite runtime: existing regression steps PASS in this run; no SQLite source changed.
- Production DB, VPS, real Binance access, Feeder activation and PR merge: NOT performed.

## Next step
Implement the adapter and runtime composition in a controlled code-edit environment, then run the adapter contracts and isolated TimescaleDB runtime integration. Preserve SQLite default and semantics. Do not create a production canonical database or activate the production Feeder in this phase.
