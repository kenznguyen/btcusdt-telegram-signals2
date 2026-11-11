# T0 Signature Contract A2.1 — Second Adversarial Self-Review

Date: 2026-11-11  
Review type: same-session second adversarial self-review; not independent review  
Disposition: **REQUEST CHANGES — DO NOT SUBMIT AS REVIEW-READY**

## 1. Exact review snapshot

Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

| Source | Exact blob SHA |
|---|---|
| A2.1 `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A2_1_2026-11-11.md` | `73ba6fd9f6bb862121842f7a1347fffc06738451` |
| Historical A2 | `e15a90b779bd86b39729208db938e9de9471ef26` |
| A1 | `00fdad293e129562145ab930507a4e6b9c2bf23d` |
| Checkpoint Contract v1 | `a6825270d59bde274bfe765d5f942144b66a84de` |
| L4 crosswalk | `e560f084642b5f81c78179ef673e5df116fc5f42` |
| Previous A2.1 self-review | `9fa179c9daf657880533eb69394b42cdb644fa0b` |

All source documents were fetched from the active branch for this review. This is a documentation/contract consistency review only.

## 2. Findings

### A2.1-R2-01 — HIGH: contradictory review status and stale acceptance gates

**Evidence**
- §13 says the exact A2.1 blob must be frozen and subjected to a fresh adversarial self-review, then labels self-review PENDING.
- The prior self-review report already records review of this exact A2.1 blob and reports PASS WITH RESIDUAL GATES.
- §10 still instructs the team to freeze and self-review “A2” and obtain review of “exact A2 blobs”, rather than the current A2.1 candidate.
- §1.3 describes A2 as the new candidate even though this document is the A2.1 revision.

**Risk:** Readers cannot reliably determine which revision has been reviewed, what gate is complete, or which exact blob must be sent to an independent reviewer.

**Required correction:** Normalize all status and gate references to the actual A2.1 snapshot; distinguish historical A2 from current A2.1. §13 must not say self-review pending once the corresponding review record exists. Do not imply independent review has occurred.

### A2.1-R2-02 — HIGH: Path B does not yet establish a verifiable owner authorization authority

**Evidence**
- §12.1 defines a Bootstrap Authorization object that MUST be independently verifiable and includes issuer identity/role and a signature descriptor “if signed”.
- Path A uses a separately pinned owner authority and a signed authorization object.
- Path B explicitly says its ceremony record is not self-authenticating; its authority comes from the independent verifier-provisioning channel and recorded operator authorization.
- The document does not define how the verifier authenticates the provisioning channel, how the operator is proven to be owner-authorized, or what trusted configuration/provisioning authority is itself pinned before the root bootstrap.
- The Path B record is alternately treated as the authorization object, an evidence record, and a direct trusted-configuration operation. These are not equivalent trust models.

**Risk:** The design may treat a record written by an unverified operator/channel as proof of owner authorization. That leaves the original bootstrap trust question unresolved and can create a circular or implicit trust assumption.

**Required correction:** Define Path B as an explicit verifier-provisioning trust ceremony, not as a signed authorization object unless it actually is signed. Specify the pre-existing verifier trust boundary, authorized operator authentication/delegation, channel authentication, exact configuration mutation and readback evidence, and the failure model. If those trust assumptions cannot be specified, Path B remains unavailable and bootstrap remains BLOCKED. Do not use the newly enrolled root to bootstrap any of these authorities.

### A2.1-R2-03 — HIGH: Bootstrap verdict rules are ambiguous across Path A and Path B

**Evidence**
- §12.3.1 says absent/unconfigured paths produce BLOCKED.
- §12.3.2 describes an authorization-object signature/issuer failure as INVALID.
- Path B has no self-authenticating signature by design, so the signature-specific branch is not directly applicable.
- §12.3.3 says unavailable owner pin, ceremony evidence, verifier configuration or channel readback produces UNKNOWN.
- The text does not define precedence when a path is unconfigured, evidence is absent, or an expected readback is temporarily unavailable.

**Risk:** Two conforming verifiers could assign different aggregate verdicts and reason codes to the same bootstrap state. This violates deterministic fail-closed behavior.

