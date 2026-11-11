# AI Calibration Ed25519 Key Management Lifecycle Contract

**Status:** DESIGN PROPOSAL — DOCUMENTATION ONLY; NOT FROZEN FOR IMPLEMENTATION  
**Date:** 2026-11-11  
**Scope:** Offline signing-key lifecycle for the future AI Calibration Registry  
**Authority:** Owner-approved GitHub append-only Registry + offline Ed25519 signing direction

## 1. Security objectives and non-goals

This contract proposes how a future authorized publisher key is created, identified, protected, used, rotated, revoked and recovered.

Objectives:
- Keep private signing material offline and outside GitHub, CI, VPS and runtime.
- Pin trust through an independently provisioned public-key fingerprint.
- Separate key identity, key authorization, manifest integrity and calibration quality.
- Make lifecycle events append-only and verifiable.
- Fail closed when key status, history, custody or trust bootstrap is unknown.

This is not authorization to generate or import keys, enroll a trust root, sign manifests, run production cryptography, create CI secrets, install a verifier, alter T0 A2.2, or activate AI admission.

## 2. Proposed key hierarchy and roles

Use a small hierarchy with distinct roles; exact deployment choice remains open:

1. **Offline Trust Root (ROOT):** authorizes publisher signing keys and key-lifecycle records. Kept offline. Its public-key fingerprint is pinned independently by the verifier owner.
2. **Offline Calibration Publisher (CALIBRATION_SIGNER):** signs calibration manifest statements and allowed registry events within a narrowly scoped namespace/audience. It must not authorize itself or alter the trust root.
3. **Recovery/Revocation Authority (RECOVERY_AUTHORITY):** authorizes emergency revocation and recovery when a publisher key is lost or suspected compromised. It must be independently provisioned from the key it can revoke.

Do not collapse these roles into one key without a separately approved threat analysis. The root and recovery keys should not be online signing services. A publisher key must not sign its own authorization, revocation or replacement authorization.

Every key record binds:
- immutable `key_id`;
- algorithm/profile exactly `Ed25519` (no algorithm negotiation);
- public key bytes and canonical encoding;
- SHA-256 public-key fingerprint;
- role, namespace, audience and permitted record types;
- authorized-from sequence and optional trusted-time interval only if trusted time is established;
- status and lifecycle-event references;
- predecessor key/authorization record where applicable.

A key is authorized by a signed authorization record, not merely because its public key appears in a repository file.

## 3. Key generation ceremony — proposed

A future ceremony must be performed on a dedicated, trusted offline device/environment with:
- reviewed and version-pinned cryptographic tooling/library;
- operating-system cryptographically secure random number generator;
- verified system entropy and no deterministic test seed;
- no network connection during generation or private-key handling;
- no shell command-line argument, environment variable, clipboard, log, terminal transcript or artifact containing private bytes;
- no generation on GitHub Actions, cloud runner, VPS, application host or phone used as an online runtime.

Ceremony record should capture tool/version and binary digest, device/OS identity, operator, date/time source and its trust limitation, key role/scope, public-key fingerprint, backup verification outcome and ceremony record digest. Do not record private-key bytes, seed phrases, recovery phrases or unencrypted secret material.

The private key should be generated once for its lifecycle. Re-running generation is not a recovery procedure. A lost private key is replaced by a new authorized key; the old key is revoked.

## 4. Custody and backup

Proposed custody:
- Keep the active private key on encrypted removable offline media or a dedicated offline signing device.
- Keep at least one encrypted recovery copy physically separate from the primary copy, with access control and a documented custody owner.
- Protect encryption/recovery material separately from the encrypted key backup; do not store both together.
- Verify backup restoration in a controlled offline ceremony using a test challenge or public-key derivation check. Do not sign a production manifest during the test.
- Record custody checks, media identifiers, encryption method/version and last verification date without exposing secrets.
- Do not put private keys in Git, GitHub Releases, Actions artifacts/cache, GitHub secrets, environment variables, VPS disks, runtime volumes, T0 database, logs or issue/PR comments.

For a personal low-cost system, physical separation and encrypted offline media are preferable to adding a hosted HSM/KMS service, unless a later threat assessment justifies the cost. This is a proposal, not a selected hardware product.

