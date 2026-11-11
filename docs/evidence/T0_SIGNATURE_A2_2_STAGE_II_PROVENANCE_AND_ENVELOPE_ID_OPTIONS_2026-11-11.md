# A2.2 Stage II — provenance mapping and envelope identity options

**Status: DOCUMENTATION-ONLY OPTIONS / OWNER DECISION REQUIRED / NON-NORMATIVE / NO IMPLEMENTATION AUTHORITY**  
**Date:** 2026-11-11  
**Branch:** `feature/t0-centralized-data-feeder-p1-20261101`  
**Base reviewed:** `83b32e40741102d47a5a2a348596fef4dfdffa37`  
**Inputs:** A1 §§4.2–4.4, 14.4; Checkpoint Contract v1 §6; Stage II adapter contract blob `944758f37f0cc3b0fa1d9968976ce2a7d6c7ce72`; field-mapping review blob `4cc1b8df2a9beb45cff8b83040bc47a7356dc92c`.

## 1. Decision required

Three provenance/authorization items required by A1 §14.4 still need a concrete signed mapping:

1. signing software/build identity;
2. signing request/decision reference;
3. signer authority/custody evidence reference.

A1 permits two broad representations. This note compares them without selecting one, inventing field names, or defining an unapproved authority source.

The Ed25519 primitive remains unchanged: it verifies the exact caller-supplied preimage bytes and makes no identity, trust, authorization, custody, or acceptance decision.

## 2. Option A — put the three references directly in the signed Signature Statement

### Shape

The canonical Signature Statement contains explicit fields for:
- signing software/build identity;
- signing request/decision reference;
- signer authority/custody evidence reference.

Each field's schema, requiredness, cardinality, issuer/namespace, and validation rules would have to be defined normatively before schema freeze. If any value points to an external evidence object, the reference must be unambiguous and integrity-bound; a bare mutable URL or human-readable label is insufficient.

### Advantages
- One signed statement contains the complete provenance reference set.
- Fewer object types and fewer verification dependencies.
- Easier to inspect and export as a self-contained statement.
- Avoids introducing a second signature-verification chain solely for the authorization evidence.

### Costs and risks
- Statement schema becomes larger and more tightly coupled to build provenance, signing workflow, and custody evidence formats.
- Changes in those evidence schemas may require a Signature Statement schema/profile change.
- Large or frequently changing evidence may be awkward to embed; external references still need exact immutable identity and digest binding.
- Consumers must understand the semantics of all three fields even if they only need a subset.

### Required contract work
- Define exact field names, types, canonical formats, cardinality, and whether each is mandatory.
- Define exact issuer/namespace and immutable-reference rules.
- Define how a reference resolves to evidence and how its digest/length/type/schema are authenticated.
- Define missing, unavailable, revoked, malformed, or conflicting evidence behavior.
- State explicitly that presence in the signed statement proves only that the signer asserted/bound the reference; it does not itself prove that the authority or custody claim is true.

## 3. Option B — create a separately signed Authorization Evidence Object

### Shape

Create a distinct canonical Authorization Evidence Object containing the three provenance/authorization items. The Signature Statement then binds that object by an exact immutable descriptor containing, at minimum, the fields required by A1:
- object ID;
- object type and schema version;
- canonicalization identifier;
- digest algorithm and digest;
- exact byte length;
- purpose/context.

The authorization object is independently signed. Its signature is verified separately; the resulting cryptographic validity is still not equivalent to signer trust or policy authorization.

### Advantages
- Separates authorization/provenance schema evolution from the core Signature Statement.
- Supports richer or independently reusable evidence without expanding every statement.
- Allows the authorization object to have its own signer, issuance context, and lifecycle.
- The core statement can bind one compact, integrity-protected descriptor.

### Costs and risks
- Adds another signed object, signature, schema, and verification dependency.
- Requires precise rules for which signer signs the authorization object and how that signer is trusted/authorized.
- Introduces ordering and availability concerns: the object must exist and be retrievable before the statement can be fully validated.
- Requires replay, substitution, expiry/revocation, and evidence-version handling at the higher trust layer.
- More difficult to make a self-contained offline evidence package; the complete dependency closure must be retained.

### Required contract work
- Define Authorization Evidence Object schema, purpose, issuer/signer role, and canonicalization.
- Define its exact signature statement/preimage domain and profile without reusing the Signature Statement domain incorrectly.
- Define the descriptor fields bound by the main Signature Statement and require exact digest/length/type/schema/purpose matching.
- Define whether one object may be reused across statements and, if so, the allowed scope and replay protections.
- Define failure behavior when the object or its signer evidence is missing, invalid, stale, or not authorized.
- Define the trust chain for the authorization-object signer separately from the Ed25519 primitive.

## 4. Comparison

