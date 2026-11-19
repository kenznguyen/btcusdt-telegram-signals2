# T0 SQLite-first CI trigger isolation — 2026-11-19

## Approval and scope

This change implements the user's approval to prevent a T0 SQLite-only source change from automatically triggering PostgreSQL, T1, paper-consumer or T2 workflows.

Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Final source HEAD: `6e5f8e04f63b5cd1806517acee32ffcee6507d0f`

No application/runtime source, requirements manifest, canonical database, VPS configuration or trading behavior was changed.

## Workflow changes

### 1. T0 Manual Validation

File: `.github/workflows/t0-manual-validation.yml`  
Blob SHA: `47c49a119a3fe55677e66582fdb28728bed4c87f`

- Removed FreqAI bridge paths from the T0 push trigger.
- Kept T0 SQLite/Feeder/Storage/API paths relevant to the T0 validation workflow.
- Narrowed the internal data-flow change detector: generic feeder/store/write-gateway changes no longer trigger the T0-to-T2 data-flow test job. That job remains eligible for explicit sync/API/HTTP consumer changes.
- The lease/fencing and recovery test jobs remain eligible for relevant T0 SQLite changes.

### 2. T0 Single Writer Gateway Contracts

File: `.github/workflows/t0-single-writer-gateway-red.yml`  
Blob SHA: `2c97678cc2587e899be1e343fe03d94e47234e22`

- Removed automatic `push` and `pull_request` triggers.
- Kept `workflow_dispatch`.
- This workflow currently bundles SQLite Gateway checks with T1 importer/Rust, paper-consumer and PostgreSQL provider/TimescaleDB jobs. It is now manual-only so a SQLite-only T0 push cannot fan out into those unrelated jobs.
- Manual dispatch still runs the workflow's existing bundled jobs; it must not be treated as a SQLite-only acceptance workflow.

### 3. T2 Freqtrade strategy smoke

File: `.github/workflows/t2-freqtrade-2026-9-strategy-smoke.yml`  
Blob SHA: `8ec80e5332a5ce4db9398acb25148927eef9fa87`

- Removed `market_data/**` from both `push` and `pull_request` path filters.
- T2 smoke remains triggered by `freqai_bridge/**`, `pipeline/**`, and its own workflow definition.

## Verification

Read-back verification from GitHub at final HEAD:
- T0 Manual Validation contains only T0 paths in its push filter; no FreqAI bridge path remains.
- T0 Single Writer Gateway has only `workflow_dispatch`; no automatic push or pull-request trigger remains.
- T2 strategy smoke has zero `market_data/**` entries in either automatic trigger.
- Recent Actions runs remain the prior runs on SHA `7faef47cb93ec8563583aa29e9a6104ccc35f835`; no new run was observed after these `[skip ci]` workflow commits.

This is source-level/read-back verification, not a completed runtime execution of each workflow. The next qualifying SQLite source push is the first end-to-end trigger verification. YAML parsing and GitHub Actions execution on the new workflow definitions are **NOT VERIFIED** yet.

## Commit provenance

Sequential commits on the same existing branch:
1. `c5b2a2f91e84e8e33ffbe18e420ec45fb5511b7e` — T0 Manual Validation trigger/data-flow scope.
2. `4a569473f6b9306367001e989335105940aa6e0b` — T0 Single Writer Gateway made manual-only.
3. `ed5b28d467ce0b92070455820f71274f0ef2287a` — T2 push trigger narrowed.
4. `6e5f8e04f63b5cd1806517acee32ffcee6507d0f` — T2 pull-request trigger narrowed; final HEAD.

No branch switch, merge, rebase, PR creation or cherry-pick.

## Status

| Item | Status |
|---|---|
| T0 SQLite push trigger no longer includes T2 bridge paths | **PASS — source verified** |
| T0 SWG no longer auto-runs bundled PG/T1/paper jobs | **PASS — source verified** |
| T2 no longer auto-runs on `market_data/**` changes | **PASS — source verified** |
| New workflow YAML parsed by Actions / end-to-end trigger behavior | **NOT VERIFIED** |
| T0 application/runtime behavior | **UNCHANGED / NOT TESTED IN THIS CHANGE** |

## Next step

Proceed with the already RED-confirmed F1 regression: require a valid existing `feeder_leases` schema during SQLite Write Gateway preflight, fail closed without creating or modifying schema, then run the isolated SQLite test suite on the exact source SHA. Keep PostgreSQL, runtime, canonical data recovery and deployment excluded.
