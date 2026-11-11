# T0 Signature A2.2 — Implementation Scope Assessment

Date: 2026-11-11  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Assessment type: documentation-only; no implementation authorization

## 1. Decision sought

Determine the smallest safe implementation increment that can follow the A2.2 documentation candidate after the owner waived mandatory independent review.

This assessment does **not** approve implementation. A separate explicit owner decision must approve the exact source snapshot, permitted files, test scope and prohibited operations.

## 2. Exact governing sources

| Source | Blob SHA | Current role |
|---|---|---|
| A2.2 signature/trust/anchor amendment | `41d41cd23f73a6e552b9ceca5ebbb39c46934e7d` | Current documentation-only contract candidate |
| A2.2 adversarial self-review report | `ab2b56376c01e4ef45b28d3dcd647feadd829b60` | Same-session self-review plus targeted governance-delta checks |
| Owner waiver of mandatory independent review | `f437dbf319b7a9570092c8cafb4bf354409e651c` | Independent review not a mandatory gate |
| Checkpoint Contract v1 | `a6825270d59bde274bfe765d5f942144b66a84de` | Base Evidence Object/checkpoint contract |
| A2.1 historical source | `73ba6fd9f6bb862121842f7a1347fffc06738451` | Historical amendment |
| A2 historical source | `e15a90b779bd86b39729208db938e9de9471ef26` | Historical amendment |
| A1 historical source | `00fdad293e129562145ab930507a4e6b9c2bf23d` | Historical signature/anchor amendment |

The current A2.2 technical clauses received the full same-session review on earlier blob `2090112370e3b4a9925e78cf1ab0e2bb8428640c`; the subsequent current-blob changes are review-governance wording only and were checked as targeted deltas. This is not independent assurance or a fresh full review of every current-blob byte.

## 3. Current implementation blockers

1. **No production signature algorithm/profile implementation selected.** A2.2 names the logical profile ID/version but does not choose the cryptographic algorithm, key type, signature encoding or implementation library. Do not silently choose one.
2. **Bootstrap is unavailable.** Path A and Path B are both `NOT_ENABLED`; initial trust bootstrap must remain `BLOCKED`. No root enrollment or verifier trust-store mutation.
3. **No trusted provisioning authority is established.** Owner authority, verifier administrative trust boundary, operator authentication, provisioning channel and independent pin/readback are not operationally established.
4. **No operational anchor authority/storage transition is approved.** The A2.2 state machine is a specification, not permission to instantiate or persist an anchor.
5. **Custody claims remain bounded.** VPS + GitHub are the approved two locations; joint rollback remains undetectable. No WORM, external monotonic anchor, global latestness or absolute anti-rollback claim.
6. **No runtime integration is approved.** No T0 writer/Feeder, SQLite, API, VPS, SSH, CI deployment or live/paper trading path changes.

## 4. Recommended staged scope

### Stage I — synthetic contract-conformance harness (recommended first candidate)

A narrowly isolated, offline-only test package, using synthetic fixtures and temporary directories only.

Allowed candidate work after explicit approval:
- Strict UTF-8/JCS parser and canonical serialization checks required by T0-JCS-1.
- Canonical unsigned-decimal parsing/range checks and U64BE boundary encoding.
- Canonical unpadded base64url encode/decode and reject-noncanonical cases.
- Domain-separated SHA-256 digest helpers for Evidence Object, Trust Policy body and Anchor envelope.
- Schema/field-binding validation for the A2.2 profile ID/version across descriptors, statements, envelopes, policies and verifier request fixtures.
- Deterministic reason-code and verdict-precedence mapping, including no-state-mutation assertions against an in-memory test state.
- Synthetic negative fixtures with exact baseline digest, one semantic mutation, per-dimension result, aggregate verdict, reason code, S0/S1 equality and forbidden-transition assertions.
- A test-only signature-verifier interface stub whose verdict is explicitly labelled **MOCK / NOT CRYPTOGRAPHIC**. It may test routing and reason precedence only; it cannot establish signature authenticity, key security or cryptographic conformance.
- Tests must not read/write the canonical T0 database, VPS files, real keys, live trust stores or anchor state.

