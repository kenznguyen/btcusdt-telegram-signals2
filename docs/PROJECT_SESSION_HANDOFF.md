# Five-Layer System — Session Handoff

Last updated: 2026-11-04 (Asia/Ho_Chi_Minh)

## Purpose

This file is the durable restart point for future ChatGPT sessions. GitHub is the source of truth for project progress and evidence; do not rely on conversation memory alone.

## Repository and workflow rules

- Repository: `kenznguyen/btcusdt-telegram-signals2`.
- GitHub stores source, plans, evidence manifests, and session handoffs.
- GitHub stores source, plans, reports, evidence and artifacts; GitHub Actions is the only runner for project workflows/tests/builds. Codemagic is retired for this project and must not be configured or triggered unless the owner explicitly reverses this decision.
- Do not create parallel branches or PRs for the same work. Continue on the existing relevant branch/PR; avoid PR divergence.
- Do not claim PASS without a traceable artifact, exact source SHA, and test result.
- Use explicit states: PASS, CONDITIONAL PASS, BLOCKED, INTERRUPTED, NOT RUN, NOT VERIFIED, DEFERRED.
- After each meaningful increment, update this handoff (or the relevant evidence document) and commit the progress to the same active branch. Include exact commit SHA, workflow/run URL, artifact URL/checksum, tests and outcomes, and next action.
- At every session boundary, record current branch/HEAD, changed files, working-tree status if known, completed work, pending work, constraints, and approvals required.

## Hard safety boundaries

- Paper trading/signals only. No live trading, real orders, or exchange execution.
- Keep `ai_execution_enabled=false`.
- Do not create or open the canonical T0 database, start the Feeder, connect to an exchange, or sync market data unless explicitly authorized.
- Do not install packages or alter runtime configuration without authorization.
- Android Natural Doze is explicitly deferred by the user. Keep its result as `INTERRUPTED`; do not investigate, design a new Doze test, or rerun it until the user reopens that scope.
- Do not rerun P4 tests already marked PASS without a concrete evidence gap and user authorization.

## Current workstream

### P1 — T0 Centralized Data Feeder, Android-first

- Canonical target: Android-hosted SQLite; Market Data and Paper Ledger share one physical file. ADR-002 assigns the existing `regular` variant as sole canonical host and `.paper` as authenticated IPC client only. PC is optional AI/research/backtest compute and read-only consumer, not T0 canonical writer.
- T0-A fixture/static CI: **PASS** on its recorded exact SHA and GitHub Actions evidence; this is not Android device/runtime acceptance.
- T0-B Android path/identity metadata preflight: **BLOCKED / NOT RUN**. The reviewed Android source did not establish a CanonicalRuntime, app-private canonical path authority, SQLite persistence, Android Feeder composition or approved IPC service. No device/path access has been authorized or performed.
- T0-C Android Feeder runtime: **NOT RUN / NOT AUTHORIZED**. T0-D Android shared-file backup/restore: **NOT RUN / NOT VERIFIED**. T0-E overall T0/P1: **BLOCKED**.
- P5.4.83 checklist: `docs/evidence/P5.4.83-ANDROID-T0-B-READ-ONLY-PREFLIGHT-CHECKLIST-2026-11-04.md`. It is documentation only; no device, DB or runtime access.
- Current next step: source-only implementation gap inventory for the regular Android host (CanonicalRuntime/path authority, shared SQLite/migrations, same-file lease/fencing, Feeder composition, authenticated `.paper` IPC and shared risk/ledger boundary). No code implementation until separately authorized.

### Android P4 evidence baseline

Manifest:
- Path: `docs/evidence/t0/P4_ANDROID_BACKGROUND_RESTART_EVIDENCE_2026-11-02.md`
- Manifest commit: `0ee3db621f6eecd42580dc29ef97915bdcc34fb2`
- Branch at manifest publication: `docs/p4-evidence-manifest-20261103`
- Commit URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/commit/0ee3db621f6eecd42580dc29ef97915bdcc34fb2

Recorded Android environment:
- Device: Xiaomi M2012K10C; Android 13 / API 33; Termux.
- Source checkout: `$HOME/five-layer-system-source-p3`.
- Observed Android source HEAD: `1c16755a07a053e1f225c8861ec76dc9ced1a5d8`.
- Checkout was recorded clean and detached at inspection.
- Canonical DB: NOT CREATED.
- Feeder: NOT RUNNING.
- Historical P4 execution source identity: UNVERIFIED. The observed checkout SHA is not proof that every earlier P4 run used that SHA.

Recorded P4 verdicts:
| Test | Recorded result | Reconciliation note |
|---|---|---|
| P4.1 runtime heartbeat | PASS (4/4) | Manifest/log identity still needs independent artifact reconciliation |
| P4.1 background runtime | PASS (8/8) | Short observation only |
| P4.2 Natural Doze | INTERRUPTED | Explicitly DEFERRED by user; do not investigate or rerun now |
| P4.2 Wake-Lock | PASS (12/12) | Applies only to Wake-Lock condition |
| P4.3 force-stop/restart fencing | PASS | Do not rerun absent a specific gap |
| P4.4 reboot/takeover fencing | PASS | Does not prove full Paper Ledger/Risk State/Paper State restore consistency |
| P4.5 two-writer fencing | PASS | Do not rerun absent a specific gap |
| Overall P4 | CONDITIONAL PASS | Not production certification |

The manifest contains 17 SHA-256 entries. They are user-supplied Android inventory fingerprints recorded in the manifest; the hashes alone do not prove semantic correctness. The actual referenced logs/scripts have not yet been independently retrieved and re-hashed from GitHub in this reconciliation. Do not describe the 17 checksums as independently verified until the corresponding files are accessible and checked.

Known manifest limitation:
- P4.5 process A stdout and process A log have the same recorded SHA-256. This is a recorded duplicate, not evidence of an error by itself.
- Natural Doze root cause (Android Doze vs. vendor/process management) remains unconfirmed and is out of current scope.
- Full backup/restore consistency across candles, Paper Ledger, Risk State, and Paper State remains unverified.
- WAL-consistent backup, extended runtime stability, and recovery after real power/kernel failure remain unproven.

## T0 CI evidence baseline (separate source identity)

The following runs used branch `feature/p5-2-5-green-contracts-20261102` and exact CI source SHA `515bdcc2c14f51652e42397161ee8a90f69dc02d`. This is NOT the Android source SHA.

1. Automated T0 contracts:
   - Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41627068432
   - Result: SUCCESS.
   - Artifact: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41627068432/artifacts/13226227655
   - Artifact SHA-256: `6e10353f084c87f0ca5942665a52886fc4d5c13d58837c98727dbce1ff723b1e`

2. Manual TimescaleDB integration:
   - Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41627507646
   - Result: SUCCESS; parity 8/8; successful insert before conflict rolled back with batch.
   - Artifact: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41627507646/artifacts/13226766555
   - Artifact SHA-256: `91c69d1b061548c9c74faefb8590242cdf38d11c632410e32978a8f16d9226a4`

3. Final Runtime Configuration contract:
   - Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41628736598
   - Result: SUCCESS; tests 8/8.
   - Artifact: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41628736598/artifacts/13227750057
   - Artifact SHA-256: `98fc07a6a64cd54b84e728c6a501cb3e5f3307edde1f41801a8a3178ab7fd7b9`
   - Important: configuration contract PASS only. DB NOT_INITIALIZED; integrity NOT_RUN; database_created=false; database_modified=false; feeder_started=false; exchange_contacted=false. Not production runtime readiness.

## Next actions — execute in order

1. Inspect the current GitHub branch/PR state and the existing manifest commit before writing. Continue on the existing documentation branch; do not create a new PR or branch.
2. Locate the actual Android P4 logs/scripts in repository history, commits, artifacts, or previously uploaded project files. Do not ask the user to repeat environment commands already recorded.
3. Build a reconciliation matrix: test → referenced file → file availability/location → recorded SHA-256 → independently computed SHA-256 (if bytes available) → source SHA evidence → result.
4. Separate:
   - manifest-recorded results;
   - artifacts independently retrieved and hash-verified;
   - source identity verified vs. unverified;
   - missing evidence.
5. Preserve P4 PASS results as historical recorded PASS; do not silently promote them to independently verified if the underlying artifacts are absent.
6. Keep Natural Doze `INTERRUPTED / DEFERRED` and outside current work.
7. Update this handoff and the evidence reconciliation report after each meaningful increment. Commit progress on the same branch and record the resulting commit SHA.
8. Only after reconciliation, identify the next non-Doze evidence gap. No runtime activation is implied.

## Do not confuse these identities

- Android source HEAD: `1c16755a07a053e1f225c8861ec76dc9ced1a5d8`.
- P4 evidence manifest commit: `0ee3db621f6eecd42580dc29ef97915bdcc34fb2`.
- T0 CI source SHA: `515bdcc2c14f51652e42397161ee8a90f69dc02d`.

They identify different source/evidence contexts and must never be substituted for one another.

## P5.3.10 → P5.4.2 integrated Gateway evidence (updated 2026-11-03)

Latest documentation/evidence work:
- P5.4.2 report: `docs/evidence/P5.4.2-INTEGRATED-EVIDENCE-RECONCILIATION-2026-11-03.md`
- Report branch: `feature/p5-4-1-post-merge-validation-20261103`
- Report correction commit: `dfd67d7a36a73f8ce836a160b9e333614acd7d3c`
- Report URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/blob/feature/p5-4-1-post-merge-validation-20261103/docs/evidence/P5.4.2-INTEGRATED-EVIDENCE-RECONCILIATION-2026-11-03.md
- P5.4.2 verdict: **PASS WITH LIMITATIONS** for CI workflow/job status, integrated source identity, artifact metadata association, and documentation only.

Integrated P5.4.1 run:
- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41601215631
- Branch: `feature/p5-4-1-post-merge-validation-20261103`
- Exact source SHA: `76fa59a5c3e0256e40e889d27f2b73f74aa89532`
- Jobs: 5/5 SUCCESS (IDs: 125800380322, 125800436843, 125800436969, 125800437004, 125800645635).
- Artifacts: 4 present/unexpired (IDs: 13214895177, 13214685271, 13214084859, 13213209943).
- Recorded SHA-256 fingerprints are listed in the P5.4.2 report.

Important verification boundary:
- Workflow/job conclusions, source SHA in logs, artifact IDs/names, artifact-to-run branch/SHA association, and unexpired status were checked against GitHub metadata.
- Artifact payload bytes were **not downloaded and independently re-hashed** in P5.4.2. Their SHA-256 values are recorded fingerprints, not independently recomputed hashes. Keep payload checksum verification **NOT VERIFIED**.
- G1 integrated acceptance: 16 tests PASS.
- G2 routing/consumer regression: 66 test invocation PASS; additional consumer regression: 56 test invocation PASS.
- T0 logged suites include atomic fencing 100, health runtime API 107, SIGKILL recovery 101, candle integrity/continuity 12, and operational contract gate PASS. Do not sum these as unique tests because overlap is not excluded.
- Earlier G2 run 41572948926: CI policy 6/6 PASS; G2 contract 18/18 PASS; market_data 210 tests, 8 TimescaleDB integration tests skipped due missing dedicated DSN. PostgreSQL/TimescaleDB canonical writer remains **NOT CERTIFIED**.
- P5.3.11.8 standalone exact-HEAD workflow evidence was not independently established; integrated coverage is only what P5.4.1 run proves.

P5.4.2 report correction commit:
- Commit: `dfd67d7a36a73f8ce836a160b9e333614acd7d3c`
- This explicitly distinguishes artifact metadata verification from payload byte/hash verification.

P5.4.3 documentation consistency review:
- This handoff update records the P5.4.2 results and correct verification boundary.
- No tests were rerun; no code/runtime config changed; no canonical DB/Feeder/exchange/data sync was touched.
- Natural Doze remains **INTERRUPTED / DEFERRED**; no Doze investigation or rerun.
- `ai_execution_enabled=false`; no paper/live execution authorized.

Current workstream status:
| Item | Status |
|---|---|
| P5.3.10 G1 | PASS (RED expected + GREEN 16/16) |
| P5.3.11 G2 | PASS at source-level; 8 TimescaleDB tests skipped |
| P5.3.11.8 standalone exact-HEAD run | NOT VERIFIED |
| P5.4.1 integrated CI | PASS, 5/5 jobs |
| P5.4.2 evidence reconciliation | PASS WITH LIMITATIONS |
| Artifact payload checksum recomputation | NOT VERIFIED |
| Canonical DB / production Feeder | NOT RUN / NOT APPROVED |
| Full multi-ledger backup/restore | NOT VERIFIED |
| Android Natural Doze | INTERRUPTED / DEFERRED |

Next permitted work: documentation-only closeout or separately scoped non-Doze evidence gap review. Do not rerun passing tests, activate runtime, create canonical storage, connect exchange, or sync market data without explicit authorization.


## P5.4.4 — Artifact Payload Integrity Verification (updated 2026-11-03)

- Report: `docs/evidence/P5.4.4-ARTIFACT-PAYLOAD-INTEGRITY-2026-11-03.md`.
- Evidence branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Report commit: `42be7897fcf04acea22ecb94e16622f5c8e18623`.
- Integrated source SHA verified: `76fa59a5c3e0256e40e889d27f2b73f74aa89532`.
- Workflow run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41601215631.
- All four P5.4.1 artifact ZIPs were downloaded. Each passed `unzip -t`; each locally computed SHA-256 matched both GitHub artifact metadata digest and the P5.4.2 recorded fingerprint:
  - T0 artifact `13214895177`: `6d009fd07c1670a80a2e26d4ced28c6fc800820b93907b2c046233394e0f7e8d`.
  - G1 artifact `13214685271`: `d62af7c48bcd7822ca328ca4f4834a20032a9dbe5a2d08d0b498a1d4dff8d52b`.
  - G2 artifact `13214084859`: `65f796c98b13788bad78c0d798bd4776c61cbde0d09ae517256fb5615d331b64`.
  - Combined artifact `13213209943`: `9bde9800f923d2c9f6aa8468517914c4fa1a3885afb984e3e926ab35114c1fab`.
- Embedded T0/G1/G2/combined source-SHA markers all match `76fa59a5c3e0256e40e889d27f2b73f74aa89532`. Selected logs inspected: G1 16 tests OK; G2 routing 66 tests OK; consumer regressions 56 tests OK; G2 T0 regression 96 tests OK; T0 SIGKILL SQLite audit PASS; T0/G2 isolation markers PASS. Counts are separate invocations and are not asserted to be unique.
- P5.4.4 status: **PASS** for artifact payload integrity and the inspected evidence provenance. This does not certify production runtime, TimescaleDB/PostgreSQL canonical writer, or full backup/restore.
- No tests were rerun; no code/runtime config changed; no canonical DB/Feeder/exchange/data sync or execution was touched.
- Existing limits remain: PostgreSQL/TimescaleDB canonical writer **NOT CERTIFIED**; canonical DB integrity **NOT RUN**; production Feeder **NOT RUN / NOT APPROVED**; full multi-ledger backup/restore **NOT VERIFIED**; Android Natural Doze **INTERRUPTED / DEFERRED**; `ai_execution_enabled=false`.
- Next permitted work: documentation-only closeout or a separately scoped non-Doze evidence-gap review. No runtime activation or execution is authorized.

## P5.4.5 — Non-Doze Evidence Gap Review (updated 2026-11-03)

- Report: `docs/evidence/P5.4.5-NON-DOZE-EVIDENCE-GAP-REVIEW-2026-11-03.md`.
- Branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Report commits: initial `883fc869465f2652c6b21b6beebd82ee9c8da364`; scope correction `41446e311c0460fde1e928b2c5a94e1e39833fad`; final lookup-record correction `feaf67a6603dc2feeb868b1d4cc5b4995637c9c6`.
- P4 manifest source: `docs/evidence/t0/P4_ANDROID_BACKGROUND_RESTART_EVIDENCE_2026-11-02.md` on `docs/p4-evidence-manifest-20261103`; blob SHA `d1b353fc86842c98adabd06dd0c0172c45b5ce4c`.
- P5.4.5 verdict: **CONDITIONAL PASS** for identifying/prioritizing non-Doze evidence gaps; P4 production readiness remains **NOT APPROVED**.
- Historical P4 outcomes remain manifest-recorded only: heartbeat 4/4, background 8/8 (short observation), Wake-Lock 12/12, force-stop/restart, reboot/takeover, and two-writer fencing PASS. No P4 tests were rerun or upgraded to independent PASS.
- Android observed checkout SHA `1c16755a07a053e1f225c8861ec76dc9ced1a5d8` is not proof of historical P4 execution identity. Per-run P4 source SHA remains **NOT VERIFIED**.
- 17 manifest SHA-256 values remain Android inventory-recorded, not independently recomputed from original bytes. Six representative log paths checked across `main`, `docs/p4-evidence-manifest-20261103`, and `feature/p5-4-1-post-merge-validation-20261103` returned 404 in all 18 exact path/ref lookups; this establishes only that those exact paths were not retrievable in the three checked refs, not global absence.
- Gaps: original raw P4 logs/scripts and run-source provenance; full multi-ledger backup/restore (candles, Paper Ledger, Risk State, Paper State); WAL-consistent backup; extended runtime stability; abrupt power/kernel failure recovery. P4.5 A stdout/log duplicate fingerprint requires provenance clarification.
- P5.4.1 run `41601215631` and source SHA `76fa59a5c3e0256e40e889d27f2b73f74aa89532` are a separate T0/Gateway CI context and must not be substituted for Android P4 source identity.
- Natural Doze remains **INTERRUPTED / DEFERRED**, explicitly excluded: no investigation, design, or rerun.
- No tests/workflows were run; no DB opened/created/modified; no Feeder/exchange/data sync; no execution. Keep `ai_execution_enabled=false`.
- Next permitted action: retrieve the original P4 log/script bytes from their actual source and independently recompute all 17 hashes; do not regenerate historical evidence. Future backup/restore, WAL, extended runtime, and abrupt-failure tests require separate scope and approval.

## P5.4.6 — Android P4 Historical Evidence Recovery (updated 2026-11-03)

- Report: `docs/evidence/P5.4.6-ANDROID-P4-HISTORICAL-EVIDENCE-RECOVERY-2026-11-03.md`.
- Latest report update commit: `a350365868c9c374ff9cea1f47c205b541f30ada`.
- Branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Baseline P4 manifest: `docs/evidence/t0/P4_ANDROID_BACKGROUND_RESTART_EVIDENCE_2026-11-02.md`, ref `docs/p4-evidence-manifest-20261103`, blob SHA `d1b353fc86842c98adabd06dd0c0172c45b5ce4c`.
- User decision (2026-11-03): **"chấp nhận dữ liệu do termux cung cấp"**. Accept the Termux-supplied manifest, 17 supplied SHA-256 inventory entries, and recorded P4 outcomes as the user-authorized evidence basis.
- P5.4.6 result: **CONDITIONAL PASS — Termux-reported evidence accepted by explicit user instruction**. This is not independent byte-level verification.
- Retrieval audit remains factual: six representative P4 log paths checked across three refs (18 exact path/ref lookups, all 404); recursive Git tree at observed Android SHA `1c16755a07a053e1f225c8861ec76dc9ced1a5d8` had no matching P4 evidence paths; GitHub evidence directory on manifest ref lists only `t0`; Project Files/Library search returned no original P4 evidence package.
- Original files independently retrieved: **0/17**. Independently recomputed hashes: **0/17**. Byte-level verification remains **NOT VERIFIED**; do not claim independently validated hashes.
- Source identity: Android observed checkout SHA `1c16755a07a053e1f225c8861ec76dc9ced1a5d8` is not proven to be the source for each P4 run. Historical P4 per-run source identity **NOT VERIFIED**.
- P4 historical results are accepted as **Termux-reported / user-accepted**: heartbeat 4/4; background 8/8 (short observation); Wake-Lock 12/12; force-stop/restart; reboot/takeover; two-writer fencing PASS. Natural Doze remains **INTERRUPTED / DEFERRED**, not PASS.
- P5.4.1 source SHA `76fa59a5c3e0256e40e889d27f2b73f74aa89532` and T0 CI SHA `515bdcc2c14f51652e42397161ee8a90f69dc02d` are separate contexts and must not be substituted for Android P4 source identity.
- P4 overall remains **CONDITIONAL PASS**; production readiness **NOT APPROVED**.
- Next work: prepare the next separately scoped non-Doze evidence task, prioritizing backup/restore validation design across candles, Paper Ledger, Risk State, and Paper State. Actual test execution requires explicit authorization.
- No tests/workflows run for this acceptance update; no Android device access; no DB/Feeder/exchange/data sync; no execution. Keep `ai_execution_enabled=false`.

## P5.4.7 — Backup/Restore Validation Architecture Review (updated 2026-11-03)

- Report: `docs/evidence/P5.4.7-BACKUP-RESTORE-ARCHITECTURE-REVIEW-2026-11-03.md`.
- Report commit: `07dc193c0fdf96a3cc63b046590e432137f8fb82`.
- Review base SHA: `9fdf3cb812b77e6d9554752d8ae0fd3db638a1b9`.
- Branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Verdict: **CONDITIONAL PASS** for source-grounded architecture review only; no backup/restore implementation or production approval.
- Reviewed source blobs: `market_data/store.py` `b28601aed70097afcb7a4eea2dd93ed163ae1cec`; `market_data/feeder.py` `70bba25f1fbf8b3edd3e28756984eed584037cc1`; `market_data/storage.py` `99b66a4d183b8664f28d6638d8d87416d32847c9`; `paper_execution/ledger.py` `68209ce48a6e5e9a995f93167684133e41cc7f55`; `paper_execution/risk_control.py` `3c76e462b0b4d924c2418842d95ed74285e2315d`; `paper_execution/equity.py` `40d6566294355c646839614c92f8fba6116b582c`; `pipeline/api.py` `0540540462b3710a25788e4ff47a88272b7ee9c3`.
- Main architecture findings:
  - SQLite WAL is used; recommend SQLite Online Backup API, not copying the active main DB file alone.
  - SQLite mode can co-locate candles, lease and paper/risk state in one DB, but PostgreSQL market-data selection plus SQLite Paper Ledger becomes a multi-store snapshot problem. Do not assume cross-store atomicity.
  - Candle page commits and paper ledger transactions are separate; recovery-grade snapshot requires a global writer barrier and per-domain high-water marks.
  - Restoring an old DB can roll back `feeder_leases` generation and the Kill Switch. Stop all old writers, re-fence beyond the old generation and explicitly assert kill/maintenance before any writer resumes.
  - Restore verifier must be read-only and must not call `PaperLedger.__init__`, `initialize_schema()` or `ensure()` helpers that can create/repair state. Missing risk/strategy rows must fail closed.
  - Restore epoch must invalidate stale Core/AI intents and consumed book snapshots.
- Required logical domains: Candles; Paper Ledger (`paper_orders`, `paper_books`, `paper_audit`); Risk State (`paper_risk_control`, equity history, daily baselines, account config and sanitized external risk-config fingerprint); Paper State (`paper_state`, `paper_strategy_state`). Lease and API budget are additional operational state.
- Open decisions: canonical host/path; one SQLite file vs multi-store; backup destination, encryption/retention, RPO/RTO, approved cadence, monotonic restore epoch and recovery approval authority. Android P4 evidence and current server DB are separate identities.
- Test ownership proposed: GitHub Actions temporary SQLite fixtures; Windows PC shadow DB for filesystem/atomic publication; Android instrumentation/Termux shadow DB for device lifecycle. No canonical DB tests authorized.
- P5.4.7 non-actions: no tests/workflows; no DB opened/created/copied/backed up/restored/modified; no Android filesystem access; no Feeder/exchange/sync; no Doze work; no execution. Keep `ai_execution_enabled=false`.
- Independent fresh-context/cross-model review: **NOT RUN**. Architecture review is not final production approval.
- Next step: **P5.4.8 — Backup/Restore Test Contract & Evidence Architecture**, documentation-only; define exact test cases, fixture schemas, failure injection, artifacts and CI isolation. Do not execute tests without separate authorization.

## P5.4.8 — Backup/Restore Test Contract & Evidence Architecture (updated 2026-11-03)

- Report: `docs/evidence/P5.4.8-BACKUP-RESTORE-TEST-CONTRACT-2026-11-03.md`.
- Report commit: `352deeaccef8f8529e312752116b77ec84d71268`.
- Specification base SHA: `69d870e1457e59f6bb5dc0ed86688cf9feec1fae`.
- Branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Status: **CONDITIONAL PASS — test contract specified; NOT EXECUTED**. Documentation only.
- Source baselines inspected: `market_data/store.py` blob `b28601aed70097afcb7a4eea2dd93ed163ae1cec`; `market_data/test_store.py` `6a3f2e6c6714926720155eb28484dd21cf977cd5`; `market_data/feeder.py` `70bba25f1fbf8b3edd3e28756984eed584037cc1`; `paper_execution/ledger.py` `68209ce48a6e5e9a995f93167684133e41cc7f55`; `paper_execution/test_ledger.py` `0c05ae1ed0d9526978f8a90c983957dbd7baed5a`; `paper_execution/risk_control.py` `3c76e462b0b4d924c2418842d95ed74285e2315d`; `paper_execution/test_risk_control.py` `69c9177a249369f52d0c81e442c9c4583c9f5b77`; `paper_execution/equity.py` `40d6566294355c646839614c92f8fba6116b582c`; `paper_execution/test_equity.py` `87eac43ff815903b1b8b7ea70dc3dcaeeb3abe43`; existing workflow `.github/workflows/p5-4-1-post-merge-validation.yml` `e0b10253225956377cb7e7724a601f442e307729`.
- Contract defines deterministic `single_sqlite` and `split_store` fixture profiles; fixed market/candle/paper/risk/lease seed state; required schema inventory; read-only restore verifier; temporary-root isolation; empty DB/credential environment; `AI_EXECUTION_ENABLED=false`; no network or worker startup.
- Planned cases: ISO-01..05; WAL-01..07; DOM-01..07; RST-01..10; SAFE-01..08; PC-01..06; AND-01..05. All are **PLANNED / NOT RUN**.
- GitHub Actions owns deterministic fixture/WAL/domain/restore/fencing tests. Windows PC and Android instrumentation own their platform-specific shadow DB checks only after separate explicit approval. Natural Doze is excluded and remains **INTERRUPTED / DEFERRED**.
- Evidence contract requires exact source SHA, run metadata, isolation audit, fixture spec, backup manifest, machine-readable test results, integrity checks, restore validation, artifact SHA-256 and execution-boundary statement. Payload checksum must be independently recomputed; artifact metadata alone is insufficient.
- Open prerequisites: canonical host/path; single SQLite vs multi-store topology; schema version/columns; backup destination/encryption/retention/RPO/RTO; monotonic restore epoch; recovery/Kill Switch approver.
- No tests/workflows/builds run; no fixture/canonical/shadow DB created or opened; no PC/Android filesystem access; no Feeder/API/exchange/data sync; no runtime configuration/dependency changes; no execution. Keep `ai_execution_enabled=false`.
- Independent fresh-context/cross-model review: **NOT RUN**.
- Next step: **P5.4.9 — Backup/Restore Test Implementation Readiness Gate**, documentation-only first. Resolve prerequisites, inspect narrow integration points and propose a test-only implementation plan. Do not implement or execute until separately authorized.

## P5.4.9 — Backup/Restore Test Implementation Readiness Gate (updated 2026-11-03)

- Report: `docs/evidence/P5.4.9-BACKUP-RESTORE-IMPLEMENTATION-READINESS-2026-11-03.md`.
- Report commit: `e6f04b3e9f88a5c85f4f6bfe0a420b2a873cf5a8`.
- Review base SHA: `1d6bf449935e675d0144f770d11fc99afcfc7eb9`.
- Branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Result: **BLOCKED for operational implementation; CONDITIONAL PASS for fixture-only CI design**. Documentation/source inspection only.
- Inspected current source blobs: existing workflow `.github/workflows/p5-4-1-post-merge-validation.yml` `e0b10253225956377cb7e7724a601f442e307729`; `market_data/test_store.py` `6a3f2e6c6714926720155eb28484dd21cf977cd5`; `market_data/store.py` `b28601aed70097afcb7a4eea2dd93ed163ae1cec`; `paper_execution/test_ledger.py` `0c05ae1ed0d9526978f8a90c983957dbd7baed5a`; `paper_execution/ledger.py` `68209ce48a6e5e9a995f93167684133e41cc7f55`; `paper_execution/test_risk_control.py` `69c9177a249369f52d0c81e442c9c4583c9f5b77`; `paper_execution/test_equity.py` `87eac43ff815903b1b8b7ea70dc3dcaeeb3abe43`.
- Existing temporary SQLite fixtures and exact-SHA CI isolation provide a narrow starting point for a dedicated fixture-only test harness.
- Proposed implementation sequence: contract/schema pinning; deterministic fixtures and read-only verifier; WAL Online Backup API tests; four-domain restore/failure injection; lease/Kill Switch/replay safety tests; CI artifact publication. This sequence is proposed only and requires explicit implementation approval.
- Operational implementation blockers: canonical target/host/path; one SQLite vs split-store topology; exact schema/columns; backup destination/encryption/retention/RPO/RTO; monotonic restore epoch; Kill Switch recovery latch/approver; Windows/Android shadow scope approvals.
- No tests/workflows/builds run; no fixture/canonical/shadow DB accessed or created; no code/dependency/workflow/runtime changes; no PC/Android filesystem; no Feeder/API/exchange/data sync; no Doze work; no execution. Keep `ai_execution_enabled=false`.
- Independent fresh-context/cross-model review: **NOT RUN**.
- Next step: **P5.4.10 — Owner Decision Record & Fixture-Only Implementation Authorization**. Record unresolved decisions and obtain explicit scope authorization. If only CI fixture tests are authorized, they can be implemented without canonical path selection; operational restore and PC/Android remain blocked. Test execution requires separate approval.

## P5.4.10 — Backup/Restore Fixture Test Implementation (updated 2026-11-03)

- Report: `docs/evidence/P5.4.10-BACKUP-RESTORE-FIXTURE-TEST-IMPLEMENTATION-2026-11-03.md`.
- Report commit: `088df0716c7507d545b8bd31f687516fcc8b3b95`.
- Active branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Runner decision: **GitHub Actions only**. The dedicated `backup-restore-test` block has been removed from `codemagic.yaml`; no Codemagic workflow is used for P5.4.10.
- Final P5.4.10 source SHA: `4c4c04070f55c7e3274f747f0594cf90a7258a3e`.
- GitHub Actions run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41639520383 — **SUCCESS**, exact source SHA matched.
- Tests: **12/12 PASS**, 0 failures, 0 errors, 0 skipped.
- Artifact: `13232815114`, `p5-4-10-backup-restore-evidence-41639520383`, 5,317 bytes, retained for 7 days.
- Artifact SHA-256 (GitHub metadata and independently downloaded/recomputed ZIP): `2b20c7b3ad390b8b4ff066800a6963480e560e28913ac901aeb5685a58be1a6c`.
- ZIP integrity check: PASS; internal evidence checksums: **8/8 independently recomputed and matched**.
- Evidence verdict: isolation PASS; exact source/branch/run metadata present; SQLite integrity `ok`; foreign-key violations 0; source/backup logical hashes equal; `production_restore=NOT_TESTED`.
- Integrated P5.4.1 gate on the same source SHA: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41639520249 — **SUCCESS, 5/5 jobs** (preflight, T0, G1, G2, combined publication). Combined artifact metadata ID `13232296509`; payload checksum was not independently verified in this workstream.
- Current implementation blobs:
  - `ci/test_backup_restore.py`: `0a3d89e25e6b822e59e69a0067405913d40ee4fb`.
  - `ci/backup_restore_test_support.py`: `7acbb6f124bfaf3a6cbdab27cc9b6c87c9c76c6c`.
  - `ci/run_backup_restore_tests.py`: `411c6b9585a6e94b0478be8ca0fa773c17f00d1f`.
  - `paper_execution/shadow_migration_fixture.py`: `0e99655cd1114ff4f18e100296ed5e251dca5d0b`.
  - `ci/test_ci_policy.py`: `e9604b56c00bca1131c76dca32285cb49c6ac85c`.
  - `.github/workflows/p5-4-10-backup-restore-fixture.yml`: `d6a7176768d9185e03df53a9316a44dcfc265d1c`.
  - `codemagic.yaml` after removing the dedicated Codemagic job: `5860ab1acc162e010040329222fff5654be0d94c`.
- Debugging history: earlier CI runs exposed missing candle schema, missing lease schema, a stale logical fingerprint key and staged WAL sidecar leakage. Each was corrected; final run `41639520383` passed.
- Coverage remains a first fixture-only slice, not all 48 planned P5.4.8 cases. Split-store metadata checks do not prove cross-database atomicity.
- Still blocked: canonical DB/host/path, storage topology, production backup destination/encryption/retention/RPO/RTO, monotonic restore epoch authority, Kill Switch recovery latch/approver, production restore/promotion, Windows PC and Android shadow drills.
- No canonical/PC/Android DB accessed or created; no Feeder/API/exchange/sync; no live or paper orders. Keep `ai_execution_enabled=false`. Natural Doze remains **INTERRUPTED / DEFERRED**.
- Status: **PASS for the 12-test fixture-only CI increment; production backup/restore readiness NOT APPROVED**.
- Next action: implement the next separately scoped fixture-only P5.4.8 test slice. Resolve all operational prerequisites before any canonical, PC/Android or production recovery testing.
- Independent fresh-context/cross-model review: **NOT RUN**.

## P5.4.11 — CI Workflow Automation Cleanup (updated 2026-11-03)

- Report: `docs/evidence/P5.4.11-CI-WORKFLOW-AUTOMATION-CLEANUP-2026-11-03.md`.
- Report commit: `4ef841e390bd33ef61428d97f093f9deefadb0b4`.
- Active branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Final validated source SHA: `2f5429b90c738fecdbffedb4dedfed930f63ce86`.
- Validation run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41640796456 — **SUCCESS, 5/5 jobs**, exact source SHA matched.
- Workflow cleanup: G1 RED and G2 RED automatic triggers removed (manual only); G1 GREEN retained as reusable only; G2 GREEN retained as reusable + manual; T0 Validation push narrowed to its dedicated release branch/path and reusable call retained; P5.4.1 push narrowed to active branch and code/CI paths; PR trigger removed; P5.4.10 fixture push/manual triggers retained; T0 Manual and G2 historical RED remain manual only.
- Reusable P5.4.1 dependencies T0, G1 GREEN and G2 GREEN are preserved. No workflow file deleted. Codemagic remains retired.
- Updated CI policy tests assert the new trigger contract. Final test summaries are recorded in the P5.4.11 report.
- Artifacts from run `41640796456`: combined `13232317905`; T0 `13232926956`; G1 `13232826692`; G2 `13232831706`. GitHub artifact digests are recorded in the report; payloads were not independently downloaded/re-hashed for this increment.
- Intermediate runs `41640490924` and `41640673926` failed because static policy assertions still encoded the old triggers. The tests/config were reconciled; final run passed without restoring unnecessary automatic triggers.
- No canonical/shadow DB, PC/Android filesystem, Feeder/API or exchange accessed; no sync or orders. Keep `ai_execution_enabled=false`; Natural Doze remains **INTERRUPTED / DEFERRED**.
- Status: **PASS for trigger cleanup and integrated CI verification**.
- Next action: continue fixture-only P5.4.8 Backup/Restore test expansion on this branch. Production restore and all canonical/PC/Android operational tests remain blocked pending separate approvals.
- Independent fresh-context/cross-model review: **NOT RUN**.

## P5.4.12 — Android APK Build Automation Retirement (updated 2026-11-03)

