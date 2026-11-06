# T1 Funding Provenance RED — 2026-11-06

## Scope

PAPER-only contract tests for funding-event provenance, account/strategy attribution, idempotency, immutable evidence, and explicit funding-coverage state. Tests use isolated temporary SQLite databases created by the test fixture. No persistent account database is opened or migrated.

## Source and CI evidence

- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact source SHA: `2af532fee6deb8daf7a337e3a42c007cb9fbf509`
- Commit: `test(t1): add funding provenance RED contracts`
- Workflow run: [42192251105](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42192251105)
- Event: push
- Checked-out SHA: `2af532fee6deb8daf7a337e3a42c007cb9fbf509` (verified in job log)
- Job: `127806851954`, conclusion FAILURE as expected for RED
- Compile: PASS
- Existing focused Dual Ledger and migration tests: 28 PASS
- New funding tests: 3 ERROR at the missing API boundaries:
  - `record_funding_event`
  - `record_funding_coverage`
- Focused test invocation: 31 tests, 3 errors; all pre-existing tests passed.
- Full `paper_execution` regression: SKIPPED after expected focused RED failure; not a PASS.
- Artifact: `dual-ledger-red-evidence-2af532fee6deb8daf7a337e3a42c007cb9fbf509`
- Artifact ID: `13490227810`
- GitHub upload digest: `sha256:0a14b243a243fc49e5503503389f4d7804f244a1b9a937303cf81cdc6a33d245` (metadata/log digest; payload bytes not independently re-hashed here)
- Artifact expires: 2026-11-13.

## Contract tests added

1. Funding event has source, source snapshot ID, event timestamp, strategy attribution, signed amount, payload hash and recorded timestamp; retries are idempotent; changed payload under the same event ID conflicts; update/delete are rejected; account equity reflects the event exactly once.
2. Known historical funding with unknown strategy owner is recorded to `LEGACY_UNATTRIBUTED`, not Core or AI.
3. Unknown funding coverage forces account risk readiness false. A funding-disabled paper test must persist explicit source, snapshot ID, payload hash and config version.

## Design constraints for GREEN

- Preserve migrations v1-v3 and their checksums; use additive migration v4.
- Keep funding events and coverage records append-only and immutable.
- Use signed funding amount semantics consistently with account equity: positive amount is a funding cost; negative amount is a funding credit.
- Stable event identity and payload hash must make retries idempotent; same identity with changed payload must fail.
- Account-level historical funding with known amount but unknown strategy owner belongs to `LEGACY_UNATTRIBUTED`; it must not contaminate Core/AI PnL.
- Unknown historical funding is not zero and blocks risk readiness.
- Funding-disabled paper tests require explicit persisted configuration/version evidence; this is not a default assumption.
- External source bytes are not fetched by this local ledger API. A stored source snapshot ID and SHA-256 fingerprint are provenance references, not proof that the external source bytes were independently re-hashed.

## Status

**RED CONFIRMED; GREEN NOT IMPLEMENTED.** No source implementation, persistent database migration, backtest, merge, deployment, exchange connection, or live execution was performed in this increment. T0 remains unchanged; Option C remains the default provider policy; `ai_execution_enabled=false`.

## Next

Implement migration v4 and the two append-only APIs in small slices. Then add account-equity cutover RED tests requiring verified funding coverage, fresh mark/candle, dataset identity, one-time capital reconciliation, HWM and UTC daily baseline creation. Run focused and full `paper_execution` regressions on the exact implementation SHA. Do not run a persistent database migration or backtest without separate approval.
