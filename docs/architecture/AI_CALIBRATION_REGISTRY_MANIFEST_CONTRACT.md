# AI Calibration Registry Manifest Contract

**Status:** FROZEN VERIFIER CONTRACT V1 — READ-ONLY SIGNATURE/INTEGRITY VERIFICATION; ADMISSION NOT AUTHORIZED  
**Date:** 2026-11-11  
**Scope:** GitHub-backed append-only registry for AI calibration artifacts  
**Authority:** Owner-approved architecture direction: GitHub append-only Registry + offline Ed25519 signing

## 1. Purpose and boundaries

This contract proposes the manifest payload that binds a calibration transform, its evaluation evidence, provenance and promotion state to exact immutable bytes.

It does not create a registry, choose a repository path, generate keys, sign or verify production objects, train a calibrator, select a calibration method, set (C_{min}), or authorize AI admission. All fields and encodings below remain proposals until a separate schema freeze.

The registry is an evidence/control plane. It is not a source of canonical market data and must not copy, mutate, supersede or become authoritative over T0. Large datasets are referenced by immutable dataset IDs and digests.

## 2. Record model

Use distinct immutable record types rather than editing one manifest in place:

1. **Calibration Artifact Manifest** — describes one exact calibrator artifact and its provenance.
2. **Evaluation Evidence Record** — binds the OOS evaluation report, dataset lineage and metrics.
3. **Registry Event** — records candidate, approval/promotion, revocation, supersession or withdrawal.
4. **Signature Envelope** — detached signature metadata for the exact canonical manifest payload.
5. **Trust Configuration Record** — identifies accepted public-key fingerprints and lifecycle state. Trust bootstrap is out-of-band; a record in the same Git repository cannot bootstrap its own authority.

Every record receives a stable immutable ID and schema version. A new state is a new record referencing the prior record; no approved record is overwritten.

## 3. Proposed manifest field inventory

| Field | Required meaning |
|---|---|
| `manifest_schema` | Exact schema identifier and version |
| `manifest_id` | Globally unique immutable manifest ID |
| `registry_namespace` | Dedicated AI-calibration namespace; not T0 checkpoint namespace |
| `record_sequence` | Canonical unsigned decimal string, monotonically increasing within the namespace |
| `previous_record_digest` | Exact predecessor record digest; explicit genesis value only for first record |
| `record_type` | `CALIBRATION_ARTIFACT` |
| `calibration_id`, `calibration_version` | Immutable registry identity |
| `artifact_path`, `artifact_digest`, `artifact_size_bytes` | Exact repository-relative path, SHA-256 and byte length |
| `artifact_media_type` | Explicit media type; no content inference |
| `calibration_method`, `method_version` | Exact transformation method and version |
| `transform_schema` | Schema for the score-to-probability transform |
| `model_id`, `model_version`, `model_artifact_digest` | Exact model identity and bytes |
| `strategy_id`, `strategy_version`, `strategy_source_commit` | Exact strategy identity/source |
| `training_dataset_id`, `training_dataset_digest`, `training_cutoff` | Model-training provenance |
| `calibration_dataset_id`, `calibration_dataset_digest`, `calibration_start`, `calibration_end` | Separate calibration-data provenance |
| `label_definition_id`, `label_definition_digest` | Exact event/target semantics |
| `forecast_horizon_value`, `forecast_horizon_unit` | Explicit forecast horizon |
| `sample_count` | Eligible sample count, canonical decimal string |
| `evaluation_record_id`, `evaluation_record_digest` | Exact OOS evidence reference |
| `created_at` | Producer timestamp, not trusted signing time |
| `publisher_id` | Authorized publisher identity reference |
| `signature_envelope_id` | Detached signature envelope reference |

The manifest must not contain one static `calibrated_confidence`. The calibration artifact defines a transform. Each inference carries its own calibrated confidence bound to the exact artifact ID/version/digest.

## 4. Proposed canonical payload and detached signature

- The signature covers the exact canonical manifest payload bytes, not a GitHub URL, mutable branch name, commit message or detached signature file.
- Signature metadata is detached to avoid self-reference. The signed payload must not contain its own signature or signature-envelope digest.
- The signature envelope binds: envelope ID, manifest ID, manifest schema, canonicalization profile, digest algorithm, manifest digest, signature algorithm/profile, key ID, signer role, namespace/audience, and signature bytes.
- The manifest digest is SHA-256 over the exact canonical payload bytes. The signature signs a domain-separated, versioned statement that binds the purpose, namespace, manifest digest and byte length. Exact domain bytes and statement schema require a separate contract freeze.
- Verification must compare the fetched manifest bytes with the declared canonical serialization; it must not parse and silently reserialize untrusted bytes before checking the signature.
- Do not use a floating Git ref such as `main` or a mutable tag as the object identity. Bind repository path, exact commit SHA, Git blob SHA and SHA-256 of the file bytes. The SHA-256 payload digest remains the cryptographic content identity.

