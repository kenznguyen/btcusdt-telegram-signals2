# GitHub Actions Execution Map — Read-only Audit

Date: 2026-11-10  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Exact source baseline: `6ab6a11e88aff3b5a12cebe2adce74bc28e8da31`

## 1. Scope and method

Read-only inspection of the exact branch's `.github/workflows/` directory, all workflow YAML files returned by the directory listing, selected complete workflow sections, `codemagic.yaml`, `ci/test_ci_policy.py`, and the branch metadata endpoint.

No workflow was dispatched or re-run. No tests were run. No secrets or secret values were read. No external SSH, exchange, provider, VPS, database or runner host was contacted. No workflow, source, package, configuration, permission or branch-protection setting was changed.

The directory contains **14 active workflow YAML files** on this branch. “Active” here means present under `.github/workflows/`, not that a run is enabled, recently executed, required, or successful.

## 2. Workflow inventory

| Workflow | Trigger / scope | Classification |
|---|---|---|
| `android-release-pair.yml` | Manual `workflow_dispatch`; exact SHA and Android signing secrets; builds paired APKs | OUTSIDE FIVE-LAYER SCOPE / LEGACY ANDROID RELEASE |
| `dual-ledger-red.yml` | Push on current branch for `paper_execution/**`; manual dispatch | PAPER LEDGER CONTRACT TEST |
| `p1-8-synthetic-evidence.yml` | Push on current branch for `synthetic_evidence/**` and named design doc; manual dispatch | SYNTHETIC EVIDENCE / ATTESTATION |
| `p5-3-11-g2-integration-green.yml` | Reusable `workflow_call` and manual dispatch | ISOLATED G2 ACCEPTANCE |
| `paper-writer-isolation-red.yml` | Push and PR on separate named branches; manual dispatch | PAPER WRITER RED CONTRACT |
| `t0-binance-connectivity-probe.yml` | Push on current branch for probe files; manual dispatch | SUPPORT-ONLY OFFLINE CONTRACT |
| `t0-evidence-contract-g2.yml` | Push and PR on current branch for synthetic checkpoint contract files | T0 G2 SYNTHETIC CONTRACT |
| `t0-manual-validation.yml` | Manual dispatch with seven gates: runtime config, P3 tests, Kraken adapter/SQLite/read API, TimescaleDB, Scaleway SSH preflight | MANUAL GATED VALIDATION; contains external SSH and secret-backed integration path |
| `t0-postgres16-grantor-repro.yml` | Push only when this workflow file changes; manual dispatch | PARKED POSTGRESQL / DISPOSABLE TIMESCALEDB REPRO |
| `t0-single-writer-gateway-red.yml` | Push, PR and manual; broad paths include `market_data/**`, `freqai_bridge/**`, `futures_intelligence/**`, `pipeline/**` and requirements | T0 CORE + T1/PAPER/POSTGRES CROSS-DOMAIN TEST AGGREGATE |
| `t0-sqlite-readonly-sandbox.yml` | Push, PR and manual; SQLite/Feeder source and harness paths | DISPOSABLE GITHUB-RUNNER SYSTEMD/WAL SANDBOX |
| `t0-systemd-feeder-api-integration.yml` | Push, PR and manual; Feeder/API source and harness paths | DISPOSABLE TWO-SERVICE GITHUB-RUNNER INTEGRATION |
| `t2-freqtrade-2026-9-strategy-smoke.yml` | Push, PR and manual for T2/pipeline/T0 paths | T2 PAPER STRATEGY LOAD / HTTP REGRESSION |
| `t2-http-consumer-red.yml` | Push only for explicit T2 HTTP adapter and consumer paths | T2 HTTP CONSUMER REGRESSION |

All 14 workflow files and exact blob SHAs:

