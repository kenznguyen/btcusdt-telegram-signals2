# T0 Signature / Trust Policy / Monotonic Anchor — Final Consistency Review

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Review type: same-session static contract consistency review  
Disposition: **CONSISTENCY CHECKS PASS — REVIEW CANDIDATE FROZEN FOR INDEPENDENT REVIEW; IMPLEMENTATION BLOCKED**

## 1. Exact review snapshot

Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Source HEAD at review freeze: `838f912139562eb185ad6035e95fd08810071525`

| Source | Exact blob SHA | Purpose |
|---|---|---|
| `docs/architecture/T0_EVIDENCE_OBJECT_CHECKPOINT_CONTRACT_V1.md` | `a6825270d59bde274bfe765d5f942144b66a84de` | Base contract plus owner-approved bounded custody addendum |
| `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A1_2026-11-11.md` | `00fdad293e129562145ab930507a4e6b9c2bf23d` | Signature statement, trust policy, anchor and 30 negative cases |
| `docs/evidence/T0_L4_CONTROL_TO_SOURCE_CROSSWALK_2026-11-11.md` | `e560f084642b5f81c78179ef673e5df116fc5f42` | Current control dispositions and exact contract/A1 pins |

This snapshot is frozen for review. Any change to these three source documents requires a new snapshot and renewed review of the changed bytes.

## 2. Scope

Reviewed for cross-document consistency:
- Checkpoint Contract v1 §§6–9, §13.2 G1 role/custody decisions and the dated owner-approved custody addendum.
- A1 §§1–14, including canonical bytes, signature statement/preimage, trust-policy chain, monotonic anchor, verifier order, role separation and negative-verification matrix.
- L4 crosswalk source pins, bounded custody claim and current control dispositions.

This is not a cryptographic implementation review, runtime audit, L4 acceptance, or qualifying independent review. It was performed in the same working session as the document edits. It MUST NOT be represented as independent assurance.

## 3. Consistency findings and closures

| ID | Finding | Closure | Status |
|---|---|---|---|
| FC-01 | A1 §2.1 still said owner ratification was pending after the owner had approved the v1 amendment | Replaced pending-ratification language with the approved VPS + GitHub bounded scope and its common-mode rollback limitation | PASS |
| FC-02 | A1 §11 item 5 still asked whether the owner accepted VPS + GitHub | Recorded the decision as resolved for the bounded claim; no external anchor authorized | PASS |
| FC-03 | A1 §14.6 CR-01 still stated owner action was pending | Updated CR-01 to reference the formal v1 addendum and §13.2 harmonization | PASS |
| FC-04 | Contract §13.2 G1 custody rows repeated the superseded outside-both requirement | Contract addendum §D explicitly harmonizes the Evidence custodian and Latest-head anchor rows; role separation is preserved | PASS |
| FC-05 | Contract §7 retained a both-locations-unavailable readback expectation that cannot be met within the approved two-location boundary | Contract addendum §E and A1 §2.1 now specify the two controlled isolation tests and disclaim both-unavailable recovery | PASS |
| FC-06 | L4 crosswalk L4M-03 referenced the pre-amendment contract blob and omitted the current A1 blob | Rebound the row to the exact amended contract and A1 blobs shown in §1 | PASS |
| FC-07 | Initial G1 A product could be confused with the later signature extension | A1 §2.1 and the contract addendum explicitly preserve G1 A as unsigned; A1 is a separate signature/trust extension | PASS |

### Required bounded-custody interpretation

- Accepted custody locations: designated VPS location + designated GitHub evidence location.
- Required qualification: exact-object readback and digest verification for each copy; demonstrate VPS-copy readback while GitHub is unavailable and GitHub-copy readback while VPS is unavailable (or equivalent controlled isolation tests).
- A verifier requiring exact two-copy agreement MUST return BLOCKED/UNKNOWN if either required copy is inaccessible or mismatched.
- No readback/recovery claim is made when both locations are simultaneously unavailable.
- Joint rollback/replacement of both locations to the same older valid chain is not detectable. No third independent failure domain, external custody, WORM, global latestness or absolute anti-rollback claim is permitted.
- The owner decision does not promote any L4 control. Aggregate L4-Minimum remains BLOCKED / NOT VERIFIED.

