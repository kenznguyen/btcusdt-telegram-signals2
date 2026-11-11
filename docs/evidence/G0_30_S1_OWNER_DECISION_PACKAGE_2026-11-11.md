# G0.30 — S1 Owner Decision Package: Schema, Synthetic Vocabulary, Limits and Gate

Date: 2026-11-11 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Baseline HEAD: `51ac7ed3845ce94d43e74c1d9e9aca9517292e3f`
Baseline handoff blob: `f1bdb1ef51b151a4cbb5729ccb0235e4e913a6f1`
Type: documentation-only owner decision package
Disposition: **DECISION PACKAGE PASS — concrete S1 options prepared; D05/D10/D11/D14 remain OPEN pending explicit owner ratification**

## 1. Purpose and boundary

G0.30 turns the recommended S1 milestone from G0.29 into a bounded owner decision package. S1 remains limited to deterministic synthetic parser/contract validation without cryptography.

This report proposes exact candidate schema fields, a closed synthetic fixture vocabulary, conservative parser limits and implementation/test boundaries. These are recommendations for owner review, not approved settings. No implementation or test execution is authorized by this report.

## 2. D05 — Proposed synthetic fixture schema v1

### 2.1 Design rule

Do not call this a production verified-facts envelope. Name it **Synthetic Contract Fixture v1**. It is a test input record only. It carries no trusted facts, no proof of identity/authority, no signature and no lifecycle disposition.

Suggested top-level shape:

| Field | Type | Required | Contract |
|---|---|---:|---|
| `schema_version` | string | yes | Exact literal `synthetic-contract-fixture/v1` |
| `fixture_id` | string | yes | Reserved prefix `syn-fixture-`; unique within suite |
| `case_id` | string | yes | Exact `SYN-01`…`SYN-38` or later explicitly registered synthetic case |
| `fixture_type` | string | yes | One value from D10 allowlist |
| `subject` | object | yes | Exactly `object_id`, `version_id`, `namespace` |
| `purpose` | string | yes | Exact literal `PARSER_CONTRACT_TEST_ONLY` |
| `claims` | object | yes | Synthetic untrusted input fields under a case-specific closed schema |
| `expected` | object | yes | Test-oracle metadata; never passed to parser-under-test |
| `notes` | string | no | Human-readable, synthetic-only, non-authoritative |

### 2.2 Structural rules proposed

- UTF-8 JSON only for the initial parser test input. This does not define canonical signed bytes.
- Reject invalid UTF-8, malformed JSON, duplicate object keys, non-finite numbers, invalid Unicode scalar sequences and trailing non-whitespace content.
- Reject unknown top-level fields and unknown fields in closed nested objects. No permissive extension bag.
- Require exact JSON types; do not coerce strings to numbers, booleans to strings, null to missing or arrays to objects.
- Reject unsupported schema versions and unsupported critical fields.
- `expected` is test-harness metadata stored separately from the untrusted input passed to the parser. It must never be accepted as a claim or influence parser output.
- IDs must be synthetic and match bounded ASCII patterns; do not include production identifiers, personal data, secrets or real evidence references.
- Timestamps, if a case needs to exercise timestamp syntax, are inert strings or integers only. S1 does not evaluate clock freshness, expiry, revocation or ordering.
- `claims` is parsed as untrusted data and must not be translated into authenticated/verified facts.
- No digest, signature, issuer proof, key identifier or authentication status is required by this S1 schema. If such fields appear in a case, they are inert negative-test payloads or rejected as unknown; no cryptographic meaning is assigned.

### 2.3 Candidate reason-code families

- `PARSE_INVALID_UTF8`
- `PARSE_INVALID_JSON`
- `PARSE_DUPLICATE_KEY`
- `PARSE_TRAILING_DATA`
- `PARSE_NONFINITE_NUMBER`
- `SCHEMA_VERSION_UNSUPPORTED`
- `SCHEMA_FIELD_MISSING`
- `SCHEMA_FIELD_UNKNOWN`
- `SCHEMA_TYPE_MISMATCH`
- `SCHEMA_VALUE_OUT_OF_RANGE`
- `SCHEMA_SYNTHETIC_ID_INVALID`
- `SCHEMA_PURPOSE_UNSUPPORTED`
- `LIMIT_INPUT_BYTES`
- `LIMIT_NESTING_DEPTH`
- `LIMIT_OBJECT_MEMBERS`
- `LIMIT_ARRAY_ITEMS`
- `LIMIT_STRING_BYTES`

These are candidate stable parser/contract reason codes only. They are not lifecycle evaluator reason codes and must not be mapped to `VERIFIED`, `REVIEWABLE_NONCANONICAL` or any authorization state.

## 3. D10 — Proposed synthetic-only fixture vocabulary

Use a dedicated `fixture_type` namespace, not production `data_class`. Proposed closed allowlist:

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

Rules:
- Every identifier and payload is fabricated and uses a `syn-` namespace.
- Vocabulary names describe the subject matter of a negative/positive parser case; they do not assert that the claim is true or authoritative.
- No real data-class mapping, production source authority, issuer trust, inventory completeness, sensitivity classification or lifecycle eligibility is implied.
- Do not add a new value without an explicit schema version change and owner approval.
- Do not include actual credentials, tokens, private keys, personal data, account identifiers, market data, T0/T1/T2 records or VPS details.

This synthetic vocabulary is deliberately separate from the existing lifecycle evaluator's production-facing class identifiers and does not change that evaluator.

## 4. D11 — Proposed resource bounds

