# T0 Signature / Negative-Verification — Architecture Review

Date: 2026-11-11  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Reviewed branch HEAD: `167b8afea5a0c290b9edc22e8eead92715c3c4ad`  
Work type: **READ-ONLY ARCHITECTURE / TEST-CONTRACT REVIEW**  
Disposition: **DESIGN BASELINE PARTIAL — IMPLEMENTATION BLOCKED PENDING CONTRACT CLOSURE AND QUALIFYING INDEPENDENT REVIEW**

## 1. Scope and safety boundary

This review covers the existing T0 Evidence Object / Checkpoint Contract v1 and its synthetic G2 reference implementation. It does not implement or authorize cryptographic signing, key generation/import/export/rotation/revocation, trust-root changes, provider/TSA calls, anchor writes, runtime/VPS/SQLite access, fault injection, retention changes, or destructive operations.

The signature work described here is a proposed **B — signed-object authenticity / owner-attestation profile**. It is distinct from the already selected **A — dataset/checkpoint proof-of-existence** TSA purpose. A TSA timestamp over a digest does not authenticate an owner signer; a signature does not prove trusted historical time. Neither claim may substitute for the other.

## 2. Exact source baseline reviewed

| Source | Exact Git blob / commit | Review use |
|---|---|---|
| `docs/architecture/T0_EVIDENCE_OBJECT_CHECKPOINT_CONTRACT_V1.md` | blob `5948dd904e1819b626aecc1a85e10c95735191a3` | Evidence Object, T0-JCS-1, digest, envelope, anchor and negative-case contract |
| `synthetic_evidence/t0_checkpoint_contract.py` | blob `9efd800189e15d35e231530d703499d40d9d7e5d` | Current digest/canonicalization/completeness oracle |
| `synthetic_evidence/test_t0_checkpoint_contract.py` | blob `beffd8c4a6cb2682c9fe0acb09cd2b182c2fde7c` | Existing 28-test design baseline (historical local run only) |
| `.github/workflows/t0-evidence-contract-g2.yml` | blob `5e22648c38fd3c6e631f912010de1489bb78f9b5` | Synthetic-only CI contract |
| `docs/evidence/T0_L4_CONTROL_TO_SOURCE_CROSSWALK_2026-11-11.md` | blob `b1f4daac9624d8deedfaf14234e0b6bb79ff81ca` | Current L4 dispositions and custody boundary |
| Branch HEAD | `167b8afea5a0c290b9edc22e8eead92715c3c4ad` | Frozen review reference |

The G2 implementation currently computes canonical content digests, row/partition Merkle roots and completeness verdicts. It contains **no signature creation/verification, trust-policy parser, key-status evaluator, monotonic anchor verifier, or replay state**. The test file contains canonicalization/Merkle/completeness tests only; it does not implement the signature negative cases listed in checkpoint contract §11. The G2 workflow is synthetic-only and its exact-commit result for the reviewed HEAD is not established by this review.

## 3. Findings — ordered by severity

### BLOCKER S-01 — The signature preimage is not defined

Checkpoint contract §6 lists envelope fields and says the signature attests the Evidence Object digest plus purpose/context, but it does not define the exact bytes that are signed. It is therefore not yet possible to guarantee that object ID, type, schema, digest, byte length, purpose, algorithm, signer identity and policy context are all cryptographically bound.

**Required closure:** define one canonical, versioned signature statement and one byte-exact preimage. No field that changes interpretation or authorization may remain unsigned metadata.

### BLOCKER S-02 — No trust-policy contract or bootstrap rule

The existing contract leaves key custody, algorithm, rotation and revocation open. It does not define how an offline verifier authenticates the trust-policy snapshot or establishes its initial root of trust. A policy file stored beside the checkpoint is not trustworthy merely because it has a digest.

**Required closure:** versioned trust-policy object, root-pinning/bootstrap contract, policy signature, monotonic policy version, permitted key roles/purposes/object types/audience, key status and revocation semantics, and offline snapshot requirements.

