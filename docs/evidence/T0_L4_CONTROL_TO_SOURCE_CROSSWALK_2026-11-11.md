# T0 L4-Minimum — Control-to-Source Crosswalk

Date: 2026-11-11  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Validated source baseline: `2e66102ced45e7a59d8885026a29fa5e38dab01e`  
Matrix blob: `7c413504db397877b308345b21c9f6f58271c89a`  
Evidence Register blob: `7ee8b11b47bec4bbd983f35e8f4a4d0f012c03bc`  
Status: **DERIVED CROSSWALK ONLY — NO CONTROL ACCEPTANCE — AGGREGATE BLOCKED**

## Rules

- The 40-file inventory proves exact identity of the listed Git objects at its source commit only.
- The six-item Actions allowlist is a separate evidence class. The repository inventory artifact is an output, not one of those four source artifacts.
- Design documents, synthetic tests, CI artifacts, owner-supplied evidence and VPS/runtime evidence are not interchangeable.
- Active denominator: L4M-01–08 and L4M-10. L4M-09 is OWNER-WAIVED / NOT MANDATORY.

## Control crosswalk

| Control | Current exact source objects | Existing CI/Actions evidence | Missing evidence / disposition |
|---|---|---|---|
| **L4M-01 Owner custody** | `T0_L4M01_L4M03_EXISTING_TRUST_EVIDENCE_NON_SUBSTITUTION_2026-11-10.md` blob `f64ebddfc5ee06d69835b433da530efa000ad64f`; `T0_L4M01_L4M03_OWNER_EVIDENCE_INTAKE_CONTRACT_2026-11-10.md` blob `d42204b82ac397b57c8d1fe4cee2e500f79510a7`; current matrix/register | Six allowlisted Actions sources: IDs `13546255148`, `13545287609`, `13771662067`, `13774031418`, `13810855669`, `13810187202`; latest repository inventory output `13818139442` | No complete owner-controlled package, authenticated latest-head anchor, copy designation/control proof or per-copy owner readback. **PARTIAL** |
| **L4M-02 Signer separation** | `T0_L4M02_SIGNER_SEPARATION_EXISTING_EVIDENCE_ASSESSMENT_2026-11-10.md` blob `87de3761a51dcfd7f53cab765fbd1bcfce5ee8d0`; waiver decision blob `f3c91ae225d2c225b8ee7ac5073b607436b190f5` | Synthetic ephemeral-key tests only | No owner signer identity/fingerprint, custody/recovery proof or runtime/admin signing separation. **NOT VERIFIED** |
| **L4M-03 Exact binding/freshness** | Non-substitution assessment above; current amended `T0_EVIDENCE_OBJECT_CHECKPOINT_CONTRACT_V1.md` blob `a6825270d59bde274bfe765d5f942144b66a84de`; current `T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A1_2026-11-11.md` blob `00fdad293e129562145ab930507a4e6b9c2bf23d`; lineage evidence blob `46824bcbd04519c0c9d699c26660995b05c6acc5` | P1.8.14 synthetic evidence and independent-runner artifacts; signature/negative-verification contract only (not implemented) | No signed canonical T0 checkpoint, authenticated latest-head anchor, per-location owner readback or runtime rollback test. **PARTIAL — DESIGN ONLY / NOT IMPLEMENTED** |
| **L4M-04 Offline verification** | Checkpoint contract; P1.8.14 verification records; matrix | Synthetic verifier and GitHub-hosted CI | No owner-run verification of exact retained T0 package with T0/VPS, GitHub, ChatGPT and network unavailable; no owner environment output/trust snapshot. **PARTIAL — SYNTHETIC/CI ONLY** |
| **L4M-05 Readback/recovery** | Read-only audit blob `d402199bcc299b3c81fb60a2c498cecf3a46543c`; 40-file inventory config/report | Repository inventory artifact `13818139442`; six Actions sources; synthetic SQLite crash/reopen model | No owner-copy readback/revalidation or observed non-destructive recovery from retained package. **PARTIAL — SYNTHETIC MODEL ONLY** |
| **L4M-06 Key/trust lifecycle** | `CENTRAL_DATA_LIFECYCLE_POLICY.md` blob `9fd46c029cff643ccc35492fd09620581f6eff35`; P1.8.143 blob `4e10c73571fe479d8f66138db8c7aa81153109b5`; P1.8.144 blob `3dfeeb82af4d75e9fcd8438a33878a570a55014f`; P1.8.152 blob `e05d0cfc02f985dc5045f504a0e81f2c30f5c7dd`; lifecycle waiver blob `2c8038ef0a00b1190f1a842011b1f1ce4c5ecb2b` | Synthetic trust snapshots and rotation/revocation/unknown-state tests | No owner-approved actual trust policy, actual key/trust fingerprints, approval lineage or rotation/revocation evidence. **PARTIAL — SYNTHETIC POLICY ONLY** |
| **L4M-07 Tamper-evident history** | T0 components-outside-L4 audit blob `b898b9fead6583b7cc0cde30bf7bd8b3acc2c1b0`; TSA/WORM audit blob `286ca18ad6cb961bb2762f2e298953eb9e8cf5ee`; P1.8.143/144/152 | Git history, four Actions sources, 40-file inventory | No independently retained manifest/copy or demonstrated wholesale-replacement detection; no WORM/immutability claim. **PARTIAL — SYNTHETIC MODEL ONLY** |
| **L4M-08 Claim discipline** | Claim discipline assessment blob `1f52eba475dd90216a2f9f3b0bad3d36fc233af2`; adversarial review blob `ecb58858b470fff841256fcf306d4e5454402486`; read-only audit and matrix | Lineage, artifact manifest and repository inventory CI | Documentary bounds exist; no frozen-package revalidation. **DOCUMENTARY PASS ONLY** |
| **L4M-09 Independent reviewer** | Owner waiver decision blob `f3c91ae225d2c225b8ee7ac5073b607436b190f5` | Not required | **OWNER-WAIVED / NOT MANDATORY**; integrity/custody controls remain mandatory |
| **L4M-10 Owner aggregate acceptance** | Readiness assessment blob `e8ef1cf40e64cc5a0200f71c506eddb6c63d0faf`; current matrix/register/plan | 40-file inventory and lineage/manifest CI | No frozen baseline ID/digest, nine active-control dispositions, assessor identity/role/conflict disclosure or separate owner acceptance tied to exact digest. **NOT VERIFIED / PENDING OWNER ASSESSMENT** |

