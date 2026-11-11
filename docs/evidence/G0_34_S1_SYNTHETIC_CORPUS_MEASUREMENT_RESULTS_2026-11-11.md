# G0.34 — S1 Synthetic Corpus Measurement Results

Date: 2026-11-11 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Baseline HEAD: `6c3ac52bc0dacac6e428844f224618b87d6a5399`
Baseline handoff blob: `426e7a497a9f1c87b3624c16b332bb024b3d1593`
Authorization: explicit owner approval of G0.33-A in this conversation
Inputs: G0.23, G0.31, G0.32, G0.33
Type: one isolated in-memory synthetic corpus generation and structural resource-measurement run
Disposition: **MEASUREMENT PASS — 24 synthetic fixtures; all 11 D10 types covered; two-pass deterministic equality PASS; numeric ceilings proposed only, NOT RATIFIED**

## 1. Authorization and scope

The owner explicitly approved G0.33-A: one isolated, deterministic, in-memory synthetic corpus generation and resource-measurement run, limited to the S1 scope and ratified D10 vocabulary; no persistent fixture files; no parser/test implementation or execution; no CI/runtime/network/database/VPS access; documentation-only evidence output; no numeric ceilings ratified by the run.

This report records that one run only. It does not authorize another measurement run, parser implementation, test module creation/execution, CI changes, cryptographic verification, verifier integration, lifecycle decisions or destructive operations.

## 2. Execution environment and containment

- Execution method: one isolated Python in-memory execution cell; no shell command or repository source module was created.
- Python: `3.13.5`.
- Platform: `Linux-6.18.57-x86_64-with-glibc2.41`.
- Unicode database: `15.1.0`.
- Payload construction: deterministic UTF-8 JSON serialization with compact separators and non-finite numbers disabled; malformed-byte cases were explicitly constructed as byte strings.
- Measurement: independent standard-library JSON decoding/structural traversal; duplicate keys detected from original object-pair sequences before mapping collapse.
- Two passes used the same in-memory corpus and same measurement procedure.
- No payload bytes were written to disk, repository, temporary file, fixture directory or artifact. Only this measurement report is persisted.
- No raw payload content is reproduced in this report.
- No network, GitHub API, provider, database, secret, credential, key store, clock, VPS, lifecycle evaluator, verifier, trading/data runtime or production dataset was accessed by the measurement execution.
- No test suite, parser implementation, CI workflow or workflow dispatch was run.

## 3. Corpus identity and coverage

- Corpus revision: `G033A-S1-INMEM-24-v1`.
- Corpus digest: SHA-256 over the concatenation of the 24 exact payload byte strings, separated by one LF byte: `b6b1ddf4530eea6d92bc7cb6bde4ed6474398db527a08cd36d891c3310b202e7`.
- Fixture count: 24.
- Total raw input bytes: 16,350.
- Largest raw input: 3,816 bytes.
- D10 vocabulary coverage: 11/11 exact ratified values.
- S1 cases represented: SYN-01, SYN-29, SYN-30, SYN-31 and SYN-32.
- SYN-33 remains excluded. SYN-02–28 and SYN-34–38 remain excluded.
- D05 parser-input/oracle separation was respected: the `expected` oracle field is not present in any well-formed parser-input payload. Expected parser-only labels are held separately in the measurement record.
- All fixture IDs and fabricated identifiers use the reserved `syn-` namespace. No production-derived values or external references were used.

### 3.1 Per-fixture measurements

Depth counts nested JSON containers with the root container at level 1. Object members are the maximum key/value pairs in any one object. Array items are the maximum elements in any one array. Scalar nodes count string, number, boolean and null values; object keys are excluded. String values and keys are reported separately in UTF-8 bytes.

`N/A` means structural dimensions were not calculated because the original bytes were malformed, invalid UTF-8, contained duplicate keys or had trailing content. Raw byte size is still measured from the original byte sequence.

