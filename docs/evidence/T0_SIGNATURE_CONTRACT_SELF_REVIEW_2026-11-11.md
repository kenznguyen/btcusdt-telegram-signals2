# T0 Signature / Trust Policy / Monotonic Anchor — Adversarial Self-Review

Date: 2026-11-11  
Review type: same-session adversarial self-review by the document authoring assistant  
Disposition: **REQUEST CHANGES — NOT AN INDEPENDENT REVIEW — IMPLEMENTATION BLOCKED**

## 1. Exact reviewed source snapshot

Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Frozen source snapshot: `838f912139562eb185ad6035e95fd08810071525`

| Source | Exact blob SHA |
|---|---|
| `docs/architecture/T0_EVIDENCE_OBJECT_CHECKPOINT_CONTRACT_V1.md` | `a6825270d59bde274bfe765d5f942144b66a84de` |
| `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A1_2026-11-11.md` | `00fdad293e129562145ab930507a4e6b9c2bf23d` |
| `docs/evidence/T0_L4_CONTROL_TO_SOURCE_CROSSWALK_2026-11-11.md` | `e560f084642b5f81c78179ef673e5df116fc5f42` |

The review is limited to the exact frozen documents above. No source document was edited during this review.

## 2. Review boundary and method

Reviewed:
- object identity, digest and canonical wire rules;
- Signature Statement and detached envelope;
- Trust Policy genesis, transitions, key status and downgrade rules;
- Monotonic Anchor genesis, serialization, publication and replay behavior;
- role separation and custody constraints;
- negative-verification matrix and verdict determinism;
- consistency with the base Checkpoint Contract and G1 A proof-of-existence boundary.

Not reviewed or verified:
- cryptographic implementation, algorithm security, actual key material or cryptographic vectors;
- production trust bootstrap, signer identity or owner authorization ceremony;
- runtime anchor persistence/concurrency, custody readback or offline verifier;
- code, tests, CI, VPS, SQLite or canonical T0 data.

This is not independent assurance. It cannot satisfy the separately requested independent-review gate or G3.

## 3. Findings

### SR-01 — HIGH: owner-attestation purpose is not backed by an explicit owner authorization binding

**Source:** A1 §4.2, line 108; §5.3; §9.

The Signature Statement fixes the checkpoint purpose to `T0_CHECKPOINT_OWNER_ATTESTATION`, but the signer is described as a checkpoint signer authorized by Trust Policy. The contract does not require that signer to be the owner, nor does it define an owner-signed delegation/approval object that authorizes this signer to make an owner-attestation claim.

A policy-authorized key proves that the key was authorized for a role/purpose under that policy. It does not, by itself, prove owner intent or that the key holder is entitled to attest on the owner's behalf.

**Required correction:** Either (a) rename the purpose to a neutral checkpoint-signature/issuer-attestation purpose that makes no owner-intent claim, or (b) define a separately authenticated owner authorization/delegation object with exact ID, digest, scope, validity/revocation semantics and binding from the Signature Statement. Preserve the existing G1 A no-signer boundary; do not imply A1 retroactively signs the initial A product.

### SR-02 — HIGH: v1 provenance/authorization requirements are not mapped to concrete A1 schema fields

**Source:** A1 §4.2 lines 101–127; §4.4; §14.4 lines 518–528.

A1 §14.4 requires signing software/build identity, signing request/decision reference and signer authority/custody evidence reference to be signed or bound by a separately signed authorization-evidence object. However, these fields and the referenced-object schema are absent from the mandatory Signature Statement field table and detached envelope field list. The same paragraph says `signature_envelope_id` is represented by A1 fields, but §4.4 does not define an envelope ID field or an exact ID derivation/descriptor rule.

The prose requirement is directionally correct but is not yet an implementable field contract. An implementation could omit or inconsistently encode these values while claiming conformance.

**Required correction:** Add an explicit field-to-v1 mapping table. For each item define exact field name, type, canonical encoding, required/optional status, object ID and digest binding, authorization semantics and verification rule. If a separate authorization-evidence object is used, define its schema, signature authority, descriptor and digest domain. Define signature-envelope identity separately from the signed statement to avoid circularity.

