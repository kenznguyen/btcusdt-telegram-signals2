# T0 L4-Minimum Read-Only Assurance Audit

- Date: 2026-11-10 UTC
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Source HEAD: `cad0453a93f7092ca490a54dc09b7d84dae5d4d4`
- Recursive tree: 712 entries, `truncated=false`
- Audit type: bounded read-only repository/source/document audit
- Overall result: **PARTIAL — L4-MINIMUM TECHNICAL/OPERATIONAL ACCEPTANCE BLOCKED**
- T0 canonical data, runtime, database, Feeder, VPS, credentials, keys, permissions, provider configuration and GitHub workflows were not modified.

## 1. Executive conclusion

The owner-approved L4-Minimum profile is a proportionate personal-use provenance/evidence profile with 10 controls (L4M-01 through L4M-10). It is not a commercial compliance program.

The repository contains meaningful synthetic assurance components:
- deterministic evidence generation and provenance binding;
- an Ed25519 verifier for exact caller-supplied event bytes, with unknown/revoked/unknown-revocation fail-closed tests;
- pinned Sigstore trust-root verification and a local offline-attestation verification script;
- synthetic trust-root snapshot/rotation/revocation-state logic;
- synthetic append-only event/observer-ACK/checkpoint models, including file-backed SQLite crash/reopen tests;
- a documented 13-vector synthetic fault inventory.

These are useful design and CI controls, but they are not integrated into T0's canonical candle write/read path. The current T0 source remains a candle-oriented store/Feeder with fenced writes and a query-window SHA-256 `datasetVersion`; it has no signed canonical checkpoint, owner-controlled signing authority, durable TSA outbox, production offline verifier package for T0 checkpoints, or independently custodied evidence copy demonstrated by this audit.

The existing P1.8.23 CI evidence records 162/162 synthetic tests and 13/13 synthetic fault vectors PASS at source SHA `082cc68b14148829c01fc63558f6781fa006756b`, workflow run `42557957929`, artifacts `13648297207` and `13648187759`. This is synthetic-only evidence. The recorded artifact expiry is `2026-11-16T03:43:37Z`; the retention manifest explicitly says `GIT_HISTORY` and `immutability=NOT_WORM`. It does not satisfy owner evidence custody or long-term independent recovery by itself.

**No L4 control is promoted to production PASS solely from synthetic tests, documentation, Git history or a CI artifact.**

## 2. Governing scope and exclusions

The controlling records are:
- Owner scope decision: `docs/decisions/D-2026-11-09-L4-PROVENANCE-PERSONAL-SCOPE.md`, blob `6b96c2c37a4989b7ceba291d027a3f8459eecb3b`.
- Acceptance matrix: `docs/evidence/p1-8/L4-MINIMUM-PROVENANCE-ACCEPTANCE-MATRIX.md`, blob `f39bef0c391e13a3656130f0e74f0e7a385b0c39`.

The matrix expressly makes L4 a design/test-plan baseline, not implementation acceptance. Multi-tenant/customer controls, commercial certification, multiple TSA quorum and dedicated paid WORM are outside the minimum profile absent a concrete need. External TSA integration and dedicated WORM are L4-Extended capabilities, not automatic L4-Minimum blockers.

However, L4-Minimum still requires owner-controlled evidence custody outside the T0/VPS failure domain, signing separation, exact-object binding, independent offline verification, independent readback/recovery, controlled key/trust lifecycle, append-only history, claim discipline, qualifying independent review and fail-closed verdicts.

## 3. Ten-control acceptance matrix

