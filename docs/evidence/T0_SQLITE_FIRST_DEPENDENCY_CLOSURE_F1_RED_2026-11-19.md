# T0 SQLite-first dependency closure and F1 RED evidence — 2026-11-19

## Scope

This increment begins the bounded T0 SQLite-first completion work with dependency-closure verification and an independent F1 regression test.

In scope:
- Static dependency inventory for the active SQLite T0 composition.
- Disposable SQLite-only dependency-closure test.
- Read-only preflight regression for a missing or malformed `feeder_leases` table.
- Exact-SHA GitHub Actions evidence for the test-first RED phase.

Explicit exclusions:
- No PostgreSQL/TimescaleDB implementation, qualification, migration or dependency changes.
- No production/runtime, VPS, systemd installation, service restart or deployment.
- No canonical SQLite database access, mutation, recovery, restoration, ingestion, export or deletion.
- No T1 activation, T2 consumer migration, paper execution or trading.

## Repository identity

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Parent source SHA: `5223cef02f0e296c4f58afc5d7992b9c641ab208`
- Test-only commit / exact CI source SHA: `7faef47cb93ec8563583aa29e9a6104ccc35f835`
- Changed source path: `market_data/test_write_gateway.py`
- New test-file blob SHA: `2c55dff1729cdfd11bd0ef2188e1e41756ed7692`
- Production source and dependency manifests were not changed in this increment.

## Dependency closure findings

The active canonical SQLite composition is:

```text
market_data.feeder_service
  -> market_data.feeder (runtime / scheduler / recovery / SQLite LeaseStore)
  -> market_data.sync (sync_window; CCXT import is deferred to CLI main)
  -> market_data.storage (SQLite factory)
  -> market_data.store (SQLite CandleStore / read path)
  -> market_data.write_gateway (SQLite fenced writer / WAL keeper)
  -> market_data.api (read-only WSGI API)
```

Findings:
- SQLite storage, lease, write-gateway, initialization and API paths use Python standard-library modules.
- `market_data.postgres` is imported by shared composition/storage modules, but `psycopg` is imported lazily inside the PostgreSQL connection function. Importing the shared modules and executing the SQLite write path does not require the PostgreSQL driver.
- `requirements-market-data.txt` currently declares both `ccxt` and `psycopg[binary]` unconditionally. This is a broad install profile, not a minimal SQLite dependency profile.
- `ccxt` is needed by the explicit Binance sync CLI path; offline SQLite tests and the tested SQLite composition do not need it.
- No package-manifest split or PostgreSQL adapter change was made because PostgreSQL is excluded from this work package.

Independent regression added:
- `test_sqlite_runtime_dependency_closure_without_site_packages` starts a subprocess with Python `-S`, imports API/Feeder Service/Storage, creates a disposable empty SQLite database, acquires a fixture lease and writes one validated candle through `SQLiteWriteGateway`.
- Result: **PASS** on exact source SHA `7faef47cb93ec8563583aa29e9a6104ccc35f835`.

## F1 defect and RED evidence

The existing `SQLiteWriteGateway._validate_existing_schema()` verifies the `candles` table, then validates `feeder_leases` only when `PRAGMA table_info(feeder_leases)` returns rows. An absent lease table therefore passes constructor preflight and fails to be rejected before the writer is used.

Tests added:
- Missing `feeder_leases` table must be rejected during gateway construction without creating or changing tables.
- Malformed `feeder_leases` schema must be rejected during gateway construction.
- SQLite import/write dependency closure must work without site-packages.

Observed RED:
- Missing-table regression: **FAIL as expected** — `AssertionError: ValueError not raised`.
- Malformed-table regression: **PASS**.
- Dependency-closure regression: **PASS**.

## Exact-SHA workflow evidence

### T0 manual validation — isolated SQLite lease/fencing

- Workflow run: `44491169869`
- URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/44491169869
- Event: push; exact checkout SHA: `7faef47cb93ec8563583aa29e9a6104ccc35f835`
- Job: `135446853190` — Automatic isolated SQLite lease and fencing tests
- Result: **FAIL / RED confirmed**; 58 tests, 57 passed, 1 failed (F1 missing lease-table preflight).
- Artifact: `14513580101`, `t0-sqlite-lease-fencing-auto-44491169869`
- Artifact digest metadata: `sha256:1b48c497bfb7953aaa37ac8935039f8a15a5c7049c4cc14c07d65f9ff75a31e7`
- Artifact payload bytes were not downloaded and hashed; payload SHA-256 is **NOT VERIFIED**.

