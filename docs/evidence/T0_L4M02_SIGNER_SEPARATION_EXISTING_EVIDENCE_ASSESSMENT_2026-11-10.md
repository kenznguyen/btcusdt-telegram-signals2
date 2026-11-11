# L4M-02 — Signer Separation Existing-Evidence Assessment

Date: 2026-11-10
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Work type: documentary source crosswalk only
Status: **ASSESSMENT RECORDED — SIGNER SEPARATION NOT PROVEN**

## 1. Question and disposition

Does the current synthetic Ed25519 verifier, synthetic event-signature tests, Sigstore/GitHub Artifact Attestations workflow, or checked-in trust-root history establish that an owner-authorized T0 checkpoint signer is separated from T0 runtime/admin credentials?

**No.** The reviewed material establishes useful synthetic verification and CI identity checks. It does not establish a production owner signer, its custody/recovery boundary, or that T0 runtime/admin credentials cannot invoke or authorize signing.

L4M-02 remains **NOT VERIFIED**.

## 2. Exact source basis

| Source | Exact blob SHA | Positive evidence | Limitation for L4M-02 |
|---|---|---|---|
| `synthetic_evidence/event_signatures.py` | `56a9fefff190de2d57dcb0afc2d4c0681487bada` | Ed25519 verification over caller-supplied exact event bytes; public-key registry metadata; fail-closed unknown/revoked/expired/unverified trust states | Module explicitly has no signing API, private-key storage, persistence or runtime integration; cannot identify or prove a production signer |
| `synthetic_evidence/test_event_signatures.py` | `c55f514f253a47b8dfa570112c99b2e20c1e077d` | Synthetic tests generate ephemeral Ed25519 private keys in test setup and exercise valid/invalid signature and rotation cases | Test-generated ephemeral keys are test fixtures, not owner-controlled signing authority, custody or separation evidence |
| `synthetic_evidence/trust_anchor.py` | `0f95a5a8714b69fe81ca5421b871dfa586af5121` | Validates GitHub CLI verification output, subject digest and trusted-root bytes/pin | Verifies GitHub/Sigstore attestation evidence; does not establish a separate T0 owner signer |
| `synthetic_evidence/trust_roots/README.md` | `e7df7d5f4575c66503a6d03a361bf312153d9401` | Documents GitHub/Sigstore trust-root pinning and explicit revocation limitations | Root history is GitHub/Sigstore trust material; README says external owner copy is not automated or claimed. It is not T0 signing-key custody evidence |
| `docs/architecture/P1.8.14_EXTERNAL_TRUST_ANCHOR_PROVENANCE_AUTHENTICITY_2026-11-07.md` | `1922b8b9640db86b22e2297956b6744ca1d9b660` | Historical synthetic CI archive attestation with GitHub OIDC/Sigstore identity and second GitHub-hosted runner verification | Authenticates a GitHub workflow attestation for a synthetic archive, not an owner-authorized T0 checkpoint signer or separation from T0 admin authority |
| `docs/evidence/T0_L4_MINIMUM_NINE_CONTROL_EVIDENCE_ACQUISITION_REGISTER_2026-11-10.md` | `e67a58591b5f6168ab3a0f3f403557292aca45d5` | Explicitly records missing signer evidence and acquisition restrictions | No actual signer identity, custody or recovery evidence is present |

## 3. Required proof not found

The current reviewed evidence does not provide:

1. An owner-approved signer role/identity and stable public-key or certificate fingerprint for T0 checkpoint signing.
2. The signer key's custody boundary, including who/what can authorize use and how recovery is controlled.
3. A technically evidenced boundary proving ordinary T0 runtime credentials and T0 host/database administrators cannot access the private key, invoke a signing service, or authorize signing.
4. An explicit authorization path binding the owner-approved signer to the exact checkpoint identity/digest and dataset scope.
5. A documented signer-loss/recovery path with authorization and substitution controls.
6. A separately authorized isolated proof that the T0 runtime/admin boundary cannot produce an accepted owner signature.

A policy statement, code comment, public-key verifier, ephemeral test key, GitHub OIDC identity, repository permission model, or absence of a signing API in one module is not sufficient proof of the complete authority boundary.

## 4. What can safely be concluded

- The synthetic event-signature module is verifier-only and does not itself hold private keys.
- The tests create ephemeral private keys solely to exercise synthetic signature behavior.
- The P1.8.14 Sigstore identity is tied to the GitHub Actions workflow/repository context and synthetic archive subject.
- The checked-in Sigstore trust-root history is not a T0 owner signer registry or custody system.
- No evidence reviewed establishes production signing integration or T0 runtime/admin inability to sign.

These are bounded source/document observations, not a proof that no signing capability exists elsewhere in an uninspected environment.

## 5. Next admissible owner evidence

After the owner identifies an already-existing approved signer arrangement, supply sanitized references only:

- signer role and non-personal identity label;
- public certificate/key fingerprint (never private key bytes);
- custody and recovery boundary at a high level;
- authorization-policy/version reference and approval lineage;
- evidence describing why T0 runtime/admin credentials cannot access or invoke the signer;
- exact scope of the signature authorization (checkpoint digest/object ID);
- status of an isolated proof, marked `NOT RUN` unless separately authorized and actually performed.

Do not provide private keys, seed phrases, credentials, account identifiers, secret URLs or access grants. If no approved signer exists, record `NOT AVAILABLE`; do not create one under this assessment.

## 6. Restrictions and final disposition

- L4M-02: **NOT VERIFIED**.
- No signer identity, custody or recovery proof accepted.
- No tests, key generation/import/export/rotation, signing, provider calls, permission probes, workflow dispatch, runtime/VPS/database/network changes or owner-system access performed.
- No source code or trust policy changed.
- Option C — No Destructive Authority — REVOKED by owner decision 2026-11-11; see the owner governance update below.
- Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders.

This assessment does not authorize a future signing design or operation. Any implementation, key/provider selection, permission change or isolated execution requires separate explicit owner approval.


## Owner governance update — Option C revoked (2026-11-11)

The owner explicitly revoked **Option C — No Destructive Authority** on 2026-11-11. Its former ACTIVE status in this document is historical and is superseded by this decision. Option C is now **REVOKED**; do not apply it as a blanket prohibition.

This governance revocation is not a blanket instruction to execute deletion or cleanup. Any specific destructive operation still requires a separately scoped plan identifying exact target/data class, operation, retention/impact, preconditions, verification, recovery/rollback and explicit approval. T0 canonical data, lease/fencing state, ledgers, audit/reconstruction/recovery evidence and owner custody records remain protected unless an exact operation is separately approved. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged. Revocation does not promote any L4 control or establish custody/signature/offline-verification assurance.