| File | Blob SHA |
|---|---|
| `android-release-pair.yml` | `b6f6b3deccc01f27fb3c00b0bb5657033508be5c` |
| `dual-ledger-red.yml` | `c7c3e16026c6b5f01b6be1a7d2f1c504a532607a` |
| `p1-8-synthetic-evidence.yml` | `bbe9361cbbeed4f881edc4ce4fbe727d6937ad78` |
| `p5-3-11-g2-integration-green.yml` | `3b75fdbf34768a315e5ed025b2ba0015ce138b17` |
| `paper-writer-isolation-red.yml` | `6a793b6be484d660f0ed50a2c2ac609313796525` |
| `t0-binance-connectivity-probe.yml` | `42050b37282d81c21149d3a25d0eb3ba6d99771b` |
| `t0-evidence-contract-g2.yml` | `5e22648c38fd3c6e631f912010de1489bb78f9b5` |
| `t0-manual-validation.yml` | `395ae93274a9202f14ab63d528be5cd582c30149` |
| `t0-postgres16-grantor-repro.yml` | `c7bc589ca8240edb25a9c33cce5b9a76e6193271` |
| `t0-single-writer-gateway-red.yml` | `2d836c6c835f414efa62137abf7b97b7bcd6d5ec` |
| `t0-sqlite-readonly-sandbox.yml` | `a41e63cc7581606c6fb1bea264c1340d6448355d` |
| `t0-systemd-feeder-api-integration.yml` | `64476a3dd281eb69b92d29f3783570107c4ab48e` |
| `t2-freqtrade-2026-9-strategy-smoke.yml` | `89fe779e88c11c9a1598d2138286b7d4bfe7742b` |
| `t2-http-consumer-red.yml` | `7690780e076c317345879dcef081951e78cf2c6a` |

## 3. Execution and trust boundaries

- Most inspected workflows declare top-level `contents: read`. The P1.8 synthetic workflow has a job with additional `id-token: write` and `attestations: write` for its attestation path. This is a distinct permission surface and should not be described as a plain unit-test job.
- `t0-manual-validation.yml` has a `scaleway-ssh-preflight` option that consumes `SCW_SSH_*` environment secrets and opens a pinned-host-key SSH connection to the configured remote host. Its script is described as read-only, but selecting this gate is still an external remote operation. It was not dispatched or exercised.
- The same manual workflow has a TimescaleDB gate consuming `secrets.MARKET_DATA_TEST_DATABASE_URL`; effective target identity and secret configuration were not inspected.
- The SQLite and Feeder/API systemd workflows create transient services and temporary files on disposable GitHub-hosted runners and include cleanup steps. Their code labels the target as disposable runner only; these workflows do not establish VPS/systemd deployment evidence.
- PostgreSQL workflows start disposable TimescaleDB containers on the GitHub runner. Their presence does not mean the T0 production backend has switched to PostgreSQL.
- T2 strategy smoke pulls the pinned Freqtrade 2026.9 image and loads the strategy without exchange synchronization or database access; config guards set paper-only behavior and blank credentials.
- Android paired release is manually triggered, requires Android signing secrets and targets a branch different from the active branch. Android Chart/Scanner remains outside the five-layer system; this workflow is not a five-layer acceptance workflow.

## 4. Findings

### F-01 — Broad T0 workflow couples unrelated domains (CONFIRMED)

`t0-single-writer-gateway-red.yml` watches broad `market_data/**` and `pipeline/**` paths, alongside T1 and T2-related paths. Its jobs include T0 gateway/Feeder regressions, paper consumer regressions, T1 CSV importer tests, T1 Rust sidecar tests, disposable PostgreSQL provider bootstrap and TimescaleDB integration.

This confirms the previously recorded T0-SM7 coupling: research-domain or consumer changes can trigger a broad multi-domain workflow. Do not narrow paths or remove jobs in this audit. Before any proposed change, map every job's required coverage and the intended test denominator.

### F-02 — Manual validation includes an external SSH operation (CONFIRMED; NOT EXECUTED)

The Scaleway preflight gate uses protected SSH inputs and strict host-key checking to connect to a remote host. It is a manual, separately gated operation, not an ordinary offline test. Do not dispatch it as part of routine T0 validation without explicit authorization.

### F-03 — CI policy test contradicts the current workflow tree (STATIC CONFLICT; NOT EXECUTED)

