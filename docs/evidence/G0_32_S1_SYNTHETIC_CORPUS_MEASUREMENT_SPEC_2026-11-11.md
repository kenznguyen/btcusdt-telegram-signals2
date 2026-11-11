# G0.32 — S1 Synthetic Corpus Measurement Specification

Date: 2026-11-11 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Baseline HEAD: `67d141397b8498f4824ecc64230e627794da675e`
Baseline handoff blob: `6d16a8de8ee22f1caac557033fb9a655428e681e`
Inputs: G0.23 synthetic verifier contract test matrix; G0.30 S1 decision package; G0.31 owner ratification
Type: documentation-only measurement specification
Disposition: **SPECIFICATION PASS — S1 measurement method and case boundaries defined; corpus bytes, executable fixtures, numeric ceilings, parser implementation and tests NOT CREATED/AUTHORIZED**

## 1. Purpose and authority

G0.32 defines how a future S1 synthetic fixture corpus is to be planned and measured so that numeric resource ceilings can be proposed from evidence rather than guessed.

G0.31 ratified D05, D10, D11's measurement-first policy and the D14 S1 implementation boundary. It did not authorize implementation or test execution. G0.32 is therefore limited to a measurement specification and abstract corpus plan. It creates no fixture payloads, code, test modules, numeric limits or CI changes.

The corpus described here is an input to a future, separately authorized measurement step. This report does not authorize that step to create files or run code.

## 2. Scope and S1 interpretation of G0.23

G0.23 defines 38 logical verifier scenarios. They are not all parser/contract test cases. S1 validates only the structural Synthetic Contract Fixture v1 input contract; it must not attempt to prove issuer authenticity, cryptographic integrity, inventory truth, sensitivity truth, freshness, custody, owner authorization, lifecycle eligibility or execution authority.

### 2.1 Structural case mapping

| G0.23 case | S1 use | Measurement/validation purpose | Boundary |
|---|---|---|---|
| SYN-01 | Structural positive control only | Smallest valid-shaped fixture with synthetic fields | Does not test the G0.23 VERIFIED path |
| SYN-29 | Applicable parser negatives | Malformed UTF-8/JSON, duplicate keys, trailing data | No cryptographic semantics |
| SYN-30 | Applicable schema negatives | Unsupported schema version and unsupported critical field | Extension behavior remains closed as ratified |
| SYN-31 | Applicable resource-boundary design | Oversized/deep/large collection/string synthetic shapes | Numeric ceilings must be approved before enforcement |
| SYN-32 | Applicable schema negatives | Missing/wrongly typed/invalid structural fields | Parser/contract only |
| SYN-33 | Deferred | Unknown non-critical extension policy remains unresolved in G0.23 | Do not invent ignore/reject behavior beyond D05 closed-schema rules |
| SYN-02–28 | Excluded from S1 measurement corpus | Issuer, subject truth, integrity, provenance, inventory, sensitivity, policy, freshness and revocation semantics | Require later verifier/trust decisions |
| SYN-34–38 | Excluded from S1 measurement corpus | Downstream use, rebuildability, verified-facts immutability and authorization separation | Require later stages; not parser resource measurements |

A fixture may contain inert strings or synthetic claims to exercise JSON shape. Its presence does not mean S1 validates the truth of that claim. The G0.23 expected `VERIFIED`, `BLOCKED` or lifecycle outcomes must not be reused as S1 parser outcomes.

### 2.2 Proposed corpus strata

The future synthetic corpus should include:
1. Minimal valid-shape controls for each D10 `fixture_type`.
2. Required-field omissions, unknown fields and wrong-type variants for each closed object shape.
3. Duplicate-key and malformed-input examples at top-level and nested locations.
4. Schema-version and purpose mismatches.
5. Boundary-shape examples for each measured dimension: byte size, nesting, members/object, array items, string bytes, scalar nodes and diagnostics.
6. A one-variable-at-a-time over-boundary mutation for every numeric ceiling after that ceiling is approved.
7. Deterministic repeated copies to verify stable measurement and result behavior.

This is a coverage plan, not a fixture inventory or payload specification. Each future case must have one primary mutation and an independent expected result outside the parser input.

