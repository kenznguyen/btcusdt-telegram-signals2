# T0 L4-Minimum — Automation Plan and Owner-Only Decision Boundaries

Date: 2026-11-10
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Status: **OWNER-APPROVED PLAN — LINEAGE GATE PASS — FOUR-ARTIFACT ACTIONS INVENTORY PILOT PASS — 40-FILE REPOSITORY INVENTORY CI PASS; REFERENCE RECONCILIATION PARTIAL PASS; REMAINING L4 CONTROLS NOT VERIFIED**
Approval: owner approval in conversation on 2026-11-10 to automate L4M-01–08 as far as technically possible and reserve owner participation for real-world custody/control assertions and L4M-10 acceptance.
Controlling matrix: `docs/evidence/p1-8/L4-MINIMUM-PROVENANCE-ACCEPTANCE-MATRIX.md` (current branch blob at plan preparation: `75db0d98134fd656d91a8545bc307c56595aebf7`).
Current register at plan preparation: `docs/evidence/T0_L4_MINIMUM_NINE_CONTROL_EVIDENCE_ACQUISITION_REGISTER_2026-11-10.md` (blob `0125abfe77c0d0f9172e66aa5d09ec8fc8a33623`).

## 1. Approved operating principle

Automate collection, hashing, structural validation, cryptographic verification, negative testing, cross-reference checks and report generation wherever the required bytes and trust inputs are available to GitHub Actions or a bounded read-only collector.

Do not make the owner manually perform a test that can be performed deterministically by CI. Do not infer real-world control or owner intent from CI. Owner participation is limited to facts that cannot be established by repository/CI evidence and the final owner disposition.

The nine active controls remain L4M-01–08 and L4M-10. L4M-09 remains OWNER-WAIVED. This plan does not change the acceptance matrix, weaken any PASS criterion, grant operational authority or make L4-Minimum accepted.

## 2. Per-control automation split

| Control | Automatable work | Owner-only assertion / remaining boundary | PASS discipline |
|---|---|---|---|
| L4M-01 — custody | Discover approved GitHub artifacts/files; produce deterministic package inventory; hash every included object; validate manifest schema and duplicate/path anomalies; download exact GitHub artifact bytes and verify digest; compare VPS read-only inventory/readback report when supplied through the approved bounded channel; generate custody report | Confirm which package/copy is owner-designated and attest any VPS custody/readback fact that CI cannot independently observe. No owner action is needed for GitHub bytes already fetched and hashed by automation | CI can mark GitHub-side integrity subchecks PASS. Overall L4M-01 remains NOT VERIFIED until required owner custody assertions and all claimed-copy readbacks satisfy the controlling matrix |
| L4M-02 — signer separation | Parse signer metadata/fingerprints; verify signatures against pinned trust policy; inspect workflow/permission boundaries; run adversarial tests proving ordinary T0 runtime credentials cannot satisfy the verifier's owner-signature policy; produce a separation evidence report | Confirm actual owner control/custody and recovery boundary only where it is not provable from machine-verifiable policy/permissions. No key creation/import/export/rotation or privilege probing | No signer is accepted solely because a test key or CI identity exists. Missing actual approved signer evidence = NOT VERIFIED |
| L4M-03 — exact binding/freshness | Verify exact payload bytes, digest, schema, dataset identity and signed envelope; test single-byte mutation, payload/signature swap, dataset substitution and replay; compare checkpoint with authenticated latest-head anchor; verify anchor digest and lineage | Owner confirms anchor is the designated owner-controlled latest-head reference only if that designation cannot be established cryptographically/documentarily | Missing or unauthenticated anchor => freshness UNKNOWN / NOT VERIFIED; sequence/generation alone is insufficient |
| L4M-04 — offline verification | Build/pin verifier; run in isolated GitHub job with network disabled; verify exact package and pinned trust snapshot; test unknown root, malformed bundle, unavailable verifier, incomplete package and fail-closed behavior; record source SHA and full output | Owner-run offline confirmation remains necessary only if the matrix requires verification in the owner's separate environment. CI offline PASS is a separate subcheck and cannot be relabelled owner-run | Keep CI_OFFLINE_VERIFICATION and OWNER_OFFLINE_VERIFICATION separate. Overall control cannot PASS until the matrix's owner-verification requirement is met |
| L4M-05 — readback/recovery | Read back exact GitHub artifact/object; hash and revalidate manifest/signatures; run non-destructive recovery/readback tests against disposable copies; test missing/truncated/corrupt inputs | Owner confirms readback of any claimed VPS-held copy only if the approved collector cannot produce verifiable machine evidence. No restore-overwrite or canonical DB operation | Disposable recovery tests are not owner custody recovery. Report each source/copy independently |
| L4M-06 — trust lifecycle | Validate versioned trust policy, signer fingerprints, approval records, rotation/revocation test vectors, policy rollback and unknown-state handling; separate cryptographic validity/current trust/historical trust-at-time | Owner approves actual trust-root/key changes and supplies missing authorization lineage; no actual key or trust mutation is performed by this plan | Unknown time/revocation evidence remains UNKNOWN. Synthetic lifecycle tests are only implementation evidence |
| L4M-07 — tamper-evident history | Build canonical event inventory; verify digest links, append-only sequence, duplicate/retry/overwrite/deletion/wholesale-replacement detection; compare history to retained manifest in approved VPS/GitHub custody; test against disposable copies | Owner identifies the designated retained history/manifest copy only where the record does not establish that designation | Claim only tamper-evident, never WORM/absolute immutability without separate evidence |
| L4M-08 — claim discipline | Automatically scan reports/matrix/handoff for unsupported PASS, operational/runtime/independent/WORM/freshness claims; compare claims with exact evidence classes and artifact expiries; generate exceptions list | Owner resolves policy choices and accepts residual limitations; no manual rechecking of mechanically verifiable references | Documentary PASS remains limited to the exact frozen package and claim set |
| L4M-10 — owner acceptance | Generate frozen input inventory, canonical SHA-256 manifest, lineage manifest, nine-control status summary and owner-disposition template; reject self-referential or mismatched baseline hashes | Owner supplies the final identity/role/conflict disclosure and explicit disposition tied to exact baseline digest | AI/CI may prepare the acceptance package but must never issue owner acceptance or mark L4M-10 PASS on the owner's behalf |

