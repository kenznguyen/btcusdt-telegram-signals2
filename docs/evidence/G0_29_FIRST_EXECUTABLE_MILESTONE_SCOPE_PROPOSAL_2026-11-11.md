# G0.29 — First Executable Milestone Scope Proposal

Date: 2026-11-11 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Baseline HEAD: `842b6aed7cf71e9681b227a1a14b3cb5a4e339db`
Baseline handoff blob: `d3b424a5aecd08baee554285ecf1009d2e802ec8`
Type: documentation-only milestone proposal
Disposition: **PROPOSAL PASS — S1 RECOMMENDED AS THE FIRST EXECUTABLE MILESTONE; S1 IMPLEMENTATION/TEST EXECUTION NOT AUTHORIZED BY THIS REPORT**

## 1. Purpose and decision boundary

G0.29 compares two candidate first executable milestones:

- **S1:** deterministic synthetic parser/contract tests without cryptography.
- **S2:** synthetic cryptographic verifier tests using isolated test-only keys.

The owner approved preparation of this scope proposal. That approval covers the proposal and its documentation only. It does not authorize implementation, test execution, workflow changes, key generation, signing, network/provider access or runtime work.

## 2. Executive recommendation

**Recommend S1 first. Defer S2 until S1 is complete and its contract boundaries are accepted.**

S1 has the lower decision and implementation surface. It can test strict parsing, schema validation, exact subject/version binding, bounded input handling, explicit fail-closed behavior and deterministic outputs without choosing a real cryptographic profile or creating keys.

S2 introduces cryptographic profile, canonicalization, test-key lifecycle, trust configuration and verified-facts binding concerns before the non-cryptographic contract has been proven stable. It has higher assurance value for cryptographic code, but a larger dependency surface and greater risk of accidentally implying a production trust model.

S1 is therefore the safer first executable increment, provided it makes no authenticity claim and cannot produce a production-usable VERIFIED result.

## 3. Candidate comparison

| Dimension | S1 — Synthetic parser/contract tests | S2 — Synthetic cryptographic verifier tests |
|---|---|---|
| Primary objective | Prove deterministic parsing and contract enforcement | Prove signature/digest verification behavior under a selected test profile |
| Minimum decision dependencies | D05, D10, D11, D14 | D01–D05, D10–D11, D13, D14; D03–D04 scoped to test-only trust/key lifecycle |
| Cryptographic algorithm decision | Not needed; cryptographic fields must be treated as opaque/rejected unless schema explicitly marks them as inert test data | Required for executable signature verification |
| Canonical signed-byte profile | Not needed if no cryptographic verification or canonical-signature claim is made | Required |
| Test keys | None | Test-only synthetic keys and strict isolation required |
| Main test targets | malformed/ambiguous JSON, duplicate keys, missing/unknown critical fields, version mismatch, type/range limits, exact subject binding, deterministic fail-closed outcomes | valid/invalid signatures, wrong key/issuer/purpose/subject, altered payload, unsupported algorithm, key scope, replay and trust-policy failures |
| Assurance established | Parser and contract behavior only | Cryptographic implementation behavior under synthetic test trust only |
| Assurance NOT established | Issuer authenticity, real-source truth, owner authorization, production completeness/custody | Real-world issuer authenticity, production trust-root security, real-source truth, owner authorization, completeness/custody |
| Complexity / risk | Lower | Higher |
| Recommended order | First | After S1 and a separate S2 approval |

## 4. Proposed S1 scope

### 4.1 In-scope capabilities

1. A bounded, deterministic synthetic input representation for the G0.23 cases selected for parser/contract coverage.
2. Strict parser contract: reject duplicate keys, malformed encodings, invalid types, unsupported versions and ambiguous security-relevant values.
3. Closed required-field contract and explicit handling of unknown critical fields.
4. Exact subject/object/version and purpose-field shape validation, without asserting that the claimed identity or authority is authentic.
5. Bounded limits for input bytes, nesting, arrays, strings and diagnostic output, selected from measured fixture bounds before implementation.
6. Pure deterministic validation outcomes with stable reason codes.
7. Synthetic-only test cases derived from G0.23; no real evidence payloads or production identities.
8. Tests that prove fail-closed behavior for missing, stale-shaped, contradictory, malformed and unsupported inputs. “Stale-shaped” means invalid/missing freshness metadata only; S1 does not establish actual freshness.

### 4.2 Explicitly out of scope

- Signature verification, signing, digest-profile selection and cryptographic canonicalization.
- Real issuer authentication, trust roots, issuer delegation and real key lifecycle.
- Real evidence-source adapters or claims about GitHub/provider/source truth.
- Production inventory completeness, hold/dependency/copy/replica closure.
- Freshness, trusted clock, revocation or anti-replay guarantees beyond structural field validation.
- Owner/steward authentication or authorization.
- Custody, retention, tamper-evident audit or independent readback.
- A production verified-facts token/handle or cross-process trust boundary.
- Lifecycle disposition authority, archive, quarantine, cleanup, expiry, compaction, VACUUM or deletion.
- Any T0/T1/T2, market-data, model, ledger, trading, VPS or runtime change.

