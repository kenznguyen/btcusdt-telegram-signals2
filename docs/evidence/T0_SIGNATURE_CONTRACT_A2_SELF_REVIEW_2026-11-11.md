# T0 Signature Contract A2 — Adversarial Self-Review

Date: 2026-11-11  
Review type: same-session adversarial self-review; not independent review  
Disposition: **REQUEST CHANGES — A2 IS NOT IMPLEMENTATION-READY**

## 1. Exact reviewed snapshot

Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

| Source | Exact blob SHA |
|---|---|
| A2 `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A2_2026-11-11.md` | `e15a90b779bd86b39729208db938e9de9471ef26` |
| A1 `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A1_2026-11-11.md` | `00fdad293e129562145ab930507a4e6b9c2bf23d` |
| Checkpoint Contract v1 `docs/architecture/T0_EVIDENCE_OBJECT_CHECKPOINT_CONTRACT_V1.md` | `a6825270d59bde274bfe765d5f942144b66a84de` |
| L4 crosswalk `docs/evidence/T0_L4_CONTROL_TO_SOURCE_CROSSWALK_2026-11-11.md` | `e560f084642b5f81c78179ef673e5df116fc5f42` |

A2 was fetched back from the active branch after its final formatting correction. A1, the base contract and crosswalk were also fetched and their current blobs match the pinned inputs above. No reviewed source was edited during this review.

## 2. Scope and method

Static adversarial review covered:
- all eight prior findings SR-01–SR-08;
- purpose semantics and owner-intent boundary;
- provenance field mapping and envelope identity;
- anchor state machine, linearization point and crash recovery;
- negative-test IDs, deterministic primary reason codes and state assertions;
- U64/base64url grammar and boundary vectors;
- bootstrap record, key pinning and recovery;
- precedence against A1 and Checkpoint Contract v1;
- preservation of bounded VPS + GitHub custody and unchanged implementation gates.

No cryptographic implementation, keys, signatures, trust bootstrap, anchor instance, runtime, database or live evidence was exercised. This review is not independent assurance and cannot satisfy G3.

## 3. Closure assessment of prior findings

| Prior finding | A2 assessment |
|---|---|
| SR-01 owner-attestation semantics | **ADDRESSED AT DRAFT LEVEL** — issuer-attestation purpose replaces owner-intent implication; separate Owner Authorization object required for any owner claim. |
| SR-02 provenance and envelope ID mapping | **ADDRESSED AT DRAFT LEVEL** — explicit signed fields, referenced evidence descriptors and pre-signing envelope ID. |
| SR-03 anchor crash consistency | **ADDRESSED AT DRAFT LEVEL** — durable transition states, a sole HEAD_COMMITTED linearization point, partial-publication recovery and no sequence skip. Durable technology/authority remains unselected. |
| SR-04 nondeterministic negative cases | **ADDRESSED AT DRAFT LEVEL** — 43 numbered cases and stable primary reason codes; A2-NV-40 is an explicitly ordered recovery test. |
| SR-05 U64/base64url boundaries | **ADDRESSED AT DRAFT LEVEL** — unsigned 64-bit grammar, boundary vectors and canonical base64url examples. |
| SR-06 common-mode rollback test classification | **ADDRESSED** — retained as a non-claim/assurance-boundary assertion, not a detection test. |
| SR-07 snapshot/draft terminology | **ADDRESSED** — distinguishes byte-frozen review candidate, draft, owner decision and implementation approval. |
| SR-08 bootstrap record | **PARTIAL** — bootstrap schema and out-of-band pinning are defined, but the owner authorization evidence's independent verification contract remains incomplete. |

## 4. New findings

### A2-SR-01 — HIGH: legacy owner-attestation purpose is not explicitly rejected by A2 verifiers

**Source:** A2 §§2.1, 3.1 and 9.

A2 states that `T0_CHECKPOINT_OWNER_ATTESTATION` is superseded by `T0_CHECKPOINT_ISSUER_ATTESTATION`, but it does not explicitly say that an A2-conforming verifier and Trust Policy MUST reject the legacy purpose value for A2 objects. A compatibility implementation could continue accepting the old purpose under an A1 policy path, preserving the exact semantic ambiguity A2 is intended to remove.

**Required correction:** State that A2 profile/version and policy entries MUST authorize only `T0_CHECKPOINT_ISSUER_ATTESTATION` for this checkpoint-signature flow. The legacy owner-attestation value MUST be rejected for A2 objects with a stable reason code (for example `PURPOSE_NOT_SUPPORTED_BY_PROFILE`). It may be interpreted only when verifying an explicitly versioned historical A1 object under its historical rules; it MUST NOT be silently upgraded or relabeled.

### A2-SR-02 — MEDIUM: owner authorization evidence in bootstrap has no complete independent verification contract

**Source:** A2 §7.1–§7.2.

The bootstrap record contains `owner_authorization_evidence_id` and an out-of-band pinned root public key, but does not fully define the authorization-evidence schema, its issuer/authority, exact signed subject, or how the verifier validates that evidence without circularly trusting the root whose enrollment it is intended to authorize.

**Required correction:** Define the bootstrap authorization as either (a) an owner-signed bootstrap authorization under a separately pre-pinned owner authority, independent of the root being enrolled, or (b) a documented owner-controlled provisioning ceremony whose exact record digest is pinned by the verifier through an independent channel. Bind the bootstrap record digest, namespace, audience, root SPKI fingerprint, role, profile, sequence and recovery policy. Explicitly prohibit using the newly enrolled root as the sole authority to authenticate its own initial enrollment. If no such independent owner authority/ceremony evidence is available, bootstrap remains BLOCKED.

## 5. Residual implementation blockers (not defects to silently decide here)

Even after the two findings above are corrected, implementation remains blocked pending:
- production signature algorithm/profile and key encoding;
- owner-controlled bootstrap and recovery ceremony;
- actual checkpoint signer and anchor authority identities;
- durable anchor journal technology and operational recovery qualification;
- trusted-time decision if historical trust-at-time is required;
- exact retention/recovery policy;
- independent second implementation and byte-vector conformance;
- qualifying independent review of the exact corrected A2 snapshot;
- separate explicit owner implementation approval.

The durable journal state machine is specified at contract level, but no storage technology or operational authority is selected by this review.

## 6. Static consistency checks

The fetched A2 source passed these content checks:
- all 43 A2-NV IDs are present;
- no malformed literal escaped-newline remains in the test matrix;
- issuer-attestation semantics and separate owner-authorization boundary are present;
- provenance fields and signature-envelope digest rule are present;
- anchor states and HEAD_COMMITTED linearization point are present;
- U64 maximum, U64BE boundary and base64url vectors are present;
- bootstrap schema and draft/frozen terminology are present;
- no implementation authorization is claimed.

These are document consistency checks only, not executable tests or cryptographic conformance evidence.

## 7. Overall disposition

**REQUEST CHANGES.** A2 substantially addresses SR-01–SR-08 at contract-design level, but A2-SR-01 and A2-SR-02 must be resolved before freezing A2 for independent review. The exact reviewed A2 blob remains preserved for traceability. Any correction must create a new A2 candidate blob and repeat self-review.

Independent review: **NOT PERFORMED**.  
Implementation: **BLOCKED**.  
CI/workflow: not run as part of this document review.

## 8. Unchanged boundaries

No code, tests, workflow, CI configuration, key, signature, trust root, policy instance, anchor instance, provider/TSA, VPS/SSH/runtime, SQLite database, canonical T0 data or destructive operation was changed or exercised. The bounded VPS + GitHub custody limitation remains unchanged. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.
