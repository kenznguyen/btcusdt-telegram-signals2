# G0.10 — Synthetic-only Lifecycle Dry-run Contract and Test Plan

Date: 2026-11-11  
Status: **DOCUMENTARY CONTRACT — NOT IMPLEMENTED / NOT EXECUTED / NOT ACTIVE**

## 1. Purpose and scope

G0.10 defines a test-only contract for a future synthetic-fixture dry-run evaluator. Its sole purpose is to demonstrate that lifecycle candidate assessment can report deterministic, fail-closed dispositions without reading or mutating production data.

This document is subordinate to:
- `docs/architecture/CENTRAL_DATA_LIFECYCLE_POLICY.md`;
- `docs/architecture/DATASET_CONSUMER_CONTRACT.md`;
- `docs/architecture/DATA_DELETION_SAFETY_CONTRACT.md`;
- `docs/evidence/p1-8/P1.8.80-retention-and-eligibility-policy.md`;
- `docs/evidence/p1-8/P1.8.143-owner-retention-policy-ratification.md`;
- `docs/evidence/G0_9_VPS_DATA_LIFECYCLE_STORAGE_GOVERNANCE_2026-11-11.md`.

G0.10 is documentation only. It does not add code, fixtures, tests, workflows, schemas, registries, adapters, schedulers, credentials, permissions or runtime behavior. No tests or workflows are run by this increment.

## 2. Authority boundary

The owner-ratified RET-01 B / RET-02 B decisions remain controlling:
- T0 canonical data is protected by default; no routine or scheduled deletion path.
- Only exact noncanonical objects in the four ratified groups may enter a future read-only eligibility assessment, subject to all applicable proof.
- Eligibility assessment is not deletion authorization.
- CORE_LEDGER, AI_LEDGER, T3 reconstruction/reconciliation/audit evidence, governance evidence and unknown/unclassified/orphaned/incompletely inventoried data remain protected from ordinary class-wide review.
- The 2026-11-11 revocation of Option C did not authorize any particular destructive operation.
- Every concrete destructive operation still requires separate explicit bounded approval. No destructive authority is granted by G0.10.

Paper-only remains mandatory; `AI_EXECUTION_ENABLED=false`. T0 remains an independent canonical asset.

## 3. Test isolation contract

A future implementation test may run only after a separate approval identifies the exact test-only source paths, output paths and CI workflow scope. The intended fixture namespace is:

`tests/fixtures/lifecycle_dry_run/`

The intended test output namespace is:

`build/test-artifacts/lifecycle-dry-run/`

These are proposed repository-relative namespaces only. They are not asserted to exist, are not currently allowlisted, and must be explicitly verified and approved before implementation or execution.

Mandatory isolation rules:

1. Test input is generated synthetic content committed specifically for lifecycle tests. It must contain no production rows, candle payloads, T0 database copies, T1 raw captures, account data, credentials, API tokens, personal data or real model artifacts.
2. Tests must not accept arbitrary filesystem paths, environment-provided production paths, mount points, database URLs, object-store identifiers or provider credentials.
3. The evaluator receives only an in-memory synthetic fixture model or an explicitly allowlisted test-fixture root. It must not discover files by scanning parent directories, home directories, mounted volumes or runtime data paths.
4. CI must run in an isolated temporary workspace with no production secrets, no external storage credentials and no network dependency.
5. Test output is limited to the explicitly approved test output namespace. It must not write to fixture inputs.
6. The evaluator has no storage mutation interface: no unlink/delete, rename/move, truncate, overwrite, archive, compress, chmod, vacuum, compaction, expiry, provider API or subprocess capability.
7. A test must fail if it detects an input/output path outside the allowlist or if the isolation assumptions cannot be established.
8. No test is permitted against an actual VPS, SQLite database, T0/T1/T2/T3/T4 runtime, exchange, backup, archive, mounted volume or provider.

The test harness must not provide a destructive executor even as a mock that can accidentally reach real storage. A pure disposition evaluator and immutable fixture data are sufficient.

## 4. Logical dry-run contract

The dry-run evaluator is a pure, deterministic assessment over supplied synthetic records. It reports a disposition; it does not perform lifecycle transitions.

### 4.1 Input record (logical fields)

