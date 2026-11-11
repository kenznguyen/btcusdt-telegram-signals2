# G0.39 — S1 Measurement Harness Implementation Authorization Package

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Baseline HEAD: `e635f157884be14c1a2735d70511f39633716515`  
Baseline handoff blob: `ad343ebf9f5101d76cb8bd4b942b1ca95fa8ccf3`  
Input analysis: G0.38 report blob `01775588ebc768801e07c72dc1c72fab874e0765`  
Type: documentation-only owner authorization package  
Verdict: **PACKAGE READY — harness implementation authorization requested; no implementation or measurement authority**

## 1. Purpose and current authorization state

G0.37-A's one-attempt measurement authorization is consumed. Its outcome remains FAILED / INCOMPLETE. G0.34 and G0.37-A intermediate metrics/digests are NOT VERIFIED for D11 policy use. Numeric D11 ceilings remain OPEN / NOT RATIFIED.

G0.38 identified that a future measurement cannot safely be authorized until the exact harness source, executable assertions, duplicate-key handling, and provenance are frozen and reviewed.

G0.39 therefore requests a staged decision: first authorize creation and focused verification of a standalone measurement harness. Only after that work is completed, reviewed and frozen should a separate G0.40 package request a new one-time measurement. Approval of G0.39 must not be interpreted as permission to generate a corpus or perform measurements.

## 2. Decision requested

The owner is asked to approve or reject the complete bounded scope in Sections 3–7, including the D14 path-boundary amendment in Section 4.

A plain approval applies only to G0.39 harness implementation and its focused local tests. It does not authorize G0.40 measurement execution, parser/verifier implementation, production use, CI changes or any external/runtime operation.

## 3. Proposed G0.39-A implementation scope

If separately approved, permit only:

1. Create a standalone deterministic measurement harness module at `tools/s1_measurement_harness.py`.
2. Create focused tests at `tools/test_s1_measurement_harness.py`.
3. Implement a frozen manifest model for the proposed S1 case inventory (SYN-01, SYN-29, SYN-30, SYN-31, SYN-32) and all 11 ratified D10 fixture types. The manifest and generator are code/specification only at this stage; no corpus generation outside unit-test execution.
4. Implement strict D05 structural validation, including exact key sets, exact JSON types, required fields, literals, synthetic identifiers and explicitly enumerated negative-case exceptions.
5. Implement duplicate-aware JSON inspection that detects repeated keys at every object depth before mapping conversion; include unique-key positive controls and top-level/nested duplicate-key negative tests.
6. Keep parser-input bytes and oracle metadata in separate structures. Only parser-input bytes may enter raw-size measurement, structural measurement or digest calculation.
7. Implement deterministic raw-byte measurement, digest framing, root-depth semantics, structural traversal, two-pass equality, assertion registry A-01–A-13 and report schema/readback validation as pure functions.
8. Make every assertion executable and evidence-producing. Missing evidence, exception, omitted assertion, unknown assertion, mismatch or provenance mismatch must fail closed. No literal/default PASS, skipped assertion or swallowed exception.
9. Add focused unit tests for the harness functions and failure paths, including proof that oracle metadata cannot enter parser-input bytes or digest.
10. Run only the focused test and compile commands specified in Section 6 after implementation approval. Record exact source/test blobs and commit.

The harness must be deterministic and bounded. It must not read the clock, filesystem inventory, environment secrets, network, database, VPS, connected services or production data. It must not write fixture payloads, oracle records, temporary corpora, caches or generated artifacts.

## 4. D14 scope amendment requested

G0.31 D14 originally ratified only `pipeline/synthetic_contract.py`, `pipeline/test_synthetic_contract.py`, evidence docs and handoff for a future S1 parser implementation. The proposed measurement harness is a distinct pre-measurement tool and must not be silently treated as inside that earlier boundary.

G0.39 explicitly requests a narrow D14 amendment for the two new `tools/` paths in Section 3, limited to synthetic measurement harness code and focused tests. It does not amend or authorize the parser implementation boundary, lifecycle evaluator, verifier, trust configuration or any production module.

If the owner does not approve this D14 amendment, do not create either source file or test file.

## 5. Mandatory harness design contract

### 5.1 Manifest and determinism
- Exact ordered fixture inventory and unique fixture IDs.
- Exact case ID and D10 mapping for every manifest entry.
- Reject missing, duplicated, reordered where order is contractually fixed, or extra manifest entries.
- Generator recipe and version are deterministic and explicitly versioned.
- No unregistered fixture type or case ID.

### 5.2 D05 structural validator
- Validate the ratified Synthetic Contract Fixture v1 structure.
- Validate exact top-level fields and exact nested `subject` fields.
- Validate exact types without coercion.
- Enforce schema version, purpose literal and reserved synthetic identifier patterns.
- Permit only the exact negative mutations listed in the manifest for their designated test cases.
- Positive controls must pass the structural validator; negative controls must fail for the expected parser-contract reason.
- Oracle metadata is held outside parser input and is never serialized into the input bytes.

