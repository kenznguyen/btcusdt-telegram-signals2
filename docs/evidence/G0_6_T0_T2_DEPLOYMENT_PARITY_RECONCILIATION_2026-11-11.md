# G0.6 — T0/T2 Deployment Parity Evidence Reconciliation
Date: 2026-11-11 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Starting branch HEAD: `26b28dbe87a324b454231d3d8e9fe1a659e0ad7d`

## Scope
Documentation-only reconciliation of the T0 → T2 deployment parity evidence on the existing branch. No source, workflow, test, runtime, VPS, canonical T0 database, T1, model-training, or trading changes are included.

## Inputs compared
- Main version: `docs/evidence/T0_T2_DEPLOYMENT_PARITY_EVIDENCE_RECONCILIATION_2026-11-10.md`, blob `4d3aeb82d373682a291222847896e104455e950c`.
- Active-branch version: `docs/evidence/T0_T2_DEPLOYMENT_PARITY_EVIDENCE_RECONCILIATION_2026-11-10.md`, blob `25aa2cae62fb7a693bc31d80a359fe304555e7ad`.
- Active-branch handoff read at start: `docs/PROJECT_SESSION_HANDOFF.md`, blob `f340207df736ef34eaa99cd0718a6b7f4c4617b4`.
- Main HEAD at review: `7021e0e1a7183c201652a0168eaffc4deb798f10`.
- Active branch HEAD at review: `26b28dbe87a324b454231d3d8e9fe1a659e0ad7d`.

## Reconciliation findings
1. Both parity documents preserve the same essential historical facts: operator-provided observations from 2026-11-09; T0 source SHA `9ae2eeae4ece3d657781b68e96b6f4509cd95f24`; T2 context SHA-256 `e22d6c7d186b1fb9a5079eb9b4224c8acbcd835a0938dc970e9bc4b072eb75d3`; historical API authentication and M15/H1 bounded reads; 8,558 ms M15 ingestion lag against configured 120,000 ms; and the bounded two-bar T2 context read.
2. Neither document proves current service state, current checkout/process byte identity, continuous freshness, scheduled FreqAI operation, or current VPS availability. Their historical PASS labels must remain time-bounded.
3. The active-branch version already contains the essential historical provenance and fail-closed limitations. Main has slightly clearer phrasing in places, but no material technical fact justifies wholesale replacement.
4. Owner-provided project context confirms the Scaleway VPS was fully deleted on 2026-11-11. This supersedes any implication that the former host remains available for current runtime inspection. The old 2026-11-09 results remain historical evidence only; they cannot establish a current deployment.
5. The handoff read at the start still contains stale SSH-preflight/G4 runtime instructions and an older PR #139 state. G0.6 does not attempt to reconcile those separate workstreams; this is recorded as a documentation consistency limitation for a separately scoped handoff correction.

## Corrected disposition
- 2026-11-09 bounded T0 → T2 loopback observation: **HISTORICAL PASS**, based on operator-provided evidence.
- Current T0/T2 deployment parity: **NOT VERIFIED**.
- Former VPS availability: **DELETED 2026-11-11**, per owner-provided project update.
- Current runtime/service/process state: **NOT APPLICABLE TO THE DELETED HOST / NOT VERIFIED ELSEWHERE**.
- New runtime probe: **NOT RUN** and not authorized by this documentation-only gate.

## Evidence and safety boundaries
- No new VPS, SSH, network, API, database, or service probe was performed.
- No workflow was dispatched; no tests or compilation were run.
- No T0 canonical data, lease/fencing state, ledger, audit/recovery evidence, or retained project data was modified.
- T1 remains not activated; PostgreSQL/TimescaleDB remains parked.
- `AI_EXECUTION_ENABLED=false`; paper-only; no real orders.
- This document does not authorize provisioning a replacement VPS, deploying services, activating T1, training FreqAI, or changing strategy/risk behavior.

## Result
G0.6 evidence reconciliation: **PASS**.
Runtime parity: **NOT VERIFIED**.
Source integration: **NOT APPLICABLE** (documentation-only).
Tests: **NOT RUN**.
Exact-SHA GitHub Actions CI: **NOT VERIFIED** (no workflow run initiated).

## Next step
If the owner wants to resume runtime validation, first approve a separate bounded VPS provisioning/deployment scope. Before that, a separately scoped handoff cleanup should reconcile the retired SSH-preflight/G4 instructions and current PR state.

## GitHub write and verification record
- Parity addendum commit: `15b9afd52e59969ac6d21bc74d418e1ac3e42bfa`; resulting parity blob: `f60953af5afdb1a0d10826580ad010e312603ee5`.
- Initial G0.6 report commit: `c48d53dbb9bea5b08ae43418e50c1578d9d300f6`.
- Handoff update commit: `337f19f356d2030fbbaeb1b436d6c22265c15a1e`; resulting handoff blob: `1bbbc749e17094561e5310c512fb841cf0f83ada`.
- Post-write readback confirmed the report, parity addendum and handoff on the active branch. Branch HEAD at readback: `337f19f356d2030fbbaeb1b436d6c22265c15a1e`.
- Exact-SHA Actions query for `337f19f356d2030fbbaeb1b436d6c22265c15a1e`: 0 workflow runs. CI: **NOT VERIFIED**.
