# G0.53 — S2 Synthetic Verifier Contract Owner Decision Package

Date: 2026-11-11 (Asia/Ho_Chi_Minh)
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/t0-centralized-data-feeder-p1-20261101
Baseline HEAD: d9baed38bad73c0d39c88f233b0f254a669a07a2
Controlling handoff blob: 6e029acbcd8f833b224c2bb981b332eefdaa7c5f
Related audit: G0.52, blob 9e716bd4903892ec338c37b6c59987204d42f6b4
Type: documentation-only Owner decision package
Status: **READY FOR OWNER DECISION — NOT RATIFIED; S2 IMPLEMENTATION NOT AUTHORIZED**

## 1. Purpose and boundary

G0.52 found that D01–D04, D11 and the implementation details of D13 are not sufficiently closed for S2. This package presents a narrow synthetic-only contract decision. It does not implement code, tests, fixtures, schemas, dependencies, workflows or keys.

The proposed first S2 increment is deliberately **byte-integrity-only**, not issuer authentication, not production trust, and not a lifecycle executor. This is the recommended minimum path because D01 defaults to exact-byte SHA-256, D02 keeps opaque bytes exact, D06 defers autonomous issuer authenticity, D04 defers key custody, and D08 provides no trusted freshness anchor.

## 2. Proposed S2 claim boundary

If the Owner approves the recommended path, S2 may claim only:

- the verifier received a bounded byte string;
- the verifier recomputed SHA-256 over those exact bytes;
- the recomputed digest matched an independently pinned expected digest in a synthetic test vector;
- the verifier evaluated a specific synthetic evidence set against an explicit test-only contract/policy version;
- the result is bound to exact subject/evidence/policy/verifier/evaluation identifiers and cannot be modified by the caller.

S2 must NOT claim:

- who produced the bytes or whether a real issuer is authentic;
- source provenance, factual truth, completeness of a real inventory, custody continuity or readback outside the tested fixture;
- freshness, latestness, anti-replay, non-revocation or trusted time;
- Owner cryptographic identity, privileged authorization or production trust;
- authorization to delete, retain, archive, expire, deploy, trade or execute any action.

The term “verified” in any S2 output must be qualified as **synthetic byte-integrity verification only**. Avoid a generic `trusted=true` field.

## 3. Owner decisions requested

### D01-S2 — Integrity only or issuer-signature verification

**Option A — recommended: exact-byte integrity only.**

- Use SHA-256 over the exact opaque input bytes.
- Expected digest comes from a source-pinned synthetic test vector/manifest, not from an untrusted claim in the same payload being checked.
- No DSSE, Ed25519, signature verification, issuer identity, signing keys or signature trust policy in this S2 increment.
- Issuer authenticity is explicitly excluded and deferred to a later separately approved stage.

**Option B — signature-verification tests.**

- Add a test-only DSSE + Ed25519 profile with a fixed domain-separated statement and deterministic test vectors.
- Requires separately defined test-only key generation/use/disposal, trust topology, statement schema/canonicalization, key identifiers, negative vectors and signature resource limits.
- Still does not prove real issuer authority or production trust.
- More dependencies and attack surface; not recommended for the first S2 increment.

**Owner selection required:** A or B, or another explicitly bounded alternative.

### D02-S2 / D05-S2 — Bytes, schema and version

For Option A:

- Evidence subject bytes remain opaque and are hashed exactly; no canonicalization is applied to opaque evidence.
- The verifier request/result envelope is a new S2-only versioned contract, separate from S1 Synthetic Contract Fixture v1.
- Structured S2 metadata must have a closed field set, exact primitive types, explicit schema/version and strict duplicate/unknown-field rejection.
- Do not introduce RFC 8785 JCS unless a later signed structured statement actually requires deterministic canonical bytes.
- The S2 contract must define how the expected digest is pinned outside the payload under test, how evidence ordering is represented, and how absent/unknown claim dimensions are represented.

For Option B, additionally define the exact DSSE payload type/domain separation, statement fields, canonicalization profile (JCS only if structured JSON is selected), signature encoding, key reference semantics and test vectors. No default is implied.

**Owner selection required:** approve a new S2-only envelope contract with Option A, or specify the additional Option B schema requirements.

### D03-S2 / D04-S2 — Trust topology and test-key lifecycle

For recommended Option A:

- No trust root, issuer key, Owner key, signing key, test key, KMS/HSM or external provider is needed or authorized.
- No key generation, import, storage, signing, verification, rotation, revocation or custody operation.
- No network access or production trust configuration.
- Test vectors use fixed synthetic bytes and independently pinned SHA-256 digests.

If Option B is selected, require a separate test-only key decision before any key operation: ephemeral or fixed test key strategy, generation source, private-key isolation, permitted use, non-exportability expectations where applicable, destruction/disposal, no reuse outside tests, and public-key trust pinning. The decision must expressly prohibit real/production keys, external KMS/HSM, provider custody and network access.

**Owner selection required:** A (no keys) or B (separate key decision required before key work).

### D13-S2 — Immutable verifier-created result

Proposed result is an immutable, versioned value created only by the verifier after successful validation. It is not accepted from caller-provided dictionaries or booleans.

