# T0 L4-Minimum — Control-to-Source Crosswalk

Date: 2026-11-11  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Validated source baseline: `0251a8cc7995903d2516fc84cc0a33b73ec02777`  
Matrix blob: `75db0d98134fd656d91a8545bc307c56595aebf7`  
Evidence Register blob: `e67a58591b5f6168ab3a0f3f403557292aca45d5`  
Status: **DERIVED CROSSWALK ONLY — NO CONTROL ACCEPTANCE — AGGREGATE BLOCKED**

## Rules

- The 40-file inventory proves exact identity of the listed Git objects at its source commit only.
- The six-item Actions allowlist is a separate evidence class. The repository inventory artifact is an output, not one of those four source artifacts.
- Design documents, synthetic tests, CI artifacts, owner-supplied evidence and VPS/runtime evidence are not interchangeable.
- Active denominator: L4M-01–08 and L4M-10. L4M-09 is OWNER-WAIVED / NOT MANDATORY.

## Control crosswalk

| Control | Current exact source objects | Existing CI/Actions evidence | Missing evidence / disposition |
|---|---|---|---|
| **L4M-01 Owner custody** | `T0_L4M01_L4M03_EXISTING_TRUST_EVIDENCE_NON_SUBSTITUTION_2026-11-10.md` blob `1fea06d455e020fb3e87d7378c8f95bb127f9c4b`; `T0_L4M01_L4M03_OWNER_EVIDENCE_INTAKE_CONTRACT_2026-11-10.md` blob `914fb398bf6f0e4ef26ae6b706212c5f2969d1c1`; current matrix/register | Six allowlisted Actions sources: IDs `13546255148`, `13545287609`, `13771662067`, `13774031418`, `13810855669`, `13810187202`; latest repository inventory output `13811119271` | No complete owner-controlled package, authenticated latest-head anchor, copy designation/control proof or per-copy owner readback. **PARTIAL** |
| **L4M-02 Signer separation** | `T0_L4M02_SIGNER_SEPARATION_EXISTING_EVIDENCE_ASSESSMENT_2026-11-10.md` blob `acea504de4608520c59b1870fe6cb7241492830e`; waiver decision blob `75e057ba482d81f6a9d896ace2b017807c9396d9` | Synthetic ephemeral-key tests only | No owner signer identity/fingerprint, custody/recovery proof or runtime/admin signing separation. **NOT VERIFIED** |
| **L4M-03 Exact binding/freshness** | Non-substitution assessment above; `T0_EVIDENCE_OBJECT_CHECKPOINT_CONTRACT_V1.md` blob `0d98a3dcbb0d403b213b5efcae0c882ac5461578`; lineage evidence blob `6cc2a2abb766948d2cd1d05e668a52a2a90484f1` | P1.8.14 synthetic evidence and independent-runner artifacts; lineage contract | No signed canonical T0 checkpoint, authenticated latest-head anchor or rollback result against anchor. **PARTIAL — SYNTHETIC/DESIGN ONLY** |
| **L4M-04 Offline verification** | Checkpoint contract; P1.8.14 verification records; matrix | Synthetic verifier and GitHub-hosted CI | No owner-run verification of exact retained T0 package with T0/VPS, GitHub, ChatGPT and network unavailable; no owner environment output/trust snapshot. **PARTIAL — SYNTHETIC/CI ONLY** |
| **L4M-05 Readback/recovery** | Read-only audit blob `cfecb7428508adf23e6b9e71dc0dfe1e0e38080c`; 40-file inventory config/report | Repository inventory artifact `13811119271`; six Actions sources; synthetic SQLite crash/reopen model | No owner-copy readback/revalidation or observed non-destructive recovery from retained package. **PARTIAL — SYNTHETIC MODEL ONLY** |
| **L4M-06 Key/trust lifecycle** | `CENTRAL_DATA_LIFECYCLE_POLICY.md` blob `9fd46c029cff643ccc35492fd09620581f6eff35`; P1.8.143 blob `6f4451f1eb193e763970581bcd6d8a782508acfd`; P1.8.144 blob `f3002ba709f874936ca434c883ef855d2f11784a`; P1.8.152 blob `e1a4d95af216e94a58fa5528850fcd0c1ff465f8`; lifecycle waiver blob `555951e36f6365012cb5b9e48ba24e455b775d16` | Synthetic trust snapshots and rotation/revocation/unknown-state tests | No owner-approved actual trust policy, actual key/trust fingerprints, approval lineage or rotation/revocation evidence. **PARTIAL — SYNTHETIC POLICY ONLY** |
| **L4M-07 Tamper-evident history** | T0 components-outside-L4 audit blob `7bfc509b9eb918750b3a25acc18f8d4f989d387f`; TSA/WORM audit blob `4a7b872656ec240ddd6862f7ed6d92ca6c26fcee`; P1.8.143/144/152 | Git history, four Actions sources, 40-file inventory | No independently retained manifest/copy or demonstrated wholesale-replacement detection; no WORM/immutability claim. **PARTIAL — SYNTHETIC MODEL ONLY** |
| **L4M-08 Claim discipline** | Claim discipline assessment blob `603ca1f1cb5fe8988f17fd866942d06c15a213b7`; adversarial review blob `a7aec29330d71cb4d34193d6db81b8e20eb295f1`; read-only audit and matrix | Lineage, artifact manifest and repository inventory CI | Documentary bounds exist; no frozen-package revalidation. **DOCUMENTARY PASS ONLY** |
| **L4M-09 Independent reviewer** | Owner waiver decision blob `75e057ba482d81f6a9d896ace2b017807c9396d9` | Not required | **OWNER-WAIVED / NOT MANDATORY**; integrity/custody controls remain mandatory |
| **L4M-10 Owner aggregate acceptance** | Readiness assessment blob `7b5653815222ed499b2d6dc57dc1238137d26aff`; current matrix/register/plan | 40-file inventory and lineage/manifest CI | No frozen baseline ID/digest, nine active-control dispositions, assessor identity/role/conflict disclosure or separate owner acceptance tied to exact digest. **NOT VERIFIED / PENDING OWNER ASSESSMENT** |