## 5. Canonicalization and field encodings — proposal

Prefer reusing an already reviewed canonicalization profile only if every manifest field conforms exactly. The existing T0 A2.2/T0-JCS-1 contract is scoped to a separate T0 signature purpose and does not automatically authorize this calibration purpose.

Proposed safe field rules:
- UTF-8 without BOM; reject duplicate keys, invalid UTF-8, unpaired surrogates and noncanonical serialization.
- No JSON floating-point numbers. Financial/decimal values, thresholds, probabilities and horizons use canonical decimal strings with an explicitly frozen grammar.
- Logical counters, sample counts, byte lengths and sequences use canonical unsigned decimal strings and are range-checked.
- Timestamps use one frozen UTC representation with explicit timezone; do not treat producer timestamps as trusted time.
- Identifiers use a restricted ASCII grammar unless Unicode is explicitly required.
- Arrays that represent sets are sorted by a stable, schema-defined key; array order is preserved only where semantically meaningful.
- Unknown fields are rejected for a frozen schema version; extensions require a new schema version.
- The canonicalization profile identifier is signed and cannot be negotiated from untrusted input.

If the T0-JCS-1 subset is reused, a compatibility review must prove its numeric/string grammar and byte-level canonicalization cover this manifest without broadening that profile. If not, define a separate versioned profile. No implicit profile fallback is permitted.

## 6. Provenance and OOS binding

The manifest/evaluation pair must bind:
- exact model artifact digest, model version and strategy source commit;
- training dataset ID/digest and cutoff;
- calibration dataset ID/digest and interval;
- label definition and forecast horizon;
- calibration implementation/method version;
- eligible sample count and exclusions;
- temporal split boundaries and horizon-aware embargo;
- evaluation metrics, uncertainty intervals and reproducible evaluation procedure;
- evaluation code/environment identity.

Training and calibration observations must be disjoint under the approved temporal protocol. Label windows crossing the split boundary must be excluded or embargoed according to the frozen horizon rule. Hashes establish byte identity, not truthful dataset construction or leakage-free methodology.

## 7. Promotion and status semantics

Proposed lifecycle:
- `CANDIDATE`: record exists but cannot support AI admission.
- `APPROVED`: explicit owner authorization and all required evidence checks exist.
- `ACTIVE`: selected approved version for a specific model/strategy/policy scope.
- `SUPERSEDED`: a later record replaces it for new inference; historical verification remains possible.
- `REVOKED`: no new inference may use it; reason and effective sequence are recorded.
- `WITHDRAWN`: publisher withdraws a candidate before promotion.

Promotion, activation, supersession and revocation are append-only signed events. A signature alone does not promote a candidate. A valid signature and digest do not establish OOS statistical quality.

The verifier must fail closed on unknown state, missing predecessor, sequence conflict, invalid signature, incompatible provenance, revoked artifact or missing evidence. Historical records must not be rewritten to make the current state appear valid.

## 8. Repository and Git evidence binding

The repository path is not yet selected. Once separately approved, the registry should have a dedicated namespace, for example `docs/registry/ai-calibration/`, with manifests, detached signature envelopes, artifact files and event records separated by type.

Each registry event must record:
- repository and exact commit SHA;
- path and Git blob SHA;
- SHA-256 of exact file bytes and byte length;
- predecessor event digest and sequence;
- event type, actor/key ID and signature-envelope reference.

Git commit history is useful append-only evidence but is not, by itself, a WORM guarantee or independent trust root. Branch protection, repository access control, backup/custody and rollback detection require separate design and approval. Do not claim global freshness from one GitHub repository.

## 9. Relationship to existing T0 A2.2 signature contract

The existing T0 A2.2 contract concerns T0 checkpoint issuer attestation, with its own purpose, namespace, profile, Trust Policy and bootstrap constraints. It is not automatically reusable as an AI-calibration signer authorization.

Before implementation, perform an explicit cross-contract review:
- keep AI calibration namespace, audience, signer role and purpose distinct from T0 checkpoint attestation;
- do not reuse T0 checkpoint policy/anchor state or claim T0 owner attestation for calibration publication;
- assess whether the already specified canonicalization/digest primitives can be reused without changing their normative bytes;
- if cryptographic primitive code is shared later, preserve purpose/domain separation and independent authorization policy;
- do not implement production signing or trust bootstrap under the existing T0 Stage I approval.

## 10. Open decisions and gates