| Control | Audit status | Evidence and gap |
|---|---|---|
| L4M-01 Owner-controlled evidence custody | **NOT VERIFIED** | GitHub source/evidence records and short-lived Actions artifacts exist. No proof in the inspected branch that the owner has an independently controlled evidence package outside both T0/VPS and GitHub, with inventory and SHA-256 manifest, readable when T0 and GitHub are unavailable. |
| L4M-02 Signing authority separated from T0 | **NOT VERIFIED** | `synthetic_evidence/event_signatures.py` is verifier-only and has no signing API/private-key persistence. Synthetic tests create ephemeral keys. GitHub/Sigstore workflow attestation is CI provenance, not evidence that an owner-controlled signing authority and tested recovery boundary exist for T0. |
| L4M-03 Exact-object binding | **PARTIAL — synthetic/design only** | P1.8.36 requires timestamp imprint binding to exact signature bytes and immutable context. The Ed25519 verifier checks exact supplied event bytes; Sigstore attestation checks subject digest/workflow identity. T0 itself has no signed canonical checkpoint object, and P1.8.36/V07 parameters and executable timestamp fixtures remain open. |
| L4M-04 Independent offline verification | **PARTIAL — CI/synthetic only** | `synthetic_evidence/verify_offline.sh` verifies a local attestation bundle against a pinned Sigstore root; P1.8.23 records offline independent Sigstore verification PASS. No owner-operated, separate-environment verification of a real T0 evidence package with T0, GitHub, ChatGPT and network unavailable was demonstrated. |
| L4M-05 Independent readback/recovery | **PARTIAL — synthetic SQLite model only** | `root_b_checkpoint_store.py` tests file-backed SQLite process death, reopen, checkpoint recovery, duplicate ACK idempotency and corruption rejection. The adapter uses temporary test paths and explicitly does not discover/open application DBs. No independent owner-custody copy or actual restore/readback of T0 evidence was verified. |
| L4M-06 Key and trust lifecycle | **PARTIAL — synthetic policy logic only** | Trust-root snapshots, digest pinning, snapshot-chain monotonicity and explicit unknown/revoked handling have tests. Offline mode correctly reports `NOT_CHECKED_OFFLINE` and does not claim current non-revocation. No production owner key, approved trust-policy lifecycle, TSA profile/authority, real revocation evidence or historical T0 verification is implemented; V07 remains BLOCKED. |
| L4M-07 Append-only evidence history | **PARTIAL — synthetic model only** | Synthetic Root B event/ACK/checkpoint records and trust snapshot chains reject changed bytes/duplicate conflicts. The retention manifest labels storage `GIT_HISTORY`, `NOT_WORM`, with 7-day Actions artifacts. No production append-only T0 evidence journal or independently retained immutable history is demonstrated. |
| L4M-08 Claim discipline | **PASS — documentary/synthetic scope only** | P1.8.36 limits `genTime` claims to existence no later than the TSA assertion and disclaims signer intent/exact signature creation time. Synthetic README and P1.8.23 explicitly disclaim production, source truth, durability, provider independence and live integration. This PASS applies only to the reviewed claim language, not to T0 provenance capability. |
| L4M-09 Independent review | **PENDING / NOT VERIFIED** | P1.8.37/P1.8.39 independently review timestamp contract documents; P1.8.78 reviews the bounded T0 source mapping. The L4 acceptance matrix itself still says independent technical review PENDING. Actual reviewer identity, independence/competence and a review of the exact complete L4 evidence package are not established here. |
| L4M-10 Fail-closed acceptance state | **PARTIAL — synthetic tests only** | Signature verifier rejects invalid, unknown, revoked and unknown-revocation states; trust lifecycle avoids claiming revocation clearance offline; synthetic fault inventory records 13/13 PASS. Production T0 acceptance, missing-copy handling, owner custody and real trust failures remain NOT VERIFIED. The separate 87 lifecycle negative vectors in P1.8.141 remain NOT RUN. |

## 4. T0 source integration findings

The source mapping in P1.8.77 (`35057494b5b3c240e636cfdea3505e8870361ca5`) and its static review P1.8.78 (`4794a531befa0bf1ce2fbb428ae466fcb6a280a9`) were rechecked against current branch blobs:

- `market_data/store.py`: `4e1b0c54bd56455abe5be0e5c7d0807e63e0bc78`.
- `market_data/write_gateway.py`: `b2029d9db15fe39dcbe575acfeb6df1b16e16acd`.
- `market_data/feeder.py`: `935d295ef42c94482a48ce6ccdc927ebfa4c7e22`.
- `market_data/feeder_service.py`: `bdcecf6bc98a2ff070f83098d2c50154a160c99c`.
- `market_data/api.py`: `81733c9b6de811cbebb2f5d472d41f37f337990c`.
- PostgreSQL migrations 001–004: `777d884d...`, `009474f...`, `1e08f77a...`, `cc79631a...`.

Confirmed source characteristics:
1. T0 stores canonical market candles and uses lease/generation-fenced writes.
2. SQLite writer uses `BEGIN IMMEDIATE`, validates the lease and rechecks it before commit.
3. PostgreSQL writer/migrations provide lease/fenced write logic; source inspection does not establish deployed backend selection, production synchronous durability or replication/failure-domain guarantees.
4. Feeder completion boundary is process-memory scheduler state, not a persisted immutable checkpoint/watermark.
5. `datasetVersion` is SHA-256 of the selected read-window JSON response, not a whole-database digest, signed checkpoint, immutable evidence object or proof of durable commit.
6. No T0 signing operation, signed checkpoint, timestamp-intent/outbox, RFC 3161 verifier/archive or WORM adapter/configuration appears in the inspected T0 source/migrations.

P1.8.77 F-19 remains OPEN/HIGH: the owner must decide whether a future T0 timestamp subject is (A) a deterministic dataset/checkpoint manifest, (B) a signed-object historical-verification object under P1.8.36, or two separately versioned products. This is a design prerequisite for TSA work, not a requirement to buy a TSA for L4-Minimum.

