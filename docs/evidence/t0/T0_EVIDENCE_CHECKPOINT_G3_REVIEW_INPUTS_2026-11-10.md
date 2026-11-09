# T0 Evidence Object / Checkpoint Contract v1 — G3 Independent Review Input Manifest

Date: 2026-11-10
Purpose: Freeze exact inputs for a genuinely independent static/design review of G0–G2.
Status: **REVIEW PACKAGE PREPARED — INDEPENDENT REVIEW NOT PERFORMED — G3 PENDING / NOT VERIFIED**
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/t0-centralized-data-feeder-p1-20261101
Frozen baseline commit before this manifest: 593d4c7a1362aef47ce47f3cd07df75d73dc585e

## 1. Review authority and scope

The project owner authorized automatic continuation within G0–G3. This authorizes preparation and correction of the review package, but does not allow the contributor to act as the independent reviewer.

The reviewer MUST:
- be genuinely independent of the author/contributor and must not have authored, operated or controlled the reviewed evidence/issuer/custody/anchor process;
- declare identity, relevant competence, role, conflicts of interest and independence basis;
- inspect the exact Git commit/blob inputs below, not a mutable branch tip or a summary alone;
- issue a written finding-by-finding disposition, including unresolved findings and limitations;
- avoid claiming runtime, database, provider, durability or deployment assurance from static source evidence.

This review package covers:
- Evidence Object / Checkpoint Contract v1 logical model and G0.2–G0.6 design;
- G1 selection of A and issuer/signer/custody/anchor/verifier boundaries;
- G2 synthetic-only reference implementation, tests and workflow;
- compatibility with the inspected T0 candle source and governing TSA/L4/lifecycle decisions.

It does NOT authorize or request:
- G4 code/schema/database integration;
- G5 runtime/VPS/provider/TSA/WORM/storage/identity/key/trust-root operations;
- canonical T0 database access or data probes;
- restore, fault injection, staging, archive, cleanup, vacuum, compaction, backup expiry, replica removal or deletion;
- live trading or real orders.

## 2. Frozen primary artifacts

| Artifact | Exact commit | Git blob SHA |
|---|---|---|
| docs/architecture/T0_EVIDENCE_OBJECT_CHECKPOINT_CONTRACT_V1.md | 3ae31cace87ae1596a126ce83618c7455021c9f3 | 0d98a3dcbb0d403b213b5efcae0c882ac5461578 |
| docs/PROJECT_SESSION_HANDOFF.md | 593d4c7a1362aef47ce47f3cd07df75d73dc585e | 7181b9d34fc5ed904aec4b02763f28ee0989cb0d |
| synthetic_evidence/t0_checkpoint_contract.py | 8affc8b9aa12f17a969bc34c395b3b66b5871829 | 9efd800189e15d35e231530d703499d40d9d7e5d |
| synthetic_evidence/test_t0_checkpoint_contract.py | 8882ef2e31d55eb726f9322a57096fa544797c2b | beffd8c4a6cb2682c9fe0acb09cd2b182c2fde7c |
| .github/workflows/t0-evidence-contract-g2.yml | a33a99bb26c569127aea9d153f95795df2c9c045 | 5e22648c38fd3c6e631f912010de1489bb78f9b5 |

Git blob SHA values above identify exact repository objects; they are not presented as SHA-256 file checksums.

## 3. Frozen T0 source compatibility inputs

| Artifact | Git blob SHA | Review purpose |
|---|---|---|
| market_data/store.py | 4e1b0c54bd56455abe5be0e5c7d0807e63e0bc78 | Candle validation, SQLite schema, serializer, read-window behavior |
| market_data/storage.py | 13fe1ae01ebb5318b69e69eef3e512d207f74c49 | Backend selection and read facade |
| market_data/postgres.py | 2fe27fe2d066dda0c192a381b72d27404487b800 | PostgreSQL reader/writer boundary and transaction behavior |
| market_data/migrations/001_initial_timescale.sql | 777d884d217004569e97821a76b506572ee8f5b7 | PostgreSQL physical candle schema |
| market_data/README.md | 660a2f0f4f88c0de4fa8c1be3c4af96df282de0e | Public candle/API semantics |

Source mapping conclusion is limited to these exact source objects. It does not establish live DB schema parity, runtime configuration, actual canonical data contents or deployment durability.

## 4. Governing architecture, assurance and lifecycle inputs

| Artifact | Git blob SHA | Review purpose |
|---|---|---|
| P1.8.67 provider-neutral TSA architecture assessment | 50654f3f4f4caa509598e4393e2634ea977df5dd | TSA asynchronous boundary, durable-commit-before-timestamp invariant |
| P1.8.68 independent static review of P1.8.67 | 9ae0c50830644d21d850da4c4d246a2837f62fc6 | Existing E0 static review and limitations |
| P1.8.77 read-only T0 source mapping | 35057494b5b3c240e636cfdea3505e8870361ca5 | Current T0 implementation gaps and A/B distinction |
| P1.8.78 independent static review of P1.8.77 | 4794a531befa0bf1ce2fbb428ae466fcb6a280a9 | Source mapping review scope and limits |
| P1.8.80 retention and eligibility policy | a38710c9d01e5409ce989cc73f791c94bc73773f | Retention, archive and deletion boundaries |
| L4-Minimum Acceptance Matrix | ed3056d81edfaf163205a172cf5ad22e230d7b41 | Custody, signing, freshness, offline verification and independent review controls |
| P1.8.152 lifecycle residual finding reconciliation | e1a4d95af216e94a58fa5528850fcd0c1ff465f8 | RET-01/02 and unresolved lifecycle findings |