### T0 Single Writer Gateway workflow — mixed-scope automatic trigger

- Workflow run: `44491169819`
- URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/44491169819
- Event: push; exact checkout SHA: `7faef47cb93ec8563583aa29e9a6104ccc35f835`
- Static Gateway contracts: job `135446852527`, 10/10 PASS.
- Behavioral / feeder regression step: 80 tests, 79 passed, 1 failed (same F1 missing lease-table preflight).
- Artifact: `14511983705`, `t0-swg-contract-evidence-7faef47cb93ec8563583aa29e9a6104ccc35f835`
- Artifact digest metadata: `sha256:40a96b19afb9a7be081abd8f5c576b001abde127f4b03cfffe893a0e1ecb02be`
- Artifact payload bytes were not downloaded and hashed; payload SHA-256 is **NOT VERIFIED**.

### Disposable SQLite systemd sandbox

- Workflow run: `44491169861`
- URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/44491169861
- Job: `135446854183`
- Result: **PASS**, disposable GitHub runner only; this is not evidence of a deployed/current T0 runtime.
- Artifact: `14512474872`, `t0-systemd-readonly-sandbox-7faef47cb93ec8563583aa29e9a6104ccc35f835`
- Artifact digest metadata: `sha256:b555b1efcb386ebf80f377928ae74c7f94f46b51cabb1a39848e1c3420f3c689`
- Payload hash: **NOT VERIFIED**.

## Scope-trigger incident / CI limitation

The push of `market_data/test_write_gateway.py` matched existing broad workflow path filters. This unintentionally triggered workflows beyond the requested SQLite-only scope:

- `t0-single-writer-gateway-red.yml` also ran a disposable PostgreSQL provider-bootstrap job (PASS), T1 offline importer and Rust tests (PASS), and paper-consumer fixtures (PASS). Its TimescaleDB read-only integration job was skipped.
- `t2-freqtrade-2026-9-strategy-smoke.yml` ran and passed (32 tests plus strategy-load smoke); run `44491169864`, artifact `14513470249`, digest metadata `sha256:61145cdd8dcbaaa261d83d3111b68ab48d4905e0da15547e8b078aea4288c2c8`.
- These jobs used disposable CI resources and no canonical database, production runtime, exchange credentials, live orders or T1 runtime. They are **incidental, out of scope and excluded from the T0 SQLite acceptance verdict**.
- Available GitHub connector operations in this session are read-only for workflow-run management; no cancellation action was available. All four triggered runs have now completed.
- Before the next source push, CI execution boundaries need to be isolated so a T0 SQLite change does not automatically execute PostgreSQL, T1, paper-consumer or T2 workflows. Do not change those workflows as part of this evidence-only increment.

## Status and next gate

| Area | Status | Basis |
|---|---|---|
| SQLite dependency closure (code/import/runtime path without site-packages) | **PASS** | Disposable subprocess created fixture DB, acquired lease and wrote a candle |
| F1 missing `feeder_leases` preflight | **RED CONFIRMED / BLOCKED** | New test fails because missing table is accepted |
| F1 malformed `feeder_leases` preflight | **PASS** | New regression passes |
| Existing SQLite lease/gateway/lifecycle regression | **PARTIAL / FAIL** | 57/58 and 79/80 pass; one F1 failure |
| Disposable SQLite WAL/systemd sandbox | **PASS (CI sandbox only)** | Exact-SHA disposable runner |
| Minimal SQLite package manifest | **NOT IMPLEMENTED** | Existing combined market-data requirements retained; no dependency removal |
| PostgreSQL / TimescaleDB | **OUT OF SCOPE / NOT QUALIFIED** | Incidental provider bootstrap is not acceptance |
| Current T0 runtime / canonical database / recovery | **NOT VERIFIED** | Not inspected or accessed |

Next:
1. Isolate workflow triggers so a T0-only source push cannot fan out into PostgreSQL, T1, paper-consumer and T2 workflows.
2. After that boundary is approved, implement only the F1 preflight rejection and run the independent SQLite-only regression on the exact resulting SHA.
3. Reconcile any additional dependency-profile changes separately; do not remove PostgreSQL support or change canonical data/runtime behavior in this work package.