**Required correction:** Add a path-specific decision table for A and B, with explicit predicates and precedence for NOT_CONFIGURED, EVIDENCE_MISSING, AUTHORIZATION_INVALID, TRUST_BOUNDARY_UNAVAILABLE, DIGEST_MISMATCH and READBACK_UNAVAILABLE. State whether each is BLOCKED, INVALID or UNKNOWN, and whether any trust/policy/anchor state may advance.

### A2.1-R2-04 — HIGH: New negative cases do not satisfy the inherited deterministic test contract

**Evidence**
- A2 §5.1 (inherited by A2.1) requires every negative case to define a clean baseline, one isolated mutation, per-dimension result, one aggregate verdict, one stable primary reason, state before/after and forbidden transitions.
- A2.1-NV-01..09 generally provide only a condition, aggregate verdict and reason code; they do not consistently define per-dimension outcomes, exact baseline/mutation, full state-before/state-after assertions or all forbidden transitions.
- NV-06 groups several independent mismatch dimensions (namespace, audience, root, role, profile, sequence, recovery policy) into one case, contrary to the inherited single-fault fixture rule in §5.1.

**Risk:** The new tests are not deterministic enough to prove that the corrected behavior is implemented, and compound cases may pass/fail for different reasons.

**Required correction:** Expand each A2.1 case to the complete §5.1 assertion schema. Split NV-06 into one isolated fixture per binding mismatch, or define a clearly separate parameterized test family where each parameter produces an independent fixture and exact expected reason. Explicitly assert that policy head, trust root, anchor head and accepted checkpoint state remain unchanged on every failed bootstrap check.

### A2.1-R2-05 — MEDIUM: “A2.1 profile” lacks an exact machine-readable profile identity

**Evidence**
- §§11–12 repeatedly require explicit A2.1 profile selection and forbid downgrade.
- The document does not define a stable profile identifier/version and the exact field/descriptor location binding that identifier to the verification request, signed statement, Trust Policy and bootstrap record.
- A2 inherited §3 says profile/algorithm fields remain mandatory, but does not by itself identify the A2.1 profile value or its versioning semantics.

**Risk:** A verifier may recognize “A2.1” as a document label rather than a protocol-level profile. This weakens version separation and makes downgrade/profile substitution behavior underspecified.

**Required correction:** Define an immutable profile ID and version, its namespace and lifecycle, and bind it consistently into the signed object descriptor, Signature Statement, Trust Policy authorization and verifier request. Define explicit unknown-profile, retired-profile and downgrade reason codes.

## 3. Checks that remain valid

- A2.1 explicitly rejects `T0_CHECKPOINT_OWNER_ATTESTATION` for A2.1 checkpoint objects.
- It requires explicit authorization of `T0_CHECKPOINT_ISSUER_ATTESTATION`.
- It separates historical A1 verification and prohibits silent fallback/downgrade.
- It binds the bootstrap authorization concept to the exact bootstrap digest and relevant namespace/audience/root/role/profile/sequence/recovery fields.
- It prohibits the newly enrolled root from being the sole authority for its own initial enrollment.
- It retains the bounded VPS + GitHub rollback limitation and does not claim WORM/global latestness.
- The historical A2, A1, base contract and crosswalk blobs were not changed by this review.

These positive observations do not close the findings above.

## 4. Overall disposition

**REQUEST CHANGES.** A2-SR-01's purpose rejection is substantially addressed. A2-SR-02 is only partially addressed: Path A is explicitly unavailable pending its separate contract; Path B still lacks a fully specified independently verifiable owner/operator provisioning trust model.

A2.1 is **NOT READY for qualifying independent review** until the HIGH findings are corrected and a fresh self-review is performed on the corrected exact blob.

Independent review: **NOT PERFORMED / NOT VERIFIED**.  
Implementation: **BLOCKED**.  
CI/workflow: **NOT RUN** for this review increment.

## 5. Unchanged boundaries

No A2.1 source, code, tests, workflow, CI configuration, key, signature, trust root, policy/anchor instance, provider/TSA, VPS/SSH/runtime, SQLite database, canonical T0 data or destructive operation was changed or exercised. This report records findings only. Any correction to A2.1 requires a new candidate blob and a fresh review. Separate owner approval is required before implementation.