## 5. Required review questions

### Contract and canonical bytes
1. Does T0-JCS-1 correctly define the restricted RFC 8785 profile, including UTF-16 key ordering, Unicode handling, duplicate-key rejection, numeric-string representation and canonical decimal grammar?
2. Does the synthetic implementation actually conform to RFC 8785 for the allowed input domain? Compare against independent RFC 8785 vectors or a separately maintained implementation; do not rely only on the author's own vector.
3. Are Evidence Object, row, partition and Merkle domain separators, length-prefixing, odd-node promotion, empty roots and descriptor membership unambiguous and non-circular?
4. Are persisted row fields correctly distinguished from serializer-derived values and nullable/unpopulated ingestion_batch_id?

### Completeness and snapshot
5. Does the expected candle set E, half-open range, row membership, duplicate/order checks, as-of rule and maximal gap encoding prove exactly the declared partition membership?
6. Are INVALID, INCOMPLETE and UNKNOWN precedence rules fail-closed, including partially available but malformed rows?
7. Are the SQLite single-connection read transaction and PostgreSQL REPEATABLE READ READ ONLY profiles technically accurate? Does the contract avoid claiming a stable snapshot token where none is exposed?
8. Does the checkpoint require every partition to share the exact same source transaction/snapshot?

### Commit and durability
9. Are COMMIT_OBSERVED, DATA_PRESENT_MATCH and COMMIT_OUTCOME_UNKNOWN correctly separated?
10. Does the receipt/readback design avoid claiming power-loss/host-loss durability from a successful transaction or later row visibility?
11. Is the TSA A submission gate correctly blocked until a separately proven DURABILITY_PROFILE_VERIFIED boundary exists?

### Authority, retention and L4
12. Is A correctly limited to dataset/checkpoint proof-of-existence, with B/P1.8.36 deferred and no signer/owner-intent claim?
13. Are issuer, custodian, anchor administrator, verifier and T0 writer sufficiently separated?
14. Do RET-01 B / RET-02 B, no-default-TTL and Option C remain intact?
15. Does the package satisfy the design intent of L4M-01 through L4M-10 without falsely claiming implementation, independent custody, freshness or reviewer acceptance?

### G2 test quality and execution evidence
16. Do tests cover every normative negative case and avoid false positives where another validation error causes the expected exception?
17. Does the workflow run only synthetic offline tests and avoid canonical DB/provider credentials?
18. Exact committed-SHA test execution and GitHub Actions run/artifact are currently NOT VERIFIED. The reviewer must not infer PASS from the local draft test result.

## 6. Known verification limitations at freeze

- G0.2 source mapping: PASS for inspected source blobs only.
- G0.3 canonical byte profile: PASS at contract-design level; production library and independent RFC 8785 conformance remain NOT VERIFIED.
- G0.4 completeness oracle: PASS at contract-design level; final committed implementation/test execution NOT VERIFIED.
- G0.5 snapshot protocol: specified, not implemented or runtime-qualified.
- G0.6 commit receipt/durability protocol: specified; current SQLite/PostgreSQL durability profile NOT VERIFIED.
- G1 A/role boundaries: PASS at architecture-design level; providers and identities not selected or provisioned.
- G2: synthetic files committed; pre-correction local development suite 28/28 PASS only. Corrections were subsequently committed; post-correction exact-SHA test execution is NOT VERIFIED.
- GitHub Actions: workflow committed; no run ID, successful status or artifact established.
- G3: NOT PERFORMED. Independent reviewer identity, competence and independence are NOT VERIFIED.
- G4/G5: NOT AUTHORIZED.

## 7. Required reviewer output and disposition

The reviewer must produce a separate immutable report containing:
- exact reviewed commit and blob SHA for every input;
- reviewer identity, competence, role and conflict/independence declaration;
- review method and tools;
- findings with severity, exact artifact/section, rationale and required correction;
- explicit verdict for each G0–G2 requirement;
- unresolved limitations and whether G3 may be marked PASS or must remain BLOCKED.

Until that report is received and checked against this exact manifest, status remains **G3 PENDING / NOT VERIFIED**. This manifest is a review-input index, not independent custody, not a review report and not a PASS certificate.

## 8. Safety and authorization

No canonical T0 database or data was accessed. No runtime/VPS/provider/TSA/WORM/storage/identity/key/trust-root operation occurred. No restore, fault injection, staging, archive, cleanup, vacuum, compaction, backup expiry, replica removal or deletion occurred.

Option C — No Destructive Authority — remains in force. T0 canonical and recovery data remain protected. AI_EXECUTION_ENABLED=false; paper-only; no live orders.
