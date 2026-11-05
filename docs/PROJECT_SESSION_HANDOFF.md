# Five-Layer System — Session Handoff

Last updated: 2026-11-05 (Asia/Ho_Chi_Minh)

## Purpose

This file is the durable restart point for future ChatGPT sessions. GitHub is the source of truth for project progress and evidence; do not rely on conversation memory alone.

## Repository and workflow rules

- Repository: `kenznguyen/btcusdt-telegram-signals2`.
- GitHub stores source, plans, evidence manifests, and session handoffs.
- Codemagic is the action/workflow runner. Do not introduce GitHub Actions as an active runner; historical workflow source may be retained under `ci/archive/github-actions/`.
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

R1 closeout status (2026-11-05): **PARTIAL / NOT VERIFIED**.
- Reconciliation report: `docs/evidence/t0/P5_2_6_2_R1_ANDROID_P4_EVIDENCE_RECONCILIATION_2026-11-05.md`.
- Latest report commit: `d37b89cf766dff574f25b8878e67d2b56e903843`.
- Latest report blob SHA: `ad3bd98d791cc9d4372e0606883d3519b758d9ef`.
- All 17 original P4 payload hashes recomputed on Android/Termux: **17/17 MATCH** (user-provided command output); payload bytes remain on device, not uploaded to GitHub.
- Read-only scans of six P4 shadow directories and standalone `$HOME/p4_*.py` scripts found no source SHA, `GITHUB_SHA`, workflow run ID, or explicit provenance metadata.
- Local checkout HEAD is `1c16755a07a053e1f225c8861ec76dc9ced1a5d8`, clean. Local Git history contains commits dated 2026-11-01/02 but cannot bind any individual P4 run to a commit. Do not substitute this observed HEAD for historical run-specific source SHA.
- No tests rerun; Natural Doze remains `INTERRUPTED / DEFERRED`.
- PR #119: https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/119 — OPEN / DRAFT / NOT MERGED; head `d37b89cf766dff574f25b8878e67d2b56e903843`. Combined commit status returned no status checks; no CI run/artifact created by these docs-only changes.
- Documentation branch: `docs/p4-evidence-manifest-20261103`.

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

The manifest contains 17 SHA-256 entries. They are user-supplied Android inventory fingerprints recorded in the manifest; the hashes alone do not prove semantic correctness. The original referenced logs/scripts were recovered on the user's Android/Termux device. The user supplied read-only `sha256sum` output showing **17/17 exact matches** against the manifest. This verifies payload integrity relative to the recorded manifest values, but the payload bytes have not been uploaded to GitHub or attached to this repository. Run-specific historical source provenance remains UNVERIFIED.

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

1. R1 evidence reconciliation completed to the extent possible; do not repeat repository/device searches already recorded.
2. Keep the 17/17 device SHA-256 result distinct from source provenance: payload integrity VERIFIED relative to manifest; run-specific source SHA NOT VERIFIED.
3. Preserve historical P4 labels as RECORDED PASS / INTERRUPTED; no promotion to independent test verification.
4. Keep Natural Doze `INTERRUPTED / DEFERRED` and outside current work.
5. Next permitted work: documentation-only review of the non-Doze multi-ledger backup/restore evidence gap (candles, Paper Ledger, Risk State, Paper State), without running tests or activating runtime. First define the evidence already present and the minimum missing proof; request explicit approval before any new runtime/test activity.
6. Continue on the existing documentation branch/PR; no new branch/PR and no merge without explicit approval.

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



## Repository cleanup increment — 2026-11-05

### Consolidated Android / five-layer PR chain

- PRs #58–#62 were reviewed by comparing base/head refs, changed-file inventories, and the cumulative diff against PR #92.
- PR #92 targets `main` from the exact same head branch and SHA as PR #62: `feature/android-five-layer-control` / `2a4b914f5e1f133544494278f3bf5117ff815418`.
- PR #92 contains the cumulative source changes from #58–#62. The three legacy Android GitHub workflow files are retained under `ci/archive/github-actions/` in the consolidated diff.
- PRs #58, #59, #60, #61 and #62 were closed as superseded by #92. Closure comments were added to each PR. No branch was deleted and no PR was merged.
- PR #92 remains OPEN / DRAFT / NOT MERGED; current head SHA `2a4b914f5e1f133544494278f3bf5117ff815418`. It is the single retained review path for that cumulative feature stack.

