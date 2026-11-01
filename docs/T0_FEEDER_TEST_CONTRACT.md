# P1 — T0 Centralized Data Feeder contract and staged implementation

**Current stage:** Scheduler and closed-candle boundaries. Retry, recovery, lease, health and lifecycle remain separate later stages.

## Scope and invariants

- Canonical market: Binance USD-M BTCUSDT perpetual.
- Timeframes: M15 and H1; only exchange-confirmed closed candles may be persisted.
- Existing `market_data.sync.sync_window()`, canonical store and storage facade remain the sole OHLCV ingestion/write path.
- `FeederScheduler` receives an injected callback. The production composition layer must bind that callback to the existing `sync_window(exchange, store, timeframe, start_ms, end_ms)`; the scheduler must not call the exchange or write to the store directly.
- No OKX/Bybit fallback, no production database access in tests, no live trading.
- Scheduler tests use a deterministic fake UTC epoch-millisecond clock and a fake sync callback.

## Approved defaults

| Setting | Default |
|---|---:|
| Scheduler polling | 5 seconds |
| Candle-close grace | 5 seconds |
| Retry attempts | 5 total attempts |
| Exponential backoff cap | 300 seconds |
| Lease TTL | 60 seconds |
| Lease heartbeat | 15 seconds |

## Current implementation contract

- `FeederConfig`: immutable configuration with validation and approved scheduler/retry/lease defaults.
- `FeederScheduler`: UTC epoch scheduling, close-grace enforcement, independent M15/H1 schedules, per-timeframe overlap prevention, completed-boundary de-duplication and bounded catch-up windows (maximum 2,000 candles per sync callback).
- `run_due()` invokes only the injected callback. M15 and H1 are attempted independently; one timeframe failure does not suppress the other. Failed windows do not advance their watermark.
- The scheduler watermark is initialized at the latest aligned boundary at process construction. Startup gap reconciliation is a later Recovery stage; until then, the runtime must not claim historical coverage from this watermark.
- The scheduler does not own retry logic, durable leases, health/readiness or restart recovery. Those remain later test groups.

## Ordered implementation and test gates

1. `market_data.test_feeder_scheduler` — scheduler and candle closure. **Current Codemagic workflow runs only this group.**
2. `market_data.test_feeder_retry` — retry, exponential backoff, jitter and Retry-After.
3. `market_data.test_feeder_recovery` — gap planning and recovery/recheck orchestration.
4. `market_data.test_feeder_lease` — singleton, durable lease, concurrent acquisition and fencing.
5. `market_data.test_feeder_health` — health states, freshness and readiness.
6. `market_data.test_feeder_lifecycle` — graceful shutdown and restart recovery.

Do not begin the next group until the current group has a GREEN Codemagic result with the exact source SHA and test log inspected.

## Codemagic verification

The normal `t0-feeder-scheduler` workflow:
1. Runs on pushes to the P1 branch when scheduler implementation, scheduler tests or Codemagic config changes.
2. Records `git rev-parse HEAD` in `ci-source-sha.txt`.
3. Runs only `python3 -m unittest market_data.test_feeder_scheduler -v`.
4. Compiles `market_data/feeder.py`.
5. Publishes source SHA, test log, verdict and compile log.

The earlier RED evidence at commit `900b189243bf629224549628dd7aa4d00049b39b` proved that the feeder module was absent. It did not execute the assertions inside the scheduler test module. This staged GREEN gate is the first executable assertion-level verification for the scheduler implementation.

No PC runtime deployment, production storage mutation or trading action is part of this stage.
