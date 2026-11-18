# T0 A2.2 Stage I — R4 Fixture Integrity Hardening

Date: 2026-11-18
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/core-operational-proof-20261112

## Authorization and scope

Continued the previously owner-approved R1–R5 repair scope: only `t0_signature_stage1/verdicts.py` and `t0_signature_stage1/tests/test_verdicts.py`; mock-only/offline. No README, workflow, runtime, production cryptography, keys, trust-root enrollment, policy/anchor persistence, T0 canonical data, VPS, credentials, exchange, deployment or trading changes.

## TDD and exact Git evidence

- RED test commit: `67782da56fb15e536e94535243a3e632350cbad2`.
- RED run was executed against the exact branch state after that test commit and before implementation: 29 tests; expected failure (30 subtest failures and 66 errors) because the independent pins and separated state contract were not implemented. This is a deliberate RED result, not a final test failure.
- Final exact tested source HEAD: `fcb188c6d0c215d5e753bad7ef5b6aeb9facad93`.
- Final blobs:
  - `verdicts.py`: `83b56d633d146f5b4df30e5c85943ab08ef7e7ca`
  - `tests/test_verdicts.py`: `9c0e487be74430bd70b8ca90e9d573fe3ea41136`
- Test sandbox fetched the public HTTPS branch archive and confirmed branch HEAD `fcb188c6d0c215d5e753bad7ef5b6aeb9facad93` before executing tests.

## R4 repairs

### 1. Independently pinned baseline identity

Added literal expected SHA-256 digests for the canonicalized B0, B0-PF and B-A baseline fixtures in source, and an independent duplicate oracle in tests:

| Baseline | SHA-256 of canonical baseline |
|---|---|
| B0 | `6f0da5da65d0892cfcb913cc7aeb46df966eedadd26281da64885302d0232cd7` |
| B0-PF | `3137e4a63a19398469f7d8b27b5fecc71d573cd43d954ed7e76e4124c4a6b223` |
| B-A | `4a75faea129d1029cbfc1f1b548b9ac5735971289522cebc7913cbd3d9f774b0` |

`fixture_catalog()` now recomputes each canonical baseline digest and fails closed on mismatch rather than treating a digest derived from the same current baseline as an independent identity. Regression test mutates B0 and confirms catalog construction rejects the drift.

### 2. Explicit signer material vs bootstrap-root state

- Replaced ambiguous `trust_roots` state with separate `bootstrap_roots` and `test_signer_trust_material`.
- All B0/B0-PF/B-A snapshots now explicitly have `bootstrap_roots=[]`.
- The synthetic checkpoint signer fingerprint is recorded only in `test_signer_trust_material`.
- `StageStateSnapshot` and evaluator comparisons validate both fields independently.
- Tests assert no bootstrap root is enrolled in any fixture and that test signer material remains separately identified.

This is fixture-model clarity only. It does not enroll or provision any real or production trust root.

## Verification

Exact source SHA `fcb188c6d0c215d5e753bad7ef5b6aeb9facad93`:
- `python -m compileall -q t0_signature_stage1`: PASS.
- Focused `test_verdicts.py`: 30/30 PASS.
- Full Stage I package discovery `test_*.py`: 53/53 PASS.

Execution was in an isolated Firecrawl-hosted Python sandbox after downloading the public HTTPS branch archive. It was not GitHub Actions. No workflow run ID or artifact exists. No CI dispatch was performed.

## Review and disposition

- Correctness: baseline drift now fails closed; fixture trust state is explicit and matches the A2.2 B0 distinction.
- Readability/architecture: two explicit state fields replace the ambiguous aggregate `trust_roots` field; no new dependency.
- Security: no production trust, key, network or runtime behavior introduced.
- Performance: only three small canonical baseline hashes are recomputed while constructing the fixture catalog; bounded and negligible.
- Scope: exactly the two previously authorized Stage I files changed.

| Item | Status |
|---|---|
| Independent baseline pins | PASS |
| Baseline drift fail-closed regression | PASS |
| Test signer / bootstrap-root separation | PASS |
| Focused tests | PASS — 30/30 |
| Stage I package tests | PASS — 53/53 |
| R4 overall | PARTIAL — signature verification and custody/readback remain NOT VERIFIED |
| Stage I full contract conformance | PARTIAL / NOT VERIFIED |
| GitHub Actions / artifact | NOT RUN |
| Workflow dispatch, Stages II–V, production crypto/bootstrap, merge, deployment, trading | NOT AUTHORIZED |

## Next step

Fresh independent static review of this R4 diff and exact-SHA test evidence. Do not infer cryptographic signature validity or custody/readback from fixture results. Keep the manual workflow undispatched unless separately authorized.
