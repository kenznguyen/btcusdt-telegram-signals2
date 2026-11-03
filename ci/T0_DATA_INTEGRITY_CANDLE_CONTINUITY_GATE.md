# T0 Data Integrity & Candle Continuity Gate

## Purpose

This is a read-only source/data-integrity contract gate. It checks the
integrity and candle-continuity audit logic using isolated test fixtures; it
does not inspect or modify the canonical database on the user's PC.

Workflow: `.github/workflows/t0-validation.yml`  
Job: `t0-validation`  
Test module: `ci.test_t0_data_integrity`

## Test contract

- Runs 12 deterministic unit tests.
- Compiles `ci/t0_data_integrity.py` and `ci/test_t0_data_integrity.py`.
- Records exact source SHA and uploads logs/verdict as an artifact.
- Uses temporary test fixtures only.

## GitHub Actions isolation boundary

The runner has no `MARKET_DATA_DB`, `T0_FEEDER_LEASE_DB`, `PAPER_DB` or
exchange credentials. The gate does not start the Feeder, run market-data
synchronization, connect to Binance/OKX, or open a canonical database.

A PASS proves the audit contract and deterministic fixture behavior only. It
does not certify the integrity, completeness, freshness or availability of
the user's actual canonical dataset.

## Explicitly not verified

- Canonical PC database contents and SQLite integrity: NOT RUN.
- Production Feeder lifecycle, lease/fencing or SIGKILL behavior: covered by
  separate automated test suites, not by this data-integrity audit.
- Runtime Health Smoke and continuous production ingestion: NOT RUN.
- External TimescaleDB: not part of this gate.
