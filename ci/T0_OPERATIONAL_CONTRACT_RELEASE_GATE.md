# T0 Operational Contract & Release Gate

## Purpose

This gate is a static, SHA-bound audit of the T0 feeder source and GitHub Actions
workflow registration. It does not start the feeder, connect to an exchange,
open a canonical database, or run the historical SIGKILL suite itself.

## GitHub Actions ownership

- Automated T0 contract suites: `.github/workflows/t0-validation.yml`.
- Manual-only T0 acceptance gates: `.github/workflows/t0-manual-validation.yml`.
- The automated workflow checks out the exact triggering commit, records
  `git rev-parse HEAD` in `ci-source-sha.txt`, and uploads its test logs.
- The manual workflow keeps runtime configuration, P3 component, Kraken Spot
  and TimescaleDB acceptance opt-in.
- TimescaleDB integration requires the dedicated disposable secret
  `MARKET_DATA_TEST_DATABASE_URL`; it is not inferred from Codemagic secrets.

## Historical evidence

Historical GREEN results remain tied to their original source SHAs. Migrating
the workflow runner does not recreate or upgrade those results. The new
GitHub Actions runs provide new evidence only for the exact commit checked out
by each run.

| Contract area | Migrated gate | Historical count assertion |
|---|---|---:|
| Feeder lease/scheduler | automated T0 validation | no fixed count |
| Feeder health/readiness | automated T0 validation | no fixed count |
| Feeder lifecycle | automated T0 validation | regression suite |
| Atomic fencing | automated T0 validation | 99 |
| SIGKILL recovery | automated T0 validation | 100 |
| Health runtime/API integration | automated T0 validation | 106 |
| Data integrity/candle continuity | automated T0 validation | 12 |
| Final runtime configuration | manual T0 validation | no fixed count |
| P3 component contracts | manual T0 validation | no fixed count |
| Kraken Spot adapter/store/read API | manual T0 validation | no fixed count |
| TimescaleDB/SQLite parity | manual T0 validation | external DB required |

## Operational invariants checked from source

1. Production feeder selects Binance USD-M through CCXT `binanceusdm`.
2. Canonical market identity is Binance / USDT perpetual / BTCUSDT.
3. Only closed candles are eligible for ingestion.
4. Production feeder rejects non-SQLite storage until a lease-fenced
   PostgreSQL Gateway exists.
5. Lease and canonical candle database paths resolve to the same SQLite file.
6. Scheduler and recovery writes use `T0WriteGateway` with typed
   `LeaseFence` admission.
7. T0-specific Codemagic workflows are retired; T0 validation is registered
   in GitHub Actions.

OKX/Bybit remain shadow sources only; this gate does not introduce fallback,
data mixing, or a second canonical writer.

## CI isolation boundary

All automated test jobs explicitly leave canonical DB, Paper DB and exchange
credential variables unset. Unit/integration tests use temporary SQLite
databases and deterministic exchange doubles. The manual TimescaleDB gate is
the only T0 CI path that may receive the dedicated disposable
`MARKET_DATA_TEST_DATABASE_URL` secret.

No gate in these workflows starts the production Feeder, performs market-data
sync against an exchange, or submits paper/live orders.

## Explicitly not certified

- Controlled Runtime Health Smoke is intentionally not performed here.
- Continuous production runtime operation is not established by static checks.
- External TimescaleDB integration is not certified until the manual gate
  completes against a dedicated disposable database.
- T1-T4 read-only enforcement is outside this T0-only gate.
- No merge or runtime activation is implied by a passing CI gate.

## Evidence artifacts

Automated T0 workflow publishes `t0-automated-evidence-<run_id>`, including
the exact source SHA, isolation verdict, suite logs, test verdicts and static
audit reports. Manual gates publish `t0-manual-<gate>-<run_id>`.
