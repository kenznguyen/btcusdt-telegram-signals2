# G0.39-A — S1 Measurement Harness Implementation Results

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Baseline HEAD: `bddbb830fb12faf252b4d824a8f83d3d5bd23b52`  
G0.39 authorization package blob: `f14e0345e37ba14dd9b1f62b93e71fc110fe33b0`  
Approval: owner message “phê duyệt tự động trong phạm vi G0”; interpreted narrowly as approval of G0.39-A implementation and its requested D14 amendment only  
Implementation HEAD at evidence capture: `61b3a0883d763c122224042c6211362c309ea9a8`  
Verdict: **PARTIAL — implementation committed and read back; local working-copy checks PASS; exact committed-blob test execution NOT VERIFIED**

## 1. Approved scope and authority

The owner approval is applied to the complete bounded G0.39-A scope:
- `tools/s1_measurement_harness.py`
- `tools/test_s1_measurement_harness.py`
- narrow D14 amendment for these two paths only.

It does not authorize corpus measurement (G0.40), numeric D11 ceiling ratification/enforcement, parser/verifier implementation, CI/workflow changes, external/runtime access, or changes to T0/T1/T2, market data, models, ledgers or lifecycle state.

## 2. Implementation delivered

### Measurement harness
- Strict UTF-8 JSON parsing; rejects invalid UTF-8, malformed/trailing JSON, non-finite numbers, invalid Unicode scalar sequences and duplicate object keys.
- Duplicate-aware object-pair representation preserves repeated keys at top-level and nested levels before any ordinary mapping conversion.
- D05 validation checks exact top-level field set, required fields, exact literals/types, reserved synthetic identifier patterns, exact `subject` keys, and the closed D10 allowlist.
- Non-empty `claims` require an explicit case-specific closed schema mapping; without one, only an empty claims object is accepted. No unratified case-specific claims vocabulary is invented.
- Parser-input bytes, manifest metadata and oracle records are separate data structures. Manifest metadata is independent of parser-input parsing so malformed SYN-29 payloads remain represented in A-01 inventory coverage.
- Exact raw byte measurement; root container depth = 1; separate key/value UTF-8 byte maxima; object member/array/scalar counts; malformed input dimensions marked NOT_APPLICABLE with a reason.
- SHA-256 digest uses manifest order and an unsigned 8-byte big-endian length prefix before each exact parser-input byte sequence.
- A-01–A-13 each have executable predicates; missing evidence and exceptions fail closed.
- Provenance verifies the frozen source-byte SHA-256 and requires it to match the reported source blob SHA-256.
- Report readback rejects duplicate JSON keys, validates the exact report/provenance schema, restricts per-fixture rows to safe measurement metadata, and independently recomputes aggregates.
- Static AST capability checks reject obvious filesystem-persistence and network/database/provider imports/calls from the harness module. The code itself exposes no I/O API.

### Focused tests
- Positive/negative D05 controls, exact typing, reserved synthetic identifiers, duplicate keys at nested levels, malformed UTF-8/JSON, non-finite values, invalid Unicode, oracle separation, exact manifest coverage, raw-byte/depth semantics, digest ordering/framing, aggregate recomputation, source-hash binding, report readback, unsafe report-row rejection, capability-boundary checks, all-assertion success and per-assertion fail-closed mutations.

## 3. Verification evidence and limitations

Local isolated authoring workspace:
- TDD RED: focused test import failed before the implementation module existed.
- Focused test command: `python -m unittest tools.test_s1_measurement_harness -v`.
- Result: **24 tests PASS**.
- Compile command: `python -m py_compile tools/s1_measurement_harness.py tools/test_s1_measurement_harness.py`.
- Result: **PASS**.
- No corpus measurement, benchmark, CI, workflow dispatch, network/provider/database/VPS/runtime access or persistent fixture payload generation was performed.

Important verification limitation:
- GitHub source/test blobs were fetched and read back, and static checks confirmed all A-01–A-13 registry entries, separate manifest metadata, source-hash binding and report schema guards.
- The exact GitHub blob contents were not re-materialized as the local test checkout after the final sequential GitHub edits. Therefore the 24/24 local test result and compile result cannot be cryptographically attributed to the exact final GitHub blobs below.
- Exact committed-source test execution is **NOT VERIFIED**. Do not claim G0.39-A acceptance PASS until a permitted focused run is performed against the exact HEAD/blob contents.

Additional design limitations:
- No ratified per-case non-empty `claims` field schemas were found in D05/G0.23/G0.32. The harness fails closed unless a case schema is supplied; future corpus preparation must either use empty claims or obtain a frozen schema map before generation.
- A-12/A-13 combine static source capability inspection with an in-memory execution trace. This is not an OS-level runtime isolation attestation and must not be represented as one.

## 4. GitHub source evidence

- Source: `tools/s1_measurement_harness.py`
  - final blob: `0f713a1cc87f4c0c355d4488f1cf6af4d8f08d98`
  - 323 lines at readback
- Tests: `tools/test_s1_measurement_harness.py`
  - final blob: `ff5e3c9d584e13948fc4265f9ca261e697fa9da6`
  - 177 lines; 24 test methods at final readback
- Final implementation HEAD before this report: `61b3a0883d763c122224042c6211362c309ea9a8`.
- Compare from G0.39 baseline: ahead 11 / behind 0; exactly two paths changed.
- No workflow files, dependencies, CI configuration or other production paths changed.
- No GitHub Actions run or artifact exists for this gate.

## 5. D14 amendment disposition

The owner approval is recorded as a narrow D14 amendment allowing only:
- `tools/s1_measurement_harness.py`
- `tools/test_s1_measurement_harness.py`

The original D14 parser boundary and all exclusions remain unchanged. This amendment does not authorize `pipeline/synthetic_contract.py`, lifecycle evaluator changes, verifier/trust implementation, CI or production/runtime integration.

## 6. Final status

| Item | Status |
|---|---|
| G0.39-A scope approval | APPROVED |
| Narrow D14 tools-path amendment | APPROVED |
| Harness source/test files | COMMITTED |
| GitHub readback | PASS |
| Local working-copy focused tests | 24/24 PASS |
| Local working-copy compile | PASS |
| Exact final GitHub blob execution | NOT VERIFIED |
| Overall G0.39-A | **PARTIAL / NOT VERIFIED** |
| G0.40 corpus measurement | NOT AUTHORIZED |
| Numeric D11 ceilings | OPEN / NOT RATIFIED |
| Parser/verifier implementation | NOT AUTHORIZED |
| CI/workflow/runtime | NOT AUTHORIZED |

Next gate: obtain an exact-source focused verification of the final GitHub HEAD and blobs, within the already approved G0.39-A test/compile commands. After that, prepare a separate G0.40 owner decision package; do not generate or measure a corpus until a distinct G0.40 approval exists.

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.
