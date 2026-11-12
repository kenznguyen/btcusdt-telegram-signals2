# Five-Layer System — Session Handoff

Updated: 2026-11-11 (Asia/Ho_Chi_Minh)

> Start here in every new session. GitHub is the source of truth. Read this short file first; consult the [archived handoff history](archive/PROJECT_SESSION_HANDOFF_HISTORY_2026-11-10.md) only when an older decision or evidence record is needed.

## Current governance override — 2026-11-11

**Option C — No Destructive Authority: REVOKED by explicit owner instruction on 2026-11-11.** This supersedes every earlier ACTIVE/in-force statement in the historical handoff and lifecycle records. Do not treat Option C as a blanket prohibition. This revocation does not authorize any specific deletion, archive, cleanup, expiry, vacuum, compaction, provider operation or other destructive action. Each concrete action still requires a separately explicit, bounded approval with exact target/data class, scope, preconditions, expected effect, verification and recovery/rollback plan. T0 canonical data, lease/fencing state, ledgers, audit/reconstruction/recovery evidence, owner custody and trust evidence remain protected unless specifically approved. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.


## 1. Repository and active work

- Repository: `kenznguyen/btcusdt-telegram-signals2`.
- Active branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Default branch: `main`. Do not switch branches or create a parallel PR without a task-specific reason and approval.
- G0.2 audit starting HEAD (2026-11-11): `d1978d3606536bb6da2471ed6c94eaf20ffa7b6d`. The final documentation commit that updates this handoff is recorded in the G0.2 completion section below. (post-amendment self-review and evidence link recorded; see current A2.2 workstream below).
- Full previous handoff preserved verbatim in `docs/archive/PROJECT_SESSION_HANDOFF_HISTORY_2026-11-10.md`; archive commit: `2fcad94aef8b15002cdba58aafe62ad208dc818b`.
- PR #139 (SSH passphrase preflight) is CLOSED / NOT MERGED as of 2026-11-11 13:02:13Z; see the retired workstream section below. Do not reopen or merge without separate approval.

## 2. Project invariants

- Personal research system; paper signals only. No live trading, real orders, exchange execution, or production claims.
- Keep `AI_EXECUTION_ENABLED=false`.
- T0 is an independent canonical data foundation. Never create, mutate, delete, migrate, or restore its canonical database unless the exact operation is separately approved.
- T1 remains NOT ACTIVATED. PostgreSQL/TimescaleDB canonical operation remains PARKED / NOT CERTIFIED.
- No service restart, Feeder/API restart, deployment, package installation, credential change, exchange connection, or market-data sync without explicit scope approval.
- No data-retention or cleanup action may touch canonical candles, lease/fencing state, audit evidence, or other durable project records.
- Android Natural Doze remains INTERRUPTED / DEFERRED. Do not investigate or rerun unless reopened by the user.

## 3. CI and evidence rules

- GitHub Actions is the default and only preferred CI. Codemagic is fallback-only; requires a concrete GitHub Actions blocker and explicit approval. Never silently migrate or remove GitHub Actions workflows.
- Before accepting a CI result, record: branch, PR head SHA, base SHA, event, exact checked-out SHA, workflow/run URL, job conclusions, test counts, and artifact ID/name/digest/expiry.
- Distinguish PR head SHA from synthetic merge SHA. A PASS applies only to the source/context proved by the logs.
- Artifact metadata/digest is not independent payload verification. Mark payload hash NOT VERIFIED unless bytes were downloaded and hashed.
- Use explicit states: PASS, CONDITIONAL PASS, BLOCKED, INTERRUPTED, NOT RUN, NOT VERIFIED, DEFERRED.
- After each meaningful increment, update this file or the relevant evidence report and commit on the same active branch. Do not erase historical evidence.

## 4. Retired workstream — SSH Preflight / G4 VPS runtime acceptance

**Status as of 2026-11-11: RETIRED / CLOSED.**

- Owner approved repository-wide SSH Preflight retirement while preserving Git history and historical evidence. Active implementation, contract tests and workflow references were removed from the six recorded refs. See `docs/evidence/SSH_PREFLIGHT_RETIREMENT_2026-11-11.md`.
- PR [#139](https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/139), “Secure Scaleway SSH preflight passphrase handling”, is **CLOSED / NOT MERGED** (closed 2026-11-11 13:02:13Z). Its head was `e6080f7ad8a9bd8b89640f6646ff49215c326602`; base was this active branch. Do not reopen or merge it unless separately approved.
- Historical G4 CI evidence remains historical: run [42824628084](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42824628084), source `a6d939252f1651c4f8f5478bf49581824cc67cc9`, reported 34/34 disposable contract tests PASS. This does not establish VPS runtime state.
- Historical SSH preflight run [42814402445](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42814402445) is retained only as audit history. The workflow feature is retired; do not invoke or restore it.
- The Scaleway VPS `btcquant-t0-t1-test-01` was fully deleted on 2026-11-11, per owner-provided project update. Its former SSH/ForceCommand, service, process, API and database state cannot be inspected. No replacement VPS is currently established by this handoff.
- Old deployment-path and forced-command dispatcher reviews are historical design records only. They do not authorize implementation, installation, SSH access, remote commands, deployment or provisioning.
- Current T0/T2 deployment parity: **NOT VERIFIED**. The bounded 2026-11-09 loopback observation remains **HISTORICAL PASS** only; see `docs/evidence/T0_T2_DEPLOYMENT_PARITY_EVIDENCE_RECONCILIATION_2026-11-10.md` and G0.6 evidence.

### Current boundary

No SSH Preflight restoration, SSH/ForceCommand change, probe installation, remote invocation, service restart, VPS provisioning, T0/T1/T2 deployment, T1 activation, model training, database mutation, or trading is authorized by the retired G4 scope. Any replacement-host work requires a separate bounded approval. Preserve `AI_EXECUTION_ENABLED=false` and paper-only posture.


## 5. Session procedure

1. Read this file, then inspect the active branch HEAD and working-tree/PR state on GitHub.
2. Read only the evidence report and source files needed for the active gate.
3. Reconcile the latest run against exact source SHA before relying on it.
4. Implement contract-first; run GitHub Actions before any runtime action.
5. Stop on missing credentials, unknown listeners, source mismatch, expired lease, unavailable probes, or ambiguous evidence. Fail closed and report NOT VERIFIED/BLOCKED.
6. Update this handoff after the gate result, recording exact commit/run/artifact identifiers and the next authorized step.

Do not infer approval from prior conversation when the durable record is ambiguous. When scope conflicts, stop and ask.

## 6. Current workstream — T0 L4-Minimum automation

**Owner approval (2026-11-10):** automate L4M-01–08 as far as technically possible using GitHub Actions and bounded read-only verification. Do not require owner manual work for deterministic checks CI can perform. Owner participation is reserved for real-world custody/control assertions that cannot be machine-proved from approved sources and final L4M-10 disposition. L4M-09 remains OWNER-WAIVED.

### Current source/evidence
- Controlling matrix: `docs/evidence/p1-8/L4-MINIMUM-PROVENANCE-ACCEPTANCE-MATRIX.md`, current blob `75db0d98134fd656d91a8545bc307c56595aebf7`. Matrix criteria were not changed in this increment.
- Automation plan: `docs/evidence/T0_L4_MINIMUM_AUTOMATION_PLAN_2026-11-10.md`, added in commit `c1a85698395b8660c1e71ecbe5e4bfcf3c504a5e`.
- Evidence register: `docs/evidence/T0_L4_MINIMUM_NINE_CONTROL_EVIDENCE_ACQUISITION_REGISTER_2026-11-10.md`, updated in commit `0ca4c3f7427f81d7adb3e382e5603cb87b6dcad6`, blob `fe4a188d336a8b0279e8e14941c9cb171c23ae0e`.
- Supporting references reconciled in commit `306645446ed1d4a5eacf1f84ac18337b6acbfc72`: policy/historical reconciliation blob `017bca148719006b22431d6eafa383fe6337a10c`; L4M-02 assessment blob `aa3789d0b0adbd6afd75c529e6fb4e56c8758b30`; L4M-08 assessment blob `3216ef081e99687867fead8deb966decdd08d499`; L4M-10 readiness blob `980c046e35429b1c668ff4e3f2069dcfb79714e8`.
- Stale references to matrix blob `2ba85af...` and register blob `4ec993d...` were removed from those four supporting documents. Historical reports were not rewritten.
- Branch remains `feature/t0-centralized-data-feeder-p1-20261101`; no parallel branch or PR created.

### Automation design
- Proposed independent L4 GitHub Actions gates: lineage/contract; exact GitHub artifact inventory and readback; SHA-256 manifest; cryptographic and negative verification; network-disabled offline verification; disposable-copy readback/recovery; tamper-evident history; claim-discipline scan; deterministic aggregate report.
- CI subchecks and owner-only assertions must be reported separately. CI success must never issue owner acceptance or override missing custody/signer evidence.
- First lineage workflow/test were added in commits `ed82a1cf7bc12429ccc3ddb3c0ab6896f3f854e7` and `8f0c5136edaa677d73278c45fb4a4d4c07e86a13`; plan register SHA correction is in `d60be930c5b35254fd336de4777ce8058187ed01`. Expanded lineage gate and trigger coverage were committed in `5b24397773eb957a7efeb0694773b1c0ff446c06`; Git blob header calculation fix in `5dc935aa4663bf3b2ccf6075b704189896e45e63`.
- Current lineage test blob: `e0cca7426176b7e2aeb00cc32fc4d136f0090c46`; artifact collector blob: `77b9fd9a7fafd1d17539fb517bcf84c4c8e024d4`; collector tests blob: `ae122dc7bf3a53be443e17edce8c19e6cb32d868`; explicit allowlist blob: `d481ca0baaca9605cfda1e3ebb79e423b17ac876`; workflow blob: `b01842b3b4ad7e834256b0f270688f758b8abed9`; automation plan blob: `1e057265290b279e5823b0acb8f86df7c8e7a0d3`.
- Expanded contract checks exact matrix/register references, computes their actual Git blob SHA-1 values, scans active L4 decision/evidence documents for superseded matrix/register references, explicitly preserves the historical non-substitution assessment, verifies L4M-01–10 presence, and enforces custody/waiver policy. Workflow triggers now cover L4 decision and evidence docs.
- Initial workflow run [42829414892](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42829414892), source `ed82a1cf7bc12429ccc3ddb3c0ab6896f3f854e7`, failed 1/7 because the plan still referenced the old register blob. Corrected; runs [42829483832](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42829483832) and [42829518609](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42829518609) passed 7/7.
- Expanded run [42830499889](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42830499889), source `5b24397773eb957a7efeb0694773b1c0ff446c06`, failed 1/11 because the new Git blob SHA helper encoded a literal backslash-zero instead of a NUL byte. Fixed in `5dc935aa4663bf3b2ccf6075b704189896e45e63`.
- Lineage gate is stable: run [42831240089](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42831240089), 11/11 PASS, source SHA `27aea002a3f404792d4c1a3dc56eff77c2163840`.
- Artifact inventory/manifest pilot: run [42834966105](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42834966105), event `push`, source SHA `db01cbe7750b75fcaafd4576d646d04c5b029c4b`; lineage job `129894622621` SUCCESS (11/11), manifest job `129894707925` SUCCESS (19/19), `L4_ARTIFACT_MANIFEST=PASS`.
- Explicit allowlist currently contains three GitHub artifacts: P1.8.14 synthetic bundle ID `13546255148`, independent-runner verification ID `13545287609` (both run `42304505004`, source `19a6629212f2f98aaa08c4ebe6ceb68801881732`), and L4 lineage artifact ID `13771662067` (run `42831240089`, source `27aea002a3f404792d4c1a3dc56eff77c2163840`).
- Manifest artifact `t0-l4-artifact-manifest-42834966105`, ID `13772792245`, 2,877 bytes, expires `2026-11-17T14:31:38Z`; ZIP SHA-256 `a361eae206bffc312e1e1c04cd86aa9f9b75c8eb748900b6f663955efa08e9e4` independently confirmed after download. Manifest JSON SHA-256 `a2d4089abd2fcf820919c4ba4cb39108fc1e1823c0e325efb2b8b005fdb5c4ec` matches its `.sha256` file.
- Source ZIP SHA-256 values independently re-read and verified against manifest: `13546255148` = `14e157cd8a393a743e01e12a915ab69636cf7cb4765f8a331953daeef1987b6f`; `13545287609` = `418fff2ffa874003527db5d83d8717bf8946b489c4e3a62b023f4c5e5e6feedd`; `13771662067` = `50991097fb0febf8f38398c656c6edf600f8a079bccd2dbf23a36873931bba68`. All 53 member digests (47+2+4) independently matched. P1.8.14 artifacts expire `2026-11-13T22:24:44Z`; lineage source artifact expires `2026-11-17T14:09:25Z`.
- This is a **three-artifact GitHub inventory pilot**, not a complete L4 evidence package or proof of owner custody. All source objects remain in the GitHub failure domain. Signature verification and offline verification have NOT been run.

### Previous verification before four-artifact inventory extension (2026-11-10)

- Latest workflow run: [42836094887](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42836094887), event `push`, branch `feature/t0-centralized-data-feeder-p1-20261101`, exact checkout/source SHA `b3a975e151241ba5d5116f49a8d00a056adf9fa4`, overall SUCCESS.
- Lineage job `129898561610`: SUCCESS, 12/12 tests PASS, verdict `L4_MINIMUM_LINEAGE_CONTRACT=PASS`.
- Artifact readback/manifest job `129898668686`: SUCCESS, 19/19 tests PASS, verdict `L4_ARTIFACT_MANIFEST=PASS`.
- Total for this workflow: 31/31 tests PASS.
- Output lineage artifact: ID `13774031418`, name `t0-l4-minimum-lineage-42836094887`, 1,151 bytes, expires `2026-11-17T14:38:12Z`, uploaded ZIP SHA-256 `801bbc22e1979b3e5260371a22db305d37ddd2bc6837aae3c00c99d60595abcf`.
- Output manifest artifact: ID `13772968950`, name `t0-l4-artifact-manifest-42836094887`, 2,882 bytes, expires `2026-11-17T14:38:12Z`, uploaded ZIP SHA-256 `a265f30e83cfc2766ad5c3d9004b1535d3d68c8170cc4bc8a2205c04d588281f`.
- The allowlisted inventory comprises the two P1.8.14 artifacts (run `42304505004`, source SHA `19a6629212f2f98aaa08c4ebe6ceb68801881732`) and the L4 lineage source artifact (run `42831240089`, source SHA `27aea002a3f404792d4c1a3dc56eff77c2163840`). These are explicitly selected GitHub artifacts, not a complete L4 evidence inventory.
- Collector failure recovery: run `42834714404` failed closed with `GITHUB_RESPONSE_TOO_LARGE` while reading GitHub compare metadata. The compare request was narrowed to `per_page=1` and its bounded response limit raised to 4 MiB; the latest run above passed. Earlier pilot and correction runs are retained in Actions history; no failure was hidden.
- Artifact ZIP SHA values above are the GitHub upload digests from workflow logs. Unlike the earlier 3-artifact pilot, this latest run's output ZIP bytes and manifest JSON have not yet been independently downloaded and re-hashed; payload readback in the collector means source artifacts were fetched and inspected by the workflow, not that the newly uploaded manifest artifact itself was independently re-read outside that run.
- No signature verification or network-disabled offline verification was performed. Do not promote L4 aggregate status or owner custody claims.

### Current status
- Automation direction: APPROVED.
- Design/documentation: RECORDED.
- L4 lineage/contract workflow: **PASS — latest 12/12**.
- GitHub artifact inventory/readback + SHA-256 manifest: **PARTIAL PASS — 4 explicitly allowlisted artifacts; 19/19 contract tests; 4/4 ZIP and 57/57 member digests independently verified**.
- Complete L4 evidence package inventory, owner custody/readback, signature verification and network-disabled offline verification: **NOT VERIFIED / NOT STARTED**.
- VPS custody/readback: NOT VERIFIED.
- Actual owner signer/custody assertions: PENDING EVIDENCE only where not machine-verifiable.
- L4M-01–08: retain prior per-control dispositions; no PASS promoted.
- L4M-09: OWNER-WAIVED.
- L4M-10: NOT VERIFIED; final disposition remains owner-only.
- Aggregate L4-Minimum: BLOCKED / NOT VERIFIED.

### Next permitted step
The lineage gate is stable (latest 12/12 PASS). The GitHub-only collector inventories four explicitly allowlisted artifacts and has independently verified the four ZIPs and 57 member digests. Next: add a separate exact-path/ref GitHub repository-file inventory for the current matrix, decisions, historical audits and lifecycle evidence, binding each file to commit/ref, Git blob SHA and SHA-256. Separately discover further eligible Actions artifacts from authoritative run metadata; never guess IDs. Do not treat this pilot as a frozen L4 package. Signature/negative verification and network-disabled offline verification remain downstream until the complete evidence inventory is reconciled. Keep owner custody assertions separate; no VPS dispatch.

### Explicit limits
No canonical T0 SQLite access or mutation; no VPS/SSH/forced-command changes; no probe installation or remote command; no key generation/signing/rotation/revocation; no trust-root/provider mutation; no artifact deletion/retention changes; no T1, PostgreSQL, service restart, live trading or real orders. Option C — No Destructive Authority remains ACTIVE. CI PASS is not VPS runtime PASS and is not L4 acceptance.


### Latest verification — four-artifact inventory extension (2026-11-10)

- Allowlist update commit: `5c9941112f24edb213c129a5962187461d8f4308`; active branch `feature/t0-centralized-data-feeder-p1-20261101`; allowlist blob `d481ca0baaca9605cfda1e3ebb79e423b17ac876`.
- Workflow run: [42837579509](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42837579509), event `push`, conclusion SUCCESS, exact checkout/source SHA `5c9941112f24edb213c129a5962187461d8f4308`.
- Lineage job `129903788538`: SUCCESS, 12/12 tests PASS. Manifest job `129903905070`: SUCCESS, 19/19 tests PASS. Total: 31/31 tests PASS.
- Four source artifacts inventoried: IDs `13546255148`, `13545287609`, `13771662067`, `13774031418`; 57 member digests (47+2+4+4). New source artifact `13774031418` from run `42836094887`, source SHA `b3a975e151241ba5d5116f49a8d00a056adf9fa4`, ZIP SHA-256 `801bbc22e1979b3e5260371a22db305d37ddd2bc6837aae3c00c99d60595abcf`, expiry `2026-11-17T14:38:12Z`; independently downloaded/re-hashed and all four member digests matched.
- Output manifest artifact `13774501896`, `t0-l4-artifact-manifest-42837579509`, 3,038 bytes, expires `2026-11-17T14:46:58Z`, ZIP SHA-256 `6f121108e6e3f98b84327251bbc965c9d6a9a849f40b2bba6d6efb8b4eff88ba`; downloaded/re-hashed independently. JSON member SHA-256 `25b0db3de3fadd9504d030310b4c2243e18cdf4601bd88d2f41c2d1bf86ab07a` matches its sidecar.
- Output lineage artifact `13772649665`, `t0-l4-minimum-lineage-42837579509`, 1,151 bytes, expires `2026-11-17T14:46:58Z`, ZIP SHA-256 `9c4c7fabdf076abb1f719d32e28edf47b2bfaec91fa5528531d178c91a51bfc4`; independently downloaded/re-hashed. It records source SHA `5c9941112f24edb213c129a5962187461d8f4308` and 12/12 lineage tests PASS.
- The four-item manifest is still a selected Actions-artifact pilot, not the complete L4 package. The current run's output artifacts are not inputs to its own manifest and may be considered only in a later run after exact verification.
- Complete repository-file evidence inventory, owner custody/readback, signature verification, network-disabled offline verification and L4M-10 owner disposition remain NOT VERIFIED / NOT STARTED. Aggregate L4-Minimum remains BLOCKED / NOT VERIFIED.

### Next permitted L4-Minimum step
Build the exact-path/ref GitHub repository-file inventory for the matrix, decisions, historical audits and lifecycle evidence. Record Git path, exact commit/ref, Git blob SHA and SHA-256 of retrieved bytes; preserve historical files unchanged. Keep this separate from Actions artifact inventory and fail closed on missing paths, ambiguous refs or digest mismatch. Do not start signature or offline gates until the complete evidence inventory is reconciled and stable.


### Lineage regression and correction — 2026-11-10

- Documentation commit `42b97bcd252537a75119b93b5eb6f55b56e98e11` updated the Evidence Register but left the expected register blob SHA stale in the lineage test and in three supporting assessments. Workflow run [42838019140](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42838019140) failed closed: lineage 11/12 (1 failure), manifest job skipped. Exact failure: `test_matrix_and_register_constants_match_checked_out_git_blobs`; expected old register blob `4379b5f115c5dac5a2779b857ab8fababf88e4f3`, actual register blob `fe4a188d336a8b0279e8e14941c9cb171c23ae0e`.
- Correction: update `REGISTER_SHA` in the lineage contract test, update the automation plan's current-register reference, and rebind L4M-02/L4M-08/L4M-10 supporting assessments to the current register blob. Preserve the historical lineage record's old reference as historical; do not rewrite the historical audit.
- The corrected run must prove the blob constants, plan reference and all supporting-document references against the exact checked-out tree before this gate is considered stable again. The failed run remains part of the audit trail.


### Corrected lineage verification — run 42838231181

- Correction commit: `fa6d317cd43d4ce4bc1091cdd50c2d5f0e8c62b7`; active branch `feature/t0-centralized-data-feeder-p1-20261101`.
- Workflow run: [42838231181](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42838231181), event `push`, exact checkout/source SHA `fa6d317cd43d4ce4bc1091cdd50c2d5f0e8c62b7`, overall SUCCESS.
- Lineage job `129906071925`: SUCCESS, 12/12 tests PASS. Artifact-manifest job `129906160055`: SUCCESS, 19/19 tests PASS. Total 31/31 tests PASS; `L4_MINIMUM_LINEAGE_CONTRACT=PASS` and `L4_ARTIFACT_MANIFEST=PASS`.
- The corrected test constant now binds to current Evidence Register blob `fe4a188d336a8b0279e8e14941c9cb171c23ae0e`; current lineage test blob `e0cca7426176b7e2aeb00cc32fc4d136f0090c46`. Automation plan and L4M-02/L4M-08/L4M-10 supporting assessments now reference the same current register blob. Historical lineage record remains unchanged.
- Output lineage artifact `13774367642`, name `t0-l4-minimum-lineage-42838231181`, 1,151 bytes, expires `2026-11-17T14:50:44Z`, ZIP SHA-256 `565dfca4b34cdb967ba49e475acfa3a0824f26df9928aaa9879651f2297f7c91`; downloaded and independently re-hashed. It records source SHA `fa6d317cd43d4ce4bc1091cdd50c2d5f0e8c62b7` and 12/12 lineage tests PASS.
- Output manifest artifact `13773284504`, name `t0-l4-artifact-manifest-42838231181`, 3,036 bytes, expires `2026-11-17T14:50:44Z`, ZIP SHA-256 `add93d2d2bf18ee4f66338a28b4a6c6f98dfa15ac224539fed46d947fcff5609`; downloaded and independently re-hashed. Manifest JSON SHA-256 `4e61cfc55c7de2147fcb9c8bddf1d984023267eda654df618a83e4b5ce68d557` matches the included sidecar. It contains four source artifacts and 57 member digests; collector source SHA is the exact commit above.
- Failed predecessor run `42838019140` remains visible and documented: lineage 11/12, manifest skipped because the register blob constant was stale. No failure was hidden; the corrected run above proves the fix.
- L4-Minimum remains **BLOCKED / NOT VERIFIED**. This run validates only lineage and the four-artifact GitHub inventory/manifest pilot. Repository-file inventory for the matrix/decisions/historical audits/lifecycle evidence remains the next implementation gate. Signature verification, network-disabled offline verification, owner custody/readback and L4M-10 owner disposition remain NOT VERIFIED / NOT STARTED.


### Exact-commit repository-file inventory — TDD contract setup

- Verified current branch head before changes: `640911d1c242c483e327b955293487517f50e29a`, tree `5a75e64cb994c18a930294cc9cddbdaf88cbc8c5`.
- Latest prior workflow [42838428048](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42838428048), exact source SHA `640911d1c242c483e327b955293487517f50e29a`: lineage job `129906779361` SUCCESS (12/12); artifact-manifest job `129906858276` SUCCESS (19/19); total 31/31.
- Output manifest artifact `13773544544`, 3,038 bytes, expires `2026-11-17T14:51:55Z`, GitHub upload digest `7f746a0bef3ae5892c97a048e2f87ddcfd14de9587e609e12f2c97169b4c9d75`. It was downloaded to the model's working session, but independent payload re-hash was not completed in this step; do not claim independent hash verification for this run. Output lineage artifact `13773424397`, 1,151 bytes, GitHub upload digest `8354ce82574c09f2cfb36792ed5d0628100fdb7e5dade6a79375e423fb8eb87a`.
- The repository-file inventory scope was identified from the exact Git tree and 27 source paths were independently fetched at ref `640911d1c242c483e327b955293487517f50e29a`; all 27 returned GitHub blob SHAs matched the tree inventory. Scope includes six owner decisions, current matrix/register/automation plan, three historical audit/review records, lifecycle policy and P1.8.143/144/146–152 evidence, and L4 supporting assessments. This is a scoped evidence-source inventory, not a claim that every repository file or every L4 evidence object has been inventoried.
- Test-first setup: contract tests `ci/test_t0_l4_repository_file_inventory.py` created as blob `bf0b053773df0ebc42dbbc64b1760288956b4461`. Workflow is being extended with a dedicated read-only job. The implementation module and inventory configuration are not yet present; this is intentionally the RED stage and must fail closed until implementation is added.
- Planned contract: exact checkout commit, exact configured branch, explicit path allowlist, Git tree path/type/blob binding, expected blob SHA equality, SHA-256 over exact Git object bytes, deterministic JSON + sidecar, missing/duplicate/unsafe path and symlink rejection. No network API is needed in the inventory job because it reads only the checked-out Git object database.
- No VPS, SQLite, runtime, keys, trust roots, destructive actions or artifact retention changes.


### Repository-file inventory — implementation increment

- Test-first contract commit: `b584cc218833bfa6f5d0345b55639c0448961a8e`; workflow run [42912485814](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42912485814). Lineage job `130166435069` SUCCESS. Repository-file inventory job `130166511944` FAILED as expected at RED: `ModuleNotFoundError: No module named 'ci.t0_l4_repository_file_inventory'`. Artifact-manifest job `130166511761` SUCCESS. Output artifacts: lineage `13806724879` (1,152 bytes, upload digest `c83b8ce84a584340973110b340fe7049cabf8996fa8ab2d6e488eea7a0d0da73`); manifest `13806324895` (3,037 bytes, upload digest `82730745a218c96b4cbf8efed1da01bca814e99e29dfb414379cf66592689ebb`); both expire `2026-11-17T22:13:09Z`.
- Implemented inventory contract: config schema `T0_L4_REPOSITORY_FILE_INVENTORY_V1`; 27 exact source paths and expected Git blob SHA-1 values. The 27 blob SHAs were fetched independently at baseline commit `640911d1c242c483e327b955293487517f50e29a` and all matched.
- Inventory implementation reads only the checked-out Git object database at exact `GITHUB_SHA`; requires configured branch match; validates exact Git tree path, regular-file mode and expected blob SHA; re-hashes Git blob framing; computes SHA-256 over raw blob bytes; emits deterministic JSON plus SHA-256 sidecar. Fail-closed path, duplicate, missing/ambiguous, symlink/non-regular, stale SHA, wrong commit/branch, per-file 2 MiB and total 16 MiB limits. No GitHub API token, network request, VPS or runtime is used by this job.
- Files introduced/updated in the implementation increment: `ci/t0_l4_repository_file_inventory.py`, `ci/l4-repository-file-inventory.json`, workflow dedicated job, and this handoff. The test-first contract is `ci/test_t0_l4_repository_file_inventory.py`.
- Next: run the dedicated inventory tests and build the 27-file manifest in GitHub Actions; independently download/re-hash the output artifact; review its exact commit/path/blob/SHA-256 records. A passing scoped inventory does not imply full L4 evidence completeness or owner custody.


### Latest L4 source inventory — 36 files and reference scope (2026-11-11)

- Validated source commit: `da0dc7bce6d3130a718a7ff7a504d8b4c06451cb`; active branch `feature/t0-centralized-data-feeder-p1-20261101`.
- Workflow run [42914214815](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42914214815), event `push`, exact checkout/source SHA `da0dc7bce6d3130a718a7ff7a504d8b4c06451cb`, overall SUCCESS.
- Lineage job `130172320448`: SUCCESS, 12/12 tests PASS. Artifact-manifest job `130172418869`: SUCCESS, 19/19 tests PASS. Repository-file inventory job `130172418954`: SUCCESS, 10/10 tests PASS. Total 41/41 contract tests PASS; `L4_REPOSITORY_FILE_INVENTORY=PASS`.
- Repository-file inventory artifact ID `13807169340`, name `t0-l4-repository-file-inventory-42914214815`, 4,101 bytes, expires `2026-11-17T22:24:09Z`; GitHub upload digest and independently recomputed ZIP SHA-256 `0bb9a774e3b9fc6718feb6e636d1f43183623dde7b69f3736c41954b655ab3bc`.
- Inventory JSON SHA-256 `2e4ee09644a0002e99974620ecd0a866dcc0b03a27311719d52fc2a2eb0fbfd2` matches its included sidecar. ZIP contains exactly JSON manifest and SHA-256 sidecar. Manifest source commit `da0dc7bce6d3130a718a7ff7a504d8b4c06451cb`, 36 unique paths, total source bytes 456,252.
- Inventory includes the matrix, current register/plan, six owner decisions, historical audit/review records, lifecycle records P1.8.142–152 (selected relevant chain), the non-substitution assessment and source-basis documents, the T0 components-outside-L4 scope audit, personal-use content audit, and the new scope reconciliation report. Exact path, Git blob SHA-1, file size and SHA-256 are recorded for each object.
- Scope reconciliation report: `docs/evidence/T0_L4_REPOSITORY_FILE_INVENTORY_SCOPE_RECONCILIATION_2026-11-11.md`, blob `2f93102a78baf40edfcd6f58fc1c1ac8e4ca62e0`. It records why three additional source records were included and why T0 deployment/API/DR, T1/T2 runtime and mutable handoff references are excluded from the L4 evidence-source set. Basename-only citations in the historical T0 components audit remain unresolved and are not guessed. Reference reconciliation is **PARTIAL PASS**, not a claim of complete repository-wide evidence discovery.
- The prior 36-file run [42914049188](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42914049188) also passed; this final run confirms the updated Automation Plan and matching inventory-config blob at the exact current commit.
- The four-artifact GitHub Actions inventory/manifest pilot remains a separate inventory class. Its source allowlist has not been silently expanded by the repository-file inventory. The latest Actions artifact-manifest output ID `13808956100` (3,037 bytes, upload digest `73aac8f5688dc7ce362cd0932df1950920b38be0612adde9df80aeebcd60f889`) and lineage output ID `13807869163` (1,152 bytes, upload digest `a85b42d823e962e8bfce994044cbc22006a16ec6605a5e5996531e3f0f3f6772`) have not been independently downloaded/re-hashed in this increment.
- Aggregate L4-Minimum remains **BLOCKED / NOT VERIFIED**. The 36-file source inventory and partial reference reconciliation do not prove completeness of all L4 evidence, VPS custody/readback, signer separation, authenticated latest-head freshness, offline verification, trust lifecycle, tamper-evident history or L4M-10 owner disposition. No control is promoted by CI.

### Next permitted step
Continue cross-reconciling the 36-file inventory against any remaining exact source objects that the current matrix/register/decisions/lifecycle chain actually relies on. Resolve basename-only references only when their exact repository paths and relevance are verified; do not guess or expand scope for unrelated T0/T1/T2 engineering. Separately reconcile the four-artifact Actions allowlist against authoritative workflow/run/artifact metadata and retention, keeping output artifacts distinct from source evidence. After both inventories are stable, prepare the exact-object signature/negative-verification contract; do not generate or use keys. Network-disabled offline verification remains downstream. No VPS/SQLite access, signer/trust-root operations, artifact deletion or destructive lifecycle actions. Option C remains ACTIVE; aggregate L4 remains BLOCKED / NOT VERIFIED.


### 40-file repository inventory — historical source references resolved (2026-11-11)

- Validated source commit: `9442386151f3ff7ce7c699e00e617b8f4033aa3c`; active branch `feature/t0-centralized-data-feeder-p1-20261101`.
- Workflow run [42914799884](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42914799884), event `push`, exact checkout/source SHA `9442386151f3ff7ce7c699e00e617b8f4033aa3c`, overall SUCCESS.
- Lineage job `130174359159`: 12/12 tests PASS. Artifact-manifest job `130174441589`: 19/19 tests PASS. Repository-file inventory job `130174441667`: 10/10 tests PASS, verdict `L4_REPOSITORY_FILE_INVENTORY=PASS`. Total 41/41 contract tests PASS.
- Repository-file inventory artifact ID `13807289589`, name `t0-l4-repository-file-inventory-42914799884`, 4,477 bytes, expires `2026-11-17T22:27:57Z`; GitHub upload digest and independently recomputed ZIP SHA-256 `40ec49a9ac0e0f3caa2883c6808cdf150151a0586f46b41901a37b4377fdf6f3`.
- Inventory JSON SHA-256 `a64553ba61414ea15c4d7c97bcd18f192df5b74094b193ae37f86dbd8ebc43b1` matches the included sidecar. Manifest source commit `9442386151f3ff7ce7c699e00e617b8f4033aa3c`, 40 unique paths, total source bytes 517,128.
- Added historical source objects: `T0_TSA_WORM_READ_ONLY_AUDIT_2026-11-10.md`, `P1.8.80-retention-and-eligibility-policy.md`, `P1.8.121-owner-decision-ratification-option-c-no-destructive-authority.md`, and `P1.8.141-holistic-data-lifecycle-design-closure-assessment.md`. Their exact paths and Git blob SHAs were resolved and included. They preserve historical scope and lifecycle lineage only; no old status is promoted to current operational evidence.
- The updated reconciliation report blob is `cd865b09c0340fa910412a9d469a7da980357e35`; it now records the four newly resolved historical source objects and exact exclusions for shared-data/PostgreSQL/backend and generic lifecycle architecture references. Reference reconciliation remains **PARTIAL PASS** because it is a bounded source set, not a repository-wide completeness proof.
- Latest Actions artifacts: repository inventory `13807289589` independently re-hashed as above; artifact-manifest output `13809042009` (3,038 bytes, upload digest `5fef6eb79efde8de9734716a997c57b83cccd57e3e7c7c76cef217ac0bc1fa60`); lineage output `13807883936` (1,152 bytes, upload digest `21f3d7ac0bd9c784e097f1d2e5f20bced382c11cea6f04f1e7f19f06081006aa`). Manifest and lineage ZIP payloads were not independently downloaded/re-hashed in this increment; upload digests only.
- Aggregate L4-Minimum remains **BLOCKED / NOT VERIFIED**. The 40-file inventory does not prove owner custody/readback, signer separation, authenticated latest-head freshness, offline verification, trust lifecycle, tamper-evident history or L4M-10 owner disposition. No control is promoted.

### Next permitted step
Perform a final coverage check against the controlling matrix and Evidence Register to confirm that each mandatory L4M-01–08 and L4M-10 evidence requirement has either an exact source object in the 40-file set, a separate Actions artifact identity, or an explicit owner-only/NOT VERIFIED disposition. Do not add unrelated T0/T1/T2 engineering references merely because they are linked. Keep source files and Actions artifacts as distinct inventory classes. Once this crosswalk is stable, design the exact-object signature and negative-verification contract; do not generate/use keys. Offline verification remains downstream. No VPS/SQLite access, signer/trust-root operation, artifact deletion or destructive lifecycle action. Option C remains ACTIVE; aggregate L4 remains BLOCKED / NOT VERIFIED.


### Nine-control register refresh and 40-file inventory revalidation (2026-11-11)

- Commit: `0e496d251af825b0ba7ba7fbbc1837578aa210f3`; branch `feature/t0-centralized-data-feeder-p1-20261101`.
- Evidence Register blob updated to `0125abfe77c0d0f9172e66aa5d09ec8fc8a33623`. It now records four Actions artifacts as a distinct pilot, 40 exact-commit repository files as a separate source inventory, reference reconciliation PARTIAL PASS, and aggregate L4 BLOCKED. It also corrects the current-policy reconciliation reference to blob `017bca148719006b22431d6eafa383fe6337a10c`.
- Updated lineage test blob `3dcb97a413b4aaeb3aa4a918689b6cf653adf6db` now binds `REGISTER_SHA=0125abfe77c0d0f9172e66aa5d09ec8fc8a33623`, treats prior register blob `fe4a188d336a8b0279e8e14941c9cb171c23ae0e` as superseded in active docs, and preserves historical references in the designated historical lineage record.
- Updated plan blob `879db03458bb3480e62108dc391dcf452e5feb19`; L4M-02 assessment blob `acea504de4608520c59b1870fe6cb7241492830e`; L4M-08 assessment blob `603ca1f1cb5fe8988f17fd866942d06c15a213b7`; L4M-10 readiness blob `7b5653815222ed499b2d6dc57dc1238137d26aff`. All active register cross-references now point to the current register blob; the repository inventory config was rebound to the changed file blobs.
- Workflow run [42915177432](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42915177432), exact source SHA `0e496d251af825b0ba7ba7fbbc1837578aa210f3`, overall SUCCESS. Lineage job `130175671173`: 12/12 PASS; repository-file inventory job `130175752435`: 10/10 PASS; artifact-manifest job `130175752509`: 19/19 PASS. Total 41/41 tests PASS.
- Repository inventory artifact ID `13809286004`, name `t0-l4-repository-file-inventory-42915177432`, 4,489 bytes, expiry `2026-11-17T22:30:27Z`; upload digest and independently recomputed ZIP SHA-256 `0035ac3c264efa094307b74349797711488d1e1b01b721ee3ede2bb737de400e`.
- Inventory JSON SHA-256 `a1193e41fb96ea546ab952b897a55a40c7a56312b8a0a63fabff851eaa09a795` matches the sidecar. Manifest source commit `0e496d251af825b0ba7ba7fbbc1837578aa210f3`, 40 unique paths, 518,716 source bytes. The changed Evidence Register and supporting assessment blobs are all present in this exact manifest.
- Output artifact-manifest ID `13809460570` (3,040 bytes, upload digest `d4b9d2db86ebe8b3f9508fc352ec4172e2e7ac86e7b46e09f257682a6db7f2b3`) and lineage ID `13809830236` (1,151 bytes, upload digest `e2bbc948f67e0698214888fa2968b066103267a138fd58b9fd755173af84ea9e`) were not independently downloaded/re-hashed in this increment; upload digests only.
- Control dispositions remain unchanged: L4M-01 PARTIAL; L4M-02 NOT VERIFIED; L4M-03 PARTIAL (synthetic/design only); L4M-04 PARTIAL (synthetic/CI only); L4M-05 PARTIAL (synthetic model only); L4M-06 PARTIAL (synthetic policy only); L4M-07 PARTIAL (synthetic model only); L4M-08 DOCUMENTARY PASS ONLY; L4M-09 OWNER-WAIVED; L4M-10 NOT VERIFIED / PENDING OWNER ASSESSMENT. Aggregate remains BLOCKED / NOT VERIFIED.

### Next permitted step
Build the final control-to-source crosswalk using the refreshed Evidence Register and current 40-file manifest. For each active control L4M-01–08 and L4M-10, classify exact source docs, Actions artifact IDs, synthetic/CI-only evidence, missing owner assertions and remaining acceptance criteria. Do not treat repository file presence or CI PASS as owner custody or runtime proof. Once the crosswalk is stable, reconcile further eligible Actions artifacts from authoritative metadata; then prepare signature/negative-verification design only. No key generation or signing operation. Offline verification remains downstream. No VPS/SQLite access, destructive action, artifact deletion or trust-root change. Option C remains ACTIVE; aggregate L4 remains BLOCKED / NOT VERIFIED.


### Control-to-source crosswalk and CI revalidation (2026-11-11)

- Crosswalk document: `docs/evidence/T0_L4_CONTROL_TO_SOURCE_CROSSWALK_2026-11-11.md`, blob `c040090bc65699df57d4ecd3e50ac805782a4cd1`. It maps L4M-01–08 and L4M-10 to exact source documents, the four Actions source artifacts, current CI evidence and missing owner/operational proof. L4M-09 remains owner-waived. This is a derived working assessment, not a source evidence object and is not part of the 40-file source inventory.
- Workflow run [42915451341](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42915451341), exact source SHA `258c971d06baa9818980ebcf3d1db046b412beb7`, overall SUCCESS. Lineage job `130176582477`: 12/12 PASS; artifact-manifest job `130176666609`: 19/19 PASS; repository-file inventory job `130176666720`: 10/10 PASS. Total 41/41 tests PASS.
- Repository-file inventory artifact ID `13810135011`, name `t0-l4-repository-file-inventory-42915451341`, 4,489 bytes, expires `2026-11-17T22:32:10Z`; upload digest and independently recomputed ZIP SHA-256 `76642680304c7c35ae9daf3f28e4e0f80e615036001e708a0d5223afda5f6926`.
- JSON SHA-256 `8b1582059c935d03f51a97b732b8561ce2a40a0ab1788e0dccebecbe6654a8d1` matches the included sidecar. Inventory source commit `258c971d06baa9818980ebcf3d1db046b412beb7`, 40 unique paths, 518,716 source bytes. The crosswalk itself is deliberately separate from the source inventory because it is derived analysis, not an underlying evidence object.
- Artifact-manifest output ID `13809910243`, 3,037 bytes, upload digest `3914efd3be41a8c92580835826f5c472b752d58a38d2fdaab123dd15e8bc19ef`; lineage output ID `13809780354`, 1,151 bytes, upload digest `9377722a00dcabe80dbb9749f86e131ffd0ac25ce3662775941591d70e7fcf42`. These two ZIPs were not independently downloaded/re-hashed in this increment; upload digests only.
- Crosswalk dispositions mirror the refreshed Evidence Register: L4M-01 PARTIAL; L4M-02 NOT VERIFIED; L4M-03 PARTIAL synthetic/design only; L4M-04 PARTIAL synthetic/CI only; L4M-05 PARTIAL synthetic model only; L4M-06 PARTIAL synthetic policy only; L4M-07 PARTIAL synthetic model only; L4M-08 DOCUMENTARY PASS ONLY; L4M-09 OWNER-WAIVED; L4M-10 NOT VERIFIED / PENDING OWNER ASSESSMENT. Aggregate remains BLOCKED / NOT VERIFIED.

### Next permitted step
Reconcile the four-artifact Actions allowlist with all eligible source artifacts from authoritative workflow/run metadata, preserving exact source run, source SHA, artifact ID/name, expiry and archive/member digests. Verify output artifacts separately; do not self-include an artifact in its own manifest. After that inventory is stable, review the crosswalk against the Evidence Register and decide whether exact-object signature/negative-verification design can begin. No key generation or signing operation. Offline verification remains downstream. No VPS/SQLite access, trust-root change, artifact deletion or destructive lifecycle operation. Option C remains ACTIVE; L4 aggregate remains BLOCKED / NOT VERIFIED.


### Four-artifact Actions source reconciliation — independent readback (2026-11-11)

- Reconciliation report: `docs/evidence/T0_L4_ACTIONS_ARTIFACT_SOURCE_RECONCILIATION_2026-11-11.md`, committed in `946e2b0d1da4ec35046ef3b37f4408f438dff27f`.
- Current source allowlist blob remains `d481ca0baaca9605cfda1e3ebb79e423b17ac876`; it declares four source artifacts from runs `42304505004`, `42831240089`, and `42836094887`.
- Authoritative per-run GitHub metadata confirms all four artifact IDs, names, branch, source SHA, byte size and expiry. All remain unexpired at this check.
- Downloaded all four exact ZIPs and independently recomputed archive SHA-256. All four sizes and ZIP digests match the run-42915451341 manifest.
- Compared all archive member paths, byte sizes and SHA-256 values against the manifest: 57/57 members PASS (47 + 2 + 4 + 4).
- Manifest output artifact `13809910243`, run `42915451341`, size 3,037 bytes, expiry `2026-11-17T22:32:10Z`; independently downloaded ZIP SHA-256 `3914efd3be41a8c92580835826f5c472b752d58a38d2fdaab123dd15e8bc19ef`. JSON member SHA-256 `75ac4d17c46c4852f2a6a646fdefb3a6f73e1c5bec911c5729acb8affbba94bc` matches its sidecar.
- Run `42915451341` outputs `13810135011` (repository inventory), `13809910243` (artifact manifest) and `13809780354` (lineage) are not self-included as source artifacts.
- **Scoped artifact payload verification: PASS.** **Repository-wide enumeration of every eligible Actions run/artifact: NOT VERIFIED.** The four-artifact allowlist is now byte-verified but must not be described as a globally complete repository artifact inventory.
- No L4 control is promoted. Aggregate L4-Minimum remains **BLOCKED / NOT VERIFIED**. Four source artifacts remain CI/synthetic evidence inside the GitHub failure domain.
- Next: enumerate relevant Actions workflow runs and artifacts from authoritative metadata, classify source evidence vs generated outputs, and reconcile eligible candidates. Keep the 40-file repository-source inventory separate. No key generation/signing, trust-root change, offline verification, VPS/SQLite access, artifact deletion or destructive action. Option C remains ACTIVE.


### Reconciliation report CI validation — run 42916283963

- Report source commit: `946e2b0d1da4ec35046ef3b37f4408f438dff27f`; report blob `ce2ccdb77b1a2f8eb4e9532f786813db0a1eb6b5`.
- Workflow run [42916283963](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42916283963), event `push`, branch `feature/t0-centralized-data-feeder-p1-20261101`, exact checkout SHA `946e2b0d1da4ec35046ef3b37f4408f438dff27f`, conclusion SUCCESS.
- Lineage job `130179444426`: 12/12 tests PASS.
- Artifact manifest job `130179520130`: 19/19 tests PASS.
- Repository-file inventory job `130179519980`: 10/10 tests PASS.
- Total: 41/41 tests PASS. All three jobs completed SUCCESS.
- Output lineage artifact `13810400590`, name `t0-l4-minimum-lineage-42916283963`, 1,151 bytes, expires `2026-11-17T22:37:35Z`, upload SHA-256 `3a77cdcd09328e5bfc54050110ddf7d2a2793d169f602a0f64f5ccc1b250f158`.
- Output repository inventory artifact `13809381785`, name `t0-l4-repository-file-inventory-42916283963`, 4,490 bytes, expires `2026-11-17T22:37:35Z`, upload SHA-256 `eb3c2adb7b6ee87bc5cadd913439e201e105c88c9d710f34605ac9cea882a884`.
- Output manifest artifact `13809057870`, name `t0-l4-artifact-manifest-42916283963`, 3,037 bytes, expires `2026-11-17T22:37:35Z`, upload SHA-256 `360554820e48d6a0fbe9d772e75fa37bc6582c0728a112217f9a6e4ab8caa9f0`.
- These are run outputs and are not silently added to the four-source allowlist. Their upload digests are recorded; independent ZIP payload re-hash for these three new outputs has not yet been completed.
- The handoff-only follow-up commit is `18d015d28ec054ce4198b4e637bd5a90cd157f59`; compare confirms exactly one file changed from the report commit: this handoff. The active branch now points to that handoff commit.
- Current gate: four-source archive/member verification PASS; 41/41 CI PASS on report commit; repository-wide eligible-run/artifact discovery remains NOT VERIFIED; aggregate L4-Minimum remains BLOCKED / NOT VERIFIED.
- Next: enumerate relevant workflow runs/artifacts comprehensively, then verify any additional eligible source payloads. Keep generated output artifacts separate. No signing keys, trust-root changes, offline verification, VPS/SQLite access or destructive actions.


### Independent readback of run 42916283963 output artifacts (2026-11-11)- Downloaded all three output ZIPs from run `42916283963` and independently recomputed their byte lengths and SHA-256 values; each matches the GitHub upload digest:
  - Lineage `13810400590`: 1,151 bytes; `3a77cdcd09328e5bfc54050110ddf7d2a2793d169f602a0f64f5ccc1b250f158`.
  - Repository inventory `13809381785`: 4,490 bytes; `eb3c2adb7b6ee87bc5cadd913439e201e105c88c9d710f34605ac9cea882a884`.
  - Artifact manifest `13809057870`: 3,037 bytes; `360554820e48d6a0fbe9d772e75fa37bc6582c0728a112217f9a6e4ab8caa9f0`.
- Repository inventory JSON SHA-256 `4b224d43b7ed8311307443907b80dad89536a2725e544372ba057b04c61972fc` matches its included sidecar.
- Artifact manifest JSON SHA-256 `58a9668f83679b650aab2d805759a55aaf7e99d8c9ce2222a0d3b2582b646626` matches its included sidecar.
- The three ZIP readbacks verify artifact-output transport integrity for this run. They do not independently prove completeness of the source artifact allowlist or owner custody.


### Complete T0 L4-Minimum workflow run/artifact discovery inventory (2026-11-11)

- Inventory report: `docs/evidence/T0_L4_ACTIONS_WORKFLOW_ARTIFACT_INVENTORY_2026-11-11.md`, created in commit `febb5ad8478d1334c13f32969a6cfae9e005656e`; report blob `1aaad4de534c2a8a8db91dcfb59743cc0878c50c`.
- Workflow ID `413351263`; repository Actions API total_count 4,442. Page 1 (100 runs) spans `2026-11-10T07:37:23Z` to `2026-11-10T22:37:35Z`, containing 32 runs of this workflow. Page 2's newest run is `2026-11-10T07:23:51Z`, earlier than the earliest target workflow run; it contains zero target runs. Reverse-chronological boundary establishes 32/32 observed runs for this workflow at query time.
- Exact source SHAs, run IDs, conclusions, timestamps and artifact counts for all 32 runs are in the report. 21 runs concluded SUCCESS and 11 FAILURE.
- Per-run artifact metadata inventory: 59 outputs — 32 lineage bundles, 18 manifest bundles, 9 repository-file inventories. IDs, sizes, expiry timestamps and GitHub-reported upload ZIP digests are recorded in the report.
- All 59 are generated outputs of the L4 workflow. The existing allowlist's two L4 lineage records (runs `42831240089`, `42836094887`) are selected historical CI outputs; the other 30 lineage outputs are not automatically added. Manifest and repository inventory artifacts are generated outputs, not owner-originated source evidence. The two P1.8.14 artifacts remain a separate source class.
- Important distinction: GitHub-reported upload digests for all 59 are metadata only; independent payload re-hash was not performed for all 59. Four allowlisted source archives and their 57 members were independently verified earlier. The three outputs of run `42916283963` were independently downloaded and re-hashed. 
- Inventory report commit `febb5ad8478d1334c13f32969a6cfae9e005656e` triggered validation run [42917592435](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42917592435), exact source SHA `febb5ad8478d1334c13f32969a6cfae9e005656e`. At handoff update time, lineage job `130183907628` SUCCESS; repository inventory job `130183969883` and artifact manifest job `130183970147` were IN_PROGRESS. Do not mark this run PASS until all jobs complete.
- Discovery result: **32-run L4 workflow inventory PASS**. Complete artifact inventory across every repository workflow remains NOT IN SCOPE / NOT VERIFIED. Independent payload verification of all 59 historical outputs remains NOT PERFORMED. Aggregate L4-Minimum remains BLOCKED / NOT VERIFIED.
- Next: assess whether any of the 30 other lineage bundles should be selected as historical CI provenance; if selected, independently download/re-hash before allowlist change. No allowlist expansion without explicit source/evidence-class rationale. No keys/signing, trust-root changes, offline verification, VPS/SQLite access, deletion, retention, cleanup or destructive action. Option C remains ACTIVE.


### L4 workflow/artifact inventory report validation — run 42917592435

- Inventory report source commit: `febb5ad8478d1334c13f32969a6cfae9e005656e`; report blob `1aaad4de534c2a8a8db91dcfb59743cc0878c50c`.
- Run [42917592435](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42917592435) completed SUCCESS on exact source SHA `febb5ad8478d1334c13f32969a6cfae9e005656e`.
- Lineage job `130183907628`: 12/12 PASS.
- Repository inventory job `130183969883`: 10/10 PASS.
- Artifact manifest job `130183970147`: 19/19 PASS.
- Total: 41/41 tests PASS; all three jobs SUCCESS.
- Output lineage artifact `13810855669`, 1,151 bytes, expiry `2026-11-17T22:46:23Z`, GitHub upload SHA-256 `83252ff9ec79730ecaa5dc13e6c7df9dca83824eaba8a0dbf94e3bcbefce838a`.
- Output manifest artifact `13809702884`, 3,038 bytes, same expiry, GitHub upload SHA-256 `049fe5bccd9d06b8ce3b3a8d3fc93ec1ab2249c636619d9c6b0530b0ee2bef87`.
- Output repository inventory artifact `13809019153`, 4,489 bytes, same expiry, GitHub upload SHA-256 `2544cabe52f6d2e6823d158788810fa22eac5ab258f2bbc0b41f0b21ea550a37`.
- These are generated outputs, not added to the source allowlist. Their upload digests have not yet been independently re-hashed.
- The workflow validation applies to report source commit, not the later handoff-only commits. The current branch HEAD is expected to move with this handoff update; verify after write.
- Gate: 32/32 L4 workflow runs inventoried; 59 outputs classified; CI validation 41/41 PASS. Independent payload re-hash of all 59 historical outputs remains NOT PERFORMED. Complete inventory of every workflow in the repository remains out of scope/not verified. Aggregate L4-Minimum remains BLOCKED / NOT VERIFIED.


### Latest successful lineage candidate review and allowlist refresh (2026-11-11)

- Independently downloaded latest prior successful lineage artifacts:
  - Run `42916283963`, source SHA `946e2b0d1da4ec35046ef3b37f4408f438dff27f`, artifact `13810400590`, ZIP 1,151 bytes, SHA-256 `3a77cdcd09328e5bfc54050110ddf7d2a2793d169f602a0f64f5ccc1b250f158`.
  - Run `42917592435`, source SHA `febb5ad8478d1334c13f32969a6cfae9e005656e`, artifact `13810855669`, ZIP 1,151 bytes, SHA-256 `83252ff9ec79730ecaa5dc13e6c7df9dca83824eaba8a0dbf94e3bcbefce838a`.
- Both archives contain exactly the four required lineage members. Each source marker matches its exact source SHA; scope marker is `T0_L4_MINIMUM_LINEAGE=GITHUB_HOSTED_READ_ONLY`; verdict is PASS; test log reports 12 tests and `OK`. Latest run `42917592435` is a more current successful lineage snapshot than the two lineage artifacts previously allowlisted.
- Verified source ancestry: `febb5ad8478d1334c13f32969a6cfae9e005656e` is an ancestor of prior branch HEAD `6a0df4d752438b622a43b43b3b47a654ca072adb` (`ahead_by=3`, `behind_by=0`).
- Added latest lineage artifact `13810855669` to `ci/l4-artifact-allowlist.json`; allowlist now has five entries. New allowlist blob `2fe01dbd2e3367db821f8e18503f965dc32fd42b`; commit `cab8122c94e8bb8f30052ae44483fb1ec7e4de65`.
- New allowlist entry is a CI lineage-contract output only. It does not constitute owner-held source evidence, independent custody, offline recovery, or control acceptance. The older lineage entries remain preserved; no historical record was deleted.
- Validation run [42917935285](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42917935285) is running on exact allowlist-update source SHA `cab8122c94e8bb8f30052ae44483fb1ec7e4de65`. At this handoff edit, lineage job `130185080754` SUCCESS; manifest job `130185161436` and repository inventory job `130185161572` still IN_PROGRESS. Do not claim PASS until run is complete.


### Latest lineage allowlist validation and five-entry manifest readback — run 42917935285

- Run [42917935285](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42917935285) completed SUCCESS on exact source SHA `cab8122c94e8bb8f30052ae44483fb1ec7e4de65`.
- Jobs/tests: lineage `130185080754` 12/12 PASS; manifest `130185161436` 19/19 PASS; repository inventory `130185161572` 10/10 PASS. Total 41/41.
- Manifest output artifact `13808799787`, 3,157 bytes, expires `2026-11-17T22:48:40Z`; independently downloaded ZIP SHA-256 `f498c08fa1076727eb39aef0ee1f80deffae51e29d2ac432c5fdc3a309fb8ff3`.
- Manifest JSON member: 11,153 bytes, SHA-256 `4853ccc243680a8a84d42ca2060a83fa6f9249ca5b04976c3065093fa0a40dde`; sidecar contains the same digest. JSON declares exactly five artifacts: two P1.8.14 synthetic CI records and three L4 lineage CI records (artifact IDs `13771662067`, `13774031418`, `13810855669`). No current-run output is self-included.
- Run output lineage artifact `13810187202`, 1,151 bytes, GitHub upload SHA-256 `db4e86e8b976304ae1daf90b14dc49cd2f4b149c9c2449867d796b515cd76d07`; repository inventory artifact `13810087972`, 4,487 bytes, upload SHA-256 `ca99e5b73f7b1574925ee6d57d15a3e30b322827f886b9247df3661343ba30d9`. Their upload digests are recorded but these two ZIPs have not yet been independently downloaded/re-hashed.
- New five-entry allowlist blob `2fe01dbd2e3367db821f8e18503f965dc32fd42b` passed manifest contract and actual GitHub artifact readback. This confirms the collector accepted the latest lineage artifact's run/SHA/name/ID/member markers and verified archive/member hashes at runtime.
- Allowlist refresh is a CI evidence-selection update only; it does not establish owner custody or upgrade any L4 control. Aggregate L4-Minimum remains BLOCKED / NOT VERIFIED.
- Next: assess whether the remaining 29 non-allowlisted lineage outputs have any distinct provenance value. Do not bulk-add them; only select a historical artifact if it contributes a distinct source/evidence class and verify its payload before any allowlist change. No keys/signing, trust-root changes, offline verification, VPS/SQLite access, deletion, cleanup or destructive actions; Option C remains ACTIVE.


### Six-entry lineage allowlist update and CI validation — 2026-11-11

- Candidate review report: `docs/evidence/T0_L4_LINEAGE_CANDIDATE_REVIEW_2026-11-11.md`, commit `4b4926944fa2548c0a7c29e7aa54c95fbdb13512`.
- Selected the newer successful lineage output from run `42917935285` because it records the exact source snapshot that introduced and validated the prior five-entry allowlist. This is still the existing `L4_LINEAGE_CONTRACT_CI` evidence class, not owner-held custody evidence.
- Candidate artifact `13810187202`, source SHA `cab8122c94e8bb8f30052ae44483fb1ec7e4de65`, 1,151 bytes; independently downloaded ZIP SHA-256 `db4e86e8b976304ae1daf90b14dc49cd2f4b149c9c2449867d796b515cd76d07`. Exact four members, matching source marker, scope `T0_L4_MINIMUM_LINEAGE=GITHUB_HOSTED_READ_ONLY`, verdict PASS, 12/12 tests.
- Allowlist update commit `0251a8cc7995903d2516fc84cc0a33b73ec02777`; new allowlist blob `0280cd7751c9660baec237242ca7aadef09205a6`; six entries total. All previous five entries preserved.
- CI run [42922670634](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42922670634), event `push`, exact checkout/source SHA `0251a8cc7995903d2516fc84cc0a33b73ec02777`, overall SUCCESS.
  - Lineage job `130201149131`: 12/12 PASS.
  - Repository inventory job `130201222951`: 10/10 PASS.
  - Artifact manifest job `130201223038`: 19/19 PASS.
  - Total 41/41 tests PASS.
- Current-run output artifacts independently downloaded and re-hashed:
  - Manifest `13813280057`: 3,269 bytes; ZIP SHA-256 `cc969116e687792321240e19cfa2125abfb8a884328e03715937746709b9b26d`. JSON member 12,001 bytes; SHA-256 `520fd49f87595cd39b412a0533ce579c8ead1456ad0361a712b52786bebad428`; sidecar matches. Exactly six source artifacts; no self-inclusion.
  - Lineage `13813120888`: 1,151 bytes; ZIP SHA-256 `4686edd0c1e80f4a5793aa8d79ac4ce232ee64bd59cee2bfa633c14afd3d29d1`; source marker matches `0251a8cc7995903d2516fc84cc0a33b73ec02777`; 12 tests; PASS.
  - Repository inventory `13811119271`: 4,490 bytes; ZIP SHA-256 `ab8944fe9edb3446a50df1b8041743e93bb6bb628dee70956913c54b862222da`; JSON sidecar matches; exact source commit `0251a8cc7995903d2516fc84cc0a33b73ec02777`; 40 paths / 518,716 bytes.
- The other historical lineage outputs remain unselected. Metadata shows the same generated lineage CI class; this does not claim every remaining archive was independently downloaded/member-rehashed. Their payload status remains NOT VERIFIED unless separately documented.
- Dispositions unchanged: no L4 control promoted; aggregate L4-Minimum remains BLOCKED / NOT VERIFIED. Option C — No Destructive Authority remains ACTIVE.
- Next: reconcile the six-entry allowlist/manifest with the current evidence register and control-to-source crosswalk. Then determine readiness for signature/negative-verification design only. No key generation/signing, trust-root change, offline verification, VPS/SQLite access, artifact deletion, retention change or destructive operation.


### Register-reference repair and latest crosswalk validation — 2026-11-11

- Root cause of the temporary lineage CI failures: the Evidence Register blob changed from `0125abfe77c0d0f9172e66aa5d09ec8fc8a33623` to `e67a58591b5f6168ab3a0f3f403557292aca45d5`, but `ci/test_t0_l4_minimum_lineage_contract.py` still pinned the old `REGISTER_SHA`. Runs [42922931718](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42922931718) and [42922961366](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42922961366) both reproduced the same assertion failure: expected old blob vs actual new blob; lineage 11/12, downstream jobs skipped.
- Corrected the test constant and synchronized the current register SHA in the Automation Plan and the L4M-02/L4M-08/L4M-10 supporting assessments. No test was skipped or weakened.
- Rebound `ci/l4-repository-file-inventory.json` to the new exact Git blob SHAs for the Register, Automation Plan and three supporting assessments. Current config blob: `95dd58f688b9ca14874613b1b94c5d5486d2e30f`.
- Latest exact-source validation of the synchronized docs/config: run [42923181975](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42923181975), source SHA `b9c2ebff7337420194f5c36a9523df28dbc6d4fc`, SUCCESS:
  - Lineage job `130202982454`: 12/12 PASS.
  - Artifact manifest job `130203053477`: 19/19 PASS; `L4_ARTIFACT_MANIFEST=PASS`.
  - Repository inventory job `130203053514`: 10/10 PASS; `L4_REPOSITORY_FILE_INVENTORY=PASS`.
  - Total 41/41.
- Run `42923181975` output artifacts independently downloaded/re-hashed:
  - Manifest `13813285687`: 3,266 bytes; ZIP SHA-256 `edcc77775e6dbe57248d87e484277dd79cf9103224c6b2e2ab05bce7bc0040cf`; JSON SHA-256 `18ed9d405bd68b3c137d56bccecf6f7f20b8b941deea8c0d7af4e3c1f97bc405`, sidecar matches; six inputs.
  - Repository inventory `13812812210`: 4,494 bytes; ZIP SHA-256 `d96efd8908f51c98160eb8089b175baa47c7695b2318555ce31fa1ab34b4f72b`; JSON SHA-256 `287398ccb0c9fbd76ea6b8316cd10748335f354e4e979fda5a36c62b2cbb2397`, sidecar matches; 40 files / 521,853 bytes; source SHA `b9c2ebff7337420194f5c36a9523df28dbc6d4fc`.
  - Lineage `13812403380`: 1,151 bytes; ZIP SHA-256 `2714104e7112fb7eac02e2ef6e00ed749f98be3e5259e4d70cc28d8379187291`; exact source marker, 12 tests, PASS.
- Updated the derived control-to-source crosswalk to point to the latest 40-file inventory and latest exact-source validation. Crosswalk blob: `b434ceb10b2c7ad5910802a6ea6de467a1769322`; commit `3ee50e77532ce5f55201c8736ad25b708915b871`. The six-entry allowlist and six-entry source manifest are unchanged.
- Crosswalk commit validation: run [42923379138](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42923379138), exact source SHA `3ee50e77532ce5f55201c8736ad25b708915b871`, all three jobs SUCCESS: lineage 12/12, manifest 19/19, repository inventory 10/10; total 41/41.
- Run `42923379138` outputs independently downloaded/re-hashed:
  - Lineage `13812917711`: 1,151 bytes; ZIP SHA-256 `69d36c6dcdce463d728cd79b9a4f76996d14023527470d7a1cbdcf808ad73930`; exact source marker `3ee50e77532ce5f55201c8736ad25b708915b871`; 12 tests; PASS.
  - Manifest `13812149048`: 3,267 bytes; ZIP SHA-256 `b84b1414ed9a2e9edcb9290d445ff361a96f4d738ff75c76edfa2c5ccb878afe`; JSON SHA-256 `444bb489964ddfca1ff437d7105c0ad0cc823cbbd8664f9bf2cd93a14f626428`, sidecar matches; exactly six source artifacts, no self-inclusion.
  - Repository inventory `13811464393`: 4,493 bytes; ZIP SHA-256 `5acbcf97ccf89fefae1a8e5f6af0e34b986c2a16177809d92fc0cc8f9fec0200`; JSON SHA-256 `d023c753582936faffad319a507630b49ae3d19df467658a8524eeb2e43007d2`, sidecar matches; 40 files / 521,853 bytes; exact source commit `3ee50e77532ce5f55201c8736ad25b708915b871`.
- The failures above were caused by a stale repository blob reference during evidence-document synchronization. The corrected exact-source runs are PASS; the failed historical runs remain visible and are not erased.
- No T0/VPS/SQLite/runtime access, key generation/signing, trust-root changes, offline verification, artifact deletion or destructive operation occurred. L4 control dispositions remain unchanged; aggregate L4-Minimum remains BLOCKED / NOT VERIFIED.
- Next: review whether the reconciled six-artifact manifest and 40-file source inventory are stable enough to start **signature/negative-verification design only**. Do not generate keys, sign, change trust roots or run offline verification without separate approval. Option C — No Destructive Authority remains ACTIVE.


### Owner decision — revoke Option C (No Destructive Authority) — 2026-11-11

- User explicitly instructed: **“thu hồi option c”**.
- Decision status: **Option C — No Destructive Authority: REVOKED** as of 2026-11-11.
- This supersedes earlier handoff statements that Option C remains ACTIVE. Do not continue treating Option C as an active blanket prohibition.
- Scope clarification: revoking Option C is a governance-state change, not an instruction to immediately delete data, clean up artifacts, alter retention, vacuum/compact databases, or run any other destructive operation. Each concrete operation must still have its target, exact scope, expected effect, recovery/rollback plan and explicit approval established before execution.
- Existing paper-only trading constraints remain unchanged: no live orders; `AI_EXECUTION_ENABLED=false`.
- T0 remains an independent data asset. Do not infer that canonical T0 data, owner evidence, GitHub artifacts or audit records are disposable merely because Option C was revoked.
- All prior L4 test results and control dispositions remain as recorded; revoking Option C does not itself promote L4 controls or establish custody/signature/offline-verification assurance.
- Next: update any active governance/evidence documents that still describe Option C as ACTIVE, preserving historical records and recording this revocation as a dated owner decision. No destructive action is authorized by this handoff update alone.


### Option C revocation synchronization and exact-source CI — 2026-11-11

- Owner revocation recorded in commit `22d8c01a86e1961e7a216ea90de751f680865c56`, handoff blob `12e9a7694e16a969ac5e542fb6aa36488d75b2d7`. Option C is REVOKED; earlier ACTIVE/in-force wording is historical and superseded.
- Added dated superseding governance notes to 37 relevant decision, lifecycle, L4, evidence, checkpoint, trust and custody documents. Historical source text was preserved; no old owner decision or test result was erased. The T0→T2 deployment parity reconciliation already states Option C REVOKED.
- Updated the 40-path repository inventory config to exact current Git blob SHAs. Latest config blob: `88835e2763f7053b2f41b2115cdd1b93e56cd255`. Latest matrix blob: `7c413504db397877b308345b21c9f6f58271c89a`; latest Evidence Register blob: `7ee8b11b47bec4bbd983f35e8f4a4d0f012c03bc`. Lineage test constants and Automation Plan/supporting references were synchronized to those exact blobs.
- Transient CI failures were not hidden:
  - Run `42936165865`, source SHA `c7a89bb64ac3ce731139e96771a98136fb89accf`: lineage 11/12 due stale matrix blob pin.
  - Run `42936425181`, source SHA `444ac7dd7f52c33b6b6b0fada6ec96c022f40d3a`: lineage 11/12 due stale register blob pin; repository inventory also exposed stale P1.8.147 inventory blob.
  - Corrected matrix/register pins and P1.8.147 inventory SHA; no test was removed or weakened.
- Final successful exact-source validation: run [42936903511](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42936903511), checkout/source SHA `2e66102ced45e7a59d8885026a29fa5e38dab01e`, all jobs SUCCESS:
  - Lineage: 12/12 PASS.
  - Artifact manifest: 19/19 PASS.
  - Repository-file inventory: 10/10 PASS.
  - Total: 41/41 PASS.
- Run `42936903511` artifacts downloaded and independently re-hashed:
  - Lineage artifact `13818891470`, 1,151 bytes; ZIP SHA-256 `a56b20af26c134e1d767ac2503dcd03c1fecfbaa7bab334edd0da55bffe2d531`; source marker exact; GitHub-hosted read-only scope; 12 tests; PASS.
  - Manifest artifact `13818887032`, 3,268 bytes; ZIP SHA-256 `69e55931705e387f60d8acd4093a713f00ba41b76256a4355674608be50ec6e9`; JSON member SHA-256 `f8954b20d2ce7c05318fcb220a07286c59f1119cfbdbfb6a60a6f7aaca7c95cf`, sidecar matches; exactly six source artifacts, no self-inclusion.
  - Repository inventory artifact `13818139442`, 4,482 bytes; ZIP SHA-256 `90866af79fc34e5eced9f552a4c178b211ca4490279ea472aa61fdb15c2e4dcb`; JSON member SHA-256 `5780dafa00ff6f7781ffa7dccd7f577901b71ef325845072d37c8931c5e21397`, sidecar matches; 40 paths / 559,566 bytes; exact source SHA `2e66102ced45e7a59d8885026a29fa5e38dab01e`.
- Updated control-to-source crosswalk: blob `b1f4daac9624d8deedfaf14234e0b6bb79ff81ca`, commit `8bda3c987e2145a636bbcc9d8609c5ea15a492b9`. It now records current matrix/register refs, latest 40-file inventory and run `42936903511`; aggregate L4-Minimum remains BLOCKED / NOT VERIFIED.
- No destructive operation, retention execution, artifact deletion, VPS/SQLite access, runtime change, key generation/signing, trust-root change or offline verification was performed. T0 remains an independent protected data asset; paper-only posture remains unchanged.
- Next: verify the post-crosswalk/post-handoff CI run on the final branch HEAD. After that, proceed only with signature/negative-verification design review; do not generate keys, sign, change trust roots or run offline verification without separate approval.


### Post-crosswalk validation — 2026-11-11

- Crosswalk commit `8bda3c987e2145a636bbcc9d8609c5ea15a492b9` was validated by run [42937191664](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42937191664), exact checkout/source SHA `8bda3c987e2145a636bbcc9d8609c5ea15a492b9`; all three jobs SUCCESS:
  - Lineage: 12/12 PASS.
  - Artifact manifest: 19/19 PASS; `L4_ARTIFACT_MANIFEST=PASS`.
  - Repository inventory: 10/10 PASS; `L4_REPOSITORY_FILE_INVENTORY=PASS`.
  - Total 41/41.
- Run `42937191664` outputs independently downloaded and re-hashed:
  - Lineage `13818967476`, 1,150 bytes; ZIP SHA-256 `155986f0f35d875fad02b6c50d0aab7aa43afdcd9191391f9ee0b832e975b67e`; exact source marker; 12 tests; PASS.
  - Manifest `13819680374`, 3,267 bytes; ZIP SHA-256 `3509f2ce14aa174a45e4200ab44d13c7ae532841a74886256e9f6fe20ea55f71`; JSON member SHA-256 `9bc86b32da5e2993729aac9f850ba15d2ff28274075a5ee2f5813119a0c5a0ef`, sidecar matches; exactly six source artifact IDs `13545287609`, `13546255148`, `13771662067`, `13774031418`, `13810187202`, `13810855669`.
  - Repository inventory `13818163804`, 4,483 bytes; ZIP SHA-256 `98fc7fca7123ae0a9e72bcf1f209032a57c24d97aa898aaa075eb7212f04c0fa`; JSON member SHA-256 `4f57be4a46cac1703135d43dd5a99cc3ffb7e56aa1d71d2bdd87ab87085b9f0b`, sidecar matches; 40 paths / 559,566 bytes; exact source commit `8bda3c987e2145a636bbcc9d8609c5ea15a492b9`.
- The latest handoff-only commit is not the source SHA tested by run `42937191664`; that run validates the crosswalk commit immediately preceding it. No source/runtime changes were made in the handoff-only update.
- Current governance status remains Option C REVOKED. Revocation is not blanket permission to perform any specific destructive action. L4 aggregate remains BLOCKED / NOT VERIFIED.


### Branch boundary snapshot — 2026-11-11

- Active branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Branch HEAD at comparison time: `49c5449c9b2a243bdcc3144265ec6debf1003872`.
- Compared with `main`: GitHub compare reports **DIVERGED**, 2,708 commits ahead and 55 behind; merge base `f5b74affb8777953fa66d241784965fbb0e577ba`.
- This divergence predates any merge/rebase action in this increment. No merge, rebase, force-push or branch switch was performed. Preserve the active branch and investigate divergence separately before any integration decision.
- The handoff-only update after run `42937191664` is not itself CI-tested; that run tested crosswalk commit `8bda3c987e2145a636bbcc9d8609c5ea15a492b9`. Do not claim CI tested the final handoff-only HEAD.


## Signature / negative-verification architecture review — 2026-11-11

- Read-only review report: `docs/evidence/T0_SIGNATURE_NEGATIVE_VERIFICATION_ARCHITECTURE_REVIEW_2026-11-11.md`.
- Review report commit: `805e4be31d741e76f21c6f2bdb367bdcc27197bd`.
- Exact source baseline reviewed: branch HEAD `167b8afea5a0c290b9edc22e8eead92715c3c4ad`; checkpoint contract blob `5948dd904e1819b626aecc1a85e10c95735191a3`; synthetic oracle blob `9efd800189e15d35e231530d703499d40d9d7e5d`; tests blob `beffd8c4a6cb2682c9fe0acb09cd2b182c2fde7c`; G2 workflow blob `5e22648c38fd3c6e631f912010de1489bb78f9b5`; crosswalk blob `b1f4daac9624d8deedfaf14234e0b6bb79ff81ca`.
- Findings: exact signature preimage missing; trust-policy/root bootstrap missing; replay/rollback protocol missing; object-ID uniqueness rule needs closure; historical signer trust needs trusted-time/revocation semantics; algorithm/profile negotiation not constrained; current G2 source/tests do not implement signatures or signature-negative cases; custody scope conflicts between checkpoint contract (outside VPS/GitHub) and accepted L4 crosswalk scope (VPS + GitHub only).
- Proposed design: sign the exact canonical Checkpoint Manifest Evidence Object digest through a detached, domain-separated canonical signature statement binding object ID/type/schema/digest/length, purpose, audience, checkpoint sequence/predecessor, signer fingerprint/role, fixed algorithm profile and authenticated trust-policy version/digest. Use a separately authenticated monotonic anchor for latestness; signature validity alone never establishes freshness.
- Proposed negative matrix: 26 cases covering signature corruption, wrong key, content mutation, digest/length/object-ID/type/schema substitution, purpose/audience confusion, algorithm downgrade, trust-policy bootstrap/rollback, key lifecycle, replay, anchor equivocation/rollback, local-clock backdating, offline missing trust material and verification-record overwrite.
- Review disposition: **DESIGN BASELINE PARTIAL; IMPLEMENTATION BLOCKED**. This was an adversarial second-pass static review, not a qualifying external/independent L4M-09 review. Formal independent review remains NOT VERIFIED.
- No code, test, workflow, runtime, VPS, SQLite, key, trust root, anchor, provider, TSA or retention operation was changed or executed. No implementation approval is requested or implied.
- Next permitted work: contract-only amendment resolving S-01–S-04 and identity/trust-time details, followed by frozen test matrix and a qualifying independent review. Do not implement until a separate explicit owner approval after review.


## Signature / Trust Policy / Monotonic Anchor contract amendment A1 — 2026-11-11

- Amendment: `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A1_2026-11-11.md`.
- Amendment commit: `ac2849764bc45122a6b17cfe9cc7ef40000e1edd`; exact file blob: `91727c8f0409fd0e6e0df0c0420e459f54bd601b`; 29,834 characters.
- Base architecture review report remains `docs/evidence/T0_SIGNATURE_NEGATIVE_VERIFICATION_ARCHITECTURE_REVIEW_2026-11-11.md`; review report commit `805e4be31d741e76f21c6f2bdb367bdcc27197bd`.
- Amendment defines: exact canonical Signature Statement preimage and detached envelope; immutable Evidence Object ID-to-type/schema/profile/digest/length binding; versioned Trust Policy, pinned-root bootstrap, signer authorization, policy sequence/rollback, key status and historical trust-time limits; separately signed Monotonic Anchor, strict sequence/predecessor rules, duplicate/equivocation/replay handling; deterministic verification order and 30 negative cases.
- Custody conflict S-04 is reconciled as a bounded claim: approved scope VPS + GitHub only. Exact dual-copy agreement can establish consistency with the retained anchor head, but cannot detect a joint rollback of both stores. Absolute/global anti-rollback and independent external custody remain NOT ESTABLISHED. No WORM or external-backup claim.
- Owner decisions still open: production algorithm/profile, root bootstrap/recovery ceremony, signer and anchor-authority identities, anchor concurrency mechanism, acceptance of the bounded custody limitation versus future external anchor, and trusted-time/TSA requirements.
- Amendment status: **DRAFT / CONTRACT-ONLY / NOT APPROVED FOR IMPLEMENTATION**. It has not received an independent review. Implementation remains BLOCKED pending frozen-contract independent review and separate explicit owner approval.
- No code/tests/workflows/CI/runtime/VPS/SQLite/canonical T0 data/keys/trust roots/policy instances/anchor records/providers/TSA/retention or destructive operations were changed or exercised. No CI run or artifact is claimed for this documentation increment.
- Next: perform a contract consistency review against base contract v1 and the L4 crosswalk, then freeze the amendment for qualifying independent review. Do not implement or generate keys/signatures/anchors.


### Amendment A1 byte-level closure — 2026-11-11

- Amendment follow-up commit: `15c4c91b2c26fe748b44af8acbb27b088e0642f7`; latest amendment blob: `d462729446d3b4c5016b43cbe1bc5b339cbcd74e`.
- Added exact domain-separated, length-prefixed SHA-256 formula for Trust Policy body; defined detached `T0-TRUST-POLICY-STATEMENT-V1` and its exact signature preimage/envelope; defined genesis and subsequent policy sequence/predecessor rules; defined canonical anchor envelope and exact anchor-object digest used by the next anchor's predecessor link.
- The earlier amendment blob `91727c8f0409fd0e6e0df0c0420e459f54bd601b` is superseded by this byte-level closure. Latest contract text is the blob recorded above.
- Production signature algorithm remains deliberately unselected. This amendment is still DRAFT, not independently reviewed and not approved for implementation.


## Signature amendment A1 cross-contract consistency review — 2026-11-11

- Updated amendment: `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A1_2026-11-11.md`.
- Consistency-review commit: `9941c6fe890be32cd87b37f3051e496527f264d6`; latest amendment blob: `ca0e73778c3e1430f1d9e8ac4aaa90721bfc113a`.
- Re-read governing Checkpoint Contract v1 blob `5948dd904e1819b626aecc1a85e10c95735191a3`, L4 crosswalk blob `b1f4daac9624d8deedfaf14234e0b6bb79ff81ca`, latest amendment and this handoff.
- Findings/corrections recorded: (CR-01) A1 cannot unilaterally supersede v1's outside-both VPS/GitHub custody requirement; VPS + GitHub-only is now explicitly a proposed alternative requiring owner ratification, and v1 remains controlling until formal amendment. (CR-02) Trust Policy body excludes its own digest/signature; detached statement/descriptor carries digest. (CR-03) all logical integers serialize as canonical unsigned decimal strings under T0-JCS-1. (CR-04) binary envelope fields use strict unpadded base64url. (CR-05) v1 signing provenance/authorization fields are mapped to signed statement or separately signed referenced evidence; post-signing verification references remain in append-only Verification Records. (CR-06) anchor Evidence Object descriptor and custody receipt/readback requirements remain unless owner formally amends v1.
- Consistency-review disposition: **PARTIAL / NOT FROZEN**. CR-01 remains an owner decision; production signature algorithm/profile, root ceremony, signer/anchor identities and trusted-time/TSA decisions remain open. This was same-session static review, not qualifying independent review.
- No implementation, code/test/workflow/CI/runtime/VPS/SQLite/key/trust-root/policy/anchor/provider/TSA/destructive action occurred. No CI run/artifact is claimed.
- Next: obtain explicit owner disposition on whether to formally amend Checkpoint Contract v1's outside-both custody requirement. Until then, v1 governs that claim and A1 cannot be frozen as a fully reconciled contract. After owner disposition, perform final contract freeze and qualifying independent review; implementation still requires separate approval.

### Amendment A1 branch correction — 2026-11-11

- The first consistency-review amendment update commit `9941c6fe890be32cd87b37f3051e496527f264d6` was created without an explicit branch argument and is not the active feature-branch version; do not use it as the branch baseline. It is a duplicate documentation commit on the repository default branch and has not been treated as approval or merge of the active work.
- Corrected active-branch amendment commit: `397ff689d9d19d3f3c7f72f2b4bc3c4c4314a9c0`; amendment blob: `ced2b7cf0c74910aed4b8d6d761d76f0b7739e27`.
- Active-branch handoff must point to this commit/blob. The default-branch duplicate was not reverted; no history rewrite or force-push was performed.
- This branch correction does not change the disposition: A1 remains DRAFT / NOT FROZEN; CR-01 custody precedence requires explicit owner decision; independent review and implementation approval remain outstanding.

## Owner approval — Checkpoint Contract v1 bounded custody amendment (2026-11-11)

- Owner explicitly approved formally amending Checkpoint Contract v1 §§7/9 to accept **VPS + GitHub as the bounded two-location custody scope**.
- The owner explicitly accepts that joint rollback/replacement of both VPS and GitHub to the same older valid chain is not detectable by this design. Permitted assurance is limited to exact two-location consistency with the authenticated retained anchor history available to the verifier. No external custody, WORM, global latestness, absolute anti-rollback or universal rollback-detection claim is permitted.
- Formal contract addendum appended to `docs/architecture/T0_EVIDENCE_OBJECT_CHECKPOINT_CONTRACT_V1.md`: commit `2fc8c3bfde08bd2b95542d20981b99321d42dbe4`; blob `2d95aaeba9d7d6d388f3d5941be6f051d40111f6`.
- Signature amendment A1 §14.1 and disposition reconciled with owner decision: commit `6baed29b63ddaa31cd390ede3e690e2211d3e21a`; blob `22fb42ba201f9105c8e612ca9b4695f6a0519382`.
- L4 control-to-source crosswalk updated to record the bounded custody scope and assurance limitation: commit `be003f35c79934833e3edbfd1af1a5da9eae0f2d`; blob `9781c299a8fd5536a9a1ff03b703ff6a5ff3dc49`.
- This resolves CR-01 at owner-governance/contract level. It does not promote any L4 control. L4-Minimum remains BLOCKED / NOT VERIFIED pending actual per-location custody evidence/readback, signer/anchor separation, authenticated trust bootstrap, signed anchor-chain verification, offline verification and separate owner acceptance.
- A1 remains DRAFT / NOT FROZEN pending final consistency verification and qualifying independent review. The prior static consistency review is not an independent review. Production algorithm/profile, root ceremony, signer/anchor identities, anchor concurrency and trusted-time/TSA decisions remain open.- No implementation, code/test/workflow/CI, key generation/signing, trust-root/policy/anchor instance, provider, VPS/SSH/runtime, SQLite or canonical T0 data operation was performed or authorized. No destructive action was authorized.- Next permitted step: re-read the amended contract, A1 and crosswalk for exact consistency; then request a qualifying independent review of the frozen contract and negative-verification test matrix. Implementation remains blocked pending that review and a separate explicit approval.


## Signature contract final consistency review — frozen review candidate (2026-11-11)

- Read-only final consistency review report: `docs/evidence/T0_SIGNATURE_CONTRACT_FINAL_CONSISTENCY_REVIEW_2026-11-11.md`; active-branch commit `cce3869098644cf35411e2fc98083f1c5f01444b`; exact report blob `8304e8e3c9f396d1baac11f851af17a173c91157`.
- Frozen review source snapshot (before report/handoff commits): branch HEAD `887f5ed6a71c31c5412e061bef58695323903512`.
  - Checkpoint Contract v1 + owner-approved custody addendum blob: `a6825270d59bde274bfe765d5f942144b66a84de`.
  - Signature Amendment A1 blob: `d8643e52a874c406339dad8f62bfe3a9ecda0577`.
  - L4 crosswalk blob: `28689ea74a4047e11e51e80e61fd0123ff424aa0`.
- Final consistency corrections closed: stale pending-owner language in A1 §2.1/§11/§14; harmonized contract §13.2 G1 custody rows; clarified §7 outage/readback scope for the bounded two-location custody; refreshed L4M-03 source pins; preserved the initial G1 A no-signer boundary while treating A1 as a separate signature/trust extension.
- Static checks: current contract/A1/crosswalk blob pins match; A1 pending-ratification language absent; A1 includes 30 negative cases; bounded joint-rollback and both-locations-unavailable limitations explicit; aggregate L4-Minimum remains BLOCKED / NOT VERIFIED.
- Review disposition: **CROSS-DOCUMENT CONSISTENCY PASS; REVIEW CANDIDATE FROZEN FOR INDEPENDENT REVIEW**. This is same-session static review, not independent assurance.
- Qualifying independent review: **NOT REQUESTED / NOT VERIFIED** because no reviewer identity or review channel is designated. The reviewer must be independent of document authors/editors and relevant T0/signing/trust/anchor/custody operators; must disclose identity, competence and conflicts; and must review the exact three source blobs pinned in the report.
- General L4M-09 remains OWNER-WAIVED for the L4 baseline. This does not waive the separate independent review requested for the signature architecture before implementation.
- Open implementation blockers: production signature algorithm/profile; owner-pinned root bootstrap/recovery; actual signer and anchor identities; atomic anchor concurrency mechanism; trusted-time/TSA decision; exact signed provenance/authorization field mapping; policy/anchor retention/recovery; independent byte-vector implementation; verifier and all 30 negative tests; offline integration and actual owner-copy readback.
- No code/tests/workflow/CI, keys/signatures/trust-root/policy/anchor instances, provider/TSA, VPS/SSH/runtime, SQLite/canonical T0 data or destructive operation was changed or exercised. No implementation approval is implied.
- Next: designate a qualifying independent reviewer (identity/channel) and send the frozen review packet. Do not edit the frozen source blobs during review; any required correction creates a new snapshot and restarts review. Implementation remains blocked pending review and separate explicit owner approval.
- Branch hygiene: the first report-file create action landed on `main` because the optional branch was omitted; it was not reverted or treated as active-branch evidence. The same report was then created explicitly on this active branch in commit `cce3869098644cf35411e2fc98083f1c5f01444b`. No merge/rebase/force-push was performed.


## Signature contract review snapshot — final source pin refresh (2026-11-11)

- The review candidate was tightened after final consistency inspection: A1 §2.1 and §6.4 now use MUST (not SHOULD) for retaining/publishing the exact anchor record and predecessor chain at both approved custody locations, matching the owner-approved base contract. No publication/readback was performed.
- Final frozen source snapshot HEAD: `838f912139562eb185ad6035e95fd08810071525` (the report-only commit `9250134f9caf73674c28fa02fa848f91d6cc2f76` records that exact snapshot and does not alter the three frozen source documents).
  - Checkpoint Contract blob: `a6825270d59bde274bfe765d5f942144b66a84de`.
  - Amendment A1 blob: `00fdad293e129562145ab930507a4e6b9c2bf23d`.
  - L4 Crosswalk blob: `e560f084642b5f81c78179ef673e5df116fc5f42`.
- Final consistency report updated: `docs/evidence/T0_SIGNATURE_CONTRACT_FINAL_CONSISTENCY_REVIEW_2026-11-11.md`, commit `9250134f9caf73674c28fa02fa848f91d6cc2f76`, blob `80d42aa9b2f51efa9037656f958c86d91eeebe6c`. It records FC-08 and the exact final source pins.
- Exact-pin and rule checks: `{"reportPinsContract":true,"reportPinsAmendment":true,"reportPinsCrosswalk":true,"crosswalkPinsContract":true,"crosswalkPinsAmendment":true,"a1AnchorMustBoth":true,"a1NoPendingApproval":true,"a1NegativeCases":true,"contractReadbackBothUnavailableSuperseded":true,"aggregateBlocked":true}`.
- Independent reviewer still not designated; review request remains NOT REQUESTED / NOT VERIFIED. Frozen source documents must not be edited during review; any required change creates a new snapshot.


## Adversarial self-review of frozen signature contract candidate (2026-11-11)

- Review report: `docs/evidence/T0_SIGNATURE_CONTRACT_SELF_REVIEW_2026-11-11.md`; commit `1d7ad5b5eaaac62ccfa01b98a1ff3968e9ef178c`; blob `d7ff88b4a5fadbf08ae8fdc62e76fdd6274e89ce`.
- Reviewed exact frozen source snapshot `838f912139562eb185ad6035e95fd08810071525`: contract blob `a6825270d59bde274bfe765d5f942144b66a84de`; A1 blob `00fdad293e129562145ab930507a4e6b9c2bf23d`; crosswalk blob `e560f084642b5f81c78179ef673e5df116fc5f42`.
- Self-review disposition: **REQUEST CHANGES** before treating A1 as implementation-ready. Findings: SR-01 HIGH owner-attestation purpose lacks explicit owner delegation/intent binding; SR-02 HIGH provenance/authorization and signature-envelope ID fields lack concrete schema mapping; SR-03 HIGH anchor compare-and-advance/two-location publication lacks crash-consistent commit/recovery protocol; SR-04 HIGH negative cases allow ambiguous outcomes without stable reason codes; SR-05 MEDIUM U64/base64url boundary rules need explicit range/vectors; SR-06 MEDIUM NV-28 is an assurance limitation, not a detection test; SR-07 MEDIUM distinguish byte-frozen review snapshot from normative A1 draft status; SR-08 MEDIUM bootstrap record/public-key provisioning is underspecified.
- Frozen source documents were not modified. The self-review report is a separate artifact and does not replace or satisfy qualifying independent review/G3. It is a same-session adversarial review, not independent assurance.
- Current implementation status remains **BLOCKED**. No code/tests/workflow/CI, key/signature/trust-root/policy/anchor instance, provider/TSA, VPS/SSH/runtime, SQLite/canonical T0 data or destructive operation was changed or exercised.
- Next permitted documentation step: prepare A2/new candidate that addresses SR-01–SR-08 and expands deterministic test vectors/matrix; preserve A1 frozen blobs for traceability. Then repeat self-review. Qualifying independent review and separate owner implementation approval remain required.


## A2 signature-contract correction candidate drafted (2026-11-11)

- User explicitly approved drafting A2 as a documentation-only correction candidate. This is not implementation approval.
- A2 path: `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A2_2026-11-11.md`.
- A2 current blob: `d76e382f5582530d4607e2cf36003e55e313cb64`; latest A2 update commit: `2f8f8e35af9c60ff9b9ae2a0f8983a078346f471`.
- Initial A2 create commit: `3925f720a5cd531333c67d22a931c6a0d2a2de63`; the deterministic-test correction is the subsequent commit above.
- A2 is a new candidate and leaves A1 unchanged. A1 blob remains `00fdad293e129562145ab930507a4e6b9c2bf23d`; self-review report blob remains `d7ff88b4a5fadbf08ae8fdc62e76fdd6274e89ce`.
- A2 addresses SR-01–SR-08 at contract-design level: changes checkpoint purpose to issuer attestation (no implied owner intent); defines explicit provenance/authorization fields and envelope identity; specifies a durable anchor transition state machine and crash recovery; makes negative tests deterministic; separates common-mode rollback limitation from detection tests; defines U64/base64url primitives and boundary vectors; distinguishes byte-frozen review candidate from draft approval; specifies owner-pinned bootstrap record and out-of-band key pinning.
- A2 negative matrix currently has A2-NV-01 through A2-NV-43. A2-NV-40 is a stateful recovery test with pre-/post-recovery assertions; A2-NV-33 and A2-NV-43 isolate missing authority evidence versus digest mismatch.
- Status: **DRAFT A2 — DOCUMENTATION ONLY — NOT IMPLEMENTATION-APPROVED — NOT INDEPENDENTLY REVIEWED**. The user-approved scope was limited to drafting A2. Do not create keys, signatures, trust roots, policy/anchor instances; do not implement or exercise runtime/VPS/SQLite/T0/provider operations.
- Next: adversarial self-review A2 against the exact current A2 blob and A1/base-contract/crosswalk source pins; record findings without mutating the reviewed candidate. If corrections are required, create a new A2 candidate revision and re-review. Qualifying independent review and separate implementation approval remain mandatory.


## A2 adversarial self-review result (2026-11-11)

- Self-review report: `docs/evidence/T0_SIGNATURE_CONTRACT_A2_SELF_REVIEW_2026-11-11.md`; report commit `a1781226db723b6edd2b24aaf64c810cb61d395f`; blob `c65f94165c0df0e323daf78ba77fdb5e88480fcd`.
- Exact reviewed A2 blob: `e15a90b779bd86b39729208db938e9de9471ef26`. Other source pins: A1 `00fdad293e129562145ab930507a4e6b9c2bf23d`; Checkpoint Contract v1 `a6825270d59bde274bfe765d5f942144b66a84de`; L4 crosswalk `e560f084642b5f81c78179ef673e5df116fc5f42`.
- Static content checks: all A2-NV-01..43 present; no malformed escaped newline; issuer-attestation/owner-authorization boundary, provenance fields, anchor transition states/linearization point, U64/base64url vectors and bootstrap schema present. These are document checks, not executable tests.
- Prior SR-01–SR-07 are addressed at draft contract level; SR-08 is partial. New findings: A2-SR-01 HIGH — A2 verifier/Trust Policy does not explicitly reject legacy owner-attestation purpose for A2 objects; A2-SR-02 MEDIUM — bootstrap owner-authorization evidence lacks a fully independent verification contract and could be circular if the enrolled root authenticates its own enrollment.
- Disposition: **REQUEST CHANGES**. Preserve the reviewed A2 blob. Any fix must create a new A2 candidate blob and repeat self-review. This same-session review is not independent and does not satisfy G3.
- Implementation remains **BLOCKED**. User approval covered documentation-only A2 drafting, not implementation. No code/tests/workflow/CI, keys/signatures/trust roots/policy/anchor instances, provider/TSA, VPS/SSH/runtime, SQLite/canonical T0 data or destructive operation was changed or exercised.
- Next permitted step: prepare A2 correction for A2-SR-01/02, then self-review the new exact blob. Qualifying independent review and separate explicit implementation approval remain required.


## A2.1 signature-contract correction and self-review — 2026-11-11

- User explicitly approved **documentation-only A2.1 drafting** to address A2 self-review findings A2-SR-01 and A2-SR-02. This approval does not authorize implementation.
- New candidate: `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A2_1_2026-11-11.md`.
- A2.1 create commit: `d4112dff435e115b474c581ce2c6f4c96e36536f`; clarification commit: `b319dc17046c4d6a53a099fd9398efa69c147ebf`; final A2.1 blob: `73ba6fd9f6bb862121842f7a1347fffc06738451`.- Historical A2 remains unchanged at blob `e15a90b779bd86b39729208db938e9de9471ef26`; A1 `00fdad293e129562145ab930507a4e6b9c2bf23d`; Checkpoint Contract v1 `a6825270d59bde274bfe765d5f942144b66a84de`; L4 crosswalk `e560f084642b5f81c78179ef673e5df116fc5f42`. All four were re-fetched from the active branch after A2.1 drafting and matched these exact blobs.
- A2-SR-01 correction: A2.1 Trust Policy MUST explicitly authorize only `T0_CHECKPOINT_ISSUER_ATTESTATION` for A2.1 checkpoint objects; legacy `T0_CHECKPOINT_OWNER_ATTESTATION` is rejected with `PURPOSE_NOT_SUPPORTED_BY_PROFILE`; historical A1 verification requires explicit A1 profile; no relabel, silent upgrade or downgrade. Four new negative cases A2.1-NV-01..04.- A2-SR-02 correction: defines `T0-TRUST-BOOTSTRAP-AUTHORIZATION-V1` and binds exact bootstrap digest/length, namespace, audience, root SPKI fingerprint, role, profile, sequence and recovery policy. Path A uses separately pre-pinned owner authority but is unavailable until its own canonical schema/preimage/profile/revocation contract is separately approved. Path B uses an owner-controlled provisioning ceremony whose exact canonical record is identified by the bootstrap record's owner-authorization evidence ID/digest and pinned/read back through an independent verifier-provisioning channel. Newly enrolled root cannot authenticate its own enrollment. Five new negative cases A2.1-NV-05..09.
- Self-review report: `docs/evidence/T0_SIGNATURE_CONTRACT_A2_1_SELF_REVIEW_2026-11-11.md`; create commit `61d65d7a242be49466e74a52d1554120c868c876`; final report commit `5e22dbb3ff53a588f8121200e3b5a2a69316a25a`; report blob `9fa179c9daf657880533eb69394b42cdb644fa0b`.
- Static source checks: PASS for legacy-purpose rejection and downgrade rules, bootstrap authorization schema/context bindings, independent Path A/Path B definitions, non-circular enrollment, fail-closed reason codes, all 9 A2.1 negative cases and inherited A2-NV-01..43. Separately re-fetched historical A2/A1/base-contract/crosswalk blobs match exact pins. These are document consistency checks only; no executable or cryptographic conformance tests.
- Self-review disposition: **PASS WITH RESIDUAL GATES — READY FOR QUALIFYING INDEPENDENT REVIEW**. This is same-session self-review, not independent assurance/G3.
- Remaining gates: Path A requires a separate contract; Path B requires actual owner-controlled ceremony and independently evidenced verifier pin/readback; production algorithm/profile, owner authority, root custody/recovery, signer/anchor authority and operational implementation remain unselected/unverified. Qualifying independent review of exact A2.1 blob and separate explicit implementation approval remain mandatory.
- Status: **DRAFT / DOCUMENTATION ONLY / NOT IMPLEMENTATION-APPROVED**. CI/workflow **NOT RUN** for this increment; no workflow run or artifact claimed.
- No code/tests/workflow/CI, keys/signatures/trust roots/policy/anchor instances, provider/TSA, VPS/SSH/runtime, SQLite/canonical T0 data or destructive operation was changed or exercised. Paper-only posture and `AI_EXECUTION_ENABLED=false` unchanged.
- Next: designate a qualifying independent reviewer and provide the exact A2.1 blob plus pinned base documents. Do not implement, generate keys/signatures, instantiate trust policy/anchor or exercise VPS/T0 until separately approved.


## A2.1 second adversarial self-review — 2026-11-11

- User requested a second self-review of A2.1. Exact reviewed source remains `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A2_1_2026-11-11.md`, blob `73ba6fd9f6bb862121842f7a1347fffc06738451`.
- Second review report: `docs/evidence/T0_SIGNATURE_CONTRACT_A2_1_SECOND_SELF_REVIEW_2026-11-11.md`; commit `ec0e34bb7acd260a34390f739dec1e1808087c5f`.
- Disposition: **REQUEST CHANGES — NOT READY FOR INDEPENDENT REVIEW**. This is a same-session adversarial review, not independent assurance.
- Findings:
  - **A2.1-R2-01 HIGH:** status/gate references are stale or contradictory: §13 says self-review pending although prior report exists; §10 still refers to freezing/reviewing A2 rather than A2.1; §1.3 calls A2 the new candidate.
  - **A2.1-R2-02 HIGH:** Path B lacks a fully specified independently verifiable owner/operator provisioning trust model. The ceremony record is not self-authenticating, but the verifier channel, operator authorization/authentication, and pre-existing verifier trust boundary are not fully defined.
  - **A2.1-R2-03 HIGH:** §12.3 verdict/reason mapping is ambiguous across Path A and Path B; signature-specific rules do not directly fit unsigned Path B ceremony evidence, and BLOCKED vs UNKNOWN precedence is unclear.
  - **A2.1-R2-04 HIGH:** A2.1-NV-01..09 do not consistently meet inherited §5.1 deterministic fixture assertions; NV-06 combines multiple independent mismatches and should be split.
  - **A2.1-R2-05 MEDIUM:** “A2.1 profile” lacks an exact machine-readable profile ID/version bound consistently to signed descriptor, Signature Statement, Trust Policy and verifier request.
- A2-SR-01 purpose rejection is substantially addressed. A2-SR-02 remains only partially addressed: Path A is unavailable pending a separate contract; Path B needs its trust boundary/owner authorization contract made explicit.
- Historical A2/A1/Checkpoint Contract/crosswalk source blobs remain unchanged. No A2.1 correction was made in this review; only the review report and this Handoff were added.
- Status: A2.1 **REQUEST CHANGES**; independent review **NOT PERFORMED / NOT VERIFIED**; implementation **BLOCKED**; CI/workflow **NOT RUN**.
- Next step, if approved: prepare a new A2.2 documentation-only candidate addressing R2-01..R2-05, then run a fresh adversarial self-review. Do not implement or instantiate trust/bootstrap/anchor until independent review and separate explicit implementation approval.



## A2.2 signature-contract correction and adversarial self-review — 2026-11-11
- User said "tiếp theo" following the proposal to prepare a new A2.2 documentation-only candidate; work was limited to drafting and self-review. No implementation approval is implied.
- New candidate: `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A2_2_2026-11-11.md`.
- A2.2 create commit: `c3bf12457d5d81ec0e4a86c279c2e5f75b821e02`. Subsequent documentation correction commits: `6c91b7e709888afa147bc4fb5c359a59e965c572`, `56d698148c18cce2ede624f75cfb2c32098195dd`, `4b1bb83ae6aa17c8676a228d273dce222948ff3c`, `67122890358691aee25f3233448023984b3818df`, `bfb27bd11a8665248d9afea505baa52e8899fed1`, `94eb0bb578391f429b4f6a4eab1c3c23922ffad4`, `e02971b1ce4d6ee16b3782b1dcd41f4cc69b127a`, final fixture clarification commit `3a3bbcb802f72904e789e4f6a94bc64986fc3bee`.
- Final A2.2 blob: `2090112370e3b4a9925e78cf1ab0e2bb8428640c`.
- A2.2 addresses A2.1 second-review findings R2-01..R2-05:
  - R2-01: current candidate/revision identity and status evidence are explicit; mutable review gates are tracked by exact-blob reports, not stale labels.
  - R2-02: Path B is explicitly NOT_ENABLED until a separate owner-approved Verifier Provisioning Authority Contract defines the verifier administrative trust anchor, operator authorization, authenticated channel, transaction, audit and independent readback. Path A also remains NOT_ENABLED pending its separate owner-authority contract/pin evidence. Bootstrap is deliberately BLOCKED; no root enrollment is possible under this draft.
  - R2-03: ordered 18-row bootstrap verdict table defines first-match precedence and deterministic BLOCKED/INVALID/UNKNOWN outcomes. Failed results cannot mutate trust root, policy head, anchor head, accepted checkpoint head or bootstrap sequence.
  - R2-04: 27 unique A2.2-NV fixtures specify exact B0/B-A/B0-PF baselines, one semantic mutation, per-dimension and aggregate result, primary reason and state/forbidden-transition assertions. Historical A2.1-NV-01..09 and inherited A2-NV-01..43 remain preserved. Signed fixture dependent artifacts are regenerated where needed to isolate the intended verification layer.
  - R2-05: immutable machine profile ID `T0-CHECKPOINT-ISSUER-SIGNATURE-PROFILE-V2`, version `2`, bound across descriptor, Signature Statement, envelope, Trust Policy, bootstrap artifacts when enabled and verifier request/configuration; lifecycle and downgrade reason codes are defined.
- Self-review report: `docs/evidence/T0_SIGNATURE_CONTRACT_A2_2_SELF_REVIEW_2026-11-11.md`; report commit `605b1ec5b25619f218906952ee43d2bceaa6b222`; report blob `1b979dfe9794f2fb39a184fabfbbe535c80be15a`.
- Static document checks: PASS for candidate/status consistency, 27 unique A2.2 fixtures, preservation of 9 A2.1 identifiers, exact profile identity/bindings/lifecycle, disabled bootstrap paths, Path B trust-boundary prerequisites, 18 deterministic verdict reason codes, single-mutation/state invariants and unchanged implementation boundaries. These are document checks only, not executable or cryptographic conformance tests.
- Self-review disposition: **PASS WITH RESIDUAL GATES — READY FOR QUALIFYING INDEPENDENT REVIEW** for the exact A2.2 blob above. Same-session review is not independent assurance/G3.
- Pinned review dependencies: A2.1 `73ba6fd9f6bb862121842f7a1347fffc06738451`; A2 `e15a90b779bd86b39729208db938e9de9471ef26`; A1 `00fdad293e129562145ab930507a4e6b9c2bf23d`; Checkpoint Contract v1 `a6825270d59bde274bfe765d5f942144b66a84de`; L4 crosswalk `e560f084642b5f81c78179ef673e5df116fc5f42`; A2.1 second self-review `e531b2d65f4872cf1355f6c3105e2403da4e5496`.
- Residual gates: Path A and B both remain disabled; no owner authority, administrative trust anchor, operator identity, authenticated provisioning channel, bootstrap pin, production signature algorithm/key, signer custody or anchor authority is selected or verified. Qualifying independent review of exact A2.2 blob and separate explicit owner implementation approval remain mandatory.
- Status: **DRAFT / DOCUMENTATION ONLY / SELF-REVIEW PASS / INDEPENDENT REVIEW NOT VERIFIED / IMPLEMENTATION BLOCKED**. CI/workflow **NOT RUN**; no run or artifact claimed.
- No code, executable tests, workflow/CI, keys/signatures/trust roots/bootstrap, policy/anchor instances, provider/TSA, VPS/SSH/runtime, SQLite/canonical T0 data or destructive operation was changed or exercised. Paper-only posture and `AI_EXECUTION_ENABLED=false` unchanged.
- Next: submit exact A2.2 blob and pinned dependencies to a qualifying independent reviewer. Do not implement, generate keys/signatures, bootstrap trust, instantiate policy/anchor or exercise VPS/T0 without separate explicit approval.


## Owner waiver: independent review no longer mandatory for A2.2 — 2026-11-11

- Owner instruction: "thu hồi quyết định cần Independent review". Recorded as a governance waiver limited to A2.2 and its pinned review dependencies.
- Decision record: `docs/evidence/OWNER_DECISION_WAIVE_INDEPENDENT_REVIEW_A2_2_2026-11-11.md`; commit `4a43ea7c0521b6670842df23e3ef8dad0c1f1b92`.
- The waiver withdraws the prior requirement for a qualifying independent review before A2.2 may proceed to the next owner-controlled decision gate. Independent review is **WAIVED / NOT PERFORMED**; this is not independent assurance/G3.
- A2.2 updated to remove the mandatory independent-review gate and point to the owner waiver:
  - Update commit: `bd9736cc50b0944283bf1693e619ddb446138dff`.
  - Current A2.2 blob: `f9138497e4b3d846260fef3c88c88d89e2ee1123`.
  - Technical clauses, negative-test matrix, disabled bootstrap paths and implementation prohibitions were not changed by this governance-only delta.
- A2.2 self-review report updated to record the waiver and the exact-blob delta check:
  - Update commit: `d3a2b67db72798e6c0fda294e9be6256f1fd560f`.
  - Current report blob: `c32173c7c9de734f5f807e61a649a1e461208f07`.
  - The original full technical self-review was performed against prior A2.2 blob `2090112370e3b4a9925e78cf1ab0e2bb8428640c`; the subsequent change only adjusts the review gate/disposition and references the waiver. The delta check is same-session, not independent.
- Updated status: **A2.2 SELF-REVIEW PASS WITH RESIDUAL GATES / INDEPENDENT REVIEW WAIVED (NOT PERFORMED) / INDEPENDENT ASSURANCE G3 NOT ESTABLISHED / IMPLEMENTATION NOT APPROVED**.
- Gates unchanged: Path A and Path B remain NOT_ENABLED; bootstrap remains BLOCKED pending their separate contracts and trusted evidence. A separate explicit owner approval is still required for any implementation and must identify exact blobs and bounded scope.
- No keys, signatures, root enrollment, verifier configuration, policy/anchor instance, executable cryptographic tests, CI/workflow, VPS/SSH/runtime, SQLite/canonical T0 data or destructive operation was changed or exercised. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.
- CI/workflow NOT RUN; no run/artifact claimed.
- This waiver supersedes the earlier handoff next-step instruction to submit A2.2 for qualifying independent review. Do not schedule or treat independent review as a mandatory gate unless the owner later reinstates it.


### A2.2 waiver consistency cleanup — latest override

- A post-update scan found residual mandatory-independent-review wording in A2.2 overview and acceptance-gate clauses. These normative A2.2 references have now been corrected; historical A1/A2/A2.1 review-history references were retained.
- Latest A2.2 correction commit: `b04734858792831d2b19c90e204a11aa0aae8d6f`; current A2.2 blob: `41d41cd23f73a6e552b9ceca5ebbb39c46934e7d`.
- Latest self-review evidence update commit: `3db05538fc4fd84dd20fa64b87115cf886ef898c`; current report blob: `ab2b56376c01e4ef45b28d3dcd647feadd829b60`.
- Current owner waiver record blob (re-fetched): `f437dbf319b7a9570092c8cafb4bf354409e651c`.
- A2.2 mandatory independent-review gate: **WAIVED**. Independent review: **NOT PERFORMED**. Independent assurance/G3: **NOT ESTABLISHED**.
- Self-review evidence is the full technical review of prior A2.2 blob `2090112370e3b4a9925e78cf1ab0e2bb8428640c`, plus targeted same-session delta checks for governance-only changes. It must not be described as a full fresh review of every byte of the latest blob or as independent review.
- Implementation remains **NOT APPROVED** and requires separate explicit owner approval. Path A/Path B remain NOT_ENABLED; bootstrap remains BLOCKED. All other safety and custody limits remain unchanged.
- No code, tests, CI/workflow, keys/signatures, trust roots, bootstrap, policy/anchor instances, VPS/runtime, SQLite/canonical T0 data or destructive operations changed. CI/workflow NOT RUN.


## A2.2 implementation-scope assessment — 2026-11-11

- User requested to continue after the owner waived mandatory independent review. Work performed: **documentation-only implementation-scope assessment**; no implementation approval inferred.
- Assessment: `docs/architecture/T0_SIGNATURE_A2_2_IMPLEMENTATION_SCOPE_ASSESSMENT_2026-11-11.md`.
- Create commit: `f5dfd8a34c4f5016b0e68a6549803b55e06fb28e`; verified source blob: `443159b3cbbae39d27c0aa58669292de9998d463`.
- Governing A2.2 source blob: `41d41cd23f73a6e552b9ceca5ebbb39c46934e7d`; owner waiver blob: `f437dbf319b7a9570092c8cafb4bf354409e651c`; current A2.2 self-review report blob: `ab2b56376c01e4ef45b28d3dcd647feadd829b60`.
- Recommendation: if owner chooses to authorize code, begin with **Stage I synthetic contract-conformance harness only**: T0-JCS-1 parser/canonicalization, unsigned integer/U64BE, base64url, domain-separated SHA-256, profile binding, deterministic reason/verdict mapping, synthetic negative fixtures and in-memory no-state-change assertions.
- Any signature-verifier stub in Stage I must be labelled `MOCK / NOT CRYPTOGRAPHIC`; it cannot prove signature authenticity or cryptographic conformance.
- Explicitly excluded from Stage I: production crypto algorithm/library/key profile, real keys/signatures, root enrollment, Path A/B activation, verifier trust-store mutation, policy/anchor instances, durable anchor/CAS/two-copy publication, VPS/runtime/T0 integration, CI secrets/deployment and all trading execution paths.
- Stages II–V (production cryptography, bootstrap, durable anchor/custody, runtime integration) remain BLOCKED pending separate contracts and explicit owner approvals.
- Status: assessment **COMPLETE / DOCUMENTATION ONLY**; Stage I **PROPOSED / NOT APPROVED**; implementation remains **NOT APPROVED**; CI/workflow **NOT RUN**.
- No code/tests/runtime/VPS/SSH/SQLite/canonical T0 data/keys/trust state/destructive operation changed. Paper-only posture and `AI_EXECUTION_ENABLED=false` unchanged.
- Next decision required from owner: explicitly approve or reject Stage I, identifying the exact A2.2 blob and accepting the synthetic-only/mock-verifier boundary. Do not begin code changes before that approval.


## A2.2 Stage I owner approval — 2026-11-11

- Owner explicitly approved Stage I only, bound to A2.2 source blob `41d41cd23f73a6e552b9ceca5ebbb39c46934e7d`.
- Approval record: `docs/decisions/OWNER_APPROVAL_T0_SIGNATURE_A2_2_STAGE_I_2026-11-11.md`; commit `b79424ad86b5f4d78da610da3c81c9e90e92fee6`.
- Scope: isolated package/test directory separate from existing `synthetic_evidence`; T0-JCS-1 strict parse/canonicalization, canonical unsigned integer/U64BE, canonical unpadded base64url, domain-separated SHA-256, profile ID/version binding, deterministic verdict/reason precedence, 27 A2.2 negative fixtures, in-memory state snapshots and no-state-mutation assertions. Any verifier test double must be labelled `MOCK / NOT CRYPTOGRAPHIC`.
- Explicit exclusions: production crypto/profile/library selection, real keys/signatures, trust-root enrollment, Path A/B activation, verifier trust-store changes, Trust Policy/Anchor instances, durable anchor/custody publication, VPS/SSH/T0/SQLite/Feeder/API/runtime integration, CI secrets/deployment, trading changes and destructive operations.
- Scope assessment updated to record owner approval: blob `6d2a167ac0cfe4128c82c1532929014ac0dda8b8`; commit `cec6b26879b29632d753a4a4b6f8a32ed6307de3`.
- **Execution status: BLOCKED / NOT STARTED.** The available execution environment cannot resolve `github.com` for a local clone (clone attempt failed with DNS resolution error). GitHub content APIs can read/write repository documents but do not provide a local Python test runtime; no untested source was committed. A local isolated checkout/test runtime is required before starting TDD.
- No source code, tests, workflow, keys, signatures, trust roots, policy/anchor state, VPS/runtime, SQLite/canonical T0 data or trading behavior changed. No CI/workflow run or artifact exists.
- Next step: obtain an isolated local working tree for this exact branch/head, inspect the project test conventions, write the Stage I failing tests first, then implement the smallest passing code and run focused plus full relevant test suites. Keep all changes on this existing branch.


## 7. Current workstream — T0 Signature A2.2 Stage I synthetic harness

**Governing contract and approval**
- A2.2 source blob: `41d41cd23f73a6e552b9ceca5ebbb39c46934e7d`.
- Owner Stage I approval record blob: `04c6deb7b04c6cef10a8e696c9bd63af69264c2a`.
- Scope is limited to isolated synthetic/offline parsing, canonicalization, U64/U64BE, base64url, domain-separated digest helpers, profile binding, deterministic reason/verdict fixtures, 27 negative cases, in-memory state snapshots and a verifier stub labelled `MOCK / NOT CRYPTOGRAPHIC`.
- Independent review is waived as a mandatory gate; not performed; G3 NOT ESTABLISHED.

**Workflow**
- Dedicated manual-only workflow: `.github/workflows/t0-signature-a2-2-stage-i.yml`, blob `90560d0257ca6cf52e6626616769a0abab8ce10b`.
- Workflow addition commit: `56909f4da6d6c00ec9629132dc5bfdce4a266098`.
- Workflow inspection evidence commit: `e5efd27a4f325351c923b8e2436b202589e91074`.
- Workflow dispatch remains NOT AUTHORIZED / NOT RUN; no run or artifact exists.

**Stage I package/tests added**
- Package: `t0_signature_stage1/`, isolated from `synthetic_evidence/`.
- Source/test commits culminate at `40b338336fcad59f058fac320bffe6182b4485f8`.
- Evidence report: `docs/evidence/T0_SIGNATURE_A2_2_STAGE_I_SYNTHETIC_HARNESS_2026-11-11.md`, blob `d756fd16aa9bc23db4ebc54001380e95d82a1557`, commit `3384e751d6bf4af79d443f6d314a33f4a538af60`.
- Local TDD: initial RED due missing implementation modules; subsequent GREEN **32/32 tests PASS**, 0 failures/errors/skips. `compileall` PASS.
- Local test runtime was Python 3.13.5 in an isolated temporary tree with source files matching committed Git blobs. Python 3.12 parity is NOT VERIFIED.
- The tests cover strict UTF-8/duplicate-key/BOM/canonical-byte behavior, UTF-16 key ordering, safe-integer JSON subset, U64 boundaries, base64url vectors, Evidence Object digest, five-location profile binding, bootstrap reason precedence, all 27 fixture records, single-mutation leaf assertions, immutable state snapshots and mock-only verifier labelling.

**Current disposition: PARTIAL PASS / STAGE I ACCEPTANCE BLOCKED**
- A1/A2.2 domain strings are inconsistent: Evidence Object uses a single-backslash `\\0` form; Trust Policy body, Monotonic Anchor object and A2.2 Signature Envelope domains are written with double-backslash `\\\\0` in source text. Their exact preimage bytes are ambiguous. The three corresponding digest helpers fail closed with `DOMAIN_SEPARATOR_ENCODING_UNRESOLVED`; do not silently select NUL or literal backslash-plus-zero.
- T0-JCS-1 numeric-domain coverage is limited: floating-point JSON tokens are rejected and JSON integer tokens are limited to IEEE-754 safe integers; broader numeric-domain conformance remains NOT VERIFIED.
- These are contract blockers, not crypto implementation findings. Passing 32 local tests proves only the implemented synthetic subset and fail-closed behavior, not full Stage I acceptance.
- No production crypto, real keys, bootstrap, Path A/B, durable Trust Policy/Anchor, VPS/SSH, Feeder/API, SQLite/canonical T0, custody publication, CI secrets, deployment, trading, or destructive operation was changed or exercised.

**Next permitted step**
- Prepare an exact contract-only correction proposal that fixes the domain-separator byte strings and clarifies the T0-JCS-1 numeric subset. Obtain explicit owner approval of that amendment before changing the digest helpers or claiming full Stage I acceptance.
- After the contract correction, update the exact tests and helpers, rerun local focused tests, then request separate explicit authorization before dispatching the manual GitHub Actions workflow. Do not dispatch while this blocker remains.


### A2.2 Stage I — follow-up proposal (2026-11-11)

- Contract ambiguity proposal: `docs/evidence/T0_SIGNATURE_A2_2_STAGE_I_CONTRACT_AMBIGUITY_PROPOSAL_2026-11-11.md`.
- Proposal blob: `37bff74053ddc1034e09f40d9cc3bf558588e897`; commit: `d5695ed7ac752d8e5570354a1389ef9c8403033c`.
- Proposal recommends exact NUL-terminated domain byte vectors for Evidence Object, Trust Policy body, Monotonic Anchor object and Signature Envelope object, plus a restricted T0-JCS-1 numeric grammar.
- Proposal is **NOT OWNER-APPROVED** and does not amend A2.2. The three digest helpers remain fail-closed. Await explicit owner decision before changing the governing contract or implementing the ambiguous helpers.


- Stage I harness evidence report was updated to reference the unapproved contract-ambiguity proposal: current evidence blob `9e5ecd7a2c47cad4d36e4d1b1ab0d8d3385e8bde`, commit `41bbaa23cb8f7f732431644ad103882caa695146`.


### A2.2 Stage I — owner-approved contract clarification and implementation delta (2026-11-11)

The prior A2.2 Stage I status/proposal notes above are historical snapshots. This delta supersedes their "proposal unapproved / digest helpers blocked" disposition.

**Owner decision and normative amendment**
- Owner approved exact proposal blob `37bff74053ddc1034e09f40d9cc3bf558588e897`.
- A2.2 §20 now normatively fixes the four domain separator byte sequences (ASCII domain name + exactly one NUL octet) and the restricted T0-JCS-1 numeric-token grammar.
- A2.2 amendment commit: `e1cb154755f127587e5a868c3ac9423ecf9bf15f`; blob: `3f4cb1fc36a58bc6ccaa26872360b8ee2961270b`.
- A1 §14.2 remains controlling for logical integer fields: logical U64/length/sequence/time/schema-version fields use canonical unsigned decimal strings. The fixed A2.2 profile-version discriminator remains integer `2`.

**Stage I code/tests**
- Test-first commit: `f1bc86d25b7ca773848c0ff5093e887e389f9a88`; test blob: `8e47af0bb98cae6e8501c609c97259ebc5e0c78f`.
- Digest implementation commit: `8af2aeca99ddcab6d93133c5a689276582e4b358`; `primitives.py` blob: `91496d70a67d12525b8399b46aeb1318693b17ee`.
- Three formerly fail-closed digest helpers now use the exact approved constants. Evidence Object digest uses the same explicit byte-constant pattern.
- Current test denominator: 23 primitive tests + 11 fixture/verdict tests = **34 test methods**.
- Independent Python spot-check: 4/4 fixed SHA-256 vectors, four distinct domain digests, both safe-integer boundaries accepted and six invalid numeric forms rejected. This does NOT constitute execution of the repository suite.

**Current evidence and verification**
- Updated evidence report: `docs/evidence/T0_SIGNATURE_A2_2_STAGE_I_SYNTHETIC_HARNESS_2026-11-11.md`, blob `f122daa5a70834077f5a93e8a43f302c7eb83890`, commit `b94e691eca70ae79ebc74cc104e47f544d26fb49`.
- Repository unit tests: **NOT RUN** after the latest change. Local clone failed because GitHub DNS resolution was unavailable.
- `compileall`: **NOT RUN** after the latest change.
- GitHub Actions: **NOT DISPATCHED**; no run/job/artifact exists. Manual workflow dispatch still requires separate explicit authorization.
- Python 3.12 parity: NOT VERIFIED.
- Disposition: **CONTRACT CLARIFICATION APPLIED / IMPLEMENTATION COMMITTED / TEST EXECUTION NOT VERIFIED**. Stage I is not PASS until all 34 repository tests and compile checks pass on exact committed source.
- Independent review remains waived/not performed; G3 is not established.

**Next permitted step**
- Obtain separate explicit authorization to dispatch the manual-only Stage I GitHub Actions workflow after confirming the current source and test files. Do not use workflow success to claim production cryptographic assurance. No production crypto, keys, root enrollment, Path A/B, durable trust state, VPS/T0, custody publication, CI secrets, deployment, trading or destructive operations.


- Follow-up contract wording consistency: A2.2 §19 now explicitly recognizes the separately owner-approved synthetic Stage I implementation while keeping production cryptography and all excluded scopes unauthorized. Current contract blob `d9f93bf390d107381b7135c3073aeca0d14894d4`, commit `96caa617ef1f5bb16b1c631ef164f4d34959592c`.
- Latest Stage I evidence report blob: `14c67c9d602546c28c25d7adef650ac6358b94ea`, commit `c6d2266670275222dcb966169667d0077e08d274`.


- Post-amendment self-review: `docs/evidence/T0_SIGNATURE_A2_2_STAGE_I_POST_AMENDMENT_SELF_REVIEW_2026-11-11.md`, blob `e44273248ef7ee68898a90e1fdfb1cd6a0a6c6dc`, commit `58a56660e50ff618d15bbea20665ce556b4378f1`; result **SELF-REVIEW PASS WITH VERIFICATION BLOCKER**. No source-level defect identified, but exact 34-test suite and compile check are NOT RUN. Independent review remains waived/not performed; G3 not established.
- Updated Stage I evidence report blob: `3c77a5043756de54d4ccc8545b0ae5329f0aacfd`, commit `f58bf6a203e8dd663003eeff97ad7580dcbb9c57`.


### A2.2 Stage I — workflow parser backport and exact-branch verification (2026-11-11)

- Owner explicitly approved backporting only the workflow parser correction from `main` into the existing active branch. No Stage I package/source/tests were copied to `main`; no parallel branch or PR was created.
- Backport commit: `ab8cc85017c0eda5da211d5fa326a9048b0239f7`.
- Changed path: `.github/workflows/t0-signature-a2-2-stage-i.yml` only; compare from prior active HEAD `e7273e918f254bd17a3ce997bb722e8d4e36d029` reports 1 commit, 1 file, +10/-1, no other paths.
- Workflow blob after backport: `5fa94939181af5f1f33686c3444bc6f8a0326962`, identical to the parser-fixed workflow blob on `main`.
- Parser now accepts both unittest summaries `Ran 1 test` and `Ran 34 tests in 0.088s`; workflow contains inline regression assertions for both forms.
- Source package and tests remain on the active feature branch; no source/test/runtime/T0/VPS/trading changes were made.
- **Dispatch status: NOT RUN.** This approval covered the workflow-only backport, not a new manual workflow dispatch. A fresh explicit dispatch authorization is still required. Previous run `42954924103` on `main` remains blocked because the Stage I package is intentionally absent from `main`.
- Stage I status remains **NOT VERIFIED end-to-end** until a new manual run on this feature branch proves compile, all 34 tests, parser, and artifact upload on the exact checkout SHA. Independent review/G3 remains not established.



### A2.2 Stage I — exact feature-branch workflow verification (2026-11-11)

- Owner separately authorized manual dispatch; workflow was run by the owner on the existing feature branch.
- Workflow run [42955676103](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42955676103): event `workflow_dispatch`, run number 5, branch `feature/t0-centralized-data-feeder-p1-20261101`, conclusion **SUCCESS**, created 2026-11-11T03:53:32Z.
- Exact triggering/checked-out source SHA: `cadcfcf66503c0a0750adcfc6646d6fa2944f03e`. Checkout log confirms detached checkout at this exact SHA; it matches the recorded active branch HEAD at dispatch.
- Workflow path: `.github/workflows/t0-signature-a2-2-stage-i.yml`; job `130310067517`, `Stage I isolated contract tests`: SUCCESS. All seven main steps completed successfully, including exact checkout, Python setup, preflight, compile, synthetic tests and artifact upload.
- Runtime: CPython `3.12.16`. Preflight evidence: `SCOPE=STAGE_I_SYNTHETIC_ONLY`, `AI_EXECUTION_ENABLED=false`, database/exchange credentials empty, `RUNTIME_INTEGRATION=NOT_AUTHORIZED`.
- Compile: `STAGE_I_COMPILE=PASS`.
- Repository suite: **34/34 tests PASS**, exit code 0; unittest summary `Ran 34 tests in 0.085s / OK`. Workflow parser accepted the timed plural summary and its inline singular/plural regression assertions completed in the successful job.
- Artifact: ID `13826832203`; name `t0-signature-a2-2-stage-i-cadcfcf66503c0a0750adcfc6646d6fa2944f03e`; size 1,810 bytes; expires `2026-11-18T03:53:32Z`. GitHub digest: `sha256:fbd311592772e3da4dda726d0a25fb768561df6ebad0667a7d607247983ed845`. Artifact ZIP was downloaded and independently hashed; local SHA-256 exactly matches GitHub's digest. ZIP contains five files: `compile.txt`, `preflight.txt`, `source-sha.txt`, `tests.log`, `verdict.txt`. Extracted verdict records `STAGE_I_TESTS=PASS`, `TEST_COUNT=34`, `EXIT_CODE=0`; embedded source SHA matches the workflow checkout.
- Result: **STAGE I SYNTHETIC CI/TEST GATE PASS** for this exact source and Python 3.12 runtime. This resolves the prior repository-suite/compile/Python-3.12 verification blocker.
- Limits remain: synthetic/mock-only, not production cryptographic assurance; independent review waived/not performed; G3 not established. No production keys/signatures, trust-root/bootstrap, policy/anchor instances, VPS/SSH/T0 runtime, SQLite/canonical data, custody publication, trading or destructive operations were exercised. `AI_EXECUTION_ENABLED=false` remains.
- Next step: record the gate as PASS and retain the artifact/run evidence. Any later stage (production crypto, bootstrap, durable trust/anchor/custody, runtime integration or trading) requires its own contract and explicit approval; this run grants none of those permissions.



### A2.2 Stage I — evidence dossier closed for synthetic CI gate (2026-11-11)

This is the current disposition and supersedes the earlier historical NOT RUN / NOT VERIFIED execution statements and the prior "next step: record the gate" note above. Historical entries remain intact.

- Exact tested source: `cadcfcf66503c0a0750adcfc6646d6fa2944f03e`; run [42955676103](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42955676103), `workflow_dispatch`, feature branch, SUCCESS.
- CPython 3.12.16; compile PASS; 34/34 tests PASS; parser PASS; artifact upload PASS. Job `130310067517`.
- Artifact `13826832203`, SHA-256 `fbd311592772e3da4dda726d0a25fb768561df6ebad0667a7d607247983ed845`, independently re-hashed from downloaded ZIP; expires `2026-11-18T03:53:32Z`.
- Evidence report append-only addendum: `docs/evidence/T0_SIGNATURE_A2_2_STAGE_I_SYNTHETIC_HARNESS_2026-11-11.md`, blob `95f2a7f81ee167657e157dc85d391355c57e3ef6`, commit `7eb57abb10d73ac21100a5d860fc5afa6eb77f68`.
- **Current gate: STAGE I SYNTHETIC CI/TEST = PASS.** Scope remains synthetic-only; independent review waived/not performed; G3 not established. No production crypto, key/root bootstrap, durable policy/anchor, custody, VPS/T0 runtime, canonical data, trading or destructive action is approved by this result.
- Latest planned follow-up is **contract-only Stage II scoping**, not implementation: first identify the exact Stage II purpose, boundaries, prerequisites, trust assumptions, negative cases, acceptance evidence and approval gates from the governing A2.2 architecture. No Stage II code, production cryptography, key handling, bootstrap, durable state or runtime integration is authorized by this handoff.
- Branch continuity preserved; evidence updates only. Current commit after this handoff append becomes the new branch HEAD.


### A2.2 Stage II — non-normative scope-gap assessment (2026-11-11)

- Draft: `docs/evidence/T0_SIGNATURE_A2_2_STAGE_II_SCOPE_GAP_ASSESSMENT_2026-11-11.md`, commit `0690e13ca01f89794bada1a71b929568d8133b6e`.
- Status: **DRAFT / NON-NORMATIVE / NOT OWNER-APPROVED / NO IMPLEMENTATION AUTHORITY**.
- Stage II concept carried forward from prior discussion: cryptographic adapter plus actual digital-signature verification. Algorithm/profile, public-key and signature formats, library/provider, trust binding, key lifecycle, error semantics and resource limits remain unresolved.
- The draft explicitly separates cryptographic validity from signer trust, Trust Policy authorization, Monotonic Anchor/replay checks and state transitions. It includes a preliminary negative-test checklist and required evidence, without selecting an algorithm or library.
- **Stage II remains BLOCKED / NOT APPROVED.** Stage I approval and PASS do not authorize Stage II. No code, keys, trust-root/bootstrap, durable policy/anchor state, runtime, VPS, canonical T0, CI secrets, deployment or trading changes were made.
- Next owner decision: confirm/reject the candidate purpose in §3 of the draft, then decide whether to authorize bounded option analysis for the unresolved §4 rows. No implementation request is implied.

### A2.2 Stage II — cryptographic option analysis draft (2026-11-11)

- Owner approved proceeding with Stages II–V as a program direction. This is not blanket implementation/runtime authority; each stage retains its own contract and bounded implementation approval gates.
- Stage II option analysis created: `docs/evidence/T0_SIGNATURE_A2_2_STAGE_II_CRYPTO_OPTION_ANALYSIS_2026-11-11.md`.
- Analysis commit: `61085c576d4ddfcffa00d2295a68569c1cbdb7f7`.
- Status: **DRAFT / NON-NORMATIVE / OWNER DECISION REQUIRED / NO IMPLEMENTATION AUTHORITY**.
- Candidate comparison: Ed25519 PureEdDSA, ECDSA P-256/SHA-256, RSA-PSS/SHA-256; candidate library PyCA `cryptography`; candidate key encodings raw 32-byte Ed25519 or DER/SPKI; signature encoding 64-byte Ed25519.
- Preliminary recommendation: Ed25519 + PyCA `cryptography`, conditional on no mandatory external interoperability/FIPS-validated-module constraint. SPKI vs raw key encoding remains an owner decision. Exact signature input bytes must be reconciled against normative A2.2; no assumption is made about envelope serialization vs digest input.
- No algorithm/library/profile is normatively selected. No code, dependencies, keys, trust root, durable state, CI workflow, VPS/runtime, T0, trading or destructive data operation changed.
- Next owner decision: approve/reject the candidate for a **contract-only** Stage II specification and resolve key representation / FIPS requirement. Implementation remains separately gated. Stage III–V scope is not inferred from Stage II.

### A2.2 Stage II — Ed25519 adapter contract draft (2026-11-11)

- Owner approval recorded for **Ed25519 PureEdDSA**, PyCA `cryptography` candidate, DER SubjectPublicKeyInfo (SPKI), 64-byte raw signature, and no mandatory FIPS-validated-module requirement.
- Contract draft: `docs/evidence/T0_SIGNATURE_A2_2_STAGE_II_ED25519_ADAPTER_CONTRACT_2026-11-11.md`.
- Contract commit: `ab66b77a18b29f7bdaac4a86dc17260f94655c58`.
- Contract status: **DRAFT / OWNER-DECISIONS RECORDED / CONTRACT-ONLY / NOT FROZEN / NO IMPLEMENTATION AUTHORITY**.
- The adapter verifies only the supplied exact A1-defined preimage bytes. It does not parse/re-serialize statements, hash again, resolve signer trust, authorize purpose/audience, check revocation or anchors, mutate state, access network, or use private keys.
- A1 §4.3 exact Signature Statement preimage and A1 §14.3 unpadded base64url envelope encoding are preserved. SPKI fingerprint remains SHA-256 over exact DER SPKI bytes.
- FIPS decision is not a FIPS certification or validated-mode claim.
- Open blockers before contract freeze: bounded resource ceilings; exact PyCA release/dependency hashes and build provenance; complete legacy v1 field mapping; final A1/A2.2 consistency review; qualifying independent security review.
- No tests were run because this increment is documentation-only. No code, dependency, key, trust root, policy/anchor state, CI workflow, VPS/runtime, T0, trading or destructive data operation changed.
- Next step: resolve the contract blockers and review the exact contract blob before asking for a separate implementation approval. Stage III–V scope remains independently gated.

### Stage II contract exact-byte correction (2026-11-11)

- Static comparison against A1 §4.3 found the draft's displayed domain-separator escape had an extra backslash. Corrected the notation to the exact single-NUL escape `\\0` used by A1. This is a documentation correction; the domain bytes remain those already fixed by A2.2 §20.
- Corrected contract commit: `232ea8f2dfeda0f08544fa483544f0f761d21914`; blob: `944758f37f0cc3b0fa1d9968976ce2a7d6c7ce72`.
- No code or test was run; no runtime or key operation occurred.


### Stage II v1 signature field-mapping review (2026-11-11)

- Review: `docs/evidence/T0_SIGNATURE_A2_2_STAGE_II_V1_FIELD_MAPPING_REVIEW_2026-11-11.md`.
- Review commit: `7914a8e3946cbdc81f0a7e6c48c2d36e9bb0c618`.
- Static crosswalk against Checkpoint Contract v1 §6 and A1 §§4.2–4.4/14.4: **PARTIAL PASS**.
- Exact evidence-object binding, purpose/audience, profile, signer fingerprint, algorithm/signature, untrusted local signing observation and Trust Policy snapshot fields are mapped. Verification references correctly remain post-signing append-only Verification Record data.
- Three higher-level signed provenance/authorization mappings remain open: signing software/build identity; signing request/decision reference; signer authority/custody evidence reference. A1 §14.4 requires these either in the signed Signature Statement or in a separately signed authorization-evidence object whose exact ID/digest is bound by the statement. Stage II review does not choose either representation.
- Envelope ID/descriptor lifecycle remains a higher-layer requirement and must avoid self-reference.
- Disposition: full Signature Statement schema freeze **BLOCKED** until owner/security contract review resolves the three provenance references and envelope descriptor mapping. The Ed25519 primitive boundary remains unchanged and stateless.
- Documentation-only; no tests run. No code, dependency, key, trust root, policy/anchor state, CI dispatch, VPS/runtime, T0, trading or destructive operation changed.
- Next step: prepare a bounded options note for the three provenance references and envelope-ID lifecycle; request owner decision before revising/finalizing the statement schema. No implementation authority implied.


### Stage II — provenance and envelope identity options recorded (2026-11-11)

- Options note: `docs/evidence/T0_SIGNATURE_A2_2_STAGE_II_PROVENANCE_AND_ENVELOPE_ID_OPTIONS_2026-11-11.md`.
- Note commit: `0212aee2efed213e6d41e96f1adcacb6cb02b135`.
- Compared Option A (three provenance/authorization references directly in the signed Signature Statement) against Option B (separately signed Authorization Evidence Object bound by exact immutable descriptor).
- Compared E1 (preassigned stable envelope ID, not derived from completed envelope bytes) against E2 (detached descriptor identity, independently assigned/derived without self-reference).
- Recorded trade-offs, required contract work, replay/substitution/offline dependency risks, and invariants. **No option selected**; no field names or object schema invented.
- Ed25519 primitive remains exact-bytes-only, stateless and unchanged.
- Status: **OPTIONS RECORDED / OWNER DECISION REQUIRED / CONTRACT FREEZE BLOCKED**.
- Documentation-only; no tests run. No A1/A2.2 normative amendment, code, dependencies, keys, trust root, policy/anchor state, CI dispatch, VPS/T0/runtime, trading or destructive operation changed.
- Next owner decision: choose A or B and E1 or E2, or request a bounded revision. Independent security review and separate implementation approval remain required downstream.


### Stage II — owner approved provenance/envelope architecture B + E2 (2026-11-11)

- Owner explicitly approved **Option B + E2**, limited to documentation and contract refinement.
- Option B: use a separately signed Authorization Evidence Object for signing software/build identity, signing request/decision reference, and signer authority/custody evidence reference. The main Signature Statement binds the object through an immutable descriptor.
- Option E2: use a detached envelope descriptor. Its ID is independently assigned as an opaque identifier and MUST NOT be derived from a descriptor serialization that contains the same ID. Envelope digest/length are computed only after complete envelope bytes exist.
- Contract refinement appended to `docs/evidence/T0_SIGNATURE_A2_2_STAGE_II_ED25519_ADAPTER_CONTRACT_2026-11-11.md`; commit `27b12af862846a8893a44a5148c7a02dbe59bb1e`; blob `e1b12fc1fc4b463fc82ff8b6b5f0b2701af5888b`.
- Mapping review decision addendum commit `6726731ba9c29a40c7147ec6167f96129aff4489`; blob `1185a3bf65d66c8cd203bd1dbc7994fdca0b1ad1`.
- Options note superseding decision addendum commit `5de8596118e1c17f6cd2c8950982f57ca1f0a383`; blob `23f3dde4e5c7cf871e6527c85a59218a0ebd61b2`.
- Detailed Authorization Evidence Object schema, signature domain/signer trust chain, descriptor schema/ID namespace and retry rules, Verification Record schema, resource ceilings, pinned dependency/build provenance, and independent security review remain open. Thus **architecture pattern approved; detailed contract NOT FROZEN; implementation BLOCKED / NOT AUTHORIZED**.
- Ed25519 adapter remains exact-bytes-only and stateless. No tests were run (documentation-only). No code, dependencies, keys, trust root, Trust Policy/Monotonic Anchor state, CI dispatch, VPS/T0/runtime, trading, or destructive operation changed.
- Next step: define the detailed object and descriptor schemas in a bounded contract draft, then run A1/A2.2 consistency review and independent security review before seeking separate implementation approval.


### Stage II — Authorization Evidence Object + detached envelope descriptor schema draft (2026-11-11)

- Following the owner's approval to proceed with the bounded documentation step, created `docs/evidence/T0_SIGNATURE_A2_2_STAGE_II_AUTHORIZATION_OBJECT_AND_DETACHED_DESCRIPTOR_SCHEMA_DRAFT_2026-11-11.md`.
- Draft commit: `3bcc8023d3205e8121af094c8e27e9385999f082`; verified blob: `6a47509fc902cfe40188f890d06f20af23cffeec`.
- Defines proposed AEO body/descriptor fields, separate AEO signature-statement requirements, main-statement binding, detached E2 envelope descriptor, non-circular lifecycle, ID/idempotency proposal, Verification Record references, validation rules and negative-test cases.
- Static source comparison pins: Checkpoint Contract v1 blob `a6825270d59bde274bfe765d5f942144b66a84de`; A1 blob `00fdad293e129562145ab930507a4e6b9c2bf23d`; A2.2 blob `d9f93bf390d107381b7135c3073aeca0d14894d4`; prior Stage II adapter contract blob `e1b12fc1fc4b463fc82ff8b6b5f0b2701af5888b`.
- **Important consistency blocker found:** A1 §14.4 permits B and A1 §4.4 is compatible with detached E2; however A2.2 §3.1 still puts provenance fields directly in the main Signature Statement and A2.2 §3.3 still embeds a preassigned envelope ID in the signed statement (E1). The draft records these conflicts and requires a normative successor/amendment (expected A2.3) before contract freeze. Existing A2.2 negative cases must be remapped, not silently dropped.
- Status: **SCHEMA DRAFT CREATED / NOT NORMATIVE / NOT FROZEN; A1-A2.2 CONSISTENCY BLOCKED ON EXPLICIT CONFLICT RESOLUTION; IMPLEMENTATION NOT AUTHORIZED**.
- No tests run (documentation-only). No code, dependencies, keys, trust roots, policy/anchor/verification state, CI dispatch, VPS/T0/runtime, trading or destructive operations changed.
- Next step: perform a focused consistency review of the draft against A1/A2.2, produce a bounded A2.3 amendment proposal for the explicit B/E2 conflicts, and preserve unresolved cryptographic-domain/trust-chain decisions as blockers. Do not implement or dispatch workflows.


### Stage II — automatic continuation: A2.3 B/E2 contract draft and adapter alignment (2026-11-11)

- Owner instruction: continue Stage II automatically until completion. Work remains on the existing branch `feature/t0-centralized-data-feeder-p1-20261101`; no new branch/PR was created.
- Read the current handoff before work; this entry records the current bounded continuation.
- Created A2.3 draft: `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A2_3_DRAFT_2026-11-11.md`.
  - Final current document blob: `41d6abfc9df20047af4668b80a6ce2edb7e07117`.
  - Initial creation commit: `d1faa3f952ccf6319d89f4de06ea09d6a498d954`; subsequent documentation-only refinements specify AEO body digest domain, AEO-specific statement/domain, field/descriptor mappings, purpose-specific profile IDs and Ed25519 bindings, fixed domain KAT, UUIDv4 descriptor identity and bounded parser/input limits.
  - Explicitly supersedes A2.2 §3.1 provenance field placement and §3.3 E1 envelope-ID placement with B + E2. Preserves A2.2 §16–17 bootstrap disabled / NOT_ENABLED.
  - Adds AEO issuer profile `T0-AUTHORIZATION-EVIDENCE-ISSUER-SIGNATURE-PROFILE-V1` and retains checkpoint profile `T0-CHECKPOINT-ISSUER-SIGNATURE-PROFILE-V2`; both use owner-approved Ed25519 PureEdDSA, strict SPKI DER and 64-byte raw signatures. Trust Policy must explicitly authorize exact profile/role/purpose/audience/scope.
  - Proposes a distinct AEO signature-statement domain. Fixed SHA-256 KAT: domain hex `54302d415554484f52495a4154494f4e2d45564944454e43452d5349474e41545552452d53544154454d454e542d563100`, domain length 49; payload `A2.3-AEO-domain-KAT-v1`, length 22, U64BE `0000000000000016`; digest `64172accdaf1f2add08b201b25c8ea26b52e2c90e68674126bbef465f4e7acde`.
  - Proposes limits: statement/AEO/dependency body <=1 MiB, preimage <=1 MiB+64 octets, SPKI <=4096 octets, signature exactly 64 octets, <=64 dependencies, <=16 MiB total frozen input set, descriptor <=64 KiB, bounded JSON nesting/member/array/string limits. These are proposed, not frozen.
- A2.3 self-review: `docs/evidence/T0_SIGNATURE_A2_3_SELF_REVIEW_2026-11-11.md`; current blob `70a76561bc20747de45fd0956ba09b22dbc48bcf`; review is same-session author self-review only, **PARTIAL PASS WITH BLOCKERS**, not independent review/G3.
- Stage II adapter contract aligned with A2.3: `docs/evidence/T0_SIGNATURE_A2_2_STAGE_II_ED25519_ADAPTER_CONTRACT_2026-11-11.md`; current blob `1bdfc87949429cfd164892eab519971954f243eb`. Adds `INPUT_LIMIT_EXCEEDED` and proposed adapter input ceilings; preserves exact-byte stateless primitive.
- Open blockers: explicit owner freeze of exact A2.3 blob/resource ceilings and distinct AEO issuer principal/key constraint; complete Trust Policy field crosswalk and exact evidence descriptor schemas/status semantics; independent security review of exact A2.3 + adapter contract; pinned PyCA version/dependency hashes/wheel/build provenance. No Stage II implementation or CI test is authorized until the exact contract/review gate is closed.
- No tests were run; documentation-only. No code/dependencies/keys/signatures/trust roots/policy/anchor/Verification Record state/CI dispatch/VPS/T0/runtime/trading/destructive operations changed.
- Next: complete a final exact-blob consistency pass and review package, then obtain qualifying independent security review. If no independent reviewer is available, mark Stage II BLOCKED at that gate; do not substitute same-session self-review.


### Stage II — PyCA dependency candidate research (2026-11-11)

- Current PyCA release research identified `cryptography==50.0.2` as a candidate; PyPI lists the release dated 2026-09-30, Python >=3.9 (excluding 3.9.0/3.9.1), and release artifacts with provenance. PyCA's published supported-platform list includes x86-64 Ubuntu 26.04 and the current CI's likely Linux/CPython lane must still be read back during build.
- Proposed CPython 3.11+ ABI3 / manylinux_2_34 x86-64 wheel: `cryptography-50.0.2-cp311-abi3-manylinux_2_34_x86_64.whl`; candidate SHA-256 `9dab55f57c74c3cad24c323bacbbd04be4705ba6eb0d92e920b1fc4837ed5079`; candidate sdist SHA-256 `7b46165bb56eb4704e2eaaf86f3c940d19154535d9b0ca7d6d590b04060e00d5`.
- Dependency note: `docs/evidence/T0_SIGNATURE_A2_3_PYCA_DEPENDENCY_CANDIDATE_2026-11-11.md`; commit `d633b478a4f158f48ccb43e379dbd14c023d9b87`.
- Adapter contract updated with candidate: blob `8ec916c152c51e75c5a3852e7977dd7f1239d8fe`; current self-review report blob `038b17c9f2cc699b3db54f4ce06d517cf61fa665`.
- Important: the wheel hash is corroborated by published lockfile records but was NOT recomputed from the downloaded PyPI artifact in this environment. The wheel itself was not installed. Transitive dependency closure, exact runner glibc, provenance attestation verification, license review and offline install remain NOT VERIFIED. No dependency file, lockfile, CI workflow or VPS package state changed.
- Stage II remains **PARTIAL / BLOCKED AT INDEPENDENT SECURITY REVIEW AND CONTRACT FREEZE**. No tests or code implementation have been run.


### Stage II — independent security review request opened (2026-11-11)

- Created GitHub issue #143 requesting independent security review of exact A2.3 + Stage II adapter contract blobs: https://github.com/kenznguyen/btcusdt-telegram-signals2/issues/143.
- Review issue pins A2.3 blob `41d6abfc9df20047af4668b80a6ce2edb7e07117`, adapter contract blob `8ec916c152c51e75c5a3852e7977dd7f1239d8fe`, self-review blob `038b17c9f2cc699b3db54f4ce06d517cf61fa665`, dependency candidate blob `9092b2cf5a9e9308d28e8436c8b91e2f9566ef4e`.
- No reviewer was assigned because no qualified independent reviewer identity was established from repository context. Do not treat issue creation as review completion.
- **Current Stage II disposition: BLOCKED at qualifying independent security review and exact contract freeze.** Same-session self-review is not independent. No Stage II implementation, test fixtures, dependency installation, lockfile change, workflow dispatch, key operation, trust bootstrap, VPS/T0/runtime or trading action is authorized/performed.
- Next action: wait for a qualified independent reviewer to review the exact pinned blobs and record PASS/REQUEST CHANGES/BLOCKED. If reviewer requests changes, address findings on the same branch, update exact blobs and request review of the new snapshot. Only after review PASS and owner freeze may the narrowly scoped adapter implementation/test/CI step proceed under the existing Stage II approval boundaries.



### Stage II — owner decision: withdraw mandatory independent review gate (2026-11-11)

- Owner explicitly withdrew the prior decision that a qualifying independent security review is mandatory before Stage II contract freeze/implementation.
- Independent review is **NOT a required gate** unless the owner re-approves it later. This supersedes the earlier handoff entries that made independent review a hard blocker.
- GitHub issue #143 is closed as not planned because the requested mandatory review is withdrawn. It received zero comments/reviewer findings before closure; therefore there are no external reviewer findings to claim as closed.
- The existing A2.3 self-review remains an author self-review only: PARTIAL PASS WITH BLOCKERS. This decision does not relabel it as independent review or as G3.
- Remaining gates are unchanged: close the documented substantive findings (including exact Trust Policy crosswalk/status and revocation semantics, canonical descriptor schemas/namespace authority, owner decision on distinct AEO issuer principal/key and resource ceilings); verify the exact PyCA artifact hash, provenance attestation, transitive dependency closure, runner compatibility and offline build; then obtain an explicit owner freeze of exact A2.3 and adapter-contract blobs.
- After those gates, proceed with the narrowly scoped stateless Ed25519 adapter, TDD tests and CI verification within the approved Stage II boundary. Do not infer approval for key custody/bootstrap, Trust Policy/Monotonic Anchor runtime, VPS/T0 integration, trading, live orders or destructive operations.
- No code, dependency, lockfile, workflow, runtime or canonical data changes were made by this decision update.
- Status: **INDEPENDENT REVIEW GATE WITHDRAWN BY OWNER / CONTRACT NOT FROZEN / IMPLEMENTATION NOT YET PASS**.
- Branch at decision time: `feature/t0-centralized-data-feeder-p1-20261101`; pre-update HEAD: `eb9ed7784d8db7db517bd145b0380ba166d01c8d`.


## Owner direction decision — pause Stage II, prioritize operational and Dual-Strategy system (2026-11-11)

**Owner explicitly confirmed this direction (“chốt phương hướng”). This entry is the current governing priority and supersedes the prior Stage II “automatic continuation until completion” instruction to the extent it conflicts with this pause.**

### Decision
- **Stage II A2.3 / Ed25519 adapter: PAUSED.** Do not continue contract refinement, dependency/provenance work, adapter implementation, tests or CI for Stage II unless the owner explicitly reopens it.
- Preserve all Stage I and Stage II work products, source blobs, GitHub runs, artifacts and historical evidence. Do not delete, rewrite or relabel them. Stage I synthetic CI/test gate remains **PASS** for its exact source; this is not production cryptographic assurance.
- Redirect active priority to the usable system: T0/T1/T2 operational readiness and data-flow consistency, then the BTCUSDT Dual-Strategy Intelligence design and implementation planning.
- Preserve Strategy Core unchanged: RSI + ADX + Smart DCA.
- AI Strategy is a separate signal-producing strategy and may emit independent LONG/SHORT signals even when Strategy Core emits no signal.
- Core and AI retain separate strategy identities/ledgers. Every candidate signal/order intent must pass the common Shared Risk Engine and Kill Switch before it can become an eligible paper-trade action. Risk controls are shared; signal generation is independent.
- Preserve paper-only posture: `AI_EXECUTION_ENABLED=false`; no live trading, real exchange orders, production deployment or execution enablement.
- Existing risk direction remains: maximum margin allocation for each new order is 1% of portfolio equity; AI leverage policy, where applicable, is sizing-only and cannot bypass shared risk checks.
- T0 remains an independent canonical data foundation. No canonical T0 data, lease/fencing state, durable evidence, owner custody/trust evidence or protected runtime state may be mutated as part of this reprioritization.
- Continue to preserve the current branch and Git history; no parallel branch/PR solely for this decision.

### Execution sequence
1. Reconcile current repository state and existing evidence for T0/T1/T2 and Dual-Strategy before proposing code changes.
2. Identify the smallest operational blockers affecting reliable T0→T2 data delivery and close them within already approved read-only/documentation/CI scopes.
3. Freeze the Dual-Strategy boundary: independent Core/AI signal contracts, separate ledgers, shared risk interface, Kill Switch precedence, sizing/leverage limits, paper-only execution boundary and deterministic conflict handling.
4. Only then propose bounded implementation increments with explicit tests, evidence and approvals. No blanket implementation, VPS/runtime or exchange-execution authority is implied by this priority decision.

### Status and limits
- Stage I synthetic harness: **PASS** for exact run/source/artifact recorded above; preserve.
- Stage II A2.3: **PAUSED BY OWNER**; contract remains draft/not frozen; no adapter implementation or runtime integration.
- T0/T1/T2 operational acceptance: retain each existing per-gate disposition; do not promote NOT VERIFIED/BLOCKED evidence.
- Dual-Strategy implementation: **NOT YET AUTHORIZED BY THIS PRIORITY DECISION**; next step is repository-state assessment and contract-level planning.
- No tests, CI workflow, runtime, VPS, SQLite/canonical T0, credentials, keys/trust state, trading ledger or exchange order state were changed by this decision.



## Read-only operational and Dual-Strategy baseline — 2026-11-11

- Owner direction remains: Stage II A2.3 paused; preserve Stage I/II artifacts; prioritize T0/T1/T2 operational readiness and Dual-Strategy; paper-only; no runtime or live execution authority.
- Read-only assessment report: `docs/evidence/DUAL_STRATEGY_AND_OPERATIONAL_BASELINE_2026-11-11.md`.
- Report commit: `aa5fa075fe8ad3179fb5c3b70c1f27eb5e6420ae`.
- Exact reviewed source snapshot: `fa12771973680c94f8d75fd48e69dafed9750d68`.
- Report disposition: **PARTIAL / IMPLEMENTATION PRESENT / END-TO-END DUAL-STRATEGY NOT VERIFIED**.
- T0: existing source/isolated CI evidence; dated feeder runtime receipt PARTIAL PASS with bounded M15/H1 coverage, scheduler completion and full recovery-history coverage NOT VERIFIED.
- T1: external collector exact SHA `4566cffbbcf8495182abbc0d3496fdc65709ac14`; manual exact-SHA validation 7/7 commands and 88 tests PASS; GitHub Actions NOT VERIFIED; T1→T0/T2 NOT VERIFIED; activation NOT AUTHORIZED/PERFORMED.
- T2: HTTP Candle Client focused tests 45/45 PASS and Freqtrade 2026.9 strategy-load smoke PASS; bounded 2026-11-09 loopback API/T2 context verification PASS; remote TLS/live endpoint and full T1 integration remain NOT VERIFIED.
- Dual-Strategy code already exists: Core RSI/ADX/Smart-DCA producer, independent AI/FreqAI decision path, strategy-scoped ledger tables, shared account risk/reservations/Kill Switch, 61 Core/AI dual-ledger test methods and paper-only workflow. No current-HEAD workflow result was established by this assessment.
- Critical static findings recorded:
  - DS-01: API `ledger()` constructs `PaperLedger` as MANUAL, then evaluate route submits with a strategy_id override. After dual-ledger migration, MANUAL writer rejects writes with `DUAL_LEDGER_MIGRATION_ACTIVE_MANUAL_WRITE_BLOCKED`; API route is not wired to the scoped writer.
  - DS-02: `core_decide()` reads `read_snapshot(db_path)` without `strategy_id="STRATEGY_CORE"`, so it reads legacy aggregate state rather than Core's own ledger.
  - DS-03: Core producer defaults to fixed `LEVERAGE=13` and `ENTRY_MARGIN_PCT=0.50`, conflicting with the current 1%-of-account-equity margin cap per new ENTRY/DCA and current leverage policy. Resolve sizing without changing RSI/ADX/Smart-DCA signal rules.
  - DS-04: Dual Ledger contract/migration docs have stale/inconsistent status statements relative to later implementation addenda and current code.
- Next permitted work: contract-level correction plan and test mapping for DS-01/DS-02; reconcile sizing for DS-03; append-only documentation status reconciliation for DS-04. Then request a bounded implementation approval. No code fix, workflow dispatch, VPS/runtime action, schema migration, T0 mutation, T1 activation or live trading was performed/authorized by this assessment.
- Branch continuity preserved; report and handoff only. No tests or workflow runs are claimed for this documentation increment.



### Dual-Strategy API/equity follow-up findings — 2026-11-11
- Second static pass appended to the baseline report; latest report blob: `743a752e7b27cf67f0ac06b3dadd9a286fb642f1`; addendum commit: `d8b164d682c828d7a53c2051afc7ec487e2afae9`.- Expanded DS-01:
  - `/v1/paper/cancel` uses the MANUAL ledger instance; the MANUAL compatibility path rejects cancellation of Core/AI-owned orders.
  - `/v1/equity` and the evaluate route use MANUAL `record_equity()`, which records legacy `paper_state` equity, not account-scoped dual-ledger mark/equity reconciliation.
  - A dedicated account-level mark/equity update and strategy-scoped cancellation path are required; account risk readiness must remain fail-closed until then.
- Acceptance mapping now includes scoped ENTRY/DCA/EXIT, owner-scoped cancellation, explicit Core/AI read models, account aggregate equity/funding/reservation reconciliation, and atomic account-wide Kill Switch admission behavior.
- Static-only; no endpoint/test execution, source code, workflow, VPS/runtime, DB or ledger mutation.


## Owner-approved Dual-Strategy DS-01 / DS-02 TDD increment — 2026-11-11

### Approval and boundary
- Owner explicitly approved implementation/TDD for DS-01 and DS-02, including Equity/account mark and cancellation paths, within paper-only scope.
- No VPS/runtime changes, no canonical T0 data changes and no real orders.
- This approval does not authorize migration activation, account cutover/funding reconciliation, deployment, DS-03 leverage/sizing changes or live execution.
- Stage II A2.3 / Ed25519 adapter remains **PAUSED BY OWNER**.

### Source and evidence
- Implementation/test source SHA: `4c8007e40f5c951a7644764756bf120c8b65c6d9`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Evidence report: `docs/evidence/DUAL_STRATEGY_AND_OPERATIONAL_BASELINE_2026-11-11.md`
- Evidence report commit: `9c7f8487447988ad8daa01efda7b0388db8f9e01`
- Evidence report blob: `34ad2ff64e8a2159fb6fe2f97c98438e695d4448`
- Dual Ledger CI: [42970058846](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42970058846), exact SHA `4c8007e40f5c951a7644764756bf120c8b65c6d9`; compile/focused/full regression PASS, **298 tests PASS**.
- Artifact ID: `13832762848`; SHA-256: `13a2f8ed2757beb61cdeb63f082725e82b8c66158c99b53479462482a403a81e`.
- T0 Single Writer Gateway: run `42969831047`, SHA `978f27b6418b0e350ebe851c74bcc498c350e7ba`, all jobs PASS.
- T2 Freqtrade 2026.9 strategy-load smoke: run `42969831103`, SHA `978f27b6418b0e350ebe851c74bcc498c350e7ba`, PASS.

### Implemented / verified in source and CI
- Core/AI API submission selects exact strategy-scoped writer only when all nine Dual Ledger migration versions/checksums are already applied.
- Scoped API ledger construction is read-only; it does not run migrations. No migration evidence => legacy path preserved. Partial/mismatched migration evidence => fail closed, never auto-migrate or silently fall back.
- Core decision reads `STRATEGY_CORE` explicitly once migration is owner-activated; legacy read path remains before activation.
- Cancellation uses persisted `paper_orders.strategy_id`; null/missing/unverified owner is rejected; Core/AI cancel is strategy-scoped.
- Account mark/equity reconciliation covers Core, AI, legacy adjustments, funding and active/partial reservations within one account transaction. Missing cutover/daily baseline keeps risk readiness false; no automatic cutover or baseline is created.
- `/v1/paper` returns separate account/Core/AI read models after migration.
- Kill-switch reset readiness checks Core and AI, all pending orders including unassigned legacy rows, and shared account risk readiness.

### Current status
- DS-01: **PASS — source/CI scope**.
- DS-02: **PASS — source/CI scope**.
- Runtime migration/activation, account cutover, funding readiness and VPS deployment: **NOT AUTHORIZED / NOT PERFORMED / NOT VERIFIED**. Shared Risk Engine remains fail-closed until a separately approved account reconciliation/cutover.
- DS-03 Core sizing/leverage: **BLOCKED**, unchanged.
- DS-04 contract/document status reconciliation: **OPEN**.
- T0 canonical DB, leases/fencing, VPS processes, T1 activation, credentials, exchange state and live orders were not changed. CI used isolated temporary paper databases only.

### Next permitted step
- Conduct a read-only code review of the exact DS-01/DS-02 source and reconcile the remaining DS-04 documentation status. Do not activate migrations, perform account cutover, deploy to VPS or change DS-03 without separate owner approval.


### Final DS-01 / DS-02 source review and verification update — 2026-11-11

- Final implementation/test source SHA: `8d9eee6cd503237f8b8a398fcaf1e055dfa9d644`.
- Final Dual Ledger CI: [42971136555](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42971136555), exact SHA above; compile/focused/full regression PASS, **300 tests PASS**.
- Artifact ID `13833202840`; SHA-256 `0eb0bbb6ad5bfbca27c9665e06548a11dba37e2d25d4939ea891301a6054f506`.
- T0 Single Writer Gateway: run `42970832396`, SHA `e99daf3f491014aa302af52629d0598d6404dbaa`, all jobs PASS.
- T2 Freqtrade 2026.9 strategy-load smoke: run `42970832365`, same SHA `e99daf3f491014aa302af52629d0598d6404dbaa`, PASS.
- Code review covered correctness, readability, architecture, security and performance. Account mark logic was extracted to `paper_execution/account_equity.py`, with separate ledger-total and reservation-total helpers. No dependency added; no Critical/Required DS-01/DS-02 finding remains.
- Final evidence report commit: `78676df074c49e8c1cca75f281300e195d06be8f`; report blob: `f824d34c09544b6b15f40695e6fe5ad7d320ce5c`.
- DS-01/DS-02 remain **PASS — source/CI scope only**. Runtime migration, account cutover, funding proof, VPS activation/deployment and live execution remain **NOT AUTHORIZED / NOT PERFORMED / NOT VERIFIED**. Risk remains fail-closed until a separately approved account cutover.
- DS-03 remains **BLOCKED**; DS-04 remains **OPEN**. Stage II A2.3 remains **PAUSED BY OWNER**.
- Next step: preserve this evidence and proceed only with read-only DS-04 documentation reconciliation or a separately scoped owner proposal. Do not migrate/activate the runtime, alter T0, change Core sizing/leverage or enable live execution without separate approval.



## DS-04 Dual Ledger documentation reconciliation — 2026-11-11

- Documentation-only, append-only reconciliation completed and recorded in
  `docs/evidence/DUAL_LEDGER_DOCUMENTATION_STATUS_RECONCILIATION_2026-11-11.md`.
- Report commit: `320abd075eb12814507762e3aac70ef903093323`.
- Appended current bounded-approval / verification status to:
  - `docs/architecture/DUAL_LEDGER_CONTRACT.md`
    (commit `6e90c95a6f801d1b8edf2aa4295bc721f0799fd5`);
  - `docs/architecture/DUAL_LEDGER_SCHEMA_MIGRATION_PLAN.md`
    (commit `2c077effb9cd4d09f7642204c0dda900c10aa055`);
  - `docs/architecture/DUAL_LEDGER_OPEN_DECISIONS_PROPOSAL.md`
    (commit `39bc98069d1fbc5f0de6fdd28b35170045bd447e`).
- Historical status statements, design decisions, migration checksums, schema
  versions and earlier evidence were retained; dated addenda clarify that the
  later owner approval covers only DS-01 / DS-02 source/test implementation.
- DS-01 / DS-02: PASS — source and isolated CI only, exact SHA
  `8d9eee6cd503237f8b8a398fcaf1e055dfa9d644`, run
  [42971136555](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42971136555),
  300 paper_execution tests PASS, artifact `13833202840`,
  SHA-256 `0eb0bbb6ad5bfbca27c9665e06548a11dba37e2d25d4939ea891301a6054f506`.
- DS-04: PASS — documentation-only reconciliation.
- Full Dual Ledger contract acceptance: NOT VERIFIED. Persistent DB migration,
  account cutover, funding readiness, runtime activation/deployment and live
  execution remain NOT AUTHORIZED / NOT PERFORMED / NOT VERIFIED.
- DS-03 remains BLOCKED; Stage II A2.3 / Ed25519 adapter remains PAUSED BY OWNER.
- No source code, tests, workflows, SQLite DB, T0 canonical data, lease/fencing,
  VPS process, credentials or exchange state was changed in this documentation
  increment.
- Next step: prepare a separate owner proposal for DS-03 Core sizing/leverage
  policy or await another explicit scope. Do not perform account migration,
  cutover, runtime activation, T0 changes, deployment or live execution without
  separate approval.



## DS-03 Core sizing/leverage policy proposal prepared — 2026-11-11

- Proposal: `docs/architecture/CORE_SIZING_LEVERAGE_POLICY_PROPOSAL.md`.
- Proposal commit: `e76499d34d791e1592823bf52935ab0af80d15b2`.
- Read-only source basis:
  - `pipeline/core_strategy.py` blob
    `b4266fc05ea41355ba9dcf6f15cb7b5a6d3800b0`;
  - `paper_execution/ledger.py` blob
    `38f71f974068eb12c56dd2174a4200d07c4c98bf`.
- Confirmed static mismatch: Core defaults to 13x leverage and 50% ENTRY margin basis; shared risk admission separately caps each exposure-increasing order at 1% of current account equity and derives notional using ledger leverage.
- Core leverage also affects ROE-based TP, DCA and stop trigger price thresholds. Therefore a leverage decision may alter behavior even if RSI/ADX predicates are untouched.
- Proposal asks owner to decide Core leverage policy, ROE threshold semantics and explicit per-ENTRY/per-DCA sizing contract. No numerical Core leverage range is assumed; AI 1x–3x policy is not automatically transferred to Core.
- DS-03 remains BLOCKED. No source/test/workflow/runtime change was made for this proposal.
- Next gate: owner decision on D1-D3 in the proposal. Only then prepare the bounded TDD implementation plan; do not change Core sizing/leverage or run backtests without separate approval.



## DS-03 Core leverage and order sizing — owner approval and TDD completion (2026-11-11)

### Owner decision
- Owner approved fixed Strategy Core leverage **13x**.
- Preserve existing leverage-adjusted ROE semantics and thresholds without reinterpretation: TP **+5 ROE**, DCA **-20 ROE**, Soft SL **-35 ROE**, Emergency SL **-90 ROE**.
- Every new Core ENTRY and every exposure-increasing Core DCA receives a fresh admission-time margin budget of **1% of current reconciled Account Equity**.
- Shared Risk Engine remains the final ACCEPT/REJECT authority and independently recalculates the admission budget at submit time.
- AI leverage/configuration remains separate; this increment does not alter AI strategy logic or AI ledger leverage configuration.
- Paper-only. No live execution, database migration/cutover, backtest, VPS operation, deployment, T0 canonical data change or T1 activation.

### Implementation
- Source commit: `6ef0d7456b2791fae73bfea8855ee30482774673`.
- Changed source blobs:
  - `pipeline/core_strategy.py`: `c14e76f2cecb9f8aca54db263ded1ff17881cb24`;
  - `pipeline/api.py`: `d3f587c795daa89b54beb5783b89f14acc189df0`;
  - `paper_execution/ledger.py`: `21ff7ce8446381baaa4102553fc8f69a8bbacbb3`;
  - `risk_policy.py`: `91b46513041033cbcd7e939ed081b71714c82ff3`.
- Core leverage is a fixed policy constant, independent of the generic `LEVERAGE` environment setting. Core ledger construction rejects any leverage other than 13x.
- Core sizing uses the reconciled account-wide equity snapshot only when `riskReady=true`; unavailable/unready equity preserves the signal result but emits no trade intent.
- ENTRY and DCA candidates are sized against the same visible limit price used by the ledger, using a fresh 1% margin budget and fixed 13x leverage. Persisted `initialMarginQuote` is no longer used as the DCA budget.
- The shared ledger admission check uses the common 1% policy constant, records the margin policy in its risk-config version, and remains authoritative if account equity changes between signal generation and admission.
- No RSI, ADX, Smart-DCA eligibility, TP, DCA, Soft SL or Emergency SL predicate/threshold was changed.

### TDD and CI evidence
- RED source commit: `92eb3f737d96e9edbfe0e8cf679ed64db79f0ba4`.
- RED workflow run [42974245487](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42974245487): compile PASS; 229 focused tests executed with the new sizing contract producing 2 errors and 1 assertion failure as expected. Artifact `13834382898`, digest `sha256:247f12f8a84b9126e0c6b599dce8df50fd29755a943d022a0d0898f010f2303f`.
- Final Dual Ledger workflow run [42975606884](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42975606884), exact source SHA `6ef0d7456b2791fae73bfea8855ee30482774673`: focused contract **237/237 PASS**; full `paper_execution` regression **300/300 PASS**; compile PASS; isolated paper-only preflight PASS.
- Final Dual Ledger artifact: ID `13834194926`, name `dual-ledger-red-evidence-6ef0d7456b2791fae73bfea8855ee30482774673`, digest `sha256:66403ab6b9c8079e2d9f3b04dcfc650709a64abd77e62554e6a54c2c101cd5c4`.
- Pinned Freqtrade 2026.9 strategy-load smoke [42975606665](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42975606665): SUCCESS at the same exact source SHA. Artifact ID `13835351582`, digest `sha256:b76352b07321f3921dcdcf8cacfefd88103f366078188fb2a212648aadc17d0e`.
- Intermediate failures were corrected before the final exact-SHA PASS: run `42974877655` exposed a missing `os` import; run `42975018595` exposed incomplete-history argument compatibility and account-risk snapshot fail-closed handling. The final run above includes both regressions.

### Review and disposition
- Five-axis self-review (correctness, readability, architecture, security, performance): no Critical or Required finding remains. The shared policy constants were placed in a root-level module to avoid a pipeline-to-execution package dependency. No dependency was added.
- DS-03: **PASS — source and isolated CI scope only**.
- Persistent DB migration, account cutover/funding readiness, VPS activation/deployment, live execution and backtest acceptance: **NOT AUTHORIZED / NOT PERFORMED / NOT VERIFIED**.
- T0 canonical candles, lease/fencing, T0 runtime, T1 activation, credentials and exchange state were not modified.
- Next permitted work: read-only review of AI Strategy leverage/configuration propagation and its independent signal-to-Shared-Risk-Engine path. Any AI sizing/code changes require a separately bounded TDD scope and approval.



## AI Strategy independent-path read-only audit — 2026-11-11

### Snapshot and scope
- Repository source reviewed: `6ef0d7456b2791fae73bfea8855ee30482774673`.
- Current branch documentation head before this addendum:
  `a9d9360ed1ea9e530ab6e4eed23a402c9baef755`.
- Read-only inspection only: no source, tests, workflow, DB, T0, VPS, runtime,
  credentials, ledger state or exchange state changed.

### Findings
- Independent AI signal path: **PASS at source level**. `signal_snapshot()`
  calls `decide()` and `core_decide()` separately. Existing
  `test_core_producer_waits_on_incomplete_history_without_suppressing_ai`
  verifies Core WAIT while AI remains BUY.
- Separate AI ledger routing: **PASS at source level, integration coverage PARTIAL**.
  In dual-ledger mode the evaluate route chooses `AI_FREQAI` and submits to
  that scoped ledger. Existing tests verify the AI ledger factory and ledger
  separation, but no dedicated end-to-end AI evaluate-route test was found.
- Shared Risk Engine: **PASS at source level, runtime NOT VERIFIED**. AI
  submissions use the same account equity, 1% margin reservation, gross
  exposure, readiness, liquidity and Kill Switch checks when dual-ledger mode
  is active. Risk readiness remains fail-closed without verified account
  cutover/funding evidence.
- AI leverage policy: **BLOCKED / NOT IMPLEMENTED**. `pipeline/api.py`
  passes generic `LEVERAGE` to the AI ledger; `PaperLedger` only requires
  positive leverage for `AI_FREQAI`. There is no AI-specific 1x–3x bound or
  dynamic leverage value in the decision/submit contract.
- Confidence calibration: **BLOCKED / NOT IMPLEMENTED**.
  `freqai_bridge/exporter.py` emits `predictedReturn`, model/strategy
  provenance, training dataset and training cutoff; it does not emit calibrated
  confidence or calibration provenance. `pipeline/decision.py` gates on
  predicted return and observed taker-flow direction, not calibrated confidence.
- AI sizing: **BLOCKED / NOT IMPLEMENTED**. `decide()` uses fixed
  `PAPER_TARGET_BASE` (default 0.001 BTC); it does not size from current
  Account Equity and an AI-specific leverage value. The Shared Risk Engine can
  reject an over-budget candidate, but it does not resize that candidate.
- Paper-only research boundary: **PASS at source level**. The FreqAI research
  strategy is dry-run restricted, emits no native entry/exit signals and
  `confirm_trade_entry()` returns false. The separate pipeline AI path emits
  PAPER intents only.

### Source evidence
- `pipeline/decision.py`: `evaluate(... target_base="0.001")`; prediction
  validation checks predictedReturn, model/data provenance and doPredict.
- `pipeline/api.py`: AI decision path uses `decide()`; AI ledger leverage
  comes from generic `LEVERAGE`; dual-mode submission selects
  `ledger(strategy_id="AI_FREQAI")`.
- `paper_execution/ledger.py`: account admission uses 1% current equity and
  the ledger's `self.leverage`; Core is now pinned to 13x, but AI has no
  min/max leverage enforcement.
- `freqai_bridge/exporter.py`: prediction artifact has predictedReturn and
  training provenance, no calibrated confidence.
- `freqai_bridge/ChartProFreqaiResearch.py`: dry-run research strategy with
  native entries/exits disabled.
- `pipeline/test_api.py`: Core WAIT does not suppress AI BUY.
- `paper_execution/test_dual_strategy_api_red.py`: verifies AI scoped ledger
  construction; no AI evaluate-route integration test.
- `pipeline/test_decision.py` and `paper_execution/test_dual_ledger_red.py`
  cover AI signal validation and dual-ledger risk primitives, but not AI
  dynamic leverage/calibration.

### Next bounded task
Prepare a separate AI contract/TDD proposal before implementation:
1. Freeze the AI calibrated-confidence and provenance schema.
2. Freeze the selected AI 1x–3x leverage mapping and fail-closed conditions.
3. Size AI ENTRY/DCA from current reconciled Account Equity, the AI leverage
   value and the same execution limit price used by the ledger.
4. Pass the leverage/config snapshot into the AI reservation; reject values
   outside the approved range. Keep the shared 1% margin gate and Kill Switch
   authoritative.
5. Add an end-to-end API test proving AI BUY can proceed while Core is WAIT,
   is written only to AI_FREQAI ledger, and is rejected on missing calibration,
   invalid leverage, stale account equity or shared-risk denial.

No AI implementation, calibration change, DB migration, runtime activation,
deployment, exchange connectivity or live execution is authorized by this
read-only audit.


## AI Strategy contract and TDD RED preparation — 2026-11-11

Owner approved recording the independent AI Strategy contract and preparing test-only RED work. Contract: `docs/architecture/AI_STRATEGY_CONTRACT.md`. Evidence: `docs/evidence/AI_STRATEGY_CONTRACT_TDD_RED_PREPARATION_2026-11-11.md`.

- Reviewed baseline source: `6ef0d7456b2791fae73bfea8855ee30482774673`.
- Contract commit: `2f498b33953cb3ecf2c66c242000e9e0de2048ce`.
- Test-only commit: `d0f1b014463e6ad1eff36425a18411233c484ba2`.
- E2E RED test commit: `550a529c2a726f82911602aee207f0df32c78eb9`.
- Evidence report latest commit: `aa4eb61b86a80a51aa2eaa940778d63a334750b5`.
- Contract covers calibrated confidence/provenance, versioned `C_min`, AI leverage [1x,3x], 1%-equity margin sizing, execution-price/lot-step sizing, AI ledger isolation and Shared Risk Engine/Kill Switch authority.
- Initial five RED test methods cover missing/invalid calibration, provenance, AI admitted leverage vs generic `LEVERAGE`, equity sizing and missing/non-positive equity.
- RED test execution: **NOT VERIFIED**. Container could not resolve `github.com` to obtain a local checkout. GitHub commit status query returned no checks for the initial test commit; no workflow run/artifact verified for final test SHA.
- E2E AI BUY while Core WAIT → AI ledger only → Shared Risk Engine denial RED test is present in `paper_execution/test_dual_strategy_api_red.py` at SHA `550a529c2a726f82911602aee207f0df32c78eb9`.
- No GREEN implementation, numerical `C_min`, calibration training, DB migration/cutover, backtest/OOS acceptance, feature activation, VPS/runtime, deployment, exchange connectivity or live trading authorized/performed.
- No T0/T1/T2 runtime or canonical data changed.

Next: execute both focused RED test files in GitHub Actions against exact SHA `550a529c2a726f82911602aee207f0df32c78eb9`; inspect and correct test-only issues, then request separate approval before GREEN implementation.


### AI Strategy TDD RED scope update — 2026-11-11

- Added an API/ledger integration RED test in `paper_execution/test_dual_strategy_api_red.py`: AI BUY remains visible while Core is WAIT; the API routes the candidate to `AI_FREQAI`; Shared Risk Engine rejects it while account risk is unready; Core position/orders remain unchanged.
- E2E test commit and exact source SHA: `550a529c2a726f82911602aee207f0df32c78eb9`.
- Combined GitHub commit-status query for this SHA returned no checks. Test execution remains **NOT VERIFIED**; container could not resolve `github.com` to clone the repository. No RED result, workflow run or artifact is claimed.
- Evidence report final revision: `aa4eb61b86a80a51aa2eaa940778d63a334750b5`.
- Next step remains: run the focused test files in GitHub Actions against exact SHA `550a529c2a726f82911602aee207f0df32c78eb9`, inspect/repair test-only issues, then seek separate approval before any GREEN implementation.


## AI Strategy automated RED workflow and first verified execution — 2026-11-11

- Owner approved automated test execution. Added `.github/workflows/ai-strategy-contract-red.yml` on the existing branch; no new branch or PR.
- Workflow commit: `be4e59d0ca0c8d764ea2fffe63234d18cd9497fc`; final workflow blob: `c0b82a4d9ef222c836b7081889206e2b4c12459b`.
- Trigger: push changes to either focused AI RED test or related AI decision/API/ledger/risk modules on this branch; manual `workflow_dispatch` supported. Python 3.12, exact `${{ github.sha }}` checkout, compile, focused unittest, and SHA-named artifact. Read-only GitHub token; empty DB/exchange credential environment; no external services.
- Test-only correction commits after initial workflow run: `14e532d4f3de6bcdec8c73c079e5521835cd1ff7`, `084b13df016dcc455f9567b9898420e7e9f91c4c`, `0c049a9b37c69cefb6a5117531c64ac579075f5e`, `747dba7e0b264547b72edc52c941357362696804`, final test SHA `aa7897520b5435ff4c981b3f2ab8a6710f811eea`. No production code changed.
- Final AI RED workflow run [42989566675](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42989566675), exact SHA `aa7897520b5435ff4c981b3f2ab8a6710f811eea): paper-only preflight PASS; dependency install PASS; compile PASS; **36 tests, 23 assertion failures, 0 errors**. Workflow conclusion FAILURE is expected because the tests are intentionally RED before GREEN implementation.
- RED findings confirmed: calibrated confidence/provenance is not enforced; AI admitted-leverage interface is missing; AI ledger does not enforce 1x–3x bounds; equity-based AI sizing and stale-equity fail-closed interface are missing. The E2E AI BUY while Core WAIT → AI ledger only → Shared Risk Engine rejection test passes at isolated test scope.
- AI RED artifact ID `13841700390`, digest `sha256:bcddb274a58013060af6293604abee08a5d11d304dc2c4a0e50ebeb852df3445`.
- Existing Dual Ledger workflow [42989566780](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42989566780) at the same exact SHA: focused 238 tests PASS; full `paper_execution` regression 301 tests PASS; compile and isolated paper-only preflight PASS. Artifact ID `13841126612`, digest `sha256:aaa0c3c4a9ccd59360c718b2748cfd7077190a84c29dd8e8b298a9ada35963c0`.
- Evidence report update commit: `e96ea5d8857e7367f49fad857f710580df7e5644`.
- Current disposition: workflow automation PASS; AI contract RED confirmed; E2E independence/ledger/risk-denial test PASS; Dual Ledger regression PASS. GREEN implementation remains NOT AUTHORIZED / NOT STARTED. No numerical `C_min`, calibration/OOS acceptance, migration/cutover, backtest acceptance, feature activation, VPS/runtime, deployment or live execution is authorized.
- No T0 canonical data, T1 activation, T2 runtime, DB, credentials, exchange state or deployment state changed.

Next: review and prioritize the 23 RED assertions, freeze remaining AI API contract details, then request separate owner approval before GREEN implementation.


## AI Strategy RED triage and API proposal — 2026-11-11

- Read the latest handoff before continuing. Reviewed the AI contract, exact RED test source and GitHub run logs.
- Exact RED baseline remains `aa7897520b5435ff4c981b3f2ab8a6710f811eea`, run [42989566675](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42989566675): 36 tests, 23 assertion failures, 0 runtime errors.
- Classified 23 failures:
  - P0 calibration fail-closed: 17 (missing calibrated confidence 1; invalid/non-finite/bool confidence 6; missing calibration provenance fields 10).
  - P0 AI leverage isolation/bounds: 4 (missing explicit admitted-leverage API 1; AI ledger accepts 0.99x, 3.01x and 13x 3).
  - P0 equity sizing/readiness: 2 (no decision sizing interface and no missing/stale-equity behavior).
- Created proposal-only `docs/architecture/AI_STRATEGY_API_CONTRACT_PROPOSAL.md`, commit `b62f0c3de6e72c5f8419f1cb7da062389a8af80b`. It proposes a pure decision function plus server-created immutable admission context (versioned AI policy, reconciled account risk, instrument rules and AI-ledger position), explicit AI admitted leverage, and behavioral API-level tests instead of permanent signature introspection.
- Proposal status: **OWNER REVIEW REQUIRED**. It does not amend the owner-approved AI Strategy contract, authorize test changes or authorize GREEN.
- Additional RED coverage proposed: C_min/leverage mapping boundaries; trusted calibration artifact hash, model/dataset/horizon matching, temporal leakage, calibration freshness/sample thresholds; lot rounding and min quantity/notional; AI-only DCA; Shared Risk Engine/Kill Switch no-partial-reservation; idempotent replay; Core 13x and strategy regression.
- Open owner decisions: numerical C_min; calibration sample/period/age thresholds; trusted calibration artifact registry; account-risk snapshot provider/freshness contract; instrument-rule source; AI DCA v1 eligibility; immutable snapshot persistence shape.
- Evidence report triage update commit: `f6d4000c6bd7a6421349319754acdd60ac879499`.
- Disposition: RED triage PASS — analysis/documentation only. API proposal pending owner review. GREEN NOT AUTHORIZED. No production source, test source, DB/schema, migration, T0/T1/T2 runtime, VPS, credentials, deployment or exchange state changed.

Next: owner review the API proposal and resolve open design decisions. Only then, seek separate approval for test-only refinement; GREEN implementation remains a separate approval gate.


## AI Strategy API Contract owner approval — 2026-11-11

- Owner explicitly approved `docs/architecture/AI_STRATEGY_API_CONTRACT_PROPOSAL.md` as the design basis for the next RED test-refinement gate.
- Approval/documentation commit for proposal: `a7f8ca579ff7990eca3f640e1d496608c0ad36f4`; approved proposal blob: `65c3e5a6102cde6f7d51784fd9638f14aec3269e`.
- Evidence record commit: `e15671302bed4a4c142ee2439c21ed6c6236673c`; evidence blob: `e5b95d6eb93abdcd31e66b97524699c78daa2d2b`.
- **Gate A — API Contract design: APPROVED.**
- **Gate B — TDD RED refinement: AUTHORIZED, TEST-ONLY.** Replace brittle signature-introspection sentinels with behavioral API/provider-boundary tests and add missing deterministic cases. Preserve intentional RED failures where production behavior is absent. No production-source edits.
- Do not select numerical `C_min` or invent calibration sample/period/age thresholds, registry/provider choices, instrument-rule source, AI DCA v1 eligibility or snapshot persistence policy. Test fixtures must be labeled as fixtures, not production defaults; unresolved mandatory policy/provider inputs remain fail-closed.
- **GREEN implementation: NOT AUTHORIZED.** No production changes, schema/database work, migration/cutover, calibration training or OOS acceptance, model changes, backtest acceptance, feature activation, VPS/T0/T1/T2 runtime, deployment, exchange connectivity or live orders.
- Existing RED baseline remains run [42989566675](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42989566675), exact source SHA `aa7897520b5435ff4c981b3f2ab8a6710f811eea`: 36 tests, 23 assertion failures, 0 runtime errors. This approval record does not claim a new test run or CI result.
- No T0 canonical data, T1 activation, T2 runtime, credentials, deployment or exchange state changed.

Next: perform only the approved test-source refinement on this existing branch, run the existing AI RED GitHub Actions workflow against the resulting exact SHA, record all tests/artifacts, then stop before GREEN and seek separate approval.


## AI Strategy RED test-only refinement — 2026-11-11

- Gate A API Contract approval remains in force; approved proposal blob `65c3e5a6102cde6f7d51784fd9638f14aec3269e`.
- Gate B test-only refinement was started on the same active branch. Test commits: `eaf441c97835efba8d7c8d8f25bd01d77b5612d2`, `ae244d7544a14182ac21dc7853eb55e15a84679e`, and `dd1b088a763276f5510f99166ba175c13f70e0d9`.
- Latest test source SHA: `dd1b088a763276f5510f99166ba175c13f70e0d9`. Tests now exercise the admission-context boundary behaviorally instead of relying on signature introspection; add calibration, confidence-policy fixture boundaries, leverage mapping, freshness/readiness, instrument sizing, Kill Switch, Core leverage and no-partial-risk-reservation assertions.
- Numeric values in tests are explicitly isolated fixtures only; they do not set production `C_min` or calibration policy. Trusted registry/provider identity, exact manifest matching fields, AI DCA v1 eligibility and immutable reservation snapshot/idempotency remain deferred pending owner/provider contract decisions.
- Production source was not changed. No DB/schema, migration, T0/T1/T2 runtime, VPS, deployment, credential, exchange or live-order changes.
- Evidence report update commit: `870e96ea2924b83b9f04a37434b5f871244c6e3b`; evidence blob `7a366ae7dadfefc3bc8c74da1fe1325dd1b6857b`.
- GitHub combined commit status for exact test SHA `dd1b088a763276f5510f99166ba175c13f70e0d9` returned no statuses; available workflow-run lookup did not return push-triggered runs. Refined-suite CI, test counts and artifacts are **NOT VERIFIED**; do not infer a run from the push.
- Historical RED baseline only: run [42989566675](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42989566675), exact SHA `aa7897520b5435ff4c981b3f2ab8a6710f811eea`, 36 tests / 23 assertion failures / 0 runtime errors.
- Current disposition: Gate A **APPROVED**; Gate B test-source refinement **WRITTEN / CI NOT VERIFIED**; GREEN **NOT AUTHORIZED**.

Next: retrieve the push-triggered AI RED workflow result for exact SHA `dd1b088a763276f5510f99166ba175c13f70e0d9`, inspect compile and test logs, correct test-only defects, record exact run/artifact, and stop before GREEN.


## AI Strategy RED exact-SHA verification — 2026-11-11

- Gate A remains **APPROVED**; Gate B remains **TEST-ONLY**. No GREEN authority.
- Refined RED workflow run [42991140429](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42991140429), event `push`, branch `feature/t0-centralized-data-feeder-p1-20261101`, exact checkout SHA `dd1b088a763276f5510f99166ba175c13f70e0d9`.
- Job `130424044648`: setup/checkout/Python 3.12/paper-only preflight/dependency installation/compile/artifact upload **PASS**; focused RED test step **FAILURE as expected**.
- Compile `AI_STRATEGY_RED_COMPILE=PASS`; test result **45 tests, 52 assertion failures, 0 errors**. Current missing behaviors confirmed by RED include the `admission_context` decision boundary, explicit AI admitted leverage API, and AI ledger [1x,3x] bounds. Positive BUY/sizing/mapping tests remain RED until GREEN implementation.
- In the same run, Core fixed-13x regression **PASS** and AI BUY while Core WAIT → AI ledger only → Shared Risk Engine rejects unready account risk → no reservation **PASS**.
- Artifact ID `13841349049`, name `ai-strategy-contract-red-dd1b088a763276f5510f99166ba175c13f70e0d9`, 4,143 bytes, GitHub digest `sha256:7e2e5048db147243eaade59aebdb01ce0245fdcf1a9062abd7dc416cb7ac64e4`, expires `2026-11-18T08:57:31Z`. Payload bytes not independently downloaded/re-hashed.
- Evidence report commit: `34b30d942580541e24ffdec9345835beb1c9ebee`; evidence blob `dd0f40923f0fb332d70edae51e15dc97ab7b845c`.
- Fixture `confidenceMin=0.6`, sample count `100`, calibration period `100ms`, and max age `60000ms` are test-only values, not production defaults or owner selection. Trusted artifact registry, exact manifest matching, AI DCA v1 eligibility and immutable snapshot/idempotency remain deferred until their providers/contracts are resolved.
- No production code, database/schema, migration, T0/T1/T2 runtime, VPS, deployment, credentials, exchange state or live orders changed.
- Disposition: Gate A **APPROVED**; Gate B **RED TESTS EXECUTED / INITIAL SUITE NEEDS REFINEMENT**; GREEN **NOT AUTHORIZED**.

Next: review test log for brittle/overbroad RED assertions, refine only test sources and re-run exact-SHA GitHub Actions; do not cross into GREEN or select C_min.


## AI Strategy RED assertion-quality correction — 2026-11-11

- Review found the prior 52 failures at SHA `dd1b088a763276f5510f99166ba175c13f70e0d9` were inflated by repeated synthetic `ADMISSION_CONTEXT_UNSUPPORTED` fallback results; they were not 52 independent defects.
- Test-only commit `63ee390c17bf32ef8be2842aa2c9f183a4a37785` separates one explicit decision-boundary API failure from downstream tests that cannot run until `admission_context` exists. Commit `d37c0d4b554bbdcb936c419ebc134c6a8ff28783` fixes test helper forwarding of book fixtures.
- Latest verified run [42991526067](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42991526067), exact SHA `d37c0d4b554bbdcb936c419ebc134c6a8ff28783`, job `130425336828`: compile PASS; 46 tests, 5 assertion failures, 48 skips, 0 errors; setup/preflight/artifact upload PASS.
- Five meaningful RED assertions: missing decision `admission_context` API (1), missing explicit AI `admitted_leverage` factory API (1), and AI ledger fails to reject leverage 0.99x/3.01x/13x (3). Forty-eight skips are downstream calibration/equity/sizing/instrument cases not yet reachable through the absent decision API; they are not PASS.
- Core fixed-13x regression PASS; AI BUY while Core WAIT → AI-only ledger → Shared Risk Engine rejection on unready account → no reservation PASS.
- Artifact `13842490278`, `ai-strategy-contract-red-d37c0d4b554bbdcb936c419ebc134c6a8ff28783`, 3,251 bytes, digest `sha256:e1f0c8e5c7a9aff58062d7b499b2b7133190c0db710bc3e5a0f6f16d9608b019`, expires 2026-11-18 09:00:26Z; payload not independently re-hashed.
- Evidence report commit `5946b897b755b9b80b909f4908e2227296607795`, blob `fc17ebf04620066a3302e10d46b6870c97d808ef`.
- No production-source changes, no C_min/calibration policy selection, no schema/migration, backtest, VPS/T0/T1/T2 runtime, deployment, exchange connectivity or live orders.
- Disposition: Gate A APPROVED; Gate B RED refined and verified for current exposed interfaces; downstream behavior tests BLOCKED/SKIPPED pending GREEN/provider interfaces; GREEN NOT AUTHORIZED.

Next: inspect whether remaining RED test expectations can be made contract-level without implementing production behavior; otherwise freeze current test baseline and document skipped cases as deferred acceptance tests. Obtain separate owner approval before GREEN.


## AI Strategy GREEN implementation plan prepared — 2026-11-11

- Created `docs/architecture/AI_STRATEGY_GREEN_IMPLEMENTATION_PLAN.md`, commit `72f390f8536731def1605236dac56f0f1f9021fd`.
- Status: PLAN ONLY / OWNER REVIEW REQUIRED. This records an ordered proposal: GREEN-0 provider/policy freeze; GREEN-1 pure decision admission boundary; GREEN-2 AI leverage isolation in API/Ledger; GREEN-3 existing Shared Risk Engine admission; GREEN-4 immutable reservation/replay evidence (separate schema gate if needed); GREEN-5 paper-only regression.
- Explicit blockers remain unresolved: trusted calibration registry and manifest compatibility; numerical C_min and calibration sample/period/age policy; account-risk snapshot provider; instrument-rule source; AI DCA v1 eligibility; immutable reservation snapshot persistence strategy.
- No production code, tests, workflow, database/schema, calibration/model, T0/T1/T2, VPS/runtime, deployment, exchange or live-order state changed in this planning step.
- Latest verified RED remains run `42991526067`, exact source SHA `d37c0d4b554bbdcb936c419ebc134c6a8ff28783`: compile PASS; 46 tests, 5 assertion failures, 48 skipped, 0 errors. Artifact `13842490278`; GitHub digest `sha256:e1f0c8e5c7a9aff58062d7b499b2b7133190c0db710bc3e5a0f6f16d9608b019`; artifact bytes not independently re-hashed.
- Current disposition: API Contract APPROVED; RED baseline VERIFIED with downstream tests SKIPPED/BLOCKED; GREEN plan WRITTEN; GREEN implementation NOT AUTHORIZED.

Next: owner reviews the GREEN implementation sequence and resolves GREEN-0 provider/policy decisions. Plan approval alone does not authorize production edits; obtain separate explicit GREEN gate authorization.


## AI Strategy GREEN-0 provider inventory — 2026-11-11

- Owner approved GREEN-0 inspection/documentation only. No GREEN implementation authority.
- Evidence report: `docs/evidence/AI_STRATEGY_GREEN0_PROVIDER_CONTRACT_FREEZE_2026-11-11.md`, commit `db6bc89db41cda48c58d1abf889cc584abd8a998`.
- Plan update: `docs/architecture/AI_STRATEGY_GREEN_IMPLEMENTATION_PLAN.md`, commit `59c4d983dc071b1d1d5f5862fdcafcf2603d87b1`.
- Existing account-risk read provider identified: `paper_execution.ledger::read_account_risk_snapshot`; it validates account equity/risk/funding state and a 30-minute mark freshness bound, and returns gross/reserved exposure, mark observation, dataset version and Kill Switch state.
- Existing final admission identified: `PaperLedger._submit_scoped` transactionally rechecks account risk/exposure, the 1% margin budget, strategy leverage and Kill Switch before reservation/fill. `risk_policy.py` supplies Core 13x and `ORDER_MARGIN_BUDGET_PCT=0.01`.
- Existing AI ledger position read identified: `read_snapshot(..., strategy_id="AI_FREQAI")`. Existing Kill Switch provider: `paper_execution.risk_control`.
- Calibration trust/manifest registry and calibrated-confidence artifact are not present in the reviewed prediction exporter/decision path. No authoritative BTCUSDT lot/tick/minimum-notional provider was identified in the reviewed AI admission paths. AI DCA event mechanics exist in the ledger, but no independent AI DCA trigger/eligibility policy is defined in the decision path. Existing idempotent intent replay does not yet establish immutable replay of the full AI calibration/equity/risk/instrument snapshot.
- GREEN-0 disposition: source inventory COMPLETE; provider/policy freeze PARTIAL/BLOCKED pending owner decisions G0-01–G0-07. Current 30-minute account-mark freshness is documented as existing behavior, not approved replacement policy. No numeric C_min or calibration thresholds selected.
- No tests or workflow were run. No production source/test changes, schema/DB/migration, calibration/model, T0/T1/T2 runtime, VPS, deployment, exchange connectivity or live orders changed.
- Latest RED evidence remains run `42991526067`, exact SHA `d37c0d4b554bbdcb936c419ebc134c6a8ff28783`: compile PASS; 46 tests, 5 assertion failures, 48 skipped, 0 errors. GREEN-1 through GREEN-5 remain NOT AUTHORIZED.
- Current GitHub commits for this update sequence: evidence `db6bc89db41cda48c58d1abf889cc584abd8a998`; plan `59c4d983dc071b1d1d5f5862fdcafcf2603d87b1`. Handoff update follows.
- Next: owner resolves G0-01–G0-07. Do not implement production code or schema until separate explicit approval names the GREEN gates.


## Latest owner decision — GREEN-0 (2026-11-11)

Owner approval recorded in the GREEN-0 evidence report and implementation plan:

- G0-04: reuse `read_account_risk_snapshot` and `PaperLedger._submit_scoped`; no parallel equity calculator or Shared Risk Engine. The existing 30-minute mark freshness is observed source behavior, not an approved AI freshness threshold. AI freshness semantics and immutable risk-policy version identity remain unresolved.
- G0-06: AI DCA is disabled in v1. AI Strategy is limited to independent LONG/SHORT ENTRY intents; any DCA capability requires a separately approved trigger/eligibility contract.
- G0-01/G0-02/G0-03/G0-05: AI trade admission remains BLOCKED pending trusted calibration registry/digest, provenance compatibility, evidence-based thresholds and authoritative versioned BTCUSDT instrument rules.
- G0-07: reservation snapshot design deferred; no schema/migration authorized.

This approval is design/documentation only. GREEN-1 through GREEN-5 remain NOT AUTHORIZED. No code, tests, schema, DB, migration, calibration, backtest, feature activation, runtime, VPS, deployment, exchange or live-trading action is authorized. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.


## Latest GREEN-0 read-only inventory — 2026-11-11

At source HEAD `723570f845c0f52ef5776218cc5486f8864e72f8`, the next read-only inspection found:

- No calibration artifact registry/manifest or calibrated-confidence provider in the inspected FreqAI exporter/decision/API paths. Current artifacts provide raw prediction and training provenance only; calibration admission remains BLOCKED.
- No authoritative instrument-filter provider in the inspected paths. The existing Binance USD-M connectivity probe calls `/fapi/v1/exchangeInfo` but only validates BTCUSDT contract status/assets, not tick/lot/minimum-notional filters. Hummingbot book depth is not instrument metadata.
- Binance USD-M `/fapi/v1/exchangeInfo` is a candidate for a future read-only adapter, not a verified implementation.
- G0-01/G0-02/G0-03/G0-05 remain BLOCKED. No network request, tests, workflow, code edits, DB/runtime/VPS/exchange actions occurred. GREEN-1..5 remain NOT AUTHORIZED.


## Latest work — GREEN-0 design contracts (2026-11-11)

Owner approved design/documentation and source-contract inspection only. Added two proposal documents:
- `docs/architecture/AI_CALIBRATION_ARTIFACT_CONTRACT.md`: trusted calibration registry/manifest, artifact digest, provenance compatibility, temporal OOS, calibrated confidence validation and fail-closed behavior. No trusted registry/provider, schema, calibration method, C_min or thresholds selected.
- `docs/architecture/BINANCE_USDM_INSTRUMENT_RULES_CONTRACT.md`: candidate public Binance USD-M `/fapi/v1/exchangeInfo` source, BTCUSDT filter requirements (PRICE_FILTER, LOT_SIZE, MARKET_LOT_SIZE scope, applicable notional filters), normalized snapshot/digest/version/freshness and fail-closed behavior. No adapter or network request.

Commits: calibration contract `65b22d179f037a6f595467bccea2425897189c9c`; instrument contract `9e2ee63f5bb6bcab3e953c24ffa40f9a4ee530ee`. These are design proposals only; no implementation spec is yet frozen for coding.

Current blockers: G0-01/02/03 calibration provider/provenance/policy; G0-05 authoritative instrument provider/filter/freshness policy; G0-07 reservation snapshot choice. G0-04 reuse and G0-06 AI DCA disabled v1 remain approved. GREEN-1..5 NOT AUTHORIZED.

No production code/test edits, tests, workflow, network/exchange calls, schema/DB/migration, calibration/model, T0/T1/T2 runtime, VPS, deployment or live orders occurred. Paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## Latest GREEN-0 verification — calibration trust and Binance filter semantics (2026-11-11)

- Calibration architecture reviewed. Recommended low-cost candidate for owner review: repository-backed append-only manifest/artifact registry, offline Ed25519 signing, pinned public key in verifier configuration, and explicit promotion/revocation. Keep private signing key outside repository, CI, VPS and runtime. Separate digest integrity, signer authorization and statistical/OOS validity. Calibration artifact holds score-to-probability transform/evaluation evidence; each prediction's calibrated confidence must reference exact artifact digest/version. No provider or key lifecycle selected.
- Official Binance USDⓈ-M documentation reviewed. Corrected instrument contract: zero in PRICE_FILTER fields disables the corresponding rule; LOT_SIZE arithmetic is `(quantity - minQty) % stepSize == 0`; MARKET_LOT_SIZE is market-order specific; PERCENT_PRICE requires fresh mark-price data; USDⓈ-M MIN_NOTIONAL schema is not to be conflated with Spot NOTIONAL; MAX_NUM_ORDERS/MAX_NUM_ALGO_ORDERS are account/open-order constraints.
- No live `/fapi/v1/exchangeInfo` request, no current BTCUSDT filter values, no adapter and no exchange connection. Documentation semantics VERIFIED; endpoint response/provider runtime NOT VERIFIED.
- G0-01/02/03 remain BLOCKED on registry/key/schema/OOS policy and numeric thresholds. G0-05 remains BLOCKED on owner source choice, live endpoint/response verification, dynamic mark-price dependency and freshness policy. G0-07 deferred. G0-04 reuse and G0-06 AI DCA disabled v1 remain approved.
- No production code/tests/workflow, schema/database/migration, calibration/model, T0/T1/T2 runtime, VPS, deployment or live orders changed. GREEN-1..5 NOT AUTHORIZED; paper-only and `AI_EXECUTION_ENABLED=false` remain.


## Latest owner decision — calibration registry architecture (2026-11-11)

Owner approved **GitHub append-only Registry + offline Ed25519 signing** as the selected architecture direction for calibration artifact trust.

- Registry records: immutable versioned manifests, calibration transform artifacts and OOS evaluation evidence.
- Signature: offline Ed25519 signing of the canonical manifest digest.
- Verification: future read-only consumers pin and verify the trusted public key.
- Governance: append-only approval/promotion, revocation, supersession and key lifecycle evidence.
- Key isolation: private signing key remains offline; never place it in repository, GitHub Actions/CI, VPS or runtime.

**Approval boundary:** architecture direction only. Registry path/schema, canonical serialization, key ceremony/rotation/revocation, verifier/CI/provider implementation, calibration method/OOS protocol, provenance compatibility and numeric thresholds are not yet frozen or authorized for implementation. No key or registry was created. G0-01/02/03 remain BLOCKED; GREEN-1..5 NOT AUTHORIZED.

No source code/tests/workflow, network/exchange, database, T0/T1/T2 runtime, VPS, deployment or trading activity occurred. Paper-only and `AI_EXECUTION_ENABLED=false` remain.


## AI Calibration Registry manifest and Ed25519 lifecycle design — 2026-11-11

Owner-requested scope completed as **documentation only** on the existing branch `feature/t0-centralized-data-feeder-p1-20261101`.

Added:
- `docs/architecture/AI_CALIBRATION_REGISTRY_MANIFEST_CONTRACT.md`: proposed immutable manifest/evaluation/event/signature record model, provenance, canonicalization, Git object evidence and explicit separation from T0 A2.2.
- `docs/architecture/AI_CALIBRATION_ED25519_KEY_LIFECYCLE_CONTRACT.md`: proposed offline ROOT/CALIBRATION_SIGNER/RECOVERY_AUTHORITY roles, key generation, custody/backup, public-key pinning, signing, rotation, revocation, compromise and recovery.
- `docs/evidence/AI_CALIBRATION_MANIFEST_AND_KEY_LIFECYCLE_DESIGN_2026-11-11.md`: scope, decisions, blockers and verification record.
- Linked both design contracts from `docs/architecture/AI_CALIBRATION_ARTIFACT_CONTRACT.md` and `docs/architecture/AI_STRATEGY_GREEN_IMPLEMENTATION_PLAN.md`.

Commits in this increment:
- Manifest contract: `90436bd56b577f39cccec6ee309ee69798218a88`.
- Key lifecycle contract: `aa5a5f5c75d7e2efb5744aeef5572596957346ce`.
- Evidence report: `5a5f9c709aa66ad2e918e4366d0c368ba17aff9f`.
- Contract/plan/handoff reference updates follow this record in the commit chain.

Design limits: manifest schema/canonicalization, signature statement/domain bytes, trust bootstrap, key tooling/custody, trusted-time and recovery topology remain NOT FROZEN. T0 A2.2 checkpoint-attestation policy/role/bootstrap is not inherited. GitHub history is not WORM or global freshness proof. SHA-256 integrity, signer authorization and statistical/OOS validity remain separate.

Verification: documentation changes only; no tests/workflow; no key generation/import, signing/verification, registry/provider, CI secrets, VPS/runtime, DB/T0/T1/T2, exchange request, calibration/model change or AI activation. No artifact/run produced. G0-01/02/03 remain BLOCKED; G0-05 BLOCKED; G0-07 DEFERRED; GREEN-1..5 NOT AUTHORIZED. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.

Next gate: owner review/approval of the manifest schema/canonicalization proposal and key hierarchy/recovery topology. Any key ceremony or implementation requires separate explicit approval.


## AI Strategy Research Gate R0 — owner-approved scope recorded (2026-11-11)

Owner approved a bounded research/evaluation workstream for an independent AI Strategy LONG/SHORT producer, including signals emitted while Strategy Core is WAIT. Approval covers protocol design and documentation only.

- Research contract: `docs/architecture/AI_STRATEGY_RESEARCH_EVALUATION_CONTRACT.md`, commit `cc64603fe944d1f7a7aa63ce70e03d6899000b2a`.
- Evidence report: `docs/evidence/AI_STRATEGY_RESEARCH_GATE_R0_2026-11-11.md`, commit `70e725a2b0a60a6ed0640525119276bc6c79f339`.
- R0 records point-in-time data rules, read-only T0 boundary, independent signal semantics, label/horizon contract, chronological train/validation/calibration/untouched-holdout protocol, purge/embargo, baselines, per-direction/Core-WAIT slices, calibration separation, economic-cost metrics and invalidation conditions.
- Strategy Core RSI + ADX + Smart DCA remains unchanged. AI DCA remains disabled in v1. AI signal generation must not depend on Core position/order/ledger state.
- R0 is RECORDED. R1 (owner review/freeze of exact dataset bundle, feature inventory, label/horizon, split schedule, execution-cost/fill assumptions and pre-registered thresholds) is PENDING. R2 offline experiment is NOT AUTHORIZED until R1 is frozen and a separate bounded execution approval is granted.
- No model training, calibration training, backtest, data export, code/test/workflow, DB/schema/migration, T0/T1/T2 runtime, VPS, deployment, exchange connectivity, feature activation, order or destructive data operation occurred. No tests/workflow/artifacts were produced.
- GREEN-1..5 remain NOT AUTHORIZED; numerical `C_min` and calibration thresholds remain unset. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.

Next: owner review of R1 research choices. Do not execute experiments until those choices are frozen and separately authorized.


## AI Strategy Research Gate R1 — freeze proposal recorded (2026-11-11)

Following owner approval of R0, a documentation-only R1 freeze proposal was added:
- Proposal: `docs/architecture/AI_STRATEGY_RESEARCH_R1_FREEZE_PROPOSAL.md`, commit `82f770adc8b2936243174b97e3e83a1ee46f1f63`.
- Evidence: `docs/evidence/AI_STRATEGY_RESEARCH_R1_FREEZE_PROPOSAL_2026-11-11.md`, commit `b11225bcca208ef6ef973b314b6dd03b84b239d7`.

Proposal recommends BTCUSDT M15 decisions with completed H1 context; an immutable read-only T0-derived bundle candidate `T0_M15_H1_DATASET_BUNDLE_V1); restricted trailing-only OHLCV features; a candidate 4-hour fixed-horizon directional label with cost-aware neutral band; expanding chronological validation, separate later calibration, untouched final holdout and purge/embargo; conservative fee/spread/slippage/funding/fill assumptions; flat/Core/simple-momentum baselines; and pre-registered statistical/economic thresholds.

Important: this is a proposal, not a frozen configuration. The candidate bundle's existence, digest, coverage and quality have not been verified. Exact feature schema, label threshold, split timestamps, cost parameters, sample minima and numerical acceptance thresholds remain unfrozen. Owner decisions D1-D6 are required, followed by artifact-level verification and final R1 freeze approval.

No dataset read/export/copy, T0 DB/runtime access or mutation, feature computation, label generation, model/calibration training, backtest, tests/workflow, code, DB/schema/migration, T0/T1/T2 runtime, VPS, deployment, exchange connectivity, feature activation, order or destructive data operation occurred. No test run or artifact produced. R2 remains NOT AUTHORIZED; GREEN-1..5 remain NOT AUTHORIZED. Strategy Core unchanged; AI DCA disabled v1; paper-only and `AI_EXECUTION_ENABLED=false` remain.

Next: owner review D1-D6 in the R1 proposal. Do not freeze numerical values or run R2 until source evidence is available and the complete R1 configuration plus separate R2 scope are explicitly approved.

### R1 owner decision — dataset integrity policy (2026-11-11)

Owner approved in principle a minimal SHA-256 + manifest policy for AI Research dataset identity, integrity comparison and provenance:- Stable dataset ID and manifest for each immutable bundle.
- SHA-256 per bundle file and manifest digest recorded with each experiment's source-code SHA/configuration.
- Dataset changes produce a new immutable version; no silent overwrite.
- SHA-256 alone does not prove source authenticity, correctness, completeness or statistical suitability.
- Keep implementation lightweight; no new service/infrastructure solely for this.

Recorded in R1 proposal commit `29139c86772320f52007dd1c2aed5487e2414f9c` and evidence commit `eb4316b22c6ae5a26880fff688a83f02d8196e81`.

Decision scope is limited to the integrity/provenance policy. It does not verify `T0_M15_H1_DATASET_BUNDLE_V1`, authorize T0 data access/export/copy, or freeze exact bundle digest/coverage/quality. D1 is PARTIALLY DECIDED; R1 remains NOT FROZEN; R2 remains NOT AUTHORIZED. No T0 data/runtime was accessed or changed; no tests/workflow were run.

Next: request a separately scoped approval for read-only verification of the candidate bundle's manifest, digest, coverage and quality. Do not begin feature extraction or R2 experiments.


### AI Strategy D1 — bounded read-only bundle inventory (2026-11-11)

Owner approved read-only verification of the candidate `T0_M15_H1_DATASET_BUNDLE_V1`. The completed pass was limited to GitHub repository metadata/tree and existing documentation; no T0 API, VPS/SSH, SQLite, runtime or dataset payload was accessed.

- Inspected branch HEAD: `03b1ab3478bbba2b5880271462ea94412667c9a9`.
- Recursive tree: 890 entries, not truncated.
- No candidate bundle path, candidate manifest or market-data payload for the AI research bundle was found in the inspected tracked tree.
- Existing P1.8 ZIPs are synthetic evidence artifacts and are not substitutes for the BTCUSDT M15/H1 research bundle.
- Existing L4 artifact pilot explicitly excludes VPS/SSH and canonical T0 SQLite access; it does not prove this bundle exists.

Evidence: `docs/evidence/AI_STRATEGY_D1_READ_ONLY_BUNDLE_VERIFICATION_2026-11-11.md`, commit `c17b26642253654bd684716f6db2069638c61d6b`.

Disposition: D1 **BLOCKED / PARTIALLY DECIDED**; candidate bundle SHA/manifest, UTC coverage, counts and quality remain NOT VERIFIED. This bounded repository inventory does not prove the bundle is absent outside GitHub. A separate scoped read-only access method/location for the actual published T0 bundle must be established before further verification. Do not create/export a bundle under this authorization. R1 remains NOT FROZEN; R2 remains NOT AUTHORIZED. No tests/workflow, data export/copy, T0 access/mutation, feature computation, model training, backtest, VPS/runtime/deployment, exchange or trading action occurred.

Next: identify the actual read-only publication/reference for the existing T0 bundle. If no bundle exists, request a separate owner decision before preparing one. Preserve T0 independence and all existing paper-only restrictions.


### AI Strategy D1 — T0 read-only API path assessment (2026-11-11)

Further repository review identified the documented T0 consumer boundary: authenticated GET `/v1/candles`, source implementation in `market_data/api.py`, with same-host loopback target documented as `http://127.0.0.1:8788`. The API contract exposes bounded M15/H1 windows, coverage/gaps, closed-candle and availability metadata, freshness, and a query-window `datasetVersion`.

Important distinction: API `datasetVersion` is a content-and-query hash for the exact response window, not a whole-bundle digest or manifest. API availability does not prove that an immutable AI research bundle `T0_M15_H1_DATASET_BUNDLE_V1` exists. Exporting API data into a bundle is a separate data-preparation action and is not authorized by the current verification approval.

Evidence: `docs/evidence/AI_STRATEGY_D1_T0_API_READONLY_PATH_ASSESSMENT_2026-11-11.md`, commit `44f383869a9e91f85525f85c4243185eb4e5a1ee`.

No live API request, token use, SSH/VPS access, SQLite read, data export/copy, bundle creation, tests/workflow, or runtime action occurred. Existing owner deployment protocol and live endpoint verification plan require explicit access/operator/origin/credential/request-budget controls. Current live endpoint, deployed source/config parity, M15/H1 API response and bundle manifest remain NOT VERIFIED. D1 remains PARTIALLY DECIDED / BLOCKED; R1 NOT FROZEN; R2 NOT AUTHORIZED.

Next: obtain sanitized owner/operator-supplied bounded API response metadata, or a separately scoped explicit authorization naming the operator, exact probe origin/endpoint, protected credential method and request budget. Do not create/export a bundle without separate approval. T0 remains independent and unchanged; paper-only and `AI_EXECUTION_ENABLED=false` remain.


## T0 L4 — GitHub artifact exact-readback increment (2026-11-11)

- Owner-approved read-only exact readback completed for the three artifacts produced by workflow run [42937191664](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42937191664), exact source SHA `8bda3c987e2145a636bbcc9d8609c5ea15a492b9` on `feature/t0-centralized-data-feeder-p1-20261101`.
- Artifact ZIPs were downloaded and independently SHA-256 hashed. All three digests matched GitHub metadata: manifest ID `13819680374` = `3509f2ce14aa174a45e4200ab44d13c7ae532841a74886256e9f6fe20ea55f71`; lineage ID `13818967476` = `155986f0f35d875fad02b6c50d0aab7aa43afdcd9191391f9ee0b832e975b67e`; repository inventory ID `13818163804` = `98fc7fca7123ae0a9e72bcf1f209032a57c24d97aa898aaa075eb7212f04c0fa`. ZIP CRC checks passed; no duplicate or unsafe member paths found. Internal JSON sidecars independently matched their payload digests; inventory has 40 unique paths and its declared byte total reconciles.
- Workflow jobs: lineage 12/12, artifact manifest 19/19, repository inventory 10/10; all SUCCESS (41/41 total).
- Detailed evidence: `docs/evidence/T0_L4_GITHUB_ARTIFACT_EXACT_READBACK_2026-11-11.md`.
- Disposition: GitHub exact-readback of these three artifacts **PASS**. L4M-01 remains PARTIAL / NOT VERIFIED because owner custody, complete package and VPS/copy assertions are absent. L4M-03 remains PARTIAL — SYNTHETIC/DESIGN ONLY because no signed canonical T0 checkpoint or authenticated latest-head anchor was verified. Aggregate L4-Minimum remains BLOCKED / NOT VERIFIED.
- No VPS/SSH, T0 API/SQLite, canonical data/runtime, signing/key operation, workflow dispatch, cleanup/deletion, or trading action occurred. T0 unchanged; paper-only and `AI_EXECUTION_ENABLED=false` remain.
- Next: reconcile this exact-readback result into the controlling L4 crosswalk/register, then continue only with separately authorized evidence acquisition. Do not infer owner custody or freshness from GitHub artifact integrity.


## L4 crosswalk/register reconciliation — GitHub exact-readback (2026-11-11)

- Owner-approved documentary reconciliation propagated the exact-readback result for workflow run [42937191664](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42937191664) into the controlling evidence records.
- Updated crosswalk: `docs/evidence/T0_L4_CONTROL_TO_SOURCE_CROSSWALK_2026-11-11.md`.
- Updated register: `docs/evidence/T0_L4_MINIMUM_NINE_CONTROL_EVIDENCE_ACQUISITION_REGISTER_2026-11-10.md`.
- Detailed exact-readback report: `docs/evidence/T0_L4_GITHUB_ARTIFACT_EXACT_READBACK_2026-11-11.md`, commit `a42a45060718d7c4bbce63f4c2756687a8231c6a`.
- Three output artifacts were independently downloaded and ZIP-hashed; all matched GitHub digests. This is a GitHub-side exact-readback PASS for those three outputs only, not a new source-allowlist entry or owner custody proof.
- L4M-01 remains PARTIAL / NOT VERIFIED; L4M-03 remains PARTIAL — SYNTHETIC/DESIGN ONLY; aggregate L4-Minimum remains BLOCKED / NOT VERIFIED. No control promoted.
- No VPS/SSH, T0 API/SQLite, canonical data/runtime, signing/key operation, workflow dispatch, cleanup/deletion or trading action occurred. T0 unchanged; paper-only and `AI_EXECUTION_ENABLED=false` remain.


## G0.2 — T0/T2 Git baseline and handoff freshness (2026-11-11)

Owner approved documentation-only baseline capture on the existing branch `feature/t0-centralized-data-feeder-p1-20261101`.

- Audit starting HEAD: `d1978d3606536bb6da2471ed6c94eaf20ffa7b6d`.
- `main` HEAD: `063f7a2eacd724f965a9723d0ae66cf95418c0fb`.
- Merge base: `f5b74affb8777953fa66d241784965fbb0e577ba`.
- Branch comparison: active branch is 3,015 commits ahead and 76 commits behind `main`; status `diverged`. The 76 main-only commits affect 13 paths. Their semantic classification is pending G0.3.
- PR #139 remains OPEN / DRAFT / NOT MERGED; head `7e635a6462c29456f1adb2e7ddcd01443909a5ac`, base `ff1f1768cab1b899494910df1b9ba0d98d35835f`, GitHub mergeable=false. Do not alter or merge it as part of this work.
- Exact-SHA Actions query for audit starting HEAD returned 0 workflow runs. CI for this SHA: NOT VERIFIED.
- Baseline evidence: `docs/evidence/G0_2_T0_T2_GIT_BASELINE_2026-11-11.md`, initial commit `b433573415c816215af84e4184b0c0fde2af5724`, wording-correction commit `e08b7b542b55db2221a2cb8740d9024d9e6497ad` (current baseline document).
- This handoff update commit: recorded in the G0.2 completion message; it is the new active branch HEAD after this update.
- G0.2: **PASS — documentation-only baseline recorded**. No source/test/workflow, T0/T1/T2 data/runtime, VPS, deployment, training, exchange, or trading changes. No workflow or artifact produced.
- G0 reconciliation remains **BLOCKED** pending G0.3 read-only semantic classification of the 76 main-only commits and a separate owner decision.

Next: perform G0.3 read-only classification only. Do not merge, rebase, cherry-pick, reset, force-push, recreate branches, or alter PR #139/T1 PR #1. Preserve paper-only posture and `AI_EXECUTION_ENABLED=false`.


## G0.4 — G0.3 classification evidence recorded (2026-11-11)

Owner approved G0.4 documentation-only update on the existing T0/T2 branch `feature/t0-centralized-data-feeder-p1-20261101`.

- G0.3 inspection source HEAD: `b06111235f8830676433b3a1279de65bc09b3c75`.
- `main` HEAD at inspection: `063f7a2eacd724f965a9723d0ae66cf95418c0fb`.
- Merge base: `f5b74affb8777953fa66d241784965fbb0e577ba`.
- Compare orientation: active branch as base, `main` as head. Result: `diverged`, `main) ahead by 76 commits and active branch behind by 3,019 commits; 76 commits total unique to `main`.
- Classification evidence: `docs/evidence/G0_3_MAIN_ONLY_76_COMMITS_CLASSIFICATION_2026-11-11.md`, commit `261019ec13e94fd80fa0116576c8de770d09f30f`.
- G0.3 classification: 48 SSH preflight / PR #140 commits; 17 SSH preflight / PR #144 commits; 3 P1.8 traceability-history commits; 2 T0 Signature A1 commits; 2 T0 Signature Stage I commits; 2 governance-documentation commits; 1 T1 review commit; 1 T0/T2 parity-evidence commit.
- Critical findings: A1 on `main) lacks the same owner-approval record as the active-branch version; SSH preflight script/test contracts differ; Stage I workflow is identical by blob SHA `5fa94939181af5f1f33686c3444bc6f8a0326962`. Do not replace A1 or copy SSH implementation wholesale.
- G0.3: inventory and classification PASS; integration readiness BLOCKED; source tests NOT RUN (read-only task); exact-HEAD CI NOT VERIFIED; no artifacts.
- G0.4: documentation-only evidence/handoff update. No source, test, workflow, CI, T0 data, database, VPS/runtime, deployment, training, exchange or trading changes. No workflow was dispatched.
- Evidence commit: `261019ec13e94fd80fa0116576c8de770d09f30f`. Handoff update commit is recorded in the completion message and is the active branch HEAD after G0.4.

Next: no automatic integration. Any adoption from `main) requires a separately approved, narrowly scoped change with exact source SHA, contract mapping, regression tests and evidence. Do not merge/rebase/cherry-pick/reset/force-push or recreate branches. Do not alter PR #139 or T1 PR #1. Preserve paper-only posture and `AI_EXECUTION_ENABLED=false`.


## SSH Preflight retirement — 2026-11-11

Owner approved repository-wide retirement of SSH Preflight while preserving Git history and historical evidence.

- Evidence report: `docs/evidence/SSH_PREFLIGHT_RETIREMENT_2026-11-11.md`.
- Evidence commit on `main`: `5a950eeaf7b2bf138774cfad3b7daa18c884a0e7`.
- Evidence commit on active T0/T2 branch: `885779a5e2602b73c2266ac65ef02515ea2e96b5`.
- Removed the SSH Preflight script `ops/ssh/t0-readonly-preflight.sh`, contract test `ci/test_t0_ssh_preflight_contract.py`, workflow inputs/jobs, and SSH-only pull-request trigger.
- Removed remaining references to the deleted test module from the active T0/T2 workflow while retaining unrelated T0 gates.
- Updated six existing refs: `main`, `feature/t0-centralized-data-feeder-p1-20261101`, `fix/p1-ssh-preflight-contract-20261110`, `fix/p1-ssh-preflight-main-20261111`, `fix/scaleway-ssh-passphrase-preflight-20261110`, and `fix/t0-ssh-preflight-passphrase-20261110`. Exact post-change heads are in the evidence report.
- PR #139 closed without merge after updating its head branch. PR #140 and #144 were already merged and remain historical.
- GitHub readback: workflow has no SSH Preflight jobs/references; script and test paths are absent on all six refs. Source removal/readback **PASS**.
- Workflow YAML/Actions execution **NOT VERIFIED**; no workflow dispatched. Regression suites **NOT RUN**. No artifacts produced.
- No SSH/VPS connection, credential/secret/ForceCommand change, T0 data/database/runtime change, T1/T2 deployment, AI training, exchange connection, or trading action. The former Scaleway VPS had already been deleted. Paper-only and `AI_EXECUTION_ENABLED=false` remain.
- Four SSH-specific branch refs were retained; no history rewrite, force-push, merge, rebase, cherry-pick, or branch deletion occurred.

Next: use ordinary non-SSH T0 validation on the exact active branch SHA if workflow runtime verification is required. Do not restore SSH Preflight or alter VPS/SSH configuration without new explicit approval.


## G0.6 — T0/T2 deployment parity reconciliation (2026-11-11)

- Evidence report: `docs/evidence/G0_6_T0_T2_DEPLOYMENT_PARITY_RECONCILIATION_2026-11-11.md`; final report commit `2c70190aaa921d25f776ed5e4f6309db654004ec`; report blob `3891c3c1a088043413d7fa8c19fbf4137274a926`.
- T0/T2 parity reconciliation updated with a current-state addendum: historical 2026-11-09 bounded loopback test remains HISTORICAL PASS; current deployment parity is NOT VERIFIED.
- The Scaleway VPS used for the historical test was fully deleted on 2026-11-11, per owner-provided project update. Do not treat the old host as available for probes or deployment.
- No replacement VPS, runtime, T1 activation, PostgreSQL/TimescaleDB operation, FreqAI training, or live trading is authorized by G0.6.
- G0.6 scope was documentation-only. No source/workflow/test/runtime/database changes; tests NOT RUN; Actions CI NOT VERIFIED.
- Evidence report and parity addendum commits are recorded in the G0.6 report. The next permitted step is a separately approved bounded VPS provisioning/deployment scope if runtime validation is desired.


## G0.7 — SSH Preflight / G4 handoff reconciliation (2026-11-11)

- Evidence report: `docs/evidence/G0_7_HANDOFF_SSH_G4_RETIREMENT_RECONCILIATION_2026-11-11.md`, created in commit `f9f5bebb1afd8faba50f5a444c7ceec8ad125c2a`.
- Handoff correction commit: `66097c56e77feb67cbc232bc9f658d6d24210cae`; handoff blob at that commit: `acc4e09742554b94755568e7fc4a8f421f2bf7d6`.
- PR #139 was confirmed CLOSED / NOT MERGED at `2026-11-11T13:02:13Z`; it is no longer an open/draft task.
- Active G4 runtime instructions were replaced with a retired-workstream record. Historical run references remain only as historical evidence. Former Scaleway VPS was deleted; current deployment parity remains NOT VERIFIED.
- G0.7 was documentation-only. Tests NOT RUN; Actions CI NOT VERIFIED; no VPS, SSH, runtime, T0 data, source, workflow, T1/T2 deployment or trading changes.

## G0.8-A — T1 Connection Sidecar and CI read-only review (2026-11-11)

Owner approved a bounded read-only review of T1 Connection Sidecar, its offline tests, Collector integration boundary, BTCUSDT configuration implications and exact-SHA CI evidence.

- T1 repository: `kenznguyen/binance-futures-collector`.
- Reviewed branch: `feature/t1-connection-sidecar-integration-20261107`.
- Exact reviewed branch HEAD: `f3bae0cfbc26aa694a4d6c9476965121818d3567`.
- Evidence report: `docs/evidence/G0_8_A_T1_CONNECTION_SIDECAR_REVIEW_2026-11-11.md`, T1 commit `b1df599697d521d0ba68c0f37468bbe61d1e20b9`.
- Sidecar library is a standalone offline crate, explicitly documented as not integrated into the upstream Collector. Root `Cargo.toml` has no workspace/dependency entry for it; inspected Collector order-book manager and CSV writer do not invoke `SidecarWriter`.
- Sidecar library contract and isolated CI checks: PASS. This does not prove live Collector event emission, actual Ping/Pong correlation, market-data completeness or Binance runtime behavior.
- Exact-SHA CI: run [42656715617](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42656715617), source `f3bae0cfbc26aa694a4d6c9476965121818d3567`, 5/5 jobs SUCCESS. Sidecar formatting, Clippy and offline tests succeeded. Push-only binary artifact steps were skipped; no artifact was produced. Exact individual test counts were not available from the retrieved job summary.
- T1 feature branch remains diverged from `main`: 144 commits ahead, 1 behind, merge base `bc4f0ef633fbeee4a49defd72827f17162693805`. No branch reconciliation was performed.
- Checked-in `config.example.toml` uses `symbols = []`, meaning all discovered USDT-M perpetuals. README's ~40 GB/day estimate is for the full ~500-symbol universe at 500 ms; it is not a BTCUSDT-only estimate. An explicit BTCUSDT whitelist is a configuration direction only and was not applied or runtime-tested. A non-empty whitelist skips dynamic discovery/delisting detection.
- G0.8-A disposition: sidecar standalone contract/CI PASS; live integration NOT IMPLEMENTED / BLOCKED; BTCUSDT runtime config and disk rate NOT VERIFIED; Binance soak NOT RUN; branch reconciliation NOT STARTED.
- No source/test/workflow/config changes, workflow dispatch, artifact, VPS/SSH, service, database, market-data payload, exchange connection, T0 canonical data, AI training or trading action occurred. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.

Next: G0.8-B read-only T0 → T1 → T2 contract mapping. Any live sidecar integration, config change, test dispatch, branch reconciliation, VPS provisioning or deployment requires separate bounded approval.

## G0.8-B — T0 → T1 → T2 data contract mapping (2026-11-11)

Owner approved a read-only source-level mapping of implemented T0/T1/T2 data paths and contracts.

- T0/T2 reviewed branch HEAD: `43ba5a917f162dd5060bfd49bc57a89a9f1d88d8`.
- T1 reviewed branch HEAD: `f3bae0cfbc26aa694a4d6c9476965121818d3567`.
- Evidence report: `docs/evidence/G0_8_B_T0_T1_T2_DATA_CONTRACT_MAP_2026-11-11.md`, created in commit `adad8efd4d23d17b0b548cf362cec145febdae5a`.

### Contract findings

- T0 independently ingests Binance USD-M BTCUSDT M15/H1 closed candles via CCXT and exposes authenticated read-only GET `/v1/candles`. SQLite remains the default backend; PostgreSQL is opt-in/uncertified. No T1→T0 canonical write contract was identified.
- T0→T2 source path exists through `freqai_bridge/context.py` and strict `CandleHttpClient`, but the current client consumes M15 only, 1–32 bars, even though T0 supports M15 and H1. The HTTP endpoint/runtime is NOT VERIFIED.
- T1 captures raw Binance futures data to CSV: depth diffs/snapshots, trades, 1m klines, liquidations, funding, open interest, long/short ratios, mark/index/premium klines and taker ratios. Example config `symbols=[]` means all discovered USDT-M perpetuals; BTCUSDT-only runtime config and disk rate are NOT VERIFIED.
- A T1→T2 file-import path exists for four streams only (trades, funding, open interest, liquidations), through `futures_intelligence/import_collector.py`. It creates bounded `OBSERVED_ONLY` snapshots and records input-file SHA-256, but explicitly sets per-stream `complete=false` and connection status `UNVERIFIABLE`. This is not a direct service/API feed.
- **Critical provenance discrepancy:** the importer pins `SOURCE_COMMIT=bc4f0ef633fbeee4a49defd72827f17162693805`, the T1 merge-base SHA, while reviewed T1 feature branch HEAD is `f3bae0cfbc26aa694a4d6c9476965121818d3567`. Accepted CSV headers do not attest the producer SHA. Current feature-branch CSV producer provenance is therefore NOT VERIFIED.
- T1 order-book CSV is not consumed by the inspected T2 paper decision function. That function requires an order-book input with source `hummingbot` and connector `binance_perpetual`.
- FreqAI exporter validates dataframe OHLCV against T0 canonical candles and requires training dataset/model/strategy provenance. Its artifact is `predictedReturn` + `doPredict`, not a standalone LONG/SHORT signal contract.
- `pipeline/decision.py` combines T0 M15 candles, T1-derived intelligence snapshot, prediction and Hummingbot book; it fails closed to WAIT and otherwise emits BUY/SELL PAPER target-position intent. It defaults to fixed `target_base=0.001` BTC. This source review does not prove Shared Risk Engine enforcement, 1% equity margin cap, leverage controls, Kill Switch, separate Core/AI ledgers, or current runtime integration.
- The candidate immutable `T0_M15_H1_DATASET_BUNDLE_V1` remains NOT VERIFIED; API `datasetVersion` is a per-query hash, not a whole-bundle manifest.

### G0.8-B disposition

- Source-level contract mapping: **PASS**.
- T0 canonical independence: **PRESERVED IN INSPECTED SOURCE**.
- T0→T2 M15 HTTP client: **IMPLEMENTED IN SOURCE / LIVE NOT VERIFIED**.
- T1→T2 four-stream CSV import: **IMPLEMENTED IN SOURCE / PRODUCER PROVENANCE NOT VERIFIED**.
- T1 Sidecar live integration: **NOT IMPLEMENTED**.
- T1 order-book → T2 adapter: **NOT IDENTIFIED**.
- H1 consumption by current FreqAI bridge: **NOT IMPLEMENTED IN INSPECTED CLIENT**.
- Shared Risk Engine enforcement on the inspected paper decision path: **NOT VERIFIED**.
- FreqAI scheduled training and immutable bundle: **NOT VERIFIED / NOT FROZEN**.
- End-to-end runtime: **NOT VERIFIED**. Tests/workflows NOT RUN for this read-only mapping.

No source/config/test/workflow change, workflow dispatch, data read/export/copy, API request/token use, SQLite access, exchange connection, VPS provisioning, service start, AI training, strategy activation, order or destructive operation occurred. T0 remains independent; paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.

Next: G0.8-C replacement VPS capacity planning may use BTCUSDT-only as a scenario, not an applied configuration. Separate budgets are required for T0 canonical candles, T1 raw streams, T2 model artifacts/logs and FreqAI training scratch. All disk-rate, RAM and training-time values remain estimates until separately approved bounded benchmarks. VPS provisioning/deployment remains unauthorized.

## G0.8-C — Replacement Scaleway VPS capacity plan (2026-11-11)

Owner approved capacity planning only for a BTCUSDT personal research host running T0, T1, T2 and scheduled FreqAI training. No resource provisioning or runtime action was included.

- Evidence report: `docs/evidence/G0_8_C_SCALEWAY_VPS_CAPACITY_PLAN_2026-11-11.md`, created in commit `9221c1729cdb0a725337125c5a0f52026fe51232`.
- Recommended initial budget-first profile: Scaleway GP1-S, 8 vCPU / 32 GB RAM / up to 800 Mbps public bandwidth, subject to current PAR-1 availability and final console quote.
- Storage planning envelope: 500 GB total, split into separate volumes: 80 GB OS/apps/logs, 20 GB T0 canonical store, 300 GB T1 raw capture, 100 GB T2 model artifacts/FreqAI staging and scratch.
- Current public price references: GP1-S about €139.24/month; 500 GB PAR-1 Performance Block Storage SSD at €0.000118/GB-hour × 730 hours = about €43.07/month; planning total **~€182.31/month before tax, flexible IP and ancillary charges**. Verify final price, quota and zone in Scaleway console.
- T1 README states ~40 GB/day for the full ~500-symbol universe at 500 ms, not BTCUSDT-only. A provisional 0.5–2.0 GB/day BTCUSDT raw capture range was used for sizing only; it is NOT measured. 90 days at that range is 45–180 GB before safety headroom.
- Proposed resource limits: T0 2–3 GB RAM; T1 2–4 GB; T2 runtime 4–6 GB; one FreqAI training job capped at 12–14 GB and 4 CPU cores; retain 2–4 GB safety headroom. These are planning limits, not configured cgroups/service limits.
- Proposed training schedule: once daily at 03:00 Asia/Ho_Chi_Minh, one job, max 4 hours, bounded CPU/RAM, no model promotion on failure. Schedule is NOT enabled and remains conditional on immutable dataset bundle, estimator, labels/purge, calibration and artifact contract freeze.
- GPU is NOT recommended initially. The selected FreqAI estimator/GPU dependency is not established; Scaleway L4 is about €0.79/hour (~€574.87/month) before storage/tax.
- Single-host limitation: separate volumes and process identities preserve logical data boundaries, but all layers still share one physical host failure domain. T0 remains a separately owned canonical data asset, not fault-domain independent on a single VPS.
- T1 BTCUSDT-only config, per-stream disk growth, FreqAI model footprint/training duration, live endpoint/runtime parity and final zone/quota/pricing remain NOT VERIFIED.
- No retention deletion/cleanup policy was authorized or applied. The proposed 300 GB T1 volume does not grant permission to delete data when full or at a retention boundary.

### G0.8-C disposition

- Capacity design and initial profile: **CONDITIONAL PASS — planning only**.
- Recommended initial compute: **GP1-S 8 vCPU / 32 GB RAM**.
- Storage: **500 GB split 80/20/300/100 GB**.
- Estimated compute + storage: **~€182.31/month before tax/IP/ancillary costs**.
- BTCUSDT raw capture rate and retention fit: **NOT VERIFIED**.
- FreqAI model/training performance fit: **NOT VERIFIED**.
- GPU need: **NOT ESTABLISHED; not recommended initially**.
- Tests/workflows: **NOT RUN**.
- VPS provisioning/deployment: **NOT AUTHORIZED by G0.8-C**.

No VPS/volume/IP/payment, SSH/firewall, package, service, configuration, deployment, exchange connection, T0 database access/mutation, T1 capture, AI training, signal publication, order or cleanup/deletion occurred. T0 remains independent; paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.

Next: if owner wants to proceed beyond planning, first approve a bounded provisioning specification and confirm the exact Scaleway zone, account quota, final checkout quote, volume persistence policy and whether single-host failure-domain coupling is acceptable. A separate approval is required before resource creation or deployment.



## G0.9 — VPS Data Lifecycle and Storage Governance Design (2026-11-11)

- Evidence report: `docs/evidence/G0_9_VPS_DATA_LIFECYCLE_STORAGE_GOVERNANCE_2026-11-11.md`, created in commit `c37b6d4b684b12e60c0d78dddcf9cfbe71805e0a`.
- Scope: documentation-only translation of the existing central lifecycle policy and owner-ratified RET-01 B / RET-02 B into the planned VPS storage domains. No implementation or runtime inventory.
- G0.8-C storage planning envelope remains 500 GB split 80/20/300/100 GB; this is not provisioned. No replacement VPS exists after deletion of the former Scaleway host.
- Earlier suggested 24-hour cache, 7-day scratch, 14–30-day log retention and 80% cleanup threshold are NOT approved policy values and are not adopted. RET-03 through RET-10 remain open/not verified; no numeric retention, TTL, grace, alert or evidence-freshness value is approved by G0.9.
- T0 canonical data remains PROTECTED. T1 raw deletion review is BLOCKED by incomplete/unverifiable streams, producer SHA mismatch, unverified BTCUSDT-only runtime config and unmeasured growth. T2/T4 object eligibility, runtime logs, backups/copies and rebuildability remain NOT VERIFIED.
- G0.9 defines a read-only inventory/classification/dependency/rebuildability/dry-run workflow and a fail-closed test matrix. The dry-run contract is not implemented; tests NOT RUN; GitHub Actions NOT DISPATCHED; no run/artifact.
- G0.9 verdict: policy alignment PASS (documentary); static storage-domain mapping CONDITIONAL PASS; implementation, runtime inventory and cleanup eligibility NOT VERIFIED/BLOCKED.
- No source/schema/API/registry/workflow/scheduler/service/permission/credential/database/storage/VPS/data change; no archive, quarantine, cleanup, expiry, compaction, vacuum or deletion. T0 remains independent; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.
- Next bounded task: prepare a synthetic-only dry-run contract and test implementation plan. Before implementation or workflow dispatch, separately bound exact synthetic fixture paths, test-only allowlist, proof of no production-data access and CI workflow scope. No destructive executor is included.



## G0.10 — Synthetic-only Lifecycle Dry-run Contract and Test Plan (2026-11-11)

- Evidence report: `docs/evidence/G0_10_SYNTHETIC_ONLY_LIFECYCLE_DRY_RUN_CONTRACT_2026-11-11.md`, created in commit `0946eaf1cab77afa67c36341cbe2a262750bef33`.
- Scope: documentary contract for a pure, deterministic synthetic-fixture disposition evaluator. No implementation, fixtures, tests, CI workflow, storage adapter or executor added.
- Proposed fixture namespace `tests/fixtures/lifecycle_dry_run/` and output namespace `build/test-artifacts/lifecycle-dry-run/` are proposals only; existence and allowlisting are NOT VERIFIED / NOT APPROVED.
- Contract prohibits production paths, T0/T1/T2/T3/T4 runtime data, VPS/database/provider access, network credentials and any storage mutation capability. Output can only be a non-executable disposition report; no ARCHIVED/DELETED/EXECUTING/AUTHORIZED state.
- Defines five protective dispositions and 26 synthetic acceptance cases covering T0/ledgers/T3 protection, unknown metadata, integrity, dependency/hold/copy/process blockers, T1/T2 constraints, determinism, input immutability, path isolation, no executor, audit failure and storage-pressure behavior.
- G0.10 verdict: contract/test-plan documentation PASS; fixture allowlist NOT VERIFIED / NOT APPROVED; implementation NOT IMPLEMENTED; tests NOT RUN; Actions NOT DISPATCHED; no run/artifact; runtime isolation NOT VERIFIED; destructive executor NOT IMPLEMENTED / NOT AUTHORIZED.
- No source, fixture, schema, API, registry, workflow, scheduler, service, permission, credential, database, storage, VPS, data, model, ledger or runtime change. No inventory read, test, dispatch, archive, quarantine, cleanup, expiry, compaction, vacuum, deletion or provider operation. T0 remains independent; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.
- Next gate: separate bounded approval must identify exact synthetic fixture files/provenance, exact test-only read/write allowlist and workspace, test implementation files/command, CI workflow/permissions, and evidence excluding production data/secrets/network/database/VPS/provider access. Then review a pure evaluator implementation plan. No destructive executor.



## G0.11 — Pure Lifecycle Disposition Evaluator Implementation Plan (2026-11-11)

- Evidence report: `docs/evidence/G0_11_PURE_LIFECYCLE_DISPOSITION_EVALUATOR_IMPLEMENTATION_PLAN_2026-11-11.md`, created in commit `6cc8b3f11a5b0da397acac754f654d4e7033cef0`.
- Scope: documentary-only implementation plan. Reconciles G0.10 with existing Stage C.5–C.14 lifecycle assurance contracts and evidence. No code, fixtures, tests, schema, adapter, runner, oracle, workflow, storage interface or executor added.
- Explicitly separates (A) narrow pure five-disposition evaluator from (B) broader TEST-01–07 lifecycle assurance harness. G0.10 evaluator cannot close TEST-01–07 or claim coverage of the 87-vector catalogue.
- Reuses Stage C.13 logical field map blob `c43c8bfbccaf698d6670f33fab66ee12d2072a7f` and Stage C.14 87-vector matrix blob `12bba6c475fc2ad8c4e2246e75034ede22d3bc20`. C.13/C.14 remain documentary; no technical gate closure.
- Proposed pure interface accepts already materialized synthetic values and returns only a protective disposition; no filesystem/path/database/network/clock/process/adapter/executor capability. No storage discovery or fixture loader.
- Decision tie-break table and reason-code catalogue remain OPEN before implementation. No TTL, retention, freshness or disk-alert values are invented.
- G0.11 verdict: documentary reconciliation PASS; evaluator boundary CONDITIONAL PASS; policy tie-break table OPEN; implementation paths/fixtures/CI not approved; implementation NOT IMPLEMENTED; tests NOT RUN; Actions NOT DISPATCHED; no run/artifact; TEST-01–07 technical closure NOT ESTABLISHED; 0/87 executed, 87/87 NOT RUN; TEST-08 NOT GRANTED.
- No source/test/fixture/schema/API/registry/adapter/runner/oracle/workflow/scheduler/service/permission/credential/database/storage/VPS/data/model/ledger/runtime changes. No test, compile, dry-run, fault injection, dispatch, inventory, provider/runtime probe, archive, quarantine, cleanup, expiry, compaction, vacuum or deletion. T0 independent; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.
- Next bounded documentary task: freeze field-level decision table and reason-code catalogue for PROTECTED / RETAIN / BLOCKED / REVIEWABLE / COPY_SPECIFIC outcomes. A separate exact-scope approval is required before pure evaluator implementation and in-memory synthetic unit tests. CI, broader TEST-01–07 harness and destructive operations remain separate gates.



## G0.12 — Lifecycle Disposition Decision Table and Reason-Code Catalogue (2026-11-11)

- Evidence report: `docs/evidence/G0_12_LIFECYCLE_DISPOSITION_DECISION_TABLE_REASON_CODES_2026-11-11.md`, created in commit `13c6c991a15ba1b0387c3b2d8f129558fabfddbe`.
- Scope: documentation-only decision precedence, field-level semantics, stable reason-code catalogue and mapping to G0.10 SYN-DRY-001–026. No implementation or execution.
- Frozen precedence: (1) verified protected class/active binding preservation hold → PROTECTED; (2) absent verified protection but unknown/stale/contradictory required facts → BLOCKED_UNKNOWN; (3) known open dependency/operational obligation → RETAIN_UNTIL_OBLIGATIONS_CLOSE; (4) exact copy with complete copy-specific evidence → COPY_SPECIFIC_REVIEW; (5) exact object in one of four ratified noncanonical groups with every applicable predicate proven → REVIEWABLE_NONCANONICAL; otherwise BLOCKED_UNKNOWN.
- Clarifies protected-vs-unknown identity, binding hold vs ordinary obligation, unknown registry vs known active dependency, exact-copy scope and reviewability conditions. No TTL, freshness, grace, retention, alert or pressure threshold invented.
- Adds stable PROT_*, UNK_*, RET_*, COPY_* and REV_* reason codes. Informational storage-pressure/ACK/heartbeat codes cannot satisfy eligibility predicates.
- G0.12 verdict: decision table and reason codes PASS at documentary level; physical schema/canonicalization NOT ESTABLISHED; implementation paths/fixtures NOT APPROVED; evaluator NOT IMPLEMENTED; tests NOT RUN; Actions NOT DISPATCHED; no run/artifact; TEST-01–07 technical closure NOT ESTABLISHED; 0/87 vectors executed, 87/87 NOT RUN; TEST-08 NOT GRANTED.
- No source/test/fixture/schema/API/registry/adapter/runner/oracle/workflow/scheduler/permission/credential/database/storage/VPS/data/model/ledger/runtime changes. No compile, tests, dry-run, dispatch, inventory, provider/runtime probe, archive, quarantine, cleanup, expiry, compaction, vacuum or deletion. T0 remains independent; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.
- Next gate: separate bounded approval for pure evaluator implementation and in-memory synthetic unit tests, with exact code/test paths and command. CI dispatch, broader TEST-01–07 harness and destructive operations remain separate approvals.



## G0.13 — Pure Lifecycle Disposition Evaluator and In-Memory Unit Tests (2026-11-11)

- Evidence report: `docs/evidence/G0_13_PURE_LIFECYCLE_DISPOSITION_EVALUATOR_2026-11-11.md`, created in commit `fb8fd8ba6c738024524ba0f53913ab9680558134`.
- Implementation: `pipeline/lifecycle_disposition.py`, blob `a528861c342c7c20ae48a9042338fec4ee2afa24`.
- Tests: `pipeline/test_lifecycle_disposition.py`, blob `068a22f833ebe922da422df5fba520e36b77586a`.
- Scope: pure evaluator over one supplied metadata mapping and 20 in-memory synthetic unit tests. Standard library only. No filesystem/database/network/provider/clock/process/runner/executor capability.
- Dispositions: PROTECTED, RETAIN_UNTIL_OBLIGATIONS_CLOSE, BLOCKED_UNKNOWN, COPY_SPECIFIC_REVIEW, REVIEWABLE_NONCANONICAL. Output fixes `mutation_performed=false` and `execution_authorized=false`.
- Protected T0, CORE_LEDGER, AI_LEDGER, protected T3 and governance evidence take precedence on positive exact identity assertion. Verified binding hold is PROTECTED. Unknown facts fail closed. Known open obligations/process/material T2 use RETAIN. Exact copy review is object-scoped. T4/T1 require rebuildability proof; T1 additionally requires a supplied producer-provenance assertion; T2 requires explicit non-material-use assertion.
- Storage pressure, consumer ACK and heartbeat loss do not change disposition. No TTL/age heuristic or numeric retention policy introduced.
- TDD local focused result: initial RED due missing module; final `python -m unittest pipeline.test_lifecycle_disposition -v` **20 PASS**, 0 failures/errors. `python -m py_compile pipeline/lifecycle_disposition.py pipeline/test_lifecycle_disposition.py` PASS. Local file Git blob hashes matched committed GitHub blob hashes.
- Important trust limitation: evaluator consumes `identity_verified`, `producer_provenance_verified`, dependency/hold/process/rebuildability/material-use facts as supplied assertions; it does not authenticate them. Digest format/length are checked but digest is not recomputed against payload bytes. Review dispositions are not deletion/archive authorization.
- Repository-wide tests NOT RUN. GitHub Actions NOT DISPATCHED; no run/artifact. TEST-01–07 harness NOT IMPLEMENTED/NOT VERIFIED; 0/87 vectors executed; TEST-08 NOT GRANTED. Runtime/VPS NOT VERIFIED.
- No workflow/fixture/schema/API/registry/adapter/runner/oracle/scheduler/service/permission/credential/database/storage/VPS/data/model/ledger/runtime changes; no production inventory, provider/network/database access, archive, quarantine, cleanup, expiry, compaction, vacuum or deletion.
- Branch remains `feature/t0-centralized-data-feeder-p1-20261101`; final source HEAD before evidence/handoff append: `8751c4505c600267559e402801ef37c689781824`.
- Next step: code-level review and contract-gap assessment against G0.10/G0.12. Independent fact authentication, payload digest verification, Stage C TEST-01–07 harness, CI workflow, production inventory and destructive executor require separate bounded approvals.



## G0.14 — Lifecycle Evaluator Code Review and Contract-Gap Assessment (2026-11-11)

- Evidence report: `docs/evidence/G0_14_LIFECYCLE_EVALUATOR_CODE_REVIEW_2026-11-11.md`, created in commit `7f335b56f0349dcd11dfd4f8b631c68a28cd1850`.
- Review target source HEAD: `7ddf48c83edffd76b339ca1be6e09b1e300eb73a`.
- Reviewed evaluator blob: `a528861c342c7c20ae48a9042338fec4ee2afa24`; tests blob: `068a22f833ebe922da422df5fba520e36b77586a`; G0.12 contract blob: `fa4e595126fe0c59ed2f9d91f274d7707d636b51`.
- Scope: source/spec review only. No source/test/schema/workflow/runtime change. G0.13 focused 20/20 tests and compile are referenced from its report, not rerun during G0.14.
- Verdict: **REQUEST CHANGES — REQUIRED FINDINGS OPEN**.
- R1 REQUIRED: malformed unhashable copy state can raise TypeError instead of fail-closed BLOCKED_UNKNOWN; add type guard and regression tests.
- R2 REQUIRED: COPY_SPECIFIC_REVIEW does not require a matching exact copy/version in complete copies inventory or bind the copy identity to the evaluated object; define canonical relation and test empty/mismatched/duplicate inventory.
- R3 REQUIRED: protected early return omits applicable UNK_* codes for missing hold/dependency/lineage/copy/process metadata; preserve PROTECTED while collecting required unknown codes.
- R4 REQUIRED: no sensitivity-label field/validation and no class-to-policy/version mapping; policy allowlist is global rather than class-specific. Remediation must use exact owner-ratified values only; do not invent a vocabulary or mapping.
- Additional limitations: identity/provenance booleans are caller assertions; evidence_revision is only checked non-empty; digest is not recomputed; completeness/freshness assertions are not authenticated. This remains a classifier over supplied facts, not an evidence verifier.
- Five-axis review: correctness BLOCKED; readability CONDITIONAL PASS; architecture PASS within pure boundary; security CONDITIONAL; bounded in-memory performance PASS.
- Repository-wide tests NOT RUN; GitHub Actions NOT DISPATCHED; no run/artifact; TEST-01–07 not implemented/not verified; 0/87 vectors executed; TEST-08 NOT GRANTED; runtime NOT VERIFIED.
- No source/test/fixture/schema/API/registry/adapter/runner/oracle/workflow/scheduler/service/permission/credential/database/storage/VPS/data/model/ledger/runtime changes. No test, compile, dry-run, dispatch, inventory, network/provider/database access, archive, quarantine, cleanup, expiry, compaction, vacuum or deletion.
- T0 remains independent/protected; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.
- Next bounded step: request owner approval for G0.15 remediation of R1–R4. R4 remains blocked if the ratified policy does not specify exact sensitivity vocabulary and class-policy mapping. CI dispatch, TEST-01–07, evidence authentication and destructive executor remain separate gates.



## G0.15 — Lifecycle Evaluator Remediation of G0.14 Findings (2026-11-11)

- Owner approved bounded remediation of G0.14 R1–R4 only.
- Implementation commit: `eb444273f54f46ca48d51f7be8cfed8d3a8a6cf9`.
- Evidence report: `docs/evidence/G0_15_LIFECYCLE_EVALUATOR_REMEDIATION_2026-11-11.md`, created in commit `be1c18cc1413f623cee0e5a2f0608c2f6c9f78b1`.
- Implementation blob `pipeline/lifecycle_disposition.py`: `6f083a6b9b7107f3b6e3c7af3b32da34b5dafb5e`.
- Test blob `pipeline/test_lifecycle_disposition.py`: `2ba03eb0deac67e1b82afb60ca24a6c15a2a56ce`.
- R1: explicit string type guard added before copy-state membership test. Regression test passes. The malformed-state case was also tested against the pre-change source and already failed closed due to the earlier shape guard; the reported TypeError was NOT REPRODUCED on baseline. Treat as defensive hardening, not a reproduced baseline bug.
- R2: COPY_SPECIFIC_REVIEW now requires copy ID to equal the evaluated object ID and exactly one complete copies-inventory entry matching copy ID, exact version, NONCANONICAL_COPY kind and supported string state. Empty, mismatched-version and duplicate matches block. RED/GREEN regression coverage added.
- R3: protected class/binding-hold precedence is retained while all applicable unknown metadata reason codes are collected. RED/GREEN regression coverage added.
- R4: BLOCKED / NOT IMPLEMENTED. RET-01/RET-02 ratification and P1.8.80/C.13 establish that sensitivity/classification is required in applicable gates, but no exact owner-ratified sensitivity vocabulary or complete class-to-policy/version mapping was found. Do not invent labels or mappings.
- Focused test command `python -m unittest pipeline.test_lifecycle_disposition -v`: 23/23 PASS.
- Compile command `python -m py_compile pipeline/lifecycle_disposition.py pipeline/test_lifecycle_disposition.py`: PASS.
- Repository-wide tests NOT RUN; GitHub Actions NOT DISPATCHED; no run/artifact.
- G0.15 verdict: PARTIAL PASS — R1–R3 remediated; R4 BLOCKED. TEST-01–07 technical closure NOT ESTABLISHED; 0/87 vectors executed; TEST-08 NOT GRANTED; runtime/VPS NOT VERIFIED.
- No workflow, fixtures, schema, API, registry, adapter, runner, oracle, scheduler, service, permission, credential, database, storage, VPS, market data, model, ledger or runtime changes. No production inventory, external evidence authentication, network/provider/database access, dispatch, archive, quarantine, cleanup, expiry, compaction, vacuum or deletion.
- Next gate: owner-ratify exact sensitivity vocabulary and class-to-policy/version mapping before R4 implementation. CI, TEST-01–07, evidence authentication and destructive operations remain separate approvals. T0 remains independent/protected; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## G0.16 — Owner Sensitivity Classification Decision Package (2026-11-11)

- Owner approved preparation of a proposed sensitivity-label vocabulary and class mapping for review; this is not owner ratification of the proposed values.
- Evidence: `docs/evidence/G0_16_OWNER_SENSITIVITY_CLASSIFICATION_DECISION_PACKAGE_2026-11-11.md`.
- Evidence commit: `3e4c86adf31a23c36669cd221e50879558aaf87e`.
- Proposal: four ordered labels `PUBLIC < INTERNAL < CONFIDENTIAL < RESTRICTED`; `UNCLASSIFIED` and `CONFLICTED` are non-label states. Proposed most-restrictive-wins inheritance for copies/derived data; exact class defaults are in the evidence report.
- Sensitivity is explicitly separate from lifecycle disposition and does not grant review eligibility, deletion/archive approval or execution authority.
- Mapping is a proposed minimum baseline, not a runtime inventory or classification of actual objects. No numeric retention/TTL/freshness values are proposed.
- Source reconciliation: RET-01 B, RET-02 B, P1.8.80, P1.8.143, P1.8.144 and Stage C.13. Unknown/conflicting classification remains fail-closed; no automatic downgrade.
- Owner ratification: PENDING. Independent review NOT RUN. Tests NOT RUN. GitHub Actions NOT DISPATCHED; no run/artifact.
- No evaluator/schema/source/test/fixture/API/registry/adapter/workflow/scheduler/service/permission/credential/database/storage/VPS/runtime changes. No inventory, file/secret scan, network/provider/database access, archive, quarantine, cleanup, expiry, compaction, vacuum or deletion.
- G0.15 R4 remains BLOCKED until exact vocabulary and mapping are owner-ratified. After ratification, evaluator integration requires separate bounded approval. CI, TEST-01–07, runtime inventory and destructive actions remain separate gates.
- T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## G0.17 — Owner Ratification of Sensitivity Classification Policy (2026-11-11)

- Owner explicitly approved all six G0.16 decisions without amendment.
- Ratification evidence: `docs/evidence/G0_17_OWNER_SENSITIVITY_CLASSIFICATION_POLICY_RATIFICATION_2026-11-11.md`.
- Ratification commit: `645f2893ce8a2e846c9298d8d6c6bdbff1f041d5`.
- G0.16 proposal blob ratified: `95cc2a1a36b05e35e15348d870a147282d659851`.
- Ratified ordered labels: `PUBLIC < INTERNAL < CONFIDENTIAL < RESTRICTED`. Non-label states: `UNCLASSIFIED`, `CONFLICTED`, `PENDING_OWNER_DECISION`.
- Ratified minimum class mapping is exactly G0.16 §3 / G0.17 §3. Unknown/stale/conflicting/unauthenticated classification fails closed and is handled as RESTRICTED pending resolution.
- Ratified most-restrictive-wins inheritance across copies, backups, replicas, exports and derived outputs; no automatic downgrade. Exact-scope owner approval and evidence are required for declassification. Credentials, keys, tokens, signing and trust-root secrets are always RESTRICTED and their values must not appear in ordinary evidence/CI artifacts.
- Sensitivity is separate from lifecycle disposition and does not grant review eligibility, retention-floor completion, archive/deletion approval or execution authority. RET-01 B / RET-02 B remain unchanged; T0 protected and independent.
- G0.15 R4 policy-definition gap: **CLOSED AT DOCUMENTARY OWNER-POLICY LEVEL**. Evaluator/schema/registry integration: NOT IMPLEMENTED; requires separate bounded approval. Evidence authentication, independent review, tests, Actions, runtime inventory/classification and TEST-01–07 remain NOT RUN / NOT VERIFIED; no status promotion.
- No source/test/fixture/schema/API/registry/adapter/runner/oracle/workflow/scheduler/service/permission/credential/database/storage/VPS/runtime changes. No inventory, file/secret scan, network/provider/database access, archive, quarantine, cleanup, expiry, compaction, vacuum or deletion.
- T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.
- Next candidate: separate bounded implementation plan for sensitivity field propagation/validation in pure evaluator and in-memory synthetic tests. No implementation, CI dispatch, TEST-01–07 harness, runtime inventory or destructive operation authorized.


## G0.18 — Sensitivity Field Integration Plan for Pure Lifecycle Evaluator (2026-11-11)

- Evidence report: `docs/evidence/G0_18_SENSITIVITY_EVALUATOR_INTEGRATION_PLAN_2026-11-11.md`.
- Report creation commit: `496e388202b6f8c3faed7cd746b9387d1c89668e`; report clarification commit: `db5124f164e7ff85c896fca422e3ab6921c77c7c`; final report blob: `d91b3d2ce998ba90a1df7849640c38dc4242d44e`.
- Scope: documentation-only plan for the pure evaluator and its in-memory tests. Existing evaluator blob `6f083a6b9b7107f3b6e3c7af3b32da34b5dafb5e`; existing test blob `2ba03eb0deac67e1b82afb60ca24a6c15a2a56ce`.
- Defines a proposed required in-memory `sensitivity` mapping, four ratified ordered labels, three non-label states, fail-closed validation, class-minimum enforcement, stable reason-code candidates and synthetic test matrix.
- G0.17 ratifies semantic domain defaults, not a canonical machine-readable `data_class` enum. G0.18 explicitly leaves exact mapping from current evaluator identifiers to G0.17 semantic domains as a pre-implementation review item; no enum renaming or inferred equivalence is authorized.
- Preserves five dispositions and their precedence; sensitivity cannot grant reviewability, retention-floor completion, archive/deletion approval or execution authority. Result flags remain false.
- G0.18 verdict: documentation/plan PASS; evaluator integration NOT IMPLEMENTED; implementation approval NOT GRANTED by the plan; sensitivity tests NOT RUN; GitHub Actions NOT DISPATCHED; no run/artifact; evidence authentication NOT ESTABLISHED; TEST-01–07 unchanged at 0/87 executed; runtime inventory/classification NOT PERFORMED / NOT VERIFIED; destructive authority NOT GRANTED.
- No source/test/fixture/schema/API/registry/adapter/runner/oracle/workflow/scheduler/service/permission/credential/database/storage/VPS/data/model/ledger/runtime changes. No inventory, file/secret scan, network/provider/database access, archive, quarantine, cleanup, expiry, compaction, vacuum or deletion.
- Next gate: separate explicit bounded approval for changes only to `pipeline/lifecycle_disposition.py` and `pipeline/test_lifecycle_disposition.py`, plus the in-memory synthetic test matrix and local commands in the G0.18 report. CI dispatch, schema/registry integration, TEST-01–07, evidence authentication, runtime inventory and destructive actions remain separate gates. T0 independent/protected; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## G0.19 — Sensitivity Validation in Pure Lifecycle Evaluator (2026-11-11)

- Owner approved the bounded G0.19 scope: modify only `pipeline/lifecycle_disposition.py` and `pipeline/test_lifecycle_disposition.py`; add in-memory synthetic tests; no CI dispatch or broader integration.
- Evidence report: `docs/evidence/G0_19_SENSITIVITY_EVALUATOR_IMPLEMENTATION_2026-11-11.md`, created in commit `48b0e046be4ef7f1f69e93436e2e79e93359511e`.
- Test-first commits: `7b3288f1cb38cdc7dd7fea17a5cf7f950eaea9e4`, `6148da02546fb9db93f991dc6d4b9a874f97938f`, `7f7b88928ab8c01dab46c8cd08029c0b3a37f70b`.
- Evaluator implementation commit: `b2210c472bb509efc5ae4969df9da7de3b6ddccc`; evaluator blob `cf22385a718c6b5b08cd50c2a45578b4180c2c4d`; test blob `c1ff994b22bfad6caeea6ee973aaf959b08759cf`.
- Added four-label order, three non-label states, fail-closed metadata validation, explicit minimum mapping for existing evaluator class identifiers, and inherited-label enforcement for `NONCANONICAL_COPY`. Unmapped classes fail closed; no new class identifiers or inferred equivalences were introduced.
- Sensitivity unknowns are collected before disposition selection. Existing protected/active binding-hold precedence and five dispositions remain unchanged. `mutation_performed=false` and `execution_authorized=false` remain fixed.
- Added nine in-memory synthetic test methods. Expected focused test count is 32 (23 existing + 9 new); this is a source-level count only.
- G0.19 status: implementation PRESENT / NOT VERIFIED. Focused unittest NOT RUN; py_compile NOT RUN because no local repository checkout is available in the execution container and outbound GitHub access is unavailable. Repository-wide tests NOT RUN. GitHub Actions NOT DISPATCHED; no run/artifact. Independent review NOT RUN.
- Trust limitation: sensitivity evidence references, identity/provenance and inherited labels are supplied assertions, not authenticated facts; payload digests are not recomputed. No claim of external evidence authentication.
- No workflow, schema, registry, adapter, runner, oracle, fixture file, scheduler, service, permission, credential, database, storage, VPS, market data, model, ledger or runtime changes. No inventory, secret scan, network/provider/database/VPS access, archive, quarantine, cleanup, expiry, compaction, vacuum or deletion.
- Next gate: run `python -m unittest pipeline.test_lifecycle_disposition -v` and `python -m py_compile pipeline/lifecycle_disposition.py pipeline/test_lifecycle_disposition.py` in a bounded test-capable local checkout; address any failures only within the two approved files. CI dispatch, schema/registry integration, TEST-01–07, evidence authentication, runtime inventory and destructive actions remain separate approvals. T0 independent/protected; CORE_LEDGER and AI_LEDGER separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## G0.20 — Local Verification Attempt and Code Review (2026-11-11)

- Evidence report: `docs/evidence/G0_20_LOCAL_VERIFICATION_CODE_REVIEW_2026-11-11.md`; created in commit `ff505ebfb8da682615cdbf8c386f35d7b60e9c34`.
- Exact reviewed evaluator blob: `cf22385a718c6b5b08cd50c2a45578b4180c2c4d`.
- G0.19 test blob before correction: `c1ff994b22bfad6caeea6ee973aaf959b08759cf`.
- Review found test helper `minimums.get(kind)` could raise `TypeError` for the existing unhashable `data_class=[]` malformed-input case. Corrected only the test helper with a string type guard.
- Correction commit: `a22e189ee18ff7ad7a5d2efa8f6a895f8335843a`; final test blob `d54d0523d6388df448cbec7c2fb9e2e092f72920`. GitHub readback verified the exact one-line correction.
- Attempted shallow clone of the exact branch to run `python -m unittest pipeline.test_lifecycle_disposition -v` and `python -m py_compile pipeline/lifecycle_disposition.py pipeline/test_lifecycle_disposition.py`; clone failed because the execution environment could not resolve `github.com`. Both commands therefore BLOCKED / NOT RUN; no test or compile PASS claim.
- Five-axis source review: correctness CONDITIONAL / NOT VERIFIED; readability PASS; architecture PASS (pure boundary intact); security CONDITIONAL (caller-supplied sensitivity/provenance facts are unauthenticated); performance PASS (bounded in-memory lookups). One fixture-helper issue corrected. No further source changes.
- GitHub Actions NOT DISPATCHED; no run/artifact. Repository-wide tests NOT RUN. TEST-01–07 unchanged, 0/87 executed. Runtime/VPS NOT VERIFIED. Destructive authority NOT GRANTED.
- No schema/registry/API/adapter/runner/oracle/workflow/scheduler/service/permission/credential/database/storage/VPS/data/model/ledger/runtime changes; no inventory, secret scan, provider/network/database access, archive, quarantine, cleanup, expiry, compaction, vacuum or deletion.
- Next gate: obtain a test-capable checkout/environment containing exact branch source, then run the two commands in the G0.20 report and record full output. Any remediation remains limited to `pipeline/lifecycle_disposition.py` and `pipeline/test_lifecycle_disposition.py` under the existing approval. T0 independent/protected; CORE_LEDGER and AI_LEDGER separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## G0.20-B — Exact-source GitHub Actions verification (2026-11-11)

- Owner approved a dedicated isolated CI workflow and one verification run for G0.20.
- Workflow: `.github/workflows/g0-20-lifecycle-evaluator-verification.yml`; workflow creation commit / run head SHA `6db05c878873790d113e0a315a9be90923a9650c`.
- Workflow is scoped to the existing feature branch and workflow-file path for its one-time push-triggered run; `workflow_dispatch` input is also defined. Repo default branch is `main`; this feature-branch verification was triggered by the narrowly path-filtered push, not a manual dispatch.
- Exact checkout commit verified: `6db05c878873790d113e0a315a9be90923a9650c`.
- Evaluator blob pinned and verified in CI: `cf22385a718c6b5b08cd50c2a45578b4180c2c4d`.
- Test blob pinned and verified in CI: `d54d0523d6388df448cbec7c2fb9e2e092f72920`.
- Workflow run ID `43036222952`, run #1, event `push`, final status `completed`, conclusion **SUCCESS**; job ID `130575627133`, conclusion **SUCCESS**.
- Run URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43036222952
- GitHub-hosted Ubuntu 26.04.1, Python 3.12.16. Focused `py_compile`: **PASS**. Focused unittest: **PASS**, 32 tests, 0 failures/errors. Full job logs fetched and inspected.
- Artifact name `g0-20-lifecycle-verification-6db05c878873790d113e0a315a9be90923a9650c`; artifact ID `13862633389`; SHA-256 `0eff7bb4c6fba66656841734b3a64f771872154d723c42eb326ebd57440f3d00`; expires 2026-11-18T14:12:21Z. Artifact URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43036222952/artifacts/13862633389
- Evidence report updated: `docs/evidence/G0_20_LOCAL_VERIFICATION_CODE_REVIEW_2026-11-11.md`; update commit `c04b423638b3e72aaf517fa9aa3a1db8f05ca858`; final report blob `2845a4ce52525b89bbc4ec7c240c994370a74e2a`.
- G0.20 verdict: **PASS for the approved pure evaluator verification scope**. Repository-wide tests NOT RUN; independent review beyond source inspection NOT RUN; TEST-01–07 remain 0/87; runtime/VPS inventory NOT PERFORMED/NOT VERIFIED; evidence authenticity and real-world identity/provenance not established; destructive authority NOT GRANTED.
- Workflow has `contents: read`, no configured secrets, no package installation and no DB/provider/exchange calls. No full CI or other workflow was dispatched by this step.
- No schema/registry/API/adapter/runner/oracle/TEST-01–07/retention/runtime integration, VPS access, data/model/ledger mutation, archive, quarantine, cleanup, expiry, compaction, vacuum or deletion.
- Next gate: separately bounded trust-boundary review for caller-asserted metadata/evidence refs and required authenticity/provenance controls before any registry or lifecycle-harness integration. Do not infer authority for schema/registry changes, TEST-01–07, runtime inventory or destructive execution from this PASS. T0 independent/protected; CORE_LEDGER and AI_LEDGER separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## G0.21 — Lifecycle Evaluator Trust-Boundary Review (2026-11-11)

- Owner approved a documentation-only security/trust-boundary review of the pure lifecycle evaluator before registry or lifecycle-harness integration.
- Review baseline / starting HEAD: `aa83cea155b4543ed8779583a212fb0b68f3f206`.
- Exact evaluator source reviewed: `pipeline/lifecycle_disposition.py`, blob `cf22385a718c6b5b08cd50c2a45578b4180c2c4d`.
- Exact tests reviewed as verification context: `pipeline/test_lifecycle_disposition.py`, blob `d54d0523d6388df448cbec7c2fb9e2e092f72920`.
- G0.20 CI evidence remains run `43036222952`, job `130575627133`, 32/32 focused tests PASS; it proves the pinned source executed, not authenticity of runtime evidence/metadata.
- Report: `docs/evidence/G0_21_LIFECYCLE_EVALUATOR_TRUST_BOUNDARY_REVIEW_2026-11-11.md`; report creation commit `1c06e8e58dcf3912488882fc31d66b182bac0afc`.
- Main findings: caller-controlled identity/provenance booleans; digest syntax without payload recomputation/signature verification; caller-asserted hold/dependency/copy/lineage completeness; unverified sensitivity evidence and inherited labels; unauthenticated steward/policy claims; caller-asserted rebuildability/non-material-use; no downstream authorization enforcement; incomplete supported class vocabulary; generic Mapping input without a canonical authenticated envelope.
- Evaluator remains a pure in-memory classifier and has no I/O/executor capability. Positive dispositions are not evidence verification, owner authorization or deletion approval.
- Recommended design-only boundary: untrusted claimants/source adapters → authenticated evidence verifier → bounded/versioned verified-facts envelope → pure evaluator → separate exact-object owner authorization → separately approved guarded executor.
- No signature algorithm, key hierarchy/trust root, canonical encoding, freshness window, revocation protocol, physical schema/registry or executor contract was selected.
- G0.21 verdict: **CONDITIONAL PASS — trust gaps identified and target boundary specified; trust/authenticity NOT ESTABLISHED**.
- Caller/issuer authentication, payload digest recomputation, signature verification, exact-version provenance, inventory completeness, sensitivity inheritance authentication, steward authority, rebuildability/non-material-use proof and downstream authorization remain NOT ESTABLISHED.
- TEST-01–07 remain 0/87; runtime/VPS inventory NOT PERFORMED / NOT VERIFIED; destructive authority NOT GRANTED.
- Documentation-only: no source/test/fixture/schema/API/registry/adapter/runner/oracle/workflow/scheduler/permission/credential/database/storage/market-data/model/ledger/VPS/runtime changes; no tests or workflow dispatch; no inventory/secret scan/network/provider/database/VPS access; no archive/quarantine/cleanup/expiry/compaction/vacuum/deletion.
- Next gate proposed: G0.22 — Verified-facts Envelope and Verifier Contract. This requires separate approval before implementation. G0.23 synthetic verifier tests, G0.24 evaluator adapter, TEST-01–07, runtime inventory and any destructive executor remain separate gates.
- T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## G0.22 — Verified-Facts Envelope and Verifier Contract (2026-11-11)

- Owner approved a documentation-only contract design following G0.21.
- Baseline / starting HEAD: `80e2e7fe9718c008716c50e7905f5523ed1870c7`.
- Report: `docs/evidence/G0_22_VERIFIED_FACTS_ENVELOPE_AND_VERIFIER_CONTRACT_2026-11-11.md`; report commit: `e7f457c9f6368599101a9a02cd4d12a05688ace3`.
- Contract defines untrusted claimant/source adapters → evidence verifier → bounded immutable verified-facts envelope → pure lifecycle evaluator → separate exact-object owner authorization → separately approved guarded executor.
- Required verifier controls: authenticated issuer and scoped authority; exact immutable subject/evidence binding; digest recomputation and approved authenticity proof; producer/build/input/output provenance; authoritative inventory scope/completeness closure; authenticated policy and G0.17 sensitivity inheritance; rebuildability/downstream-use evidence; freshness, expiry and revocation checks; bounded parsing and fail-closed outcomes.
- No signature/hash/canonical-encoding profile, trust root/key hierarchy, revocation protocol, numeric freshness window, physical schema, evidence registry, API or executor was selected. These remain explicit owner/security decisions.
- G0.22 verdict: **DESIGN PASS — contract specified; trust authenticity and operational enforcement NOT ESTABLISHED**.
- G0.23 synthetic verifier tests/fixtures, owner/security ratification of open decisions, G0.24 evaluator adapter, implementation/CI, TEST-01–07, runtime inventory and any executor each remain separate gates and approvals.
- Documentation-only. No source/test/fixture/schema/API/registry/adapter/runner/oracle/workflow/scheduler/permission/credential/database/storage/market-data/model/ledger/VPS/runtime changes; no tests or workflow dispatch; no key operation, network/provider/database/VPS access, inventory, archive, quarantine, cleanup, expiry, compaction, VACUUM or deletion.
- T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## G0.23 — Synthetic Verifier Contract Test Matrix (2026-11-11)

- Owner approved G0.23 synthetic verifier contract test design.
- Baseline / starting HEAD: `be802d46efd7399b84212c9724f70aadb49fa0a2`.
- Report: `docs/evidence/G0_23_SYNTHETIC_VERIFIER_CONTRACT_TEST_MATRIX_2026-11-11.md`; report commit: `dbc03705a16ae84b7419f6d200f9831c7f293c84`.
- Defined 38 wholly synthetic logical cases covering positive control; forged identity/issuer/authority; exact object/version binding; digest/signature/purpose binding; provenance and inventory completeness; sensitivity/policy inheritance; freshness/revocation; malformed/oversized envelopes; downstream-use proof; immutable verified-facts output; and separation from owner authorization/execution.
- Fixture identifiers and data must be synthetic only. No real identities, production evidence, T0/T1/T2 records, credentials, keys or secrets.
- Because G0.22 leaves physical schema, verifier interface, cryptographic profile, trust root, revocation source, freshness windows, registries and resource limits open, G0.23 records abstract fixture descriptors and expected outcomes only. No serialized/executable fixture files or test modules were created.
- G0.23 verdict: **TEST-DESIGN PASS — 38 cases specified; executable verification NOT RUN because verifier implementation and ratified physical envelope/trust profile do not exist.**
- No source/test module/fixture/schema/API/registry/adapter/runner/oracle/workflow/scheduler/permission/credential/key/database/storage/market-data/model/ledger/VPS/runtime changes; no test or workflow dispatch; no network/provider/database/VPS access, inventory or secret scan; no archive, quarantine, cleanup, expiry, compaction, VACUUM or deletion.
- Next: owner/security decision package for open cryptographic, trust-root, canonical encoding, revocation/freshness, registry, schema and resource-limit choices. Verifier implementation and executable synthetic tests require separate approval. G0.24 adapter, TEST-01–07, runtime inventory and any executor remain separate gates.
- T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## G0.24 — Owner/Security Decision Package (2026-11-11)

- Owner requested continuation after G0.23; prepared a documentation-only decision worksheet.
- Baseline HEAD: `9d46abb937fa553523e2f5c2dc564826f7a96b74`; branch compare confirmed the active branch was identical to this SHA before the G0.24 change.
- Report: `docs/evidence/G0_24_OWNER_SECURITY_DECISION_PACKAGE_2026-11-11.md`.
- Report commit: `cf78562c62187775bd00f3e15d700ab19e618c47`.
- Decision register D01–D14 covers cryptographic integrity/authenticity, canonical representation, trust roots/delegation, key lifecycle, envelope schema, evidence authorities, inventory closure, freshness/revocation, owner authentication, data-class vocabulary, resource limits, audit custody, verified-facts binding and review/release gates.
- Candidate approaches and decision criteria are documented; **no option is ratified**. All D01–D14 remain OPEN and block dependent implementation.
- G0.24 verdict: **DECISION PACKAGE DRAFTED — owner/security ratification pending; trust profile NOT ESTABLISHED**.
- Documentation-only. No source/test/fixture/schema/API/registry/adapter/runner/workflow/permission/credential/key/database/storage/market-data/model/ledger/VPS/runtime change; no tests or workflow dispatch; no network/provider/database/VPS access or inventory; no archive, quarantine, cleanup, expiry, compaction, VACUUM or deletion.
- Next: owner/security review and explicit exact-scope decisions. Verifier/parser/schema/registry/adapter, real keys, evidence-source integration, CI permission changes, TEST-01–07, runtime inventory and any executor remain separate gates.
- T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## G0.25 — D01–D04 Crypto, Trust and Key-Lifecycle Assessment (2026-11-11)

- Baseline HEAD: `dc75ab5ce6a4f5cc5db82fa9ebe48ff0a2825509`.
- Report: `docs/evidence/G0_25_D01_D04_CRYPTO_TRUST_KEY_RECOMMENDATIONS_2026-11-11.md`.
- Report commit: `721b069e390830d82498f5168633b252fbee7d68`.
- Technical recommendations: D01 DSSE + Ed25519 + SHA-256; D02 RFC 8785 JCS over UTF-8 JSON with strict parsing/numeric/Unicode rules; D03 offline owner root + narrowly scoped delegated issuer keys + verifier-owned trust policy; D04 offline root and hardware-backed or managed isolated issuer signing, never plaintext private keys on VPS/CI.
- All four are recommendations only; D01–D04 remain OPEN and NOT RATIFIED. D06–D09/D12 dependencies remain unresolved.
- G0.25 verdict: TECHNICAL ASSESSMENT PASS — recommendations documented; trust profile NOT ESTABLISHED.
- References consulted: DSSE protocol/PAE, RFC 8785, RFC 8032. No source implementation or test vectors were created.
- Documentation-only. No source/test/fixture/schema/API/registry/adapter/workflow/permission/credential/key/database/storage/market-data/model/ledger/VPS/runtime changes; no tests or workflow dispatch; no network/provider/database/VPS access or inventory; no key operations or lifecycle mutation.
- Next: owner reviews and explicitly ratifies/modifies/rejects D01–D04. No verifier implementation, real keys, trust registry, evidence-source adapters or runtime integration authorized.
- T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## G0.26 — Minimal Signature Scope Reconciliation (2026-11-11)

- Owner requested continuation of the documentation-only minimal-signature review after G0.25; no cryptographic decision was ratified.
- Baseline handoff blob before G0.26: `d3fa7ab5d92517456832f08f072ec21b6a7767a6`.
- Report: `docs/evidence/G0_26_MINIMAL_SIGNATURE_SCOPE_RECONCILIATION_2026-11-11.md`; report creation commit: `b85bbc57885c2113cec842919e6dce3297f299fa`.
- G0.26 separates byte integrity, signer authenticity, owner authorization, freshness/anti-replay, evidence truth/completeness and custody. These claims are not interchangeable.
- G1 A in T0 Checkpoint Contract v1 remains an unsigned proof-of-existence product. A1 is a separate signature/trust extension; do not retroactively impose signer-authenticity claims on G1 A.
- Minimality framework: digest-only for byte-integrity claims; a detached, domain-separated signature binding exact subject/version, digest, purpose and audience only where signer authenticity is required; separate owner authorization for actions; separate anchor/freshness mechanism only where latestness is claimed.
- G0.25 D01–D04 were assessed for complexity/justification but remain OPEN / NOT RATIFIED. D05–D14 remain OPEN; D06–D09/D12/D13 dependencies are unresolved. No option was approved or rejected by G0.26.
- G0.26 verdict: **ANALYSIS PASS — minimality principles and cross-document boundaries recorded; signature profile NOT RATIFIED; implementation NOT AUTHORIZED**.
- Documentation-only. No source/test/fixture/schema/API/registry/adapter/workflow/CI permission/credential/key/trust-root/provider/database/storage/market-data/model/ledger/VPS/runtime changes; no tests or workflow dispatch; no key operations, signing, anchor creation, inventory, provider/network/database/VPS access or lifecycle mutation.
- Next owner decision: identify exact G0 evidence classes that require signer authenticity versus digest integrity only; then explicitly ratify/modify/reject D01–D04. Do not infer ratification from continuation requests. Synthetic verification, verifier implementation, real evidence adapters and runtime integration remain separate gates and approvals.
- T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## G0.27 — G0 Evidence-Class Assurance Requirements Matrix (2026-11-11)

- Baseline HEAD: `db95116a5b0625835eda78abcbb5050bd5f79aa6`; active branch was identical to this baseline before G0.27.
- Report: `docs/evidence/G0_27_G0_EVIDENCE_CLASS_ASSURANCE_REQUIREMENTS_MATRIX_2026-11-11.md`.
- Report creation commit: `53131e89b555da3b757326f3823bbd07c73eaf05`.
- Classified 14 evidence classes against six separate assurance dimensions: byte integrity, signer/issuer authenticity, owner authorization, freshness/anti-replay, completeness/provenance, and custody/readback.
- Key boundaries: G1 A remains unsigned; signer authenticity is claim-specific; owner authorization is a separate gate; signatures do not prove completeness or custody; custody claims require independent readback; freshness is required only for claims that depend on current/latest/non-revoked state.
- G0.27 verdict: **CLASSIFICATION PASS — claim-specific assurance requirements mapped; D01–D14 remain OPEN / NOT RATIFIED where previously open; cryptographic profile and implementation NOT AUTHORIZED**.
- Documentation-only. No source/test/fixture/schema/API/registry/adapter/runner/workflow/permission/credential/key/trust-root/database/storage/market-data/model/ledger/VPS/runtime changes; no tests or workflow dispatch; no key operations, signing, anchor creation, provider/network/database/VPS access or inventory; no archive, quarantine, cleanup, expiry, compaction, VACUUM or deletion.
- Next: owner/security review of evidence-class boundaries; then explicitly ratify/modify/reject only the applicable D01–D14 decisions. Synthetic executable verification, verifier implementation, real evidence adapters, owner authorization and any executor remain separate gates and approvals.
- T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## G0.28 — Owner Decision Closure and Dependency Matrix (2026-11-11)

- Baseline HEAD: `12f781b077526eae3b5856fdb3c6a9ceba724ce4`; baseline handoff blob: `803a47772461d4d510718e5c088f746fc512f18a`.
- Report: `docs/evidence/G0_28_OWNER_DECISION_CLOSURE_DEPENDENCY_MATRIX_2026-11-11.md`.
- Report creation commit: `b118101eca29c1a17fc2e5aa6ae55c22a11aab06`.
- Mapped D01–D14 into claim/stage dependencies, conditional deferral rules, and closure evidence. Defined staged minimum decision sets for documentation-only, synthetic logical tests, synthetic cryptographic tests, real evidence verification, owner authorization and guarded execution.
- Key distinction: a decision may be deferred only by explicitly excluding every dependent capability/claim from that stage. D01–D04 are coupled for real issuer authenticity; D05/D10/D11 are prerequisites for bounded synthetic executable contract work; D06–D08 govern real-source authority/completeness/freshness; D09/D12/D13 gate owner authorization and trust-boundary binding; D14 controls transitions.
- G0.28 verdict: **DEPENDENCY ANALYSIS PASS — decision scope reduced and dependencies mapped; all D01–D14 remain OPEN / NOT RATIFIED; implementation and operational authority NOT GRANTED**.
- Documentation-only. No source/test/fixture/schema/API/registry/adapter/runner/workflow/permission/credential/key/trust-root/database/storage/market-data/model/ledger/VPS/runtime changes; no tests or workflow dispatch; no cryptographic operations, provider/network/database/VPS access or inventory; no archive, quarantine, cleanup, expiry, compaction, VACUUM or deletion.
- Next: owner must explicitly choose the scope of the first executable milestone, including supported evidence classes and claims. Do not infer this scope decision or any D01–D14 ratification from a continuation request.
- T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## G0.29 — First Executable Milestone Scope Proposal (2026-11-11)

- Baseline HEAD: `842b6aed7cf71e9681b227a1a14b3cb5a4e339db`; baseline handoff blob: `d3b424a5aecd08baee554285ecf1009d2e802ec8`.
- Owner approved preparation of the G0.29 proposal; this does not authorize implementation or tests.
- Report: `docs/evidence/G0_29_FIRST_EXECUTABLE_MILESTONE_SCOPE_PROPOSAL_2026-11-11.md`.
- Report creation commit: `048df0cd0bdba0b32c2641f29211e18186954f09`.
- Compared S1 deterministic synthetic parser/contract tests without cryptography against S2 synthetic cryptographic verifier tests with isolated test-only keys.
- Recommendation: **S1 first** because it has a smaller dependency and risk surface; it can validate deterministic parsing, schema, exact structural binding, bounded inputs and fail-closed behavior without selecting cryptographic algorithms or creating keys. S2 is deferred until S1 acceptance and separate approval.
- S1 prerequisites before implementation: D05 synthetic schema/version contract; D10 explicit synthetic-only class allowlist; D11 measured bounded resource limits; D14 exact implementation/test gate. D01–D04, D06–D09, D12 and D13 remain OPEN and excluded only because S1 explicitly makes no dependent claims.
- G0.29 verdict: **PROPOSAL PASS — S1 recommended; S1 implementation/test execution NOT AUTHORIZED; no D01–D14 ratified**.
- Documentation-only. No source/test/fixture/schema/API/registry/adapter/runner/workflow/permission/credential/key/trust-root/database/storage/market-data/model/ledger/VPS/runtime changes; no tests or workflow dispatch; no cryptographic operations, provider/network/database/VPS access or inventory; no archive, quarantine, cleanup, expiry, compaction, VACUUM or deletion.
- Next owner decision: explicitly approve or modify the exact S1 scope, D05/D10/D11/D14 decisions, permitted paths, commands, CI inclusion and acceptance evidence. Do not infer implementation authorization from approval of this proposal.
- T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## G0.30 — S1 Owner Decision Package (2026-11-11)

- Baseline HEAD: `51ac7ed3845ce94d43e74c1d9e9aca9517292e3f`; baseline handoff blob: `f1bdb1ef51b151a4cbb5729ccb0235e4e913a6f1`.
- Report: `docs/evidence/G0_30_S1_OWNER_DECISION_PACKAGE_2026-11-11.md`.
- Report creation commit: `2fefcd681531d13f437dbe970406d3195a2a52cb`.
- G0.30 prepared explicit owner options for S1 only: D05 Synthetic Contract Fixture v1 strict JSON/schema contract; D10 a separate 11-value synthetic-only `fixture_type` vocabulary; D11 resource-limit measurement method and provisional ceilings; D14 bounded implementation paths, focused local commands and acceptance evidence.
- D11 caveat: G0.23 contains abstract fixture descriptors, not serialized fixture bytes. Numeric ceilings (64 KiB input, depth 8, 32 object members, 64 array items, 1 KiB/string, 512 scalar nodes, 16 reason codes) are provisional candidate ceilings, not empirically measured. Recommendation is to ratify measurement-first and measure a synthetic corpus before fixing numeric ceilings.
- Proposed implementation paths if separately authorized: `pipeline/synthetic_contract.py`, `pipeline/test_synthetic_contract.py`, docs/evidence and handoff only. No CI workflow changes in initial S1 increment.
- G0.30 verdict: **DECISION PACKAGE PASS — D05/D10/D11/D14 remain OPEN; S1 implementation/tests NOT AUTHORIZED**.
- Documentation-only. No source/test/fixture/schema/API/registry/adapter/runner/workflow/permission/credential/key/trust-root/database/storage/market-data/model/ledger/VPS/runtime changes; no tests or workflow dispatch; no cryptographic operations, provider/network/database/VPS access or inventory; no lifecycle mutation.
- Next owner decision: explicitly ratify or amend each D05/D10/D11/D14 recommendation. No implementation authorization is implied.
- D01–D04, D06–D09, D12 and D13 remain OPEN / NOT RATIFIED. T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## G0.31 — Owner Ratification of S1 Decisions (2026-11-11)

- Baseline HEAD: `1eacb16bf78aa96818a5bd4ec34e4ef4d4bb8d14`; baseline handoff blob: `c2ce28871cef5ded62f8c4c5fd54be0aab9cd7bf`.
- Owner explicitly approved all four G0.30 recommendations without amendment.
- Report: `docs/evidence/G0_31_OWNER_RATIFICATION_S1_DECISIONS_2026-11-11.md`.
- Report creation commit: `daf7d989a42c9822e80dc7986fb022c5343d6577`.
- D05 OWNER-RATIFIED: Synthetic Contract Fixture v1 structure; UTF-8 JSON only; strict duplicate/unknown/type/version/encoding rejection; parser-only reason codes; no trusted facts or cryptographic semantics.
- D10 OWNER-RATIFIED: closed 11-value synthetic-only `fixture_type` allowlist. It is separate from production `data_class`.
- D11 OWNER-RATIFIED: measurement-first resource policy. Numeric candidate ceilings from G0.30 are explicitly NOT RATIFIED; measure a synthetic corpus, report maxima and safety margin, then seek separate approval of numeric limits.
- D14 OWNER-RATIFIED: future S1 boundary is limited to `pipeline/synthetic_contract.py`, `pipeline/test_synthetic_contract.py`, evidence docs and handoff; focused local commands are specified; no CI workflow changes. This ratifies the boundary only, not permission to begin implementation or run tests.
- G0.31 verdict: **OWNER-RATIFICATION PASS — D05/D10/D11 measurement-first/D14 ratified; numeric D11 ceilings remain open; S1 implementation/tests NOT AUTHORIZED**.
- D01–D04, D06–D09, D12–D13 remain OPEN / NOT RATIFIED. No source/test/fixture/schema implementation, workflow, key, cryptographic operation, provider/network/database/VPS/runtime access or lifecycle mutation.
- Next gate: prepare measured synthetic corpus profile and numeric-limit proposal as documentation/evidence only, or obtain separate exact approval for S1 implementation. Do not infer implementation authority from G0.31.
- T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## G0.32 — S1 Synthetic Corpus Measurement Specification (2026-11-11)

- Baseline HEAD: `67d141397b8498f4824ecc64230e627794da675e`; baseline handoff blob: `6d16a8de8ee22f1caac557033fb9a655428e681e`.
- Inputs re-read: G0.23 test matrix, G0.30 S1 owner decision package, G0.31 owner ratification.
- Report: `docs/evidence/G0_32_S1_SYNTHETIC_CORPUS_MEASUREMENT_SPEC_2026-11-11.md`.
- Report creation commit: `76013861f3dc90ba0296675394af4a27178a5a2b`.
- Defines S1-only structural subset of G0.23: SYN-01 structural positive control; SYN-29 malformed/duplicate/trailing input; SYN-30 unsupported schema/critical field; SYN-31 resource-boundary shapes; SYN-32 structural type/required-field failures. SYN-33 remains deferred because its extension semantics are unresolved. SYN-02–28 and SYN-34–38 are explicitly excluded from S1 measurement because they require verifier/trust/downstream authorization capabilities.
- Specifies synthetic corpus strata, data hygiene, raw-byte and structural measurement definitions, deterministic measurement procedure, evidence record and a blank numeric-ceiling decision table.
- D11 measurement-first remains in force. No numeric ceilings were proposed or ratified; G0.30 candidate values remain NOT RATIFIED.
- G0.32 verdict: **SPECIFICATION PASS — measurement method and case boundaries documented; corpus payloads/measurements NOT CREATED/NOT RUN; numeric ceilings OPEN; implementation/tests NOT AUTHORIZED**.
- Documentation-only. No parser/source/test/fixture bytes, schema implementation, API/registry/adapter/runner/oracle/workflow/permissions/credentials/keys/trust roots/database/storage/market-data/model/ledger/VPS/runtime changes; no tests, fixture generation, measurement execution, workflow dispatch, network/provider/database/VPS access or inventory; no lifecycle mutation.
- Next gate requires separate owner authorization for synthetic corpus creation and isolated measurement only. That authorization would not permit parser implementation, tests or CI changes unless explicitly included.
- D05/D10/D11 measurement-first/D14 remain ratified within S1 limits; numeric D11 ceilings remain open. D01–D04, D06–D09, D12–D13 remain OPEN. T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## G0.33 — S1 Synthetic Corpus Measurement Authorization Package (2026-11-11)

- Baseline HEAD: `58d76499cc824b065aad43c94bd60c12459785ea`; baseline handoff blob: `573460697b31dc4b06cd0cfb0b195639ac6e016c`.
- Inputs re-read: G0.30 owner decision package, G0.31 ratification, G0.32 measurement specification.
- Report: `docs/evidence/G0_33_S1_SYNTHETIC_CORPUS_MEASUREMENT_AUTHORIZATION_PACKAGE_2026-11-11.md`.
- Report creation commit: `1ef3236b64af59ae058b643e26aebbf217bcf57f`.
- Presents exact owner decision G0.33-A: one isolated, deterministic, in-memory synthetic corpus generation and resource-measurement run; S1-only case subset; all 11 D10 fixture types; no persistent fixture files; documentation-only evidence output.
- Explicitly excludes parser/test implementation or execution, CI changes, cryptography/verifier, network/provider/database/VPS/runtime access, production data, T0/T1/T2/ledger mutation, and all lifecycle/destructive operations.
- Numeric D11 ceilings remain OPEN/NOT RATIFIED. The run may propose values but cannot activate/enforce them; a separate owner decision is required.
- G0.33 verdict: **DECISION PACKAGE PASS — bounded owner decision prepared; corpus creation/measurement NOT AUTHORIZED pending explicit approval of G0.33-A**.
- Documentation-only. No corpus bytes generated, no measurements run, no tests/workflows, no source changes, no external access/inventory and no lifecycle mutation.
- Next gate: wait for explicit approval or amendment of G0.33-A. Do not infer authorization from “tiếp theo” or from approval of G0.30/G0.31/G0.32.
- D05/D10/D11 measurement-first/D14 remain ratified within S1 boundaries; numeric D11 ceilings remain open. D01–D04, D06–D09, D12–D13 remain OPEN. T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## G0.34 — S1 Synthetic Corpus Measurement Results (2026-11-11)

- Baseline HEAD: `6c3ac52bc0dacac6e428844f224618b87d6a5399`; baseline handoff blob: `426e7a497a9f1c87b3624c16b332bb024b3d1593`.
- Owner explicitly approved G0.33-A in this conversation: one isolated, deterministic, in-memory synthetic corpus generation and measurement; no persistent fixture files; no parser/tests/CI/runtime/network/database/VPS access; documentation-only evidence; no numeric ceilings ratified.
- Report: `docs/evidence/G0_34_S1_SYNTHETIC_CORPUS_MEASUREMENT_RESULTS_2026-11-11.md`.
- Report creation commit: `5a156f57fe6e1cf1ff31337c177f528312937cee`.
- Corpus revision `G033A-S1-INMEM-24-v1`; 24 fixtures; all 11 D10 values; SYN-01, SYN-29, SYN-30, SYN-31 and SYN-32; two identical measurement passes (24/24).
- Corpus SHA-256 (ordered payload bytes, LF separator): `b6b1ddf4530eea6d92bc7cb6bde4ed6474398db527a08cd36d891c3310b202e7`.
- Aggregate: 16,350 raw bytes total; max payload 3,816 bytes; depth 13; max object members 48; max array items 480; max UTF-8 string value 3,328 bytes; max UTF-8 key 132 bytes; max scalar nodes 489; eight distinct synthetic oracle reason labels.
- Candidate ceilings proposed only: 8,192 raw bytes; depth 16; 64 object members; 640 array items; 4,096 value bytes; 256 key bytes; 1,024 scalar nodes; 16 reason labels. All remain NOT RATIFIED and must not be enforced.
- Important limits: structural/payload-size measurement only; no CPU/RAM benchmark, parser implementation, parser correctness claim or actual parser diagnostic measurement. Malformed/duplicate/trailing/invalid-UTF8 cases report raw size only. No payload files/artifacts persisted.
- G0.34 verdict: **MEASUREMENT PASS — G0.33-A completed within scope; numeric D11 ceilings OPEN/NOT RATIFIED; parser implementation and tests NOT AUTHORIZED**.
- No tests, CI, crypto/verifier, external access, inventory, runtime/VPS/database/network, T0/T1/T2, ledger or lifecycle mutation. T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.
- Next gate: present the exact candidate numeric ceiling table for owner ratification or amendment. Do not begin S1 parser implementation/tests until a separate explicit implementation authorization.

## G0.35 — G0.34 Measurement Evidence Integrity Correction (2026-11-11)

- Baseline HEAD: `807381f03e25fc5a816d0d847f2458a240d411fd`; baseline handoff blob: `cc625179dc34e49455711c13124b143e3a410ce4`.
- Report: `docs/evidence/G0_35_G0_34_MEASUREMENT_EVIDENCE_INTEGRITY_CORRECTION_2026-11-11.md`.
- Report creation commit: `8d02051cb24032b1b1eda6215c78669243f30261`; report blob: `642f35dea186dfb0e5fce7017e92902595b60982`.
- Review found the G0.34 recorded generator serialized the `expected` oracle field into the measured payload, contrary to G0.31 D05 parser-input/oracle separation.
- The execution cell then failed at a namespace assertion comparing bytes to text and terminated before emitting the final aggregate summary object. Intermediate metrics had been computed, but the captured run did not complete its final output/acceptance path.
- Accordingly, G0.34's aggregate metrics, corpus digest and candidate ceilings are **NOT VERIFIED for D11 policy use**. The prior G0.34 MEASUREMENT PASS is superseded by this correction; retain the historical report unchanged.
- G0.33-A authorized exactly one run. That attempt is consumed; no rerun, repaired rerun, persistent fixture creation, parser/test implementation, CI, CPU/RAM benchmark or external/runtime access is authorized. Any further measurement needs a new explicit owner approval.
- G0.35 verdict: **EVIDENCE CORRECTION PASS — G0.34 assurance downgraded to NOT VERIFIED; D05 separation FAIL; numeric D11 ceilings remain OPEN/NOT RATIFIED; parser/tests NOT AUTHORIZED**.
- Next gate: documentation-only proposal for a corrected measurement authorization with oracle/input separation and completion assertions specified before any new separately approved run.
- T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.

## G0.36 — Corrected S1 Measurement Authorization Design (2026-11-11)

- Baseline HEAD: `5b7db072ec71c9594d77e74f49d44937f9552944`; baseline handoff blob: `e9f1879b69d38b37323f2817c0591cd5e528d3ed`.
- Report: `docs/evidence/G0_36_CORRECTED_S1_MEASUREMENT_AUTHORIZATION_DESIGN_2026-11-11.md`.
- Report creation commit: `2c53ed0bd0ee2129e31e688c8cba16e88d755d2b`.
- Corrected protocol separates exact parser-input UTF-8 bytes from external oracle metadata; oracle fields must never be serialized into or measured as parser input.
- Predeclares A-01–A-13 completion assertions, two-pass repeatability, exact raw-byte measurement, malformed/duplicate-key handling, final report readback, evidence fields and stop/fail behavior.
- Retains G0.32 S1 case scope (SYN-01, SYN-29–32; all 11 D10 values); SYN-33 remains deferred.
- Proposes a new bounded G0.37-A owner authorization: one in-memory attempt only, no payload persistence, no parser/tests/CI, no CPU/RAM benchmark, no external/runtime access, no D11 ratification. This is a proposal only.
- G0.34 historical metrics remain NOT VERIFIED for D11 use; G0.33-A is consumed. No re-execution occurred in G0.36.
- G0.36 verdict: **DESIGN PASS — corrected protocol specified; new measurement NOT AUTHORIZED; numeric D11 ceilings OPEN/NOT RATIFIED**.
- No source/tests/fixtures/workflows/dependencies/credentials/keys/runtime/database/network/VPS/market data/model/ledger/lifecycle changes; no tests, workflow dispatch, corpus generation or measurement run.
- Next gate: prepare the G0.37-A owner authorization package for explicit review. Do not execute until separately approved.
- T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.

## G0.37 — S1 Corrected Measurement Owner Authorization Package (2026-11-11)

- Baseline HEAD: `3a39e300400495adca078e9d1042b3613da21ad7`; baseline handoff blob: `0ab7143b30b722cb92f43cfd3dd79db3755700a9`.
- User approval in this conversation authorized preparation of the G0.37 package only; it did not authorize measurement execution.
- Report: `docs/evidence/G0_37_S1_CORRECTED_MEASUREMENT_OWNER_AUTHORIZATION_PACKAGE_2026-11-11.md`.
- Report creation commit: `29747e22e2ad8e711e68a1d84feaa4a9ab031722`.
- Package requests a separate explicit approval for exactly one in-memory attempt: SYN-01, SYN-29–32, all 11 D10 fixture types, separate parser-input/oracle structures, two measurement passes, A-01–A-13, and one validated evidence report without payload persistence.
- Failure/incomplete output consumes the one-attempt authorization if approved; no retry or repair-and-rerun. No parser/tests/CI, benchmarks, external/runtime/VPS/database/network, T0/T1/T2, ledger, lifecycle or destructive operations.
- G0.37 verdict: **PACKAGE READY — preparation approved; measurement execution PENDING EXPLICIT OWNER APPROVAL**.
- G0.34 metrics remain NOT VERIFIED for D11 use; numeric ceilings OPEN/NOT RATIFIED.
- No corpus generation, measurement, source/test/workflow/runtime changes or external access occurred.
- Next gate: await explicit approval of the complete G0.37-A scope in the report. Do not execute before that approval.
- T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.

## G0.37-A — Corrected S1 Synthetic Measurement Attempt (2026-11-11)

- Baseline HEAD: `89fd0d2a9461978a71793d6e7f33cd22fe211c3f`; baseline handoff blob: `5e2c4689bfaf14e095ef43c2cecc18ffb1a7ed09`.
- Owner explicitly approved the exact G0.37-A one-attempt scope in this conversation. The authorization is now consumed.
- One in-memory corpus attempt executed: 22 synthetic fixtures, SYN-01/SYN-29–32, all 11 D10 fixture types; two measurement passes compared equal.
- Intermediate observations: total bytes 42,995; maximum input 16,742 bytes; depth 26 (root=1); max object members 1,251; max array items 720; max string value 5,200 bytes; max key 18 bytes; scalar nodes 1,260. Corpus digest: `e04e13a1025a7957c4f96f550893aa65c029b58a64001e206f5900f2b2ebdb4c`.
- These metrics are NOT VERIFIED for D11 policy use. Review found A-02 was hard-coded true instead of performing D05 structural validation; A-06 did not verify duplicate-key handling; A-10 was hard-coded true and exact harness source revision/hash was not captured. The attempt therefore fails the package acceptance contract.
- Report: `docs/evidence/G0_37A_S1_CORRECTED_MEASUREMENT_ATTEMPT_2026-11-11.md`.
- Report creation commit: `59943a4b81d8bdfe0dbc6d0814c2ef8a6a056d34`; report finalization commit: `f4adda967bb3a9334985a6b5b83d79059c71f019`; final report blob: `868f1a4cb0fa343bebd9e11fdf7bdc4056801c4f`.
- Final report was fetched from GitHub; A-11 report readback PASS. This does not change the overall FAILED/INCOMPLETE verdict.
- G0.37-A verdict: **FAILED / INCOMPLETE — one attempt consumed; no retry or repair-and-rerun authorized**.
- No raw payload/oracle files persisted; no parser/tests/CI, benchmark, external/network/provider/database/VPS/runtime, T0/T1/T2, market data, model, ledger or lifecycle change. No numeric D11 ceiling proposed or ratified.
- Next gate: prepare a new owner decision package before any further measurement. Do not rerun or repair the consumed attempt. D11 remains OPEN / NOT RATIFIED.
- T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.

## G0.38 — G0.37-A Failure Analysis and Corrected Harness Design (2026-11-11)

- Baseline HEAD: `b3fc29d44622f4b4ce7bce00f26ea41c8dd9c547`; baseline handoff blob: `ec6a9d210b7b6c6bee54db2eafe49b43db630158`.
- Report: `docs/evidence/G0_38_G0_37A_FAILURE_ANALYSIS_AND_HARNESS_REDSEIGN_2026-11-11.md`.
- Report creation commit: `575d41e2413ddcda09f0e36866429503e20fcdcf`.
- G0.38 analyzes the consumed G0.37-A failure and specifies future harness controls: executable assertions (no hard-coded PASS), duplicate-aware JSON validation, frozen harness provenance, separate evidence layers, deterministic two-pass checks and independent report readback.
- G0.37-A remains FAILED / INCOMPLETE and its one-attempt authorization remains consumed. No retry, repair-and-rerun or new measurement was performed.
- G0.37-A intermediate metrics/digest remain NOT VERIFIED for D11 policy use. G0.34 historical metrics also remain NOT VERIFIED. Numeric D11 ceilings remain OPEN / NOT RATIFIED.
- G0.38 verdict: **ANALYSIS PASS — failure causes and preventive controls documented; no new execution authority**.
- Documentation-only: no corpus generation/measurement, harness/parser/tests/CI/benchmark, dependencies, external/network/provider/database/VPS/runtime, T0/T1/T2, market-data, model, ledger, lifecycle or destructive changes.
- Next gate: optionally prepare a new owner decision package for a distinct future attempt, after preflight requirements are reviewed. No execution until a separate explicit approval. Parser/tests/CI remain NOT AUTHORIZED.
- T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.

## G0.39 — S1 Measurement Harness Implementation Authorization Package (2026-11-11)

- Baseline HEAD: `e635f157884be14c1a2735d70511f39633716515`; baseline handoff blob: `ad343ebf9f5101d76cb8bd4b942b1ca95fa8ccf3`.
- Input analysis: G0.38 report blob `01775588ebc768801e07c72dc1c72fab874e0765`.
- Report: `docs/evidence/G0_39_S1_MEASUREMENT_HARNESS_IMPLEMENTATION_AUTHORIZATION_PACKAGE_2026-11-11.md`.
- Report creation commit: `084851b2765441b746a2e1e9bb35bc63390e5d01`.
- G0.39 proposes a staged gate: first separately authorize a standalone deterministic measurement harness and focused tests; only after implementation, verification, review and source freeze may a separate G0.40 package request a new measurement.
- Requested paths: `tools/s1_measurement_harness.py` and `tools/test_s1_measurement_harness.py`, plus evidence/handoff. This explicitly requests a narrow D14 amendment; it does not assume the original G0.31 path boundary already permits these files.
- Proposed focused commands, only after approval: `python -m unittest tools.test_s1_measurement_harness -v` and `python -m py_compile tools/s1_measurement_harness.py tools/test_s1_measurement_harness.py`.
- G0.39 verdict: **PACKAGE READY — G0.39-A harness implementation and D14 amendment PENDING EXPLICIT OWNER APPROVAL**.
- No source/test file, corpus, measurement, parser, CI, benchmark, dependency, external/runtime/VPS/database/network or production change. No tests or compile command run.
- G0.37-A remains FAILED / INCOMPLETE and consumed; its intermediate metrics/digest remain NOT VERIFIED for D11 policy use. G0.34 metrics also remain NOT VERIFIED. Numeric D11 ceilings OPEN / NOT RATIFIED.
- G0.40 measurement is NOT AUTHORIZED and requires a separate package and explicit approval. Parser/verifier implementation and CI remain NOT AUTHORIZED.
- T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.

## G0.39-A — S1 Measurement Harness Implementation Results (2026-11-11)

- G0.39-A approved narrowly by owner message “phê duyệt tự động trong phạm vi G0”: standalone harness implementation and D14 amendment for exactly two `tools/` paths. This does not authorize G0.40 measurement or any other open gate.
- Baseline HEAD: `bddbb830fb12faf252b4d824a8f83d3d5bd23b52`.
- Source: `tools/s1_measurement_harness.py`; final blob `0f713a1cc87f4c0c355d4488f1cf6af4d8f08d98`.
- Tests: `tools/test_s1_measurement_harness.py`; final blob `ff5e3c9d584e13948fc4265f9ca261e697fa9da6`; 24 test methods.
- Source/test implementation commits are on the existing branch; no workflow, dependency, CI, production or runtime path changed.
- Harness includes strict UTF-8/JSON handling, duplicate-aware pair preservation, D05 shape/type checks, D10 allowlist, separated parser-input/manifest/oracle structures, exact byte/depth/structural metrics, length-prefixed digest, A-01–A-13 executable predicates, source-hash provenance and safe report readback.
- Local isolated working-copy verification: `python -m unittest tools.test_s1_measurement_harness -v` 24/24 PASS; `python -m py_compile tools/s1_measurement_harness.py tools/test_s1_measurement_harness.py` PASS. TDD RED was observed before module creation.
- Verification limit: final GitHub blobs were read back and statically checked, but were not re-materialized as the exact local checkout after sequential GitHub edits. Therefore exact final-blob test/compile attribution is NOT VERIFIED; overall G0.39-A is PARTIAL / NOT VERIFIED, not PASS.
- Review limitations: non-empty case-specific `claims` schemas are not ratified; harness accepts only empty claims unless a closed schema is supplied. A-12/A-13 static AST inspection plus supplied trace is not OS-level runtime isolation attestation.
- Report: `docs/evidence/G0_39A_S1_MEASUREMENT_HARNESS_IMPLEMENTATION_RESULTS_2026-11-11.md`.
- Report creation commit: `2c0f468120ac42a7b2d3abf2e027449bcf5036ed`.
- G0.39-A verdict: **PARTIAL / NOT VERIFIED — implementation committed/read back; local prototype checks pass; exact final GitHub blob execution not verified**.
- G0.40 corpus generation/measurement remains NOT AUTHORIZED. Numeric D11 ceilings remain OPEN / NOT RATIFIED. Parser/verifier, CI, external/runtime and destructive actions remain NOT AUTHORIZED.
- Next gate: run only the already approved focused test and compile commands against the exact final GitHub HEAD/blob contents; then prepare a separate G0.40 decision package. Do not generate or measure a corpus without a separate explicit G0.40 approval.
- T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.

### G0.39-B — Exact-source verification attempt (2026-11-11)
- Owner request “chạy tự động” applied only to the already-scoped exact-source verification gate: read-only checkout of target HEAD `30fa54e6a24e95a275c4fbfd27170371e1d56d78`, then the two focused unit-test and py_compile commands.
- Attempted read-only Git clone failed before checkout: GitHub hostname resolution error `Could not resolve host: github.com` (exit 128).
- Neither focused command ran against the exact final GitHub checkout. No exact-source PASS may be claimed.
- No GitHub Actions/workflow/artifact, source change, corpus measurement, external runtime, or production action was performed.
- G0.39-B status: **BLOCKED — GitHub DNS/network resolution unavailable**.
- G0.39-A remains PARTIAL / NOT VERIFIED; earlier local working-copy 24/24 tests and compile PASS do not establish final GitHub blob verification.
- Evidence report updated: `docs/evidence/G0_39A_S1_MEASUREMENT_HARNESS_IMPLEMENTATION_RESULTS_2026-11-11.md`; update commit `0f9dfe5fdaf403f7c69a5eb486c9347bfe6da150`.
- Retry only exact read-only checkout plus the two approved commands when GitHub DNS/network is available. G0.40 remains NOT AUTHORIZED.

### G0.39-B — Exact-source verification via GitHub Actions (2026-11-11)

- Owner explicitly approved Cách 2: add and run an isolated GitHub Actions workflow for exact-source verification.
- Workflow: `.github/workflows/g039-b-exact-source-verification.yml`.
- Workflow blob: `1e6241911845762c8770f7e59e23e21d4d51b0a8`.
- Workflow commit / run head: `bae7430ca68fd0ab35806dd7f00d133166c53699`.
- Workflow run ID: `43046949518`; job ID: `130613317796`; conclusion SUCCESS.
- Run URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43046949518
- The workflow checked out exact frozen commit `30fa54e6a24e95a275c4fbfd27170371e1d56d78`, then asserted harness blob `0f713a1cc87f4c0c355d4488f1cf6af4d8f08d98` and tests blob `ff5e3c9d584e13948fc4265f9ca261e697fa9da6`.
- Python 3.14.4; `python -m unittest tools.test_s1_measurement_harness -v`: **24 tests PASS** (`Ran 24 tests in 0.124s`, `OK`); `python -m py_compile tools/s1_measurement_harness.py tools/test_s1_measurement_harness.py`: SUCCESS.
- Artifact: `g039-b-exact-source-verification`, ID `13867028275`, size 1,338 bytes, SHA-256 `554a0bb3afdb00f8f2319471873a128676f7c64549c1c8f9f382170496853d62`; identity, test and compile logs only; expires 2026-11-18T15:17:56Z.
- G0.39-B verdict: **PASS**. The prior exact-source attribution gap is closed; G0.39-A implementation + focused test/compile scope is PASS.
- Evidence report: `docs/evidence/G0_39B_EXACT_SOURCE_VERIFICATION_2026-11-11.md`; report commit `20eabc02ba093c895eb61df2a11a0383294c68e0`.
- Earlier DNS-blocked manual checkout remains historically accurate but is superseded by this successful exact-source GitHub Actions run.
- G0.40 corpus generation/measurement remains NOT AUTHORIZED. Numeric D11 ceilings remain OPEN / NOT RATIFIED. Parser/verifier production implementation and CI beyond this isolated workflow remain NOT AUTHORIZED.
- No T0/T1/T2, runtime/VPS, market-data, model, ledger or destructive changes. T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.

## G0.40 — S1 Measurement Owner Decision Package (2026-11-11)

- Baseline HEAD: `c3eeff5810e64673c6404bfcbae1364b76944a11`; baseline handoff blob: `8b1b133090ae9955b26c524ce25a9b91373e7dc8`.
- G0.39-B exact-source verification: workflow run `43046949518`, job `130613317796`, 24/24 focused tests PASS, compile PASS; exact checkout `30fa54e6a24e95a275c4fbfd27170371e1d56d78`; artifact `13867028275`.
- Harness source/test blobs: `0f713a1cc87f4c0c355d4488f1cf6af4d8f08d98` / `ff5e3c9d584e13948fc4265f9ca261e697fa9da6`.
- Decision package: `docs/evidence/G0_40_S1_MEASUREMENT_OWNER_DECISION_PACKAGE_2026-11-11.md`; report commit `a59c6c1899d0a16d471741359819933bc163b4f1`; report blob `40e6313e20684519f3c5c2522961fc1c22658acf`.
- Recommended G0.40-A: deterministic in-memory corpus builder/measurement orchestrator and focused tests; exact paths `tools/s1_measurement_runner.py`, `tools/test_s1_measurement_runner.py`; narrow D14 amendment requested. Existing frozen harness remains unchanged.
- G0.40-A does not execute corpus measurement. A separate G0.41 package and explicit owner approval are required for one measurement attempt.
- G0.41 measurement, numeric D11 ceiling proposal/ratification/enforcement, parser/verifier, CI/workflow, external/runtime/VPS, T0/T1/T2, market data, model, ledgers and destructive operations remain NOT AUTHORIZED.
- Historical G0.34/G0.37-A metrics and digests remain NOT VERIFIED for D11 use; their one-attempt authorizations remain consumed. No retry or reuse.
- Verdict: **REVIEW PACKAGE READY — G0.40-A and D14 runner-path amendment PENDING EXPLICIT OWNER APPROVAL**.
- Documentation-only. No runner, corpus, fixture, measurement, test, compile, workflow, runtime, database, T0/T1/T2, model, ledger or lifecycle operation. T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.

## G0.40-A — S1 Measurement Runner Implementation Results (2026-11-11)

- Owner approved G0.40-A and D14 amendment for exactly `tools/s1_measurement_runner.py` and `tools/test_s1_measurement_runner.py`.
- Baseline HEAD: `f34706c32c839856a28a5e4fd651508428fafa44`.
- Test-first file commit: `0d5f32ebb816463f8b1294685276f8c14fbfda91`; runner initial commit: `f6dc5d26e7359de5ad48346381689db259fd62ef`; source correction commits: `e36721d1a7264a9c3985d92edde126996a19e944`, `38a841f7d02cdf124def9cc30e7c03ef13315fe5`; final structural-test commit / HEAD: `59b59a4c8505edc0bcaae6e5603efc2329859d73`.
- Final runner blob: `784d2b5381fa50007ceba468b8bc81ce045b80c2`; final tests blob: `47363d0a30cd12795fe43b22e0b5a22f934854bf`; frozen G0.39 harness blob unchanged: `0f713a1cc87f4c0c355d4488f1cf6af4d8f08d98`.
- Runner defines 22 deterministic synthetic fixture recipes, five approved case IDs, all 11 D10 types, separate parser bytes/manifest/oracle, D05/D10 validation, deterministic two-pass test orchestration, runner/harness source digest checks, A-01–A-13 evaluator integration and report readback. SYN-31 structural tests cover nested objects/arrays and exact input byte/structural metrics.
- Compare with G0.40 baseline: ahead 5 / behind 0; exactly two changed files, both approved paths.
- Evidence report: `docs/evidence/G0_40A_S1_MEASUREMENT_RUNNER_IMPLEMENTATION_RESULTS_2026-11-11.md`; report commit `32a867256b047582c611760d35868f39379e4d75`; report blob `6a51f229b2abe031512ab59ef39ff6e1e652f19d`.
- Exact focused commands were NOT RUN. A read-only local checkout attempt failed before checkout because `github.com` DNS resolution failed (Git exit 128). No GitHub Actions workflow was added or dispatched because CI/workflow is outside G0.40-A approval.
- Status: implementation and scope PASS; focused tests NOT RUN/NOT VERIFIED; compile NOT RUN/NOT VERIFIED; TDD RED execution NOT VERIFIED; overall G0.40-A **PARTIAL / NOT VERIFIED**.
- No corpus generation or measurement attempt occurred; no raw payload/oracle/report/digest persisted. G0.41 remains NOT AUTHORIZED. Numeric D11 ceilings remain OPEN / NOT RATIFIED.
- No CI/workflow, dependency, external/provider/network/database/VPS/runtime, T0/T1/T2, market-data, model, ledger, lifecycle or destructive change. T0 remains independent/protected; CORE_LEDGER and AI_LEDGER separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.

### G0.40-A — Exact-source GitHub Actions verification (2026-11-11)

- Owner instruction “tự chạy git action” authorized an isolated exact-source focused verification workflow for G0.40-A.
- Workflow: `.github/workflows/g040-a-exact-source-verification.yml`; blob `ebb0ad4296b8656b62220d3d88be8dc0a8866596`.
- Workflow commit / run head: `6222102147431c25ba2796ab111240e9e1129c18`.
- Exact frozen checkout: `a68d0096f6a04b9ce25591118a47b89660c0965c`.
- Exact runner/test blobs asserted: `784d2b5381fa50007ceba468b8bc81ce045b80c2` / `47363d0a30cd12795fe43b22e0b5a22f934854bf`.
- Workflow run: [43048826022](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43048826022), event `push`, conclusion SUCCESS; job `130620048937` SUCCESS.
- Python 3.14.4; focused unit tests **18/18 PASS**; focused `py_compile` PASS; immutable source identity assertions PASS.
- Artifact `g040-a-exact-source-verification`, ID `13868137683`, 1,153 bytes, GitHub-reported ZIP SHA-256 `fe0d2aefacd12ba6da86bd101333865732b1c652a9ef121e15c6c671495b3247`, expires `2026-11-18T15:29:14Z`. Repository retention policy capped actual retention to 7 days; artifact payload was not independently downloaded/re-hashed.
- Evidence report: `docs/evidence/G0_40A_EXACT_SOURCE_GITHUB_ACTIONS_VERIFICATION_2026-11-11.md`; report commit `5060923dfc4604e3129f4adcd16f39e3fbbbff49`.
- G0.40-A focused implementation verification: **PASS**. TDD RED execution remains NOT VERIFIED; this workflow does not prove a pre-implementation failing test run.
- No separate corpus generation/measurement occurred. G0.41 measurement remains NOT AUTHORIZED; numeric D11 ceilings OPEN / NOT RATIFIED. No parser/verifier implementation, broad CI, runtime/VPS, external/provider/database/network, T0/T1/T2, market data, model, ledger, lifecycle or destructive operation.
- T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## G0.40-A — Source Review and G0.41 Readiness (2026-11-11)

- Read-only review baseline: frozen source commit `a68d0096f6a04b9ce25591118a47b89660c0965c`.
- Reviewed runner blob `784d2b5381fa50007ceba468b8bc81ce045b80c2`, tests blob `47363d0a30cd12795fe43b22e0b5a22f934854bf`, harness blob `0f713a1cc87f4c0c355d4488f1cf6af4d8f08d98`.
- Prior exact-source Actions run `43048826022` remains SUCCESS (18/18 tests and compile PASS).
- Review report: `docs/evidence/G0_40A_SOURCE_REVIEW_G0_41_READINESS_2026-11-11.md`; report commit `f3267fc2b1516e89fcbf28322fad5f789f7d3553`; report blob `eb334331362374db279e37a3a48e3ef1248eeac2`.
- Findings R1–R3 REQUIRED and OPEN:
  - R1: tests use placeholder runner/harness bytes, not actual frozen source; CI blob assertions are separate and not bound into preflight provenance.
  - R2: AST capability denylist can be bypassed by archive extraction, aliased file APIs and unlisted network-capable modules; existing negative probes are incomplete.
  - R3: report readback checks shape/aggregates and digest syntax but not exact ordered fixture inventory, uniqueness or digest binding to parser-input bytes.
- G0.40-A remains PASS for its bounded implementation/test/compile/Actions scope. Review does not retroactively alter that CI result.
- G0.41 measurement readiness: **BLOCKED** until R1–R3 are corrected, focused verification and exact-source CI pass, and source review is complete. No measurement was run during review.
- Numeric D11 ceilings remain OPEN / NOT RATIFIED. G0.34 and G0.37-A one-attempt authorizations remain consumed; no retry or reuse.

## G0.40-B — Exact-Source Assurance Corrections Owner Package

- Package: `docs/evidence/G0_40B_EXACT_SOURCE_ASSURANCE_CORRECTIONS_OWNER_PACKAGE_2026-11-11.md`.
- Package commit `8f273495b334c8dca35a2dfaa1d59bea12b27867`; package blob `304bd6976ffee472b07bfbb5312311bc733d5104`.
- Requests explicit approval for exactly four paths: `tools/s1_measurement_harness.py`, `tools/s1_measurement_runner.py`, `tools/test_s1_measurement_runner.py`, and `.github/workflows/g040-b-exact-source-verification.yml`.
- Acceptance criteria explicitly close R1 actual-source provenance, R2 bounded capability policy, and R3 report-to-corpus integrity.
- This is docs-only. **G0.40-B implementation and workflow are NOT AUTHORIZED pending owner approval.**
- G0.41 corpus generation/measurement remains NOT AUTHORIZED; numeric D11 ceilings OPEN / NOT RATIFIED.
- No T0/T1/T2, market data, model, ledger, runtime/VPS, external/provider/database/network, lifecycle, or destructive changes. T0 remains independent/protected; CORE_LEDGER and AI_LEDGER separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


### G0.40-B — Exact-source assurance corrections implementation and verification (2026-11-11)

- Owner explicitly approved the exact four-path G0.40-B package (`8f273495b334c8dca35a2dfaa1d59bea12b27867`).
- Implementation was limited to:
  - `tools/s1_measurement_harness.py`
  - `tools/s1_measurement_runner.py`
  - `tools/test_s1_measurement_runner.py`
  - `.github/workflows/g040-b-exact-source-verification.yml`
- R1: focused tests now read actual checked-out harness/runner bytes and hash those bytes; workflow independently asserts checkout HEAD equals `GITHUB_SHA`, approved branch, and exact source blobs; commit mismatch and source-digest negative tests added.
- R2: conservative AST import/syntax allowlist replaces incomplete denylist; negative probes cover aliased `io.open`, ZIP/TAR extraction and `smtplib`, plus existing direct `open` and `socket` probes. Claim is explicitly static source-policy validation, **not** OS-level/runtime isolation.
- R3: report readback requires the canonical 22 ordered fixture IDs, exact parser-input inventory and bytes, and recomputes complete rows, aggregates and corpus digest from those bytes. Negative tests cover duplicate, reordered, missing/extra, modified raw-byte counts, altered digest and noncanonical expected inventory.
- Final exact source checkout: `0e757114e738a2330ad4cc96b6cf8d9da7d17c7b`.
- Final source blobs: harness `e8db71c11e0503ea6d9a2480d75470185c4d5100`; runner `23a35aab7f7aeacd8a3f63d630a875fe76b1ff6a`; tests `d06a5b533af14378ed284051e5b057cf57377876`; workflow `d42b57e78cd545099474e9256381f8c428997b1e`.
- Final GitHub Actions run [43050706119](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43050706119), job `130626755285`, exact checkout assertion PASS, **29/29 tests PASS**, focused `py_compile` PASS, Python 3.14.4.
- Artifact `g040-b-exact-source-verification`, ID `13869536480`, 1,469 bytes, GitHub-reported SHA-256 `9ba9734367b41a3e677fb547cf23d91c5d8cef53a4c1f4db1a7dc71e40c74c23`, expiry `2026-11-18T15:40:29Z`. Payload was not independently downloaded/re-hashed.
- Intermediate failures remain recorded in Actions: run `43050375099` (duplicate test keyword syntax error), `43050453674` (stale test blob pin), `43050625804` (stale harness blob pin), and `43050692431` (stale test blob pin). All were corrected before the final successful run.
- Compare from pre-implementation handoff HEAD `a81a92bda4eca626ca002b8399ef008d3526c46e` to verification source: ahead 15 / behind 0; exactly the four approved paths changed.
- Evidence report: `docs/evidence/G0_40B_EXACT_SOURCE_ASSURANCE_CORRECTIONS_RESULTS_2026-11-11.md`; report commit `1ad963fae98c8ba6aafcb4aa4cae302181d00b48`.
- G0.40-B bounded implementation and exact-source focused verification: **PASS**; R1–R3 **CLOSED** within the stated static-source and frozen S1-report boundary.
- TDD pre-implementation RED run: **NOT VERIFIED**. Independent reviewer sign-off: **NOT PERFORMED**. Artifact payload hash: **NOT VERIFIED**.
- G0.41 corpus generation/measurement remains **NOT AUTHORIZED / NOT RUN**. D11 numeric ceilings remain **OPEN / NOT RATIFIED**. No standalone measurement was run.
- No T0/T1/T2, market data, model/training, CORE_LEDGER, AI_LEDGER, Shared Risk Engine, Kill Switch, VPS/runtime, external provider/database/network, lifecycle or destructive change. T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.
- Next gate: prepare a separate G0.41 owner decision package; do not measure the corpus or propose/ratify numeric D11 ceilings until that scope is explicitly approved.


### G0.41 — S1 single-measurement owner decision package (2026-11-11)

- Baseline HEAD before package: `377023bbd56b651879d5a57e341a94a4b431e159`; baseline handoff blob `58f676d97104852d231fc276a9997ad0fffefe45`.
- G0.40-B results report blob: `cc9894cc3d48f4df5f98b62ab7608359e1b7366e`; G0.40-B exact verification run [43050706119](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43050706119), exact source checkout `0e757114e738a2330ad4cc96b6cf8d9da7d17c7b`, job `130626755285`, 29/29 focused tests PASS and py_compile PASS.
- G0.41 owner package: `docs/evidence/G0_41_S1_SINGLE_MEASUREMENT_OWNER_DECISION_PACKAGE_2026-11-11.md`; package commit `ed37acab60df5f35d303f4e352cf474bcae339be`; package blob recorded in the package commit/readback.
- Package proposes exactly one 22-fixture in-memory measurement invocation using the existing frozen harness/runner; two measurement passes are internal determinism checks within that one invocation. It requests a new exact-path workflow `.github/workflows/g041-s1-single-measurement.yml`, a narrow D14 amendment for that path, and one report-only artifact.
- Frozen Python source blobs required by the package: harness `e8db71c11e0503ea6d9a2480d75470185c4d5100`; runner `23a35aab7f7aeacd8a3f63d630a875fe76b1ff6a`; tests `d06a5b533af14378ed284051e5b057cf57377876`.
- G0.41 package preparation was documentation-only. No corpus generation, measurement function, test, workflow dispatch, benchmark or runtime action was performed.
- G0.41 measurement: **PENDING EXPLICIT OWNER APPROVAL / NOT RUN**. Workflow creation and D14 amendment: **PENDING exact-path approval**. D11 numeric ceilings: **OPEN / NOT RATIFIED**.
- One-shot constraints: no retry/rerun/second attempt; report-only artifact, no raw parser-input or oracle payload persistence; no numeric ceiling proposal or enforcement. Failure after invocation begins consumes the one-time authorization.
- Explicit exclusions remain: parser/verifier production implementation, cryptography/trust changes, T0/T1/T2, market/model data, CORE_LEDGER/AI_LEDGER, Shared Risk Engine, Kill Switch, PostgreSQL, VPS/runtime, provider/database/network/exchange and destructive lifecycle operations.
- T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.
- Next gate: owner must explicitly approve or reject the exact G0.41 scope in the package. No measurement is authorized by the package's preparation or by a generic continuation request.


### G0.41 — Owner approval and D14 amendment (2026-11-11)

- Owner explicitly approved the exact one-shot G0.41 package in `docs/evidence/G0_41_S1_SINGLE_MEASUREMENT_OWNER_DECISION_PACKAGE_2026-11-11.md` (package commit `ed37acab60df5f35d303f4e352cf474bcae339be`; package blob `9ac65f797711e1d74e2ff847aad52c87a361cf18`).
- Approved scope is indivisible and one-shot: add exactly `.github/workflows/g041-s1-single-measurement.yml`; amend D14 for that exact workflow; one push-triggered call to the frozen `tools.s1_measurement_runner.prepare_preflight(...)`; persist exactly one bounded JSON report artifact with seven-day retention.
- D14 ratification record amended: commit `79c7023690c66d1b7295ff52feb5db52e102177d`; blob `f2bb2252b68188caf96742a29d2f879cfb33ff5b`. No other D14 paths are added.
- Frozen Python source identities must remain unchanged: harness blob `e8db71c11e0503ea6d9a2480d75470185c4d5100`; runner blob `23a35aab7f7aeacd8a3f63d630a875fe76b1ff6a`; focused tests blob `d06a5b533af14378ed284051e5b057cf57377876`.
- Workflow constraints: exact event SHA/branch, three source-blob assertions, read-only `contents: read`, no secrets/install/network/provider/database/VPS/exchange, Python 3.14.4, timeout ≤5 minutes, no retry, and a first-attempt guard so any GitHub rerun attempt skips before measurement. The sole workflow trigger is the push that adds the exact workflow path; later modifications/manual dispatch/schedule/PR/tag/other branches are excluded.
- The one runner invocation contains two internal deterministic construction/measurement passes. No standalone test suite is run in this workflow because that would invoke the runner repeatedly.
- Persist only one JSON report. No raw parser inputs, oracle payloads, corpus/fixture files, caches or intermediate source copies. No diagnostic-output ceiling invention and no numeric D11 proposal/ratification/enforcement.
- Any pre-invocation source/runtime guard failure: stop and return for a new owner decision, without measurement. Any failure after invocation begins consumes the one-shot authorization; no repair/rerun.
- This approval does not authorize harness/runner/test/dependency changes, production parser/verifier, crypto/trust changes, S2, T0/T1/T2, market/model data, CORE_LEDGER/AI_LEDGER, Shared Risk Engine, Kill Switch, PostgreSQL, VPS/runtime, external services/network or destructive lifecycle actions.
- D11 numeric ceilings remain **OPEN / NOT RATIFIED**. T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.
- At this point the D14 amendment is recorded; the exact workflow file is the remaining implementation step. No G0.41 measurement has yet been invoked.


### G0.41 — Workflow admission blocked before measurement (2026-11-11)

- Owner-approved G0.41 package: commit `ed37acab60df5f35d303f4e352cf474bcae339be`; D14 narrow amendment commit `79c7023690c66d1b7295ff52feb5db52e102177d`, blob `f2bb2252b68188caf96742a29d2f879cfb33ff5b`.
- Exact workflow `.github/workflows/g041-s1-single-measurement.yml` added in commit / event checkout `168d06fbd46348ae23fb21d61e05fb6930c00e10`; workflow blob `c2b0227429a9858860f7b2aef9a8b94f06bca57c`.
- Frozen source blobs remain unchanged: harness `e8db71c11e0503ea6d9a2480d75470185c4d5100`; runner `23a35aab7f7aeacd8a3f63d630a875fe76b1ff6a`; tests `d06a5b533af14378ed284051e5b057cf57377876`.
- GitHub Actions run [43052133091](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43052133091), run attempt 1, job `130631821560`: **SKIPPED**. No steps reported and no artifacts.
- Job-level admission condition did not admit the job. Available metadata does not identify which sub-expression evaluated false; root cause **NOT VERIFIED**.
- `prepare_preflight(...)`: **NOT INVOKED**. No corpus measurement, digest, A-01–A-13 run or report was generated. G0.41 measurement is **NOT RUN**; workflow admission **BLOCKED**.
- Per the approved package's stop condition, no workflow edit, rerun, dispatch, retry or replacement attempt is permitted under the prior approval. The measurement one-shot itself was not consumed because invocation did not begin, but a **new explicit owner decision is required** before correcting the admission gate or attempting another push.
- Evidence report: `docs/evidence/G0_41_S1_PRE_MEASUREMENT_WORKFLOW_BLOCKED_2026-11-11.md`; report commit `90a8cca7dec6ecd9310276fc0237cf53e15784ba`.
- D11 numeric ceilings remain **OPEN / NOT RATIFIED**. No harness/runner/tests/dependency changes, no production parser/verifier/crypto/trust work, no T0/T1/T2, market/model data, ledgers, Shared Risk Engine, Kill Switch, PostgreSQL, VPS/runtime, external provider/network/database or destructive lifecycle action.
- T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.
- Next gate: prepare a new owner decision package limited to diagnosing/correcting the exact workflow admission condition and requesting a fresh one-shot G0.41 attempt. No edits or execution until separately approved.


### G0.42 — G0.41 workflow admission correction owner package (2026-11-11)

- Prepared docs-only owner package: `docs/evidence/G0_42_G041_WORKFLOW_ADMISSION_CORRECTION_OWNER_PACKAGE_2026-11-11.md`.
- Package commit: `91478d3382bdde22bcc9f251d72aff20f8d96a83`.
- G0.41 workflow run [43052133091](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43052133091) was SKIPPED; job `130631821560` reported no steps; no artifact. Frozen runner `prepare_preflight(...)` was NOT INVOKED.
- The workflow job condition included `contains(github.event.head_commit.added, '.github/workflows/g041-s1-single-measurement.yml')`. GitHub REST commit metadata labels the workflow file `added`, but run/job metadata does not expose expression evaluation. Exact false sub-expression and root cause remain **NOT VERIFIED**; the `contains(...)` clause is only a plausible fault, not a proven cause.
- G0.42 requests explicit approval for one edit to the existing workflow path, one narrow D14 amendment, and one fresh one-shot G0.41 measurement attempt. Proposed gate uses exact branch, exact immediate parent SHA (the final handoff HEAD recorded below), `head_commit.id == github.sha`, and `run_attempt == 1`; existing branch/path trigger remains. No `contains(head_commit.added, ...)` check.
- After this package and handoff commit are both recorded, the exact current branch HEAD becomes the required `github.event.before` value for the single authorized implementation push. That exact SHA is the next owner package's baseline and must be copied literally into the workflow condition; no wildcard/fallback.
- Approval scope, if granted, permits only the existing workflow file and the D14 ratification record for this one correction; then exactly one `prepare_preflight(...)` invocation and one bounded JSON artifact if all pre-invocation guards pass. Frozen source blobs remain harness `e8db71c11e0503ea6d9a2480d75470185c4d5100`, runner `23a35aab7f7aeacd8a3f63d630a875fe76b1ff6a`, tests `d06a5b533af14378ed284051e5b057cf57377876`.
- No workflow edit or measurement was performed in G0.42. D11 numeric ceilings remain OPEN / NOT RATIFIED. T0 remains independent/protected; ledgers remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.
- Current disposition: **G0.42 READY FOR OWNER DECISION — WAITING FOR EXPLICIT APPROVAL**. No further changes or execution until the owner approves this exact package.


### G0.41 — One-shot runner completed; report artifact invalid (2026-11-11)

- G0.42 exact-parent correction commit / measurement checkout SHA: `b337318f0e494f90ae2db0e7c5b711a55eaed3f0`; parent was `8f9f854cad4ec460ad10e850613af4d880d0c357`.
- Workflow blob: `5f42799b5b790b3916aea447812dd3f085e1ddf6`; D14 amendment blob: `427cd0caccabd5f255029860eab9d49fb43ab6b4`.
- Frozen Python blobs unchanged: harness `e8db71c11e0503ea6d9a2480d75470185c4d5100`; runner `23a35aab7f7aeacd8a3f63d630a875fe76b1ff6a`; tests `d06a5b533af14378ed284051e5b057cf57377876`.
- GitHub Actions run [43052908975](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43052908975), attempt 1, conclusion SUCCESS; job `130634571198`, all five substantive steps completed successfully. Exact checkout, branch, parent/head, Python 3.14.4 and source blob guards passed.
- Frozen `prepare_preflight(...)` was invoked exactly once. Runner completed: 22 synthetic fixtures, 11 D10 fixture types, case counts SYN-01=11, SYN-29=3, SYN-30=2, SYN-31=3, SYN-32=3; A-01–A-13 all true; two measurement passes equal; runner's internal report readback true; execution trace empty.
- Observed aggregate measurements (diagnostic only; no D11 limit decision): total raw bytes 6,418; max depth 6; max object members 8; max array items 4; max UTF-8 string key 19 bytes; max UTF-8 string value 100 bytes; scalar nodes 13. Corpus digest `1c9a302d9df179322bfd7a00aa6db322a66b578a0609b9264481c3801b8a2d94`.
- Exactly one artifact: `g041-s1-single-measurement-report`, ID `13869458648`, 1,664 bytes ZIP, expiry `2026-11-18T15:53:56Z`; GitHub digest `sha256:14655e26eda4452f21e285ad27c7c3027538d4c796aaaa0c607e84bc8d018af2`. The downloaded ZIP was independently SHA-256 checked and matched GitHub's digest. ZIP contains exactly one JSON file.
- **Artifact defect:** the JSON file ends with literal two-byte sequence `\\n` rather than a JSON whitespace newline. Strict JSON parsing fails with extra data. Removing those two trailing bytes in a local diagnostic copy allows the JSON body to parse and confirms the runner fields above; the artifact itself was not modified or replaced. Thus the runner assertions passed, but the required report artifact is malformed.
- Overall G0.41 disposition: **FAILED / INCOMPLETE — artifact serialization failure after invocation**. The one-shot authorization is consumed. No retry, rerun, repair-and-rerun, second measurement or replacement attempt is authorized. No further workflow edit is made.
- This failure does not authorize a D11 numeric ceiling proposal, ratification or enforcement. Observed maxima are recorded only as diagnostic measurement output. D11 numeric ceilings remain OPEN / NOT RATIFIED.
- No T0/T1/T2, market/model data, CORE_LEDGER, AI_LEDGER, Shared Risk Engine, Kill Switch, PostgreSQL, VPS/runtime, provider/database/network/exchange or destructive lifecycle action occurred. T0 remains independent/protected; ledgers remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.
- Evidence report: `docs/evidence/G0_41_S1_MEASUREMENT_RESULT_ARTIFACT_INVALID_2026-11-11.md`. Next gate: prepare a new owner decision package for a separately authorized artifact-serialization correction/review; no correction or new measurement under the consumed authorization.


### G0.43 — Report serialization correction owner package (2026-11-11)

- G0.42 one-shot run [43052908975](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43052908975), job `130634571198`, completed SUCCESS. Frozen runner was invoked exactly once; 22 fixtures, A-01–A-13 true, two passes equal, internal report readback true, empty execution trace.
- The sole artifact `13869458648` was downloaded and ZIP SHA-256 independently matched GitHub digest `14655e26eda4452f21e285ad27c7c3027538d4c796aaaa0c607e84bc8d018af2`. ZIP contains one JSON report file, but strict JSON parsing fails because its final two bytes are literal backslash+n (`5c 6e`), not a JSON newline. Artifact was preserved unmodified.
- G0.41 overall: **FAILED / INCOMPLETE — artifact serialization failure after invocation**. G0.42 one-shot authorization consumed; no repair/rerun/second attempt allowed.
- Evidence report: `docs/evidence/G0_41_S1_MEASUREMENT_RESULT_ARTIFACT_INVALID_2026-11-11.md`; commit `a3ceac0cd4558bd75a5987ab377a9e6e31e7dfc6`; blob `0f81d6ea245d4a02e2d4da8c6849c64560a31749`.
- Prepared G0.43 docs-only owner package: `docs/evidence/G0_43_G041_REPORT_SERIALIZATION_CORRECTION_OWNER_PACKAGE_2026-11-11.md`. It requests a new explicit approval for one correction to the existing workflow, one narrow D14 amendment and one fresh one-shot measurement. Required serialization fix: write exact UTF-8 JSON bytes without literal suffix, parse those exact bytes before upload, require object equality and reject trailing data. The validation must not call the frozen runner again.
- G0.43 exact implementation parent if approved: `a3ceac0cd4558bd75a5987ab377a9e6e31e7dfc6`. No workflow or source code changed in this milestone; no measurement performed.
- Frozen Python blobs remain unchanged: harness `e8db71c11e0503ea6d9a2480d75470185c4d5100`; runner `23a35aab7f7aeacd8a3f63d630a875fe76b1ff6a`; tests `d06a5b533af14378ed284051e5b057cf57377876`.
- D11 numeric ceilings remain OPEN / NOT RATIFIED. T0 remains independent/protected; ledgers separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.
- Current disposition: **G0.43 READY FOR OWNER DECISION — WAITING FOR EXPLICIT APPROVAL**.


### G0.43 — G0.41 report serialization correction PASS (2026-11-11)

- Implementation/measurement checkout: `93ac905a3b8afb5bebb7c841140c0bccb9f1a47c`; exact parent/event-before: `66a2f9fc70c09ffbe073dfc98acfb500df5aeb42`.
- Workflow blob `dcfcb09f865ddfc280a4c7368f5ba68036ad9bac`; D14 blob `c9793430e8a92f66ad1fa3d783cade5ff5481104`.
- Frozen Python blobs unchanged: harness `e8db71c11e0503ea6d9a2480d75470185c4d5100`; runner `23a35aab7f7aeacd8a3f63d630a875fe76b1ff6a`; tests `d06a5b533af14378ed284051e5b057cf57377876`.
- GitHub Actions run [43053648998](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43053648998), job `130637223760`, attempt 1, SUCCESS. Exact parent/head/branch/runtime/source guards PASS. Frozen runner invoked exactly once.
- Exactly one artifact `g041-s1-single-measurement-report`, ID `13870492247`, 1,661 bytes, expiry `2026-11-18T15:58:31Z`. GitHub SHA-256 `4cdefc2ed049bd49b1092fb8cf113f92b411c08281f9f7c8db0137e36a85fcca`; independently downloaded ZIP hash matched. ZIP contains exactly one JSON file; strict JSON parse and exact 13-key inventory PASS; persisted JSON has no literal suffix or trailing non-whitespace.
- Measurement: 22 fixtures; 11 D10 types; SYN-01=11, SYN-29=3, SYN-30=2, SYN-31=3, SYN-32=3; A-01–A-13 all true; two passes equal; internal readback true; execution trace empty. Corpus SHA-256 `1c9a302d9df179322bfd7a00aa6db322a66b578a0609b9264481c3801b8a2d94`.
- Observed diagnostic maxima: raw bytes 6,418; depth 6; object members 8; array items 4; key bytes 19; value bytes 100; scalar nodes 13. These are measured values only, not D11 limits.
- Evidence report: `docs/evidence/G0_43_G041_REPORT_SERIALIZATION_CORRECTION_RESULTS_2026-11-11.md`. G0.43 PASS for the exact workflow correction, one measurement and artifact verification. D11 numeric ceilings remain OPEN / NOT RATIFIED. Next: build evidence-based D11 measured-limit proposal, document assumptions/headroom and failure modes, then apply standing authorization only within the established bounded G0 governance scope.
- No T0/T1/T2, canonical data, model/training, ledgers, Shared Risk Engine, Kill Switch, PostgreSQL, VPS/runtime, provider/database/network/exchange or destructive lifecycle operations. T0 protected; ledgers separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


### G0.44 — D11 measured resource limits ratified and complete (2026-11-11)

- Accepted G0.43 evidence: checkout `93ac905a3b8afb5bebb7c841140c0bccb9f1a47c`; Actions run `43053648998`, job `130637223760`; artifact `13870492247`; independently verified ZIP SHA-256 `4cdefc2ed049bd49b1092fb8cf113f92b411c08281f9f7c8db0137e36a85fcca`; corpus SHA-256 `1c9a302d9df179322bfd7a00aa6db322a66b578a0609b9264481c3801b8a2d94`.
- 22 synthetic fixtures, all 11 D10 types; A-01–A-13 all true; two passes equal; empty execution trace. Observed maxima: raw bytes 501 per fixture; depth 6; object members 8; array items 4; string value 100 UTF-8 bytes; key 19 UTF-8 bytes; scalar nodes 13; one fixed reason code per invalid fixture (scalar return contract; A-02 oracle validation).
- Ratified D11 ceilings: raw input 8,192 bytes; depth 8 (root container level 1); object members 32/object; array items 64/array; string value 1,024 UTF-8 bytes; string key 256 UTF-8 bytes; scalar nodes 256/fixture; diagnostic reason codes 1/invalid fixture.
- Ratified fail-closed policy: reject any over-limit input; raw-byte check before decode/parse; strict UTF-8; malformed input structural metrics N/A; measure duplicate keys from original bytes; no truncation/normalization/silent drop/raw-input echo/partial acceptance; no more than one fixed reason code.
- Decision recorded under user's standing bounded authorization through D11. Full table and rationale: `docs/evidence/G0_44_D11_MEASURED_RESOURCE_LIMITS_RATIFICATION_2026-11-11.md`.
- D11: **COMPLETE — MEASUREMENT-FIRST REQUIREMENT SATISFIED; NUMERIC CEILINGS AND FAIL-CLOSED STRUCTURAL POLICY RATIFIED.**
- Runtime enforcement: **NOT IMPLEMENTED / NOT VERIFIED**. No parser/verifier source, tests, CI, runtime, T0/T1/T2, data, ledgers, risk engine, VPS, external services or destructive lifecycle changes. D14 implementation scope remains separate. D01–D04, D06–D09 and D12–D13 remain OPEN / NOT RATIFIED.

## G0.45 — S1 synthetic parser implementation owner package (2026-11-11)

- D11 completion is recorded in G0.44; exact ceilings and fail-closed structural policy are ratified. Runtime enforcement remains NOT IMPLEMENTED / NOT VERIFIED.
- Current branch baseline: `6a8491526dceceeabfdb048a5621bf2f2e273809`.
- Prepared documentation-only owner package: `docs/evidence/G0_45_S1_SYNTHETIC_PARSER_IMPLEMENTATION_OWNER_PACKAGE_2026-11-11.md`.
- Package requests explicit authorization for exactly `pipeline/synthetic_contract.py`, `pipeline/test_synthetic_contract.py`, one G0.45 evidence report and this handoff update.
- The requested parser is synthetic-only and pure/in-memory. It must enforce the D05/D10 contract and all G0.44 D11 ceilings. It conveys no trust, verified-facts, lifecycle, authorization or execution authority.
- Proposed focused TDD gate: `python -m unittest pipeline.test_synthetic_contract -v` and `python -m py_compile pipeline/synthetic_contract.py pipeline/test_synthetic_contract.py`; no workflow/CI changes or broad suite.
- No implementation, test, compile, workflow, runtime, T0/T1/T2, data, ledger, risk-engine, VPS, external-service or destructive lifecycle action was performed in G0.45 package preparation.
- **G0.45 disposition: READY FOR OWNER DECISION — S1 parser implementation NOT AUTHORIZED pending explicit approval of the exact package.**

### G0.45 — S1 synthetic parser implementation and focused verification (2026-11-11)

- Owner granted standing bounded automatic approval through S1 completion; G0.45 exact package scope was applied. Package commit: `ab838f824a9f60fe4e872ad4c99032e0b1b7bb76`.
- Implemented exactly `pipeline/synthetic_contract.py` and `pipeline/test_synthetic_contract.py`; added this evidence report and updated handoff. No other paths changed.
- Parser blob: `f114bd08de56ff641e29697f63ac6d11d127e3cc`; test blob: `4125d56f94ea4c06df6fa6f3c02232e23ec61108`.
- TDD RED: focused unittest import failed as expected while parser module was absent. GREEN: exact focused unittest command **22/22 PASS**. `py_compile` on both files PASS. Local isolated Python runtime: 3.13.5. No dependency installation.
- Implements strict UTF-8 JSON, D05 structure, all 11 D10 values, duplicate-key rejection before mapping conversion, one fixed reason code, no raw-input echo, no trust/execution authority, and all G0.44 D11 ceilings.
- The frozen S1 measurement recipe has empty claims objects and no non-empty claims schemas; parser therefore rejects non-empty claims fail-closed. No unratified claims schema was invented.
- Focused source review performed; independent reviewer sign-off NOT PERFORMED. Full repository suite and GitHub Actions were not run because the G0.45 D14 scope excluded broader suite/CI changes.
- **G0.45: PASS — bounded S1 synthetic parser implementation and focused verification.** Production verifier/cryptography/trust/runtime remain NOT IMPLEMENTED / NOT AUTHORIZED. T0 protected; T1/T2 unchanged; ledgers separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.


## G0.46 — S2 minimal trust and key owner decision package (2026-11-11)

- Owner approved preparation of G0.46 as documentation-only work on the existing branch. Baseline before this increment: `799d8dfc273a690c16279ee40c1ca6fa02aa0f59`.
- Added `docs/evidence/G0_46_S2_MINIMAL_TRUST_AND_KEY_OWNER_DECISION_PACKAGE_2026-11-11.md` in package commit `04a60805821400b656eebeaabcfe4e11d72720af`.
- Package applies G0.26 minimality: digest integrity, issuer authenticity, owner authorization, freshness/anti-replay, and evidence truth/completeness/custody remain separate claims.
- G1 A remains unsigned under T0 Checkpoint Contract v1; A1 remains a separate extension. No retroactive signature requirement is introduced.
- D01–D04 remain OPEN / NOT RATIFIED. Recommendations are conditional: digest-only where integrity is sufficient; evaluate DSSE/Ed25519/SHA-256 only for named issuer-authenticity claims; JCS only for structured signed statements; avoid delegated multi-issuer topology unless distinct principals require it; no real key operation in the current paper-only posture.
- D06–D09 and D12–D14 remain dependencies for evidence authority, inventory closure, freshness/revocation, owner authentication, audit/custody, verified-facts binding and exact S2 implementation scope.
- Independent reviewer sign-off remains waived as a mandatory gate under the prior owner decision; no independent assurance claim is made.
- G0.46 changed only the owner decision package and this handoff. No source, tests, fixtures, schemas, workflow, CI permission, dependency, key, trust root, provider, database, VPS, runtime, T0/T1/T2, ledger, risk engine, or lifecycle operation changed.
- **G0.46: PACKAGE PREPARED — docs-only scope PASS. D01–D04 OPEN / NOT RATIFIED. S2 IMPLEMENTATION NOT AUTHORIZED.**
- Next: owner decides exact evidence classes requiring issuer authenticity and whether manual owner attestation is sufficient initially. Only after the dependent decisions close should a separate exact S2 implementation package be prepared for approval.

## G0.47 — D06 minimal issuer authority owner decision record (2026-11-11)

- Baseline before G0.47: `0e7a62ec565fff003edc5ab48956e6e7d2f282e4`; G0.46 handoff blob: `5ff090c0ad8cf7f690aa3a893c7171532f05d327`.
- Owner selections D01–D04 recorded: issuer authenticity minimal; single key topology; custody deferred; signature/canonicalization conditional.
- D01: SHA-256 over exact bytes by default; DSSE + Ed25519 + SHA-256 only considered for a specifically approved issuer-authenticity claim.
- D02: opaque bytes remain exact; UTF-8 JSON + RFC 8785 JCS only considered for a future structured signed statement.
- D03: single topology preference does not authorize an Issuer Key. Issuer attestation, Owner authorization and trust administration remain logically separate.
- D04: no real key generation/import/custody enrollment/signing/rotation/revocation/KMS/HSM/provider operation; paper-only posture retained.
- G0.47 D06 record: `docs/evidence/G0_47_D06_MINIMAL_ISSUER_AUTHORITY_OWNER_DECISION_RECORD_2026-11-11.md`; final blob `8a4bbb32fee04d01ef5a62f17a0d84bfc5262688`.
- Owner explicitly decided **manual Owner attestation only for the initial phase**. No autonomous Issuer Key, producer/service signature or autonomous issuer-authenticity mechanism is required or authorized initially.
- Manual attestation is bound to an exact, bounded claim/subject/version/digest or evidence references/scope/purpose. Its format and authentication mechanics remain open under D09. It proves only that the Owner made the bounded attestation; it does not prove source truth, inventory completeness, recovery success, readback correctness or custody continuity.
- Three initial evidence classes may be reviewed under manual Owner attestation: source/provenance; inventory closure/completeness; recovery/readback/custody event. Underlying evidence must still be independently resolvable/reconciled; missing or conflicting evidence fails closed. This is not an autonomous issuer allowlist.
- **D06 initial-phase policy: OWNER-DECIDED — MANUAL OWNER ATTESTATION ONLY; AUTONOMOUS ISSUER AUTHENTICITY DEFERRED.** D09 remains open for authentication and exact-scope authorization mechanics; D07, D08, D12–D14 remain open.
- G0.47 changed only the D06 decision record and handoff. No source, tests, fixtures, schemas, workflows, dependencies, keys, trust roots, providers, database, VPS, runtime, T0/T1/T2, ledgers, risk engine, or lifecycle operations changed.
- Tests/compile/CI: NOT RUN (docs-only). Runtime/VPS/database/provider/key operations: NOT PERFORMED.
- **G0.47: DOCUMENTATION PASS — D01–D04 owner selections recorded; D06 initial-phase manual Owner-attestation policy decided; D07–D09 and D12–D14 remain open; S2 IMPLEMENTATION NOT AUTHORIZED.**
- Next: prepare the next bounded owner decision record for D07/D08/D09 and remaining dependencies. No autonomous issuer key, cryptographic operation or S2 implementation is authorized.

## G0.48 — D07/D08/D09 inventory, freshness and Owner authentication decision package (2026-11-11)

- Baseline before G0.48: `eeaeec02b38d428cb535a5dffc7ded4dec3bfe85`; G0.47 D06 decision record blob: `8a4bbb32fee04d01ef5a62f17a0d84bfc5262688`.
- Added `docs/evidence/G0_48_D07_D08_D09_INVENTORY_FRESHNESS_OWNER_AUTH_DECISION_PACKAGE_2026-11-11.md` in package commit `b08fcfc9cbfd90748a4f9c0399d357e42026cac7`.
- G0.48 is documentation-only. It prepares owner options for D07 inventory closure/omission detection, D08 freshness/expiry/revocation/replay/rollback, and D09 manual Owner authentication/exact-scope authorization.
- D07 recommendation: declared scope, independently defined expected population, deterministic enumeration, expected/observed reconciliation; unresolved/inaccessible/ambiguous items block completeness. Explicitly partial inventories may be labelled partial, not complete.
- D08 recommendation: initial posture makes no global latestness claim; use integrity-only or named-snapshot claims. Freshness-dependent actions fail closed when freshness is unknown. No TTL, trusted time source, anchor technology, revocation transport or replay window is ratified.
- D09 recommendation: consider platform-attributed manual Owner action only if Owner accepts its assurance limits; explicitly do not label it cryptographically signed. Separate evidence-review attestation from privileged-action authorization and bind any authorization to exact target/action/scope/policy version/evidence references. Detached signatures remain deferred.
- D07/D08/D09 are all OPEN / NOT RATIFIED. The package recommendations are not decisions. No numeric limits or implementation authority are granted.
- D06 remains owner-decided: manual Owner attestation only in the initial phase; no autonomous Issuer Key or producer/service signature.
- G0.48 changed only the new decision package and this handoff. No source, tests, fixtures, schemas, workflows, dependencies, keys, trust roots, providers, database, VPS, runtime, T0/T1/T2, ledgers, risk engine or lifecycle operations changed.
- Tests/compile/CI: NOT RUN (docs-only). Runtime/VPS/database/provider/key operations: NOT PERFORMED.
- **G0.48: PACKAGE PREPARED — D07/D08/D09 READY FOR OWNER DECISION; ALL THREE OPEN / NOT RATIFIED; S2 IMPLEMENTATION NOT AUTHORIZED.**
- Next: Owner selects or amends D07, D08 and D09. No automatic progression to S2.


## G0.49 — D07/D08/D09 Owner decision record (2026-11-11)

- Owner explicitly selected D07-A, D08-A and D09-A from G0.48. Decision record: `docs/evidence/G0_49_D07_D08_D09_OWNER_DECISION_RECORD_2026-11-11.md`.
- D07-A is OWNER-DECIDED: complete inventory requires declared scope, independently defined expected population, deterministic complete enumeration and expected/observed reconciliation. Any unresolved/inaccessible/ambiguous item or unexplained enumeration defect blocks COMPLETE. Explicitly partial inventories may be labelled PARTIAL only; no completeness claim.
- D08-A is OWNER-DECIDED: initial phase permits `INTEGRITY_ONLY` or `AS_OF_SNAPSHOT`; no global latestness/freshness claim. Freshness-dependent decisions fail closed when freshness is unknown. TTLs, trusted time source/anchor, expiry durations, revocation transport, replay window and rollback policy remain OPEN / NOT RATIFIED.
- D09-A is OWNER-DECIDED for initial phase: authenticated Owner-controlled GitHub action/commit may be labelled `PLATFORM_ATTRIBUTED_OWNER_ACTION`, not a cryptographic signature. Commit metadata alone does not prove uncompromised identity or factual truth. Review attestation, exact-scope privileged authorization and trust administration remain separate.
- D06 remains manual Owner attestation only; autonomous issuer authenticity and cryptographic key operations remain deferred.
- G0.49 changed only the D07/D08/D09 decision record and this handoff. No source, tests, fixtures, schemas, workflows, dependencies, keys, trust roots, providers, database, VPS, runtime, T0/T1/T2, ledgers, risk engine or lifecycle operations changed.
- Tests/compile/CI: NOT RUN (docs-only). Runtime/VPS/database/provider/key operations: NOT PERFORMED.
- **G0.49: DOCUMENTATION PASS — D07-A/D08-A/D09-A OWNER-DECIDED FOR INITIAL PHASE; S2 IMPLEMENTATION NOT AUTHORIZED.**
- Next: prepare bounded decisions for remaining open dependencies D12–D14. No automatic S2 progression.


## G0.50 — D12/D13/D14 audit custody, verified-facts binding and stage-gate owner decision package (2026-11-11)

- Baseline before G0.50: `2b4e59a59faebb34b0d62a658d08fa95ece68ffa`; G0.49 decision record remains controlling for D07-A/D08-A/D09-A.
- Added `docs/evidence/G0_50_D12_D13_D14_AUDIT_VERIFIED_FACTS_STAGE_GATE_OWNER_DECISION_PACKAGE_2026-11-11.md` in package commit `c33594bb9c47753be2a57bb5e935b0b0e76ae8ad`.
- G0.50 is documentation-only. It prepares owner options for D12 audit custody/retention/redaction/readback, D13 verified-facts exact binding/process boundary, and D14 per-increment review/implementation/release gates.
- D12 recommendation: append-only logical decision history in the existing GitHub repository; exact artifact payload readback/hash before custody claims; explicitly GitHub-domain only; no automatic deletion, silent rewrite or unsupported recoverability claim.
- D13 recommendation: immutable exact-subject/evidence/policy/evaluation-bound envelope; verifier-only construction; no caller-controlled trusted boolean; explicit claim dimensions; no execution authority.
- D14 recommendation: strict per-increment Owner approval; every executable stage and real-source/runtime operation separately approved; CI PASS never substitutes for Owner authorization or production acceptance.
- D12/D13/D14 remain OPEN / NOT RATIFIED. Recommendations are not decisions. No retention duration, backup cadence, serialization/IPC mechanism, production trust mechanism or implementation scope is ratified.
- G0.50 changed only the new decision package and this handoff. No source, tests, fixtures, schemas, workflows, dependencies, keys, trust roots, providers, database, VPS, runtime, T0/T1/T2, ledgers, risk engine or lifecycle operations changed.
- Tests/compile/CI: NOT RUN (docs-only). Runtime/VPS/database/provider/key operations: NOT PERFORMED.
- **G0.50: PACKAGE PREPARED — D12/D13/D14 READY FOR OWNER DECISION; ALL THREE OPEN / NOT RATIFIED; S2 IMPLEMENTATION NOT AUTHORIZED.**
- Next: Owner selects or amends D12, D13 and D14. No automatic S2 progression.


## G0.51 — D12/D13/D14 Owner decision record (2026-11-11)

- Owner explicitly agreed to all three option-A recommendations in G0.50. Decision record: `docs/evidence/G0_51_D12_D13_D14_OWNER_DECISION_RECORD_2026-11-11.md`.
- D12-A OWNER-DECIDED: append-only logical audit history in the existing approved GitHub repository/commit history; GitHub-domain custody only, not independent backup/DR/WORM. Exact artifact payload must be retrieved and independently digest-checked before making custody/readability claims. Redaction/correction/supersession is a new linked event, not silent historical rewrite. No retention duration, automated expiry/deletion, second custody domain or backup schedule approved.
- D13-A OWNER-DECIDED as the required future target: immutable/versioned verifier-created envelope bound to exact subject, source, evidence digests, claim/scope, policy, verifier build/contract and evaluation/evidence set. No caller-created generic trust boolean; consumers reject mismatches/unknown states; claim dimensions remain separate; no execution authority. D13-B is not selected as a substitute. Any single-process synthetic experiment would require its own exact approval and would not satisfy D13-A.
- D14-A OWNER-DECIDED: strict per-increment Owner approval. Each executable stage, S2 implementation step, workflow/permission change, real evidence adapter, provider/runtime operation and lifecycle/destructive action requires separate exact-scope approval. CI PASS never substitutes for Owner authorization or acceptance. No automatic stage transition and no standing authorization granted here.
- D06/D09 manual platform-attributed Owner action remains; no cryptographic signature or autonomous issuer key is introduced. D07/D08 remain controlling. S1 parser remains synthetic-only.
- G0.51 changed only the D12/D13/D14 decision record and this handoff. No source, tests, fixtures, schemas, workflows, dependencies, keys, trust roots, providers, database, VPS, runtime, T0/T1/T2, ledgers, risk engine or lifecycle operation changed.
- Tests/compile/CI: NOT RUN (docs-only). Runtime/VPS/database/provider/key operations: NOT PERFORMED.
- **G0.51: DOCUMENTATION PASS — D12-A/D13-A/D14-A OWNER-DECIDED; S2 IMPLEMENTATION AND OPERATIONAL/DESTRUCTIVE ACTIONS NOT AUTHORIZED.**
- Next: reconcile remaining open dependencies and prepare a separate exact-scope S2 readiness package only after closure. No automatic implementation.


## G0.52 — D01–D14 closure audit and S2 readiness (2026-11-11)

- Baseline HEAD: `7dd321f5960291873dd8f374e6dd62c6a988c7b8`. Read controlling handoff blob `b6af9a90f3b4202a1ee02beb5f7e9d48096cb202` before work.
- Added `docs/evidence/G0_52_D01_D14_S2_READINESS_AUDIT_RECORD_2026-11-11.md` in documentation-only scope; report blob `9e716bd4903892ec338c37b6c59987204d42f6b4`.
- Reconciled D01–D14 against G0.21/G0.22/G0.26/G0.27/G0.28/G0.31/G0.44/G0.45/G0.47/G0.49/G0.50/G0.51.
- D01–D04: conditional/minimal selections recorded, but exact S2 signature/canonicalization/test-key profile remains unresolved; no key or crypto operation authorized.
- D05/D10/D11: ratified only for S1 Synthetic Contract Fixture v1/parser boundary. They do not establish an S2 verifier envelope or verifier-specific resource limits.
- D06–D09: initial-phase policies owner-decided (manual Owner attestation; independent inventory reconciliation; no freshness without trusted anchor; GitHub platform attribution not crypto identity). Real-source authenticity, live inventory/freshness and privileged Owner authorization are not established.
- D12–D14: option-A policies owner-decided in G0.51. They are policy decisions, not technical implementation or stage authorization.
- G0.21 trust-boundary findings remain material; G0.45 proves only S1 synthetic parser contract (22 focused tests and compile PASS), not production evidence verification.
- **G0.52 verdict: AUDIT PASS; S2-SYNTHETIC-VERIFIER BLOCKED / NOT READY.** Required next owner package: exact test-only crypto/profile choice (or explicit exclusion of issuer-authenticity tests), S2 schema/byte contract, test-only key lifecycle, D13-A verifier-created result binding, S2-specific resource limits and exact D14 gate.
- This increment changed only the audit report and handoff. No source, tests, fixtures, schemas, workflows, dependencies, keys, trust roots, providers, database, VPS, runtime, T0/T1/T2, ledgers, risk engine or lifecycle operation changed.
- Tests/compile/CI: NOT RUN (docs-only). Runtime/VPS/database/provider/key operations: NOT PERFORMED. Independent reviewer sign-off remains waived as a mandatory gate; no independent assurance claim.
- No S2 implementation or operational/destructive action is authorized.


## G0.53 — S2 Synthetic Verifier Contract Owner Decision Package (2026-11-11)

- Baseline HEAD: `d9baed38bad73c0d39c88f233b0f254a669a07a2`; controlling handoff blob read before work: `6e029acbcd8f833b224c2bb981b332eefdaa7c5f`.
- Added `docs/evidence/G0_53_S2_SYNTHETIC_VERIFIER_CONTRACT_OWNER_DECISION_PACKAGE_2026-11-11.md`; package commit `1142423eae2a9f931b42fc3c706d546e411c6d2e`; report blob `8c9f7980d14a13b16b2f9f79f4cc2bc176253f15`.
- G0.53 proposes a narrow first S2 scope: SHA-256 exact-byte integrity only; explicitly exclude issuer-signature verification; keep evidence bytes opaque; define a new S2-only versioned verifier envelope separate from S1 Fixture v1; no keys/trust roots/providers; verifier-created immutable D13-A result binding; D11 measurement-first with numeric ceilings still OPEN; separate D14 approval required before any implementation.
- Alternative signature-testing Option B is documented but requires separate exact decisions for signature profile, schema/canonicalization, test-only keys and resource limits. No option is Owner-ratified yet.
- Owner decisions requested: D01-S2, D02/D05-S2, D03/D04-S2, D13-S2, D11-S2 and D14-S2.
- This increment changes only the G0.53 decision package and this handoff. No source, tests, fixtures, schemas, workflows, dependencies, keys, trust roots, providers, database, VPS, runtime, T0/T1/T2, ledgers, risk engine or lifecycle operation changed.
- Tests/compile/CI: NOT RUN (docs-only). Runtime/VPS/database/provider/key operations: NOT PERFORMED. Independent reviewer sign-off remains waived as a mandatory gate; no independent assurance claim.
- **G0.53: PACKAGE PREPARED — READY FOR OWNER DECISION; D01-S2/D02-S2/D03-S2/D04-S2/D13-S2/D11-S2/D14-S2 NOT RATIFIED; S2 IMPLEMENTATION NOT AUTHORIZED.**
- Next: Owner selects/amends the exact S2 contract. Even if ratified, a separate D14 implementation approval is required.

## G0.4 — Main-only delta and topology refresh (2026-11-11)

Owner approved this documentation-only increment. Detailed report: `docs/evidence/G0_4_MAIN_ONLY_DELTA_AND_TOPOLOGY_REFRESH_2026-11-11.md`, report commit `5e36eee3c23fa6e25fc2c5af530f36cfaa5bc6f5`, report blob `33e875e933ce25814625a8ef350feb4f1ecf6a65`.

- Exact active-branch baseline HEAD: `ba8569e704fc256b7743abf0163116878e06e89c`.
- Exact `main` baseline HEAD: `b9b938b4c78f143ca63330d047a8a799ef450a13`.
- Merge base: `f5b74affb8777953fa66d241784965fbb0e577ba`.
- Compare orientation: `base=main`, `head=feature/t0-centralized-data-feeder-p1-20261101`. Result: **DIVERGED; active branch ahead 3,215 / behind 82**. Integration remains BLOCKED.
- G0.3 historical checkpoint had 76 main-only commits. From its exact `main` checkpoint `063f7a2eacd724f965a9723d0ae66cf95418c0fb` to current `main` HEAD, GitHub compare returned exactly six additional commits. All six were classified in G0.4: three SSH Preflight retirement implementation removals, retirement evidence, handoff update, and G0.52 D01–D14 audit.
- Active-branch exact readback: SSH Preflight script and contract-test paths absent; workflow blob `eda43deee000f138690b1a15c8db46dd2fe97d99` has no Preflight references; retirement evidence is present. This is source/path readback only, not workflow/runtime/VPS verification.
- Open PR snapshot: 39 open Draft PRs. Open issue snapshot: #138 (T1 P1.42) and #91 (Dashboard). PR #139 remains CLOSED / NOT MERGED; PR #144 is MERGED into `main`.
- L4 Automation Plan/Register report bounded 40-file repository-source inventory and reference reconciliation PARTIAL PASS. Aggregate L4-Minimum remains BLOCKED / NOT VERIFIED. G0.52 disposition remains audit PASS, S2 BLOCKED / NOT READY; no implementation authorized.
- Roadmap evidence-index correction: the exact G0.52 path is `docs/evidence/G0_52_D01_D14_S2_READINESS_AUDIT_RECORD_2026-11-11.md`.
- Tests/compile/CI: NOT RUN (documentation-only). No workflow run or artifact generated by G0.4. No source, workflow, test, T0/T1/T2, ledger, risk engine, database, VPS/runtime, provider/key, lifecycle or trading changes.
- **G0.4: DOCUMENTATION RECONCILIATION PASS; INTEGRATION BLOCKED; L4 BLOCKED / NOT VERIFIED; S2 NOT AUTHORIZED.**

Next: preserve the active branch and divergence. Any integration candidate requires its own exact source/base SHA review, dependency mapping, tests/evidence and Owner approval. Do not merge, rebase, cherry-pick, reset, force-push, delete branches, close PRs, activate T1, run S2, provision VPS, alter data or enable live execution.

## AI calibrated confidence and provenance — bounded implementation increment (2026-11-11)

Owner approved autonomous work through completion of calibrated-confidence/provenance handling, subject to existing project invariants and unresolved trust/policy gates.

- Active branch unchanged: `feature/t0-centralized-data-feeder-p1-20261101`.
- Latest branch HEAD: `fd75159719c99e8eef1ee72d22f74d724b1990e8`.
- Source implementation commit: `fedf4ef9e144a5bba21a53369ff876d00580e964`; `pipeline/decision.py` blob `5a5cf05c8de2cb1b00eb411c31380928cf80d862`.
- Test/fixture commits: `8dffe7e6ceee999381743116ae3c3cf77580a93c`, `072b9148b4ef35f31e0dfad37e6c1055454b4e99`, `9d9e82645d63aeb7c69e2e7e3edfefb6715f7c28`, `6c1bbb6ceddcbeaa1ce950d31bf8b537761a2ddc`, `d43c71b69bde702fb94374370951e843646a21f1`, and `fd75159719c99e8eef1ee72d22f74d724b1990e8`.
- Test blobs: `pipeline/test_decision.py` = `8417d6c53c0263836e906dca572032eaa008f6ce`; `pipeline/test_ai_strategy_contract_red.py` = `740a975f8a3b8d3e99e7bcb2d7a8bbc4eb56c915`.
- The decision boundary now requires explicit admission context; missing context/policy returns WAIT. It validates finite calibrated confidence, required explicit C_min, sample/period/age thresholds, calibration digest formats, model/strategy/training-dataset compatibility, label/horizon compatibility, timestamp order, calibration-window maturity before the prediction candle and freshness. Accepted confidence and calibration/policy provenance are bound into the paper intent.
- No numeric C_min or production sample/period/age values were selected. Test values remain fixtures only. The normal API path currently supplies no trusted calibration admission provider and therefore fails closed to WAIT.
- Existing CI run [43063510163](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43063510163), job `130672173869`, exact source SHA `6c1bbb6ceddcbeaa1ce950d31bf8b537761a2ddc`: compile PASS; 51 tests executed, 13 failures and 6 errors. Calibration-specific cases for policy validation, confidence bounds, provenance compatibility, timestamp/horizon checks, digest shape, stale/insufficient calibration, intent binding and API fail-closed behavior passed. The missing-confidence test had a fixture-coupling false positive and was corrected in `d43c71b69bde702fb94374370951e843646a21f1`; the inclusive C_min boundary test was added later. These later test changes have NOT been re-run.
- The remaining failures/errors in that RED workflow concern out-of-scope leverage mapping, account-equity/risk readiness, instrument filters, Kill Switch and AI ledger wiring; this increment did not claim those gates.
- Workflow updated in commit `da753989eacd77459500c695fc04bf905c1faeb7` to run a dedicated calibration/confidence subset plus `pipeline.test_decision`. Workflow blob: `d046512de4a74e2ae7ad48ec432d7b207e65f66b`. No check runs were present for `da753989eacd77459500c695fc04bf905c1faeb7` or latest HEAD `fd75159719c99e8eef1ee72d22f74d724b1990e8`; latest focused tests and decision regression are therefore NOT VERIFIED.
- RED evidence artifact from run `43063510163`: ID `13873544695`, name `ai-strategy-contract-red-6c1bbb6ceddcbeaa1ce950d31bf8b537761a2ddc`, upload ZIP SHA-256 `ebf0e7f6c85dd43a01e7d3f888f4e637cbaa7e1b04bf1aab82050eb4aa047719`. Payload was not independently downloaded/re-hashed.
- **Critical trust boundary remains BLOCKED:** no trusted calibration registry/provider exists. The validator's digest-format and provenance checks do not prove registry membership, exact artifact-byte digest, publisher authenticity, approved/revoked status or OOS dataset lineage. The API therefore remains fail-closed; test fixtures are not trusted evidence.
- Existing owner-approved direction is GitHub append-only Registry + offline Ed25519 signing. Exact manifest schema/canonicalization, pinned public-key/trust-root profile, revocation/rollback semantics, calibration method/OOS evidence provider and numerical thresholds remain unresolved. No registry, key, calibration artifact, model/training job, dependency, DB/schema, migration, runtime or exchange operation was created.
- **Disposition:** structural confidence/provenance validator IMPLEMENTED; focused latest verification NOT VERIFIED; trusted calibration provenance provider BLOCKED. No AI production intent can pass the current API path. Core, T0, Dual Ledger schema and Shared Risk Engine were not changed.
- **Next permitted work:** prepare a compact exact registry manifest/verifier contract using the already approved GitHub append-only + offline Ed25519 direction, then stop for the remaining owner choices that cannot be inferred (especially trust-root/key profile and OOS/calibration evidence source). Do not select C_min or claim trusted calibration until those are resolved.

## AI calibration verifier v1 — RFC 8785 + Ed25519 (2026-11-11)

Owner approved RFC 8785 JCS canonicalization, Ed25519 detached-signature verification and an independently pinned public-key configuration. Work remained on the active branch; no branch/PR divergence was introduced.

- Active branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Latest source HEAD before this handoff update: `9dca3380c9a94fd36dc871729ba52b54c46698ee`.
- Verifier implementation: `pipeline/calibration_registry.py`, blob `cf6571a3bc7037eda6b3a9cf778204c0a7ae6fc6`, introduced in commit `e0bf825a957cd9b4e8ef9032fe816715ba410fa8`.
- Verifier tests: `pipeline/test_ai_calibration_registry.py`, blob `6127e6817e5625183431c1cf5a2913980575ec1a`, latest test update commit `ee5a649cdd5b24adc25ff2083b6dee820f5717af`.
- Dependencies: `requirements-web.txt` blob `1ee5316a56713357a8008da7e5423af69e2e9b9b`; `requirements.txt` blob `f5c242bdac51eba200b19233e08e7d4b22f598c4`. Added `cryptography>=42.0.0,<47` and `rfc8785>=0.1.4,<0.2`.
- Workflow `.github/workflows/ai-strategy-contract-red.yml` blob `d976d2ea2c7927e5b5183d7f63fef70e41db7f07`; it compiles and runs the registry tests in the isolated paper-only CI.
- Frozen contract: `docs/architecture/AI_CALIBRATION_REGISTRY_MANIFEST_CONTRACT.md`, blob `5ab39f31933a0626d674abb1530a3509c56ef29a`. Exact 37-field manifest v1, envelope v1, JCS bytes, domain-separated signature statement and external trust-config field set are frozen for read-only verification only.
- Evidence report updated: `docs/evidence/AI_CALIBRATION_MANIFEST_AND_KEY_LIFECYCLE_DESIGN_2026-11-11.md`, blob `119e4a9863490fa2ee3fbba24582211075927560`.

Exact CI evidence:
- Workflow run `43065112950`, job `130677863812`, source SHA `ee5a649cdd5b24adc25ff2083b6dee820f5717af`: compile PASS; calibrated confidence/provenance 13 tests PASS; decision regression 15 tests PASS; registry verifier 12 tests PASS.
- Same run's full AI/dual-strategy contract: 52 tests, 12 failures and 6 errors. Outstanding failures/errors are leverage mapping, account-equity readiness/sizing, instrument lot/tick/minimum rules, Kill Switch and API/AI-ledger routing. Full AI contract remains NOT PASS.
- Artifact ID `13875776318`, name `ai-strategy-contract-red-ee5a649cdd5b24adc25ff2083b6dee820f5717af`, upload ZIP SHA-256 `02491d09b1aa41e24b4140999030aa4e977819677f09ab25539408da79c914e1`.
- Dual Ledger workflow run `43065112813`, job `130677863091`, same source SHA `ee5a649cdd5b24adc25ff2083b6dee820f5717af`: 238 tests, 3 failures and 170 errors; regression suite BLOCKED. This was not used as proof of a verifier regression or PASS.
- Freqtrade 2026.9 smoke run `43065113040` was queued/pending when inspected; no success claim is made.

Verifier security boundary:
- Requires exact canonical UTF-8 JCS bytes, no BOM/duplicate keys/JSON numbers/unknown fields, exact artifact SHA-256 and byte length, strict Ed25519 envelope, and independently pinned raw public key fingerprint plus key ID, signer role, publisher ID, namespace and allowed record type.
- The only success result is `SIGNATURE_VERIFIED_ONLY`. It does not establish predecessor/event-chain integrity, approval/active/revocation state, trusted time, evaluation-record content, dataset lineage, OOS quality, or per-inference confidence computed from the transform.
- Test-only RFC 8032 private seed is confined to unit-test fixture; no production key, key ceremony, trust-root enrollment or signature publication was performed.
- `pipeline/api.py::decide` remains without a trusted calibration provider and the production decision path fails closed to WAIT. No production registry provider, manifest/artifact, model/calibrator training, numerical threshold, DB/schema migration, runtime activation or live execution was introduced.

**Disposition:** RFC8785/Ed25519 verifier v1 and focused verifier tests PASS. Overall Calibrated confidence/provenance completion remains BLOCKED / NOT VERIFIED. Outstanding material gates: externally provisioned real public-key pin and key authorization lifecycle; immutable approved/active/revoked registry event chain; evaluation-record byte verification and dataset lineage/horizon embargo; approved calibration transform/evaluation protocol; per-inference confidence generated by applying the exact transform and cryptographically/structurally bound to the manifest; explicit numerical policy values (never infer C_min/sample/period/age defaults). Keep API fail-closed until those gates are closed.

### AI calibration verifier v1 hardening — exact follow-up (2026-11-11)

- Implementation `pipeline/calibration_registry.py` blob `6008726c53d0b67c1ffc2471df70be83019d3f65`; test `pipeline/test_ai_calibration_registry.py` blob `5c0e734af0434c6600c4c9fc87306f6abaed842d`.
- Added bounded uint64 canonical decimal parsing; GENESIS is permitted only for sequence 1; subsequent sequences require a predecessor digest; calibration start must not precede training cutoff plus forecast-horizon embargo; artifact creation must not predate calibration end.
- Frozen manifest contract updated: `docs/architecture/AI_CALIBRATION_REGISTRY_MANIFEST_CONTRACT.md` blob `5ab39f31933a0626d674abb1530a3509c56ef29a`.
- Evidence report updated: `docs/evidence/AI_CALIBRATION_MANIFEST_AND_KEY_LIFECYCLE_DESIGN_2026-11-11.md` blob `3a2d22c1d167b01b913d5c757520006681c9fc55`.
- Exact CI run `43065750329`, job `130680105605`, source SHA `cbfef9b48dfd996f7788e80f8f62f9c92a51628d`: compile PASS; calibrated confidence/provenance 13 PASS; decision regression 15 PASS; registry verifier 14 PASS. Full AI/dual-strategy RED still 52 tests, 12 failures, 6 errors (leverage/equity/instrument/Kill Switch/ledger gates remain).
- Artifact ID `13875077587`, name `ai-strategy-contract-red-cbfef9b48dfd996f7788e80f8f62f9c92a51628d`, upload ZIP SHA-256 `1a82bd0eeb050956adecb54281723650e2905a714996d256d8d8e05a6238f73c`.
- These additional checks are structural only. The verifier still does not validate the full predecessor chain, owner approval/revocation state, trusted time, evaluation evidence bytes/metrics, dataset lineage or OOS statistical quality, and it does not calculate per-inference confidence from the artifact.
- **Disposition unchanged:** verifier code and focused tests PASS; overall calibrated confidence/provenance completion BLOCKED / NOT VERIFIED; API remains fail-closed with no trusted provider. No production key/pin, manifest/artifact, calibration training, database migration, runtime activation or live execution.

## AI calibration transform and verified-evidence decision gate (2026-11-11)

Owner-approved autonomous implementation continued on the existing branch. No branch creation, PR split, merge/rebase or destructive operation.

- Source HEAD before this handoff append: `3a7eb76ab1762e7f68e911944d751cf0f6723de0`.
- `pipeline/calibration_registry.py` blob `2a077783878a5bbfc67afb3ba5a8df8241346fe9`: strict JCS/Ed25519 manifest and artifact verifier, monotone score/probability transform validation, exact transform/manifest compatibility, and per-inference confidence calculation by piecewise-linear interpolation with no extrapolation. Timestamp conversion uses integer UTC arithmetic.
- `pipeline/decision.py` blob `8720d8ab988529b1545a27aa0792beca9e6a84aa`: consumes server-constructed calibration evidence rather than prediction-report confidence. It requires `SIGNATURE_VERIFIED_ONLY`, registry `ACTIVE`, trusted-time `VERIFIED`, and OOS-evidence `VERIFIED` before confidence/policy/provenance checks. Missing any state => WAIT.
- Tests: `pipeline/test_ai_calibration_registry.py` blob `fe3c016a88149a198afac594dbe716303abcffca`; `pipeline/test_ai_strategy_contract_red.py` blob `3592d7aa9edeb4eac039153f1e5c19a9bf3b5fcf`; `pipeline/test_decision.py` blob `6781f26d66635f56662a627bdd3b4a63f26c1f28`.
- Frozen contract updated: `docs/architecture/AI_CALIBRATION_REGISTRY_MANIFEST_CONTRACT.md` blob `955a7cc4addc7b282c3b88b7753a1dd1b0ce680e`.
- Evidence report: `docs/evidence/AI_CALIBRATION_MANIFEST_AND_KEY_LIFECYCLE_DESIGN_2026-11-11.md` blob `0fb037a9d912e8e8807cad605ab3e4c8fa365c36`.

Exact CI:
- Workflow run `43066900003`, job `130684294885`, source SHA `f3a873c38f9ad917a6566faa5fa52e8dc013e0fd`: compile PASS; calibrated confidence/provenance 14 PASS; decision regression 15 PASS; registry verifier/transform 18 PASS.
- Full AI/dual-strategy RED: 54 tests, 12 failures, 6 errors. Remaining failures/errors are leverage mapping, account equity/sizing, instrument lot/tick/minimum rules, Kill Switch and AI ledger/API routing; no full-system PASS claim.
- Artifact ID `13875183120`, name `ai-strategy-contract-red-f3a873c38f9ad917a6566faa5fa52e8dc013e0fd`, ZIP SHA-256 `0dee6d84732a7be668e162ad782570014eb33f66c353105d36418b8446321054`.

Critical limits:
- The transform evaluator can derive confidence from a signed exact artifact, but no production calibration transform/artifact or OOS dataset exists. No training was performed.
- The verifier returns only signature/integrity status. No production key/public-key pin was provisioned; no signed registry event-chain, Owner promotion/revocation provider, trusted-time anchor, or evaluation/OOS lineage verifier exists.
- The decision boundary now explicitly requires registry ACTIVE, trusted time and OOS verification statuses. Test fixtures exercise these states only; no production provider can assert them. `pipeline/api.py::decide` still supplies no admission context, so production AI remains fail-closed to WAIT.
- No C_min, sample-count, calibration-duration or max-age numeric threshold was selected. No registry/artifact/key, training job, DB migration, runtime activation, VPS operation or live execution occurred.

**Disposition:** RFC8785/Ed25519 verifier, transform evaluator and fail-closed decision evidence contract IMPLEMENTED; focused CI PASS. Overall Calibrated confidence/provenance completion BLOCKED / NOT VERIFIED until an authorized real trust pin/key lifecycle, append-only active/revocation chain, trusted time, OOS evaluation/dataset lineage and real calibrated artifact are available. Do not weaken the new ACTIVE/time/OOS gates or enable AI execution to bypass missing evidence.

## AI calibration verifier BOM rejection hardening — 2026-11-12

- Scope: correct UTF-8 BOM detection for exact manifest bytes and calibration-transform artifact bytes; no schema, policy, trust, provider, registry-state or runtime changes.
- Code review found both guards compared against the six-character text sequence `\\ufeff` instead of the decoded Unicode BOM character. This meant BOM-prefixed manifest/transform bytes could fall through to generic JSON parse errors instead of the explicit fail-closed BOM rejection.
- Added regression tests in `pipeline/test_ai_calibration_registry.py` for actual UTF-8 BOM bytes in both inputs. Test file commit: `7fd55aad514675888877307a05bfafef6844b3cc`; blob `e3e07cde15f3e4bc00758ff9ff94c7288c4ee18c`.
- Corrected both guards in `pipeline/calibration_registry.py`. Implementation commit: `9be4c7061db2eef3b521e966bee89296b5de45f9`; blob `084bae77874bfbb4aca4974511e4e2f5acd68284`.
- Intermediate test-authoring commit `23f77ea0dcf2fbb99f10f540644cea346deb9dd1` was superseded by the corrected test bytes in `7fd55aad514675888877307a05bfafef6844b3cc`.
- Verification: source diff confirms both guards now check the actual U+FEFF character and tests construct bytes from hex `efbbbf`. GitHub combined status for implementation SHA `9be4c7061db2eef3b521e966bee89296b5de45f9` returned no status checks; no workflow run/job log was available for the new commits. RED and GREEN execution are therefore **NOT VERIFIED**; do not claim these tests PASS until CI runs against the exact source SHA.
- No independent runtime, local checkout test, artifact, model, calibration data, key, registry event, provider, database, T0/T1/T2, VPS, trading or destructive operation was performed.
- Review: narrow correctness fix; existing verifier boundaries and failure semantics preserved. No new dependency or public API.
- **Disposition: implementation committed; verification NOT VERIFIED.** Next: obtain a GitHub Actions run against exact SHA `9be4c7061db2eef3b521e966bee89296b5de45f9` and inspect the focused verifier job before promoting this increment to PASS.

## Calibration verifier path-separator hardening — 2026-11-12

- Scope: enforce the frozen artifact-path rule by rejecting any backslash character in artifact_path; no manifest schema, trust, signature, registry, admission or runtime semantics changed.
- TDD regression test added for a single-backslash path containing dot-dot-like segments. Test commit: 47adb6f4d952167142ef2646e57267dbb4619f0b, superseded test correction commit: dbe492580d4d13e492394ffc1a23b0d4c7119519; latest test blob: a5c36c7b32fc5bee16ca2c619c96f9270d22b8ff.
- Fix: pipeline/calibration_registry.py now checks for any single backslash. Code commit: 2ccff7a55c8572125a9e8c50fd575f97e7082f70; blob: 691ef04d69b5aad6362fc9f2024ca300b39150e1.
- Exact GitHub Actions workflow run: 43069684925, job 130693994891, source SHA 2ccff7a55c8572125a9e8c50fd575f97e7082f70; at handoff update time the run was QUEUED, so test result is NOT VERIFIED. No local test execution was available in this session. Do not claim RED/GREEN or PASS until the focused registry test log is inspected.
- Scope review: the frozen v1 contract restricts artifact paths to the registry artifact subtree; rejecting backslashes removes cross-platform path interpretation ambiguity while retaining valid POSIX registry paths.
- No production key, registry event chain, trusted-time/OOS provider, calibration data/artifact, model training, database, T0/T1/T2, VPS, runtime, or live trading change.
- **Disposition: code committed; CI QUEUED / NOT VERIFIED.** Next: inspect run 43069684925; then continue only verifier-v1-safe correctness fixes. Active/revocation chain, trusted-time, OOS evidence schema/lineage and numerical policy remain blocked by their separate approval/evidence gates.

### Exact CI result — path-separator hardening

- Run 43069684925, job 130693994891, exact source SHA 2ccff7a55c8572125a9e8c50fd575f97e7082f70, completed FAILURE.
- Compile step PASS.
- Calibrated confidence/provenance: 14/14 PASS.
- Decision regression: 15/15 PASS.
- Calibration registry verifier/transform: 21/21 PASS, including single-backslash rejection and both UTF-8 BOM rejection tests.
- Full AI/dual-strategy RED remains 54 tests, 12 failures, 6 errors in unrelated leverage mapping, equity/sizing, instrument constraints, Kill Switch and AI ledger/API scope. This run is not a full-system PASS.
- Artifact: ID 13876519708; name ai-strategy-contract-red-2ccff7a55c8572125a9e8c50fd575f97e7082f70; ZIP SHA-256 8aace1904bb0c6ae9667f329876f4b7af793e12f8aa175a6274baa2768d3930a.
- Focused verifier disposition: PASS at exact SHA above. Overall calibrated confidence/provenance remains BLOCKED / NOT VERIFIED due absent production trust pin/key lifecycle, active/revocation chain, trusted time, evaluation bytes/dataset lineage/OOS evidence, real calibration artifact and Owner-approved numeric policy.


## OOS Evaluation Evidence v1 design proposal — 2026-11-12

- Owner explicitly approved the bounded design step. Added `docs/architecture/AI_CALIBRATION_OOS_EVALUATION_EVIDENCE_V1_PROPOSAL.md` in commit `1528bb944a5710939cf86cba51f97cc75579891d`.
- Scope is proposal only: immutable OOS evaluation record bound by existing manifest `evaluation_record_id` / `evaluation_record_digest`; proposed identity, dataset partition, temporal embargo, metric/uncertainty, evaluator reproducibility and provider-result requirements; deterministic contract-test matrix for a later frozen schema.
- Frozen manifest v1 (37 fields), signature envelope v1, transform v1 and decision gate were not modified. No production provider, schema implementation, executable tests, real evaluation data, model training, calibration artifact, key, trust root, registry event, S2, VPS/runtime, T0/T1/T2 or live trading operation occurred.
- Proposal explicitly leaves unresolved the exact field/metric schema, authoritative dataset lineage, split protocol, detached evaluation signature choice, statistical thresholds, trusted-time source and resource limits. These require Owner decisions before schema freeze.
- Verification: source/document commit recorded; no CI workflow was run for this documentation-only proposal. Executable contract tests are NOT RUN because schema is not frozen.
- **Disposition: DESIGN PROPOSAL RECORDED; NOT FROZEN; NOT IMPLEMENTED.** Next: Owner review of the open decisions in section 9 of the proposal. Do not implement provider/schema or assert OOS VERIFIED before those decisions and a separate implementation gate.


## OOS Evaluation Evidence v1 structural contract freeze — 2026-11-12

- Owner approved using the existing OOS Evaluation Evidence v1 proposal as the baseline for structural freeze.
- Frozen the exact top-level field set, metric-set shape, uncertainty shape, digest/canonical-byte rules, data-partition invariants and provider verification boundary in `docs/architecture/AI_CALIBRATION_OOS_EVALUATION_EVIDENCE_V1_PROPOSAL.md`, section “Owner-approved OOS Evaluation Evidence v1 — structural contract freeze”.
- Contract document commit: `70d5260691f16d986cebd31d09da3d133213fa17`; document blob: `69025272ff13d1a4ae5264bc701fd33f07845d6f`.
- Explicitly not frozen: authoritative dataset-lineage source/method, concrete split protocol algorithm, approved metric catalogue, statistical thresholds/minimum sample count/C_min interaction, trusted-time source/freshness semantics, extra detached-signature requirement and resource limits. These require separate Owner decisions; no assumptions were silently selected.
- Frozen manifest v1, signature envelope v1, transform v1 and decision gate unchanged. No code, provider, executable contract tests, real OOS evidence, model training, calibration artifact, production key/trust bootstrap, registry event, S2, VPS/runtime, T0/T1/T2 or AI admission created.
- Verification: GitHub source/document commit recorded; no CI run for documentation-only freeze. Executable tests NOT RUN; validator NOT IMPLEMENTED.
- **Disposition: STRUCTURAL CONTRACT FROZEN; IMPLEMENTATION NOT STARTED; OOS NOT VERIFIED.** Next eligible increment is a separately approved pure offline validator and deterministic contract tests for F1–F5. Production decision remains fail-closed.


## OOS Evaluation Evidence v1 offline validator — implementation increment (2026-11-12)

- Owner approved implementation of a pure offline validator and deterministic F1-F5 contract tests. Work stayed on feature/t0-centralized-data-feeder-p1-20261101; no branch/PR split.
- Added pipeline/oos_evaluation.py: strict UTF-8/no-BOM JSON parsing, duplicate-key and JSON-number rejection, RFC 8785 JCS exact-byte enforcement, exact F1 top-level/nested field sets, ID/digest/commit/timestamp/count/decimal validation, manifest evaluation ID + exact-byte digest binding, locally checkable dataset partition identity/time-order invariants, metric/baseline compatibility and uncertainty consistency.
- Added pipeline/test_oos_evaluation.py: synthetic-only deterministic tests for valid structural record, exact fields, BOM/UTF-8/duplicate keys, JSON numbers/noncanonical bytes, manifest ID/digest mismatch, dataset duplication, temporal ordering, uint64/count handling, candidate-population arithmetic, metric grammar/direction/uniqueness, baseline compatibility, uncertainty bounds and scalar/commit validation.
- Updated .github/workflows/ai-strategy-contract-red.yml to compile the new module/tests, run the OOS validator tests, and upload the OOS test log.
- Source commits: validator initial 475d2941685ce709c56f65364660e6183660b9fe; test suite d6638828d047431cee270f26bda6716df1ae57c5; metric direction type-guard correction 3ae3c4304d39d0033265db740dfab1edcd1f1176; CI workflow 26575235ffb230ddf0653eab94e29728bf65c638 (latest source SHA at this handoff update).
- Latest blobs: validator ed7b19d6d2d9595019c7d650832fce09f43aa3ff; tests 149df55597fb830a585002e6e83fdda47a496ac2; workflow 4deebeae9bc33a4bc7aa2a84e57633b0ab5d8b1d.
- Verification status: GitHub combined status for source SHA 26575235ffb230ddf0653eab94e29728bf65c638 returned no status checks. No workflow run/job log was available during this increment; local clone/test execution was unavailable in this session. Therefore compile/test result is NOT VERIFIED, not PASS. Workflow is configured to run these tests on the branch push, but exact run evidence must be collected before promoting status.
- Validator result vocabulary deliberately returns oos_evidence_status=NOT_VERIFIED, lineage_status=NOT_VERIFIED, horizon_embargo_status=NOT_VERIFIED, reproducibility_status=NOT_VERIFIED, statistical_policy_status=NOT_EVALUATED, and ai_admission_eligible=false. It does not assert sample-level lineage, trusted time, OOS quality or admission.
- No production provider, authoritative lineage source, split algorithm, statistical threshold, trusted-time anchor, production key/trust, real OOS data/evaluation, model training/calibration, registry event, S2, VPS/runtime, T0/T1/T2, database migration or live trading change.
- Review boundary: structural/local consistency only. F4 sample-level disjointness and horizon embargo remain unverified because no authoritative lineage evidence is accepted or inferred by this offline validator. F6 decisions remain open. Frozen manifest v1, transform v1, decision gate and F1-F5 contract unchanged.
- **Disposition: IMPLEMENTED; CI/TESTS NOT VERIFIED; OOS NOT VERIFIED; AI ADMISSION FAIL-CLOSED.** Next: inspect GitHub Actions run for exact source SHA 26575235ffb230ddf0653eab94e29728bf65c638; correct any failures and record run/job/artifact evidence. Do not wire the validator into production admission or claim OOS VERIFIED.


## OOS Evidence v1 validator — CI verification and review closure (2026-11-12)

- Follow-up fixes on the same branch after exact-SHA CI feedback:
  - `b36c5520a34d954475c24a9306f131aee400f8c6`: accept canonical fractional decimal strings including 0.2 and -0.2 while retaining no-exponent/no-trailing-zero representation.
  - `6cc1845dfe23fbe3cd9a902e567e320ed9721b86`: repair mutated-fixture tests to recompute the test manifest digest; JSON boolean is used for scalar-type rejection because JSON numeric tokens are rejected earlier by contract.
  - `196317638d5be7bc3e542aaa1a9249250c9cab6f` and `0a3f73801cc5f1f5225658673b447ec658ac454d`: distinguish digest equality against caller-supplied binding from signed-manifest authenticity. Validator reports `manifest_binding_status=DIGEST_MATCHED_TO_SUPPLIED_BINDING` and `manifest_authenticity_status=NOT_VERIFIED`; no signature/authenticity claim is made.
- Latest exact-SHA CI: workflow run `43073542645` (#60), source SHA `0a3f73801cc5f1f5225658673b447ec658ac454d`, job `130707512877`.
- Exact verification:
  - Python compile step: PASS.
  - Calibrated Confidence/Provenance focused tests: 14/14 PASS.
  - Decision regression tests: 15/15 PASS.
  - Calibration Registry verifier/transform tests: 21/21 PASS.
  - OOS Evaluation Evidence v1 validator tests: **13/13 PASS**.
  - Broader AI Strategy/dual-strategy RED suite: 54 tests, 12 failures and 6 errors; job/run overall FAILURE. Failures are in existing AI sizing/leverage/instrument rules, Kill Switch and AI ledger/API contracts, outside this OOS validator increment. The validator-specific step completed successfully before this separate RED suite.
- Exact artifact: ID `13878273616`; name `ai-strategy-contract-red-0a3f73801cc5f1f5225658673b447ec658ac454d`; SHA-256 `sha256:76407ecdb6311a186967fa8ac6e187cac43fd9cec9a31b1499ca3353d685e28d`; expires 2026-11-18T18:00:14Z.
- Earlier run `43073350688` at SHA `6cc1845dfe23fbe3cd9a902e567e320ed9721b86` also recorded OOS 13/13 PASS; run `43073542645` is the latest run covering the final manifest-authenticity status refinement.
- Review findings addressed: decimal grammar now accepts ordinary fractional values; fixture mutations retain exact manifest digest binding; supplied binding is not mislabeled as authenticated manifest. The offline validator remains separate from production decision path and has no authority to set OOS VERIFIED.
- F4 sample-level dataset disjointness, complete forecast horizon embargo, future-feature dependency and exclusion accountability remain **NOT VERIFIED** because no authoritative sample lineage/provider is part of this approved scope. Optional candidate-population arithmetic is only a local consistency check.
- No F6 policy/provider choices were made: authoritative lineage source, split algorithm/reproducibility tolerance, approved metric catalogue, statistical thresholds/sample floor/freshness/calibration duration/C_min interaction, trusted-time anchor, detached signature requirement and resource limits remain open.
- No real OOS record/provider, model training/calibration artifact, production key/trust, registry event, S2, VPS/runtime, T0/T1/T2, DB migration or live order path changed.
- **Disposition: OOS OFFLINE VALIDATOR IMPLEMENTED; COMPILE PASS; OOS CONTRACT TESTS 13/13 PASS; FULL WORKFLOW FAILURE DUE TO SEPARATE AI/DUAL-STRATEGY RED CONTRACTS; OOS NOT VERIFIED; AI ADMISSION FAIL-CLOSED.**
- Next eligible work: prepare a concise Owner decision package for the remaining F6 policy/provider choices before any provider or real OOS evaluation is implemented. No F6 value may be silently inferred from the structural freeze.


## OOS Evidence v1 F6 Owner decision package (2026-11-12)

- Prepared docs/architecture/AI_CALIBRATION_OOS_EVIDENCE_V1_F6_OWNER_DECISION_PACKAGE.md as a documentation-only package for the seven F6 decisions still open after F1-F5 structural freeze.
- Package commit: d16fd498a8d66f9104922e24531b52189fc55098.
- Covers: (F6.1) authoritative dataset lineage; (F6.2) split protocol and reproducibility; (F6.3) metric catalogue/label suitability; (F6.4) statistical acceptance and C_min interaction; (F6.5) trusted time/freshness; (F6.6) detached evaluation signature; (F6.7) provider resource limits.
- Each item contains explicit options and a recommended candidate, clearly marked as proposal only. No F6 choice is ratified or inferred. Recommended minimal path keeps evidence descriptive, freshness UNKNOWN and AI admission fail-closed until provider/policy gates close.
- No source code, test, workflow, dependency, provider, real dataset/evaluation, key, trusted-time anchor, model training/calibration, S2, VPS/runtime, T0/T1/T2 or trading path changed in this documentation increment.
- CI is not applicable to this documentation-only decision package; no tests were run for it. Validator verification remains tied to exact source SHA 0a3f73801cc5f1f5225658673b447ec658ac454d, workflow run 43073542645, job 130707512877, OOS tests 13/13 PASS, artifact ID 13878273616, digest sha256:76407ecdb6311a186967fa8ac6e187cac43fd9cec9a31b1499ca3353d685e28d.
- **Disposition: F6 OWNER DECISION PACKAGE PREPARED; F6 POLICY/PROVIDER IMPLEMENTATION BLOCKED PENDING OWNER DECISIONS; OOS NOT VERIFIED; AI ADMISSION FAIL-CLOSED.**
- Next: Owner reviews and decides F6.1-F6.7. Do not implement a lineage provider, real OOS evaluation or admission threshold before explicit decisions and a separate exact implementation gate.


## OOS Evaluation Evidence v1 — F6 Owner decisions approved (2026-11-12)

- Owner explicitly approved the recommended design direction for all F6.1–F6.7 items. Durable decision record: `docs/architecture/AI_CALIBRATION_OOS_EVIDENCE_V1_F6_OWNER_DECISION_RECORD.md`; decision-record commit `14d622a150a0a792980264671a7f0ec54e261ef2`.
- F6.1: A — read-only canonical bundle lineage; T0 remains canonical and unmodified.
- F6.2: A — fixed chronological holdout; embargo covers maximum forecast/label horizon and overlapping feature windows. Exact split algorithm/version, seed and reproducibility tolerance must be specified before implementation.
- F6.3: approved minimal metric categories: Brier, Log Loss, reliability-bin evidence, sample counts, uncertainty intervals and same-population baseline. Exact mathematical definitions, binning, missing/imbalance handling and aggregation remain to be frozen before real evaluation.
- F6.4: A — descriptive evidence only; all admission thresholds, minimum effective sample count, calibration duration, freshness/age and C_min interaction remain deferred.
- F6.5: A — trusted time deferred; freshness UNKNOWN; freshness-dependent admission remains fail-closed.
- F6.6: A conditional — no detached evaluation signature only if provider independently verifies signed manifest authenticity and exact record bytes/digest binding; otherwise defer and keep OOS NOT_VERIFIED.
- F6.7: provisional design ceilings approved for planning: record 256 KiB, JSON depth 8, 64 members/object, 128 metric/uncertainty/reliability items, identifier length 128 ASCII chars. These are not measured provider CPU/time/memory limits; validate and freeze enforcement details in a bounded implementation specification.
- **Approval scope is policy/design only.** It does not authorize provider/adapter or split/metric implementation, real dataset inventory/lineage collection/OOS evaluation, model training/calibration, threshold tuning, key/trust/timestamp operations, registry events, S2, VPS/runtime, T0/T1/T2/database/ledger/risk/kill-switch changes or trading. Separate exact implementation approval is required.
- Frozen F1–F5, manifest v1, transform v1 and decision gate remain unchanged. Offline validator's supplied-binding digest match is not authenticity. F4 sample-level disjointness, full horizon embargo, future-feature exclusion and exclusion accountability remain NOT VERIFIED until authoritative lineage verification.
- Existing CI evidence remains unchanged: source SHA `0a3f73801cc5f1f5225658673b447ec658ac454d`, workflow run `43073542645`, job `130707512877`; OOS validator tests 13/13 PASS. Overall workflow FAILURE from separate AI/Dual Strategy RED suite (12 failures, 6 errors). Artifact ID `13878273616`, SHA-256 `sha256:76407ecdb6311a186967fa8ac6e187cac43fd9cec9a31b1499ca3353d685e28d`.
- **Disposition: F6 DESIGN APPROVED WITH QUALIFICATIONS; PROVIDER/REAL OOS IMPLEMENTATION NOT AUTHORIZED; OOS NOT VERIFIED; AI ADMISSION FAIL-CLOSED.**
- Next: preserve this approved baseline. If proceeding, prepare a narrowly scoped implementation proposal and request separate approval before any provider or real OOS work.


## OOS lineage + chronological holdout implementation scope prepared (2026-11-12)

- Owner approved preparation of the next bounded implementation scope; this is approval to prepare the proposal only, not approval to modify code.
- Created `docs/architecture/AI_CALIBRATION_OOS_LINEAGE_CHRONOLOGICAL_HOLDOUT_IMPLEMENTATION_SCOPE.md`; commit `a9668257606be867d46aad958aa38f0332d85dcc`.
- Scope is divided into WP0 read-only inventory of the exact existing `T0_M15_H1_DATASET_BUNDLE_V1` contract; WP1 freeze of minimum read-only lineage-verification contract; WP2 freeze of deterministic fixed chronological holdout/embargo semantics; WP3 pure offline verifier with test-first deterministic tests; WP4 CI and exact evidence capture.
- Important sequencing: WP0 must inspect existing bundle contract before any new schema or code is proposed. If sample identity, timestamp semantics, feature windows, label horizons, exclusions, canonical bytes/digest or independent source derivation are missing/ambiguous, stop and request Owner decisions. Do not invent or reinterpret bundle schema.
- Proposed test coverage includes exact bytes/digest, malformed/noncanonical bundle, sample identity/disjointness, chronological ordering, label horizon and feature-window embargo, missing source coverage, exclusions, bounded parser ceilings, NOT_VERIFIED behavior when source evidence is absent, and deterministic output.
- Candidate source scope is a pure `pipeline/` verifier + tests + narrowly scoped CI; no change to `market_data/`, T0 API/feeder/storage, `freqai_bridge/context.py`, registry/decision contracts, databases or runtime absent separate approval.
- No source code, tests, workflow, dependency, dataset/bundle, provider, model training/calibration, real OOS evaluation, key/trust/time, S2, VPS/runtime, T0/T1/T2, DB, ledger/risk/kill-switch or trading path changed. Documentation-only increment; no tests run.
- Existing evidence unchanged: offline OOS validator tests 13/13 PASS at source SHA `0a3f73801cc5f1f5225658673b447ec658ac454d`, workflow run `43073542645`, job `130707512877`; overall workflow FAILURE due separate AI/Dual Strategy RED suite (12 failures, 6 errors).
- **Disposition: IMPLEMENTATION SCOPE PREPARED; CODE IMPLEMENTATION NOT AUTHORIZED; OOS NOT VERIFIED; AI ADMISSION FAIL-CLOSED.**
- Next: Owner reviews WP0–WP4 and approves the exact inventory and contract freeze gates before any code/test/workflow changes.


## OOS lineage WP0 — read-only repository inventory (2026-11-12)

- Owner authorized automatic continuation toward completion of Calibrated Confidence and Provenance, subject to all existing scope boundaries and explicit approval gates. This does not override the WP0 stop condition or authorize T0/VPS/runtime/data access, bundle creation, training, real OOS evaluation, provider/trust implementation, S2 or trading.
- Inspected active branch HEAD `f012305b9c13d0deb7ec1bdfeda22a2affb7a5d2`; recursive Git tree `14a19ff0f659eaaf9114cd77ed08c9d6ac1da429`, 978 entries, not truncated. Handoff and approved implementation scope were read first.
- WP0 inventory report: `docs/evidence/AI_CALIBRATION_OOS_LINEAGE_WP0_REPOSITORY_INVENTORY_2026-11-12.md`; commit `8426a5a417018f5a091a3999f6c9f5098437f9f3`; blob `6d1bfac8977e10b47da5a5431c8990624be20bdf`.
- Findings: the named `T0_M15_H1_DATASET_BUNDLE_V1` schema, immutable bundle payload, producer and consumer binding are not present/identifiable in the tracked branch. Synthetic P1.8 evidence bundles are unrelated and cannot be substituted. A prior bounded D1 inventory also recorded the candidate as absent from the then-inspected Git tree; neither inventory proves absence outside GitHub.
- Existing T2 source proves only a bounded M15 T0 HTTP inference window. FreqAI source has M15 features and a four-candle future-return target; config has `shuffle=false` and `test_size=0.2`, but no frozen three-way train/calibration/evaluation split, sample IDs, sample-level feature/label mapping, H1 bundle binding, or explicit horizon/feature embargo. Training provenance is supplied by an external sidecar and is not independently reconstructed by this code.
- Dataset consumer contract remains design-only. OOS offline validator explicitly does not verify authoritative lineage, sample-level embargo, reproducibility, trusted time or statistical acceptability.
- **Disposition: WP0 BLOCKED / PARTIAL STATIC INVENTORY COMPLETE.** No WP1/WP2 contract freeze or WP3 implementation may proceed against an inferred schema. OOS, lineage, horizon embargo and reproducibility remain NOT_VERIFIED; AI admission remains fail-closed.
- No tests were run (documentation-only evidence capture). No source, test, workflow, dependency, dataset, T0/T1/T2, DB, VPS/runtime, trust/key/time, registry, S2, ledger/risk/Kill Switch or trading path changed.
- Next: identify the exact authoritative read-only location/reference and access method for the already-existing bundle, if it exists outside GitHub. Any T0/VPS/database access requires its own bounded approval. If no bundle exists, Owner must separately approve whether/how to specify a derived read-only bundle without mutating T0.


## T0 full-history M15/H1 bundle creation — bounded read approval (2026-11-12)

- Owner explicitly approved reading the full currently available BTCUSDT M15 and H1 history from T0 through the existing read-only Candle API for the purpose of creating a derived dataset bundle.
- Approved scope: read-only `GET /v1/candles`; BTCUSDT; M15 and H1; full currently retained history; paginated windows no larger than 2,000 candles/request; no writes or mutations to T0, its database, API, feeder, lease, or runtime.
- Intended output: a separate immutable derived bundle with a versioned manifest, source/range/coverage metadata, exact payload digests and sample-level lineage. T0 remains canonical; the bundle is not a second canonical store.
- Explicitly excluded: T0/T1/T2 code/runtime changes, DB migration, VPS deployment or service activation, model training/calibration, real OOS evaluation, registry/trust/key/time operations, S2, AI admission changes, and all live trading/orders.
- Repository inspection reconfirmed the API contract from `market_data/api.py` (blob `81733c9b6de811cbebb2f5d472d41f37f337990c`) and `market_data/README.md` (blob `d90f84f8135c8ab9da1b57863e145d86565bf179`): Bearer authentication, fixed BTCUSDT market, `[startMs,endMs)`, aligned boundaries, max 2,000 candles/request, M15/H1 support via `INTERVAL_MS`, and explicit coverage/gap metadata. API returns `availableAtMs`, `availabilityKind=FIRST_OBSERVED`, `quality=VALIDATED` and `datasetVersion`.
- Access limitation: the current ChatGPT-connected GitHub interface can inspect repository files and workflow evidence but provides no authenticated network route to the private T0 API/VPS. No endpoint address or credential was exposed in the repository, and no token was requested or copied into chat. Therefore no T0 data request or bundle export has yet been performed.
- **Disposition: READ SCOPE APPROVED; REPOSITORY API CONTRACT VERIFIED; T0 DATA ACCESS BLOCKED pending a secure execution path that can read the API without disclosing credentials. No T0/runtime/data mutation performed.**
- Next: establish a secure execution path on the approved operator environment (for example, run the dedicated read-only exporter there with `MARKET_DATA_TOKEN` supplied through its local secret environment, never command-line arguments, URL, GitHub commit or logs). First perform a bounded metadata/coverage probe; then confirm expected ranges and gaps before full export. Keep the resulting bundle outside Git until its size, integrity and intended storage location are assessed; publish only non-secret manifest/evidence to GitHub.


## Latest verification — exact-commit repository-file inventory (2026-11-11)

- Active branch HEAD before this increment: `385f667f1532e358f4870cad1c8daf5c54f7789c`.
- Read-only comparison used the complete recursive Git tree at that commit (979 entries; `truncated=false`) and fetched every file in the 40-path `ci/l4-repository-file-inventory.json` allowlist.
- The comparison found five stale expected Git blob SHA-1 pins: the L4 automation plan, L4M08 claim-discipline assessment, L4M10 readiness assessment, L4M02 signer assessment, and T0 evidence checkpoint contract. The actual path/blob identities were re-read from the exact active branch; no file contents were modified.
- Corrected only those five pins in `ci/l4-repository-file-inventory.json`. Config update commit: `8efbcda80a64c5b84bbfb747f0e1f15bdec54149`; config blob: `9088690b6d4216b88e66461969f0f5e666564524`. The inventory remains 40 exact paths; no source, tests, workflow, dependency, runtime, data or policy contract changed.
- Workflow run [43078011975](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43078011975), event `push`, branch `feature/t0-centralized-data-feeder-p1-20261101`, exact source/checkout SHA `8efbcda80a64c5b84bbfb747f0e1f15bdec54149`, overall **SUCCESS**.
- Job `130722878680` lineage contract: **12/12 PASS**.
- Job `130722952886` exact-commit repository-file inventory: **10/10 tests PASS**; builder verdict `L4_REPOSITORY_FILE_INVENTORY=PASS`; all 40 configured paths and Git blob pins validated from the exact checkout. Manifest JSON SHA-256: `1c29166df7acc6a69403f8ccceee0a358b6757c8e45a99e76efa493c47bba6d9`.
- Repository-file inventory artifact ID `13883615482`, name `t0-l4-repository-file-inventory-43078011975`, size 4,492 bytes, uploaded ZIP digest `sha256:204ae06603ce59696b874049f7db8edb88fbcd1916ea60da1e550ea5579c3ef0`, expiry `2026-11-18T18:27:53Z`.
- Job `130722953038` artifact manifest: **19/19 tests PASS**; verdict `L4_ARTIFACT_MANIFEST=PASS`. Artifact ID `13882703668`, name `t0-l4-artifact-manifest-43078011975`, size 3,267 bytes, uploaded ZIP digest `sha256:21525f90837ff2155767d2e770493c839f16cbe748746b23e23030d0135ae20b`, expiry `2026-11-18T18:27:53Z`.
- Lineage artifact ID `13881784397`, name `t0-l4-minimum-lineage-43078011975`, size 1,153 bytes, uploaded ZIP digest `sha256:cad6cf6e4daf753651eb0f0593a69c098754343017c059317bc3de49ce5e2425`, expiry `2026-11-18T18:27:53Z`.
- The three ZIP digests above are upload-log digests; they have not yet been independently downloaded and re-hashed. The repository-file manifest JSON digest was emitted by the workflow, but the uploaded ZIP/payload still requires independent readback if promoted as custody evidence.
- **Disposition: EXACT REPOSITORY-FILE INVENTORY — PASS (40 paths, exact commit/blob binding); L4 ARTIFACT MANIFEST PILOT — PASS at its scoped 19-test contract; L4-MINIMUM AGGREGATE — BLOCKED / NOT VERIFIED.** This does not prove owner custody, signer separation, trusted time, signature verification, offline verification or acceptance of any L4 control.
- Next permitted step: independently download and re-hash the new inventory artifact and inspect its manifest payload against the exact 40-path set; then reconcile any remaining authoritative source references without promoting historical documents as current authority. Keep T0/VPS access, bundle export (currently paused), trust/key/time operations, destructive data operations, T1 activation, runtime and trading out of scope.


### Independent repository-file inventory artifact readback (2026-11-11)

- Downloaded artifact ID `13883615482` (`t0-l4-repository-file-inventory-43078011975`) and independently hashed the downloaded ZIP bytes.
- Independent ZIP SHA-256: `204ae06603ce59696b874049f7db8edb88fbcd1916ea60da1e550ea5579c3ef0`; matches the GitHub artifact metadata and workflow upload log exactly.
- ZIP contains exactly two members: `l4-repository-file-inventory.json` (9,757 bytes) and its SHA-256 sidecar (100 bytes); no extra members.
- Independently computed JSON SHA-256: `1c29166df7acc6a69403f8ccceee0a358b6757c8e45a99e76efa493c47bba6d9`; matches the sidecar and the workflow log.
- Parsed payload: schema `T0_L4_REPOSITORY_FILE_INVENTORY_V1`; branch `feature/t0-centralized-data-feeder-p1-20261101`; source commit `8efbcda80a64c5b84bbfb747f0e1f15bdec54149`; 40 entries, 40 unique paths, total source bytes 567,960. The payload source commit is the exact workflow checkout SHA.
- **Disposition: INVENTORY ARTIFACT ZIP READBACK + SHA-256 — PASS; MANIFEST JSON + SIDECAR — PASS; 40-entry structure — PASS.** This proves integrity of the downloaded inventory artifact and its manifest, not independent custody of the 40 source documents outside GitHub, not signatures/trusted time/offline verification, and not L4 control acceptance.
- Current next step: reconcile the inventory payload entries against the allowlist and retain the independent ZIP/JSON hash evidence; then continue the remaining bounded L4 evidence acquisition work. Aggregate L4-Minimum remains BLOCKED / NOT VERIFIED.


### L4 Actions source allowlist extension — eight-item baseline (2026-11-11)

- After independent readback, two outputs from run `43078011975` were classified as eligible source inputs for a subsequent collector run: lineage contract CI artifact `13881784397` and exact repository-file inventory artifact `13883615482`. Both were exact-run/source-bound, unexpired, independently downloaded and re-hashed before inclusion. The manifest output artifact was not added as a source input.
- Allowlist update commit: `f00b30af40f65a5ce06501ade6ccf72a27740306`; allowlist blob: `c1f270fc64d101c1c94da78d5909ac6ce5a79fde`. The allowlist now contains eight unique source artifacts. No workflow logic, source code, tests, dependencies or runtime changed.
- Subsequent workflow run [43078412140](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43078412140), event `push`, branch `feature/t0-centralized-data-feeder-p1-20261101`, exact source/checkout SHA `f00b30af40f65a5ce06501ade6ccf72a27740306`, overall **SUCCESS**.
- Job `130724283481`: lineage contract **12/12 PASS**.
- Job `130724361663`: repository-file inventory **10/10 PASS**, verdict `L4_REPOSITORY_FILE_INVENTORY=PASS`.
- Job `130724361672`: artifact manifest **19/19 PASS**, verdict `L4_ARTIFACT_MANIFEST=PASS`. Total: **41/41 tests PASS** across all three jobs.
- Current-run output artifacts:
  - Lineage ID `13883561072`, name `t0-l4-minimum-lineage-43078412140`, 1,150 bytes, ZIP digest `sha256:7533fb1f81acd5001509e01c4808ed41f5e5e2151c826f9faaaaf043a53cacaa`, expiry `2026-11-18T18:30:27Z`.
  - Repository inventory ID `13882149316`, name `t0-l4-repository-file-inventory-43078412140`, 4,489 bytes, ZIP digest `sha256:a48fe17269f6faf58237f9adfca1887cf9e7cd22b82cdd4647e786396b83ea55`, expiry `2026-11-18T18:30:27Z`.
  - Manifest ID `13881878807`, name `t0-l4-artifact-manifest-43078412140`, 3,626 bytes, ZIP digest `sha256:8ea24a3eafd04cb424593251a9bb76c5c62b88409e19634162ffe1786a0ffe95`, expiry `2026-11-18T18:30:27Z`.
- Independently downloaded and re-hashed manifest artifact `13881878807`: ZIP SHA-256 `8ea24a3eafd04cb424593251a9bb76c5c62b88409e19634162ffe1786a0ffe95`, matching GitHub metadata; ZIP CRC passed. Manifest JSON SHA-256 `4b37dbe429626deae17f50b95b903e16bc6b6e9210b71567764fb608d0343627` matches its sidecar. Parsed schema `T0_L4_GITHUB_ARTIFACT_MANIFEST_V1`, collector source SHA `f00b30af40f65a5ce06501ade6ccf72a27740306`, exactly eight unique allowlisted artifacts.
- The eight-item manifest reconciles the two P1.8.14 synthetic artifacts and six L4 CI source artifacts. It keeps generated current-run outputs separate from source inputs; the current run's outputs are not self-included. The newly produced current-run lineage and repository-inventory outputs have not yet been independently read back and are not in the eight-item source allowlist.
- **Disposition: EIGHT-ITEM SOURCE ALLOWLIST + COLLECTOR MANIFEST — PASS at the stated CI/readback scope; L4-MINIMUM AGGREGATE — BLOCKED / NOT VERIFIED.** No owner custody, signer separation, authenticated latest-head, trusted-time, network-disabled offline verification or control acceptance is established.
- Next: freeze the current eight-item source inventory unless a separately reviewed candidate materially adds evidence; proceed only with read-only exact-object signature/negative-verification design review. No key generation/signing/rotation, trust-root/provider mutation, offline owner execution, VPS/T0 access, data deletion, T1 activation, runtime or trading.


### Eight-item L4 source inventory — follow-up CI and manifest readback (2026-11-11)

- Allowlist commit/source: `f00b30af40f65a5ce06501ade6ccf72a27740306`; allowlist blob `c1f270fc64d101c1c94da78d5909ac6ce5a79fde`; eight unique source artifacts.
- Workflow run [43078412140](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43078412140), event `push`, exact checkout/source SHA `f00b30af40f65a5ce06501ade6ccf72a27740306`, overall **SUCCESS**.
- Job `130724283481`: lineage 12/12 PASS.
- Job `130724361663`: repository-file inventory 10/10 PASS; `L4_REPOSITORY_FILE_INVENTORY=PASS`.
- Job `130724361672`: artifact manifest 19/19 PASS; `L4_ARTIFACT_MANIFEST=PASS`.
- Total: **41/41 tests PASS**.
- Output artifacts: lineage `13883561072` (1,150 bytes; upload ZIP SHA-256 `7533fb1f81acd5001509e01c4808ed41f5e5e2151c826f9faaaaf043a53cacaa`); repository inventory `13882149316` (4,489 bytes; `a48fe17269f6faf58237f9adfca1887cf9e7cd22b82cdd4647e786396b83ea55`); manifest `13881878807` (3,626 bytes; `8ea24a3eafd04cb424593251a9bb76c5c62b88409e19634162ffe1786a0ffe95`). All expire `2026-11-18T18:30:27Z`. These are GitHub upload digests until independently read back.
- Independently downloaded artifact `13881878807`: ZIP SHA-256 `8ea24a3eafd04cb424593251a9bb76c5c62b88409e19634162ffe1786a0ffe95`, matching GitHub metadata; ZIP CRC passed. Manifest JSON SHA-256 `4b37dbe429626deae17f50b95b903e16bc6b6e9210b71567764fb608d0343627` matches sidecar. Parsed schema `T0_L4_GITHUB_ARTIFACT_MANIFEST_V1`, collector SHA `f00b30af40f65a5ce06501ade6ccf72a27740306`, eight entries, exactly reconciling the two P1.8.14 synthetic sources and six L4 CI sources in the allowlist.
- Current-run outputs `13883561072` and `13882149316` remain outputs, not inputs to their own manifest; they have not yet been independently downloaded/read back. Do not self-include.
- **Disposition: EIGHT-ITEM ALLOWLIST AND MANIFEST — PASS at stated scope; L4-MINIMUM AGGREGATE — BLOCKED / NOT VERIFIED.** This does not establish owner custody, signer separation, authenticated freshness, trusted time, offline verification or control acceptance.
- Next: refresh the exact-object signature/negative-verification design review against the current amended Checkpoint Contract v1, A1/A2.2/A2.3 documents and current custody decision. Keep implementation, keys, trust bootstrap, anchor persistence, VPS/T0/runtime and trading excluded.


## L4 exact-object signature / negative-verification refresh (2026-11-12)

- Read-only review refreshed the prior 2026-11-11 architecture assessment against current Checkpoint Contract v1 blob `a6825270d59bde274bfe765d5f942144b66a84de`, A1 blob `00fdad293e129562145ab930507a4e6b9c2bf23d`, A2.2 blob `d9f93bf390d107381b7135c3073aeca0d14894d4`, A2.3 draft blob `41d6abfc9df20047af4668b80a6ce2edb7e07117`, Stage II adapter contract blob `8ec916c152c51e75c5a3852e7977dd7f1239d8fe`, and field mapping review blob `1185a3bf65d66c8cd203bd1dbc7994fdca0b1ad1`.
- Refresh report: `docs/evidence/T0_L4_SIGNATURE_NEGATIVE_VERIFICATION_REFRESH_2026-11-12.md`; commit `ec8d8c7793a88f3444eae6b4b840a34c29f7c4bc`.
- Findings: Checkpoint v1 remains draft/documentation-only; Ed25519 adapter remains stateless/draft/not implemented; owner-selected B + E2 representation is recorded but AEO schema, signer-role/trust chain, issuer separation, descriptor schema/ID lifecycle, Verification Record schema, resource ceilings and reason-code contract are not frozen. PyCA 50.0.2 remains a candidate; exact wheel hash, transitive closure, provenance and offline install are NOT VERIFIED.
- Owner governance override: independent security review is **WAIVED as a mandatory gate** for Stage II A2.3/Ed25519 adapter work by later Owner instruction. This does not establish independent review, G3 or assurance. Harmonize contrary draft wording in a dated addendum before implementation. The existing A2.2 waiver record remains scoped to its stated A2.2 source candidate; this handoff records the later A2.3 instruction separately.
- L4 custody remains BLOCKED/NOT VERIFIED: VPS + GitHub is the bounded approved scope, but the former VPS was deleted and no replacement host is established. GitHub-only inventory/artifacts do not prove owner-controlled two-location custody, signed latest-head, offline verification or trust bootstrap.
- **Disposition: DESIGN PARTIAL; CONTRACT FREEZE BLOCKED; DEPENDENCY/BUILD PROVENANCE NOT VERIFIED; STAGE II IMPLEMENTATION NOT AUTHORIZED; L4-MINIMUM AGGREGATE BLOCKED / NOT VERIFIED.**
- Next: close the remaining contract decisions (AEO issuer separation, AEO/preimage schema, descriptor ID/namespace semantics, resource ceilings, Verification Record and reason codes), verify exact dependency/build provenance, freeze exact contract blobs and a bounded implementation scope, then obtain separate Owner implementation authorization. Do not generate/use real keys, bootstrap trust, persist anchors, access VPS/T0, deploy runtime, activate T1, train/calibrate or trade.


### L4 signature dependency provenance spot-check (2026-11-12)

- Added the PyPI provenance spot-check to `docs/evidence/T0_L4_SIGNATURE_NEGATIVE_VERIFICATION_REFRESH_2026-11-12.md`; report update commit `4f07d2a3ad55d4556e154bed657fe1200b46d433`; report blob `a483b21b5e6b919545bfa37d88b08bf62af99764`.
- Official PyPI metadata for `cryptography==50.0.2` confirms the candidate CPython 3.11+ abi3 / manylinux_2_34 x86-64 wheel, declared SHA-256 `9dab55f57c74c3cad24c323bacbbd04be4705ba6eb0d92e920b1fc4837ed5079`, and PyPI provenance metadata showing GitHub Actions publishing from `pyca/cryptography`, commit `fe12d283180ea89ceed622021242fddb31d27f84`, workflow `.github/workflows/pypi-publish.yml`, run `36731020563`.
- Exact wheel download into the review environment failed. No independent hash of downloaded bytes, Sigstore bundle verification or offline provenance verification was completed.
- **Disposition: OFFICIAL RELEASE METADATA / DECLARED HASH / PROVENANCE PRESENCE — CORROBORATED; EXACT WHEEL PAYLOAD / ATTESTATION CRYPTOGRAPHIC VERIFICATION — NOT VERIFIED.** No package installation, lockfile change or CI dependency change.
- Next: prepare an Owner decision package for the remaining AEO issuer separation, resource ceilings, exact schemas/ID namespace and Verification Record contract. Keep package installation, key/trust operations, Stage II implementation and CI changes blocked pending explicit contract freeze and exact-scope authorization.


### Owner decision package prepared — A2.3 / Stage II contract freeze (2026-11-12)

- Decision package: `docs/decisions/T0_L4_SIGNATURE_CONTRACT_FREEZE_OWNER_DECISION_PACKAGE_2026-11-12.md`; commit `ef3a97418f2c45c91371767d024e7e31b8e38e12`.
- D1: whether AEO issuer principal and SPKI fingerprint must be distinct from the subject checkpoint signer (recommended: MUST be distinct).
- D2: whether to freeze the A2.3 proposed bounded resource ceilings as normative v1 limits.
- D3: whether to freeze the AEO body/statement/package descriptor/detached descriptor schemas, with the authorized descriptor namespace explicitly resolved.
- D4: whether to approve a schema-only append-only Verification Record contract, with no storage/runtime implementation.
- Non-owner technical gates remain: exact PyCA wheel byte hash and Sigstore attestation verification; transitive dependency/build provenance; exact cross-contract mapping; frozen deterministic vectors/state-immutability tests; exact-scope implementation request.
- The Owner's independent-review waiver remains in force for Stage II A2.3; it does not establish independent assurance/G3 and does not waive technical gates.
- **Disposition: DECISION PACKAGE PREPARED; OWNER DECISIONS PENDING; A2.3 NOT FROZEN; STAGE II IMPLEMENTATION NOT AUTHORIZED; L4-MINIMUM BLOCKED / NOT VERIFIED.**
- Next: wait for Owner decisions on D1–D4. Do not infer approval or proceed to code/dependency/CI changes from the package itself.


### Owner decision D1 recorded — AEO issuer separation (2026-11-12)

- Owner explicitly approved D1 (“có”): the AEO issuer principal MUST differ from the subject checkpoint signer principal, and the AEO issuer SPKI fingerprint MUST differ from the subject checkpoint signer SPKI fingerprint. Same principal or same SPKI fingerprint is rejected with `AUTHORIZATION_EVIDENCE_SELF_ISSUED`.
- Decision package updated: `docs/decisions/T0_L4_SIGNATURE_CONTRACT_FREEZE_OWNER_DECISION_PACKAGE_2026-11-12.md`; final content commit `4f5c5e3873609fb92cbc4bfd11b08bddfd6ccbb4`; blob `dcfba078383c875c1513acfbe54de07fcbf01c42`.
- Scope of approval is D1 policy only. It does not freeze AEO schema, issuer namespace/authority, signature preimage, trust chain or full A2.3; it does not authorize code/CI/dependency changes, key operations, trust bootstrap, real signing/verification or custody publication.
- D2 resource ceilings, D3 exact schemas/descriptor namespace and D4 schema-only Verification Record remain PENDING OWNER DECISION.
- **Disposition: D1 APPROVED; D2–D4 PENDING; A2.3 CONTRACT NOT FROZEN; STAGE II IMPLEMENTATION NOT AUTHORIZED; L4-MINIMUM BLOCKED / NOT VERIFIED.**
- Next: request/record D2 independently; do not infer approval of D2–D4 from D1.


### Owner decision D2 recorded — A2.3 normative v1 resource ceilings (2026-11-12)

- Owner approved D2 Option A (“phê duyệt”): adopt the exact A2.3 §9 ceilings as normative v1 parser/resource limits.
- Approved values: AEO body 1,048,576 B; canonical Signature Statement 1,048,576 B; fully prefixed signature preimage 1,048,640 B; SPKI DER 4,096 B; Ed25519 signature exactly 64 B; canonical signature envelope 1,114,112 B; detached descriptor 65,536 B; each nested evidence dependency 1,048,576 B; maximum 64 dependencies/AEO package; total frozen verification input set 16,777,216 B (16 MiB); JSON depth 32; object members 256; array elements 256; UTF-8 string length 16,384 B.
- Required later conformance: exact-boundary and immediately-over-limit tests for each ceiling; reject before unbounded allocation/processing; all failures fail closed without advancing policy, anchor, trust-root, accepted-checkpoint or verification-history state.
- Decision package updated: `docs/decisions/T0_L4_SIGNATURE_CONTRACT_FREEZE_OWNER_DECISION_PACKAGE_2026-11-12.md`; commit `1f1bbbef49c158e4692e3418ae93c888e384985e`; blob `b735979f1396c14ea45c5e359f2e0803d6572ced`.
- D2 applies only to parser/resource limits. It is not a retention/deletion/cleanup policy and does not authorize implementation, CI/dependency changes, package installation, key/trust operations or real evidence verification.
- **Disposition: D1 APPROVED; D2 APPROVED; D3–D4 PENDING; A2.3 CONTRACT NOT FROZEN; STAGE II IMPLEMENTATION NOT AUTHORIZED; L4-MINIMUM BLOCKED / NOT VERIFIED.**
- Next: request/record D3 independently; do not infer approval of D3/D4 from D1/D2.


## T0 → T2 M15/H1 consumer completion increment (2026-11-12)

- Final tested source commit: `625441535a7fcf76cfcb47ebd48eef87240cee41`; active branch remains `feature/t0-centralized-data-feeder-p1-20261101`. No new branch or PR.
- T2 `CandleHttpClient` now accepts M15/H1, validates interval alignment and timeframe identity, pages bounded 32-candle requests across windows up to 3,000 candles, rejects any incomplete/stale/identity-invalid page, and combines coverage/freshness. A single-page response preserves T0's `datasetVersion`; multi-page responses recompute the same T0 canonical hash over the full combined read-window identity and candles.
- T2 `canonical_context` accepts `timeframe="15m"|"1h"`; CLI exposes `--timeframe`. T0 API, storage, feeder, lease/writer and canonical data were not changed.
- Independent fixture coverage: M15/H1 pagination, timeframe identity, coverage, freshness thresholds, aggregate hash, unsupported timeframe, oversized windows and fail-closed page errors. Isolated SQLite + loopback T0 API + T2 integration now exercises complete and gapped M15 and H1 paths using synthetic exchange rows only.
- T0 manual validation run [43082340629](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43082340629), exact checkout/source SHA `625441535a7fcf76cfcb47ebd48eef87240cee41`, overall SUCCESS:
  - SQLite lease/fencing: 55/55 PASS; artifact `13884362952`, ZIP SHA-256 `f9abdfe9d946304bd75f0f950f8af48b14093aa08a2b8764a05d77b933ea1a4a`.
  - SQLite recovery: 64/64 PASS; artifact `13884233076`, ZIP SHA-256 `a9818675a5085050e3e92387bda19ec3604eb0557ac2ecddd2afdfda8ab3fab2`.
  - Isolated T0 → T2 data flow: 87/87 PASS, verdict `SQLITE_T0_TO_T2_DATA_FLOW=PASS`; artifact `13884602890`, ZIP SHA-256 `71d6e5f349807f760f627e5c0d05411e827225540526afc672b1ecfe69bab966`.
  - Manual runtime acceptance and G4 probe jobs were skipped; this is fixture/loopback CI evidence, not VPS or canonical-runtime acceptance.
- T2 HTTP consumer workflow [43081968562](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43081968562), source SHA `6697ad6d5f081e62ffd7e877a8d3ff6805e714f0`: adapter 45/45, context/migration 11/11, exporter 6/6 PASS; artifact `13883923321`, ZIP SHA-256 `ab3e7a051602d6a2013249fb9afd18cbb101d175d3c63c19d07da694e83f9917`. Freqtrade 2026.9 strategy-load smoke [43082340809](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43082340809) also PASS at final tested source SHA.
- A separate T0 Single Writer Gateway workflow [43082340853](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43082340853) has an unrelated five-layer paper-consumer regression failure; its static Gateway contract verification and TimescaleDB read-only integration jobs passed. Do not attribute that failure to the M15/H1 consumer change or promote the overall workflow to PASS.
- **Disposition:** T2 M15/H1 client/context + independent fixture and isolated SQLite/API loopback path **PASS**. Actual canonical T0 API read, T0 runtime acceptance, bundle creation/export and VPS deployment remain **NOT VERIFIED / NOT PERFORMED**. No live orders; paper-only guards unchanged.


### L4-Minimum CI increment — claim discipline and synthetic trust/history (2026-11-12)

- Repository: `kenznguyen/btcusdt-telegram-signals2`; existing branch `feature/t0-centralized-data-feeder-p1-20261101`.
- Exact code/workflow/crosswalk source SHA tested: `373303d65cc7c4b0d7b451efccd7df5a624c81b5`. This entry is a handoff-only update; do not treat the resulting documentation commit SHA as a tested code baseline.
- Workflow run [43085786627](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43085786627): **5/5 jobs SUCCESS** — lineage/policy contract, exact-commit repository inventory, GitHub artifact readback/manifest, L4M-08 claim discipline, and L4M-06/07 synthetic trust/history.
- L4M-08: **11/11 focused tests PASS**; actual current crosswalk audit PASS. Claim-discipline artifact ID `13885594414`, ZIP digest `422f472c7555644993b7ef6bdccc3e5503b9491fdc7135ca1395bd99d901743f`.
- L4M-06: **19/19 synthetic trust-lifecycle tests PASS**. L4M-07: **11/11 synthetic event/checkpoint/archive-history tests PASS**. Synthetic evidence artifact ID `13886257085`, GitHub digest and independently recomputed ZIP SHA-256 `8f81daefd6ff8c3d706f4febfa8dd5e71796e8fa2c67f876345713e4b8df4f70`; ZIP readback confirms source marker `373303d65cc7c4b0d7b451efccd7df5a624c81b5`, both PASS markers and test summaries.
- Other run artifacts: lineage ID `13885987505`, digest `35367b2ad82b3cdbd79a5f3d6eb26b7a8560a49992dfd0cc2a6aafca792a02b1`; repository inventory ID `13885064697`, digest `f693985b761b9ce8c15cefdfa5bc234b1e54b98c2c591dda64f8b00e89112a7e`; artifact manifest ID `13886991029`, digest `c2938256a43e471cb29d3db1d765f66ea2eecc06873ba10ab893d52537963c13`.
- Control disposition: L4M-06 and L4M-07 **PARTIAL — SYNTHETIC ONLY**; L4M-08 **DOCUMENTARY PASS ONLY** with automated crosswalk subcheck PASS. No control is promoted to full acceptance. L4M-01–05 and L4M-10 remain as recorded in the crosswalk. Aggregate L4-Minimum remains **BLOCKED / NOT VERIFIED**.
- Explicit limits: no T0/VPS/runtime access, no real signer/key operation, no trust-root or monotonic-anchor mutation, no production checkpoint signing, no owner custody/readback, no owner-run offline verification, no destructive action and no trading.
- Next bounded increment: inspect L4M-05 readback/recovery evidence and L4M-10 baseline-package automation using existing CI artifacts only. Do not cross into Stage II A2.3/Ed25519 implementation while that workstream remains PAUSED; actual custody, signer authority and owner acceptance remain external evidence gates.


### L4-Minimum CI increment — L4M-05 readback and L4M-10 fail-closed readiness (2026-11-12)

- Repository: `kenznguyen/btcusdt-telegram-signals2`; branch remains `feature/t0-centralized-data-feeder-p1-20261101`.
- Exact code/workflow/crosswalk source SHA tested: `f76e6f6d4697fe0d0609e70b02ded775f15bebe6`. This handoff-only update does not change the tested code baseline.
- Workflow run [43086457661](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43086457661): **6/6 jobs SUCCESS**. The run revalidated the updated crosswalk and all L4 automation jobs.
- L4M-05 GitHub artifact readback: artifact manifest contract **19/19 PASS**; exact current-run artifact readback/manifest job SUCCESS. Manifest artifact ID `13886856958`, GitHub ZIP digest `64e7956e82ff79fdf5adc138ec7fe8fe2041b05f98b7de7da500eef78161d1d1`. This is a GitHub-side CI readback subcheck only; owner-copy readback and non-destructive recovery from the owner's retained package remain NOT VERIFIED.
- L4M-10: **10/10 tests PASS**. The current nine-control status set, without a frozen baseline or owner disposition, evaluates to `BLOCKED / NOT VERIFIED` with all three expected blockers: active controls not all PASS, frozen baseline required, owner disposition required. L4M-09 is excluded from the denominator.
- L4M-10 artifact ID `13887580296`, GitHub digest and independently recomputed ZIP SHA-256 `f880d5968b24416d68a02a1531135a1ed47ef79315bf8d222cbd9af6f092c5af`; exact ZIP downloaded and read back. JSON binds source SHA `f76e6f6d4697fe0d0609e70b02ded775f15bebe6`, reports all nine active controls, no baseline, no owner disposition and `claims_l4_minimum_accepted=false`.
- Companion subchecks in the same run: lineage 12/12 PASS; repository inventory 10/10 PASS; L4M-06 trust lifecycle 19/19 PASS (synthetic); L4M-07 history 11/11 PASS (synthetic); L4M-08 claim discipline 11/11 PASS and crosswalk audit PASS.
- Disposition: L4M-05 GitHub readback subcheck PASS but overall PARTIAL; L4M-06/07 remain PARTIAL — SYNTHETIC ONLY; L4M-08 remains DOCUMENTARY PASS ONLY; L4M-10 readiness guard PASS but owner acceptance remains NOT VERIFIED. Aggregate L4-Minimum remains **BLOCKED / NOT VERIFIED**.
- Remaining non-CI evidence gates: owner-controlled custody/readback, real signer separation, signed canonical T0 checkpoint plus authenticated freshness anchor, owner-run offline verification, actual trust/revocation authority and final owner disposition. No VPS/runtime, real key, T0 canonical database, external provider, destructive operation or trading action was used. Stage II A2.3/Ed25519 implementation remains PAUSED.
- Next step: continue only with evidence that can be established from the existing approved GitHub/CI boundary. Do not promote synthetic results to owner or runtime evidence; do not claim L4-Minimum accepted.

### T1 producer decimal-integrity increment (2026-11-12)

- T1 source repository: `kenznguyen/binance-futures-collector`; existing branch `feature/t1-connection-sidecar-integration-20261107`. No new branch or PR.
- Current T1 source SHA under full verification: `a02efce222a04f69c08a18890528f6308c1d82b1`.
- Scope: remove lossy fixed-12-place `f64` formatting from producer persistence; preserve exchange decimal lexemes; reject malformed/missing numeric values rather than fabricate zero; calculate derived liquidation/open-interest notional values using exact decimal-string multiplication; skip long/short ratio rows when source account fields are absent; sort and retain order-book snapshot source decimal strings without reconstructing CSV values from floats.
- CSV writer increment at source SHA `daa43ef02c80b45ab4751718c89df439bed8de77`: Rust format, Clippy, build and tests PASS. Collector unit tests 50/50 PASS; sidecar writer tests 12/12 PASS. Artifact ID `13888122292`, SHA-256 `beada82e7d7c9ff7784d5117ea2f1bc60e2a72a0f43a335cc82a6de44f900715`. This artifact proves the writer-only increment, not the later upstream producer changes.
- Full producer change set now includes `src/utils/decimal.rs` exact string arithmetic/order comparison; WebSocket depth model no longer receives preconverted float arrays; order-book CSV snapshots use raw decimal source values; REST kline extraction rejects malformed timestamp/decimal fields; REST open-interest and liquidation notional calculations no longer use `f64`; missing long/short source fields are skipped rather than synthesized.
- Full-source CI run [43089869611](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43089869611) is **QUEUED** at source SHA `a02efce222a04f69c08a18890528f6308c1d82b1`. Duplicate push/PR run [43089863157](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43089863157) is also queued. Full-source compile/test and artifact are therefore **NOT VERIFIED** yet.
- Remaining implementation boundary: order-book in-memory computational maps still use `f64`; persisted snapshots use separate exact source-decimal maps and exact decimal ordering. No live Binance connection, collector activation, VPS/runtime access, T0/T2 change, trading or real order occurred.
- **Disposition: CSV writer increment PASS; full T1 producer decimal-integrity increment PARTIAL / NOT VERIFIED pending CI at exact source SHA above.**
- Next: allow the full-source CI run to complete; inspect fmt/Clippy/build/tests and artifact provenance; fix any failures on this same branch before changing the status. Do not deploy or activate T1.

- CI follow-up (2026-11-12): Full producer run `43089869611` at `a02efce222a04f69c08a18890528f6308c1d82b1` failed at the Rust `Format` step only; Clippy/build/tests were skipped. Dashboard frontend/backend, Docker build, and security jobs passed. Failure logs identified rustfmt-only diffs in `orderbook_manager.rs`, `rest_collector.rs`, `decimal.rs`, and `models.rs`; no compiler/test failure was observed because those steps did not execute.
- Applied rustfmt corrections on the same T1 branch. Intermediate CI attempts `43138890684`, `43138897209`, `43138905720` exposed remaining formatting in REST kline let-else and a blank line in `DepthUpdateWs`; those were corrected.
- Latest T1 branch HEAD: `e047bcebb0c0f28aa1d1fc8d9a83a56fb259cbd9`. Full CI run `43139023378` is QUEUED at this exact SHA; duplicate run `43139017716` is also queued. No final verification or artifact is available yet.
- Status remains **PARTIAL / NOT VERIFIED**. The earlier writer-only PASS remains bounded to its own SHA and does not validate the full producer changes. Do not mark the finding resolved until full CI (fmt, Clippy, build, tests, security, artifact provenance) passes at the exact final SHA.



### T1 producer decimal-integrity increment — exact-head CI PASS (2026-11-12)

- T1 repository: `kenznguyen/binance-futures-collector`; existing branch: `feature/t1-connection-sidecar-integration-20261107`. No new branch or PR; existing PR #1 remains open/draft and unmerged.
- Final T1 source SHA: `42b7a3c928ee62a0440ae176e7ebd0e5b2db5662`.
- CI run [43143191168](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43143191168), push event on the exact source SHA: **5/5 jobs SUCCESS** — collector fmt/Clippy/build/tests, sidecar writer checks, dashboard backend pytest, dashboard frontend typecheck/Vitest, Docker images, and security audits.
- Rust collector: `cargo fmt --all --check` PASS; `cargo clippy --all-targets --all-features -- -D warnings` PASS; release build PASS; workspace tests **56/56 library + 1/1 binary PASS**. Sidecar: format PASS, Clippy PASS, offline tests **12/12 unit + 27/27 integration PASS**.
- Artifact ID `13910212503`, name `t1-collector-linux-x86_64-42b7a3c928ee62a0440ae176e7ebd0e5b2db5662`; GitHub artifact digest and independently recomputed ZIP SHA-256: `a6ddb149befb999f48adb88bf7574d6a0cd3cae537319c6b864ac4f661bb524a`. ZIP readback confirms binary SHA-256 `192c070311cefd7497c956b3215e4fb079a670b5781ef9f285f1bb0938a21cd6` via embedded `SHA256SUMS`.
- Clippy findings from run `43139023378` were fixed on the same branch: remove unnecessary `mut` in `connection_manager.rs`; use `find(['e', 'E'])` in exact decimal parser. Rustfmt correction then made to satisfy `cargo fmt --check`; final exact-head run above passes.
- Targeted source review of `models.rs`, `rest_collector.rs`, `decimal.rs`, and `orderbook_manager.rs`: exchange decimal lexemes are preserved for CSV; malformed REST kline fields are rejected/skipped instead of synthesized as zero; derived OI/liquidation notionals use exact decimal-string multiplication; order-book snapshot CSV uses retained source strings and exact decimal sorting. No fixed-12-place formatter or `unwrap_or("0")` fallback was found in these reviewed files.
- Explicit residual: order-book's in-memory computational maps still parse prices/quantities to `f64`; raw decimal maps remain the CSV snapshot source. This increment does not claim removal of binary floating point from all computational order-book state, nor does it prove numerical equivalence of that internal view.
- **Disposition: T1 producer decimal-integrity code + exact-head CI verification PASS.** Runtime/operational acceptance remains NOT VERIFIED. No Binance live connection, T1 activation, VPS deployment, T0/T2 change, or trading was performed. Keep T1 inactive and `ai_execution_enabled=false`.
- Next step: preserve this CI evidence and continue with the next bounded GitHub-only T1 finding; do not activate/deploy T1 without explicit approval.

### T1 exact-decimal order-book key correction (2026-11-12)

- T1 repository: `kenznguyen/binance-futures-collector`; existing branch: `feature/t1-connection-sidecar-integration-20261107`; PR #1 remains OPEN/DRAFT and unmerged.
- Scope: remove binary-float price identity from in-memory order-book levels while retaining the current `f64` quantity calculation view. No T0/T2, strategy, risk, VPS, runtime, or exchange activation changes.
- Regression test `distinct_decimal_price_levels_do_not_collide_in_the_computational_book` was added first at source SHA `5fc28fce8c161ebc663a6c8af68eb218f3137cfd`. Exact-head CI run [43144192074](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43144192074) confirmed RED: inserting `1.00000000000000001` and `1.00000000000000002` produced 1 computational level instead of 2; 56 other library tests passed. This establishes the reported f64-key collision.
- Implementation now keys `Orderbook.bids` and `Orderbook.asks` by normalized exact decimal strings. Snapshot ingest and WS diff insert/update/delete use the same canonical key. Best bid/ask and depth trimming compare normalized decimal strings using the existing exact decimal comparator. Quantity values remain `f64`; no claim is made that all order-book arithmetic is exact.
- T1 implementation commit SHA: `70be9f13870bd59ee1a379b3ee7393cbcd0afd2e`; rustfmt-only follow-up commit: `5f6ecd879ce25426cfd31d39fb4282acce7a1a76`. Current T1 branch HEAD verified at `5f6ecd879ce25426cfd31d39fb4282acce7a1a76`.
- Current exact-head CI push run [43144963631](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43144963631), source SHA `5f6ecd879ce25426cfd31d39fb4282acce7a1a76`: collector job **SUCCESS** — `cargo fmt --all --check` PASS; Clippy PASS; release build PASS; collector tests **57/57 library + 1/1 binary PASS**, including the decimal-price collision regression; sidecar writer format/Clippy PASS and offline tests **12/12 unit + 27/27 integration PASS**. Dashboard backend/frontend jobs PASS.
- Exact-head artifact: ID `13910993244`, name `t1-collector-linux-x86_64-5f6ecd879ce25426cfd31d39fb4282acce7a1a76`, size 4,195,579 bytes; GitHub digest `sha256:a32a45a0712c297fc912576e6212b20362da0ac982a9419af68e2b5795d35269`. Downloaded ZIP independently hashes to the same SHA-256. ZIP contains `binance-futures-collector` and `SHA256SUMS`; embedded binary checksum verifies (`8d643b0ba743d21c6917dcabbf26a6f9353aff01c258fac0ae7324d8c46ac8eb`). Binary is ELF 64-bit x86-64.
- Exact-head workflow `43144963631` completed **5/5 jobs SUCCESS**: Collector, Dashboard frontend, Dashboard backend, Docker build, Security audit. Collector fmt/Clippy/release build/tests PASS; collector tests 57/57 library + 1/1 binary; sidecar fmt/Clippy and offline tests 12/12 unit + 27/27 integration PASS. Dashboard frontend/backend and Docker/security jobs PASS.
- Branch API confirms HEAD `5f6ecd879ce25426cfd31d39fb4282acce7a1a76`. PR #1 remains OPEN/DRAFT, unmerged, head SHA matches. Existing PR comment on sidecar manifest publication failure path remains a separate unresolved review finding; do not merge or mark PR ready on this evidence alone.
- **Disposition: exact-decimal order-book price-key correction PASS** at source, full exact-head CI, artifact ZIP digest, and embedded binary checksum levels. Runtime/operational acceptance remains NOT VERIFIED. Quantity calculations still use `f64`; do not claim all order-book arithmetic is exact.
- Next: select the next bounded T1 producer finding for GitHub-only investigation on the existing branch, without changing T0/T2, strategy, risk, lifecycle, or runtime. Keep T1 inactive: no Binance live connection, VPS deployment, or trading.

### T1 order-book quantity decimal preservation — investigation in progress (2026-11-12)

- After exact price-key correction PASS, inspected all Rust source paths for remaining decimal-to-f64 conversions. Relevant live order-book path still parses REST snapshot and WebSocket diff quantities into `HashMap<String, f64>` in `src/collectors/orderbook_manager.rs`; the raw side maps separately retain exact source lexemes for CSV. Current production reads of computational quantity values appear limited; do not claim downstream numerical impact without further evidence.
- Added a focused regression test `computational_orderbook_preserves_exact_quantity_decimal_values` using quantity `1.23456789123456789123456789`. Exact-head run [43147074675](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43147074675) confirmed intended RED: actual `1.234567891234568` vs expected `1.23456789123456789123456789`; 57 library tests passed and this one failed. Format, Clippy, release build PASS; downstream sidecar steps skipped due to test failure. Dashboard frontend/backend PASS; Docker/Security were still running at last poll.
- Implemented the narrow correction in `src/collectors/orderbook_manager.rs`: computational bid/ask quantity values now remain validated decimal strings rather than `f64`; exact zero detection still uses `normalize_plain_decimal`; price-key identity, depth trimming, CSV raw maps and unrelated collector paths are unchanged. Existing assertions/fixtures updated to string values. Implementation commit/current T1 branch HEAD: `dd03ee31a620d80cb006a39faaee6a5ceddaef06`.
- Exact-head CI run [43147426632](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43147426632) is QUEUED at last poll; no GREEN/full-suite result yet. PR #1 remains OPEN/DRAFT, unmerged; runtime remains NOT VERIFIED.
- **Disposition: RED confirmed; fix committed; implementation NOT VERIFIED pending exact-head CI.** Next: poll run `43147426632`, inspect fmt/Clippy/build/tests and all downstream jobs. Do not change T0/T2, strategy, risk, data lifecycle, VPS, or runtime. Keep T1 inactive. Do not change T0/T2, strategy, risk, data lifecycle, VPS, or runtime. Keep T1 inactive.


## T1 order-book quantity decimal preservation — CI PASS (2026-11-12)
- Scope: GitHub-only changes on T1 branch `feature/t1-connection-sidecar-integration-20261107`; no T0/T2, Strategy Core, AI, risk, data lifecycle, VPS, Binance live connection, or runtime changes.
- Implementation: commit `dd03ee31a620d80cb006a39faaee6a5ceddaef06` changed computational order-book bid/ask quantity storage from f64 to exact decimal strings and added regression coverage using quantity `1.23456789123456789123456789`.
- Test-fixture correction: commit `1309473fb30f03e2f720647aa8cb46a96b8aef54` (parent `dd03ee31a620d80cb006a39faaee6a5ceddaef06`) aligned two existing assertions with the exact wire string representation. GitHub branch HEAD and PR head both verified at this SHA.
- Exact-head Push CI [43148312447](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43148312447): SUCCESS, 5/5 jobs PASS (Collector, Security, Docker, Dashboard backend, Dashboard frontend).
- Exact-head PR CI [43148318241](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43148318241): SUCCESS, 5/5 jobs PASS.
- Collector test evidence from job `130951274017`: main library 58/58 PASS, binary/config test 1/1 PASS, doc tests 0; regression `computational_orderbook_preserves_exact_quantity_decimal_values` PASS. Connection sidecar unit tests 12/12 PASS and integration tests 27/27 PASS. Format, Clippy, release build and Docker/security/dashboard jobs passed.
- Artifact: ID `13912927151`, name `t1-collector-linux-x86_64-1309473fb30f03e2f720647aa8cb46a96b8aef54`, size 4,195,215 bytes, GitHub ZIP SHA-256 `7c8ed301b7d6325a123fb827da3c17e2dd2717f86fbaa79a8555cbd9d015ca43`. Downloaded ZIP independently and recomputed matching SHA-256. ZIP contains `binance-futures-collector` and `SHA256SUMS`; embedded binary SHA-256 `ad83347fd9b4786480763f60e7613bf03daca8cb5f0f7953f4dce69fe6457da2` verified with `sha256sum -c`. Binary identified as ELF 64-bit LSB PIE x86-64.
- Status: source implementation + CI + artifact integrity = PASS for this bounded decimal-preservation scope. Runtime/operational acceptance remains NOT VERIFIED. This is not approval to activate T1, connect Binance live, deploy VPS, or trade.
- PR #1 remains OPEN / DRAFT / UNMERGED. Existing sidecar manifest-publication failure-path review comment remains unresolved; passing CI does not close that review finding or authorize merge.
- Next: do not merge or activate T1. Preserve the current scope and constraints; await a separate decision on whether to address the outstanding PR review comment or proceed to another bounded T1 GitHub-only task.


### T1 sidecar manifest post-publication failure — source and CI verification (2026-11-12)

- Repository: `kenznguyen/binance-futures-collector`; existing branch: `feature/t1-connection-sidecar-integration-20261107`; PR #1 remains open/draft/unmerged per the latest recorded PR state. No branch or PR was created.
- Re-read PR #1 review thread `PRRT_kwDOVl7azs600IGI`, comment `4500939117`: the comment describes the possibility that manifest hard-link publication succeeds and later temp unlink/directory sync fails while the writer remains appendable. GitHub marks the thread `is_outdated=true`, but `is_resolved=false`.
- Current source at PR head `1309473fb30f03e2f720647aa8cb46a96b8aef54` has blob `crates/connection-sidecar/src/lib.rs` = `0a2c127000ee1c9776b3594e1292b481c42c878c`. `finalize_with_publish()` sets `self.poisoned = true` after validation and before the first filesystem operation, so all finalize I/O failures (including post-hard-link cleanup/sync failures) leave the writer terminal.
- Regression test `post_hard_link_publication_failure_poisons_writer_and_preserves_manifest_consistency` injects an error immediately after successful `fs::hard_link`; it asserts the final manifest exists, a subsequent event append is rejected with `BrokenPipe`, and `validate_capture()` classifies the sidecar/manifest pair as `SealedConsistent`.
- Exact PR-head-triggered CI run [43148318241](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43148318241) completed SUCCESS, 5/5 jobs: collector fmt/Clippy/build/tests; sidecar format/Clippy/offline tests; dashboard frontend/backend; Docker; security. Collector tests 58/58 library + 1/1 binary PASS. Sidecar tests 12/12 unit + 27/27 integration PASS, including the post-hard-link regression and `poisons_writer_when_manifest_publication_fails_closed`. The PR workflow checked out synthetic merge SHA `5f19ce4f654f60de6231d278fc6fec883b35c8ac` (merge of PR head `1309473...` into base `45218c6...`); it is not the PR head SHA itself.
- Exact-head push CI run [43148312447](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43148312447) is recorded as SUCCESS, 5/5 jobs PASS at source SHA `1309473fb30f03e2f720647aa8cb46a96b8aef54`. Artifact ID `13912927151`, ZIP SHA-256 `7c8ed301b7d6325a123fb827da3c17e2dd2717f86fbaa79a8555cbd9d015ca43`; independently downloaded ZIP hash and embedded binary checksum were verified in the preceding T1 increment record.
- **Disposition: source correction + regression test + CI verification PASS for the reported post-publication writer-poisoning failure.** The review thread remains technically unresolved in GitHub metadata (outdated but unresolved); no comment reply or thread-resolution mutation was made in this increment. PR #1 remains OPEN/DRAFT/UNMERGED; do not merge or mark ready based solely on this result.
- Runtime/operational acceptance remains NOT VERIFIED. No Binance live connection, T1 activation, VPS, T0/T2, strategy/risk, lifecycle, or trading changes.
- Next: continue with another bounded GitHub-only T1 source finding or, if explicitly chosen, reconcile the stale review-thread metadata. Keep T1 inactive.


### T1 decimal-path audit — strengthen exact CSV round-trip assertions (2026-11-12)

- Scope: read-only audit of T1 market-data paths at source SHA `1309473fb30f03e2f720647aa8cb46a96b8aef54`; then a test-only update on the existing T1 branch. No production numeric behavior changed.
- Inspected `src/models.rs`, `src/collectors/rest_collector.rs`, `src/collectors/orderbook_manager.rs`, `src/websocket/message_handler.rs`, `src/websocket/connection_manager.rs`, and `src/utils/csv_writer.rs`.
- Finding: no remaining production conversion of market price/quantity strings to `f64` was identified in those inspected paths. The remaining `f64` uses found are operational metrics/timing (WebSocket processing-lag EMA; scheduling/backoff/jitter), not market price/quantity persistence. CSV round-trip tests still parsed stored decimal strings as `f64` and used tolerances, weakening the precision guarantee. `src/collectors/orderbook_manager.rs` also contains an outdated comment saying the order-book uses f64, while the actual `Orderbook.bids/asks` are `HashMap<String, String>`.
- Test-only commit `38fd0caa354406b49471437b8fe9e7fbe6596ef4` updates trade, kline, and open-interest CSV round-trip assertions to exact string equality instead of floating-point parsing/tolerance. No production code changed. Blob `src/utils/csv_writer.rs` = `2dbbeb7a056478311ab16819b536331dd85b6a61`.
- Exact-source Push CI run [43150334194](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43150334194) was observed IN_PROGRESS at last check. Dashboard backend and frontend jobs SUCCESS; collector fmt SUCCESS and Clippy IN_PROGRESS; Docker and Security IN_PROGRESS. No artifact published at that observation. Do not claim full CI PASS until run concludes.
- PR #1 head verified at `38fd0caa354406b49471437b8fe9e7fbe6596ef4`; PR remains OPEN/DRAFT/UNMERGED. No new branch/PR, merge, runtime, VPS, live Binance, T0/T2, strategy/risk, lifecycle, or trading changes.
- Status: decimal-path source audit = PARTIAL (reviewed paths only; not a whole-repository proof); exact CSV assertion change = CI PENDING; runtime acceptance = NOT VERIFIED.
- Next: verify exact-head workflow completion and artifact, then correct the stale order-book comment in a separate minimal commit if still applicable. Keep T1 inactive.


### T1 CSV exact-roundtrip assertions and order-book comment correction (2026-11-12)

- T1 repository: `kenznguyen/binance-futures-collector`; existing branch: `feature/t1-connection-sidecar-integration-20261107`; PR #1 remains OPEN/DRAFT/UNMERGED.
- Test-only CSV exact-string assertion commit `38fd0caa354406b49471437b8fe9e7fbe6596ef4`: exact-source Push CI run [43150334194](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43150334194) completed successfully, **5/5 jobs PASS** (collector fmt/Clippy/build/tests; sidecar format/Clippy/offline tests; dashboard backend/frontend; Docker; security). Artifact preparation/upload steps were skipped; no artifact exists for this run, so payload/artifact verification is NOT AVAILABLE. The earlier six-file decimal-path audit remains PARTIAL, not a whole-repository proof.
- Corrected one stale comment in `src/collectors/orderbook_manager.rs` from claiming f64 storage to accurately state that order-book levels store normalized exact decimal strings for prices and quantities. This is comment-only (1 insertion/1 deletion); no runtime behavior changed.
- Comment correction commit / T1 branch HEAD: `53ffed3979429ed9f28529cf27d6e508f74ba6f2`, parent `38fd0caa354406b49471437b8fe9e7fbe6596ef4`; changed-file blob `bc7978b897fc03d6cefde679e3351e2c717f2123`. Commit API confirms only `src/collectors/orderbook_manager.rs` changed.
- Exact-source workflow for `53ffed3979429ed9f28529cf27d6e508f74ba6f2` is **NOT YET IDENTIFIED/VERIFIED**; no run ID or artifact has been confirmed. Do not infer CI success from the preceding SHA's green run.
- Status: CSV test assertion change = **PASS (CI 5/5)**; stale comment correction = **SOURCE PASS / CI NOT VERIFIED**; decimal-path audit = **PARTIAL**; runtime acceptance = **NOT VERIFIED**.
- Next: locate and verify exact-head CI for `53ffed3979429ed9f28529cf27d6e508f74ba6f2`; if the push workflow did not trigger, do not manually dispatch or rerun without checking workflow policy. Preserve T1 inactive: no VPS, live Binance, T0/T2, strategy/risk, lifecycle or trading changes.


### T1 order-book comment correction — exact-head CI and artifact verification (2026-11-12)

- T1 repository/branch: `kenznguyen/binance-futures-collector` / `feature/t1-connection-sidecar-integration-20261107`; source HEAD remains `53ffed3979429ed9f28529cf27d6e508f74ba6f2`. PR #1 remains OPEN/DRAFT/UNMERGED.
- Exact-source Push CI [43152091765](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43152091765): **5/5 jobs SUCCESS** — collector fmt/Clippy/tests/build, sidecar tests, dashboard backend/frontend, Docker and security. Exact-source PR CI [43152098560](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43152098560): **5/5 jobs SUCCESS**. Both runs identify the same head SHA `53ffed3979429ed9f28529cf27d6e508f74ba6f2`.
- Test evidence from push collector job: main collector **58/58 library tests + 1/1 binary test PASS**; sidecar **12/12 unit + 27/27 integration tests PASS**.
- Artifact ID `13913364179`, name `t1-collector-linux-x86_64-53ffed3979429ed9f28529cf27d6e508f74ba6f2`, size 4,195,215 bytes; GitHub digest and independently downloaded ZIP SHA-256 both `0982c1e6a9b8528cb46ce9338d7513f409d18eb2b483c85513dd8aef4075e79c`. ZIP contains binary plus `SHA256SUMS`; embedded binary checksum independently verified: `ad83347fd9b4786480763f60e7613bf03daca8cb5f0f7953f4dce69fe6457da2`. Binary identified as ELF 64-bit LSB PIE x86-64. This proves artifact integrity/provenance, not runtime acceptance.
- Disposition: order-book comment correction **PASS** (comment-only source change, exact-source Push and PR CI 5/5); artifact integrity **PASS**; CSV exact-string assertions at parent commit remain **PASS**; decimal-path audit remains **PARTIAL**; T1 runtime acceptance **NOT VERIFIED**.
- Next bounded step: continue a repository-wide static audit for market price/quantity `f64` conversions and persistence paths, distinguishing operational timing metrics from market numeric data. Audit only; do not alter runtime behavior until a concrete lossy path and regression case are established. T1 remains inactive; no VPS/live Binance, T0/T2, strategy/risk, data lifecycle, or trading changes.


### T1 decimal-path audit — dashboard read/API boundary finding (2026-11-12)

- Audit source baseline: T1 `kenznguyen/binance-futures-collector`, branch `feature/t1-connection-sidecar-integration-20261107`, exact source SHA `53ffed3979429ed9f28529cf27d6e508f74ba6f2`. Inspected the Rust collector/REST/WebSocket/model/utility paths, dashboard backend and its tests, selected dashboard frontend data consumers, and data verification script. This is a targeted static audit, not a formal proof over every possible runtime path.
- No new production Rust conversion of exchange market price/quantity strings into `f64` was identified in the inspected collector paths. Remaining Rust floating-point usage observed is operational/telemetry (resync timing/backoff, request/WS latency, rates, throughput, CPU/memory, fractional event timestamps) or a test helper; do not classify those as market price/quantity persistence defects.
- **Confirmed downstream precision-loss finding (dashboard only):** `dashboard/backend/server.py` converts raw CSV/JSON price, quantity, candle OHLCV, funding, open-interest, ratio and liquidation values to Python `float` before returning API payloads. Order-book replay/reconstruction also keys bid/ask maps by float prices and applies float quantity updates; merged exports calculate VWAP/liquidation aggregates using float. Frontend API types and replay/chart consumers expect JavaScript `number` and format values with numeric methods. This can round high-precision decimal lexemes and can compromise exact order-book price identity in dashboard-derived views. It does **not** rewrite the producer's source CSV files.
- Evidence locations at this source SHA include `server.py` lines 449-474 (candles), 477-492 (trades), 526-537 (summary), 665-732 (book replay), 745-749 (`_fnum`), 1244-1281 (book series/trade VWAP), 1405-1456 and 1505-1534 (book reconstruction), 1747-1776 and 1827-1853 (replay payload). Frontend examples: `src/lib/api.ts` Candle numeric contract; `src/components/SymbolExplorer.tsx` and `src/pages/Replay.tsx` numeric price/quantity rendering.
- Other observed float usage is operational rather than market-data persistence: `orderbook_manager.rs` resync delays/backoff and test helper; `config.rs` backoff factor; REST/proxy latency and success-rate telemetry; `stats_exporter.rs` system metrics; `gap_registry.rs` fractional Unix event timestamp.
- Disposition: producer-side exact-decimal fixes already merged into current T1 branch history and their exact-head CI/artifact checks remain PASS as recorded above. Repository-wide precision audit = **PARTIAL — dashboard read/API precision-loss finding CONFIRMED**. No dashboard code or API contract changed in this audit. T1 runtime acceptance remains NOT VERIFIED.
- Next bounded step: define the intended dashboard contract for exact market decimals, then add RED regression tests at the backend API/order-book reconstruction boundary before any implementation. Because the current dashboard API and frontend explicitly use numeric fields, changing them to decimal strings (and deciding where approximate numeric conversion is allowed for plotting) is a cross-layer contract change; do not silently alter it as part of producer-only precision work. No VPS/live Binance, T0/T2, strategy/risk, lifecycle, or trading changes.


### T1 overall maturity assessment (2026-11-12)

- Read-only assessment source: T1 repo `kenznguyen/binance-futures-collector`, branch `feature/t1-connection-sidecar-integration-20261107`, HEAD `53ffed3979429ed9f28529cf27d6e508f74ba6f2`; PR #1 OPEN, DRAFT, UNMERGED, 182 commits / 18 changed files. Main project handoff was read before assessment.
- Source/CI maturity: **GOOD for the standalone raw collector**. Current HEAD has exact-source Push CI [43152091765](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43152091765) and PR CI [43152098560](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43152098560), each 5/5 jobs PASS. Collector 58 library + 1 binary tests; sidecar 12 unit + 27 integration tests. Artifact ID `13913364179` and ZIP/binary checksums independently verified (see preceding section).
- Capture capability: the standalone collector documents WebSocket depth diffs, trades, 1m klines and liquidations, plus REST funding, open interest, long/short ratios, taker ratio and mark/index/premium klines. It writes append-only raw CSV, gap events and stats. Order-book snapshot/bridge/update-ID continuity, REST rate limiting/circuit breaker, symbol lifecycle and memory soak evidence are documented. This supports a mature raw-capture codebase, not a canonical data platform.
- Critical integration gap: **no T0 canonical ingestion/adapter or T1→T0 delivery contract is implemented in this repository**. The collector's output is local CSV/JSON files. No evidence in this source tree establishes handoff to T0, canonical normalization, durable cross-layer acknowledgements, or T2 consumption.
- Connection evidence gap: `crates/connection-sidecar` README explicitly says it is a portable offline reference implementation and **not integrated into the upstream collector**. CI tests its isolated writer/validator only; it does not establish live collector connection/heartbeat evidence.
- Data precision gap: Rust producer paths reviewed have exact-decimal fixes and tests, but Dashboard backend converts market decimal strings to Python `float`, reconstructs order books with float price keys/quantities, and emits numeric API values consumed as JS `number`. This downstream display/replay/export precision finding is confirmed; API contract migration is not approved or implemented.
- Runtime/operational gaps: no current T1 runtime acceptance, BTCUSDT-only configuration run, target storage-rate measurement, real Binance reconnect/heartbeat test, end-to-end data coverage reconciliation, or T0/T2 integration test. Historical soak evidence in `docs/SOAK_TEST.md` describes 523-symbol operation over 6.2 days, but it is not current BTCUSDT-only acceptance evidence and does not validate the current sidecar or T0 integration.
- Governance: PR #1 remains DRAFT/OPEN/UNMERGED. The manifest-publication review thread is outdated but still unresolved in GitHub metadata. The feature branch is not protected and has no required status checks configured. CI PASS therefore does not equal merge approval or runtime certification.
- Overall verdict: **T1 standalone collector source = substantially complete / CI-verified; T1 as a layer of the five-layer system = PARTIAL / NOT READY FOR INTEGRATION OR OPERATIONAL ACCEPTANCE**. Do not assign a single percentage because capture source, canonical integration, dashboard precision and runtime acceptance are separate gates.
- Recommended sequence (no implementation authorized by this assessment): (1) approve T1→T0 boundary and raw/canonical ownership contract; (2) design exact-decimal Dashboard/API contract and regression tests; (3) separately approve and integrate connection sidecar with bounded writer worker and durable acknowledgements; (4) create isolated BTCUSDT-only end-to-end tests to T0 with coverage reconciliation; (5) only after explicit approval plan controlled runtime acceptance. Keep current no-VPS/no-live-Binance/no-real-orders posture. No source/runtime/config/branch/PR changes were made in this assessment.


### T1 datatype schema review for independent T1 → T2 ingestion (2026-11-12)

- Main repository: `kenznguyen/btcusdt-telegram-signals2`; active branch `feature/t0-centralized-data-feeder-p1-20261101`.
- T1 source reviewed: `kenznguyen/binance-futures-collector`, branch `feature/t1-connection-sidecar-integration-20261107`, exact HEAD `53ffed3979429ed9f28529cf27d6e508f74ba6f2`.
- Read-only review covered T1 `docs/SCHEMA.md`, `docs/ARCHITECTURE.md`, `docs/ORDERBOOK.md`, `src/constants.rs`, `src/models.rs`, `src/collectors/rest_collector.rs`, and `src/utils/csv_writer.rs`.
- Evidence report: `docs/evidence/T1_DATATYPE_SCHEMA_REVIEW_2026-11-12.md`; created in commit `da3225826b95d89b755e447bca4f259ff6fc241d`. Report readback was verified from GitHub.
- Findings: T1 documents 11 data series / record families. Important unresolved contract items include `orderbooks` datatype vs `depth_updates`/`depth_snapshot` record subtype, missing snapshot group identity, liquidation stable event identity, candle interval/closed-bar semantics, exact arithmetic/rounding for derived values and ratios, decimal lexical grammar, RFC4180 CSV parsing, and explicit schema-version mapping.
- Review disposition: order-book diff/snapshot and liquidation identity remain BLOCKED for schema freeze; trades, candles, funding, OI, ratios and price-index candles have conditional decisions listed in the evidence report. This is not owner approval and does not freeze the schema.
- No T1 source code, T0 contract, T2 code, Dashboard, sidecar, runtime or configuration changed. No tests run. No VPS, live Binance, training, trading, retention, cleanup, or deletion.
- Architecture remains: T0 → T2 through existing Candle Contract v1; T1 → T2 through a separate future adapter. **No T1 → T0 path.**
- Next design gate: resolve order-book record subtype/snapshot grouping and trade/liquidation event identity before proposing a frozen schema contract. Implementation remains unauthorized until explicit owner approval.


### T1 → T2 schema freeze v1.0.0 — 2026-11-12

- Owner approved automatic continuation through completion of schema freeze. This approval is bounded to resolving schema decisions, recording the frozen contract, and updating evidence/handoff. It does not authorize producer or adapter implementation, VPS/runtime, live Binance, trading, T0 mutation, or data deletion.
- Frozen contract: `docs/evidence/T1_T2_SCHEMA_FREEZE_V1_2026-11-12.md`.
- Final schema document commit: `0ec2271bf4a4a9525da447c92c1d5b171203b8ac`; final blob SHA: `0f20078ac536fbef32a847bceccd8dcd1e29e081`. GitHub readback verified, including the decimal grammar and final status section.
- T1 source baseline remains `53ffed3979429ed9f28529cf27d6e508f74ba6f2` on `feature/t1-connection-sidecar-integration-20261107`. Read-only inspection covered models/constants, REST collector, order-book manager, CSV writer, decimal utility, and SCHEMA/ORDERBOOK docs.
- Resolutions frozen: retain `datatype=orderbooks` and use manifest `record_kind`; group snapshots by contiguous same-timestamp/event-type/update-ID row ranges within an immutable file; enforce update-ID continuity and mark gaps; use aggTrade ID for trade identity; use file digest + row ordinal for liquidations because persisted rows lack a stable exchange event ID; define 1m bar-open intervals and require producer closure attestation; preserve source ratios without invented recomputation/rounding; define bounded exact-decimal parsing and RFC4180-compatible CSV parsing; record market-universe provenance and timestamp semantics.
- Explicit limitations frozen into the contract: periodic order-book snapshots are not automatically trusted after continuity gaps; liquidation semantic cross-batch dedup is unavailable in v1; OI notional is indicative because mark-price timestamp is not persisted; current REST price-index bars need manifest closure attestation. These are not hidden as PASS claims.
- Schema status: **FROZEN v1.0.0** for the T1 CSV compatibility profile and T2 interpretation. No T1 producer schema was changed.
- Implementation status: immutable sealed batches/manifest **NOT IMPLEMENTED**; T1 → T2 adapter **NOT IMPLEMENTED**; producer conformance **NOT VERIFIED**. No tests were run in this docs-only freeze increment.
- The previous datatype review's “next design gate: resolve order-book subtype/snapshot grouping and event identity” is superseded by this freeze record.
- Architecture remains T0 and T1 independent; T0 → T2 Candle Contract v1 unchanged; **no T1 → T0 path**. T1 inactive; no VPS, live Binance, trading, T0/T2 strategy/risk changes, retention, cleanup, or deletion.
- Next authorized step: report the schema freeze completion and await a separate implementation scope/approval for contract tests, immutable manifest publication, and T1 → T2 adapter. Do not begin implementation under this schema-freeze approval.


## T1 producer conformance — initial implementation audit (2026-11-12)

Status: **BLOCKED — implementation not started; producer lifecycle prerequisites identified.**

Authorized objective: make T1 producer conform to the frozen T1 → T2 manifest/batch contract v1.0.0. Work is limited to the existing T1 branch and its producer-side publication path. No T1 → T2 adapter is authorized by this task.

Exact reviewed T1 source:
- Repository: `kenznguyen/binance-futures-collector`
- Branch: `feature/t1-connection-sidecar-integration-20261107`
- PR #1: OPEN / DRAFT / UNMERGED
- Source SHA: `53ffed3979429ed9f28529cf27d6e508f74ba6f2`

Findings from read-only source inspection:
1. `RestCollector::start` spawns seven detached long-running REST collector tasks. It retains no JoinHandles and exposes no stop/join operation. Current main shutdown stops WebSocket ingest and drains the message handler, but does not stop/join REST collectors before CSV flush. Therefore a shutdown-time file snapshot cannot yet be proven quiescent.
2. `CsvWriter::flush_all` logs per-file flush errors and continues, then returns `Ok(())`. It cannot currently serve as a fail-closed prerequisite for sealing/publishing.
3. The existing CSV writer appends to daily/hourly paths and does not create immutable, content-addressed batch segments or a T1 market-data manifest. The existing connection sidecar manifest is a separate JSONL connection-lifecycle artifact and is explicitly not integrated with the collector; it is not a substitute for the market-data manifest.
4. The current build/runtime path does not embed an exact source SHA as manifest provenance. CI names artifacts with `github.sha`, but this does not by itself make that identity available to a running collector process.

Required order before producer conformance can be claimed:
- Add deterministic tests for REST-task shutdown/join and strict flush error propagation (TDD RED first).
- Implement stop/join and strict flush without changing CSV row schemas or T0.
- Implement immutable sealed-batch publication and manifest generation with exact source/build identity, symbol-universe digest, file SHA-256/length/row count/timestamp bounds, datatype schema/timestamp semantics, closure attestations and truthful quality/gap states.
- Verify crash/failure paths are fail-closed: no manifest publication for an incomplete or mutating batch; no overwrite/reuse of batch IDs or published paths.
- Run focused and full CI on exact source SHA; inspect artifacts and read back evidence.

Verification:
- Static source inspection only; no code changes, no tests run, no workflow run, no artifact generated in this audit.
- Producer conformance: **NOT VERIFIED / BLOCKED**.
- T1 runtime remains inactive. No VPS, live Binance connection, T0 modification, T1 → T0 path, T2 adapter, strategy/risk changes, trading, deletion, retention, cleanup or compaction authorized.


## T1 producer conformance — lifecycle prerequisite implementation (2026-11-12)

Status: **PARTIAL — code committed; exact-source CI queued; manifest publisher not implemented.**

T1 repository: `kenznguyen/binance-futures-collector`
T1 branch: `feature/t1-connection-sidecar-integration-20261107`
PR #1 remains OPEN / DRAFT / UNMERGED.
Current T1 source SHA: `013e9188823b7ee59dbcf0153dffa518aa2b0e8f`.

Changes on the existing T1 branch:
- Added deterministic REST task-group tests for cancellation and join.
- Added `RestTaskGroup` ownership of all seven REST collector task handles; shutdown aborts and joins each task.
- Main shutdown now stops REST collectors before final CSV flush.
- Added CSV flush aggregation tests and changed `CsvWriter::flush_all` to attempt every buffer but return an error if any flush failed (fail-closed).
- The T1 schema/CSV row formats and T0 are unchanged.

Relevant commits:
- RED tests: `41c1a469202ed70cb9283d1917791498616c48aa`, `dd46916b892b846fc030475e10c276d5a14f99ad`
- Implementation: `cc5419a3083d59830d3c7c5b21b681efa37ab3c9`, `eea35508aae6182baf017eca1379c311fa4d21a8`, `57dc9738193eb39eed6e7a240694993c5fb1537a`, `ab029ca3dd7feb0d836d38203eb8e8fa705e6621`
- Test formatting/assertion follow-ups: `9c33d635375189e5e2e754b8d0976eddcc62f5c9`, `013e9188823b7ee59dbcf0153dffa518aa2b0e8f`

CI:
- Exact-head push workflow [43158622441](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43158622441), run #337, event push, head SHA `013e9188823b7ee59dbcf0153dffa518aa2b0e8f).
- At handoff update time workflow status was QUEUED; all five jobs queued. No PASS claim is made; exact-source CI is NOT VERIFIED pending completion.
- No artifact result is available yet.

Remaining lifecycle review before sealing:
- CSV writer has detached periodic flush/rotation tasks; GapRegistry has a detached periodic-save task.
- Orderbook manager, WebSocket connection manager, symbol discovery and stats exporter also have background tasks. Their shutdown ownership/order must be audited so no producer can mutate a segment or gap file after its manifest is sealed.
- Therefore this change only closes the REST-task and flush-error gaps; it does not yet establish global producer quiescence or immutable batches.

Next:
1. Verify workflow 43158622441 and correct any exact-source CI failures.
2. Add lifecycle ownership/stop/join for remaining producer-side writers and collectors, with tests.
3. Implement immutable sealed batch + manifest publisher only after the full write graph can prove file closure.
4. Test crash/failure atomicity, digest/length/row-count/timestamp bounds, source/build identity and schema conformance.

Constraints remain: no T1 → T0; T0 unchanged; no T1 → T2 adapter; no VPS/live Binance/runtime activation; no real orders/trading; no deletion, retention, cleanup or compaction.


## T1 producer conformance — exact-head CI correction and expanded lifecycle audit (2026-11-12)

- Previous exact-head CI run [43158622441](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43158622441), source SHA `013e9188823b7ee59dbcf0153dffa518aa2b0e8f`, failed at the Rust `Format` step only. Retrieved job log confirms rustfmt differences in seven `RestTaskGroup::spawn` call sites in `src/collectors/rest_collector.rs` and one test assertion in `src/utils/csv_writer.rs`. Clippy/build/test were skipped by workflow after format failure; this is not a compile/test result.
- Formatting-only corrections committed on the existing T1 branch:
  - `2cebd9be15ea430b9c50c21b66870548b5f34064` — REST task call formatting.
  - `3b48549494af1a073b73c5d1158a27094581931a` — CSV flush test formatting.
- Current T1 branch HEAD: `3b48549494af1a073b73c5d1158a27094581931a`; PR #1 remains OPEN / DRAFT / UNMERGED.
- Exact-head workflows triggered for current HEAD:
  - Push CI [43159092318](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43159092318) — QUEUED at handoff update.
  - PR CI [43159085950](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43159085950) — QUEUED at handoff update.
  - Runs [43159077413](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43159077413) and [43159071969](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43159071969) are associated with intermediate source SHA `2cebd9be15ea430b9c50c21b66870548b5f34064`; do not use them as final-HEAD evidence.
- Expanded read-only producer lifecycle audit confirms the earlier REST task fix is insufficient to prove quiescence:
  - `CsvWriter::start_periodic_flush` starts three detached tasks (periodic flush, stale-buffer cleanup, midnight cleanup); `start_hourly_rotation` starts another detached task.
  - `GapRegistry::start_periodic_save` starts a detached periodic writer.
  - `OrderbookManager::start` starts detached per-symbol management tasks plus periodic snapshot, live depth update, and stale-symbol cleanup tasks.
  - `main.rs` additionally detaches orderbook-manager startup, stats reporting/export, and symbol discovery tasks. Shutdown currently explicitly stops WebSocket ingest and REST tasks, drains the message handler, flushes CSV and saves gaps, but does not join/stop the full set of background tasks.
- Consequence: **producer quiescence remains BLOCKED**. No immutable segment sealing or manifest publication may start until every task that can mutate market-data, gap, stats, or rotation outputs is tracked/stopped/joined and the shutdown ordering is proven. Do not infer that stopping WebSocket ingest alone stops all in-flight orderbook/REST writers.
- Current disposition: REST task tracking + strict CSV flush implementation are committed; exact-head CI for `3b48549494af1a073b73c5d1158a27094581931a` is **NOT VERIFIED**. Full producer lifecycle control, immutable batch/manifest publisher, and schema conformance tests remain **NOT IMPLEMENTED / NOT VERIFIED**.
- Next: verify exact-head CI; then add TDD coverage and task ownership/shutdown for CSV background tasks, GapRegistry, OrderbookManager, WebSocket manager, discovery, stats, and startup orchestration. Re-audit all write paths before implementing immutable sealed batches.
- Boundaries unchanged: T0 and T1 remain independent (no T1→T0); T0 unchanged; no T1→T2 adapter; no VPS/runtime activation or live Binance; no real orders; no retention/deletion/cleanup/compaction; no strategy/AI/risk changes. Schema v1.0.0 remains frozen.


### T1 producer conformance — second exact-head CI finding (2026-11-12)

- Exact-head Push CI [43159092318](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43159092318) at SHA `3b48549494af1a073b73c5d1158a27094581931a` passed `cargo fmt --all --check`, then failed Clippy because `error` was unused in the `src/utils/csv_writer.rs` import. The failure is directly evidenced by the job log; tests/build did not complete.
- Removed only the unused import in commit `d310b577ad5c3bb8bdf6f63cb12c6044677c1b2f`. No behavioral code changed in this correction.
- Current T1 HEAD: `d310b577ad5c3bb8bdf6f63cb12c6044677c1b2f`.
- Exact-head CI for this SHA:
  - Push run [43159224062](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43159224062) — QUEUED at this update.
  - PR run [43159218481](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43159218481) — IN_PROGRESS at this update.
- Disposition: formatting correction validated by the prior CI at parent SHA; Clippy finding fixed in source, but exact-head Clippy/build/tests/security/artifact remain **NOT VERIFIED** pending these runs.
- Lifecycle audit remains **BLOCKED** as stated above: periodic CSV tasks, GapRegistry saver, orderbook manager, WebSocket internal tasks, stats exporter, symbol discovery and startup orchestration are not yet under a single provable stop/join barrier. No batch sealing or manifest publisher work is permitted until that is resolved.


## T1 producer conformance — GapRegistry and CSV task ownership increment (2026-11-12)

Current T1 repository/branch:
- `kenznguyen/binance-futures-collector`
- `feature/t1-connection-sidecar-integration-20261107`
- PR #1 remains OPEN / DRAFT / UNMERGED.
- Current source HEAD: `9fcf73817f1b920760745224ea6d8c0cdb0b5246`.

### CI evidence carried forward
- At parent source SHA `d310b577ad5c3bb8bdf6f63cb12c6044677c1b2f`, PR workflow [43159218481](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43159218481) completed SUCCESS; its collector fmt/clippy/test job passed. This is parent-SHA evidence only, not verification of current HEAD.
- Push workflow [43159224062](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43159224062) at the same parent SHA showed collector fmt/clippy/test SUCCESS; security and Docker jobs were still in progress at last check.
- A later intermediate SHA `66c93af883a5850988e528c9efd9cd01a2775e65` failed only the Rust format gate due one extra blank line in the newly added CSV test; the line was corrected in current history.
- Exact-head workflows for current SHA `9fcf73817f1b920760745224ea6d8c0cdb0b5246`:
  - Push [43159794469](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43159794469) — QUEUED at update.
  - PR [43159787695](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43159787695) — QUEUED at update.
- Current exact-head CI, including compile/tests/clippy/security/Docker/artifact, remains **NOT VERIFIED**.

### GapRegistry corrections
- Added regression coverage for aggregated save failures and shutdown flush/join:
  - Test commit `bb3109ee391dfe17092ca6cb2c6e82cad626eb70`.
  - Lifecycle test commit `06bbef43a92edf823a797b53aa98ac05bc186d9b`.
- Implemented `collect_failed_gap_saves`: failed symbol names and errors are aggregated instead of silently returning success.
- `save_all_dirty` now re-adds failed symbols to the dirty set so the next periodic/final save can retry; any failed save returns Err.
- Periodic saver now retains a JoinHandle and uses a watch shutdown signal. `GapRegistry::shutdown` signals stop, joins the periodic task, then performs a final dirty save.
- Main shutdown calls GapRegistry shutdown rather than directly invoking save_all_dirty.
- Relevant commits:
  - `23692797df1c62f33cfb8e7034b36d010daae3ce` — aggregate failures and retry failed symbols.
  - `115583aade910239efd9bc23f097494c8a0741d9` — own/join periodic saver.
  - `af12024bb702895da149027aa71c9e7c6409ab49` — call GapRegistry shutdown in main.
- Note: the new tests have not yet passed exact-head CI. The test-only intermediate workflow first stopped at rustfmt, so do not claim a completed TDD RED execution.

### CSV background task ownership
- Added a regression test requiring all periodic CSV tasks to be joined during shutdown (`1977d846f14f9b9cddc327329419436def71ec89`).
- CSV writer now retains handles for periodic flush, stale-buffer cleanup, UTC-midnight cleanup and hourly depth rotation; each task observes a watch shutdown signal and exits cooperatively.
- Added `CsvWriter::shutdown_background_tasks` to signal, join all handles, and propagate join failures.
- Main shutdown now stops CSV background tasks before the final `flush_all`.
- Relevant commits:
  - `c1337a75c1d17de3fa4bcae2e94b98b6fabec180` — own and join CSV background tasks.
  - `9fcf73817f1b920760745224ea6d8c0cdb0b5246` — stop CSV tasks before final flush.
- This closes only CSV periodic-task ownership. It does not prove global quiescence because OrderbookManager, WebSocket, symbol discovery, stats exporter and startup orchestration still contain detached tasks.
- Shutdown ordering is still incomplete: OrderbookManager may continue writing CSV/gap events until its own tasks are stopped. The next implementation step must establish an OrderbookManager stop/join barrier before CSV and GapRegistry finalization.

### Current status
- REST task tracking: implemented, exact current HEAD not verified.
- CSV flush fail-closed: implemented, exact current HEAD not verified.
- GapRegistry save error propagation/retry: implemented, exact current HEAD not verified.
- GapRegistry periodic task join: implemented, exact current HEAD not verified.
- CSV periodic task join: implemented, exact current HEAD not verified.
- OrderbookManager/WebSocket/discovery/stats global lifecycle: **BLOCKED / NOT IMPLEMENTED**.
- Immutable sealed batches and market-data manifest publisher: **NOT IMPLEMENTED**.
- Producer conformance v1.0.0: **NOT VERIFIED**.

Next: verify exact-head CI for `9fcf73817f1b920760745224ea6d8c0cdb0b5246`; then implement/test OrderbookManager and WebSocket task ownership, retain and join startup orchestration, and stop discovery/stats tasks. Do not seal or publish a manifest until every writer is quiescent and final CSV/gap flushes have succeeded.

Boundaries unchanged: T0 and T1 remain independent (no T1→T0); T0 unchanged; no T1→T2 adapter; no VPS/runtime activation or live Binance; no real orders; no deletion/retention/cleanup/compaction; no strategy/AI/risk changes. Frozen schema v1.0.0 must not be modified.


## T1 producer conformance — OrderbookManager and WebSocket shutdown ownership (2026-11-12)

- Current T1 source HEAD: `7743377df75c392c78c1b86628dc9dc5dfb0c1cc`.
- Existing T1 branch retained; PR #1 remains OPEN / DRAFT / UNMERGED.
- OrderbookManager now retains JoinHandles for per-symbol `manage_symbol` tasks, periodic snapshot, live depth update, and stale-symbol cleanup. Its shutdown aborts and joins every retained task.
- Main now retains the OrderbookManager startup orchestration JoinHandle, stops/joins that startup task before signaling WebSocket shutdown, then joins REST and OrderbookManager tasks before stopping CSV background tasks, final CSV flush, and GapRegistry final save.
- WebSocketManager now retains JoinHandles for both route connections per batch and heartbeat monitor; global watch shutdown wakes reconnect/backoff waits; `run_connection` selects shutdown against connection/reconnect waits; ping timer is explicitly aborted and joined; shutdown awaits connection and heartbeat tasks.
- Main now awaits WebSocketManager shutdown before the message-handler drain.
- Regression coverage added for OrderbookManager task abort/join helper and WebSocket task join helper.
- Relevant commits:
  - `796a1165cbcb783ccb4d6a6ffaa44411d94e0b08` — OrderbookManager task ownership.
  - `a09dd8ac16e5e4f280b559f5cc3dcb974f0d36c7` — main startup orchestration and manager shutdown ordering.
  - `035cc31463ecb9b84cf08d9598f0eedda7b352b2` — WebSocket route/heartbeat task ownership and shutdown signal.
  - `7b1d017a915d0c4b45f0d6509b9a25c7bcc1d2df` — main awaits WebSocket shutdown.
  - `7743377df75c392c78c1b86628dc9dc5dfb0c1cc` — WebSocket join regression test.
- Exact-head CI for SHA `7743377df75c392c78c1b86628dc9dc5dfb0c1cc`:
  - Push [43160304859](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43160304859) — QUEUED.
  - PR [43160298716](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43160298716) — QUEUED.
  - No test/build/pass claim is made for this SHA; **NOT VERIFIED**.
- Remaining detached tasks in `main.rs`: periodic stats report, StatsExporter, and periodic symbol discovery. StatsExporter writes to the separate stats output; discovery mutates symbol lifecycle state. Retain/stop/join these tasks before claiming all-process quiescence. Also audit any internal spawned tasks not yet captured by WebSocket/OrderbookManager task groups.
- Lifecycle caveat: OrderbookManager currently aborts and joins its worker tasks; this is a bounded stop barrier but needs exact CI and focused tests. The full system is not yet proven quiescent because stats/discovery and any untracked nested tasks remain.
- Current disposition: REST, CSV, GapRegistry, OrderbookManager and WebSocket task ownership have implementation changes committed; exact current-head CI is **NOT VERIFIED**. Immutable batches/manifest publisher remain **NOT IMPLEMENTED**. Producer conformance remains **NOT VERIFIED**.
- Next: verify exact-head CI and correct all findings; then retain/stop/join stats report, StatsExporter and symbol discovery tasks; inspect all remaining `tokio::spawn` call sites across producer modules; only after complete quiescence and successful final flushes begin immutable batch and manifest publication.
- Boundaries unchanged: no T1→T0, no T0 changes, no T1→T2 adapter, no VPS/runtime activation/live Binance/trading, no deletion/retention/cleanup/compaction, no strategy/AI/risk changes, schema v1.0.0 frozen.


### T1 producer conformance — final application-owned background tasks (2026-11-12)

- Current T1 source HEAD: `d9870a0247be0d74124ab01979332f7edef26f92`.
- StatsExporter `start` now returns its JoinHandle to main instead of detaching it.
- Main retains and stops/joins StatsExporter, the periodic stats report, and optional periodic symbol discovery task.
- Main shutdown order now includes: stop discovery/stats; abort+join OrderbookManager startup orchestration; signal+join WebSocket route/heartbeat tasks; drain message handler; stop REST; stop+join OrderbookManager workers; stop+join CSV background tasks; final CSV flush; stop+join GapRegistry periodic saver and final gap save.
- Relevant commits:
  - `4396b6eae3bcd58ae7fc222d7bf62355e8c50a70` — StatsExporter returns owned task handle.
  - `d9870a0247be0d74124ab01979332f7edef26f92` — main retains and joins stats/discovery tasks.
- Exact-head CI:
  - Push [43160512168](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43160512168) — QUEUED.
  - PR [43160506604](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43160506604) — QUEUED.
  - Current exact-source CI **NOT VERIFIED**.
- This is still an implementation-level shutdown barrier, not a claim of proven quiescence. Exact CI, focused cancellation/join tests, and source-wide audit of every `tokio::spawn`/spawn_blocking path remain required. In particular, inspect whether any task can spawn nested work not owned by the top-level task group and whether cancellation during in-flight async file/network operations leaves writes in progress.
- No immutable batch or manifest publisher work has started. Producer conformance remains **NOT VERIFIED**. Schema v1.0.0 unchanged.
- Next: wait for exact-head CI, fix compile/format/test findings; perform a source-wide spawn/write-path audit; add deterministic shutdown tests for each owned task group and final persistence ordering. Only then start immutable sealed-batch/manifest implementation.
- Constraints unchanged: no T1→T0, no T0 changes, no T1→T2 adapter, no VPS/runtime activation/live Binance/trading, no deletion/retention/cleanup/compaction, no strategy/AI/risk changes.


### T1 producer conformance — handler drain fail-closed and blocking-write audit (2026-11-12)

- Current T1 source HEAD: `5e38a18682da60c66ed644d88ec9433d196288b5`.
- PR #1 remains OPEN / DRAFT / UNMERGED on the existing branch `feature/t1-connection-sidecar-integration-20261107`.
- Audit found the previous main shutdown path logged a 5-second message-handler drain timeout and continued to REST/orderbook shutdown and final CSV flush. A timed-out JoinHandle was consumed by `timeout`, detached, and the program could proceed to flush while the handler was still capable of writing.
- Added `await_handler_drain`: successful join permits shutdown to continue; handler task failure or timeout returns an error. Main now uses `await_handler_drain(...).await?`, so a drain timeout blocks final CSV and gap persistence instead of logging and continuing.
- Added tests:
  - `handler_drain_timeout_is_an_error_not_permission_to_flush`
  - `handler_drain_completes_successfully_before_final_persistence`
- Commits:
  - `237fce5d5cd8a955d0fe4a8966954ed9812221a4` — add handler drain regression tests.
  - `56f713711dd45486a6c56d3bc1f9d6881178c1d8` — implement fail-closed drain handling.
  - `5e38a18682da60c66ed644d88ec9433d196288b5` — rustfmt correction.
- Exact-head CI for SHA `5e38a18682da60c66ed644d88ec9433d196288b5`:
  - Push [43161941983](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43161941983) — QUEUED at this handoff update.
  - PR [43161948830](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43161948830) — QUEUED at this handoff update.
  - Exact-head fmt/Clippy/build/tests/security/Docker/artifact: **NOT VERIFIED** pending these runs.
- Prior exact-head run on parent SHA `56f713711dd45486a6c56d3bc1f9d6881178c1d8` failed only the Rust format gate because the new assertion needed rustfmt wrapping. Corrected in `5e38a18682da60c66ed644d88ec9433d196288b5`; parent failure is not current-head verification.
- Source-wide audit identified a remaining global-quiescence blocker: CSV writer uses `tokio::task::spawn_blocking` for buffer creation, row writes, depth-buffer mutation, emergency flush and flush/finalize operations. Aborting/joining an async parent task does not cancel an already-started blocking closure. A blocking closure may therefore continue mutating a CSV file after its parent task has been aborted and joined.
- Required next producer-side fix: introduce a CSV-writer-owned in-flight blocking-operation barrier. After all producer tasks and the message handler have stopped, close admission to new blocking writes, await every already-started blocking operation, and only then run final CSV flush. Add deterministic regression coverage proving a blocked/in-flight closure prevents the final flush barrier from completing and no new write can enter after closure.
- This does not authorize changing CSV row/schema contracts. Do not start immutable batch segments or manifest publication until this barrier and exact-head CI pass.
- Current disposition: handler drain timeout is now fail-closed at source level; exact CI is **NOT VERIFIED**. Global producer quiescence remains **BLOCKED** by in-flight `spawn_blocking` work. Immutable segments/manifest publisher remain **NOT IMPLEMENTED**; T1 producer conformance remains **NOT VERIFIED**.
- Constraints unchanged: T0/T1 independent; no T1→T0; no T0 edits; no T1→T2 adapter; no VPS/runtime activation/live Binance/trading; no deletion/retention/cleanup/compaction; no strategy/AI/risk changes; schema v1.0.0 frozen.


### T1 CI follow-up — regression-test visibility corrections (2026-11-12)

- T1 current HEAD: `31f66142d4ee65987cbe531f5f9a3d97aaf99c54`.
- On parent SHA `5e38a18682da60c66ed644d88ec9433d196288b5`, exact-head push run [43161941983](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43161941983) and PR run [43161948830](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43161948830) passed Format and failed Clippy. Clippy exposed two test visibility errors:
  - CSV shutdown regression test referenced `test_writer` from a sibling test module.
  - WebSocket shutdown regression test referenced `join_websocket_tasks` without importing the private helper into its test module.
- Corrections:
  - `fab87b37c5068c41f43cde11dc8c507c858dc010` — added a local test helper to the CSV test module.
  - `31f66142d4ee65987cbe531f5f9a3d97aaf99c54` — imported the WebSocket join helper into its test module.
- Exact-head workflows for SHA `31f66142d4ee65987cbe531f5f9a3d97aaf99c54`:
  - Push [43162106634](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43162106634) — IN_PROGRESS at update; Format PASS, Clippy IN_PROGRESS; Dashboard frontend/backend PASS; Security and Docker IN_PROGRESS.
  - PR [43162112374](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43162112374) — QUEUED at update.
  - Exact-head full CI/artifact: **NOT VERIFIED**.
- No schema/CSV contract changes. No T0 changes, adapter, runtime, VPS or trading activity.
- Global quiescence remains **BLOCKED** on a CSV-writer-owned in-flight `spawn_blocking` admission/drain barrier. The handler timeout fail-closed change is in the current source history but its exact-head test result is pending.
- Next: complete exact-head CI and fix any findings; then implement and test the CSV blocking-operation barrier before final flush. Do not begin immutable batch or manifest work before that barrier is proven.


### T1 follow-up — symbol-discovery option type correction (2026-11-12)

- Current T1 HEAD: `9d9d9f29a8b2d801d2c2d7b3fa45121cd1320599`.
- On parent SHA `31f66142d4ee65987cbe531f5f9a3d97aaf99c54`, exact-head push run [43162106634](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43162106634) passed Format but Clippy/compile failed because the optional symbol-discovery branch returned a bare `JoinHandle` while the whitelist branch returned `None`.
- Corrected in commit `9d9d9f29a8b2d801d2c2d7b3fa45121cd1320599` by wrapping the spawned task in `Some(...)`; this preserves the intended optional task ownership and does not change data contracts.
- Exact-head PR workflow [43162245242](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43162245242) — QUEUED at this update. Exact-head push workflow not yet visible at this update. CI remains **NOT VERIFIED**.
- No code changes to T0, frozen schema, CSV row schema, data transport, strategy or risk. T1→T2 adapter remains out of scope.
- Remaining blocker is still the CSV writer's in-flight `spawn_blocking` operation barrier; do not proceed to immutable segments or manifest publication before it is closed and tested.


### T1 producer conformance — test visibility fixes and symbol discovery handle type finding (2026-11-12)

- T1 PR #1 remains OPEN / DRAFT / UNMERGED. Existing branch retained.
- The two Clippy compile errors seen at SHA `5e38a18682da60c66ed644d88ec9433d196288b5` were corrected:
  - CSV background-task shutdown test now defines its own local `test_writer` helper within the test module.
  - WebSocket shutdown test imports `join_websocket_tasks` into its test module.
- Commits:
  - `fab87b37c5068c41f43cde11dc8c507c858dc010` — fix CSV test helper scope.
  - `31f66142d4ee65987cbe531f5f9a3d97aaf99c54` — import WebSocket join helper in test module.
- CI at SHA `31f66142d4ee65987cbe531f5f9a3d97aaf99c54`:
  - Push run [43162106634](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43162106634): Rust format PASS; Clippy FAIL; build/tests/artifact skipped.
  - PR run [43162112374](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43162112374) was still running at the time of this update.
  - Clippy log showed a separate compile error in `src/main.rs`: `symbol_discovery_join` if branch returned a bare JoinHandle while else branch returned `None` (expected `Option<JoinHandle<_>>`).
- Current T1 PR head subsequently advanced to `9d9d9f29a8b2d801d2c2d7b3fa45121cd1320599`, commit message `Wrap optional symbol discovery task handle`. This is the current source SHA observed during this update; the commit's change has not yet been accepted as CI PASS.
- Exact-head CI at SHA `9d9d9f29a8b2d801d2c2d7b3fa45121cd1320599`:
  - Push [43162239707](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43162239707): Dashboard Backend PASS, Dashboard Frontend PASS; collector fmt/Clippy/test, Security and Docker were still in progress at last check.
  - PR [43162245242](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43162245242): Dashboard Backend PASS, Dashboard Frontend PASS; collector fmt/Clippy/test, Security and Docker were still in progress at last check.
  - These workflows are associated with exact current HEAD but are not complete; overall exact-head CI **NOT VERIFIED**.
- In-flight `spawn_blocking` remains the global quiescence blocker described above. Need a writer-owned admission-close/in-flight-operation barrier before final CSV flush. Do not start immutable segments or manifest publisher.
- Status: test visibility fixes committed; symbol discovery optional-handle correction committed at latest head but CI pending; producer quiescence **BLOCKED**; immutable batch/manifest **NOT IMPLEMENTED**; T1 producer conformance **NOT VERIFIED**.
- Boundaries unchanged: T0/T1 independent; no T1→T0; no T0 changes; no T1→T2 adapter; no VPS/runtime/live Binance/trading; no data deletion/retention/cleanup/compaction; no strategy/AI/risk changes; schema v1.0.0 frozen.


### T1 producer quiescence — CSV blocking-operation barrier (2026-11-12)

- T1 repository: `kenznguyen/binance-futures-collector`; existing PR #1 remains OPEN / DRAFT / UNMERGED on branch `feature/t1-connection-sidecar-integration-20261107`. No new branch or PR.
- Baseline PR head `9d9d9f29a8b2d801d2c2d7b3fa45121cd1320599`; prior exact-head CI run `43162239707` (push) and `43162245242` (PR) remained IN_PROGRESS at last observation; they are not promoted as PASS.
- TDD regression test added first. RED confirmed at test source `4b804517d3589488d124b6d203af721842a97ff9`, PR workflow `43169296398`, collector job `131018425726`: compile errors for missing blocking-operation tracker and post-shutdown final-flush method. Earlier test-only run `43169186884` failed at rustfmt and was corrected in `4b804517...`.
- Implementation commits: `fed559870b73c76c0a4bdc12143d6d92983eb7b6` adds shared admission/in-flight tracking to all four ordinary `spawn_blocking` call sites, closes admission and drains after CSV background-task joins, and provides a guarded final-flush path; `d9958122ecc3319cb3a2da47020901478f24cbe6` switches main shutdown to that final-flush path; `8bfe1cbee61dd3cf47d4c7bc414a7eb0758d078f` corrects rustfmt; `f64419dd3e4a9d64dbd4281f206f1a8b2c5637db` scopes the test-only admission probe to test builds to satisfy Clippy.
- Current T1 PR head: `f64419dd3e4a9d64dbd4281f206f1a8b2c5637db`. PR workflow run `43169863860`: Format PASS, Clippy PASS, Build PASS; Test IN_PROGRESS; Dashboard frontend/backend, Security and Docker PASS at last observation. This is PR-triggered validation; synthetic merge checkout SHA and exact-head push result are NOT VERIFIED. No artifact verified yet.
- No CSV/schema/manifest contract changes; no T0/T1 integration, T1→T0, T1→T2 adapter, VPS/runtime, Binance live connection, retention/deletion, strategy/risk or trading changes.
- **Disposition: TDD RED CONFIRMED; source barrier implementation COMMITTED; CI PARTIAL / NOT VERIFIED; global producer quiescence remains BLOCKED until exact-source tests and all required CI jobs complete successfully.**
- Next: poll run `43169863860`; inspect test results, sidecar checks and artifact provenance. Do not begin immutable segments or manifest publication until the barrier and exact-head CI are verified.


### AI Ledger CANCEL — RED contract and integrity boundary (2026-11-12)

- Scope: test-only work on the existing branch `feature/t0-centralized-data-feeder-p1-20261101`. No production source, T0/T1/T2, VPS/runtime, model inference, or trading execution changes.
- Policy fixed for this test phase: an active dual-strategy order with a missing reservation or a reservation whose `strategy_id` / `intent_id` does not match its persisted order must fail closed and roll back. Expiry sweep remains account-wide; only expired reservations from the other strategy may be mutated by housekeeping. A non-expired reservation from the other strategy must remain untouched. Repeated CANCEL must not release or audit twice.
- Tests added/updated: `paper_execution/test_dual_ledger_red.py`, `paper_execution/test_dual_strategy_api_red.py`, `paper_execution/test_dual_ledger_migration_red.py`, and `pipeline/test_core_sizing.py`. Legacy fixtures now supply explicit AI admitted leverage / 3x fixture leverage and use sizes within the AI 1% margin budget.
- Source baseline remains `ef97abec1b832ae553c1f4c1b461ae13073c6628`; no production source files changed. Current branch HEAD: `4efb126748cd77b418c7a117ebd36a5404e9cc5a` (10 test/progress commits ahead, 0 behind baseline).
- Exact-head workflow run `43178245969`, job `131047618684`: Python compile PASS; focused contract FAIL with 0 errors and 5 distinct failing tests (the three new reservation-integrity assertions, AI CANCEL without fresh leverage, and the existing AI evaluate routing test). The reservation expiry scope, non-expired cross-strategy isolation, and repeated-CANCEL idempotency tests pass. Full `paper_execution` regression was skipped because the focused stage failed.
- Evidence artifact: `dual-ledger-red-evidence-4efb126748cd77b418c7a117ebd36a5404e9cc5a`, artifact ID `13925815485`, SHA-256 `d8f5c019ed93cc5d3936fea2c9db725759961b79c09eb2867927806320415a07`; workflow [43178245969](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43178245969).
- Disposition: RED coverage established; current code does not yet enforce reservation/order ownership and API AI CANCEL still attempts AI ledger construction without admitted leverage. AI evaluate also remains a separate unresolved ordering issue (decision/admission must precede ledger construction). **GREEN implementation NOT AUTHORIZED**; no runtime changes.
- Next: implement the narrow CANCEL-only DB transaction path after reviewing the failing assertions and current reservation schema; keep AI evaluate routing as a separate issue. Re-run focused RED/verification and full paper_execution regression. Do not change T0/T1/T2 or enable live execution.



### AI Ledger CANCEL — transaction-path source review (2026-11-12)

- Read-only review baseline/source HEAD: `d16f29e5d98a5d9019e207a5e3e0b90663fd7003`; preceding RED test HEAD: `4efb126748cd77b418c7a117ebd36a5404e9cc5a`. Branch remains `feature/t0-centralized-data-feeder-p1-20261101`; no branch/PR split.
- Exact reviewed blobs:
  - `paper_execution/ledger.py`: `84597a8815c62bcddaa63fd3d2fcd890510931b6`
  - `pipeline/api.py`: `835a17dd062a2494f1adce981b7f411167afbf45`
  - `paper_execution/test_dual_ledger_red.py`: `f612c5454ad878511f80136ed565acd4296ed2a0`
  - `paper_execution/test_dual_strategy_api_red.py`: `e6c32e6897ed3b303954a0f114be247e21dbef38`
- Review report: `docs/evidence/AI_LEDGER_CANCEL_TRANSACTION_PATH_SOURCE_REVIEW_2026-11-12.md`; report blob `be4b9d688a6c01307dcbb1857cd679f1e9f749d4`; report commit `8ed48923454dca8307671e2e3b352d97273b91db`.
- Required findings: (R1) active dual order may be canceled when reservation row is missing; (R2) reservation intent/strategy/account identity is not checked against persisted order; (R3) AI CANCEL constructs an AI PaperLedger and fails because fresh admitted leverage is required; (R4) owner is read outside the cancellation write transaction; (R5) account-wide expiry sweep also lacks exact reservation/order identity validation.
- Existing schema already stores the required order/reservation identity fields; no migration is indicated. Recommended future shape is one CANCEL-only transaction helper shared by API and direct dual-ledger calls, with owner resolution, exact order/reservation checks, account-wide expiry validation, guarded release, one audit event and rollback on any mismatch. Do not inject fake leverage or invoke AI prediction/calibration for CANCEL.
- AI evaluate ordering remains a separate unresolved issue; do not fold it into CANCEL remediation or weaken the AI leverage policy.
- Five-axis review verdict: correctness REQUEST CHANGES; readability CONDITIONAL PASS; architecture REQUEST CHANGES; security/integrity REQUEST CHANGES; performance CONDITIONAL PASS (expiry sweep currently scans all ACTIVE/PARTIAL rows rather than selecting expired rows via the existing index).
- Verification: this was static/read-only review only; tests/compile NOT RUN in this increment. Prior RED workflow remains run `43178245969`, job `131047618684`, compile PASS and focused RED as recorded above. No production source, schema, API, workflow, runtime, VPS, T0/T1/T2 or live trading change.
- **Disposition: REVIEW COMPLETE — REQUIRED FINDINGS OPEN; GREEN CANCEL IMPLEMENTATION NOT AUTHORIZED.**
- Next gate: explicit Owner approval of exact implementation files, helper/API integration boundary, regression matrix and focused/full test commands. Preserve RED tests until approval. Do not modify production source or runtime before that gate.


### AI Ledger CANCEL — approved GREEN implementation, focused CI partial (2026-11-12)

- Owner approval received in chat for the bounded CANCEL-only implementation. Scope remained `paper_execution/ledger.py`, `pipeline/api.py`, `paper_execution/test_dual_ledger_red.py`, and `paper_execution/test_dual_strategy_api_red.py`; work committed on the existing branch `feature/t0-centralized-data-feeder-p1-20261101`.
- Exact tested source/branch HEAD: `81b408a423be1b3c60fe0489db494a8895d70c47`. Branch comparison against the prior review HEAD `d16f29e5d98a5d9019e207a5e3e0b90663fd7003`: ahead 16, behind 0. No branch or PR split.
- Exact final source blobs at tested HEAD:
  - `paper_execution/ledger.py`: `37c0aeb9dd28514dd19b87667b762c5592baf61f`
  - `pipeline/api.py`: `c247b07a1915e5090b218aa036230c898f9a9b78`
  - `paper_execution/test_dual_ledger_red.py`: `2c2104ada5743cbf55f64c8bc9690a14142fe3e0`
  - `paper_execution/test_dual_strategy_api_red.py`: `563bce930baf4febc78335a2eb75ef7d96e1570f`
- Implementation: introduced `cancel_dual_order()`, a CANCEL-only SQLite `BEGIN IMMEDIATE` transaction. API no longer pre-reads owner or constructs a strategy ledger for dual-schema cancellation. Direct Core/AI ledger calls retain expected-owner scope. AI CANCEL does not require prediction, calibration, confidence or newly admitted leverage. MANUAL cancellation on dual-schema DBs retains a compatibility branch.
- Transaction checks: persisted order/document identity and status consistency; reservation ID, intent ID, strategy ID and account ID exact match; active order requires an active/partial reservation; guarded order/reservation updates require one affected row; release sets remaining margin/notional to zero and selects RELEASED/CONSUMED based on filled quantity; CANCEL audit is written in the same transaction. Account-wide expiry sweep uses the expiry index, detects malformed non-null expiry values, validates each reservation against its order before mutation, and rolls back all changes on mismatch. Non-expired cross-strategy reservations remain untouched; repeated CANCEL is idempotent.
- Regression additions: missing reservation row and ID, wrong strategy/intent/account, order-document owner mismatch, expiry-sweep mismatch rollback, audit-trigger failure rollback, API cancel-only helper path and no AI ledger construction. Existing Core/AI cancellation and cross-strategy scope tests retained.
- Exact-head GitHub Actions run `43182313512`, job `131061349945`, checked out exactly `81b408a423be1b3c60fe0489db494a8895d70c47`: paper-only preflight PASS; compile PASS; focused suite ran 261 tests with 1 failure and 0 errors. All CANCEL-specific cases passed, including AI cancel without new leverage, missing reservation, strategy/intent/account mismatch, document mismatch, expiry rollback, audit rollback, idempotency and Core/AI owner scope. The only focused failure is the pre-existing separate `test_ai_buy_while_core_wait_routes_only_to_ai_ledger_and_shared_risk_rejects` (API returns 400 instead of expected 200); do not fold its AI evaluate ordering issue into CANCEL remediation.
- Full `paper_execution` regression was skipped because the focused stage failed. Overall validation: compile PASS; CANCEL-focused coverage PASS; combined focused suite PARTIAL/BLOCKED by separate AI evaluate test; full regression NOT RUN.
- Artifact: `dual-ledger-red-evidence-81b408a423be1b3c60fe0489db494a8895d70c47`, ID `13926976242`, SHA-256 `106913edf5cc0113a011a35b61aa6ec0c505430501e0bd49561d958455ce91b5`; expires `2026-11-19T08:21:49Z`. Workflow: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43182313512
- No schema migration, T0/T1/T2, VPS/runtime, deployment, model inference, live trading or real-order changes. `AI_EXECUTION_ENABLED=false` remains unchanged.
- **Disposition: CANCEL implementation COMMITTED; CANCEL-specific CI assertions PASS; broader validation PARTIAL; do not enable live execution.** AI evaluate remains a separate blocker. Next: address the isolated AI evaluate decision/admission/leverage/ledger construction ordering in its own approved workstream, then rerun the full focused and `paper_execution` regression suites. No runtime activation.


### AI Ledger CANCEL — final focused verification refresh (2026-11-12)

- Added an API regression proving MANUAL order cancellation remains compatible when the dual-ledger schema is active. The test passes on the exact latest validation head.
- Latest branch HEAD and exact workflow checkout: `2f0aa9e0093c5f0b30be9be2c64433e71ebd9110`. Relative to prior review HEAD `d16f29e5d98a5d9019e207a5e3e0b90663fd7003`: ahead 18, behind 0. Existing branch only.
- Final relevant blobs: `paper_execution/ledger.py` `37c0aeb9dd28514dd19b87667b762c5592baf61f`; `pipeline/api.py` `c247b07a1915e5090b218aa036230c898f9a9b78`; `paper_execution/test_dual_ledger_red.py` `2c2104ada5743cbf55f64c8bc9690a14142fe3e0`; `paper_execution/test_dual_strategy_api_red.py` `0d3b4ec1e1d5a52c70154bfb20b43613a703b04e`.
- Latest exact-head workflow run `43182680232`, job `131062244043`: paper-only preflight PASS; compile PASS; focused suite ran 262 tests, 1 failure, 0 errors. All CANCEL-specific tests PASS, including AI cancel without newly admitted leverage, missing reservation row/ID, wrong strategy/intent/account, document mismatch, expiry rollback, audit rollback, repeated CANCEL idempotency, Core/AI direct owner scope, API helper route and MANUAL compatibility. The sole failure remains the separate pre-existing `test_ai_buy_while_core_wait_routes_only_to_ai_ledger_and_shared_risk_rejects` (HTTP 400 instead of expected 200); no CANCEL assertion failed.
- Full `paper_execution` regression: SKIPPED by workflow because the combined focused stage has the separate AI evaluate failure. Do not mark full regression PASS.
- Artifact `dual-ledger-red-evidence-2f0aa9e0093c5f0b30be9be2c64433e71ebd9110`, ID `13927261274`, SHA-256 `bfbbc1c5405d7b33c93bd4f5f2de0c6b5e7d413cfc0231b6d44c695ad586fb7b`, expires `2026-11-19T08:24:30Z`. Workflow: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43182680232
- Final status: CANCEL implementation COMMITTED; CANCEL-specific CI PASS; overall focused contract PARTIAL/BLOCKED by separate AI evaluate routing; full regression NOT RUN. No schema, T0/T1/T2, VPS/runtime, deployment or live execution changes. `AI_EXECUTION_ENABLED=false` remains unchanged.
- Next workstream requires separate bounded approval: repair AI evaluate ordering (decision → trusted admission context → admitted leverage → AI ledger → submit) without weakening AI leverage policy. Do not merge that issue into CANCEL changes or enable live execution.


### AI Evaluate Admission Flow — owner auto-approval and initial RED boundary (2026-11-12)

- Owner has authorized autonomous execution of the separate AI Evaluate Admission Flow through completion: Decision → Trusted Admission Context → Admitted Leverage → AI Ledger → Submit. This authorization does not reopen or modify the completed CANCEL workstream and does not authorize T0/T1/T2, VPS/runtime, deployment, live execution, Core strategy or model-training changes.
- Existing branch retained: `feature/t0-centralized-data-feeder-p1-20261101`; no new branch or PR.
- Source baseline before this increment: latest CANCEL-verified HEAD `2f0aa9e0093c5f0b30be9be2c64433e71ebd9110`.
- Test-only commit `87d12e836dcb7f418aa6f143b284cf1b3a5d1c03` adds `test_ai_wait_does_not_construct_ai_ledger_or_require_admitted_leverage` to `paper_execution/test_dual_strategy_api_red.py` (blob `de39b80005ac951d18d86ec258544f716d3646e4`). It asserts that an AI WAIT decision returns HTTP 200 with no order and does not instantiate an AI ledger. This targets the observed current ordering defect: `/v1/paper/evaluate` constructs `ledger(strategy_id="AI_FREQAI")` before Decision, which raises `AI_ADMITTED_LEVERAGE_REQUIRED` even when no trade intent exists.
- Additional source findings at baseline: `api.decide()` does not pass `admission_context` to `pipeline.decision.evaluate()`; the decision function fails closed without that context. `pipeline.calibration_registry.verify_calibration_manifest()` explicitly proves signature/integrity only, not registry promotion/revocation, trusted time, OOS quality or admission. `pipeline.oos_evaluation.validate_oos_evaluation_record()` explicitly returns structural-only evidence with `ai_admission_eligible=false`. Production numerical `C_min` remains unset by the approved AI Strategy contract.
- RED workflow execution for commit `87d12e836dcb7f418aa6f143b284cf1b3a5d1c03`: **NOT VERIFIED** in this update; the GitHub connector exposes PR-associated workflow runs only and returned no run/status for this push commit. Do not claim test failure/pass until an exact-SHA run is retrieved.
- No production source changed in this increment. No AI admission is fabricated from fixture values, no default `C_min` or trust state is selected, and no order/live execution is enabled.
- Current disposition: owner auto-approval RECORDED; API ordering RED test ADDED; exact test execution NOT VERIFIED; trusted-admission production inputs BLOCKED/NOT VERIFIED. Next: obtain exact-SHA RED workflow evidence, then implement the minimum API sequencing fix. Trusted Admission Context may only admit when signature, active registry state, trusted time, OOS evidence and versioned AI policy are genuinely verifiable; otherwise return a blocked/no-intent decision. Keep the existing 1x–3x leverage domain and shared 1% margin gate unchanged.


### AI Evaluate Admission Flow — exact-SHA RED confirmation (2026-11-12)

- Exact source commit tested: `87d12e836dcb7f418aa6f143b284cf1b3a5d1c03`; branch `feature/t0-centralized-data-feeder-p1-20261101`. Workflow `Dual Ledger RED and Migration Contract`, run [43183897962](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43183897962), event `push`, run number 334; job `131066249991` checked out the exact source SHA (checkout log confirms `git rev-parse HEAD`).
- Preflight paper-only isolation: PASS. Python compile: PASS. Focused contract: 263 tests, 2 failures, 0 errors. Full `paper_execution` regression: SKIPPED because focused contract failed.
- Relevant failure 1: `test_ai_wait_does_not_construct_ai_ledger_or_require_admitted_leverage` failed because API called `ledger(strategy_id='AI_FREQAI')` once before returning WAIT. This confirms the test's intended sequencing assertion.
- Relevant failure 2: `test_ai_buy_while_core_wait_routes_only_to_ai_ledger_and_shared_risk_rejects` returned HTTP 400 `INVALID_INPUT` instead of 200. Its fixture patches an AI BUY decision without authentic admission context, so the test currently bypasses the intended trust boundary and must be revised to use a genuine admitted-context fixture only when such a trusted provider exists; do not weaken admission validation to make this test pass.
- Remaining 261 focused tests passed. The two failures are recorded separately; do not claim the entire suite is green.
- Evidence artifact: `dual-ledger-red-evidence-87d12e836dcb7f418aa6f143b284cf1b3a5d1c03`, ID `13927088648`, GitHub-reported ZIP SHA-256 `5b680f8f23b28db5a8fb8d877095a011f829375bfd6943d0dbf82cfd78b79158`, expires `2026-11-19T08:33:17Z`. Artifact metadata digest recorded; payload was not independently downloaded/re-hashed in this increment.
- Workflow file `.github/workflows/dual-ledger-red.yml` blob at branch ref: `8b1620482dabd59d46e6f3f4e7ad66c178e520e8`. It runs on push to this branch when `paper_execution/**`, `pipeline/**`, or the workflow itself changes. This is why the push run exists; the earlier connector-specific lookup was incomplete, not evidence that no run existed.
- This exact-SHA result supersedes the preceding statement that RED execution was NOT VERIFIED. Disposition: **TDD RED CONFIRMED; API ordering defect reproduced; second AI BUY fixture is not a valid admission-positive test; GREEN NOT STARTED**.
- Next: separate the test concerns. Keep the WAIT/no-ledger regression. Rework the AI BUY routing test to use a valid Trusted Admission Context only after an authoritative provider exists. Then implement Decision → Trusted Admission Context → Admitted Leverage → AI Ledger → Submit, with no Ledger construction for WAIT/no intent and no fabricated leverage/context. Trusted registry ACTIVE/revocation, trusted time, OOS eligibility, model/calibration provenance and versioned AI policy including `C_min` remain required blockers. Preserve 1x–3x leverage and 1% margin/shared-risk controls. Do not edit CANCEL, T0/T1/T2, VPS/runtime, Core strategy or enable live execution.
