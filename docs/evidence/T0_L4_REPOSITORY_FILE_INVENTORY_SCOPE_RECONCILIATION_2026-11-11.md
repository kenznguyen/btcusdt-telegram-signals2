# T0 L4-Minimum Repository-File Inventory — Reference Scope Reconciliation

Date: 2026-11-11
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Reference scan commit: `1c9ab68ed61ed4352e4775ecbeb03647731b9ae5`
Status: **DOCUMENTARY SCOPE RECONCILIATION — NOT A COMPLETE L4 EVIDENCE PACKAGE — NO CONTROL ACCEPTANCE**

## 1. Purpose and method

Reconcile literal repository-path references found in the 32-file exact-commit inventory across the current L4 matrix, register, automation plan, owner decisions, historical audit/review documents and lifecycle records. Every path selected for inclusion was resolved through GitHub at the stated branch commit and bound to its exact Git blob SHA in `ci/l4-repository-file-inventory.json`.

This is a bounded reference/path review, not a semantic audit of every referenced document and not proof that every possible L4 evidence object exists. A reference in a historical document does not automatically make its target a controlling L4 evidence object.

## 2. Additional source objects included

Three additional files are included in the next inventory revision because they materially support L4 scope or lifecycle lineage:

| Path | Git blob SHA | Inclusion reason |
|---|---|---|
| `docs/evidence/T0_COMPONENTS_OUTSIDE_L4_MINIMUM_AUDIT_2026-11-10.md` | `7bfc509b9eb918750b3a25acc18f8d4f989d387f` | Historical scope audit distinguishing L4-Minimum controls from optional T0/TSA/WORM/HTTPS/PostgreSQL/DR work; preserve as historical, not as current acceptance authority |
| `docs/evidence/p1-8/P1.8.142-owner-retention-and-data-class-disposition-decision-package.md` | `a8b6027c5ff25192ebba82dadc52c70dd1983c82` | Predecessor lifecycle decision package; historical lineage to owner-ratified P1.8.143 and later P1.8.152 |
| `docs/evidence/COMMERCIAL_SCOPE_CONTENT_AUDIT_2026-11-09.md` | `dc313df4a9c11893751e43cec41042c58198cfff` | Supporting scope audit for the personal/non-commercial owner decision; its bounded audit result is not repository-wide proof of absence |
| `docs/evidence/T0_TSA_WORM_READ_ONLY_AUDIT_2026-11-10.md` | `4a7b872656ec240ddd6862f7ed6d92ca6c26fcee` | Historical review of TSA/WORM claims; included to preserve L4 scope boundaries, not as operational TSA/WORM evidence |
| `docs/evidence/p1-8/P1.8.80-retention-and-eligibility-policy.md` | `a38710c9d01e5409ce989cc73f791c94bc73773f` | Historical retention-policy predecessor; subordinate to current owner-ratified lifecycle records |
| `docs/evidence/p1-8/P1.8.121-owner-decision-ratification-option-c-no-destructive-authority.md` | `b92c63f593af0088fc522a55dc841af0ad1e5ac7` | Historical owner ratification establishing Option C — No Destructive Authority |
| `docs/evidence/p1-8/P1.8.141-holistic-data-lifecycle-design-closure-assessment.md` | `c20616d79f6dcedde08128f589a5c0e04d6257f1` | Historical lifecycle assessment preceding P1.8.142 and current P1.8.143/152 records |

The reconciliation report itself is also included as a source-controlled scope record. The selected repository-file inventory therefore expands from 36 to 40 exact paths.

## 3. Referenced paths excluded from the L4-Minimum evidence-source set

The following exact paths were found in the scanned documents and resolved at the reference scan commit. They remain separate T0 architecture, deployment, security, T1/T2 runtime or process records; they are not used as L4 provenance evidence or as substitutes for owner custody, signer separation, freshness, offline verification or tamper-evident history.

| Path | Git blob SHA | Exclusion reason |
|---|---|---|
| `docs/PROJECT_SESSION_HANDOFF.md` | Not pinned in this report | Mutable session/process handoff; it records progress but is not an immutable L4 source-evidence object |
| `docs/T0_PRODUCTION_SECURITY_BACKUP_RPO_RTO.md` | `d5e7ed8f9a6608fcfcb97a01cc1ced9119d76f61` | Separate production security/backup/RPO/RTO engineering scope |
| `docs/T0_STAGING_ACCEPTANCE_CHECKLIST.md` | `bece714ef5a5a5fabd847ebd012218379837fc35` | Separate staging acceptance scope |
| `docs/T0_STAGING_PROVIDER_RESEARCH.md` | `f511b259daf576f44037399555045a1c45a00f1f` | Provider research/procurement context; no provider selection or account/runtime acceptance implied |
| `docs/architecture/T0_API_DOMAIN_SELECTION_CRITERIA_2026-11-08.md` | `c647911d0e6ad36320e2ec03a95ee4247df9c475` | API domain/deployment design, not provenance evidence |
| `docs/architecture/T0_T1_T2_DATA_CONSUMPTION_ARCHITECTURE_2026-11-08.md` | `1b11883b9d2b93e3039d509ecaed98694afe430e` | Cross-layer data transport architecture, not L4 assurance evidence |
| `docs/architecture/T0_CANDLE_API_HTTPS_FRONT_DOOR_DESIGN_2026-11-08.md` | `bd8d0f7dff159494fd954f5f14c7949b74e0c607` | Separate HTTPS/front-door deployment design |
| `docs/architecture/T0_READ_ONLY_CANDLE_CONTRACT_V1_2026-11-08.md` | `e4ce9e30b64c73610369dcfeeb8d76dd88f99be9` | T0 consumer/API data contract, not an L4 provenance evidence object |
| `docs/evidence/t0/T0_INTERNAL_API_SECURITY_REVIEW_2026-11-08.md` | `a94db66682d3410d858e39176b075f67262c9c54` | Separate API security review; does not prove L4 signer/custody controls |
| `docs/evidence/t1/T1_MANUAL_VPS_TEST_RECEIPT_2026-11-09.md` | `0f756f89140eb1272e0f30d7e9de332921581e17` | T1 manual VPS test evidence; separate layer/runtime scope |
| `docs/evidence/t2/T2_LIVE_T0_ENDPOINT_OFFLINE_READINESS_AUDIT_2026-11-08.md` | `51629f6086b8aea4ab606895ec329ecaa435fc91` | T2 endpoint readiness evidence; not L4 evidence custody or offline cryptographic verification |