### BLOCKER S-03 — Replay/rollback is not solved by a valid signature

A previously valid signature remains cryptographically valid when replayed. The current manifest has a predecessor digest, and the checkpoint contract separately requires a latest-head anchor, but there is no defined sequence/anchor transition protocol or replay verdict.

**Required closure:** independently authenticated monotonic anchor; unique sequence; predecessor linkage; same-sequence conflict/equivocation rule; exact object/digest binding; and explicit STALE / REPLAY / ROLLBACK outcomes. A signature alone must never imply latestness.

### BLOCKER S-04 — Custody boundary conflict must be reconciled

The checkpoint contract §§7 and 9 require custody/anchor outside both T0/VPS and GitHub failure domains. The current L4 control crosswalk records the accepted custody scope as VPS + GitHub only, with no external backup requirement. These are incompatible requirements. Do not silently implement one or claim L4 custody/rollback assurance until the governing contract is reconciled with the owner-accepted scope. Under the accepted scope, simultaneous loss/unavailability of VPS and GitHub remains outside the claim; no WORM/immutability claim is made.

### HIGH S-05 — Object identity and digest binding needs an explicit uniqueness invariant

The current model uses an opaque stable `evidence_object_id`, and the external descriptor binds the manifest bytes to that ID/digest. The verifier needs a normative rule: an object ID is immutable and can map to exactly one tuple of object type, schema, digest algorithm, digest and byte length for its lifetime. Same ID with a different tuple is an identity-reuse/substitution failure, not a new version.

### HIGH S-06 — Historical trust cannot be inferred from local timestamps

The contract correctly labels local times as observations and says a valid signature does not prove historical trust-at-signing-time. The trust-policy design must preserve that limitation: if trusted signing time and authenticated revocation history are absent, historical validity is UNKNOWN, not PASS.

### HIGH S-07 — Algorithm/profile negotiation is underspecified

The envelope must not choose an arbitrary algorithm and ask the verifier to accept it. A trust policy must authorize one fixed algorithm/profile per signature-profile version. Unknown algorithms, deprecated profiles, fallback, downgrade and algorithm/key-type mismatch must fail closed. Algorithm choice remains an owner/security decision; this review does not select a production algorithm or provider.

### HIGH S-08 — G2 workflow evidence does not cover signature assurance

Current G2 tests prove a subset of canonicalization, digest, Merkle and completeness behavior. They do not prove cryptographic authenticity, policy trust, revocation, replay resistance, anti-substitution or offline verification. The historical 28/28 local draft run is not an exact committed-SHA CI result and must not be promoted to signature assurance.

## 4. Proposed signed-object contract (design proposal; not approved)

### 4.1 Object to sign

The primary signed subject should be the **exact serialized T0 Checkpoint Manifest Evidence Object**, not a mutable database row, API response, Git commit, ZIP container, display metadata, or the bare `content_root`.

1. Build the complete manifest under the existing T0-JCS-1 profile.
2. Validate schema, market identity, partitions, snapshot boundary, completeness and all declared provenance/claims.
3. Compute exact canonical byte length and Evidence Object digest:
   `SHA256(UTF8("T0-EVIDENCE-OBJECT-V1\\0") || U64BE(byte_length) || canonical_manifest_bytes)`.
4. Keep object ID and signature envelope external to the manifest to avoid recursive/self-referential hashing, as the existing contract already requires.
5. Bind every separately stored data segment/sidecar by exact object ID, media type, byte length and digest in the manifest. A row Merkle root alone does not identify the transport bytes of an independently stored file.
6. A changed manifest, segment, scope, claim, provenance, schema or predecessor produces a new digest and new immutable object identity. An ID must never be reused for changed content.

### 4.2 Exact signature statement and preimage

Define a new versioned canonical statement, for example `T0-SIGNATURE-STATEMENT-V1`. Its canonical JCS bytes should include at least:

