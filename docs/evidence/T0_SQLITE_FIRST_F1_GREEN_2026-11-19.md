# T0 SQLite-first F1 fix and independent regression GREEN — 2026-11-19

## Scope and guardrails

This increment continues the approved SQLite-first T0 work on the existing branch.

In scope:
- Close the F1 SQLite Write Gateway preflight gap.
- Keep the SQLite dependency-closure regression.
- Narrow automatic CI so a T0 SQLite-only change does not fan out into PostgreSQL, T1, paper-consumer, T2, recovery or service-runtime jobs.
- Record exact-SHA test and artifact evidence.

Explicitly excluded and unchanged:
- PostgreSQL / TimescaleDB source, dependencies, tests and runtime.
- Feeder service runtime behavior, deployment, VPS, systemd installation, autostart or process management.
- Canonical data recovery, restoration, re-ingestion, migration, overwrite or deletion.
- Canonical T0 database access or mutation.
- T1/T2 integration, paper execution, exchange credentials and live orders.

## Repository and provenance

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Final branch HEAD: `dca7317907d2902d76a2e4e16c2076f03b17585a`
- F1 production source commit: `82383e16b33a0ab09ff35b23411dbb6857ed0036`
- F1 production source file: `market_data/write_gateway.py`
- Final write-gateway blob SHA: `585caf5250c7382f8e391533882f08c8ec97efaa`
- Regression test file: `market_data/test_write_gateway.py`
- Test-only RED commit: `7faef47cb93ec8563583aa29e9a6104ccc35f835`
- Existing branch was retained; no merge, rebase, PR, cherry-pick or branch switch.

## F1 fix

Previously, `SQLiteWriteGateway._validate_existing_schema()` checked `feeder_leases` only if `PRAGMA table_info(feeder_leases)` returned rows. A missing table therefore passed preflight.

The fix now obtains lease columns through the same read-only schema helper used for candles and requires:
- Exact ordered columns: `lease_name, owner, generation, expires_at_ms`.
- Exact primary key: `lease_name`.
- Missing or incompatible schema raises `ValueError` before writer construction completes.

The check opens the existing SQLite database with `mode=ro`. It does not create tables, repair schema, or modify data.

Regression cases:
- Missing `feeder_leases` table is rejected at construction and remains absent afterward.
- Malformed `feeder_leases` table is rejected.
- Empty/missing database and incompatible candles schema remain fail-closed.
- Python `-S` subprocess imports API, Feeder Service and Storage, creates a disposable SQLite fixture, acquires a fixture lease and writes one candle without site-packages.

## Exact-SHA GREEN evidence

### T0 Manual Validation / isolated SQLite lease and fencing

- Workflow run: `44492153886`
- URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/44492153886
- Exact checkout SHA: `dca7317907d2902d76a2e4e16c2076f03b17585a`
- Overall workflow conclusion: **SUCCESS**
- SQLite lease/fencing job: `135450239678` — **SUCCESS**
- Test output: `Ran 24 tests in 0.376s`; `OK`
- F1 missing-table regression: **PASS**
- F1 malformed-table regression: **PASS**
- SQLite dependency-closure test: **PASS**
- Recovery-change detector: success; recovery job **SKIPPED**
- Data-flow-change detector: success; T0-to-T2 data-flow job **SKIPPED**
- G4-change detector: success; G4 runtime probe job **SKIPPED**
- Manual acceptance job: **SKIPPED** (not selected/run)
- Artifact ID: `14512993080`
- Artifact name: `t0-sqlite-lease-fencing-auto-44492153886`
- Artifact digest metadata: `sha256:976c4e89b2044ad87a76f21953e8e37767a3451df756ea503a65b23571e297df`
- Artifact payload bytes were not downloaded and independently hashed; payload SHA-256 is **NOT VERIFIED**.

### Disposable SQLite WAL sandbox

- Workflow run: `44491903813`
- URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/44491903813
- Exact checkout SHA: `82383e16b33a0ab09ff35b23411dbb6857ed0036`
- Job: `135449372722`
- Result: **PASS**, disposable GitHub runner only.
- Artifact ID: `14512892115`
- Artifact digest metadata: `sha256:276af0237b6bc42b7e28faf768a634c0965cb1acc4505cef3b67476be32c21ca`
- Payload SHA-256: **NOT VERIFIED**.

## CI boundary changes

Final workflow definitions read back from GitHub:

1. `.github/workflows/t0-manual-validation.yml`, blob `127648c5810c303e43b67cba1b32b344ae1ff889`
   - SQLite lease/fencing automatic gate now runs only `market_data.test_feeder_lease` and `market_data.test_write_gateway`.
   - `market_data.test_feeder_lifecycle` was removed from this gate because runtime/lifecycle testing is outside this increment.
   - Workflow-only changes no longer count as recovery, data-flow or G4 application-source changes.
   - Push run name now identifies the `sqlite-regression` gate instead of displaying an empty manual input.

2. `.github/workflows/t0-single-writer-gateway-red.yml`, blob `2c97678cc2587e899be1e343fe03d94e47234e22`
   - Automatic push and pull-request triggers removed; manual dispatch retained.
   - This workflow bundles SQLite with PostgreSQL provider, T1 importer/Rust and paper-consumer jobs; it is not a SQLite-only acceptance gate and must remain manual-only until those concerns are separated.

3. `.github/workflows/t2-freqtrade-2026-9-strategy-smoke.yml`, blob `8ec80e5332a5ce4db9398acb25148927eef9fa87`
   - `market_data/**` removed from both push and pull-request filters.
   - T2 remains triggered by its own `freqai_bridge/**`, `pipeline/**` and workflow paths.

4. `.github/workflows/t0-systemd-feeder-api-integration.yml`, blob `1dc4e3d701f9e623659fcf03cd9c176d1ddb2d38`
   - Automatic push and pull-request triggers removed; manual dispatch retained because service-runtime integration is outside this increment.

5. `.github/workflows/t0-sqlite-readonly-sandbox.yml`
   - Retained as an automatic disposable SQLite WAL/filesystem isolation test; it does not install or alter the user's runtime.

## Superseded / out-of-scope CI runs

- RED run `44491169869` on `7faef47...`: expected F1 missing-table failure (57/58 tests). Superseded by the GREEN run.
- Run `44491904163` on `82383e1...`: F1 regressions passed, but the gate also ran lifecycle tests; 6 lifecycle fixture errors showed the newly enforced lease table was absent from those legacy runtime fixtures. Runtime/lifecycle is excluded and was removed from the SQLite-only gate.
- Run `44491997402` on `d896926...`: 24 SQLite lease/fencing tests passed, but the workflow also incorrectly triggered isolated recovery tests because the workflow file itself was in the recovery detector. The recovery job failed; this is superseded by the detector correction and final successful run `44492153886`.
- Run `44491903793` on `82383e1...`: disposable Feeder/API systemd integration completed PASS after it had already been triggered. It is out of scope and is not part of T0 SQLite acceptance; its automatic triggers are now removed.
- Earlier mixed workflow `44491169819` on `7faef47...` ran incidental PostgreSQL provider, T1 and paper-consumer jobs. It is not part of T0 acceptance. The workflow is now manual-only.
- Earlier T2 run `44491169864` on `7faef47...` is not part of T0 acceptance. T2 automatic path filters have been narrowed.

No cancellation operation was available through the connected GitHub actions; already-started disposable CI runs were allowed to complete. They did not access the canonical database or VPS.

## Status

| Area | Status | Evidence |
|---|---|---|
| SQLite dependency closure without site-packages | **PASS** | Python `-S` subprocess in 24-test suite |
| F1 missing/malformed lease schema preflight | **PASS** | Exact-SHA tests in run `44492153886` |
| SQLite lease/fencing regression | **PASS** | 24/24 tests |
| Disposable SQLite WAL sandbox | **PASS** | Run `44491903813` |
| T0 automatic CI isolation from PG/T1/paper/T2 | **PASS — source verified** | Workflow read-back and final run |
| Runtime / lifecycle behavior | **OUT OF SCOPE / NOT VERIFIED** | Lifecycle tests removed from SQLite gate |
| Canonical data recovery / restoration | **OUT OF SCOPE / NOT VERIFIED** | Recovery gate skipped in final run |
| PostgreSQL / TimescaleDB | **OUT OF SCOPE / NOT VERIFIED** | No source, dependency or test changes |
| Current canonical DB / VPS runtime | **NOT INSPECTED** | No access or mutation in this increment |
| Minimal SQLite-only dependency manifest | **NOT IMPLEMENTED** | Existing requirements retained |

Overall increment status: **PASS for dependency closure, F1 and independent SQLite lease/fencing regression; T0 completion remains PARTIAL.**

## Next bounded step

Continue the SQLite-first dependency inventory and independent tests for the remaining T0 SQLite storage, initialization and read-only API boundaries. Do not enter PostgreSQL, service runtime/lifecycle, canonical recovery, VPS or deployment without a separate approval.
