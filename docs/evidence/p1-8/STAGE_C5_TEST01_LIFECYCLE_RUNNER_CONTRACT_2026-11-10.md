# Stage C.5 — TEST-01 Lifecycle Runner Contract

Date: 2026-11-10  
Repository: kenznguyen/btcusdt-telegram-signals2  
Branch: feature/t0-centralized-data-feeder-p1-20261101  
Work type: documentation-only contract; no runner implementation or execution  
Baseline: Stage C.4 blob 62594cf9db3270fedeab29f30872754afa0a86d3

## 1. Purpose and authority boundary

Define the minimum deterministic runner contract for a future synthetic lifecycle negative-vector suite. This document specifies behavior and evidence, not a selected framework, executable, workflow, dependency, container image or implementation.

It does not authorize code changes, test/compile/dry-run/fault-injection, GitHub Actions dispatch, secrets access, permission changes, runtime/VPS/database/provider access, or production/staging interaction. TEST-08 remains a separate exact-scope authorization gate. Option C remains active; no deletion, archive, cleanup, expiry, compaction, vacuum, backup/replica removal, export mutation or irreversible transition is permitted.

## 2. Runner responsibilities

A conforming runner, when separately authorized and implemented, must:

1. Accept one immutable run manifest and reject ambiguous or unknown fields.
2. Resolve only explicitly selected vector IDs from the frozen 87-ID catalogue union.
3. Resolve each selected vector to exactly one versioned test-case definition, expected invariant and oracle assertion.
4. Validate source/spec/fixture/toolchain identity before invoking a test.
5. Invoke tests only through explicitly registered synthetic adapters; no implicit backend discovery or fallback.
6. Emit one structured result per vector plus a run-level summary.
7. Preserve complete execution and oracle evidence even on failure or abort.
8. Return non-zero for failed, blocked, invalid, incomplete or indeterminate runs; never convert missing evidence to PASS.
9. Avoid performing cleanup itself. Any future synthetic cleanup is a separate capability governed by TEST-07 and explicit authorization.
10. Make no network calls and consume no secrets by default.

## 3. Immutable run manifest contract

The future manifest must contain, at minimum:

| Field | Requirement |
|---|---|
| schema_version | Required, exact supported version |
| run_id | Unique, immutable identifier; no reuse |
| namespace_id | Unique synthetic-only namespace, bound to run_id |
| catalogue_digest | SHA-256 of canonical 87-vector catalogue |
| selected_vector_ids | Non-empty, unique, catalogue members only |
| test_case_map | Exact vector ID → test case ID and version |
| source_commit | Full immutable Git commit SHA |
| spec_digests | Exact hashes for P1.8.90, P1.8.94 and applicable contracts |
| fixture_digest | Hash of immutable synthetic fixture set |
| runner_identity | Exact runner build/toolchain identity |
| adapter_set | Explicit allowlisted synthetic adapter identifiers and versions |
| oracle_identity | Independent oracle version and identity |
| deterministic_seed | Required where randomness is used; no implicit entropy |
| schedule_id | Required for concurrency/race vectors |
| time_profile | Fixed synthetic clock profile; wall-clock use explicitly prohibited unless contractually required |
| artifact_destination | Pre-approved synthetic evidence destination; no arbitrary URL/path |
| network_policy | Must be DENY_ALL for initial harness |
| created_at | Provenance metadata only; not a trusted lifecycle decision clock |

Unknown fields, duplicate vector IDs, digest mismatch, missing required fields, unsupported schema versions, production-like paths/URIs or non-allowlisted adapters must fail before test discovery or execution.

## 4. Discovery and selection semantics

- Discovery is manifest-driven, not broad repository test auto-discovery.
- The selected vector set is explicit and frozen before execution.
- Every selected vector must resolve to one and only one test case and one expected oracle assertion.
- Duplicate, unknown, deprecated or unmapped vector IDs invalidate the run.
- A partial selection is allowed only when the manifest explicitly records the intended subset and its denominator. A subset result must never be represented as full 87-vector coverage.
- Test order is deterministic: canonical vector ID order unless a frozen schedule explicitly defines another order.
- Retries are disabled by default. A retry, if ever approved, is a new attempt with a distinct attempt ID and preserved prior evidence; it cannot overwrite a failed result.
- No test may silently skip due to missing adapter, fixture, capability or environment.

## 5. Per-vector result schema

Each vector result must record:

- run_id, namespace_id, vector_id and test_case_id/version;
- source commit and catalogue/spec digests;
- fixture, adapter, runner and oracle identities/digests;
- deterministic seed and schedule/fault-point trace, where applicable;
- expected invariant and machine-readable assertion outcome;
- executor result and independently observed oracle result;
- pre/post synthetic object digests and protected-root invariance evidence;
- audit-event digest and artifact references;
- status and reason.

Allowed statuses:

| Status | Meaning |
|---|---|
| PASS | All declared assertions and independent oracle checks succeeded |
| FAIL | An expected invariant was violated or an assertion failed |
| BLOCKED | Required prerequisite/capability was unavailable or invalid |
| NOT RUN | Vector was not invoked |
| INDETERMINATE | Evidence is contradictory, incomplete or cannot establish outcome |

