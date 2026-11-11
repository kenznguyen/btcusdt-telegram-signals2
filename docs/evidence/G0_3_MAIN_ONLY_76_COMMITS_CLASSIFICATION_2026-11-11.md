# G0.3 — Classification of 76 main-only commits

- Date: 2026-11-11 (Asia/Ho_Chi_Minh)
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Classification scope: commits reachable from `main` and not reachable from the active T0/T2 branch at the G0.3 inspection point.
- Active branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Active branch HEAD at inspection: `b06111235f8830676433b3a1279de65bc09b3c75`
- `main` HEAD at inspection: `063f7a2eacd724f965a9723d0ae66cf95418c0fb`
- Merge base: `f5b74affb8777953fa66d241784965fbb0e577ba`
- GitHub compare: `base=active branch`, `head=main`; status `diverged`, `ahead_by=76`, `behind_by=3019`, `total_commits=76`.
- Owner approved read-only G0.3 on 2026-11-11. No Git history or repository content was changed during the classification.

## 1. Classification summary

| Group | Commits | Interpretation |
|---|---:|---|
| SSH preflight / PR #140 | 48 | Read-only T0 preflight script, contract tests, isolated CI gate, fail-closed probe/classifier changes, review evidence and PR #140 merge closeout |
| SSH preflight / PR #144 | 17 | Encrypted-key SSH contract workflow/tests, strict fail-closed evidence classifier and sanitized diagnostics, PR #144 merge/evidence |
| P1.8 traceability history | 3 | Documentation correction/restore/revert sequence; treat as history, not a net feature to replay |
| T0 Signature A1 | 2 | Signature trust policy amendment and candidate freeze |
| T0 Signature Stage I | 2 | Isolated A2.2 Stage I workflow and unittest summary parsing fix |
| Governance documentation | 2 | Contribution/effort ledger and handoff record |
| T1 review | 1 | P1.38 second-pass review of receipt contract |
| T0/T2 parity evidence | 1 | Reconciliation of prior loopback runtime evidence |
| **Total** | **76** | |

Classification is based on the complete 76-commit compare inventory (commit SHA and subject) plus inspection of the material file contents/diffs called out below. This is a change-surface and integration-risk classification, not a claim that every commit has undergone a full independent code review.

## 2. File-level change surface

GitHub compare reports 13 paths, all added or modified on `main` relative to the merge base:

| Path | Status | Additions | Deletions |
|---|---|---:|---:|
| `.github/workflows/t0-manual-validation.yml` | modified | 249 | 0 |
| `.github/workflows/t0-signature-a2-2-stage-i.yml` | added | 121 | 0 |
| `ci/test_t0_ssh_preflight_contract.py` | added | 369 | 0 |
| `docs/PROJECT_CONTRIBUTION_EFFORT_LEDGER.md` | added | 150 | 0 |
| `docs/PROJECT_SESSION_HANDOFF.md` | modified | 228 | 0 |
| `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A1_2026-11-11.md` | added | 550 | 0 |
| `docs/evidence/P1_SSH_PREFLIGHT_CONTRACT_RUN_42793921622.md` | added | 48 | 0 |
| `docs/evidence/PR140_FAIL_CLOSED_PROBE_FIX_20261110.md` | added | 61 | 0 |
| `docs/evidence/PR140_SOURCE_REVIEW_20261110.md` | added | 74 | 0 |
| `docs/evidence/T0_SIGNATURE_CONTRACT_FINAL_CONSISTENCY_REVIEW_2026-11-11.md` | added | 101 | 0 |
| `docs/evidence/T0_T2_DEPLOYMENT_PARITY_EVIDENCE_RECONCILIATION_2026-11-10.md` | added | 59 | 0 |
| `docs/reviews/t1/P1_38_SECOND_PASS_ADVERSARIAL_REVIEW_P137_2026-11-09.md` | added | 62 | 0 |
| `ops/ssh/t0-readonly-preflight.sh` | added | 118 | 0 |

The compare response shows these paths as added/modified on the main-side diff. It does not mean all should be copied into the active branch.

## 3. Material compatibility findings

### 3.1 T0 signature A1 — do not replace the active-branch version

