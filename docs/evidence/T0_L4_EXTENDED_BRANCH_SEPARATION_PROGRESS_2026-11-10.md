# T0 L4-Extended Branch Separation — Progress Record

Date: 2026-11-10
Repository: kenznguyen/btcusdt-telegram-signals2
Active branch: feature/t0-centralized-data-feeder-p1-20261101
Baseline HEAD before this record: f18134154eb40b564cc4aef9f2af2452d7515208

## Decision retained

- Keep T0 Core and L4-Minimum on the existing active branch.
- Develop L4-Extended independently on the planned branch `feature/l4-extended-provenance`.
- Create the Extended branch only from a frozen, accepted L4-Minimum commit. Do not branch from an unaccepted or blocked baseline.
- Extended must not modify the T0 canonical write path, weaken or replace L4-Minimum controls, become a prerequisite for T0 operation, or auto-merge into the active branch.
- Preserve all parked modules, documentation, tests and data; PARK means preserve, not delete.

## Scope boundary

### T0 Core + L4-Minimum — remain on active branch

Preserve Binance USD-M BTCUSDT M15/H1, SQLite canonical storage, fenced writer/lease, fail-closed recovery and integrity, read-only Candle API, T2 contract, regression coverage, canonical/recovery data and provenance.

L4-Minimum acceptance policy:
- L4M-01–08 remain mandatory.
- L4M-09 (mandatory independent review) is owner-waived.
- L4M-10 is owner self-assessment.
- All nine applicable controls must PASS on one frozen evidence baseline.
- Current L4-Minimum status remains BLOCKED / NOT VERIFIED; therefore no accepted/frozen branch point exists yet.

### L4-Extended — planned separate branch

Candidate scope:
- RFC3161 timestamp authority (TSA)
- OCSP / CRL
- Multi-TSA and quorum
- WORM / Object Lock
- Root A / Root B extensions

Constraints:
- Optional extension only; never required for T0 or L4-Minimum acceptance.
- No change to canonical write path or T0 authority boundaries.
- No automatic merge.
- PostgreSQL / TimescaleDB migration, public HTTPS, disaster recovery and multi-region durability remain separate/PARKED scopes unless separately approved.
- Do not delete or relocate existing implementation, tests, docs or data merely to achieve branch separation.

## Current repository evidence

- Active branch HEAD at planning time: f18134154eb40b564cc4aef9f2af2452d7515208.
- Existing branch handoff blob before this update: 593776475684b3e582069b1192161354aa2d9b89.
- Branch search found no existing `feature/l4-extended-provenance`.
- No Extended branch was created because L4-Minimum has not reached the required frozen acceptance gate.

## Status

- Scope decision: RECORDED.
- Separation design: DOCUMENTARY PLAN.
- L4-Minimum acceptance: BLOCKED / NOT VERIFIED.
- Extended branch creation: BLOCKED pending accepted/frozen L4-Minimum commit.
- Implementation, migration and merge: NOT AUTHORIZED by this record.
- Tests / GitHub Actions: NOT RUN; no workflow run or artifact is claimed.
- Runtime, VPS, SQLite, PostgreSQL, secrets, permissions and network: NOT ACCESSED OR CHANGED.
- Destructive authority: NONE; Option C remains ACTIVE.
- Trading posture: paper-only; AI_EXECUTION_ENABLED=false; no live orders.

## Next gate

Continue L4-Minimum documentary closure and obtain the single frozen evidence baseline with all nine applicable controls PASS. Then create `feature/l4-extended-provenance` from that exact accepted commit SHA, record parent SHA and branch SHA, and begin Extended-only work without merging it into the active branch.

Until that gate passes, keep Extended design and scope isolated as documentation only.
