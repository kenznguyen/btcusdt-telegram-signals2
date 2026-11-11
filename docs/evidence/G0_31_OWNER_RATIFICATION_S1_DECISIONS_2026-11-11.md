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



## 10. D14 narrow amendment — G0.42 admission correction and one fresh attempt

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Owner decision: explicit approval of `docs/evidence/G0_42_G041_WORKFLOW_ADMISSION_CORRECTION_OWNER_PACKAGE_2026-11-11.md`  
Package commit: `91478d3382bdde22bcc9f251d72aff20f8d96a83`  
Exact implementation parent / approved `github.event.before`: `8f9f854cad4ec460ad10e850613af4d880d0c357`

The owner approves one correction to the existing `.github/workflows/g041-s1-single-measurement.yml` and one fresh G0.41 one-shot measurement attempt. This amendment supersedes the earlier "adds exact workflow file" admission condition only for this exact correction push and fresh attempt.

The single implementation push must have exact parent SHA `8f9f854cad4ec460ad10e850613af4d880d0c357`. The job may enter only when all are true: event is `push`; ref is exactly `refs/heads/feature/t0-centralized-data-feeder-p1-20261101`; `github.event.before` equals `8f9f854cad4ec460ad10e850613af4d880d0c357`; `github.event.head_commit.id == github.sha`; and `github.run_attempt == 1`. The existing branch/path trigger remains limited to this exact workflow path. The `contains(github.event.head_commit.added, ...)` condition is prohibited. A pre-measurement step must independently assert exact event-before SHA, event-head SHA, checkout SHA, branch, first run attempt, Python 3.14.4 and all three frozen Python Git blobs.

If all pre-invocation guards pass, the workflow may make exactly one call to the frozen `tools.s1_measurement_runner.prepare_preflight(...)` and persist exactly one bounded JSON report artifact with seven-day retention. Existing report assertions, no-payload-persistence/no-external-access requirements, read-only permissions, pinned actions, no package installation, no network/provider/database/VPS/exchange access and five-minute timeout remain unchanged.

Frozen source blobs remain exact: harness `e8db71c11e0503ea6d9a2480d75470185c4d5100`; runner `23a35aab7f7aeacd8a3f63d630a875fe76b1ff6a`; tests `d06a5b533af14378ed284051e5b057cf57377876`. No Python source, test, dependency, other workflow or application file may change.

Any pre-invocation guard failure means NOT RUN and requires a new owner decision. Any failure after invocation begins consumes this authorization and is FAILED/INCOMPLETE. No rerun, retry, manual dispatch, repair-and-rerun, second invocation or replacement attempt. Run attempts greater than one must skip before any step.

This amendment authorizes only the existing workflow correction, this D14 record update and the single bounded measurement attempt. All prior exclusions remain, including no D11 numeric ceiling proposal/ratification/enforcement; no parser/verifier production implementation, cryptography, trust/key work or S2; no T0/T1/T2, market/model data, CORE_LEDGER, AI_LEDGER, Shared Risk Engine, Kill Switch, PostgreSQL, VPS/runtime, provider/database/network/exchange or destructive lifecycle operation.

**D14 G0.42 verdict:** OWNER-APPROVED FOR THIS EXACT PARENT-BOUND CORRECTION AND ONE FRESH G0.41 ATTEMPT ONLY. D11 numeric ceilings remain OPEN / NOT RATIFIED.


## 11. D14 narrow amendment — G0.43 report serialization correction and one fresh attempt

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Owner authorization: standing bounded G0 authorization through D11 completion, applied to exact G0.43 owner package  
Package: `docs/evidence/G0_43_G041_REPORT_SERIALIZATION_CORRECTION_OWNER_PACKAGE_2026-11-11.md`  
Package commit: `66a2f9fc70c09ffbe073dfc98acfb500df5aeb42`  
Exact implementation parent / approved `github.event.before`: `66a2f9fc70c09ffbe073dfc98acfb500df5aeb42`

The owner has authorized this exact G0.43 correction and one fresh G0.41 one-shot attempt under the standing bounded authorization through D11. The existing `.github/workflows/g041-s1-single-measurement.yml` may be corrected only for report serialization and exact-parent binding; this D14 record may be amended; then exactly one frozen runner invocation may occur if all pre-invocation guards pass.

The single implementation push must have exact parent SHA `66a2f9fc70c09ffbe073dfc98acfb500df5aeb42`. Job admission requires push event, exact branch `refs/heads/feature/t0-centralized-data-feeder-p1-20261101`, exact `github.event.before` equal to `66a2f9fc70c09ffbe073dfc98acfb500df5aeb42`, `github.event.head_commit.id == github.sha`, and `github.run_attempt == 1`. Existing exact workflow-path push trigger remains. Reruns must skip before any step.