The A1 document exists on both refs but has different blob identities:
- `main`: `ca0e73778c3e1430f1d9e8ac4aaa90721bfc113a`
- active branch: `00fdad293e129562145ab930507a4e6b9c2bf23d`

The main-side copy does not include the same owner-approval statement present in the active-branch copy. The active branch version records the later owner decision and VPS + GitHub custody scope, including the joint-rollback constraint. Replacing it with the main-side copy would regress the decision record. Do not cherry-pick or copy the main-side A1 document over the branch version.

The signature consistency review also differs:
- `main` blob: `8304e8e3c9f396d1baac11f851af17a173c91157`
- active branch blob: `80d42aa9b2f51efa9037656f958c86d91eeebe6c`
- source HEAD named in main review: `887f5ed6a71c31c5412e061bef58695323903512`
- source HEAD named in branch review: `838f912139562eb185ad6035e95fd08810071525`

These are review snapshots with distinct source identities. Neither should be silently substituted for the other.

### 3.2 SSH preflight / PR #140 — functional overlap, contract mismatch

The main-side script `ops/ssh/t0-readonly-preflight.sh` is 118 lines; the active-branch counterpart is 66 lines. The main-side test file is a 369-line subprocess/command-stub contract suite; the active branch has a different test implementation. The workflow exists on both refs, but the script/test protocol and workflow result classification are not identical.

Observed main-side behavior includes explicit distinction between unavailable and failed checks and command-stub coverage for read-only/fail-closed outcomes. The active-branch script uses a different probe and result protocol (including `LOOPBACK_ONLY`). These are not safe file-level cherry-picks without contract mapping and regression tests.

Recommendation: retain the active-branch implementation unchanged for now. If additional test coverage is desired, separately map relevant negative/fail-closed cases into the active contract, then test that branch-specific contract. Do not copy the main-side script wholesale.

### 3.3 SSH preflight / PR #144 — useful history, not authorization to merge

The 17-commit group includes encrypted SSH-key contract coverage, strict evidence classification, sanitized diagnostic artifacts, and PR #144 merge closeout on `main`. The workflow on both refs contains encrypted-key handling and a pull-request contract-only path, but this does not establish complete behavioral equivalence. PR #144's evidence is tied to its own source SHA and workflow runs, not to the active branch HEAD.

No PR, workflow or source changes are authorized by this classification.

### 3.4 Stage I workflow — identical blob

`.github/workflows/t0-signature-a2-2-stage-i.yml` has the same blob SHA on both refs: `5fa94939181af5f1f33686c3444bc6f8a0326962`. No import is needed for this path.

### 3.5 Documentation-only groups

- Contribution ledger: governance artifact; can be considered for a later documentation-only reconciliation, after checking current branch conventions.
- P1.8 traceability sequence: includes restore and revert commits; do not replay individual commits as additive feature changes.
- P1.38 T1 review: review evidence, not T0/T2 source functionality.
- T0/T2 parity evidence: related in subject, but must be compared against the active branch's existing evidence and source identity before any replacement.

## 4. Commit-by-commit inventory

All 76 commit SHAs and subjects from the GitHub compare response are recorded below. Group labels are semantic classification labels, not proposed cherry-pick batches.