## Latest CI evidence

Run [42936903511](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42936903511), exact source SHA `2e66102ced45e7a59d8885026a29fa5e38dab01e`:
- Lineage contract: 12/12 PASS.
- Artifact manifest: 19/19 PASS; collector verdict `L4_ARTIFACT_MANIFEST=PASS`.
- Repository-file inventory: 10/10 PASS; verdict `L4_REPOSITORY_FILE_INVENTORY=PASS`.
- Total: 41/41 tests PASS; all three jobs SUCCESS.
- Six-item source allowlist blob: `0280cd7751c9660baec237242ca7aadef09205a6`; two P1.8.14 synthetic artifacts and four L4 lineage CI artifacts.
- Current inventory config blob: `88835e2763f7053b2f41b2115cdd1b93e56cd255`; 40 source paths.
- Current-run lineage artifact `13818891470`: 1,151 bytes; ZIP SHA-256 `a56b20af26c134e1d767ac2503dcd03c1fecfbaa7bab334edd0da55bffe2d531`; exact source marker `2e66102ced45e7a59d8885026a29fa5e38dab01e`; scope GitHub-hosted read-only; 12 tests; PASS.
- Current-run manifest artifact `13818887032`: 3,268 bytes; ZIP SHA-256 `69e55931705e387f60d8acd4093a713f00ba41b76256a4355674608be50ec6e9`; JSON member 12,001 bytes, SHA-256 `f8954b20d2ce7c05318fcb220a07286c59f1119cfbdbfb6a60a6f7aaca7c95cf`, sidecar matches; exactly six source artifacts and no self-inclusion.
- Current-run repository inventory artifact `13818139442`: 4,482 bytes; ZIP SHA-256 `90866af79fc34e5eced9f552a4c178b211ca4490279ea472aa61fdb15c2e4dcb`; JSON member 9,757 bytes, SHA-256 `5780dafa00ff6f7781ffa7dccd7f577901b71ef325845072d37c8931c5e21397`, sidecar matches; 40 unique paths / 559,566 bytes; exact source commit `2e66102ced45e7a59d8885026a29fa5e38dab01e`.
- All three current-run output ZIPs were downloaded and independently re-hashed. These are generated outputs, not new source evidence.

## Aggregate disposition

