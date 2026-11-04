# P1 — T0 Centralized Data Feeder: Current Test Contract

**Current gate:** T0-A fixture-only CI and static-contract closeout — **PASS** on exact source SHA `81252f3e954216d638d3655623d765c38b6f960b`.

**Overall P1/T0:** OPEN. T0-A is not production deployment acceptance.

## Repository execution rules

- Repository: `kenznguyen/btcusdt-telegram-signals2`.
- GitHub stores source, plans, evidence and handoff records.
- GitHub Actions is the only runner for T0 tests and validation workflows.
- Codemagic is retired for this project and must not be used or reconfigured unless the owner explicitly reverses that decision.
- Continue on the existing branch; do not create parallel branches or PRs for the same work.
- Every PASS requires exact source SHA, workflow run, job outcome and artifact evidence.
- Test and operational claims must distinguish fixture CI from PC/production runtime.

## Scope and invariants

- Canonical market: Binance USD-M BTCUSDT perpetual.
- Timeframes: M15 and H1; only exchange-confirmed closed candles may be persisted.
- Existing `market_data.sync.sync_window()`, concrete `T0WriteGateway`, canonical store and storage facade remain the sole OHLCV ingestion/write path.
- Scheduler and recovery receive injected callbacks; production composition must route them through the existing canonical sync/Gateway path.
- No alternate writer, OKX/Bybit fallback, live trading or real order execution.
- `AI_EXECUTION_ENABLED=false`.

## Approved runtime defaults

| Setting | Default |
|---|---:|
| Scheduler polling | 5 seconds |
| Candle-close grace | 5 seconds |
| Retry attempts | 5 total attempts |
| Exponential backoff cap | 300 seconds |
| Lease TTL | 60 seconds |
| Lease heartbeat | 15 seconds |

## Storage target and boundary

- Owner-selected target: Windows PC.
- Database: SQLite.
- Lease: same physical database as canonical market data.
- Backup cadence: daily.
- Canonical filesystem path: **NOT DECIDED**.
- PC use is currently deferred. No PC path or database was inspected in P5.4.63/T0-A.
- GitHub Actions fixture tests use temporary/in-memory test state only. They must not create, open or write the future canonical DB.

## Fixture test inventory

The following feeder modules are registered in GitHub Actions and passed on tested source SHA `81252f3e954216d638d3655623d765c38b6f960b`:

| Module | Test methods |
|---|---:|
| `market_data.test_feeder_scheduler` | 15 |
| `market_data.test_feeder_retry` | 12 |
| `market_data.test_feeder_recovery` | 22 |
| `market_data.test_feeder_lease` | 11 |
| `market_data.test_feeder_health` | 11 |
| `market_data.test_feeder_health_api` | 9 |
| `market_data.test_feeder_lifecycle` | 23 |
| `market_data.test_feeder_atomic_fencing` | 9 |
| `market_data.test_feeder_health_runtime_api` | 6 |
| `market_data.test_feeder_sigkill_recovery` | 1 |
| **Total across these modules** | **119** |

Additional T0 CI coverage includes 16 Gateway runtime tests, market-data/store/sync/API tests, 11 static operational contract checks, and CI policy checks. Invocation counts overlap and are not unique-test totals.

## Exact-SHA evidence

- Tested source SHA: `81252f3e954216d638d3655623d765c38b6f960b`.
- T0 standalone run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41747057849 — SUCCESS, all 19 substantive steps.
- Integrated P5.4.1 run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41747057869 — SUCCESS, 5/5 jobs.
- Regression invocation markers: atomic fencing 112; runtime health API 119; SIGKILL recovery 113.
- Static operational contract: PASS.
- Detailed artifacts and metadata digests: `docs/evidence/P5.4.63-RECOVERY-COORDINATOR-PARTIAL-WINDOW-RETRY-2026-11-04.md`.
- Artifact payload-byte checksum recomputation: NOT VERIFIED.

## Ordered gates

1. **T0-A — Fixture contracts and static CI closeout: PASS.** Scheduler, retry, recovery, lease, health, lifecycle, Gateway, fencing, CI policy and operational static audit are green on GitHub Actions.
2. **T0-B — PC storage identity and SQLite integrity: BLOCKED / DEFERRED.** Resolve canonical path on Windows PC and verify database identity/integrity read-only. Requires PC use to be reopened.
3. **T0-C — Controlled Feeder runtime acceptance: NOT RUN.** Verify production composition, same-DB lease, readiness, lease loss, M15/H1 closed-candle ingestion, retry/recovery, stop and restart. Requires separate approval.
4. **T0-D — Production backup/restore and continuity: NOT RUN / NOT VERIFIED.** Validate daily backup, WAL-consistent capture, restore, lease generation and continuity across required ledgers. Requires separate approval.
5. **T0-E — Overall T0/P1 acceptance: BLOCKED.** Do not close P1 or advance to P2 until T0-B, T0-C and T0-D have evidence.

## Prohibited without separate explicit approval

- Do not create, open or modify the canonical PC database.
- Do not start the production Feeder.
- Do not connect to Binance or another exchange or sync market data.
- Do not run production backup/restore.
- Do not enable live orders or exchange execution.
