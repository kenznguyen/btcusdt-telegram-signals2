# Five-Layer System — Session Handoff

Updated: 2026-11-11 (Asia/Ho_Chi_Minh)

> Start here in every new session. GitHub is the source of truth. Read this short file first; consult the [archived handoff history](archive/PROJECT_SESSION_HANDOFF_HISTORY_2026-11-10.md) only when an older decision or evidence record is needed.

## Current governance override — 2026-11-11

**Option C — No Destructive Authority: REVOKED by explicit owner instruction on 2026-11-11.** This supersedes every earlier ACTIVE/in-force statement in the historical handoff and lifecycle records. Do not treat Option C as a blanket prohibition. This revocation does not authorize any specific deletion, archive, cleanup, expiry, vacuum, compaction, provider operation or other destructive action. Each concrete action still requires a separately explicit, bounded approval with exact target/data class, scope, preconditions, expected effect, verification and recovery/rollback plan. T0 canonical data, lease/fencing state, ledgers, audit/reconstruction/recovery evidence, owner custody and trust evidence remain protected unless specifically approved. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.


## 1. Repository and active work

- Repository: `kenznguyen/btcusdt-telegram-signals2`.
- Active branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Default branch: `main`. Do not switch branches or create a parallel PR without a task-specific reason and approval.
- Latest repository HEAD before this handoff update: `f58bf6a203e8dd663003eeff97ad7580dcbb9c57` (post-amendment self-review and evidence link recorded; see current A2.2 workstream below).
- Full previous handoff preserved verbatim in `docs/archive/PROJECT_SESSION_HANDOFF_HISTORY_2026-11-10.md`; archive commit: `2fcad94aef8b15002cdba58aafe62ad208dc818b`.
- PR #139 is OPEN / DRAFT / NOT MERGED. It concerns SSH passphrase handling and targets this active branch. Do not merge or alter it as part of unrelated work.

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

## 4. Current workstream — G4 read-only runtime acceptance

**User-approved scope:** bounded read-only runtime inspection only. Do not restart Feeder/API, write or modify canonical SQLite, activate T1, or issue trades/orders.

### Verified evidence

1. **SSH preflight — point-in-time read-only snapshot**
   - Workflow run: [42814402445](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42814402445), SUCCESS.
   - Workflow checkout SHA: `8ad36cae8aa971a537a6f363902f86046aa32e5e`.
   - Remote checkout SHA reported: `9ae2eeae4ece3d657781b68e96b6f4509cd95f24`.
   - Host: `btcquant-t0-t1-test-01`; user: `ubuntu`.
   - Feeder PIDs observed: `22045,22046` (point-in-time only).
   - API 8788: `127.0.0.1:8788`, loopback-only.
   - SQLite integrity: `PRAGMA integrity_check=ok`.
   - Artifact ID: `13762564163`; SHA-256: `f6303919c69b05d412722492f05b8dd3aefa1a655043fa98029a94fee5ee8c28`; expires 2026-11-17.
   - This is not continuous health, candle freshness, lease validity, or data-flow proof.

2. **G4a/G4b disposable CI contracts**
   - Run: [42824628084](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42824628084), SUCCESS.
   - Exact source SHA: `a6d939252f1651c4f8f5478bf49581824cc67cc9`.
   - G1, G2, G3 jobs: SUCCESS.
   - G4 contract job: 34/34 tests PASS, including local WSGI + disposable SQLite integration.
   - SSH preflight and manual VPS acceptance jobs: SKIPPED.
   - G4 artifact ID: `13768391449`; SHA-256: `bafc77c273497e762860b7e39e8b341e5493aaae3e3cbba07e991d7a5179f910`; expires 2026-11-17.
   - These results prove disposable GitHub-runner behavior only, not VPS runtime.

### Current blockers / limits

- G4 VPS runtime: **NOT VERIFIED**.
- Safe installation/invocation path for the new probes: **BLOCKED / NOT VERIFIED**.
- Detailed Flask feeder-health listener and its loopback binding: **NOT VERIFIED**.
- Secure remote source for `MARKET_DATA_TOKEN`: **NOT VERIFIED**. Never place the token in an SSH command, URL, shell history, log, or artifact.
- Deployment-path review: `docs/evidence/G4_RUNTIME_DEPLOYMENT_PATH_REVIEW_2026-11-10.md`, commit `5db0c0acbc2a8e8014671db2cd3015577c083dcb`.
- Existing SSH forced command is a fixed read-only preflight; current workflow has no approved SCP/rsync/installer path or second-probe dispatcher. Do not add general shell access or bypass the forced-command boundary.
- Dispatcher design review: `docs/evidence/G4_FORCED_COMMAND_DISPATCHER_DESIGN_REVIEW_2026-11-10.md`, commit `50c99cf3c71e8d85dddaceeb4f8e604000a254c5`. Target contract documented; implementation NOT STARTED.

### Next permitted step

Obtain the bounded owner-supplied deployment evidence described in `docs/evidence/T0_OWNER_READONLY_DEPLOYMENT_EVIDENCE_PROTOCOL_2026-11-10.md`, especially the effective forced-command entry and root-owned update path, with secrets redacted. This is a documentary evidence step; it does not require probe installation or a new remote command.

The dispatcher target design is recorded in `docs/evidence/G4_FORCED_COMMAND_DISPATCHER_DESIGN_REVIEW_2026-11-10.md`. Reassess implementation only after the installed command path, root-owned update mechanism, secure token source, and any claimed Flask listener are evidenced. Obtain separate approval for the exact implementation and risk boundary before any VPS installation or new remote invocation. Existing G4 scope approval does not authorize a new installation mechanism or wider SSH access.

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
- A1 remains DRAFT / NOT FROZEN pending final consistency verification and qualifying independent review. The prior static consistency review is not an independent review. Production algorithm/profile, root ceremony, signer/anchor identities, anchor concurrency and trusted-time/TSA decisions remain open.
- No implementation, code/test/workflow/CI, key generation/signing, trust-root/policy/anchor instance, provider, VPS/SSH/runtime, SQLite or canonical T0 data operation was performed or authorized. No destructive action was authorized.
- Next permitted step: re-read the amended contract, A1 and crosswalk for exact consistency; then request a qualifying independent review of the frozen contract and negative-verification test matrix. Implementation remains blocked pending that review and a separate explicit approval.


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

- Second static pass appended to the baseline report; latest report blob: `743a752e7b27cf67f0ac06b3dadd9a286fb642f1`; addendum commit: `d8b164d682c828d7a53c2051afc7ec487e2afae9`.
- Expanded DS-01:
  - `/v1/paper/cancel` uses the MANUAL ledger instance; the MANUAL compatibility path rejects cancellation of Core/AI-owned orders.
  - `/v1/equity` and the evaluate route use MANUAL `record_equity()`, which records legacy `paper_state` equity, not account-scoped dual-ledger mark/equity reconciliation.
  - A dedicated account-level mark/equity update and strategy-scoped cancellation path are required; account risk readiness must remain fail-closed until then.
- Acceptance mapping now includes scoped ENTRY/DCA/EXIT, owner-scoped cancellation, explicit Core/AI read models, account aggregate equity/funding/reservation reconciliation, and atomic account-wide Kill Switch admission behavior.
- Static-only; no endpoint/test execution, source code, workflow, VPS/runtime, DB or ledger mutation.
