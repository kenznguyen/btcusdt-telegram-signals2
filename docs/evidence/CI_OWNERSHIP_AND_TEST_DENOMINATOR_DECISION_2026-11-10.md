# CI Ownership and Test Denominator — Decision Record

Date: 2026-11-10  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Audit baseline: `af49ac0fd8eaa7049bdc7d6e5858c5bee85fb03a`  
Related audit: `docs/evidence/GITHUB_ACTIONS_EXECUTION_MAP_READ_ONLY_AUDIT_2026-11-10.md`

## 1. Purpose

Resolve the CI ownership ambiguity and establish a safe test-denominator policy for the two confirmed findings:

- F-01: `t0-single-writer-gateway-red.yml` triggers a mixed-domain set of jobs from broad source paths.
- F-03: `ci/test_ci_policy.py` asserts there are no active GitHub Actions YAML files, while the inspected branch contains 14; the tracked Codemagic workflow still invokes this test on push.

This record is a decision proposal and scope boundary, not an implementation authorization. It does not dispatch workflows, alter CI configuration, run tests, or change repository permissions.

## 2. Governing decisions

### D-01 — Canonical CI owner

**Proposed target state: GitHub Actions is the sole canonical CI/workflow execution system for the five-layer project.**

- GitHub is the source, branch, history and evidence store.
- GitHub Actions is the runner for five-layer validation and workflow evidence.
- Workflow PASS is recognized only when the run is tied to the exact source SHA and its job results/artifacts are retained and checked.
- Codemagic is legacy configuration for independent/older workflows, not a required five-layer CI dependency.
- Android Chart/Scanner, Python bot/backtest, Telegram and legacy backtest UI remain outside the five-layer architecture. Their legacy CI configuration must not silently become five-layer acceptance.

**Important current-state distinction:** the repository still contains `codemagic.yaml` with push-triggered workflows. The external Codemagic app, webhook, branch filters, environment groups, secrets and actual build execution are NOT VERIFIED. Therefore Codemagic is classified as *legacy by project policy, but operationally unresolved until external state is confirmed*. Do not claim it is disabled.

### D-02 — Codemagic disposition

Recommended disposition is **PARK / NO NEW FIVE-LAYER DEPENDENCY / NO DELETION YET**.

1. Preserve `codemagic.yaml`, setup documentation and historical artifacts during this decision phase.
2. Do not add new five-layer tests or acceptance gates that require Codemagic.
3. Do not infer that a README label changes external webhook or app behavior.
4. Before disabling or removing anything, obtain a separately authorized, metadata-only inventory of Codemagic app/project connectivity, webhook state, branch filters, workflow history, environment-group names and artifact retention. Do not reveal secret values.
5. If external execution remains active, prepare a separate owner-approved deactivation/migration plan, with exact workflows and replacement evidence mapped first.

### D-03 — F-03 CI policy contradiction

The existing test `CiPolicyTest.test_github_has_no_active_actions_workflows` encodes an obsolete repository assumption. The current branch contains 14 workflow YAML files. The tracked Codemagic `canonical-market-data` push workflow discovers `ci/test_*.py`, so it includes this assertion.

**Recommended eventual correction:** replace the negative “no GitHub workflows” assumption with explicit, testable CI ownership invariants. Candidate invariants:

- Five-layer validation workflows are stored under `.github/workflows/`.
- Canonical T0/T1/T2/paper validation does not depend on Codemagic.
- Android/legacy workflows are classified outside five-layer acceptance.
- Manual/stateful/external operations do not run on ordinary push unless specifically approved.
- A workflow file existing is not equivalent to a passing run.
- Each required acceptance workflow has an exact-SHA evidence contract.

**No test edit is authorized by this record.** Before changing `ci/test_ci_policy.py`, determine whether it remains in the active test denominator after Codemagic ownership is resolved. If the file is retained, its assertions must reflect the approved GitHub Actions model rather than hiding or deleting checks to make CI green.

### D-04 — Test denominator for F-01

The broad T0 workflow currently includes multiple job domains. The job inventory below is a preservation baseline, not a recommendation to drop tests.

| Job | Domain | Minimum coverage to preserve |
|---|---|---|
| `shadow-contracts` | T0 core | Static gateway contract; write-gateway/fenced-store/store/sync/storage/feeder lifecycle; health/readiness; process restart/fencing; full `market_data` regression suite |
| `paper-consumer-regressions` | T2/paper consumer | `pipeline.test_decision`, `pipeline.test_api`, `freqai_bridge.test_exporter`, T0–T2 parity |
| `t1-importer-offline-tests` | T1 importer | Offline CSV fixture importer and connection-event tests |
| `t1-collector-sidecar-rust` | T1 sidecar | Rust sidecar writer tests; must remain clearly separate from claims of collector integration or trusted custody |
| PostgreSQL/TimescaleDB job(s) | PARKED optional backend | Provider bootstrap/grantor and SQLite parity coverage; do not count as active SQLite production acceptance |
| Remaining jobs in the workflow | Cross-domain integration | Preserve their named contracts and exact test commands until separately mapped |

