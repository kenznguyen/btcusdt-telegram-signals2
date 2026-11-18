# Workflow Integration Review — bounded pass 2 — 2026-11-18

## Scope and exact refs

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/core-operational-proof-20261112`
- Branch HEAD before review record: `9c0c7866dc62593a7e3412f439c7c65781b4f9ba`
- Main HEAD: `6bff2aff91657238297848ef644a0cb4112ab428`
- Core operational proof workflow:
  - main blob: `1c0d9e7b6c8355264aa509342175d72931b64cc4`
  - branch blob: `0c2d86d76d4d3281e3d7ffb9904a820cf30df547`
- T0 manual validation workflow:
  - main blob: `e4d5ecc712bf590d5b4f7587fa649cbc94d4f8e2`
  - branch blob: `e298db15ce16f1deb72dbce466513037319b0f6f`
- Review type: static workflow source comparison only. No workflow dispatch, Actions run, test execution, source edit, runtime access or merge simulation.

## 1. Core operational proof workflow

### Parity and branch additions

- Both versions have one `operational-proof` job, Ubuntu runner, 20-minute timeout, Python 3.12, `requirements-web.txt`, read-only repository permission, concurrency protection, and disposable paper-only environment.
- Both versions compile operational/Core modules and run the same overall sequence of Core, Shared Risk/Paper Ledger, T0/Paper isolation, T1/T2 order-book, crash-checkpoint and evidence-publication gates.
- Main has 35 steps; branch has 37.
- Branch adds two explicit regressions:
  1. `Run Dual Ledger bootstrap fixture contracts` — `paper_execution.test_dual_ledger_bootstrap`.
  2. `Run Kill Reset RED-to-GREEN regression contracts` — targeted Kill Switch control-token, bootstrapped dual-ledger reset, and fail-closed not-ready tests.
- Branch push path filters additionally include `paper_execution/test_support.py` and `paper_execution/test_dual_ledger_bootstrap.py`.
- The two additional branch tests are material Core First safety coverage and should be preserved. Main's version is weaker on these explicit regressions.
- Both versions retain `AI_EXECUTION_ENABLED=false`, blank exchange credential/database environment values, exact-source checkout with `persist-credentials: false`, `contents: read`, and artifact publication without raw candle DB.

### Disposition

**Prefer the branch workflow's two additional tests and path coverage.** No reason was identified to replace it with main's shorter version. This is a source-level parity result, not a fresh CI execution; the previously recorded branch exact-SHA workflow PASS remains tied to its recorded source SHA and does not transfer to main.

## 2. T0 manual validation workflow

### Main version

- 126 lines, one job (`manual-gate`), 11 steps.
- Trigger: `workflow_dispatch` only.
- Six manual choices: final runtime config, P3 component tests, Kraken adapter, Kraken SQLite persistence, Kraken read API, disposable TimescaleDB integration.
- No automatic lease/fencing, recovery, data-flow or G4 read-only runtime-contract jobs.

### Branch version

- 533 lines, eight jobs: seven automatic/change-scope jobs plus `manual-gate`.
- Adds a manual `sqlite-lease-fencing` choice.
- Adds automatic isolated jobs for:
  - SQLite lease/fencing;
  - recovery/scheduler/startup lifecycle;
  - T0 sync/API to T2 HTTP consumer data flow;
  - G4 read-only SQLite runtime contract.
- Retains the manual runtime config, P3, Kraken and disposable TimescaleDB gates.
- Automatic jobs clear relevant database, token and exchange credential environment variables, check isolated scope, record source SHA, and upload scoped artifacts.

### F-07 — Change-scoped job dependency chain can suppress independent tests

The branch workflow currently has this dependency pattern:

- `sqlite-recovery-auto` runs only when `recovery-change-scope.outputs.changed == 'true'`; otherwise it is skipped.
- `sqlite-data-flow-auto` requires `sqlite-recovery-auto.result == 'success'` as well as its own data-flow change scope.
- `sqlite-g4-runtime-contract-auto` requires both `sqlite-recovery-auto.result == 'success'` and `sqlite-data-flow-auto.result == 'success'`, in addition to its own G4 change scope.

Consequently, when a data-flow-only change occurs and the recovery job is correctly skipped, the data-flow job cannot satisfy its upstream `sqlite-recovery-auto == success` requirement. Likewise, a G4-only change can be suppressed because the recovery or data-flow job is skipped. The current dependency chain couples separately change-scoped gates to unrelated changes.

- Classification: **STATIC WORKFLOW CONTROL-FLOW DEFECT — HIGH CONFIDENCE**.
- No Actions run was dispatched to demonstrate the skip in practice.
- Recommended design for a future approved workflow fix: make each scoped test job depend on its own change detector and only genuine prerequisites; if skipped upstream jobs are intentionally acceptable, encode that explicitly (e.g. success-or-skipped with a deliberate status-check condition) rather than requiring unconditional success. Preserve fail-closed behavior for failed prerequisites.

### F-08 — Pull-request condition has no pull-request event trigger

- Several automatic jobs use `github.event_name == 'push' || github.event_name == 'pull_request'`.
- The workflow's event declaration contains `workflow_dispatch` and a `push` trigger, but no `pull_request` trigger.
- Therefore the pull-request branches in those job conditions are unreachable under the current trigger declaration. This is dead condition logic, not PR CI coverage.
- The push trigger is restricted to `feature/t0-centralized-data-feeder-p1-20261101`; it does not trigger automatically on the current Core First branch or main.
- Whether to add PR/main coverage is a governance/integration decision; do not widen triggers without approval.

### F-09 — Main T0 workflow is a reduced manual-only workflow

- Main's T0 workflow does not contain the branch's automatic isolated lease/fencing, recovery, data-flow or G4 jobs.
- Main's workflow is not an equivalent replacement for the branch workflow. Replacing the branch file with main would remove those automatic gates and the manual lease/fencing option.
- The branch workflow includes broader automated coverage, but F-07/F-08 mean that coverage is not reliably activated for all independent changes or pull requests.
- The workflow's manual TimescaleDB gate consumes `MARKET_DATA_TEST_DATABASE_URL`; it explicitly fails when the secret is missing. This is a disposable integration-test dependency, not authorization to access canonical T0. No secret value was read.

### F-10 — Several P3 components remain manual-only and are outside the push path filter

The branch's manual P3 gate runs `market_data.test_feeder_retry`, `market_data.test_feeder_health`, `market_data.test_feeder_health_api`, and compiles `app.py`. These paths are not present in the workflow's push path filter. A change limited to one of these files therefore does not trigger this workflow automatically. Kraken adapter/store/API source and tests are also manual-choice gates rather than automatic push gates.

- Classification: **AUTOMATION COVERAGE LIMIT — CONFIRMED FROM PATH FILTER**.
- This may be intentional for manually selected/less frequently changed components; it is not automatically a defect unless those files are expected to receive push-time CI.
- The workflow currently has no `pull_request` trigger and its push branch filter is limited to the legacy T0 branch, so this manual-only coverage is not automatically activated on the current Core First branch or main.

## Integration disposition

1. Preserve the branch Core operational proof workflow, including Dual Ledger bootstrap and Kill Reset regressions.
2. Do not replace the branch T0 workflow with main's manual-only file.
3. The branch T0 workflow is the richer candidate, but it is **NOT READY FOR INTEGRATION AS-IS** until F-07 dependency semantics and F-08 trigger intent are corrected/reviewed.
4. Do not add PR/main triggers automatically; first decide intended branch/event coverage.
5. Decide whether P3 and Kraken gates are intentionally manual-only; if not, update path coverage in a separately approved change.
6. Do not infer test PASS from YAML presence. No workflow was run in this review.

## Status

- Core workflow comparison: **PASS — branch has stronger explicit Core First regressions**.
- T0 workflow feature inventory: **PASS — branch retains and extends manual gates with scoped automation**.
- T0 job dependency semantics: **BLOCKED — F-07**.
- PR trigger coverage: **NOT CONFIGURED / NOT VERIFIED — F-08**.
- Main-vs-branch workflow integration decision: **PARTIAL**.
- Runtime/test evidence for this review: **NOT RUN**.
- Merge: **BLOCKED / NOT AUTHORIZED**.

## Next bounded actions

1. Inspect the remaining T0 workflow gate bodies and exact change-path coverage for omissions or accidental secret/data exposure.
2. Prepare a minimal proposed correction for F-07/F-08 without applying it.
3. Reconcile the main-only G0.52 audit evidence against the current handoff and evidence baseline.
4. Prepare an integration map only. No workflow edits, dispatch, merge, rebase, reset, force-push, VPS/runtime/T0 access, AI execution or real orders without separate approval.
