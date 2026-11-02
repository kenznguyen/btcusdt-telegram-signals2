# T0 Single Writer Gateway — RED contract scope

Baseline: `a58b6163a78861ecf5bb7d2c8fc11aa420142837`

Phase: RED only. This branch contains contract tests and their isolated runner only.
It must not add or alter production write behavior.

## Safety boundary

- Disposable Shadow directories only.
- No MARKET_DATA_DB, T0_FEEDER_LEASE_DB, or PAPER_DB.
- No exchange credentials or network calls.
- No canonical database creation, Feeder startup, sync, or runtime migration.
- Manual Codemagic workflow only; no push/PR trigger.
- Do not merge this branch or begin GREEN based only on RED results.

## Contract groups

- SWG-A: one Gateway owns the canonical write API; legacy direct write entrypoints must be closed.
- SWG-B: Lease owner, generation, and expiry are checked in the same write transaction.
- SWG-C: batch writes are atomic and operation retries are idempotent.
- SWG-D: non-Gateway consumers receive read-only access; process/filesystem boundaries are tested separately per OS.
- SWG-E: CLI, recovery, adapters, scripts, and direct SQL callers are inventoried and cannot bypass the Gateway.

## RED interpretation

A RED result is valid only when the test process compiles and runs, and failures are attributable to an unmet contract assertion. Import errors, fixture errors, environment leakage, skipped tests, and infrastructure failures are invalid evidence.

This branch deliberately does not implement the Gateway. A successful test run is not evidence that production write paths are closed.
