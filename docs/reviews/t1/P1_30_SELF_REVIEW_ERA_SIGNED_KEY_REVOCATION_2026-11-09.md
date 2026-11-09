# P1.30 — Adversarial self-review of signed ERA key revocation

Date: 2026-11-09  
Review type: Same-session adversarial static self-review; NOT independent.  
Exact normative contract blob reviewed: fef90de3176dffd7bd9979d46b68f976ceb5c878  
Prior finding: P1.29 F02-R12 MEDIUM.  
Branch: feature/t0-centralized-data-feeder-p1-20261101

## Verdict

**REQUEST CHANGES — F02-R13 HIGH; F02-R14 MEDIUM.**

P1.30 adds a root-key-signed ERA key-revocation operation and binds the trust-file sequence to its receipt payload. Two gaps remain: the trust file pins the receipt payload but not the signed response envelope that authenticates it; and root-key rotation/recovery is not defined.

## F02-R13 — HIGH: trust-file revocation entry does not pin signed revocation envelope

Evidence:
- `ERA_KEY_REVOCATION_RECEIPT_V1` payload is authenticated by the Ed25519-signed `ERA_RESPONSE_ENVELOPE_V1`.
- The operational key entry stores `revocation_receipt_ref` and `revocation_receipt_sha256`, both described as referring to the receipt payload.
- No `revocation_receipt_envelope_ref` or envelope digest is defined.
- The receipt payload itself contains no signature.

Consequence:
After restart, the trust file can prove the receipt payload bytes/digest but cannot independently verify that the ERA root key signed the revocation event or that the signed envelope's authority sequence/operation/ERA identity matched the payload. This recreates the P1.27 evidence-binding defect at the key-revocation layer.

Required correction:
- Pin both exact receipt payload and exact signed response envelope (or one immutable evidence bundle containing both) in the ERA trust file.
- Bind envelope operation, ERA identity, root key ID, payload digest and authority sequence to the receipt payload.
- Define no-replace/durable update ordering for receipt evidence and trust-file publication.
- Verify retained signed revocation evidence after restart; fail closed on missing or mismatched envelope.

## F02-R14 — MEDIUM: ERA root-key rotation and compromise recovery are undefined

Evidence:
- The trust bootstrap contains a separately pinned `era_root_key`.
- This root key authenticates operational-key revocation receipts.
- Generic operational ERA-key rotation is described, but no explicit root-key rotation, dual-signature transition, emergency revocation or recovery procedure is defined.

Consequence:
If the root key must be rotated or is suspected compromised, the verifier cannot determine a safe trust transition. Replacing the trust file out-of-band without a pinned transition could silently replace the ultimate authority root.

Required correction:
- Define root-key rotation as a separately approved offline administrative operation, with old/new key IDs, exact trust-file version/digest, transition receipt and no ambiguous overlap.
- Require dual authorization or an independently pinned recovery root for routine root-key rotation; define emergency compromise as quarantine and manual re-provisioning outside this automated profile.
- State explicitly that root-key compromise is outside the automated protocol and no old-root-signed statement can restore trust after compromise.
- Add fixtures for unauthorized root replacement, missing transition proof, duplicate active roots, emergency compromise and recovery.

## Checks that passed at contract-text level

- Exact P1.30 contract blob re-fetched: `fef90de3176dffd7bd9979d46b68f976ceb5c878`.
- `REVOKE_ERA_KEY` operation and closed request/receipt payload schemas are present.
- Revocation receipt binds ERA identity through envelope, key ID, prior/resulting status and effective authority sequence.
- Revocation envelope is required to be signed by a distinct pinned root key, not the operational key being revoked.
- Host trust-file entry binds revocation sequence and receipt payload reference/digest.
- C175–C179 are present and ordered.
- Existing recovery-evidence bundle and no-promotion boundaries remain.

Static checks do not prove cryptographic implementation, ERA durability, root-key custody, filesystem behavior or runtime.

## Residual blockers

F07 filesystem/provider semantics NOT VERIFIED; Binance REST completeness oracle NOT ACCEPTED; producer decimal defect CONFIRMED / NOT FIXED; producer FINAL_ONLY/product identity NOT VERIFIED; C01–C179 NOT IMPLEMENTED / NOT EXECUTED; ERA/root key and monotonic store NOT IMPLEMENTED / NOT VERIFIED.

## Required next action

Bind the signed revocation envelope into durable trust evidence and specify root-key rotation/compromise handling, add negative fixtures, then self-review the exact new contract SHA. Retarget issue #138 only after a subsequent exact-SHA self-review passes.

## Authorization boundary

No implementation, executable tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes, strategy/AI/ledger/risk changes, trading or destructive data operations are authorized.

T0 remains independent/canonical; no T1 writes to T0; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement. No destructive data operations without separate explicit approval.