### P5.2.5 PR chain disposition

- PR #112 remains OPEN / DRAFT / NOT MERGED and PAUSED per user instruction. Do not resume its implementation without explicit instruction.
- PRs #113–#117 remain OPEN / DRAFT / NOT MERGED. They represent distinct historical RED evidence, source-review closure, GREEN plan, G0 contract freeze, and G1/P1 contract review. No evidence currently justifies bulk closure.
- PR #111 remains OPEN / DRAFT / NOT MERGED. Its RED contract evidence is historical and overlaps the later T0 Gateway implementation in PR #134. Do not close it yet: the #134 branch has a GitHub Actions workflow, while the user's current execution preference is Codemagic. Resolve the CI-provider alignment and decide whether the Codemagic RED workflow/evidence must be retained before closing #111.
- PR #134 remains OPEN / DRAFT / NOT MERGED. Its exact-head implementation evidence is recorded in its PR body; current head `76e6bb9e91ee3fa02cb7d97d2058fca1b5261582`, tested source SHA `5b678a0419aa283cd54703a2a7c0e20df385e41c`. The tested source and current head differ by a documentation-only commit per the PR body. The GitHub Actions workflow choice must be reconciled with the user's current Codemagic execution preference before treating CI policy as aligned.
- PR #119 remains OPEN / DRAFT / NOT MERGED; latest head after this handoff update must be recorded in its PR body.

### Cleanup boundaries

- No merges, branch deletions, source-code changes, deployments, canonical DB creation, Feeder startup, exchange connection, market-data synchronization, or live execution were performed.
- Keep `ai_execution_enabled=false`; paper-only.
- Android Natural Doze remains `INTERRUPTED / DEFERRED`.
- Next cleanup action: resolve the PR #134 CI-provider policy discrepancy, then determine whether PR #111 can be closed as superseded while preserving its RED evidence trail. Do not close #112 or bulk-close #113–#117.


## CI provider alignment — 2026-11-05 (PR #134)

- Repository operating rule corrected to the user's current direction: GitHub stores source and Codemagic runs actions.
- On existing branch `feature/t0-atomic-write-fencing-20261105` (PR #134), added the `t0-single-writer-gateway` workflow to `codemagic.yaml`.
- Preserved the former active GitHub Actions workflow at `ci/archive/github-actions/t0-single-writer-gateway-red.yml`; removed its active `.github/workflows/` copy.
- Relevant commits, in order:
  - Archive legacy workflow: `e6a1dfe7faef0e8779866e5cb78a18af9732678d`
  - Add Codemagic workflow: `8070c366e00c583e587fff27714d5545fe32eac3`
  - Remove active GitHub Actions workflow: `c81a268075b24778c81d0b1071d0a5e581d20d21`
- Static file checks: Codemagic workflow key present; archived workflow blob matches original blob `9f03dc9bc0c6df62942bf6d384bb1ff294e6d5b2`; former active workflow path absent.
- Codemagic execution: NOT RUN / NOT VERIFIED. No workflow run ID or artifact exists for this increment. No tests executed.
- PR #111 remains open pending a real Codemagic run and confirmation of source SHA, test results, and artifacts. PR #112 remains paused.
- No merge, branch deletion, canonical DB, Feeder activation, exchange access, market-data sync, or live execution.
- Next: run the new workflow in Codemagic against the exact PR #134 head; inspect logs/artifacts and record PASS/BLOCKED/NOT VERIFIED. Only then decide whether #111 is superseded and may be closed.


### Codemagic workflow follow-up correction — 2026-11-05

- Static review found the new Gateway workflow initially invoked system `python` although `ci/setup-python.sh` provisions the isolated interpreter and exports `CI_PYTHON` through Codemagic's `CM_ENV`.
- Corrected every compile/test invocation in the Gateway workflow to use `"$CI_PYTHON"`.
- Latest PR #134 branch commit after correction: `fda26f48eb9a3f2242d098ae546bfda8cc671d41`.
- Latest `codemagic.yaml` blob: `7dade638d74542513ed881763fc233261ec52ea9`.
- Static verification: all Gateway test commands use `CI_PYTHON`; no system `python -m unittest/py_compile` remains in the workflow block; archived legacy workflow blob still matches original; active GitHub Actions workflow path remains absent.
- Codemagic runtime remains NOT RUN / NOT VERIFIED. No test results, workflow run ID, or artifacts are available yet.
