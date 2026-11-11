# G0.38 — G0.37-A Failure Analysis and Corrected Harness Design

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Baseline HEAD: `b3fc29d44622f4b4ce7bce00f26ea41c8dd9c547`  
Baseline handoff blob: `ec6a9d210b7b6c6bee54db2eafe49b43db630158`  
Input report blob: `868f1a4cb0fa343bebd9e11fdf7bdc4056801c4f`  
Type: documentation-only failure analysis and future-gate design  
Verdict: **ANALYSIS PASS — failure causes and preventive controls documented; no new execution authority**

## 1. Purpose and boundary

G0.38 analyzes the consumed G0.37-A attempt and defines controls that a future owner decision package should require before any new measurement authorization. It does not repeat, repair, or validate the failed measurement.

The G0.37-A one-attempt authorization remains consumed. All recorded corpus metrics and digest remain NOT VERIFIED for D11 policy use. Numeric ceilings remain OPEN / NOT RATIFIED.

## 2. Evidence baseline

G0.37-A report: `docs/evidence/G0_37A_S1_CORRECTED_MEASUREMENT_ATTEMPT_2026-11-11.md`, final blob `868f1a4cb0fa343bebd9e11fdf7bdc4056801c4f`.

Recorded outcome:
- 22 in-memory fixtures; SYN-01, SYN-29–32; all 11 D10 fixture types.
- Two intermediate measurement passes compared equal.
- A-02 NOT VERIFIED: hard-coded true; no full D05 structural validation.
- A-06 NOT VERIFIED: duplicate-key handling assertion not actually verified.
- A-10 NOT VERIFIED: hard-coded true; exact harness source revision/hash not captured.
- A-03 bounded lexical scan, A-04 separation mapping, A-05 raw-byte measurement and A-09 repeatability were reported PASS, but do not compensate for failed mandatory assertions.
- A-11 final report readback PASS; this is report integrity evidence only.
- Overall attempt FAILED / INCOMPLETE; authorization consumed.

The report contains intermediate figures (42,995 bytes total; max input 16,742; depth 26; max object members 1,251; max array 720; max value string 5,200 bytes; max key 18 bytes; 1,260 scalar nodes; digest `e04e13a1025a7957c4f96f550893aa65c029b58a64001e206f5900f2b2ebdb4c`). These are historical observations only and MUST NOT be used to derive or ratify D11 ceilings.

## 3. Root-cause analysis

### RC-01 — Assertions were labels, not executable gates
A-02 and A-10 were assigned unconditional success values. Their presence in an assertion table did not prove the required operation occurred.

**Control:** every mandatory assertion must be computed from independently inspectable inputs/outputs; prohibit literal success constants in the harness; produce assertion evidence fields that identify the check and measured result. A missing/exceptional check must fail closed.

### RC-02 — Duplicate-key handling lacked a decisive test
A pair-preserving decoder was described, but A-06 did not prove that a duplicate key was detected and treated according to the ratified contract.

**Control:** include a byte-exact duplicate-key negative input; independently count repeated keys at every object depth before any conversion to a normal mapping; require the expected rejection classification; include a positive unique-key control. Do not silently collapse duplicates.

### RC-03 — Harness provenance was not frozen
The inline harness was not committed or hashed before execution. The report therefore could not bind observations to an exact, reproducible measurement program.

**Control:** in any future proposal, freeze the harness source as a reviewed immutable revision before authorizing execution; record repository commit, file blob SHA-256, interpreter/runtime versions and exact command. The executed source must match the frozen digest before and after execution.

### RC-04 — Acceptance evidence was not independently derived
The attempt's two-pass equality and aggregate consistency were useful but could not establish schema validity or parser contract correctness. A-11 readback validated report persistence, not measurement correctness.

**Control:** keep separate evidence layers: input-contract checks, raw-byte measurement, structural traversal, repeatability, report serialization/readback and provenance. Never infer one layer from another.

## 4. Proposed future harness architecture (design only)

A future, separately approved attempt should use a deterministic, bounded pipeline:

1. **Frozen manifest:** explicit fixture IDs, case IDs, D10 type mapping, expected negative mutation and stable order; reject missing, duplicate or extra entries.
2. **Separate data planes:** parser-input byte strings and oracle metadata remain distinct objects. Only parser-input bytes enter digest and measurement functions. Oracle metadata is joined by fixture ID only after parser-input validation.
3. **D05 validator:** validate exact top-level and nested key sets, exact JSON types, required fields, literals, synthetic identifier constraints and permitted case-specific negative mutations. Positive controls must pass; each intended negative must fail for its declared reason.
4. **Duplicate-aware JSON inspection:** use a pair-preserving representation or a streaming token scan that retains duplicate occurrences; test nested duplicate keys as well as top-level duplicates. No mapping conversion before duplicate detection.
5. **Raw-byte accounting:** count supplied bytes directly; never parse and reserialize to calculate input size or digest.
6. **Structural metrics:** define root-depth, object member, array, string-value, string-key and scalar-node semantics before execution. Mark malformed payload dimensions NOT_APPLICABLE with a specific reason.
7. **Two-pass determinism:** run the same immutable in-memory input set twice; compare per-fixture records, aggregate records and corpus digest exactly.
8. **Assertion registry:** A-01–A-13 each maps to a real check function, required evidence fields, and explicit failure behavior. No skipped assertion, default PASS, swallowed exception or success constant.
9. **Provenance envelope:** capture frozen source commit/blob digest, command, Python/runtime/platform versions and measurement-definition revision before executing.
10. **Report validation:** serialize once, parse/read back, validate required fields and independently recompute aggregates from report rows. Final readback is a separate report-integrity check, not a proxy for earlier assertions.

This architecture is a design recommendation only. It is not an implementation or authorization to run a new measurement.

## 5. Required preflight and stop conditions for any future authorization package

Before requesting another one-attempt authorization, a package should provide:
- Exact frozen harness source and its SHA-256, reviewed before execution.
- Executable A-01–A-13 mapping with no unconditional/default-success paths.
- D05 positive and negative structural-validation table, including intentional negative exceptions.
- Duplicate-key detection semantics and nested duplicate-key test vectors, described without generating a corpus.
- Exact manifest and deterministic generator specification.
- Digest framing/order, root-depth convention and all measurement definitions.
- A dry review demonstrating that parser-input bytes cannot include oracle metadata.
- Failure semantics: any assertion missing, exception, mismatch, report-readback failure or provenance mismatch consumes the one-time authorization.
- Explicit statement that observed measurements are not numeric policy limits and do not authorize parser implementation.

If any preflight item is unresolved, stop before generating payloads and return to owner decision. No implicit repair-and-rerun.

## 6. D11 disposition

G0.37-A figures are not accepted as D11 evidence. G0.34 historical figures were already downgraded by G0.35 and remain NOT VERIFIED. Therefore:
- No numeric ceiling is proposed or ratified in G0.38.
- No limit is enforced or silently substituted.
- No production parser safety, CPU/RAM safety, throughput or adversarial resilience claim is made.
- A future valid measurement, if separately approved and completed, would still require a separate owner decision to ratify exact numeric ceilings and enforcement semantics.

## 7. Scope and non-actions

Documentation-only. No corpus generation, measurement, harness implementation, parser/verifier implementation, tests, benchmarks, CI/workflow changes, dependency changes, executable artifacts, network/provider/database/VPS/runtime access, T0/T1/T2 access or changes, market data, model, ledger, lifecycle or destructive operations.

No retry or repair of G0.37-A. No new measurement authorization is requested or implied.

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.

## 8. Final verdict and next gate

**G0.38: ANALYSIS PASS — root causes and preventive design controls documented. G0.37-A remains FAILED / INCOMPLETE and consumed. D11 remains OPEN / NOT RATIFIED.**

Next gate: prepare a new owner decision package only if the owner wants to authorize a distinct future attempt after reviewing the frozen-harness preflight requirements. Until then, no corpus generation or measurement. Parser/tests/CI remain NOT AUTHORIZED.
