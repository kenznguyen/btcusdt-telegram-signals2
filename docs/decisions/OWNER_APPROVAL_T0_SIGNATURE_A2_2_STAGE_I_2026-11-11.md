# Owner Approval — T0 Signature A2.2 Stage I

Date: 2026-11-11  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

## Decision

The owner approves implementation of **Stage I only** from the A2.2 implementation-scope assessment, bound to the exact A2.2 source blob:

`41d41cd23f73a6e552b9ceca5ebbb39c46934e7d`

The approved scope is a synthetic-only, offline contract-conformance harness. It may cover:
- T0-JCS-1 strict parsing and canonical serialization;
- canonical unsigned integer parsing and U64BE encoding;
- canonical unpadded base64url encoding/decoding;
- domain-separated SHA-256 digest helpers;
- immutable signature profile ID/version binding checks;
- deterministic verdict/reason-code precedence;
- the 27 A2.2 negative fixtures with single-mutation discipline;
- in-memory state snapshots and proof that failed cases leave state unchanged.

Any signature-verifier test double MUST be labelled `MOCK / NOT CRYPTOGRAPHIC`. It MUST NOT assert or emit production signature authenticity, cryptographic conformance, trusted-root validity or real key possession.

## Exact boundaries

This approval does NOT authorize:
- production algorithm/library/key-profile selection or production cryptographic adapter;
- real key generation/import, signing or verification;
- root enrollment, trust-store mutation, Path A or Path B activation;
- Trust Policy or Monotonic Anchor instance creation or durable state;
- VPS, SSH, systemd, Feeder, API, SQLite, canonical T0, custody publication or external-provider/TSA operations;
- CI secrets, deployment or runtime integration;
- changes to trading strategy, ledgers, Shared Risk Engine, Kill Switch or order execution;
- destructive operations or data deletion.

Use an isolated package and test directory separate from the existing `synthetic_evidence` P1.8 implementation. Tests must use temporary/in-memory fixtures only and must not access external network, production filesystem, credentials or canonical T0.

## Approval semantics

- Stage I: **OWNER APPROVED**, subject to the exact scope above.
- Stages II–V: **NOT APPROVED / BLOCKED**.
- Independent review: waived as a mandatory gate; not performed; no independent assurance/G3 claim.
- CI/workflow execution: not authorized by this decision; use local isolated test commands unless separately approved.
- T0/VPS/runtime: unchanged.
- Paper-only posture and `AI_EXECUTION_ENABLED=false`: unchanged.

This approval authorizes only the bounded Stage I implementation. Any scope expansion requires a new explicit owner decision.
