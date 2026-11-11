# T0 L4 — Exact-object Signature and Negative-verification Design Refresh

Date: 2026-11-12  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Work type: **READ-ONLY CONTRACT / EVIDENCE REVIEW**  
Disposition: **DESIGN PARTIAL — IMPLEMENTATION AND L4 ACCEPTANCE BLOCKED**

## 1. Purpose and boundary

Refresh the prior 2026-11-11 signature/negative-verification architecture review against the current Checkpoint Contract v1, A1, A2.2, A2.3 and L4 custody evidence after the eight-item Actions source inventory was verified.

This is a documentation-only review. No source/test/workflow/dependency changes, key operation, signing, cryptographic verification, trust-root/bootstrap mutation, Trust Policy/Monotonic Anchor state, VPS/T0/SQLite access, custody publication, provider/TSA operation, destructive data action or trading occurred.

## 2. Exact current source baseline

| Source | Exact blob SHA | Review use |
|---|---|---|
| `docs/architecture/T0_EVIDENCE_OBJECT_CHECKPOINT_CONTRACT_V1.md` | `a6825270d59bde274bfe765d5f942144b66a84de` | Current v1 plus owner-approved bounded VPS + GitHub custody addendum |
| `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A1_2026-11-11.md` | `00fdad293e129562145ab930507a4e6b9c2bf23d` | Signature Statement, Trust Policy, Anchor and negative-verification model |
| `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A2_2_2026-11-11.md` | `d9f93bf390d107381b7135c3073aeca0d14894d4` | Exact digest domains and T0-JCS-1 numeric grammar |
| `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A2_3_DRAFT_2026-11-11.md` | `41d6abfc9df20047af4668b80a6ce2edb7e07117` | Authorization Evidence Object (AEO), detached descriptor and proposed resource limits |
| `docs/evidence/T0_SIGNATURE_A2_2_STAGE_II_ED25519_ADAPTER_CONTRACT_2026-11-11.md` | `8ec916c152c51e75c5a3852e7977dd7f1239d8fe` | Stateless Ed25519 adapter boundary |
| `docs/evidence/T0_SIGNATURE_A2_2_STAGE_II_V1_FIELD_MAPPING_REVIEW_2026-11-11.md` | `1185a3bf65d66c8cd203bd1dbc7994fdca0b1ad1` | v1/A1 field mapping and B + E2 owner choice |
| `docs/evidence/T0_SIGNATURE_A2_3_SELF_REVIEW_2026-11-11.md` | `038b17c9f2cc699b3db54f4ce06d517cf61fa665` | A2.3 self-review findings |
| `docs/evidence/T0_SIGNATURE_A2_3_PYCA_DEPENDENCY_CANDIDATE_2026-11-11.md` | `9092b2cf5a9e9308d28e8436c8b91e2f9566ef4e` | Proposed cryptographic dependency pin/provenance |
| `docs/evidence/p1-8/L4-MINIMUM-PROVENANCE-ACCEPTANCE-MATRIX.md` | `7c413504db397877b308345b21c9f6f58271c89a` | Controlling L4 acceptance requirements |

The earlier architecture review `T0_SIGNATURE_NEGATIVE_VERIFICATION_ARCHITECTURE_REVIEW_2026-11-11.md` (blob `02fa7464e26416c85a2be6ae3f478de60ff265fa`) reviewed an earlier branch baseline and stale checkpoint/crosswalk blobs. Its historical findings remain useful, but it is not a current-baseline closure review.

## 3. Findings

### F-01 — Content and checkpoint foundation: PARTIAL

Checkpoint Contract v1 defines canonical T0-JCS-1 bytes, exact object digests, row/partition commitments, completeness, snapshot and durability dimensions, Signature Envelope, Custody Receipt, Verification Record, latest-head anchor and negative cases.

The contract remains **DRAFT / documentation-only**. G2 synthetic conformance is not the same as current exact-commit cryptographic signature verification. Current L4 artifact inventory does not prove the canonical T0 snapshot, durable commit, or owner custody.

### F-02 — Signature primitive boundary: DESIGN MAPPED, NOT IMPLEMENTED

Owner decisions recorded in the current draft select Ed25519 PureEdDSA, strict DER SPKI public keys, exactly 64 raw signature octets, and exact caller-supplied preimage bytes. The adapter is intended to be stateless and must not decide signer identity, trust, role, purpose, revocation, anchor freshness, custody or acceptance.

The adapter contract is not frozen. No production cryptographic adapter or real signature verification has been implemented or authorized.

### F-03 — AEO and detached descriptor: REPRESENTATION SELECTED, SCHEMAS NOT FROZEN

Owner selected Option B + E2:
- three A1 §14.4 provenance/authorization references are carried by a separately signed Authorization Evidence Object;
- the main Signature Statement binds the AEO through an immutable descriptor;
- envelope identity uses a detached descriptor with independently assigned opaque ID.

Still open:
1. exact AEO field schema, cardinality, issuer namespace and canonicalization;
2. AEO signature domain/preimage and signer-role/trust-chain contract;
3. explicit owner decision on AEO issuer separation from the subject checkpoint signer;
4. detached descriptor canonical schema, namespace authority, ID allocation, collision, retry and abort/replacement semantics;
5. Verification Record schema, retention and append-only enforcement;
6. stable public reason-code compatibility policy, if externally consumed.

### F-04 — Resource limits: PROPOSED, NOT FROZEN

A2.3 proposes bounded object/parser/input-set ceilings, including a 16 MiB total frozen verification input set and bounded dependency count/size. The adapter draft also has proposed preimage/SPKI/signature ceilings.