- Report: `docs/evidence/P5.4.12-ANDROID-APK-BUILD-AUTOMATION-RETIREMENT-2026-11-03.md`.
- Report commit: `ee5c2b4b7e4b17a72c31819d93fd4b87bd1cb923`.
- Active branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Final verified source SHA: `f751193f5a0d9d83f2711855563680e0572a9762`.
- Retired Codemagic workflows: `android-chart-pro-debug` (push-triggered Debug + Parallel APK build) and `android-chart-pro-release` (manual signed Release APK build).
- All nine current GitHub Actions workflow YAML files scanned: no Gradle APK assemble tasks, Android build setup/release scripts, APK output paths or APK artifact names.
- `ci/test_ci_policy.py` now guards that Android APK builds/publishing do not return to either Codemagic configuration or GitHub Actions workflows.
- Source commits: `bfcb13baeb8e177f412d4a1288fac6d95706b2e8` (retire APK jobs); `19ab3aef9aab77696f653249947aac977b8a2202` (policy test); `32f31a03d4aa2109c963ca8906d4480f62deff34` (restore Codemagic YAML root mapping); `f751193f5a0d9d83f2711855563680e0572a9762` (GitHub Actions no-APK regression guard).
- Final integrated CI run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41642448498 — **SUCCESS, 5/5 jobs**, exact source SHA matched.
- Artifacts: combined `13233611587`; T0 `13232554165`; G1 `13234045140`; G2 `13233278350`. GitHub metadata digests are recorded in the report; payloads not independently downloaded/re-hashed.
- Backup/Restore fixture run on preceding configuration-fix SHA `32f31a03d4aa2109c963ca8906d4480f62deff34`: run `41641922222`, SUCCESS 1/1; artifact `13232558451`.
- Intermediate integrated run `41641752492` failed because the Codemagic YAML root `workflows:` mapping was temporarily absent after APK workflow removal. Restoring the root mapping fixed the CI policy errors without restoring APK workflows.
- No APK built/signed/published; no signing secrets or keystore accessed; no Android filesystem/instrumentation, canonical DB, Feeder/API, exchange, sync or orders. Keep `ai_execution_enabled=false`.
- No GitHub Actions APK build workflow currently exists. A manual signed Release APK workflow is not available; require separate approval and implement it as manual-only GitHub Actions if a release is requested. Do not restore automatic APK build triggers.
- Codemagic non-Android legacy YAML entries remain but Codemagic is not an authorized runner. Account-level project/webhook settings were not changed.
- Status: **PASS for APK automation retirement and integrated CI verification**.
- Next: keep APK packaging disabled by default; continue fixture-only P5.4.8 scope unless the owner requests a separately approved manual APK release workflow.
- Natural Doze: **INTERRUPTED / DEFERRED**. Independent fresh-context/cross-model review: **NOT RUN**.


## P5.4.13 — Fixture-only Backup/Restore Test Expansion (updated 2026-11-03)

- Report: `docs/evidence/P5.4.13-FIXTURE-RESTORE-TEST-EXPANSION-2026-11-03.md`.
- Report commit: `7612046816e59df5b51767cff7f99c7ec05c07e8`.
- Branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Exact tested source SHA: `78a45631e0aa70a2ee1ca4e8e3b479d63a6f85ee`.
- Source change: five new fixture-only tests in `ci/test_backup_restore.py`; blob SHA `eecafc212d20b819e4c07c20c827713dd5dcf509`.
- Final GitHub Actions run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41643277796 — **SUCCESS, 17/17 tests, 0 failures, 0 errors, 0 skipped**.
- Initial diagnostic run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41643182657 — **FAIL, 16/17** because the test's generation-7 lease timestamp exceeded its fixture TTL by 1 ms. The fixture timestamp was corrected; this was not a production runtime failure.
- Artifact: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41643277796/artifacts/13234335493; artifact ID `13234335493`, 5,465 bytes.
- GitHub digest and independently downloaded ZIP SHA-256 both: `8b0f1b042f9302563373348bde789c8d52b4bd695fc4d08c12300bb053681515`.
- ZIP integrity PASS; 12 files; 8/8 internal evidence checksums independently recomputed and matched.
- Isolation PASS: temporary fixture DBs only; no canonical DB, network, exchange, Feeder startup or order execution; `ai_execution_enabled=false`.
- Integrated P5.4.1 gate: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41643277914 — **SUCCESS, 5/5 jobs**, same source SHA.
- New test coverage: all-domain cursor/lease-generation round-trip; independent Paper Ledger pause and Risk Control Kill Switch persistence; stale lease generation rejected; runtime startup remains incomplete until recovery completion; Kill Switch rollback/tampering detected.
- P5.4.8 S1/S2: **PARTIALLY COVERED**, not complete. Restore-epoch intent/book invalidation, full duplicate-intent/fill replay behavior, external Kill Switch recovery latch and combined writer-start gate remain NOT VERIFIED.
- Windows PC and Android shadow tests remain NOT RUN and separately gated. Split-store cross-database atomicity remains NOT VERIFIED. Production restore NOT TESTED / NOT APPROVED.
- Next: continue fixture-only S1/S2 tests for restore epoch, replay/idempotency and recovery-latch/writer-start gating. Do not access canonical DB, activate runtime, use PC/Android shadow, start Feeder/API or connect exchanges without separate approval.
- Natural Doze remains **INTERRUPTED / DEFERRED**; no investigation or rerun.


## P5.4.16 — Versioned Manifest and Schema-Drift Fixture Validation (2026-11-03)

- Report: `docs/evidence/P5.4.16-VERSIONED-MANIFEST-SCHEMA-DRIFT-FIXTURE-VALIDATION-2026-11-03.md`.
- Report commit: `795bd68fda397d8301fdaf9eb005fd638a81a7ec`.
- Exact tested source SHA: `7bd7ab7445d66c6ddd36a2fdaadecbd850606e16`.
- Test file blob SHA: `ccae781e9beb8a022c28539ac85b281ba417a4aa`.
- Test-support blob SHA: `b92d23d9030573f911cfe71f405fe47823d3b617`.
- Fixture run [41646671449](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41646671449): **SUCCESS, 25/25 tests, 0 failures, 0 errors, 0 skipped**.
- Diagnostic runs: [41645337564](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41645337564) failed 23/25 and [41645442360](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41645442360) failed 24/25; both failures exposed validator/test gaps and were corrected without skipping tests.
- Artifact ID `13234989035`, 5,664 bytes; GitHub digest and independently downloaded ZIP SHA-256 match: `01d8d99466a0fbd22d28b5f122b7becd3611c60e4fc669fe2d0128aacca160b4`. ZIP integrity PASS, 12 files, 8/8 internal checksums independently matched.
- Integrated P5.4.1 gate [41646671452](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41646671452): **SUCCESS, 5/5 jobs**, same source SHA. Artifacts: G1 `13235392424`; T0 `13235147776`; G2 `13234539084`; integrated `13234014039`. Their GitHub digests are recorded in the P5.4.16 report; independent ZIP download/hash in this increment was performed only for the fixture artifact.
- Coverage added: schema drift detection; exact version-1 split-store manifest field set; per-store schema version; invalid manifest types/values, blank identifiers and unapproved stores.
- Status: **PASS** for the exact 25 fixture cases and integrated gate. **NOT VERIFIED**: split-store partial-backup failure injection, filesystem crash/power interruption, production manifest publisher/consumer integration, restore-epoch enforcement, external re-fencing and combined writer-start gate.
- Isolation: disposable TemporaryDirectory fixtures only. No canonical DB, PC/Android filesystem, Feeder/API, exchange, network sync, production restore or order execution. GitHub Actions only; no Codemagic. `ai_execution_enabled=false`.
- Next: fixture-only split-store partial-failure injection and binding per-store manifest metadata to verifiable fixture snapshot content/high-water marks. Production restore and runtime activation remain prohibited without separate approval. Natural Doze remains `INTERRUPTED / DEFERRED`.


## P5.4.17 — Split-Store Partial Backup Failure Injection (2026-11-03)

- Report: `docs/evidence/P5.4.17-SPLIT-STORE-PARTIAL-BACKUP-FAILURE-INJECTION-2026-11-03.md`.
- Report commit: `9627290c6958c3f066df55bf770804b1f0bd24a8`.
- Exact tested source SHA: `24208ebb43e34db4d68b686e0bbeb32cbe349228`.
- Test file blob SHA: `5068d925fd28b127de88c79f5d1e1c88493f1a64`.
- Fixture support blob SHA: `370817e66aa78e3051267a7e340a764dd76a4aff`.
- Fixture run [41647310614](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41647310614): **SUCCESS, 27/27 tests, 0 failures, 0 errors, 0 skipped**.
- Diagnostic RED run [41647082163](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41647082163): expected import failure before helper implementation. First implementation run [41647234831](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41647234831): 26/27; success path exposed invalid JSON newline escaping, corrected before final run.
- Artifact ID `13234929605`, 5,704 bytes; GitHub digest and independently downloaded ZIP SHA-256 match: `37bf873c63f419484ebedac6461a05776f1098892ebc326620c293e1c9a4b522`. ZIP integrity PASS, 12 files, 8/8 internal checksums independently matched.
- Integrated P5.4.1 gate [41647311051](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41647311051): **SUCCESS, 5/5 jobs**, same source SHA.
- Added fixture-only partial-failure injection: after first store backup, no final directory or manifest is published and staging is removed. Added success-path check that both stores and manifest appear together in one completed fixture directory.
- Important limitation: this proves only the tested Linux fixture directory-publication behavior. It does not prove true cross-database snapshot consistency, production atomicity, Windows behavior or crash/power-loss recovery.
- Status: **PASS** for the exact 27 fixture cases and integrated gate. **NOT VERIFIED**: manifest-to-backup content binding, production publisher/consumer integration, true cross-store consistency, filesystem crash recovery and production restore.
- Isolation: disposable TemporaryDirectory DBs only; no canonical DB, PC/Android filesystem, Feeder/API, exchange, network sync, production restore or order execution. GitHub Actions only; no Codemagic. `ai_execution_enabled=false`.
- Next: bind each store's manifest snapshot ID, schema version and high-water mark to independently inspected backup contents; reject missing, swapped or mismatched stores before restore validation. Natural Doze remains `INTERRUPTED / DEFERRED`.


## P5.4.18 — Split-Store Manifest-to-Backup Content Binding (2026-11-03)

- Report: `docs/evidence/P5.4.18-SPLIT-STORE-MANIFEST-CONTENT-BINDING-2026-11-03.md`.
- Report commit: `b3f15ee9d5399e97162f5b7011536e172c89e99a`.
- Exact tested source SHA: `faddcffe9fd6d7a44d4070adebbabc2ce101addf`.
- Test file blob SHA: `c6924c594f3304c47e2b5dccc8471f4ab404a3a9`.
- Test-support blob SHA: `03834de94ec8f901a10cf533f07593556faec76b`.
- Fixture run [41648301945](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41648301945): **SUCCESS, 31/31 tests, 0 failures, 0 errors, 0 skipped**.
- Diagnostic run [41647957594](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41647957594): expected RED import failure before helper implementation. Run [41648171548](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41648171548): 29/31; exposed directory path handling and outdated positive manifest fixture, both corrected.
- Artifact ID `13237180708`, 5,784 bytes; GitHub digest and independently downloaded ZIP SHA-256 match: `d405999b885df972a15eaf87833da3f17e95422be3f8433f5c0dc41683f23eca`. ZIP integrity PASS, 12 files, 8/8 internal checksums independently matched.
- Integrated P5.4.1 gate [41648301789](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41648301789): **SUCCESS, 5/5 jobs**, same source SHA.
- Added fixture identity derivation: logical SHA-256, physical backup SHA-256, per-table row counts, fixture high-water mark (sum of row counts) and SQLite `PRAGMA user_version`. Publisher compares supplied identity fields against staged backup contents; read-only verifier rejects tampered hash, swapped DB images and missing DB.
- Important limitation: fixture row-count high-water is not a production event cursor. The checks do not establish distributed cross-database atomicity or a production publisher/consumer contract.
- Status: **PASS** for exact 31 fixture cases, artifact and integrated gate. **NOT VERIFIED**: domain cursor semantics, production manifest integration, true cross-store consistency, filesystem crash recovery, Windows behavior and production restore.
- Isolation: disposable TemporaryDirectory DBs only; no canonical DB, PC/Android filesystem, Feeder/API, exchange, network sync, production restore or order execution. GitHub Actions only; no Codemagic. `ai_execution_enabled=false`.
- Next: adversarial tests for validly re-hashed semantic mismatch, table-count/high-water/schema-version tampering; then determine whether production manifest design decisions are needed before production implementation. Natural Doze remains `INTERRUPTED / DEFERRED`.


## P5.4.19 — Split-Store Adversarial Manifest Tampering Tests (2026-11-03)

- Report: `docs/evidence/P5.4.19-SPLIT-STORE-ADVERSARIAL-MANIFEST-TAMPERING-2026-11-03.md`.
- Report commit: `5abecc82b3561279f579e710d828abcd50ce70e3`.
- Exact tested source SHA: `b91243778164d1f4f8222bcd3a1705cd1fbe7e7e`.
- Test file blob SHA: `be6eb3f7f35e38027df1affe668c5a4955167384`.
- Fixture run [41649479146](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41649479146): **SUCCESS, 35/35 tests, 0 failures, 0 errors, 0 skipped**.
- Added adversarial cases: mutate candle data then update physical file hash (logical identity must still reject); tamper table count while adjusting high-water to preserve manifest sum; tamper high-water; tamper schema version. All four rejected by read-only verifier.
- Artifact ID `13236338248`, 5,853 bytes; GitHub digest and independently downloaded ZIP SHA-256 match: `74a10b17d10e91dc0491d4a68c629e51c04b3d4ba6e84dc0963773372c331ee5`. ZIP integrity PASS, 12 files, 8/8 internal checksums independently matched.
- Integrated P5.4.1 gate [41649479110](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41649479110): **SUCCESS, 5/5 jobs**, same source SHA.
- No production/runtime code changed in this increment; only fixture tests and `hashlib` import.
- Status: **PASS** for 35 fixture tests, fixture artifact and integrated gate. **NOT VERIFIED**: production cursor semantics, distributed snapshot consistency, production manifest integration, filesystem crash recovery, Windows behavior and production restore.
- Isolation: disposable TemporaryDirectory DBs only; no canonical DB, PC/Android filesystem, Feeder/API, exchange, network sync, production restore or order execution. GitHub Actions only; no Codemagic. `ai_execution_enabled=false`.
- Next: document unresolved production manifest decisions before any production implementation: store identity, domain cursor/high-water semantics, global barrier, schema-version authority, canonicalization and restore epoch/fencing ownership. Natural Doze remains `INTERRUPTED / DEFERRED`.


## P5.4.20 — Proposed Production Backup Manifest Contract (2026-11-03)

- Decision record: `docs/decisions/ADR-001-PRODUCTION-BACKUP-MANIFEST-CONTRACT.md`.
- ADR commit: `588931420e411c024011a0a8841be173b810bb4c`.
- Status: **PROPOSED — NOT ACCEPTED; production implementation BLOCKED**.
- Source-grounded findings:
  - SQLite candle schema creation is explicit through `CandleStore.initialize_schema()`; inspected SQLite candle source does not define a production schema-version registry.
  - PostgreSQL migration code records migration ID and checksum in `market_data.schema_migrations`.
  - PaperLedger construction creates/ensures its SQLite tables; inspected code does not define a formal ledger migration registry and therefore must not be used by a read-only restore verifier.
  - Fixture `PRAGMA user_version` values are test metadata, not proof of a production migration authority.
  - Row-count sum is not a production cursor; shared barrier ID alone does not prove cross-store atomicity.
- ADR captures seven unresolved decision groups: canonical store topology/identity; per-domain high-water/cursors; global barrier and consistency model; schema authority; canonicalization; external restore epoch/lease/Kill Switch recovery; backup destination/security/RPO/RTO.
- No topology, canonical host/path, cursor, migration scheme, backup destination or operational value was selected or approved.
- No code, schema, dependency, workflow, runtime or database changed. No tests were run for this documentation-only decision record.
- Next: obtain explicit decisions/approval for D1–D7 before production implementation. Fixture-only testing may continue, but no canonical DB, PC/Android shadow, Feeder/API, exchange, production restore or writer activation. Natural Doze remains `INTERRUPTED / DEFERRED`; `ai_execution_enabled=false`.


### P5.4.20 clarification — existing T0 storage decision

- Owner-confirmed correction (2026-11-03): **T0 runs on Android; Android-hosted SQLite is the canonical T0 storage target.** This supersedes the older PC-hosted T0 wording.
- PC is a separate compute/backtest environment; it is not the T0 canonical writer under the current decision.
- Owner decision (2026-11-03): **Market Data and Paper Ledger share one physical SQLite database file on Android.** This supersedes the unaccepted two-file proposal.
- Still unresolved: exact canonical Android path; schema/domain boundaries and transaction semantics inside the shared file; Feeder lease placement/fencing; backup destination, cadence, encryption and retention.
- The earlier PC + same-store lease + daily-backup statement is superseded where it conflicts with Android-first and must not be reused as an approved Android configuration.
- PostgreSQL remains an optional/experimental adapter, not the selected T0 canonical backend.
- ADR Android-host correction commit: `55adf229ed4fa6a8cb4626c38562252cf629b1cf`.


## P5.4.21 — T0 Android-First Decision Correction (2026-11-03)

- Owner clarification: T0 runs on **Android**, using Android-hosted **SQLite** as canonical storage. This supersedes the prior PC-hosted T0 statement in the P5.4.20 clarification.
- ADR: `docs/decisions/ADR-001-PRODUCTION-BACKUP-MANIFEST-CONTRACT.md`; Android-host correction commit: `55adf229ed4fa6a8cb4626c38562252cf629b1cf`.
- Current branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Scope: documentation only. No code, schema, workflow, runtime configuration or database changed. No tests/workflows were run.
- Not decided: exact Android canonical path; same-file versus split-file Market Data/Paper Ledger topology; Feeder lease placement; backup destination/cadence/security/retention; restore epoch authority and operational approvals.
- The previous recommendation to split Market Data and Paper Ledger into two SQLite files is **PROPOSED ONLY**, not an owner-approved decision. Do not encode it as accepted until explicitly confirmed.
- No Android filesystem access, canonical DB access/creation, Feeder/API startup, exchange connection, data sync, production backup/restore, or writer activation was performed or authorized.
- `ai_execution_enabled=false`; paper-only; Natural Doze remains `INTERRUPTED / DEFERRED`.
- Status: **PASS** for recording the owner-confirmed Android-first host direction in documentation; **NOT VERIFIED** for Android runtime readiness, canonical path, physical file topology and production recovery.
- Next: resolve whether Market Data and Paper Ledger use one SQLite file or two, then separately resolve the exact Android canonical path and lease placement. Production implementation remains BLOCKED pending D1–D7 approvals.


## P5.4.22 — Shared Android SQLite Topology Decision (2026-11-03)

- Owner decision: T0 runs on Android; Market Data and Paper Ledger share **one physical SQLite database file** on Android.
- This supersedes the unaccepted proposal for two SQLite files. PC remains a separate compute/backtest environment, not the T0 canonical writer.
- ADR: `docs/decisions/ADR-001-PRODUCTION-BACKUP-MANIFEST-CONTRACT.md`; topology decision commit: `cb078005696810830f02401978cdbc98494bf06e`.
- Branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Scope: documentation only. No code, schema, dependency, workflow, runtime configuration or database changed. No tests/workflows were run.
- Remaining open: exact Android canonical path; schema/domain ownership and transaction boundaries; Feeder lease placement/fencing; stable store identity; backup destination/cadence/encryption/retention; D2–D7 manifest and recovery decisions.
- One-file topology enables a single SQLite Online Backup API snapshot for DB-resident Market Data and Paper Ledger state, but does not prove writer quiescence, WAL handling, external control-plane consistency or production restore safety.
- No Android filesystem access, canonical DB access/creation, Feeder/API startup, exchange connection, data sync, production backup/restore or writer activation was performed or authorized.
- `ai_execution_enabled=false`; paper-only; Natural Doze remains `INTERRUPTED / DEFERRED`.
- Status: **PASS** for recording owner-approved Android/shared-file topology; **NOT VERIFIED** for runtime readiness, canonical path, WAL/backup integration and recovery correctness. Production backup/restore remains **BLOCKED**.
- Next: resolve the exact Android canonical path and Feeder lease/fencing ownership, then review D2–D7 before production implementation.


## P5.4.23 — Shared Android SQLite Source-Level Integration Review (2026-11-03)

- Report: `docs/evidence/P5.4.23-SHARED-ANDROID-SQLITE-SOURCE-INTEGRATION-REVIEW-2026-11-03.md`.
- Report commit: `b39cd52e916e8b02afc23c0685a7579ac0cbd2d1`.
- Branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Read-only source files and blob SHAs:
  - `market_data/store.py`: `b28601aed70097afcb7a4eea2dd93ed163ae1cec`.
  - `market_data/storage.py`: `99b66a4d183b8664f28d6638d8d87416d32847c9`.
  - `paper_execution/ledger.py`: `68209ce48a6e5e9a995f93167684133e41cc7f55`.
- Exact branch HEAD SHA was not independently returned by the file-fetch operation: **NOT VERIFIED**.
- Findings: Market Data and PaperLedger accept independent DB paths; no shared canonical path authority/invariant is demonstrated by the inspected files. CandleStore schema initialization is explicit; PaperLedger construction creates/ensures tables and state. PaperLedger writes use `BEGIN IMMEDIATE`; cross-domain transaction coordination is not demonstrated. Both initialization paths request WAL, but production backup coordination is not proven. The inspected source set does not establish Feeder lease/fencing ownership; this is not a claim that no such implementation exists elsewhere.
- Status: **PASS** for recording source-level findings; **NOT VERIFIED** for application shared-path wiring, lease implementation elsewhere, exact branch HEAD, cross-domain atomicity and production WAL backup.
- No code/schema/workflow/runtime changes; no tests/workflows run; no Android filesystem or database access; no Feeder/API, exchange or sync; no production backup/restore or writer activation.
- Next: continue repository source review to locate lease/fencing implementation and wiring. Exact Android canonical path discovery requires separate explicit device/filesystem inspection authorization. Production implementation remains **BLOCKED** pending D1 details and D2–D7. Keep `ai_execution_enabled=false`; Natural Doze remains `INTERRUPTED / DEFERRED`.


## P5.4.24 — Feeder Lease and Fencing Source Review (2026-11-03)

- Report: `docs/evidence/P5.4.24-FEEDER-LEASE-FENCING-SOURCE-REVIEW-2026-11-03.md`.
- Report commit: `77f284cac4697ae6850556afb93244a422d03d37`.
- Branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Inspected source blob identities:
  - `market_data/feeder.py`: `70bba25f1fbf8b3edd3e28756984eed584037cc1`.
  - `market_data/test_feeder_lease.py`: `0512fefc046a48fc8bf46341a1cd936883bcb7b7`.
  - `market_data/feeder_status.py`: `f35309a7429cb73213018fb51ce3fc30419de20d`.
  - `app.py`: `90df28c5409463c524b1d286d5fe502d3b39f59d`.
  - `.github/workflows/t0-manual-validation.yml`: `35fbc75055390ddd5e31258c6d88075b418d2688`.
- Exact branch HEAD SHA was not independently verified.
- Source findings: LeaseStore implements SQLite singleton ownership, generation fencing, TTL 60s and configured heartbeat cadence 15s; lease transitions use `BEGIN IMMEDIATE`; runtime transactions use `mode=rw` and fail closed on storage errors. Contract tests cover concurrent acquisition, takeover generation, stale-owner rejection, heartbeat and missing DB behavior; tests were not run in this review.
- Important gaps: heartbeat cadence configuration does not prove a runtime heartbeat supervisor; LeaseStore accepts an independent DB path and no shared canonical path invariant was found; FeederRuntimeStatusStore reads lease/status from its supplied DB path, while app health fallback uses `MARKET_DATA_DB`; no runtime construction/writer integration was established in inspected files.
- Fencing concern: `authorize_write()` performs lease verification in its own transaction. A separate candle write transaction leaves a TOCTOU window unless the generation is revalidated/serialized inside the canonical write transaction.
- Restore concern: lease generation is stored in the restored SQLite file and can roll back with an old snapshot; external restore epoch/re-fencing authority and a writer-start gate remain required.
- Status: **PASS** for locating and documenting lease implementation; **NOT VERIFIED** for runtime heartbeat, supervisor, write-call-site enforcement, shared Android file wiring, external restore epoch and runtime readiness; production Backup/Restore remains **BLOCKED**.
- No source/schema/workflow/runtime changes; no tests/workflows run; no Android filesystem/DB access; no Feeder/API, exchange or sync; no production backup/restore or writer activation. `ai_execution_enabled=false`; Natural Doze remains `INTERRUPTED / DEFERRED`.
- Next: read-only trace all LeaseStore construction and canonical candle write call sites to establish whether fencing generation is transactionally coupled to writes. Do not access device/runtime without separate explicit authorization.


## P5.4.25 — Feeder Runtime to Canonical Candle Write-Path Trace (2026-11-03)

- Report: `docs/evidence/P5.4.25-FEEDER-CANONICAL-WRITE-PATH-TRACE-2026-11-03.md`.
- Report commit: `95501f32c25f65c7c9136606de02aab3a90ba915`.
- Branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Inspected source blob identities:
  - `market_data/feeder.py`: `70bba25f1fbf8b3edd3e28756984eed584037cc1`.
  - `market_data/store.py`: `b28601aed70097afcb7a4eea2dd93ed163ae1cec`.
  - `market_data/storage.py`: `99b66a4d183b8664f28d6638d8d87416d32847c9`.
  - `market_data/feeder_status.py`: `f35309a7429cb73213018fb51ce3fc30419de20d`.
- Exact branch HEAD SHA was not independently verified.
- Findings: FeederRuntime.start acquires lease, runs recovery, renews lease, starts scheduler and heartbeat. Heartbeat thread exists with default 15s cadence and stops scheduler on lease loss. Scheduler callback is wrapped by LeaseStore.authorize_write before callback execution.
- Critical gaps: preflight authorization uses a separate transaction from the eventual candle write; the actual sync_window upsert transaction was not established. RecoveryCoordinator has an independently injected sync callback; inspected code does not prove it is wrapped by the scheduler guard or fenced inside the canonical mutation transaction. LeaseStore, CandleStore, status store and Paper Ledger each accept paths independently; no production composition root enforcing one physical Android DB path was found in inspected source.
- Status: **PASS** for source trace of heartbeat supervisor implementation and scheduler preflight guard; **NOT VERIFIED** for atomic candle-write fencing, recovery callback fencing, actual sync_window implementation, production construction and shared DB path. Production writer activation and Backup/Restore remain **BLOCKED**.
- No source/schema/workflow/runtime changes; no tests/workflows run; no Android filesystem/DB access; no Feeder/API, exchange or sync; no production backup/restore or writer activation. `ai_execution_enabled=false`; Natural Doze remains `INTERRUPTED / DEFERRED`.
- Next: read-only trace actual `sync_window()`, candle upsert transaction and application composition root. Do not infer missing runtime wiring or access device/runtime without separate explicit authorization.


## P5.4.26 — sync_window and Atomic T0 Write Gateway Trace (2026-11-03)

- Report: `docs/evidence/P5.4.26-SYNC-WINDOW-ATOMIC-GATEWAY-TRACE-2026-11-03.md`.
- Report commit: `b79f2ef91b539698263281c3fe88a391f11015cf`.
- Branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Inspected source blob identities:
  - `market_data/sync.py`: `98e18e327d871809750cbc7e9e59203a03c17320`.
  - `market_data/gateway.py`: `e7fc9cb913f499fe9c4c9e92b7b9e1322a1ccc04`.
  - `market_data/feeder.py`: `70bba25f1fbf8b3edd3e28756984eed584037cc1`.
  - `market_data/store.py`: `b28601aed70097afcb7a4eea2dd93ed163ae1cec`.
  - `market_data/storage.py`: `99b66a4d183b8664f28d6638d8d87416d32847c9`.
  - `market_data/test_sync.py`: `2d74a47e52e7017ffd5c71a56ae24fba44218b8f`.
  - `market_data/test_store.py`: `6a3f2e6c6714926720155eb28484dd21cf977cd5`.
  - `market_data/test_feeder_lease.py`: `0512fefc046a48fc8bf46341a1cd936883bcb7b7`.
  - `app.py`: `90df28c5409463c524b1d286d5fe502d3b39f59d`.
- Exact branch HEAD SHA was not independently verified.
- Correction to P5.4.25: `T0WriteGateway.insert_batch()` uses one SQLite connection and `BEGIN IMMEDIATE`, validates lease owner/generation/expiry before and after the candle batch, then commits; this is atomic fencing for writes routed through Gateway on the same physical DB file. `sync_window()` calls Gateway for each fetched page. CandleStore has no legacy insert methods.
- Fixture tests construct CandleStore, LeaseStore and Gateway with one TemporaryDirectory DB path. This is fixture-only evidence, not proof of production Android wiring.
- Remaining gaps: no production composition root found proving FeederRuntime scheduler and recovery callbacks both route through Gateway; no single canonical Android DB-path authority/invariant found across Gateway, LeaseStore, status store and Paper Ledger; dedicated deterministic Gateway concurrency/final-check test coverage not established.
- Status: **PASS** for source-level atomic Gateway fence, sync_window Gateway use and fixture shared-path construction; **NOT VERIFIED** for production scheduler/recovery callback wiring, canonical Android DB identity and dedicated gateway race coverage. Production writer activation and Backup/Restore remain **BLOCKED**.
- No source/schema/workflow/runtime changes; no tests/workflows run; no Android filesystem/DB access; no Feeder/API, exchange or sync; no production backup/restore or writer activation. `ai_execution_enabled=false`; Natural Doze remains `INTERRUPTED / DEFERRED`.
- Next: P5.4.27 read-only trace all Gateway construction and scheduler/recovery callback composition references. Do not infer missing production wiring or access device/runtime without separate explicit authorization.


## P5.4.27 — Gateway Construction and Feeder Callback Composition Review (2026-11-03)

- Report: `docs/evidence/P5.4.27-GATEWAY-FEEDER-CALLBACK-COMPOSITION-REVIEW-2026-11-03.md`.
- Report commit: `f266e71349a21091eda913a48c34f8954046afdb`.
- Branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Source blob identities:
  - `market_data/gateway.py`: `e7fc9cb913f499fe9c4c9e92b7b9e1322a1ccc04`.
  - `market_data/sync.py`: `98e18e327d871809750cbc7e9e59203a03c17320`.
  - `market_data/feeder.py`: `70bba25f1fbf8b3edd3e28756984eed584037cc1`.
  - `market_data/test_sync.py`: `2d74a47e52e7017ffd5c71a56ae24fba44218b8f`.
  - `market_data/test_store.py`: `6a3f2e6c6714926720155eb28484dd21cf977cd5`.
  - `market_data/storage.py`: `99b66a4d183b8664f28d6638d8d87416d32847c9`.
  - `market_data/feeder_status.py`: `f35309a7429cb73213018fb51ce3fc30419de20d`.
  - `app.py`: `90df28c5409463c524b1d286d5fe502d3b39f59d`.
  - `.github/workflows/t0-manual-validation.yml`: `35fbc75055390ddd5e31258c6d88075b418d2688`.
- Exact branch HEAD SHA not independently verified.
- Critical finding: gateway.py header explicitly states G1 only implements the Gateway primitive and existing writer paths are not routed through it until G2. The explicit sync CLI constructs Gateway and sync_window calls it, but that does not establish FeederRuntime wiring.
- FeederRuntime receives arbitrary scheduler callback and LeaseStore; it adds only a preflight authorize_write wrapper and does not construct Gateway/LeaseFence or a Gateway-backed sync adapter. RecoveryCoordinator accepts a separate arbitrary sync callback and invokes it directly. No reviewed composition root proves either production callback uses Gateway.
- Tests in test_sync.py and test_store.py directly construct Gateway with a temporary DB; they do not prove FeederRuntime scheduler/recovery integration. app.py health path does not construct FeederRuntime/Gateway. T0 manual CI workflow keeps DB path variables empty as an isolation guard.
- Correction to P5.4.26: its primitive-level atomic fencing finding remains valid, but its broad claim that the canonical Feeder writer path uses Gateway was overgeneralized. Production scheduler/recovery migration is BLOCKED / NOT INTEGRATED per G1 scope statement.
- Status: **PASS** for Gateway primitive and explicit CLI/sync source path; **BLOCKED / NOT INTEGRATED** for FeederRuntime scheduler and recovery callback migration; **NOT VERIFIED** for production composition root, canonical Android DB path authority and G2 implementation. Production writer activation and Backup/Restore remain **BLOCKED**.
- No source/schema/workflow/runtime changes; no tests/workflows run; no Android filesystem/DB access; no Feeder/API, exchange or sync; no production backup/restore or writer activation. `ai_execution_enabled=false`; Natural Doze remains `INTERRUPTED / DEFERRED`.
- Next: P5.4.28 inspect repository history and branch source for G2 integration scope/implementation. If G2 is absent, produce a bounded implementation plan and fixture-only test contract; do not change source without explicit authorization.


## P5.4.28 — G2 History, Runtime Composition and Integration Status Review (2026-11-03)

- Report: `docs/evidence/P5.4.28-G2-HISTORY-RUNTIME-COMPOSITION-REVIEW-2026-11-03.md`.
- Report commit: `fb726a0b36f1af4ee42a6a8735a7b53e73a92282`.
- Review branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Observed pre-report review branch HEAD from GitHub compare metadata: `acbe25b8f4c4e7d47e6114ead61469a845042d81`.
- Important correction to P5.4.27: it omitted `market_data/feeder_service.py`, which is the actual composition root. Current branch has `build_runtime()` creating one `canonical_sync` closure and injecting it into FeederScheduler and RecoveryCoordinator (through retry wrapper). Therefore scheduler and recovery Gateway routing are **PASS at source level**; the prior P5.4.27 “NOT INTEGRATED” conclusion is superseded.
- Current source blob SHAs:
  - `market_data/feeder_service.py`: `a160715b66b085afe8a9650dcf8c1e6ea3a3285e`.
  - `market_data/feeder.py`: `70bba25f1fbf8b3edd3e28756984eed584037cc1`.
  - `market_data/sync.py`: `98e18e327d871809750cbc7e9e59203a03c17320`.
  - `market_data/gateway.py`: `e7fc9cb913f499fe9c4c9e92b7b9e1322a1ccc04`.
  - `market_data/store.py`: `b28601aed70097afcb7a4eea2dd93ed163ae1cec`.
  - `market_data/storage.py`: `99b66a4d183b8664f28d6638d8d87416d32847c9`.
  - `market_data/test_feeder_lifecycle.py`: `d48e0171813cedc1d82672c51836bd713035791c`.
  - `market_data/test_feeder_atomic_fencing.py`: `db66d6577f16d9b057e4dd77f5cb75a78660d05f`.
  - `market_data/test_sync.py`: `2d74a47e52e7017ffd5c71a56ae24fba44218b8f`.
  - `market_data/test_store.py`: `6a3f2e6c6714926720155eb28484dd21cf977cd5`.
- G2 branches found:
  - RED contracts: `feature/p5-3-11-5-g2-red-tests-20261103`, head `8c33a23a95a246a21654a56e7829be86b4856cdb`.
  - Routing: `feature/p5-3-11-8-g2-gateway-routing-20261103`, head `cc81721821670cef499ca4a8adee1e2e10769d4d`.
  - GREEN integration: `integration/p5-3-11-g2-gateway-green-20261103`, head `b271efae590528a278f44c4e7c8e67290cc81429`, ancestor of current review branch.
