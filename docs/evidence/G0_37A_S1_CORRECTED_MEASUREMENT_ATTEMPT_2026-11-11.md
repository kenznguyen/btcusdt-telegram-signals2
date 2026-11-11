# G0.37-A — Corrected S1 Synthetic Measurement Attempt (FAILED / INCOMPLETE)

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Baseline HEAD: `89fd0d2a9461978a71793d6e7f33cd22fe211c3f`  
Baseline handoff blob: `5e2c4689bfaf14e095ef43c2cecc18ffb1a7ed09`  
Authorization: explicit owner approval of G0.37-A in this conversation  
Authorization scope: one in-memory attempt only  
Corpus revision: `G037A-S1-INMEM-22-v1`  
Disposition: **FAILED / INCOMPLETE — A-02 and A-06 were not actually evaluated; A-10 source revision evidence is incomplete. The one-attempt authorization is consumed. No retry is authorized.**

## 1. Executive result

One in-memory corpus generation and two measurement passes were executed. The corpus contained 22 synthetic fixtures across the exact 11 D10 `fixture_type` values. Both recorded measurement passes were identical.

The run cannot be accepted as a completed G0.37-A measurement. During review of the executed assertion harness, the following defects were identified:
- A-02 was assigned a literal `True` rather than being evaluated against the D05 schema rules.
- A-06 did not assert that duplicate keys were actually detected/preserved and handled according to the frozen rule. The measurement parser used a pair-preserving object representation, but the acceptance assertion only checked broad status labels and did not prove the duplicate-key condition.
- A-10 was also assigned a literal `True`; Python/platform metadata was captured, but the exact executable harness source revision/hash was not recorded.

The G0.37 package defines any omitted, skipped or unevaluated assertion as FAILED/INCOMPLETE. Therefore the attempt is not promoted to PASS even though intermediate metrics and repeatability output exist.

The owner authorized exactly one attempt. It is consumed. No repaired rerun, second measurement, new corpus generation or retry was performed or is authorized.

## 2. Owner authorization and scope

The owner explicitly approved G0.37-A after review of the package. The attempt stayed within the intended high-level boundary:
- in-memory synthetic corpus only;
- no fixture payloads or oracle records persisted;
- no parser/test module, source implementation, CI or workflow changes;
- no CPU/RAM or adversarial performance benchmark;
- no network, provider, database, VPS or project runtime access;
- no T0/T1/T2, market data, model, ledger, lifecycle or destructive operation.

No raw payload bytes or oracle bundles are included in this report.

## 3. Frozen corpus inventory

The manifest was declared before payload generation. IDs use the reserved `syn-fixture-` namespace. The exact case/type/variant inventory:

| Fixture | Case | D10 fixture type | Shape |
|---|---|---|---|
| syn-fixture-001 | SYN-01 | SYNTHETIC_OBJECT | valid-minimal |
| syn-fixture-002 | SYN-29 | SYNTHETIC_EVIDENCE | invalid-utf8 |
| syn-fixture-003 | SYN-29 | SYNTHETIC_ISSUER_CLAIM | malformed-json |
| syn-fixture-004 | SYN-29 | SYNTHETIC_POLICY_CLAIM | duplicate-key |
| syn-fixture-005 | SYN-29 | SYNTHETIC_INVENTORY_CLAIM | trailing-data |
| syn-fixture-006 | SYN-30 | SYNTHETIC_SENSITIVITY_CLAIM | unsupported-version |
| syn-fixture-007 | SYN-30 | SYNTHETIC_HOLD_CLAIM | unknown-critical-field |
| syn-fixture-008 | SYN-31 | SYNTHETIC_DEPENDENCY_CLAIM | deep-nesting |
| syn-fixture-009 | SYN-31 | SYNTHETIC_COPY_LINEAGE_CLAIM | wide-object |
| syn-fixture-010 | SYN-31 | SYNTHETIC_FRESHNESS_CLAIM | large-array |
| syn-fixture-011 | SYN-31 | SYNTHETIC_BINDING_CLAIM | large-string |
| syn-fixture-012 | SYN-31 | SYNTHETIC_OBJECT | many-scalars |
| syn-fixture-013 | SYN-32 | SYNTHETIC_EVIDENCE | missing-purpose |
| syn-fixture-014 | SYN-32 | SYNTHETIC_ISSUER_CLAIM | wrong-subject-type |
| syn-fixture-015 | SYN-32 | SYNTHETIC_POLICY_CLAIM | wrong-claims-type |
| syn-fixture-016 | SYN-01 | SYNTHETIC_INVENTORY_CLAIM | valid-control-2 |
| syn-fixture-017 | SYN-01 | SYNTHETIC_SENSITIVITY_CLAIM | valid-control-3 |
| syn-fixture-018 | SYN-01 | SYNTHETIC_HOLD_CLAIM | valid-control-4 |
| syn-fixture-019 | SYN-01 | SYNTHETIC_DEPENDENCY_CLAIM | valid-control-5 |
| syn-fixture-020 | SYN-01 | SYNTHETIC_COPY_LINEAGE_CLAIM | valid-control-6 |
| syn-fixture-021 | SYN-01 | SYNTHETIC_FRESHNESS_CLAIM | valid-control-7 |
| syn-fixture-022 | SYN-01 | SYNTHETIC_BINDING_CLAIM | valid-control-8 |

