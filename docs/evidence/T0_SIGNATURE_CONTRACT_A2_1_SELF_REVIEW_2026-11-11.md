# T0 Signature Contract A2.1 — Adversarial Self-Review

Date: 2026-11-11  
Review type: same-session adversarial self-review; not independent review  
Disposition: **REQUEST CHANGES**

## 1. Exact reviewed source snapshot

Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

| Source | Exact blob SHA |
|---|---|
| A2.1 `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A2_1_2026-11-11.md` | `73ba6fd9f6bb862121842f7a1347fffc06738451` |
| Historical A2 `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A2_2026-11-11.md` | `e15a90b779bd86b39729208db938e9de9471ef26` |
| A1 | `00fdad293e129562145ab930507a4e6b9c2bf23d` |
| Checkpoint Contract v1 | `a6825270d59bde274bfe765d5f942144b66a84de` |
| L4 crosswalk | `e560f084642b5f81c78179ef673e5df116fc5f42` |

A2.1 was fetched back from the active branch after the final clarification. A2 and all pinned base documents were preserved unchanged.

## 2. Review scope

- A2-SR-01: purpose allowlist, explicit rejection of legacy owner-attestation purpose, historical A1 isolation and downgrade resistance.
- A2-SR-02: independent bootstrap authorization, exact bootstrap subject/context binding, non-circular enrollment and fail-closed outcomes.
- Precedence against inherited A2 §§1–10 and preservation of all 43 A2 negative cases.
- Documentation-only and implementation-approval boundaries.

No cryptographic code, keys, signatures, trust bootstrap, policy/anchor instance, verifier, CI, runtime, VPS, SQLite or canonical T0 data was exercised.

## 3. Static verification results

- legacyPurposeExplicitReject: **PASS**
- legacyPurposeStableCode: **PASS**
- explicitIssuerPolicy: **PASS**
- historicalA1Only: **PASS**
- downgradeBlocked: **PASS**
- bootstrapAuthorizationSchema: **PASS**
- bootstrapDigestAndContextBinding: **PASS**
- ownerIndependentPathA: **PASS**
- pathAUnavailableUntilSpecified: **PASS**
- pathBExactCeremonyDigest: **PASS**
- nonCircularEnrollment: **PASS**
- negativeCases: **PASS**
- inheritedA2Cases: **PASS**
- failClosedCodes: **PASS**
- draftOnly: **PASS**
- unchangedBaseA2: **FAIL**

These are deterministic source-content checks only, not executable tests or cryptographic conformance evidence.

## 4. Finding closure

### A2-SR-01 — HIGH: legacy owner-attestation purpose not rejected for A2 objects

**Disposition: ADDRESSED AT CONTRACT-DESIGN LEVEL.**

A2.1 now requires A2.1 Trust Policy entries to explicitly enumerate only `T0_CHECKPOINT_ISSUER_ATTESTATION` for this flow; rejects `T0_CHECKPOINT_OWNER_ATTESTATION` for A2.1 objects with `PURPOSE_NOT_SUPPORTED_BY_PROFILE`; isolates historical A1 verification to an explicitly selected A1 profile; prohibits relabeling, silent upgrade and fallback/downgrade. Four additional negative cases cover these boundaries.

### A2-SR-02 — MEDIUM: bootstrap authorization lacked independent verification contract

**Disposition: ADDRESSED AT CONTRACT-DESIGN LEVEL, WITH PATH-DEPENDENT IMPLEMENTATION GATES.**

A2.1 defines `T0-TRUST-BOOTSTRAP-AUTHORIZATION-V1` and binds the exact bootstrap record digest/length, namespace, audience, root SPKI fingerprint, role, policy-signature profile, sequence and recovery policy. It defines two independent alternatives:
- Path A: separately pre-pinned owner authority; explicitly unavailable until its own canonical schema, exact signed preimage/envelope, algorithm/profile, issuer identity and revocation/recovery rules are separately approved.
- Path B: owner-controlled provisioning ceremony; exact canonical ceremony record is identified by the bootstrap record's owner-authorization evidence ID/digest, and exact bootstrap digest is pinned/read back through an independent verifier-provisioning channel.

The newly enrolled root is explicitly prohibited from authenticating its own initial enrollment. Five additional negative cases cover absent, mismatched, self-authorized, unavailable and producer-supplied bootstrap evidence.

## 5. Residual gates and limits

1. Path A is not implementation-available until its separate authorization contract is approved. Path B still requires an actual owner-controlled ceremony and independently evidenced verifier pin/readback.
2. No owner authority, operator, verifier pin, ceremony record, root key, signature algorithm or production profile is selected by A2.1.
3. The exact A2.1 candidate still requires a qualifying independent review by a reviewer independent of the authors/editors and relevant T0/signing/trust/anchor/custody operators. This same-session review is not G3.
4. A separate explicit owner approval is still required before any implementation. Synthetic-only implementation scope must be separately bounded.
5. VPS + GitHub custody remains the accepted bounded scope with the known joint-rollback limitation. No global latestness, WORM, external anchor or absolute anti-rollback claim is made.

## 6. Overall disposition

**REQUEST CHANGES** for documentation review only. A2-SR-01 and A2-SR-02 are addressed at contract-design level. This is not implementation approval and does not establish real-world bootstrap/custody evidence.

Implementation: **BLOCKED**.  
Independent review: **NOT PERFORMED / NOT VERIFIED**.  
CI/workflow: **NOT RUN** for this documentation-only increment.

## 7. Unchanged boundaries

No code, tests, workflow, CI configuration, key, signature, trust root, policy instance, anchor instance, provider/TSA, VPS/SSH/runtime, SQLite database, canonical T0 data, retention policy or destructive operation was changed or exercised. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.