- signature profile/version and fixed algorithm identifier;
- purpose enum (e.g. `T0_CHECKPOINT_OWNER_ATTESTATION`);
- fixed audience/system identifier (e.g. `BTCUSDT-QUANT-T0`);
- `evidence_object_id`, `object_type`, `object_schema_version`;
- digest algorithm, exact content digest and byte length;
- checkpoint ID, monotonic sequence and predecessor checkpoint digest;
- signer key fingerprint and signer role;
- trust-policy ID, version and exact policy digest;
- local signing observation time, explicitly marked untrusted (optional and never used alone for historical validity).

Exact preimage:

```
statement_bytes = T0-JCS-1(statement)
signature_preimage =
    UTF8("T0-SIGNATURE-STATEMENT-V1\\0")
    || U64BE(len(statement_bytes))
    || statement_bytes
signature = Sign(private_key_for_profile, signature_preimage)
```

The detached envelope carries the exact statement bytes (or canonical statement fields), signature bytes and envelope schema. The verifier MUST reconstruct the preimage from the received canonical statement and verify the signature; it MUST NOT trust a producer-supplied “signed bytes” digest without recomputing it.

The envelope ID/digest is calculated after the signature exists and is not included in its own signed statement. Any envelope metadata that affects verification or authorization must either be in the signed statement or be treated as non-authoritative display metadata.

### 4.3 Trust-policy model

A versioned trust-policy snapshot should contain:

- policy ID, schema/profile version, monotonically increasing policy sequence, predecessor policy digest and exact policy digest;
- root-policy signer fingerprint and policy signature;
- allowed signature profile/algorithm identifiers;
- signer entries keyed by exact public-key fingerprint (SHA-256 over a specified DER SubjectPublicKeyInfo encoding), not display name alone;
- each key's role, permitted object types, purposes and audience;
- validity interval and status: ACTIVE, REVOKED, COMPROMISED, EXPIRED or UNKNOWN;
- revocation event ID, effective time, reason class and whether compromise is treated as retroactive;
- minimum verifier/profile version and explicit retirement/downgrade rules.

The offline verifier must start from an owner-approved, pre-pinned root fingerprint or equivalent authenticated bootstrap. It must validate the policy signature and policy-chain monotonicity before trusting any signer entry. A trust-policy snapshot supplied only by the object producer is untrusted. Missing, invalid, stale, conflicting or unbootstrappable policy material yields UNKNOWN/BLOCKED.

Key rotation is a policy transition signed by an already trusted policy root or authorized rotation authority. A new key is not trusted merely because its public key is present in the envelope. Private keys never belong in Git, Actions artifacts, T0, or test fixtures committed as secrets.

Role separation should preserve the existing architecture: T0 writer/Feeder ≠ checkpoint builder/issuer ≠ checkpoint signer ≠ custodian ≠ anchor administrator ≠ verifier. The signer must not be granted signing authority through ingestion credentials. The anchor signer must be distinct from the checkpoint signer. A verifier cannot alter the object it verifies or be its sole creator.

### 4.4 Freshness and anti-replay anchor

A separate signed latest-head anchor should bind:

- anchor schema/profile and audience;
- checkpoint ID, checkpoint object ID, object digest and sequence;
- predecessor anchor digest and predecessor checkpoint digest;
- anchor signer fingerprint/role and policy version/digest;
- observation time as untrusted unless separately authenticated.

Acceptance requires the anchor to be authenticated under a separate anchor role, sequence to advance strictly, predecessor linkage to match, and the checkpoint digest to equal the current accepted head. Same sequence + same exact digest may be treated as an idempotent duplicate read; same sequence + different digest is equivocation/conflict and MUST fail closed. A valid old signature that is not the current anchored head is STALE/REPLAYED, not PASS.

The verifier must compare against the latest authenticated anchor available under the approved VPS/GitHub custody scope. If both are unavailable, or the latest anchor cannot be established, freshness is UNKNOWN/NOT VERIFIED. No local database max(sequence), branch tip, file timestamp or untrusted wall clock can replace the anchor.

## 5. Required verifier order and fail-closed semantics

The verifier should use one deterministic pipeline:

1. Parse strict bytes; reject invalid UTF-8, duplicate keys, unsupported schema/profile and noncanonical encodings.
2. Recompute exact byte length and Evidence Object digest from the actual manifest bytes.
3. Enforce object-ID uniqueness mapping and validate object type/schema/purpose/audience.
4. Recompute all row/partition/content roots and semantic/snapshot/completeness checks from the preserved inputs.
5. Validate the signature statement canonical bytes and exact field bindings.
6. Resolve signer fingerprint only from the authenticated trust-policy snapshot; enforce role, purpose, type, audience, algorithm and policy version.
7. Verify signature bytes over the exact domain-separated preimage.
8. Evaluate key validity/revocation under trusted time evidence. If historical signing time cannot be established, report historical trust UNKNOWN.
9. Verify anchor signature, sequence, predecessor chain and current-head equality; detect replay, rollback and equivocation.
10. Emit a new immutable Verification Record with per-dimension results and reason codes; never overwrite an earlier result.

Required verdict separation:

- `PASS`: all mandatory checks for the stated claim pass.
- `INVALID`: cryptographic mismatch, altered bytes, malformed/noncanonical statement or forbidden binding.
- `UNTRUSTED`: signer/policy/algorithm/role is not authorized.
- `STALE_REPLAY`: valid old signature/object is not the current anchored head or was already consumed in a conflicting sequence.
- `BLOCKED`: mandatory trust/anchor/custody material is unavailable or contradictory.
- `UNKNOWN`: the verifier cannot establish a required fact, including historical trust time.

Do not collapse these into a Boolean. No “best effort”, online fallback, auto-fetch of a new trust root, algorithm downgrade or producer-supplied trust decision is allowed in offline verification.

## 6. Negative-verification test matrix (minimum contract)

All tests must use deterministic synthetic objects and disposable ephemeral test keys only after a separate test/implementation gate. No canonical T0 data, production key, VPS, provider or live runtime.

| ID | Attack / defect | Expected result |
|---|---|---|
| NV-01 | Flip one bit in signature bytes | INVALID |
| NV-02 | Verify with a different public key | INVALID / UNTRUSTED |
| NV-03 | Alter one manifest byte but retain original digest/signature | INVALID — content digest mismatch |
| NV-04 | Alter byte length or digest in envelope | INVALID — signed binding mismatch |
| NV-05 | Substitute digest from another valid checkpoint | INVALID — signature statement mismatch |
| NV-06 | Reuse object ID with different digest/type/schema/length | INVALID — OBJECT_ID_REUSE |
| NV-07 | Change object type or schema under same signed envelope | INVALID |
| NV-08 | Replay a valid checkpoint signature for a different purpose | INVALID — purpose binding |
| NV-09 | Replay for a different audience/system | INVALID — audience binding |
| NV-10 | Change signer fingerprint, key ID or algorithm after signing | INVALID |
| NV-11 | Unknown/disabled algorithm or downgrade attempt | UNTRUSTED / BLOCKED |
| NV-12 | Unknown key, wrong role or key not authorized for checkpoint purpose | UNTRUSTED |
| NV-13 | Missing/invalid trust-policy signature or unpinned root | BLOCKED / UNKNOWN |
| NV-14 | Old policy version, policy rollback or conflicting policy sequence | BLOCKED — POLICY_ROLLBACK |
| NV-15 | Revoked/compromised/expired key | UNTRUSTED; historical status UNKNOWN if trusted signing time/revocation chronology is absent |
| NV-16 | Valid old checkpoint replayed after anchor advanced | STALE_REPLAY |
| NV-17 | Same sequence with different checkpoint digest | BLOCKED — EQUIVOCATION |
| NV-18 | Anchor signature invalid, wrong anchor role or predecessor mismatch | BLOCKED / INVALID |
| NV-19 | Anchor missing, stale, conflicting or inaccessible | UNKNOWN / NOT VERIFIED |
| NV-20 | Local clock backdated to evade revocation | UNKNOWN; local time cannot establish historical validity |
| NV-21 | Trust-policy snapshot or verifier root altered | BLOCKED / INVALID |
| NV-22 | Signature statement has duplicate keys, noncanonical bytes or unknown critical fields | INVALID |
| NV-23 | Object is valid but snapshot/completeness is UNKNOWN or INVALID | Signature may verify; checkpoint claim still BLOCKED/INVALID |
| NV-24 | Offline verifier lacks required root/policy/revocation/anchor snapshot | BLOCKED / UNKNOWN; no network fallback |
| NV-25 | Duplicate exact envelope/object re-read with same digest and sequence | Idempotent verification only; no new sequence advancement |
| NV-26 | Later verification attempts to overwrite an earlier record | INVALID — append-only verification history contract |

