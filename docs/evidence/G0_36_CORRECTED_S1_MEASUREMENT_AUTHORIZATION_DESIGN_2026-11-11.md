# G0.36 — Corrected S1 Measurement Authorization Design

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Baseline HEAD: `5b7db072ec71c9594d77e74f49d44937f9552944`  
Baseline handoff blob: `e9f1879b69d38b37323f2817c0591cd5e528d3ed`  
Inputs: G0.31 D05/D10/D11/D14 owner ratification; G0.32 measurement specification; G0.35 evidence correction  
Type: documentation-only authorization design  
Verdict: **DESIGN PASS — corrected protocol defined; new measurement NOT AUTHORIZED; numeric D11 ceilings OPEN**

## 1. Purpose

G0.36 defines a corrected, bounded proposal for a future S1 synthetic corpus measurement. It addresses the G0.35 findings without reusing G0.34 measurements as policy evidence.

This document is not an execution authorization. The earlier G0.33-A approval covered one attempt, which is consumed. A new owner decision is required before any further corpus generation or measurement.

## 2. Governing decisions and boundaries

The future protocol remains subordinate to:
- D05: strict Synthetic Contract Fixture v1; parser input and test-oracle metadata must be separate.
- D10: exact closed 11-value synthetic-only `fixture_type` allowlist.
- D11: measurement-first; numeric resource ceilings require separate owner ratification.
- D14: S1 implementation boundary does not itself authorize implementation or test execution.

G0.34 is retained as historical evidence but marked NOT VERIFIED for D11 policy use by G0.35. No value from G0.34 may be used as an observed maximum, baseline, safety margin or ceiling.

## 3. Corrected input/oracle separation

The proposed corpus representation has two physically and logically distinct in-memory objects:

1. **Parser input**: the exact UTF-8 JSON byte sequence supplied to the structural measurement/parser boundary. It contains only fields allowed by the D05 fixture schema. It MUST NOT contain `expected`, `oracle`, `assertion`, `test_result`, or equivalent expected-outcome metadata.
2. **Oracle record**: a separate test-harness record keyed by a synthetic fixture identifier. It contains the expected parser-only disposition/reason code and is never serialized, concatenated, nested, or otherwise included in parser-input bytes or parser-input structural metrics.

The fixture identifier may be used as an external harness correlation key only if the D05 parser-input contract independently permits its presence in the input. The harness MUST NOT infer parser success from the oracle record. The measurement report records the oracle identifier and expected outcome as metadata outside the input measurement.

Required invariant for every fixture:
- Parser-input byte digest and length are computed only from the exact parser-input bytes.
- Oracle metadata has its own separately reported metadata representation and is excluded from parser-input digest, byte length, nesting, member, array, string and scalar counts.
- No measurement function accepts a combined input-plus-oracle object.
- A preflight structural check rejects any parser-input top-level or nested field reserved for harness/oracle metadata.
- The corpus is rejected before measurement if input/oracle separation cannot be demonstrated.

## 4. Corrected corpus scope

The proposal retains the G0.32 S1 subset:
- SYN-01: positive structural controls.
- SYN-29: malformed UTF-8/JSON, duplicate keys and trailing data.
- SYN-30: unsupported schema version and unknown critical field.
- SYN-31: bounded resource-shape probes.
- SYN-32: missing required field and wrong structural type.
- All 11 exact D10 fixture types must be represented across the corpus.

SYN-33 remains excluded until its extension semantics are separately decided. SYN-02–28 and SYN-34–38 remain outside S1 parser measurement. The future corpus must use fabricated `syn-` identifiers only and contain no production data, personal data, credentials, market data, ledger/model records or external evidence.

The exact fixture count and case-by-case mapping must be frozen in the new authorization request before execution; G0.34's 24-fixture count is not a required target and is not evidence.

## 5. Predeclared completion and acceptance assertions

The future run is considered complete only if every predeclared assertion below is evaluated and its result is captured in the final report. An assertion failure means the run is FAILED/INCOMPLETE; no partial metrics may be promoted to accepted D11 evidence.

| ID | Predeclared assertion | Required result |
|---|---|---|
| A-01 | Corpus has exactly the approved case inventory and all 11 D10 values | PASS |
| A-02 | Every parser-input payload conforms to the D05 input envelope shape, subject to its declared negative case | PASS |
| A-03 | No oracle/expected/test-result field occurs anywhere inside parser-input JSON | PASS |
| A-04 | Oracle records are held separately and keyed unambiguously to parser-input fixture IDs | PASS |
| A-05 | Input bytes are measured exactly as supplied; no parse-and-reserialize size substitution | PASS |
| A-06 | Malformed UTF-8/JSON and duplicate-key dimensions are handled according to G0.32 definitions without silent normalization | PASS |
| A-07 | Every required measurement dimension is reported per fixture or explicitly marked NOT_APPLICABLE with reason | PASS |
| A-08 | Every corpus aggregate is reproducible from the per-fixture records | PASS |
| A-09 | A second pass over the same immutable in-memory corpus produces identical per-fixture and aggregate records | PASS |
| A-10 | Corpus revision, generator/tool revision, interpreter/runtime version and measurement-definition revision are captured | PASS |
| A-11 | Final report serialization/validation succeeds and is read back before the run is declared complete | PASS |
| A-12 | No fixture payload is persisted; only approved aggregate/per-fixture metadata is emitted | PASS |
| A-13 | No network, provider, database, VPS, project runtime, market-data, ledger or lifecycle access occurs | PASS |