| Criterion | Option A: direct fields | Option B: separately signed object |
|---|---|---|
| Schema complexity | Lower object count; richer main statement | More object types and verification steps |
| Coupling | Provenance schema coupled to statement | Provenance schema can evolve independently |
| Offline completeness | Simpler if all references resolve | Requires full dependency closure |
| Reuse | Usually statement-specific | Potentially reusable, subject to strict scope rules |
| Verification | One statement signature plus referenced-evidence checks | Main statement and authorization-object signatures plus trust checks |
| Failure surface | Fewer cryptographic links | More links, availability and replay cases |
| Best fit | Small, stable, compact provenance fields | Rich, independently governed or reusable authorization evidence |

Neither option is inherently more trustworthy. Trust depends on signer authorization, evidence provenance, policy, revocation, time, and custody controls outside the cryptographic primitive.

## 5. Envelope ID and descriptor lifecycle — non-circular requirements

The completed envelope cannot contain an identifier that is itself defined as a hash of the completed envelope bytes if that identifier is included in those same bytes. That creates self-reference.

The contract must distinguish at least:
- **pre-signing statement identity:** fields included in the canonical Signature Statement and therefore covered by its signature;
- **envelope/descriptor identity:** identity assigned to the envelope or its descriptor;
- **envelope content digest:** digest computed only after the complete envelope bytes exist;
- **external references:** records that refer to the completed envelope by its immutable digest/descriptor.

Two lifecycle patterns are possible and remain undecided:

### Pattern E1 — preassigned stable envelope ID
Assign an opaque unique envelope ID before signing. The ID may be included in the signed statement only if its generation, uniqueness, namespace, and semantics are normative and it is not derived from the completed envelope bytes. After signing, construct the envelope/descriptor and compute its content digest. External records bind the completed digest.

Risk: preassignment and retries must not cause ID reuse, ambiguous abandoned IDs, or a mismatch between statement and final envelope.

### Pattern E2 — detached descriptor identity
Keep the envelope ID outside the signed statement. After the signed statement and signature are complete, construct a detached descriptor that binds the statement identity, signature profile, signer fingerprint, and exact envelope content digest/length. The descriptor ID must be independently assigned or derived from descriptor bytes that do not include the ID itself. External records bind this descriptor.

Risk: consumers must validate the descriptor-to-envelope binding and must not treat an untrusted descriptor ID alone as integrity evidence.

### Invariants required for either pattern
- Never define an ID as a digest of bytes that contain that same ID.
- Never use a mutable locator as the immutable identity.
- Define the exact bytes covered by each digest and signature.
- Define retry/re-sign behavior and whether a new signature creates a new envelope identity.
- Keep post-signing Verification Records append-only and bind them to the exact completed envelope/descriptor digest; do not insert verification results retroactively into the signed statement.
- Define how offline bundles include the complete descriptor and referenced evidence closure.

No E1/E2 pattern is selected in this note.

## 6. Decision table for owner/security review

| Decision | Option / question | Current status |
|---|---|---|
| Provenance representation | A: three direct signed fields | OPEN |
| Provenance representation | B: separately signed Authorization Evidence Object | OPEN |
| Envelope identity | E1: preassigned stable ID | OPEN |
| Envelope identity | E2: detached descriptor identity | OPEN |
| Authorization-object signer role (if B) | Must be specified by governing trust contract | OPEN |
| Exact field/object schemas | Must follow selected representation | NOT DEFINED |
| Verification Record schema | Separate append-only contract | OPEN |
| Ed25519 primitive interface | Exact bytes only; stateless | UNCHANGED |

## 7. Recommendation boundary

This note deliberately makes **no recommendation or owner decision** between A/B or E1/E2. The choice should be based on the expected size/stability/reuse of authorization evidence and the operational requirement for offline evidence completeness. It must not be chosen merely to simplify implementation.

A security review should explicitly assess:
- authority and signer separation;
- substitution and replay;
- evidence immutability and retention;
- revocation and historical trust-at-time;
- offline dependency closure;
- schema/version migration;
- retry and duplicate-signing behavior.

## 8. Scope and disposition

- This is a non-normative documentation options note only.
- No A1/A2.2 normative contract is amended.
- No field names or object schemas are selected.
- No code, tests, dependencies, CI workflow, key, trust root, policy/anchor state, VPS/T0/runtime, trading, or destructive operation is authorized or changed.
- No tests were run; this increment is documentation-only.

**Disposition: OPTIONS RECORDED / OWNER DECISION REQUIRED / CONTRACT FREEZE BLOCKED / IMPLEMENTATION NOT AUTHORIZED.**

**Next step:** owner chooses A or B and E1 or E2, or requests a bounded revision. After that, revise the normative contract and obtain independent security review before seeking separate implementation authorization.
