# G0.40 — S1 Measurement Owner Decision Package

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Baseline HEAD: `c3eeff5810e64673c6404bfcbae1364b76944a11`  
Baseline handoff blob: `8b1b133090ae9955b26c524ce25a9b91373e7dc8`  
G0.39-B evidence blob: `32c4aaa5bb3a44e9c8f588b1da1e8e71a23c7da3`  
Harness source blob: `0f713a1cc87f4c0c355d4488f1cf6af4d8f08d98`  
Harness test blob: `ff5e3c9d584e13948fc4265f9ca261e697fa9da6`  
Type: owner decision package; documentation only  
Verdict: **REVIEW PACKAGE READY — measurement execution NOT AUTHORIZED; preflight gap identified**

## 1. Purpose and current state

G0.39-A and G0.39-B are now verified for the narrow standalone harness implementation and its focused test/compile scope.

- Exact checkout: `30fa54e6a24e95a275c4fbfd27170371e1d56d78`.
- Harness/test blobs: `0f713a1cc87f4c0c355d4488f1cf6af4d8f08d98` / `ff5e3c9d584e13948fc4265f9ca261e697fa9da6`.
- GitHub Actions run `43046949518`, job `130613317796`: SUCCESS.
- Focused tests: 24/24 PASS; focused compile: PASS.
- Artifact `13867028275`, SHA-256 `554a0bb3afdb00f8f2319471873a128676f7c64549c1c8f9f382170496853d62`.

This closes the exact-source verification gap. It does not establish that the harness can produce a valid, sufficiently representative S1 corpus or that every measurement dimension can be exercised under D05.

## 2. Decision requested

The owner is asked to decide whether to authorize a *pre-measurement runner hardening gate* (recommended) before any new corpus attempt.

**Recommended decision: authorize G0.40-A only**, with the exact scope below:
1. Add a deterministic, pure in-memory corpus builder and one-shot measurement orchestrator in a new file `tools/s1_measurement_runner.py`.
2. Add focused synthetic-only tests in `tools/test_s1_measurement_runner.py`.
3. Keep the existing frozen harness source unchanged.
4. Exercise all 11 ratified D10 fixture types and case IDs SYN-01, SYN-29, SYN-30, SYN-31 and SYN-32 using fresh synthetic bytes, with oracle metadata in a separate structure.
5. Prove the generator's manifest, D05 outcomes, parser/oracle separation, deterministic order, two-pass equality and all A-01–A-13 evidence inputs before any actual measurement attempt.
6. Run only the focused runner tests and py_compile commands specified in Section 7.
7. Update evidence and handoff on the existing branch.

G0.40-A would be implementation/test only. It would **not** execute the corpus measurement. A separate G0.41 owner package and explicit approval would be required for one new measurement attempt.

A simple “approve G0.40” must not be interpreted as approval to measure. The approval should name G0.40-A and the two exact paths above.

## 3. Why direct measurement is not ready

The verified harness exposes generic JSON measurement functions, but its current D05 contract constrains accepted fixtures:

- Top-level fields are closed; only the required fields plus optional `notes` are accepted.
- `subject` has exactly three string fields.
- `claims` must be empty unless a case-specific schema is explicitly supplied.
- The current runner/generator and exact per-fixture manifest are not frozen as committed source.
- The current harness has no standalone deterministic corpus builder or orchestration entry point.

Consequently, simply invoking the measurement functions on hand-assembled inputs would leave the most failure-prone part—the generator, manifest, oracle, and assertion evidence—unfrozen. The G0.34 and G0.37-A failures show why an ad hoc inline generator is not acceptable.

A further coverage constraint must be handled explicitly: valid D05 fixtures are structurally shallow. To measure nested containers, arrays, and larger object shapes without weakening D05, the runner must use explicitly declared negative SYN-31 inputs (for example, a single unknown-field mutation containing synthetic nested JSON) and keep their expected parser-only rejection reason outside the parser bytes. The runner tests must prove that the raw bytes are still measured exactly and that the expected D05 rejection is not mistaken for a successful contract validation.

## 4. Proposed synthetic corpus contract for the runner

The following is a proposed *logical inventory*, not generated payloads and not an authorization to create them:

| Case ID | Proposed role | Expected contract result |
|---|---|---|
| SYN-01 | Positive controls; one minimal valid-shape fixture per D10 type (11 fixtures) | Accept D05 structure |
| SYN-29 | Parser-level malformed/duplicate-key controls | Exact parser reason code; no mapping collapse |
| SYN-30 | Unsupported schema-version/purpose controls | Exact D05 reason code |
| SYN-31 | Structural measurement probes using one declared unknown-field mutation per probe; include nested object/array and boundary shapes | D05 rejects with declared schema reason; raw structural dimensions remain measurable |
| SYN-32 | Wrong-type/missing/unknown-field controls | Exact D05 reason code |

Proposed total: 22 fresh fixtures (11 SYN-01 controls plus 11 negative/measurement probes distributed across SYN-29–32). The exact fixture IDs, ordered manifest, D10 mapping, mutation per fixture, raw bytes, and oracle reason codes must be frozen in the runner source and test suite before measurement. No G0.34/G0.37-A payloads, intermediate measurements or digests may be reused.

All `claims` objects must be empty for this first runner version. If non-empty claims are later needed, a separate exact per-case schema decision is required before any generation. Do not infer a claims vocabulary from D10 fixture types.