Tests should assert both the per-dimension result and the aggregate disposition. A valid signature must not mask invalid content, incomplete data, unproven durability, missing custody or stale freshness.

## 7. Test architecture and acceptance gates

- **Unit / byte vectors:** exact canonical statement bytes, signature preimage bytes, digest and signature vectors; malformed encoding; algorithm/key-type mismatch.
- **Crypto negative tests:** wrong key, corrupted signature, altered signed fields, digest/length/object-ID substitution, wrong purpose/audience.
- **Trust-policy tests:** root bootstrap, policy signature, monotonic policy version, role constraints, rotation, revocation, compromise, expiry, unknown key and downgrade.
- **Stateful anchor tests:** monotonic advancement, duplicate idempotency, stale replay, sequence conflict/equivocation, predecessor mismatch, rollback and unavailable anchor.
- **Offline integration tests:** run with network disabled and only the frozen object, pinned root, trust-policy snapshot, revocation evidence and anchor snapshot. Missing any required item must fail closed.
- **Independent conformance:** compare T0-JCS-1 and signature preimage against independently generated byte vectors and a second implementation; the reviewer must not reuse the implementation helper as the oracle.
- **CI isolation:** synthetic fixtures only; no credentials/secrets; explicit network-deny assertion; no imports of market_data/runtime/database/provider modules; ephemeral keys generated only inside the test process and never persisted as reusable secrets.

Acceptance requires all negative tests to fail for the intended reason, positive tests to pass only under the complete policy/anchor state, exact checked-out SHA to be recorded, and independent review of the frozen contract, source and outputs. A test suite that merely calls the same producer helper to construct and verify its own expected bytes is insufficient.

## 8. Independent review result

This is an adversarial second-pass static review of the exact source baseline in §2. It is **not** a qualifying external/independent L4M-09 review and does not claim reviewer independence.

- Existing content identity/canonicalization foundation: **PARTIAL — DESIGN + SYNTHETIC REFERENCE ONLY**.
- Exact signed preimage: **NOT SPECIFIED**.
- Trust-policy/root bootstrap: **NOT SPECIFIED**.
- Signature verifier and negative signature tests: **NOT IMPLEMENTED / NOT VERIFIED**.
- Replay/anti-rollback protocol: **PARTIAL — anchor concept exists, protocol/tests absent**.
- Custody scope reconciliation: **BLOCKED — contract/crosswalk conflict**.
- Formal independent reviewer: **NOT VERIFIED**.

**Review conclusion:** do not authorize implementation yet. First approve a contract-only amendment that resolves S-01 through S-04 and the object identity/trust-time details; then freeze the amendment and test matrix for a genuinely independent review. Only after that review and explicit owner decisions on algorithm/profile, trust bootstrap and anchor authority should a separate implementation authorization be requested.

## 9. Unchanged project constraints

T0 remains an independent protected canonical data asset. No canonical database, feeder, API, writer, schema, VPS or runtime was accessed or changed. No key was generated or used. No trust root, policy, anchor, TSA or provider was changed or contacted. No retention, cleanup, expiry, archive, compaction, vacuum, backup/replica removal or deletion was performed. Paper-only remains in force; `AI_EXECUTION_ENABLED=false`; no live orders.

