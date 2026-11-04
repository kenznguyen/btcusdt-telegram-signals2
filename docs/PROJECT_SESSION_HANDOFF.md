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