The T0 core acceptance denominator must remain explicit and independently identifiable from T1, T2/paper, PostgreSQL and research-domain tests. A combined workflow may orchestrate several domains, but a green aggregate must not blur which domain's jobs ran or failed.

### D-05 — Safe future workflow organization

Recommended target organization, subject to separate implementation approval:

- T0 core: dedicated workflow for canonical SQLite/Feeder/Candle API contracts and regression tests.
- T1 importer and sidecar: separately scoped offline fixture workflows.
- T2/paper consumers: separately scoped consumer and ledger workflows.
- PostgreSQL/TimescaleDB: PARKED optional-backend integration workflow, not an unconditional T0 acceptance dependency.
- Evidence G0–G3 and P1.8 synthetic/attestation: separate assurance workflows and status namespace.
- Manual VPS/SSH/provider validation: manual gated workflows only; never imply they ran from ordinary source-only CI.
- Android/legacy systems: outside five-layer acceptance.

Do not split, rename, narrow or remove any current job until a complete mapping exists for all job commands, fixtures, artifacts, path filters, required checks, branch/ruleset policies and consumers.

## 3. Required evidence contract

For every workflow considered required for acceptance, record:

1. Workflow filename and immutable workflow blob SHA.
2. Trigger type and matched branch/path filters.
3. Exact source commit SHA checked out by the run.
4. Every job's conclusion, including skipped/cancelled jobs.
5. Test command and test count/result where available.
6. Artifact names, artifact IDs, retention/expiry and digest where available.
7. Whether the run is offline fixture-only, disposable-service integration, or an external/runtime operation.
8. Any secrets/permissions used, described by name and scope only; never record secret values.
9. Explicit status: PASS / PARTIAL / BLOCKED / NOT VERIFIED.

A workflow-level SUCCESS is not sufficient if required jobs were skipped, evidence artifacts are missing, or the run tested a different source SHA.

## 4. Open governance gates

| Gate | Current state | Closure evidence required |
|---|---|---|
| GitHub Actions canonical owner | Policy direction established in root README; operational coverage incomplete | Confirm every required five-layer gate has a GitHub Actions owner |
| Codemagic external state | NOT VERIFIED | Authorized metadata-only account/app/webhook/workflow inventory |
| F-03 test policy correction | OPEN / NOT IMPLEMENTED | Owner-approved test semantics and active runner ownership |
| F-01 job/path split design | OPEN | Complete job-command, path, artifact and test-denominator crosswalk |
| Required status checks / rulesets | NOT VERIFIED | Read-only repository/org ruleset and effective branch policy inventory |
| Workflow run and artifact evidence | NOT VERIFIED in this audit | Exact-SHA runs with complete job/artifact readback |
| Independent review | PENDING | Reviewer independent of authoring |

## 5. Explicit prohibitions

This record does not authorize:

- Editing `ci/test_ci_policy.py`, `codemagic.yaml` or any `.github/workflows/*.yml`.
- Narrowing path filters, removing jobs, changing test discovery or reducing test counts.
- Disabling/deleting Codemagic apps, webhooks, credentials or artifacts.
- Dispatching or rerunning GitHub Actions/Codemagic workflows.
- Reading secret values, rotating credentials, changing permissions, rulesets or branch protection.
- SSH/VPS, provider, exchange, database, runtime, deployment or live-order operations.
- Any archive, cleanup, compaction, vacuum, backup expiry or data deletion.

Option C — No Destructive Authority — remains in force. T0 canonical data, recovery copies and CORE_LEDGER/AI_LEDGER separation remain protected. `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.

## 6. Status

- Decision proposal and denominator baseline: DOCUMENTATION PASS.
- Owner policy approval: PENDING.
- Implementation: NOT AUTHORIZED / NOT STARTED.
- Tests: NOT RUN.
- GitHub Actions: NOT DISPATCHED.
- Workflow runs/artifacts: NOT VERIFIED.
- External Codemagic state: NOT VERIFIED.
- Rulesets/effective permissions: NOT VERIFIED.
- Independent review: NOT PERFORMED.

**Next gate:** owner decision on D-01 through D-05, especially whether Codemagic is to be treated as disabled/legacy after an external metadata-only check. Only after that decision should a separate implementation plan be prepared for F-03 and F-01. No CI changes are authorized by “documentation PASS.”