| Commit SHA | Group | Subject |
|---|---|---|
| `d9610348260a79269bad45aa60c8d456ede75a5f` | Governance documentation | docs: add project contribution and effort ledger |
| `3e9c8452f1e62cb61f861facd80006476a2fa835` | Governance documentation | docs: record contribution ledger baseline in handoff |
| `9099e4ffc7f58d700cd3886425e86225e6d0f9cc` | P1.8 traceability history | docs(p1.8): close negative traceability coverage gaps |
| `cbf41b04b47bfaad287bcebb51a610ed41cdccdc` | P1.8 traceability history | docs(p1.8): restore default-branch file to pre-review content |
| `1599e5f4d9a9b23e0295d1ab8073f92ab0473761` | P1.8 traceability history | revert accidental default-branch documentation file creation |
| `e02cbe14c506c5f02ace6c250862e726a2ad57e5` | T1 review | P1.38: perform second-pass adversarial review of receipt contract |
| `08a98e04b337c491313030dbdd94f4c405349137` | T0/T2 parity evidence | docs(t0-t2): reconcile prior loopback runtime evidence |
| `9cb38cdd995158704fe2993e277396bb9bf4b50a` | SSH preflight / PR #140 | ci: expose Scaleway SSH preflight workflow dispatch |
| `a7eb6fe069ef09141a1405faa0551032bc0b9e2e` | SSH preflight / PR #140 | fix(ssh): add bounded read-only T0 preflight script |
| `fb13c6ac392c9c81482216652e0cae8c08b9ed2f` | SSH preflight / PR #140 | test(ssh): enforce read-only T0 preflight contract |
| `80700054c08ad331749d91db988db6567ba9c5d7` | SSH preflight / PR #140 | test(ssh): correct forbidden-operation contract patterns |
| `5a0c9b3dc3b8711994b08bd0c4bacec7e36d7966` | SSH preflight / PR #140 | fix(ssh): align preflight install path with forced command |
| `e63ed5f9481d4d5968d7eeba122963d5f6fbc769` | SSH preflight / PR #140 | ci: add isolated SSH contract-only gate |
| `87146b00c07cfc32ccc12cb2286e10cb68bb6a5b` | SSH preflight / PR #140 | docs: record isolated SSH contract-only gate |
| `00e482b8c6e7577ff5fc8227abc7419b21ccb775` | SSH preflight / PR #140 | docs: record SSH contract-only CI verification |
| `6398fd7077a57b3b06a37d81ff1077cff3aff474` | SSH preflight / PR #140 | test(ssh): require fail-closed listener probe |
| `b0dc600c5e417fe1d29e02a095b8cb899cdc3f88` | SSH preflight / PR #140 | fix(ssh): fail closed on listener probe errors |
| `bf26a0478dab4dd86050787367da6c1b80ffd482` | SSH preflight / PR #140 | fix(ssh): correct listener probe pattern escaping |
| `029f4b66b51699c4c037f79bcfece2c522690580` | SSH preflight / PR #140 | docs: record fail-closed SSH listener probe update |
| `d8da2a9b16185462e9dc20e4c5b53830418f0670` | SSH preflight / PR #140 | docs: record P1 SSH contract run 42793921622 |
| `8fd573fc01b1fb5b1f19056b971733083f7ea333` | SSH preflight / PR #140 | docs: record PR 140 source review blockers |
| `a83f4792a3a5719fdcdda685c61f0bcf98142faa` | SSH preflight / PR #140 | docs: correct exact regex in PR 140 review |
| `ec5ae7a5dd399c1bdfa3b889a71abace4303f010` | SSH preflight / PR #140 | docs: correct source snippets in PR 140 review |
| `17bd2ddc12e3be415356322a34881d85a56c928f` | SSH preflight / PR #140 | test(ssh): cover fail-closed preflight probe states |
| `81b50e1a81954c729dad715e1f9ad06f97d4bfc2` | SSH preflight / PR #140 | fix(ssh): fail closed on unavailable preflight probes |
| `5daf34054348e9f3baae1eeb59b4a8bee3653088` | SSH preflight / PR #140 | fix(ssh): correct shell escaping in preflight probes |
| `e7e1c45577d54dc72e8f4cb9a4a53a1558cd0d6d` | SSH preflight / PR #140 | fix(ssh): normalize probe regex and newline escaping |
| `c592cdbe4f60d23244e9903e0ef0f3898c30d429` | SSH preflight / PR #140 | fix(ci): classify unavailable preflight probes as blocked |
| `abd04c39c9c9db75a56df9c64925d3d6251f02e5` | SSH preflight / PR #140 | fix(ci): restore fail-closed preflight evidence classification |
| `3288a040091595be01afd8fa1d2ae93b0d7b3813` | SSH preflight / PR #140 | test(ci): align preflight workflow classification contracts |
| `683f8b2a25d3b93c1410f20b0c57871f22fcff06` | SSH preflight / PR #140 | test(ssh): exercise unavailable and failed probe commands |
| `e4461fc240c0b0df052d014f24838f74892e6d15` | SSH preflight / PR #140 | test(ssh): correct deterministic probe command stubs |
| `3a80256f8fced1be6e8060bb23859b9edf7baa1e` | SSH preflight / PR #140 | test(ssh): cover loopback and non-loopback listener outcomes |
| `fa7aadb3878dd5ade67ce8bd6d112807b16c8b3d` | SSH preflight / PR #140 | docs(evidence): record PR140 fail-closed probe fixes |
| `483aa6fd76a001a1d9561b83e4dd206ccc35f8c3` | SSH preflight / PR #140 | docs(handoff): record PR140 fail-closed probe follow-up |
| `55c08a312543260f320d20c54d06033a5a414554` | SSH preflight / PR #140 | test(ssh): correct read-only command boundary assertion |
| `e728fcafe84374e66bf481114585859e4c0739e1` | SSH preflight / PR #140 | docs(evidence): pin latest PR140 test source identity |
| `b7f5519eeda4bf28cbbcf90543506be6398624db` | SSH preflight / PR #140 | docs(handoff): pin latest PR140 test source identity |
| `a41ca435ce593af36eb7bc25a32d9095c54c9564` | SSH preflight / PR #140 | test(ssh): correct SQL mutation boundary assertion |
| `38cb1869a8f932965f0e287ed9ab0b497f90ffab` | SSH preflight / PR #140 | docs(evidence): update final contract test source identity |
| `3aedc2753f67726078e399e245d364264b86419b` | SSH preflight / PR #140 | docs(handoff): pin final PR140 contract test source |
| `01efb54f6b948af0f0f5c538540f3a083dc22741` | SSH preflight / PR #140 | fix(ci): remove duplicated SSH preflight workflow tail |
| `0e716372604b7b077febd7a560ee59af079c3540` | SSH preflight / PR #140 | test(ssh): exercise successful and unavailable preflight probes |
| `0fa44b7146361f60946600eec97d1daf6c74b1be` | SSH preflight / PR #140 | test(ssh): make probe stubs self-contained |
| `7abb55421d3faf6924004e8df4b08ec5ef4330e4` | SSH preflight / PR #140 | test(ci): assert clean workflow file termination |
| `41f0a385308321c090f6639b502c092baee22e76` | SSH preflight / PR #140 | docs(pr140): record workflow cleanup and test hardening |
| `abeacb931b0d429f3ceb532d4cb5355a6a292e6e` | SSH preflight / PR #140 | docs(pr140): preserve main handoff updates on PR branch |
| `9566b40cb8c14b1ceaacf688773ebb91c034ac64` | SSH preflight / PR #140 | docs(pr140): reconcile main handoff history |
| `47002584fbab0fdabc031668658af408f057d3d3` | SSH preflight / PR #140 | test(ssh): isolate SQLite preflight contract fixture |
| `76cd8bd1ed4026ec5d0d25faea07f8870fff4d3f` | SSH preflight / PR #140 | docs: record PR 140 contract harness correction |
| `7d3fe3372596db25855c5aa2a874f553154fa0b6` | SSH preflight / PR #140 | docs: record PR 140 exact-head contract verification |
| `ed4f9ef0e669301d638d05d5dcb56219b3b3528f` | SSH preflight / PR #140 | Merge PR #140: restore P1 read-only SSH preflight contract |
| `4c83aca1b48af1bebac2669f17bcbe3bebcb6bf6` | SSH preflight / PR #140 | docs: record main reset and PR 140 merge closeout |
| `36e8b86b9f4b46009ce7f48aecc106c90b856f67` | SSH preflight / PR #140 | docs: correct reset evidence SHA in handoff |
| `aa05d111da13c4ed44e7122aace708574f1b48bb` | SSH preflight / PR #140 | docs: record main SSH contract-only verification |
| `9941c6fe890be32cd87b37f3051e496527f264d6` | T0 Signature A1 | docs(architecture): reconcile signature amendment with v1 contract |
| `506023e480550a10ab35658bec056d4b3026ee38` | T0 Signature A1 | docs(t0): freeze signature contract review candidate |
| `eed06ee653c5594f77caeb66156d30aae8ca5875` | T0 Signature Stage I | ci(t0): expose isolated A2.2 Stage I workflow |
| `8ed3be3707560bdb3930479c5e552d3e03a42fd4` | T0 Signature Stage I | ci(t0): fix Stage I unittest summary parsing |
| `8515d35a8fe1fe348e3411f7fe905d99730043f6` | SSH preflight / PR #144 | ci(t0): isolate SSH preflight contract on PRs |
| `9c925d233fae490cb295692d77c2587061b826bd` | SSH preflight / PR #144 | test(t0): cover encrypted SSH preflight contract |
| `a8daefbe0a4719433458e71f160ed6ad4ee53e6c` | SSH preflight / PR #144 | test(t0): define workflow path for SSH contract checks |
| `11570ceb06d00f20a2632ca30f71208b4ed36572` | SSH preflight / PR #144 | test(t0): correct repository root for workflow contract path |
| `64e47f8b1e410c1318cdd01560dd9b3e8cf6ccdc` | SSH preflight / PR #144 | test(t0): require successful and complete SSH preflight evidence |
| `51180381de163a7bfd1192dfd1b936b748827191` | SSH preflight / PR #144 | fix(t0): fail closed on SSH and incomplete preflight evidence |
| `946b553a9342c494042258084570c40dbb69b630` | SSH preflight / PR #144 | test(t0): align evidence artifact contract with diagnostics |
| `7e29914cd9925cec2031c5499f20a2be6f69726a` | SSH preflight / PR #144 | fix(t0): restore strict SSH preflight evidence classifier |
| `161e9c25d6b887f6349d4bea3c920d132154bc0b` | SSH preflight / PR #144 | fix(t0): retain sanitized SSH failure evidence in artifact |
| `aca022ee081ffb697c60180c878f9a3bd4e6a5d0` | SSH preflight / PR #144 | test(t0): correct classifier and artifact contract assertions |
| `c9d8858e740b76475ae1d2c4017335e4a6ed981b` | SSH preflight / PR #144 | fix(t0): upload sanitized SSH preflight diagnostics |
| `4f5dfde7d7bd1bde65696922be93f3c1cd4a8c75` | SSH preflight / PR #144 | fix(t0): replace corrupted classifier tail with fail-closed evidence gate |
| `ee3ea34c4cbaa91b6906e2da76ba230e8afe4897` | SSH preflight / PR #144 | fix(t0): normalize SSH failure exit-code evidence |
| `b1363358c56dcf80b02ec504e8343f5edd63502d` | SSH preflight / PR #144 | test(t0): exercise fail-closed SSH preflight verdict scenarios |
| `5f7763e0a8f57a5b35813493e31f13f119c8b0d8` | SSH preflight / PR #144 | Merge pull request #144 from kenznguyen/fix/p1-ssh-preflight-main-20261111 |
| `9b49cd70af18f7cc734c718be016b85aecd047c4` | SSH preflight / PR #144 | docs: record PR #144 SSH preflight merge evidence |
| `063f7a2eacd724f965a9723d0ae66cf95418c0fb` | SSH preflight / PR #144 | docs: record post-merge SSH contract CI evidence |

