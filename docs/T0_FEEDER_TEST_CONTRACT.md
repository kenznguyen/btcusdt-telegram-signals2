# P1.2 — T0 Centralized Data Feeder test contract

**Phase:** test specification only. The feeder implementation is intentionally absent.

## Scope and invariants

- Canonical market: Binance USD-M BTCUSDT perpetual.
- Timeframes: M15 and H1; only exchange-confirmed closed candles may be persisted.
- Existing `market_data.sync.sync_window()`, canonical store and storage facade remain the source of truth.
- No OKX/Bybit fallback, no production database access in tests, no live trading.
- Test clocks, exchange responses, retry sleeps and network boundaries are deterministic/faked.
- Each test uses a temporary SQLite database where persistence is needed.

## Approved defaults

| Setting | Default |
|---|---:|
| Scheduler polling | 5 seconds |
| Candle-close grace | 5 seconds |
| Retry attempts | 5 total attempts |
| Exponential backoff cap | 300 seconds |
| Lease TTL | 60 seconds |
| Lease heartbeat | 15 seconds |

Retry-After is a server-directed minimum wait. It must never be shortened to the local backoff cap; a Retry-After value above 300 seconds takes precedence to avoid retrying before the exchange permits it. Invalid negative/non-finite Retry-After values fail closed.

## Internal interfaces specified by these tests

- `FeederConfig`: validates timing, retry and lease settings and exposes the approved defaults.
- `FeederScheduler`: UTC epoch scheduling, close-grace enforcement, independent M15/H1 schedules, per-timeframe overlap prevention, completed-slot de-duplication and bounded catch-up windows.
- `RetryPolicy`: retries transient transport/rate-limit/server failures only; exponential backoff with jitter; bounded attempts; Retry-After support.
- `RecoveryPlanner`: validates timeframe alignment and gap bounds and returns chronological recovery windows.
- `RecoveryCoordinator`: reads canonical coverage, calls the injected canonical sync callback once per gap, then re-reads coverage. It must not report success while gaps remain. The production adapter must call the existing `sync_window(exchange, store, timeframe, start_ms, end_ms)`; it must not implement a second OHLCV writer.
- `LeaseStore`: durable SQLite lease with atomic acquisition, expiry, heartbeat, owner/generation checks and fencing authorization.
- `HealthEvaluator`: independent liveness/readiness, STARTING/HEALTHY/DEGRADED/STALE/FAILED/STOPPED states, per-timeframe freshness and unresolved-gap handling.
- `FeederRuntime`: acquire lease before recovery, become ready only after recovery, and stop scheduling/drain in-flight work before releasing the lease.

## Health rules under test

- Liveness answers only whether the process is alive.
- Readiness requires storage access, a valid lease, successful startup recovery, both M15 and H1 fresh, and no unresolved gaps.
- One full timeframe of freshness lag is DEGRADED; two or more intervals is STALE.
- A fatal error or unavailable storage is FAILED; a stopped process is STOPPED.
- A stale or degraded timeframe must not be hidden by the other healthy timeframe.
- Freshness is evaluated against the latest expected closed-candle boundary, not merely the process heartbeat.

## Ordered test groups

1. `market_data.test_feeder_scheduler` — scheduler and candle closure.
2. `market_data.test_feeder_retry` — retry, exponential backoff, jitter and Retry-After.
3. `market_data.test_feeder_recovery` — gap planning and recovery/recheck orchestration.
4. `market_data.test_feeder_lease` — singleton, durable lease, concurrent acquisition and fencing.
5. `market_data.test_feeder_health` — health states, freshness and readiness.
6. `market_data.test_feeder_lifecycle` — graceful shutdown and restart recovery.

## RED verification protocol

The RED-only Codemagic workflow must:
1. Record `git rev-parse HEAD` in `ci-source-sha.txt`.
2. Install only the existing market-data requirements.
3. Run all six feeder contract modules without network access.
4. Treat the current missing `market_data.feeder` module as the expected RED cause.
5. Fail the workflow if tests unexpectedly pass, or if the failure is caused by syntax/collection errors rather than the missing implementation.
6. Publish the complete test log and source SHA as artifacts.

A successful Codemagic workflow in this RED stage means the expected failing-test condition was verified, not that the tests passed. After the RED evidence is inspected, replace this temporary RED gate with a normal P1 test gate before implementation begins.

## Verification status

The GitHub branch stores source only. Test execution and build actions belong to Codemagic. A RED result is not considered verified until the Codemagic build log and artifact SHA have been inspected. No implementation, PC runtime deployment, production storage mutation or trading action is part of this phase.
