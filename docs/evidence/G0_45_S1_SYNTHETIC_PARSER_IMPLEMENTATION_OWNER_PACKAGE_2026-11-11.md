# G0.45 — S1 Synthetic Parser Implementation Owner Package

Date: 2026-11-11 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Baseline HEAD: `6a8491526dceceeabfdb048a5621bf2f2e273809`
D11 controlling decision: `docs/evidence/G0_44_D11_MEASURED_RESOURCE_LIMITS_RATIFICATION_2026-11-11.md` (blob `432e7c544efe0234a6acce2a67e2f9a91c4588c1`)
D14 controlling decision: `docs/evidence/G0_31_OWNER_RATIFICATION_S1_DECISIONS_2026-11-11.md` (blob `541692cae4cfabf78897d91d9681c6601f000e1e`), as narrowly amended for G0.41–G0.43 only
Type: documentation-only owner authorization package
Disposition: **READY FOR OWNER DECISION — IMPLEMENTATION NOT AUTHORIZED**

## 1. Purpose

D11 is complete. Its measured numeric ceilings and fail-closed structural requirements are ratified, but enforcement is not implemented or verified. G0.45 requests a separate, exact owner authorization to implement only the synthetic S1 parser contract already defined by D05/D10/D14, incorporating D11 ceilings.

This is not a production evidence verifier, cryptographic verifier, trust engine, lifecycle evaluator or execution component. A successful parse means only that a synthetic test fixture satisfies the bounded parser contract.

## 2. Exact scope requested

If explicitly approved, permit changes only to:

1. `pipeline/synthetic_contract.py` — new pure, deterministic, in-memory synthetic contract parser/validator.
2. `pipeline/test_synthetic_contract.py` — new focused unit tests with inline synthetic bytes only.
3. `docs/evidence/G0_45_S1_SYNTHETIC_PARSER_IMPLEMENTATION_RESULTS_2026-11-11.md` — result/evidence record.
4. `docs/PROJECT_SESSION_HANDOFF.md` — append the milestone and exact evidence.

No standalone fixture corpus or payload files. No dependency additions. No other source/test/config/workflow changes.

## 3. Binding contracts

### 3.1 D05 / D10

Implement the exact Synthetic Contract Fixture v1 contract and closed 11-value D10 `fixture_type` allowlist from G0.31. Enforce exact top-level and closed nested key sets, exact types without coercion, schema-version and purpose literals, reserved synthetic identifier patterns, and explicit rejection of unknown critical fields. Keep oracle metadata outside parser input; the parser accepts only raw fixture bytes and returns a bounded parse/contract result.

The `expected` oracle field is test-harness metadata, never a parser claim and never an input to the parser. Do not infer trust, authenticity, evidence truth, inventory completeness, freshness, sensitivity, lifecycle eligibility, authorization or execution permission.

### 3.2 D11 exact ceilings

Enforce these per-fixture limits exactly:

| Dimension | Ceiling |
|---|---:|
| Raw input | 8,192 bytes |
| Container nesting depth | 8 levels; root object/array = level 1 |
| Object members | 32 per object |
| Array items | 64 per array |
| String value | 1,024 UTF-8 bytes per value |
| String key | 256 UTF-8 bytes per key |
| Scalar nodes | 256 per fixture |
| Diagnostic reason codes | At most 1 fixed code per invalid fixture |

Check raw byte length before UTF-8 decoding or JSON parsing. Use strict UTF-8. Reject malformed JSON, duplicate keys at every object depth, non-finite numbers, invalid Unicode scalar sequences, trailing non-whitespace content, unknown fields, wrong types and any exceeded ceiling. Duplicate-key detection must inspect original parser input, not a mapping after duplicate collapse.

No truncation, normalization, coercion, silent field dropping, partial acceptance, raw-input echo, secret/oracle echo, arbitrary parser excerpts or multi-code diagnostics. For malformed UTF-8/JSON, do not claim structural metrics. Return one stable fixed reason code only.

### 3.3 D14 exact implementation boundary

The original D14 paths remain the only source/test paths:

- `pipeline/synthetic_contract.py`
- `pipeline/test_synthetic_contract.py`

Evidence and handoff updates are permitted as already ratified. This package requests implementation authorization only for those two paths plus the two evidence paths listed in Section 2. It does not amend any other D14 scope.

## 4. Test-first and verification plan

Use test-driven development:

1. Add focused tests first for valid fixture, each D05 rejection, each D10 allowlist value, duplicate keys at top-level and nested levels, invalid UTF-8/JSON, non-finite numbers, invalid Unicode scalar sequences, trailing data, unknown fields, exact-type rejection, each exact D11 boundary and one-over-boundary case.
2. Demonstrate RED against the absent/unimplemented parser module without weakening or skipping tests.
3. Implement the smallest pure parser/validator that makes the focused tests pass.
4. Run only:
   - `python -m unittest pipeline.test_synthetic_contract -v`
   - `python -m py_compile pipeline/synthetic_contract.py pipeline/test_synthetic_contract.py`
5. Review the exact diff and prove no I/O, network, environment, clock, secret, database, filesystem, T0/T1/T2, model, ledger, risk-engine, execution or runtime side effects.

Acceptance requires exact boundary tests at limit and one unit over for every D11 dimension; duplicate detection before mapping conversion; strict UTF-8 and JSON behavior; oracle/input separation; deterministic output; no more than one fixed reason code; no raw input echo; all focused tests and compile checks passing; exact source/test blob SHAs and commit recorded.

If the focused RED test cannot be demonstrated because the test runner/import environment is unavailable, record RED as NOT VERIFIED; do not claim TDD RED PASS. No test may be skipped to manufacture a pass.

## 5. Explicit exclusions

Not authorized by this package:

- Any implementation or change to `pipeline/lifecycle_disposition.py`, its tests, evaluator, verifier, trust/verified-facts envelope, authorization or executor.
- S2, cryptography, signatures, keys, trust roots, issuer authority, revocation, freshness, registry, production source adapters or real evidence.
- Any workflow/CI change, workflow dispatch, dependency installation, broad repository test suite, benchmark or build.
- T0/T1/T2, canonical market data, market/model/training/inference, CORE_LEDGER, AI_LEDGER, Shared Risk Engine, Kill Switch, PostgreSQL, VPS, deployment, service/runtime changes, external provider/network/database/exchange access.
- Any retention, cleanup, archive, expiry, compaction, VACUUM, deletion or other destructive lifecycle operation.
- Live trading or real orders; paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.

## 6. Owner decision requested

Please explicitly approve or reject this complete G0.45 package. A generic continuation request is not implementation approval. If approved, authorization is limited to the exact four paths, tests and commands in this package. Any scope expansion, acceptance failure requiring out-of-scope changes, or new CI/runtime requirement returns for a separate owner decision.

**Current verdict: G0.45 READY FOR OWNER DECISION. S1 parser implementation, test execution and source changes remain NOT AUTHORIZED.**