## 5. G0.3 disposition

- Inventory completeness: **PASS** — GitHub compare returned 76/76 commits.
- Group classification: **PASS** — all 76 commit subjects assigned to one group; group counts sum to 76.
- Material path comparison: **PASS** — 13-path diff surface and critical A1/SSH/Stage I files inspected.
- Integration readiness: **BLOCKED** — incompatible SSH contract implementations and distinct A1 decision snapshots make wholesale or opportunistic cherry-picking unsafe.
- Tests on active branch: **NOT RUN** — G0.3 was read-only and did not change source.
- Exact-HEAD CI: **NOT VERIFIED** — no workflow was dispatched as part of G0.3.
- Artifacts: none generated.

## 6. Recommended disposition

1. Preserve active T0/T2 branch and its owner-approved A1 decision record.
2. Do not merge/rebase the branch wholesale into `main`.
3. Do not cherry-pick the 76 commits as a batch.
4. Keep the Stage I workflow as already identical; no action required.
5. If needed, handle each future adoption as a narrowly scoped change with contract mapping, tests, evidence, exact SHA, and owner approval.
6. Treat PR #140 and PR #144 evidence as historical evidence for their respective source SHAs, not proof of current active-branch behavior.

## 7. Next step and restrictions

G0.3 is read-only and complete. Suggested next step: a separately approved G0.4 documentation-only update to the active branch handoff and this evidence report. Until separately approved, no repository writes.

No source, workflow, test, CI, T0 data, database, VPS/runtime, deployment, training, exchange or trading action was performed. Preserve paper-only posture and `AI_EXECUTION_ENABLED=false`.
