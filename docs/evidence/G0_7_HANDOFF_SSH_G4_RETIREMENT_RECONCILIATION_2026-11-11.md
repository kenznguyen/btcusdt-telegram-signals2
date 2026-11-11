# G0.7 — Session Handoff SSH Preflight / G4 Retirement Reconciliation
Date: 2026-11-11 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Starting HEAD: `2881ad334d9e73f9ff7ac146d47b0ddf13f0a5c8`

## Approved scope
Documentation-only cleanup of stale active handoff instructions concerning SSH Preflight, G4 VPS runtime acceptance, and PR #139. No source/workflow/test/runtime/VPS/database/T1/T2/strategy/trading changes.

## Read-only findings
- Current handoff blob before edit: `8db70b843ac0001a2ac996dfb49be0feb2a477e1`.
- The top-level repository status incorrectly described PR #139 as OPEN / DRAFT / NOT MERGED.
- GitHub PR #139 current API state at review: **CLOSED**, `draft=true`, `merged=false`; closed at `2026-11-11T13:02:13Z`. Title: “Secure Scaleway SSH preflight passphrase handling”. Head SHA `e6080f7ad8a9bd8b89640f6646ff49215c326602`; base branch `feature/t0-centralized-data-feeder-p1-20261101`.
- Existing retirement record in the handoff confirms repository-wide SSH Preflight removal on six refs while retaining history. The dedicated retirement evidence is `docs/evidence/SSH_PREFLIGHT_RETIREMENT_2026-11-11.md`.
- Historical G4 contract CI run `42824628084`, source `a6d939252f1651c4f8f5478bf49581824cc67cc9`, is retained as historical disposable-runner evidence, not VPS runtime evidence.
- Owner-provided project update states the former Scaleway VPS was fully deleted on 2026-11-11. No replacement VPS is established in this workstream.
- The active handoff also contained a detailed G4 runtime acceptance section, old SSH preflight host/process observations, and a next step requiring evidence from the former host. Those are no longer actionable.

## Changes made
1. Corrected the top-level PR #139 status to CLOSED / NOT MERGED.
2. Replaced the obsolete active G4 runtime workstream with a retired-workstream record.
3. Preserved historical workflow run references and explicitly labeled them historical.
4. Recorded that the former VPS was deleted and that current deployment parity remains NOT VERIFIED.
5. Explicitly prohibited restoring SSH Preflight or treating old G4 approval as authority for provisioning, deployment, remote commands, or runtime changes.
6. Left the historical archive and earlier dated G0 audit records unchanged; their point-in-time PR status statements remain historical snapshots.

## Verification
- Handoff was written on the existing active branch; no branch/PR divergence introduced.
- No tests, compile, workflow dispatch, Actions artifact generation, SSH/VPS/API/database probe, or runtime operation was performed.
- Exact-SHA CI: **NOT VERIFIED**.
- Source/workflow changes: none.
- Runtime parity: **NOT VERIFIED**.
- PR #139: **CLOSED / NOT MERGED**.

## Result
G0.7 documentation reconciliation: **PASS**.
Handoff status accuracy for retired SSH/G4 workstream and PR #139: **PASS**.
Tests: **NOT RUN**.
GitHub Actions CI: **NOT VERIFIED**.

## Next step
Use this corrected handoff as the starting point for the next task. Any replacement VPS provisioning/deployment or reactivation of a retired capability requires separate explicit approval.