## 5. Signing ceremony

Before signing a manifest:
1. Freeze exact canonical manifest bytes and compute SHA-256 independently.
2. Verify manifest schema, predecessor sequence, provenance references and candidate status.
3. Confirm the requested signer key is currently authorized for the exact namespace, audience and record type.
4. Confirm the signer key is not expired under an approved trusted-time rule, revoked, superseded for new signing, or otherwise blocked.
5. Confirm owner promotion authorization and OOS evidence are present where the event requires them.
6. Sign only the domain-separated, versioned statement binding purpose, namespace, manifest ID, schema/canonicalization profile, digest algorithm, digest and byte length.
7. Produce a detached signature envelope; do not embed the signature in the bytes being signed.
8. Verify the resulting signature using the independently pinned public key before publication.
9. Publish manifest, signature envelope and evidence as a new append-only commit. Read back exact bytes and verify SHA-256, Git blob identity and signature.

The exact statement bytes, domain separator, signature envelope and signing tool are open decisions. They must be frozen before any production key is used. Do not assume the T0 A2.2 checkpoint signature statement can be copied unchanged.

A valid signature means the authorized key signed the exact statement. It does not mean the manifest is statistically sound, owner-promoted, leakage-free or safe to trade.

## 6. Public-key pinning and bootstrap

The verifier must obtain its initial trust anchor from an independent owner-controlled channel, not from the same untrusted GitHub registry it is asked to verify.

Bootstrap record must bind:
- root key ID, algorithm, public key and fingerprint;
- exact registry namespace and audience;
- accepted trust-policy version/digest;
- recovery authority identity/fingerprint;
- bootstrap authorization and its provenance;
- verifier configuration version and the exact pin.

The verifier must compare the configured pin to the presented root fingerprint. A mismatch, missing pin or registry-only self-assertion blocks verification. A GitHub manifest cannot add a new root by declaring itself trusted.

The owner must retain a human-readable offline copy of the accepted public fingerprint and trust configuration. Any change to the pin requires a separately authorized trust-root transition; it must not be learned automatically from the latest repository commit.

## 7. Rotation

Routine rotation is planned and overlapping:
1. Generate a new key through the same offline ceremony.
2. Authorize the new public key with the current trusted root/recovery authority under a new immutable key-authorization record.
3. Publish and verify the new record while the old key remains valid.
4. Verify that the verifier recognizes both keys for their explicitly defined sequence windows.
5. Switch the active signer at a declared registry sequence; new manifests use the new key only.
6. Append a supersession event for the old key, including last permitted signing sequence and reason.
7. Retain old public keys and authorization evidence for historical signature verification. Do not delete or rewrite old signatures.

Rotation must not create an interval where no authorized recovery path exists. A new key must never be authorized solely by a signature from the key being replaced if that key may be compromised.

## 8. Revocation and compromise response

Revocation is immediate for new admission after a trusted revocation event is accepted. Reasons should distinguish:
- suspected/confirmed private-key compromise;
- private-key loss or inaccessible custody;
- unauthorized signing or scope violation;
- algorithm/tool weakness;
- planned retirement/supersession.

A revocation event must bind key ID/fingerprint, reason code, effective registry sequence, issuer authority, event time semantics, predecessor event digest and affected manifest/event range.

For compromise:
1. Stop using the affected key; do not attempt to repair or overwrite its history.
2. Use the independently provisioned recovery authority/root through the offline recovery ceremony.
3. Append a signed revocation event and authorize a replacement key.
4. Mark all manifests signed after the earliest defensible compromise boundary as `TRUST_STATUS_UNKNOWN` or revoked pending review; do not assume local timestamps prove signing preceded compromise.
5. Re-evaluate affected manifests with independent provenance/OOS evidence before any future promotion.
6. Keep old public key, signatures and event records for forensic verification.

If the root itself is compromised, a recovery path that depends only on that root is insufficient. Use a separately pre-pinned recovery authority or an owner-controlled out-of-band re-bootstrap. Until that trust transition is verified, all new AI calibration admission remains blocked.

