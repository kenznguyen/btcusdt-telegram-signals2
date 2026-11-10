# P1 SSH Preflight Contract Run — 2026-11-10

## Scope

Record the contract-only GitHub Actions verification of the fail-closed SSH listener probe on PR #140. This run is not an authenticated SSH test and does not establish VPS runtime state.

## Source and workflow provenance

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- PR: [#140](https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/140) — OPEN / DRAFT / NOT MERGED
- Branch: `fix/p1-ssh-preflight-contract-20261110`
- PR head / checked-out source SHA: `029f4b66b51699c4c037f79bcfece2c522690580`
- Workflow: [run #42793921622](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42793921622)
- Event: `workflow_dispatch`
- Gate: `scaleway-ssh-contract-only`
- Run result: SUCCESS
- Contract job ID: `129754062623` — SUCCESS
- T0 isolated acceptance job ID: `129754064980` — SKIPPED
- Authenticated Scaleway SSH job ID: `129754109557` — SKIPPED
- Artifacts: NONE

## Verification results

The contract job log confirms checkout of exact SHA `029f4b66b51699c4c037f79bcfece2c522690580`.

- `bash -n ops/ssh/t0-readonly-preflight.sh`: PASS
- `python -m unittest ci.test_t0_ssh_preflight_contract -v`: 6 tests, 6 PASS
- New test `test_listener_probe_fails_closed_when_ss_is_unavailable_or_fails`: PASS
- Existing listener classification, machine-readable evidence, no-mutating-commands, expected paths/port, and strict SQLite read-only tests: PASS

## Verdict

**PASS — contract-only CI on the exact PR head SHA.**

The run validates shell syntax and the six static contract tests for this source revision. It does not prove that the SSH preflight script has been installed or run on Scaleway, that SSH authentication works, or that T0 services/listeners/database are healthy.

## Safety and limits

- Authenticated SSH path was skipped; no SSH connection or VPS command was run by this workflow.
- No credential, passphrase, GitHub secret, host configuration, runtime, service, database, or data was changed.
- No artifact was emitted by this run.
- No deployment, database migration, data deletion, exchange connection, or trading action occurred.
- PR #140 remains OPEN / DRAFT / NOT MERGED. CI PASS is not merge approval.
- Do not dispatch `scaleway-ssh-preflight` without separate explicit authorization.

## Next step

Perform source review of PR #140 and its changed files. Keep VPS/SSH execution, deployment, and merge as separate approval gates.