The CI result proves exact identity of explicitly allowlisted repository files and the declared synthetic/lineage artifact contracts. It does not prove owner custody, signer separation, signed latest-head freshness, owner-offline verification, owner-copy recovery, actual key/trust lifecycle or tamper-evident retained history.

Aggregate L4-Minimum remains **BLOCKED / NOT VERIFIED**. No control is promoted by file presence, test success, Git history or GitHub upload digest.

Next: reconcile any additional eligible Actions artifacts against exact run/artifact/source SHA/expiry and verify source artifact bytes. Only after the evidence inventories are stable should exact-object signature/negative-verification design begin. No key generation/signing, VPS/SQLite access, trust-root change, cleanup, expiry, artifact deletion or destructive lifecycle action. Option C was REVOKED by owner decision on 2026-11-11; see the owner governance update below.


## Latest allowlist reconciliation

The six-item allowlist and current six-entry manifest are reconciled to the exact source SHA `0251a8cc7995903d2516fc84cc0a33b73ec02777`. Candidate selection rationale and limitations are recorded in `T0_L4_LINEAGE_CANDIDATE_REVIEW_2026-11-11.md`. This derived crosswalk does not promote any control; aggregate L4-Minimum remains BLOCKED / NOT VERIFIED.


## Latest allowlist and repository-source reconciliation

The six-entry source allowlist and six-entry artifact manifest are validated on the current evidence-document source baseline. The exact-commit repository inventory has been rebound to the refreshed register, automation plan and supporting assessments; the latest 40-file inventory is from source SHA `2e66102ced45e7a59d8885026a29fa5e38dab01e`. Candidate selection rationale and payload verification are recorded in `T0_L4_LINEAGE_CANDIDATE_REVIEW_2026-11-11.md`. This derived crosswalk does not promote any control; aggregate L4-Minimum remains BLOCKED / NOT VERIFIED.


## Owner governance update — Option C revoked (2026-11-11)

The owner explicitly revoked **Option C — No Destructive Authority** on 2026-11-11. Its former ACTIVE status in this document is historical and is superseded by this decision. Option C is now **REVOKED**; do not apply it as a blanket prohibition.

This governance revocation is not a blanket instruction to execute deletion or cleanup. Any specific destructive operation still requires a separately scoped plan identifying exact target/data class, operation, retention/impact, preconditions, verification, recovery/rollback and explicit approval. T0 canonical data, lease/fencing state, ledgers, audit/reconstruction/recovery evidence and owner custody records remain protected unless an exact operation is separately approved. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged. Revocation does not promote any L4 control or establish custody/signature/offline-verification assurance.


## Current governance state — Option C revoked

Owner decision dated 2026-11-11: **Option C — No Destructive Authority is REVOKED**. Historical ACTIVE/in-force statements in earlier source records are superseded by dated addenda. Revocation removes the blanket prohibition but is not authorization for any specific destructive action. Each deletion/archive/cleanup/expiry/vacuum/compaction/provider action still requires separate explicit approval and a bounded target, impact, preconditions, verification and recovery plan. T0 canonical data, lease/fencing, ledgers, audit/recovery and custody/trust evidence remain protected unless specifically approved. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.


## Owner decision — bounded VPS + GitHub custody accepted (2026-11-11)

The owner approved the formal amendment to Checkpoint Contract v1 §§7/9. The bounded custody scope for this system is the designated VPS location plus the designated GitHub evidence location. This supersedes the former outside-both-VPS-and-GitHub location requirement only for the bounded claims described in the amended contract.

**Assurance limitation:** This arrangement does not provide an independent custody domain outside VPS and GitHub. A joint rollback/replacement of both locations to the same older valid chain is not detectable by this design. Permitted wording is limited to exact two-location consistency with the authenticated retained anchor chain available to the verifier; do not claim globally latest, absolute anti-rollback, WORM, external custody or independent external assurance.

The amendment does not promote L4M-01, L4M-03, L4M-04, L4M-05 or L4M-07. Actual owner custody, signer/anchor separation, per-location receipts/readback, authenticated trust bootstrap, signed anchor-chain verification and offline verification remain evidence gates. Aggregate L4-Minimum remains **BLOCKED / NOT VERIFIED** until those controls are independently evidenced and the owner performs the separate final disposition.

Source: T0_EVIDENCE_OBJECT_CHECKPOINT_CONTRACT_V1.md dated owner-approved addendum; T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A1_2026-11-11.md §14 and owner-disposition addendum.

