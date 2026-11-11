# G0.49 — D07/D08/D09 Owner Decision Record

Date: 2026-11-11 (Asia/Ho_Chi_Minh)
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/t0-centralized-data-feeder-p1-20261101
Decision baseline: 9eee57397f6887cd0760f17477a647f9ba39e4e2
Related package: G0.48, blob d3aaabf214dc22dba274ec5e7eba8ace4de0117e
Type: owner decision record; documentation-only
Disposition: **D07/D08/D09 OWNER-DECIDED — INITIAL-PHASE POLICY RECORDED; S2 IMPLEMENTATION NOT AUTHORIZED**

## 1. Owner selections

The Owner explicitly selected option A for each of D07, D08 and D09. This record converts those selections into bounded initial-phase policy. It does not grant implementation or operational authority.

## 2. D07 — Inventory closure: A selected

**OWNER-DECIDED.** A claim that an inventory is complete requires all of the following:

1. Declared and bounded inventory scope, including source/domain, object classes, filters, snapshot/cut boundary and claim purpose.
2. An expected population defined independently of the producer-supplied observed manifest, with its authoritative source and known limitations identified.
3. Deterministic enumeration with stable identifiers and immutable versions/references where available; pagination/cursor continuity and terminal condition must be evidenced.
4. Expected/observed reconciliation for every expected item, with explicit disposition and evidence for observed, absent/not-applicable, inaccessible, ambiguous or unresolved items.
5. Binding to exact scope definition/version, source reference, snapshot/cut, enumeration procedure/version, manifest bytes/digest and reconciliation result.

Any unresolved, inaccessible, ambiguous or unexplained item; duplicate identity; missing page; cursor discontinuity; source error; or unexplained count mismatch prevents a COMPLETE disposition. The result must be INCOMPLETE / NOT VERIFIED or BLOCKED as appropriate.

Explicitly partial inventories may be reported as PARTIAL only when the claim and coverage limitation are stated. They must not be promoted to complete. A producer-supplied manifest or Owner attestation alone cannot establish completeness.

No corpus-size, pagination, retry, byte or time ceilings are ratified here.

## 3. D08 — Freshness and anti-replay: A selected

**OWNER-DECIDED.** Initial phase makes no global latestness/freshness claim.

Permitted claim levels:
- `INTEGRITY_ONLY`: exact bytes match the referenced digest; no freshness assertion.
- `AS_OF_SNAPSHOT`: evidence is valid only relative to a named immutable snapshot/cut/checkpoint; no global latestness assertion.
- `FRESHNESS_UNKNOWN`: no trusted comparison point or required evidence is available.

Any freshness-dependent decision or action must fail closed when freshness is unknown. Producer/local wall-clock timestamps, a sequence field without a trusted comparison point, or a digest alone cannot establish freshness or anti-replay.

No `FRESHNESS_VERIFIED` claim is permitted until a separate owner decision approves the exact trusted anchor/comparison mechanism and its scope. TTLs, expiry durations, trusted time source, monotonic sequence/anchor technology, revocation transport, replay window and rollback policy remain OPEN / NOT RATIFIED.

## 4. D09 — Owner authentication: A selected

**OWNER-DECIDED for the initial phase.** An authenticated Owner-controlled GitHub action/commit containing the exact bounded decision record may be recorded as:

`PLATFORM_ATTRIBUTED_OWNER_ACTION`

It must not be described as a cryptographically signed Owner attestation. A commit SHA, Git author/committer metadata or repository attribution alone does not prove cryptographic identity, uncompromised account control, session assurance level, or the factual truth of the attested evidence.

Each record must bind, at minimum:
- record type/schema and version;
- Owner identity reference and the platform authentication context available;
- purpose/audience;
- exact subject identifier/type/version;
- exact artifact digest and byte length, or immutable evidence references;
- claim and explicit limitations/non-claims;
- scope and applicable policy/profile version;
- unique decision identifier and any superseded decision reference;
- decision timestamp as metadata, with trusted-time status stated;
- status and supporting evidence references.

Keep these actions separate:
1. **Review attestation:** Owner confirms review of specified evidence.
2. **Privileged-action authorization:** Owner authorizes one exact action on one exact target and scope.
3. **Trust administration:** Owner changes trusted identities, policy or recovery state.

A review attestation never implicitly authorizes a privileged action. Any privileged authorization must independently bind exact target, action, scope, policy version and evidence digest/references. Cryptographic signatures and key custody remain deferred; no key operation is authorized.

## 5. Cross-decision constraints

- D06 remains manual Owner attestation only in the initial phase; autonomous issuer authenticity remains deferred.
- D07 completeness is established by scoped independent enumeration and reconciliation, not Owner assertion.
- D08 freshness is separate from integrity, Owner attribution and inventory completeness.
- D09 platform attribution is not issuer authenticity, cryptographic signature, trust-root establishment or proof of source truth.
- Missing/conflicting evidence remains unresolved and fail-closed.
- D12–D14 and any remaining dependencies remain open unless separately decided.

## 6. Explicit non-authorizations

This decision record does not authorize:
- S2 verifier/parser/adapter/registry/API/schema/source/test/fixture/workflow/CI implementation or modification;
- production evidence promotion to trusted, complete or freshness-verified;
- trusted time/anchor/revocation provider setup or external service access;
- key generation/import/custody/signing/verification/rotation/revocation or trust-root changes;
- inventory collection against VPS, T0, T1, T2, databases or external providers;
- cleanup, deletion, archive, expiry, compaction, VACUUM or other destructive lifecycle action;
- changes to T0/T1/T2, CORE_LEDGER, AI_LEDGER, Shared Risk Engine, Kill Switch or trading runtime;
- deployment, exchange connection, live trading or real orders.

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged. VPS remains absent; no runtime state is inferred.

## 7. Verification and disposition

- Scope: record the Owner's three explicit policy selections and update project handoff only.
- Tests/compile/CI: NOT RUN (documentation-only).
- Runtime/VPS/database/provider/key operations: NOT PERFORMED.
- Independent reviewer sign-off: not mandatory under the existing Owner waiver; no independent assurance claim is made.

**G0.49: DOCUMENTATION PASS — D07-A, D08-A AND D09-A OWNER-DECIDED FOR INITIAL PHASE. D12–D14 AND OTHER OPEN DEPENDENCIES REMAIN OPEN. S2 IMPLEMENTATION NOT AUTHORIZED.**

Next: prepare the next bounded decision package for remaining open dependencies. Do not begin S2 implementation without a separate exact-scope approval.
