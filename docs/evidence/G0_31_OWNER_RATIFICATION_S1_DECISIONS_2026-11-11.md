# G0.31 — Owner Ratification of S1 Decisions D05, D10, D11 and D14

Date: 2026-11-11 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Baseline HEAD: `1eacb16bf78aa96818a5bd4ec34e4ef4d4bb8d14`
Baseline handoff blob: `c2ce28871cef5ded62f8c4c5fd54be0aab9cd7bf`
Decision basis: G0.30 owner decision package
Type: owner decision record; documentation-only
Disposition: **D05, D10, D11, D14 OWNER-RATIFIED FOR S1 CONTRACT/SCOPE; S1 IMPLEMENTATION AUTHORIZATION NOT GRANTED**

## 1. Owner approval

On 2026-11-11, the owner explicitly approved all four G0.30 recommendations (D05, D10, D11 and D14) without amendment. This record captures the exact approved decisions.

The approval ratifies the S1 contract and proposed implementation boundary. It does **not** authorize starting implementation, creating fixture/test files, running tests, changing CI, dispatching workflows, merging, deploying or progressing to S2. A separate explicit implementation authorization remains required.

## 2. D05 — Synthetic Contract Fixture v1 ratified

The owner ratifies the **Synthetic Contract Fixture v1** as a synthetic parser-test input only, with this exact top-level structure:

| Field | Type | Required | Ratified rule |
|---|---|---:|---|
| `schema_version` | string | yes | Exact literal `synthetic-contract-fixture/v1` |
| `fixture_id` | string | yes | Reserved ASCII prefix `syn-fixture-`; unique within suite |
| `case_id` | string | yes | Registered synthetic case ID, initially `SYN-01`…`SYN-38` |
| `fixture_type` | string | yes | Closed D10 allowlist only |
| `subject` | object | yes | Exactly `object_id`, `version_id`, `namespace` |
| `purpose` | string | yes | Exact literal `PARSER_CONTRACT_TEST_ONLY` |
| `claims` | object | yes | Untrusted synthetic fields under case-specific closed schema |
| `expected` | object | yes | Test-oracle metadata kept outside parser-under-test input |
| `notes` | string | no | Synthetic-only, non-authoritative |

Ratified parser/contract rules:
- Initial encoding is UTF-8 JSON only; this is not a canonical signed-byte or cryptographic encoding profile.
- Reject invalid UTF-8, malformed JSON, duplicate object keys, non-finite numbers, invalid Unicode scalar sequences and trailing non-whitespace content.
- Reject unknown top-level fields and unknown fields in closed nested objects.
- Enforce exact types; no implicit coercion between strings, numbers, booleans, null, arrays or objects.
- Reject unsupported schema versions and unsupported critical fields.
- Keep `expected` test-oracle metadata separate from parser input; it cannot be interpreted as a claim or affect parser output.
- Synthetic identifiers use bounded ASCII patterns and reserved `syn-` namespaces. No real identifiers, personal data, secrets or production evidence.
- Any timestamps are inert syntax-only values. S1 does not evaluate freshness, expiry, revocation, clock trust or ordering.
- `claims` remains untrusted input; parser success cannot materialize authenticated or verified facts.
- No cryptographic meaning is assigned to digest, signature, issuer, key or authentication-shaped fields. Such fields are rejected unless explicitly included as inert fields in a case-specific negative fixture.

Candidate reason-code families in G0.30 are approved as parser/contract-only codes. They must not be mapped to lifecycle dispositions, verified facts or action authority.

## 3. D10 — Synthetic-only fixture vocabulary ratified

The owner ratifies this exact closed `fixture_type` allowlist:

1. `SYNTHETIC_OBJECT`
2. `SYNTHETIC_EVIDENCE`
3. `SYNTHETIC_ISSUER_CLAIM`
4. `SYNTHETIC_POLICY_CLAIM`
5. `SYNTHETIC_INVENTORY_CLAIM`
6. `SYNTHETIC_SENSITIVITY_CLAIM`
7. `SYNTHETIC_HOLD_CLAIM`
8. `SYNTHETIC_DEPENDENCY_CLAIM`
9. `SYNTHETIC_COPY_LINEAGE_CLAIM`
10. `SYNTHETIC_FRESHNESS_CLAIM`
11. `SYNTHETIC_BINDING_CLAIM`