Serialization contract: create one canonical compact sorted UTF-8 JSON byte sequence from the already-produced report object; require the exact expected top-level field inventory; parse the exact bytes with `json.loads`; require parsed-object equality; write those exact bytes without any appended suffix; read the persisted file bytes back; require byte equality and parse/equality again before upload. JSON parsing must reject trailing non-whitespace data. This validation must not invoke `prepare_preflight` again, reconstruct fixtures, inspect parser input bytes, or create another artifact.

If guards pass, invoke frozen `tools.s1_measurement_runner.prepare_preflight(...)` exactly once and upload exactly one validated JSON report artifact with seven-day retention. Preserve the existing report schema and evidence fields, read-only `contents: read`, pinned actions, exact SHA checkout, shallow clone, `persist-credentials: false`, Python 3.14.4, no secrets/packages/network/providers/databases/VPS/exchange, and five-minute timeout.

Frozen Python blobs must remain unchanged: harness `e8db71c11e0503ea6d9a2480d75470185c4d5100`; runner `23a35aab7f7aeacd8a3f63d630a875fe76b1ff6a`; tests `d06a5b533af14378ed284051e5b057cf57377876`.

Any pre-invocation guard failure means NOT RUN and requires a new owner decision; do not repair or repush under this authorization. Any failure after the runner invocation begins consumes this one-shot attempt and is FAILED/INCOMPLETE. No retry, rerun, repair-and-rerun, second invocation or replacement attempt.

This amendment authorizes only this workflow correction, this D14 update and the one bounded G0.41 measurement attempt. It does not authorize any other workflow/CI changes, source/test/dependency changes, D11 numeric ceiling proposal/ratification/enforcement, parser/verifier production implementation, cryptography/trust/key changes, S2, T0/T1/T2, canonical market data, model/training, ledgers, Shared Risk Engine, Kill Switch, PostgreSQL, VPS/runtime, provider/database/network/exchange or destructive lifecycle operations. T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.

**D14 G0.43 verdict:** OWNER-AUTHORIZED FOR THIS EXACT PARENT-BOUND SERIALIZATION CORRECTION AND ONE FRESH G0.41 ATTEMPT ONLY. D11 numeric ceilings remain OPEN / NOT RATIFIED.


## 12. D11 numeric resource ceiling ratification — G0.44

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Decision basis: user's standing bounded authorization to approve G0 work automatically through D11 completion, explicitly granted 2026-11-11.  
Evidence report: `docs/evidence/G0_44_D11_MEASURED_RESOURCE_LIMITS_RATIFICATION_2026-11-11.md`.

The G0.43 one-shot measurement is accepted as D11 evidence: checkout `93ac905a3b8afb5bebb7c841140c0bccb9f1a47c`; Actions run `43053648998`; job `130637223760`; artifact `13870492247`; independently verified ZIP SHA-256 `4cdefc2ed049bd49b1092fb8cf113f92b411c08281f9f7c8db0137e36a85fcca`; corpus SHA-256 `1c9a302d9df179322bfd7a00aa6db322a66b578a0609b9264481c3801b8a2d94`. 22 fixtures, 11 D10 types, A-01–A-13 all true, two measurement passes equal, empty execution trace.

**Ratified exact ceilings for S1 Synthetic Contract Fixture v1:**
- Raw input: 8,192 bytes per fixture.
- Nesting depth: 8 container levels (root container = level 1).
- Object members: 32 per object.
- Array items: 64 per array.
- String value: 1,024 UTF-8 bytes per value.
- String key: 256 UTF-8 bytes per key.
- Scalar nodes: 256 per fixture.
- Diagnostic reason codes: at most 1 fixed code per invalid fixture.

**Ratified fail-closed policy:** reject an input when any ceiling is exceeded; check raw byte size before decoding/parsing; strict UTF-8; malformed inputs are measured by raw bytes only where structural dimensions are not applicable; count original duplicate-key input bytes; no truncation, normalization, silent field drop, raw-input echo or partial acceptance; no more than one fixed reason code per invalid fixture. Passing structural validation conveys no trust or execution authority.

Diagnostic evidence note: report rows explicitly contain parser-level `parse_reason_code`; schema outcomes are checked by A-02 against the frozen oracle and the frozen validator returns a single scalar reason code. No multi-code diagnostic output is permitted by this ratification.

D11 status: **COMPLETE — MEASUREMENT-FIRST REQUIREMENT SATISFIED; EXACT NUMERIC CEILINGS AND FAIL-CLOSED STRUCTURAL POLICY RATIFIED.** Runtime enforcement remains NOT IMPLEMENTED / NOT VERIFIED. This decision does not authorize parser/verifier source changes, tests, CI changes, runtime, T0/T1/T2, market/model data, ledgers, Shared Risk Engine, Kill Switch, PostgreSQL, VPS, external services or destructive lifecycle operations. Existing D14 implementation scope remains separate and unchanged. D01–D04, D06–D09 and D12–D13 remain OPEN / NOT RATIFIED.
