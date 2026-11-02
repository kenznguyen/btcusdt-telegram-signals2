# T0 Final Runtime Configuration Check

## Purpose

Workflow: **T0 - Final Runtime Configuration Check**  
Workflow key: `t0-final-runtime-configuration-check`

This is an independent, manually started gate for the production T0 feeder configuration. It does not replace or alter the Operational Contract, Data Integrity, feeder lifecycle, lease/fencing, recovery, or health workflows.

## What the workflow validates

- Python 3.10+ and the installed `ccxt` dependency.
- The production feeder backend is SQLite. PostgreSQL is deliberately rejected by the current production composition because its lease fencing is not implemented in the same transaction.
- `MARKET_DATA_DB` is configured and its parent directory already exists and is writable.
- `T0_FEEDER_LEASE_DB`, when set, resolves to the exact same file as `MARKET_DATA_DB`; otherwise it defaults to `MARKET_DATA_DB`.
- Feeder numeric settings using the actual defaults and validation in `market_data.feeder_service.build_production_runtime()` and `FeederConfig`: poll, close grace, retry attempts, lease TTL, heartbeat, and recovery lookback.
- If the database file already exists, it is opened with SQLite `mode=ro` and `PRAGMA query_only=ON`; SQLite integrity and the required `candles` and `feeder_leases` tables are checked. The runtime status table is reported as present or not yet published.

The report never emits database paths, owner IDs, DSNs, or secret values.

## Codemagic setup

Start the workflow manually on the intended T0 branch. Configure the required variables in the appropriate Codemagic environment group:

- `MARKET_DATA_DB`: canonical SQLite database file path.
- `T0_FEEDER_LEASE_DB`: optional; if supplied, it must resolve to the same file as `MARKET_DATA_DB`.
- `MARKET_DATA_BACKEND`: optional; defaults to `sqlite` and any other backend fails closed.

Optional feeder settings are read using the production code's defaults:

| Variable | Default |
| --- | ---: |
| `T0_FEEDER_POLL_SECONDS` | 5 |
| `T0_FEEDER_CLOSE_GRACE_SECONDS` | 5 |
| `T0_FEEDER_RETRY_ATTEMPTS` | 5 |
| `T0_FEEDER_LEASE_TTL_SECONDS` | 60 |
| `T0_FEEDER_LEASE_HEARTBEAT_SECONDS` | 15 |
| `T0_FEEDER_RECOVERY_CANDLES` | 2000 |
| `T0_FEEDER_OWNER_ID` | host:pid fallback |

The database parent directory must already exist on the Codemagic worker. The workflow intentionally does not create it. A missing database file is reported as `NOT_INITIALIZED`; this is a configuration-only pass and does not certify an initialized or persistent database. If a database file is present, its existing schema and integrity are audited read-only.

## Safety boundary

The workflow only imports configuration primitives and performs read-only inspection of an existing SQLite file. It never calls `build_production_runtime()`, constructs a CCXT exchange client, starts `FeederRuntime`, invokes synchronization/recovery, creates directories or database files, or mutates SQLite data.

Codemagic workers are build environments. A configured path is useful only if the required storage is actually mounted and accessible to that worker; a path string alone does not make local or production storage available. Do not treat a PASS with `database.state=NOT_INITIALIZED` as proof of database readiness, feeder health, continuous ingestion, or live exchange connectivity.

## Artifacts

- `ci-source-sha.txt`
- `t0-final-runtime-config-tests.log`
- `t0-final-runtime-config-report.json`

A PASS proves the static configuration contract and any optional read-only SQLite checks performed in that build. It does not start or authorize the feeder.
