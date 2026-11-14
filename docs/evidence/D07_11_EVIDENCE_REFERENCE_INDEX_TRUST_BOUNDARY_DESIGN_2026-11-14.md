# D07.11 Evidence Reference Index — Trust Boundary Design

Date: 2026-11-14
Status: DESIGN ONLY — NOT IMPLEMENTED
Branch: feature/core-operational-proof-20261112

## 1. Purpose

Define what must be true before a D07.11 evidence reference index can be treated as independently controlled. The existing D07.11 resolver checks safe relative paths, byte lengths and SHA-256 values, but it does not authenticate who created the index, who controls the referenced evidence, whether the index is immutable, or whether the evidence supports the associated claim.

A JSON index committed beside the package is not independent merely because it has hashes. Hashes detect byte changes relative to a supplied declaration; they do not establish who made that declaration.

## 2. Trust domains

Keep these roles distinct and record their actual identities only when evidence exists:

1. Evidence producer — creates the source receipt, acquisition logs, custody records or other evidence object.
2. Evidence custodian — controls retention and access to preserved evidence bytes.
3. Index issuer — creates and publishes the reference-index envelope.
4. Signing authority — controls the signing key and its authorization policy.
5. Verifier — independently obtains the index, verifies its authenticity and resolves referenced objects.
6. Claim assessor — determines whether a verified evidence object actually supports a specific V2 claim.

Do not treat two roles as independent when they share an operator, host, credential, storage administrator, deployment pipeline or other material control plane. Record dependencies explicitly; unknown materiality stays NOT_VERIFIED.

## 3. Minimum index envelope

A future index format should be separately versioned and include:

- indexVersion, indexId, packageId, createdAt, issuedAt.
- Exact subject package manifest digest and canonicalization profile.
- Entries keyed by opaque evidenceRef, each with normalized relative path, byte length, SHA-256, media type, evidence class, producer identity assertion, creation-time assertion and custody reference.
- Explicit UNKNOWN / UNAVAILABLE states for absent producer, timestamps or custody facts; no fabricated defaults.
- issuer identity assertion and signing-key identifier.
- Signature algorithm, signature bytes and signed-payload digest.
- Key authorization metadata: key validity interval, purpose, revocation status and rotation/revocation evidence references.
- Optional append-only publication/receipt proof and trusted timestamp evidence.
- An explicit statement that a valid signature authenticates the index issuer's signed declaration only; it does not prove the truth of evidence contents or the factual support for a claim.

Canonical serialization and signature domain separation must be specified before implementation. Reject duplicate JSON keys, duplicate evidence references, duplicate normalized paths, path traversal, symlinks, absolute paths, case/Unicode normalization collisions and unsupported algorithms.

## 4. Independence and acceptance rules

An index is NOT_VERIFIED unless all required controls can be checked from evidence outside the package under review:

- Index issuer and signing authority are identified and authorized for this package/index purpose.
- The verifier obtains the signed index through a channel not writable by the evidence producer alone.
- Signature verification uses a separately pinned trust root or independently authenticated key-distribution record.
- Key validity, revocation and rotation are checked at the relevant signing time.
- The index publication event is retained in an independently controlled append-only or equivalent tamper-evident system.
- Referenced evidence bytes are stored under a custody boundary not solely controlled by the index issuer.
- A separate verifier can resolve every required reference and recompute byte length and SHA-256.
- The claim assessor maps each evidence object to the exact V2 claim it supports and records limitations.

A Git commit, GitHub Actions artifact, SHA-256 checksum file, or signature whose key is stored in the same repository/runner secret boundary is not sufficient by itself to establish independent custody or authority.

If any role separation, key authority, publication history or storage independence is unknown, do not emit an independence PASS. Use NOT_VERIFIED or BLOCKED for contradictions.

## 5. D07.11 integration boundary

Do not overload the current resolver with trust decisions. Keep distinct stages:

1. Index authenticity verifier — verifies envelope schema, canonical payload, signature, key authorization/revocation and publication proof.
2. Reference resolver — current D07.11 safe-path and separate-process byte readback.
3. Claim-support assessment — records which resolved evidence supports which V2 claim, including contradictory or missing support.
4. Aggregate disposition — reports only bounded results; no generic provenance PASS.

A resolver PASS remains a byte-resolution result. It must never imply provider authenticity, collector independence, issuer independence, completeness or factual truth.

## 6. Safe staged implementation plan

No implementation is authorized by this design note. If separately approved, use these increments:

- Stage A — inventory and threat model: document available evidence sources, control-plane ownership, key custody and storage boundaries. No new data acquisition.
- Stage B — contract: specify versioned index schema, canonicalization, signature profile, key lifecycle, revocation and publication-proof formats.
- Stage C — TDD verifier: synthetic positive/negative fixtures for signature tampering, wrong key, unauthorized key, expired/revoked key, duplicate refs/paths/JSON keys, path normalization collisions, missing publication proof and shared-control-plane dependencies.
- Stage D — resolver integration: verify the signed index before passing its entries to the existing safe resolver; retain independent byte readback.
- Stage E — real evidence gate: only after owner supplies genuine source/custody objects and separately authenticated trust-root/publication evidence. Do not manufacture these objects from the current ChatGPT-retrieved CSV.

## 7. Current BTCUSDT disposition

The current D07.8 v4 package and V2 draft do not contain an independently issued index, authenticated trust root, provider receipt, original collector execution record, or pre-ChatGPT custody evidence.

Therefore:
- Index authenticity: NOT_VERIFIED.
- Index issuer / signing authority: UNKNOWN.
- Independent custody: NOT_VERIFIED.
- Provider authenticity / upstream origin: NOT_VERIFIED.
- Collector independence: NOT_VERIFIED.
- D07.11 real resolution: NOT RUN.
- D07.2: BLOCKED_SHARED_LINEAGE.
- D07: PARTIAL.
- Paper Ledger bootstrap: BLOCKED / NOT APPROVED.

## 8. Explicit non-actions

This document does not create an index, key pair, signature, custody record, evidence object, provider receipt or trust root. It does not modify D07.8 package bytes, V1/V2 schemas, validators or D07.11 resolver. No network acquisition, VPS/T0 access, ledger write, Runner/One-shot, credential use, live trading or data deletion occurred.

Next gate: owner review of the trust-boundary design and a separately scoped approval before any index contract or verifier implementation.