| Fixture | SYN | D10 type | Oracle category | Raw bytes | Depth | Max object members | Max array items | Max value bytes | Max key bytes | Scalars |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| S1-TYPE-01 | 01 | SYNTHETIC_OBJECT | VALID_SHAPE | 379 | 2 | 8 | 0 | 29 | 14 | 11 |
| S1-TYPE-02 | 01 | SYNTHETIC_EVIDENCE | VALID_SHAPE | 381 | 2 | 8 | 0 | 29 | 14 | 11 |
| S1-TYPE-03 | 01 | SYNTHETIC_ISSUER_CLAIM | VALID_SHAPE | 385 | 2 | 8 | 0 | 29 | 14 | 11 |
| S1-TYPE-04 | 01 | SYNTHETIC_POLICY_CLAIM | VALID_SHAPE | 385 | 2 | 8 | 0 | 29 | 14 | 11 |
| S1-TYPE-05 | 01 | SYNTHETIC_INVENTORY_CLAIM | VALID_SHAPE | 388 | 2 | 8 | 0 | 29 | 14 | 11 |
| S1-TYPE-06 | 01 | SYNTHETIC_SENSITIVITY_CLAIM | VALID_SHAPE | 390 | 2 | 8 | 0 | 29 | 14 | 11 |
| S1-TYPE-07 | 01 | SYNTHETIC_HOLD_CLAIM | VALID_SHAPE | 383 | 2 | 8 | 0 | 29 | 14 | 11 |
| S1-TYPE-08 | 01 | SYNTHETIC_DEPENDENCY_CLAIM | VALID_SHAPE | 389 | 2 | 8 | 0 | 29 | 14 | 11 |
| S1-TYPE-09 | 01 | SYNTHETIC_COPY_LINEAGE_CLAIM | VALID_SHAPE | 391 | 2 | 8 | 0 | 29 | 14 | 11 |
| S1-TYPE-10 | 01 | SYNTHETIC_FRESHNESS_CLAIM | VALID_SHAPE | 388 | 2 | 8 | 0 | 29 | 14 | 11 |
| S1-TYPE-11 | 01 | SYNTHETIC_BINDING_CLAIM | VALID_SHAPE | 386 | 2 | 8 | 0 | 29 | 14 | 11 |
| S1-29-MALFORMED | 29 | SYNTHETIC_OBJECT | MALFORMED_JSON | 18 | N/A | N/A | N/A | N/A | N/A | N/A |
| S1-29-DUPKEY | 29 | SYNTHETIC_OBJECT | DUPLICATE_KEY | 99 | N/A | N/A | N/A | N/A | N/A | N/A |
| S1-29-TRAILING | 29 | SYNTHETIC_OBJECT | TRAILING_DATA | 378 | N/A | N/A | N/A | N/A | N/A | N/A |
| S1-29-UTF8 | 29 | SYNTHETIC_OBJECT | INVALID_UTF8 | 9 | N/A | N/A | N/A | N/A | N/A | N/A |
| S1-30-VERSION | 30 | SYNTHETIC_EVIDENCE | UNSUPPORTED_SCHEMA_VERSION | 383 | 2 | 8 | 0 | 31 | 14 | 11 |
| S1-30-CRITICAL | 30 | SYNTHETIC_ISSUER_CLAIM | UNKNOWN_CRITICAL_FIELD | 425 | 2 | 9 | 0 | 29 | 18 | 12 |
| S1-31-DEPTH | 31 | SYNTHETIC_POLICY_CLAIM | RESOURCE_SHAPE | 471 | 13 | 8 | 0 | 29 | 14 | 10 |
| S1-31-MEMBERS | 31 | SYNTHETIC_INVENTORY_CLAIM | RESOURCE_SHAPE | 1,632 | 2 | 48 | 0 | 29 | 14 | 57 |
| S1-31-ARRAY | 31 | SYNTHETIC_SENSITIVITY_CLAIM | RESOURCE_SHAPE | 1,776 | 2 | 8 | 96 | 29 | 14 | 105 |
| S1-31-STRING | 31 | SYNTHETIC_HOLD_CLAIM | RESOURCE_SHAPE | 3,816 | 2 | 8 | 0 | 3,328 | 132 | 11 |
| S1-31-SCALARS | 31 | SYNTHETIC_DEPENDENCY_CLAIM | RESOURCE_SHAPE | 2,428 | 3 | 8 | 480 | 29 | 14 | 489 |
| S1-32-MISSING | 32 | SYNTHETIC_COPY_LINEAGE_CLAIM | MISSING_REQUIRED_FIELD | 353 | 2 | 7 | 0 | 29 | 14 | 10 |
| S1-32-WRONGTYPE | 32 | SYNTHETIC_FRESHNESS_CLAIM | WRONG_FIELD_TYPE | 317 | 2 | 8 | 0 | 29 | 14 | 9 |

## 4. Aggregate measurements

| Dimension | Observed maximum / total |
|---|---:|
| Fixture count | 24 |
| Total raw bytes | 16,350 |
| Raw bytes, per-fixture maximum | 3,816 |
| Nesting depth | 13 |
| Members in one object | 48 |
| Items in one array | 480 |
| String value UTF-8 bytes | 3,328 |
| String key UTF-8 bytes | 132 |
| Scalar nodes per fixture | 489 |
| Distinct synthetic parser-only oracle reason labels | 8 |
| D10 types | 11/11 |