## 5. Lifecycle and destructive-authority boundary

P1.8.152 remains the latest lifecycle reconciliation:
- RET-01 B / RET-02 B are owner-ratified policy only.
- T0 canonical data and its availability/recovery copies remain protected from routine, automatic or scheduled deletion.
- RET-03 and RET-06–RET-10 remain open/not verified; no numeric retention floor or object eligibility has been established.
- V07 remains BLOCKED; V08 and Restore remain OPEN/BLOCKED.
- Mutation-fence/adapter qualification remains NOT VERIFIED.
- Runtime consumer/copy inventory remains NOT VERIFIED.
- 87 lifecycle negative vectors remain NOT RUN.
- Option C technical enforcement remains NOT VERIFIED; GitHub permission inventory remains PAUSED.
- Archive remains non-executable; no deletion authority exists.

This means L4 evidence retention and recovery obligations are not closed. It does not justify adding a destructive retention mechanism or treating WORM as mandatory.

## 6. Consolidated status

- L4 profile/scope: OWNER-APPROVED.
- L4 acceptance matrix: DOCUMENTATION BASELINE only.
- L4M-08: documentary claim discipline PASS within scope.
- L4M-03/04/05/06/07/10: PARTIAL synthetic/design evidence; production NOT VERIFIED.
- L4M-01/02: NOT VERIFIED.
- L4M-09: PENDING / NOT VERIFIED.
- T0 source-to-L4 integration: BLOCKED by missing signed checkpoint/evidence object and custody/verifier path.
- TSA: L4-Extended, not mandatory for minimum profile; T0 TSA integration remains BLOCKED on object-model and V07 decisions.
- WORM: dedicated WORM is not mandatory for minimum profile; no technical WORM claim is supported. The required independent evidence custody/readback remains unproven.
- Overall L4-Minimum technical/operational acceptance: **BLOCKED / NOT VERIFIED**.

## 7. Next bounded gates (no execution authorized)

1. Independent review of the L4 acceptance matrix and this exact audit report, with explicit reviewer identity/independence/competence evidence. This review must not be represented as performed by the author of this report.
2. Define a minimum T0 evidence object/checkpoint contract that does not silently repurpose `datasetVersion`; decide whether the initial provenance claim is integrity/attribution only or includes a timestamped checkpoint.
3. Define owner-controlled signing boundary and a separate owner evidence-custody location outside T0/VPS and GitHub; specify a readback/recovery proof before any operational action.
4. Freeze a separate offline verifier package and trust-policy snapshot for the exact T0 evidence object; keep unknown/revoked/unavailable states fail-closed.
5. Keep V07, V08 and Restore lifecycle gates open until their own exact parameters and evidence are resolved. No inference from synthetic tests.
6. Preserve T0 canonical data and recovery copies. No TSA provider call, key operation, permission inventory, runtime probe, restore, staging, fault injection, archive, cleanup, vacuum, compaction, backup expiry, replica removal or deletion without separate explicit authorization.

## 8. Verification and authorization

- Source ref: `cad0453a93f7092ca490a54dc09b7d84dae5d4d4`; recursive tree complete (`truncated=false`, 712 entries).
- Documents/source blobs: exact identities recorded in this report and referenced P1.8 records.
- Tests for this audit: **NOT RUN** (read-only).
- Existing synthetic CI evidence: run `42557957929`, source SHA `082cc68b14148829c01fc63558f6781fa006756b`, 162/162 PASS, 13/13 synthetic vectors PASS; artifacts `13648297207` and `13648187759`, recorded expiry `2026-11-16T03:43:37Z`. Not L4 production acceptance.
- GitHub Actions for this audit: **NOT DISPATCHED**; no new run/artifact.
- Runtime/VPS/database/consumer/copy/provider/personnel/identity/effective-permission inventory: **NOT PERFORMED / NOT VERIFIED**.
- No TSA/OCSP/CRL calls, provider contact, signing-key/trust-root operation, workflow dispatch, restore, staging, fault injection or runtime probe.
- No source/schema/API/runtime/VPS/Feeder/SQLite/PostgreSQL/data/credential/key/permission changes.
- No archive, cleanup, vacuum, compaction, backup expiry, replica removal, export mutation or deletion.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Option C — No Destructive Authority — remains in force.

**Final verdict: BOUNDED READ-ONLY AUDIT COMPLETE — L4-MINIMUM DOCUMENTATION/SYNTHETIC PARTIAL — T0 TECHNICAL/OPERATIONAL ACCEPTANCE BLOCKED — NO RUNTIME OR DESTRUCTIVE ACTION.**