## 3. Proposed GitHub Actions architecture

Implement as a separate, path-scoped L4 validation workflow on the existing active branch after source/contract review.

1. **L4 contract and lineage gate** — validate matrix/register versions, decision references, evidence references, required controls and allowed status vocabulary. Fail on stale SHA references, duplicate IDs, missing mandatory controls or contradictions.
2. **L4 package inventory gate** — consume only explicitly selected GitHub evidence artifacts/files; download exact bytes; build inventory and SHA-256 manifest; verify every digest and record artifact ID, source run, source SHA and expiry. Never silently substitute a newer artifact.
3. **L4 cryptographic gate** — verify exact signed objects and pinned trust inputs; run mutation/replay/substitution negative tests. No key generation or signing.
4. **L4 offline gate** — run a network-disabled verifier job on the exact package and pinned trust snapshot. Record CI offline verification separately from owner offline verification.
5. **L4 readback/recovery gate** — verify exact GitHub readback and disposable-copy recovery. A VPS read-only collector may be considered separately only after its access contract, command allowlist, token source and output sanitization are reviewed and explicitly approved.
6. **L4 history/tamper gate** — validate canonical event linkage and detect mutation/replacement against the retained manifest.
7. **L4 claim-discipline gate** — cross-check evidence classes, claims, expiry and statuses; produce a deterministic exceptions report.
8. **L4 aggregate report** — produce per-control subcheck results and aggregate BLOCKED unless all active control requirements pass. Never allow CI success to override owner-only assertions.

### Workflow security and isolation

- GitHub-hosted disposable runners only for the CI stages.
- Least privilege: `contents: read` unless a narrowly justified artifact read requires another read-only permission.
- Checkout exact source SHA; record it in every report.
- No VPS SSH, no secrets, no production database, no exchange API credentials, no T1, no PostgreSQL, no networked signer/TSA/OCSP operation.
- Offline job must explicitly disable network access and prove the condition; if network isolation cannot be established, mark NOT VERIFIED rather than calling it offline.
- No upload of private keys, bearer tokens, credentials or sensitive owner identifiers.
- Artifact outputs are evidence, not automatic owner acceptance. Record retention expiry and exact digest.
- Fail closed on missing inputs, ambiguous identity, expired or unknown trust, malformed evidence, digest mismatch or stale lineage.

