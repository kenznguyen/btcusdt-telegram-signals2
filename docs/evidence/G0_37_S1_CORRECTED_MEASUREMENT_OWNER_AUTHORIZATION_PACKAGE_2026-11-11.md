# G0.37 — S1 Corrected Measurement Owner Authorization Package

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Baseline HEAD: `3a39e300400495adca078e9d1042b3613da21ad7`  
Baseline handoff blob: `0ab7143b30b722cb92f43cfd3dd79db3755700a9`  
Design input: G0.36 report blob `a0c9f20c8fc40e704239d9d4b48fe7fdd2caf454`  
Type: documentation-only owner authorization package  
Verdict: **PACKAGE READY — owner decision required; no measurement execution authority**

## 1. Purpose and interpretation of current approval

The user approved proceeding with G0.37 after G0.36. This authorizes preparation of this owner authorization package only. It does not authorize corpus generation, measurement, parser/test implementation, CI, or any runtime operation.

G0.33-A's single attempt remains consumed. G0.34 measurements remain NOT VERIFIED for D11 policy use. G0.37-A below is a new proposed one-attempt authorization and requires a separate explicit owner approval before execution.

## 2. Decision requested

Approve or reject the exact bounded scope in Section 3. A plain approval should be interpreted only against this package's G0.37-A scope. Any amendment to the case inventory, execution environment, persistence, tools, assertions, or excluded activities requires a revised decision package.

## 3. Proposed G0.37-A authorization — one in-memory attempt

If explicitly approved, permit exactly one isolated attempt to:

1. Generate the frozen synthetic S1 corpus in memory only.
2. Cover the exact S1 case set SYN-01, SYN-29, SYN-30, SYN-31 and SYN-32, with all 11 D10 `fixture_type` values represented.
3. Keep parser-input UTF-8 bytes and test-oracle metadata in separate in-memory structures. Oracle metadata MUST NOT be serialized into parser input or included in any parser-input measurement.
4. Measure the exact immutable parser-input byte sequences and the G0.32 structural dimensions using the G0.36 definitions.
5. Perform two measurement passes over the same in-memory corpus and require exact equality.
6. Evaluate all predeclared assertions A-01 through A-13. No assertion may be omitted, skipped or deferred.
7. Emit one evidence report containing per-fixture metadata, aggregate measurements, corpus digest, assertion outcomes, execution environment/tool versions and explicit limitations. Do not emit raw fixture payloads or oracle bundles.
8. Read back and validate the final report before declaring the attempt complete.

The exact fixture inventory, deterministic generation recipe, root-depth convention, duplicate-key treatment, ordering/framing rule for the digest and report schema must be frozen in the execution record before the first payload is generated. If any required definition cannot be fixed without changing the ratified contract, stop and return for owner decision.

## 4. Hard execution boundaries

**Allowed only after separate approval**
- One in-memory corpus generation.
- Two measurement passes over the same in-memory corpus.
- Evaluation of A-01–A-13.
- One evidence report with non-payload metadata and measurements.

**Not allowed**
- A second attempt, rerun, repair-and-rerun or retry after failure/incomplete output.
- Persisting fixture payloads, oracle records, executable fixtures, temporary corpora or caches.
- Parser, verifier, production source, or test-module implementation or execution.
- CI changes, workflow dispatch, build/deployment, dependencies or generated executable artifacts.
- CPU/RAM, allocation, throughput or adversarial performance benchmarking.
- Any numeric D11 ceiling ratification, enforcement or claim of production resource safety.
- Network, external providers, databases, VPS, local project runtime, external inventory or connected-app access.
- T0/T1/T2, market data, models, CORE_LEDGER, AI_LEDGER, storage lifecycle or destructive operations.
- Cryptographic operations, keys, signatures, trust-root changes or owner-authorization implementation.

A failed or incomplete run consumes the one-attempt authorization. No automatic retry is permitted. A new attempt requires a new owner decision.

## 5. Mandatory acceptance gates

The attempt is accepted as a completed measurement only if every item passes:

| Assertion | Acceptance requirement |
|---|---|
| A-01 | Exact approved case inventory and all 11 D10 values present |
| A-02 | Each input matches the D05 structural envelope, except intentional negative-case violations |
| A-03 | No oracle/expected/test-result metadata appears at any depth in parser-input JSON |
| A-04 | Oracle records remain separate and map unambiguously to synthetic fixture IDs |
| A-05 | Exact supplied bytes are measured; no parse/reserialize substitution |
| A-06 | Malformed UTF-8/JSON and duplicate keys handled per frozen measurement definitions |
| A-07 | Every dimension reported or marked NOT_APPLICABLE with a reason |
| A-08 | Aggregates reproducible from per-fixture records |
| A-09 | Two passes produce identical per-fixture and aggregate records |
| A-10 | Corpus, generator, tool/runtime and measurement-definition revisions captured |
| A-11 | Final report serialization, validation and readback succeed |
| A-12 | No payload persistence; only approved metadata is emitted |
| A-13 | No prohibited external, runtime, database, VPS, market-data, ledger or lifecycle access |

Any failure, exception, omitted assertion, incomplete output or report readback failure means **FAILED/INCOMPLETE**. Intermediate values must not be represented as a completed measurement or used to ratify D11.

## 6. Required output and evidence

The only permitted persistent output is the G0.37 completion report and the corresponding handoff update in the existing branch. The report must contain:
- Exact owner approval reference and scope.
- Baseline source SHA and branch.
- Frozen corpus revision, case inventory and D10 coverage.
- Parser-input/oracle separation evidence, including A-03.
- Exact measurement definitions and digest framing/order.
- Per-fixture metadata and aggregate metrics.
- Two-pass equality evidence.
- All A-01–A-13 outcomes.
- Runtime/tool versions and exact source/tool revision.
- Final report readback validation.
- Commit SHA, report blob SHA, handoff blob SHA and branch comparison.
- Clear limitations and next owner gate.

No raw payloads, oracle bundles or fixture files are to be committed or attached. No CI run or artifact is expected or authorized.

## 7. D11 policy status

Even if the one attempt completes successfully:
- Measurements are observations, not approved limits.
- Candidate ceilings may be presented for review only if directly supported by observed dimensions.
- No ceiling becomes active until the owner separately approves the exact numeric table and enforcement semantics.
- No CPU/RAM or production parser-safety conclusion may be drawn from this structural-only measurement.

## 8. Current decision record

| Item | Status |
|---|---|
| G0.36 design | PASS |
| Approval to prepare G0.37 package | APPROVED |
| G0.37-A one-attempt measurement | PENDING EXPLICIT APPROVAL |
| G0.34 historical metrics | NOT VERIFIED for D11 use |
| Numeric D11 ceilings | OPEN / NOT RATIFIED |
| Parser/tests/CI | NOT AUTHORIZED |
| Runtime/VPS/external access | NOT AUTHORIZED |

## 9. Owner response required

To authorize execution, the owner must explicitly approve the complete G0.37-A scope in Section 3 and accept all exclusions and one-attempt failure semantics in Section 4. If not approved, no corpus generation or measurement may occur.

**G0.37 verdict: PACKAGE READY — preparation approved; measurement execution remains NOT AUTHORIZED pending a separate explicit owner decision.**

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.
