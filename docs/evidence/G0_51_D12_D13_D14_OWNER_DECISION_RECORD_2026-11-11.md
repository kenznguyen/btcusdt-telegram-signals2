# G0.51 — D12/D13/D14 Owner Decision Record

Date: 2026-11-11 (Asia/Ho_Chi_Minh)
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/t0-centralized-data-feeder-p1-20261101
Decision baseline: 0566280db1e3ffa1347ace68ce6dcbafa07d6276
Related package: G0.50, blob 2c63e295edbf3f52a85d4d13b7e0551cbcc26977
Type: Owner decision record; documentation-only
Disposition: **D12-A, D13-A, D14-A OWNER-DECIDED; S2 IMPLEMENTATION NOT AUTHORIZED**

## 1. Owner decision

The Owner explicitly agreed to all three recommended option-A selections in G0.50. This record formalizes those selections for the initial governance posture. The agreement does not authorize implementation, runtime activity or stage transition.

## 2. D12-A — Audit custody, retention, redaction and readback

**OWNER-DECIDED.**

1. Maintain an append-only logical audit history for decision records in the existing approved GitHub repository/commit history.
2. Treat this as GitHub-domain custody only. It is not an independent backup domain, disaster-recovery guarantee, durable custody proof outside GitHub, or proof against GitHub account/platform compromise.
3. Before making a payload custody/readability/integrity claim for an artifact, retrieve the exact payload from the claimed GitHub custody location and independently verify its digest against the recorded digest. Artifact ID/name/size/expiry metadata alone is insufficient.
4. Record artifact identifiers, expected digest, observed digest, retrieval time as untrusted/platform-reported metadata, retrieval result and exact source reference. If payload cannot be retrieved or digest does not match, custody/readability verification is NOT VERIFIED or BLOCKED.
5. Historical decision evidence must not be silently rewritten. A redaction, correction, supersession or revocation is represented as a new attributable event linked to the prior immutable record; retain the prior digest/reference and state what is no longer exposed.
6. No automatic retention expiry/deletion, cleanup, archive, artifact purge, second custody-domain provisioning, backup cadence or retention duration is authorized or ratified. Any destructive or retention-changing operation requires separate exact-scope Owner authorization, preconditions, impact assessment, verification and recovery plan.
7. Do not place credentials, keys, tokens, trust-root secrets or RESTRICTED values in ordinary evidence or CI artifacts. G0.17 sensitivity inheritance/no-auto-downgrade remains controlling.

D12-A does not establish an append-only technical guarantee beyond the actual GitHub repository controls and history available; do not claim WORM storage or independent tamper-proof custody.

## 3. D13-A — Verified-facts binding and process boundary

**OWNER-DECIDED as the required target contract for any future verified-facts consumer.**

1. A future verified-facts envelope must be versioned and immutable, and bind exact subject identifier/type/version, source reference, evidence class, exact evidence digest(s), claim type, declared scope, purpose/audience, policy/profile version, verifier contract/schema version, verifier build/source identity, evaluation identifier and exact evidence set consumed.
2. Only the verifier may construct a verified-facts result, and only after validating the exact input evidence and all applicable claim dimensions. Callers/consumers may not create or mutate a trusted result by supplying generic dictionaries, mappings or booleans.
3. Consumers must validate exact subject/evidence/policy/purpose/evaluation binding and reject mismatches, unknown fields/states, stale policy references, malformed representations and cross-subject/cross-purpose reuse. Unknown or unresolved claim dimensions remain explicit and fail closed for dependent uses.
4. Keep byte integrity, issuer authenticity, Owner attribution/authorization, inventory completeness, freshness and custody/readback as separate dimensions. No generic `trusted=true` flag may collapse them.
5. Freshness remains independently governed by D08. An envelope cannot create a trusted anchor or override `FRESHNESS_UNKNOWN`.
6. Verified facts are descriptive evidence only. They do not authorize deletion, retention changes, key operations, trust administration, deployment, trading or any other action.
7. D13-B process-local opaque results are NOT selected as a substitute target contract. A future synthetic-only single-process experiment, if needed, requires its own exact D14-scoped Owner approval and cannot be represented as satisfying the D13-A target or production trust.
8. No serialization format, schema, IPC protocol, cryptographic envelope, process isolation mechanism, constructor capability or production adapter is selected or authorized by this decision.

