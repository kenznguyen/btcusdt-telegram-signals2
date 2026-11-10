# Five-Layer System — Session Handoff

Updated: 2026-11-10 (Asia/Ho_Chi_Minh)

> Start here in every new session. GitHub is the source of truth. Read this short file first; consult the [archived handoff history](archive/PROJECT_SESSION_HANDOFF_HISTORY_2026-11-10.md) only when an older decision or evidence record is needed.

## 1. Repository and active work

- Repository: `kenznguyen/btcusdt-telegram-signals2`.
- Active branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Default branch: `main`. Do not switch branches or create a parallel PR without a task-specific reason and approval.
- Latest repository HEAD before this handoff update: `b584cc218833bfa6f5d0345b55639c0448961a8e` (test-first repository-file inventory contract; run #42912485814 has an intentional RED result for the missing implementation module).
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


### Independent readback of run 42916283963 output artifacts (2026-11-11)

- Downloaded all three output ZIPs from run `42916283963` and independently recomputed their byte lengths and SHA-256 values; each matches the GitHub upload digest:
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
