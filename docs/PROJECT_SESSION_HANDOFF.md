# Five-Layer System — Session Handoff

Updated: 2026-11-10 (Asia/Ho_Chi_Minh)

> Start here in every new session. GitHub is the source of truth. Read this short file first; consult the [archived handoff history](archive/PROJECT_SESSION_HANDOFF_HISTORY_2026-11-10.md) only when an older decision or evidence record is needed.

## 1. Repository and active work

- Repository: `kenznguyen/btcusdt-telegram-signals2`.
- Active branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Default branch: `main`. Do not switch branches or create a parallel PR without a task-specific reason and approval.
- Latest repository HEAD before the current handoff update: `50c99cf3c71e8d85dddaceeb4f8e604000a254c5` (G4 dispatcher design review commit).
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

### Next permitted step

Review a narrowly scoped, root-owned forced-command dispatcher design that:
1. preserves the existing preflight behavior;
2. accepts only exact, fixed command selectors (no arbitrary arguments or shell);
3. invokes only bounded read-only SQLite/HTTP probes;
4. redacts lease owner/token and emits sanitized evidence;
5. obtains the API token only through a separately verified secure source.

The exact proposed change and risk boundary require separate approval before any VPS installation or remote probe invocation. Do not treat the existing G4 scope approval as approval for a new installation mechanism or wider SSH access.

## 5. Session procedure

1. Read this file, then inspect the active branch HEAD and working-tree/PR state on GitHub.
2. Read only the evidence report and source files needed for the active gate.
3. Reconcile the latest run against exact source SHA before relying on it.
4. Implement contract-first; run GitHub Actions before any runtime action.
5. Stop on missing credentials, unknown listeners, source mismatch, expired lease, unavailable probes, or ambiguous evidence. Fail closed and report NOT VERIFIED/BLOCKED.
6. Update this handoff after the gate result, recording exact commit/run/artifact identifiers and the next authorized step.

Do not infer approval from prior conversation when the durable record is ambiguous. When scope conflicts, stop and ask.