Stage I explicitly excludes:
- Production signing or verification implementation.
- Choosing an algorithm, key type, library, key format or production profile.
- Creating or enrolling keys, trust roots, owner authorities, bootstrap records or anchor instances.
- Claiming that signature-invalidity cases prove cryptographic correctness when a mock verifier is used.
- Any VPS/GitHub publication, custody update, CI secret, deployment or runtime integration.

### Stage II — cryptographic adapter (not currently ready)

Blocked until the owner separately selects and approves an exact cryptographic profile, supported library/version, key encoding/custody boundary, test vectors and threat model. Requires real cryptographic known-answer and negative tests. No approval is implied here.

### Stage III — bootstrap authority and trust enrollment (not currently ready)

Blocked until a separate Path A or Path B authority contract is approved and its trust boundary, operator authorization, provisioning channel, independent verifier pin/readback and recovery/revocation process are evidenced. The newly enrolled root MUST NOT authenticate its own enrollment.

### Stage IV — durable monotonic anchor and two-copy custody (not currently ready)

Blocked until anchor authority, compare-and-advance semantics, crash recovery, publication ordering, readback and rollback limits are separately approved and tested. No anchor persistence or publication is part of Stage I.

### Stage V — integration with T0/VPS/runtime (not currently ready)

Requires separate explicit approval. T0 remains independent; no direct modification of canonical T0 data or writer/lease/fencing path is permitted by this assessment.

## 5. Stage I acceptance criteria

A Stage I implementation, if separately approved, is PASS only if:
1. All parser/canonicalization/encoding/digest boundary vectors pass.
2. Every A2.2 fixture has deterministic baseline and exactly one intended semantic mutation.
3. Each test asserts dimension result, aggregate verdict, one stable primary reason code, state before/after and forbidden transitions.
4. Failed verification leaves all in-memory trust/policy/anchor/checkpoint state unchanged.
5. Mock signature behavior is explicitly labelled and cannot produce a production `VALID_SIGNATURE` claim.
6. No tests access external network, VPS, secrets, production filesystem or canonical T0 SQLite.
7. Test output records exact source SHA, command, environment and results.
8. No weakened assertion, skipped negative case or broad exception is accepted to obtain a green run.

A passing Stage I result means only **synthetic contract plumbing/conformance PASS**. It does not mean production cryptography, bootstrap, anchor custody, anti-rollback or L4 controls PASS.

## 6. Recommendation

Stage I is now **OWNER APPROVED** by `docs/decisions/OWNER_APPROVAL_T0_SIGNATURE_A2_2_STAGE_I_2026-11-11.md` (approval commit `b79424ad86b5f4d78da610da3c81c9e90e92fee6`). The approval is limited to the synthetic-only scope below:
- exact A2.2 blob `41d41cd23f73a6e552b9ceca5ebbb39c46934e7d`;
- an isolated package/test directory (to be named in the implementation authorization);
- parser/canonicalization/U64/base64url/digest/profile/reason-code fixture scope;
- mock-only signature adapter, clearly non-cryptographic;
- temporary in-memory state only;
- prohibited operations listed in §4 and §7.

Do not combine Stage I with production cryptography, bootstrap, anchor persistence, two-copy publication or VPS integration. If the owner does not approve the mock-only boundary, do not begin code changes.

## 7. Non-negotiable prohibitions for the proposed first increment

- No real private/public key generation or import.
- No signatures using real trust identities.
- No trust-root enrollment or verifier trust-store mutation.
- No Path A/Path B activation.
- No Trust Policy or Monotonic Anchor instance in production or VPS.
- No writes to canonical T0 SQLite, lease, fencing, Feeder or API.
- No VPS/SSH/systemd/autostart/network/provider/TSA operation.
- No GitHub Actions secrets or deployment workflows.
- No real orders or changes to Core/AI trading strategy, ledgers, Shared Risk Engine or Kill Switch.
- No destructive cleanup/deletion.

## 8. Status

- Assessment: **COMPLETE — DOCUMENTATION ONLY**; owner has subsequently approved Stage I in a separate decision record.
- A2.2 self-review: **PASS WITH RESIDUAL GATES**; independent review waived/not performed.
- Stage I implementation: **OWNER APPROVED — EXECUTION BLOCKED pending an isolated local working tree/test runtime**.
- Stages II–V: **BLOCKED / NOT APPROVED**.
- CI/workflow: **NOT RUN**; the approval record does not authorize CI/workflow changes or execution.
- Runtime/T0: **UNCHANGED**.