| Field | Meaning | Fail-closed condition |
|---|---|---|
| fixture_id | Stable synthetic record identifier | Missing or duplicate |
| dataset_id / version_id | Synthetic immutable identity | Missing, mutable alias or ambiguous |
| object_id | Synthetic exact object identity | Missing or duplicate |
| data_class | Ratified functional class | Unknown, conflicting or unrecognized |
| steward_id | Synthetic accountable owner | Missing or conflicting |
| policy_id / policy_version | Governing policy reference | Missing, unknown or superseded without resolution |
| source_lineage | Synthetic source/version references | Missing or inconsistent where required |
| content_digest / byte_size | Synthetic integrity metadata | Missing or mismatch |
| dependency_records | Exact synthetic consumer references and states | Missing, stale, contradictory or incomplete |
| hold_records | Synthetic legal/security/incident/audit/recovery holds | Active, ambiguous or unverifiable |
| copy_records | Synthetic replica/backup/export/derived-copy references | Unknown or incomplete where relevant |
| process_state | Synthetic writer/job/lock state | Active or unknown |
| rebuildability_evidence | Exact source + transform + integrity proof | Absent or insufficient where rebuildability is claimed |
| evidence_revision | Stable fixture evidence revision | Missing or inconsistent |

These are logical contract fields, not an approved physical schema or production registry design. Synthetic IDs must be visibly synthetic and must not reuse production identifiers.

### 4.2 Output record (logical fields)

| Field | Meaning |
|---|---|
| evaluation_id | Deterministic synthetic evaluation identifier |
| fixture_id / object_id | Exact fixture/object evaluated |
| policy_version | Policy version applied |
| disposition | One of PROTECTED, RETAIN_UNTIL_OBLIGATIONS_CLOSE, REVIEWABLE_NONCANONICAL, COPY_SPECIFIC_REVIEW or BLOCKED_UNKNOWN |
| blockers | Stable machine-readable reason codes |
| evidence_refs | References to synthetic input records only |
| input_manifest_digest | Digest of the complete synthetic input manifest |
| evaluator_version | Version of the pure evaluator |
| evaluated_at | Test-run timestamp for diagnostics; not a trusted authorization clock |
| mutation_performed | Must always be false |
| execution_authorized | Must always be false |

The output must not use states such as DELETED, ARCHIVED, EXECUTING or AUTHORIZED. It must not emit an executable command, storage path, provider request, SQL statement or deletion manifest.

## 5. Disposition rules

- `PROTECTED`: exact class or policy invariant prohibits ordinary review (including T0 canonical, CORE_LEDGER, AI_LEDGER and protected T3/governance evidence).
- `RETAIN_UNTIL_OBLIGATIONS_CLOSE`: one or more known dependencies, replay/recovery/research/audit/model obligations remain open.
- `REVIEWABLE_NONCANONICAL`: exact noncanonical object is within a ratified review class and all required synthetic evidence is complete. This means review may be considered; it is not approval.
- `COPY_SPECIFIC_REVIEW`: exact individually identified copy may enter copy-specific review after lineage, recovery chain, holds and dependencies are complete.
- `BLOCKED_UNKNOWN`: any identity, classification, provenance, evidence, registry, copy, process or policy state is missing, stale, contradictory, untrusted or incomplete.

Precedence is protective: any protected-class rule or unresolved blocker overrides a less restrictive candidate result. No heuristic, default TTL, age, storage-pressure score, consumer ACK, read completion, job completion or missing heartbeat may make an object reviewable.

## 6. Synthetic acceptance test matrix

All cases below are test specifications only. They were not implemented or executed in G0.10.

