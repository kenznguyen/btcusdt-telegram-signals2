# PR #140 Source Review — 2026-11-10

## Review identity

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Pull request: [#140](https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/140)
- Branch: `fix/p1-ssh-preflight-contract-20261110`
- Exact reviewed PR head: `d8da2a9b16185462e9dc20e4c5b53830418f0670`
- Base SHA: `9cb38cdd995158704fe2993e277396bb9bf4b50a`
- Review scope: all 5 changed files; correctness, security, architecture, readability, test adequacy, workflow isolation.
- PR state at review: OPEN / DRAFT / NOT MERGED.

## Summary

**Verdict: BLOCKED — do not promote PR to ready-for-review or merge.**

The contract-only workflow structure is correctly isolated from authenticated SSH: the generic manual job excludes both SSH gate values, the contract job runs for either SSH gate, and the authenticated job runs only for `scaleway-ssh-preflight`. The contract-only job does not receive the Scaleway private-key secret. The SSH job retains pinned known-host checking and BatchMode.

However, the remote preflight script still contains a fail-open branch and an incorrect process-matching regular expression. The current six tests are source-text assertions and do not exercise these runtime failure modes.

## Required findings

### R1 — awk failure is incorrectly treated as a verified loopback listener

- File: `ops/ssh/t0-readonly-preflight.sh`
- Relevant block: `printf '%s\\n' "$listeners" | awk ...`
- Severity: **Required / security correctness blocker**.
- Current behavior: the `if` condition's pipeline returns nonzero when `awk` is unavailable or fails. Its `else` branch then assigns `api_state="LOOPBACK_LISTENER"`. Because the script only rejects `NON_LOOPBACK_LISTENER`, `CHECK_UNAVAILABLE`, and `CHECK_FAILED`, this unverified state can exit 0.
- Required correction: explicitly verify the parser dependency and classify parser absence/failure as `CHECK_UNAVAILABLE` / `CHECK_FAILED`; only emit `LOOPBACK_LISTENER` after a successful parse that positively validates every listener address. Preserve fail-closed nonzero exit behavior.
- Required regression tests: simulate missing `awk`, nonzero `awk`, valid loopback output, and non-loopback output using controlled command stubs/PATH. Assert the first two return nonzero and never emit a successful loopback state.

### R2 — feeder process pattern is over-escaped

- File: `ops/ssh/t0-readonly-preflight.sh`
- Relevant expression: `pgrep -f '[m]arket_data\\\\.feeder'`
- Severity: **Required / evidence correctness blocker**.
- Finding: the single-quoted argument passes two backslashes before the dot to the extended regular-expression matcher. The resulting expression matches a literal backslash followed by a character, rather than the dot in the expected module name. A representative command line `python -m market_data.feeder` does not match this pattern (reproduced with the equivalent Python regular expression engine).
- Impact: an existing Feeder can be reported as `FEEDER_PIDS=NONE`, producing misleading runtime evidence and a false partial-component classification.
- Required correction: use a correctly escaped literal dot for the target regex, or use a more robust process identification method that does not rely on an ambiguous over-escaped pattern.
- Required regression tests: test the exact pattern against representative command lines for `market_data.feeder`, unrelated processes, and the pgrep self-match avoidance behavior.

### R3 — pgrep unavailable/error is indistinguishable from no feeder

- File: `ops/ssh/t0-readonly-preflight.sh`
- Severity: **Required / evidence quality blocker**.
- Current behavior: if `pgrep` is missing or returns an operational error, `|| true` suppresses the distinction and the script reports `FEEDER_PIDS=NONE`.
- Required correction: distinguish a successful empty process query from unavailable/failed process inspection (for example, explicit `CHECK_UNAVAILABLE` / `CHECK_FAILED` states). Ensure the workflow does not label an unavailable check as confirmed process absence.
- Required regression tests: simulate missing `pgrep`, failed `pgrep`, and successful empty output.

## Test quality assessment

The six Python tests pass in workflow run #42793921622 on source SHA `029f4b66b51699c4c037f79bcfece2c522690580`. They are static substring/pattern checks, not execution tests. They did not detect R1 or R2. Add behavior-oriented tests for the failure cases above before accepting the script contract.

The workflow run verifies the six static tests and shell syntax only. It does not verify live remote command behavior or VPS state. The run checked out SHA `029f4b66b51699c4c037f79bcfece2c522690580`; the current reviewed head `d8da2a9b...` adds the evidence document only, leaving the reviewed script/test blobs unchanged.

## Other file assessments

- `.github/workflows/t0-manual-validation.yml`: gate conditions are separated correctly. Contract-only does not execute the generic acceptance job or authenticated SSH job. Authenticated SSH remains exclusive to the original gate.
- `ci/test_t0_ssh_preflight_contract.py`: useful basic source guardrails, but insufficient behavioral coverage as described above.
- `docs/PROJECT_SESSION_HANDOFF.md`: records the fail-closed code change but its latest next-step text still asks for a contract-only run, despite run #42793921622 now being complete. Update the handoff to point to the new run/evidence and these review blockers.
- `docs/evidence/P1_SSH_PREFLIGHT_CONTRACT_RUN_42793921622.md`: correctly records the run's scope and limits; no artifact was produced and SSH job was skipped.

## Verification provenance

- Workflow [#42793921622](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42793921622): SUCCESS, contract job SUCCESS; six tests PASS; authenticated SSH job SKIPPED; no artifact.
- Exact checked-out SHA for that run: `029f4b66b51699c4c037f79bcfece2c522690580`.
- Review source SHA: `d8da2a9b16185462e9dc20e4c5b53830418f0670`.
- Script blob SHA: `b89b6315fd56965db95be1dcf92ac9256c394f97`.
- Test blob SHA: `1da7b0eb0f20a4c2f69542ee9d7c211cd4e2e67f`.
- No VPS/SSH access, deployment, credentials/secret changes, database access, service changes, or data deletion performed.

## Next permitted step

Fix R1–R3 and add behavior-oriented regression tests on the same PR branch. Run the contract-only workflow again against the resulting exact head SHA. Keep PR #140 OPEN / DRAFT / NOT MERGED. Do not dispatch authenticated `scaleway-ssh-preflight`, deploy the script, or change VPS state without separate explicit authorization.
