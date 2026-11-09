# P1.24 — Adversarial self-review of signed recovery approval authority

Date: 2026-11-09  
Review type: Same-session static adversarial self-review; NOT independent.  
Exact normative contract blob reviewed: dd33b60649d8881ca935d34b62b8b54b6d0e9d42  
Prior finding: P1.23 F02-R5 HIGH (approval identity/authority unauthenticated)  
Branch: feature/t0-centralized-data-feeder-p1-20261101

## Verdict

**DOCUMENTATION-LEVEL PASS for F02-R5 correction and C141–C145 negative-fixture specifications.**

The previous self-asserted GitHub-login approval path is replaced by Ed25519 signature verification against an administrator-provisioned external approver trust policy. The signed approval is bound to the exact recovery decision, predecessor/new source-root IDs, recovery epoch and v1.1 isolated-only scope. The trust policy is outside the source-root snapshot/restore/clone domain and has explicit key identity, validity, revocation, rotation and fail-closed rules.

This is a same-session static self-review, NOT independent review. It does not prove the future implementation, host trust configuration, key custody, filesystem durability, target runtime or Binance completeness.

## F02-R5 — closure analysis

### Prior defect

P1.23 showed that a repository writer could create an immutable approval JSON, self-assert the owner's GitHub login, and compute matching commit/blob digests. The record's content identity did not authenticate approval authority.

### P1.24 correction

- Approval JSON is a closed twelve-key JCS schema.
- Ed25519 signature covers the canonical JCS bytes of the exact eleven-field payload excluding only the signature field; the payload includes decision ID, decision, predecessor/new root IDs, recovery epoch, exact allowed/prohibited scopes, login, key ID and audit timestamp.
- The key ID is recomputed as SHA-256 of the decoded 32-byte Ed25519 public key; signature encoding is canonical unpadded base64url for exactly 64 bytes.
- The GitHub login is not trusted by itself. It must match the login mapped to the signing key in the external approver policy.
- The external policy is a closed JCS schema, administrator-provisioned outside the source root and all source-root restore/clone/snapshot sets. It contains the public keys, authorized login mappings, validity intervals and ACTIVE/REVOKED status.
- Policy file digest, ownership, mode, stable identity, no-symlink path and separate administrative provisioning are required. No repository-derived policy or source-root fallback is permitted.
- Verification requires the key to be ACTIVE at verification time and the trusted clock to be within the key's configured validity interval. The signed approval timestamp is audit-only and cannot prove signing time.
- Revocation immediately invalidates approvals under that key, including historical approvals. Rotation is administrator-controlled; private keys remain outside the source root.
- Missing/invalid policy, unknown/revoked/expired key, login mismatch, invalid signature, unavailable crypto verifier or untrusted/unavailable clock all reject/quarantine; no GitHub metadata fallback or manual bypass.
- The policy and signature are expressly NOT an independent monotonic anti-rollback anchor. The design states the trust assumption: the separately administered host policy and signing key are not compromised.

## Adversarial checks against the exact contract blob

The exact blob `dd33b60649d8881ca935d34b62b8b54b6d0e9d42` was re-fetched after the final contract edit.

| Check | Result |
|---|---|
| Twelve-key approval record schema | PASS |
| Eleven-field canonical JCS signature payload | PASS |
| Ed25519 public-key and signature byte lengths/encoding | PASS |
| Key ID recomputation and signed key-ID binding | PASS |
| GitHub login is mapped through trusted policy, not self-asserted | PASS |
| External policy schema, digest and admin-only provisioning | PASS |
| Policy outside source-root rollback/clone/snapshot domain | PASS |
| Key validity uses verifier clock at verification time; approval timestamp is audit-only | PASS |
| Revocation invalidates prior approvals | PASS |
| Rotation and private-key custody boundary | PASS |
| Missing/ambiguous/unavailable trust material fails closed | PASS |
| Epoch record now requires signature and policy verification | PASS |
| Approval trust is not misrepresented as an anti-rollback anchor | PASS |
| C137–C145 fixture specifications present and ordered | PASS |
| F01 v1.1 canonical-resumption prohibition preserved | PASS |
| F05 Envelope-record vs Raw-body namespace rule preserved | PASS |

The checks are static contract-text consistency checks, not executable cryptographic tests. No keypair was generated, no signature was created or verified, and no trust-policy file was provisioned.

## Negative fixture specifications

- C141: missing/malformed signature, altered/noncanonical signed payload, or root/epoch/scope mismatch.
- C142: unknown key, incorrect key ID, login mismatch, or key outside validity interval.
- C143: revoked key, including historical approval; require a new approval under an ACTIVE key.
- C144: missing/unreadable/writable/symlinked/digest-mismatched/ambiguous/malformed trust policy.
- C145: crypto verifier or trusted clock unavailable, malformed signature encoding, or verification error.

C137–C145 remain design specifications only; NOT IMPLEMENTED / NOT EXECUTED.

## Residual blockers

- F07 target filesystem/mount/device/provider identity and actual `flock`, `renameat2(RENAME_NOREPLACE)`, file-fsync and directory-fsync behavior: NOT VERIFIED.
- Binance REST no-trade, boundary, pagination, finality and correction semantics: NOT ACCEPTED.
- Pinned producer f64 conversion, fixed 12-decimal formatting and parse-error-to-zero defect: CONFIRMED / NOT FIXED.
- Producer FINAL_ONLY/product identity implementation: NOT VERIFIED.
- Manifest, receipt, publication counter, recovery checkpoint, recovery-epoch/approval verifier, external trust-policy loader and ExchangeInfo evidence store: NOT IMPLEMENTED.
- C01–C145: NOT IMPLEMENTED / NOT EXECUTED.
- No GitHub Actions run/artifact, source implementation, REST request, VPS/runtime or T1 activation.

## Authorization boundary

This self-review PASS permits only retargeting issue #138 to the exact P1.24 contract blob for genuinely independent review. It does not authorize implementation, executable tests, Actions dispatch, REST, VPS/runtime, T1 activation, T0/T2 changes, strategy/AI/ledger/risk changes, trading or destructive data operations.

T0 remains independent/canonical. No T1 writes to T0. Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement. No destructive data operations without separate explicit approval.