- Historical PR #123 G2 RED evidence: GitHub Actions run `41572948926`, exact SHA `c68b9515862ae1a5815c1e9d9064453da58e444f`, 18/18 G2 contracts; 210 market_data regression tests, zero failures/errors, 8 Timescale tests skipped; artifact `13202670154`, SHA-256 `4aa0b32a727bd7ad6d56889f90f877efc11509daba61873d6fdd44652116e8d3`.
- Historical PR #125 G2 GREEN evidence: PR branch head/tested SHA `b271efae590528a278f44c4e7c8e67290cc81429`; GitHub Actions run `41591818246`; artifact `13209729706`, SHA-256 `1953b91e21578c8f5d9e60829a40f76a9d4d5f135097dd52b496339450df8e77`. Reported groups: G1 16/16, G2 routing/lease/fencing/lifecycle 66/66, T0 regressions 96/96, operational/CI policy 16/16, pipeline/FreqAI 56/56; compile and shadow-only isolation PASS. PR #125 description says Draft/unmerged. Historical evidence does not validate current branch SHA.
- PR #124 routing body records a stale Codemagic Build #132 and merge conflict/dirty state; it is not accepted as current validation. No Codemagic use is authorized; GitHub Actions remains the only runner.
- Production Feeder factory source aligns `MARKET_DATA_DB`, LeaseStore, Gateway, read facade and status store to the same SQLite path and rejects a distinct lease DB. This does not prove the actual Android canonical path or physical runtime file.
- Current `CandleStore` no longer exposes legacy `insert()` / `insert_fenced()` writer APIs in inspected source. Repository-wide mutation-path audit not repeated.
- Test gap: lifecycle tests assert Recovery calls sync_window with the supplied Gateway and typed LeaseFence, but do not directly invoke the Scheduler callback and assert the Gateway/token. Add fixture-only scheduler callback assertion in P5.4.29.
- Path gap: lower-level `build_runtime()` accepts independently supplied store/Gateway/LeaseStore without enforcing same DB identity. Production factory enforces it. Paper Ledger still has independent path acceptance per P5.4.23; canonical Android path authority across Feeder + Paper Ledger remains NOT VERIFIED.
- Status: **PASS** G2 source composition (Scheduler and Recovery same Gateway-backed callback); **PASS** production Feeder path alignment at source level; **NOT VERIFIED** scheduler callback integration test, Paper Ledger unified DB authority, actual Android canonical path/runtime, current-branch exact-head CI. PostgreSQL/Timescale canonical writer NOT CERTIFIED.
- No source/test/workflow/runtime changes; no tests/workflows run. No canonical/Paper DB or Android filesystem access, no Feeder/API, exchange, sync, production backup/restore or writer activation. `ai_execution_enabled=false`; Natural Doze remains `INTERRUPTED / DEFERRED`.
- Next P5.4.29: add a fixture-only test contract for Scheduler callback invocation and Gateway/LeaseFence identity; consider fail-closed mismatched path test if identity can be exposed safely. Execute only on GitHub Actions with disposable fixtures after explicit test authorization. No Codemagic; no PR merge or new PR.


## P5.4.31 — Shared Gateway Lifecycle Contract (updated 2026-11-03)

