# Five-Layer System — Session Handoff

Updated: 2026-11-10 (Asia/Ho_Chi_Minh)

> Start here in every new session. GitHub is the source of truth. Read this short file first; consult the [archived handoff history](archive/PROJECT_SESSION_HANDOFF_HISTORY_2026-11-10.md) only when an older decision or evidence record is needed.

## 1. Repository and active work

- Repository: `kenznguyen/btcusdt-telegram-signals2`.
- Active branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Default branch: `main`. Do not switch branches or create a parallel PR without a task-specific reason and approval.
- Latest repository HEAD before this handoff update: `306645446ed1d4a5eacf1f84ac18337b6acbfc72` (L4 source-reference reconciliation).
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
- Evidence register: `docs/evidence/T0_L4_MINIMUM_NINE_CONTROL_EVIDENCE_ACQUISITION_REGISTER_2026-11-10.md`, updated in commit `0ca4c3f7427f81d7adb3e382e5603cb87b6dcad6`, blob `cee949666da611a4efca7e7b51aea47ab4b13eff`.
- Supporting references reconciled in commit `306645446ed1d4a5eacf1f84ac18337b6acbfc72`: policy/historical reconciliation blob `017bca148719006b22431d6eafa383fe6337a10c`; L4M-02 assessment blob `aa3789d0b0adbd6afd75c529e6fb4e56c8758b30`; L4M-08 assessment blob `3216ef081e99687867fead8deb966decdd08d499`; L4M-10 readiness blob `980c046e35429b1c668ff4e3f2069dcfb79714e8`.
- Stale references to matrix blob `2ba85af...` and register blob `4ec993d...` were removed from those four supporting documents. Historical reports were not rewritten.
- Branch remains `feature/t0-centralized-data-feeder-p1-20261101`; no parallel branch or PR created.

### Automation design
- Proposed independent L4 GitHub Actions gates: lineage/contract; exact GitHub artifact inventory and readback; SHA-256 manifest; cryptographic and negative verification; network-disabled offline verification; disposable-copy readback/recovery; tamper-evident history; claim-discipline scan; deterministic aggregate report.
- CI subchecks and owner-only assertions must be reported separately. CI success must never issue owner acceptance or override missing custody/signer evidence.
- Workflow implementation is NOT STARTED. This increment records the approved plan and updates the acquisition register only.

### Current status
- Automation direction: APPROVED.
- Design/documentation: RECORDED.
- L4 workflow implementation: NOT STARTED.
- GitHub artifact inventory/readback automation: NOT VERIFIED / NOT STARTED.
- VPS custody/readback: NOT VERIFIED.
- Actual owner signer/custody assertions: PENDING EVIDENCE only where not machine-verifiable.
- L4M-01–08: retain prior per-control dispositions; no PASS promoted.
- L4M-09: OWNER-WAIVED.
- L4M-10: NOT VERIFIED; final disposition remains owner-only.
- Aggregate L4-Minimum: BLOCKED / NOT VERIFIED.

### Next permitted step
The identified stale matrix/register references in the policy reconciliation, L4M-02, L4M-08 and L4M-10 supporting documents have been updated; a readback check found no remaining references to the two superseded blob SHAs in those four files. Next: inspect existing CI contract-test conventions and implement failing tests first for L4 source-lineage rules. TDD skill has been read. Keep each gate incremental and GitHub-runner-only. Do not dispatch or invoke VPS workflows as part of this plan.

### Explicit limits
No canonical T0 SQLite access or mutation; no VPS/SSH/forced-command changes; no probe installation or remote command; no key generation/signing/rotation/revocation; no trust-root/provider mutation; no artifact deletion/retention changes; no T1, PostgreSQL, service restart, live trading or real orders. Option C — No Destructive Authority remains ACTIVE. CI PASS is not VPS runtime PASS and is not L4 acceptance.