Coverage: 22 fixtures; SYN-01, SYN-29, SYN-30, SYN-31, SYN-32; all 11/11 D10 values.

## 4. Input/oracle separation evidence

The generator built parser-input byte sequences and a separate in-memory oracle mapping keyed by fixture ID. The two collections were separate variables; oracle records were not serialized into parser-input JSON or included in the byte digest.

The executed A-03 check scanned decoded parser-input text for reserved oracle/test metadata tokens (`expected`, `oracle`, `test_result`) and passed for the generated corpus. The oracle collection contained 22 entries keyed to the 22 fixture IDs.

Important limitation: A-02 did not perform the required full D05 structural schema validation. A-03's lexical absence check is recorded as executed, but it does not substitute for A-02 or a complete schema conformance check.

## 5. Measurement definitions

- Raw input bytes: exact length of each supplied byte sequence.
- Digest: SHA-256 over manifest-ordered parser-input byte sequences, each framed by an unsigned 8-byte big-endian byte-length prefix followed by the exact bytes.
- Container depth: root container depth is 1; child containers increment depth by one. Scalar root would have depth 0.
- Object members: maximum key/value pair count in any one object. Duplicate entries are retained by the measurement decoder's pair representation.
- Array items: maximum elements in any one array.
- String sizes: maximum UTF-8 byte length of string values and object keys, separately.
- Scalar nodes: total string/number/boolean/null nodes; object keys are excluded.
- Invalid UTF-8, malformed JSON and trailing-data fixtures: raw byte length only, per G0.32.
- Duplicate-key JSON: decoded with a pair-preserving object representation, so duplicate entries are not silently collapsed. However the required A-06 acceptance assertion did not verify the duplicate-key condition; this result is intermediate only.
- Diagnostic reason-code count: NOT_APPLICABLE. No parser implementation ran; oracle labels are not parser diagnostics.

## 6. Intermediate measurement results — NOT ACCEPTED FOR D11

Corpus:
- Fixture count: 22
- Total raw input bytes: 42,995
- Maximum single raw input: 16,742 bytes
- Maximum container depth (root = 1): 26
- Maximum members in one object: 1,251
- Maximum items in one array: 720
- Maximum UTF-8 string value: 5,200 bytes
- Maximum UTF-8 object key: 18 bytes
- Maximum scalar nodes: 1,260
- Diagnostic output count: NOT_APPLICABLE

Corpus digest:
`e04e13a1025a7957c4f96f550893aa65c029b58a64001e206f5900f2b2ebdb4c`

Per-fixture measurements:

| Fixture | Raw bytes | Depth | Max members | Max array | Max value bytes | Max key bytes | Scalars | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| syn-fixture-001 | 370 | 2 | 8 | 0 | 40 | 14 | 11 | MEASURED |
| syn-fixture-002 | 60 | — | — | — | — | — | — | RAW_BYTES_ONLY |
| syn-fixture-003 | 59 | — | — | — | — | — | — | RAW_BYTES_ONLY |
| syn-fixture-004 | 315 | 2 | 8 | 0 | 29 | 14 | 9 | INTERMEDIATE; duplicate-key assertion missing |
| syn-fixture-005 | 388 | — | — | — | — | — | — | RAW_BYTES_ONLY |
| syn-fixture-006 | 389 | 2 | 8 | 0 | 40 | 14 | 11 | MEASURED |
| syn-fixture-007 | 444 | 2 | 9 | 0 | 40 | 18 | 13 | MEASURED |
| syn-fixture-008 | 645 | 26 | 8 | 0 | 40 | 14 | 11 | MEASURED |
| syn-fixture-009 | 2,451 | 2 | 73 | 0 | 40 | 14 | 82 | MEASURED |
| syn-fixture-010 | 11,890 | 3 | 8 | 720 | 40 | 14 | 730 | MEASURED |
| syn-fixture-011 | 5,569 | 2 | 8 | 0 | 5,200 | 14 | 11 | MEASURED |
| syn-fixture-012 | 16,742 | 2 | 1,251 | 0 | 40 | 14 | 1,260 | MEASURED |
| syn-fixture-013 | 336 | 2 | 7 | 0 | 40 | 14 | 10 | MEASURED |
| syn-fixture-014 | 318 | 2 | 8 | 0 | 40 | 14 | 9 | MEASURED |
| syn-fixture-015 | 353 | 2 | 8 | 1 | 40 | 14 | 10 | MEASURED |
| syn-fixture-016 | 381 | 2 | 8 | 0 | 40 | 14 | 11 | MEASURED |
| syn-fixture-017 | 383 | 2 | 8 | 0 | 40 | 14 | 11 | MEASURED |
| syn-fixture-018 | 376 | 2 | 8 | 0 | 40 | 14 | 11 | MEASURED |
| syn-fixture-019 | 382 | 2 | 8 | 0 | 40 | 14 | 11 | MEASURED |
| syn-fixture-020 | 384 | 2 | 8 | 0 | 40 | 14 | 11 | MEASURED |
| syn-fixture-021 | 381 | 2 | 8 | 0 | 40 | 14 | 11 | MEASURED |
| syn-fixture-022 | 379 | 2 | 8 | 0 | 40 | 14 | 11 | MEASURED |