These values describe synthetic test subject matter only. They are not production `data_class` values and do not assert truth, issuer authority, inventory completeness, sensitivity, freshness, custody or lifecycle eligibility. Adding or renaming a value requires an explicit schema-version/owner decision. All fixture identifiers and payloads must be fabricated and use the reserved synthetic namespace.

## 4. D11 — Measurement-first resource policy ratified

The owner ratifies the **measurement-first method**, not numeric resource ceilings.

Before implementation:
1. Prepare a wholly synthetic fixture corpus mapped to selected G0.23 test IDs.
2. Measure raw input bytes, maximum nesting depth, object member counts, array lengths, UTF-8 string sizes, scalar-node counts and diagnostic output requirements.
3. Record the exact corpus revision, measurement method and observed maxima.
4. Propose conservative ceilings above observed maxima with an explicit safety margin.
5. Obtain owner approval of the resulting numeric ceilings before they are enforced in the implementation.

The G0.30 candidate values (64 KiB input, depth 8, 32 members/object, 64 items/array, 1 KiB/string, 512 scalar nodes and 16 reason codes) are **NOT RATIFIED** and must not be treated as approved limits. No arbitrary numeric limit may be silently substituted.

Non-numeric safeguards already ratified:
- No unbounded recursive traversal, error aggregation, input echo, logging or fixture expansion.
- Do not allocate large secondary representations before enforcing bounds where the parser permits.
- Diagnostics use fixed reason codes and never echo raw input.
- This policy applies only to the synthetic S1 parser, not production payloads or T0/T1/T2 data paths.

## 5. D14 — S1 proposed implementation boundary and test gate ratified

The owner ratifies the following proposed boundary for a **future separately authorized S1 implementation**.

Permitted paths, if implementation is separately authorized:
- `pipeline/synthetic_contract.py`
- `pipeline/test_synthetic_contract.py`
- `docs/evidence/` for bounded evidence records
- `docs/PROJECT_SESSION_HANDOFF.md`

Fixture definitions may be embedded in the focused test module. Standalone fixture corpus files are not included in this boundary unless separately approved.

Explicitly excluded:
- `pipeline/lifecycle_disposition.py` and its existing tests.
- T0/T1/T2, market-data storage/API/clients, model/training/inference, CORE_LEDGER, AI_LEDGER, trading/execution, credentials, trust configuration and runtime deployment.
- All workflow files, CI permission changes, workflow dispatch, merge and deployment.
- S2 cryptographic verifier, keys, signatures, trust roots, real source adapters and production evidence.

Ratified focused local commands for the future authorized implementation:
- `python -m unittest pipeline.test_synthetic_contract -v`
- `python -m py_compile pipeline/synthetic_contract.py pipeline/test_synthetic_contract.py`

Acceptance evidence must include stable test-ID mapping, positive and negative contract cases, boundary and over-boundary tests after numeric limits are separately approved, deterministic results, oracle/input separation, no trusted-facts/evaluator/authorization output, no external dependencies, passing focused tests and compile checks, exact source/test blobs and commit SHA, and focused review confirming no I/O or authority side effects.

This D14 ratification defines the allowed boundary and test gate; it does not grant permission to begin the implementation or execute the commands. A separate explicit owner approval must authorize S1 implementation.

## 6. Decisions remaining open

- D01–D04 remain OPEN / NOT RATIFIED: cryptographic integrity/authenticity profile, canonical signed representation, trust roots/delegation and key lifecycle.
- D06–D08 remain OPEN / NOT RATIFIED: real evidence authorities, inventory closure, freshness/revocation.
- D09 remains OPEN / NOT RATIFIED: authenticated owner authorization.
- D12–D13 remain OPEN / NOT RATIFIED: audit custody and verified-facts binding/process boundary.
- D14 is ratified only for the S1 scope/boundary stated here; it does not approve later stages.
- Numeric D11 ceilings remain OPEN pending corpus measurement and separate owner approval.

## 7. Explicit non-actions and prohibitions