Still unresolved:
1. Exact repository path and GitHub branch protection/custody model.
2. Frozen manifest schema and canonicalization profile.
3. Signature statement schema, exact domain-separation bytes and signature-envelope format.
4. Trust-root bootstrap source and key lifecycle contract.
5. Publisher identity and role authorization.
6. Promotion authority and required OOS acceptance evidence.
7. Calibration method, event semantics, OOS protocol and numerical thresholds.
8. Whether repository history plus independent backup is sufficient for rollback/freshness requirements.

**Disposition:** manifest contract proposal only. No registry files, keys, signatures, provider, workflow, model, calibrator or AI admission path have been created or activated.


## 12. Frozen verifier contract v1 — Owner approval (2026-11-11)

The Owner approved RFC 8785 JSON Canonicalization Scheme (JCS), Ed25519 verification and an independently pinned public-key configuration. The following exact byte/schema rules are frozen for the read-only verifier implementation.

### 12.1 Manifest v1

- Schema ID: `ai-calibration-manifest/v1`.
- The exact required field set is the 37 fields implemented by `pipeline/calibration_registry.py::MANIFEST_FIELDS`; unknown and missing fields are rejected.
- Every manifest value is a JSON string. JSON numeric values, floating-point values and non-finite constants are rejected; counters, sizes, sample counts, horizons and decimal values use canonical decimal strings.
- UTF-8 without BOM; duplicate object keys, invalid UTF-8, invalid JSON and noncanonical serialization are rejected.
- Canonical bytes are exactly `rfc8785.dumps(parsed_manifest)`; fetched bytes must equal those canonical bytes before signature verification. No parse-and-reserialize normalization is performed on accepted noncanonical input.
- Timestamp fields use UTC `YYYY-MM-DDTHH:MM:SSZ`; identifiers use the frozen ASCII identifier grammar; SHA-256 values use lowercase `sha256:` plus 64 lowercase hex digits.
- Artifact bytes are independently checked against both `artifact_digest` and `artifact_size_bytes`. The artifact path must remain under `docs/registry/ai-calibration/artifacts/`.
- Calibration start must be after the declared training cutoff; calibration end must not precede calibration start. This structural check is not a complete dataset-lineage/OOS proof.

### 12.2 Detached signature envelope v1

- Envelope schema ID: `ai-calibration-signature-envelope/v1`; exact field set is frozen by `pipeline/calibration_registry.py::ENVELOPE_FIELDS`.
- Fixed algorithms/profiles: `SHA-256`, `RFC8785-JCS`, `Ed25519`; algorithm negotiation and fallback are forbidden.
- The detached Ed25519 message is exactly the byte prefix `BTCUSDT-AI-CALIBRATION-MANIFEST\\x00v1\\x00` followed by RFC 8785 JCS bytes for a statement with these fields: `domain`, `namespace`, `manifest_id`, `manifest_schema`, `canonicalization_profile`, `digest_algorithm`, `manifest_digest`, `manifest_size_bytes`, `key_id`, `signer_role`, `publisher_id`.
- The signature binds the exact canonical manifest SHA-256 and byte length, namespace, manifest identity/schema, key identity, signer role and publisher identity.
- Public key is raw 32-byte Ed25519 encoded as strict Base64. Its fingerprint is SHA-256 over those exact raw public-key bytes.

### 12.3 Independent verifier trust configuration

The verifier accepts only a server-supplied trust configuration with the exact fields: `key_id`, `algorithm`, `public_key_base64`, `public_key_fingerprint`, `signer_role`, `registry_namespace`, `publisher_id`, `allowed_record_types`.

This configuration is a trust input and must be provisioned independently of the registry bytes being verified. A registry manifest cannot add, replace or bootstrap its own trusted key. No production public key or fingerprint has yet been enrolled; test-only RFC 8032 fixture material is never trusted by production code.

### 12.4 Verifier result and explicit limits

A successful verification returns only `SIGNATURE_VERIFIED_ONLY` with manifest/artifact digest, byte length and signer identity. It does not return an approval/active state or an admission-eligible flag.

The verifier does not yet verify:
- append-only predecessor/event history, duplicate sequence or rollback/equivocation;
- Owner promotion, active selection, revocation or supersession events;
- trusted signing time or global registry freshness;
- the referenced evaluation record's exact bytes/metrics;
- dataset lineage, horizon embargo, OOS methodology or statistical calibration quality;
- a per-inference calibrated confidence generated by applying the artifact transform.

Those remain separate requirements. The production API must continue to fail closed until a trusted provider binds all required evidence and the Owner-approved policy to the exact prediction. No key generation, private-key custody operation, signature publication, calibration training, registry activation, runtime enablement or AI trade admission is included in this approval.