## 4. Negative-verification matrix

A1 contains **30** synthetic negative cases, NV-01 through NV-30. The matrix covers:
- signature corruption and wrong-key verification;
- content/digest/length/object-ID/type/schema/profile substitution;
- purpose/audience/signer/role/policy/algorithm confusion and downgrade;
- root bootstrap, policy rollback/equivocation, revocation and historical-time uncertainty;
- stale checkpoint replay, anchor equivocation, broken predecessor, missing/conflicting custody copies;
- local-clock backdating, offline missing trust material and verification-record overwrite;
- common-mode joint rollback limitation and concurrent anchor-writer races.

The matrix is a test contract only. No cryptographic test, key generation, signature operation, anchor transition or offline verification was run in this review.

## 5. Residual issues — implementation remains blocked

The following are intentionally unresolved and must be addressed in a later owner/security and independent review:
1. Production signature algorithm and exact profile/version.
2. Owner-pinned root bootstrap, custody and recovery/rotation ceremony.
3. Actual checkpoint signer and anchor-authority identities, fingerprints and role evidence.
4. Concrete atomic compare-and-advance mechanism for anchor concurrency.
5. Whether trusted time/TSA is required for any historical trust-at-time claim.
6. Exact field/schema mapping for signing software/build identity, signing request/decision and signer authority/custody evidence references.
7. Concrete policy/anchor object retention and recovery configuration.
8. Independent second implementation and byte-vector conformance.
9. Verifier implementation, 30 negative tests, positive tests, network-disabled offline integration and owner copy readback.

No production algorithm/provider is selected. No private key, signature, trust-root instance, policy instance, anchor instance or verifier implementation exists as a result of this work.

## 6. Independent review request package

A qualifying reviewer must:
- be independent of the authors/editors of this review candidate and must not be the sole operator/controller of the T0 writer, checkpoint signer, trust root, anchor or custody process;
- provide identity, relevant cryptographic/security competence and conflict-of-interest disclosure;
- review the exact three blobs in §1, not a moving branch tip or a later unpinned copy;
- independently reconstruct byte-level digest/preimage rules and challenge canonicalization, numeric wire representation, base64url rules and domain separation;
- assess signer/policy/root authorization, role separation, key lifecycle and historical-time limits;
- challenge anchor genesis, monotonicity, concurrency, replay, substitution, equivocation and the explicitly bounded joint-rollback limitation;
- assess whether all 30 negative cases have unambiguous preconditions, reason codes and expected verdicts;
- return a signed or otherwise attributable review record with PASS / PASS WITH CONDITIONS / REQUEST CHANGES, findings, evidence and exact reviewed blob SHAs.

The general L4M-09 waiver remains in force for the L4 baseline; it does not waive the separately requested independent review of this signature architecture before implementation.

## 7. Final disposition

- Cross-document consistency at this exact snapshot: **PASS**.
- Review candidate frozen for independent review: **PASS**.
- Qualifying independent review: **NOT REQUESTED / NOT VERIFIED** — no reviewer identity or review channel has been designated.
- Signature/negative-verification implementation: **BLOCKED** pending qualifying review and separate explicit owner implementation approval.
- Aggregate L4-Minimum: **BLOCKED / NOT VERIFIED**.

No code, test, workflow, CI, key, signature, trust root, policy instance, anchor, provider, TSA, VPS/SSH/runtime, SQLite database, canonical T0 data or destructive operation was changed or exercised. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.


### FC-08 — Anchor retention strength aligned

A1 §2.1 and §6.4 were tightened from SHOULD to MUST for retaining/publishing the exact anchor record and predecessor chain at both approved custody locations, matching the base contract's two-copy requirement. The crosswalk source pin was refreshed. This is a normative alignment correction; no publication/readback was executed.