### SR-03 — HIGH: anchor compare-and-advance and two-location publication lack a crash-consistent transition protocol

**Source:** A1 §6.3 lines 272–282; §6.4 lines 284–296.

A1 requires atomic compare-and-advance (or an equivalent single-writer mechanism) and requires each signed anchor plus predecessor chain to be published at both VPS and GitHub. It does not define:
- the durable serialization authority/state store that owns the accepted sequence;
- the precise linearization/commit point at which an anchor becomes the accepted head;
- whether advancement occurs before or after both copies are persisted and read back;
- recovery behavior if one copy succeeds and the other fails, or if the process crashes between compare-and-advance and second publication;
- how a retry distinguishes a partially published committed anchor from an uncommitted candidate.

A process-local single-writer lock is not sufficient evidence of durable monotonicity across process restart. Fail-closed verification prevents false PASS but does not by itself define safe anchor-writer recovery.

**Required correction:** Specify a durable state machine with explicit states (candidate, authorized, committed, published-to-VPS, published-to-GitHub, readback-verified, accepted-head, blocked/recovery). Define one durable linearization point, idempotent retry rules, partial-publication recovery and the prohibition on advancing to sequence N+1 while N is unresolved. The protocol must preserve the approved limitation that joint VPS + GitHub rollback is undetectable.

### SR-04 — HIGH: negative-test expected outcomes are not deterministic enough to implement as a conformance suite

**Source:** A1 §8 lines 330–363.

Several cases combine multiple causes or permit alternative verdicts without defining a stable reason code and per-dimension result:
- NV-02: `INVALID or UNTRUSTED`;
- NV-11, NV-13, NV-15, NV-18, NV-19, NV-21 and NV-24: mixed outcomes or multiple fault classes;
- NV-29: “exactly one serialized transition” does not define the losing writer's stable reason code or recovery state.

The final sentence requires per-dimension results and stable reason codes, but the matrix does not enumerate them. A test implementation could choose whichever allowed verdict makes the test pass. Several rows also combine conditions that should be isolated to identify the failing control.

**Required correction:** Split compound cases into single-fault cases. For every case specify preconditions, mutation, expected per-dimension verdict, aggregate verdict, exact stable reason code and whether state must remain unchanged. Keep only one expected outcome per deterministic fixture.

### SR-05 — MEDIUM: binary and integer canonicalization rules need explicit range and boundary vectors

**Source:** A1 §14.2–§14.3 lines 508–516; digest formulas in §§3, 4, 6 and 13.

A1 requires canonical unsigned decimal strings and U64BE length prefixes, but it does not explicitly state the accepted numeric range (`0..2^64-1`), leading-zero rule, maximum decimal digit count, overflow behavior, or whether every timestamp/schema-version field shares the same bound. The base64url rule is stated, but there are no listed byte-vector tests for empty bytes, one-byte boundaries, invalid alphabet, padding, noncanonical pad bits or decode/re-encode mismatch.

**Required correction:** Define a single unsigned-64 wire primitive (canonical decimal grammar, range, no leading zeros except `0`, overflow rejection) and reference it from every logical integer field. Add positive and negative byte vectors for U64BE boundaries and base64url canonicalization. Any narrower timestamp/schema constraints should be specified separately.

### SR-06 — MEDIUM: the negative matrix counts a known limitation as if it were a negative verification case

**Source:** A1 §8, NV-28 line 359.

NV-28 explicitly says common-mode joint rollback is not detectable. That is an important assurance limitation, but it is not an attack that the verifier can detect and reject. It should be a non-claim/limitation assertion, not counted as a detection test among the 30 negative cases.

**Required correction:** Move NV-28 to a “known undetectable conditions / assurance boundaries” section. Replace the test slot with an assertion test that verifies the verifier reports only `CONSISTENT_WITH_RETAINED_ANCHOR_HEAD` and never claims global latestness when both supplied copies contain the same older valid chain. The test must assert the limitation, not pretend to detect the joint rollback.