## 4. Required output contract

Every run must produce:
- exact branch, event, source SHA and workflow run URL;
- matrix/register/decision blob SHAs used;
- per-control automated subchecks with PASS / BLOCKED / NOT VERIFIED;
- exact input object identities, sizes and SHA-256 digests;
- artifact IDs, names, source run IDs and expiry;
- verifier version/source SHA and trust-policy fingerprint;
- negative-test outcomes;
- owner-only assertions still outstanding;
- aggregate disposition and explicit non-claims.

A successful workflow means only that its declared automated subchecks passed. It does not mean L4-Minimum is accepted, T0 runtime is healthy, data is truthful/complete, the owner controls a key, or any trading operation is safe.

## 5. Implementation sequence

1. Reconcile stale matrix/register/decision SHA references without rewriting historical records.
2. Add workflow contract tests first; prove stale references fail and current references pass.
3. Implement GitHub-side artifact inventory/readback and manifest verification.
4. Add exact-object cryptographic and adversarial verification using existing test fixtures and pinned trust inputs.
5. Add network-disabled offline verification and clearly separated owner offline status.
6. Add non-destructive disposable readback/recovery and tamper-history checks.
7. Add claim-discipline scan and deterministic aggregate report.
8. Run GitHub Actions on exact source SHA; archive artifacts and update handoff with run/job/artifact IDs and digests.
9. Only after all active controls are satisfied, prepare (not sign) the L4M-10 owner acceptance package.

Each implementation increment must be reviewed and tested before proceeding. Do not combine all gates into one unreviewable change.

## 6. Explicitly prohibited by this plan

- No T0 canonical SQLite read/write, schema change, migration, restore, vacuum or compaction.
- No Feeder/API restart, service installation, deployment or runtime configuration change.
- No SSH access expansion, forced-command change, SCP/rsync, probe installation or VPS command dispatch.
- No signer/key generation, import/export, rotation, revocation or signing operation.
- No trust-root mutation or external provider call.
- No artifact deletion, expiry change, cleanup, archive mutation or retention-policy change.
- No T1 activation, PostgreSQL canonical switch, live trading or real order.
- No L4-Extended work until L4-Minimum is frozen and accepted.

## 7. Current disposition

- Approval to automate: **APPROVED**.
- Documentation/design plan: **RECORDED**.
- L4 workflow implementation: **LINEAGE CONTRACT GATE PASS (12/12); FOUR-ARTIFACT GITHUB INVENTORY/READBACK + SHA-256 MANIFEST PILOT PASS (19/19 CONTRACT TESTS)**.
- GitHub-side artifact inventory/readback: **PARTIAL PASS — 4 explicitly allowlisted artifacts, 57 member digests; not a complete L4 evidence package**.
- VPS-side custody/readback: **NOT VERIFIED**.
- Owner signer/custody assertions: **PENDING EVIDENCE**.
- L4-Minimum aggregate: **BLOCKED / NOT VERIFIED**.
- L4M-09: **OWNER-WAIVED**.
- Option C — No Destructive Authority: **ACTIVE**.


### Latest inventory increment — 2026-11-10

