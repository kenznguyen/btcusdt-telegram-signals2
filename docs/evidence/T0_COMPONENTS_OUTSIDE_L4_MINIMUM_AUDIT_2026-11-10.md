# T0 Components Outside L4-Minimum — Read-Only Scope Audit

- Date: 2026-11-10
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Branch HEAD at audit start: `bda461e0a3d0752da2545ad3f84575e2121821cf`
- Audit type: bounded read-only source and architecture-document review
- Scope: identify T0-related components/claims that are not required by the owner-approved personal-use L4-Minimum profile, distinguish optional enhancements from separate T0 engineering/security requirements, and identify scope creep.
- Result: **DOCUMENTARY REVIEW COMPLETE — NO IMPLEMENTATION OR OPERATIONAL ACCEPTANCE CLAIMED**

## 1. Governing boundary

The controlling L4-Minimum matrix is `docs/evidence/p1-8/L4-MINIMUM-PROVENANCE-ACCEPTANCE-MATRIX.md`, blob `ed3056d81edfaf163205a172cf5ad22e230d7b41`.

L4-Minimum is a personal, non-commercial provenance/evidence profile. It requires L4M-01–L4M-10: owner-controlled independent evidence custody/readback, signing separation, exact-object binding and freshness anchor, offline verification, independent recovery/readback, key/trust lifecycle, tamper-evident history, claim discipline, qualifying independent review and fail-closed aggregate acceptance.

The matrix expressly excludes independent market-data-source corroboration. It also states that multi-TSA quorum, dedicated WORM and paid third-party assurance are not required absent a concrete need. TSA is not mandatory solely for L4M-06; without qualifying trusted-time and revocation evidence, historical trust-at-time remains UNKNOWN/NOT ESTABLISHED.

L4-Minimum does NOT mean “no security controls”. It still requires the controls listed above. A feature being outside L4-Minimum does not automatically mean it is unnecessary for safe T0 operation or for a separately chosen claim.

## 2. T0-related components outside L4-Minimum

| Component / claim | L4-Minimum status | Classification and recommendation |
|---|---|---|
| RFC 3161 TSA integration for T0 checkpoint/data existence | Not mandatory | **L4-Extended / optional claim capability.** Keep asynchronous and outside Feeder commit path. Only pursue if the owner wants a trusted third-party time assertion for a precisely defined object and durable-commit boundary. |
| TSA provider selection, certificate/OCSP/CRL interoperability, TSA policy OID, multi-provider failover | Not mandatory for base L4 | **Optional provider assurance.** Do not provision/contact providers as part of L4 closure. If historical time is claimed, these become prerequisites for that claim, not universal T0 prerequisites. |
| Multi-TSA quorum or independent timestamp authorities | Explicitly not required | **Out of minimum scope.** Avoid unless threat model or legal/evidentiary requirement justifies the cost and complexity. |
| Dedicated WORM / Object Lock / Bucket Lock for T0 canonical candle database | Not required by L4-Minimum | **Optional stronger immutability architecture; not a current T0 control.** L4M-07 requires tamper-evident history and an independently retained owner-controlled copy/manifest, not WORM. Do not describe SQLite WAL, DB fencing, Git history or CI artifacts as WORM. |
| Two-root Root A / Root B WORM topology, separate cloud accounts, dual provider administration, provider exit tests | Not required for T0 L4-Minimum | **Separate forward-evidence architecture.** Existing Root A/Root B design is not T0 canonical-store WORM and must not be pulled into T0 by analogy. Consider only if the project separately adopts this threat model. |
| Independent market-data source corroboration (e.g. second exchange as truth oracle) | Explicitly excluded | **Out of L4-Minimum.** Binance USD-M BTCUSDT remains the selected canonical source per current design. Kraken Spot is a separate research dataset; OKX Shadow/non-canonical is not an L4 requirement. Do not treat a second venue as a substitute for evidence custody or offline verification. |
| Independent market-data replicas / multi-exchange consensus | Explicitly excluded | **Out of L4-Minimum.** No quorum, consensus, venue voting or cross-exchange reconciliation requirement is created by L4. Separate data-quality research may justify it, but it is a different objective. |
| Commercial controls: multi-tenant/customer isolation, subscription, billing, customer audit portal, SLA, commercial certification | Explicitly excluded by personal-use scope | **Out of scope.** Do not add SaaS/commercial architecture to T0. |
| Public HTTPS API front door, custom DNS, Caddy/reverse proxy, public TLS certificate | Not an L4 provenance requirement | **Separate deployment/security workstream.** It may be required before exposing the API publicly, but it is not an L4 evidence control. Current design says NOT DEPLOYED; no public endpoint established. |
| PostgreSQL/Timescale provider qualification and privileged role-provisioning capability | Not an L4 provenance requirement | **Separate storage/backend engineering gate.** Needed only if selecting PostgreSQL as an operational backend. Do not make managed PostgreSQL provider certification a condition of documentary L4-Minimum design. |
| Production host/power-loss durability qualification (D2–D4), storage-provider guarantees and fault injection | Not a blanket L4 technology requirement; claim-dependent | **Separate durability assurance gate.** A successful DB commit/readback is not power-loss durability. If a checkpoint claims durable commit, its exact failure-domain profile must be proven. Do not claim this from L4 labels or synthetic tests. |
| Production restore rehearsal, measured RPO/RTO, multi-region DR | Not automatically required by L4-Minimum | **Separate operational resilience objective.** L4M-05 requires independent evidence readback/recovery and non-destructive verification; it does not automatically require production database restore, multi-region DR or a paid backup service. |
| Numeric retention floors, TTLs, grace periods, lifecycle timers, automated archive/cleanup/delete | Not an L4-Minimum requirement; destructive actions are prohibited under current policy | **Separate lifecycle-governance workstream; currently OPEN/BLOCKED.** RET-03 and RET-06–RET-10 remain unresolved. Option C prohibits archive and destructive transitions. No auto-delete-after-use, TTL or expiry may be introduced. |
| Automatic evidence expiry based on GitHub Actions artifact retention | Not acceptable as L4 evidence-retention policy | **Not a valid substitute.** CI artifact expiry is a platform setting, not owner-approved retention. Git history and short-lived Actions artifacts are not independent custody and not WORM. |
| T0 evidence checkpoint contract G0–G3 | Not itself a mandatory L4 component set | **Optional assurance implementation path that can support L4 claims.** Its content identity, completeness, snapshot, durability and role boundaries are useful, but G2 exact-SHA execution is NOT VERIFIED and G3 independent review is PENDING. Do not call the checkpoint implementation complete or an L4 pass. |