The G0.23 matrix contains abstract case descriptors, not serialized fixture bytes. Therefore exact limits cannot honestly be described as empirically measured yet. The following conservative values are **candidate ceilings for owner review**, to be confirmed against a future fixture corpus before implementation:

| Resource | Candidate ceiling | Enforcement point |
|---|---:|---|
| Raw input | 64 KiB | Before JSON parsing |
| Nesting depth | 8 | During bounded parse |
| Members per object | 32 | During parse/schema validation |
| Items per array | 64 | During parse/schema validation |
| UTF-8 bytes per string | 1 KiB | During parse/schema validation |
| Total scalar nodes | 512 | During bounded traversal |
| Diagnostic reason codes | 16 | Before returning result |
| Diagnostic text | No raw input echo; fixed reason codes only | All error paths |

Additional constraints:
- No recursive traversal without an explicit depth bound.
- No unbounded error aggregation, input echo, logging or fixture expansion.
- Reject over-limit inputs before constructing large secondary representations where the parser permits.
- Limits apply only to the synthetic test parser, not to production payloads or the T0/T1/T2 data plane.
- Before ratification, generate a proposed fixture corpus from the abstract SYN cases and record actual maximum bytes/depth/member/array/string/node counts. Set each ceiling above the observed maximum with a documented safety margin; do not silently raise limits after tests fail.

**D11 recommendation:** ratify the measurement method now, but keep numeric ceilings provisional until fixture-size evidence exists. If the owner wants numeric values ratified immediately, treat the table as conservative fixed limits and explicitly accept that they are policy ceilings, not empirically derived maxima.

## 5. D14 — Proposed S1 implementation and test gate

### 5.1 Permitted scope if separately approved

Proposed paths:
- New parser/contract module: `pipeline/synthetic_contract.py`
- New focused test module: `pipeline/test_synthetic_contract.py`
- Optional fixture definitions embedded in test code; no standalone fixture corpus unless separately approved.
- Documentation/evidence and `docs/PROJECT_SESSION_HANDOFF.md` updates.

Explicitly excluded paths:
- `pipeline/lifecycle_disposition.py` and its existing tests.
- T0/T1/T2, market-data storage/API/clients, model/training/inference, CORE_LEDGER, AI_LEDGER, trading/execution, credentials, trust configuration and runtime deployment.
- Any workflow file or CI permission change in the initial S1 implementation increment.

### 5.2 Proposed commands

- Focused tests: `python -m unittest pipeline.test_synthetic_contract -v`
- Syntax check: `python -m py_compile pipeline/synthetic_contract.py pipeline/test_synthetic_contract.py`

These commands are proposed only. They have not been run for G0.30.

### 5.3 Acceptance evidence

- Test IDs and expected outcomes map to the selected subset of G0.23.
- Positive structural controls and negative malformed/ambiguous/unsupported/boundary cases are covered.
- Every numeric resource limit has a test at the boundary and one beyond the boundary.
- Determinism is proven for repeated identical inputs.
- Test oracle is isolated from parser input.
- No trusted-facts object, evaluator input, lifecycle eligibility or execution authorization is emitted.
- No network, provider, filesystem inventory, database, key store, clock or VPS dependency.
- Focused tests and compile checks pass; exact source/test blobs and commit SHA are recorded.
- Code review confirms the module has no I/O or authority side effects.
- CI changes, workflow dispatch, merge, deployment and S2 remain outside this gate.

### 5.4 Proposed status vocabulary

- `PASS`: every in-scope acceptance criterion evidenced.
- `BLOCKED`: a required decision or dependency remains unresolved.
- `NOT VERIFIED`: a check/evidence item was not performed.
- No status may be promoted based on a design statement alone.

## 6. Decision register — owner response required

| Decision | Recommendation | Current status |
|---|---|---|
| D05 | Ratify Synthetic Contract Fixture v1 structure and strict JSON/schema rules in §2 | OPEN |
| D10 | Ratify the 11-value synthetic-only `fixture_type` allowlist in §3 | OPEN |
| D11 | Ratify measurement-first process; numeric ceilings remain provisional until synthetic corpus metrics are recorded | OPEN |
| D14 | Approve only the proposed S1 implementation paths/commands and local focused tests; no CI workflow changes | OPEN |

A single approval may ratify all four recommendations only if it explicitly confirms each one. Any modification must identify the affected field/value/path/command.

## 7. Explicit non-decisions and prohibitions

- D01–D04, D06–D09, D12 and D13 remain OPEN / NOT RATIFIED.
- No cryptographic profile, signature algorithm, canonical signed-byte format, trust root, key, issuer authority, freshness window or revocation mechanism is selected.
- No real-source evidence verification, owner authentication, production inventory closure, custody proof or verified-facts process boundary is established.
- No parser, test module, fixture file, schema implementation, API, registry, adapter, runner, workflow or permission change is made.
- No tests or workflow dispatch are performed.
- No provider/network/database/VPS/runtime access or inventory is performed.
- No archive, quarantine, cleanup, expiry, compaction, VACUUM or deletion is performed.
- T0 canonical data and lease/fencing remain independent and protected; no T0 mutation.
- CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.

## 8. Final verdict and next gate

**G0.30: DECISION PACKAGE PASS — exact S1 schema, vocabulary, resource-bound options and implementation gate are prepared for owner review. D05/D10/D11/D14 remain OPEN; implementation and test execution are NOT AUTHORIZED.**

Next gate: owner explicitly ratifies or amends each of D05, D10, D11 and D14. Only after that decision may a separate bounded S1 implementation authorization be considered.