## 4. D14-A — Per-increment stage and release gates

**OWNER-DECIDED.**

1. Strict per-increment Owner approval is the default. Every executable increment, S2 implementation step, workflow/permission change, real-evidence adapter, provider/runtime operation and lifecycle/destructive operation requires a separate exact-scope Owner approval before work begins.
2. Each pre-implementation package must state exact objective/stage, allowed and forbidden paths, baseline commit and source/blob pins, commands/test matrix, data classification, filesystem/network/credential/provider permissions, resource ceilings, stop conditions, evidence requirements, claim limitations, recovery/rollback boundary and exact completion boundary.
3. After work, record exact source SHA, changed paths, workflow event/run/checkout SHA/jobs/results, artifact identity/size/expiry/digest/readback, PASS/BLOCKED/NOT VERIFIED status, deviations, residual risks and non-authorizations.
4. A passing test or CI run closes only the explicitly named verification scope. It does not constitute Owner acceptance, production trust, custody proof, runtime acceptance or authorization to proceed.
5. No automatic stage transition. “Continue”, prior approvals, a green workflow or a completed document do not authorize the next increment.
6. A bounded standing authorization is not the default and may be used only if the Owner separately approves the exact complete sequence, paths, source pins, commands, side-effect permissions, stop conditions and expiry/completion boundary. No such standing authorization is granted here.

## 5. Cross-decision consistency

- D06/D09: manual Owner attestation only in the initial phase; GitHub action is platform-attributed, not a cryptographic signature.
- D07: inventory completeness requires independently defined expected population and expected/observed reconciliation.
- D08: no global freshness claim without trusted anchor; freshness-dependent uses fail closed.
- D12: GitHub-domain logical audit history; exact payload readback/digest verification before custody claims; no automatic deletion or silent historical rewrite.
- D13: exact-bound immutable verifier-created facts; separate claim dimensions; no execution authority.
- D14: explicit per-increment Owner approval; no automatic stage transition.
- D01–D04 retain the prior minimal/conditional/deferred choices. No issuer key, signature operation, trust root or key custody is approved.
- D05/D10/D11 and S1 parser remain synthetic-only. Ratified S1 limits do not establish production verifier limits or authorize S2.
- G1 A remains unsigned proof-of-existence; A1 remains a separate extension.

## 6. Explicit non-authorizations

This decision record does not authorize:
- S2 or any verifier/adapter/registry/schema/serialization/IPC/source/test/fixture/workflow/CI implementation;
- synthetic or real cryptographic keys, signing, verification, trust roots, trusted time/anchor or revocation services;
- second custody domain, backup provider, retention schedule or automated artifact expiry/deletion;
- inventory collection from VPS/T0/T1/T2/databases/providers;
- artifact deletion, cleanup, archive, compaction, VACUUM, redaction execution or other destructive lifecycle action;
- changes to T0/T1/T2, canonical data, CORE_LEDGER, AI_LEDGER, Shared Risk Engine, Kill Switch or trading runtime;
- deployment, exchange connection, live trading or real orders.

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged. VPS remains absent; no runtime state is inferred.

## 7. Verification and disposition

- Scope: record Owner decisions D12-A, D13-A and D14-A; update project handoff only.
- Tests/compile/CI: NOT RUN (documentation-only).
- Runtime/VPS/database/provider/key operations: NOT PERFORMED.
- Independent reviewer sign-off: not mandatory under the existing Owner waiver; no independent assurance claim is made.

**G0.51: DOCUMENTATION PASS — D12-A, D13-A AND D14-A OWNER-DECIDED. S2 IMPLEMENTATION AND ALL OPERATIONAL/DESTRUCTIVE ACTIONS REMAIN NOT AUTHORIZED.**

Next: reconcile remaining open dependencies and prepare a separate exact-scope S2 readiness package only after they are closed. Do not begin implementation automatically.