## 3. Synthetic safety and data hygiene

All corpus data must be fabricated from scratch and must:
- Use only the reserved `syn-` namespace and D10's exact 11-value `fixture_type` allowlist.
- Use only synthetic object IDs, versions, namespaces, case IDs and inert timestamp-shaped values.
- Contain no actual user/account identifiers, personal data, credentials, tokens, keys, market data, ledger/model data, T0/T1/T2 records, provider evidence or VPS details.
- Contain no real source paths, repository secrets, production artifact references or external URLs.
- Keep expected outcomes and test-oracle metadata outside the parser input.
- Never embed a real digest/signature/issuer proof or represent a fabricated value as cryptographically valid.
- Avoid logging or echoing raw fixture content in future diagnostics.

If any candidate fixture accidentally contains non-synthetic or sensitive content, exclude it and stop the measurement step; do not sanitize by silently rewriting source evidence into a fixture.

## 4. Measurement dimensions and definitions

The future measurement record must report at least the following dimensions per fixture and corpus aggregate:

| Dimension | Measurement definition | Unit / reporting |
|---|---|---|
| Raw input size | Exact number of bytes in the UTF-8 encoded JSON input as supplied to parser | bytes |
| Nesting depth | Maximum number of nested JSON container levels along any path; define root-depth convention in the measurement tool and keep it fixed | integer levels |
| Object members | Maximum number of key/value pairs in any single object | count |
| Array items | Maximum number of elements in any single array | count |
| String size | Maximum UTF-8 byte length of any JSON string value and key; report value/key maxima separately | bytes |
| Scalar nodes | Total number of scalar JSON values (string, number, boolean, null) across one fixture; keys are not scalar values | count |
| Diagnostic output | Maximum number of fixed reason codes returned for one invalid fixture; no raw-input echo | count |
| Corpus aggregate | Number of fixtures, total bytes, and maxima for each dimension | counts/bytes |

Measurement definitions must be applied consistently to valid and invalid fixtures. Malformed byte sequences that cannot be decoded as UTF-8 are measured by raw byte size only; no JSON structural dimensions are reported for them. Duplicate-key fixtures are measured from original bytes, not from a parsed mapping that has already discarded duplicate entries.

## 5. Measurement procedure for a separately authorized future step

1. **Freeze the abstract corpus plan.** Record the exact selected SYN IDs, D10 type coverage, structural variants and expected parser-only outcomes.
2. **Generate synthetic payloads deterministically.** Use a fixed documented generation recipe and stable synthetic identifiers. No runtime clock, randomness or external source should affect payload content.
3. **Preserve raw bytes.** Measure the exact byte sequence supplied to the parser; do not reserialize parsed objects to calculate input size.
4. **Measure structural dimensions independently.** Use a bounded measurement approach that does not depend on the parser-under-test and does not silently normalize duplicate keys or malformed encodings.
5. **Record per-fixture and aggregate results.** Include fixture ID, case ID, fixture type, byte length, each structural maximum/count, and whether a dimension is not applicable.
6. **Re-run the measurement.** The same corpus revision and recipe must produce identical measurements. Record tool/runtime version if a measurement utility is later authorized.
7. **Review coverage and outliers.** Confirm every required D10 type and each structural dimension is represented; explain the largest fixture in each dimension.
8. **Propose ceilings only after measurement.** For each dimension, show observed maximum, proposed safety margin, proposed ceiling and rationale. Do not derive a ceiling from an unobserved dimension.
9. **Obtain owner approval.** Numeric ceilings remain OPEN until the owner explicitly approves the exact table and any parser enforcement policy.
10. **Only then consider implementation.** S1 implementation still requires separate explicit authorization under D14.

No step above is performed by G0.32.

## 6. Required measurement evidence record

A future measurement report must include:

- Corpus revision identifier and immutable digest, if a corpus artifact is separately authorized.
- Exact SYN case IDs and D10 fixture-type coverage.
- Synthetic generation recipe and deterministic seed policy, if any.
- Measurement definitions and root-depth convention.
- Per-fixture measurements and corpus aggregate maxima.
- Repeated-run equality result.
- Any excluded case, unsupported shape or not-applicable measurement with reason.
- Proposed ceiling table with observed maximum, margin, candidate ceiling and justification.
- Explicit statement that no production data, real secrets or external evidence were used.
- Exact source/tool revision and command only if code/tool execution is separately authorized.
- Owner decision reference for numeric ceilings.

Do not include raw fixture payloads in ordinary evidence if doing so creates unnecessary disclosure or artifact size. Synthetic IDs and measurements are sufficient for the report; any future corpus artifact needs its own explicit path, retention and access approval.

## 7. Numeric ceiling proposal format — intentionally blank

The following table is the required future decision format. Values are intentionally left unset until corpus measurements exist.

| Resource | Observed maximum | Safety margin and rationale | Proposed ceiling | Owner status |
|---|---:|---|---:|---|
| Raw input bytes | NOT MEASURED | NOT PROPOSED | NOT SET | OPEN |
| Nesting depth | NOT MEASURED | NOT PROPOSED | NOT SET | OPEN |
| Object members | NOT MEASURED | NOT PROPOSED | NOT SET | OPEN |
| Array items | NOT MEASURED | NOT PROPOSED | NOT SET | OPEN |
| String value bytes | NOT MEASURED | NOT PROPOSED | NOT SET | OPEN |
| String key bytes | NOT MEASURED | NOT PROPOSED | NOT SET | OPEN |
| Scalar nodes | NOT MEASURED | NOT PROPOSED | NOT SET | OPEN |
| Diagnostic reason codes | NOT MEASURED | NOT PROPOSED | NOT SET | OPEN |

The G0.30 candidate values (64 KiB, depth 8, 32 object members, 64 array items, 1 KiB/string, 512 scalar nodes, 16 reason codes) remain explicitly NOT RATIFIED and are not defaults.

## 8. Future implementation and test boundary

If separately authorized, implementation remains restricted to:
- `pipeline/synthetic_contract.py`
- `pipeline/test_synthetic_contract.py`
- `docs/evidence/`
- `docs/PROJECT_SESSION_HANDOFF.md`

Future focused commands ratified under D14:
- `python -m unittest pipeline.test_synthetic_contract -v`
- `python -m py_compile pipeline/synthetic_contract.py pipeline/test_synthetic_contract.py`

G0.32 does not authorize these commands, file creation, fixture generation, test execution, CI workflow changes or workflow dispatch. No workflow file or CI permission changes are included in the initial S1 boundary.

## 9. Open decisions and limitations

- D01–D04, D06–D09 and D12–D13 remain OPEN / NOT RATIFIED.
- SYN-33's unknown non-critical extension behavior remains unresolved; do not create an S1 case that assumes a policy contrary to the ratified closed-schema rule.
- Numeric D11 ceilings remain OPEN until measured corpus evidence and explicit owner approval.
- No cryptographic profile, canonical signed-byte format, trust root, key lifecycle, issuer authority, freshness window, revocation mechanism, real evidence authority or verified-facts API is selected.
- S1 parser output remains structural validation only. It cannot be converted into trusted facts, evaluator input, lifecycle eligibility, owner authorization or execution permission.

## 10. Explicit non-actions and verdict

Documentation-only. No parser/source/test/fixture bytes, schema implementation, API, registry, adapter, runner, oracle, workflow, permission, credential, key, trust root, database, storage, market-data, model, ledger, VPS or runtime change. No tests, fixture generation, measurement execution, workflow dispatch, network/provider/database/VPS access or inventory. No archive, quarantine, cleanup, expiry, compaction, VACUUM or deletion.

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.

**G0.32: SPECIFICATION PASS — measurement dimensions, procedure, evidence format and S1/G0.23 case boundaries documented. Corpus payloads and measurements NOT CREATED/NOT RUN; numeric ceilings OPEN; implementation and tests NOT AUTHORIZED.**

Next gate: a separate owner decision may authorize creation of a wholly synthetic measurement corpus and isolated measurement run, limited to the approved synthetic namespace and without implementing the parser or verifier. Alternatively, request a later numeric-limit decision after such evidence exists. No permission is implied by this specification.