No source code, parser, tests, fixtures, schema implementation, API, registry, adapter, runner, workflow, permission, credential, key, trust root, database, storage, market-data, model, ledger, VPS or runtime change is made by G0.31. No tests or workflow dispatch are performed. No provider/network/database/VPS access or inventory. No archive, quarantine, cleanup, expiry, compaction, VACUUM or deletion.

S1 parser success must never be represented as issuer authenticity, verified facts, lifecycle eligibility, owner authorization or execution permission. No lifecycle evaluator or executor may consume the S1 result as trusted authorization.

T0 canonical data and lease/fencing remain independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.

## 8. Final verdict and next gate

**G0.31: OWNER-RATIFICATION PASS — D05, D10, D11 measurement-first policy and D14 S1 boundary ratified as recorded. Numeric D11 ceilings remain unapproved. S1 implementation and test execution remain NOT AUTHORIZED.**

Next gate: prepare the measured synthetic corpus profile and numeric-limit proposal as documentation/evidence only, or request a separate explicit owner authorization for the exact bounded corpus-preparation/implementation step. Do not infer implementation permission from this ratification.


## 9. D14 narrow amendment — G0.41 one-shot measurement workflow

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Owner decision: explicit approval of the exact G0.41 package in `docs/evidence/G0_41_S1_SINGLE_MEASUREMENT_OWNER_DECISION_PACKAGE_2026-11-11.md`  
Package commit: `ed37acab60df5f35d303f4e352cf474bcae339be`

The owner has separately approved one narrowly bounded G0.41 measurement operation. D14 is amended only as follows:

**One additional permitted path:** `.github/workflows/g041-s1-single-measurement.yml`.

That workflow may execute exactly one invocation of the already frozen `tools.s1_measurement_runner.prepare_preflight(...)` against the exact event checkout, and may persist exactly one bounded JSON measurement report as one seven-day GitHub Actions artifact. It must assert the three frozen Python source Git blobs and record those plus the workflow's own Git blob, exact checkout SHA, run/job identity and artifact metadata.

The workflow is limited to the one push event that adds this exact workflow file on `feature/t0-centralized-data-feeder-p1-20261101`. It must not trigger on later workflow modifications, manual dispatch, schedule, pull request, tag or another branch. It must guard `github.run_attempt == 1`; any rerun attempt must skip the job before measurement. The job uses read-only `contents: read`, exact SHA checkout, no secrets, no package installation, no external services, no application network, no provider/database/VPS/exchange access, no retry, and a maximum five-minute timeout. It persists only the JSON report, never parser-input bytes, oracle metadata, corpus files, fixture files, caches or intermediate source copies.

The approved measurement consists of the runner's one call, including its two internal deterministic construction/measurement passes. The workflow may read only the three frozen source files and Git/GitHub-provided checkout/run metadata. It must not read secrets, arbitrary environment variables, user files, clock state or external resources. The report may contain only the fields and bounded measurement data specified in the G0.41 package. The source and report checks must fail closed.

This amendment does **not** authorize:
- a second invocation, retry, rerun or replacement attempt;
- any modification to the frozen harness, runner, tests or dependencies;
- standalone tests that call the measurement runner multiple times;
- any additional workflow, CI expansion, write permission, secret, network, package installation or service;
- raw corpus/oracle persistence or any additional artifact;
- diagnostic-output dimension invention or numeric D11 ceiling proposal, ratification or enforcement;
- parser/verifier production implementation, cryptography, trust/key changes, or any S2 work;
- T0/T1/T2, canonical market data, model/training, ledgers, Shared Risk Engine, Kill Switch, PostgreSQL, VPS/runtime, providers, databases, external network or destructive lifecycle operations.

If an exact source assertion or pre-invocation environment guard fails, no measurement has begun; stop and return for a new owner decision. If any failure occurs after the measurement invocation begins, the one-shot authorization is consumed and the result is G0.41 FAILED/INCOMPLETE. No repair-and-rerun is allowed.

**D14 amendment verdict:** OWNER-APPROVED FOR THIS EXACT G0.41 ONE-SHOT WORKFLOW ONLY. All other D14 exclusions remain in force. Numeric D11 ceilings remain OPEN / NOT RATIFIED. This amendment grants no production parser/verifier or runtime authority.

