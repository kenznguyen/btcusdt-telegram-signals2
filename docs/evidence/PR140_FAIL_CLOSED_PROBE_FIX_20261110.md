# PR #140 — Fail-Closed Probe Follow-up — 2026-11-10

## Scope

Address the three required findings from `PR140_SOURCE_REVIEW_20261110.md` on the existing PR branch only:

- R1: distinguish missing/failed `awk` from a positively parsed loopback listener.
- R2: correct the Feeder process regular expression and preserve self-match avoidance.
- R3: distinguish a successful empty `pgrep` result from missing/failed process inspection.

Also update the authenticated workflow's evidence classifier so unavailable/failed probes cannot be reported as a successful preflight.

## Changes

- `ops/ssh/t0-readonly-preflight.sh`
  - API listener state starts as `CHECK_UNAVAILABLE`.
  - Missing `awk` remains `CHECK_UNAVAILABLE`; nonzero parser execution becomes `CHECK_FAILED`.
  - Only explicit parser output `LOOPBACK_LISTENER` is accepted as loopback.
  - Non-loopback listeners remain rejected.
  - Feeder regex is now `[m]arket_data\.feeder`.
  - Missing `pgrep` becomes `CHECK_UNAVAILABLE`; exit status 1 means a successful no-match result (`NONE`); other nonzero statuses become `CHECK_FAILED`.
  - Both unavailable/failed probe states force a nonzero script exit.
- `ci/test_t0_ssh_preflight_contract.py`
  - Added command-stub subprocess tests for missing/failed `awk`, missing/failed `pgrep`, successful empty process results, loopback and non-loopback listener outcomes.
  - Added a semantic regex assertion against representative Feeder and unrelated process command lines.
  - Retained read-only and expected-path guardrails.
- `.github/workflows/t0-manual-validation.yml`
  - The authenticated preflight classifier now rejects `FEEDER_PIDS` or `API_8788` values in `CHECK_UNAVAILABLE` / `CHECK_FAILED` states.
  - Contract-only gate remains isolated from authenticated SSH.

## Source identity

- PR: [#140](https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/140)
- Branch: `fix/p1-ssh-preflight-contract-20261110`
- Current source commit: `55c08a312543260f320d20c54d06033a5a414554`
- Script blob: `6fc3a54c4d91e0ef82aedf1fba2543b4468c756e`
- Test blob: `b823ed3fc5c3d5f7629fee97d237e44eb8e68577`
- Workflow blob: `749d53bf94168a0e0423e1b52f8699ffe2a605d3`

## Verification

- Source-level review of the changed blocks: completed.
- Automated Python tests: **NOT RUN in this session**.
- `bash -n`: **NOT RUN in this session**.
- GitHub Actions contract-only run on this exact source SHA: **NOT RUN**.
- VPS/SSH authentication and deployed script behavior: **NOT VERIFIED**.
- No artifact exists for this source revision yet.

The new subprocess tests are intended to execute the actual preflight script with controlled command stubs. Their success is not claimed until the exact-head workflow has run.

## Safety boundary

- No authenticated SSH workflow was dispatched.
- No VPS connection or remote command was executed.
- No credential, secret, host configuration, runtime, service, database, or T0 data was changed.
- No deployment, Feeder activation, PostgreSQL operation, exchange connection, market-data sync, or trading action was performed.
- PR #140 remains OPEN / DRAFT / NOT MERGED.

## Next step

Manually run GitHub Actions **T0 Manual Validation** on branch `fix/p1-ssh-preflight-contract-20261110` with gate `scaleway-ssh-contract-only`. Provide the run URL so the checked-out SHA, shell syntax, all Python tests, skipped SSH job, and artifact metadata can be verified. Do not select `scaleway-ssh-preflight`.