The run must not report an overall PASS if any assertion is missing, skipped, errors, or is evaluated after the final report has already been emitted. Assertion evaluation order and failure behavior must be fixed before execution.

## 6. Measurement dimensions and reporting

Use G0.32 definitions without silently changing root-depth convention. Report per-fixture and aggregate:
- exact raw parser-input bytes;
- maximum JSON container nesting depth;
- maximum object members in one object;
- maximum array items in one array;
- maximum UTF-8 string value bytes and key bytes, separately;
- total scalar nodes;
- diagnostic reason-code count only where the measurement boundary actually produces such output; otherwise mark NOT_APPLICABLE rather than using oracle labels as parser diagnostics.

For malformed UTF-8/JSON, report raw byte length and only those additional dimensions that can be measured without normalization or pretending the input is valid JSON. Duplicate-key detection must inspect original input structure and must not rely on a mapping that discards duplicate occurrences.

This structural corpus measurement does not establish CPU/RAM limits, allocation amplification, throughput, worst-case parser behavior or production resource safety. Such benchmarking is outside this proposal and requires separate authorization.

## 7. Output, custody and data hygiene

The future run may emit only:
- the approved evidence report;
- per-fixture measurement metadata without raw payload content;
- aggregate metrics;
- corpus digest computed over exact parser-input bytes using a predeclared ordering and framing rule;
- assertion results and execution environment metadata.

No raw fixture payload, oracle bundle, executable fixture file, cache, temporary artifact, or persistent corpus is permitted by this proposal. If output persistence or a new artifact location is later required, that path and retention/access controls need separate approval.

All identifiers and values must be synthetic. Never include secrets, actual account/user identifiers, credentials, keys, tokens, real market data, provider records or VPS information. On detecting non-synthetic/sensitive material, stop and mark BLOCKED; do not silently sanitize and continue.

## 8. Proposed new owner authorization: G0.37-A

The next decision package should request one bounded attempt with the following exact scope:

**Allowed if separately approved**
- Generate the frozen synthetic S1 corpus in memory only.
- Maintain parser-input bytes and oracle metadata in separate structures.
- Run the predeclared structural measurement twice against the same in-memory parser-input bytes.
- Evaluate A-01 through A-13.
- Emit one documentation evidence report containing per-fixture metadata, aggregates, digest, environment and all assertion outcomes.
- Read back and validate the final report before declaring completion.

**Explicitly excluded**
- Any second attempt, rerun, repair-and-rerun or follow-on benchmark.
- Persistent fixture payloads or executable fixture files.
- Parser, verifier, test-module or production source implementation.
- Unit/integration tests, CI changes or workflow dispatch.
- CPU/RAM benchmark, adversarial performance benchmark or production-safety claim.
- Numeric D11 ratification or enforcement.
- Network/provider/database/VPS/runtime access or external inventory.
- T0/T1/T2, model, ledger, storage, lifecycle or destructive operations.
- Cryptographic operations, keys, signatures, trust-root or owner-authorization implementation.

A failed or incomplete attempt consumes the one-run authorization if G0.37-A is approved. Any further attempt requires a new explicit owner decision.

## 9. Acceptance evidence required after an approved run

A completion report must record:
1. Exact approval statement and approved scope.
2. Baseline HEAD and branch.
3. Corpus revision, exact case inventory and D10 coverage.
4. Separate parser-input/oracle data model and A-03 proof.
5. Exact measurement definitions, including root-depth convention and duplicate-key handling.
6. Per-fixture and aggregate measurement metadata.
7. Both-pass equality evidence.
8. A-01–A-13 individual results; no omitted assertions.
9. Runtime/tool versions and exact source/tool revision.
10. Final report readback validation.
11. Exact commit SHA, report blob SHA, handoff blob SHA and branch comparison.
12. Explicit limitations and next owner decision.

No workflow run or CI artifact is expected because the proposed step is documentation-only and isolated from CI. If the implementation approach changes, seek approval before changing the scope.

## 10. Current status and next gate

| Item | Status |
|---|---|
| G0.35 evidence correction | PASS |
| G0.34 metrics for D11 use | NOT VERIFIED |
| D05/D10/D11 measurement-first/D14 | OWNER-RATIFIED |
| Corrected measurement protocol | DESIGN PASS |
| New corpus/measurement attempt | NOT AUTHORIZED |
| Numeric D11 ceilings | OPEN / NOT RATIFIED |
| Parser implementation/tests/CI | NOT AUTHORIZED |

**G0.36 verdict: DESIGN PASS — G0.37-A authorization package may be prepared; no execution authority is granted.**

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.
