# P1.28 — Adversarial self-review of signed ERA evidence bundle

Date: 2026-11-09  
Review type: Same-session adversarial static self-review; NOT independent.  
Exact normative contract blob reviewed: b6c613c41613a409dca741d9ce64bdad4670c293  
Prior finding: P1.27 F02-R10 HIGH.  
Branch: feature/t0-centralized-data-feeder-p1-20261101

## Verdict

**REQUEST CHANGES — F02-R11 MEDIUM.**

P1.28 closes the prior evidence-binding gap at the document level: the recovery epoch now pins an immutable bundle containing the exact consume request, receipt payload and signed ERA response envelope. The bundle binds their digests, nonce, operation, tuple and signature, and is required to be durably published before the epoch record. A remaining ambiguity exists in ERA signing-key revocation and historical receipt verification.

## F02-R11 — MEDIUM: ERA key revocation semantics conflict with offline historical verification

Evidence:
- The ERA trust bootstrap key entries have only `era_key_id`, raw public key and status ACTIVE/REVOKED.
- The protocol requires offline validation of the retained signed envelope after restart.
- C165 says an old-key response after revocation rejects.
- The verifier also requires fresh live ERA policy-head/revocation checks before each gated operation.
- No revocation effective sequence/time or distinction between cryptographic evidence verification and current authorization is defined.

Ambiguity:
1. If a key is marked REVOKED, does offline verification of an envelope signed before revocation still validate the historical signature?
2. If all signatures from a revoked key are rejected, previously persisted evidence becomes unverifiable, even though the bundle is immutable.
3. If historical signatures remain valid, what prevents an envelope signed after revocation from being treated as historical?
4. The trust file has no authenticated revocation sequence tied to ERA's monotonic authority sequence.

Required correction:
- Add a revocation-effective authority sequence to each ERA key entry, with null for ACTIVE and a positive uint64 for REVOKED.
- Define historical cryptographic verification separately from authorization: verify the Ed25519 signature using retained public-key bytes even when revoked; then compare the signed envelope authority_sequence with the authenticated revocation-effective sequence.
- An envelope sequence strictly less than the revocation sequence may remain valid historical evidence, but it MUST NOT by itself authorize a new recovery or gated operation after revocation; current ERA status must be ACTIVE at each authorization gate.
- An envelope sequence greater than or equal to the revocation sequence MUST reject as a post-revocation response.
- If revocation sequence cannot be authenticated or compared, retain bytes but quarantine; do not infer ordering from local wall-clock timestamps.
- Add fixtures for pre-revocation signed envelope, post-revocation envelope, equal-sequence boundary, missing/untrusted revocation sequence and revoked key with a current operation.

## Checks that passed at contract-text level

- Exact P1.28 contract blob re-fetched: `b6c613c41613a409dca741d9ce64bdad4670c293`.
- Closed evidence-bundle schema includes request bytes/digest, receipt payload bytes/digest, signed envelope bytes/digest and bundle digest.
- Recovery epoch binds exact bundle reference/digest; previous payload-only fields are absent.
- Request nonce, operation, ERA identity, payload digest, receipt tuple and policy head are cross-checked.
- Bundle no-replace/file-fsync/parent-fsync ordering precedes epoch publication.
- Offline signature evidence validation is separated from fresh live ERA policy/revocation checks.
- C167–C170 are present and ordered.
- F01/F02 canonical-resumption and no-promotion boundaries remain intact.

Static checks do not prove implementation, cryptographic correctness, ERA durability, filesystem behavior or runtime.

## Residual blockers

F07 filesystem/provider semantics NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; C01–C170 NOT IMPLEMENTED / NOT EXECUTED; ERA and its monotonic store NOT IMPLEMENTED / NOT VERIFIED.

## Required next action

Clarify ERA-key revocation ordering and historical-signature semantics, add negative fixtures, then self-review the exact new contract SHA. Retarget issue #138 only after a subsequent exact-SHA self-review passes.

## Authorization boundary

No implementation, executable tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes, strategy/AI/ledger/risk changes, trading or destructive data operations are authorized.

T0 remains independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement. No destructive data operations without separate explicit approval.
