# A2.2 Stage II — scope and decision-gap assessment

**Status: DRAFT / NON-NORMATIVE / NOT OWNER-APPROVED / NO IMPLEMENTATION AUTHORITY**  
**Date:** 2026-11-11  
**Branch:** `feature/t0-centralized-data-feeder-p1-20261101`

## 1. Purpose

Record the minimum decisions needed before Stage II can be specified. The only prior Stage II description available is the concept of a cryptographic adapter and verification of actual digital signatures. The algorithm, key profile, library and production trust/key handling have not been selected or approved.

This document is an architecture-readiness assessment only. It does not amend A2.2, select cryptographic primitives, choose a vendor/library, create keys, or authorize implementation.

## 2. Current baseline

- A2.2 §20 fixes the byte-level digest domains and T0-JCS-1 canonical numeric subset.
- Stage I is an isolated synthetic-only harness. Its CI/test gate passed on exact source SHA `cadcfcf66503c0a0750adcfc6646d6fa2944f03e` (run [42955676103](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42955676103)); this does not establish production cryptographic assurance.
- Stage I's mock/synthetic verifier must not be mistaken for a real cryptographic adapter.
- Independent review was waived/not performed; G3 is not established.
- `AI_EXECUTION_ENABLED=false`; paper-only posture remains.

## 3. Candidate Stage II purpose — pending owner confirmation

A future Stage II may define and test a narrow adapter boundary that performs cryptographic verification over the exact contract-defined message bytes, using an explicitly selected signature profile and a supplied public-key representation.

The adapter's result must remain separate from:
1. canonical parsing and object/digest binding;
2. cryptographic signature validity;
3. signer identity / trust-root resolution;
4. Trust Policy authorization (purpose, role, namespace, audience and profile);
5. monotonic-anchor / replay / sequence checks;
6. any state transition or custody acceptance.

A valid signature alone MUST NOT imply a trusted signer, authorized purpose, accepted policy, trusted checkpoint, or permission to mutate durable state.

This purpose is a candidate only, not a normative requirement until approved.

## 4. Decisions that block a Stage II contract

| Decision | Required owner decision / evidence | Current state |
|---|---|---|
| Signature algorithm and exact profile/version | Named algorithm, parameter set, encoding and profile identifier; security rationale and compatibility constraints | NOT SELECTED |
| Public-key representation | Exact SPKI/key encoding, permitted key types/curves/sizes, canonical parsing rules | NOT SELECTED |
| Signature representation | Exact wire encoding, length rules, canonicality and malformed-input behavior | NOT SELECTED |
| Cryptographic library | Library/provider, pinned version, supported platforms, maintenance/security posture, license and build provenance | NOT SELECTED |
| Verification input | Exact bytes passed to verifier; binding to A2.2 domain-separated objects and no reserialization | PARTIALLY CONSTRAINED BY A2.2 §20; adapter contract NOT DEFINED |
| Key source and trust binding | How a public key is supplied and independently bound to signer identity/role; no producer self-assertion | NOT DEFINED |
| Trust-root bootstrap | Whether Stage II consumes a pre-provisioned test trust root only or depends on a separately approved bootstrap stage | NOT AUTHORIZED |
| Key lifecycle | Rotation, retirement, revocation, compromise response, historical verification and algorithm deprecation | NOT DEFINED |
| Error semantics | Distinguish INVALID, UNSUPPORTED, MALFORMED, UNAVAILABLE/ERROR and fail-closed behavior | NOT DEFINED |
| Resource limits | Maximum message/key/signature sizes, timeouts, concurrency and denial-of-service limits | NOT DEFINED |
| Build/runtime boundary | Offline/deterministic CI, dependency pinning, no network fetch at verification time, no VPS/runtime integration by default | NOT APPROVED |

No default or inferred value is supplied for any unresolved row.

## 5. Minimum negative-verification matrix for a future contract

A future contract should require deterministic fixtures for at least:

- valid signature over the exact expected bytes;
- one-bit message mutation;
- one-bit signature mutation;
- wrong public key;
- wrong algorithm/profile identifier or version;
- malformed/truncated/oversized key and signature encodings;
- unsupported key type or parameters;
- valid cryptographic signature with unauthorized purpose/profile/policy;
- valid signature with untrusted or unbound signer identity;
- downgrade/fallback attempt to a legacy profile;
- unavailable or failing crypto backend;
- duplicate/ambiguous signer-key resolution;
- canonicalization/domain mismatch before cryptographic verification.

For every non-accepted case, the future contract must assert no Trust Policy, Monotonic Anchor, accepted-checkpoint, trust-root or custody state advancement. The exact expected verdict and primary reason code must be fixed per fixture. This list is a planning checklist, not an approved test contract.

## 6. Required evidence before implementation approval

A Stage II implementation request should include:

1. approved algorithm/profile decision and threat-model rationale;
2. exact key/signature wire-format contract;
3. pinned cryptographic library/provider and dependency provenance;
4. precise adapter input/output/error interface;
5. separation proof between signature validity and trust/policy authorization;
6. known-answer vectors sourced independently of the implementation;
7. the complete negative-verification matrix and state-immutability assertions;
8. deterministic offline CI plan, supported Python/runtime versions and artifact evidence;
9. security review plan and explicit treatment of the existing independent-review waiver/G3 status;
10. explicit exclusions and rollback/recovery boundaries.

## 7. Explicit exclusions pending separate approval

This assessment does NOT authorize:
- selecting or implementing a production cryptographic algorithm/profile/library;
- generating, importing, storing, exporting, rotating or revoking real keys;
- using private keys or signing production evidence;
- enrolling or changing a trust root;
- enabling Path A or Path B bootstrap;
- creating or mutating durable Trust Policy or Monotonic Anchor instances;
- changing custody, publication, VPS, SSH, T0, SQLite, Feeder, API or runtime;
- adding CI secrets, network-dependent verification, deployment or workflow dispatch;
- integrating trading, ledgers, Shared Risk Engine, Kill Switch or order execution;
- deleting, expiring, compacting or otherwise destructively changing data.

## 8. Proposed approval sequence

1. Owner confirms or rejects the candidate Stage II purpose in §3.
2. Owner resolves the decision rows in §4, or explicitly authorizes a bounded option-analysis document that compares choices without implementation.
3. A contract-only Stage II specification is drafted and reviewed against A2.2 §§20 and 19.
4. Owner approves the exact contract blob and the exact implementation scope separately.
5. Only then may test-first implementation begin, with independent-review/G3 treatment explicitly decided rather than inferred.

**Current disposition: BLOCKED — Stage II is not specified or approved. Stage I PASS does not open Stage II.**