- Commit `5c9941112f24edb213c129a5962187461d8f4308` added the latest verified lineage artifact (run `42836094887`, artifact `13774031418`) to the explicit allowlist; resulting allowlist blob `d481ca0baaca9605cfda1e3ebb79e423b17ac876`.
- Run `42837579509`: lineage 12/12 PASS; artifact manifest 19/19 PASS; four exact source artifacts and 57 member digests in the manifest.
- Output manifest artifact `13774501896` (3,038 bytes), ZIP SHA-256 `6f121108e6e3f98b84327251bbc965c9d6a9a849f40b2bba6d6efb8b4eff88ba`; downloaded and independently re-hashed. Manifest JSON SHA-256 `25b0db3de3fadd9504d030310b4c2243e18cdf4601bd88d2f41c2d1bf86ab07a` matches its sidecar.
- New source lineage artifact `13774031418` ZIP SHA-256 `801bbc22e1979b3e5260371a22db305d37ddd2bc6837aae3c00c99d60595abcf`; independently re-hashed with all four member hashes matched. Current run's own lineage output artifact `13772649665` was also independently re-hashed (SHA-256 `9c4c7fabdf076abb1f719d32e28edf47b2bfaec91fa5528531d178c91a51bfc4`).
- Next implementation gap: collector inventories Actions artifacts only. Build a separate exact-path/ref GitHub repository-file inventory for the current matrix, decisions, historical audits and lifecycle evidence; bind each object to Git path, commit/ref, Git blob SHA and SHA-256 of retrieved bytes. Do not infer completeness from the four-artifact pilot. Keep signature and offline gates downstream.


### Repository-file inventory scope review — 2026-11-11

- Initial repository-file inventory run [42912784110](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42912784110), source SHA `57898ea1dd0d812f2aa39575b90d957cbbb6d2d9`: repository-file job 10/10 PASS; 27 files; total source bytes 300,623. Output artifact ID `13808276963`, size 3,271 bytes, expiry `2026-11-17T22:15:02Z`, GitHub digest and independently recomputed ZIP SHA-256 `b9635c842ca3df2c1f8e19d7f4403e6c01c5be94db91092cf68747e877d78f59`; JSON SHA-256 `9133738d21c8c09492059182fe9c09cb817f853683e2d234d94721afc29b9d96` matches sidecar.
- Review of the included historical non-substitution assessment identified five additional direct source objects omitted from the first-pass list: `T0_L4M01_L4M03_EXISTING_TRUST_EVIDENCE_NON_SUBSTITUTION_2026-11-10.md`, the cited P1.8.14 external trust-anchor record, T0 checkpoint contract v1, G3 review-input manifest, and owner evidence intake contract. Their exact blob SHAs were fetched at the same source commit and are now included in the 32-file scope.
- Workflow triggers now cover those exact paths and the handoff file no longer triggers this workflow by itself; handoff-only evidence updates must not create redundant validation runs.
- Current source-object inventory remains a bounded, explicit list, not a claim that every L4-related repository object has been discovered. Preserve historical documents unchanged.


### 32-file exact-commit repository inventory — verified

- Workflow run [42913380578](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42913380578), source SHA `7d6cbb10f903625f2051db7d5322e0648ae7727d`, overall SUCCESS. Lineage job `130169487545` SUCCESS; repository-file inventory job `130169556821` SUCCESS (10/10 tests); artifact-manifest job `130169556932` SUCCESS (19/19 tests). Lineage test count remains 12/12; total workflow contract tests 41/41.
- Repository-file inventory artifact ID `13807208514`, name `t0-l4-repository-file-inventory-42913380578`, 3,750 bytes, expires `2026-11-17T22:18:48Z`; uploaded digest and independently recomputed ZIP SHA-256 `f77ed0a0480134e5f7d9f386e900acc6547177033130b35ff0e1ab6cfd5cc3f6`.
- Manifest JSON SHA-256 `67876c21dd8639892362c426a377533d9fdd093b4f9a3e0b1adc082ccfb7180d` matches the included SHA-256 sidecar. ZIP contains exactly two regular files: JSON manifest and sidecar.
- Manifest source commit `7d6cbb10f903625f2051db7d5322e0648ae7727d`, branch `feature/t0-centralized-data-feeder-p1-20261101`, file count 32, total source size 399,691 bytes, 32 unique paths. Each entry includes exact path, Git blob SHA-1, byte size and SHA-256.
- The inventory job uses the exact checked-out Git object database, not network/API retrieval. It rejects missing/ambiguous paths, wrong object type/mode, stale blob SHA, wrong commit/branch, unsafe/duplicate paths, oversized individual files and oversized aggregate content. No token, secret, VPS or canonical database is used.
- Predecessor inventory run `42913229506` failed closed because the Automation Plan blob changed in the same commit but the inventory config still expected its previous blob SHA. The config was rebound to current Plan blob `8413befc9a1d7acaaa935e3d21a9993dc2d26484`; retry run `42913380578` passed. The failed run remains visible.
- Aggregate L4-Minimum remains BLOCKED / NOT VERIFIED. The 32-file inventory is a bounded source-object set; it does not prove completeness of all L4 evidence, VPS custody, owner signer separation, offline verification, or final owner disposition. No control is promoted by this CI result.


