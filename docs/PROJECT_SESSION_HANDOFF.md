# Five-Layer System — Session Handoff

Last updated: 2026-11-03 (Asia/Ho_Chi_Minh)

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

### P5.2.6.2-R1 — Evidence Reconciliation

Objective: reconcile Android P4 evidence from the recorded manifest against source identity, artifact files, logs, scripts, and SHA-256 inventory. Do not start runtime or repeat tests.

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