### 5.3 Duplicate-aware parser
- Detect duplicate object keys at every nesting level before converting objects into ordinary mappings.
- Preserve exact byte input and distinguish invalid UTF-8, malformed JSON, duplicate keys and trailing content.
- Include both a unique-key positive control and top-level plus nested duplicate-key negative controls.
- No “last value wins” behavior and no silent duplicate collapse.

### 5.4 Measurement semantics
- Raw byte count is calculated from the exact supplied byte sequence.
- Digest framing/order is fixed in source and documented; no parse/reserialize substitution.
- Root container depth is 1; child containers increment depth by one; scalar root depth is 0.
- Object members count key/value pairs; array items count elements.
- String values and object keys are measured separately in UTF-8 bytes.
- Scalar-node definition is fixed and excludes object keys.
- Malformed inputs report only dimensions that can be measured safely; every NOT_APPLICABLE field has a reason.
- Two passes consume the same immutable in-memory corpus and compare all per-fixture and aggregate records.

### 5.5 A-01–A-13 assertion registry
Every assertion must map to:
- A named executable check.
- Explicit inputs and outputs.
- Required evidence fields.
- A deterministic pass/fail predicate.
- Fail-closed behavior on exception, missing evidence or mismatch.

The test suite must include deliberate fault injection proving that each mandatory assertion fails when its evidence is missing or false. Literal success constants, skipped checks, broad exception swallowing and implicit success defaults are prohibited.

### 5.6 Provenance and report
- The eventual measurement run must bind to exact source commit and harness blob SHA-256.
- Capture exact command, interpreter/runtime/platform and measurement-definition revision.
- Verify the harness digest against the frozen revision before and after any future measurement.
- Serialize one report, read it back, validate the schema and independently recompute aggregates from per-fixture rows.
- Report readback is a separate integrity assertion and cannot substitute for any measurement assertion.

## 6. Focused implementation verification gate

After explicit G0.39-A approval, permitted commands are:

- `python -m unittest tools.test_s1_measurement_harness -v`
- `python -m py_compile tools/s1_measurement_harness.py tools/test_s1_measurement_harness.py`

Tests must use synthetic inline inputs only and must not persist corpus payloads or oracle records. No broader repository suite, CI workflow, workflow dispatch, benchmark, dependency installation, build, deployment or external access is included.

Acceptance evidence:
- Every focused test passes.
- Compile check passes.
- A-01–A-13 registry has no missing or default-success checks.
- Fault-injection tests demonstrate fail-closed behavior for missing/false evidence.
- D05 positive and negative controls behave as declared.
- Duplicate keys are detected at top-level and nested levels.
- Oracle/input separation is demonstrated by tests.
- Two-pass determinism and report aggregate recomputation are tested.
- No filesystem/network/database/clock/environment/secret/VPS/runtime side effects.
- Exact source/test blob SHAs, commit SHA and command outputs are recorded.
- Final code review verifies only the two approved `tools/` paths plus evidence/handoff changed.

Any acceptance failure means G0.39-A is BLOCKED/FAILED; no measurement is permitted. Fixes beyond the approved scope require a new owner decision. Do not infer G0.40 measurement authority from a passing harness.

## 7. Explicit exclusions

Not authorized by this package:
- Any corpus generation or measurement attempt, including a dry-run outside unit tests.
- Any new G0.37-A retry, repair, reuse of its in-memory corpus or reliance on its metrics/digest.
- Numeric D11 ceiling selection, ratification or enforcement.
- Parser/verifier implementation, lifecycle evaluator changes, S2, cryptography, signatures, keys, trust roots, registries or production adapters.
- CI/workflow changes, dispatch, merge, deployment, dependency changes or executable release artifacts.
- CPU/RAM, throughput, allocation or adversarial performance benchmarking.
- Filesystem inventory, network/provider/database/VPS/runtime/connected-app access.
- T0/T1/T2, market data, models, CORE_LEDGER, AI_LEDGER, storage lifecycle or destructive operations.
- Any production or live trading action.

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.

## 8. Decision register

| Decision | Requested disposition |
|---|---|
| G0.39-A standalone harness implementation | Explicit owner approval required |
| D14 amendment for the two `tools/` paths | Explicit owner approval required |
| Focused local harness tests and compile | Included only if G0.39-A is approved |
| New corpus measurement (G0.40) | NOT AUTHORIZED; separate package and approval required |
| Numeric D11 ceilings | OPEN / NOT RATIFIED |
| Parser/verifier implementation | NOT AUTHORIZED |
| CI / external / runtime access | NOT AUTHORIZED |

## 9. Current status and next gate

**G0.39: PACKAGE READY — documentation prepared; G0.39-A harness implementation and D14 amendment PENDING EXPLICIT OWNER APPROVAL.**

No source or test file was created. No focused test, compile, corpus generation or measurement was run. No new authorization is implied.

If approved, the next work is only the two-file standalone harness implementation and its focused local verification under the stated boundary. After that, a separate G0.40 owner decision package may be prepared for a distinct one-time measurement attempt. Do not execute G0.40 without its own explicit approval.

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.