No implementation, key generation/signing, trust-root mutation, anchor creation, provider operation, VPS/SQLite/runtime action or T0 canonical data change is authorized by this decision.


## Signature / negative-verification design status — final consistency correction (2026-11-11)

### Bounded-custody readback clarification

The owner-approved amendment supersedes the former requirement to demonstrate recovery/readback while both approved locations are simultaneously unavailable. The two permitted outage-isolation tests are VPS-copy readback while GitHub is unavailable and GitHub-copy readback while VPS is unavailable. No third-domain recovery or both-unavailable availability claim is made. A verifier requiring exact two-copy agreement MUST fail closed if either required copy is currently inaccessible.


- Current contract source: T0_EVIDENCE_OBJECT_CHECKPOINT_CONTRACT_V1.md; current A1 source: T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A1_2026-11-11.md. Exact blobs are recorded in the session handoff after commit.
- Owner custody decision is propagated through the contract addendum, A1 §2.1/§11/§14 and the §13.2 G1 custody-row clarification. VPS + GitHub is the bounded two-location scope; common-mode joint rollback is not detectable. No third-domain, WORM, global latestness or absolute anti-rollback claim is permitted.
- The initial G1 A proof-of-existence product remains explicitly unsigned. A1 defines a separate signature/trust extension and does not retroactively add signer-authenticity claims to G1 A.
- Signature statement, trust policy, anchor and negative-verification cases remain contract/design only. No cryptographic implementation, keys, signatures, anchor instances, runtime readback or offline verification exist from this work.
- Aggregate L4-Minimum remains **BLOCKED / NOT VERIFIED**. L4M-09 remains OWNER-WAIVED for the general L4 baseline; the separate requested architecture review for this signature extension has not been performed by a qualifying independent reviewer.
- Next gate: freeze the exact contract/A1/test-matrix candidate for review and obtain a qualifying reviewer. Do not implement before review and separate owner implementation approval.


## GitHub artifact exact-readback increment — run 42937191664 (2026-11-11)

A separately owner-approved read-only exact-readback pass downloaded the three output artifacts from [workflow run 42937191664](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42937191664), checked ZIP integrity/member paths, and independently recomputed SHA-256 over each complete ZIP. All three computed digests matched GitHub artifact metadata and the workflow upload digest:

| Output artifact | ID | ZIP bytes | Independently verified SHA-256 | Result |
|---|---:|---:|---|---|
| `t0-l4-artifact-manifest-42937191664` | `13819680374` | 3,267 | `3509f2ce14aa174a45e4200ab44d13c7ae532841a74886256e9f6fe20ea55f71` | PASS |
| `t0-l4-minimum-lineage-42937191664` | `13818967476` | 1,150 | `155986f0f35d875fad02b6c50d0aab7aa43afdcd9191391f9ee0b832e975b67e` | PASS |
| `t0-l4-repository-file-inventory-42937191664` | `13818163804` | 4,483 | `98fc7fca7123ae0a9e72bcf1f209032a57c24d97aa898aaa075eb7212f04c0fa` | PASS |

The manifest and repository-inventory JSON payload SHA-256 values independently matched their sidecars. The repository inventory contains 40 unique paths and reconciles to 559,566 declared bytes. The lineage output binds to exact source SHA `8bda3c987e2145a636bbcc9d8609c5ea15a492b9`; workflow jobs passed 12/12 lineage, 19/19 manifest and 10/10 repository inventory tests (41/41 total).

**Classification:** these are three current-run GitHub Actions output artifacts, not additions to the six-item source-artifact allowlist and not owner custody copies. Their exact-readback is PASS for the three named artifacts only. The result strengthens GitHub-side artifact integrity/readback evidence but does not prove owner custody, VPS copy, signed canonical T0 checkpoint, authenticated latest-head anchor, freshness or recovery from GitHub unavailability.

- L4M-01 remains **PARTIAL / NOT VERIFIED**.
- L4M-03 remains **PARTIAL — SYNTHETIC/DESIGN ONLY**.
- Aggregate L4-Minimum remains **BLOCKED / NOT VERIFIED**.
- Detailed evidence report: `docs/evidence/T0_L4_GITHUB_ARTIFACT_EXACT_READBACK_2026-11-11.md`, report commit `a42a45060718d7c4bbce63f4c2756687a8231c6a`.