## 3. Distinctions that must remain explicit

1. **TSA vs L4M-06:** L4 requires truthful separation of signature validity, current trust and historical trust-at-time. It does not require TSA. Without qualified time/revocation evidence, historical status remains UNKNOWN.
2. **WORM vs L4M-07:** L4 requires tamper evidence and an independently retained owner-controlled manifest/copy, with storage-administrator assumptions stated. It does not require absolute immutability or WORM.
3. **Data-source independence vs evidence-custody independence:** a second exchange is not required; independent custody of the evidence package and latest-head anchor outside T0/VPS and GitHub is required.
4. **Evidence readback vs production DR:** L4M-05 does not authorize overwriting/restoring the canonical T0 database. Evidence-package readback is a separate, non-destructive assurance task.
5. **Policy protection vs technical enforcement:** RET-01 B protects T0 canonical data by owner policy; it is not technical WORM. Option C remains the operative no-destructive-authority boundary.
6. **Synthetic PASS vs production PASS:** synthetic models, GitHub history, CI artifacts and design documents cannot establish production T0 custody, signer separation, runtime parity, durability, provider independence or L4 acceptance.

## 4. Findings / scope risks

- **SR-01 — TSA/WORM scope inflation risk (HIGH):** prior T0 evidence discussions can make TSA and WORM appear mandatory. The controlling matrix expressly says otherwise. Keep both outside the L4-Minimum acceptance denominator unless the owner separately approves a claim-specific extension.
- **SR-02 — Source independence confusion (HIGH):** do not add Kraken/OKX corroboration or multi-venue consensus to L4. This does not waive L4 evidence-custody independence.
- **SR-03 — Evidence architecture conflation (HIGH):** forward-evidence Root A/Root B WORM designs are not deployed T0 candle-store controls. Keep their ownership, failure domains and scope separate.
- **SR-04 — Operational resilience conflation (MEDIUM):** PostgreSQL provider qualification, D2–D4 durability, production restore and HTTPS front-door deployment are separate T0 engineering gates, not automatic L4 provenance criteria.
- **SR-05 — Lifecycle scope creep (HIGH):** retention-floor and automated cleanup work must not be imported into L4 as a reason to weaken preservation. RET-03/06–10 remain open; Option C prohibits destructive execution.
- **SR-06 — False assurance risk (HIGH):** never claim TSA-backed time, WORM, independent custody, durable checkpoint, production restore, or L4 PASS without the exact corresponding evidence and qualifying independent review.

## 5. What remains mandatory for L4-Minimum

Do not remove or downgrade these controls merely because adjacent advanced features are out of scope:

- L4M-01: owner-controlled evidence copy and latest-head anchor outside both T0/VPS and GitHub, with independent readback during failure-domain outages.
- L4M-02: owner signing authority separated from T0 runtime/admin credentials.
- L4M-03: exact-object binding and separately authenticated latest-head/monotonic freshness anchor.
- L4M-04: deterministic offline verification using pinned trust-policy material.
- L4M-05: independent evidence readback/recovery, without implying production DB restore.
- L4M-06: key/trust lifecycle; historical trust-at-time remains UNKNOWN absent qualifying time/revocation proof.
- L4M-07: tamper-evident history and independently retained manifest/copy; no WORM claim unless separately proven.
- L4M-08: claim discipline.
- L4M-09: genuinely independent, competent reviewer with conflict assessment.
- L4M-10: all mandatory controls PASS against the same frozen baseline and a separate review disposition.