A revocation record in the same repository is not self-authenticating. Its signer must chain to an independently pinned authority.

## 9. Recovery and loss scenarios

| Scenario | Required response | Admission state |
|---|---|---|
| Active signer media unavailable, backup verified | Restore offline from encrypted backup; verify derived public key/fingerprint before use | BLOCKED until custody check passes |
| Active signer private key irrecoverably lost | Revoke old key through recovery authority; generate and authorize a new key | BLOCKED during transition |
| Active signer suspected compromised | Stop signing; revoke via independent recovery authority; assess affected signatures | BLOCKED for affected scope |
| Root key lost but not known compromised | Use separately provisioned recovery authority and documented root-replacement ceremony; if absent, no automated recovery | BLOCKED |
| Root key compromised | Out-of-band owner re-bootstrap using an independent trust channel; do not trust repository-only replacement | BLOCKED |
| Registry history unavailable or conflicting | Preserve local evidence, do not select a convenient branch head; restore from independently held verified copy and reconcile chain | BLOCKED / UNKNOWN |
| GitHub account/repository compromised | Freeze publication, preserve external copies, restore repository under owner-controlled account; rotate affected credentials/keys as indicated | BLOCKED |
| Encrypted backup corrupted | Use separately verified recovery copy; if none works, revoke and rotate rather than reconstruct key material | BLOCKED |

Recovery must not silently roll back to an older manifest or key status. A restored repository snapshot is historical until its predecessor chain and latest independently known registry sequence are reconciled.

## 10. Historical verification and trusted time

A valid signature alone cannot prove when it was created. A local timestamp or Git commit timestamp is not trusted signing time.

The verifier must distinguish:
- signature cryptographic validity;
- key authorization at a defensible sequence/time;
- current key status;
- manifest promotion/revocation status;
- statistical/OOS validity.

If trusted time is unavailable, do not make a definitive claim that a signature predates a compromise. Use registry sequence and independently retained evidence only to the extent the approved protocol supports it; otherwise return UNKNOWN/BLOCKED.

## 11. Audit and negative cases

A future implementation contract must include deterministic tests for:
- unknown key ID, wrong fingerprint and unpinned root;
- wrong algorithm/profile, altered signature, changed manifest digest/length;
- key outside namespace/audience/record-type scope;
- revoked, superseded, not-yet-authorized and unknown-status key;
- rotation overlap and exact cutover sequence;
- duplicate sequence, predecessor mismatch, same-sequence equivocation and history rollback;
- root compromise with no independent recovery authority;
- lost/corrupt primary and backup media;
- revocation record signed by the compromised key itself;
- signature timestamp claims without trusted time;
- old valid signature after current revocation;
- missing/inaccessible registry or conflicting repository copies.

Every negative case must prove no partial trust-state advancement and no AI admission.

## 12. Relationship to T0 A2.2

The T0 A2.2 signature contract has a separate T0 checkpoint issuer-attestation purpose, namespace, bootstrap design and explicit production-implementation boundary. The AI calibration key hierarchy must not silently inherit its role authorization, Trust Policy, Monotonic Anchor, owner-approval semantics or bootstrap.

A future cross-contract review may reuse already specified canonicalization or cryptographic primitives only after checking exact byte compatibility, profile scope and domain separation. Reuse of code does not imply reuse of trust authority. The existing owner approval for T0 A2.2 Stage I synthetic implementation does not authorize AI production keys, signing, trust-root enrollment, or calibration registry implementation.

## 13. Open decisions

1. Root/recovery topology and independent bootstrap channel.
2. Number of physical offline devices/media and custody arrangements.
3. Accepted cryptographic tool/library, version pinning and reproducible build evidence.
4. Key encoding, fingerprint format and public-key record schema.
5. Trusted-time policy and validity-window semantics.
6. Rotation overlap and maximum key lifetime.
7. Compromise boundary and retroactive treatment of historical signatures.
8. Repository backup/freshness mechanism and independent failure domain.
9. Whether a dedicated offline signing device is warranted versus encrypted removable media.

**Disposition:** lifecycle design proposal only. No key generation, key import, signing, verification, trust-root enrollment, CI/VPS/runtime integration or AI admission is authorized.