### 36-file repository inventory and reference reconciliation — verified

- Run [42914049188](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42914049188), source SHA `b2abc8e8014b5ae0c48f7c67736712bf1a7cd9db`, overall SUCCESS. Lineage job `130171747981`: 12/12 PASS. Repository-file inventory job `130171829416`: 10/10 PASS. Artifact manifest job `130171829353`: 19/19 PASS. Total 41/41 contract tests PASS.
- Inventory artifact `13806969533`, name `t0-l4-repository-file-inventory-42914049188`, 4,100 bytes, expiry `2026-11-17T22:23:03Z`; upload digest and independently recomputed ZIP SHA-256 `0b7b5588330d4070e13db361ff28931b86e4a08584b7ba9e65f2e1bb1fe6fb5a`.
- JSON SHA-256 `12ffa072f340ec421274dd062e901951969df29a36f24b307862f6fef4ed1b60` matches the included sidecar. Manifest binds source commit `b2abc8e8014b5ae0c48f7c67736712bf1a7cd9db`, 36 unique paths and 453,535 source bytes.
- Added source objects: `T0_COMPONENTS_OUTSIDE_L4_MINIMUM_AUDIT_2026-11-10.md` (historical L4 scope classification), `P1.8.142-owner-retention-and-data-class-disposition-decision-package.md` (predecessor lifecycle package), `COMMERCIAL_SCOPE_CONTENT_AUDIT_2026-11-09.md` (supporting personal/non-commercial scope audit), and the scope reconciliation report `T0_L4_REPOSITORY_FILE_INVENTORY_SCOPE_RECONCILIATION_2026-11-11.md`.
- Reference reconciliation is **PARTIAL PASS**: direct references in the scanned current matrix/register/plan/decisions/historical review/lifecycle documents were classified. Handoff, T0 deployment/API/DR architecture and T1/T2 runtime records were excluded as process or separate engineering/layer evidence, with exact paths/blob SHAs recorded in the reconciliation report. Three additional material L4 scope/lifecycle records were included.
- The historical T0 components-outside-L4 audit contains basename-only source citations that have not been resolved to exact repository paths. They are not guessed or added. If a later L4 claim relies on one, resolve the exact path/blob before inclusion. This and the bounded nature of the scan prevent a claim of complete repository-wide evidence discovery.
- The reconciliation report is documentary and does not rewrite any historical source. It explicitly preserves old matrix references as historical and distinguishes out-of-scope T0/T1/T2 documents from L4 evidence.
- Aggregate L4-Minimum remains BLOCKED / NOT VERIFIED; no control is promoted by the 36-file CI result. VPS custody, signer separation, authenticated freshness anchor, offline verification, readback/recovery, trust lifecycle, tamper-evident history and L4M-10 owner disposition remain unproven as previously recorded.


### Historical source-reference resolution — 2026-11-11

- Resolved the exact paths/blob SHAs for basename-only citations in the historical T0 components-outside-L4 audit at source tree `da0dc7bce6d3130a718a7ff7a504d8b4c06451cb`.
- Added to the inventory: `T0_TSA_WORM_READ_ONLY_AUDIT_2026-11-10.md`, `P1.8.80-retention-and-eligibility-policy.md`, `P1.8.121-owner-decision-ratification-option-c-no-destructive-authority.md`, and `P1.8.141-holistic-data-lifecycle-design-closure-assessment.md`.
- Resolved but excluded as separate T0 architecture/backend/lifecycle background: shared data foundation, PostgreSQL role/writer decisions, and generic consumer/deletion/copy-lifecycle contracts. Exact paths and blob SHAs are recorded in the scope reconciliation report.
- The 40-file inventory remains a bounded L4 source set, not repository-wide completeness proof. Reference reconciliation remains PARTIAL PASS.