No VPS/SSH, T0 API/SQLite, canonical data/runtime, signing/key operation, workflow dispatch, cleanup/deletion or trading action occurred. T0 remains unchanged; paper-only and `AI_EXECUTION_ENABLED=false` remain.


## L4M-08 — Bounded claim-discipline CI verification (2026-11-12)

- Existing workflow extended with a dedicated read-only claim-discipline job; no separate workflow, secrets, network provider, T0/VPS/runtime access or production data access was added.
- Exact tested source SHA: `18dea2a9097f711466bb792d3722ad36d0a2720a`.
- Workflow run [43085172937](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43085172937): all four jobs SUCCESS. The L4M-08 job ran 11/11 focused tests PASS and the current control-to-source crosswalk audit returned `L4M08_CLAIM_DISCIPLINE=PASS`.
- Claim-discipline artifact ID `13885858302`, ZIP SHA-256 `153d9b1ec6310603b6b5e184f9039886a92a6db8e0e3d557550ec5e0235d9606`; exact artifact ZIP was downloaded and independently hashed, matching GitHub's digest. Its JSON report binds source SHA `18dea2a9097f711466bb792d3722ad36d0a2720a`, lists all ten current control dispositions, and explicitly retains aggregate `BLOCKED / NOT VERIFIED`.
- Other workflow artifacts: lineage ID `13885468780`, digest `dbaed9f7b729871444d3ef8663817f8262c9c22e228b85a2c16bd837522a36c4`; repository inventory ID `13885328510`, digest `6154d6be8c1039b1b5b956916beb533a2a3083a76f228d91331439b2fe5dd641`; artifact manifest ID `13886396112`, digest `d101885d228a04429dab44805f58f561bff7c52c26428e451c90796c90ccfbb4`.
- Scope limitation: this is a deterministic audit of the current control-to-source crosswalk only, not a repository-wide scan of every report/handoff, not owner custody evidence, not a signed checkpoint/anchor verification, not owner-run offline verification and not final L4 acceptance.
- Disposition: **L4M-08 automated crosswalk subcheck PASS; L4M-08 overall remains DOCUMENTARY PASS ONLY; L4M-01–07 and L4M-10 are not promoted; aggregate L4-Minimum remains BLOCKED / NOT VERIFIED.**


## L4M-06 / L4M-07 — Synthetic trust lifecycle and history CI verification (2026-11-12)

- Exact tested source SHA: `c24159128a6b227e2407997e16b416384a820d64`.
- Workflow run [43085631073](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43085631073): all five jobs SUCCESS, including the dedicated synthetic trust/history job and the existing lineage, artifact-manifest, repository-inventory and claim-discipline jobs.
- L4M-06 synthetic trust lifecycle: **19/19 tests PASS**. Coverage includes snapshot digest/sequence/predecessor validation, rotation detection, stale/future timestamps, offline revocation limits and retention-manifest integrity.
- L4M-07 synthetic history: **11/11 tests PASS**. Coverage includes event/checkpoint crash recovery, persisted-byte corruption detection, idempotent checkpoint ACK, append-chain predecessor/sequence checks and archive-job source ancestry guard.
- Synthetic evidence artifact ID `13885878853`, ZIP SHA-256 `08db5e871df1bf0dd452b80a12a43156169f2324910758d098535a223b9b2fe1`; downloaded exact ZIP and independently re-hashed, matching GitHub's digest. Embedded source marker matches `c24159128a6b227e2407997e16b416384a820d64`; both test logs and PASS markers were read back.
- L4M-08 remained green at the same source SHA: claim-discipline artifact ID `13886576408`, GitHub ZIP digest `eb85325845c275baa2e004da17d587562dba2fb225edd5aacc395705da82bafe`; focused crosswalk audit and 11/11 tests PASS.
- Scope limitation: these are synthetic model/CI subchecks. They do not establish actual owner key custody, current trust-root authorization, a signed canonical T0 checkpoint, authenticated latest-head anchor, real-world revocation truth, WORM/absolute immutability or owner-run offline verification.
- Disposition: **L4M-06 synthetic trust lifecycle subcheck PASS; L4M-07 synthetic history subcheck PASS. Both overall controls remain PARTIAL — SYNTHETIC ONLY. L4M-08 remains DOCUMENTARY PASS ONLY with automated crosswalk subcheck PASS. L4M-01–05 and L4M-10 are not promoted; aggregate L4-Minimum remains BLOCKED / NOT VERIFIED.**
