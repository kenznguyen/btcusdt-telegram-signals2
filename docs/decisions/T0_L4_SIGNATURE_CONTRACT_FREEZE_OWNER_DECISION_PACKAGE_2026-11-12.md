# Owner Decision Package — T0 L4 Signature Contract Freeze

Date: 2026-11-12  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Status: **PROPOSAL ONLY — NO CONTRACT FREEZE OR IMPLEMENTATION AUTHORITY**

## 1. Purpose

Present the remaining owner decisions required to freeze the A2.3 Authorization Evidence Object (AEO), detached envelope descriptor and Stage II Ed25519 adapter contracts after the 2026-11-12 read-only design refresh.

This package is not an approval record. It does not modify A1/A2.2/A2.3, select a production trust root, instantiate a Trust Policy/Monotonic Anchor, install dependencies, create keys, sign or verify real evidence, dispatch CI, access VPS/T0, publish custody evidence or authorize implementation.

## 2. Exact baseline

- Checkpoint Contract v1: blob `a6825270d59bde274bfe765d5f942144b66a84de`.
- A1: blob `00fdad293e129562145ab930507a4e6b9c2bf23d`.
- A2.2: blob `d9f93bf390d107381b7135c3073aeca0d14894d4`.
- A2.3 draft: blob `41d6abfc9df20047af4668b80a6ce2edb7e07117`.
- Stage II Ed25519 adapter contract: blob `8ec916c152c51e75c5a3852e7977dd7f1239d8fe`.
- Current design refresh: `docs/evidence/T0_L4_SIGNATURE_NEGATIVE_VERIFICATION_REFRESH_2026-11-12.md`.

Owner-selected architecture patterns already recorded:
- Ed25519 PureEdDSA; strict DER SPKI public key; exactly 64 raw signature octets.
- Option B: separately signed AEO contains signer provenance/authority/custody evidence; main checkpoint Signature Statement binds its exact package descriptor.
- Option E2: detached envelope descriptor with non-self-referential opaque identity.
- Independent security review is waived as a mandatory gate by later Owner instruction; no independent assurance/G3 claim is implied.

## 3. Owner decisions requested

### D1 — AEO issuer separation

**Status: OWNER APPROVED — 2026-11-12**

**Decision: Option A — AEO issuer MUST be distinct from the subject checkpoint signer.**

- AEO issuer principal MUST differ from the subject checkpoint signer principal.
- AEO issuer SPKI fingerprint MUST differ from the subject checkpoint signer SPKI fingerprint.
- Same principal or same SPKI fingerprint MUST be rejected with `AUTHORIZATION_EVIDENCE_SELF_ISSUED`.
- This approval freezes the D1 policy decision only. It does not freeze the complete AEO schema, issuer namespace/authority contract, signature preimage, trust chain, or authorize implementation, key operations, trust bootstrap or real evidence signing/verification.

Owner response: “có” (yes), in this conversation on 2026-11-12.

### D2 — Freeze proposed resource ceilings

**Question:** Adopt the current A2.3 §9 limits as normative v1 ceilings?

| Input | Proposed ceiling |
|---|---:|
| AEO body | 1,048,576 bytes |
| Canonical Signature Statement | 1,048,576 bytes |
| Fully prefixed signature preimage | 1,048,640 bytes |
| SPKI DER | 4,096 bytes |
| Ed25519 signature | exactly 64 bytes |
| Canonical signature envelope | 1,114,112 bytes |
| Detached descriptor | 65,536 bytes |
| Each nested evidence dependency | 1,048,576 bytes |
| Dependencies per AEO package | 64 |
| Total frozen verification input set | 16,777,216 bytes (16 MiB) |
| JSON nesting depth | 32 |
| Object members | 256 |
| Array elements | 256 |
| UTF-8 string length | 16,384 bytes |

- Option A (recommended): adopt these exact ceilings, with boundary and over-limit negative tests.
- Option B: defer numeric limits until a separate measurement exercise. If selected, the verifier remains NOT READY for real evidence and must fail closed on unbounded inputs.

Recommendation: Option A for the bounded offline verifier. These are parser/resource ceilings, not evidence-retention or data-deletion limits.

### D3 — Freeze AEO and descriptor schemas

**Question:** Freeze the exact AEO body, AEO Signature Statement, package descriptor and detached envelope descriptor field sets from the current A2.3 draft, with only corrections required by D1/D2?

- Option A (recommended): freeze exact field sets and canonicalization after cross-contract consistency checks; unknown fields rejected; `extensions` remains empty in v1; no mutable URL/display-label substitution.
- Option B: defer schema freeze and keep Stage II blocked.

The descriptor draft uses `urn:uuid:<lowercase-canonical-UUIDv4>`, an independently assigned opaque ID, hard conflict on same ID/different bytes, idempotency only for exact same bytes, and exact readback before retry after uncertain write. The contract still needs to identify the authorized issuer namespace and its authority boundary; do not infer a production issuer identity from a draft role name.

### D4 — Verification Record contract

**Question:** Approve a separate schema-only contract for append-only Verification Records, with no storage/runtime implementation?

Recommended minimum binding:
- immutable verification record ID and schema version;
- exact envelope descriptor ID/type/schema and envelope digest/length;
- frozen verification input-set ID/digest;
- verifier source/build identity and version;
- per-dimension results and stable reason codes;
- aggregate disposition;
- local observation time explicitly untrusted;
- predecessor record digest or explicit first-record reason;
- no overwrite; duplicate exact record is idempotent; conflicting same-ID bytes fail closed.

This schema-only approval would not authorize a database, event ledger, VPS service, anchor writer, custody publication or persistent state.

## 4. Non-owner technical gates

These do not require a policy choice but must be closed before implementation:

1. Reconcile A1/A2.2/A2.3/adapter contract field and domain mappings against exact blobs.
2. Independently download and hash the exact PyCA wheel. Official PyPI metadata currently declares the expected hash and provenance, but the exact binary download in the review environment failed; payload hash and Sigstore attestation verification remain NOT VERIFIED.
3. Freeze transitive dependency closure, runner/platform/glibc compatibility, wheel provenance verification and offline installation procedure.
4. Freeze deterministic positive/negative vectors and state-immutability assertions.
5. Freeze exact source blobs, allowed paths, test commands and CI scope.

The Owner's waiver means independent security review is not a mandatory gate. It does not waive the above technical gates and does not create G3.

## 5. Explicit non-authorizations

No production key generation/import/signing; no private-key handling; no trust-root enrollment or bootstrap; no Trust Policy/Monotonic Anchor instance or durable state; no provider/TSA; no VPS/SSH/T0/SQLite/Feeder/API/runtime; no package installation or CI workflow change; no custody publication; no deletion/retention/cleanup; no T1 activation; no training/calibration/OOS execution; no AI admission or trading.

## 6. Decision response format

Owner may approve/reject each D1–D4 independently. Partial approval is valid. Any rejected/deferred item remains OPEN and blocks full contract freeze. This package must not be interpreted as approval by silence or by prior unrelated approval.

**Current disposition: DECISION PACKAGE PREPARED; OWNER DECISIONS PENDING; A2.3 NOT FROZEN; STAGE II IMPLEMENTATION NOT AUTHORIZED; L4-MINIMUM BLOCKED / NOT VERIFIED.**
