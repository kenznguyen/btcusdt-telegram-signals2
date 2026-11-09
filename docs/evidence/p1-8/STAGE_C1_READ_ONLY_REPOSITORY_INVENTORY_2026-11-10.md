# Stage C.1 — Read-Only Repository Inventory and Enforcement Evidence Baseline

Date: 2026-11-10  
Repository: kenznguyen/btcusdt-telegram-signals2  
Branch: feature/t0-centralized-data-feeder-p1-20261101  
Work type: read-only GitHub repository/configuration inspection and evidence recording  
Frozen source commit: d82475036f4bb731ea8ae65a4338d814e2e1399b

## 1. Owner authorization and scope

The owner explicitly approved automatic Stage C. This increment applies that approval to a bounded, read-only inspection of the existing GitHub repository tree, lifecycle specifications, workflow YAML and repository metadata, followed by evidence recording on the existing branch.

This increment does not read secret values, access external Codemagic, access VPS/T0/T1/T2/T3/T4 runtime or databases, contact providers, inspect exchange data, change repository/workflow/runner/branch permissions, dispatch or rerun workflows, create credentials, or mutate data. No destructive operation is permitted. Option C remains controlling.

## 2. Frozen sources

| Source | Exact identity | Use |
|---|---|---|
| Source baseline | commit `d82475036f4bb731ea8ae65a4338d814e2e1399b` | Tree and repository snapshot |
| P1.8.141 | blob `c20616d79f6dcedde08128f589a5c0e04d6257f1` | Prior owner pause and lifecycle gaps |
| P1.8.152 | blob `e1a4d95af216e94a58fa5528850fcd0c1ff465f8` | LDA-06/07/08 residual definitions |
| P1.8.90 | blob `8014ef15f347d255ee3d02f6f28847a02db27aff` | Negative-case execution constraints |
| P1.8.94 | blob `4588379d8e101ee496bcf8927186c6c989e6c6a6` | 87-vector traceability catalogue |
| L4-Minimum matrix | blob `2ba85af550fb7e369ea39ade6d73878d78dbf6bc` | Protected classes and Option C |
| Synthetic workflow | blob `bbe9361cbbeed4f881edc4ce4fbe727d6937ad78` | Static workflow/permission inspection |
| CI ownership decision | blob `68c14033f32bdd8bbbd675ed58ea8157f95dcb3d` | Canonical CI and workflow evidence constraints |
| CI policy test | blob `f5ef5213c8356cacc441b59ec8e1a06ccd4a61da` | Existing CI policy assertion inspection |

The Git tree query for the frozen commit returned 745 entries and was not truncated. This is a repository tree inventory, not an inventory of deployed/runtime/provider-side objects.

## 3. RET-09 / LDA-06 — consumer and copy inventory

### Repository-visible evidence

- Repository tree includes T0 market-data code/tests, T1 collector/importer/sidecar code, T2 FreqAI/pipeline consumers, T3 paper-execution/ledger code, T4 dashboard/control surfaces, synthetic-evidence code and 14 GitHub Actions workflow YAML files.
- Repository documentation and source provide candidate producer/consumer relationships and workflow references that can be followed in a subsequent bounded static dependency pass.
- The repository tree is finite and enumerable at this source commit.

### Not established

This read-only GitHub tree cannot establish deployed process state, live consumer registrations, actual data dependencies, filesystem locations, SQLite/PostgreSQL contents, WAL/journal/snapshot copies, VPS backups, replicas, exports/downloads, caches, recipients, provider-side copies, external CI/Codemagic state or restore paths. No runtime/provider/recipient inventory was performed.

**Disposition: RET-09 / LDA-06 NOT VERIFIED.** Repository-visible candidate inventory only; no completeness, no-dependency or all-copies-known claim. Unknown/unclassified/orphaned objects remain protected.

## 4. LDA-08 — GitHub workflow and permission evidence

### Repository and workflow metadata

- Repository metadata reports the connected GitHub principal has repository-level `admin=true`, `maintain=true`, `push=true`. This describes the connected principal's repository permission only; it does not establish the effective permissions of workflow jobs, runners, OIDC trust, environments or external providers.
- Frozen tree contains 14 workflow YAML files.
- Workflow-file SHA-1 blob identities and static permission/secret-reference scan:

| Workflow | Blob SHA | Static observation |
|---|---|---|
| android-release-pair.yml | `b6f6b3deccc01f27fb3c00b0bb5657033508be5c` | contents:read; references Android signing secret names; manual dispatch |
| dual-ledger-red.yml | `c7c3e16026c6b5f01b6be1a7d2f1c504a532607a` | contents:read; paper_execution path trigger; manual dispatch |
| p1-8-synthetic-evidence.yml | `bbe9361cbbeed4f881edc4ce4fbe727d6937ad78` | job has contents:read, id-token:write, attestations:write, actions:read; manual dispatch |
| p5-3-11-g2-integration-green.yml | `3b75fdbf34768a315e5ed025b2ba0015ce138b17` | contents:read; workflow_call and manual dispatch |
| paper-writer-isolation-red.yml | `6a793b6be484d660f0ed50a2c2ac609313796525` | contents:read; branch/path-triggered and manual dispatch |
| t0-binance-connectivity-probe.yml | `42050b37282d81c21149d3a25d0eb3ba6d99771b` | contents:read; manual dispatch |
| t0-evidence-contract-g2.yml | `5e22648c38fd3c6e631f912010de1489bb78f9b5` | contents:read; no workflow_dispatch trigger observed |
| t0-manual-validation.yml | `395ae93274a9202f14ab63d528be5cd582c30149` | contents:read; references database and Scaleway SSH secret names; manual dispatch |
| t0-postgres16-grantor-repro.yml | `c7bc589ca8240edb25a9c33cce5b9a76e6193271` | contents:read; push path trigger and manual dispatch |
| t0-single-writer-gateway-red.yml | `2d836c6c835f414efa62137abf7b97b7bcd6d5ec` | contents:read; manual dispatch |
| t0-sqlite-readonly-sandbox.yml | `a41e63cc7581606c6fb1bea264c1340d6448355d` | contents:read; manual dispatch |
| t0-systemd-feeder-api-integration.yml | `64476a3dd281eb69b92d29f3783570107c4ab48e` | contents:read; manual dispatch |
| t2-freqtrade-2026-9-strategy-smoke.yml | `89fe779e88c11c9a1598d2138286b7d4bfe7742b` | contents:read; T2/T0 path triggers and manual dispatch |
| t2-http-consumer-red.yml | `7690780e076c317345879dcef081951e78cf2c6a` | contents:read; no workflow_dispatch trigger observed |

No secret values were requested or read. The static scan found secret references only by name in the Android release workflow and T0 manual-validation workflow.

### Important restrictions and unresolved controls

- The P1.8 synthetic-evidence workflow requests `id-token:write` and `attestations:write`; it also obtains the Sigstore trusted root and generates evidence. It is not a purpose-built LDA-07 87-vector negative-case harness. Dispatch is not justified by this static review.
- The T0 manual-validation workflow references database and SSH secret names. It was not dispatched; no secret values were accessed.
- The Android release workflow references signing secret names. It was not dispatched; no secret values were accessed.
- Repository rulesets API returned an empty list. Branch-protection read returned HTTP 403 (Resource not accessible by integration); therefore effective branch protection is NOT VERIFIED.
- No environment protection rules, runner group restrictions, OIDC trust policy, org-level policy, provider IAM, Codemagic app/webhook state or effective secret access policy was established.

**Disposition: LDA-08 HOLD / NOT VERIFIED.** This is a static repository configuration inventory only. No permission, secret, workflow or runner setting was changed.

## 5. LDA-07 — negative-vector execution readiness

- P1.8.94 records 87 unique vector IDs and traceability from the original 45 cases.
- P1.8.90 requires isolated synthetic identities, disposable test-only storage, deterministic event/concurrency scheduling, exact object scope, independent oracle, audit evidence and artifact provenance. It explicitly excludes T0–T4 canonical/runtime systems, VPS, production credentials, real ledgers, backups and external recipients.
- P1.8.90 lists TEST-01 through TEST-08 as open: framework/runner, synthetic storage adapters, isolation proof, independent oracle, deterministic concurrency harness, artifact signing/provenance, cleanup containment and separately authorized test scope.
- The existing P1.8 synthetic-evidence workflow runs `synthetic_evidence/test_*.py` and generates signed/attested synthetic evidence; it does not establish that all 87 lifecycle vectors are implemented or covered. Its OIDC/attestation write permissions make it inappropriate to assume a dispatch is a harmless read-only test.
- No negative-vector test code, deterministic runner/oracle qualification or 87-vector run was established in this increment.

**Disposition: LDA-07 NOT RUN (0/87 execution evidence in this increment).** No tests or Actions were dispatched.

## 6. Stage C.1 result

| Workstream | Result |
|---|---|
| RET-09 / LDA-06 | Repository tree inventory recorded; runtime/copy completeness NOT VERIFIED |
| LDA-08 | 14 workflow files and repository metadata statically inventoried; effective permissions NOT VERIFIED; HOLD |
| LDA-07 | 87-vector specification confirmed; safe execution prerequisites not qualified; NOT RUN |
| Option C | PRESERVED |
| Protected T0/T3/ledger/evidence classes | UNCHANGED |
| Independent human review | Owner-waived; no independent assurance claim |
| Technical verifier separation | Still mandatory where applicable |

Stage C.1 is a partial evidence baseline, not Stage C closure. No requirement is promoted to PASS based on static configuration or documentation.

## 7. Execution record and next bounded work

- GitHub read-only tree/file/repository metadata queries: performed.
- GitHub Actions: NOT DISPATCHED.
- Tests: NOT RUN.
- Secret values: NOT READ.
- Runtime/VPS/database/provider/Codemagic/recipient/backup/replica probes: NOT PERFORMED.
- Workflow, branch protection, ruleset, runner, OIDC, secret, credential or permission changes: NONE.
- Source/schema/API/adapter/runtime/data changes: NONE.
- Destructive operations: NONE.

Next bounded work within Stage C: (1) static source-level consumer/dependency crosswalk against the frozen tree, keeping runtime/copy gaps explicit; (2) inspect workflow job steps and permission/secret boundaries without reading values; (3) assess whether any existing test code maps to each of the 87 vector IDs and record uncovered vectors. Do not dispatch a workflow or run tests until the specific runner, isolation, independent oracle, fixture, artifact and cleanup prerequisites are evidenced. Do not enter external/provider/runtime inventory or mutate permissions under this read-only baseline.

**Status: STAGE C IN PROGRESS — LDA-06 PARTIAL / NOT VERIFIED; LDA-07 NOT RUN; LDA-08 HOLD / NOT VERIFIED.**
