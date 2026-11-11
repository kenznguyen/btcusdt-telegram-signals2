# AI Calibration Manifest and Ed25519 Lifecycle Design Review

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Pre-work source reference: `f58bf6a203e8dd663003eeff97ad7580dcbb9c57`

## 1. Authorized scope

The owner requested completion of the documentation design for:
- calibration registry manifest structure;
- Ed25519 key generation ceremony;
- public-key pinning and signature verification;
- custody and backup;
- routine rotation;
- revocation and compromise response;
- recovery after loss, corruption or repository compromise.

The scope is **documentation only**. No key generation/import, signature operation, production cryptography, trust-root enrollment, registry creation, CI/workflow, runtime provider, VPS, database, T0/T1/T2, exchange connectivity or AI activation is authorized.

## 2. Documents added

1. `docs/architecture/AI_CALIBRATION_REGISTRY_MANIFEST_CONTRACT.md`
   - Proposed immutable record model: manifest, evaluation evidence, registry events, detached signature envelope and trust configuration.
   - Proposed manifest field inventory for model/strategy/dataset/label/horizon/calibrator provenance.
   - Detached signature to avoid circularity; SHA-256 over exact canonical payload bytes; signature binds a versioned purpose/namespace/digest/length statement.
   - Exact GitHub commit/path/blob SHA and SHA-256 evidence binding; branch names and mutable URLs are not object identities.
   - Append-only candidate/approved/active/superseded/revoked/withdrawn events.
   - Explicit separation from T0 canonical data and from the T0 A2.2 checkpoint-attestation purpose.

2. `docs/architecture/AI_CALIBRATION_ED25519_KEY_LIFECYCLE_CONTRACT.md`
   - Proposed ROOT, CALIBRATION_SIGNER and independent RECOVERY_AUTHORITY roles.
   - Offline CSPRNG-based key generation ceremony; no generation on CI, VPS or runtime.
   - Encrypted offline custody and independently separated backup.
   - Pre-sign validation, detached signature, independent verification and readback.
   - Out-of-band public-key fingerprint pinning.
   - Planned overlapping rotation, append-only supersession and immediate fail-closed revocation.
   - Compromise, lost-key, root-loss, root-compromise, backup-corruption and repository-compromise recovery.
   - Historical verification and trusted-time limitations.

## 3. Important architecture boundaries

- T0 A2.2 is a separate checkpoint issuer-attestation protocol. Its profile, Trust Policy, Monotonic Anchor, role authorization and bootstrap do not automatically authorize AI calibration signing.
- A future cross-contract review may assess reuse of canonicalization or cryptographic primitives, but code reuse does not imply trust-authority reuse. No T0 A2.2 production cryptography or trust bootstrap was invoked.
- GitHub commit history is content-addressed evidence, not a WORM guarantee, independent trust root or proof of global latestness.
- SHA-256 proves exact bytes; Ed25519 verifies authorization by a pinned key; neither establishes statistical calibration quality or absence of data leakage.
- No static calibrated-confidence value is stored in the calibration artifact. The artifact defines a transform; each inference has its own calibrated confidence bound to the exact artifact version/digest.
- Local/Git commit timestamps are not trusted signing time. Where compromise timing cannot be established, historical trust must remain UNKNOWN/BLOCKED.

## 4. Remaining decisions

The documents are proposals, not frozen implementation contracts. Still open:
- repository path, branch-protection and independent backup/custody model;
- manifest schema and exact canonicalization profile;
- signature statement bytes/domain separator/envelope schema;
- trust-root and recovery bootstrap topology;
- key encoding/fingerprint format, accepted tooling and custody media;
- rotation overlap, lifetime, trusted-time and compromise-boundary rules;
- calibration method, OOS protocol, promotion authority and numerical thresholds;
- Binance instrument-rule provider G0-05 and reservation snapshot G0-07.

## 5. GitHub change record

- Manifest contract added: commit `90436bd56b577f39cccec6ee309ee69798218a88`.
- Key lifecycle contract added: commit `aa5a5f5c75d7e2efb5744aeef5572596957346ce`.
- Both were committed to the existing active branch; no parallel branch or PR was created.
- Evidence record and plan/handoff references are appended in the subsequent documentation commits for this increment.

## 6. Verification and disposition

- Document content was created through GitHub repository file operations on the active branch.
- No tests were run because no executable code or workflow changed.
- No workflow was dispatched; no artifact was produced.
- No key was generated/imported; no signature was created or verified.
- No network request, exchange endpoint, database, VPS or runtime was accessed.

**Disposition**
- Manifest design: **DRAFTED / OWNER REVIEW REQUIRED**.
- Key lifecycle design: **DRAFTED / OWNER REVIEW REQUIRED**.
- Registry schema/canonicalization freeze: **NOT FROZEN**.
- Trust bootstrap/key ceremony authorization: **NOT AUTHORIZED**.
- Calibration provider/OOS thresholds G0-01/02/03: **BLOCKED**.
- Instrument rules G0-05: **BLOCKED**.
- Reservation evidence G0-07: **DEFERRED**.
- GREEN-1 through GREEN-5: **NOT AUTHORIZED**.
- Paper-only posture and `AI_EXECUTION_ENABLED=false`: unchanged.

## 7. Next gate

Review and approve/revise the manifest field contract, canonicalization approach, key-role topology and recovery authority. After those design choices are frozen, a separate owner decision is required before any key ceremony, production signing/verifying code, CI workflow, registry provider or AI admission integration.
