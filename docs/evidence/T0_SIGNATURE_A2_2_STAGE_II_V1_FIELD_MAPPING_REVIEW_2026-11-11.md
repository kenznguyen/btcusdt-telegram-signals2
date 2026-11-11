# A2.2 Stage II — v1 Signature Envelope field-mapping review

**Status: DOCUMENTATION REVIEW / PARTIAL PASS / THREE REQUIRED MAPPINGS OPEN / NO IMPLEMENTATION AUTHORITY**  
**Date:** 2026-11-11  
**Branch:** `feature/t0-centralized-data-feeder-p1-20261101`

## 1. Purpose and review boundary

This review compares the legacy Checkpoint Contract v1 §6 Signature Envelope fields with A1 §§4.2–4.4 and 14.4 and the Stage II Ed25519 adapter contract.

This is a static documentation crosswalk only. It does not modify the normative A1 or v1 contracts, freeze a schema, authorize code/tests/CI, or authorize key or runtime operations.

## 2. Field crosswalk

| Checkpoint Contract v1 §6 field | A1 mapping / treatment | Stage II disposition |
|---|---|---|
| `signature_envelope_id` | Detached envelope/object identity; computed after signature exists and must not be part of its own signed statement | Outside primitive adapter; exact descriptor/ID lifecycle remains a higher-layer schema requirement |
| `evidence_object_id` | A1 §4.2 `evidence_object_id` | Preserved in signed statement |
| `object_type`, schema version, content digest | A1 §4.2 `object_type`, `object_schema_version`, `content_digest`; descriptor also binds canonicalization/digest/length | Preserved in signed statement; exact bytes supplied to primitive |
| purpose/context | A1 §4.2 `purpose`, `audience`, object type and checkpoint binding | Preserved |
| signing-profile version | A1 §4.2 `signature_profile_id` | Preserved; Ed25519 PureEdDSA only under owner-approved profile |
| signer key identifier/fingerprint | A1 §4.2 `signer_key_fingerprint`, exact SHA-256 of DER SPKI bytes | Preserved; adapter parses key bytes but does not authorize identity |
| algorithm identifier and signature bytes | A1 §4.2 algorithm identifier; A1 §4.4 detached envelope carries signature bytes | Preserved; Ed25519 only, exactly 64 raw octets |
| signing software/build identity | A1 §14.4 requires it in signed Signature Statement or separately signed authorization-evidence object whose exact ID/digest is bound by the statement | **OPEN — no concrete field or referenced-object schema is defined in Stage II draft** |
| signing request/decision reference | A1 §14.4 requires it in signed statement or separately signed authorization-evidence object bound by exact ID/digest | **OPEN — no concrete field or referenced-object schema is defined in Stage II draft** |
| signer authority/custody evidence reference | A1 §14.4 requires it in signed statement or separately signed authorization-evidence object bound by exact ID/digest | **OPEN — no concrete field or referenced-object schema is defined in Stage II draft** |
| local signing observation time | A1 §4.2 `signing_time_observed_ms`, explicitly untrusted | Preserved; cannot establish historical trust-at-time |
| verification references | A1 §14.4 classifies as post-signing evidence in append-only Verification Records; must not be inserted retroactively into signed statement | Correctly excluded from signed statement; higher-layer record schema remains required |
| current Trust Policy snapshot | A1 §4.2 `trust_policy_id`, `trust_policy_sequence`, `trust_policy_digest`, authenticated policy chain | Preserved in statement; adapter itself does not evaluate policy |

## 3. Findings

### F-01 — Signed provenance references are underspecified

Three v1-required provenance/authorization items have no concrete field names, schema, cardinality, or exact binding rule in the Stage II contract:

1. signing software/build identity;
2. signing request/decision reference;
3. signer authority/custody evidence reference.

A1 §14.4 allows these to be included directly in the signed Signature Statement or placed in a separately signed authorization-evidence object whose exact object ID and digest are bound by the statement. The Stage II document currently repeats this as an open blocker but does not select either representation.

**Disposition: OPEN / BLOCKING FOR HIGHER-LEVEL STATEMENT-SCHEMA FREEZE.** This does not prevent the cryptographic primitive interface from remaining narrowly stateless, but the overall Signature Statement/envelope contract MUST NOT be declared complete until the mapping is resolved.

### F-02 — Envelope identity must remain non-circular

The v1 envelope ID must be represented at the envelope/descriptor layer, not naively added to the signed statement if it is derived from the completed envelope bytes. A1 §4.4 prohibits self-reference. The exact stable object-ID assignment and descriptor binding remain higher-layer requirements.

**Disposition: PARTIAL.** The Stage II draft correctly excludes envelope identity from the primitive inputs; the envelope descriptor lifecycle is not specified by the primitive contract.

### F-03 — Verification references are correctly post-signing

Verification references cannot be inserted into the signed statement after signing. They belong in append-only Verification Records referencing the exact envelope digest.

**Disposition: PASS AT MAPPING LEVEL.** Verification Record schema and append-only storage implementation are outside this Stage II primitive review.

### F-04 — Cryptographic and trust decisions remain separated

The Stage II adapter can validate only the mathematical Ed25519 signature over caller-supplied exact preimage bytes. It cannot resolve signer identity, authorization evidence, Trust Policy, revocation, anchor freshness, custody, or historical trust-at-time.

**Disposition: PASS AT BOUNDARY LEVEL.** No trust claim is made by a primitive `VALID` result.

## 4. Required next contract decision

Before declaring the complete signed-statement schema ready for freeze, the owner/security contract review must choose one of:

- **Option A:** add the three provenance/authorization references as explicit fields in the signed Signature Statement; or
- **Option B:** define a separately signed authorization-evidence object, then bind its exact object ID, type/schema, digest algorithm, digest, byte length and purpose into the Signature Statement.

Neither option is selected by this review. Do not invent field names, object schemas, issuer identity, or evidence sources. The cryptographic adapter itself should remain independent of these higher-layer fields and continue to receive exact preimage bytes only.

## 5. Overall disposition

- Basic v1-to-A1 field crosswalk: **PARTIAL PASS**.
- Exact cryptographic fields and message binding: **MAPPED**.
- Signing software/build, signing request/decision, signer authority/custody evidence: **OPEN / BLOCKING FOR FULL STATEMENT-SCHEMA FREEZE**.
- Verification references: **MAPPED TO POST-SIGNING APPEND-ONLY RECORDS**.
- Envelope ID/descriptor lifecycle: **PARTIAL / HIGHER-LAYER CONTRACT REQUIRED**.
- Stage II primitive boundary: **UNCHANGED**.
- Contract freeze: **BLOCKED**.
- Code implementation, tests, dependency installation, CI dispatch, key operations, trust-root/bootstrap, policy/anchor state, VPS/T0/runtime, trading and destructive operations: **NOT AUTHORIZED / NOT PERFORMED**.

No tests were run because this increment is documentation-only.