## Latest CI evidence

Run [42922670634](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42922670634), exact source SHA `0251a8cc7995903d2516fc84cc0a33b73ec02777`:
- Lineage: 12/12 PASS.
- Artifact manifest: 19/19 PASS.
- Repository-file inventory: 10/10 PASS.
- Total: 41/41 tests PASS; all three jobs SUCCESS.
- Six-item source allowlist blob: `0280cd7751c9660baec237242ca7aadef09205a6`; two P1.8.14 synthetic artifacts plus four L4 lineage CI artifacts.
- Newly selected lineage artifact `13810187202`, run `42917935285`, source SHA `cab8122c94e8bb8f30052ae44483fb1ec7e4de65`, ZIP SHA-256 `db4e86e8b976304ae1daf90b14dc49cd2f4b149c9c2449867d796b515cd76d07`; exact four-member payload independently verified.
- Current run manifest artifact `13813280057`: ZIP SHA-256 `cc969116e687792321240e19cfa2125abfb8a884328e03715937746709b9b26d`; JSON SHA-256 `520fd49f87595cd39b412a0533ce579c8ead1456ad0361a712b52786bebad428` matches sidecar; exactly six source artifacts and no self-inclusion.
- Current run repository inventory artifact `13811119271`: ZIP SHA-256 `ab8944fe9edb3446a50df1b8041743e93bb6bb628dee70956913c54b862222da`; JSON sidecar matches; 40 unique files, 518,716 source bytes, exact source commit `0251a8cc7995903d2516fc84cc0a33b73ec02777`.
- Current run lineage output artifact `13813120888`: ZIP SHA-256 `4686edd0c1e80f4a5793aa8d79ac4ce232ee64bd59cee2bfa633c14afd3d29d1`; exact source marker, 12 tests and PASS verdict.
- All three current-run output ZIPs were independently downloaded and re-hashed. These are generated outputs, not new source evidence.

## Aggregate disposition

The CI result proves exact identity of explicitly allowlisted repository files and the declared synthetic/lineage artifact contracts. It does not prove owner custody, signer separation, signed latest-head freshness, owner-offline verification, owner-copy recovery, actual key/trust lifecycle or tamper-evident retained history.

Aggregate L4-Minimum remains **BLOCKED / NOT VERIFIED**. No control is promoted by file presence, test success, Git history or GitHub upload digest.

Next: reconcile any additional eligible Actions artifacts against exact run/artifact/source SHA/expiry and verify source artifact bytes. Only after the evidence inventories are stable should exact-object signature/negative-verification design begin. No key generation/signing, VPS/SQLite access, trust-root change, cleanup, expiry, artifact deletion or destructive lifecycle action. Option C remains ACTIVE.


## Latest allowlist reconciliation

The six-item allowlist and current six-entry manifest are reconciled to the exact source SHA `0251a8cc7995903d2516fc84cc0a33b73ec02777`. Candidate selection rationale and limitations are recorded in `T0_L4_LINEAGE_CANDIDATE_REVIEW_2026-11-11.md`. This derived crosswalk does not promote any control; aggregate L4-Minimum remains BLOCKED / NOT VERIFIED.
