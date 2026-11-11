# SSH Preflight Retirement — 2026-11-11

## Owner decision and scope

Owner approved retiring SSH Preflight across the repository while preserving Git history and historical evidence. The change removes the repository-managed SSH Preflight feature from the default branch, the active T0/T2 branch, and the four SSH-specific working branches listed below.

## Changes

- Removed `ops/ssh/t0-readonly-preflight.sh`.
- Removed `ci/test_t0_ssh_preflight_contract.py`.
- Removed the `scaleway-ssh-preflight` and `scaleway-ssh-contract-only` workflow inputs.
- Removed the `ssh-preflight-contract` and authenticated `ssh-preflight` jobs and the workflow trigger used only for SSH contract checks.
- Removed stale references to the deleted contract test from the active T0/T2 workflow, including its isolated test step, test command lists, path filters, and changed-file allowlists. Other T0 workflow gates were retained.
- Preserved historical evidence documents and all existing Git commits. No history rewrite, force-push, branch recreation, merge, rebase, or cherry-pick was performed.

## Exact branch heads after retirement

| Branch | Head SHA |
|---|---|
| `main` | `a4e3a625c84dcc2130f1642b6e2abf60aef66384` |
| `feature/t0-centralized-data-feeder-p1-20261101` | `171084311f00517eba529fdf1ea026af7c4dcdc7` |
| `fix/p1-ssh-preflight-contract-20261110` | `abd8242d879136a467d91d3d2b1d0c84794834a1` |
| `fix/p1-ssh-preflight-main-20261111` | `540857245f59e72c12a7cb36b07ee5a30c0e37b9` |
| `fix/scaleway-ssh-passphrase-preflight-20261110` | `e6080f7ad8a9bd8b89640f6646ff49215c326602` |
| `fix/t0-ssh-preflight-passphrase-20261110` | `e36c7e49b5b2ad875104766f846c3bebef048e91` |

The four SSH-specific branches remain present as historical branch refs; their Preflight implementation has been removed. Branch deletion was not performed.

## Pull requests

- PR #139: closed without merge after removing the feature from its head branch.
- PR #140: already merged before this retirement; historical merge retained.
- PR #144: already merged before this retirement; historical merge retained.

## Verification

- GitHub readback confirms, on all six listed branches, that the workflow no longer contains SSH Preflight jobs/references and both the script and contract-test paths are absent.
- The active T0/T2 workflow retains its non-SSH manual gates. Its remaining workflow text contains no references to the deleted SSH script, test module, SSH Preflight inputs, or SSH secrets.
- Repository changes are committed on the existing branch refs; no branch history was rewritten.
- Source removal/readback: **PASS**.
- Workflow YAML/Actions execution: **NOT VERIFIED**; no workflow was dispatched.
- Regression test execution: **NOT RUN**. The dedicated SSH contract tests were removed by design; unrelated T0 test suites were not run as part of this retirement.

## Safety boundaries

- No SSH connection or VPS command was made.
- No SSH key, GitHub secret, credential, host configuration, or ForceCommand setting was changed.
- The previously used Scaleway VPS had already been deleted; this repository change does not modify any replacement VPS.
- No T0 canonical database/data, T1/T2 runtime, deployment, AI training, exchange connection, or trading state was changed.
- Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.

## Status and next step

- Retirement of repository-managed SSH Preflight on the six scoped branches: **PASS**.
- CI/workflow runtime verification: **NOT VERIFIED**.
- Next: if the retained T0 workflow is to be relied on after this edit, run its ordinary non-SSH CI/validation gate on the exact active-branch SHA and record the resulting run/artifacts. Do not restore SSH Preflight or modify VPS/SSH configuration without a new explicit approval.