Only PASS is a passing result. BLOCKED, NOT RUN and INDETERMINATE are never counted as PASS. A runner process exit code alone is not a vector result.

## 6. Run-level exit contract

| Exit | Meaning |
|---|---|
| 0 | Every selected vector is PASS; manifest and evidence validation succeed |
| 1 | One or more vectors FAIL |
| 2 | Invalid manifest, identity, mapping, configuration or unsupported contract |
| 3 | Isolation, adapter or required prerequisite BLOCKED |
| 4 | Oracle/evidence inconsistency or INDETERMINATE result |
| 5 | Runner internal error or interrupted execution |

A run with zero selected vectors, missing vector results, missing oracle evidence, incomplete artifacts or a mismatch between selected and reported IDs must not return exit 0.

## 7. Determinism and reproducibility

- Freeze runner build, dependencies/toolchain, source commit, catalogue/spec hashes, fixtures, adapter versions, oracle version and schedule.
- Use an injected deterministic clock and seeded randomness only; no ambient wall-clock or entropy dependency.
- Race tests must use named barriers and scheduler-controlled interleavings, not timing sleeps.
- Record a canonical event trace and stable serialization format.
- Repeated runs with identical frozen inputs must produce equivalent semantic outcomes and trace digests, except explicitly declared nondeterministic metadata fields.
- Any nondeterministic outcome is INDETERMINATE and blocks PASS promotion pending investigation.

## 8. Isolation and protected-resource constraints

The runner contract assumes TEST-03 proof exists before execution. Required boundaries:

- synthetic-only filesystem and storage namespaces;
- no mounts, credentials, routes or configuration resolving to T0/T1/T2/T3/T4, VPS, real ledgers, backups, replicas or external recipients;
- no GitHub secrets or production credentials;
- network DENY_ALL;
- allowlisted synthetic adapters only;
- no cleanup capability in the runner process;
- independent oracle outside executor's mutable trust boundary.

T0 canonical data and recovery copies, CORE_LEDGER, AI_LEDGER and required T3 reconstruction/audit evidence must remain inaccessible and unchanged. Failure to prove any boundary means BLOCKED before test execution.

## 9. Evidence completeness and provenance interface

The runner must emit a canonical run manifest, per-vector results, event traces, oracle attestations, protected-root invariance evidence, and a run summary. TEST-06 must later define cryptographic binding of source/spec/fixture/runner/oracle/run/result/artifact identities. This document does not select or authorize an attestation workflow.

Evidence must be append-preserving for the run; later attempts create new records rather than overwrite previous results. An evidence write failure makes the run BLOCKED or INDETERMINATE, never PASS.

## 10. Acceptance criteria for TEST-01 closure

TEST-01 can be marked CLOSED only after all of the following are evidenced in an explicitly approved synthetic implementation:

1. Frozen manifest schema and strict validation.
2. Deterministic vector selection/discovery and one-to-one mapping.
3. Stable per-vector result schema and exit semantics.
4. Unknown/duplicate/unmapped vector rejection.
5. Missing fixture/adapter/oracle/evidence fail-closed behavior.
6. Partial selection cannot claim full-suite coverage.
7. Retry cannot erase or overwrite failed attempts.
8. Repeated-run semantic equivalence under frozen inputs.
9. No production import/config/path/backend fallback.
10. Reviewable source/spec/run/artifact binding, coordinated with TEST-06.

This contract alone does not satisfy these criteria and does not close TEST-01.

## 11. Current disposition and next dependency

- TEST-01: CONTRACT DOCUMENTED / IMPLEMENTATION NOT ESTABLISHED.
- TEST-02: OPEN / NOT ESTABLISHED.
- TEST-03: OPEN / NOT ESTABLISHED.
- TEST-04: OPEN / NOT ESTABLISHED.
- TEST-05: OPEN / NOT ESTABLISHED.
- TEST-06: PARTIAL / NOT ESTABLISHED.
- TEST-07: OPEN / NOT ESTABLISHED.
- TEST-08: NOT GRANTED; separate exact-scope authorization required.
- LDA-07: NOT RUN; 87/87 vectors remain NOT RUN.
- LDA-06: PARTIAL / NOT VERIFIED.
- LDA-08: HOLD / NOT VERIFIED.

Next bounded documentary step: Stage C.6 — TEST-02 Synthetic Adapter Interface Contract. Do not implement or execute until prerequisite evidence is established and exact execution authorization is separately granted.

No tests, compile, dry-run, fault injection or Actions dispatch were performed. No secrets, runtime, VPS, database, provider, recipient, backup or replica were accessed. No source, schema, adapter, workflow, runner, permission, runtime or data changes were made. No destructive operation was performed.

**STAGE C.5 DOCUMENTARY CONTRACT COMPLETE — TEST-01 NOT CLOSED — NO IMPLEMENTATION OR EXECUTION AUTHORITY.**