| ID | Synthetic fixture condition | Required result |
|---|---|---|
| SYN-DRY-001 | Complete synthetic noncanonical cache record, rebuildability proven, no dependencies/holds/copies | REVIEWABLE_NONCANONICAL; mutation_performed=false; execution_authorized=false |
| SYN-DRY-002 | T0 canonical synthetic record | PROTECTED regardless of age, size or consumer ACK |
| SYN-DRY-003 | CORE_LEDGER or AI_LEDGER synthetic record | PROTECTED; ledgers remain distinct |
| SYN-DRY-004 | T3 event/reconciliation evidence still needed for paper reconstruction | PROTECTED or RETAIN_UNTIL_OBLIGATIONS_CLOSE; never reviewable |
| SYN-DRY-005 | Unknown or conflicting data class/steward | BLOCKED_UNKNOWN |
| SYN-DRY-006 | Missing content digest, size mismatch or manifest mismatch | BLOCKED_UNKNOWN with integrity reason |
| SYN-DRY-007 | Missing, stale, contradictory or unavailable dependency registry | BLOCKED_UNKNOWN; do not infer no consumers |
| SYN-DRY-008 | Active consumer dependency or unresolved release | RETAIN_UNTIL_OBLIGATIONS_CLOSE |
| SYN-DRY-009 | Active/ambiguous legal, security, incident, audit or recovery hold | PROTECTED or RETAIN_UNTIL_OBLIGATIONS_CLOSE |
| SYN-DRY-010 | Unknown replica, backup, export or derived-copy lineage | BLOCKED_UNKNOWN |
| SYN-DRY-011 | Active writer, open process, lock or training job | BLOCKED_UNKNOWN or RETAIN_UNTIL_OBLIGATIONS_CLOSE |
| SYN-DRY-012 | Rebuildability asserted but exact source/transform/integrity proof absent | BLOCKED_UNKNOWN |
| SYN-DRY-013 | T1 raw observation where dependent outputs are not demonstrably reproducible from retained authoritative inputs | RETAIN_UNTIL_OBLIGATIONS_CLOSE; T1 remains blocked |
| SYN-DRY-014 | T2 ephemeral inference output with unresolved material-decision/ledger use | RETAIN_UNTIL_OBLIGATIONS_CLOSE |
| SYN-DRY-015 | Individually identified noncanonical copy with complete copy-specific evidence | COPY_SPECIFIC_REVIEW only |
| SYN-DRY-016 | Policy version missing or conflicting | BLOCKED_UNKNOWN |
| SYN-DRY-017 | Repeat evaluation with byte-identical inputs and evaluator version | Identical disposition, blockers and input digest |
| SYN-DRY-018 | Input fixture payload hash before/after evaluation | Identical hashes and byte counts |
| SYN-DRY-019 | Attempt to supply a path outside test allowlist | Test fails closed before reading the path |
| SYN-DRY-020 | Attempt to direct output into fixture input or outside output allowlist | Test fails closed; fixture bytes unchanged |
| SYN-DRY-021 | Attempt to invoke mutation/executor capability | Capability absent; evaluation cannot invoke it |
| SYN-DRY-022 | Audit/report output sink unavailable | Evaluation reports failure; no fallback mutation or permissive result |
| SYN-DRY-023 | Storage-pressure indicator crosses any supplied synthetic threshold | Report/alert only; no disposition relaxation or mutation |
| SYN-DRY-024 | Consumer ACK, elapsed time or missing heartbeat supplied without other proof | No eligibility upgrade; protective state remains |
| SYN-DRY-025 | Same fixture evaluated in different record order | Deterministic canonicalized output |
| SYN-DRY-026 | Fixture contains a production-like identifier or forbidden secret marker | Fixture validation rejects it |

The test suite must assert both semantic outcomes and absence of mutation. A passing disposition assertion without input immutability and isolation assertions is insufficient.

## 7. Required test evidence if separately approved later

A future implementation/test increment must record:

- exact source commit SHA and branch;
- exact test command and environment;
- exact fixture inventory and fixture-manifest digest;
- proof that test workspace contains synthetic fixtures only;
- proof that production secrets and external storage credentials are absent;
- test results for all required cases, including skipped cases and reasons;
- before/after fixture hashes and byte counts;
- proof that no production paths, network services, databases or provider APIs were accessed;
- workflow run ID, job IDs/logs and artifact identity/digest, if CI is separately approved and run;
- final status PASS / BLOCKED / NOT VERIFIED with residual limitations.

No artifact may be described as evidence of production cleanup safety. It proves only behavior against the exact synthetic fixtures and evaluator version.

## 8. G0.10 status

- Contract and test-plan documentation: **PASS — documentary specification**.
- Alignment with central lifecycle/deletion safety/consumer contracts: **PASS — source-level mapping**.
- Fixture namespace existence and allowlist: **NOT VERIFIED / NOT APPROVED**.
- Test implementation: **NOT IMPLEMENTED**.
- Tests: **NOT RUN**.
- CI workflow: **NOT DISPATCHED**; no run/artifact.
- Production data isolation at runtime: **NOT VERIFIED** because no test was executed.
- Destructive executor: **NOT IMPLEMENTED / NOT AUTHORIZED**.
- Cleanup/archive/deletion/runtime/VPS operations: **NOT PERFORMED**.

## 9. Explicit non-actions and next gate

No source code, test, fixture, schema, API, registry, workflow, scheduler, service, permission, credential, database, storage, VPS, market data, model, ledger or runtime was changed. No live inventory, production-data read, test execution, workflow dispatch, archive, quarantine, cleanup, expiry, compaction, vacuum, deletion or provider operation occurred.

Before any future implementation or CI execution, a separate bounded approval must identify:
1. exact fixture files and their synthetic-only provenance;
2. exact read/write allowlist and isolated test workspace;
3. exact test implementation files and command;
4. exact CI workflow and permitted permissions;
5. evidence proving no production data, secret, network, database, VPS or provider access.

The next review should assess whether this contract can be implemented as a pure evaluator with no storage adapter dependency. Any test implementation, workflow dispatch or operational inventory remains a separate approval gate.

T0 remains independent. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.