| `docs/architecture/SHARED_DATA_FOUNDATION.md` | `18f8566723b95c4b38586e3848bde5305295a4dc` | Shared data architecture background; not an L4 control evidence object |
| `docs/architecture/T0_PG16_ROLE_PROVISIONING_PROVIDER_CAPABILITY_DECISION.md` | `f6f8fffcc05214e2fc285cf5920a413da526a9b9` | PostgreSQL provider/role qualification, separate backend engineering gate |
| `docs/architecture/T0_POSTGRESQL_ATOMIC_WRITER_P0_2026-11-05.md` | `beca4f06321bfda109c9a326b3b6ff078a72e616` | PostgreSQL writer implementation design, separate T0 backend gate |
| `docs/architecture/DATASET_CONSUMER_CONTRACT.md` | `ef5e946b26ad17410023a79a765be73aeb198f0f` | General consumer lifecycle contract; not a signed L4 evidence object |
| `docs/architecture/DATA_DELETION_SAFETY_CONTRACT.md` | `e055d88308d8576c5c6826e12280b847f5ec5717` | General deletion-safety design; does not grant destructive authority |
| `docs/architecture/DATA_COPY_BACKUP_REPLICA_LIFECYCLE_CONTRACT.md` | `639e5ee5b5a78130cc523a4bcab8b77c0a0a5463` | General copy/backup/replica lifecycle contract; broader than L4 evidence custody |

These exclusions do not invalidate the documents or their separate engineering gates. They prevent cross-layer readiness material from being silently counted as L4 control evidence.

## 4. Historical references and unresolved path resolution

- P1.8.142 is included as a historical lifecycle predecessor. Its older subordinate policy/contract references are not promoted over current controlling records P1.8.143, P1.8.144 and P1.8.152.
- The historical T0 components-outside-L4 audit is included unchanged. Its matrix SHA and status language are historical snapshots and must not be rewritten to resemble the current matrix.
- That historical audit includes several basename-only references (for example, TSA/WORM and PostgreSQL source records) without a fully qualified repository path in its evidence table. They are not guessed or silently inserted into the inventory. If a later L4 claim relies on one of those records, resolve its exact repository path and blob SHA first.
- The commercial-scope content audit is bounded evidence for personal-project scope, not proof that all repository or external account surfaces are free of commercial capabilities.
- The session handoff is intentionally excluded because it is mutable process state. Exact workflow/run/artifact evidence remains separately identified in the handoff and Actions artifact inventory.

## 5. Inventory contract and limitations

- Included repository files are allowlisted by exact path and expected Git blob SHA-1.
- The CI job checks the exact checkout commit and branch, Git tree path, regular-file mode, expected blob identity and raw-object SHA-256.
- Missing/ambiguous paths, unsafe/duplicate paths, non-regular objects, stale blob IDs and size-limit violations fail closed.
- Repository files and GitHub Actions artifacts remain separate inventory classes. This reconciliation does not expand or replace the four-artifact Actions allowlist.
- A source-file inventory is not owner custody/readback, a signature, a trusted latest-head anchor, independent offline verification, production runtime evidence or L4 acceptance.
- No historical audit or owner decision is modified by this report.

## 6. Verdict

**Reference reconciliation: PARTIAL PASS.** Seven historical scope/lifecycle records and this reconciliation report are included in the 40-file inventory; operational, API, PostgreSQL/provider, T1/T2 and handoff references are explicitly excluded with reasons. All known basename-only citations in the historical T0 components-outside-L4 audit have exact paths and blob SHAs resolved; the scan remains bounded and is not a repository-wide completeness proof.

**L4-Minimum aggregate: BLOCKED / NOT VERIFIED.** No L4 control is promoted. Signature/negative verification and network-disabled offline verification remain downstream until the complete source and Actions-artifact inventories are reconciled and stable.

Option C — No Destructive Authority — remains ACTIVE. No VPS access, canonical T0 SQLite access, signer/key operation, trust-root mutation, cleanup, archive, expiry, vacuum, compaction, backup expiry, replica removal or deletion is authorized or performed.


## Superseding owner governance decision — Option C revoked (2026-11-11)

The owner revoked **Option C — No Destructive Authority** on 2026-11-11. Any earlier statement in this historical record that Option C is ACTIVE, remains in force, is unchanged/current, or prohibits all destructive authority is superseded. Current status: **REVOKED**.

This revocation removes Option C as a blanket prohibition but does not authorize any particular destructive operation. Deletion, archive, cleanup, expiry, vacuum, compaction, backup/replica removal, export mutation or provider operation still requires a separately explicit, scoped approval with exact target/data class, preconditions, expected effect, dependencies, verification and recovery/rollback plan. T0 canonical data, lease/fencing, ledgers, audit/reconstruction/recovery, custody and trust evidence remain protected unless separately approved. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged. No L4 control or technical-enforcement status is promoted by this decision.
