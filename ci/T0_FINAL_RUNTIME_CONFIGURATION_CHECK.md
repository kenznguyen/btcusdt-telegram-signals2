# T0 Final Runtime Configuration Check

## Purpose

This is a manually selected, read-only GitHub Actions gate for validating the
T0 runtime configuration contract in an isolated CI runner. It does not
validate the user's PC runtime path or inspect the canonical T0 database.

Workflow: `.github/workflows/t0-manual-validation.yml`  
Manual input: `final-runtime-config`

## What the workflow validates

1. The T0 runtime configuration contract tests.
2. Python syntax for `ci/t0_final_runtime_config.py` and its tests.
3. The configuration report produced by `python -m ci.t0_final_runtime_config`.
4. Exact source SHA and isolation evidence in the workflow artifact.

## Explicit CI isolation boundary

The GitHub Actions job sets these variables to empty:

- `MARKET_DATA_DB`
- `T0_FEEDER_LEASE_DB`
- `PAPER_DB`
- Binance/OKX API credentials

The job does not receive a canonical DB path or exchange credentials. It
cannot see the user's Windows PC filesystem or Android storage. Therefore:

- Canonical DB path on PC: **NOT VERIFIED**
- Existing canonical SQLite database integrity: **NOT RUN**
- Feeder startup, exchange connectivity and data sync: **NOT RUN**
- Production runtime readiness: **NOT CERTIFIED**

The report may state that the runner has no configured database. This is an
expected consequence of isolation, not evidence that the user's PC database
is missing.

## Why this gate remains manual

A manual selection prevents a configuration-only audit from being mistaken
for runtime acceptance. It is safe to run in GitHub Actions because it has no
canonical DB or exchange access. It must not be used as a substitute for a
separately approved PC-side runtime check.

## Artifacts

The workflow uploads:

- `ci-source-sha.txt`
- `t0-final-runtime-config-tests.log`
- `t0-final-runtime-config-report.json`
- `t0-final-runtime-config-scope.txt`

The source SHA must match the exact commit shown in the GitHub Actions run.
