# T0 A2.2 Stage I — Static Implementation Review

Date: 2026-11-18
Repository: `kenznguyen/btcusdt-telegram-signals2`
Review branch: `feature/core-operational-proof-20261112`
Branch HEAD reviewed: `9491aa89cdaedee5d73fb6a7f7a1d1363c0c22a6`
Review type: read-only static review; no tests executed.

## Scope and pinned inputs

The owner-approved Stage I scope is recorded in commit `b79424ad86b5f4d78da610da3c81c9e90e92fee6`, tied to A2.2 source blob `41d41cd23f73a6e552b9ceca5ebbb39c46934e7d`. It permits only an isolated synthetic/offline harness and explicitly excludes CI/workflow execution absent separate authorization.

Reviewed package blobs:
- `t0_signature_stage1/README.md`: `883f1adcd866b769c3e094e1c0b5167f278733a5`
- `t0_signature_stage1/primitives.py`: `91496d70a67d12525b8399b46aeb1318693b17ee`
- `t0_signature_stage1/tests/test_primitives.py`: `8e47af0bb98cae6e8501c609c97259ebc5e0c78f`
- `t0_signature_stage1/verdicts.py`: `600c49865279e03ef28466f267a6bf0b57176aa1`
- `t0_signature_stage1/tests/test_verdicts.py`: `d37ab48b0455d788bd5c87398281420a7aa121d8`

Workflow blob: `.github/workflows/t0-signature-a2-2-stage-i.yml` `5fa94939181af5f1f33686c3444bc6f8a0326962` (identical on main and review branch).

## Findings

### F-01 — Critical: fixture mutations do not mutate the intended baseline fields

`_BASELINES` defines B0 and B-A using flat/small structures, while `_MUTATION_DEFINITIONS` declares nested paths such as `statement.purpose`, `policy.allowed_purposes`, `verification_request.profile_id`, and `bootstrap.authorization.signature`. `build_fixture()` creates missing intermediate dictionaries rather than requiring the target path to exist. Consequently, many mutations add a new nested leaf while leaving the corresponding baseline semantic field unchanged.

The leaf-diff test can still pass because it checks only that one declared leaf was added/changed; it does not prove the mutation altered the intended pre-existing contract field. This defeats the intended single-semantic-mutation assurance.

Disposition: Stage I fixture conformance **BLOCKED** until every mutation path is bound to a real, schema-shaped baseline field and missing mutation targets fail closed.

### F-02 — Critical: fixture verdicts are not derived from mutated fixture content

`evaluate_stage1_fixture()` obtains a preassigned `fact_key` from the fixture catalog and calls `evaluate_stage1_facts({fixture.fact_key: True})`. It does not evaluate the baseline or mutated fixture returned by `build_fixture()`. Thus, the expected verdict/reason test proves only the manually configured fact-to-verdict table, not that a mutated A2.2 fixture is recognized correctly.

Disposition: the 27-case matrix is **NOT VERIFIED** as a contract-conformance harness. Derive facts from the actual fixture content using explicit validation/routing, or clearly relabel the current matrix as verdict-table unit tests rather than fixture conformance.

### F-03 — Documentation inconsistency: README understates implemented digest helpers

README says Trust Policy, Anchor and Signature Envelope digest helpers fail closed with `DOMAIN_SEPARATOR_ENCODING_UNRESOLVED`, and only Evidence Object digest is implemented. However, `primitives.py` defines all four exact domain constants from §20.1 hex and implements all four digest helpers; tests include four fixed digest vectors and exact domain-byte assertions.

The source implementation appears aligned with the owner-approved §20.1 byte clarification, while README describes the earlier ambiguity. Update documentation only after verifying the exact current A2.2 contract dependency; this is a documentation mismatch, not evidence that the code should fail closed.

### Positive bounded observations

- `primitives.py` uses exact domain byte strings ending in one NUL, U64BE length-prefixing, canonical U64 decimal parsing, unpadded base64url round-trip validation, duplicate-key rejection, UTF-8 strict decoding, safe-integer bounds, and UTF-16BE key ordering.
- The mock verifier is explicitly labelled `MOCK / NOT CRYPTOGRAPHIC` and emits only `MOCK_ACCEPTED` / `MOCK_REJECTED`.
- The verdict router has no positive bootstrap acceptance path; default is BLOCKED.
- The inspected package imports do not show network/database/process integrations in the package source. This is a bounded static observation, not a full sandbox proof.
- The workflow is manual-only (`workflow_dispatch`), has read-only contents permission, clears DB/exchange credential environment variables, and sets `AI_EXECUTION_ENABLED=false`. It checks out `github.sha` but does not assert the approved A2.2 source blob SHA. Workflow execution remains unauthorized by the Stage I owner decision.

## Verification and safety

- Static source review: **COMPLETE for the five listed package files and workflow**.
- Tests: **NOT RUN** (no test/CI execution in this review).
- Workflow dispatch: **NOT RUN / NOT AUTHORIZED**.
- Exact approved A2.2 source-blob runtime assertion: **NOT PRESENT** in workflow; workflow checkout SHA alone does not prove the contract blob binding.
- No source, test, workflow, runtime, VPS, credentials, T0 canonical data, exchange or trading state changed.
- No merge, rebase, reset, cherry-pick, force-push or deployment performed.

## Overall disposition

**BLOCKED / NOT READY TO CLAIM STAGE I CONTRACT-CONFORMANCE PASS.**

F-01 and F-02 undermine the core fixture acceptance criteria. F-03 is a documentation mismatch. Positive primitive observations do not compensate for the fixture/evaluation defects. No test pass, cryptographic assurance, bootstrap, anchor, custody, anti-rollback or production readiness is claimed.

## Required next steps

1. Correct the fixture baselines so every declared mutation path already exists at the intended semantic location; reject missing paths.
2. Make fixture evaluation derive verdict facts from the actual mutated fixture, not the catalog's preassigned expected fact key.
3. Add regression tests that fail if a mutation adds a new unrelated leaf or if the evaluator ignores the mutated content.
4. Reconcile README digest statements with A2.2 §20.1 and the implementation.
5. Separately decide whether workflow should enforce the approved A2.2 blob identity. Do not dispatch without explicit authorization.

Any implementation change requires the appropriate scoped authorization and exact-SHA validation. Stages II–V remain BLOCKED / NOT APPROVED.
