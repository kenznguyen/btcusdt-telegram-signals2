# D-2026-11-09 — L4 Provenance Scope for a Personal, Non-Commercial System

Date: 2026-11-09  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Target branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Record type: owner-direction capture and bounded scope proposal  
Status: NON-COMMERCIAL DIRECTION CONFIRMED; L4-MINIMUM PROFILE PROPOSED; TECHNICAL ACCEPTANCE NOT GRANTED

## 1. Governing owner direction

The system is a personal BTCUSDT research/trading system, not a SaaS, multi-customer platform, subscription service or commercial data product. Reliability, data ownership and independent verification take priority over commercialization.

This record applies that direction to L4 Provenance. It does not amend the T0 canonical-data boundary, the existing V07/V08/Restore contracts, Option C, or any operational authorization.

## 2. Scope consequence

L4 should provide proportionate, owner-controlled assurance for one system owner. It does not need commercial product features merely to appear enterprise-grade.

Out of scope unless a concrete personal risk or legal obligation later justifies them:
- multi-tenant identity, customer isolation and customer-facing audit portals;
- customer SLA, commercial support and regulatory/compliance certification claims;
- multi-provider TSA quorum or cross-provider timestamp ordering;
- dedicated paid WORM service solely as a commercial assurance signal;
- third-party assurance reports or legal-admissibility claims;
- commercial retention schedules or customer data lifecycle workflows.

No inference is made that these features are inherently useless; they are deferred because the current system has no commercial/customer requirement.

## 3. Proposed L4-Minimum assurance profile

The following are proposed minimum controls for a personal system and remain subject to explicit owner ratification and independent review:

1. **Owner custody:** the owner retains control of canonical data, evidence exports, signing authority and trust-policy approval. T0/VPS must not be the sole custodian of the evidence needed to assess T0.
2. **Independent signing boundary:** evidence signing authority must be separated from the T0 process and its ordinary administrative/runtime credentials. Key custody and recovery must be documented; no key operation is authorized by this record.
3. **Exact-object binding:** signed evidence must bind the exact immutable checkpoint/signature/context required by P1.8.36. A digest or timestamp of an unsigned payload alone is insufficient.
4. **Independent offline verification:** the owner must be able to verify the evidence package on a separate environment without ChatGPT, the producing runtime or a live TSA connection, using a separately controlled trust-policy baseline.
5. **Independent evidence custody:** retain at least one integrity-checkable copy outside the T0/VPS failure domain. GitHub may be one repository for records but must not be the only evidence custodian or be treated as WORM.
6. **Append-only history and lifecycle control:** preserve original signed bytes, attempts, verification decisions, trust/revocation evidence and provenance. Unknown or incomplete evidence remains UNKNOWN/BLOCKED; no silent overwrite or evidence deletion.
7. **Key/trust lifecycle:** trust-root changes, key rotation/revocation and historical re-verification require explicit owner-controlled approval, traceable evidence and independent review.
8. **Claim discipline:** provenance proves integrity/attribution and only the specific timestamp assertions actually verified. It does not prove market-data truth, source completeness, event truth, database durability or trading correctness.

## 4. L4-Extended capabilities deferred

The following are not acceptance prerequisites solely because the system might someday be commercialized:
- external TSA integration and automated OCSP/CRL acquisition;
- dedicated WORM or immutable object storage;
- multiple TSA providers, quorum or failover;
- formal third-party audit and compliance certification.

A single external TSA may still be selected later if it closes a documented timestamp-assurance gap. The existing architecture correctly keeps TSA optional/asynchronous and outside T0's authoritative write path. No provider, profile, endpoint, key, trust anchor or numeric parameter is selected here.

## 5. Evidence baseline and limitations

This scope proposal is grounded in the following current-branch records:

| Record | Blob SHA | What it establishes |
|---|---|---|
| P1.8.67 TSA architecture | `50654f3f4f4caa509598e4393e2634ea977df5dd` | TSA optional/asynchronous; outside T0 write path; provider and profile unresolved |
| P1.8.68 static review | `9ae0c50830644d21d850da4c4d246a2837f62fc6` | E0 architecture review PASS only |
| P1.8.69 evidence contract | `caf0943865b096a0d592ae0718472754424991d0` | Logical evidence records and independent-verifier boundary; no implementation |
| P1.8.76 final static review | `f559f642b48f1e7ea1e7f37935d00273d53ba161` | Contract review PASS only; archive/retention/restore unverified |
| P1.8.141 lifecycle assessment | `c20616d79f6dcedde08128f589a5c0e04d6257f1` | Lifecycle design PARTIAL; runtime, authority and retention gaps |
| P1.8.152 reconciliation | `e1a4d95af216e94a58fa5528850fcd0c1ff465f8` | Lifecycle design NOT CLOSED; Option C preserved |

The static PASS results above do not establish implementation or operational readiness. Current unresolved matters include:
- V07 BLOCKED; trusted-time/revocation authority, profile and parameters unresolved;
- V08 OPEN/BLOCKED; actual durable commit/seal ordering and source-progress proof unresolved;
- Restore OPEN/BLOCKED; provider semantics and measured recovery capability unresolved;
- mutation fencing/adapter qualification NOT VERIFIED;
- runtime consumer/copy inventory NOT VERIFIED;
- 87 lifecycle negative vectors NOT RUN per P1.8.141 baseline;
- Option C technical enforcement NOT VERIFIED; GitHub permission inventory remains PAUSED;
- independent evidence custody and offline verifier capability have not been demonstrated by the cited records.

## 6. Acceptance gates

Do not mark L4 PASS until evidence demonstrates, at minimum:
- an independently controlled signing boundary;
- exact-object/signature/context binding;
- an offline verifier on a separate environment;
- a separately retained evidence copy and a verified recovery/readback procedure;
- controlled trust-root/key lifecycle and historical verification behavior;
- negative cases for tampering, missing evidence, rollback, revoked/unknown keys and unavailable dependencies;
- independent review by a qualifying reviewer who is not the evidence producer or sole authority for the claim.

If any prerequisite cannot be demonstrated, report the affected claim as NOT VERIFIED or BLOCKED. A documentary design PASS must never be promoted to a runtime PASS.

## 7. Explicit non-authorizations

This record authorizes documentation and scope alignment only. It does not authorize:
- TSA/provider selection, provider contact or endpoint calls;
- signing-key creation, export, rotation, revocation or trust-root modification;
- GitHub permission inventory or changes;
- runtime, VPS, T0/T1/T2, database, feeder, ledger or strategy changes;
- staging, restore rehearsal, fault injection, workflow dispatch or live trading;
- archive, cleanup, compaction, vacuum, backup expiry, replica removal or deletion.

Option C — No Destructive Authority — remains in force. T0 remains an independent canonical data asset. `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.

## 8. Decision status

- Personal/non-commercial system direction: CONFIRMED from the owner's prior explicit project decision.
- L4-Minimum control profile: OWNER-APPROVED on 2026-11-09 in the conversation; approval covers the scope and acceptance profile in this record only. Implementation and independent technical acceptance remain outstanding.
- L4-Extended commercial assurance features: DEFERRED unless a concrete need is established.
- L4 overall: BLOCKED / NOT VERIFIED for implementation and operational acceptance.
- This record does not close P1.8.152 residual findings or replace the documented next gate P1.8.153.


## Superseding owner governance decision — Option C revoked (2026-11-11)

The owner revoked **Option C — No Destructive Authority** on 2026-11-11. Any earlier statement in this historical record that Option C is ACTIVE, remains in force, is unchanged/current, or prohibits all destructive authority is superseded. Current status: **REVOKED**.

This revocation removes Option C as a blanket prohibition but does not authorize any particular destructive operation. Deletion, archive, cleanup, expiry, vacuum, compaction, backup/replica removal, export mutation or provider operation still requires a separately explicit, scoped approval with exact target/data class, preconditions, expected effect, dependencies, verification and recovery/rollback plan. T0 canonical data, lease/fencing, ledgers, audit/reconstruction/recovery, custody and trust evidence remain protected unless separately approved. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged. No L4 control or technical-enforcement status is promoted by this decision.