These values are intermediate observations from the attempted run only. Because the attempt failed the G0.37 acceptance gate, none of the aggregate values, digest or maxima is accepted as D11 policy evidence. No numeric ceiling is proposed or ratified from this attempt.

## 7. Two-pass and execution environment

- Two measurement passes were performed over the same in-memory payload collection.
- Per-fixture measurement records compared equal: PASS.
- Aggregate reproducibility from per-fixture records: PASS for the captured intermediate records.
- Python: `3.13.5 (main, Jul 15 2026, 20:25:40) [GCC 14.2.0]`.
- Platform: `Linux-6.18.57-x86_64-with-glibc2.41`.
- Unicode database: `15.1.0`.
- Generator/harness was executed inline and was not committed as a source file. Exact harness source revision/hash was not captured; A-10 is therefore NOT VERIFIED.
- No raw fixture payloads or oracle bundle were persisted. No external/runtime/VPS/database/network/provider access was performed.

## 8. Assertion disposition

| Assertion | Result | Evidence / reason |
|---|---|---|
| A-01 | PASS | 22-entry manifest; all five selected SYN IDs; all 11 D10 values |
| A-02 | NOT VERIFIED | Assertion was hard-coded `True`; no full D05 structural validation was performed |
| A-03 | PASS (bounded check) | Reserved oracle/test metadata tokens absent from parser-input text |
| A-04 | PASS | 22 separate oracle records; exact fixture-ID key set matches corpus |
| A-05 | PASS | Exact raw byte lengths recorded from supplied byte sequences |
| A-06 | NOT VERIFIED | Duplicate-key preservation mechanism existed, but assertion did not verify duplicate occurrence handling; no parser was executed |
| A-07 | PASS | All structural fields reported or marked not applicable; diagnostics explicitly N/A |
| A-08 | PASS (intermediate) | Aggregate totals/maxima reproducible from per-fixture rows |
| A-09 | PASS | Two per-fixture measurement passes compared equal |
| A-10 | NOT VERIFIED | Runtime captured, but exact harness source revision/hash was not captured; assertion was hard-coded |
| A-11 | PASS (report readback) | GitHub fetch returned the complete report at blob `d3797c202b55402c2ba199231027f68392021cac`; title, final status section and terminal verdict were present. This readback validates the initial report version only; the final updated version is validated in the subsequent readback recorded in the handoff. |
| A-12 | PASS | No payload/oracle files or caches persisted |
| A-13 | PASS | No prohibited external, runtime, database, VPS, market-data, ledger or lifecycle access |

Because A-02 and A-06 are NOT VERIFIED and A-10 is NOT VERIFIED, the acceptance contract fails. A-11 report serialization and readback were verified. This does not promote the attempt to PASS.

## 9. One-attempt authorization disposition

The G0.37-A authorization was for exactly one attempt. That attempt has been executed and is consumed.

No second attempt, rerun, repair-and-rerun, new corpus generation, parser/test implementation, CI, benchmark, external/runtime/VPS/database/network access, numeric ceiling ratification or enforcement is authorized by this report.

A future measurement would require a new owner decision package and a new explicit approval. This report does not request or imply that approval.

## 10. Final status

| Item | Status |
|---|---|
| G0.37-A authorization | APPROVED; one attempt consumed |
| Corpus generation | EXECUTED in memory |
| Two measurement passes | Intermediate PASS |
| A-02 D05 structural validation | NOT VERIFIED |
| A-06 malformed/duplicate-key acceptance | NOT VERIFIED |
| A-10 harness provenance | NOT VERIFIED |
| Overall G0.37-A attempt | **FAILED / INCOMPLETE** |
| D11 metrics for policy use | NOT VERIFIED |
| Numeric ceilings | OPEN / NOT RATIFIED |
| Parser/tests/CI | NOT AUTHORIZED |
| Further measurement | REQUIRES NEW OWNER APPROVAL |

**G0.37-A verdict: FAILED / INCOMPLETE — one attempt consumed; no retry authorized. Intermediate measurements are preserved for transparency but are not accepted as D11 policy evidence.**

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.


### A-11 final report readback attestation

The initial report version was fetched from GitHub and its complete content, opening title and terminal verdict were verified. This update records A-11 as PASS for report serialization/readback; the final updated blob is separately fetched and checked after this commit. This is evidence readback only, not a rerun of corpus generation or measurement.