`ci/test_ci_policy.py` blob `42b2c4164b28e1dac32457f36435d05207350714` contains `test_github_has_no_active_actions_workflows`, which asserts that `.github/workflows/` contains no `.yml/.yaml` files. The exact branch tree inspected above contains 14 such files. Therefore this assertion is incompatible with the current tree and is expected to fail if this test is executed unchanged.

The `codemagic.yaml` `canonical-market-data` workflow has a push trigger and runs `python -m unittest discover -s ci -p 'test_*.py'`, which includes `ci/test_ci_policy.py`. This creates a configuration/documentation discrepancy: the root README now describes Codemagic as legacy, but the tracked Codemagic config still declares push-triggered workflows. Whether the external Codemagic application is connected/enabled and actually executes these triggers is NOT VERIFIED.

No CI policy test or Codemagic job was run. Do not silently edit the test or disable the Codemagic workflow here; a separate owner-approved CI ownership/parity change is required.

### F-04 — Current feature branch has no branch protection reported by GitHub (METADATA OBSERVED; RULESET COVERAGE INCOMPLETE)

GitHub branch metadata for this exact branch returned `protected: false` and protection `enabled: false`, with required status-check enforcement off and no contexts. This means this branch does not report classic branch protection/required checks through the inspected endpoint.

Repository/organization rulesets, bypass actors, environment protection, approval policies and effective permissions were not inspected. Do not generalize this one branch response into a complete repository governance assessment.

### F-05 — Workflow presence is not execution evidence (BOUNDARY)

Workflow definitions, triggers and artifact-upload steps were inspected. No workflow run status, job result, artifact bytes, recent execution frequency, secret values, environment approval history, external Codemagic state or deployed runtime was inspected in this task. Workflow files alone cannot establish PASS, G2 exact-SHA acceptance, production readiness or L4-Minimum.

## 5. Scope classification

- **T0 ACTIVE validation:** `t0-binance-connectivity-probe.yml` (offline contract only), `t0-single-writer-gateway-red.yml` (mixed-domain aggregate), `t0-sqlite-readonly-sandbox.yml`, `t0-systemd-feeder-api-integration.yml`.
- **T0 separate assurance:** `t0-evidence-contract-g2.yml`, `p1-8-synthetic-evidence.yml`, and the G2 reusable workflow. Synthetic/attestation outputs must remain distinct from production evidence.
- **T0 PARKED / support / manual:** PostgreSQL reproduction, manual Kraken/Timescale gates, Binance connectivity support probe and Scaleway SSH preflight. The workflow file does not change the T0 Active Scope Index classification.
- **T1/T2/paper cross-domain:** jobs embedded in the broad T0 aggregate, dual-ledger/paper writer workflows, and T2 Freqtrade/HTTP workflows.
- **Outside five-layer scope:** Android paired-release workflow. Do not classify Android Chart/Scanner or Python bot/backtest as five-layer dependencies.

## 6. Status and next gate

- Exact branch workflow directory inventory: PASS (14/14 files returned and inspected).
- Selected workflow triggers, jobs, permissions and side-effect boundaries: PARTIAL PASS; selected exact files/sections inspected.
- F-01 broad path/job coupling: CONFIRMED.
- F-02 external SSH manual gate: CONFIRMED, NOT EXECUTED.
- F-03 CI policy assertion conflict: STATIC CONFLICT CONFIRMED, NOT EXECUTED.
- F-04 branch metadata: `protected=false` observed; ruleset/effective governance NOT VERIFIED.
- Workflow runs/artifacts, external Codemagic state, effective secrets/permissions, all reusable-workflow call sites and full repository governance: NOT VERIFIED.
- Tests: NOT RUN. GitHub Actions: NOT DISPATCHED. Independent review: NOT PERFORMED.
- No source, test, workflow, package, schema, runtime, VPS, database, provider, secret, key, permission or data changes. No PR or merge.
- Option C — No Destructive Authority — unchanged. No deletion, TTL, cleanup, archive, compaction, vacuum, backup expiry or replica removal.

Next safe step: prepare a separate documentation-only CI ownership and test-denominator decision record covering F-01 and F-03. Do not modify workflow triggers, CI tests, Codemagic config, branch protections, secrets or dispatch any workflow until that decision is approved.