S1 output must be named and documented as **synthetic contract validation only**, never as proof of issuer authenticity or lifecycle eligibility. It must not be consumable as an authorization token by the lifecycle evaluator or any executor.

## 5. S1 decision closure required before implementation

| Decision | Minimum S1 closure |
|---|---|
| D05 — Schema/versioning | Owner/security ratify a synthetic-only schema version, required fields, duplicate/unknown-field policy and compatibility behavior |
| D10 — Data-class vocabulary | Owner ratifies a tiny explicit synthetic fixture class allowlist; no production class mapping inferred |
| D11 — Resource limits | Engineering proposes measured fixture-based bounds; owner/security accepts exact values before implementation |
| D14 — Stage gate | Explicitly authorize S1 implementation/test scope, permitted files, test command/CI permissions and acceptance evidence |

D01–D04, D06–D09, D12 and D13 remain OPEN and are not needed only because S1 excludes the claims and capabilities that depend on them. They remain blockers for S2/S3/S4 and any later stage that relies on those claims.

## 6. Proposed S1 acceptance criteria

S1 may be considered complete only when all are evidenced:

1. Every selected synthetic case maps to a stable test ID and expected result.
2. Parser rejects malformed, ambiguous, duplicate-key and unsupported critical input.
3. Schema validation rejects missing, wrongly typed, out-of-range and unsupported-version fields.
4. Subject/version/purpose fields are bound structurally and cannot be silently substituted between test cases.
5. Input limits are enforced before unbounded allocation or traversal.
6. Identical inputs produce identical validation outcomes and stable reason codes.
7. All negative cases fail closed; no malformed or incomplete case becomes an accepted synthetic contract.
8. Test output explicitly states that authenticity, owner authorization, freshness, completeness, custody and lifecycle eligibility were not verified.
9. No network, provider, database, filesystem inventory, key store or VPS/runtime dependency is introduced.
10. CI, if separately authorized, uses least-privilege read-only permissions and records exact checkout SHA, workflow run, job result and artifact digest.
11. No code path converts S1 success into a lifecycle evaluator VERIFIED/REVIEWABLE result or execution permission.

## 7. S2 entry gate after S1

S2 should be considered only after S1 acceptance and a separate owner approval. Before S2:
- D01 must select an exact synthetic cryptographic profile and statement binding.
- D02 must select canonical bytes and strict parser/canonicalization rules.
- D03 must define a test-only trust root and narrowly scoped test issuer authority, isolated from production.
- D04 must define test-key generation, storage, access and destruction boundaries.
- D05 must extend the schema to bind the cryptographic statement.
- D13 must define verified-result subject/evaluation binding and anti-replay semantics.
- D14 must authorize the exact synthetic cryptographic test stage.

No production keys, real trust roots or real issuer integration are part of the proposed S2 scope. A successful S2 test would prove only implementation behavior under the synthetic test profile.

## 8. Implementation and evidence workflow — not yet authorized

If S1 is later authorized, the work should follow the repository's existing branch and evidence process:

1. Record exact implementation scope and permitted paths.
2. Establish failing synthetic tests first, then implement only the minimum parser/contract behavior.
3. Run focused tests and compile/type checks as applicable.
4. Record exact source/test blobs and commit SHA.
5. Use a dedicated least-privilege CI workflow only if explicitly included in the S1 authorization.
6. Record workflow run, job, artifact ID/digest and expiry where applicable.
7. Perform focused code review and update the session handoff with PASS/BLOCKED/NOT VERIFIED.
8. Do not merge, deploy or advance to S2 without separate approval.

This section is a proposed process only; no implementation or test has been started by G0.29.

## 9. Decision requested from owner

The recommended next owner decision is narrowly scoped:

**Approve or modify the S1 scope and its D05/D10/D11/D14 decisions before any implementation.**

A suitable approval must specify:
- S1 only, synthetic parser/contract tests without cryptography;
- exact schema/class/resource-limit values to be ratified;
- permitted source/test/workflow paths and whether CI changes are included;
- allowed local/CI test commands;
- acceptance criteria and evidence required.

If these are not explicitly approved, S1 remains proposal-only. “Continue” does not authorize implementation.

## 10. Final verdict

**G0.29: PROPOSAL PASS — S1 is recommended as the lower-risk first executable milestone; S2 is deferred until S1 acceptance and separate approval. No D01–D14 decision is ratified by this proposal. No implementation, tests, workflow dispatch, keys, signatures, source adapters, runtime access or lifecycle action is authorized.**

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.