Minimum bound fields proposed:

- result schema/version and explicit assurance label, e.g. `SYNTHETIC_BYTE_INTEGRITY_ONLY`;
- unique evaluation ID;
- exact subject ID/type/version;
- exact evidence-set identifier and ordered evidence references;
- each evidence item's exact byte length and recomputed SHA-256 digest;
- expected digest reference and its pinned test-vector/manifest identity;
- explicit claim dimensions and statuses, with UNKNOWN/NOT_EVALUATED kept distinct from PASS/FAIL;
- policy/contract version and digest;
- verifier implementation/build/source identity;
- evaluation result and fixed reason code(s), without raw payload echo;
- explicit `execution_authorized=false` or equivalent non-authority declaration.

The result must not contain a generic `trusted=true`. Consumers must reject subject/evidence/policy/purpose/evaluation mismatch, duplicate/reordered evidence where order is contractually significant, unknown schema/claim state, cross-subject reuse and caller mutation. The verifier's result-construction capability must not be exposed as a public arbitrary constructor.

This package does not choose a programming-language class, serialization format, API, IPC mechanism, process boundary or production adapter. Those belong to the exact implementation package after this contract is ratified.

**Owner selection required:** approve this minimum binding set or amend exact fields/semantics.

### D11-S2 — Resource limits and measurement

- Do not inherit S1 parser ceilings as S2 verifier ceilings without measurement.
- First measure the approved synthetic corpus and actual serialized inputs using a frozen, source-pinned harness.
- Record raw and structured input sizes, evidence count, nesting/member/array bounds, digest count, worst-case execution time, peak memory where measurable, and error-path behavior.
- Propose conservative ceilings with safety margin only after measurements; Owner must ratify numeric limits before implementation.
- Until ratified, no S2 parser/verifier may process real evidence. Oversize, timeout, malformed input or resource exhaustion must fail closed without partial verified output or raw payload/secret echo.

**Owner selection required:** approve measurement-first; numeric ceilings remain OPEN pending a later evidence-backed decision.

### D14-S2 — Stage gate

If this contract is ratified, it authorizes only preparation of a separate exact-scope implementation package. It does not authorize implementation.

That later package must pin:
- exact baseline commit and source blobs;
- exact allowed/forbidden paths;
- source/test/fixture/schema files and dependencies;
- commands, focused test matrix and expected negative cases;
- filesystem/network/credential/provider permissions;
- synthetic-only data boundary and resource ceilings;
- stop conditions and failure handling;
- artifact format, retrieval/readback and digest verification;
- exact claims allowed after tests and rollback boundary.

No automatic progression from contract approval to code. Every implementation increment requires a separate explicit Owner approval under D14-A.

**Owner selection required:** approve this two-step gate or amend it.

## 4. Recommended combined decision

Recommended first S2 scope:

- D01-S2: Option A — SHA-256 exact-byte integrity only; explicitly exclude issuer-signature verification.
- D02/D05-S2: new S2-only versioned envelope for verifier metadata; evidence payload remains opaque exact bytes; no JCS in this stage.
- D03/D04-S2: Option A — no keys or trust roots; no key operations.
- D13-S2: approve the immutable verifier-created result binding described above, with no generic trust boolean and no execution authority.
- D11-S2: measurement-first; no numeric ceilings ratified in this package.
- D14-S2: contract approval only permits a separate implementation package; a further Owner approval is required before implementation.

This is a deliberately smaller claim than issuer authentication. It is consistent with the initial manual Owner-attestation policy and avoids introducing key custody before a specific issuer-authenticity claim has been approved.

## 5. Explicit non-authorizations

Regardless of selected options, this package itself authorizes none of the following:

- source, test, fixture, schema, parser, verifier, adapter, registry, serialization or IPC implementation;
- dependency addition/upgrade or workflow/CI/permission change;
- generation/use/import/storage/signing/verification/rotation/revocation/disposal of any key;
- trust-root creation, provider/KMS/HSM setup or network access;
- collection or processing of real evidence from VPS/T0/T1/T2/databases/providers;
- artifact retention change, deletion, cleanup, archive, expiry, compaction, VACUUM or redaction execution;
- changes to T0/T1/T2, canonical data, CORE_LEDGER, AI_LEDGER, Shared Risk Engine, Kill Switch or trading runtime;
- deployment, exchange connection, live trading or real orders.

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged. VPS remains absent.

## 6. Verification and status

- Baseline: `d9baed38bad73c0d39c88f233b0f254a669a07a2`.
- Controlling handoff blob read before work: `6e029acbcd8f833b224c2bb981b332eefdaa7c5f`.
- Scope: documentation-only Owner decision package.
- Tests/compile/CI: NOT RUN.
- Runtime/VPS/database/provider/key operations: NOT PERFORMED.
- Independent reviewer sign-off remains waived as a mandatory gate; no independent assurance claim.

**G0.53: PACKAGE PREPARED — READY FOR OWNER DECISION. D01-S2/D02-S2/D03-S2/D04-S2/D13-S2/D11-S2/D14-S2 NOT RATIFIED. S2 IMPLEMENTATION NOT AUTHORIZED.**