### SR-07 — MEDIUM: review-snapshot freeze and normative A1 freeze status are described inconsistently

**Source:** A1 §14.6 line 548; final consistency review report disposition.

The review report says the exact source snapshot is frozen for independent review, while A1 §14.6 says “A1 remains DRAFT / NOT FROZEN pending final consistency verification and a qualifying independent review.” These statements can be reconciled if “frozen” means only immutable review bytes, not owner-approved/final normative contract status, but the distinction is not stated.

**Required correction:** State consistently that the *review candidate snapshot is byte-frozen for review*, while A1 remains a draft contract and is not approved for implementation. Do not describe the current self-review as independent review.

### SR-08 — MEDIUM: policy/root bootstrap is not yet a complete verifier bootstrap object

**Source:** A1 §5.2.

The verifier is told to begin with an owner-pinned root public-key fingerprint or equivalent authenticated bootstrap record, but the exact bootstrap object/record schema and its byte-level binding are not defined here. A fingerprint alone is not the public key bytes needed for signature verification; the verifier needs a trusted key source and a deterministic rule to match its SPKI bytes to the pinned fingerprint. The root replacement recovery ceremony is also deliberately unresolved.

**Required correction:** Define the bootstrap record schema and trusted provisioning boundary: exact root public-key encoding, fingerprint calculation, namespace/audience, role, profile, version, owner authorization reference, recovery policy and verifier pinning mechanism. Until then, keep root bootstrap explicitly BLOCKED and do not allow producer-supplied root material to fill the gap.

## 4. Test-matrix additions recommended

In addition to splitting ambiguous existing rows, add explicit cases for:
- owner-attestation without owner delegation; invalid/expired/revoked delegation;
- missing or altered signing build identity, signing request/decision and signer authority evidence;
- missing/duplicate/mutated signature-envelope ID and descriptor mismatch;
- cross-stream checkpoint substitution where audience is shared;
- integer leading zero, negative, overflow, max U64 and malformed decimal strings;
- base64url padding, standard alphabet, invalid alphabet, noncanonical encoding and round-trip mismatch;
- anchor writer crash before/after durable commit and between the two custody publications;
- partial two-location publication, retry of exact same anchor and prohibition of sequence N+1 while N is unresolved;
- policy/anchor genesis substitution and missing bootstrap public-key bytes;
- append-only Verification Record duplicate/overwrite and tampered verifier identity/version.

Each case should have one expected reason code and explicit state-transition assertions.

## 5. Overall verdict

| Area | Self-review result |
|---|---|
| Evidence object digest and domain separation | **PARTIAL — draft rules present; byte vectors not reviewed/executed here** |
| Signature Statement / owner authorization semantics | **REQUEST CHANGES — SR-01, SR-02** |
| Trust Policy / root bootstrap | **PARTIAL — root bootstrap object and recovery remain underspecified** |
| Monotonic Anchor | **REQUEST CHANGES — SR-03** |
| Negative-verification matrix | **REQUEST CHANGES — SR-04, SR-06** |
| Canonical wire representation | **PARTIAL — range/boundary vectors needed** |
| Custody boundary | **PASS AS BOUNDED CLAIM ONLY**; joint rollback remains undetectable |
| Cross-document consistency | **PASS at the previously frozen snapshot for the previously checked items; this self-review identifies additional semantic/protocol gaps** |
| Independent review | **NOT PERFORMED** |
| Implementation | **BLOCKED** |

**Overall disposition: REQUEST CHANGES before treating A1 as implementation-ready or presenting it as a fully closed signature protocol.** The exact snapshot remains preserved for traceability. Address findings in a new candidate snapshot, then repeat self-review and still obtain the separately required qualifying independent review before implementation.

## 6. Unchanged boundaries

No frozen source document was edited. No code, tests, workflow, CI, key, signature, trust root, policy instance, anchor instance, provider/TSA, VPS/SSH/runtime, SQLite database, canonical T0 data or destructive operation was changed or exercised. No implementation approval is implied. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.