The corpus must be wholly synthetic: reserved `syn-` identifiers only; no personal/account data, credentials, keys, tokens, production paths, market data, T0/T1/T2 records, models, ledgers, provider evidence or external URLs.

## 5. Required runner acceptance gates

The runner and tests must prove all of the following before G0.41 can be prepared:

1. **Frozen inventory:** exactly 22 unique fixture IDs; exact ordered manifest; exactly the five approved case IDs; all 11 D10 types represented; no extras or omissions.
2. **Oracle separation:** parser-input values are exact UTF-8 bytes; expected reason codes and case/type metadata remain in separate mappings; no oracle serialization or reserved oracle keys enter parser bytes.
3. **D05 outcomes:** every positive control passes; each negative fixture fails with its predeclared exact reason; no expected reason is computed from the actual parser result.
4. **Duplicate handling:** unique-key positive control and top-level/nested duplicate-key negative controls are decisive.
5. **Exact measurement:** byte count uses original bytes; structural metrics traverse pair-preserving parsed values; malformed inputs carry NOT_APPLICABLE dimensions with explicit reasons.
6. **Coverage:** at least one fixture exercises nested object depth, arrays, multiple object members, string value bytes, string key bytes and scalar count. SYN-31 structural probes are deliberately D05-invalid and must remain clearly labeled as such.
7. **Determinism:** two independently constructed passes over the frozen recipe produce identical ordered input bytes, oracle records, per-fixture measurements, aggregate measurements and digest.
8. **A-01–A-13:** every assertion is evaluated by the frozen harness; no literal PASS, missing evidence, default-success path or swallowed exception. Each assertion has a test proving a missing/false input fails closed.
9. **Provenance:** runner source and harness source are bound to exact Git commit/blob SHA-256; the exact command and Python/platform version are recorded.
10. **Report:** one serialized report is read back; duplicate keys rejected; schema validated; aggregate values independently recomputed from rows.
11. **Isolation:** no filesystem writes, fixture files, caches, environment/secret reads, clock reads, network/provider/database/VPS/runtime access or external dependencies. The execution trace is explicit and empty.
12. **No numeric policy inference:** output observations only; no D11 ceiling proposed, selected, ratified or enforced.

Any missing assertion, mismatch, exception, provenance mismatch, non-determinism, or unsafe fixture consumes the future one-attempt authorization if it occurs during the separately approved measurement. Runner implementation tests must catch these conditions before that measurement authorization is requested.

## 6. Scope requested for G0.40-A

**Allowed only after explicit owner approval:**
- Create `tools/s1_measurement_runner.py`.
- Create `tools/test_s1_measurement_runner.py`.
- Update `docs/evidence/` and `docs/PROJECT_SESSION_HANDOFF.md`.
- Implement deterministic in-memory synthetic construction and assertion-evidence orchestration only.
- Run focused tests and compile only.

**Not included:**
- Any corpus generation or measurement attempt outside unit tests.
- Any report containing observed corpus measurements or digest.
- Any numeric D11 ceiling proposal, ratification or enforcement.
- Any modification to `tools/s1_measurement_harness.py` or its tests.
- Parser/verifier production implementation, cryptography, trust profile, keys, registry, adapter or lifecycle evaluator changes.
- CI/workflow changes or dispatch.
- Benchmarking, performance claims or dependency installation.
- Filesystem inventory, network/provider/database/VPS/runtime access.
- T0/T1/T2, canonical data, market data, model, CORE_LEDGER, AI_LEDGER, storage lifecycle or destructive operations.

## 7. Focused commands proposed for G0.40-A

- `python -m unittest tools.test_s1_measurement_runner -v`
- `python -m py_compile tools/s1_measurement_runner.py tools/test_s1_measurement_runner.py`

Acceptance requires all focused tests and compile to pass against the exact committed source. No broader suite or Actions workflow is part of G0.40-A.

## 8. Later G0.41 measurement gate

Only after G0.40-A is implemented, tested, reviewed, and frozen should a separate G0.41 package request:
- one single deterministic in-memory corpus generation + measurement attempt;
- exact frozen runner/harness source identities and command;
- a single execution, two measurement passes within that execution;
- no retry, repair-and-rerun, or reuse of prior failed corpora;
- report-only persistence (no raw corpus/oracle payload files);
- exact output evidence and explicit stop conditions.

A failed/incomplete G0.41 attempt consumes its one-time authorization. No retry without a new owner decision package. Numeric D11 ceilings remain a later, separate owner decision after valid measurement evidence exists.

## 9. Owner decision register

| Decision | Requested disposition |
|---|---|
| G0.40-A runner implementation | PENDING EXPLICIT OWNER APPROVAL |
| D14 amendment for the two runner paths | PENDING; exact-path amendment requested |
| Focused runner tests/compile | Included only if G0.40-A is approved |
| G0.41 one-time measurement | NOT AUTHORIZED; separate package/approval |
| Numeric D11 ceilings | OPEN / NOT RATIFIED |
| Parser/verifier production implementation | NOT AUTHORIZED |
| CI/workflow, external/runtime, T0/T1/T2, ledger or destructive actions | NOT AUTHORIZED |

## 10. Final disposition

**G0.40: REVIEW PACKAGE READY — recommended next decision is G0.40-A runner implementation + narrow D14 path amendment. Measurement remains NOT AUTHORIZED.**

Historical G0.34 and G0.37-A metrics/digests remain NOT VERIFIED for D11 policy use. Their authorizations were consumed and neither attempt may be repaired, rerun or reused. G0.39-B exact-source verification PASS does not change that.

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.
