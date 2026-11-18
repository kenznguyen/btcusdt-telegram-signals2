# T0 A2.2 Stage I — R1–R5 Contract-Semantic Repair

Date: 2026-11-18
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/core-operational-proof-20261112
Reviewed/tested source HEAD: 64b859e6b5fbbb45e4f764cfc7af22c1e0d57667
Governing A2.2 specification blob: d9f93bf390d107381b7135c3073aeca0d14894d4
Scope: only t0_signature_stage1/verdicts.py and t0_signature_stage1/tests/test_verdicts.py.

## Authorization

Owner explicitly approved the narrow R1–R5 repair in the two Stage I files and isolated tests. Work remained on the existing branch. No workflow dispatch, CI run, README change, runtime integration, cryptographic production implementation, T0/VPS access, credentials, exchange, deployment or trading action was authorized or performed.

## TDD evidence

- RED test commit: 0a2c823b2d823c64353fd4b4805c918084603a48.
- RED was executed against that exact commit before implementation. New regression cases failed as expected: NV-03/NV-04 fields absent, zero-mutation accepted, normative binding locations rejected, and fixture schema/dimension/state evidence missing.
- Final GREEN tested source SHA: 64b859e6b5fbbb45e4f764cfc7af22c1e0d57667.
- Final source blobs:
  - verdicts.py: 6f3af6288dec3dc23f01a297b80467aa03515663
  - tests/test_verdicts.py: 2d4a44eecaccce26329c0ed98e30d2fd8a6a6812
- Final exact-SHA source was fetched from the public repository into an isolated ephemeral Python sandbox and tested there.

## Repairs and dispositions

### R1 — NV-03 historical profile scenario: PASS

- Removed the label-trigger design based on `subject_fixture == A1_HISTORICAL`.
- The immutable A1 historical object is represented separately with its own object ID and A1 profile ID/version.
- NV-03 changes only the verifier request's `subject_object_id` to that unchanged historical object while the request explicitly selects the A2.2 V2 `signature_profile_id/signature_profile_version`.
- The evaluator derives `PROFILE_VERSION_MISMATCH` from the actual request/object profile mismatch.
- Regression asserts the historical object is byte-for-byte/equality unchanged and there is no `subject_fixture` label field.

### R2 — normative profile field names and binding locations: PASS for modeled contract structure

- Replaced `profile_id/profile_version` aliases with `signature_profile_id/signature_profile_version`.
- Modeled and checked nine locations: descriptor, statement, detached envelope, Trust Policy profile authorization, Trust Policy signed binding, bootstrap record, bootstrap authorization, verifier request, and verifier-local allowed-profile configuration.
- B0-PF now has only the pre-existing statement profile ID mismatch: LEGACY ID, V2 version; the other applicable profile locations retain V2.
- NV-20 now mutates `bootstrap_record.signature_profile_id` and reaches `ROOT_BOOTSTRAP_PROFILE_MISMATCH` through the §17 bootstrap rule, rather than a duplicate shorthand string.
- Profile binding regression checks all nine locations and fails closed when a required location is absent or differs.

### R3 — exactly one semantic mutation: PASS

- Evaluator now rejects zero changed leaves and compound/multiple changes.
- Added regression for zero mutation and retained compound mutation rejection.
- State snapshot changes are independently rejected as `FIXTURE_STATE_TRANSITION_FORBIDDEN`.

### R4 — fixture/evidence/dimension/state assertions: PARTIAL

Implemented and tested:
- Explicit fixture schema version and canonical baseline digest per case.
- Canonical Evidence Object with object ID, type, schema, canonical bytes, byte length and domain-separated digest; evaluator verifies canonical bytes, byte length and digest.
- Separate synthetic test signer and Trust Policy authorization metadata binding signer ID/role, namespace, audience, purpose and profile.
- Per-dimension result map for parsing/canonicalization, object binding, profile, purpose, signature, policy authorization, bootstrap authorization and custody/readback.
- S0 is represented in each baseline and compared with the supplied state snapshot; S1 is recorded and asserted equal to S0.
- Explicit forbidden-transition assertions for root enrollment, policy-head advancement, anchor-head advancement, checkpoint acceptance, sequence reservation and durable trust-state write.
- Regression tests reject malformed Evidence Object digest, object-binding mismatch and state snapshot mutation.

Limits that remain explicit:
- Signature dimension is `NOT_VERIFIED`; the mock verifier and synthetic signature markers are not cryptographic verification.
- Custody/readback dimension is `NOT_VERIFIED`; no live or durable readback is performed.
- Trust Policy signed-binding marker/digests are synthetic fixture metadata, not proof of a valid policy signature.
- Bootstrap authorization predicates are deterministic synthetic routing checks only; B-A is hypothetical and does not enable Path A.
- Therefore R4 is not a claim of full §18.1/§18.4 cryptographic or operational conformance.

### R5 — independent contract-row oracle: PASS for verdict/reason routing

- Added a hard-coded 27-row oracle in tests, separate from the fixture catalog's expected verdict fields.
- All 27 catalog rows and actual evaluator outputs must match the exact A2.2 §18 verdict/reason pairs.
- Added focused semantic regressions for NV-03, NV-04 and NV-20, all profile binding locations, zero/compound mutations, state immutability and canonical Evidence Object validation.

## Exact verification

Commands executed on exact source SHA `64b859e6b5fbbb45e4f764cfc7af22c1e0d57667`:
- `python -m compileall -q t0_signature_stage1`: PASS.
- `python -m unittest t0_signature_stage1.tests.test_verdicts -v`: 28 tests PASS.
- `python -m unittest discover -s t0_signature_stage1/tests -p 'test_*.py' -v`: 51 tests PASS.

This was an isolated ephemeral Python test sandbox run, not GitHub Actions. No workflow run ID or artifact exists. No CI dispatch was performed.

## Source-scope and safety verification

- GitHub compare from pre-repair review/handoff HEAD `b607a948be2347c4f2c6ba80856864a3076d4f75` to tested source HEAD reports 23 commits ahead, 0 behind, and exactly two changed paths:
  - `t0_signature_stage1/verdicts.py`
  - `t0_signature_stage1/tests/test_verdicts.py`
- All commits are sequential on the existing branch; no new branch or PR was created.
- No README, workflow, production crypto, key management, trust-root enrollment, durable policy/anchor state, T0 canonical data, VPS/runtime, credentials, exchange or trading files were changed.
- No merge, rebase, reset, cherry-pick, force-push or history rewrite occurred.

## Final disposition

| Item | Status |
|---|---|
| R1 NV-03 semantic scenario | PASS |
| R2 profile field names and modeled bindings | PASS |
| R3 exactly-one-mutation and S0/S1 guard | PASS |
| R4 fixture metadata/dimensions/state | PARTIAL — crypto and custody/readback NOT VERIFIED |
| R5 independent 27-row verdict/reason oracle | PASS |
| Focused tests | PASS — 28/28 |
| Stage I package tests | PASS — 51/51 |
| Stage I full contract conformance | PARTIAL / NOT VERIFIED |
| F-03 README digest-helper inconsistency | OPEN / NOT RESOLVED |
| Workflow dispatch / CI | NOT RUN / NOT AUTHORIZED |
| Stages II–V | BLOCKED / NOT APPROVED |
| Merge / deployment / trading | NOT AUTHORIZED |

## Next step

Perform a fresh read-only review of the exact final two-file diff and the updated Stage I report. Handle F-03 README consistency as a separate documentation-only increment if approved. Do not dispatch the manual workflow or proceed to Stages II–V without separate explicit authorization.
