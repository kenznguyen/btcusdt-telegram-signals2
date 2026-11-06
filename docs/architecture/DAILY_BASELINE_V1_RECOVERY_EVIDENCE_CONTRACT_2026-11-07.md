# Daily Baseline v1 Recovery Evidence Contract

**Status:** Read-only assessment contract; no migration or recovery execution is authorized.

## Purpose

A legacy daily-baseline audit payload without the v2 `riskState` snapshot cannot be promoted to a v2 baseline by filling in current values. In particular, current `high_water_mark_quote`, `version`, readiness, or mark metadata do not prove what those values were when the historical baseline was committed.

The only supported automated outcome is:

- `BLOCKED`: evidence is missing, malformed, or contradictory.
- `ELIGIBLE_FOR_MANUAL_REVIEW`: the supplied evidence manifest is internally complete and consistent enough to begin a separate manual review.

A positive result is **not** migration-ready, does not authorize risk readiness, and does not permit writes.

## Required evidence

The pure assessor `paper_execution.daily_baseline_v1_recovery.assess_daily_baseline_v1_recovery_manifest` accepts a normalized manifest with these sections:

| Section | Required proof |
|---|---|
| `baseline` | Immutable row identity, UTC day boundary, positive equity, mark/cutover IDs, algorithm version and replay digest |
| `audit` | Matching v1 audit identity/type, canonical payload, independently verified digest, replay equity, mark/cutover and algorithm identity |
| `cutover` | Verified immutable cutover and immutable per-ledger snapshots for Core, AI and Legacy |
| `execution` | VERIFIED complete interval from cutover to the half-open UTC boundary; all events attributed/provenanced; explicit USDT fee currency; no late-arriving pre-boundary events |
| `funding` | VERIFIED continuous coverage over the required interval; every event has provenance; no unknown amount is treated as zero |
| `mark` | Verified mark effective exactly at 00:00:00 UTC, source snapshot, dataset version, payload hash and raw-payload byte rehash attestation |
| `risk_state` | Independently retained historical risk snapshot for that exact baseline: UTC day, equity, HWM, version, readiness, mark identity, source snapshot, payload hash and raw-payload byte rehash attestation |

The assessor also cross-checks the shared identities and values: baseline/audit digest, equity, mark, cutover, algorithm, risk-state day/equity/mark, and HWM versus equity when historical readiness was true. Coverage start/end must match the cutover and exact UTC boundary.

## Evidence collection rules

1. Evidence must be read from retained immutable sources. A locally stored hash string by itself is not proof that the original source bytes are authentic.
2. Set `raw_payload_bytes_rehashed=true` only after a separate evidence collector retrieves the exact original payload bytes and recomputes the recorded digest. The pure assessor does not fetch or hash external bytes.
3. Execution history must account for every Core, AI and Legacy fill, partial fill, reduction, reversal, fee and adjustment. Missing owner, fee currency, source identity, or late-arrival watermark blocks review.
4. Funding must have continuous VERIFIED coverage and event-to-coverage membership. UNKNOWN, missing, or ambiguous funding is not zero.
5. The boundary mark must be the exact 00:00:00 UTC mark with matching source snapshot and dataset identity.
6. Historical HWM, risk-state version and readiness must come from independently retained historical risk evidence. Do not infer them from the current risk row or reconstruct them from a single end-of-day equity value.
7. Any mismatch or unavailable field leaves the legacy row unresolved and blocks exposure increases.

## Output contract

The assessor returns:

- `status`: `BLOCKED` or `ELIGIBLE_FOR_MANUAL_REVIEW`
- `eligible_for_manual_review`: boolean
- `missing_evidence`: sorted field paths
- `contradictions`: sorted semantic conflicts
- `migration_authorized=false`
- `automatic_upgrade_authorized=false`
- `mutation_performed=false`

The function is pure: it does not open SQLite, modify its manifest input, alter risk state, create an audit row, or update a baseline.

## Explicitly out of scope

- No automatic v1-to-v2 conversion.
- No inferred or synthesized HWM, risk version, readiness, or mark provenance.
- No historical backfill or baseline replacement.
- No persistent account database opening or migration.
- No admission override and no readiness promotion.
- No production deployment, exchange connection, or live orders.

A future migration/reconciliation requires a separate explicit approval after manual review of the original evidence and a separately tested atomic transaction plan.
