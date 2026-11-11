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


## 8. Frozen read-only verifier v1 implementation (2026-11-11)

Owner approved RFC 8785 JCS, Ed25519 verification and an independently pinned public-key configuration. The following implementation was added on the existing active branch:

- `pipeline/calibration_registry.py`: strict manifest v1 field/schema validation; duplicate-key and JSON-number rejection; exact UTF-8/JCS byte equality; SHA-256 exact artifact-byte digest and length; strict detached envelope bindings; raw Ed25519 public-key verification; independent key fingerprint, signer role, publisher, namespace and record-type scope pinning.
- `pipeline/test_ai_calibration_registry.py`: 14 deterministic tests, including valid RFC 8032 test-only fixture verification and negative cases for noncanonical bytes, duplicate keys, JSON numbers, schema mismatch, manifest/signature tampering, artifact digest/size, wrong key pin, wrong signer/publisher scope envelope binding, sequence predecessor semantics and horizon-aware OOS embargo. The test-only seed is not a production key and is not used outside tests.
- `requirements-web.txt` and `requirements.txt`: added `cryptography>=42.0.0,<47` and `rfc8785>=0.1.4,<0.2`.
- `.github/workflows/ai-strategy-contract-red.yml`: added compile and focused test execution for the verifier.

Exact verification:
- Workflow run: [43065112950](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43065112950), job `130677863812`, checked out source SHA `ee5a649cdd5b24adc25ff2083b6dee820f5717af`.
- Compile: PASS.
- Calibrated confidence/provenance tests: 13 PASS.
- Existing AI decision regression: 15 PASS.
- Registry verifier tests: 14 PASS (including sequence/genesis and horizon-embargo boundaries).
- Full AI/dual-strategy RED contract: 52 tests, 12 failures and 6 errors. Remaining failures concern leverage mapping, equity readiness/sizing, instrument lot/tick/minimum rules, Kill Switch and API/AI-ledger routing. They are not represented as verifier regressions or PASS.
- Artifact ID `13875776318`, name `ai-strategy-contract-red-ee5a649cdd5b24adc25ff2083b6dee820f5717af`, upload ZIP SHA-256 `02491d09b1aa41e24b4140999030aa4e977819677f09ab25539408da79c914e1`.

Verifier output is deliberately only `SIGNATURE_VERIFIED_ONLY`. It does not verify registry predecessor/event history, promotion/active/revocation state, trusted time, evaluation-record bytes/metrics, dataset lineage or OOS statistical quality. It does not generate a calibrated confidence from the transform artifact and is not wired as a production provider. The normal API path continues to fail closed; no production key/fingerprint, manifest, calibration artifact, Owner promotion, provider, model/training job, registry state, runtime or live execution was created.

**Disposition:** verifier implementation and focused tests PASS; overall AI confidence/provenance completion BLOCKED pending a real independently pinned trust configuration, approved calibration transform/evidence lineage, promotion/revocation state and per-inference confidence binding. No production admission is enabled.


### 8.1 Verifier hardening follow-up

- Added bounded canonical unsigned integer-string parsing (uint64) for sequence, byte length, sample count and horizon.
- Enforced GENESIS only for sequence 1; later records must carry a predecessor digest. This validates local record shape only; the full predecessor chain and rollback/equivocation state are not fetched or verified.
- Enforced calibration start no earlier than training cutoff plus the declared forecast-horizon embargo, and artifact creation no earlier than calibration end.
- Exact follow-up CI: run `43065750329`, job `130680105605`, source SHA `cbfef9b48dfd996f7788e80f8f62f9c92a51628d`. Compile PASS; calibrated confidence/provenance 13 PASS; decision regression 15 PASS; registry verifier 14 PASS. Full AI/dual-strategy RED remains 52 tests, 12 failures and 6 errors due the separately outstanding leverage/equity/instrument/Kill Switch/ledger contracts.
- Artifact ID `13875077587`, name `ai-strategy-contract-red-cbfef9b48dfd996f7788e80f8f62f9c92a51628d`, upload ZIP SHA-256 `1a82bd0eeb050956adecb54281723650e2905a714996d256d8d8e05a6238f73c`.