The eight diagnostic labels are the distinct expected categories represented by the negative fixtures: malformed JSON, duplicate key, trailing data, invalid UTF-8, unsupported schema version, unknown critical field, missing required field and wrong field type. This is an oracle-category count only. No parser was implemented or run, so this is **not** a measurement of actual parser diagnostic output.

## 5. Repeatability

The exact same 24 payload byte strings were measured twice in the same isolated execution.

- Fixture count matched: PASS.
- Per-fixture identity/order matched: PASS.
- Every per-fixture raw-byte and structural measurement matched: PASS.
- Aggregate measurements matched: PASS.
- Corpus digest matched by construction of the same ordered byte sequence: PASS.

**Repeatability: PASS — 24/24 per-fixture records identical across both passes.**

## 6. Candidate numeric ceiling proposal — NOT RATIFIED

The following are proposals derived from observed maxima with an explicit margin. They are not defaults, active constraints or owner-approved policy. No implementation may enforce them until a separate owner decision ratifies the exact table.

| Resource | Observed maximum | Proposed ceiling | Approx. margin above observed | Rationale |
|---|---:|---:|---:|---|
| Raw input bytes | 3,816 | 8,192 | 114.7% | More than 2x observed maximum; accommodates moderate schema growth |
| Nesting depth | 13 | 16 | 23.1% | Small bounded headroom while limiting recursion depth |
| Object members | 48 | 64 | 33.3% | One-third headroom for structural expansion |
| Array items | 480 | 640 | 33.3% | One-third headroom above the largest measured array |
| String value UTF-8 bytes | 3,328 | 4,096 | 23.1% | Bounded headroom above the long Unicode value |
| String key UTF-8 bytes | 132 | 256 | 93.9% | Near 2x headroom for schema key evolution |
| Scalar nodes | 489 | 1,024 | 109.4% | More than 2x headroom while keeping total nodes finite |
| Diagnostic reason codes | 8 | 16 | 100% | 2x headroom above the eight oracle categories |

These candidate values are a design recommendation, not a result mechanically compelled by this small synthetic corpus. The corpus intentionally exercises bounded shapes; it does not establish production distributions, adversarial workload maxima, CPU cost, peak memory, parser allocation amplification or safe operational limits. Before ratification, review whether the proposed array, depth and string limits align with the intended S1 contract and whether an additional memory/CPU benchmark is necessary. Such further measurement would require its own scope decision if it falls outside G0.33-A.

The G0.30 provisional values remain NOT RATIFIED and are not substituted for this measured proposal.

## 7. Limitations and non-claims

- This was structural and payload-size measurement, not CPU/RAM profiling, peak-allocation measurement, throughput benchmarking or denial-of-service testing.
- No parser-under-test was present. This report does not establish parser correctness, rejection behavior, runtime resource bounds or production safety.
- The standard-library JSON decoder was used only as an independent structural measurement aid. It is not the proposed S1 parser and does not prove exact future parser behavior.
- Malformed UTF-8, malformed JSON, duplicate-key and trailing-data inputs were measured by original raw byte length only; structural dimensions are N/A.
- Diagnostic reason-code count is based on the synthetic expected-category list, not emitted parser diagnostics.
- Two-pass equality establishes deterministic output for this fixed in-memory corpus and method only; it is not a general determinism proof.
- No persistent corpus file or artifact exists. The digest identifies the ordered in-memory payload sequence recorded by this run; payload reconstruction requires the documented deterministic recipe, not retrieval of a stored artifact.

## 8. Final status and next gate

| Item | Status |
|---|---|
| G0.33-A exact authorization | APPROVED |
| One in-memory corpus generation | PASS |
| 24-fixture S1 subset coverage | PASS |
| D10 type coverage | PASS — 11/11 |
| Two-pass repeatability | PASS — 24/24 |
| Payload persistence | NONE |
| Structural/payload-size measurements | PASS |
| CPU/RAM benchmark | NOT RUN / OUT OF SCOPE |
| Candidate numeric ceilings | PROPOSED ONLY |
| Numeric D11 ratification | OPEN / NOT RATIFIED |
| Parser implementation | NOT AUTHORIZED |
| Test module creation/execution | NOT AUTHORIZED |
| CI changes/dispatch | NOT AUTHORIZED |
| Cryptographic/verifier work | NOT AUTHORIZED |
| Runtime/VPS/database/network access | NOT PERFORMED |
| Lifecycle/destructive operation | NOT PERFORMED / NOT AUTHORIZED |

**G0.34 verdict: MEASUREMENT PASS — G0.33-A completed within its approved boundary. Numeric ceilings remain OPEN pending separate owner ratification. S1 parser implementation and tests remain NOT AUTHORIZED.**

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.