- Evidence report: `docs/evidence/P5.4.31-SHARED-GATEWAY-LIFECYCLE.md`.
- Test implementation commit: `d8833d0b3a0aa768ddc7d8079e09a7c00e95697f`.
- Evidence report PASS update commit: `292d56bbd8f92c587b413a100e46638c03ceb5b1`.
- Branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Exact tested source SHA: `32f7e729de9f1a85e25bfb745e12b81c1e85060d`.
- Workflow: [G2 integration GREEN #41661665771](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41661665771), event `workflow_dispatch`, attempt 1, conclusion `success`.
- Job: `G2 and T0 isolated regression acceptance`, ID `126006148696`, conclusion `success`.
- New test `test_scheduler_and_recovery_share_injected_gateway_and_current_fence`: PASS.
- Test totals: G1 16, G2 69, T0 96, CI contracts 24, consumer regressions 56; **261 total PASS**. Python compile and shadow-only isolation PASS.
- Artifact: `p5-3-11-g2-integration-green-41661665771`, ID `13242762087`, 9,494 bytes, SHA-256 `23fbc2f8198773098062522a4bde67bd3589c2178ceeeb6d6e8f9aea4051bc4a`, expires `2026-11-10T15:13:38Z`. [Artifact URL](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41661665771/artifacts/13242762087).
- Status: **PASS — fixture-only Shared Gateway Lifecycle contract verified on exact SHA**. Production code unchanged.
- Limits: no Feeder startup/service, canonical DB or Paper Ledger access, exchange connectivity, data sync, Android instrumentation, SIGKILL, PC multiprocess, Timescale integration or production backup/restore. `AI_EXECUTION_ENABLED=false`; no live orders. This CI result does not certify production runtime readiness.
- Next: preserve these boundaries; do not initiate runtime/production operations. Define and authorize the next bounded phase separately.


## P5.4.32 — Production SQLite DB Identity Contract (updated 2026-11-03)

- Evidence report: `docs/evidence/P5.4.32-PRODUCTION-DB-IDENTITY-CONTRACT.md`.
- Baseline HEAD after P5.4.31 evidence: `e0397a179602ecf0e03c5dc98583dd7f8e155a10`.
- Fixture-only test commit: `4976d25485f99dbe2707714a9afd04ef54ed9409`.
- Evidence report commit: `fb56db6e9dea3ff8e96377bb6f28323216514c75`.
- Branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Added three tests to `market_data/test_feeder_gateway_contract.py`:
  - Distinct lease DB path is rejected before exchange construction/runtime composition; neither file is created.
  - Store, T0 Gateway, LeaseStore and runtime status store resolve to the same file when configured paths are lexically different but equivalent.
  - Omitted lease DB path defaults to canonical `MARKET_DATA_DB`.
- Existing G2 integration GREEN workflow already runs the containing test module; no workflow change.
- Production source unchanged. Only temporary nonexistent paths and stub CCXT are used; no DB open/create, network or runtime startup.
- Source read-back: PASS; all three test names are present. Local execution: NOT RUN. Exact-SHA GitHub Actions: PENDING.
- Status: **IMPLEMENTED / NOT VERIFIED**; await manual G2 integration GREEN workflow on final branch HEAD, then record exact SHA, job/test results, artifact ID and checksum.
- Scope limitation: this verifies the production factory's SQLite path invariant. Lower-level dependency-injected `build_runtime()` still accepts independently supplied components; identity of arbitrary injected paths is NOT CERTIFIED here.
- Prohibited: Feeder startup/service, canonical DB/Paper Ledger access, exchange connectivity, data sync, Android instrumentation, PC multiprocess, Timescale integration, backup/restore or live execution. `AI_EXECUTION_ENABLED=false`.
- Next: run existing G2 integration GREEN workflow on this branch and verify the three new contracts plus all required regressions. No production activation or phase advance before evidence review.

## P5.4.32 — Production SQLite DB Identity Contract (CI verified, updated 2026-11-03)

- Evidence report: `docs/evidence/P5.4.32-PRODUCTION-DB-IDENTITY-CONTRACT.md`.
- Branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Test implementation commit: `4976d25485f99dbe2707714a9afd04ef54ed9409`.
- Evidence report PASS update commit: `8e6c1a50cd95b8ac077bdd352a24e4a1ce381f93`.
- Exact tested source SHA: `cddea2e65c4123e2478766b55124c14b36e85671`.
- Workflow: [G2 integration GREEN #41662758250](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41662758250), event `workflow_dispatch`, attempt 1, run #76, conclusion SUCCESS.
- Job: `G2 and T0 isolated regression acceptance`, ID `126009991274`, SUCCESS.
- Three P5.4.32 contracts PASS:
  - `test_production_factory_rejects_distinct_lease_database_before_composition`.
  - `test_production_factory_composes_all_sqlite_roles_on_same_resolved_path`.
  - `test_production_factory_defaults_lease_database_to_canonical_database`.
- Regression groups: G1 16/16; G2 72/72; T0 96/96; CI contracts 24/24; consumer regressions 56/56. Separate invocations; 264 passing test invocations, not asserted unique.
- Python compile PASS; `ISOLATED_SHADOW_ONLY=PASS`; `AI_EXECUTION_ENABLED=false`.
- Artifact: `p5-3-11-g2-integration-green-41662758250`, ID `13243775760`, 9,581 bytes, expires `2026-11-10T15:19:54Z`; [artifact](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41662758250/artifacts/13243775760).
- Artifact SHA-256: `8b92b04499e09c6c0fbb430e79056b0486b8d20b9711a8699b469624a36d2476`. Downloaded ZIP integrity test passed and locally computed SHA-256 matched GitHub digest.
- Status: **PASS — fixture-only DB identity contract verified on exact SHA**. Production source/workflow unchanged.
- Limits: tests validate production factory SQLite path composition with disposable/nonexistent paths and stub CCXT only. Lower-level injected `build_runtime()` arbitrary path identity remains NOT CERTIFIED. No canonical DB/Paper Ledger access, Feeder startup, exchange, sync, Android instrumentation, Timescale, backup/restore or live execution. This is not production runtime certification.
- Next: wait for a separately scoped task/approval. No automatic production activation or phase advance.

## P5.4.33 — Shared Android SQLite Boundary Review

- Evidence: `docs/evidence/P5.4.33-SHARED-ANDROID-SQLITE-BOUNDARY-REVIEW.md`; evidence commit `3766f8f6d310036623f71535f8602db4380daee2`.
- Reviewed source ref: `ed0177709fe5e8a20b72b2e9c9bda24e4cddf6a2`.
- T0 factory aligns its SQLite roles to one resolved path. PaperLedger accepts an independent `db_path` and initializes its own SQLite tables. The inspected app entrypoint does not compose PaperLedger with Feeder.
- Status: **PASS** for bounded source review; **NOT VERIFIED / BLOCKED** for shared physical Android DB identity and canonical path authority.
- Documentation-only; no tests/workflows or runtime actions. No Android filesystem, canonical DB, Feeder startup, exchange or backup/restore access. `AI_EXECUTION_ENABLED=false`.
- Next: identify the Android composition root and authoritative path provider, then specify a fixture-only cross-component identity contract. No production activation.

## P5.4.34 — Android-First Canonical Ownership Correction (updated 2026-11-03)

- Evidence: `docs/evidence/P5.4.34-PC-CANONICAL-ANDROID-SHADOW-BOUNDARY.md`.
- Correction commit: `e5caefd36429209cc4b24f92879a25ef52ce1d5a`.
- Original review source ref: `c7412c4c24c4b54803903c913d1d48ad045828ba`.
- The previous PC-canonical / Android-shadow conclusion is withdrawn as inconsistent with the user's confirmed architecture.
- Confirmed owner direction: Android is the primary data/monitoring environment; T0 canonical SQLite is intended on Android after validation and explicit activation approval; Android is the initial sole T0 writer once activated. Windows PC is for AI training, FreqAI, backtesting and analysis, not current canonical ownership. GitHub stores source/evidence and GitHub Actions runs isolated CI.
- Any future transfer of canonical write ownership to PC requires an explicit architecture decision and controlled handover with fencing, identity verification and rollback.
- Source observations retained: inspected Android service uses `SharedPreferences("strategy_state_v1")`; inspected source did not establish Android canonical SQLite/Feeder/Paper Ledger composition. Python Feeder and Paper Ledger modules do not establish PC canonical ownership.
- Android canonical DB path/schema, Feeder runtime composition, Paper Ledger Android persistence, and whether Paper Ledger shares one physical SQLite file with T0 remain **NOT VERIFIED**. Android-first does not automatically decide the shared-file question.
- Status: **PASS** for documentation correction; **NOT VERIFIED** for implementation; production canonical DB/Feeder activation **NOT ACTIVATED / NOT AUTHORIZED**.
- Documentation-only. No tests/workflows, Android device/DB, PC canonical DB, Feeder, exchange, sync, backup/restore or execution touched. `AI_EXECUTION_ENABLED=false`.
- Next: source-only inventory and gap assessment against Android-first; no production activation.

## P5.4.35 — Android Persistence Source Inventory (updated 2026-11-03)

- Evidence: `docs/evidence/P5.4.35-ANDROID-PERSISTENCE-SOURCE-INVENTORY.md`.
- Evidence commit: `14cbea5d57a02d916b5ccf4033ebcae545e93db8`.
- Review baseline: `80f98123e3365b02a482352f8d829ef61a90758b` (Android-first handoff correction).
- Bounded Android source review inspected MainActivity, StrategyMonitorService, CompleteDashboard, AlertHistoryStore, PaperOrderHistory, app Gradle dependencies and AndroidManifest.
- Durable Android monitor/dashboard state is currently stored in `SharedPreferences("strategy_state_v1")`: strategy state/cursor, monitor health, alert dedupe/history, scanner state, order-book snapshots and UI preferences. Alert history is a JSON array capped at 100.
- PaperOrderHistory is a read/display component for a bounded server snapshot, not local persistence.
- Inspected app dependencies do not declare Room, SQLite wrapper or AndroidX DataStore. No canonical Android SQLite path provider, T0 schema owner, Android T0WriteGateway/LeaseStore/Feeder composition, or Android Paper Ledger persistence integration was established by the reviewed files.
- Python `paper_execution/ledger.py` owns an injected SQLite `db_path`; Python `market_data/feeder_service.py` composes T0 storage/Gateway/lease/status from environment paths. These do not establish PC canonical ownership and are not shown composed into Android.
- Status: **PASS** for bounded source inventory; **NOT VERIFIED** for complete Android source-set inventory, Android canonical DB/path/schema, Feeder composition, Paper Ledger/Risk/Paper State persistence and runtime behavior; production activation **BLOCKED / NOT AUTHORIZED**.
- Documentation-only. No tests/workflows, device/filesystem/DB, Feeder, exchange, sync, backup/restore or execution touched. `AI_EXECUTION_ENABLED=false`.
- Next: P5.4.36 design-only Android canonical storage contract: path authority, schema, Paper Ledger/Risk State boundary, single-writer fencing, PC read interface and backup/restore invariants. No implementation or activation.

## P5.4.36 — Android Canonical Storage Architecture Contract (updated 2026-11-03)

- Evidence: `docs/evidence/P5.4.36-ANDROID-CANONICAL-STORAGE-DESIGN.md`.
- Design evidence commit: `f2bee33f8df5af0177df709249bf9ee5cf4c22e5`.
- P5.4.35 reconciliation commit: `bf0a035fbdbaf7ec6502fa5262296748f98b4dd5`.
- P5.4.34 subsequent-decision note commit: `29943922671f6aa015151908c85485bb45f1cdfe`.
- Reconciled the evidence chronology: ADR-001 records the explicit owner selection of **one shared physical Android SQLite file for T0 Market Data + Paper Ledger**. P5.4.34's earlier open status was correct when written but is superseded for topology only; P5.4.35's earlier undecided wording is stale and corrected. The topology decision is not proof of implementation.
- Design contract: one Android canonical path authority and single DB identity; explicit domain ownership; controlled schema migration; coordinated transaction boundaries; Android sole canonical writer; PC read-only consumer; shared risk/ledger boundary; fencing and external post-restore epoch; WAL-aware backup/restore; fixture-only acceptance gates.
- Still OPEN/NOT VERIFIED: exact Android path, Android composition root, migration authority, exact cross-domain transaction set, lease placement/Android fencing integration, external recovery epoch authority, Paper Ledger/Risk persistence integration, backup policy and runtime readiness.
- Status: **PASS** for design-only contract and evidence reconciliation; **NOT VERIFIED** for implementation; production activation **BLOCKED / NOT AUTHORIZED**.
- Documentation-only. No tests/workflows, device/filesystem/DB, Feeder, exchange, sync, backup/restore or execution touched. `AI_EXECUTION_ENABLED=false`.
- Next: P5.4.37 bounded source-only composition-root/path-authority trace. No device path probing, DB creation/opening or runtime activation.

## P5.4.37 — Android Composition Root & Canonical Path Authority Source Trace (updated 2026-11-03)

- Evidence: `docs/evidence/P5.4.37-ANDROID-COMPOSITION-ROOT-PATH-AUTHORITY-SOURCE-TRACE.md`.
- Evidence commit: `3fad8b26d3533abde02ed5761b6f9fb9a73f7b28`.
- Reviewed MainActivity, AndroidManifest, app Gradle dependencies, StrategyMonitorService, FiveLayerStandaloneDashboard, FiveLayerPanel, FiveLayerApi and Android README.
- No custom Android Application composition root, canonical DB path provider, Room/SQLite/DataStore dependency, migration coordinator or shared DB transaction boundary is visible in the reviewed entrypoints.
- Normal app starts StrategyMonitorService on Activity resume; service directly constructs MarketEngine/StrategyEngine/OrderBookEngine/Scanner and persists monitor/strategy/scanner/order-book state in SharedPreferences `strategy_state_v1`.
- Parallel `.paper` variant mounts FiveLayerStandaloneDashboard only and skips StrategyMonitorService. FiveLayerPanel persists API URL locally, keeps tokens and fetched state in Compose memory, and reads/writes the remote Paper API over HTTPS. README states variants may share the same server-side paper ledger when using the same API; that is not Android-local canonical SQLite.
- Source trace finds no Android T0 CandleStore, write Gateway, LeaseStore, Feeder composition, PaperLedger/Risk repository or shared SQLite path injection.
- Status: **PASS** for bounded source trace; **NOT VERIFIED** for complete source-set storage inventory and all Android canonical persistence/composition; production implementation/activation **BLOCKED / NOT AUTHORIZED**.
- Documentation-only; no tests/workflows, device/filesystem/DB, Feeder, exchange, sync, backup/restore or execution touched. `AI_EXECUTION_ENABLED=false`.
- Next: P5.4.38 design-only Android composition-root interface/dependency wiring contract, including regular/parallel variant database identity and duplicate-writer prevention. No implementation or activation.

## P5.4.38 — Android Composition Root & Dependency Wiring Contract (updated 2026-11-03)

- Evidence: `docs/evidence/P5.4.38-ANDROID-COMPOSITION-ROOT-WIRING-CONTRACT.md`.
- Evidence commit: `6797f69d1fda1292c5607e0b7d11dbd1d1cc2b02`.
- Design-only contract defines one application-scoped CanonicalRuntime owner, one opaque DB identity/transaction coordinator injected into T0, lease/fencing, Paper Ledger, Shared Risk/Kill Switch, equity, audit and read-only projections.
- Lifecycle is fail-closed: process start does not create schema/start Feeder/connect exchange; read-only preflight precedes explicitly authorized migration; readiness is separate from writer activation; restart revalidates fencing/recovery/Kill Switch.
- Critical Android sandbox constraint: regular and `.paper` variants have distinct application IDs. Their app-private DB files are not the same physical file. One package/process must own the canonical SQLite file and writer capability. A second package must be a typed authenticated IPC client or remote-only API client; no raw path/DB handle/lease authority, no shadow DB.
- Packaging choice remains OPEN: (A) same application ID for local variants; (B) dedicated canonical host plus authenticated IPC; (C) separate `.paper` app remains remote API-only. This document does not select among them.
- Status: **PASS** design contract; **NOT VERIFIED** implementation/runtime; **BLOCKED / OWNER DECISION REQUIRED** for package ownership choice; implementation and production activation **NOT AUTHORIZED**.
- Documentation-only. No tests/workflows, package changes, dependencies, device/filesystem/DB, Feeder, exchange, sync, backup/restore or execution touched. `AI_EXECUTION_ENABLED=false`.
- Next: P5.4.39 resolve package ownership choice and record owner decision. No implementation before that choice.

## P5.4.39 — Android Canonical Host + Authenticated IPC Owner Decision (updated 2026-11-03)

- Owner explicitly selected **Option B — Dedicated canonical host package plus authenticated IPC client**.
- Accepted ADR: `docs/decisions/ADR-002-ANDROID-CANONICAL-HOST-IPC-OWNERSHIP.md`; ADR commit `1245d0a638350ece0ef405f0c2a821183d620645`.
- Decision evidence: `docs/evidence/P5.4.39-ANDROID-CANONICAL-HOST-IPC-OWNER-DECISION.md`; evidence commit `997b6b4097c75cfbc1a65dfa6bbfe02a3d011aaa`.
- P5.4.38 reconciliation commit: `3a36288440001720e3d4be7b83a329c8d1941fc2`; its former open option selection is superseded by ADR-002.
- Binding invariants: one designated host package/process owns the one physical Android canonical SQLite file and sole writer capability; the separately installed `.paper` package is a typed authenticated IPC client, receives no raw DB path/handle/file descriptor/SQL/lease/writer credential, and cannot create a shadow DB. Host revalidates caller, readiness, fencing/recovery, idempotency and Kill Switch. All Core/AI paper intents use the same host-side Shared Risk/Paper Ledger boundary. PC remains read-only.
- Still OPEN: exact host application ID/variant, IPC primitive (bound service vs ContentProvider), signature permission/caller allowlist, API schema/versioning/retry/idempotency details, process lifecycle, DB path/driver/migrations and threat-model review.
- Status: **PASS** owner decision recorded; **NOT VERIFIED** implementation/device behavior; runtime implementation and activation **NOT AUTHORIZED**.
- Documentation-only. No tests/workflows, code/dependency/package changes, IPC components, DB/path/device, Feeder, exchange, sync, backup/restore or execution touched. `AI_EXECUTION_ENABLED=false`.
- Next: P5.4.40 design-only IPC threat model and typed contract specification. No runtime implementation until separately authorized.



## P5.4.40 — Android IPC Threat Model and Typed Contract Specification (updated 2026-11-03)

- Evidence: docs/evidence/P5.4.40-ANDROID-IPC-THREAT-MODEL-TYPED-CONTRACT.md.
- Evidence commit: eccd71c131f47ff20023c3ba68655516a205bf7c.
- Baseline source HEAD: b7db2c7e475b603cfab8fa273096778ec9795705.
- Scope: documentation-only threat model and typed IPC contract for ADR-002's dedicated canonical host plus authenticated .paper client.
- Defined trust zones and threat actors; verified Binder UID/package/signing identity; signer allowlist, rotation and revocation; signature-level permission and exported-component constraints; forbidden capabilities; bounded read-only projections; typed Paper intent/cancel commands; host-side readiness, fencing/recovery, Kill Switch, risk and audit sequence; versioned envelopes; timeout/idempotency/transaction-unknown reconciliation; process death/reconnect/upgrade; privacy and abuse safeguards.
- Added fixture-only GitHub Actions acceptance matrix using synthetic identities and isolated fixtures. It is a proposed plan only; no workflow was run.
- Explicitly retained OPEN decisions: host application ID/variant, IPC primitive, permission/manifest details, signing rotation policy, DTO/serialization schema, idempotency persistence/retention, transaction boundary, quotas/timeouts, lifecycle/process model, compatibility and audit policy.
- Status: **PASS** for design specification; **NOT VERIFIED** for implementation, Android Binder/signing/device behavior; **NOT RUN** for tests/workflows; implementation and runtime activation **NOT AUTHORIZED**.
- No code, dependencies, package IDs, exported components, database/path, device, Feeder, exchange, market-data sync, backup/restore or writer activation touched. Paper-only; AI_EXECUTION_ENABLED=false.
- Next: P5.4.41 design review and resolution of minimum owner decisions only. No runtime implementation without separate explicit authorization.


## P5.4.41 — Android IPC Security Contract Review (updated 2026-11-03)

- Evidence: docs/evidence/P5.4.41-ANDROID-IPC-SECURITY-CONTRACT-REVIEW.md.
- Evidence commit: 070053af2366607827deee38c377c0f0f63eb8d2.
- Evidence blob: 0b0e113b00d8bb741e27337c43c999a12acf1af0.
- Review baseline HEAD: 9709c3d8a853b6a1ffb8fe839c8cae796a78e052.
- Scope: documentation-only review of ADR-002 and P5.4.40. No code, manifest, package, signing, dependency, device or runtime changes.
- Verdict: **CONDITIONAL PASS** for design review only.
- Finding F-01: correct mutation ordering so a retry with an already committed idempotency key returns the durable recorded result even if current Kill Switch/risk state has changed. Authenticate/authorize and validate first; resolve existing idempotency key before dynamic readiness/risk checks; only new commands pass current readiness/fencing/Kill Switch/risk gates and enter atomic command+ledger+audit commit. Conflicting payload for same key is rejected.
- Recommendation F-02: prefer an explicit Android bound Service with narrow Binder/AIDL typed methods and a custom signature-level bind permission over ContentProvider's URI/CRUD surface. This is a recommendation only, NOT an owner-approved primitive.
- Signing recommendation: common controlled installed signing identity where feasible, plus host-side expected package and signer/lineage allowlist; staged rotation and explicit revocation. Exact certificate identities and release-key policy remain owner decisions.
- Host package ID/variant remains OPEN; no ID was inferred or changed. .paper client identity requires confirmation. DTO schemas, serialization, transaction boundaries, idempotency retention, limits, compatibility and audit policies remain to be specified.
- Status: **CONDITIONAL PASS** design review; **OWNER DECISION REQUIRED** for IPC primitive, canonical host package/variant, .paper package identity and signing policy; **NOT VERIFIED** implementation/device behavior; **NOT RUN** tests/workflows; runtime implementation **NOT AUTHORIZED**.
- No GitHub Actions workflow or tests were run. Paper-only; AI_EXECUTION_ENABLED=false. No DB, Feeder, exchange, sync, backup/restore or writer activation.
- Next: obtain owner decisions, then P5.4.42 detailed implementation design. Do not implement runtime components without separate authorization.


## P5.4.41 owner decisions and P5.4.42 design (updated 2026-11-04)

- Active branch: `feature/p5-4-1-post-merge-validation-20261103`.
- P5.4.41 owner decisions explicitly confirmed 2026-11-04: **IPC = Bound Service** (explicit binding + typed Binder/AIDL + signature-level permission); **canonical host = existing regular variant**; **signing = same controlled installed signing identity for regular host and .paper client**.
- ADR-002 updated to record these owner decisions. The .paper variant remains an IPC client only; regular is the single canonical host and sole SQLite/writer/risk authority. No client DB access, raw path/FD/SQL, shadow DB or fallback writer.
- P5.4.42 design report: `docs/evidence/P5.4.42-ANDROID-CANONICAL-HOST-IPC-IMPLEMENTATION-DESIGN.md`.
- P5.4.42 defines service boundary, two-layer caller authorization, proposed typed read/query and paper-only mutation contract, bounded DTO envelope, corrected durable idempotency ordering, atomic command+ledger+audit transaction, Shared Risk Engine parity, lifecycle/version-skew rules and future fixture-only acceptance plan.
- Owner decision policy is recorded, but exact regular/.paper application IDs, installed signer digest/lineage, service/permission names, DTO bounds, idempotency retention, transaction/schema mapping and compatibility matrix remain OPEN or NOT VERIFIED.
- Status: **PASS** for recording owner decisions and producing documentation design baseline; **NOT RUN** (no tests/workflow); implementation/device/runtime **NOT VERIFIED / NOT AUTHORIZED**.
- No code, Gradle, manifest, package ID, signing configuration, dependencies, DB, device or runtime changed. No canonical DB access, Feeder, exchange, market-data sync, backup/restore or execution. Keep `AI_EXECUTION_ENABLED=false`.
- Next permitted step: read-only source inventory of regular/.paper package IDs, signing declarations and manifest/exported-component baseline. Do not inspect private keys or canonical storage. Implementation requires separate explicit authorization.
- ADR update commit: `d104aae6bbfaf14f3d8c09fdd0410d2c2e23e5be`.
- P5.4.42 evidence commit: `ee8be590dc93d058028f35ebab27940a06f34c54`.
- Handoff update commit (initial P5.4.44 handoff append): `254e6285af28b25fa2810a8003a3f9b9481fd4c7`.


## P5.4.43 — Android read-only package/signing/manifest inventory (updated 2026-11-04)

- Evidence: `docs/evidence/P5.4.43-ANDROID-READONLY-PACKAGE-SIGNING-MANIFEST-INVENTORY.md`.
- Evidence commit: `80ffe91abc67163d2acf948d2cffec7b75923e4e`.
- Exact inspected source/tree SHA: `c6e48c80140f06d528fade286e5267093ec302e1` (recursive tree complete; 296 entries; not truncated).
- Source-derived package IDs: regular unsuffixed `com.kenznguyen.btclivealerts`; parallel/Paper `com.kenznguyen.btclivealerts.paper` via `applicationIdSuffix=".paper"`.
- Terminology correction: Paper is currently a `parallel` build type using `initWith(debug)`, not a product flavor. Owner-approved regular host maps to unsuffixed application ID; debug vs release host deployment remains open.
- Signing source: regular release explicitly uses environment-driven `release` signing config; parallel inherits debug build type and does not explicitly use regular release signing. Therefore matching signer for regular release + parallel is **NOT VERIFIED** and not demonstrated by source. No keystore/private key or secret was accessed.
- Main manifest: MainActivity exported=true launcher; StrategyMonitorService exported=false; no custom signature permission, exported IPC service, AIDL or ContentProvider declaration. Merged manifests/APKs/install state not inspected.
- README contains historical Codemagic instructions inconsistent with current GitHub Actions-only handoff; left unchanged.
- Status: **PASS** for static source inventory at exact SHA; **NOT RUN** tests/build/workflow; installed signer, merged manifest and runtime **NOT VERIFIED**; code/build/signing/runtime changes **NOT AUTHORIZED**.
- No code/config/manifest/signing/dependency/device/database/Feeder/exchange/sync/backup/restore/writer or execution changes. Keep `AI_EXECUTION_ENABLED=false`.
- Next: P5.4.44 bounded signing/variant compatibility design; determine whether existing artifacts already prove matching installed signer. If not, document the needed build policy and obtain explicit approval before any Gradle/manifest change.


## P5.4.44 — Android signing and variant compatibility design (updated 2026-11-04)

- Evidence: `docs/evidence/P5.4.44-ANDROID-SIGNING-VARIANT-COMPATIBILITY-DESIGN.md`.
- Evidence commit: `ab2a6f40b7ab874b82a96ce5064f4b94579ecf85`.
- Baseline branch HEAD before evidence: `4966479befdb33b9e724e0d3a82dc1410862f2e9`.
- Android source inventory SHA remains `c6e48c80140f06d528fade286e5267093ec302e1`.
- Bounded GitHub metadata check: Releases API returned no releases; no Android/APK build appeared in the latest 100 Actions run metadata entries. This is not proof that no expired/older Actions artifact ever existed.
- P5.4.12 retirement evidence confirms there was no active GitHub Actions APK build/publish workflow at that time and no APK was built/signed/installed/published in that increment. Android workflow definitions currently visible in repository are archived under `ci/archive/github-actions/`.
- Archived verifier `ci/verify-android-apks.py` compares the DEBUG and parallel certificate fingerprints and explicitly labels signing as DEBUG. Its fixture tests use synthetic inputs; neither proves regular-release/.paper release signer parity.
- No GitHub Release or verified regular-host + .paper APK pair was located. No APK payload or signer certificate was inspected.
- Verdict: **CONDITIONAL PASS** for bounded source/metadata review and design recommendation; **BLOCKED / NOT VERIFIED** for actual signing compatibility. Regular release uses environment-driven release signing; parallel inherits debug and does not explicitly use regular release signing.
- Proposed next acceptance contract: separately approved manual-only GitHub Actions workflow, pinned source SHA, build both regular host and parallel/.paper from the same SHA, explicitly use the approved controlled signer for both, verify package/version/signature/lineage independently, publish source/run/artifact/checksum evidence, then download and independently inspect payloads. No automatic push-triggered APK build; Codemagic remains retired.
- Owner approval still required before any Gradle signing change, workflow creation/reactivation, secret use, APK build or install. No approval inferred.
- No tests or workflows run for this documentation-only increment. No code, Gradle, manifest, signing, dependency, package ID, workflow, device, DB, Feeder, exchange, market-data sync, backup/restore, writer or execution state changed. `AI_EXECUTION_ENABLED=false`.
- Next: obtain explicit owner approval for a manual-only paired-APK GitHub Actions signing workflow and the parallel/.paper release-signing policy. Until then, do not change Gradle/manifest/workflows or build/install APKs.
- Handoff update commit: `254e6285af28b25fa2810a8003a3f9b9481fd4c7`.



## P5.4.45 — Paired Android release signing implementation (updated 2026-11-04)

- Evidence: `docs/evidence/P5.4.45-ANDROID-PAIRED-RELEASE-SIGNING-IMPLEMENTATION.md`.
- Evidence commit: `c05cac998bd516631502e19341f9856b5035dfda`.
- Final implementation source SHA tested by GitHub Actions: `8c9cbdb66cab58c457c85e140462da4dab156ca9`.
- Gradle: `parallel` build type now explicitly uses the existing environment-backed `release` signing config; regular release remains unchanged. Application IDs are unchanged.
- Added `.github/workflows/android-release-pair.yml`, trigger is only `workflow_dispatch`, exact SHA required and bound to `GITHUB_SHA`, branch restricted to this existing branch, read-only repository permission, secret presence checks for four existing Android signing secret names, expected alias `btc-chart-release`, runner-temp keystore restoration/cleanup, Android unit tests, `assembleRelease` + `assembleParallel`, paired APK identity/signer/hash verifier and 14-day artifact publication. No push/PR trigger.
- Added `ci/verify-android-release-pair.py`; checks exact source SHA, package ID, label, launcher activity, versionCode/versionName, valid signatures, same signer certificate SHA-256, APK SHA-256 and size.
- Added `ci/test_android_release_pair.py`: **5/5 PASS** (synthetic fixtures; no real APK signing evidence).
- Updated `ci/test_ci_policy.py`: **25/25 PASS** in G2; verifies manual-only workflow, exact SHA, secret gates, release signer config and allowlist.
- P5.4.1 integrated workflow: run [41731773366](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41731773366), exact SHA `8c9cbdb66cab58c457c85e140462da4dab156ca9`, **SUCCESS 5/5 jobs** (preflight, G1, G2, T0, combined publication).
- Artifacts from run 41731773366: combined P5.4.1 ID `13277745786`, G2 ID `13277431031`, T0 ID `13276353143`, G1 ID `13276343000`. GitHub ZIP digest metadata is recorded in the P5.4.45 evidence. Payloads were not downloaded/re-hashed; none are Android APK artifacts.
- Default branch is `main`; `.github/workflows/android-release-pair.yml` is not yet present on `main`. The Actions UI's Run workflow control requires the workflow file to be present on the default branch. No open PR exists for this post-merge branch; no new PR and no direct main update were made. Manual APK workflow dispatch remains **BLOCKED** pending owner approval to promote only the workflow file (or another explicitly approved promotion path).
- Android signing secrets were not read; secret existence/validity is **NOT VERIFIED**. Workflow checks presence and alias at dispatch.
- Actual Android unit tests/build/signing, real signer fingerprint parity, APK artifact and APK payload checksum remain **NOT RUN / NOT VERIFIED**. No device/installation/IPC testing.
- Early workflow-file validation records on prior commits (run IDs `41731548513`, `41731588091`, `41731601202`, `41731670605`) failed with no jobs; no signing/build job executed. Final P5.4.1 integrated run 41731773366 passed on the corrected final source SHA.
- No canonical DB, Feeder, exchange, market-data sync, production backup/restore, writer or live execution. No strategy/risk parameters changed. `AI_EXECUTION_ENABLED=false`; Codemagic remains retired.
- Next: obtain owner approval to publish the manual workflow file on default branch `main` without merging unrelated branch work. Then dispatch with exact SHA `8c9cbdb66cab58c457c85e140462da4dab156ca9`; stop if any signing secret is missing/invalid and report names only. Do not install APKs or test IPC without separate authorization.
- Handoff update commit: `63e3d613440b6d206dab77928e1e4968fde5ea53`.



## P5.4.46 — Android paired-release workflow SDK setup fix (updated 2026-11-04)

Scope:
- Fix only the Android SDK setup input in the existing manual paired-release workflow.
- Preserve the exact branch restriction, source-SHA equality check, signing-secret checks, keystore cleanup, package identities, signer-parity verifier, artifact paths, and paper-only environment.
- No PR or new branch created.

Failure evidence:
- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41732942790
- Job: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41732942790/job/126254693104
- Branch: `feature/p5-4-1-post-merge-validation-20261103`
- Source SHA tested: `6dc3e2c6949d2a16d4f8d39ca68b99115a6d1d42`
- Result: FAILURE at `Set up Android SDK`; setup-android@v3 attempted `sdkmanager tools`, but the package repository returned `Failed to find package 'tools'`.
- Java/Gradle setup, source/branch/paper-only checks, signing-secret presence check, temporary keystore restore and cleanup passed.
- Android platform install, unit tests, APK build/signing, APK verification and artifact upload were skipped. No artifact was produced.

Remediation:
- In `.github/workflows/android-release-pair.yml`, set `packages: platform-tools` for `android-actions/setup-android@v3`, avoiding the obsolete default `tools` package.
- Main commit: `7dc66b9c53f63b73f6e14975d5f44c172e6f654c`.
- Feature commit: `c035cad68dbead8e5e0268f05725ae0d19ffe69f`.
- The two workflow files were updated independently on their existing branches; no other file was changed by either workflow commit.
- The feature workflow commit is a configuration fix only; no Android test/build was run locally.

Current verdict:
- Root cause identified: PASS.
- Workflow config updated and read back on main and feature: PASS; both copies have identical blob SHA `b6f6b3deccc01f27fb3c00b0bb5657033508be5c`.
- New manual dispatch: NOT RUN (must use GitHub Actions UI; no dispatch action is available in this session).
- Android unit tests / paired APK build / signer parity / APK artifacts: NOT RUN / NOT VERIFIED.
- Signing secret values were not read or exposed.
- `AI_EXECUTION_ENABLED=false`; all exchange credentials and DB/Feeder environment variables remain empty in this workflow.

Next action:
1. Dispatch the workflow on `feature/p5-4-1-post-merge-validation-20261103` using the exact branch HEAD fetched immediately before dispatch as `source_sha` (do not reuse a SHA recorded earlier in this handoff, because each handoff update advances the branch). The connected GitHub toolset has no workflow-dispatch operation, so this must be initiated from the Actions UI.
2. Inspect the new run's job steps, logs and artifacts. Do not claim release readiness until unit tests, both APK builds, package identity checks, signer parity and artifact integrity are evidenced.
3. Do not install/distribute APKs or enable live execution. Paper-only boundary remains unchanged.


## P5.4.47 — Android unit-test fixture JSON null compile fix (updated 2026-11-04)

Scope:
- Resolve the Kotlin overload ambiguity in the existing `FiveLayerApiTest.kt` fixture only.
- Preserve fixture semantics by representing JSON null explicitly as `JSONObject.NULL`.
- Existing branch only; no PR, no new branch, no main-branch update.

Change:
- File: `android-app/app/src/test/java/com/kenznguyen/btclivealerts/FiveLayerApiTest.kt`
- Replaced `.put("nextBeforeId",null)` with `.put("nextBeforeId",JSONObject.NULL)`.
- Source commit: `9d674a38c8e051ed68c9143a616364e2834d045a`.
- Test file blob SHA: `5526a9475287b098d7ef10856ac63a68c69634b0`.
- Commit diff independently read back and confirms exactly this one-line change.
- Branch HEAD after commit: `9d674a38c8e051ed68c9143a616364e2834d045a`.

Validation:
- Pre-fix compiler evidence: workflow run `41733660820`, job `126257158157`; main Kotlin compile passed, unit-test Kotlin compilation failed at the null fixture due to overload ambiguity.
- Post-fix local/CI test execution: NOT RUN.
- Android unit-test compilation/execution: NOT VERIFIED.
- Paired APK builds, signing, signer parity and artifact integrity: NOT RUN / NOT VERIFIED.
- No workflow run or artifact is claimed for this source SHA yet.

Safety and boundaries:
- Paper-only remains enforced; `AI_EXECUTION_ENABLED=false`.
- No canonical DB, Feeder, exchange connection, market-data sync, production backup/restore, APK installation or live execution.
- No signing secret values were accessed or changed.

Status:
- Source fixture correction: PASS (commit and file content read back).
- Test result after correction: NOT VERIFIED.
- APK/release readiness: NOT VERIFIED.

Next:
1. Manually dispatch `.github/workflows/android-release-pair.yml` from GitHub Actions on branch `feature/p5-4-1-post-merge-validation-20261103`, using exact `source_sha=9d674a38c8e051ed68c9143a616364e2834d045a`.
2. Inspect the resulting run's job steps, logs and artifacts. If unit tests fail, stop and diagnose before APK release conclusions.
3. Do not install or distribute APKs without separate authorization.

Handoff update commit: `b8d8c41f29407444bdb466890a5a7a5887072f89` (verified as branch HEAD; handoff blob SHA `264dcc6363788630345ca122c68bc343dcfac29d`).


## P5.4.48 — Android paired-release workflow dispatch SHA mismatch (updated 2026-11-04)

Run evidence:
- Workflow run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41734951363
- Job: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41734951363/job/126261621390
- Event: `workflow_dispatch`; branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Workflow checked out `GITHUB_SHA=2366a02869a957624f4ae8ec3c3188d8c896849f`.
- Supplied `source_sha=9d674a38c8e051ed68c9143a616364e2834d045a`.
- Preflight failed at `test "$INPUT_SOURCE_SHA" = "$GITHUB_SHA"`; this is an input/checkout SHA mismatch, not a Kotlin or Android build failure.
- Run conclusion: FAILURE. All setup/build/test/signing/verification/upload steps were skipped. Temporary keystore cleanup passed. No artifact was produced.
- `AI_EXECUTION_ENABLED=false`; DB/Feeder and exchange credential environment variables were empty. No live execution or market-data operations occurred.

Current verdict:
- Fixture source correction remains committed at `9d674a38c8e051ed68c9143a616364e2834d045a`.
- The workflow dispatch itself selected current branch HEAD `2366a02869a957624f4ae8ec3c3188d8c896849f`; the supplied older SHA caused preflight rejection.
- Android unit tests/build/signing/signer parity/artifacts: NOT RUN / NOT VERIFIED.

Next:
- Re-dispatch the same workflow on this same branch and enter the exact current branch HEAD as `source_sha=2366a02869a957624f4ae8ec3c3188d8c896849f`. This commit contains the fixture fix as an ancestor and satisfies the workflow's exact SHA equality gate.
- Re-read branch HEAD immediately before dispatch. If it has advanced, use that newly verified exact HEAD instead.
- Inspect the new run before making any APK readiness claim. Do not install APKs or enable live execution.


## P5.4.49 — Android paired-release workflow successful (updated 2026-11-04)

Run evidence:
- Workflow run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41735402129
- Job: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41735402129/job/126263199091
- Event: `workflow_dispatch`; branch: `feature/p5-4-1-post-merge-validation-20261103`; attempt 1.
- Exact run/source SHA: `621857b4568af67fcf571968f1b732558e16ccbc`; workflow input `source_sha` matched `GITHUB_SHA` and checked-out HEAD.
- Run conclusion: **SUCCESS**; job conclusion: **SUCCESS**; all relevant steps completed successfully.
- Paper-only preflight passed; `AI_EXECUTION_ENABLED=false`; DB/Feeder and exchange credential environment variables were empty. No live execution or exchange/data operation occurred.
- Temporary signing keystore restore and cleanup passed; secret values were not printed.
- Android unit-test step `gradle :app:testDebugUnitTest --no-daemon --stacktrace` completed; Gradle reported `BUILD SUCCESSFUL`. The available job log does not provide a trustworthy explicit test-case count, so record **PASS (count not independently extracted)**.
- Both `assembleRelease` and `assembleParallel` completed; Gradle reported `BUILD SUCCESSFUL`.
- `ci/verify-android-release-pair.py` passed and logged: regular release host and parallel/.paper APK identities verified, matching release signer, and source SHA verified.
- Artifact: `android-release-pair-621857b4568af67fcf571968f1b732558e16ccbc`; ID `13278029439`; size 16,209,168 bytes; ZIP digest `sha256:7ab1372b0b0fd36d50f03a572b86a22fb8aa6c0ba81a230774f8221c2aba07bb`; expires 2026-11-10T22:59:00Z.
- Artifact URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41735402129/artifacts/13278029439
- GitHub artifact metadata associates the artifact with run `41735402129`, branch `feature/p5-4-1-post-merge-validation-20261103`, and source SHA `621857b4568af67fcf571968f1b732558e16ccbc`.
- The ZIP digest is the digest reported by the GitHub upload action and artifact metadata; payload download, independent ZIP/APK SHA-256 recomputation, and independent APK certificate inspection have **NOT YET BEEN PERFORMED**.

Verdict:
- Manual workflow, source-SHA gate, Android unit-test task, paired release builds, workflow verifier checks, signer parity as checked by the verifier, and artifact publication: **PASS**.
- Independent artifact payload integrity and independent APK signer inspection: **NOT VERIFIED**.
- Device installation, runtime behavior, host/.paper IPC, and upgrade/install compatibility: **NOT RUN / NOT VERIFIED**.
- This is a successful build-and-verification workflow, not approval to install or distribute either APK.

Safety and boundaries:
- `AI_EXECUTION_ENABLED=false`; no live orders, DB/Feeder activation, exchange connection, market-data sync, production backup/restore, or strategy/risk parameter changes.
- APK installation/distribution and device/IPC testing remain outside this run and require separate approval.

Next:
1. Preserve the artifact before expiry and, if supported, download both APKs and evidence bundle for independent ZIP/APK checksum and certificate inspection.
2. Review test XML/report files to obtain exact unit-test case counts and identify skipped/ignored tests, without rerunning the suite unless an evidence gap requires it.
3. Do not install or distribute APKs or begin device/IPC testing without separate explicit authorization.



## P5.4.50 — Independent paired-release artifact inspection (updated 2026-11-04)

Scope: download the exact GitHub Actions artifact from run `41735402129` / artifact `13278029439`, inspect archive integrity, extract test XML totals, compare APK digests to the embedded manifest, and independently extract v2 signing certificates. No APK installation or runtime execution.

Source/artifact identity:
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Build source SHA: `621857b4568af67fcf571968f1b732558e16ccbc`
- Artifact ID: `13278029439`
- Downloaded file: `android-release-pair-621857b4568af67fcf571968f1b732558e16ccbc.zip`
- Actual size: 16,209,168 bytes.
- Independently computed ZIP SHA-256: `7ab1372b0b0fd36d50f03a572b86a22fb8aa6c0ba81a230774f8221c2aba07bb`, exactly matching GitHub artifact metadata.
- `unzip -t`: all 44 entries passed; no compressed-data errors.
- Embedded `android-source-sha.txt` equals the build source SHA above.
- Embedded `android-release-pair.json` sourceSha also equals the build source SHA.

Unit-test evidence from archived JUnit XML:
- 16 XML test suites.
- 96 tests total; 96 passed; 0 failures; 0 errors; 0 skipped.
- This provides the exact test count absent from the initial job-log summary.

APK payload evidence:
- Release APK: `android-app/app/build/outputs/apk/release/app-release.apk`; 7,206,843 bytes; SHA-256 `87039344c8f5d122644be648f7be8d7388f2eaca470576aeec023da4c81697c3`.
- Parallel APK: `android-app/app/build/outputs/apk/parallel/app-parallel.apk`; 9,766,090 bytes; SHA-256 `a9c13cfb8224dc8daa05669c4e93214a482b94b77398d31d266bdded5be6d467`.
- Both computed APK SHA-256 values match their respective entries in `android-release-pair.json`.
- Embedded metadata identifies release package `com.kenznguyen.btclivealerts`, version `0.2.0`; parallel package `com.kenznguyen.btclivealerts.paper`, version `0.2.0-paper`.
- Independently parsed the APK Signing Block v2 certificate sequence from both APKs and extracted the DER certificate. Both certificates have SHA-256 fingerprint `e65a490a75786c5b76e886be1aa11e66acaea23e5e875560a94b37fb4a9942e8`, matching the embedded metadata and the workflow verifier's reported signer parity. Certificate subject: `CN=BTCUSDT Chart ProKey alias: btc-chart-release, O=Personal, C=VN`.
- Full signature verification was in fact executed by the original GitHub Actions runner: `ci/verify-android-release-pair.py` invokes Android Build Tools 34.0.0 `apksigner verify --verbose --print-certs <apk>` for each APK. The script only returns success and emits its final verification message after both commands exit successfully. The script's successful completion is recorded in job log `126263199091` at 2026-11-03T23:04:21.8295842Z (`Verified regular release host and parallel/.paper APK identities, matching release signer, and source SHA.`), immediately before artifact upload. Therefore both APKs passed Android `apksigner` cryptographic signature verification on the trusted GitHub runner. The later local inspection environment lacking `apksigner` does not invalidate this runner evidence.

Verdict:
- Artifact download, exact ZIP digest match, archive integrity, source SHA identity, 96/96 JUnit result, APK payload digests, and matching extracted v2 certificate fingerprints: **PASS**.
- Full APK signature cryptographic verification using Android Build Tools 34.0.0 `apksigner verify --verbose --print-certs` on both APKs within the successful GitHub Actions run: **PASS**, evidenced by successful completion of `ci/verify-android-release-pair.py` and the corresponding job log before artifact upload.
- Device installation, launch/runtime behavior, app update compatibility, and inter-app/host-paper IPC: **NOT RUN / NOT VERIFIED**.
- No APK installation, distribution, live execution, exchange connection, DB/Feeder activation, or market-data sync was performed.

Next:
1. Preserve the inspected artifact and its checksums in the evidence record.
2. If independent signature validity is required, run Android SDK Build Tools `apksigner verify --verbose --print-certs` on both exact APK payloads in a trusted environment.
3. Await separate explicit authorization before device installation or runtime/IPC tests. Keep `AI_EXECUTION_ENABLED=false`.



## P5.4.51 — Pre-install Android manifest and lifecycle review (updated 2026-11-04)

Scope:
- Static review only of the paired APK's Android manifest, Gradle build variants, MainActivity lifecycle, and StrategyMonitorService lifecycle before any device installation.
- No source-code behavior changes, no workflow dispatch, no APK install, no app launch, no device/runtime/IPC test, and no network request initiated by this review.

Source identity reviewed:
- Branch: `feature/p5-4-1-post-merge-validation-20261103`
- Review source SHA: `762e5fc50f1c86e74e9ade0ad3617b1a3a58125b`
- `android-app/app/src/main/AndroidManifest.xml` blob: `e505a1829899f32c211f5390b5ae7753048ae15b`
- `android-app/app/build.gradle.kts` blob: `419f30ca44e0ead9f7a595e5baa9dd11c0eb6623`
- `MainActivity.kt` blob: `c03c87993a1d696cdb9cab629114ff5ef8420ec2`
- `StrategyMonitorService.kt` blob: `2d494af5e47d51d5111af2bc466e6aaf48a0e75b`

Static findings:
- Manifest declares INTERNET, POST_NOTIFICATIONS, VIBRATE, FOREGROUND_SERVICE and FOREGROUND_SERVICE_DATA_SYNC. Backup is disabled and cleartext traffic is disabled.
- StrategyMonitorService is non-exported; MainActivity is the exported launcher activity. No other exported component is declared in the reviewed manifest.
- The release host uses application ID `com.kenznguyen.btclivealerts`; parallel uses suffix `.paper` and `BuildConfig.PARALLEL_INSTALL=true`. MainActivity gates notification-channel setup, notification permission prompt, and foreground-service start to the non-parallel host.
- The regular host starts StrategyMonitorService from Activity.onResume. The service starts a dataSync foreground service, initializes OrderBookEngine and scanner state, fetches M15/H1 market candles, processes closed-candle signals and writes monitoring state to SharedPreferences. This is read-only market-data monitoring in the reviewed path; no order-placement call was identified in the inspected service path.
- Parallel/.paper Activity does not start StrategyMonitorService via onResume and renders FiveLayerStandaloneDashboard.
- Android 15 dataSync foreground-service timeout handling is explicitly present: onTimeout records the stop reason, cancels monitor work, posts a user-visible restart notification, and stops the service. This behavior still requires device validation.

Review verdict:
- Manifest/exported-component and variant separation static review: **PASS** for the inspected files.
- No live-order path identified in the inspected Activity/Service code: **PASS (limited static scope; not a repository-wide proof)**.
- Runtime behavior, Android-version-specific foreground-service behavior, notification permission flow, market-data network behavior, and installation/update compatibility: **NOT RUN / NOT VERIFIED**.
- Potential operational consideration: opening/resuming the regular host automatically starts background market monitoring and the service's scanner according to persisted preferences. This is expected by the current code but must be disclosed before device testing; no such automatic service start occurs in the inspected parallel Activity branch.

Safety:
- No APK installation/distribution, device interaction, live order, exchange credential, canonical DB, Feeder, market-data sync from this review, or production backup/restore.
- Preserve `AI_EXECUTION_ENABLED=false`; no runtime or IPC authorization is implied.

Next:
1. Obtain explicit approval before installing either APK and running device lifecycle/notification/IPC tests.
2. When approved, test regular host and parallel app separately, including co-install, launch, force-stop/reopen, notification permission, service timeout/recovery, and no-order boundary.
3. Do not enable live execution or connect exchange trading credentials.


## P5.4.52 — Device validation gate and test matrix (2026-11-04)

Purpose:
- Prepare the exact next validation scope without installing or launching either APK. User's latest instruction was to continue, but it did not explicitly authorize device installation/runtime actions; retain the installation gate.

Static manifest/build observations:
- Manifest blob `e505a1829899f32c211f5390b5ae7753048ae15b`: only launcher Activity is exported; StrategyMonitorService is explicitly non-exported. No provider or receiver is declared in this manifest.
- Gradle blob `419f30ca44e0ead9f7a595e5baa9dd11c0eb6623`: compileSdk/targetSdk 35, minSdk 26; release ID `com.kenznguyen.btclivealerts`; parallel ID `com.kenznguyen.btclivealerts.paper`; parallel build sets `PARALLEL_INSTALL=true`; both variants use the release signing config.
- These observations are static only; the installed package state and OS behavior have not been inspected.

Prepared device test matrix (NOT RUN):
1. Artifact integrity: re-download artifact `13278029439`, verify ZIP and both APK SHA-256 values against P5.4.50 before install.
2. Co-install: install regular and .paper APK; confirm both package IDs coexist and both launch independently.
3. Regular app launch/resume: verify POST_NOTIFICATIONS prompt behavior on Android 13+, foreground-service notification, service start/stop, M15/H1 monitoring state, and resume after backgrounding.
4. Parallel app isolation: launch .paper and confirm it does not start StrategyMonitorService, does not create regular-host notification channels, and does not alter regular-host SharedPreferences.
5. Lifecycle: force-stop/reopen, process death, reboot behavior only if separately approved, foreground-service timeout callback and user-tap recovery. Record device model, Android API/build, timestamps, logcat and package state.
6. IPC/export boundary: verify external apps cannot start/bind StrategyMonitorService; verify no unexpected exported components; test cross-package storage isolation and absence of implicit intent/data leakage.
7. No-order boundary: inspect logs/network activity during read-only market monitoring; assert no exchange trading endpoints/order payloads and `AI_EXECUTION_ENABLED=false`. No exchange trading credentials are to be supplied.
8. Regression: launch both apps repeatedly and verify no crash, ANR, or cross-app state contamination.

Acceptance/evidence:
- Record exact artifact ID, APK hashes, package IDs, signer fingerprint, device/API/build, test commands, timestamps, test outcomes and sanitized logcat evidence.
- Any crash, unexpected exported component, cross-app state leakage, order endpoint activity, or signer mismatch is BLOCKED; do not continue to broader runtime tests until triaged.
- No production data, canonical DB, Feeder, exchange credentials, live order, or app distribution is permitted by this test plan.

Current result:
- Static manifest/build review: **PASS** within inspected scope.
- Device installation/runtime/IPC test matrix: **BLOCKED — explicit user authorization for APK installation and device testing not yet received**.
- No workflow run or artifact generated by this planning step.

Next:
- Await explicit approval for installation and device runtime testing. If approval is not granted, remain at static-review boundary. Preserve `AI_EXECUTION_ENABLED=false`.


## P5.4.53 — Expanded static security review: paper API mutation boundary (2026-11-04)

Scope:
- Extended static review of the Android application sources at source SHA `3071737221b4afb8af6ad9b7b00c3ba5732975c0`; no install, launch, network calls, or runtime actions.

Files and source blobs:
- `AndroidManifest.xml`: `e505a1829899f32c211f5390b5ae7753048ae15b`
- `MainActivity.kt`: `c03c87993a1d696cdb9cab629114ff5ef8420ec2`
- `FiveLayerApi.kt`: `91c9ce61a14dc54a2e2bf1b47285d5645b3f119e`
- `StrategyMonitorService.kt`: `2d494af5e47d51d5111af2bc466e6aaf48a0e75b`
- `MarketEngine.kt`: `ed921c7278ce3397c85c49c9706c2b5550fc5012`
- `FiveLayerStandaloneDashboard.kt`: `0a98affe08a52c2721baac4f31419945dd67a56d`

Findings:
1. The manifest declares only the launcher Activity exported; StrategyMonitorService is non-exported. No ContentProvider or BroadcastReceiver is declared in this manifest. Static manifest result: PASS within this module manifest scope.
2. MainActivity calls notification-channel creation, POST_NOTIFICATIONS permission request (Android 13+), and starts StrategyMonitorService only when `BuildConfig.PARALLEL_INSTALL == false`. The parallel Activity renders FiveLayerStandaloneDashboard instead.
3. StrategyMonitorService creates OrderBookEngine, MultiSymbolScanner and MarketEngine work; the inspected MarketEngine URLs are Binance USD-M public market-data REST/WebSocket endpoints (klines, exchangeInfo, ticker24hr, premiumIndex, mark price and kline streams). No exchange order endpoint or trading credential use was found in these inspected files.
4. Important correction to the prior broad description of the .paper app: `FiveLayerApi.kt` exposes POST methods for `paper/evaluate`, `paper/pause`, `paper/kill`, `paper/reset-kill`, and `paper/cancel`. These are paper-service state/control mutations, not evidence of real exchange order placement. The same client also reads system, intelligence, decision, paper ledger, equity, signals, quality, audit, candles and order-book endpoints.
5. FiveLayerApi requires HTTPS base URLs, a non-empty printable bearer token, disables automatic retry for POST controls, disables redirects, and restricts endpoint path segments to a fixed allowlist. These safeguards are statically present, but the actual configured URL, backend identity and backend behavior are NOT VERIFIED in this review.
6. `MainActivity.onResume()` starts the regular host's foreground service. The service has START_STICKY and uses public Binance market data; Android OS lifecycle/timeout behavior requires device testing.

Risk interpretation:
- Static evidence supports that the inspected regular monitor uses public market-data endpoints and does not itself submit exchange orders.
- Static evidence also shows that the parallel paper dashboard can issue state-changing requests to a configured paper API. Before any device test, confirm that the configured HTTPS host is the intended paper backend and that all paper endpoints are isolated from exchange execution. Do not enter exchange trading credentials.
- A repository-wide proof that no other code can create real orders was not established; scope was the manifest, Activity, FiveLayerApi, monitor service and MarketEngine files above.

Results:
- Manifest component/export boundary: **PASS (scoped)**.
- Public market-data-only behavior in inspected MarketEngine/StrategyMonitorService path: **PASS (scoped)**.
- Paper API mutation boundary identified and documented: **PASS**.
- Actual paper backend identity/configuration and server-side execution boundary: **NOT VERIFIED**.
- Device installation/runtime/IPC/network test: **BLOCKED pending explicit approval**.

Safety constraints:
- Do not install or launch either APK without explicit authorization.
- Do not configure exchange trading credentials, call exchange trading endpoints, or perform live/paper backend mutations as part of static review.
- Keep `AI_EXECUTION_ENABLED=false`; no live execution is authorized.

Next:
1. If device testing is approved, verify the configured FiveLayer API HTTPS origin against the intended paper service before using any POST control; test GET endpoints first, then only explicitly approved paper controls in a disposable test environment.
2. Keep regular-host public market-data lifecycle tests separate from parallel paper API tests.
3. Capture sanitized logcat and HTTP method/path/status evidence; never record bearer tokens or secrets.


## P5.4.54 — Paper API/backend contract verification (2026-11-04)

Scope:
- Read-only static trace of Android client → shared API → paper ledger → Hummingbot market-data bridge. No HTTP request, API call, app install/launch, backend start, or paper mutation was performed.

Source SHA: `7d7199686ed48393398444d2bc1e18904c0a3769`.
Files inspected:
- `android-app/app/src/main/java/com/kenznguyen/btclivealerts/FiveLayerPanel.kt`: `de1c6c1e11663a0c6f9330160665bf4c67e6af2f`
- `android-app/app/src/main/java/com/kenznguyen/btclivealerts/FiveLayerApi.kt`: `91c9ce61a14dc54a2e2bf1b47285d5645b3f119e`
- `pipeline/api.py`: `0540540462b3710a25788e4ff47a88272b7ee9c3`
- `pipeline/test_api.py`: `2c021f14c5326ec7defa2b9c6606ac60ae9df558`
- `paper_execution/ledger.py`: `68209ce48a6e5e9a995f93167684133e41cc7f55`
- `paper_execution/README.md`: `f93dc79de167cb96ea5924465e35fd641985dc16`
- `integrations/hummingbot_bridge.py`: `aa9db7522ffb7ce911c7fbbdc73a7f9b47401331`
- `integrations/README.md`: `8df3ffcf3d1f5222ba40a0f032e7eb6f5b7f92ab`
- `android-app/app/src/test/java/com/kenznguyen/btclivealerts/FiveLayerApiTest.kt`: `5526a9475287b098d7ef10856ac63a68c69634b0`
- `docs/FIVE_LAYER_PAPER_RUNBOOK.md`: `184ffa7e8df9d4f4f81a4902d9b6bc84783d7d07`

Verified source-level contract:
1. Android stores only the API URL in SharedPreferences. Read and control tokens are held in screen-session state, not persisted; control token must differ from read token. GET requests use read token; POST requests use control token.
2. Android client accepts HTTPS only, rejects URL userinfo/query/fragment, restricts path segments to a fixed allowlist, disables redirects and automatic retry for POST controls, and uses a 10-second call timeout.
3. Backend `pipeline/api.py` maps GET routes to `MARKET_DATA_TOKEN` and POST paper controls to a distinct `CONTROL_TOKEN`; reusing the read token for POST is rejected. Routes are limited to the defined `/v1/*` allowlist. POSTs have a shared SQLite rate budget.
4. POST `/v1/paper/evaluate` evaluates either AI or CORE input and, if an intent exists, submits it only to `PaperLedger.submit()`. Pause, cancel, kill and reset-kill mutate paper ledger state only. Kill reset checks server-side readiness. API responses identify mode PAPER and `liveTradingSupported=false`.
5. `paper_execution/ledger.py` explicitly documents no network client. Its submit path simulates fills against a supplied order-book snapshot and persists paper orders/fills/audit in SQLite. It does not call exchange order endpoints.
6. Hummingbot bridge is read-only with respect to trading: it calls Hummingbot `POST /market-data/order-book` to retrieve a depth snapshot (the HTTP method is POST, but the resource is market data); no order placement/cancel endpoint is called. Hummingbot Basic credentials remain server-side. This is not proof that the configured Hummingbot server is safe or that any other server-side process cannot trade.
7. Existing test source covers distinct-token enforcement, unknown route rejection, paper evaluate/pause/kill/reset behavior, rate limiting and no-prediction WAIT behavior. Android API tests cover HTTPS/path allowlisting. These test definitions were inspected but NOT executed in this task.

Important operational distinction:
- The Android Paper app's POST controls are real state changes to the configured paper backend and may create simulated paper fills. They are not live exchange orders in the inspected implementation. Do not press Evaluate, Pause/Resume, Cancel, Kill or Reset during a connection check unless that exact paper mutation has been explicitly authorized and a disposable paper ledger is confirmed.
- The backend runbook describes a source-level deployment contract, but this review did not identify or verify a currently deployed backend URL, DNS/TLS identity, environment variables, database path, Hummingbot target or server process. The UI accepts a user-entered URL, so actual host identity remains **NOT VERIFIED**.

Results:
- Android client/backend auth and route contract: **PASS (static source review)**.
- Paper mutation isolation to SQLite ledger in inspected backend path: **PASS (scoped)**.
- Hummingbot integration method/resource is market-data snapshot only in inspected bridge: **PASS (scoped)**.
- Actual deployed backend identity, environment, Hummingbot server identity and runtime behavior: **NOT VERIFIED**.
- Existing test cases inspected, not executed in this task; device tests: **BLOCKED pending explicit approval**.

Safety limits:
- Do not connect the app to any endpoint until the operator independently confirms the HTTPS origin belongs to the intended isolated paper server.
- Do not use exchange API keys or trading-enabled Hummingbot credentials. Keep `AI_EXECUTION_ENABLED=false` and no live trading.
- No API calls or POST controls were made. No workflow/artifact was generated.

Next step:
- Prepare a no-write endpoint identity checklist (origin, TLS certificate/hostname, server build SHA, `MARKET_DATA_TOKEN` vs `CONTROL_TOKEN` separation, DB canonical path and paper-only Hummingbot account/connector config). Then request explicit approval before any connection test; first test should be authenticated GET-only against a confirmed paper host.


## P5.4.55 — HTTP method vs data-side-effect classification (2026-11-04)

Scope:
- Read-only review of API route dispatch and existing equity persistence test. No API call, DB access, server start, endpoint probe, or paper mutation was performed.

Source SHA: `4c5a1ad8b61ce1a17c254c3a989b5ad0665779fc`.
Evidence:
- `pipeline/api.py` blob: `0540540462b3710a25788e4ff47a88272b7ee9c3`
- `pipeline/test_api.py` blob: `2c021f14c5326ec7defa2b9c6606ac60ae9df558`
- `docs/FIVE_LAYER_PAPER_RUNBOOK.md` blob: `184ffa7e8df9d4f4f81a4902d9b6bc84783d7d07`

Finding — GET is not synonymous with read-only:
1. `GET /v1/equity` dispatches to `equity_snapshot()`. When a complete closed M15 candle is available, that function constructs `PaperLedger` and calls `record_equity(...)`, which persists an equity observation in SQLite. The source comment explicitly notes that constructing the ledger initializes a fresh Paper store before the first persistent equity observation.
2. Existing test `test_equity_endpoint_persists_history_and_returns_drawdown_daily_metrics` asserts that calling this GET endpoint causes `paper_equity_history` row count to become 1. This is direct test-source evidence of a persistent write, not merely an inferred possibility.
3. Therefore a GET-only smoke test that calls every GET route can still mutate canonical Paper DB state. `GET /v1/equity` is **READ + WRITE / SIDE-EFFECTING** and must be excluded from a no-write connection check.
4. `GET /v1/paper` uses `read_snapshot()`; `GET /v1/audit` uses `read_audit()`; `GET /v1/candles` reads the configured market-data store. Other GET routes may fetch/compute snapshots (including Hummingbot market data) but should still be individually checked for indirect persistence before being called against a production/canonical store.
5. Hummingbot bridge's upstream `POST /market-data/order-book` remains a market-data retrieval resource. HTTP verb alone does not identify whether the operation changes trading or persistent state; resource semantics and implementation must be checked.

Endpoint test policy update:
- A future no-write smoke test may consider only routes whose full call graph is confirmed read-only and which are safe for the selected environment. Do not call `/v1/equity`.
- Avoid `/health` as proof of backend identity; it is unauthenticated and only reports process identity string.
- Do not call any POST control route (`evaluate`, `pause`, `cancel`, `kill`, `reset-kill`) during identity verification.
- Do not run tests against canonical production DB. Any later persistence test must use a disposable isolated SQLite copy/store with known path and verified backup/hash, separately authorized.

Results:
- Side-effecting GET discovery: **PASS** (source and existing test source agree).
- Endpoint-level no-write allowlist: **NOT YET CERTIFIED**; complete call-graph audit and environment-specific review remain required.
- Runtime endpoint identity/connectivity: **NOT VERIFIED**.
- No test execution, workflow, artifact, device installation, API call, or DB mutation occurred.

Safety/next:
1. Amend the future endpoint checklist to explicitly blacklist `GET /v1/equity` and all POST controls for no-write checks.
2. Audit each remaining candidate GET call graph for indirect DB writes and external side effects before any probe.
3. Verify the deployed host/TLS identity out of band before an authenticated read-only request; do not treat `/health` alone as identity proof.
4. Keep `AI_EXECUTION_ENABLED=false`; do not enable exchange credentials or live execution.


## P5.4.56 — GET endpoint call-graph side-effect audit (2026-11-04)

Scope:
- Static call-graph review of every GET route in `pipeline/api.py`, plus SQLite/PostgreSQL candle readers, PaperLedger read helpers and Hummingbot snapshot bridge. No endpoint was called; no server, DB, Hummingbot process or external network request was started.

Source SHA: `4c5a1ad8b61ce1a17c254c3a989b5ad0665779fc`.
Inspected source blobs:
- `pipeline/api.py`: `0540540462b3710a25788e4ff47a88272b7ee9c3`
- `market_data/storage.py`: `99b66a4d183b8664f28d6638d8d87416d32847c9`
- `market_data/store.py`: `b28601aed70097afcb7a4eea2dd93ed163ae1cec`
- `market_data/postgres.py`: `92d336caa7b8e64dc6c1798aeabb750b7a469dfd`
- `paper_execution/ledger.py`: `68209ce48a6e5e9a995f93167684133e41cc7f55`
- `futures_intelligence/import_collector.py`: `5effe6540b86edcb190456c95b6bb11456aec099`
- `integrations/hummingbot_bridge.py`: `aa9db7522ffb7ce911c7fbbdc73a7f9b47401331`

Call-graph findings and classification:
1. `GET /health`: returns a constant service identity/status document. No DB or Hummingbot call. **No-write / local-only**, but unauthenticated and not proof of deployed host identity, source SHA, TLS identity or backend configuration.
2. `GET /v1/system`: falls through to the system/layer summary branch. Reads candle window, report files and environment/configuration; checks whether dashboard index exists. Candle read path uses SQLite URI `mode=ro` or PostgreSQL `SET TRANSACTION ... READ ONLY`; no Hummingbot fetch and no PaperLedger constructor in this branch. **Static no-persistent-write candidate**, but does read configured stores/files and therefore still touches the selected runtime dependencies.
3. `GET /v1/candles`: validates query and calls `market_window()`. SQLite `read_window` requires an existing DB and connects with `mode=ro`; PostgreSQL reader explicitly opens a read-only transaction. Storage factory constructors are inert and do not migrate/create schema. **Read-only candidate**; must point to the intended data store and may perform DB/network reads.
4. `GET /v1/paper`: calls `read_snapshot()`, which requires an existing file and opens SQLite with `mode=ro`, starts a read transaction, and SELECTs state/orders/risk/strategy. **Read-only candidate**; missing/corrupt state returns an error rather than initializing a ledger.
5. `GET /v1/audit`: calls `read_audit()`, which requires an existing file and opens SQLite with `mode=ro`; it checks table existence and SELECTs audit rows. **Read-only candidate**.
6. `GET /v1/intelligence`: reads `INTELLIGENCE_REPORT_PATH` and validates the loaded JSON snapshot. No DB write or Hummingbot call identified. **File-read-only candidate**; may read a configured local file and is not an identity check.
7. `GET /v1/order-book`: calls `book_snapshot()`; may issue authenticated upstream Hummingbot `POST /market-data/order-book` to obtain a market-data snapshot and updates an in-process cache. The upstream resource is read-only market data, not order placement/cancel, but this is an external network call and memory-state mutation. **Not suitable for offline/no-external-call probe**; no live-order path in inspected bridge.
8. `GET /v1/decision`: calls `context()` then AI decision evaluation. Context reads candle/report inputs and may fetch/cache Hummingbot order-book snapshot. **No persistent write identified, but may call external Hummingbot**; not a no-network probe.
9. `GET /v1/signals`: evaluates AI and Core signal snapshots; Core uses `read_snapshot()` (SQLite read-only) and candle reads, while context/Core may fetch/cache Hummingbot snapshot. **No persistent write identified, but may call external Hummingbot**; not a no-network probe.
10. `GET /v1/quality`: builds quality streams from context, candle/report reads, Core evaluation and PaperLedger read snapshot. It can fetch/cache Hummingbot snapshot. **No persistent write identified, but may call external Hummingbot**; not a no-network probe.
11. `GET /v1/equity`: previously classified P5.4.55. Calls `equity_snapshot()`, constructs `PaperLedger` (creates directories/tables/initial state and enables WAL as needed) and calls `record_equity()`. **Persistent write / ledger initialization**; explicitly excluded from all no-write checks.

Important boundary:
- The Hummingbot bridge uses HTTP POST to the `/market-data/order-book` resource. Its body selects connector, pair and depth; inspected bridge has no order placement/cancel route. The HTTP verb alone is not proof of a trade mutation. However, it is an external request and cannot be described as an offline/no-side-effect check.
- `GET /health` only reports a service label; it does not attest deployment provenance or prove that the target is the intended isolated paper backend.
- Static review cannot prove environment variables, actual DB path, remote PostgreSQL permissions, mounted report files, Hummingbot target identity or deployed code match the reviewed SHA.

Provisional no-write policy:
- Lowest-side-effect candidates for a future carefully scoped identity/read test: `/v1/system`, `/v1/intelligence`, `/v1/candles`, `/v1/paper`, `/v1/audit`. This is a source-level classification only, not permission to call them against an unknown or canonical production host.
- Require the actual host/TLS/source identity and configured storage target to be confirmed out of band first. Prefer an isolated disposable read-only replica/copy for validation. Do not expose bearer tokens in logs.
- Exclude `/v1/equity` from no-write tests. Exclude `/v1/order-book`, `/v1/decision`, `/v1/signals`, and `/v1/quality` from offline/no-network checks because they may fetch Hummingbot market data.
- Do not call any POST paper control during endpoint identity verification.

Results:
- Static route/call-graph classification: **PASS** within inspected source scope.
- Candidate read-only routes: **PROVISIONAL / NOT RUNTIME VERIFIED**.
- Endpoint identity, deployed source SHA, TLS, environment and runtime DB permissions: **NOT VERIFIED**.
- No tests/workflow/artifact, API request, external network call, DB access or mutation occurred.

Next:
1. Prepare P5.4.57 minimal endpoint identity evidence contract (what must be independently confirmed before even a GET probe).
2. Keep API probes blocked until the exact host and storage target are confirmed and the user explicitly authorizes the probe.
3. Keep `AI_EXECUTION_ENABLED=false`; no exchange trading credentials, live execution or APK installation.


## P5.4.57 — Minimal Endpoint Identity Evidence Contract (2026-11-04)

- Report: `docs/evidence/P5.4.57-MINIMAL-ENDPOINT-IDENTITY-EVIDENCE-CONTRACT-2026-11-04.md`.
- Branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Source baseline: `ddd0a40faa893d87f9dae320dfcbf435d9e4540c` (P5.4.56 reviewed source baseline).
- Objective: define all evidence gates required before any authenticated Paper backend endpoint probe.
- Seven mandatory gates: exact intended HTTPS origin; valid TLS certificate/SAN identity; deployed immutable source/build SHA; distinct non-empty `MARKET_DATA_TOKEN` and `CONTROL_TOKEN` without exposing values; exact isolated/disposable Paper DB or verified read-only replica identity; Hummingbot server/connector identity with no trading credentials/order permissions; effective deployed `AI_EXECUTION_ENABLED=false`.
- `/health` is explicitly not identity/provenance evidence. Successful DNS, process status, Android-entered URL or repository defaults are insufficient.
- Provisional candidates remain only `/v1/system`, `/v1/intelligence`, `/v1/candles`, `/v1/paper`, `/v1/audit`, each subject to a separate explicit authorization and exact isolated-target confirmation.
- Explicit denylist: `GET /v1/equity` (persistent ledger write/initialization); `GET /v1/order-book` (Hummingbot request/cache); `GET /v1/decision`, `/v1/signals`, `/v1/quality` (may fetch Hummingbot); all POST paper controls; `GET /health` cannot be used as identity proof.
- Result: identity contract definition **PASS (documentation only)**. Actual origin/TLS/build, credentials, storage, Hummingbot and deployed execution flag **NOT VERIFIED**. Endpoint probe **BLOCKED / NOT AUTHORIZED**.
- No tests/workflows/artifacts, API requests, network calls, DB access, service startup, exchange access, APK install or paper mutations.
- Next: obtain seven sanitized evidence items out-of-band, reconcile deployed SHA and isolated storage identity, then request separate authorization for one exact GET route. Checklist completion does not itself authorize a probe.
- Safety: keep `AI_EXECUTION_ENABLED=false`; no live execution, canonical DB/Feeder activation, exchange credentials, market-data sync or POST controls.


## T0 Re-check — 2026-11-04

- Report: `docs/evidence/T0-RECHECK-2026-11-04.md`.
- Repository/branch: `kenznguyen/btcusdt-telegram-signals2` / `feature/p5-4-1-post-merge-validation-20261103`.
- Reviewed HEAD: `e9271a52a13f5213b387aa8f474a4e9b85b0d7f1`.
- Static findings: scheduler callback still hands ingestion to `sync_window()` + T0 Gateway; M15/H1, 5s poll, 5s close grace, retry max 5, lease TTL 60s and heartbeat 15s; production SQLite candle/Gateway/lease/status paths are required to align.
- Retry/recovery/lease/fencing: PASS (static source review). Health state machine explicitly keeps STARTING not-ready until recovery, storage and lease gates pass; runtime API integration test definitions cover startup-in-progress, healthy-after-recovery, lease loss, incomplete recovery, stopped state and stale-generation fencing. The prior `test_startup_in_progress_is_not_ready` expectation matches current source, but no fresh test run was executed.
- Current source test inventory: scheduler 15, retry 12, recovery 10, lease 11, health 11, health API 9, runtime health API 6, lifecycle 23, atomic fencing 9, SIGKILL recovery 1 = 107 test methods. Workflow source asserts groups 100/107/101 and separate data-integrity 12; manual final runtime config module has 7 test methods.
- CI routing issue: `.github/workflows/t0-validation.yml` push trigger only names `feature/t0-operational-contract-release-gate-20261102`, not the current branch `feature/p5-4-1-post-merge-validation-20261103`. It has `workflow_call`; no current-branch caller or current-HEAD workflow evidence was established. `t0-manual-validation.yml` is workflow_dispatch but no run/artifact for reviewed HEAD was retrieved.
- Final runtime config audit is source-level read-only; GitHub runner intentionally has no canonical DB path or exchange credentials. Actual Windows PC canonical path/DB integrity, runtime feeder, exchange connectivity, sync and M15/H1 freshness remain NOT VERIFIED.
- Result: source-level T0 contracts **PASS**; workflow auto-trigger on active branch **BLOCKED / CONFIG GAP**; fresh current-HEAD tests **NOT VERIFIED**; PC/runtime acceptance **NOT VERIFIED**.
- No tests/workflows/artifacts, DB access, feeder start, exchange/network request, market-data sync or production mutation occurred.
- Next: correct/confirm T0 CI routing and obtain fresh isolated exact-SHA test evidence; then separately verify Windows canonical path and integrity before any runtime smoke test.
- Safety: keep `AI_EXECUTION_ENABLED=false`; no live trading, exchange trading credentials, canonical DB writes, feeder startup or market-data sync.


## T0 Exact-SHA CI Validation — 2026-11-04
# T0 Exact-SHA CI Validation — 2026-11-04

## Scope
Correct the active-branch T0 CI trigger and align its policy test with the branch allowlist. Execute the T0 regression workflow and integrated P5.4.1 acceptance on the same source SHA. No production runtime or canonical storage actions.

## Source identity
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/p5-4-1-post-merge-validation-20261103`
- Exact source SHA: `bb9a032705bc100311d91b1d3f6506173e0784ef`
- Parent SHA: `58aca4d59bf42baec60058fc271937ec483d06c4`
- CI workflow blob: `234d11ab48d26d85ad300e887227b71683d1257c`
- CI policy test blob: `2aba882b93b79d8ed7d510c2ab5cdbe8888d6f92`

## Changes
1. Added the active branch to `.github/workflows/t0-validation.yml` push allowlist.
2. Updated `ci/test_ci_policy.py` to assert both supported branches.
3. Changed the CI policy test step to use `set -euo pipefail`, so a failed unittest command cannot be hidden by `tee` returning success.

## Workflow evidence
### Direct T0 workflow
- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41739693635
- Conclusion: **SUCCESS**
- Exact head SHA: `bb9a032705bc100311d91b1d3f6506173e0784ef`
- Job: T0 isolated automated contracts — SUCCESS; all 19 substantive steps completed successfully.
- Evidence artifact: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41739693635/artifacts/13280772186
- Artifact ID: `13280772186`; name: `t0-automated-evidence-41739693635`
- Downloaded ZIP SHA-256 independently recomputed: `8cf99e8c301e124d414c17d0ab63ab1ff92e03bf1f55e1489e4c699ecb99c910` (matches GitHub artifact digest).
- ZIP integrity: `unzip -t` passed.

### Integrated P5.4.1 workflow
- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41739693660
- Conclusion: **SUCCESS**
- Exact head SHA: `bb9a032705bc100311d91b1d3f6506173e0784ef`
- Jobs: 5/5 SUCCESS — exact source/environment verification; G2 writer routing and consumer regression; G1 Gateway transaction acceptance; T0 full automated regression; common-SHA/evidence publication.
- Artifacts:
  - T0: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41739693660/artifacts/13280772186
  - G1: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41739693660/artifacts/13280263110
  - G2: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41739693660/artifacts/13279553639

## Verified T0 test evidence
All listed invocations returned unittest `OK` on the exact SHA:
- CI policy: 14 tests.
- Market-data core/Gateway: 55 tests.
- Feeder lease: 11 tests.
- Feeder health + health API: 20 tests.
- Feeder lifecycle regression group: 91 tests.
- Atomic fencing regression group: 100 tests.
- Runtime health API regression group: 107 tests.
- SIGKILL recovery regression group: 101 tests.
- Operational contract tests: 11 tests; static audit verdict `T0_OPERATIONAL_CONTRACT_RELEASE_GATE=PASS`.
- Data integrity/candle continuity: 12 tests.

These are overlapping test-suite invocations; **do not sum them as unique test cases**. The SIGKILL audit recorded: process A terminated by SIGKILL; SQLite quick_check=ok; uncommitted batch rows=0; lease generation advanced 1→2; M15 and H1 coverage each 4/4; replacement lease generation valid; RESULT=PASS.

## Verdict
- Active-branch T0 push routing: **PASS**.
- T0 exact-SHA automated regression: **PASS**.
- Integrated P5.4.1 workflow: **PASS (5/5 jobs)**.
- Artifact payload integrity for downloaded T0 ZIP: **PASS** (ZIP valid; locally recomputed digest matches GitHub digest).
- T0 operational source/static release gate: **PASS**.

## Explicit limits
- These are isolated GitHub Actions tests, not Windows PC runtime acceptance.
- Windows canonical SQLite path/integrity: **NOT VERIFIED**.
- Actual Feeder startup/continuous operation, live M15/H1 freshness and exchange connectivity: **NOT VERIFIED / NOT RUN**.
- No canonical DB was opened or modified; no Feeder started; no exchange connection or market-data sync occurred.
- PostgreSQL/TimescaleDB canonical writer is not certified by this run.
- No live trading or real orders. Keep `AI_EXECUTION_ENABLED=false`.

## Next step
Proceed with the separately scoped Windows PC canonical-path and SQLite integrity verification only when that environment is available and the user explicitly authorizes access. Do not start the Feeder or connect an exchange as part of that check.


## P5.4.59-R1 — Feeder Runner Architecture & Fixture-Only Test Review (2026-11-04)

- Report: `docs/evidence/P5.4.59-R1-FEEDER-FIXTURE-REVIEW-2026-11-04.md`.
- Report commit: `1c6a76b950883ab0865c3e6e6236eb7f469fe3aa`.
- Active branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Tested source SHA: `7629aa0d8328394e9caff1eeffaf1402930d68a7`.
- T0 workflow: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41741878732 — **SUCCESS**, all 19 substantive steps.
- Integrated P5.4.1 workflow: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41741878993 — **SUCCESS**, 5/5 jobs on the same source SHA.
- Finding: `RecoveryPlanner.plan()` did not validate consistency between `coverage.complete` and `coverage.gaps`. Two fixture regressions now require `complete=false` iff gaps are reported, and `complete=true` iff no gaps are reported. Contradictory snapshots fail closed.
- Final invocation counts: atomic fencing/lifecycle group 102 OK; runtime health API group 109 OK; SIGKILL group 103 OK; CI policy 14 OK; operational contract 11 OK; data integrity/candle continuity 12 OK. These commands overlap and must not be summed as unique tests.
- Workflow count assertions, CI policy and static operational audit were synchronized to the expanded fixture suite.
- Source blobs: recovery test `69a39ed972f597be44daf980944317b91b471045`; `market_data/feeder.py` `4ac05efc2cd402fc2eddf1612953b106b976c03d`; T0 workflow `4abecd4cf95c35adb19da73e89cf0f5c9c8bc6e5`; CI policy `db302c46cb6b5f123e07200af389d01bd0ebcf5f`; static audit `139812700e6b72fe376e5784129b042187e06bfd`.
- T0 artifact ID `13281626301`, GitHub metadata digest `sha256:daf79d75db5f7e312b283d19e00994c095eb6cacdea5b70972a1bc89acdf24c2`.
- Integrated combined artifact ID `13282650628`, metadata digest `sha256:17b54b9f3690229d2c11aa384e3a5def7cd58470363522e2e65f9240496a3597`. Artifact payload byte-level checksum recomputation remains **NOT VERIFIED**.
- Verdict: fixture-only T0 validation **PASS**; integrated CI **PASS**; continuous production Feeder, PC canonical DB, exchange connectivity and production recovery **NOT VERIFIED / NOT RUN**.
- Runner architecture: GitHub-hosted runner is ephemeral CI only, not a continuous production Feeder host. Continuous host selection remains deferred; PC pause remains in force.
- No PC access, canonical DB creation/open, production Feeder startup, exchange connection, market-data sync, or execution. Keep `AI_EXECUTION_ENABLED=false`.
- Next: continue fixture-only malformed recovery snapshot and failure/restart lifecycle coverage on GitHub Actions. No production/runtime step is implied or authorized.


## P5.4.59-R2 — Malformed Recovery Snapshot Fixtures (2026-11-04)

- Report: `docs/evidence/P5.4.59-R2-MALFORMED-RECOVERY-FIXTURES-2026-11-04.md`.
- Report commit: `caca2a1490a888df1c97c050f0f30156a4798c1a`.
- Tested source SHA: `1757ffc0770c3dd7ca0406d4691dcd61ddac82a5`; active branch remains `feature/p5-4-1-post-merge-validation-20261103`.
- Added three fixture test methods for missing `coverage.complete`, null completeness and non-boolean completeness values (0, 1, "false", "true"). Existing strict RecoveryPlanner validation already rejects these; no production behavior change was needed.
- Regression invocation thresholds updated: atomic fencing 105; runtime health API 112; SIGKILL recovery 106. These command groups overlap; do not sum as unique tests.
- T0 workflow: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41742626536 — **SUCCESS**, all 19 substantive steps on exact SHA.
- Integrated P5.4.1: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41742626689 — **SUCCESS**, 5/5 jobs on exact same SHA.
- T0 artifact ID `13281393329`, metadata digest `sha256:44d95eb87e3fa16b5d7983caccedbcaf2fca193311c9b5bb74cdb766fd2e76f6`.
- Combined artifact ID `13281457705`, metadata digest `sha256:d31a03ea71d9cce87a2663cb8303241b6e7019de3663d9e768a85580018818f8`. Artifact payload byte-level checksum recomputation is **NOT VERIFIED**.
- Source blobs: recovery test `066452fc4aff8e3292bc0cc5b6cb0b430d842657`; feeder source unchanged `4ac05efc2cd402fc2eddf1612953b106b976c03d`; workflow `2635916fa18ad43191c84a47fe6edd01fe2a9a7a`; CI policy `a1adf1d1d1b0bcbb1d117cd9148e91f3903ceeec`; static audit `8d18fc807fb8c46feff75035fa9150174b0073dd`.
- Verdict: malformed snapshot fixtures **PASS**; T0 exact-SHA CI **PASS**; integrated workflow **PASS**; production Feeder, canonical PC DB and continuous runtime **NOT VERIFIED / NOT RUN**.
- Next: fixture-only recovery coordinator partial-sync/recheck tests; no PC/runtime or exchange action.
- Safety remains unchanged: no PC access, no canonical DB open/create, no production Feeder start, no exchange connection or data sync; keep `AI_EXECUTION_ENABLED=false`.

## P5.4.59-R3 — Recovery Coordinator Partial-Sync and Recheck Fixtures (2026-11-04)

- Report: docs/evidence/P5.4.59-R3-RECOVERY-COORDINATOR-PARTIAL-SYNC-2026-11-04.md.
- Work continues on the existing branch feature/p5-4-1-post-merge-validation-20261103; base documentation HEAD was 180282231eb1b88e8761ba0f5f30ffc2b921b142.
- Added two fixture-only RecoveryCoordinator tests: a multi-gap partial recovery where one gap remains after the second coverage read, and a malformed second snapshot missing coverage.complete.
- Both cases fail closed: remaining gaps raise RecoveryIncompleteError; malformed recheck snapshots raise ValueError. Neither path can return complete=true.
- No production runtime source changes. Existing tests continue to verify the injected sync callback as the only sync path.
- Updated overlapping T0 regression count gates: atomic fencing 107, runtime health API 114, SIGKILL recovery 108. Counts overlap and are not unique totals.
- T0 and integrated P5.4.1 GitHub Actions results are pending exact-SHA execution; do not mark PASS until both complete.
- Production Feeder, canonical PC DB, exchange connection and data sync remain NOT VERIFIED / NOT RUN. No PC access or runtime activation; keep AI_EXECUTION_ENABLED=false.

## P5.4.59-R3 — CI status reconciliation (2026-11-04)

- Tested source SHA: cee77b38181c2fa06a585714b9269b9a9c398e40.
- T0 automated validation run 41743273231: SUCCESS; all 19 substantive steps succeeded. Atomic fencing 107, runtime health API 114, SIGKILL recovery 108, and static operational contract all passed on the exact SHA.
- T0 artifact ID 13282236958; GitHub metadata digest sha256:50b70f750bbcf128d2baec625f7961629c5af255dc96e6788aaf29b04cdd3452. Payload byte-level checksum recomputation NOT VERIFIED.
- Integrated P5.4.1 run 41743273286: IN PROGRESS; preflight, G1 and G2 completed successfully; integrated T0 job was still running at this update.
- Current verdict: T0 fixture-only CI PASS; integrated workflow PENDING. Do not promote the overall integrated result until the run reaches SUCCESS.
- No PC/canonical DB/Feeder/exchange/data-sync/order execution.


## Final CI result (2026-11-04)

- Tested source SHA: cee77b38181c2fa06a585714b9269b9a9c398e40.
- T0 automated validation run 41743273231: SUCCESS; all substantive steps passed, including regression invocations 107 / 114 / 108 and static operational audit. Artifact 13282236958; metadata digest sha256:50b70f750bbcf128d2baec625f7961629c5af255dc96e6788aaf29b04cdd3452.
- Integrated P5.4.1 run 41743273286: SUCCESS; preflight, G1, G2, T0 and common-SHA evidence publication all succeeded against the same tested source SHA.
- Integrated artifacts: T0 13282466753 (sha256:95a30caeafc6efaec92dcb241013dc183cf9c1e728deac60c9727330b97f9d94); G1 13282857005 (sha256:07775fcb4035d308008eb5390e5fa83e958ae6440519a4386cc742fae72bfd33); G2 13282906319 (sha256:1beca3dbd79f31321e41b4c054f26e4847229dcdfffb36e37d0c96c3be1f0a98); combined 13282726794 (sha256:56bb4c233dd3cfe5237909ff3c18945287918724dab80e99e6a77101941e901f).
- GitHub artifact metadata digests are recorded; artifact payload bytes were not independently downloaded and re-hashed in this increment. Payload checksum verification remains NOT VERIFIED.
- Final fixture-only R3 CI verdict: PASS. Production Feeder, canonical PC DB, continuous runtime, exchange connectivity and production recovery remain NOT VERIFIED / NOT RUN.
- No PC access, DB open/create, Feeder startup, exchange connection, market-data sync or order execution.

## P5.4.60 — Recovery Coordinator Idempotency & Failure Lifecycle (2026-11-04)

- Report: docs/evidence/P5.4.60-RECOVERY-IDEMPOTENCY-FAILURE-LIFECYCLE-2026-11-04.md
- Base SHA: 3ab933035fa721d645463f6ef7ff5741d9b12972; branch remains feature/p5-4-1-post-merge-validation-20261103.
- Added two fixture-only tests: repeated recovery after coverage becomes complete is idempotent and does not re-call sync; a mid-batch callback failure followed by retry re-reads coverage and syncs only the remaining gap.
- Tests use mutable in-memory fixture state and injected callbacks only. No runtime source change.
- Updated overlapping T0 regression invocation thresholds: atomic fencing 109, runtime health API 116, SIGKILL recovery 110. Counts overlap and are not unique totals.
- Exact-SHA workflow run 41743708652: SUCCESS (completed), head SHA 57330081ae601493ddb3c64a98a3ead5914181b6. All five jobs succeeded: exact-source/preflight, G1, G2+T0 isolated regression, T0 full regression, and common-SHA evidence publication.
- PC, canonical DB, production Feeder, exchange, market-data sync and order execution remain NOT RUN. Keep AI_EXECUTION_ENABLED=false.


### P5.4.60 CI reconciliation — 2026-11-04

- Exact source SHA: `57330081ae601493ddb3c64a98a3ead5914181b6`; branch head verified unchanged before documentation update.
- Workflow: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41743708652 — **SUCCESS**, 5/5 jobs completed successfully.
- Jobs: preflight 126291314007; G2 + T0 isolated regression 126291358415; G1 126291358503; T0 full regression 126291358771; combined evidence 126291806967.
- T0/G2 job completed all test, operational contract, policy, compile and evidence-publication steps successfully. G1 and combined evidence publication also succeeded.
- Artifacts (GitHub metadata digests; payload bytes not downloaded/re-hashed in this increment):
  - Combined: 13283080513, `sha256:7d3a00224b727bc66d4c793ea9a6e08300bf8f0aef0d5c5418bcabe653926900`.
  - G1: 13282846847, `sha256:237f162722b44de0437c5bffd3936d56571383f0d037d9cd02b1428a182f95de`.
  - T0: 13282667248, `sha256:052463d7171fc221c351362fb2d81d7f627df56c39f6d2465b4818433da3e97c`.
  - G2: 13281434349, `sha256:cce960daf6eb8f274e97638a9234d8ddab4d430b3fda44204cebba9f23f4dd3e`.
- Verdict: P5.4.60 fixture-only source tests and integrated exact-SHA CI **PASS**. Artifact payload byte-level checksum verification **NOT VERIFIED**.
- Documentation closeout commit follows this tested source; it changes only this handoff and the P5.4.60 report. The test source SHA remains `57330081ae601493ddb3c64a98a3ead5914181b6`.
- No runtime code, PC, canonical DB, production Feeder, exchange, market-data sync or order execution. `AI_EXECUTION_ENABLED=false`.
- Next permitted step: continue fixture-only RecoveryCoordinator lifecycle edge-case review on this same branch; do not activate runtime.


## P5.4.61 — Recovery Planner Overlap and Duplicate Gap Contracts (2026-11-04)

- Report: `docs/evidence/P5.4.61-RECOVERY-PLANNER-OVERLAP-DUPLICATE-GAPS-2026-11-04.md`.
- Added fixture-only coverage for partially overlapping and exact-duplicate gap windows; both must be rejected with ValueError.
- No runtime source change; this formalizes the existing planner overlap rejection as a regression contract.
- Updated overlapping CI invocation thresholds: atomic fencing 110, runtime health API 117, SIGKILL recovery 111. Counts overlap.
- Exact-SHA GitHub Actions pending; do not claim PASS until all required jobs complete.
- No PC/canonical DB/production Feeder/exchange/data sync/order execution. Keep AI_EXECUTION_ENABLED=false.


## P5.4.61 result — 2026-11-04

- Final tested source SHA: `4384c33955011ad7a33e6957b26f97a7d89f42f5`.
- P5.4.61 fixture-only RecoveryPlanner overlap/duplicate-gap regression: **PASS**.
- T0 workflow run 41744435926: **SUCCESS**.
- Integrated P5.4.1 workflow run 41744436065: **SUCCESS**, 5/5 jobs (preflight, G2+T0, G1, T0 full regression, combined evidence).
- Combined artifact ID 13283042285, GitHub metadata digest `sha256:6bc351302876c7843d980e3a6742c3937798833b2a2f8d625a8a8c1506622b61`. G1/G2/T0 artifact details are in the P5.4.61 report.
- Artifact payload checksum recomputation remains **NOT VERIFIED**.
- This closeout changes documentation only; the verified test source remains `4384c33955011ad7a33e6957b26f97a7d89f42f5`.
- No PC, canonical DB, production Feeder, exchange connectivity, market-data sync or order execution. Keep `AI_EXECUTION_ENABLED=false`.
- Next permitted scope: continue fixture-only RecoveryPlanner/Coordinator boundary tests; runtime activation remains prohibited.


## P5.4.62 — Recovery Coordinator Boundary & Invalid Snapshot Lifecycle Tests (2026-11-04)

- Report: docs/evidence/P5.4.62-RECOVERY-COORDINATOR-INVALID-SNAPSHOT-BOUNDARY-2026-11-04.md.
- Tested source SHA: `1d83517e808f0fdeb7da2f6eb3162273546c09f4`.
- Added one fixture-only test method with eight malformed initial snapshot shapes. Each must raise ValueError, read once, and never call the injected sync callback.
- No production runtime source changes. CI thresholds: atomic fencing 111; runtime health API 118; SIGKILL recovery 112. These invocations overlap.
- T0 run 41744990176: **SUCCESS**, exact tested SHA; regression markers 111/118/112 and static operational audit PASS.
- Integrated P5.4.1 run 41744990552: **SUCCESS**, 5/5 jobs on the same exact SHA. Jobs: 126295624205, 126295675661, 126295675695, 126295676210, 126296028338.
- Artifacts: standalone T0 13282703680 (`sha256:efe690c4931ce633dcb844d66ccc0d796f0464a24aae8ab2db007dc4ec7e7cb2`); integrated G2 13283775052 (`sha256:beba9284abd88612b9b5378f4e6eea9dfe4e59602c93be31f9e5ae8548c104fa`); combined 13283555803 (`sha256:8501ab7cc7ab419a7f5821cf24032db04a530df43a6bef43b5c4c55db8fa0b39`); G1 13282913241 (`sha256:e5d3f6655c582cbe26b8cdc4ed83cbdf58a70c7d739f9627f6129339dd36b329`); integrated T0 13281744271 (`sha256:9780ad3a32dcc6028eda6b3a7701f9e9fba6bfb9a35d8e937514cfb538d51c0d`).
- Artifact payload bytes were not independently downloaded/re-hashed; payload checksum remains **NOT VERIFIED**.
- No PC, canonical DB, production Feeder, exchange, data sync or order execution. Keep `AI_EXECUTION_ENABLED=false`.
- Next: continue fixture-only RecoveryCoordinator retry/recheck malformed-window and callback failure boundary coverage; no runtime activation.


## P5.4.63 + T0-A Closeout Review (2026-11-04)

- P5.4.63 report: `docs/evidence/P5.4.63-RECOVERY-COORDINATOR-PARTIAL-WINDOW-RETRY-2026-11-04.md`.
- T0-A closeout review: `docs/evidence/T0-A-FIXTURE-CI-CLOSEOUT-REVIEW-2026-11-04.md`.
- T0 feeder test contract refreshed: `docs/T0_FEEDER_TEST_CONTRACT.md`; stale Codemagic staged-verification instructions removed and replaced with current GitHub Actions evidence and T0 gate states.
- Tested source SHA: `81252f3e954216d638d3655623d765c38b6f960b`.
- Source commit: https://github.com/kenznguyen/btcusdt-telegram-signals2/commit/81252f3e954216d638d3655623d765c38b6f960b.
- T0 standalone run 41747057849: **SUCCESS**, job 126302650681, all 19 substantive steps. Invocation markers 112 / 119 / 113; static operational audit PASS. Artifact 13283633166, metadata digest `sha256:eb1989f7fbb8c07cf575de81739920782612beafc728e009a0742226aac90924`.
- Integrated P5.4.1 run 41747057869: **SUCCESS**, 5/5 jobs: preflight 126302840094; G1 126302883297; G2+T0 126302883357; T0 full regression 126302883452; combined publication 126303133516.
- Integrated artifacts: G1 13284077569 (`sha256:69cd1c70bc31abf7852e62c92b892d4d9d79258e67fcf331914670effaa93cad`); G2 13284546036 (`sha256:aacb79ce1928b62d2955311478e1998dbce9039ca5aa09eb804476dc3045cb47`); T0 13283524018 (`sha256:2e68c20b98f101be50c5552f52618eb10d884e42c327dc07b34688bfae2c29ae`); combined 13283049864 (`sha256:c8009e0c534c06ac7d2898aaffbfd19d72032c0878fca72a17714fc6f5f358eb`). These are GitHub metadata digests; payload bytes were not independently re-hashed.
- Added P5.4.63 fixture contract for partial progress inside one failed recovery window; retry reads authoritative coverage again, requests only the remaining sub-window, then performs a final coverage recheck. No production runtime changes.
- T0-A fixture CI/static-contract closeout: **PASS**. Overall P1/T0 remains **OPEN**.
- T0-B PC/SQLite canonical path and integrity: **BLOCKED / DEFERRED** (PC use not reopened; path undecided). T0-C production Feeder runtime: **NOT RUN**. T0-D production backup/restore: **NOT RUN / NOT VERIFIED**. T0-E overall T0 acceptance: **BLOCKED**.
- No PC, canonical DB, production Feeder, exchange, market-data sync or order execution. Keep `AI_EXECUTION_ENABLED=false`.
- Next permitted step: when PC use is explicitly reopened, resolve canonical path and perform read-only storage identity/integrity preflight before any separately authorized runtime action.


## P5.4.64 — Android-First T0 Roadmap Reconciliation (2026-11-04)

- Scope: documentation reconciliation only. This section supersedes stale forward-looking statements in earlier handoff sections that describe Windows PC as the required T0 canonical host or direct T0-B runtime target. Earlier entries remain historical records of the decisions and assumptions at the time they were written.
- Owner-confirmed architecture, grounded in ADR-001 and the recorded P5.4.21/P5.4.22/P5.4.34/P5.4.35 decisions: Android-hosted SQLite is the canonical T0 store; Market Data and Paper Ledger share one physical SQLite file; Android is the initial sole canonical writer once separately activated; PC is a separate compute/backtest/AI consumer and read-only consumer of canonical data in the initial model.
- ADR-001 status corrected from blanket “PROPOSED — NOT ACCEPTED” to **PARTIALLY ACCEPTED — D1 host and physical topology only**. D2–D7 remain unresolved/proposed. This correction does not approve production implementation or activation.

### Corrected T0 gates

| Gate | Correct target and scope | Status |
|---|---|---|
| T0-A | Fixture contracts, static audit and GitHub Actions exact-SHA evidence | **PASS** |
| T0-B | Android canonical-storage preflight: resolve exact app-owned path and store identity; inspect existing state read-only; validate schema/migration authority and SQLite/WAL identity without creating or modifying the canonical DB | **BLOCKED / NOT RUN** — device/path evidence not yet collected; Android filesystem access requires explicit scope approval |
| T0-C | Controlled Android Feeder runtime acceptance against the approved Android canonical store, including C1–C8 runtime checks | **NOT RUN / NOT AUTHORIZED** — requires T0-B evidence, explicit permission to open/use the canonical DB and start the controlled Feeder, and separately scoped exchange/data-source permission if those are required |
| T0-D | Android-hosted shared-file backup/restore, WAL consistency, cross-domain Market Data + Paper Ledger recovery, external restore epoch and fencing | **NOT RUN / NOT VERIFIED** — requires approved D2–D7 recovery contract and separate explicit backup/restore test authorization |
| T0-E | Overall T0/P1 acceptance | **BLOCKED** until T0-B, T0-C and T0-D have acceptable evidence |

### Execution boundary and responsibilities

- GitHub Actions remains the CI runner for fixture-only tests, static audits and source/evidence checks. A GitHub-hosted runner is not a persistent Android Feeder host.
- Android/Termux or the approved Android application host owns platform-specific shadow/runtime validation and, after explicit approval, canonical T0 runtime. Do not infer that GitHub Actions can validate Android filesystem semantics or continuous device lifecycle.
- PC is optional compute infrastructure for AI training, FreqAI, backtesting and analysis. It is not a prerequisite for T0-B/T0-C and is not the canonical T0 writer.
- Android-first architecture does not itself authorize Android filesystem inspection, canonical DB creation/open/write, Feeder startup, exchange connection, market-data synchronization, production backup/restore or writer activation.
- Keep AI_EXECUTION_ENABLED=false; no live orders or exchange execution.
- Android Natural Doze remains **INTERRUPTED / DEFERRED** and outside this reconciliation. Do not investigate or rerun it unless the owner explicitly reopens that scope.

### Next permitted step

1. Reconcile ADR-002/host packaging and current source composition with the Android canonical-host decision; do source-only review first.
2. Prepare a read-only Android T0-B checklist that identifies the exact app-owned path through the approved host configuration without probing or opening the canonical DB.
3. Request explicit, narrowly scoped Android device access before any filesystem inspection. Request separate permission before opening the canonical DB, creating it, starting Feeder, connecting a source or syncing data.
4. Do not resume Windows PC T0-B or describe PC access as a prerequisite.

- This update is documentation-only. No tests/workflows, Android device access, database access, Feeder startup, exchange connection, market-data sync, backup/restore or order execution are performed by this update.


## P5.4.65 — ADR-002 and Android Canonical Host Source Review (2026-11-04)

- Evidence report: `docs/evidence/P5.4.65-ADR-002-ANDROID-CANONICAL-HOST-SOURCE-REVIEW-2026-11-04.md`.
- Report commit: `cab36e66884b849589f5cb0488cc9a876fd6eb9e`.
- Review baseline branch HEAD: `36f5b00dbccf63ec0ba4e7bc1ca8877483878acd`; active branch remains `feature/p5-4-1-post-merge-validation-20261103`.
- Reviewed ADR-002 blob `91f78f1be2d16d24585d7ebbd2b649abea91a0b7`, Gradle blob `419f30ca44e0ead9f7a595e5baa9dd11c0eb6623`, main manifest blob `e505a1829899f32c211f5390b5ae7753048ae15b`, MainActivity `c03c87993a1d696cdb9cab629114ff5ef8420ec2`, StrategyMonitorService `2d494af5e47d51d5111af2bc466e6aaf48a0e75b`, FiveLayerPanel `de1c6c1e11663a0c6f9330160665bf4c67e6af2f`, and FiveLayerApi `91c9ce61a14dc54a2e2bf1b47285d5645b3f119e`.
- Corrected P5.4.43 historical signing finding: current parallel build type explicitly uses the same environment-backed release signing config as regular release. The current Gradle blob is identical to the Gradle file at P5.4.49 successful paired-build source SHA `621857b4568af67fcf571968f1b732558e16ccbc`. Historical GitHub Actions run 41735402129 succeeded; verifier reported package identities and matching signer for the two APKs. This does not prove installed-device signer identity; artifact payload bytes were not independently re-hashed.
- Major implementation gap: current Android manifest has no custom signature permission or exported canonical-host IPC service; no AIDL/Binder contract or caller UID/package/signer verification was found. Existing StrategyMonitorService is non-exported and `onBind()` returns null, so it is not the approved ADR-002 Bound Service.
- Regular MainActivity starts the existing StrategyMonitorService, which constructs MarketEngine/StrategyEngine/OrderBookEngine/MultiSymbolScanner and persists state in SharedPreferences. This is not the Android T0 canonical SQLite Feeder/composition root.
- Parallel/.paper currently uses FiveLayerPanel and HTTPS FiveLayerApi endpoints for remote paper evaluation/control; it is not yet the ADR-002 local authenticated IPC client. Existing preferences, Compose state and remote server-side Paper API do not implement the approved shared Android SQLite file.
- No Android SQLite/Room/DataStore canonical persistence, canonical path authority, migration coordinator, shared transaction coordinator, Android LeaseStore, Paper Ledger/Risk repository or CanonicalRuntime composition root was found in the reviewed source.
- Verdict: **PASS** for source-only review and signing declaration reconciliation; **BLOCKED** for ADR-002 implementation; **NOT RUN** for tests/workflows; runtime/device/storage **NOT VERIFIED**. Report lists ordered implementation gaps and future fixture contracts.
- No code/Gradle/manifest/dependency/package changes, APK build/install, device access, DB path probing/open/create/write, Feeder, exchange, market-data sync, backup/restore, writer activation or order execution. Keep `AI_EXECUTION_ENABLED=false`. Natural Doze remains INTERRUPTED / DEFERRED.
- Next permitted step: P5.4.66 implementation-readiness gap specification — source-only plan and fixture acceptance contracts, including the boundary between remote Paper API and future host IPC. No code implementation until separately authorized.



## P5.4.66 — Android Canonical Host Implementation-Readiness Specification (2026-11-04)

- Evidence/specification: `docs/evidence/P5.4.66-ANDROID-CANONICAL-HOST-IMPLEMENTATION-READINESS-2026-11-04.md`.
- Specification commit: `2c16cb785d6f6aa164e31b63142a534d55c24bef`.
- Baseline handoff blob: `1a67b3c1925576af1f20e197f5d6086cba9713c3`; baseline ADR-002 blob: `91f78f1be2d16d24585d7ebbd2b649abea91a0b7`; input P5.4.65 report blob: `8682500ccc61cb6da82d90f97fb122dd292dd134`.
- Scope: documentation-only implementation-readiness plan; no Kotlin, Gradle, manifest, dependency, schema or runtime changes.
- Reaffirmed already-approved ADR-002 decisions: regular variant is sole canonical host; .paper is IPC-only client; explicit Bound Service + typed Binder/AIDL; signature-level permission plus host verification of UID/package/signer; one host-owned SQLite/transaction/lease/risk/ledger/audit authority; no DB capabilities or fallback writer to client; Core and independent AI intents pass through the same host-side Shared Risk Engine and Kill Switch.
- Identified ADR-002 documentation inconsistency: earlier “Open implementation decisions” still describes IPC primitive and package roles as undecided, despite P5.4.41 owner addendum resolving them. P5.4.41 addendum is authoritative; proposed follow-up is documentation-only reconciliation.
- Specified current remote FiveLayer Paper API disposition: canonical Paper evaluate/mutations and canonical ledger/risk/audit reads must move behind host IPC; remote health/research/FreqAI analytics and explicitly noncanonical read-only telemetry may remain separate. No dual-write, HTTP mutation fallback or remote acceptance as local canonical success.
- Ordered slices: (0) contract/ADR reconciliation; (1) host composition and capability boundary; (2) authenticated Bound Service contract; (3) canonical storage/transaction/lease/recovery contracts; (4) shared Risk Engine + separate Core/AI intent provenance; (5) .paper client migration and remote API containment; (6) GitHub Actions fixture/static acceptance; (7) separately authorized Android device acceptance.
- Enumerated D2–D7/schema/SQLite/WAL/transaction/lease/fencing/recovery/version-skew/signer-rotation decisions that must be resolved before storage implementation. No assumptions were converted into accepted decisions.
- Status: **PASS** for readiness specification; source implementation **BLOCKED**; D2–D7 storage/transaction/lease contract **BLOCKED**; fixture tests **SPECIFIED / NOT IMPLEMENTED**; GitHub Actions **NOT RUN**; Android device/runtime **NOT AUTHORIZED / NOT RUN**. T0-B remains BLOCKED, T0-C NOT RUN/NOT AUTHORIZED, T0-D NOT RUN/NOT VERIFIED, T0-E BLOCKED.
- No Android access, APK build/install, canonical DB path probing/open/create/write, Feeder, exchange, market-data sync, backup/restore, writer activation or orders. Keep `AI_EXECUTION_ENABLED=false`; Natural Doze remains INTERRUPTED / DEFERRED.
- Next permitted increment: P5.4.67 — resolve ADR-002 documentation conflict and produce a D2–D7 decision register by tracing existing ADR/handoff evidence, distinguishing owner-approved decisions from unresolved owner choices. No code or runtime implementation.



## P5.4.67 — ADR-002 Reconciliation and D2–D7 Decision Register (2026-11-04)

- Evidence: `docs/evidence/P5.4.67-ADR-002-D2-D7-DECISION-REGISTER-2026-11-04.md`.
- ADR-002 reconciliation commit: `0e17e277d75ecfaa2d77adef335915ce6b46d948`; new ADR-002 blob: `cc5b0c392906bf4bd4c95abddded4c8c76ec9231`.
- Decision-register commit: `a3491128d4e9153ee6ae3dc9585a8120b06e87aa`.
- Baseline handoff blob: `fac4272a5a0a05bea88252a4b10ca9f207879616`; ADR-001 baseline blob: `dd17f3cf92cb54c448ed69ce76a4823f0b35bc58`.
- Corrected ADR-002's stale “Open implementation decisions” wording. P5.4.41 owner addendum remains authoritative: regular host, .paper IPC client, explicit Bound Service + typed Binder/AIDL, signature-level permission, per-call UID/package/signer verification and same controlled signing identity direction.
- Exact application IDs as security allowlist values, installed certificate digest/key custody/rotation, final manifest names, Binder DTO/version/retry contract and runtime conformance remain OPEN or NOT VERIFIED.
- Traced ADR-001 D2–D7 verbatim: D2 per-store high-water semantics; D3 global snapshot barrier/cross-store consistency; D4 schema-version authority; D5 canonicalization/logical identity; D6 restore epoch/lease re-fencing/Kill Switch recovery; D7 backup destination/security/service objectives. All six explicitly remain **NOT DECIDED / BLOCKING**. No candidate requirement was promoted to an owner-approved decision.
- D1 remains **PARTIALLY ACCEPTED** only for Android canonical host, Android SQLite and one shared physical file for Market Data + Paper Ledger. Exact path, stable store ID, domain/transaction ownership, lease placement and backup details remain open.
- P5.4.65 source review and P5.4.49 historical paired-build facts are recorded with limits; neither proves current installed signer or implemented IPC/canonical DB runtime.
- Tests/workflows **NOT RUN** (documentation-only). No code, Gradle, manifest, IPC, schema, runtime, device, DB, Feeder, exchange, sync, backup/restore or writer activation. `AI_EXECUTION_ENABLED=false`.
- Status: ADR-002 documentation **PASS**; D2–D7 decision register **PASS as traceability record**, decisions themselves **BLOCKED / NOT DECIDED**; T0-B **BLOCKED**, T0-C **NOT RUN / NOT AUTHORIZED**, T0-D **NOT RUN / NOT VERIFIED**, T0-E **BLOCKED**.
- Next permitted increment: owner decision review of D2–D7, without implementation or operational access.

## P5.4.68 — D2 High-Water Cursor Decision Proposal (2026-11-04)

- Proposal: `docs/evidence/P5.4.68-D2-HIGH-WATER-CURSOR-PROPOSAL-2026-11-04.md`.
- Proposal commit: `493ce8167b8443ee98b8aced570a096e3b9f324a`.
- Baseline handoff blob: `8bb6785efad731128bcf89af5a9c99d786bdaec7`.
- Scope: documentation-only technical proposal; no owner decision inferred or applied.
- Proposed model: Market Data per-partition contiguous closed-candle coverage cursor with explicit gaps; Paper Ledger dedicated monotonic commit sequence with idempotency and same-transaction state/audit advancement; Risk State version bound to the ledger sequence for same-transaction changes; Feeder Lease generation kept separate as a host-checked fencing token.
- Proposed manifest evidence is a vector of domain cursors, not a synthetic global integer. It does not prove snapshot atomicity; D3 remains required.
- Five owner decisions are listed in the proposal. D2 remains **PROPOSED / NOT DECIDED**; D3–D7 unchanged.
- Fixture-only acceptance tests specified but not implemented. GitHub Actions **NOT RUN**.
- No code/schema/migration/IPC/runtime/device/DB/Feeder/exchange/sync/backup/restore/writer activation. `AI_EXECUTION_ENABLED=false`.
- Status: proposal documentation **PASS**; D2 owner decision **NOT DECIDED**; T0-B **BLOCKED**, T0-C **NOT RUN / NOT AUTHORIZED**, T0-D **NOT RUN / NOT VERIFIED**, T0-E **BLOCKED**.
- Next: owner decision on the five D2 questions; if approved, record D2 in ADR-001 and proceed to D3 proposal. No implementation before approval.

## P5.4.69 — D2 Owner Decision Recorded (2026-11-04)

- Owner explicitly approved all five D2 decisions, with no additional notes:
  - **D2.1 APPROVED:** Market Data per-partition contiguous closed-candle cursor; gaps/backfill recorded separately.
  - **D2.2 APPROVED:** dedicated monotonic Paper Ledger commit sequence, stable idempotency key, and same-transaction advancement of affected state plus audit; `paper_audit.id` alone is insufficient.
  - **D2.3 APPROVED:** same-transaction Risk State changes bind to the Ledger sequence; independently committed risk-only transitions require a separate monotonic risk version committed with risk mutation and audit.
  - **D2.4 APPROVED:** Feeder Lease generation remains separate from data cursors; host-side fencing is validated at every canonical write boundary.
  - **D2.5 APPROVED:** manifest uses a domain-cursor evidence vector; it is descriptive and does not prove atomic snapshot consistency. D3 remains required.
- No additional owner notes.
- ADR-001 updated to **PARTIALLY ACCEPTED — D1 host/physical topology and D2 high-water semantics**. D3–D7 remain **NOT DECIDED / BLOCKING**. D1 residual path/store/transaction/lease/WAL/backup details remain open.
- P5.4.68 proposal updated to an owner decision record: D2 **ACCEPTED**; fixture tests remain **SPECIFIED / NOT IMPLEMENTED**.
- Scope: documentation-only. No code, schema, migration, IPC, tests or workflow execution. No Android device access, canonical DB open/create/write, Feeder, exchange connection, data sync, backup/restore, writer activation or orders.
- Post-write verification: all three documents fetched again from the same branch; ADR-001 blob `51a4e7e8d56dcdb74acae850bf7e48b993d9b502`, P5.4.68 blob `b7a1f4e65e442651961a29e7f3d854120f50ee76`, handoff blob before this verification-note update `80fc94eca921526dddb771c3fb9b657f897a9758`. Decision-record commit chain: ADR-001 `608d18b6badce62aedd28e3d99ec9ebdd063e177` → P5.4.68 `ddd798519413366da8163ad2026c13ab5af4ebe8` → handoff `2ddc0c96a215ab81196855f38a32933d4a9de849`. The complete D2 documentation update was present at source commit `2ddc0c96a215ab81196855f38a32933d4a9`. No new GitHub Actions run; workflow status **NOT RUN**.
- Gate status: T0-A **PASS** (prior fixture-only closeout); T0-B **BLOCKED / NOT RUN**; T0-C **NOT RUN / NOT AUTHORIZED**; T0-D **NOT RUN / NOT VERIFIED**; T0-E **BLOCKED**.
- Safety: `AI_EXECUTION_ENABLED=false`; paper-only; Android Natural Doze remains **INTERRUPTED / DEFERRED**.
- Next permitted work: prepare D3 snapshot-barrier/cross-domain consistency proposal, explicitly **PROPOSED / NOT DECIDED**, without assuming D2 approval decides D3. No runtime implementation until separately authorized.


## P5.4.70 — D3 Snapshot Barrier & Cross-Domain Consistency Proposal (2026-11-04)

- Proposal: `docs/evidence/P5.4.70-D3-SNAPSHOT-BARRIER-CROSS-DOMAIN-CONSISTENCY-PROPOSAL-2026-11-04.md`.
- Proposal creation commit: `a120498e3e635bde017efe3322c23c71e27c926c`; verified current proposal blob: `b5482ca02ccaff5c1de5418c3cf12caf3d1c072d`.
- ADR-001 update commit: `d9e86da838e50ebe641fe16e766289a34e5d3552`; verified current ADR blob: `f81a6022b4c0d1f53caf04b6f07969264241ec55`.
- Branch: `feature/p5-4-1-post-merge-validation-20261103`; source baseline before P5.4.70: `bee4d539962211c3672f6c0ad433d834f00d890b`.
- Scope: documentation-only D3 proposal for the owner-approved Android-hosted single shared SQLite file. D2 remains ACCEPTED; D3 is **PROPOSED / NOT DECIDED**; D4–D7 remain **NOT DECIDED / BLOCKING**.
- Recommended protocol: one regular-host-owned write barrier for all included canonical mutation domains; close new-write admission and drain in-flight transactions; revalidate host/lease fencing; capture the full D2 vector and metadata from one SQLite read transaction; use SQLite Online Backup API into staging; verify integrity/domain invariants and physical digest; atomically publish only after verification; fail closed on stale fencing, unknown transaction outcomes, process interruption, failed publication or uncertain barrier release.
- WAL boundary: do not copy only the main DB file or independently copy DB/WAL/SHM. Use the supported SQLite backup mechanism to include committed WAL-backed state. Checkpoint is not a substitute for the backup API.
- Consistency boundary: proposed point-in-time snapshot covers the shared SQLite file only. External lease authority, restore epoch, Kill Switch/recovery latch, app configuration and exchange state are not claimed as captured; D6/D7 remain required.
- Fixture acceptance: 20 scenarios specified (barrier/drain, vector coherence, WAL inclusion, fencing, partial failure, publication, process interruption and release ownership). Tests are **SPECIFIED / NOT IMPLEMENTED**; no test evidence is claimed.
- GitHub Actions: **NOT RUN** for P5.4.70; no workflow run or artifact exists for this increment. No tests were executed.
- D3 owner approval: **NOT RECEIVED**. Six decision questions are in the proposal. No owner decision is inferred.
- T0-A **PASS** from prior fixture-only closeout (not rerun); T0-B **BLOCKED / NOT RUN**; T0-C **NOT RUN / NOT AUTHORIZED**; T0-D **NOT RUN / NOT VERIFIED**; T0-E **BLOCKED**.
- No code, schema, migration, IPC, Android device access, canonical DB open/create/write, Feeder startup, exchange connection, market-data sync, backup/restore execution, writer activation or orders. Keep `AI_EXECUTION_ENABLED=false`; paper-only. Android Natural Doze remains **INTERRUPTED / DEFERRED**.
- Next step: obtain owner decisions on the six D3 questions. If accepted, record D3 and proceed to D4 proposal. No implementation or production operation until separately authorized.


## P5.4.70 — D3 Owner Decision Recorded (2026-11-04)

- Owner decision: **APPROVE D3.1–D3.6 and all supplemental conditions A–E**, with note "Không có". This is an explicit owner approval; no additional conditions were inferred.
- D3.1: one Android Canonical Host-owned write barrier covers every included canonical mutation domain; close new-write admission and drain in-flight transactions; timeout/unknown outcome aborts barrier establishment.
- D3.2: one SQLite read snapshot plus SQLite Online Backup API (or documented supported equivalent); raw main-file-only copy and independent DB/WAL/SHM copy are not accepted.
- D3.3: full D2 vector and manifest metadata are read from the same SQLite read transaction; timestamps are diagnostic only.
- D3.4: staging → integrity/domain verification → atomic publication; no accepted manifest for partial/unverified output.
- D3.5: stale fencing, uncertain transaction outcome, process death while held, backup/verification/publication failure and uncertain barrier release fail closed; writers remain blocked until safe ownership and recovery reconciliation.
- D3.6: consistency boundary is the shared SQLite file only. External lease authority, restore epoch, Kill Switch/recovery latch, app configuration and exchange state are not claimed as included.
- Supplemental A: minimize and measure write-pause/admission/capture duration; never automatically reopen writers after timeout or uncertain state.
- Supplemental B: immutable backup identity includes unique Backup ID, Barrier ID, source DB identity, D2 vector, physical SHA-256, verification result and completion status; filename/timestamp alone is not identity.
- Supplemental C: preserve the last known-good backup until the replacement is fully verified and published.
- Supplemental D: SQLite integrity check is necessary but insufficient; additionally verify foreign-key/domain invariants, Ledger sequence/audit consistency, Risk State↔Ledger sequence, Market Data cursor↔gap/backfill and isolated-copy openability. No repair/constructor paths during verification.
- Supplemental E: D3 approves snapshot validity only, not successful restore. Restore proof remains D6/D7 and separately authorized.
- D3 is **ACCEPTED as an architecture contract only**. Implementation details remain open; D4–D7 remain NOT DECIDED.
- Proposal decision-record commit: `e1e04e1db78a8057ce05f25a88fae960d897b5f1`; proposal blob: `bff7db5f6027bf4ba11ebe4cf26611e78cd18221`.
- ADR-001 decision update commit: `f6ac7261ae10141348716e061808d70db95f6195`; ADR blob: `17bc208e6c129c226b952a5a5715da3b6491d613`.
- This handoff update records owner decision and evidence pointers. GitHub Actions: **NOT RUN**; tests: **NOT RUN**; fixture plan remains specified/not implemented; no workflow run or artifact exists for this increment.
- No code, schema, migration, IPC, device access, canonical DB open/create/write, Feeder startup, exchange connection, market-data sync, backup/restore execution, writer activation or orders. Keep `AI_EXECUTION_ENABLED=false`; paper-only. Android Natural Doze remains **INTERRUPTED / DEFERRED**.
- Next step: prepare D4 Schema Version Authority proposal as documentation-only work. No implementation or production operation until separately approved.


## P5.4.71 — D4 SQLite Schema Version Authority Proposal (2026-11-04)

- Proposal: `docs/evidence/P5.4.71-D4-SQLITE-SCHEMA-VERSION-AUTHORITY-PROPOSAL-2026-11-04.md`.
- Proposal commit: `7d6da0a1c42606490c95762c3290b565d520524c`.
- ADR-001 reference update commit: `d1a7d2ffa46657c2dadfd999edf5908657bddeab`; ADR blob: `910dc19f0728d3c69109c50f86a04902f982432f`.
- Branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Scope: documentation-only D4 proposal and read-only source review. No implementation, schema, migration, test or runtime change.
- Source reviewed:
  - `market_data/store.py` blob `b28601aed70097afcb7a4eea2dd93ed163ae1cec`: explicit SQLite candle schema initialization; no SQLite migration registry in this file.
  - `paper_execution/ledger.py` blob `68209ce48a6e5e9a995f93167684133e41cc7f55`: constructor creates/ensures ledger/risk/equity schema and seeds legacy state; not a formal versioned migration authority.
  - `market_data/migrations.py` blob `5ff71e3ffa9e7c14d26d09f3881313bbbdc3bef0`: migration ID + checksum registry is for PostgreSQL only, not canonical Android SQLite.
  - `market_data/storage.py` blob `99b66a4d183b8664f28d6638d8d87416d32847c9`: SQLite default/PostgreSQL opt-in adapter; does not establish a shared SQLite migration registry.
- Proposal: one database-wide SQLite `schema_migrations` authority; immutable migration IDs, ordered sequence and exact-byte SHA-256; DDL and registry row in one transaction; explicit maintenance-only migration runner; registry authoritative and `PRAGMA user_version` optional same-transaction mirror only; explicit read-only legacy inventory/adoption; read-only verifier and fail-closed on missing/unknown/mismatched chain or schema drift; include migration-chain evidence in D3 same-snapshot manifest.
- D4 status: **PROPOSED / NOT APPROVED**. Owner decision has not been received. D5–D7 remain NOT DECIDED.
- Fixture acceptance: 20 cases specified, **NOT IMPLEMENTED / NOT RUN**. GitHub Actions **NOT RUN**; no workflow run/artifact exists for this increment.
- T0 gates unchanged: T0-A prior fixture-only PASS (not rerun); T0-B BLOCKED / NOT RUN; T0-C NOT RUN / NOT AUTHORIZED; T0-D NOT RUN / NOT VERIFIED; T0-E BLOCKED.
- No canonical DB opened/created/modified/inspected; no Android device access; no Feeder, exchange connection or market-data sync; no backup/restore; no writer activation. Keep `AI_EXECUTION_ENABLED=false`; paper-only. Android Natural Doze remains **INTERRUPTED / DEFERRED**.
- Next step: owner review of D4.1–D4.7. If approved, record decision in ADR/evidence/handoff; only then prepare D5 proposal. No runtime implementation is authorized by this proposal.


## P5.4.72 — D4 owner approval recorded (2026-11-04)

- Decision: **APPROVE D4.1–D4.7** exactly as specified in `docs/evidence/P5.4.71-D4-SQLITE-SCHEMA-VERSION-AUTHORITY-PROPOSAL-2026-11-04.md`; no amendments requested.
- Approved contract: one database-wide SQLite migration authority for the shared file; immutable migration IDs/sequence/domain/exact-byte SHA-256; DDL and registry row in one transaction through explicit maintenance only; registry is authoritative and `PRAGMA user_version` is optional mirror/diagnostic; legacy DB remains `LEGACY / UNVERSIONED` until separately approved baseline adoption; read-only fail-closed verifier; D3 manifest includes migration authority and applied chain from the same read snapshot.
- Documentation records updated: P5.4.71 proposal, ADR-001, this handoff.
- Scope: documentation/decision recording only. No code, schema, migration runner, tests, IPC or app configuration changed.
- Tests / GitHub Actions: **NOT RUN**; no workflow run or artifact for this docs-only decision record.
- Canonical DB: **NOT OPENED / NOT CREATED / NOT MODIFIED**. Android device not accessed. Feeder not started; no exchange connectivity or market-data sync; no backup/restore; no writer activation.
- Status: D4 **APPROVED (architecture only)**. D4 implementation **NOT IMPLEMENTED / NOT VERIFIED**. D4 fixture acceptance tests **NOT IMPLEMENTED / NOT RUN**. D5–D7 **NOT DECIDED**.
- Safety: keep `AI_EXECUTION_ENABLED=false`; paper-only.
- Next step: prepare D5 canonicalization and digest-rules proposal. D5 must define deterministic schema representation and canonicalization version before any implementation. No implementation or canonical DB operation is authorized by D4 approval.


## P5.4.73 — D5 canonicalization and digest rules proposal (2026-11-04)

- Proposal: `docs/evidence/P5.4.73-D5-CANONICALIZATION-AND-DIGEST-RULES-PROPOSAL-2026-11-04.md`.
- Proposal commit: `2effbb6c5fa7203bb0d743ed71b950d5aabf1ad7`.
- D5 status: **PROPOSED / NOT APPROVED**; owner decision required for D5.1–D5.4.
- Proposed layers: exact physical snapshot SHA-256; D4 migration-chain digest; logical schema digest based on versioned canonical envelope and SQLite schema/introspection; optional row/data digest excluded from initial mandatory scope.
- Proposed safeguards: record canonicalization/runtime identity; no initial SQLite/PostgreSQL equivalence claim; unsupported or ambiguous inputs fail closed; digests do not override D3 barrier, D4 chain or integrity/domain checks.
- ADR-001 updated to mark D4 approved and reference P5.4.73 as the pending D5 proposal.
- D4 decision recording is complete; latest branch head at this handoff update will be recorded by the resulting commit SHA.
- Scope: documentation only. No source code, schema, migration, test, IPC, app configuration or runtime changed.
- Tests / GitHub Actions: **NOT RUN**; no workflow run/artifact for this proposal.
- Canonical DB/device/Feeder/exchange/synchronization/backup/restore/writer: **NOT TOUCHED**.
- D4: **APPROVED (architecture only)**; implementation NOT IMPLEMENTED / NOT VERIFIED. D5: **PROPOSED / NOT APPROVED**. D6–D7: **NOT DECIDED**.
- Safety: keep `AI_EXECUTION_ENABLED=false`; paper-only.
- Next step: owner review of D5.1–D5.4; do not implement or run canonicalization against the canonical database before explicit approval and separate implementation/test scope.


## P5.4.74 — D5 owner approval recorded (2026-11-04)

- Decision: **APPROVE D5.1–D5.4** exactly as specified in `docs/evidence/P5.4.73-D5-CANONICALIZATION-AND-DIGEST-RULES-PROPOSAL-2026-11-04.md`; no amendments requested.
- Accepted contract: distinct exact-byte physical snapshot SHA-256; ordered D4 migration-chain digest; versioned logical SQLite schema digest using conservative SQL bytes plus structured introspection and runtime identity; optional logical row/data digest excluded from initial mandatory scope; no initial SQLite/PostgreSQL equivalence claim; explicit algorithm/canonicalization identity; fail-closed unknown/ambiguous inputs.
- Remaining design details: exact canonical envelope grammar/framing, canonicalization identifier/version value, SQLite runtime pinning policy, introspection field schema, virtual-table module inventory and digest composition. Must be specified and fixture-tested before implementation.
- Decision/evidence updated: P5.4.73 proposal and ADR-001. This handoff records the owner decision.
- Scope: documentation/decision recording only. No code, schema, migration runner, canonicalizer, tests, IPC or app configuration changed.
- Tests / GitHub Actions: **NOT RUN**; no workflow run or artifact for this docs-only decision record.
- Canonical DB: **NOT OPENED / NOT CREATED / NOT MODIFIED / NOT INSPECTED**. Android device not accessed. Feeder not started; no exchange connectivity or market-data sync; no backup/restore; no writer activation.
- Status: D4 **APPROVED (architecture only)**; D5 **APPROVED (architecture only)**. D4/D5 implementation **NOT IMPLEMENTED / NOT VERIFIED**. D5 fixture acceptance tests **NOT IMPLEMENTED / NOT RUN**. D6–D7 **NOT DECIDED**.
- Safety: keep `AI_EXECUTION_ENABLED=false`; paper-only. Android Natural Doze remains **INTERRUPTED / DEFERRED**.
- Next step: prepare D6 restore epoch, lease re-fencing and Kill Switch recovery proposal. D5 approval does not authorize restore design execution, canonical DB access or writer activation.


## P5.4.75 — D6 restore/recovery fencing proposal (2026-11-04)

- Proposal: `docs/evidence/P5.4.75-D6-RESTORE-EPOCH-LEASE-REFENCING-KILL-SWITCH-PROPOSAL-2026-11-04.md`.
- Proposal commit: `150c8a3576e280a0c198352da74df0eb51f77f06`.
- D6 status: **PROPOSED / NOT APPROVED**; owner decision required for D6.1–D6.7.
- Proposal establishes external monotonic Restore Epoch Authority and Recovery Latch; positive prior-owner stop/fence proof; idempotent irreversible epoch allocation; isolated staging and verified publication; lease-generation re-fencing above restored and external floors; stale intent/capability/order-book/risk provenance invalidation; Kill Switch held through readiness and separate authenticated acknowledgement; latch release, Kill Switch clearing and writer admission remain separate decisions.
- ADR-001 updated: D5.1–D5.4 marked owner-approved; D6 proposal linked as pending.
- Scope: documentation only. No code, schema, migration, restore implementation, tests, IPC, app configuration or runtime changed.
- Tests / GitHub Actions: **NOT RUN**; no workflow run or artifact for this proposal.
- Canonical DB/device/Feeder/exchange/synchronization/production backup/restore/writer: **NOT TOUCHED**.
- Status: D4 **APPROVED (architecture only)**; D5 **APPROVED (architecture only)**; D6 **PROPOSED / NOT APPROVED**; D7 **NOT DECIDED**. D4/D5 implementation NOT IMPLEMENTED / NOT VERIFIED; D5 fixtures NOT IMPLEMENTED / NOT RUN.
- Safety: keep `AI_EXECUTION_ENABLED=false`; paper-only. Android Natural Doze remains **INTERRUPTED / DEFERRED**.
- Next step: owner review of D6.1–D6.7. No restore, epoch allocation, lease mutation, Kill Switch clearing or writer activation is authorized.


## P5.4.76 — D6 owner approval recorded (2026-11-04)

- Decision: **APPROVE D6.1–D6.7** exactly as specified in `docs/evidence/P5.4.75-D6-RESTORE-EPOCH-LEASE-REFENCING-KILL-SWITCH-PROPOSAL-2026-11-04.md`; no amendments requested.
- Accepted contract: external monotonic Restore Epoch Authority and Recovery Latch; positive prior-owner stop/fence proof; idempotent irreversible epoch allocation; isolated staging and verified publication; lease-generation re-fencing above restored/external floors; stale intent/capability/market-assumption invalidation; Kill Switch held through readiness and separate authenticated acknowledgement; latch release, Kill Switch clearing and writer admission remain separate decisions; fail-closed recovery.
- Decision records updated: P5.4.75 proposal and ADR-001.
- Scope: documentation/decision recording only. No code, schema, migration, restore implementation, epoch/lease mutation, tests, IPC, app configuration or runtime changed.
- Tests / GitHub Actions: **NOT RUN**; no workflow run or artifact for this docs-only decision record.
- Canonical DB/device/Feeder/exchange/synchronization/production backup/restore/writer: **NOT TOUCHED**.
- Status: D4 **APPROVED (architecture only)**; D5 **APPROVED (architecture only)**; D6 **APPROVED (architecture only)**; D7 **NOT DECIDED**. D6 implementation NOT IMPLEMENTED / NOT VERIFIED; D6 fixtures NOT IMPLEMENTED / NOT RUN.
- Safety: keep `AI_EXECUTION_ENABLED=false`; paper-only. Android Natural Doze remains **INTERRUPTED / DEFERRED**.
- Next step: prepare D7 proposal for backup destination, encryption/key custody, retention, RPO/RTO and restore authorization. No restore or writer operation is authorized.


## P5.4.77 — D7 backup security and recovery policy proposal (2026-11-04)

- Proposal: `docs/evidence/P5.4.77-D7-BACKUP-SECURITY-RETENTION-RPO-RTO-RESTORE-AUTHORIZATION-PROPOSAL-2026-11-04.md`.
- Proposal commit: `6a6a04139837b95ed70b6719dbe0a083ce855cb5`.
- D7 status: **PROPOSED / NOT APPROVED**; owner decision required for D7.1–D7.6.
- Proposal covers separate canonical/staging/published-backup/recovery-audit trust boundaries; independent immutable destination, authenticated manifest and read-back verification; encryption and separate auditable key custody; last-known-good retention and deletion safeguards; explicit RPO/RTO; authenticated restore approval and separation of backup, restore, readiness, latch, Kill Switch and writer gates.
- Explicitly unresolved: destination/provider/failure domain, encryption suite and key custody/escrow/rotation, retention schedule/capacity, numerical RPO/RTO, restore approver roles/emergency exception, data residency/export and cost. No PC or VPS is selected or required by this proposal.
- ADR-001 updated to link P5.4.77 as pending D7.
- Scope: documentation only. No code, schema, backup/restore implementation, keys, tests, IPC, app configuration or runtime changed.
- Tests / GitHub Actions: **NOT RUN**; no workflow run or artifact for this proposal.
- Canonical DB/device/PC/production storage/key material/Feeder/exchange/synchronization/backup/restore/writer: **NOT TOUCHED**.
- Status: D4 **APPROVED (architecture only)**; D5 **APPROVED (architecture only)**; D6 **APPROVED (architecture only)**; D7 **PROPOSED / NOT APPROVED**. D6 implementation NOT IMPLEMENTED / NOT VERIFIED; D6 fixtures NOT IMPLEMENTED / NOT RUN. D7 fixtures NOT IMPLEMENTED / NOT RUN. Numerical RPO/RTO NOT SET / NOT VERIFIED.
- Safety: keep `AI_EXECUTION_ENABLED=false`; paper-only. Android Natural Doze remains **INTERRUPTED / DEFERRED**.
- Next step: owner review of D7.1–D7.6. No destination selection, key provisioning, backup scheduling, restore, Kill Switch clearing or writer activation is authorized.


## P5.4.78 — D7 owner approval recorded (2026-11-04)

- Decision: **APPROVE D7.1–D7.6** exactly as specified in `docs/evidence/P5.4.77-D7-BACKUP-SECURITY-RETENTION-RPO-RTO-RESTORE-AUTHORIZATION-PROPOSAL-2026-11-04.md`; no amendments requested.
- Accepted policy: independent canonical/staging/published-backup/recovery-audit trust boundaries; independent immutable destination, authenticated manifest and read-back verification; encryption before leaving trusted capture boundary with separate auditable key custody; protected last-known-good retention/deletion safeguards; explicit measurable owner-approved RPO/RTO; authenticated restore approval with separate backup/restore/readiness/latch/Kill Switch/writer gates; CI credentials never substitute for restore authorization.
- Still unresolved: destination/provider/failure domain, encryption suite and key custody/escrow/rotation, retention schedule/capacity, numerical RPO/RTO, approver roles/emergency exception, data residency/export and operational cost. No PC/VPS requirement introduced.
- Scope: documentation/decision recording only. No code, schema, backup/restore implementation, key material, tests, IPC, app configuration or runtime changed.
- Tests / GitHub Actions: **NOT RUN**; no workflow run or artifact for this docs-only decision.
- Canonical DB/device/PC/production storage/key material/Feeder/exchange/synchronization/backup/restore/writer: **NOT TOUCHED**.
- Status: D2 **APPROVED**; D3 **APPROVED**; D4 **APPROVED**; D5 **APPROVED**; D6 **APPROVED**; D7 **APPROVED** (architecture/policy only). Implementation and fixture acceptance remain NOT IMPLEMENTED / NOT VERIFIED / NOT RUN as applicable.
- Safety: keep `AI_EXECUTION_ENABLED=false`; paper-only. Android Natural Doze remains **INTERRUPTED / DEFERRED**.
- Next step: perform documentation/source-only cross-contract consistency review for D2–D7 and prepare a bounded fixture-only acceptance-test plan. Do not select a live destination, provision keys, access canonical DB, execute backup/restore, clear Kill Switch or activate writers without separate explicit authorization.


## P5.4.79 — D2–D7 cross-contract consistency review (2026-11-04)

- Review: `docs/evidence/P5.4.79-D2-D7-CROSS-CONTRACT-CONSISTENCY-AND-FIXTURE-PLAN-2026-11-04.md`.
- Reviewed ADR-001, current handoff and D2–D7 decision/evidence documents. D2–D7 are all **OWNER-APPROVED at architecture/policy level only**; D1 remains partially accepted with exact Android DB path/stable identity open.
- Result: cross-contract architecture **PASS WITH EXPLICIT OPEN DESIGN BLOCKERS**. D2 vector and D3 same-read-snapshot barrier align; D4 migration chain and D5 schema digest align; D6 external epoch/latch and re-fencing remain outside rollback-prone SQLite state; D7 RPO evidence uses Ledger sequence and contiguous Market Data cursor vector.
- Blocking clarification before digest/publication implementation: distinguish pre-encryption SQLite snapshot-image SHA-256 from encrypted destination-object SHA-256 and bind both in the authenticated manifest. This is a design clarification proposal, not an amendment to D5/D7 approval.
- Other open details: D3 barrier/runtime/publication contract; D4 DDL/transaction/lock/reconciliation; D5 canonical envelope/runtime/introspection; D6 external authority/stop-proof/epoch API; D7 destination, key custody, retention, numerical RPO/RTO and approver roles.
- Fixture plan: **60 cases SPECIFIED / NOT IMPLEMENTED / NOT RUN**, grouped F1–F7 across D2 vector, D3 barrier, D4 migration, D5 digest, D7 encrypted publication/retention, D6 restore fencing/authorization and negative safety.
- GitHub Actions: **NOT RUN**; no workflow run or artifact for this docs-only review. Source SHA is the branch commit recorded below; no source/runtime code changed.
- Status: architecture consistency **PASS WITH OPEN BLOCKERS**; documentation chronology reconciled in ADR-001; production implementation **BLOCKED**; fixture tests **NOT IMPLEMENTED / NOT RUN**.
- No canonical DB, Android device, PC, production storage, key material, Feeder, exchange, backup/restore or writer was accessed. Keep `AI_EXECUTION_ENABLED=false`; paper-only.
- Next step: resolve digest-domain/manifest field semantics and the remaining detailed contracts, then separately authorize fixture-only implementation on GitHub Actions. No production/runtime operation is authorized.


## P5.4.80 — Digest domains and authenticated manifest proposal (2026-11-04)

- Proposal: `docs/evidence/P5.4.80-DIGEST-DOMAINS-AND-AUTHENTICATED-BACKUP-MANIFEST-PROPOSAL-2026-11-04.md`.
- Status: **PROPOSED / NOT APPROVED**; owner decision required for P5.4.80 D1–D5.
- Separates `snapshot_image_sha256` over exact verified SQLite backup image bytes before encryption from `encrypted_object_sha256` over exact encrypted payload bytes verified by complete destination read-back.
- Proposes authenticated manifest binding both digest domains and lengths, Backup ID, immutable payload object ID/version and D2–D5 evidence. Manifest authentication is distinct from payload digest; secret key material never enters manifest/logs/artifacts.
- Proposes separate immutable payload and manifest objects, AVAILABLE only after both are durable/authenticated/verified; uncertain outcomes remain STAGING/UNKNOWN and cannot replace last-known-good.
- Restore order: authenticate manifest → verify ciphertext digest/length/object version → decrypt through approved key authority → verify snapshot-image digest → D2/D3/D4/D5/domain checks → D6 isolated restore staging and separate authorization/fencing gates.
- Adds 16 proposed fixture cases to P5.4.79's 60-case plan; total 76 specified, all **NOT IMPLEMENTED / NOT RUN**.
- Cryptographic suite, manifest authentication mechanism/encoding, key custody/escrow/rotation, storage provider and object publication atomicity remain unselected and require separate review.
- GitHub Actions: **NOT RUN**; no workflow run/artifact. Docs-only changes; no code/schema/runtime changed.
- No canonical DB, Android device, PC, production storage, key material, Feeder, exchange, backup/restore or writer touched. Keep Android-first, no PC, paper-only and `AI_EXECUTION_ENABLED=false`.
- Next step: await explicit owner decision on P5.4.80. Do not implement fixtures or runtime changes until separately authorized.


## P5.4.80 — Owner approval recorded (2026-11-04)

- Owner decision: **APPROVE P5.4.80 D1–D5 WITHOUT AMENDMENTS**.
- Proposal: `docs/evidence/P5.4.80-DIGEST-DOMAINS-AND-AUTHENTICATED-BACKUP-MANIFEST-PROPOSAL-2026-11-04.md`.
- Approved: separate `snapshot_image_sha256` for exact verified SQLite image bytes before encryption; separate `encrypted_object_sha256` for exact encrypted payload bytes independently checked by full destination read-back; authenticated manifest binding both digests/lengths, Backup ID, immutable payload object ID/version and D2–D5 evidence; separate immutable payload and manifest publication; fail-closed state model; restore verification order; 16 added fixture cases.
- Fixture plan now contains **76 specified cases** (60 from P5.4.79 + 16 from P5.4.80). All are **NOT IMPLEMENTED / NOT RUN**.
- Approval is architecture/contract only. Cryptographic suite, signature/MAC mechanism and canonical encoding, key custody/escrow/rotation, storage provider, publication atomicity implementation, retention values and numerical RPO/RTO remain unresolved.
- GitHub Actions: **NOT RUN**; no workflow run/artifact. No source/runtime/schema/test implementation changed in this approval-recording increment.
- No canonical DB, Android device, PC, production storage, key material, Feeder, exchange, backup/restore, latch/Kill Switch or writer touched.
- Status: P5.4.80 **OWNER-APPROVED / ARCHITECTURE ONLY**; fixture implementation/execution **NOT AUTHORIZED / NOT RUN**; production implementation **BLOCKED** on remaining design closures and separate authorization.
- Safety: Android-first; no PC; paper-only; `AI_EXECUTION_ENABLED=false`; no live orders.
- Next step: continue resolving unselected cryptographic/key custody/storage/retention/RPO-RTO contracts in bounded documentation proposals. Do not implement fixtures or runtime until separately authorized.


## P5.4.81 — Cryptographic profile and key lifecycle proposal (2026-11-04)

- Proposal: docs/evidence/P5.4.81-CRYPTOGRAPHIC-PROFILE-AND-KEY-LIFECYCLE-PROPOSAL-2026-11-04.md.
- Status: **PROPOSED / NOT APPROVED**; explicit owner decision required for P5.4.81.1–.5.
- Recommends AES-256-GCM envelope encryption; unique random 256-bit DEK per Backup ID; 96-bit nonce; full 128-bit tag; versioned AAD.
- Recommends Ed25519 signature over canonical P5.4.80 manifest bytes with separate signing key; separate external KMS/HSM-managed KEK, DEK and manifest signing roles; lifecycle, rotation, revocation and destruction safeguards; strict identity separation and fail-closed handling.
- Adds 20 proposed fixture cases to the approved 76-case plan: **96 specified if approved; NOT IMPLEMENTED / NOT RUN**.
- Provider, KMS/HSM vendor, Android/JVM library compatibility, compliance requirements, key custody jurisdiction, escrow/recovery method, operational roles and audit integration remain unresolved.
- GitHub Actions: **NOT RUN**; no workflow run/artifact. Documentation only; no code/schema/runtime/key/storage changed.
- No canonical DB, Android device, PC, production storage/KMS/HSM, key material, Feeder, exchange, backup/restore or writer touched.
- Safety: Android-first, no PC, paper-only, AI_EXECUTION_ENABLED=false.
- Next step: obtain explicit owner decision on P5.4.81.1–.5. If approved, continue a separate proposal for KMS/HSM custody/provider-neutral interfaces and restore-key recovery controls; do not provision keys or implement fixtures without separate authorization.


## P5.4.81 — Owner approval recorded (2026-11-04)

- Owner decision: **APPROVE P5.4.81.1–.5 WITHOUT AMENDMENTS**.
- Proposal: docs/evidence/P5.4.81-CRYPTOGRAPHIC-PROFILE-AND-KEY-LIFECYCLE-PROPOSAL-2026-11-04.md.
- Approved profile: AES-256-GCM envelope encryption; unique random 256-bit DEK per Backup ID; 96-bit nonce; full 128-bit tag; versioned AAD; Ed25519 signatures over canonical P5.4.80 manifest bytes with signing key separate from payload KEK; explicit trusted public-key set; separate KEK/DEK/signing-key roles; lifecycle/rotation/revocation/destruction safeguards; identity separation and fail-closed handling.
- Fixture plan: **96 cases specified** (76 previously approved + 20 P5.4.81 additions), **NOT IMPLEMENTED / NOT RUN**.
- Status: P5.4.81 **OWNER-APPROVED / CRYPTOGRAPHIC ARCHITECTURE ONLY**.
- Still unselected: KMS/HSM vendor, storage provider, custody jurisdiction, escrow/recovery method, concrete canonical-manifest serialization implementation, operational roles and audit integration.
- Approval does not authorize key generation/provisioning, production KMS/HSM or storage access, fixture execution, canonical DB access, backup/restore or runtime changes.
- GitHub Actions: **NOT RUN**; no workflow run/artifact. Documentation-only decision record; no code/schema/runtime/key/storage changed.
- No canonical DB, Android device, PC, production KMS/HSM, production storage, key material, Feeder, exchange, backup/restore or writer touched.
- Safety: Android-first, no PC, paper-only, AI_EXECUTION_ENABLED=false.
- Next step: propose provider-neutral KMS/HSM custody and recovery-key control requirements, without selecting a vendor or provisioning keys. Fixture and runtime implementation remain blocked pending separate authorization and unresolved design closure.


## P5.4.82 — Provider-neutral key custody and recovery proposal (2026-11-04)

- Proposal: `docs/evidence/P5.4.82-PROVIDER-NEUTRAL-KEY-CUSTODY-AND-RECOVERY-ARCHITECTURE-PROPOSAL-2026-11-04.md`.
- Status: **PROPOSED / NOT APPROVED**; no owner decision inferred from “tiếp tục”.
- Scope: provider-neutral KMS/HSM adapter boundaries, key inventory, workload identity separation, DEK/KEK/signing-key lifecycle, break-glass recovery case, proposed two-person approval, append-only audit contract, fail-closed matrix and CI fake-provider isolation.
- No KMS/HSM/storage vendor, recovery model, custody jurisdiction, quorum/roles, audit sink or federation mechanism selected.
- P5.4.81 remains owner-approved; P5.4.82 does not amend it.
- Fixture plan: **96 approved cases specified / NOT IMPLEMENTED / NOT RUN**. P5.4.82 test ideas are candidates only, not counted or authorized.
- GitHub Actions: **NOT RUN**; no workflow run/artifact. Documentation-only change.
- No code/schema/runtime, key material, provider account, storage, canonical DB, Android device or PC accessed/changed.
- No backup/restore, Feeder, exchange, Kill Switch/Recovery Latch mutation or writer activation.
- Safety: Android-first, no PC, paper-only, AI_EXECUTION_ENABLED=false.
- Next step: owner review/decision on P5.4.82 and its ten open design decisions. Implementation, fixtures and provider integration remain unauthorized.


## P5.4.82A — Key custody open-decision matrix (2026-11-04)

- Added: `docs/evidence/P5.4.82A-KEY-CUSTODY-OPEN-DECISION-MATRIX-2026-11-04.md`.
- Status: **DECISION SUPPORT ONLY / NOT AN APPROVAL**. “tiếp tục” was not treated as approval or selection of any policy.
- Frames ten owner decisions: recovery model; approval quorum/roles; jurisdiction/account ownership; audit sink/tamper evidence; KEK rotation; signing-key revocation; workload identity; RPO/RTO; Android/JVM crypto qualification; wrapped-DEK metadata/canonical encoding.
- Provides options, trade-offs, non-binding discussion defaults and evidence required before provider comparison. No option/provider/jurisdiction/role/quorum selected.
- P5.4.82 remains **PROPOSED / NOT APPROVED**; P5.4.81 remains owner-approved and unchanged.
- Fixture plan: **96 specified / NOT IMPLEMENTED / NOT RUN**. P5.4.82A adds no approved or counted tests.
- GitHub Actions: **NOT RUN**; no workflow run/artifact. Documentation-only changes.
- No code/schema/runtime, key material, provider account, storage, canonical DB, Android device or PC accessed/changed.
- No backup/restore, Feeder, exchange, Kill Switch/Recovery Latch mutation or writer activation.
- Safety: Android-first, no PC, paper-only, AI_EXECUTION_ENABLED=false.
- Next step: owner decision on P5.4.82 and explicit selections for D82-A through D82-J. No implementation, fixture execution, provider selection or provisioning is authorized.


## P5.4.82 — D82-A owner approval recorded (2026-11-04)

- Owner decision: **APPROVE D82-A** — select **Independent escrow authority** for recovery, combined with the primary KMS/HSM for routine operations.
- Accepted loss-of-recovery risk: **LOW**; prioritize recoverability while accepting additional operational controls/cost.
- Approval control constraint: at least **two independent approvers**; requester and executor are excluded from approving the same recovery request/execution.
- D82-B remains open for authorized roster, exact two-of-N quorum, succession/unavailability handling and emergency exception. D82-C–D82-J remain open.
- D6 remains unchanged: key recovery cannot allocate Restore Epoch, prove prior writers stopped, re-fence leases, publish restored DB, release Recovery Latch, clear Kill Switch or admit writers. Those remain separate authenticated gates.
- No vendor/custodian/jurisdiction/account selected. No implementation, fixtures, key generation, provider selection/provisioning, KMS/HSM/storage access, canonical DB, backup/restore, device/PC, Feeder/exchange or writer activation authorized.
- P5.4.82 status: **PARTIALLY APPROVED — D82-A ACCEPTED; D82-B–D82-J OPEN**. P5.4.82A remains a decision-support matrix with D82-A recorded as approved.
- Existing 96 fixture cases: **SPECIFIED / NOT IMPLEMENTED / NOT RUN**. GitHub Actions NOT RUN; no workflow/artifact for this docs-only decision record.
- Branch: `feature/p5-4-1-post-merge-validation-20261103`. Pre-update HEAD: `8f314ae10a67794daca356d65b6e5492a6147758`. Documentation commits before handoff update ended at: `15769c75bd08100eb0e20ca32792430addbf117b`.
- Next step: continue D82-B quorum/role design only; no implementation without separate authorization.
- Keep `AI_EXECUTION_ENABLED=false`; paper-only.


## P5.4.82B — D82-B quorum decision support prepared (2026-11-04)

- Added `docs/evidence/P5.4.82B-APPROVAL-QUORUM-AND-ROLE-SEPARATION-OPTIONS-2026-11-04.md`.
- Status: **RECOMMENDATION ONLY / NOT APPROVED**. “tiếp tục” was treated as authorization to prepare bounded decision support, not as owner approval.
- Compares A: fixed 2-of-2; B: role-based 2-of-3; C: 3-of-5.
- Recommended candidate: **2-of-3** across three pre-enrolled functional trust domains: system-owner delegate, independent escrow custodian delegate, and independent security/recovery delegate. Two distinct people from distinct trust domains must approve. Requester and executor are excluded from the quorum.
- Recommends pre-designated alternates governed before an incident, no ad hoc enrollment during recovery, and no single-person emergency bypass. If two eligible approvers cannot be assembled, remain `BLOCKED_QUORUM_UNAVAILABLE`.
- Owner decisions still required: select A/B/C; accept role/trust-domain model; alternate governance; emergency no-bypass policy; additional independence requirements.
- Updated P5.4.82A matrix and P5.4.82 proposal to link this decision support. D82-B remains OPEN until explicit owner approval.
- No code, tests, fixture execution, identity enrollment, key generation, provider/KMS/HSM/escrow provisioning, DB/device/PC access, backup/restore, Feeder/exchange, D6 gate mutation or writer activation.
- Existing 96 fixtures: **SPECIFIED / NOT IMPLEMENTED / NOT RUN**. GitHub Actions NOT RUN; no workflow/artifact.
- Branch: `feature/p5-4-1-post-merge-validation-20261103`. No PR or new branch created. Latest documentation commit at this handoff update follows prior D82-B document commit `c6dd9e8ea4d02c527aaa23c764784b6833bacf36`.
- Next step: obtain explicit owner decision on D82-B recommendation; do not implement or provision.
- Keep `AI_EXECUTION_ENABLED=false`; paper-only.


## P5.4.82B — D82-B owner approval recorded (2026-11-04)

- Owner decision: **APPROVE D82-B** — role-based **2-of-3** quorum across three independent trust-domain roles: system-owner delegate, independent escrow custodian delegate, independent security/recovery delegate.
- Two distinct people from distinct trust domains must approve the exact recovery case. Requester and executor are excluded from the counted quorum.
- Pre-designated alternates are permitted only if designated/governed before an incident. No ad hoc enrollment or role transfer during an active case.
- No emergency bypass below quorum. If two eligible independent approvers cannot be assembled, case remains `BLOCKED_QUORUM_UNAVAILABLE`. Chat/verbal approval, GitHub review and executor assertion do not substitute for authenticated case-bound approval.
- Decision support: `docs/evidence/P5.4.82B-APPROVAL-QUORUM-AND-ROLE-SEPARATION-OPTIONS-2026-11-04.md`; status **OWNER-APPROVED — ARCHITECTURE/POLICY ONLY**.
- D82-B operational details remain open before implementation: actual roster/identity proofing; alternate mapping/activation authority; trust-domain independence evidence; credential lifecycle/revocation; case-bound approval/audit protocol; conflict-of-interest handling; quorum availability monitoring. D82-C–D82-J remain open.
- Updated P5.4.82A, P5.4.82 and ADR-001. Historical status text retained only as audit chronology; latest decision addendum is authoritative.
- No implementation, identity enrollment, fixture creation/execution, key generation, provider/KMS/HSM/escrow selection or provisioning, production access, DB/device/PC, backup/restore, Feeder/exchange, D6 gate mutation or writer activation authorized.
- Existing 96 fixtures: **SPECIFIED / NOT IMPLEMENTED / NOT RUN**. GitHub Actions NOT RUN; no workflow/artifact.
- Branch: `feature/p5-4-1-post-merge-validation-20261103`. No PR or new branch. Keep `AI_EXECUTION_ENABLED=false`; paper-only.
- Next step: continue bounded D82-B operational design details and D82-C custody jurisdiction/account ownership; obtain explicit owner decisions for D82-C–D82-J. No implementation without separate authorization.


## P5.4.82C — Custody jurisdiction and account ownership proposal prepared (2026-11-04)

- Added `docs/evidence/P5.4.82C-CUSTODY-JURISDICTION-AND-ACCOUNT-OWNERSHIP-PROPOSAL-2026-11-04.md`.
- Status: **DECISION SUPPORT / RECOMMENDATION ONLY — NOT APPROVED**. D82-C remains OPEN.
- Compares A: one legal owner/provider organization with separated accounts; B: one legal owner with primary KMS/HSM and escrow in separate provider organizations; C: separate legal entities and provider organizations.
- Recommendation: defer A/B/C selection until legal owner, contracting authority, applicable jurisdictions, residency/export/retention constraints and account-admin boundaries are evidenced. Do not infer user's country, corporate status or eligible contracting entity.
- Minimum design boundary: escrow must not share primary KMS/HSM privileged account/admin group; separate privileged identities and authentication roots; document ownership/recovery rights; inventory residency separately for payload, manifest, audit, replicas and processing; establish provider exit/recovery.
- Owner decisions required: ownership model/defer; legal data owner; primary KMS/HSM account owner; escrow custodian/account owner; permitted jurisdictions/regions by data class; independence standard across legal entities/provider organizations/identity providers; qualified legal/compliance review gate.
- Fail-closed: unknown ownership/jurisdiction/data location => `BLOCKED_D82C_UNRESOLVED`; unproven primary/escrow admin separation => `BLOCKED_TRUST_BOUNDARY`.
- Updated P5.4.82A matrix and P5.4.82 proposal. No source code or runtime changes.
- No legal incorporation, contracting, provider/account selection or provisioning, identity enrollment, key generation, storage/data upload, fixture execution, production/DB/device/PC access, backup/restore, Feeder/exchange, D6 gate mutation or writer activation authorized.
- Existing 96 fixtures: **SPECIFIED / NOT IMPLEMENTED / NOT RUN**. GitHub Actions NOT RUN; no workflow/artifact.
- Branch: `feature/p5-4-1-post-merge-validation-20261103`. No PR or new branch. Keep `AI_EXECUTION_ENABLED=false`; paper-only.
- Next step: obtain explicit owner decision on D82-C; if ownership/jurisdiction facts are unknown, keep unresolved and defer provider selection. D82-B operational details also remain design-only.


## D82-C — Owner direction to defer model selection (2026-11-04)

- Owner direction: **keep model choice A/B/C on hold until legal ownership and applicable legal conditions are established**.
- Status: `DEFERRED — LEGAL/OWNERSHIP FACTS REQUIRED`; this is a deferral only, not approval of A, B or C.
- Legal data owner, contracting authority, primary KMS/HSM account owner, escrow custodian/account owner, permitted jurisdictions/regions, independence standard and qualified legal/compliance review gate remain unresolved.
- Do not infer user's country, corporate status, legal entity, jurisdiction or eligible contracting authority.
- No provider/account selection, legal incorporation, contracting, identity enrollment, key generation, KMS/HSM/escrow provisioning, storage setup or data upload authorized.
- D82-B 2-of-3 quorum and all D6 recovery gates remain unchanged. Existing 96 fixtures remain SPECIFIED / NOT IMPLEMENTED / NOT RUN. GitHub Actions NOT RUN; no artifact.
- Next step: prepare a neutral evidence checklist for ownership, contracting authority and legal conditions; reopen A/B/C selection only after facts are supplied and reviewed. Keep `AI_EXECUTION_ENABLED=false`; paper-only.


## P5.4.83 — Android T0-B Read-Only Preflight Checklist (2026-11-04)

- Added `docs/evidence/P5.4.83-ANDROID-T0-B-READ-ONLY-PREFLIGHT-CHECKLIST-2026-11-04.md`.
- Reconciled `docs/T0_FEEDER_TEST_CONTRACT.md` and `docs/evidence/T0-A-FIXTURE-CI-CLOSEOUT-REVIEW-2026-11-04.md` from stale Windows-PC canonical wording to the owner-selected Android-first topology.
- Annotated `docs/evidence/T0-RECHECK-2026-11-04.md` as historical; its PC follow-up recommendation is superseded by P5.4.64/P5.4.65.
- Android architecture retained: regular variant is intended sole canonical host; `.paper` is authenticated IPC client; one shared physical SQLite file for Market Data + Paper Ledger; PC optional compute/read-only consumer.
- Current gate state: T0-A **PASS** on prior exact-SHA GitHub Actions evidence; T0-B **BLOCKED / NOT RUN** because Android CanonicalRuntime/path authority and DB identity are not implemented/verified and device access has not been authorized; T0-C **NOT RUN / NOT AUTHORIZED**; T0-D **NOT RUN / NOT VERIFIED**; T0-E **BLOCKED**.
- Checklist distinguishes source prerequisites from later device metadata preflight. It prohibits guessed paths, SQLite open/PRAGMA/integrity checks without separate authorization, DB creation, Feeder startup, exchange connectivity and market sync.
- Commits on existing branch: checklist `2311635bf554bad06e73761b36e561e8ff1dcc67`; T0 contract `732993bdee4b4a8788faeb561b732deabb23fbb6`; closeout correction `f454061e87befd942ffb181e4f43185d84eebbe0`; historical re-check annotation `df783cbcbe087e628c03d36597504abef6849b58`.
- This increment is documentation-only. No tests/workflows/builds/artifacts, Android device/filesystem, PC, canonical DB, Feeder, exchange, sync, backup/restore or writer activation. Branch HEAD before handoff update: `df783cbcbe087e628c03d36597504abef6849b58`.
- Safety: `AI_EXECUTION_ENABLED=false`; paper-only; no live orders. Android Natural Doze remains INTERRUPTED / DEFERRED.
- Next step: perform source-only current-HEAD gap inventory for the regular Android canonical host; no code changes until separately authorized.


## P5.4.84 — Android T0 Current-HEAD Source Gap Inventory (2026-11-04)

- Report: `docs/evidence/P5.4.84-ANDROID-T0-CURRENT-HEAD-SOURCE-GAP-INVENTORY-2026-11-04.md`.
- Report commit: `9a5501ea69730e431b0d195f522146373eb3e4ea`.
- Reviewed branch HEAD before report: `771c2778a84e5389603c7fa4121d3cb301018139`; report is source/tree/Gradle/manifest review only.
- Current source confirms: regular application ID `com.kenznguyen.btclivealerts`; parallel source-derived ID `com.kenznguyen.btclivealerts.paper`; main manifest only declares the existing non-exported StrategyMonitorService; its `onBind()` returns null; regular MainActivity starts that monitor; monitor uses SharedPreferences; .paper dashboard still uses remote HTTPS FiveLayerApi.
- No Android CanonicalRuntime, canonical SQLite path authority, migration registry, T0 Gateway/Feeder composition, same-file LeaseStore/fencing, Paper Ledger/Risk repository, signature-bound IPC service, AIDL or Android instrumentation-test source tree was found in the bounded current tree/source review. Gradle does not declare Room, AndroidX DataStore or a SQLite wrapper.
- Verdict: bounded source review **PASS**; ADR-002 implementation **NOT IMPLEMENTED**; T0-B **BLOCKED / NOT RUN**; T0-C **NOT RUN / NOT AUTHORIZED**; T0-D **NOT RUN / NOT VERIFIED**; T0-E **BLOCKED**.
- No Kotlin/Gradle/manifest/dependency/schema changes, tests, workflows, APK build/install, device/filesystem, DB, Feeder, exchange, market sync, backup/restore or writer activation. Keep `AI_EXECUTION_ENABLED=false`; paper-only.
- Next step: prepare a bounded implementation slice plan and acceptance-test contract for regular-host CanonicalRuntime/path authority. Code implementation remains separately gated and is not inferred from “tiếp tục”.


## P5.4.85 — Android T0 CanonicalRuntime and Path Authority Slice Plan (2026-11-04)

- Plan: `docs/evidence/P5.4.85-ANDROID-T0-CANONICAL-RUNTIME-AND-PATH-AUTHORITY-SLICE-PLAN-2026-11-04.md`.
- Status: **DESIGN / ACCEPTANCE PLAN ONLY — NOT APPROVED FOR IMPLEMENTATION**.
- Product context recorded: personal, non-commercial, single-owner use; no SaaS, multi-tenant, subscription or billing scope. This does not waive security, integrity, encryption, recovery, audit, provider terms or legal requirements.
- Android remains the primary operating/canonical-storage platform; PC optional compute/read-only consumer; GitHub Actions only CI; Codemagic retired.
- Bounded first candidate: regular-host application-scoped CanonicalRuntime and host-owned metadata-only canonical path authority. Runtime construction/path resolution must not open/create SQLite, start Feeder, acquire lease, connect exchange or sync data.
- Client exclusion: `.paper` has no CanonicalRuntime, DB resolver, shadow DB, lease/fencing or fallback writer.
- Acceptance contract CR-01–CR-08 is fixture/static CI only, using fakes/temp/in-memory state. No Android device or canonical DB access.
- Authorization: documentation/planning only. Code implementation, dependency changes, device/DB/runtime/Feeder/IPC/exchange, APK build/install, backup/restore and key/storage provisioning remain NOT AUTHORIZED.
- T0-A remains PASS on prior exact-SHA evidence; T0-B BLOCKED / NOT RUN; T0-C NOT RUN / NOT AUTHORIZED; T0-D NOT RUN / NOT VERIFIED; T0-E BLOCKED.
- No tests/workflows/builds/artifacts were run or created in this increment. No Android device, PC runtime, canonical DB, Feeder, exchange, backup/restore or writer touched. `AI_EXECUTION_ENABLED=false`; paper-only.
- Next step: request explicit owner approval for Slice 1 + Slice 2 source implementation only, then fixture/static CI on GitHub Actions. Device T0-B remains separately gated.


## P5.4.86 — Android T0 Slice 1 + Slice 2 implementation and CI closeout (2026-11-04)

- Owner explicitly approved source implementation of Slice 1 + Slice 2 only.
- Added `CanonicalRuntime.kt`: stable DB identity/location metadata, metadata-only `CanonicalPathAuthority`, app-private candidate path `files/canonical/t0.sqlite`, side-effect-free `CanonicalRuntime`, synchronized lazy `CanonicalRuntimeRegistry`; non-host variant gets no runtime.
- Added `CanonicalApplication.kt`; updated main manifest to use it. Runtime is lazy and does not open/create SQLite or start services/workers.
- Added four JVM fixture tests for metadata-only resolution/no file creation, one runtime per host registry, non-host exclusion and no resolution during construction.
- Added static audit and Android T0 Foundation GitHub Actions workflow. Workflow executes `:app:testDebugUnitTest` and static audit only; no APK build/sign/publish.
- Implementation commit: `10bf761cb323b3e19d8c48d7b447e373c5cf9e83`; CI allowlist correction commit: `a9c43ef2e0273716220d479ea6fa7df64a0809fa`.
- Exact validated SHA: `a9c43ef2e0273716220d479ea6fa7df64a0809fa`.
- Android Foundation run #41757183862: **PASS**; Gradle unit test task BUILD SUCCESSFUL; static audit PASS. Artifact ID `13288214753`; run https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41757183862 ; artifact https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41757183862/artifacts/13288214753 .
- T0 automated validation run #41757183811: **PASS** on the same SHA: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41757183811 .
- P5.4.1 aggregate run #41757183822: **PASS** on the same SHA; preflight, T0, G1, G2 and common-SHA verification passed. Combined evidence artifact ID `13288682358`; run https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41757183822 ; artifact https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41757183822/artifacts/13288682358 .
- Closeout report: `docs/evidence/P5.4.86-ANDROID-T0-CANONICAL-RUNTIME-PATH-AUTHORITY-IMPLEMENTATION-CLOSEOUT-2026-11-04.md`.
- Historical CI failures were isolated and corrected: first SDK setup used removed `tools` package; next aggregate gate exposed missing explicit workflow allowlist entry. Later exact-SHA runs above all passed.
- Limits: no SQLite open/create/PRAGMA/schema/migration; no Feeder, lease, exchange, sync, IPC/Binder, Paper Ledger/Risk activation, Android device/install/instrumentation, PC/VPS, APK build/sign/publish or writer activation. `AI_EXECUTION_ENABLED=false`; paper-only.
- Status: Slice 1 **PASS — source/JVM CI**; Slice 2 **PASS — source/JVM CI/static audit**. Device runtime conformance **NOT VERIFIED**; T0-B **NOT RUN / NOT AUTHORIZED**; T0-C **NOT RUN / NOT AUTHORIZED**; T0-D **NOT RUN / NOT VERIFIED**; T0-E **BLOCKED**.
- Next step: source-only review of Slice 1 + 2 and prepare Slice 3 design/tests for canonical DB identity and schema-migration verifier boundary. No SQLite access or DB implementation without separate approval.


### P5.4.86 source-review addendum

- Post-implementation five-axis source review: **PASS FOR AUTHORIZED FOUNDATION SCOPE WITH LIMITS**; no critical issue found in side-effect-free runtime/path-authority boundary.
- Identity caveat: t0-canonical-sqlite-v1 is a shared logical role/version token, not a unique physical DB or installation identity. It must not be used as snapshot/restore/clone identity until Slice 3 defines identity semantics.
- Variant caveat: Android CI ran :app:testDebugUnitTest; `.paper` registry exclusion fixture and Gradle BuildConfig static check passed, but the actual parallel Android build variant was not compiled/executed. `.paper` Android variant conformance remains NOT VERIFIED.
- Next step before Slice 3 implementation: define logical-vs-instance identity semantics and add CI coverage for the parallel variant build/test task. No DB access, Android device, APK build/install or runtime operation is authorized by this review.


## P5.4.87 — Android T0 database identity and read-only schema verifier plan (2026-11-04)

- Plan: docs/evidence/P5.4.87-ANDROID-T0-DATABASE-IDENTITY-AND-READONLY-SCHEMA-VERIFIER-SLICE-PLAN-2026-11-04.md.
- Status: DESIGN / ACCEPTANCE CONTRACT ONLY — NOT APPROVED FOR IMPLEMENTATION.
- Prepared against source HEAD bae182cef3b906c3083e440245c20ab07aa53dee; P5.4.86 exact validated SHA remains a9c43ef2e0273716220d479ea6fa7df64a0809fa.
- Separates CanonicalDatabaseRoleId (stable logical role) from CanonicalDatabaseInstanceId (physical DB lineage); BackupId, RestoreEpoch and LeaseGeneration remain distinct. No instance ID format, allocation, storage or clone/adoption lifecycle selected or provisioned.
- Translates already-approved D4.1–D4.7 into a proposed Android read-only verifier boundary; no writable connection, migration runner, schema initialization, PRAGMA mutation, baseline stamping or repair permitted.
- D3 same-snapshot manifest and D5 logical schema digest remain separate evidence domains; verifier PASS does not release D6 gates or admit writers.
- Specifies 26 pure domain/fixture/static CI acceptance cases, including actual regular and .paper parallel unit-test variant execution. All 26 are NOT IMPLEMENTED / NOT RUN.
- Explicitly no Kotlin changes, DB open/create/inspection, migration, dependency addition, Android device, APK, Feeder, IPC, exchange, backup/restore, key provisioning or writer activation.
- Status: Slice 1+2 PASS on prior evidence; detailed physical DB identity lifecycle PROPOSED / OWNER DECISION REQUIRED; D4 architecture APPROVED but implementation NOT APPROVED; .paper actual variant CI NOT VERIFIED; T0-B BLOCKED / NOT RUN / NOT AUTHORIZED; T0-C NOT RUN / NOT AUTHORIZED; T0-D NOT RUN / NOT VERIFIED; T0-E BLOCKED.
- Next step: owner review/decision on identity model and verifier contract. Any implementation requires separate explicit approval. Keep AI_EXECUTION_ENABLED=false; paper-only.


## P5.4.88 — Android T0 database identity and read-only schema contract implementation closeout (2026-11-04)

- Closeout: `docs/evidence/P5.4.88-ANDROID-T0-DATABASE-IDENTITY-AND-READONLY-SCHEMA-CONTRACT-IMPLEMENTATION-CLOSEOUT-2026-11-04.md`.
- Owner approved implementation of pure Kotlin domain contracts + fixture tests and GitHub Actions execution for regular and `.paper` variants. No DB/device/runtime permission was granted.
- Commits: test-first RED `4ab28faf86f78b6e5f77064a2405743c44fe0b53`; domain implementation/workflow `d2bb81b316379ebce2fdb31e2841bcdbace49d42`; generated variant identity assertion `b5dcd0d0700d19b9ea3092593566385c48d6d635`.
- Exact Android Foundation validated SHA: `b5dcd0d0700d19b9ea3092593566385c48d6d635`.
- Android Foundation run #41758947843: PASS; regular `:app:testDebugUnitTest` and parallel `:app:testParallelUnitTest` BUILD SUCCESSFUL; static audit PASS. Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41758947843 .
- Artifact ID `13289358031`, name `android-t0-foundation-b5dcd0d0700d19b9ea3092593566385c48d6d635`, size 92,064 bytes; downloaded ZIP SHA-256 `29ef7cf76fdf188bf18fc8813d63680f7ce112b1d6f68606dbf3c0994b2824d0`. Artifact: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41758947843/artifacts/13289358031 .
- JUnit artifact verified: 115 tests / 18 suites for regular; 115 tests / 18 suites for `.paper`; 0 failures, 0 errors, 0 skipped in each. `CanonicalDatabaseContractsTest` has 15 passing tests per variant, including generated BuildConfig/application ID suffix assertion.
- T0 automated validation run #41758416364 and P5.4.1 aggregate run #41758416565 both PASS on preceding exact SHA `d2bb81b316379ebce2fdb31e2841bcdbace49d42`, not the later test-only follow-up SHA. Aggregate preflight/T0/G1/G2/common-SHA checks passed; artifact IDs `13289721104` (aggregate) and `13290000113` (T0).
- Implemented: distinct logical role and physical instance ID types; restore lineage preservation model; clone/fork with distinct child ID; distinct BackupId/RestoreEpoch/LeaseGeneration types; immutable migration descriptor checksum; pure read-only evidence verifier with fail-closed role/instance/catalog/checksum/sequence/incomplete/schema-drift outcomes.
- The verifier is a pure in-memory domain verifier, not a SQLite adapter. No instance ID generator, DB persistence, schema_migrations DDL, migration runner, schema introspection, D3 manifest integration or legacy adoption is implemented.
- Status: authorized domain/fixture scope PASS; SQLite schema/migration and read-only adapter NOT IMPLEMENTED; identity persistence/lifecycle NOT IMPLEMENTED; Android device NOT VERIFIED; T0-B NOT RUN / NOT AUTHORIZED; T0-C NOT RUN / NOT AUTHORIZED; T0-D NOT RUN / NOT VERIFIED; T0-E BLOCKED.
- No SQLite/device/Feeder/lease/exchange/IPC/backup/restore/key provisioning/APK/writer action. `AI_EXECUTION_ENABLED=false`; paper-only.
- Next step: design-only proposal for persisted physical DB identity lifecycle, read-only SQLite adapter, D4 DDL + D5 schema digest + D3 manifest integration. Any runtime/database operation remains separately gated.


## P5.4.89 — Persisted identity lifecycle and read-only SQLite adapter design (2026-11-04)

- Proposal: `docs/evidence/P5.4.89-ANDROID-T0-PERSISTED-IDENTITY-LIFECYCLE-AND-READONLY-SQLITE-ADAPTER-DESIGN-2026-11-04.md`.
- Status: **OWNER-APPROVED DESIGN CONTRACT — ID-1–ID-7 APPROVED**; pure Kotlin domain contracts/parser/state classifier and fixture tests authorized within the limits below.
- Owner decision (2026-11-04): APPROVE P5.4.89 ID-1–ID-7; select B — app-private `noBackupFilesDir` Identity Pin.
- Approved decisions: UUIDv4 random physical DB identity; immutable identity row in canonical DB plus separate host pin; B is a local consistency anchor only; atomic DB bootstrap identity + D4 registry in explicit maintenance transaction; legacy adoption requires inventory, verified D3 backup and owner-approved baseline before writes; restore preserves ID and requires D6 recovery on fresh device; clone/fork creates new child ID + parent lineage; read-only adapter is fixed-query and one-snapshot only.
- Pin lifecycle design: strict versioned canonical record with PENDING/ACTIVE states; pending → explicit DB bootstrap transaction → read-only verification → explicit promotion to ACTIVE. Cross-resource crash/uncertain states fail closed; never auto-create/re-pin/promote during startup or read-only verification.
- Missing, malformed, unreadable, unsupported or mismatched pin/DB evidence remains BLOCKED. `noBackupFilesDir` pin is not tamper-proof, not independent of app sandbox, and does not prevent whole-sandbox cloning. No anti-clone or cryptographic-authenticity claim.
- P5.4.88 remains pure in-memory domain contracts; actual DB identity persistence, Android filesystem adapter, SQLite adapter, D4 DDL and D5 digest acquisition remain NOT IMPLEMENTED.
- Permissions used in this increment: repository read/write and documentation-only commit on existing branch. No tests/workflows run because no executable source changed.
- Not authorized: actual filesystem/SQLite open/read/write/create; Android device/install/instrumentation; backup/restore execution; D6 authority/provider/Keystore; Feeder/lease/writer/IPC/exchange/data sync; APK build/sign/publish; paper/live execution. `AI_EXECUTION_ENABLED=false`.
- Next step: implement pure pin parser/value and fail-closed lifecycle classifier with fixture tests using TDD; run the existing GitHub Actions JVM/static workflow only. Request separate authorization before real Android filesystem or SQLite adapter work.


## P5.4.89 pure identity-pin contract implementation — 2026-11-04

- Owner approval: ID-1–ID-7 approved; ID-3 selects B (noBackupFilesDir) as a local consistency pin only.
- Approved design/protocol is recorded in docs/evidence/P5.4.89-ANDROID-T0-PERSISTED-IDENTITY-LIFECYCLE-AND-READONLY-SQLITE-ADAPTER-DESIGN-2026-11-04.md.
- Test-first RED commit: fdaa31db7359ff1a94847b17b5fea87c989ed1ca; Android T0 Foundation run #41760416208 failed as expected with unresolved references to the new contract types: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41760416208 .
- Pure implementation: canonical lowercase UUIDv4 validation; pin value + PENDING/ACTIVE state; strict version-1 parser/serializer; pure fail-closed lifecycle classifier. No UUID generation, filesystem access, DB access, or automatic repair.
- Added 10 new fixture tests; existing persisted-ID fixtures updated to UUIDv4.
- Intermediate implementation SHA ae4580490dcea78240800a6d5434d42e60ebc29d failed compile due escaped newline literals. Corrected source SHA: e841bea2c9b29a7fd813c43bb34d88ead46cbb86.
- Corrected SHA Android T0 Foundation run #41760783949: **PASS** on exact source SHA e841bea2c9b29a7fd813c43bb34d88ead46cbb86. Regular :app:testDebugUnitTest and parallel :app:testParallelUnitTest both BUILD SUCCESSFUL; static audit PASS. Run URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41760783949 .
- JUnit evidence: regular 125 tests / 0 failures / 0 errors / 0 skipped; .paper 125 tests / 0 failures / 0 errors / 0 skipped. CanonicalIdentityPinTest 10/10 PASS in each variant.
- Artifact ID 13290850310, name android-t0-foundation-e841bea2c9b29a7fd813c43bb34d88ead46cbb86, size 97,029 bytes; ZIP SHA-256 ca3d96c717398791719f0cff7b2505050a4218f916ab6e20f0f3ce98f3b4cce7. Downloaded ZIP passed integrity check for all 92 entries; locally computed SHA-256 matches GitHub artifact metadata. Artifact URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41760783949/artifacts/13290850310 .
- Workflow ran JVM tests and static audit only; no APK assembly/sign/publish.
- Permissions used: source/test/documentation changes on existing branch and GitHub Actions fixture test workflow. No APK build/sign/publish.
- No actual noBackupFilesDir access, SQLite open/create/read/write, DDL/migration/adoption, Android device/install/instrumentation, backup/restore, D6 authority, Keystore, Feeder, lease, IPC, exchange/data sync or writer admission. AI_EXECUTION_ENABLED=false; paper-only.
- Status: **PASS** for pure Kotlin UUIDv4/pin codec/lifecycle classifier source + fixture tests + static audit + verified workflow artifact on exact SHA e841bea2c9b29a7fd813c43bb34d88ead46cbb86. Physical filesystem/SQLite/device behavior remains NOT IMPLEMENTED / NOT VERIFIED. Next: separately scope Android filesystem adapter and SQLite read-only adapter, and obtain separate explicit authorization before actual runtime access.


## P5.4.90 — Pure identity provisioning recovery planner (2026-11-04)

Scope: implement the approved P5.4.89 pending/active cross-resource provisioning protocol as a pure decision planner. This is not an Android filesystem adapter or SQLite adapter.

- Added `IdentityProvisioningPlanner.kt`: pure state-to-plan mapping only. It does not generate UUIDs, touch files, open SQLite, execute transactions, write/promote pins, retry uncertain transactions or admit writers.
- Preconditions are phase-specific: START/RESUME require explicit maintenance authorization, confirmed absent/approved-empty DB path, no active writer/lease, no accepted identity and no legacy data. FINALIZE requires explicit maintenance authorization, no active writer/lease, no accepted identity and no legacy data; it does not incorrectly require the now-created DB path to remain absent.
- Fail-closed outcomes include blocked evidence/preconditions, explicit same-pending-ID resume, read-only reconciliation for uncertain evidence, and explicit promotion only after matching DB evidence is read-only verified.
- Added 11 JUnit tests covering start, blocked preconditions, legacy data, explicit resume, no automatic retry, uncertain commit reconciliation, explicit finalization, no auto-promotion, mismatch, unreadable/unsupported pin, active verified identity and finalization precondition scoping.
- Test-first test-only commit: `9ff24c5376f4fc4b85fcdf1b64de2cec101dca5d`; Android T0 Foundation run #41762010142 is IN PROGRESS at this update (test-only RED expected because planner types were not yet implemented): https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41762010142 .
- Implementation + phase-specific precondition correction SHA: `9a6242924c6dfdcc9d66b67ae0c11e5be171bb77`. Exact-SHA Android T0 Foundation run #41762155551 is PENDING at this update: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41762155551 . No PASS is claimed until regular + .paper tests and static audit complete.
- Intermediate implementation SHA `5351791bb4ae5888e5376fef12d5f8e985babf91` had its queued workflow run cancelled when the follow-up phase-specific precondition correction was pushed; it is superseded by `9a6242924c6dfdcc9d66b67ae0c11e5be171bb77`.
- No filesystem/SQLite/device/APK/Feeder/lease/IPC/exchange/backup/restore/writer action. `AI_EXECUTION_ENABLED=false`; paper-only.

Next: complete exact-SHA CI verification on `9a6242924c6dfdcc9d66b67ae0c11e5be171bb77`; fix any failures. After that, the next implementation boundary is Android filesystem/SQLite adapter work, which still requires separate explicit authorization.


## P5.4.90 CI reconciliation note — 2026-11-04

- First implementation CI run #41762155551 on SHA 9a6242924c6dfdcc9d66b67ae0c11e5be171bb77 failed in the regular JVM suite: 137 tests, 2 assertion failures. One expected outcome was corrected in the test because legacy DB evidence is classified as BLOCKED_EVIDENCE. The other expected outcome was also corrected: an ACTIVE pin with matching identity but without read-only verification requires READ_ONLY_RECONCILIATION, not BLOCKED_EVIDENCE.
- The first corrected-test commit f4f87a072cb4b9765c147804b9bf12bb81713e1d corrected the legacy assertion. Exact-SHA run #41762440354 is still IN PROGRESS at this update; no result is claimed. It may still fail the remaining ACTIVE-pin expectation.
- The ACTIVE-pin test correction has not yet been committed. Next action: wait for #41762440354, update the assertion if confirmed, rerun both regular and .paper variants and static audit on the resulting exact SHA.
- P5.4.90 status remains NOT VERIFIED pending exact-SHA CI completion. No runtime/filesystem/SQLite/device/backup/restore/writer/APK operation was performed.


## P5.4.90 latest test correction — 2026-11-04

- Corrected-test run #41762440354 on SHA f4f87a072cb4b9765c147804b9bf12bb81713e1d completed FAILURE: 137 tests, 1 failure. Remaining failure was the ACTIVE pin + matching DB identity + readOnlyVerified=false case; the planner correctly returns REQUIRE_READ_ONLY_RECONCILIATION, so the test expectation was corrected accordingly.
- Latest test commit: 8e8ca2f07709287e40ece2ed89ee7589779dbfb8.
- Exact-SHA Android T0 Foundation run #41762849876 is QUEUED on SHA 8e8ca2f07709287e40ece2ed89ee7589779dbfb8: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41762849876 . No PASS is claimed yet. The previous failures were test expectation mismatches; no implementation defect has been established by those assertions.
- Next: verify exact-SHA regular and .paper test suites plus static audit. Keep P5.4.90 NOT VERIFIED until all required checks pass.


## P5.4.90 final validation — 2026-11-04

**Status: PASS — pure Kotlin identity provisioning planner and fixture validation.**

- Final implementation SHA tested: `8e8ca2f07709287e40ece2ed89ee7589779dbfb8`.
- Android T0 Foundation run #41762849876 completed SUCCESS on that exact SHA: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41762849876 .
- Regular host JVM suite: 137 tests, 0 failures, 0 errors, 0 skipped.
- Parallel `.paper` JVM suite: 137 tests, 0 failures, 0 errors, 0 skipped.
- `IdentityProvisioningPlannerTest`: 12/12 passed in both variants.
- Android T0 Foundation static audit: PASS.
- Artifact ID `13291082274`, size 102,293 bytes, SHA-256 `b299e1c00e02517afb3863e24d6c882a43e84c55c3125bb6ba8cacd9efac21f5`; downloaded archive passed ZIP integrity validation. Artifact: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41762849876/artifacts/13291082274 .
- The two earlier failures were assertion expectation mismatches and are corrected in the final tested SHA; no source planner defect remained in final suite.
- Documentation/handoff update is recorded after the tested source SHA; it does not alter source under test.

Scope remains pure decision planning only. No actual `noBackupFilesDir` file read/write, SQLite open/read/write, DB bootstrap/migration/adoption, Android device test, backup/restore, Keystore, Feeder, lease, IPC, exchange sync, writer admission, APK build/sign/publish or live trading was performed. `AI_EXECUTION_ENABLED=false`; paper-only.

Next bounded increment: add pure immutable read-snapshot evidence contracts and fixture tests, then design the Android read-only SQLite adapter. Do not open SQLite or access Android filesystem/device until a separate runtime authorization is granted.


## P5.4.91 — Immutable read-snapshot evidence contract (2026-11-04)

**Status: PASS — pure Kotlin contract and fixture validation.**

- Added `CanonicalDatabaseReadSnapshot.kt` and `CanonicalDatabaseReadSnapshotTest.kt`.
- Snapshot DTO captures database state, transaction-consistency claim, observed role/instance identity, migration catalog and applied chain, expected/observed schema digest, SQLite runtime version and source ID, plus a nonblank read-transaction token.
- Catalog and applied-migration lists are defensively copied and wrapped as unmodifiable lists.
- Verifier rejects missing DB, legacy/unversioned DB, missing identity, uncertain reads, unproven/multiple-transaction evidence and incomplete evidence. For complete evidence it delegates role/instance, migration-chain, checksum and schema-digest checks to the existing pure `ReadOnlySchemaVerifier`.
- The consistency enum is an adapter-supplied claim, not cryptographic proof. This contract does not itself open SQLite or prove that a future adapter really sourced all fields from one SQLite read transaction.
- TDD RED test-only commit: `86fdf6eb0cebf70ad849263df534e10534409dc8`; Android T0 Foundation run #41763344817 failed as expected with unresolved references to the new snapshot contract types: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41763344817 .
- Implementation SHA: `10b1029fa0427372898f02d4723565109d0e0304`.
- Exact-SHA Android T0 Foundation run #41763401473: **PASS**: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41763401473 . Regular suite 147 tests / 0 failures / 0 errors / 0 skipped; `.paper` suite 147 / 0 / 0 / 0. New snapshot tests 10/10 pass in both variants. Static audit PASS.
- Artifact ID `13291688186`, size 107,251 bytes, SHA-256 `031fd69e596d672140e8ebb873376ec82226388edc5638ce9a3e6cd5f689d451`; downloaded ZIP integrity check passed. Artifact: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41763401473/artifacts/13291688186 .
- No Android filesystem or SQLite adapter implementation/execution, no DB open/create/read/write, no device test, no DDL/migration/adoption, no backup/restore, no APK, no Feeder/lease/IPC/exchange/writer action. `AI_EXECUTION_ENABLED=false`; paper-only.

Next: define and test the fixed read-only SQLite query contract against the approved D4 schema details, then implement an isolated Android adapter that can only open an existing DB with read-only flags. Do not invoke it against a real DB/device until separate runtime authorization; do not wire it into startup or writer paths.



## P5.4.92 pending owner decision — 2026-11-04

- Added a documentation-only proposal for exact canonical_database_identity and schema_migrations DDL, append-only immutability triggers, and a fixed read-only query family for SQLite runtime identity, canonical identity row, migration chain, sqlite_schema, and structured PRAGMA introspection.
- The proposal requires one read transaction for all evidence; incomplete/uncertain reads fail closed. The transaction API/mode compatible with Android OPEN_READONLY, D5 schema-introspection coverage, and exact migration bytes/IDs remain unresolved.
- No SQL was executed; no DB or filesystem was opened or created. Owner approval is requested for the proposed DDL and query families only. This is not runtime authorization.


## P5.4.92 — Owner approval and next boundary (2026-11-04)

- Owner decision: **APPROVE P5.4.92**, no amendments. Approval covers only the proposed `canonical_database_identity` DDL, `schema_migrations` append-only DDL/triggers, and fixed read-only query families documented in `docs/evidence/P5.4.89-ANDROID-T0-PERSISTED-IDENTITY-LIFECYCLE-AND-READONLY-SQLITE-ADAPTER-DESIGN-2026-11-04.md`.
- The query contract requires one SQLite read transaction for all evidence; any query, cursor, transaction, or connection uncertainty fails closed as `READ_UNCERTAIN`; partial evidence is never COMPLETE.
- Design-only approval. No Android filesystem access, DB open/create/read/write, DDL execution, migration/adoption, device runtime, Feeder, backup/restore, writer admission, APK work, exchange connectivity or trading is authorized. `AI_EXECUTION_ENABLED=false`; paper-only.
- Before an Android adapter: resolve the read-only transaction API on minSdk 26, freeze D5 schema-introspection coverage, define exact immutable bootstrap migration bytes/ID/sequence/owner, and prove missing-path read-only open cannot create a DB.
- Next bounded increment: pure source-level DDL/query contract and fixture tests only; no SQLite connection or SQL execution.
- At approval recording time, branch `feature/p5-4-1-post-merge-validation-20261103` was verified at source HEAD `2d55ae36bdc603beffdb1c8c2e84e24252c836a1`. Approval documentation is being committed directly to this branch; no PR or parallel branch.


## P5.4.93 — Pure fixed SQLite DDL/query contract (2026-11-04)

- Scope: source-level Kotlin contract and fixture tests only. No SQLite connection, SQL execution, filesystem access, Android device access, or DB creation/open/read/write.
- Added `CanonicalSqliteReadContract.kt`: six bootstrap DDL statements (two tables + four immutability triggers), four fixed read-query families (runtime identity, full identity rows, full migration chain, deterministic `sqlite_schema` catalog), and catalog-derived quoted PRAGMA templates for table_info/index_list/foreign_key_list/index_info.
- Added `CanonicalSqliteReadContractTest.kt` covering DDL shape, immutability triggers, unbounded deterministic queries, stable PRAGMA ordering, identifier escaping, and exclusion of internal/unsupported schema objects.
- TDD RED: test-only SHA `7eb1b07b738db8e6518035610ef5523b0c962e33`; Android T0 Foundation run #41765133608 failed in regular JVM compile due expected unresolved references to the not-yet-added contract types. This confirms RED; the .paper/static-audit steps were skipped by fail-fast.
- Implementation commit: `3a49568d6beaafea863faa6dc4792e074b6bb70b`.
- Test assertion correction commit: `cf16ad1c39fa9e015c11fd39cfaafe61c8f41d15` (corrected a false-positive check that treated a semicolon inside a safely quoted identifier as an unquoted SQL statement separator).
- Current exact source/test SHA: `cf16ad1c39fa9e015c11fd39cfaafe61c8f41d15`. Android T0 Foundation run #41765316296 is IN_PROGRESS at this handoff update: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41765316296 . Do not claim PASS until regular, .paper and static audit all complete on this exact SHA.
- No artifact is confirmed yet. If CI succeeds, record its artifact ID, size and SHA-256; if no artifact is produced, state that explicitly.
- Known remaining design limits: this is a query/DDL source contract, not a transaction executor. The future adapter must guarantee one read transaction and return READ_UNCERTAIN without partial evidence. The minSdk 26 OPEN_READONLY transaction API, complete D5 introspection coverage, exact immutable bootstrap migration bytes/ID/sequence/owner, and missing-path no-create behavior remain unresolved.
- Next: reconcile exact-SHA CI result; fix any failures and rerun both variants/static audit. Then review DDL edge cases (especially controlled clone-fork lineage under immutable triggers) before any future adapter design. No adapter/runtime authorization is implied.
- All limits remain: `AI_EXECUTION_ENABLED=false`; paper-only; no Feeder, exchange connectivity, backup/restore, writer admission, APK build/sign/publish or live trading.


## P5.4.93 CI closure — 2026-11-04

- Status: PASS. Exact source SHA: `cf16ad1c39fa9e015c11fd39cfaafe61c8f41d15`.
- Android T0 Foundation workflow #41765316296: success; exact head SHA verified. Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41765316296
- Regular host JVM suite: 154 tests, 0 failures, 0 errors, 0 skipped. `.paper` JVM suite: 154 tests, 0 failures, 0 errors, 0 skipped. `CanonicalSqliteReadContractTest`: 7/7 in each variant.
- Static audit: `ANDROID_T0_FOUNDATION_STATIC_AUDIT=PASS`.
- Artifact #13292826118, `android-t0-foundation-cf16ad1c39fa9e015c11fd39cfaafe61c8f41d15`, 112,305 bytes; ZIP integrity verified. SHA-256: `143c15b8cc7d017dfbeec25f1b3c096ca4f2cdda88d790fa4557894be393d365`. Artifact URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41765316296/artifacts/13292826118
- Current branch HEAD at documentation update start: `f2c4da47e7e8f8f68503266eac3a84d9b14c73eb` (branch `feature/p5-4-1-post-merge-validation-20261103`).
- Scope is pure Kotlin contract + JVM tests + static audit only. No SQLite open/create/read/write, SQL execution, filesystem/device access, DDL/migration/adoption, backup/restore, Feeder, lease, IPC, exchange, writer admission, APK build/sign/publish, or live trading.
- Remaining adapter prerequisites are unchanged: minSdk 26 read-only transaction API, complete D5 introspection coverage, immutable bootstrap migration bytes/ID/sequence/owner, missing-path no-create proof, and safe clone-fork procedure under immutable triggers. Separate authorization is required before adapter/runtime work.
- Next: resolve adapter prerequisites and review clone-fork procedure as design-only work. Do not implement or execute an adapter/DDL without separate authorization.


## P5.4.94 — Clone/fork immutability review (2026-11-04)

- Evidence: `docs/evidence/P5.4.94-ANDROID-T0-CLONE-FORK-IMMUTABILITY-REVIEW-2026-11-04.md`.
- Source/design review PASS: P5.4.93 immutable identity UPDATE/DELETE triggers conflict with changing a byte-for-byte cloned DB's parent identity. Dropping triggers to rewrite identity is rejected. A physical copy alone is not a clone protocol.
- Safe executable fork procedure: BLOCKED pending owner decision. Option A is a fresh child DB + new UUIDv4/parent lineage + fully specified allowlisted logical data import from a D3-consistent parent snapshot. Option B is to keep fork unsupported and fail closed until a later approved protocol. Recommendation recorded: Option B for current release until Option A has complete data inventory and fixture contract.
- No code/runtime/DB/device/filesystem/DDL/backup/restore/Feeder/writer/APK/exchange work was performed. `AI_EXECUTION_ENABLED=false`; paper-only.
- Owner decision required before any fork implementation. If Option A, next design the complete logical data-transfer contract and fixture failure matrix; if Option B, separately approve a source-only fail-closed unsupported-capability contract.

## P5.4.94 — Option B source-only fail-closed validation CLOSED (2026-11-04)

**Status: PASS for the approved source-only fail-closed capability, fixture tests, exact-SHA CI and artifact evidence. Runtime remains NOT AUTHORIZED.**

- Owner approval: `APPROVE P5.4.94 OPTION B`; current release rejects all clone/fork requests. Option A logical child provisioning/import is not approved.
- Capability implementation SHA tested: `c0d6d57ac3794663b10a8e9ab3015630f4f2faad`.
- Test-only RED commit `072af4fc09865fc31e90d9fe08e069281cabc2e0`; run #41767853060 failed as expected at compile time because implementation types were not yet present: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41767853060 .
- Exact-SHA implementation workflow #41767868429: **SUCCESS** on `c0d6d57ac3794663b10a8e9ab3015630f4f2faad`: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41767868429 .
- Regular host JVM suite: **159/159 PASS**; parallel `.paper` JVM suite: **159/159 PASS**; `CloneForkCapabilityTest`: **5/5 PASS** in each variant; Android T0 static audit: `ANDROID_T0_FOUNDATION_STATIC_AUDIT=PASS`.
- Artifact ID `13293821069`, size 116,176 bytes, GitHub SHA-256 digest `2ae0b7c331845c53a5d401541a85f5795cbdfda1a091925c83850c1ad2dd7033`; ZIP downloaded and 108 report/XML entries inspected. Artifact: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41767868429/artifacts/13293821069 .
- Evidence report updated in commit `08b49231812b7d06e3e213a2b6c61030cdd27fd3`: `docs/evidence/P5.4.94-ANDROID-T0-CLONE-FORK-IMMUTABILITY-REVIEW-2026-11-04.md`.
- No APK build/sign/publish, DB/SQLite/SQL/filesystem/device/runtime/Feeder/backup/restore/writer/exchange/trading action occurred. `AI_EXECUTION_ENABLED=false`; paper-only.

Next bounded step: continue design-only resolution of the remaining Android read-only SQLite adapter prerequisites (minSdk 26 read-only transaction API, complete D5 introspection coverage, immutable bootstrap migration bytes/ID/sequence/owner, and proof that read-only open of a missing path cannot create a DB). No adapter or runtime work until separately authorized.

## Read-only SQLite transaction API review — minSdk 26 BLOCKED (2026-11-04)

- Design note: `docs/evidence/P5.4.89-ANDROID-T0-PERSISTED-IDENTITY-LIFECYCLE-AND-READONLY-SQLITE-ADAPTER-DESIGN-2026-11-04.md`, section 10.
- App config confirms `minSdk=26`; current app dependencies do not include AndroidX SQLite/Room.
- Platform `SQLiteDatabase.beginTransactionReadOnly()` is API 35, so it is not directly available throughout minSdk 26 support. Platform `beginTransaction()` is EXCLUSIVE and `beginTransactionNonExclusive()` is IMMEDIATE; neither is accepted as equivalent to a DEFERRED read-only transaction.
- AndroidX `SupportSQLiteDatabase.beginTransactionReadOnly()` is documented since 2.5.0, but the interface default can delegate to ordinary `beginTransactionWithListener()` when the implementation does not support read-only transactions. A method name alone is not sufficient evidence. No dependency was added.
- Official references: https://developer.android.com/reference/android/database/sqlite/SQLiteDatabase and https://developer.android.com/reference/androidx/sqlite/db/SupportSQLiteDatabase .
- Decision: **BLOCKED** — no transaction primitive approved. No adapter, SQL, DB, filesystem, device or instrumentation operation was performed.
- Remaining prerequisites: (1) minSdk 26 read-only consistent-snapshot transaction API; (2) complete D5 schema-introspection coverage; (3) exact immutable bootstrap migration bytes/ID/sequence/owner; (4) proof that read-only open of a missing path cannot create a DB.
- Next: continue source/API design review only. Any device, filesystem or SQLite runtime conformance test requires separate explicit authorization. Keep `AI_EXECUTION_ENABLED=false`; paper-only.

## P5.4.95 — D5 SQLite schema introspection coverage (2026-11-04)

**Status: PASS — approved source-level query contract and pure fixture CI scope. Full D5 canonicalization and runtime readiness remain NOT VERIFIED.**

- Evidence report: `docs/evidence/P5.4.95-D5-SQLITE-SCHEMA-INTROSPECTION-COVERAGE-REVIEW-2026-11-04.md`.
- Evidence report commit: `cc2ca423087d22cbbeaf2098c3ac829634427cc9`.
- Existing branch only: `feature/p5-4-1-post-merge-validation-20261103`; no new branch or PR.
- Exact Android source/test code SHA validated: `df4f8815d87684691ae24fa6080bf944012ba2ba`.
- Source file blob: `4cb50f780900bf8d7dda58e949c987cc7d89df3b`.
- Test file blob: `cf527f5c622275a77552795e514643f76dcd6799`.

### Implemented source contract

- `table_xinfo` for catalog tables and views.
- `index_xinfo` for catalog indexes.
- Retain `index_list` and `foreign_key_list` for tables only.
- Reject unknown catalog object types and missing SQL metadata.
- Fail-closed on virtual-table declarations until module inventory and implementation provenance are verified; leading SQL comments are handled.
- Trigger SQL remains in catalog evidence; no trigger PRAGMA is generated.

### Test / CI evidence — PASS

- RED confirmed: [run #41771886754](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41771886754), SHA `7fb5a054354ed834afa74ee357ebbf495f51532d`; 162 tests, 4 D5 assertions failed as expected.
- GREEN: [run #41773126210](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41773126210), exact SHA `df4f8815d87684691ae24fa6080bf944012ba2ba); workflow SUCCESS.
- Regular host variant: **163/163 PASS**, 23 test classes, 0 failures/errors/skips.
- `.paper` variant: **163/163 PASS**, 23 test classes, 0 failures/errors/skips.
- `CanonicalSqliteReadContractTest`: **11/11 PASS** in each variant.
- Static audit: `ANDROID_T0_FOUNDATION_STATIC_AUDIT=PASS`.
- Artifact #13295911777, 116,938 bytes; SHA-256 `d0560be824c6f8eb1b094bf72b9bd57909fba6cb3f52cee3657a04c70f8052c0`. Artifact ZIP downloaded and XML reports inspected for both variants.
- Branch HEAD after evidence commits: `cc2ca423087d22cbbeaf2098c3ac829634427cc9`; code under test remains exactly the workflow SHA above. Handoff update follows this report commit.

### Remaining blockers / limits

- Shadow-table classification and inclusion/association policy remain OPEN. Current query contract cannot identify every shadow table; complete D5 schema coverage and schema digest are NOT VERIFIED.
- SQLite runtime feature matrix and `module_list` capability detection remain OPEN. Source-level PRAGMA selection does not prove runtime support.
- Virtual module implementation provenance/allowlist remains OPEN; current policy rejects all virtual tables.
- Canonical envelope grammar, canonicalization ID/version, full introspection field schema and digest composition remain OPEN.
- minSdk 26 read-only consistent-snapshot transaction primitive remains BLOCKED (see P5.4.89 section 10).
- Exact bootstrap migration bytes/ID/sequence/owner remain OPEN.
- Missing-path read-only open no-create proof remains OPEN.
- SQLite adapter/runtime/device remains NOT IMPLEMENTED / NOT AUTHORIZED.

No SQLite database was opened; no SQL/PRAGMA was executed against a database; no filesystem/device access, adapter/dependency, APK build/sign/publish, Feeder, writer, backup/restore, exchange or trading operation occurred. Keep `AI_EXECUTION_ENABLED=false`; paper-only.

**Next bounded step:** design and review the still-open D5 requirements (runtime feature matrix, shadow-table policy, virtual-module provenance, canonical envelope) before proposing another source delta. Do not proceed to SQLite adapter or runtime work without separate authorization.


## P5.4.96 — D5 runtime feature, shadow-table and canonical-envelope design review (2026-11-04)

- Evidence report: `docs/evidence/P5.4.96-D5-RUNTIME-FEATURE-SHADOW-TABLE-AND-CANONICAL-ENVELOPE-REVIEW-2026-11-04.md`.
- Baseline HEAD reviewed: `b93e417c91d87da6b14f4f86f2e99eec9685560c`.
- Documentation/API review only; no source code, tests, dependency, SQL execution, SQLite connection, DB, filesystem, Android device or instrumentation changed/accessed.
- Official SQLite docs establish: unknown PRAGMAs are silently ignored; `PRAGMA table_list` first appeared in SQLite 3.37.0 and classifies table/view/shadow/virtual; its output can gain columns; shadow classification depends on a virtual-table module's `xShadowName` callback; `module_list` only reports registered module names and is not implementation provenance.
- Recommended runtime floor: SQLite >= 3.37.0; positively probe table-list capability via table-valued `pragma_table_list`, validate exact result columns, fail closed on missing/unknown shape, and cross-check against `sqlite_schema`. Runtime source ID is recorded; exact source-ID allowlist remains an owner decision.
- Recommended current-release policy: reject both `shadow` and `virtual` objects. Do not infer parent/module by naming convention or regex. Future virtual-table support requires a versioned implementation/provenance allowlist and complete module-specific fixtures.
- Proposed D5 canonical envelope field inventory documented: runtime identity/feature set; deterministic catalog objects with exact SQL UTF-8; full `table_xinfo`, `index_list`, `index_xinfo`, `foreign_key_list` fields; view/trigger SQL; unsupported-object and result-shape fail-closed rules. This is not yet a frozen byte serialization/digest.
- Status: P5.4.96 design review PASS; D5 source unchanged; canonical envelope/digest NOT IMPLEMENTED; recommendations require owner decision before source delta. Tests/workflow/artifact NOT RUN / NOT APPLICABLE (docs-only).
- Still blocked/open: minSdk 26 read-only consistent transaction API; exact bootstrap migration bytes/ID/sequence/owner; missing-path read-only no-create proof; runtime SQLite feature/source-ID allowlist; adapter/runtime/device NOT IMPLEMENTED / NOT AUTHORIZED.
- No DB, SQL/PRAGMA execution, filesystem/device, APK, Feeder, writer, backup/restore, exchange or trading action. Keep `AI_EXECUTION_ENABLED=false`; paper-only.

Next bounded step: obtain owner decisions on the five items in P5.4.96 section 7. Do not implement the canonical-envelope source delta or SQLite adapter until the relevant approval; no runtime authorization is implied.


## P5.4.97 — Android minSdk 26 read-only transaction API review (2026-11-04)

- Evidence report: `docs/evidence/P5.4.97-ANDROID-MINSDK26-READONLY-TRANSACTION-API-REVIEW-2026-11-04.md`.
- Baseline HEAD reviewed: `5a47879d3483e826d63a95d5449970613810d1c6`.
- Documentation/AOSP source review only; no source/dependency, DB, filesystem, Android device, SQL, instrumentation or workflow changed/used.
- Framework facts: `OPEN_READONLY` API 1; `beginTransaction()` is EXCLUSIVE; `beginTransactionNonExclusive()` is IMMEDIATE; framework `beginTransactionReadOnly()` only API 35 and DEFERRED/read-only.
- AndroidX SupportSQLiteDatabase adds `beginTransactionReadOnly()` in the 2.5.0 line. Interface default delegates to `beginTransaction()`, so interface presence alone is not proof.
- Reviewed AndroidX FrameworkSQLiteDatabase implementation attempts reflective `SQLiteSession.beginTransaction(TRANSACTION_MODE_DEFERRED,...)`; if reflection is unavailable, fallback is `beginTransaction()` (EXCLUSIVE). Reflection/hidden-API behavior must be proven for app target SDK and each supported runtime. Candidate is not certified.
- Decision: minSdk 26 read-only consistent transaction remains **BLOCKED / NOT RUNTIME VERIFIED**. AndroidX framework driver is a candidate only if concrete override and DEFERRED reflection path are verified; EXCLUSIVE fallback is unacceptable.
- Required future proof is documented: API 26+ device/runtime matrix; exact app target SDK and pinned dependency; read-only open/no-create test; actual DEFERRED path proof; concurrent writer snapshot stability across WAL/rollback-journal if supported; write rejection; no DB/WAL/SHM mutation; injected failure cleanup and READ_UNCERTAIN behavior.
- Source/dependency change: NOT MADE. Adapter: NOT IMPLEMENTED / NOT AUTHORIZED. DB/device/instrumentation tests: NOT RUN / NOT AUTHORIZED. Workflow/artifact: NOT RUN / NOT APPLICABLE.
- No DB, SQL, filesystem/device, Feeder, writer, backup/restore, APK, exchange or trading operation. Keep `AI_EXECUTION_ENABLED=false`; paper-only.

Next bounded step: owner review/authorization for a source-level dependency/API spike and test design only. This is separate from any DB/device/instrumentation authorization.

## P5.4.96 + P5.4.98 — D5 source contract and read-only transaction spike (2026-11-04)

- Owner approvals: P5.4.96 recommendations and P5.4.98 source-level spike explicitly approved.
- Evidence report: `docs/evidence/P5.4.98-MINSDK26-READONLY-SQLITE-SOURCE-SPIKE-2026-11-04.md`.
- Report commit: `96898405b9438752cbe847c311fa9ac1970a6d14`.
- Active branch: `feature/p5-4-1-post-merge-validation-20261103`.
- Source implementation commit: `25bb4a16fba0651cbcffb473f0ad8b1b7e75d750`.
- Transaction evidence gate + tests commit: `d34b6ef2652b964294a3b815ba7e93343f1cfa11`.
- Current HEAD at this handoff update: `96898405b9438752cbe847c311fa9ac1970a6d14`.
- Added `CanonicalD5SchemaContract.kt`: SQLite >=3.37.0; positive exact table-list feature probe; exact output-shape validation; reject virtual/shadow/unknown objects; compare table-list against sqlite_schema after sqlite_* exclusion; D5 envelope v1 logical field inventory; rootpage excluded; exact source ID recorded without imposing an unapproved allowlist.
- Added JVM tests: `CanonicalD5SchemaContractTest.kt` and `D5ReadOnlyTransactionGateTest.kt`.
- Added a pure source gate requiring concrete implementation identity, DEFERRED mode, read-only enforcement and no fallback. This validates adapter-supplied evidence only; it is not runtime proof.
- P5.4.98 source spike: AndroidX SupportSQLiteDatabase default read-only transaction method delegates to EXCLUSIVE `beginTransaction()`. Framework driver override attempts reflection into SQLiteSession for DEFERRED; if reflection is unavailable it falls back to EXCLUSIVE. API 26 + target SDK 35 reflection behavior remains unproven. No dependency was added; no adapter selected.
- minSdk 26 consistent read-only transaction: **BLOCKED / NOT RUNTIME VERIFIED**.
- Canonical envelope v1 field inventory: implemented. Canonical byte serialization and schema digest: **NOT IMPLEMENTED**.
- GitHub Actions Android T0 Foundation:
  - Test-spec RED run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41775292767 (run 41775292767; observed in progress when recorded).
  - Source implementation run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41775320141 (run 41775320141; cancelled by subsequent push before final verification).
  - Latest source test run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41775378163 (run 41775378163; exact source SHA `d34b6ef2652b964294a3b815ba7e93343f1cfa11`; pending at handoff time).
- CI/test status for new code: **NOT VERIFIED** until run 41775378163 completes. No artifact is claimed.
- No Android device, instrumentation, filesystem, SQLite database, SQL/PRAGMA execution, Feeder, lease, writer, backup/restore, APK, exchange or trading action. Keep `AI_EXECUTION_ENABLED=false`.
- Next step: reconcile run 41775378163 and its jobs/artifact. Fix source-level failures if present, then update this handoff/report with exact outcome. Runtime/device/DB authorization remains separate.