These values are not frozen constants. They need one internally consistent limit table across A2.3 parsers, descriptor/AEO validation and the adapter boundary, with tests for exact-boundary and over-limit inputs.

### F-05 — Dependency/build provenance: NOT VERIFIED

The proposed `cryptography==50.0.2` wheel/hash is a candidate, not a verified lock. The exact wheel bytes have not been downloaded and independently hashed in this repository. Transitive dependency closure, upstream provenance verification, runner/glibc compatibility, offline installation and build provenance remain open. No package was installed and no lockfile was changed.

### F-06 — Trust, anchor and custody: BLOCKED / NOT VERIFIED

The bounded custody design accepts VPS + GitHub, with the explicit limitation that joint rollback of both locations cannot be detected. The former VPS was deleted; no replacement host is established. Current evidence inventory and Actions artifacts are GitHub-hosted only.

No owner-controlled two-location object/anchor readback, authenticated trust bootstrap, actual signer authority evidence, Trust Policy/Monotonic Anchor instance, offline owner verification or append-only Verification Record store is established. Synthetic trust-root fixtures cannot substitute for real custody or trust evidence.

### F-07 — Independent-review gate: OWNER-WAIVED, NO ASSURANCE CLAIM

The Owner has withdrawn the requirement that a qualifying independent security review be a mandatory gate for Stage II A2.3/Ed25519 adapter work. Any contrary mandatory-review wording in the A2.3 draft is superseded by this later Owner instruction and must be harmonized in a dated governance addendum before implementation.

This waiver does **not** convert same-session self-review into independent review and does not establish G3, external assurance, cryptographic certification or a production security claim. All remaining technical, contract-freeze, dependency/build-provenance and exact-scope authorization gates remain.

## 4. Negative-verification coverage required before any implementation request

The A1/A2.3 matrices cover mutation, wrong key, wrong purpose/audience/profile, malformed/noncanonical bytes, key-role mismatch, unknown/revoked key, policy rollback/equivocation, stale anchor replay, missing/conflicting custody copy, missing offline dependency, descriptor ID reuse, AEO substitution/self-issuance and append-only record overwrite.

Before implementation, every fixture must have a single intended mutation, exact expected dimension result, aggregate disposition and stable primary reason code. Every rejected/error path must prove no policy, anchor, accepted-checkpoint, trust-root or verification-history state advancement. Test vectors must not use the implementation helper as their own oracle.

## 5. Recommended next sequence

1. Harmonize the A2.3 draft with the Owner's independent-review waiver without making any G3/assurance claim.
2. Close the AEO issuer-separation decision and freeze the exact AEO statement/body/package schemas and signature preimage.
3. Freeze detached descriptor schema, namespace/ID allocation, uniqueness, retry and conflict behavior.
4. Freeze one cross-layer resource-limit table and stable result/reason-code contract.
5. Independently verify the exact PyCA wheel bytes, dependency closure and provenance/build inputs; then freeze the exact dependency lock and supported CI environment.
6. Freeze the exact A1/A2.2/A2.3 contract blobs and a bounded implementation/test/CI scope.
7. Request separate explicit Owner authorization for implementation. No automatic progression to real keys, trust bootstrap, anchor state, custody publication, VPS/T0/runtime or trading.

## 6. Disposition

- Current exact-object signature design: **PARTIAL**.
- AEO/descriptor schema freeze: **BLOCKED**.
- Resource ceilings: **NOT FROZEN**.
- Dependency/build provenance: **NOT VERIFIED**.
- Trust bootstrap, anchor and actual custody: **BLOCKED / NOT VERIFIED**.
- Independent security review: **WAIVED as a mandatory gate by Owner; NOT PERFORMED; no independent-assurance/G3 claim**.
- Stage II implementation and CI: **NOT AUTHORIZED until the remaining contract/build gates close and a separate exact-scope authorization is recorded**.
- L4-Minimum aggregate: **BLOCKED / NOT VERIFIED**.

No tests were run because this is a read-only, documentation-only review. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.


## 7. PyPI dependency provenance spot-check (2026-11-12)

The proposed dependency candidate was checked against the official PyPI release page for `cryptography==50.0.2`.

- PyPI lists `cryptography-50.0.2-cp311-abi3-manylinux_2_34_x86_64.whl` as a CPython 3.11+ stable-ABI Linux x86-64 wheel requiring glibc 2.34+, approximately 4.8 MB.
- PyPI displays SHA-256 `9dab55f57c74c3cad24c323bacbbd04be4705ba6eb0d92e920b1fc4837ed5079`, matching the candidate evidence document.
- PyPI marks this file as having provenance, signed by GitHub Actions and verified by PyPI on 2026-09-30. Published repository identity: `pyca/cryptography`; publishing commit `fe12d283180ea89ceed622021242fddb31d27f84`; workflow `.github/workflows/pypi-publish.yml`; publishing run `36731020563`.
- Official source: https://pypi.org/project/cryptography/50.0.2/ (release file details and provenance metadata).
- An attempt to download the exact wheel bytes into the review environment failed. Therefore no independent SHA-256 calculation, Sigstore bundle verification, or offline provenance verification was completed.
- **Disposition: OFFICIAL PYPI METADATA / DECLARED HASH / PROVENANCE PRESENCE — CORROBORATED; EXACT WHEEL BYTES AND ATTESTATION CRYPTOGRAPHIC VERIFICATION — NOT VERIFIED.** This does not authorize installing the package, freezing the dependency, changing lockfiles or CI.