## 6. Evidence inspected

| Artifact | Blob SHA | Purpose |
|---|---|---|
| `L4-MINIMUM-PROVENANCE-ACCEPTANCE-MATRIX.md` | `ed3056d81edfaf163205a172cf5ad22e230d7b41` | Controlling scope and L4M-01–10 |
| `T0_L4_MINIMUM_READ_ONLY_AUDIT_2026-11-10.md` | `cfecb7428508adf23e6b9e71dc0dfe1e0e38080c` | Existing implementation gap assessment |
| `T0_L4_MINIMUM_ADVERSARIAL_REVIEW_2026-11-10.md` | `a7aec29330d71cb4d34193d6db81b8e20eb295f1` | Scope/freshness/custody adversarial findings |
| `T0_TSA_WORM_READ_ONLY_AUDIT_2026-11-10.md` | `4a7b872656ec240ddd6862f7ed6d92ca6c26fcee` | TSA/WORM source mapping |
| `T0_EVIDENCE_OBJECT_CHECKPOINT_CONTRACT_V1.md` | `0d98a3dcbb0d403b213b5efcae0c882ac5461578` | G0–G3 checkpoint design boundaries |
| `SHARED_DATA_FOUNDATION.md` | `18f8566723b95c4b38586e3848bde5305295a4dc` | Shared data architecture scope |
| `T0_CANDLE_API_HTTPS_FRONT_DOOR_DESIGN_2026-11-08.md` | `bd8d0f7dff159494fd954f5f14c7949b74e0c607` | Separate HTTPS deployment design |
| `T0_PG16_ROLE_PROVISIONING_PROVIDER_CAPABILITY_DECISION.md` | `f6f8fffcc05214e2fc285cf5920a413da526a9b9` | Separate PostgreSQL provider gate |
| `T0_POSTGRESQL_ATOMIC_WRITER_P0_2026-11-05.md` | `beca4f06321bfda109c9a326b3b6ff078a72e616` | Separate backend/writer gate |
| `P1.8.80-retention-and-eligibility-policy.md` | `a38710c9d01e5409ce989cc73f791c94bc73773f` | Retention scope and non-executable policy |
| `P1.8.152-retention-and-lifecycle-residual-finding-reconciliation.md` | `e1a4d95af216e94a58fa5528850fcd0c1ff465f8` | Current unresolved lifecycle gates |

## 7. Overall verdict and limitations

- Scope classification: **PASS — documentary interpretation**.
- TSA integration: **OUTSIDE L4-MINIMUM / OPTIONAL L4-EXTENDED**; production path remains blocked/not implemented.
- Dedicated WORM: **OUTSIDE L4-MINIMUM**; not implemented/qualified for T0.
- Independent market-data corroboration: **EXPLICITLY OUTSIDE L4-MINIMUM**.
- Commercial/multi-customer controls: **OUT OF PERSONAL PROJECT SCOPE**.
- HTTPS front door, PostgreSQL provider/role qualification, D2–D4 durability and production DR: **SEPARATE T0 ENGINEERING/OPERATIONS GATES**, not L4 provenance criteria.
- Mandatory L4 controls: **still NOT ACCEPTED operationally**; prior read-only audit says L4M-01/02 NOT VERIFIED, several controls PARTIAL, L4M-09 PENDING, aggregate acceptance BLOCKED/NOT VERIFIED.
- This review is same-session documentary analysis, not a qualifying independent review.
- Tests/workflows: NOT RUN / NOT DISPATCHED by this audit.
- Source/runtime/schema/database/VPS/provider/key/permission changes: NONE.
- No TSA/OCSP/CRL/provider call, WORM provisioning, restore, fault injection, archive, cleanup, vacuum, compaction, backup expiry, replica removal or deletion.

**Final: advanced components are classified and kept outside the L4-Minimum denominator. The minimum evidence controls remain mandatory and unaccepted until their own evidence and independent review are complete.**


## Superseding owner governance decision — Option C revoked (2026-11-11)

The owner revoked **Option C — No Destructive Authority** on 2026-11-11. Any earlier statement in this historical record that Option C is ACTIVE, remains in force, is unchanged/current, or prohibits all destructive authority is superseded. Current status: **REVOKED**.

This revocation removes Option C as a blanket prohibition but does not authorize any particular destructive operation. Deletion, archive, cleanup, expiry, vacuum, compaction, backup/replica removal, export mutation or provider operation still requires a separately explicit, scoped approval with exact target/data class, preconditions, expected effect, dependencies, verification and recovery/rollback plan. T0 canonical data, lease/fencing, ledgers, audit/reconstruction/recovery, custody and trust evidence remain protected unless separately approved. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged. No L4 control or technical-enforcement status is promoted by this decision.
