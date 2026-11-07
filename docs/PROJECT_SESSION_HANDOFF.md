# Five-Layer System — Session Handoff

Last updated: 2026-11-07 (Asia/Ho_Chi_Minh)

## Purpose

This file is the durable restart point for future ChatGPT sessions. GitHub is the source of truth for project progress and evidence; do not rely on conversation memory alone.

## Repository and workflow rules

- Repository: `kenznguyen/btcusdt-telegram-signals2`.
- GitHub stores source, plans, evidence manifests, and session handoffs.
- GitHub Actions is the default CI. Use Codemagic only when GitHub Actions cannot run or is blocked by its limits.
- **CI platform selection is locked:** before creating, editing, disabling, or migrating any workflow, reread this section and inspect the current repository workflows. Never infer that Codemagic is preferred from a prior task, workflow presence, or convenience.
- **Codemagic is fallback-only:** do not move a GitHub Actions workflow to Codemagic unless a concrete GitHub Actions blocker is recorded (for example, unavailable runner/service, exhausted quota, or a documented platform restriction) and the user has authorized the fallback. Record the failed GitHub Actions run/error and why a retry or adjustment cannot solve it. Do not use Codemagic merely because it already exists in the repository.
- **No silent platform migration:** if a fallback is authorized, keep the GitHub Actions workflow/configuration intact where possible; document scope, reason, approval, parity gaps, and the condition for returning to GitHub Actions. Never remove the default workflow as part of a temporary fallback.
- **Before each CI run, verify provenance:** record PR head SHA, base SHA, workflow run ID/event, checked-out SHA from logs, job conclusions, artifact ID/name/digest, and test summaries. For pull_request runs, distinguish the PR head SHA from GitHub's synthetic merge SHA (refs/pull/<n>/merge); do not label a merge-SHA run as a direct-head run. A PASS applies only to the exact checked-out source/context proven by logs.
- **Evidence mismatch rule:** if the checked-out SHA, PR head SHA, or artifact identity is ambiguous or differs from the expected source, mark exact-head verification NOT VERIFIED; do not promote stale evidence or close a superseded PR on that basis.
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

- Artifact download requests succeeded for all four P5.4.1 artifacts and ZIP files were materialized in the working session:
  - `13214895177`
  - `13214685271`
  - `13214084859`
  - `13213209943`
- The download step proves retrievability only. ZIP integrity checks, SHA-256 recomputation, comparison against the P5.4.2 recorded fingerprints, and inspection of embedded source-SHA/log evidence have **NOT BEEN COMPLETED**.
- A subsequent data-analysis operation was unavailable due to a temporary capacity limit. Do not treat the prior conversational claim that all four checksums matched as verified evidence; no successful hash-computation output was produced.
- P5.4.4 status: **PARTIAL / NOT VERIFIED**. No workflow was rerun and no code, runtime configuration, canonical DB, Feeder, exchange connection, or market data was changed.
- Next step: independently inspect the four downloaded ZIP payloads, run ZIP integrity checks, compute SHA-256 from the actual bytes, compare each result to the P5.4.2 fingerprints, and inspect embedded evidence. Record VERIFIED / MISMATCH / NOT RETRIEVABLE per artifact.
- Existing restrictions remain: `ai_execution_enabled=false`; Natural Doze stays **INTERRUPTED / DEFERRED**; no runtime activation or execution is authorized.


## 2026-11-05 — CI platform guard and PR #134 post-restoration verification

### CI platform rule strengthened

The GitHub Actions default is a project-level constraint, not a discretionary tool choice. Codemagic is fallback-only and requires a recorded GitHub Actions blocker plus explicit user authorization. Do not migrate or remove the GitHub Actions workflow during a temporary fallback. Before any CI workflow change, reread the repository rules and inspect the active workflow configuration.

### PR #134 latest run

- PR: #134, OPEN / DRAFT / NOT MERGED.
- Branch: feature/t0-atomic-write-fencing-20261105.
- PR head SHA: ee291c4d4a179f91b93a9d3f378d4c7a1e2df741.
- Base branch/SHA: feature/t0-centralized-data-feeder-p1-20261101 / 8b196d2720eab804728df7c0227c606c094b16ad.
- Workflow: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41996998169, run ID 41996998169, event pull_request, conclusion SUCCESS.
- Job ID: 127142557807; all 10 steps completed successfully.
- Checkout identity: GitHub Actions checked out synthetic PR merge SHA 7f3be0e5da5fcade121c7526d367eab157237f3a (merge of PR head ee291c4... into base 8b196d2...). This run validates the PR merge context, not a direct checkout of the PR head. Do not describe it as a direct-head test.
- Logs: source-only preflight PASS; Python compile PASS; Gateway RED contracts 10/10 PASS; Gateway + store + sync + storage + Feeder lifecycle regression 54/54 PASS; full market_data suite 175 PASS, 8 TimescaleDB integration tests skipped because MARKET_DATA_TEST_DATABASE_URL was not supplied.
- Artifact: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41996998169/artifacts/13400124790; name t0-swg-contract-evidence-7f3be0e5da5fcade121c7526d367eab157237f3a; ID 13400124790; 7,676 bytes; GitHub digest sha256:33166350b71e67f3c40fb7e208bba26b945861421509c9a377111fa8971118a9.
- Artifact digest is GitHub's upload digest from run metadata/logs; payload bytes have not been independently downloaded and re-hashed in this step.
- Workflow file restored on PR branch; active workflow blob and archived copy both previously verified as 9f03dc9bc0c6df62942bf6d384bb1ff294e6d5b2. Codemagic no longer contains the temporary t0-single-writer-gateway job.
- Verdict: workflow execution PASS for synthetic merge context; direct PR-head-only verification NOT VERIFIED; TimescaleDB integration NOT RUN; artifact payload hash independently recomputed NOT VERIFIED.
- No merge, no branch deletion, no canonical DB/Feeder activation, no exchange/data sync, and no live trading.

### Next action

Compare PR #111 RED contract coverage against PR #134's verified Gateway RED tests and full regression evidence. Preserve PR #111 until the coverage comparison establishes whether it is genuinely superseded. Any follow-up workflow run must explicitly record both PR head SHA and checked-out merge SHA. Keep PR #134 open and unmerged pending review and explicit user approval.


### PR #111 versus PR #134 — contract overlap review (2026-11-05)

- PR #111 remains OPEN / DRAFT / NOT MERGED; head SHA 65f8baa1e198666f7cb6da2600505947665a9a78; base SHA a58b6163a78861ecf5bb7d2c8fc11aa420142837. Its scope is a RED-only contract test file, a scope note, and a manual-only Codemagic runner; it explicitly contains no production implementation.
- PR #134 remains OPEN / DRAFT / NOT MERGED; head SHA ee291c4d4a179f91b93a9d3f378d4c7a1e2df741. It includes the same 10-test contract suite concept plus Gateway implementation, caller routing, regression updates, evidence report, and GitHub Actions workflow.
- The RED test files are not byte-identical: PR #111 blob c4336e8f9b5b1c373af425801a8679bbf22ed626; PR #134 blob 1ae31341e207c49d660dc0e54a69a60a646d2198. They contain 10 tests each with seven line-level differences: wording, renamed A04/E01/E03 tests, rollback token case, and E02 source path changed from market_data/feeder.py to market_data/feeder_service.py. PR #134's 10 tests all passed in run 41996998169's synthetic merge context.
- Preliminary disposition: PR #134 appears to supersede the implementation/test purpose of PR #111 for the current code line, but this is not a byte-identical replacement and the RED-baseline history is useful as an audit trail. PR #111 is therefore marked CANDIDATE SUPERSEDED / KEEP OPEN pending explicit user approval to close; do not close it automatically.
- PR #111's Codemagic-only runner conflicts with the now-locked GitHub Actions-default policy. Do not run or extend that Codemagic workflow. If the historical RED baseline ever needs reproduction, port only the required runner to GitHub Actions on a separately authorized scope; do not migrate the current PR #134 workflow away from GitHub Actions.
- No merge or branch deletion. No production activation, canonical DB, Feeder startup, exchange connection, market-data sync, or live execution.


## 2026-11-05 — PR #134 source-provenance reconciliation

- Current PR API head: ee291c4d4a179f91b93a9d3f378d4c7a1e2df741; base: 8b196d2720eab804728df7c0227c606c094b16ad. PR remains OPEN / DRAFT / NOT MERGED.
- Direct push run 41977057660 tested and checked out source SHA 5b678a0419aa283cd54703a2a7c0e20df385e41c; conclusion SUCCESS. Test results: RED 10 PASS; focused Gateway/store/sync/storage/Feeder regression 54 PASS; full market_data suite 175 PASS, 8 skipped.
- Compare 5b678a0419aa283cd54703a2a7c0e20df385e41c...ee291c4d4a179f91b93a9d3f378d4c7a1e2df741 reports exactly 8 commits ahead and only two changed paths: archived copy of the workflow and evidence markdown. No market_data source file or active workflow file changed after the tested push SHA.
- Therefore direct-head source equivalence is established for the implementation and active workflow at current PR head by GitHub compare, but there is no push run whose head_sha equals the current PR head. State precisely: implementation/workflow content tested on 5b678a and unchanged through ee291c; current PR head itself was separately exercised in pull_request synthetic merge run 41996998169 (checkout SHA 7f3be0e5da5fcade121c7526d367eab157237f3a). Do not conflate these forms of evidence.
- PR body contained a stale sentence claiming current head 76e6bb9e91ee3fa02cb7d97d2058fca1b5261582. GitHub PR API currently reports ee291c4d4a179f91b93a9d3f378d4c7a1e2df741; correct the stale body statement.
- Current active workflow includes push on the feature branch and workflow_dispatch. Available GitHub connector exposes no workflow-dispatch trigger action, so no manual dispatch was attempted. No dummy commit was created solely to trigger CI.
- Verdict: tested implementation/workflow content PASS and unchanged through current PR head; current PR merge-context PASS; exact current-head push-run NOT PRESENT; TimescaleDB integration NOT RUN; production readiness NOT GRANTED.


## 2026-11-05 — SWG-F Paper Writer Gate status check (read-only)

- PR #112 remains OPEN / DRAFT / NOT MERGED on branch feature/t0-paper-writer-isolation-red-20261102; current head and tested SHA d6465e073d7aade8ac60716db2ffef273334c5b0; base a58b6163a78861ecf5bb7d2c8fc11aa420142837.
- Existing branch already contains P1-P3 GREEN implementation (PaperWriterGate, PaperLedger isolation, API integration) and a P4 read-only consumer audit. This is existing work, not authorization to resume implementation, merge, deploy, or activate runtime.
- GitHub Actions run 41989509168, event pull_request, SUCCESS; job 127118102636; workflow explicitly checked out and verified exact head SHA d6465e073d7aade8ac60716db2ffef273334c5b0.
- Verified logs: P2 PaperLedger 12/12 PASS, P3 API integration 31 tests completed, selected Paper execution regression 59 tests completed, P1 process-level runtime 12/12 PASS; zero errors/failures in the P2 and P1 classifiers. Job conclusion SUCCESS.
- Artifact ID 13397124437; name paper-writer-isolation-p1-p3-green-d3a29e30dc226ef8d6e0d64f8f8da08895069cf2; size 4,477 bytes; GitHub digest sha256:038bf8e8612e0755f97cf2b7ee122debdb76d4bfdb4383fabaff7a6500bb7061; expires 2026-11-12.
- Scope remains Linux only. Windows/Android lock semantics, full process crash/recovery on those platforms, deployment concurrency, and live recovery are NOT VERIFIED. This CI is isolated tests only; no Paper/T0 production DB, canonical ingestion, Feeder, exchange sync, deployment, or orders.
- PR #112 includes a Codemagic workflow addition from historical implementation work. Do not run or extend Codemagic; GitHub Actions remains default. Keep the PR and its implementation paused pending explicit user direction; no code changes, merge, or branch deletion were performed in this status check.
- Next allowed step without resuming implementation: read-only compare SWG-F P1-P3 acceptance against the existing RED/plan artifacts and document platform gaps; do not start P4/P5 or enable Paper runtime until explicitly authorized.


## 2026-11-05 — PR #110–#117 dependency inventory (read-only)

- #110 OPEN/DRAFT/NOT MERGED; head a58b6163a78861ecf5bb7d2c8fc11aa420142837; base 1c16755a07a053e1f225c8861ec76dc9ced1a5d8. Owns isolated Paper/T0 shadow migration fixture and tests (3 Python files plus historical Codemagic runner). It is the base of #111 and #112; preserve as dependency until consumers are dispositioned.
- #111 OPEN/DRAFT/NOT MERGED; head 65f8baa1e198666f7cb6da2600505947665a9a78; base #110 head a58b6163a78861ecf5bb7d2c8fc11aa420142837. RED SWG-A–E contracts only. Candidate superseded by evolved Gateway work in #134, but keep open pending explicit approval.
- #112 OPEN/DRAFT/NOT MERGED; head d6465e073d7aade8ac60716db2ffef273334c5b0; base #110 head. Contains P1-P3 GREEN PaperWriterGate/PaperLedger/API work plus P4 read-only audit. Existing implementation is paused; do not extend or merge without user instruction.
- #113 OPEN/DRAFT/NOT MERGED; head b14793db142e603c658eb01673816b0b82c85e06; base #110 head. One standalone SWG-A–F RED freeze report. Historical evidence, not implementation.
- #114 OPEN/DRAFT/NOT MERGED; head 2fd8d9d7b7a08b7c4dab05dbebd66be719774b9e; base c188a4d193f870a93efd348f993a4c1b2f1dfda0. One standalone RED source-review closure report. Distinct audit artifact.
- #115 OPEN/DRAFT/NOT MERGED; head 25159d4635c9f568d133b24ce5f6555d3faf5e4f; base c188a4d193f870a93efd348f993a4c1b2f1dfda0. Two standalone GREEN design/implementation-plan documents. Planning artifact, not implementation.
- #116 OPEN/DRAFT/NOT MERGED; head b8c5bb474008233260a571ad18c5848f02f55d97; base c188a4d193f870a93efd348f993a4c1b2f1dfda0. Adds G0 RED validation workflow and G0 contract freeze/test harness rules. Distinct CI/contract foundation.
- #117 OPEN/DRAFT/NOT MERGED; head 4298914726b4926745de8d31391923a655730d11; base 34bfc746e31777941fe0012f3f4d078abeae3254. One G1/P1 contract review report. Distinct review artifact; base SHA differs from #116 current head, so do not assume it is stacked on the latest #116 head without commit-graph verification.
- No PR in #110–#117 was closed, merged, rebased, or deleted during this inventory. Current recommendation: preserve #110, #112–#117 as separate dependency/evidence artifacts; only #111 is a candidate for user-approved closure after the #134 overlap decision.


## 2026-11-05 — PR #113–#117 ancestry check

- #114 (head 2fd8d9d7b7a08b7c4dab05dbebd66be719774b9e) and #115 (head 25159d4635c9f568d133b24ce5f6555d3faf5e4f) are sibling documentation branches from common base c188a4d193f870a93efd348f993a4c1b2f1dfda0; #115 adds two GREEN plan documents and #114 adds the RED source-review closure report. Compare reports diverged (10 commits ahead, 2 behind; only the two plan documents appear in the reported file diff). Do not treat one as replacing the other.
- #116 (head b8c5bb474008233260a571ad18c5848f02f55d97) is a distinct G0 workflow + contract freeze/harness branch from common base c188a4d193f870a93efd348f993a4c1b2f1dfda0; compare with #114 diverged (3 ahead, 2 behind). Preserve as distinct artifact.
- #117 is a G1/P1 contract review document (head 4298914726b4926745de8d31391923a655730d11). Its PR metadata reports base SHA 34bfc746e31777941fe0012f3f4d078abeae3254 on branch feature/p5-2-5-g0-contract-test-harness-20261102, while the current branch API reports tip b8c5bb474008233260a571ad18c5848f02f55d97. Compare shows the recorded PR base is behind current #116 branch tip by 2 commits. Treat #117 as BASE-STALE / NEEDS RECONCILIATION; do not merge, rebase, or retarget without explicit approval.
- #113 remains a standalone RED freeze report on #110's head; distinct from #114's source review, #115's GREEN plan, #116's G0 harness, and #117's G1/P1 review. No evidence supports bulk closure.
- No PR state, branch, or base was changed in this ancestry audit. Recommendation: preserve #113–#116 as separate artifacts; flag #117 for base reconciliation before any review-ready transition. PR #111 remains the only current candidate superseded by #134, pending explicit closure approval.

## 2026-11-05 — PR #117 base ancestry reconciliation (read-only)

- Repository `main` HEAD at inspection: `1144dda080ed9252f9f28dd8418699e7d116c6d8`.
- Canonical CI rule remains GitHub Actions by default; Codemagic is fallback-only with a documented GitHub Actions blocker and explicit user authorization.
- PR #117: OPEN / DRAFT / NOT MERGED.
  - Head branch/SHA: `docs/p5-2-5-g1-p1-contract-review-20261102` / `4298914726b4926745de8d31391923a655730d11`.
  - Base branch recorded by PR: `feature/p5-2-5-g0-contract-test-harness-20261102`.
  - Base SHA recorded by PR: `34bfc746e31777941fe0012f3f4d078abeae3254`.
  - Current base branch tip: `b8c5bb474008233260a571ad18c5848f02f55d97`.
  - Compare result: current base branch is 2 commits ahead of recorded PR base, 0 behind; merge base is the recorded PR base.
- The two missing commits are:
  1. `66088d879628141688065eb80cffe0eda55b7343` — `ci: add isolated GitHub Actions validation for P5.2.5 G0`; adds `.github/workflows/p5-2-5-g0-runtime-red-validation.yml`.
  2. `b8c5bb474008233260a571ad18c5848f02f55d97` — `docs: reconcile G0 contract with approved evidence and Gateway API`; updates `docs/t0/P5.2.5_G0_CONTRACT_FREEZE_AND_TEST_HARNESS.md`.
- PR #117 changes one documentation file only. Its review document still identifies parent baseline `34bfc...`, and its decision section says it does not override the G0 Codemagic evidence checklist. The updated G0 document records the actual GitHub Actions run and a narrower G0-only exception. Therefore PR #117's review text is stale relative to the current G0 evidence and should be reconciled before it is treated as current.
- The G0 document also contains stale policy wording that calls Codemagic the default for later work. This conflicts with the canonical `PROJECT_SESSION_HANDOFF.md` rule. The canonical handoff rule controls; do not migrate workflows to Codemagic.
- Status: **BASE-STALE / REVIEW TEXT NEEDS RECONCILIATION**. This was a read-only ancestry and document comparison. No rebase, retarget, branch update, PR state change, workflow run, test, runtime, database, Feeder, exchange, or execution action occurred.
- Next safe step: prepare a documentation-only correction to PR #117's existing review document on its current branch, preserving its review-only boundary and explicitly distinguishing the G0-only GitHub Actions evidence from the project-wide CI default. Do not rebase/retarget/merge or authorize G1/P1 implementation without explicit approval.

## 2026-11-05 — PR #117 base ancestry reconciliation (read-only)

- Repository `main` HEAD at inspection: `1144dda080ed9252f9f28dd8418699e7d116c6d8`.
- Canonical CI rule remains GitHub Actions by default; Codemagic is fallback-only with a documented GitHub Actions blocker and explicit user authorization.
- PR #117: OPEN / DRAFT / NOT MERGED.
  - Head branch/SHA: `docs/p5-2-5-g1-p1-contract-review-20261102` / `4298914726b4926745de8d31391923a655730d11`.
  - Base branch recorded by PR: `feature/p5-2-5-g0-contract-test-harness-20261102`.
  - Base SHA recorded by PR: `34bfc746e31777941fe0012f3f4d078abeae3254`.
  - Current base branch tip: `b8c5bb474008233260a571ad18c5848f02f55d97`.
  - Compare result: current base branch is 2 commits ahead of recorded PR base, 0 behind; merge base is the recorded PR base.
- The two missing commits are:
  1. `66088d879628141688065eb80cffe0eda55b7343` — `ci: add isolated GitHub Actions validation for P5.2.5 G0`; adds `.github/workflows/p5-2-5-g0-runtime-red-validation.yml`.
  2. `b8c5bb474008233260a571ad18c5848f02f55d97` — `docs: reconcile G0 contract with approved evidence and Gateway API`; updates `docs/t0/P5.2.5_G0_CONTRACT_FREEZE_AND_TEST_HARNESS.md`.
- PR #117 changes one documentation file only. Its review document still identifies parent baseline `34bfc...`, and its decision section says it does not override the G0 Codemagic evidence checklist. The updated G0 document records the actual GitHub Actions run and a narrower G0-only exception. Therefore PR #117's review text is stale relative to the current G0 evidence and should be reconciled before it is treated as current.
- The G0 document also contains stale policy wording that calls Codemagic the default for later work. This conflicts with the canonical `PROJECT_SESSION_HANDOFF.md` rule. The canonical handoff rule controls; do not migrate workflows to Codemagic.
- Status: **BASE-STALE / REVIEW TEXT NEEDS RECONCILIATION**. This was a read-only ancestry and document comparison. No rebase, retarget, branch update, PR state change, workflow run, test, runtime, database, Feeder, exchange, or execution action occurred.
- Next safe step: prepare a documentation-only correction to PR #117's existing review document on its current branch, preserving its review-only boundary and explicitly distinguishing the G0-only GitHub Actions evidence from the project-wide CI default. Do not rebase/retarget/merge or authorize G1/P1 implementation without explicit approval.

## 2026-11-05 — PR #117 review document reconciliation

- Updated the existing PR #117 documentation branch only; no new branch or PR created.
- Documentation commit: `8698d59fc910c261e469e296f6e347bc0a3ee234`.
- Changed file: `docs/t0/P5.2.5_G1_P1_CONTRACT_REVIEW.md` (documentation only).
- Added exact G0 GitHub Actions source SHA/run/artifact evidence and corrected the stale statement that treated Codemagic as the G0 evidence authority.
- Added the two-commit base ancestry record and retained the explicit `BASE-STALE / NEEDS RECONCILIATION` status. This commit does not fix ancestry.
- Current PR state at verification: head SHA `8698d59fc910c261e469e296f6e347bc0a3ee234`; OPEN / DRAFT / NOT MERGED.
- Workflow runs associated with this commit: none returned.
- No tests were run in this documentation-only increment. Exact-head CI verification: NOT VERIFIED unless a run is later observed and its checked-out SHA is confirmed.
- No rebase, retarget, merge, PR closure, runtime, DB, Feeder, exchange, deployment, or live execution action occurred.
- Next step: reconcile PR #117 ancestry only after explicit approval for a rebase/retarget strategy; otherwise keep it open and draft. G1/P1 implementation remains unauthorized.

## 2026-11-05 — PR #117 live mergeability recheck

- Direct GitHub PR API recheck: PR #117 remains OPEN / DRAFT / NOT MERGED; head SHA `8698d59fc910c261e469e296f6e347bc0a3ee234`; recorded base SHA remains `34bfc746e31777941fe0012f3f4d078abeae3254`; `mergeable=true`, `mergeable_state=clean`.
- Current branch tips: base `feature/p5-2-5-g0-contract-test-harness-20261102` = `b8c5bb474008233260a571ad18c5848f02f55d97`; PR head branch = `8698d59fc910c261e469e296f6e347bc0a3ee234`.
- Compare current base tip to PR head: `diverged`, 2 commits ahead and 2 behind, merge base `34bfc746e31777941fe0012f3f4d078abeae3254`. PR-side commits are `4298914726b4926745de8d31391923a655730d11` and `8698d59fc910c261e469e296f6e347bc0a3ee234`; base-side commits are the previously recorded G0 workflow and G0 contract evidence commits.
- The compare reports one changed file on the PR side: `docs/t0/P5.2.5_G1_P1_CONTRACT_REVIEW.md`. GitHub reports the current merge result clean, so a rebase is not currently required merely to resolve a textual merge conflict. However, recorded base SHA is stale and ancestry is diverged; retain the audit flag until the owner decides whether to refresh ancestry. Do not rebase or retarget automatically.
- No workflow run was returned for the new documentation commit. No tests were run. Exact-head CI: NOT VERIFIED.
- Recommended disposition: keep PR #117 OPEN / DRAFT; do not close or merge. The documentation is now reconciled to G0 evidence; ancestry is mergeable-clean but remains historically divergent. Any rebase/retarget is optional history cleanup, not a correctness prerequisite shown by GitHub's mergeability check.


## 2026-11-05 — User operating directives: implementation + repository cleanup in parallel

This section records the latest user direction and takes precedence over older conflicting workflow and sequencing statements in this handoff.

### Delivery and repository strategy

- Work in an integrated loop: implement the next justified capability while cleaning and restructuring the repository around that same work. Do not postpone all implementation until a separate repository-wide cleanup is finished.
- For each implementation increment, inspect and clean the directly related structure: duplicate code/files, obsolete paths, stale documentation, unnecessary dependencies, unclear module boundaries, dead workflows, and redundant tests. Keep cleanup scoped to the active workstream and preserve historical evidence.
- Branches and pull requests are allowed when they improve isolation, reviewability, rollback, or parallel work. They are not prohibited. Control divergence deliberately: define one clear scope per branch/PR, choose the correct current base, avoid multiple branches/PRs implementing the same objective, keep dependent work ordered, regularly reconcile with the integration/base branch, and record head/base SHAs. Prefer continuing an existing branch/PR when it remains the right home; create a new one when separation materially reduces risk. Do not merge until checks/review and explicit user approval are satisfied.
- Preserve progress: do not restart or replace working foundations merely for stylistic consistency. Reuse tested components and migrate incrementally with regression coverage.
- Before deleting, closing, moving, or replacing anything, verify references, dependency/consumer usage, Git ancestry, CI ownership, and whether the item is a unique evidence artifact. Age or apparent overlap alone is not sufficient.
- Implementation and cleanup must both be testable. Add/update regression tests for behavior changes; documentation-only changes must be identified as such and must not be represented as code validation.
- After every meaningful increment, update this handoff or the relevant evidence report with scope, files, test commands/results, exact source SHA, workflow run and artifact identity where applicable, status, remaining limitations, and next action. Commit to the appropriate existing or newly created task branch. Do not claim unobserved tests or runtime behavior.

### Source hosting and action execution policy

- GitHub is the canonical repository and durable storage for source, documentation, plans, evidence, and session handoffs.
- GitHub Actions is the default CI/automation runner. Codemagic is an optional alternative only when it offers a meaningful cost saving or GitHub Actions usage/cost limits make it preferable for the specific workflow. Do not default to Codemagic and do not migrate solely for consistency.
- This is not permission to migrate, remove, disable, or duplicate existing workflows automatically. Before changing CI ownership, inspect the current workflow graph and record the exact reason, affected workflows, parity gaps, and rollback path. Keep historical workflows/evidence archived where useful.
- **Current T0 phase-specific approval:** the currently approved isolated T0 test phase uses GitHub Actions; VPS is design/research only. Codemagic may be proposed only with a concrete cost comparison and phase-specific approval before switching this T0 workflow.
- For every run, distinguish source branch/head SHA from the checked-out SHA (including synthetic merge SHA), and record run ID/event, job conclusions, artifact ID/name/digest, test counts, skips, and verification limitations.
- Do not create dummy commits solely to trigger a workflow. If no authorized trigger is available, record BLOCKED/NOT RUN and continue with read-only analysis or a concrete test-gap plan.

### Phase gates and change authority

- Existing restrictions are defaults for the current phase, not permanent bans. At each phase boundary, propose only the specific limit changes needed for the next stage, with purpose, benefit, risks, prerequisites, acceptance tests, rollback, and architecture/data-ownership impact.
- A phase proposal is not authorization. Apply a restriction change only after explicit user approval for that change. Approval for one phase does not authorize the next phase.
- Current T0 phase: isolated tests through GitHub Actions are allowed; VPS investigation/design only. Do not create/open canonical T0 DB, start Feeder, connect to an exchange, sync exchange market data, deploy on PC/VPS, or change canonical ownership without separate approval.
- Preserve the T0 independent data-asset boundary and fail-closed writer/lease fencing. Never use production or canonical storage for tests; use isolated temporary databases and synthetic/test data.
- Preserve paper-only behavior: no live trading, real orders, or exchange execution; keep `ai_execution_enabled=false`.
- Android-first remains a product priority. Infrastructure choices must be justified by reliability and evidence, not commercialization speed.

### Active state at this handoff update

- Repository: `kenznguyen/btcusdt-telegram-signals2`.
- PR #134: OPEN / DRAFT / NOT MERGED; head branch `feature/t0-atomic-write-fencing-20261105`; head SHA `ee291c4d4a179f91b93a9d3f378d4c7a1e2df741`; base branch `feature/t0-centralized-data-feeder-p1-20261101`. Do not merge without explicit approval.
- Latest recorded T0 Gateway CI run: `41996998169`; pull_request event; checked-out synthetic merge SHA `7f3be0e5da5fcade121c7526d367eab157237f3a`; PR head `ee291c4d4a179f91b93a9d3f378d4c7a1e2df741`. Result: 10 Gateway contract tests PASS, 54 focused regression tests PASS, 175 market_data tests PASS, 8 TimescaleDB integration tests skipped. Artifact ID `13400124790`, GitHub digest `sha256:33166350b71e67f3c40fb7e208bba26b945861421509c9a377111fa8971118a9`. Artifact payload bytes have not been independently re-hashed in this run.
- Evidence interpretation: PASS applies to the recorded CI synthetic merge context and test suites only. Direct current-head push run is not established; TimescaleDB integration, production runtime, 24/7 operation, canonical ingestion, and production readiness remain NOT VERIFIED / NOT AUTHORIZED.
- Current T0 test permission does not authorize canonical DB creation, Feeder startup, exchange access, market-data sync, or VPS/PC deployment.
- This handoff update is documentation-only. No source code, workflow, tests, database, runtime, Feeder, exchange, or deployment was changed or run by this update.

### Next integrated work loop

1. Read this handoff and inspect the actual active branch/PR state before each new session.
2. Select one concrete T0 acceptance gap; inspect its implementation, callers, tests, and related docs before editing.
3. Implement the smallest behavior change and perform adjacent repository cleanup in the same increment, without removing unique historical evidence.
4. Run only the authorized isolated GitHub Actions workflow for the current T0 phase. If triggering is unavailable, do not fabricate a run; record the blocker and prepare the exact test gap for the next authorized run.
5. Reconcile logs/artifacts against exact source and checkout SHAs; record PASS/BLOCKED/NOT VERIFIED separately.
6. Update this handoff/evidence on the existing relevant branch, preserve open PR dependencies, and do not merge or broaden phase permissions without explicit approval.


## 2026-11-05 — PR #111 superseded disposition (owner-approved)

- PR #111 was compared against PR #134 before disposition.
- PR #111 head: `65f8baa1e198666f7cb6da2600505947665a9a78`; base: `a58b6163a78861ecf5bb7d2c8fc11aa420142837`. Scope: 10 static RED contract tests, one scope document, and a manual Codemagic-only runner; no production Gateway implementation.
- PR #134 head at disposition: `ee291c4d4a179f91b93a9d3f378d4c7a1e2df741`; base: `8b196d2720eab804728df7c0227c606c094b16ad`. Scope includes the evolved 10-test contract suite, Gateway implementation, caller routing, regression coverage, evidence report, and GitHub Actions workflow.
- The two test files are not byte-identical. PR #134's version updates the recovery contract target to `market_data/feeder_service.py` and reflects the active implementation. The suite passed 10/10 in run `41996998169` on synthetic merge checkout `7f3be0e5da5fcade121c7526d367eab157237f3a`; this is merge-context evidence, not a direct-head-only run.
- Owner approved closing the superseded PR. PR #111 is now **CLOSED / NOT MERGED**: https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/111
- Closure rationale and evidence were added to the PR discussion (comment ID `6654250071`). The head branch `feature/t0-single-writer-gateway-red-20261102` is preserved; no branch deletion, rebase, retarget, or merge occurred.
- PR #134 remains **OPEN / DRAFT / NOT MERGED** at head `ee291c4d4a179f91b93a9d3f378d4c7a1e2df741`. Do not merge without separate explicit approval.
- No tests or workflows were run as part of this closure/documentation increment. No canonical DB, Feeder startup, exchange connection, market-data sync, PC/VPS deployment, or live execution was performed.
- Disposition: PR #111 **SUPERSEDED / CLOSED**; PR #134 remains the active implementation line. Remaining verification limits for #134 are unchanged: direct-head-only current SHA run NOT VERIFIED, 8 TimescaleDB integration tests skipped, artifact payload bytes not independently re-hashed, and production/canonical runtime NOT VERIFIED / NOT AUTHORIZED.


## 2026-11-05 — PR #134 TimescaleDB integration test contract review

- Read-only review performed against PR #134 branch `feature/t0-atomic-write-fencing-20261105`, head `ee291c4d4a179f91b93a9d3f378d4c7a1e2df741`.
- Relevant source identities:
  - `market_data/postgres.py`: blob `c7cd2120a2117af70029195a084a98a8b9e54e43`; `PostgresCandleStore` is explicitly read-only and exposes no `insert()`.
  - `market_data/test_timescaledb.py`: blob `d1cf413bae59e6b61699f861f4b75243de1f4879`; still calls `PostgresCandleStore.insert()` and passes the Postgres adapter to `sync_window()` as a writer.
  - `.github/workflows/t0-single-writer-gateway-red.yml`: blob `9f03dc9bc0c6df62942bf6d384bb1ff294e6d5b2`; installs `requirements-web.txt`, runs the full market_data suite, and does not provision a TimescaleDB service.
- Finding: the 8 TimescaleDB integration tests skipped in run `41996998169` are not merely unexecuted; the checked-in integration module still targets the former writable PostgreSQL adapter. Enabling its DSN against the current read-only adapter is expected to fail at missing `insert()`; this expectation is based on static inspection and has NOT been runtime-tested.
- Safety finding: the current integration fixture calls `migrate(DSN)`, inserts/deletes candle rows, and temporarily changes/restores a migration checksum. The test module does not independently enforce that DSN is disposable. A wrong DSN could mutate a non-test database. Do not enable `MARKET_DATA_REQUIRE_TIMESCALE=1` or provide a DSN to the existing module.
- Review comment recorded on PR #134: https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/134#issuecomment-6654284161
- Required next increment: rewrite integration tests for the read-only PostgreSQL adapter; provision a pinned, ephemeral TimescaleDB service in GitHub Actions; enforce a disposable test target and isolated setup/teardown; add explicit no-write assertions. Keep PostgreSQL canonical writes disabled.
- Status: **REQUIRED / NOT VERIFIED**. No source/workflow files changed and no tests/workflows were run during this review. No canonical DB, Feeder, exchange, market-data sync, deployment, or live execution was touched.


## 2026-11-05 — PR #134 TimescaleDB read-only integration test rewrite

- Work continued on the existing PR #134 branch; no new branch or PR was created.
- Branch: `feature/t0-atomic-write-fencing-20261105`.
- Latest source commit: `61e4deefa463afd2d42ec06c6a6a6eb91ae305cb`.
- Changed file: `market_data/test_timescaledb.py`; latest blob SHA `59f8ca223b1cd7e580afed18e0be0d0fb0e72ea4`.
- The previous integration tests called `PostgresCandleStore.insert()` and passed the PostgreSQL adapter to the ingestion writer, contradicting the current read-only adapter. The test module was rewritten to verify read-only adapter behavior, exact decimal/gap/as-of reads, read-only transaction rejection, hypertable/migration consistency, checksum mismatch recovery, and API 503 behavior.
- The new test fixture requires `MARKET_DATA_TEST_DISPOSABLE=1`, loopback host, port 5432, and exact test user/database `t0_test`; it rejects configured canonical storage, paper execution, and exchange credentials. Direct SQL is limited to fixture seeding/cleanup in the dedicated test database. The production PostgreSQL adapter remains read-only.
- GitHub Actions run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42001626017; run ID `42001626017`, event `pull_request`, PR head `61e4deefa463afd2d42ec06c6a6a6eb91ae305cb`, checked-out synthetic merge SHA `c9494d6101056d8c1d6a0c525b27e2e3a6a0f04c`, conclusion SUCCESS.
- Results: 173 market_data tests PASS; 6 rewritten TimescaleDB integration tests SKIPPED because the workflow did not provision the dedicated service/DSN. This is not TimescaleDB acceptance. No direct-head run is established.
- Artifact: ID `13402093837`; name `t0-swg-contract-evidence-c9494d6101056d8c1d6a0c525b27e2e3a6a0f04c`; GitHub digest `sha256:bc3cfbed5801ccb759705799dacec716bc5ac926c805698e4d2906965ea8eaf9`. Payload bytes have not been independently downloaded/re-hashed.
- PR #134 discussion review comment `6654284161` was updated with the corrected finding and current CI evidence.
- The attempted GitHub Actions workflow service-job update was blocked; no workflow file was changed. Current workflow remains blob `9f03dc9bc0c6df62942bf6d384bb1ff294e6d5b2`.
- Status: test contract rewrite **COMMITTED / CI MERGE-CONTEXT PASS**; TimescaleDB runtime integration **BLOCKED / NOT VERIFIED**; direct PR-head-only run **NOT VERIFIED**.
- Next: resolve the workflow-change blocker and add a pinned, ephemeral TimescaleDB service job on GitHub Actions; run all six integration tests on the exact resulting PR head and record the checkout SHA separately. Do not use canonical DB or enable production writes. Keep T0 phase permissions, GitHub Actions default, `ai_execution_enabled=false`, and paper-only boundaries unchanged.


## 2026-11-05 — Disposable TimescaleDB CI acceptance

- Owner approved the isolated TimescaleDB CI job only. No permission was granted for canonical DB, Feeder startup, exchange access, market-data sync, deployment, or live execution.
- Existing PR #134 branch only; no new branch/PR and no merge.
- Workflow commit: `fcb62d800943e898cdccf9f59b8b4bd32cd5087a`; workflow blob: `f1d61ea83ac2bac31c5fccbcaf8086ad33e94af6`.
- Added a dependent GitHub Actions job using `timescale/timescaledb:2.17.2-pg16`, dedicated disposable loopback test DB/user `t0_test`, explicit disposable-target checks, and cleared canonical/paper/exchange environment settings. The six PostgreSQL tests exercise the read-only adapter; SQL writes are limited to isolated fixture setup/teardown.
- Updated `market_data/README.md` to state GitHub Actions is the default CI. Documentation-only commit: `f528beaf0d4d0b130c3e5826c7d9eb05a67f53ab`; blob: `340584fc8acecea01bef1c0de4eda4ced4fe419a`.
- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42002260231 (run ID `42002260231`), SUCCESS. PR source head at run: `fcb62d800943e898cdccf9f59b8b4bd32cd5087a`; checked-out synthetic merge SHA: `256348e1c2a1f70a170bdacbf49ec3d4710bf802`; base SHA: `8b196d2720eab804728df7c0227c606c094b16ad`.
- Results: 10/10 Gateway contracts PASS; 54/54 focused Gateway/Feeder tests PASS; 173/173 market_data tests PASS; 6/6 TimescaleDB integration tests PASS. The disposable service was stopped/removed at job completion.
- Artifacts: Timescale ID `13402754440`, digest `sha256:45526a1fbf67512dd7848838136090aa763bce38f006b67d30c40bf11dffe6f6`; Gateway ID `13402833162`, digest `sha256:cbb8f5467cec6e42703a58f64c4f34ffe86ac9b1bed03b34af769266a18482ff`. Artifact payload bytes not independently re-hashed.
- The only commit after the tested source head is the README-only commit above; GitHub compare confirms only `market_data/README.md` changed. Latest PR head is `f528beaf0d4d0b130c3e5826c7d9eb05a67f53ab`; a separate run on this docs-only head is NOT VERIFIED.
- PR #134 remains OPEN / DRAFT / NOT MERGED. Its review comment `6654284161` records the completed acceptance.
- Status: isolated TimescaleDB integration PASS; focused and full market_data regression PASS; latest docs-only head run NOT VERIFIED; artifact byte re-hash NOT VERIFIED; production/canonical runtime NOT VERIFIED / NOT AUTHORIZED.
- Next: continue isolated review/testing of T0 health/readiness and process-level restart/fencing. Do not create/use canonical DB, start Feeder, connect exchange, sync market data, deploy PC/VPS, enable live execution, or merge PR #134 without separate explicit approval.


## 2026-11-05 — T0 Health/Readiness and process-level SIGKILL acceptance

- Continued on the existing PR #134 branch `feature/t0-atomic-write-fencing-20261105`; no new branch/PR, no merge.
- Latest source commit: `5ae66d28ed583d7cb16891d27aa6dd1c057260d0`; PR base SHA: `8b196d2720eab804728df7c0227c606c094b16ad`; PR remains OPEN / DRAFT / NOT MERGED.
- Added `market_data/test_feeder_process_restart.py`, blob `1e7df1c0a97d186bae73bae3778555c2c930f09b`. This uses a child Python process and temporary SQLite DB. Child commits one candle through `SQLiteWriteGateway`, begins a second uncommitted SQLite transaction and pauses. Parent sends SIGKILL. After recovery, test verifies first committed candle survives, uncommitted row is rolled back, a replacement owner takes lease with incremented generation, stale owner cannot release or write, replacement writer succeeds, and duplicate write is idempotent. This is an isolated DB/process crash test, not a real Feeder service restart.
- Workflow blob `b462e72554db7eb0e6ee46bf8aadc0f997975518`; explicit steps now run Health/Readiness and process-level SIGKILL tests.
- Exact-head push run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42003658527; run ID `42003658527`; event push; source SHA `5ae66d28ed583d7cb16891d27aa6dd1c057260d0`; conclusion SUCCESS. Job IDs: Gateway `127165136878`, TimescaleDB `127165347207`; both SUCCESS.
- PR merge-context run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42003666364; run ID `42003666364`; event pull_request; PR head `5ae66d28ed583d7cb16891d27aa6dd1c057260d0`; synthetic merge checkout SHA `46073cff84a4e7d24d5a8b05cf90e4227b054ffc`; base `8b196d2720eab804728df7c0227c606c094b16ad`; conclusion SUCCESS. Job IDs: Gateway `127165167606`, TimescaleDB `127165262504`; both SUCCESS.
- Both CI contexts: Gateway static contracts 10/10 PASS; focused Gateway/store/sync/storage/Feeder lifecycle regression 54/54 PASS; Health/Readiness 20/20 PASS (includes `test_startup_in_progress_is_not_ready`); SIGKILL process restart test PASS; complete `market_data` suite 174 PASS, 6 skipped in this job; separate disposable TimescaleDB job 6/6 PASS.
- Direct-head artifacts: Gateway ID `13403124094`, digest `sha256:81cf8c30896e1f16499333505bd45254ff215b891d0e0cb2cfdd4f4e47576734`; TimescaleDB ID `13404500394`, digest `sha256:7fc00da6ffe6415f4b3b49834eb88b0947267233411b491e1aaaef6be0684b7a`.
- PR merge-context artifacts: Gateway ID `13403966291`, digest `sha256:73911f2848e36b0e830d961ed4e768de68f33aa7bf09872e3908bb4a877b7052`; TimescaleDB ID `13402994447`, digest `sha256:d3bac110ca7c8319723b5f4972645126cf12215dd61c99182b6eeb2d693771ae`. Artifact payload bytes not independently downloaded/re-hashed.
- Initial implementation run exposed a test-script nested-quote SyntaxError; corrected before final head. A later ResourceWarning from subprocess pipes was also corrected. Final exact-head and PR merge-context runs have no test failures or ResourceWarnings.
- PR description and existing review evidence comment `6654284161` updated with the new acceptance results and limits.
- Status: Health/Readiness **PASS**; isolated SQLite process SIGKILL rollback + lease takeover/stale-writer fencing **PASS**; full market_data regression **PASS**; TimescaleDB disposable integration **PASS**. Actual FeederRuntime service restart/24-7 operation, Android canonical host integration, production DB restore and canonical ingestion **NOT VERIFIED / NOT AUTHORIZED**.
- Next safe increment: inspect actual `FeederRuntime` composition/lifecycle in a subprocess using only temporary SQLite and fake exchange/scheduler boundaries, then test readiness transitions across startup, lease loss and restart. Do not create canonical DB, start production Feeder, connect exchange, sync market data, deploy PC/VPS, enable live execution, or merge PR #134 without separate explicit approval.


## 2026-11-05 — Actual FeederRuntime subprocess restart + startup readiness correction

- Continued on the existing PR #134 branch; no new branch/PR and no merge.
- Latest PR head: `451d7b14ff6dcaed63af7067b54c557203b5a04a`; base: `8b196d2720eab804728df7c0227c606c094b16ad`; PR OPEN / DRAFT / NOT MERGED.
- New health finding: a real `FeederRuntime.health_snapshot()` in NEW/STARTING has no valid lease yet. The evaluator previously appended DEGRADED for missing lease, causing STARTING to be reported as DEGRADED. Fixed `market_data/feeder.py` blob `d74d1b7a7890d3d0de7fd7d1278aa8976aac29f9`: missing/lost lease degrades health only after `startup_complete=true`. Readiness still requires startup complete, valid lease, healthy storage and fresh complete timeframes. Added `test_startup_before_lease_acquisition_is_starting_and_not_ready` in `market_data/test_feeder_health.py`, blob `80e0b7d042c821d4814d626b69c3196853dc49d9`.
- Extended `market_data/test_feeder_process_restart.py`, blob `7600225b7e9be8137ddeadf61b1ba347be0a71ce`, with a second subprocess test using actual `FeederRuntime`, `FeederScheduler`, `LeaseStore` and `HealthEvaluator`. Child confirms NEW => STARTING/live/not-ready and RUNNING => HEALTHY/live/ready, then is SIGKILLed. Parent starts replacement runtime after lease expiry, verifies fencing generation increments, readiness becomes healthy only after start, clean stop reports STOPPED and releases lease. Uses temporary SQLite and inert sync callbacks; no exchange, data sync or canonical DB.
- Previous run `42004439055` failed the new real-runtime assertion because startup-before-lease was DEGRADED. Root cause fixed; no tests skipped or weakened. Final runs below verify the corrected behavior.
- Exact-head push run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42004594376; run ID `42004594376`; source SHA `451d7b14ff6dcaed63af7067b54c557203b5a04a`; SUCCESS. Jobs `127168055235` (Gateway/static) and `127168181700` (TimescaleDB) both SUCCESS.
- PR merge-context run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42004604915; run ID `42004604915`; PR source head `451d7b14ff6dcaed63af7067b54c557203b5a04a`; synthetic merge checkout SHA `fcc4c52dbc983b1f10580acd03c991c541863863`; base `8b196d2720eab804728df7c0227c606c094b16ad`; SUCCESS. Jobs `127168091144` and `127168184951` both SUCCESS.
- Both contexts: 10 Gateway contracts PASS; 54 focused Gateway/Feeder regressions PASS; 21 Health/Readiness tests PASS; 2 process-level restart tests PASS; complete `market_data` suite 176 PASS / 6 skipped in the static job; separate disposable TimescaleDB integration 6/6 PASS.
- Exact-head artifacts: Gateway `13404606206`, digest `sha256:3b6933ec2eed8322e12f672166238ce55c65b9ba8a91e0119aab4f08f5fa3454`; TimescaleDB `13403508214`, digest `sha256:7783d7aa2b96727dd2c1d5ad50b384764c983f67daf782fda234a07257b03bce`.
- PR merge-context artifacts: Gateway `13404277206`, digest `sha256:28d06787a3f92f1ca0c138c8b44ad7a8bba3fdd42d8749da2691266e33f3e747`; TimescaleDB `13404302111`, digest `sha256:03dc251ae020966b8e0e3462fdaa2474d93d0c8672cd2ef40a0bceb6c7ba8795`. Artifact bytes not independently downloaded/re-hashed.
- PR description and review comment `6654284161` updated with the correction and current evidence.
- Status: startup Health/Readiness semantics **PASS**; isolated SQLite crash rollback + stale-generation fencing **PASS**; actual FeederRuntime/Scheduler subprocess restart and readiness transition **PASS**; full market_data regression **PASS**; disposable TimescaleDB integration **PASS**. Actual `build_runtime()` with exchange adapter, canonical DB restore, production service supervision, 24/7 operation and deployment remain **NOT VERIFIED / NOT AUTHORIZED**.
- Next safe increment: exercise `build_runtime()` composition with temporary SQLite, synthetic candles and a fake exchange/sync boundary; verify startup recovery must finish before readiness, scheduler/recovery share the same fenced Gateway, and restart recovery remains complete. Keep all external exchange access and canonical ingestion disabled. Do not deploy PC/VPS or merge PR #134 without separate explicit approval.


## 2026-11-05 — build_runtime real SQLite recovery + readiness acceptance

- Continued on existing PR #134 branch `feature/t0-atomic-write-fencing-20261105`; no new branch/PR and no merge.
- Latest PR head SHA: `880c31a3833a23f804b3294f8fbd2638b7441d7f`; base SHA: `8b196d2720eab804728df7c0227c606c094b16ad`; PR remains OPEN / DRAFT / NOT MERGED.
- Added `RuntimeIntegrationContractTest.test_build_runtime_recovers_real_temp_sqlite_before_readiness_and_reuses_gateway` in `market_data/test_feeder_lifecycle.py`, blob SHA `13a33ba79406b8ef54274a88d871b608033955b5`. Test uses actual `SQLiteCandleStore`, `LeaseStore`, `build_runtime()`, `RecoveryAdapter`, `RecoveryCoordinator`, `sync_window()` and `SQLiteWriteGateway`, with a temporary SQLite DB and a synthetic Binance-compatible exchange object; no network/credentials.
- The fake exchange blocks the recovery fetch. While blocked, runtime remains STARTING/live/not-ready. Once released, recovery fetches and commits one closed candle through the actual fenced Gateway, re-reads storage and verifies complete coverage, then runtime becomes RUNNING/HEALTHY/ready. Test manually exercises the scheduler callback against the same window; captured Gateway object identity is identical to recovery's Gateway, duplicate write returns 0, and clean stop releases the lease.
- Workflow `.github/workflows/t0-single-writer-gateway-red.yml` blob SHA `66681e9543e285a96719dbf288c3b8245fac57e8` now retains `t0-health-readiness-tests.log` and `t0-process-restart-tests.log` in the Gateway evidence artifact, in addition to the existing full-suite logs.
- Exact-head push run https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42006453406; run ID `42006453406`; source SHA `880c31a3833a23f804b3294f8fbd2638b7441d7f`; SUCCESS. Gateway job `127174300774`, TimescaleDB job `127174436844`, both SUCCESS.
- PR merge-context run https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42006462698; run ID `42006462698`; PR source head `880c31a3833a23f804b3294f8fbd2638b7441d7f`; synthetic merge checkout SHA `e00f81c6ddd21444525391df54fb2d65d725877a`; base `8b196d2720eab804728df7c0227c606c094b16ad`; SUCCESS. Gateway job `127174332991`, TimescaleDB job `127174466081`, both SUCCESS.
- Both contexts: Gateway contracts 10/10 PASS; focused Gateway/Feeder regressions 55/55 PASS; Health/Readiness 21/21 PASS; process restart 2/2 PASS; complete `market_data` suite 177 PASS / 6 skipped; separate disposable TimescaleDB read-only integration 6/6 PASS.
- Exact-head artifacts: Gateway ID `13405505290`, digest `sha256:cd50171bc32e1f48050f82cce19832f3e55e7f9599fdb3e470f090b60f8913db`; TimescaleDB ID `13404444438`, digest `sha256:508e1859e78c4ee34f7a27648ab7d53c7ddc310067c1319b9cf53cef851a1963`.
- PR merge-context artifacts: Gateway ID `13405001863`, digest `sha256:4b6bb267b722367da6192dcc1d75b5c2bcbea6b5bce17d1bbad3423b9c492cd6`; TimescaleDB ID `13404529152`, digest `sha256:8fc7cf3c0ad4f3bcd33594d7d473f8a2c9a2f019b197b6a2b713c91623fae449`. Artifact bytes not independently downloaded/re-hashed.
- Compared with previous tested head `451d7b14...`, this increment modifies only `market_data/test_feeder_lifecycle.py` and adds two workflow artifact paths; no production runtime code changed.
- Status: real build_runtime startup recovery on temporary SQLite/synthetic exchange **PASS**; readiness withheld during blocked recovery **PASS**; scheduler/recovery share exact Gateway instance **PASS**; duplicate idempotence **PASS**; graceful stop/lease release **PASS**; full regression and TimescaleDB disposable CI **PASS**.
- Limits: synthetic exchange does not prove real Binance connectivity, rate-limit behavior or real-market correctness. Canonical DB, real exchange, production Feeder service, PC/VPS deployment and 24/7 operation remain **NOT VERIFIED / NOT AUTHORIZED**.
- Next safe increment: fail-closed startup acceptance for incomplete recovery and lease loss during a recovery page; verify readiness never opens and lease is retained/released only according to the existing lifecycle rules. Continue isolated temporary DB/synthetic data only. No canonical DB, real exchange, deployment or merge.


## Fail-closed startup recovery and lease takeover acceptance — 2026-11-05

- PR head: `14dfa54c49cf6713954c783ccf18d64e104dcb26`; base: `8b196d2720eab804728df7c0227c606c094b16ad`; branch `feature/t0-atomic-write-fencing-20261105`; PR #134 remains OPEN / DRAFT / NOT MERGED.
- Scope changed only three files relative to previously tested head `880c31a3833a23f804b3294f8fbd2638b7441d7f`: `market_data/feeder.py`, `market_data/feeder_service.py`, and `market_data/test_feeder_lifecycle.py`.
- Added `test_build_runtime_incomplete_recovery_never_opens_ready_and_releases_idle_lease`: real `build_runtime()`, `SQLiteCandleStore`, `LeaseStore`, recovery coordinator and HealthEvaluator use a temporary SQLite database plus an empty synthetic exchange. Unresolved coverage raises `RecoveryIncompleteError`; runtime remains FAILED/not-ready, scheduler never starts, and its idle lease generation is released.
- Added `test_build_runtime_lease_takeover_between_recovery_pages_blocks_next_write_and_ready`: two distinct recovery gaps are seeded in temporary SQLite. The first synthetic recovery page commits, then a replacement owner takes the expired lease. The next page's heartbeat is rejected before any exchange fetch/write. Runtime records LEASE_LOST, readiness remains false, only the first page is written, and the replacement owner's generation remains current.
- Runtime correction: a failed/exceptional recovery lease heartbeat calls `on_lease_lost()` immediately. If startup cleanup then cannot release its exact owner/generation, it preserves LEASE_LOST instead of leaving the runtime in STARTING or releasing another owner's lease.
- TDD evidence: initial RED runs exposed the missing LEASE_LOST transition (`STARTING` persisted after replacement takeover). A test-fixture market key mismatch was corrected; tests were not skipped or weakened.
- Exact-head push run [#42008186782](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42008186782): SUCCESS on source SHA `14dfa54c49cf6713954c783ccf18d64e104dcb26`; Gateway job `127180175263`, TimescaleDB job `127180352476`, both SUCCESS.
- PR merge-context run [#42008449494](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42008449494): SUCCESS; PR source head `14dfa54c49cf6713954c783ccf18d64e104dcb26`; synthetic merge SHA `b43b6a35c110d3dfeaade87600d246d4c18f2430`; base `8b196d2720eab804728df7c0227c606c094b16ad`. Jobs `127181053375` and `127181178227`, both SUCCESS.
- Both CI contexts: Gateway contracts 10/10 PASS; focused Gateway/Feeder lifecycle tests 57/57 PASS; Health/Readiness 21/21 PASS; process restart 2/2 PASS; full `market_data` suite 179 PASS / 6 SKIPPED; disposable TimescaleDB read-only integration 6/6 PASS.
- Exact-head artifacts: Gateway ID `13404998362`, digest `sha256:99cd71cc6017e639ff87b2fcb06f54f70f2731238d3eca1b0d8159c6370409a1`; TimescaleDB ID `13406410855`, digest `sha256:da6597cb6d477c7b51c0cd2346f90d6f2e2bfa0672d96154e830955748f6c895`.
- PR merge-context artifacts: Gateway ID `13405582111`, digest `sha256:0b78ac34568843a212968afc1d8f671df25a34a2a758772e4d2fec4f188eba5e`; TimescaleDB ID `13405677160`, digest `sha256:7c47918a49b0db34b797cd161925c2e21b4953bd5e57b1dbe372b73bceae0fb8`. Artifact bytes were not independently downloaded/re-hashed.
- Status: incomplete recovery fail-closed **PASS**; lease takeover between recovery pages / no subsequent write **PASS**; replacement lease preserved **PASS**; readiness remains closed **PASS**; exact-head and PR merge-context CI **PASS**.
- Limits: synthetic exchange and temporary SQLite do not verify live exchange behavior, canonical DB, production Feeder operation, 24/7 reliability or PC/VPS deployment. All remain **NOT VERIFIED / NOT AUTHORIZED**. No real exchange, canonical DB, deployment or live execution was used.
- Next: perform a focused code review of startup failure/lease-loss cleanup and consider a separate isolated test for lease expiry during an in-flight SQLite write transaction. Do not merge PR #134 or activate canonical ingestion without separate explicit approval.


## Atomic SQLite expiry rollback and concurrent lease takeover — 2026-11-05

- PR #134 branch `feature/t0-atomic-write-fencing-20261105`; source head `a569eb6248cd53252fcf32065482921fc4c8ffcd`; base `8b196d2720eab804728df7c0227c606c094b16ad`. PR remains OPEN / DRAFT / NOT MERGED.
- Test-only increment: `market_data/test_fenced_store.py` blob `0573d0728f3e62a95b8d2a4f16359e33dd4789b4`. Compare from prior accepted head `14dfa54c49cf6713954c783ccf18d64e104dcb26`: 2 commits ahead, 0 behind; only this test file changed (70 additions, 1 deletion). No runtime code or workflow changed.
- Added `test_expiry_during_gateway_transaction_rolls_back_before_takeover`: temporary SQLite only. Writer A enters `BEGIN IMMEDIATE`, inserts a candle in an uncommitted transaction, and synthetic time expires its lease before commit. Writer B attempts takeover while A holds the transaction. Gateway rejects A at the commit-time lease check and rolls back; only after rollback can B acquire the next generation. Assertions prove no partial candle remains, B's lease is current, and stale A is not current.
- Focused review of `SQLiteWriteGateway.write_batch()`: same SQLite database is enforced at construction; `BEGIN IMMEDIATE` serializes takeover against the writer; owner/generation/expiry are checked inside the transaction before inserts and again before commit; exceptions rollback the batch. Existing takeover serialization test covers successful commit. No production-code finding required in this scoped review; this is not a complete T0 security or production-readiness audit.
- Initial CI attempt at `4fd9bc12baa9acc37af8bc1041aaf81bea681c18` failed because the new test omitted the `read_window` import (NameError). Corrected in commit `a569eb6248cd53252fcf32065482921fc4c8ffcd`; no assertions were weakened.
- Exact-head push run [#42009482638](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42009482638): SUCCESS on source SHA `a569eb6248cd53252fcf32065482921fc4c8ffcd`; Gateway job `127184539099`, TimescaleDB job `127184669634`, both SUCCESS.
- PR merge-context run [#42009489878](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42009489878): SUCCESS; source head `a569eb6248cd53252fcf32065482921fc4c8ffcd`; base `8b196d2720eab804728df7c0227c606c094b16ad`; synthetic merge prefix `bd3b174c11fa46e44885e87a2a1a0fe92faa3dc2`. Gateway job `127184562761`, TimescaleDB job `127184670256`, both SUCCESS.
- Both contexts: Gateway contracts 10/10 PASS; focused Gateway/Feeder 58/58 PASS; Health/Readiness 21/21 PASS; process restart 2/2 PASS; full `market_data` suite 180 PASS / 6 SKIPPED; disposable TimescaleDB read-only integration 6/6 PASS.
- Exact-head artifacts: Gateway ID `13406357160`, digest `sha256:f63fc1deb3d70a92f5f44329a46fcedc342e0277a8b3dc593ad7ba13ccb3c7e3`; TimescaleDB ID `13406222752`, digest `sha256:5907fa342b8f3aca392465f17880b245ee662cecfb9b554141f936442bf1f771`.
- PR merge-context artifacts: Gateway ID `13406636016`, digest `sha256:97602f2725466ed4cb901a4346a0f60114c92afd23d22e166d3ce10271f7d76f`; TimescaleDB ID `13406730977`, digest `sha256:81b1efcecd4e620f9f9ee0345ccf295ea6bd3ae48248f177c86bf80b75584e1a`. Artifact bytes not independently downloaded/re-hashed.
- Status: in-flight transaction expiry rejection and full rollback PASS; concurrent takeover blocked until transaction rollback PASS; replacement generation preserved PASS; exact-head and PR merge-context CI PASS.
- Limits: isolated temporary SQLite and synthetic time/data only. No canonical DB, real exchange, production Feeder, PC/VPS deployment, or live execution. NOT VERIFIED / NOT AUTHORIZED. No merge without separate explicit approval.
- Next: inspect the independent Paper Writer Isolation Gate (SWG-F) RED contract and its boundaries against T0 lease authority; do not implement or activate a writer gate before reviewing its existing acceptance tests.


## SWG-F / T0 authorization-boundary review — 2026-11-05

- Read-only review only; no source/runtime code changed. Reviewed `paper_execution/writer_gate.py`, `paper_execution/test_writer_gate_runtime.py`, `paper_execution/test_ledger_writer_isolation.py`, `paper_execution/PAPER_WRITER_ISOLATION_RED.md`, and T0 `market_data/test_feeder_atomic_fencing.py`.
- Confirmed separate authorization/storage domains in source: SWG-F has a dedicated Paper coordinator sidecar, lock file and `paper_only` generation-bound non-serializable `WriterToken`; its writer transaction requires the configured PAPER_DB path and read/write-opens only that existing Paper DB. T0 canonical candle writes use a separate SQLite CandleStore + LeaseStore path and owner/generation/expiry fencing. No source import or runtime API coupling between the Paper gate and T0 Lease was found in the inspected paths.
- Existing RED contract explicitly requires proving both directions of isolation: Paper gate cannot authorize T0 writes and T0 lease capability cannot authorize Paper writes. The current P1-P3 acceptance suites exercise each subsystem independently but do not contain a direct cross-boundary negative test. **Boundary test coverage gap identified; implementation NOT VERIFIED.**
- SWG-F exact-head push run [#41989501714](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41989501714): SUCCESS on `d6465e073d7aade8ac60716db2ffef273334c5b0`; job `127118078360`. Counts from job log: P2 12/12, P3 API 31/31, Paper regression 59/59, process runtime 12/12; all PASS. Artifact `13397103329`, digest `sha256:4685944f45b5ffe5c06bfe5042bec39bc36dca2327387fe52e03bba17cffc3e9` (artifact bytes not independently downloaded/re-hashed).
- PR #112 remains OPEN / DRAFT / NOT MERGED; head `d6465e073d7aade8ac60716db2ffef273334c5b0`; base `a58b6163a78861ecf5bb7d2c8fc11aa420142837`. Compare against its declared base: 97 commits ahead, 0 behind. This is a separately scoped Paper workstream; do not merge or retarget it as part of T0 work.
- Windows and Android file-lock runtime semantics remain NOT VERIFIED. Linux CI success does not certify either platform.
- Proposed next increment requires explicit approval: add **test-only** cross-boundary negative acceptance in isolated temporary SQLite fixtures. Test that a PaperWriterGate token is rejected by T0 lease-fenced candle write and that a T0 lease capability is rejected by PaperWriterGate token validation; also assert separate database paths and no cross-domain writes. Run the focused T0 and SWG-F regression suites on GitHub Actions, record exact SHAs/artifacts. No production code, canonical DB, exchange, migration, deployment or live execution. This approval would authorize only isolated tests, not a new shared authority or merged integration.


## Cross-domain T0 / Paper writer isolation acceptance — 2026-11-05

- Scope approved by user: test-only cross-boundary negative acceptance. No production runtime code, schema, migration, canonical DB, exchange, deployment or live execution changed or accessed.
- Existing SWG-F branch retained: `feature/t0-paper-writer-isolation-red-20261102`; latest exact test source SHA `68ec3080fb0393e688ea8bcb99ef338d7ba393dd`. Increment is 2 commits ahead / 0 behind from prior reviewed SWG-F head `d6465e073d7aade8ac60716db2ffef273334c5b0`; changed files only `.github/workflows/paper-writer-isolation-red.yml` (+29/-1) and new `paper_execution/test_cross_domain_writer_isolation.py` (+155). No production code changed.
- Cross-boundary test pins T0 source SHA `a569eb6248cd53252fcf32065482921fc4c8ffcd` and verifies checkout SHA before testing. Paper gate is imported from the SWG-F branch; T0 LeaseStore/CandleStore/SQLiteWriteGateway are imported from the exact separate T0 source checkout. All paths are disposable temporary SQLite files.
- `test_paper_writer_token_cannot_authorize_t0_candle_writes`: positive control confirms the actual T0 lease generation writes a T0 candle. Replacing the T0 generation provider with a Paper WriterToken is rejected before write; the T0 DB remains at the positive-control candle only and PAPER_DB has no rows.
- `test_t0_lease_capability_cannot_authorize_paper_writer_gate`: positive control confirms a Paper token validates and Paper writer transaction can write PAPER_DB. Passing the real, current T0 Lease object to Paper token validation raises `WriterTokenInvalid`; PAPER_DB remains at the one positive-control row and T0 has no candles.
- Both tests assert resolved PAPER_DB and T0 DB paths are physically distinct. No cross-domain data write occurred. Result: both directions PASS.
- Exact-head GitHub Actions push run [#42011860956](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42011860956): SUCCESS on SWG-F source SHA `68ec3080fb0393e688ea8bcb99ef338d7ba393dd`; job `127192605334`. Exact T0 source checkout SHA `a569eb6248cd53252fcf32065482921fc4c8ffcd` verified in job.
- Exact-head job test results: PaperLedger P2 12/12 PASS; cross-domain negative acceptance 2/2 PASS; T0 Gateway/fencing regression 9/9 PASS; P3 API 31/31 PASS; Paper execution regression 59/59 PASS; SWG-F process runtime 12/12 PASS. All steps completed successfully.
- Artifact ID `13408205186`, name `paper-writer-isolation-p1-p3-green-68ec3080fb0393e688ea8bcb99ef338d7ba393dd`, digest `sha256:bee24bbcf58b94569138fec3325a733b8afabdb7375315a95543edcb08cd2a47`. Artifact bytes not independently downloaded/re-hashed.
- A PR merge-context run [#42011831972](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42011831972) succeeded on earlier head `559490b7776d23839dc224e131cf44ee7222c7fc`; because the base branch workflow predates the added checkout/test steps, the cross-boundary acceptance is evidenced by the exact-head push run above, not by that PR-context run.
- PR #112 remains OPEN / DRAFT / NOT MERGED; head `68ec3080fb0393e688ea8bcb99ef338d7ba393dd`; base `a58b6163a78861ecf5bb7d2c8fc11aa420142837`. It remains 99 commits ahead / 0 behind its declared base; do not retarget or merge as part of this test increment. PR #134 remains OPEN / DRAFT / NOT MERGED.
- Status: cross-domain capability rejection in both directions PASS; T0 Gateway regression PASS; SWG-F P2/P3/runtime regression PASS; separate DB paths PASS. Windows/Android lock semantics and production runtime behavior remain NOT VERIFIED.
- Next safe step: review the new test harness and workflow diff for import-path/source-pinning robustness, then decide whether a separately approved PR-base workflow alignment is needed to make PR merge-context CI execute the cross-boundary tests. No production integration or deployment is implied.


## Final source-pinned cross-domain verification — 2026-11-05

- Tightened the test harness to assert Python actually imported T0 modules from the pinned `T0_SOURCE_ROOT` and Paper WriterGate from the SWG-F checkout. This prevents same-named package shadowing on the CI runner. Test-only change; no production code.
- Final SWG-F source SHA: `bd1f658ab04ef119c82b8a84ea90f3555d3dd50e`. Pinned T0 source SHA: `a569eb6248cd53252fcf32065482921fc4c8ffcd`; both SHAs are emitted and checked in CI.
- Exact-head push run [#42012176347](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42012176347): SUCCESS; job `127193657644`.
- PR merge-context run [#42012185380](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42012185380): SUCCESS on the same source head; job `127193688722`. Unlike the prior run, this run executed the added checkout and cross-boundary steps in merge context.
- Both runs report: PaperLedger P2 12/12 PASS; cross-domain tests 2/2 PASS; T0 Gateway/fencing 9/9 PASS; P3 API 31/31 PASS; Paper regression 59/59 PASS; SWG-F process runtime 12/12 PASS.
- Exact-head artifact ID `13407946143`, digest `sha256:8313e47f4c98463ee7e10aa2d795140642ae1a798fa9b7a7905ca21bf8be956a`.
- PR merge-context artifact ID `13407307373`, digest `sha256:26506ca10fd4578cfe40bacdaddf01efee73de246050018424e81abfb13e0ee8`. Artifact bytes not independently downloaded/re-hashed.
- PR #112 remains OPEN / DRAFT / NOT MERGED; head `bd1f658ab04ef119c82b8a84ea90f3555d3dd50e`, base `a58b6163a78861ecf5bb7d2c8fc11aa420142837`. Current compare: 100 commits ahead, 0 behind. No retarget or merge performed. PR #134 remains OPEN / DRAFT / NOT MERGED.
- Final status: both directions of capability isolation PASS; exact-head and PR merge-context CI PASS; T0 and SWG-F regression suites PASS. Windows/Android lock semantics and production runtime remain NOT VERIFIED.


## SWG-F Windows platform gap — read-only audit 2026-11-05

- User requested continuation; this increment was limited to read-only source/CI inspection. No code, workflow, branch, PR state, database or runtime was changed.
- Source reviewed on SWG-F branch `feature/t0-paper-writer-isolation-red-20261102`, head `bd1f658ab04ef119c82b8a84ea90f3555d3dd50e`.
- Current SWG-F acceptance workflow `.github/workflows/paper-writer-isolation-red.yml` runs only on `ubuntu-latest`; no Windows runner acceptance evidence exists.
- `paper_execution/writer_gate.py` contains a Windows `msvcrt.locking` path. It ensures the lock file has a byte, seeks to byte offset 0, uses `LK_NBLCK` with bounded retry, and unlocks with `LK_UNLCK` on close. Windows uses the same byte-range exclusive lock call for both logical shared/exclusive requests; concurrent writer admissions are therefore serialized on Windows (conservative, but behavior differs from POSIX shared flock).
- `paper_execution/test_writer_gate_runtime.py` uses multiprocessing `spawn` and temporary SQLite fixtures for admission/drain race, admitted writer drain, rejection after DRAINING, crash-after-commit, drain timeout, reopen/generation invalidation, and transaction commit/rollback. These tests are not currently run on Windows CI.
- SIGKILL test is explicitly skipped unless `os.name == "posix"`; Windows crash recovery is therefore not covered by that test. Windows termination semantics need a separate process-termination test (e.g. child process termination via supported multiprocessing API) and assertions that lock release and stale-token reconciliation complete.
- Read-only findings: Windows lock adapter source exists, but Windows byte-range lock contention/release, timeout behavior, process termination recovery, and full runtime suite remain NOT VERIFIED. Linux success is not Windows evidence.
- PR #112 remains OPEN / DRAFT / NOT MERGED, head `bd1f658ab04ef119c82b8a84ea90f3555d3dd50e`, base `a58b6163a78861ecf5bb7d2c8fc11aa420142837`; 100 commits ahead / 0 behind its declared base. PR #134 remains OPEN / DRAFT / NOT MERGED.
- Proposed next increment requires separate explicit approval: Windows-only test/CI addition, retaining the existing Linux workflow. Add a `windows-latest` job using only TemporaryDirectory + synthetic SQLite; run cross-domain isolation and focused SWG-F runtime tests; add Windows process-termination recovery coverage; verify lock contention, timeout, DRAINING fail-closed behavior, drain completion, and generation invalidation. No production code changes, no canonical DB, exchange, migration, deployment, or live execution.


## SWG-F Windows lock and process-recovery acceptance — 2026-11-05

- User explicitly approved a Windows-only test/CI increment. Linux CI was retained. Scope stayed test/workflow-only; no production writer_gate.py, T0 source, database schema, migration, app consumer or runtime behavior was changed.
- SWG-F branch: feature/t0-paper-writer-isolation-red-20261102; exact final head SHA 6f7c0acff3df0d7ee8de610cf4837312e964bee6.
- Exact T0 source remains pinned and verified at a569eb6248cd53252fcf32065482921fc4c8ffcd. Windows job verifies both source checkouts before tests.
- Increment changes relative to prior reviewed SWG-F head d6465e073d7aade8ac60716db2ffef273334c5b0: workflow .github/workflows/paper-writer-isolation-red.yml, paper_execution/test_writer_gate_runtime.py, and paper_execution/test_cross_domain_writer_isolation.py only. No production files changed.
- Windows-specific runtime tests:
  - test_windows_lock_contention_times_out_and_releases_cleanly: PASS. A child process holds the writer lock; exclusive contention reaches bounded WriterLockTimeout; after child release, lock can be reacquired and drain completes.
  - test_windows_terminate_releases_lock_and_reconciles_orphan_token: PASS. Persist DRAINING while a child holds the lock, verify new admission fails closed with bounded timeout, terminate the child process, then verify OS lock release, DRAINED transition, zero orphan token rows, and continued admission denial.
  - Existing runtime suite also verifies DRAINING rejection, drain timeout/completion, crash recovery, and settlement-gated generation advancement on Windows.
- Windows runtime job: 14 tests run, 1 expected POSIX-only SIGKILL test skipped; 13 passed, 0 failures/errors. Both Windows-specific tests explicitly PASS.
- Windows cross-domain T0/Paper boundary acceptance: 2/2 PASS. T0 Gateway/fencing regression: 9/9 PASS. Source-only preflight PASS; no exchange credentials or external database configured.
- Linux exact-head regression: P2 12/12, cross-domain 2/2, T0 Gateway 9/9, P3 API 31/31, full Paper execution 61 tests (2 expected Windows-only skips), runtime 14 tests (2 expected Windows-only skips); all PASS.
- Exact-head push #42015411992: SUCCESS on 6f7c0acff3df0d7ee8de610cf4837312e964bee6. Linux job 127204622664; Windows job 127204623364.
- PR merge-context #42015419602: SUCCESS on the same source head. Linux job 127204647210; Windows job 127204647751.
- Exact-head artifacts: Windows ID 13409002242, digest sha256:6a967066b9212e009a3678bc022ed3a64d27ddd5dd4e37476ce04f5135cb1332; Linux ID 13408962324, digest sha256:952859fbf97593c0d91209b0bbd7c9b73b9399c410ee6610a312f9255c05761a.
- PR-context artifacts: Windows ID 13409800095, digest sha256:f63a564c78573afdb83662a58cddc9aba729ccfd18e77140f67b3d05830b920a; Linux ID 13408278805, digest sha256:baff895d872f0e801705dd25f7b9dd21c7a97aac685a1229346fa3bd812dfcac. Artifact bytes were not independently downloaded/re-hashed.
- Early Windows CI attempts exposed two test-harness issues and were corrected without weakening assertions: Windows serializes logical shared/exclusive lock admission, so admission attempts while DRAINING now use explicit bounded timeouts; temporary SQLite fixtures now explicitly close test connections before cleanup. Final exact-head and PR-context runs both pass.
- PR #112 remains OPEN / DRAFT / NOT MERGED; head 6f7c0acff3df0d7ee8de610cf4837312e964bee6, base a58b6163a78861ecf5bb7d2c8fc11aa420142837, 111 commits ahead / 0 behind. No retarget or merge.
- PR #134 remains OPEN / DRAFT / NOT MERGED. T0 branch/source was not changed by this increment.
- Status: Windows SWG-F lock contention, bounded timeout, DRAINING fail-closed, process termination lock release, orphan-token reconciliation and generation invalidation PASS on GitHub Windows runner. Linux regression PASS. Android lock semantics remain NOT VERIFIED; production runtime/deployment remains NOT VERIFIED.
- Limits retained: temporary SQLite + synthetic data only; no canonical DB, exchange, production feeder, PC/VPS deployment, migration or live execution.


## 2026-11-05 — T0 VPS deployment authorization and canonical source decision

User explicitly expanded the T0 deployment scope:
- T0 is no longer Android-first. PC/VPS is the primary operating environment; Android is not the central runtime.
- User authorized the conditional end-to-end T0 VPS rollout, including canonical database creation, production Feeder activation, and synchronization of real market data **only after the required safety gates pass**.
- This authorization is a phase-gated deployment authorization, not permission to bypass acceptance criteria or claim production readiness prematurely.
- Canonical source decision: **temporarily retain Binance USD-M (BTCUSDT USDT perpetual) as the canonical source**. This is a temporary source selection and must be revisited if Binance access, data quality, reliability, or policy constraints fail acceptance.
- Kraken Spot remains isolated and must not be promoted to the Futures canonical dataset. OKX Shadow remains non-canonical.
- Keep `ai_execution_enabled=false`; no live orders or exchange trading endpoints. Market-data access only.

### Deployment authorization boundaries

Authorized in principle, subject to gates:
1. Prepare PC/VPS deployment architecture and operational runbook.
2. Implement and verify the production storage/write path, including atomic lease fencing and recovery.
3. Provision the canonical T0 database only after storage, backup/restore, access-control, and rollback gates pass.
4. Start the production Feeder and synchronize Binance USD-M market data only after staging acceptance and explicit pre-production checklist completion.
5. Monitor data continuity, closed-candle semantics, duplicate/gap handling, provenance, restart recovery, and operational health.

Not yet verified / not to be treated as complete:
- VPS provider/account, region, OS, resource sizing, firewall and access policy.
- Canonical database backend. Current SQLite Gateway has same-database atomic lease fencing; current PostgreSQL/Timescale adapter is read-only and is **not** a valid canonical writer. Do not enable PostgreSQL writes until an equivalent same-transaction lease-fenced writer and disposable integration tests are implemented and accepted.
- Backup/restore procedure and measured recovery behavior on the selected VPS/database.
- Production service supervision, secrets handling, alerting, disk/retention limits, and recovery from host/process failure.
- Live Binance public market-data connectivity, rate-limit behavior, data correctness, and real Feeder stability.
- No canonical DB has been created and no production Feeder or real exchange synchronization has been started by this authorization record.

### Immediate next phase: P0 production architecture and safety design

Produce a concrete decision record covering:
- VPS provider/region/OS and least-privilege network/access model.
- Canonical storage choice and the required writer/lease transaction boundary.
- Binance USD-M public market-data endpoints and credential policy (no trading permissions or order endpoints).
- DB initialization/migration ownership, backup cadence, restore test, retention and disk monitoring.
- Feeder service lifecycle, readiness gates, restart policy, health/alerting, and shutdown behavior.
- Staging acceptance tests, production cutover checklist, rollback/stop conditions, and cost ceiling.

Acceptance rule: no production database creation, real exchange connection, or Feeder start until the design is recorded and the corresponding staging safety gates are evidenced. Preserve existing PR #134 as OPEN / DRAFT / NOT MERGED; do not merge it automatically. GitHub Actions remains the default CI; Codemagic is fallback-only under the existing policy.

Current status:
- VPS rollout authorization: **APPROVED CONDITIONALLY**.
- Binance USD-M canonical source: **TEMPORARILY SELECTED**.
- Production canonical DB: **NOT CREATED**.
- PostgreSQL canonical writer: **BLOCKED / NOT IMPLEMENTED**.
- Production Feeder: **NOT STARTED**.
- Real market-data synchronization: **NOT STARTED**.
- VPS deployment and 24/7 operation: **NOT VERIFIED**.
- Live trading / order execution: **NOT AUTHORIZED**; `ai_execution_enabled=false`.


## 2026-11-05 — P0 PostgreSQL/TimescaleDB production architecture design

- User directed P0 production architecture design and explicitly retained the boundaries: do not merge PR #134, create a canonical DB, or start the Feeder in this increment.
- Added decision/design record: `docs/architecture/T0_POSTGRESQL_ATOMIC_WRITER_P0_2026-11-05.md`.
- Documentation commit on `main`: `5f45b1d09d5d735fcc3132c3a7f9b5e2bf50c233`.
- The design was based on source inspection of PR #134's `market_data/write_gateway.py`, `postgres.py`, `storage.py`, `migrations.py`, and `test_timescaledb.py`.
- Verified current boundary: SQLite Gateway uses same-database `BEGIN IMMEDIATE` lease fencing; PostgreSQL adapter remains read-only (`canonical_writes_disabled=True`); TimescaleDB integration fixtures seed rows directly and do not prove fenced canonical writes.
- Proposed PostgreSQL contract: lease row and candle batch in one DB transaction; row-level lease lock; exact owner/generation checks; expiry checked with PostgreSQL `clock_timestamp()`; final expiry check before commit; all-or-nothing rollback; atomic generation increment on takeover; identical duplicates idempotent and conflicting candle values rejected.
- Design includes least-privilege migration/Feeder/read-only API roles, explicit checksum migrations, disposable PG/Timescale acceptance matrix, backup/restore and RPO/RTO requirements, VPS deployment choices, stop conditions, and a PG-RED test-first next increment.
- No source/runtime code or workflow changed. No tests were run because this increment is architecture documentation only.
- No VPS/provider/cost ceiling selected; no database provisioned or created; no Binance connection or market-data sync; no Feeder activation.
- PR #134 remains OPEN / DRAFT / NOT MERGED; no merge was attempted.
- Status: P0 architecture proposal **RECORDED**; PostgreSQL writer **BLOCKED / NOT IMPLEMENTED**; PostgreSQL fenced integration **NOT RUN**; backup/restore **NOT VERIFIED**; VPS provisioning **NOT STARTED**.
- Next increment: PG-RED — add failing, isolated PostgreSQL lease-fencing and takeover contract tests using disposable local TimescaleDB and synthetic candles only. SQLite behavior must remain unchanged. No canonical DB, production exchange connection, VPS provisioning, Feeder activation, or merge.


## 2026-11-05 — T0 PostgreSQL writer PG-RED

- Continued the P0 design into PG-RED on the existing PR #134 source branch `feature/t0-atomic-write-fencing-20261105`; PR #134 remains OPEN / DRAFT / NOT MERGED.
- Added `market_data/test_postgres_write_gateway.py` with seven isolated contract tests: valid owner/generation commit with decimal fidelity; wrong owner/stale generation rejection; DB-clock lease expiry; idempotent duplicate and conflicting duplicate rollback; invalid candle rollback; concurrent takeover and stale-generation fencing; generation-bound heartbeat/release.
- Added the PostgreSQL writer RED step to `.github/workflows/t0-single-writer-gateway-red.yml`, executed only against the disposable local TimescaleDB CI service. No production DSN, canonical DB path, Paper DB, Binance/OKX credentials, or external exchange access is used.
- Final tested source SHA: `b9111a022d3e66f7a17032e40f9597bc7e24e38f`.
- Exact-head GitHub Actions run [#42019166710](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42019166710): static Gateway/Feeder regression job SUCCESS; PostgreSQL writer RED step intentionally FAILED with 7 errors because `PostgresLeaseStore` is not implemented. The failure confirms the missing API boundary; transaction behavior is not yet verified.
- The existing read-only TimescaleDB step was SKIPPED after the expected RED failure; it is NOT PASS for this run.
- Artifacts: static evidence ID `13410937055`, digest `sha256:544b8b77603727cc2261935830ca24259b689ff4f78f84e30446b944dfede5ae`; Timescale service evidence ID `13410853344`, digest `sha256:5098c1703998bce6275a5be3c2dfe29c1b54e1dc1e9059b873e717ee1d83ab10`.
- Evidence report: `docs/evidence/T0_POSTGRESQL_WRITER_PG_RED_2026-11-05.md` on PR #134 branch.
- PR #134 description updated with the PG-RED scope, exact source SHA, workflow run, artifact IDs/digests, expected failure meaning, and next step.
- No runtime source implementation changed; existing SQLite Gateway behavior was not changed. No canonical DB, VPS, Binance connection, Feeder activation, or live trading was used.
- Status: PG-RED contracts **RECORDED**; missing Postgres lease API **CONFIRMED**; PostgreSQL atomic writer **BLOCKED / NOT IMPLEMENTED**; PostgreSQL transaction acceptance **NOT VERIFIED**; read-only TimescaleDB integration in this run **SKIPPED / NOT VERIFIED**; SQLite regression **PASS** in static job.
- Next increment: PG-GREEN — implement PostgreSQL lease lifecycle and atomic write gateway to satisfy these contracts, preserving SQLite unchanged. Ensure one DB transaction covers lease row lock, owner/generation/expiry checks, candle batch, final `clock_timestamp()` check and commit; run both writer contracts and existing read-only TimescaleDB integration in the isolated service job. No production DB creation, VPS provisioning, real Binance connection, Feeder activation, or PR merge.


## 2026-11-05 — T0 PostgreSQL writer PG-GREEN

- Implemented standalone `PostgresLeaseStore` and `PostgresWriteGateway` in `market_data/postgres.py`; added explicit checksum-managed lease migration `market_data/migrations/002_t0_feeder_leases.sql`.
- Writer and lease store use the same PostgreSQL database. The writer locks the lease row, checks exact owner/generation, then checks expiry with a separate `clock_timestamp()` query after acquiring the row lock, writes the batch, rechecks expiry immediately before commit, and rolls back on any exception.
- Identical duplicate candles are idempotent; conflicting candle values are rejected. Decimal precision is preserved. Existing `PostgresCandleStore` remains read-only and no unfenced write method was added.
- Replaced the initial `-infinity` timestamp sentinel after CI showed Psycopg cannot load it as a Python datetime; inactive leases now use a finite UTC sentinel from the explicit migration.
- Fixed a CI-discovered race: expiry projection in the same `SELECT ... FOR UPDATE` can be stale after lock wait. Both lease takeover and writer authorization now recheck expiry in a separate database-clock query after acquiring the row lock.
- Exact-head GitHub Actions run [#42021445350](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42021445350), source SHA `3818d729ceca0577b59a22e922088b346bc42471`: static Gateway/Feeder job SUCCESS; full static `market_data` suite 187 tests, 13 skipped; isolated TimescaleDB job SUCCESS; PostgreSQL writer/lease contracts 7/7 PASS; existing read-only TimescaleDB integration 6/6 PASS.
- Artifacts: static ID `13411592265`, digest `sha256:de95a12b985160be04d2ce3f87a45f5d5f9d0b5ad1609123aadb00f57e0e1c2c`; TimescaleDB ID `13412206069`, digest `sha256:84344ae6299dab5358df91bc9cab2d7aed5616627998a4f5bfdbcc43f5663c91`.
- Evidence report: `docs/evidence/T0_POSTGRESQL_WRITER_PG_GREEN_2026-11-05.md` on PR #134 branch. PR #134 description updated with exact tested SHA, workflow, test results, artifacts, review limits and next step.
- Code review boundary: PostgreSQL writer is standalone and not wired into `build_runtime()` / `build_production_runtime()`. FeederRuntime currently expects SQLite lease/store method signatures and same-path database semantics. PostgreSQL runtime composition, role separation/grants, backup/restore, VPS, production Feeder and real Binance ingestion remain **NOT IMPLEMENTED / NOT VERIFIED / NOT STARTED**.
- SQLite Gateway and its behavior remain unchanged. No production DB, VPS, Binance connection, Feeder activation or live trading was used.
- Status: standalone PostgreSQL lease/writer **IMPLEMENTED; 7/7 PASS in disposable TimescaleDB**; read-only TimescaleDB integration **6/6 PASS**; SQLite regression **PASS**; PostgreSQL runtime composition **BLOCKED / NOT IMPLEMENTED**; role/permission acceptance **NOT RUN**; backup/restore **NOT VERIFIED**; production deployment **NOT STARTED**. PR #134 remains OPEN / DRAFT / NOT MERGED.
- Next increment: PG-RUNTIME-ADAPTER — define a shared FeederRuntime lease protocol and add PostgreSQL runtime composition using PostgresLeaseStore + PostgresWriteGateway + PostgresCandleStore against one DSN. Add RED tests for recovery, scheduler Gateway identity, heartbeat, readiness, lease loss, shutdown drain, and restart/takeover using disposable TimescaleDB only. Preserve SQLite default and behavior. No production DB, VPS, real exchange connection, Feeder activation, or merge.


## 2026-11-05 — T0 PostgreSQL runtime adapter PG-RED

- Added `market_data/test_postgres_feeder_runtime.py` on PR #134 branch with four RED contracts for a PostgreSQL runtime lease adapter: acquire, heartbeat, DB-clock current/write authorization, and generation-bound release.
- Exact test source commit: `66157193bbaf7c3960ef52736a3f4dbadcac9e0c`.
- Exact-head GitHub Actions run [#42023493409](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42023493409): compile and preceding Gateway/Feeder, Health/Readiness, and process-restart steps passed. Full-suite discovery failed as expected because `PostgresRuntimeLeaseAdapter` is not implemented; 188 tests discovered, 1 import error, 13 skipped. TimescaleDB dependent job was skipped, not passed.
- Artifact ID `13412547723`, SHA-256 `80068b0f3f1352244bd35a7b66362666d0b442028ce5c46be1a582234de7c886`.
- Evidence report: `docs/evidence/T0_POSTGRESQL_RUNTIME_ADAPTER_PG_RED_2026-11-05.md` on PR #134 branch.
- Attempted runtime source update was blocked by repository write safety gate; no runtime source implementation was changed. This increment therefore records RED only.
- Status: adapter contract **RED CONFIRMED / IMPLEMENTATION PENDING**; PostgreSQL runtime composition **NOT IMPLEMENTED**; PostgreSQL scheduler/recovery shared Gateway, heartbeat, readiness, lease-loss, shutdown and restart **NOT VERIFIED**. Existing SQLite regression steps before full-suite discovery passed; no SQLite source changed.
- Next: implement `PostgresRuntimeLeaseAdapter` so FeederRuntime's `now_ms` is ignored for PostgreSQL expiry decisions; compose matching PostgreSQL store/lease/Gateway on one DSN; verify scheduler and recovery use the same gateway; run adapter and disposable TimescaleDB integration contracts. Preserve SQLite default and behavior.
- No production DB, VPS, real Binance connection, production Feeder activation, or PR merge was performed. PR #134 remains OPEN / DRAFT / NOT MERGED.


## 2026-11-05 — T0 PostgreSQL FeederRuntime adapter PG-GREEN

- Implemented `PostgresRuntimeLeaseAdapter` in `market_data/feeder_service.py`. It maps FeederRuntime acquire/heartbeat/current/write-authorization/release calls to `PostgresLeaseStore`; the legacy runtime `now_ms` argument is never forwarded as PostgreSQL expiry authority. PostgreSQL remains DB-clock authoritative.
- `build_runtime()` now supports both existing SQLite composition (unchanged same-file store/lease invariant) and PostgreSQL composition. PostgreSQL Candle Store, Lease Store and `PostgresWriteGateway` must share the exact same DSN. Scheduler and startup recovery use the same Gateway instance; recovery heartbeat also uses the PostgreSQL adapter.
- `build_production_runtime()` selects `PostgresLeaseStore` when `MARKET_DATA_BACKEND=postgres`, supports `T0_FEEDER_LEASE_NAME`, and rejects a separate `T0_FEEDER_LEASE_DB` in PostgreSQL mode.
- Added 9 static adapter/composition contracts and one disposable TimescaleDB runtime integration test. The integration test starts the real FeederRuntime with a synthetic exchange, verifies startup recovery persists a closed candle through the fenced PostgreSQL Gateway, verifies scheduler duplicate sync is idempotent through that same Gateway, then verifies graceful stop releases the exact lease generation. No real exchange/network is used.
- Exact implementation/test source SHA accepted by CI: `3a3e81396ec1c9d03039e0139fab260e83efedd1`. Current PR #134 branch head after evidence-only commit: `d3312d56849e9145d55f0710cad5f31e98eb17a6`. PR base remains `feature/t0-centralized-data-feeder-p1-20261101`; PR #134 remains OPEN / DRAFT / NOT MERGED.
- Exact-head push workflow [#42027052569](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42027052569): **SUCCESS**. Static job `127243768694` PASS (197 tests, 14 skipped); isolated TimescaleDB job `127243882931` PASS (PostgreSQL writer 7/7, FeederRuntime adapter/composition/integration 10/10, read-only TimescaleDB 6/6).
- Push artifacts: static ID `13414222523`, SHA-256 `ebb61daf23e225223ab4efcca8eb481d1e52cffbc93ca3c042a313f1b3de4e2b`; TimescaleDB ID `13414162575`, SHA-256 `77fc8ffd7a1b21ad62491c3ea353327c3ca602f820729aadba06512c8c635d23`.
- PR merge-context workflow [#42027061402](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42027061402): **SUCCESS**. PR head `3a3e81396ec1c9d03039e0139fab260e83efedd1`; base `8b196d2720eab804728df7c0227c606c094b16ad`; synthetic merge checkout SHA `a0179e13a83db4a18aa03e1518647e1f32379b0a`. Static job `127243954898` PASS (197 tests, 14 skipped); TimescaleDB job `127244083814` PASS (writer 7/7, FeederRuntime 10/10, read-only 6/6).
- PR merge-context artifacts: static ID `13414885785`, SHA-256 `a01a42aba6db339b9aa082d021d0694d8e7a17756e616f4d6521883b0bd2e58d`; TimescaleDB ID `13413668679`, SHA-256 `4e2d5289f4550c026e42c2f2752fd4fec7b9e30430aadd88511baea0b92654da`.
- Local focused tests: 43 PASS / 1 SKIP across adapter, Feeder lifecycle and health. Local broader market_data subset: 171 PASS / 14 SKIP / 3 deselected / 91 subtests PASS; the local runner lacks Flask and injects a Python startup warmup that affects three subprocess tests. CI's full static suite passed; the isolated TimescaleDB service tests are the authoritative PostgreSQL runtime integration evidence.
- First TimescaleDB CI attempt on source `61813f3d74162d82b0bee505a05f8181da82566d` failed because the new integration test omitted imports for `EXCHANGE` and `MARKET_TYPE`. Corrected in source commit `3a3e81396ec1c9d03039e0139fab260e83efedd1`; both later push and PR merge-context workflows passed. The evidence report also records an intermediate contents-update commit that was immediately superseded; use only the final tested source SHA and current branch head above.
- Evidence report: `docs/evidence/T0_POSTGRESQL_FEEDER_RUNTIME_PG_GREEN_2026-11-05.md` on PR #134 branch.
- Status: PostgreSQL runtime adapter **PASS**; runtime composition/shared Gateway **PASS**; disposable TimescaleDB recovery/scheduler/lease release integration **PASS**; SQLite lifecycle/health regression **PASS**; push and PR merge-context CI **PASS**. Production roles/grants, credential separation, backup/restore, RPO/RTO, VPS deployment and real Binance ingestion remain **NOT VERIFIED / NOT STARTED**.
- No production canonical DB was created; no production Feeder was activated; no real Binance API was called; no order execution occurred. `ai_execution_enabled=false` remains unchanged.
- Next increment: continue P0 production architecture. Define least-privilege DB roles/grants (migration owner, Feeder canonical writer, read-only consumers), credential handling, backup/restore runbooks and measurable RPO/RTO acceptance. Then staging preflight. Do not create production canonical DB, connect real Binance, activate the Feeder or merge PR #134 without the appropriate separate approval.


## 2026-11-05 — T0 P0 production security, backup and recovery architecture

- Continued after PG-RUNTIME-ADAPTER PG-GREEN. Confirmed PR #134 remains OPEN / DRAFT / NOT MERGED and the source branch baseline was `d3312d56849e9145d55f0710cad5f31e98eb17a6`; the passing implementation/test SHA is `3a3e81396ec1c9d03039e0139fab260e83efedd1`.
- Added `docs/T0_PRODUCTION_SECURITY_BACKUP_RPO_RTO.md` on the existing PR #134 branch. It defines separate PostgreSQL principals for schema owner, ephemeral migrator, Feeder writer, read-only consumers, backup and break-glass administration; least-privilege grant requirements and negative tests; credential/TLS/network controls; independent encrypted backup/PITR; restore/failover fencing; restored lease invalidation; and staging acceptance.
- Proposed initial service objectives for review: RPO <= 5 minutes and RTO <= 60 minutes, with monthly isolated restore drills and at least 7 days PITR retention where supported. These are targets, not verified provider guarantees. Provider choice, cost ceiling and region remain unset.
- Corrected existing PostgreSQL design and acceptance docs: GitHub Actions is the default CI/evidence platform; Codemagic is only a documented fallback when GitHub Actions is unavailable or materially constrained.
- No application source, SQL migration, database, credentials, VPS, network rules, backup job, Binance connection or Feeder service was changed or created. No tests were run; this increment is architecture/documentation only.
- Current status: PG writer/runtime integration **PASS in disposable TimescaleDB CI**; production role/grant acceptance **NOT RUN**; secret/TLS/network acceptance **NOT RUN**; backup/PITR **NOT PROVISIONED / NOT VERIFIED**; restore/RPO/RTO **NOT VERIFIED**; provider/VPS/cost selection **PENDING**.
- Next: P0-SECURITY-RED — implement disposable TimescaleDB role/grant negative tests and credential isolation tests only after the exact required SQL privileges are derived from runtime SQL. Keep production DB/VPS/real Binance/Feeder activation blocked until staging and operator approvals. PR #134 must not be merged without explicit approval.


### P0 security architecture — source-derived grant review

- Reviewed the PG runtime SQL at tested implementation SHA `3a3e81396ec1c9d03039e0139fab260e83efedd1`: `PostgresLeaseStore.acquire()` seeds the singleton lease row, lease lifecycle uses SELECT/UPDATE, and `PostgresWriteGateway` performs SELECT/SELECT FOR UPDATE plus INSERT on candles. `PostgresStore.initialize()` is a no-op; migrations are explicitly applied, not by Feeder startup.
- Derived minimum Feeder grants for staging verification: database CONNECT; schema USAGE; `market_data.feeder_leases` SELECT/INSERT/UPDATE; `market_data.candles` SELECT/INSERT. Reader: CONNECT, schema USAGE, candles SELECT only; no lease access. Neither runtime identity needs DDL, DELETE, TRUNCATE, role administration or extension privileges. These are source-derived requirements, not yet tested against PostgreSQL roles.
- Found and documented a configuration contract mismatch: source currently reads `MARKET_DATA_POSTGRES_DSN`, while older design/acceptance documents named `MARKET_DATA_DATABASE_URL`. Documentation now follows the current runtime key; no compatibility alias or code change was introduced. Production config remains blocked until a deliberate interface decision and tests.
- Updated `docs/T0_PRODUCTION_SECURITY_BACKUP_RPO_RTO.md`, `docs/market-data-postgresql-timescaledb-design.md`, and `docs/market-data-postgresql-timescaledb-acceptance.md` on the PR branch.
- No tests run: documentation/source-review only. Next increment P0-SECURITY-RED: add disposable TimescaleDB role/grant tests proving positive Feeder operations and negative DDL/delete/truncate/reader-write/lease-read boundaries; verify credential rotation and TLS/network controls separately. Do not provision production infrastructure or activate Feeder.


## 2026-11-05 — P0-SECURITY-RED least-privilege role contracts

- Added `market_data/test_postgres_role_privileges.py` and wired it into the isolated TimescaleDB integration job in `.github/workflows/t0-single-writer-gateway-red.yml`.
- Test creates ephemeral Feeder and Reader LOGIN roles with random per-run passwords in disposable local TimescaleDB only. Grants reflect source-derived runtime minimums. Positive contracts: Feeder lease acquire/heartbeat/release and fenced candle insert. Negative contracts: Feeder DDL/DELETE/TRUNCATE denial; Reader lease SELECT/write/update denial while candle SELECT succeeds; schema CREATE and role-admin membership absent.
- Test role creation uses psycopg SQL Identifier/Literal composition. Credentials are generated at runtime and are not written to repository, logs or artifacts.
- Static GitHub Actions job passed on candidate SHA `2ed5328521f560cd2c0cb6257ddf0690c367d850` (compile, focused Gateway/Feeder/Health/process restart and full market_data suite). Exact runs: push `42030527904`, PR `42030518396`. Both isolated TimescaleDB jobs are still initializing/running; role integration is **PENDING / NOT VERIFIED**. Do not claim PG role acceptance until the step and full run conclude success on this exact SHA.
- Branch head is `2ed5328521f560cd2c0cb6257ddf0690c367d850`. This is a test/workflow-only increment; no production source, migrations, credentials, infrastructure, database or Binance access changed.
- Next: inspect both TimescaleDB job outcomes and role-test logs. Fix any failure with test-first changes and rerun exact-head CI. Only after role grants pass, proceed to credential rotation/TLS controls; production DB/VPS/Feeder activation remain blocked.


### P0-SECURITY-RED — permission failure reproduced and source fix awaiting CI

- Initial disposable TimescaleDB role run failed in both push/PR workflows `42030527904` / `42030518396` on candidate SHA `2ed5328521f560cd2c0cb6257ddf0690c367d850`. PostgreSQL service logs explicitly showed `permission denied for table candles` on the Gateway's `SELECT ... FOR UPDATE`. This confirms PostgreSQL requires a stronger privilege for that row-lock operation than the intended Feeder SELECT/INSERT grant.
- Rejected the unsafe workaround of granting Feeder UPDATE on canonical candles. Added a negative test that Feeder UPDATE must be denied, then removed `FOR UPDATE` from the candle lookup in `PostgresWriteGateway`. The transaction still holds `SELECT ... FOR UPDATE` on the singleton lease row; that lock serializes writers for the lease, while the candle primary key, `ON CONFLICT DO NOTHING`, and value comparison protect idempotency/conflict handling.
- Updated `docs/T0_PRODUCTION_SECURITY_BACKUP_RPO_RTO.md` to explain why candle UPDATE is not required.
- Candidate source fix SHA: `a71dbe4323f12b5e404f59ccbafa7672a96ba5cc`; branch head after doc clarification: `d0f503ee3ba987784daa36e904588829c44e93b6`.
- Static Gateway/Feeder/Health/process/full-suite job passed on candidate SHA `a71dbe4323f12b5e404f59ccbafa7672a96ba5cc`. New disposable TimescaleDB push/PR runs are queued; role integration remains **NOT VERIFIED** until they complete. Older run failure remains preserved as RED evidence.
- No production database, VPS, secret, network rule, Binance connection or Feeder activation. Next: obtain latest exact-head TimescaleDB result; if role suite passes, add credential rotation and TLS tests as the next isolated increment.

## 2026-11-05 — Android PR #42–44 source recovery audit

- Read-only audit of closed/unmerged Android PRs #42 (Order Book sequence), #43 (signal-frequency diagnostics), and #44 (observe-only Multi-Symbol Scanner) against current branch `feature/android-btcusdt-live-alerts`, SHA `4bb768ad55a89e9ad1e4a65b32bdd7ebd7ef48d4`.
- Historical PR heads: #42 `2c380d31adef96d4f7b38442318b796e5d7a813e`; #43 `1655a92ddf9a111c1e895e6853a0bc2a54177018`; #44 `32d60728c42aebe9a7c02bcf92f75e4fa8e4d53c`.
- #42: historical `OrderBookSequence.kt` and tests exist, but helper absent at the same path on current branch. Current `OrderBookEngine.kt` inspected; equivalence of inline sequence checks remains NOT VERIFIED.
- #43: historical diagnostic logic found in `StrategyEngine.kt` and `StrategyMonitorService.kt`; corresponding diagnostic markers/counters not found in current StrategyEngine/dashboard/monitor source. Classification: MISSING at inspected source level.
- #44: historical `MultiSymbolScanner.kt`, `BinanceRestGate.kt`, and `OrderBookSequence.kt` exist at PR head but are absent at those paths on current branch. Current MarketEngine/dashboard inspection did not find a dedicated MultiSymbol scanner. PR #45's changed-file list does not include these dedicated files and therefore does not prove equivalent replacement.
- GitHub reports #42/#43/#44 closed with `merged=false`; merge_commit_sha fields on #43/#44 are not treated as proof of integration into the current Android branch.
- Evidence report committed on main: `docs/evidence/ANDROID_PR_42_44_SOURCE_RECOVERY_AUDIT_2026-11-05.md`, commit `83ce91047eed3f3a2a8297ca3d809d1d8b57407a`.
- Status: source-level audit **RECORDED**; #42 equivalent behavior **NOT VERIFIED**; #43 diagnostics **MISSING at inspected source level**; #44 scanner/replacement **MISSING at inspected source level**; build/tests **NOT RUN**; no source code, workflows, PR states or branches changed.
- Next: inspect current OrderBook snapshot/sequence behavior and dashboard/monitor event pipeline; define a test-first, non-duplicative recovery plan. Preserve strategy thresholds and paper/analysis-only safety. Do not delete historical branches or replay/merge closed PRs until CI validates recovery and explicit approval is given.



## 2026-11-05 — BTC Chart Pro separation audit

- Read-only audit recorded in docs/evidence/CHART_PRO_SEPARATION_AUDIT_2026-11-05.md; report commit: 3c90449bfa393092f92042da7b2c46446c91a4d1.
- Confirmed separate private Chart Pro repository: kenznguyen/btcusdt-chart-pro-android (main). Chart Pro-only Android product code should remain in that repository.
- Inspected five-layer PR #134 head d0f503ee3ba987784daa36e904588829c44e93b6 (branch feature/t0-atomic-write-fencing-20261105; base feature/t0-centralized-data-feeder-p1-20261101 at 8b196d2720eab804728df7c0227c606c094b16ad). PR #134 remains OPEN / DRAFT / NOT MERGED.
- Confirmed boundary contamination: root README and android-app README identify the combined repository/module as BTCUSDT Chart Pro; MainActivity has regular Chart Pro CompleteDashboard/StrategyMonitorService path plus a parallel five-layer FiveLayerStandaloneDashboard; Chart Pro chart/scanner/backtest/alerts sources and Chart Pro release signing remain in the same Android Gradle module; architecture/runbook docs call the five-layer APK a Chart Pro client and describe stale Codemagic Android workflows.
- Five-layer standalone Paper UI already has a runtime entrypoint, but the module/source-set boundary is not isolated. Do not delete Chart Pro source until the five-layer-only build compiles and tests with an explicit app identity and package ID.
- Preserve T0–T4, React control_dashboard, FiveLayerPanel/API/canonical-candle UI, shared risk/paper ledger, and shared StrategyEngine/order-book contracts pending dependency proof. MultiSymbolScanner/chart UI/Chart Pro alert/backtest/monitoring path are Chart Pro-only candidates, but exact compile/runtime dependency map remains NOT VERIFIED.
- Root main branch remains a legacy Telegram Signal Bot snapshot (42 paths), distinct from the active five-layer PR #134 source line (234 paths). Do not assume main represents the complete five-layer runtime. Legacy Telegram/dashboard files are not automatically Chart Pro; ownership/deployment review required before removal.
- Status: inventory PASS; dependency graph NOT VERIFIED; source cleanup NOT STARTED; Android/Python/React tests NOT RUN; no source/workflow/PR/branch changes other than this documentation evidence on main. T0, PR #134, canonical DB, Feeder, exchange ingestion and paper/live execution were not touched.
- Next: trace the parallel variant's imports and packaged classes/resources, create a keep/move/remove manifest, then isolate a five-layer-owned Android module/application ID. Keep Chart Pro source in its separate repository. Do not mix cleanup into PR #134's T0 scope; no branch/PR deletion or merge without separate approval.


### BTC Chart Pro separation — Android dependency-map increment

- Extended docs/evidence/CHART_PRO_SEPARATION_AUDIT_2026-11-05.md with file-level disposition and source-set findings; update commit e7f0537a981d67c5a1037866f02326a80057fc89.
- Android source line reviewed at PR #65 head 51f4edf5776b06b927db980faac4ca0ca91c44ce. PR #65 is OPEN / DRAFT / NOT MERGED; its seven changed files are only FiveLayer API/panel/candles/presentation and associated tests. Keep its PnL/freshness scope separate.
- Confirmed MainActivity runtime branch alone is insufficient isolation: parallel build type inherits debug and compiles common src/main; no Chart Pro source-set exclusion is defined. AndroidManifest still declares StrategyMonitorService and foreground-service permissions for both variants.
- FiveLayerStandaloneDashboard -> FiveLayerPanel subtree has no direct source references to CompleteDashboard, MarketEngine, MultiSymbolScanner, StrategyMonitorService or direct Binance OrderBookEngine. FiveLayer-specific API/candle/paper/Hummingbot snapshot components can remain.
- Chart Pro candidate groups: CompleteDashboard, MarketEngine/chart models, ChartAnalytics, ChartMarketSession, BacktestPanel, chart alert classes, BinanceRestGate, MultiStreamSignalEngine, MultiSymbolScanner/ScannerMarketFeed/SnapshotRetryGate, direct Binance OrderBookEngine/Panel/Sequence, StrategyMonitorService. MainActivity, Gradle, Manifest and app resources need five-layer-only rewrite.
- StrategyEngine.kt and StrategyEngineTest.kt are protected as CORE STRATEGY candidates; preserve RSI/ADX/Smart DCA/TP/SL behavior and thresholds. Do not delete or change until owner/placement is decided. Preserve HummingbotOrderBook + OrderBookAnalytics for T3.
- Separate Chart Pro repo exists, but seven sampled source files (MainActivity, CompleteDashboard, MarketEngine, StrategyEngine, MultiSymbolScanner, BinanceRestGate, ChartAnalytics) have different blob SHAs from PR #65 source. This is not a byte-identical copy; do not blindly delete or overwrite. Line-level reconciliation is required.
- Status: Activity-level runtime routing PASS; FiveLayerPanel dependency boundary PASS at inspected source level; source-set/DEX isolation NOT VERIFIED; manifest isolation FAIL at source level; Chart Pro source parity NOT VERIFIED; no source/build/test changes in this increment.
- Next: finish line-level parity/migration manifest, then add RED APK-content + manifest contract and isolate a five-layer-owned Android application identity/source set. Do not mix into PR #65 or PR #134; keep both PRs unmerged pending explicit approval.


## 2026-11-05 — Remove BTC Chart Pro from the five-layer system

- User direction: prioritize removing Chart Pro components from the five-layer repository; no source parity or migration to the separate Chart Pro repository is required.
- Cleanup branch: `cleanup/remove-chart-pro-from-five-layer-20261105`; PR #135: https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/135 (OPEN / DRAFT / NOT MERGED). Base `feature/android-five-layer-control` at `2a4b914f5e1f133544494278f3bf5117ff815418`; PR head at evidence checkpoint `ba2b18c963b237fffc7337deb2dffaf90ba47f05`.
- Evidence report: `docs/evidence/FIVE_LAYER_CHART_PRO_REMOVAL_2026-11-05.md` on PR #135 branch (blob `d3751ec06d5420f6e81505a6add954ec22adfcee`).
- Removed 18 Chart Pro-only Android source files and 10 Chart Pro tests: chart alert/history, chart analytics/session, CompleteDashboard, Binance MarketEngine/REST gate, scanner and signal stream, direct Binance OrderBook engine/panel/sequence, local StrategyEngine and StrategyMonitorService. Removed obsolete parallel resources and dual-APK/release-signing CI scripts.
- Android app now has one five-layer entrypoint (FiveLayerStandaloneDashboard), one applicationId `com.kenznguyen.fivelayerpaper`, one debug build variant, five-layer label/icon, INTERNET-only permission and no StrategyMonitorService/foreground-service/notification permissions. No Chart Pro APK source path remains in the Android source tree.
- Renamed FreqAI research strategy `ChartProFreqaiResearch` to `FiveLayerFreqaiResearch`, updating config, README and smoke test. Preserved Python `pipeline/core_strategy.py` and its test files; RSI/ADX/Smart DCA defaults were inspected and unchanged.
- Preserved T0–T4, FiveLayer API/panel/candles/presentation/paper history, Hummingbot snapshot parser and OrderBookAnalytics, Shared Risk Engine/Kill Switch, paper ledger, React dashboard and canonical data. No T0 source, database, Feeder, lease, exchange ingestion, live execution or order endpoint changed.
- Added `ci.test_five_layer_android_boundary`, `ci.test_five_layer_android_apk` and `ci/verify-five-layer-android-apk.py`. Codemagic Android workflow renamed to `five-layer-android`, building one debug APK and checking package/label/DEX/manifest/signature.
- Verification: Git tree/source inventory PASS; Strategy Core source/defaults inspection PASS. New static tests NOT RUN; Android unit tests/build NOT RUN; APK DEX/manifest artifact NOT VERIFIED; Codemagic run/artifact NOT VERIFIED. PR #135 is draft and unmerged; do not merge without explicit approval.
- PR #65 remains OPEN / DRAFT and was not modified. Its 7-file PnL/freshness additions are on a divergent head based on an older base and are not included in this cleanup branch; preserve that work for a controlled rebase/replay after the cleanup boundary is accepted. PR #134 remains OPEN / DRAFT / NOT MERGED and untouched.
- Next: obtain Codemagic `five-layer-android` result on exact PR head; run Core Strategy + relevant T0–T4 regressions; inspect APK artifact JSON, DEX and merged manifest; review PR #135 diff/mergeability. Do not close PR #65 or merge any PR without explicit approval.


- PR #135 mergeability rechecked via GitHub API after evidence commit: `mergeable=true`, `mergeable_state=clean`; head `ba2b18c963b237fffc7337deb2dffaf90ba47f05`, base `2a4b914f5e1f133544494278f3bf5117ff815418`. This is only Git mergeability, not test/build acceptance. PR remains DRAFT / NOT MERGED.


- Follow-up hygiene commit after the evidence checkpoint: `b8af26a039a0089ae3469cd4727ca1e4a1d6db18` (removed stale chart-simulation comment and renamed Android preferences namespace to `five_layer_state_v1`). Current PR #135 head: `b8af26a039a0089ae3469cd4727ca1e4a1d6db18`; GitHub mergeability after this update: `true` / `clean`. This is not build/test evidence.


## 2026-11-05 — Five-layer cleanup: preserve existing Android install and T0 boundary

- User clarified the acceptance target: remove Chart Pro without affecting T0 or the five-layer system; do not pursue Chart Pro repository parity.
- Review found two avoidable Android upgrade regressions in the initial cleanup candidate: changing applicationId away from the existing five-layer parallel APK identity, and changing the SharedPreferences namespace used for the saved API URL.
- Corrected PR #135 to retain applicationId `com.kenznguyen.btclivealerts.paper` and SharedPreferences namespace `strategy_state_v1`. Added boundary assertions and changed APK verifier expected package accordingly.
- No T0 source paths are included in PR #135's 55 changed files. T0 DB, canonical data, Feeder, lease/fencing, recovery and exchange ingestion remain outside the diff. T1/T3/T4 backend source remains untouched; T2 FreqAI research class/config naming and Android/CI/docs are changed as part of ownership cleanup.
- PR #135 current source checkpoint after compatibility correction: `907c5d254d3f832f7d5062ac22b3c529305a6c20`; OPEN / DRAFT / NOT MERGED. Codemagic and GitHub Actions run lookup did not return a workflow run for this SHA. Static tests, Android unit tests, APK build, Core Strategy tests and T0–T4 regression tests remain NOT RUN/NOT VERIFIED.
- Important remaining compatibility check: compare debug APK signing certificate against the currently installed five-layer APK before claiming in-place upgrade is guaranteed. Same package ID and preference key are preserved, but Android also requires compatible signing identity.
- Next: run boundary/verifier tests, Core Strategy and relevant T0–T4 regressions, then Codemagic `five-layer-android`; verify exact SHA, APK package, certificate, manifest and DEX. Do not merge PR #135 without explicit approval. PR #65 and #134 remain untouched.

- Final follow-up evidence commit on PR #135 branch: `0cf57e7bcd015cf4638642fa7ae6efd757945311`; this is the latest PR head after updating the evidence report. PR #135 remains OPEN / DRAFT / NOT MERGED and GitHub reports mergeable=true.
- Exact PR file inventory was rechecked: 55 changed paths; no T0 data foundation, canonical market-data, feeder, lease/fencing, recovery or exchange-ingestion source path is part of the diff. The `ci/release-android.sh` path is an obsolete Chart Pro Android release script, not T0.
- GitHub Actions workflow lookup for the latest PR SHA returned no PR-triggered runs. Codemagic run/artifact remains NOT VERIFIED; do not mark the change accepted based on mergeability.

## 2026-11-05 — Full CI gate coverage for Chart Pro cleanup branch

- Continued PR #135 validation. Found Codemagic branch filters only included the cleanup branch for `five-layer-android`; `canonical-market-data` and `five-layer-dashboard` would not run on this branch.
- Updated `codemagic.yaml` to include `cleanup/remove-chart-pro-from-five-layer-20261105` in both missing workflow branch filters. Since the changed paths include `codemagic.yaml` and `ci/`, all three workflows' changeset gates match.
- Added `test_cleanup_branch_runs_android_data_and_dashboard_gates` to `ci/test_five_layer_android_boundary.py`, asserting all three workflows include the cleanup branch. Corrected its YAML section extraction to use top-level section boundaries.
- Static YAML section check: PASS for `five-layer-android`, `canonical-market-data`, `five-layer-dashboard`; each has the cleanup branch and changeset filter. Python test, YAML parser, Codemagic execution, and artifacts remain NOT VERIFIED / NOT RUN.
- PR #135 latest known head before evidence commit: `ed9fc45248b25669a849f98a5844977ed2deccb0`. PR remains OPEN / DRAFT / NOT MERGED. No T0 source, DB, Feeder, lease/fencing, recovery or ingestion files changed. PR #65 and #134 untouched.
- Next: obtain Codemagic runs for all three workflows on the final PR SHA; confirm canonical-market-data tests (T0/T1/Core Strategy/paper integration), dashboard test/build, Android unit tests and APK verification. Verify APK signer continuity before asserting upgrade compatibility. Do not merge without explicit approval.

- Final evidence report update committed on PR #135 branch: `e197715ef4623af2e490b08da2499a97831fa779`; current PR head must be read from PR metadata after this evidence update.
- Protected source SHA comparison against the PR base returned identical blobs for `pipeline/core_strategy.py`, `pipeline/test_core_strategy.py`, `pipeline/core_signal.py`, `pipeline/test_core_signal.py`, `paper_execution/risk_control.py`, and `paper_execution/ledger.py` (values recorded in the evidence report). This is source-integrity evidence, not executed regression evidence.
- PR #135 exact changed-file inventory remains 55 paths; no T0 `market_data`, `futures_intelligence`, integration/Feeder/lease/fencing/canonical-data path is modified. Codemagic branch filters now include the cleanup branch for Android, canonical-market-data and dashboard workflows; static configuration check PASS.
- Latest workflow/status lookup for the evidence checkpoint returned no GitHub Actions PR workflow runs or status checks. Codemagic is not connected to the available tools in this session; all runtime CI and artifact gates remain NOT VERIFIED. Do not merge.

## 2026-11-05 — PR #135 CI runner migration: Codemagic to GitHub Actions

- User reaffirmed the project decision: GitHub Actions is the default and official CI runner; Codemagic is not used for the normal five-layer repository workflows.
- Applied migration on existing PR #135 branch `cleanup/remove-chart-pro-from-five-layer-20261105`; no parallel PR/branch was created.
- Added `.github/workflows/five-layer-pr-validation.yml`: three isolated jobs for Android Paper, backend T0–T3/Core, and T4 Dashboard. Triggers on PRs targeting `feature/android-five-layer-control`, pushes to the cleanup branch, and manual dispatch.
- Each job checks out the exact PR head SHA, uses `contents: read`, does not receive production credentials or production database configuration, and keeps `AI_EXECUTION_ENABLED=false`.
- Retired `codemagic.yaml`, `docs/CODEMAGIC_SETUP.md`, and Codemagic-only `ci/setup-android.sh`. README and evidence now describe GitHub Actions as the runner. Replaced obsolete Codemagic policy tests with GitHub Actions policy tests.
- Initial GitHub Actions run on SHA `c6de7e06acfef4d6f8e7d20cec145c5a2697afdf` failed because the boundary test edit was malformed (duplicated method after `unittest.main()`). Corrected by rewriting the test file. Do not describe this attempt as PASS.
- Corrective source SHA before the evidence-only follow-up: `d7cce0172cb7b25a8a7cd0feb0a4ce4a521f1b99`. Exact PR run #42044440154 was IN_PROGRESS and push run #42044431785 QUEUED when recorded; neither was PASS at that point.
- The cleanup PR's declared base is older than current main. The T0 regression commands in this workflow are restricted to T0 test modules that exist on that branch: `market_data.test_store`, `market_data.test_sync`, `market_data.test_storage`, and `market_data.test_api`. Newer feeder scheduler/recovery acceptance modules present on current main are not part of this PR's branch and are not claimed as executed by this PR workflow.
- T0 source paths remain outside PR #135's changed-file inventory; protected Core Strategy, signal, Paper Risk and Ledger files remain byte-identical to PR base. PR #65, PR #134 and main T0 source were not modified by this migration.
- Current status at this handoff update: workflow/config migration **IMPLEMENTED**; boundary test repair **COMMITTED**; latest CI **PENDING / NOT VERIFIED**; Android build/APK/signing continuity **NOT VERIFIED**; backend and Dashboard latest-SHA acceptance **NOT VERIFIED**.
- PR #135 remains OPEN / DRAFT / NOT MERGED. Do not merge, deploy T0, create canonical DB, start Feeder, connect exchange, or enable live execution based on this migration.


## 2026-11-05 — PR #135 GitHub Actions validation follow-up

- Latest PR #135 branch source SHA: `de93f0e5353a79bb13611f72067442cfaaefc005`.
- CI trigger policy refined to run automatically on pull requests targeting `feature/android-five-layer-control` plus manual dispatch. Removed duplicate push trigger because branch pushes already synchronize the open PR and previously caused duplicate runs; concurrency key separates event contexts.
- On prior SHA `79d51e487a50b09e7472a13f37cccca0e23b71ec`, backend T0–T3/Core regression job PASS and T4 Dashboard test/build/audit job PASS. Artifacts: backend `13421689873`, digest `sha256:3227003f0dc58b333e133c6b1f1bf5efa61954d687ca98fbd06645711d2c7444`; Dashboard `13423997573`, digest `sha256:2e5189f9889b8a99ab31a1e7b888b286ee6fccfe97768e2673409a21b84a0eb3`. These are not artifacts for the latest SHA.
- Android boundary/APK contract tests passed on SHA `79d51e...`; Android SDK setup initially failed due deprecated `tools` package. A subsequent direct SDK install attempt failed because `yes` exited with SIGPIPE under pipefail.
- Replaced license acceptance input with finite `printf` input and pinned SDK package installation. Latest PR run #42045293791 on exact SHA `de93f0e5353a79bb13611f72067442cfaaefc005`: backend job PASS; Dashboard job PASS; Android boundary tests PASS; JDK 17 and pinned Android SDK installation PASS; Gradle 8.9 setup PASS; Android `:app:testDebugUnitTest` was still IN_PROGRESS at this handoff snapshot. APK build, verifier and artifact remain NOT VERIFIED until job completion.
- Latest PR run URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42045293791.
- T0 regression in this PR branch is limited to available modules `market_data.test_store`, `market_data.test_sync`, `market_data.test_storage`, and `market_data.test_api`; the PR's old base branch does not contain newer feeder scheduler/recovery modules. T0 source remains unchanged by the PR. This does not replace the separate current-main T0 acceptance runs.
- Codemagic config/docs/setup script have been removed from the PR branch. GitHub Actions is the sole automatic CI runner for this PR.
- PR #135 remains OPEN / DRAFT / NOT MERGED. Do not merge, deploy T0, provision canonical DB, start Feeder, connect exchange, or enable live execution based on this CI migration.


## 2026-11-05 — PR #135 Android compile failure and correction

- Exact PR workflow run #42045293791 on source SHA `de93f0e5353a79bb13611f72067442cfaaefc005` completed with failure only in the Android job. Backend T0–T3/Core job PASS; T4 Dashboard job PASS.
- Android source-boundary and APK verifier contract tests PASS. JDK 17, Android SDK 35 / Build Tools 34.0.0 installation, and Gradle 8.9 setup PASS.
- Android unit-test compilation failed at `android-app/app/src/test/java/com/kenznguyen/btclivealerts/FiveLayerApiTest.kt:199`: Kotlin overload ambiguity for `JSONObject.put("nextBeforeId", null)` because null matches collection/map/Any overloads.
- Root cause is test fixture JSON null construction, not a production API or T0 issue. Corrected fixture to use explicit `JSONObject.NULL`, preserving the intended JSON null value. Commit/source SHA: `29328907b71f5c7f7a171a46d319fc4dc64f322e`.
- Run #42045293791 artifacts on prior SHA de93: backend ID `13424620454`, digest `sha256:424181cb948ff4f119748a37ef35b5881eb687b8e80f58cb59136c9a30c5e7e1`; Dashboard ID `13423944222`, digest `sha256:24be23019c613b22b02dbfbb9515d5bf6e32fd8ee9bf6f3af8356f97082c5ace`; Android artifact ID `13423849570` was only a 199-byte empty/failure evidence archive, not an APK.
- Latest source checkpoint after the test fixture fix is `29328907b71f5c7f7a171a46d319fc4dc64f322e`. The rerun is required; Android unit tests, APK build, APK verification and signing continuity remain NOT VERIFIED until the rerun succeeds.
- No production Android behavior, T0 source, Core Strategy, Paper Risk/Ledger, canonical DB, exchange or Feeder runtime changed. PR #135 remains OPEN / DRAFT / NOT MERGED.


## 2026-11-05 — Android Gradle dependency egress failure and mirror mitigation

- The Android test fixture fix `JSONObject.NULL` was committed at PR #135 source SHA `29328907b71f5c7f7a171a46d319fc4dc64f322e`.
- Exact-head rerun #42045784920 confirmed the previous Kotlin compile ambiguity no longer appeared; Gradle configuration instead failed before compilation because fetching `org.jetbrains.kotlin:kotlin-compiler-embeddable:2.0.21` redirected to GitHub Releases and returned HTTP 504 twice.
- Classified this as a dependency transport failure, not a code/test assertion failure. No test was skipped and no acceptance threshold was weakened.
- Added Google Cloud's Maven Central mirror ahead of the default Maven Central repository in Android `pluginManagement` and `dependencyResolutionManagement`: `https://maven-central.storage-download.googleapis.com/maven2/`. Default Google/Maven Central/Gradle Plugin Portal repositories remain as fallbacks.
- PR #135 source SHA after mirror addition: `5aedfe7c6f55163b3bbb5a3b6c82677da0272eb1`. New exact-head GitHub Actions run is required to determine whether the mirror resolves the artifact reliably.
- Backend and Dashboard had PASS on prior exact SHA `de93f0e5353a79bb13611f72067442cfaaefc005`; they must rerun on the new SHA before current acceptance.
- Android APK build, DEX/manifest/package/signature verification, and signing continuity remain NOT VERIFIED. PR #135 remains OPEN / DRAFT / NOT MERGED.


## 2026-11-05 — PR #135 T4 validation scope relaxed by user

- User confirmed T4 Dashboard will be rebuilt; strict React tests, production build, dependency audit, and T4-specific CI blocking are unnecessary for the current cleanup.
- T4 source/data must remain intact until the rebuild scope is defined. No T4 application code or data was deleted in this adjustment.
- Updated PR #135 workflow: renamed the job to `dashboard-boundary`, reduced it to checking that `control_dashboard/package.json` and `package-lock.json` exist and parse, and set `continue-on-error: true`. T4-only failures therefore do not fail the overall workflow or block other jobs.
- Updated `ci/test_ci_policy.py` to enforce this minimum/non-blocking T4 policy and ensure no npm install/test/build/audit gate remains in the T4 job.
- Strict validation remains for Android Paper boundary/unit/APK verification and backend T0–T3/Core Strategy/Paper Risk/Ledger regression. `AI_EXECUTION_ENABLED=false`; no production DB, exchange credentials, Feeder, or live execution is enabled.
- Commits on existing branch `cleanup/remove-chart-pro-from-five-layer-20261105`:
  - CI policy test: `e12370382a7402afbc4aa784ab23358c20e5d617`.
  - Workflow adjustment: `03275ec43487b14e417ed94c67106d1f7c98d21f`.
  - Evidence report: `e4bdff8b44a2ba453fb2755c437327d2e4d430e4`.
- Current PR #135 head: `e4bdff8b44a2ba453fb2755c437327d2e4d430e4`. Exact-head CI after this change is **PENDING / NOT VERIFIED**. Prior run #42046383582 and its artifacts validate the earlier SHA `5aedfe7c6f55163b3bbb5a3b6c82677da0272eb1`, not the current head.
- PR #135 remains OPEN / DRAFT / NOT MERGED. Do not merge without explicit user approval. PR #65 and PR #134 remain untouched; T0 production data/runtime and Core/Risk implementation were not changed.


### PR #135 T4 policy first CI attempt and correction

- Exact run #42047835005 checked out source SHA `e4bdff8b44a2ba453fb2755c437327d2e4d430e4`.
- T4 minimal boundary job PASS and did not block the workflow; backend T0–T3/Core/Paper regression job PASS.
- Android boundary suite failed only because `ci/test_five_layer_android_boundary.py` still expected the old workflow job marker `dashboard:` after the job was renamed to `dashboard-boundary:`. Android Gradle tests/build were skipped after that contract failure.
- Fixed the stale test marker in commit `f8209f1b2449d865ab916fd64359d443f45ef883`.
- Follow-up evidence commit: `3467021e12d7c564cc807755dddabffab020cd34`. New exact-head CI must be checked against the updated PR head; until then Android and overall current-head acceptance are **NOT VERIFIED**. Do not treat run #42047835005 as PASS.
- No T0–T3 production code, Core Strategy, Shared Risk Engine, T4 source/data, DB, Feeder, exchange access or execution mode was changed.


## 2026-11-05 — PR #135 final review and APK artifact policy

- PR #135 remains the controlled cleanup of BTC Chart Pro-only components from the Five-layer repository. Current base is feature/android-five-layer-control at 2a4b914f5e1f133544494278f3bf5117ff815418.
- Compared PR branch with base: 97 commits ahead, 0 behind. The changed-file inventory contains no T0 source paths. The six protected Core Strategy/signal/Paper Risk/Ledger source and test files remain byte-identical to base (blob SHA evidence is recorded in docs/evidence/FIVE_LAYER_CHART_PRO_REMOVAL_2026-11-05.md).
- User requested that APK may be removed from CI deliverables. Kept Android unit tests, debug APK assembly and APK identity/manifest/DEX verifier as blocking build checks, but removed artifacts/*.apk from uploaded artifact contents. The Android artifact now retains source SHA, test reports and android-apk.json metadata only.
- Added a CI policy assertion that APK files are not uploaded. Commits: workflow 660668ef68423229b21babbf0cff47c2dd67a813; CI policy test eac8c22b0cba710226a413d4b788df5f5197beab; evidence update 849af0614e4c6f1b0d9419cb6b8a463d6cb9a2ee.
- Prior exact-head run #42048061499 on SHA 3467021e12d7c564cc807755dddabffab020cd34 passed Android, backend T0-T3/Core/Paper and T4 minimum-boundary jobs. It predates the APK artifact-policy change and is not acceptance for the new head.
- Current PR head at handoff update: 849af0614e4c6f1b0d9419cb6b8a463d6cb9a2ee. Exact-head GitHub Actions after the artifact-policy change must complete successfully before the PR is marked ready. Runs #42049165020 (workflow commit 660668e...) and #42049181829 (policy commit eac8c22...) were in progress at the time of inspection; the final evidence commit may trigger a further exact-head run.
- Status: source-scope review PASS; protected Core/Risk file identity PASS; no T0 source diff PASS; APK artifact exclusion configuration PASS; latest exact-head CI PENDING / NOT VERIFIED; existing installed APK signer continuity NOT VERIFIED.
- T4 remains source-retained and its CI boundary is non-blocking by user direction. T0–T3/Core/Risk gates remain blocking. AI_EXECUTION_ENABLED=false; no production DB, exchange credentials, Feeder activation or live execution is authorized.
- PR #135 remains OPEN / DRAFT / NOT MERGED. Do not merge without explicit user approval. PR #65 and PR #134 remain untouched.

## 2026-11-05 — PR #135 exact-head acceptance completed

- PR #135 source SHA tested: `849af0614e4c6f1b0d9419cb6b8a463d6cb9a2ee`.
- GitHub Actions run #42049228828: **SUCCESS**. Android Paper job 127320495187 PASS; backend T0–T3/Core/Paper isolation job 127320494121 PASS; T4 minimum boundary job 127320494634 PASS (non-blocking by user direction).
- Android completed source-boundary/APK contract tests, Gradle unit tests, debug APK assembly, and package/signer/manifest/DEX verification.
- Backend completed Python compilation and the configured T0 storage/sync/read API, T1 futures intelligence, T2 Core/FreqAI, T3 risk/ledger/Hummingbot and CI policy regressions.
- Artifacts for run #42049228828: Android metadata/reports ID 13424859409 (sha256:ec4bea98b465c3377e259e0b2a1e8ff52d5a195e29e626b558f14f6f94c9e0a9); backend evidence ID 13425896747 (sha256:98bbfb1bfe10751f011d48732bc17f8fc9fc3649573c32e9e30297ff402123d4).
- Android artifact ZIP inspected: source SHA matches; contains source SHA file, unit-test reports and android-apk.json; contains no APK. Metadata reports package com.kenznguyen.btclivealerts.paper, debug/PAPER_ONLY, no Chart Pro DEX markers, manifest and permission isolation PASS. The APK was built temporarily for verification only and not uploaded.
- Overall PR #135 cleanup acceptance: **PASS** for configured CI and artifact policy. Existing-install signer continuity and physical device installation remain **NOT VERIFIED**. No T0 production deployment, canonical DB creation, Feeder activation, exchange access, or live execution.
- PR #135 remains OPEN / DRAFT / NOT MERGED until moved to Ready for review; merge requires explicit user approval. PR #65 and PR #134 remain untouched.


## 2026-11-05 — PR #135 merge and PR #134 T0 CI provenance update

### PR #135 — legacy bridge / Chart Pro cleanup
- PR #135 was merged into `feature/android-five-layer-control`.
- Merged source head: `f200251c8cc13160913155180f019291793bf640`.
- Merge commit: `96244d6f0b44c7621b4782abaa9d08596646349c`.
- Exact-head GitHub Actions run #42056221905: SUCCESS, 3/3 jobs. Android Paper, backend T0–T3/Core/Risk/Ledger, and non-blocking T4 manifest boundary all passed.
- Android metadata artifact ID 13429662311, digest `sha256:deddcb520cda1617d994e94c87c233a8d76147f41336e2868927fcfef30e339b`; backend artifact ID 13429087211, digest `sha256:e224bfaff42f6c680d86e98fb37b0debec9f200c59af5e035b471be97ee05125`.
- The merge retired the old Flask/Telegram/Codemagic dispatch bridge and old HTML dashboard while preserving the T0–T3/Core/Risk/Ledger/Hummingbot source and the T4 rebuild target, as scoped by PR #135.
- Independent Codex review receipt for the final PR head was not present before merge: **NOT VERIFIED**. Existing-install signing-certificate continuity and physical Android installation remain **NOT VERIFIED**.
- PR URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/135
- Merge URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/commit/96244d6f0b44c7621b4782abaa9d08596646349c

### PR #134 — T0 atomic write fencing
- Current state at this handoff update: OPEN / NOT MERGED; branch `feature/t0-atomic-write-fencing-20261105`; PR head `d0f503ee3ba987784daa36e904588829c44e93b6`; base `feature/t0-centralized-data-feeder-p1-20261101` at `8b196d2720eab804728df7c0227c606c094b16ad`.
- Latest observed workflow run #42030968449: event `pull_request`, conclusion SUCCESS, 2/2 jobs. PR head SHA is `d0f503ee3ba987784daa36e904588829c44e93b6`; logs prove the jobs checked out synthetic merge SHA `510ca182aea15cfbc10694601d85c1aefb6c0f04` (PR head merged into base), not a direct PR-head checkout. Therefore this is **merge-context PASS**, not direct-head-only verification.
- Static Gateway / feeder / market_data regression job: 201 tests completed successfully.
- Disposable TimescaleDB job: PostgreSQL writer integration 7/7, Feeder runtime integration 10/10, role privilege integration 4/4, read-only TimescaleDB integration 6/6. This disposable CI database was torn down; it is not the canonical T0 database.
- Artifacts: Gateway evidence ID 13415403895, digest `sha256:03ec5474720cc0ac71193b1403541daa325263a28b519087e8451ea7e5a9f6fc`; TimescaleDB evidence ID 13416940060, digest `sha256:b5f1b11b227f262e342c9fbbe35d6809349d8bccb0c6ac23d71d09ca08dd7824`. These are GitHub artifact upload digests; payload bytes have not been independently downloaded and re-hashed in this reconciliation.
- No PR review submissions or inline review threads were present at inspection.
- PR URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/134
- Workflow URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42030968449

### PR #111 disposition
- PR #111 is CLOSED / NOT MERGED. Preserve its RED-contract history as an audit record; do not reopen or delete its branch unless explicitly requested.

### Safety and next action
- No canonical T0 database creation, production Feeder activation, exchange connection, market-data synchronization, deployment, or live execution was performed or authorized.
- Keep `ai_execution_enabled=false`.
- Next permitted work: continue the scoped PR #134 source/review assessment, keep PR #134 unmerged pending independent review and explicit user approval. Do not equate synthetic merge-context CI with direct-head verification or production readiness.


## 2026-11-05 — PR #134 scoped source review: SQLite provisioning blocker

- Reviewed the PR #134 Gateway/Feeder runtime composition after reconciling workflow #42030968449. Review found a blocking safety/correctness issue in `market_data/feeder_service.py`.
- In the SQLite branch of `build_runtime()`, `initialize_store()` is called before `SQLiteWriteGateway` construction. The changed `SQLiteStore.initialize()` constructs `CandleStore(self.path)`; `CandleStore.__init__` creates parent directories, opens SQLite, and creates the candles table. Thus a missing canonical DB is created before the Gateway's `is_file()` fail-closed check.
- The existing direct-Gateway missing-DB test does not cover this runtime composition path. Required fix: remove implicit initialization from production/runtime composition; keep DB provisioning explicit and separately authorized; add a regression that exercises `build_runtime()` with a missing path and proves no directory/DB is created and startup fails closed.
- Finding recorded in PR #134 comment [#6662614013](https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/134#issuecomment-6662614013). A formal REQUEST_CHANGES review could not be submitted because the authenticated user is the PR author; the finding is documented as a self-review blocker instead.
- PR #134 status remains OPEN / DRAFT / NOT MERGED. No source fix has been applied yet. Current PR head remains `d0f503ee3ba987784daa36e904588829c44e93b6`; current CI remains merge-context PASS only (synthetic checkout `510ca182aea15cfbc10694601d85c1aefb6c0f04`).
- Next action: correct the implicit DB creation path on the existing PR branch, add the missing-path runtime regression, run relevant tests and exact-provenance GitHub Actions, then self-review again. Do not merge PR #134 until resolved.
- No canonical DB was created/opened, no Feeder started, no exchange contacted, no market data synchronized, and no live execution. `ai_execution_enabled=false`.


## 2026-11-05 — PR #134 fail-closed runtime correction
- Fixed the self-review blocker: `build_runtime()` no longer calls SQLite `initialize()`; missing canonical DB now fails closed before provisioning. Explicit DB setup remains separate.
- Added `test_build_runtime_does_not_create_a_missing_canonical_sqlite_database`; it asserts FileNotFoundError and no DB/parent creation. Two existing disposable fixtures now provision explicitly.
- Final head `c09fe85fab7de3ec799cfed37087718dfa6b87c4`; run [#42060578659](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42060578659) SUCCESS 2/2. Both jobs checked out synthetic merge `634ee1c9c1337e730e736f413fc5cd6868b2a6d0`; direct-head-only verification NOT VERIFIED.
- Static: 202 market_data tests PASS (10 Gateway contracts, 59 focused, 21 Health/Readiness, 2 process tests are overlapping subsets). Disposable TimescaleDB: writer 7/7, FeederRuntime 10/10, role privileges 4/4, read-only 6/6 PASS.
- Artifacts: 13432026320 `sha256:ac441602e12f6ac706e2da4c9d3cd35be6a2be99d068586a7926df81ef0e711d`; 13431121903 `sha256:c673dd36760ca909408903ec26b3c539da7aee77e0d6eb169987dd1fb412ba98`. Upload digests; payload hashes not independently recomputed.
- PR #134 remains DRAFT / OPEN / NOT MERGED. No canonical DB/Feeder/exchange/sync/deployment/live execution. `ai_execution_enabled=false`.


## 2026-11-05 — PR #134 independent review request
- Requested an independent Codex review of exact PR head `c09fe85fab7de3ec799cfed37087718dfa6b87c4` in PR comment #6662766709.
- Review scope: SQLite fail-closed runtime composition, SQLite/PostgreSQL lease fencing and atomicity, PostgreSQL runtime composition/least privilege, T0 data integrity, and Feeder recovery. Reviewer was asked not to modify files or merge.
- Review result: **PENDING / NOT VERIFIED** at this handoff update. Do not send duplicate review requests while this request is pending.
- PR #134 remains DRAFT / OPEN / NOT MERGED. No merge or production activation authorized.


## 2026-11-05 — PR #135 post-merge Codex findings and follow-up

### PR #135
- PR #135 is merged into `feature/android-five-layer-control`.
- Merged base SHA confirmed by PR #136 creation: `96244d6f0b44c7621b4782abaa9d08596646349c`.
- Merged source head: `f200251c8cc13160913155180f019291793bf640`.
- Exact-head CI before merge: run #42056221905, SUCCESS, 3/3 jobs; this evidence applies to PR #135 source head only.
- Codex review receipt for `f200251c8c` subsequently surfaced two additional findings:
  1. `ci/run-legacy.py` still exposed scanner/Telegram/dashboard modes after their targets and Codemagic adapter had been retired; scanner could exit successfully without producing a scan.
  2. Root README overstated T0 Gateway/Feeder regression coverage. The active workflow runs T0 Store, Sync, Storage and read API tests; it does not run a dedicated Gateway/Feeder suite.

### Follow-up PR #136
- PR: https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/136
- Branch: `cleanup/pr135-codex-followup-20261105`.
- Base: `feature/android-five-layer-control`, base SHA `96244d6f0b44c7621b4782abaa9d08596646349c`.
- Current head SHA: `032fc304345f32756c6730f85c39c916f0d2adef`.
- Changes: delete `ci/run-legacy.py`; add it to `RETIRED_PATHS` in `ci/test_legacy_bridge_retirement.py`; correct README's T0 coverage description.
- Commits:
  - README correction: `d61850c9630529c900c4d1f160cd1f9946180386`.
  - Retirement regression: `75ecff06c000b0ef397713eb9e009aa3a56291bb`.
  - Legacy runner deletion: `032fc304345f32756c6730f85c39c916f0d2adef`.
- PR #136 remains DRAFT / OPEN. No GitHub Actions workflow run or status check is present yet for head SHA `032fc304345f32756c6730f85c39c916f0d2adef`; verification is **NOT RUN / NOT VERIFIED**. Do not treat PR #135 CI as evidence for this new source.
- No T0 source/runtime changes; no canonical DB, Feeder, exchange, market-data sync, or live execution.
- Next: obtain exact-head GitHub Actions run for PR #136; inspect logs and artifacts; self-review the diff; update PR and handoff. Only mark ready after verification and review. Merge requires explicit user approval.


### PR #136 CI progress — run #42068647963 (updated 2026-11-05)

- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42068647963
- PR head SHA: `032fc304345f32756c6730f85c39c916f0d2adef`; workflow checked out the exact PR head per the active workflow's checkout configuration.
- T0–T3/Core/Risk/Ledger backend job ID `127389933031`: **SUCCESS**. Compile, legacy bridge retirement regression (including the new retired-runner path), T0 Store/Sync/Storage/API tests, T1, T2, T3 and CI policy tests all completed. This run does not include a dedicated Gateway/Feeder suite.
- Backend artifact ID `13435410626`, name `five-layer-backend-42068647963-1`, size 6,030 bytes, digest `sha256:fe515ffb4c53d2a59c2c871c3f0529b6116172f37fcec83de74a79aba3b5baca`; unexpired at metadata check.
- T4 minimum boundary job ID `127389932371`: SUCCESS (non-blocking).
- Android job ID `127389932589`: **IN PROGRESS** at last check; unit tests passed and debug APK build was still running. APK verification and artifact upload had not completed.
- Overall PR #136 CI: **IN PROGRESS / NOT YET PASS**. Do not mark the PR complete or merge until Android job and exact-head evidence finish and the diff receives final review.


### PR #136 exact-head CI completion — 2026-11-05

- GitHub Actions run #42068647963 completed with **SUCCESS, 3/3 jobs** on PR head `032fc304345f32756c6730f85c39c916f0d2adef`.
- Run URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42068647963
- Backend job `127389933031`: PASS. Regression summaries: legacy retirement 5/5; T0 Store/Sync/Storage/API 35/35; T1 10/10; T2 56/56; T3 42/42; CI policy 5/5; Python compile PASS.
- Android job `127389932589`: PASS. Boundary/APK verifier tests 16/16; Android unit tests PASS; debug APK build SUCCESS; verifier reported `Verified five-layer-only APK for source 032fc304345f32756c6730f85c39c916f0d2adef`.
- T4 minimum boundary job `127389932371`: SUCCESS, non-blocking.
- Backend artifact ID `13435410626`, name `five-layer-backend-42068647963-1`, digest `sha256:fe515ffb4c53d2a59c2c871c3f0529b6116172f37fcec83de74a79aba3b5baca`.
- Android artifact ID `13433879418`, name `five-layer-android-42068647963-1`, digest `sha256:5c7f0633a90ecfe460143ae7198bb12390f1a83956e19ac634ba4ffb689b444f`.
- Artifact metadata associates both artifacts with branch `cleanup/pr135-codex-followup-20261105` and exact head SHA above. These digests are GitHub upload digests; payload bytes have not been independently downloaded and re-hashed here.
- Overall PR #136 CI: **PASS 3/3**. This validates the follow-up source SHA only. It does not add Gateway/Feeder test coverage; README now explicitly states that limitation.
- Independent Codex review requested in PR comment #6663897791; pending at handoff update.
- PR #136 remains OPEN / READY FOR REVIEW / NOT MERGED. Do not merge without explicit user approval.


## 2026-11-06 — PR #136 Codex P2 follow-up

- Independent Codex review completed on prior head `032fc304345f32756c6730f85c39c916f0d2adef` and reported P2: `ci/test_legacy_runner.py` still imported the deleted `ci/run-legacy.py`, causing `FileNotFoundError` during test discovery. Review thread: https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/136#discussion_r4483417138.
- Fixed on the existing PR #136 branch `cleanup/pr135-codex-followup-20261105`: deleted obsolete `ci/test_legacy_runner.py`.
- Commit / current PR head: `e5eb944c253bbe2ba441ee2f7b77ae861ed68ea4`.
- Existing `ci.test_legacy_bridge_retirement` still asserts `ci/run-legacy.py` is absent. No supported legacy-runner behavior is retained.
- PR #136 body and discussion updated to identify the finding and fix.
- Prior CI run #42068647963 validates only the previous SHA `032fc304345f32756c6730f85c39c916f0d2adef`; it is not evidence for the new head. Exact-head CI for `e5eb944c253bbe2ba441ee2f7b77ae861ed68ea4` is **PENDING / NOT VERIFIED** at this update.
- Fresh independent Codex review of the new head has not yet been requested; request after exact-head CI and self-review.
- PR #136 remains OPEN / NOT MERGED. Merge requires explicit user approval.
- No T0 source/runtime, DB, Feeder, exchange, market-data sync, or execution changes. `AI_EXECUTION_ENABLED=false`.
- Next: inspect exact-head Actions run, verify test collection and full configured gates, self-review changed files and stale references, then request Codex review on the final SHA. Do not merge automatically.


## 2026-11-06 — PR #136 exact-head CI and independent review complete

- PR #136 current head: `e5eb944c253bbe2ba441ee2f7b77ae861ed68ea4`; branch `cleanup/pr135-codex-followup-20261105`; base SHA `96244d6f0b44c7621b4782abaa9d08596646349c`.
- Exact-head GitHub Actions run #42071311091: **SUCCESS 3/3**. URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42071311091.
- Backend job `127399668850`: PASS — legacy retirement 5/5; T0 Store/Sync/Storage/read API 35/35; T1 10/10; T2 56/56; T3 42/42; CI policy 5/5; compile PASS.
- Android job `127399668153`: PASS — boundary/APK verifier 16/16; Android unit tests PASS; debug APK build PASS; verifier confirms five-layer-only identity, signer, manifest and DEX for exact source SHA.
- T4 job `127399669080`: PASS (non-blocking).
- Backend artifact ID `13436041657`, name `five-layer-backend-42071311091-1`, digest `sha256:ec871aa95e29920749e40fe6ef33d3acbfd266c7de8de69935d11d52b24eb0c5`.
- Android artifact ID `13435587810`, name `five-layer-android-42071311091-1`, digest `sha256:3d05b83e646e288c9966ab49604fd8e20429a335ec148be4718c4f0ef0cb5179`.
- Artifact digests are GitHub upload metadata; payload bytes were not independently downloaded/re-hashed.
- Codex review completed on exact head `e5eb944c253bbe2ba441ee2f7b77ae861ed68ea4`: no findings and no unresolved findings (summary comment #6663865157).
- P2 review thread #4483417138 was addressed by deleting obsolete `ci/test_legacy_runner.py` and has been resolved on GitHub.
- Self-review confirms README accurately limits T0 CI coverage; the obsolete test module is absent on the PR branch; retirement regression continues asserting `ci/run-legacy.py` absence.
- PR #136 remains OPEN / NOT MERGED; merge requires explicit user approval.
- No T0 source/runtime, DB, Feeder, exchange, market-data sync, or live execution changes. `AI_EXECUTION_ENABLED=false`.
- Next: await user decision on PR #136; do not merge without explicit approval. After approval/merge, record merge SHA and re-check base branch CI.


## 2026-11-06 — PR #136 merged

- User explicitly approved merge; PR #136 merged successfully.
- PR: https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/136
- Final PR source SHA: `e5eb944c253bbe2ba441ee2f7b77ae861ed68ea4`.
- Merge commit SHA: `0edd0032597ce11c9896b7182d358284e47edb85`.
- Verified GitHub PR state after merge: CLOSED / MERGED; `merged=true`; `merged_at=2026-11-05T17:14:30Z`.
- PR-head CI remains exact-head run #42071311091, SUCCESS 3/3, and Codex review on exact head reported no findings. These validate the PR source SHA, not a separately built artifact from the merge commit.
- Querying workflow runs for merge commit SHA returned no runs at the time of verification. Base-branch post-merge CI: **NOT VERIFIED / no run found**. Do not imply a fresh run on merge SHA.
- Changes merged: retire `ci/run-legacy.py`, protect its absence in retirement regression, remove stale `ci/test_legacy_runner.py`, correct README T0 CI coverage.
- T0 source/runtime unchanged; no DB/Feeder/exchange/market-data operations; `AI_EXECUTION_ENABLED=false`.
- T4 remains a non-blocking boundary check, not functionally certified.
- Next: check base branch workflow status and verify `feature/android-five-layer-control` points to the merge commit; do not activate T0/Feeder or live execution.


## 2026-11-06 — PR #136 post-merge branch reconciliation and next T0 work

- Compared `feature/android-five-layer-control` with merge commit `0edd0032597ce11c9896b7182d358284e47edb85`: GitHub compare status **identical**, ahead 0 / behind 0. Base branch therefore points exactly at PR #136 merge commit.
- PR #136 remains CLOSED / MERGED. PR-head CI #42071311091 is PASS 3/3 on source SHA `e5eb944c253bbe2ba441ee2f7b77ae861ed68ea4`; this is not a fresh base-branch workflow run. Available GitHub workflow-run lookup only exposes PR-triggered runs, and no post-merge run on the merge SHA was found through available lookup. Post-merge Actions execution remains **NOT VERIFIED**.
- Next active work is the existing T0 PR #134, not a new cleanup PR. Current PR #134: OPEN / DRAFT / mergeable; branch `feature/t0-atomic-write-fencing-20261105`; head `c09fe85fab7de3ec799cfed37087718dfa6b87c4`; base `8b196d2720eab804728df7c0227c606c094b16ad`.
- Codex review on PR #134 head `c09fe85...` reports findings and unresolved findings. Three P2 review comments:
  1. Pin PostgreSQL canonical lease identity so separate `T0_FEEDER_LEASE_NAME` values cannot create independent lease rows for the same canonical candle table (comment #4482929078, `market_data/feeder_service.py`).
  2. Validate the existing SQLite canonical schema before runtime/lease startup; an empty existing DB currently passes the file-exists check and can be mutated by lease-table creation before recovery fails (comment #4482929091, `market_data/write_gateway.py`).
  3. Prevent feeder-role direct `INSERT` into `market_data.candles` from bypassing Gateway lease fencing; current grants allow raw INSERT (comment #4482929107, `market_data/test_postgres_role_privileges.py`).
- PR #134 remains BLOCKED for merge until all findings are assessed and either fixed with test-first evidence or explicitly shown inapplicable. Existing CI success does not clear these source-level findings.
- No source changes made in this step. Next: inspect migrations, PostgreSQL Gateway SQL and role grants; add RED tests for fixed canonical lease identity, SQLite schema fail-closed startup and direct SQL insert denial; implement the smallest safe DB-side design; run focused suites and exact-source GitHub Actions. Keep all DB tests disposable; no canonical DB/Feeder/exchange/sync/deployment/live execution. `ai_execution_enabled=false`.


## 2026-11-06 — PR #134 first two Codex P2 mitigations (verification pending)

- Continued existing PR #134 on branch `feature/t0-atomic-write-fencing-20261105`; no new PR and no merge.
- Added regression contracts before implementation:
  - `market_data/test_postgres_feeder_runtime.py`: production PostgreSQL runtime rejects any `T0_FEEDER_LEASE_NAME` other than the single canonical identity `binance-btcusdt-canonical`. Test commit `d1d5aa610d9c62c4db8f6b8630d2175f2fdc698f`.
  - `market_data/test_write_gateway.py`: an existing empty SQLite file is rejected by Gateway construction and remains without tables. Test commit `180e0ee62d9187b0b9cf38b2e25d09b50870a7eb`.
- Implemented the corresponding mitigations:
  - `market_data/feeder_service.py`: production PostgreSQL runtime now rejects custom lease names and always uses `binance-btcusdt-canonical`. Commit `f6a214dc1b0e149f761d29327bee7286295df7cf`.
  - `market_data/write_gateway.py`: SQLite Gateway opens the existing DB read-only and validates the canonical candles columns/primary key before allowing runtime lease acquisition; if a lease table already exists, its columns/primary key are validated too. A missing lease table is allowed because `LeaseStore.acquire()` creates it after the canonical candles schema has passed validation. Commit `9688d176c4b0e9151111e11c33d27eca5d825059`.
- Current branch tip expected from sequential commits: `9688d176c4b0e9151111e11c33d27eca5d825059`. Exact PR-head metadata was not independently retrieved in this step; verify before any further writes.
- CI status: **NOT VERIFIED**. The available commit-workflow lookup returned no runs for the latest commit and only exposes PR-triggered runs; do not infer test pass or fail from that empty result. RED failure of the new tests was not captured as workflow evidence before implementation.
- Codex P2 #3 remains unresolved: PostgreSQL feeder role has direct INSERT on `market_data.candles`, allowing bypass of the fenced Gateway. Do not mark PR ready or merge.
- Next: design a DB-enforced writer boundary (likely a tightly scoped SECURITY DEFINER function with fixed search_path, explicit EXECUTE grant, and no direct INSERT privilege), add disposable TimescaleDB integration tests proving direct INSERT is denied while Gateway writes still work, then run exact-source CI and obtain a fresh Codex review. Keep tests confined to the disposable local TimescaleDB service.
- No canonical DB, production Feeder, exchange, sync, deployment, or live execution was started. T0 source changes are limited to the two mitigations above. `ai_execution_enabled=false`.


## 2026-11-06 — PR #134 PostgreSQL DB-enforced writer boundary (verification pending)

- Continued existing PR #134 on branch `feature/t0-atomic-write-fencing-20261105`; no new PR and no merge.
- Added role-boundary regression first in commit `af35fdb5208fca0948a2b5c9f409fc547fb64774`: Feeder login role is expected to have no direct candle INSERT and must write through the database function capability. The intended RED run was not captured; do not claim a demonstrated failing test.
- Added immutable migration `market_data/migrations/003_t0_database_fenced_candle_writer.sql` in commit `d68fd288329b946e410e29160640c4fdf3d9663a`, subsequently strengthened in `3b46ef3d56df6c379b5f61de26beabdb81116f02`:
  - Defines `market_data.write_canonical_candle(...)` as `SECURITY DEFINER` with fixed `search_path`, fully-qualified table references, DB-side lease row lock, owner/generation/expiry validation, idempotent duplicate handling and conflict rejection.
  - Revokes function EXECUTE from PUBLIC.
  - Creates stable NOLOGIN capability role `t0_feeder_writer`, revokes candle-table INSERT/UPDATE/DELETE/TRUNCATE from that capability role, and grants it EXECUTE on the fenced function.
- Changed `PostgresWriteGateway` in commit `63a1a59d806902a8c38f77765e3d3426deee0da7` to call the database function rather than directly SELECT/INSERT candle rows; maps DB lease denial and conflict SQLSTATEs to PermissionError/ValueError while retaining transaction rollback and final lease-expiry check.
- Updated `market_data/test_postgres_role_privileges.py` in commits `49efce78506f70fef84c527f8091db777c99579a` and `5a0c13c696cb80580d40563d0522f5c9d8b2ccf8`: dynamic Feeder login role receives membership in `t0_feeder_writer`; direct INSERT is asserted denied; Gateway write is exercised; direct function invocation with stale generation is asserted denied. Reader role remains read-only.
- Updated `market_data/README.md` in commit `bec2710dface0bce679e0bfda49d57faba62df4c` to document separate read adapter and fenced writer capability.
- Updated workflow PR base filters in commit `85a37f1fe2b715c855b95778277e16bc60082dbc` to include `feature/android-five-layer-control`, the actual PR #134 base, so the Gateway/TimescaleDB workflow can run as a PR check.
- Current branch tip after these sequential commits: `85a37f1fe2b715c855b95778277e16bc60082dbc`. PR-head metadata and workflow run status were not independently returned by the available lookup; CI is **NOT VERIFIED**. No claim that tests passed.
- Self-review limits: capability-role revocation does not erase any separately granted direct table privilege on an already-existing login role. Production role provisioning must grant Feeder membership in `t0_feeder_writer` and must not separately grant table INSERT/UPDATE/DELETE/TRUNCATE. The disposable role test creates a fresh role and verifies the intended least-privilege setup; production role provisioning remains **NOT VERIFIED**. Migration creates a cluster role and therefore requires a migration identity with CREATEROLE (the existing initial TimescaleDB migration already requires elevated extension privileges).
- P2 #3 is **implementation drafted / verification pending**, not yet cleared. Require exact-head GitHub Actions with disposable TimescaleDB, review SQL function owner/privileges and role provisioning, then fresh Codex review on the exact final SHA.
- No canonical DB, production Feeder, exchange, sync, deployment, or live execution was used. T0 source/runtime remains inactive; `ai_execution_enabled=false`.


### PR #134 writer-boundary follow-up correction — 2026-11-06

- Follow-up review tightened the SECURITY DEFINER boundary in migration `003_t0_database_fenced_candle_writer.sql`: the function is transferred to a dedicated NOLOGIN `t0_candle_writer_owner` role with only schema USAGE, lease SELECT/UPDATE and candle SELECT/INSERT; schema CREATE is revoked after function ownership transfer. This avoids running the SECURITY DEFINER body with the migration superuser's privileges.
- The DB function now rechecks owner/generation/expiry after the insert or duplicate comparison, so a direct authorized function call cannot commit a write after lease expiry merely because it passed the initial check.
- Latest workflow filter was corrected to the actual PR #134 base branch `feature/t0-centralized-data-feeder-p1-20261101` (not the similarly named branch without the date suffix). Commit: `fb37edb39261d0470d7a0fa7c876275d1af0a67d`.
- Current PR source tip: `fb37edb39261d0470d7a0fa7c876275d1af0a67d`. Combined status lookup returned no checks; exact-head CI remains **NOT VERIFIED**. The run lookup wrapper only surfaces PR-triggered runs and did not return a run at the time of this update. Do not interpret empty status as PASS.
- The migration creates the two NOLOGIN capability/owner roles and therefore requires elevated migration permissions; this is consistent with the existing TimescaleDB extension migration, but must be explicitly verified in disposable CI.
- The Feeder login role must be granted membership in `t0_feeder_writer`; it must not receive separate direct candle-table write grants. The capability role's REVOKE does not erase unrelated direct grants on arbitrary login roles. Production role provisioning is not present/verified in this repository yet.
- No database migration was executed from this session outside GitHub source edits. No canonical DB, Feeder, exchange, sync, deployment, or live execution was used.


### PR #134 exact-head review boundary — 2026-11-06

- Added an additional disposable role assertion in commit `26fd82fd8fd9ca5f1e7f765ccdd474833465ab52`: the dedicated function owner is NOLOGIN/non-superuser, has no schema CREATE or candle DELETE, retains only required candle INSERT and lease UPDATE; Feeder has no direct candle INSERT; PUBLIC has no function EXECUTE.
- Latest PR #134 head is `26fd82fd8fd9ca5f1e7f765ccdd474833465ab52`; base branch is `feature/t0-centralized-data-feeder-p1-20261101`; PR remains OPEN / DRAFT / NOT MERGED.
- The Gateway workflow is present on the PR head but is absent from the base branch. Its push trigger targets the PR source branch; its pull_request filter now names the exact PR base, but GitHub pull_request workflows require the workflow definition on the base branch to run. Therefore the push workflow may run, but available GitHub run lookup filters to PR events and cannot verify push-run completion. Combined commit status returned no status entries. Exact-head CI is **NOT VERIFIED**; do not claim tests passed.
- No migration was executed against any database in this session. Function SQL, owner role creation, group membership, error mapping, duplicate/conflict handling, and role integration tests remain **NOT VERIFIED** pending disposable TimescaleDB execution.
- Next: obtain exact push-run evidence through an Actions run listing capable of including push events (or arrange a base-branch workflow definition through a separately reviewed change); then inspect logs/artifacts, run fresh Codex review on the verified head, and update PR description. Keep PR draft and do not merge.


## 2026-11-05 — PR #134 PostgreSQL atomic writer + runtime exact-head acceptance

- PR #134 remains OPEN / DRAFT / NOT MERGED. Branch: `feature/t0-atomic-write-fencing-20261105`; base: `feature/t0-centralized-data-feeder-p1-20261101`.
- Exact tested PR source SHA: `905abeeed3bd0b28d85de096e5c8d6c543e7e485`; base SHA: `8b196d2720eab804728df7c0227c606c094b16ad`.
- Prior exact-head push run [#42075649645](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42075649645) failed in three Mock-based SQLite runtime fixtures. They touched an empty file instead of explicitly provisioning the canonical schema; the Gateway's fail-closed schema validator rejected it. This was a test-fixture issue, not a production runtime defect.
- Test-only correction commit: `905abeeed3bd0b28d85de096e5c8d6c543e7e485`, file `market_data/test_feeder_lifecycle.py`. Three fixtures now call `SQLiteCandleStore(db_path).initialize()` before runtime composition. No production source or database/runtime configuration changed.
- Exact-head push workflow [#42076214263](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42076214263): **SUCCESS**, event `push`, both jobs completed successfully. Workflow logs explicitly record `T0_TIMESCALE_SOURCE_SHA=905abeeed3bd0b28d85de096e5c8d6c543e7e485`.
- Static job ID `127416975734`: Gateway RED contracts 10/10 PASS; focused Gateway/Feeder behavior 60/60 PASS; Health/Readiness 21/21 PASS; process-level restart/fencing 2/2 PASS; full `market_data` suite 205 PASS / 19 SKIPPED. Counts overlap; PostgreSQL/TimescaleDB integration suites run separately in the disposable service job.
- Disposable TimescaleDB job ID `127417119287`: PostgreSQL atomic writer 7/7 PASS; PostgreSQL FeederRuntime composition 11/11 PASS; least-privilege roles 5/5 PASS; read-only TimescaleDB integration 6/6 PASS. CI service database was isolated and torn down.
- Artifacts: static ID `13437478538`, GitHub digest `sha256:115924aa449c4a7265ab5c9fb0f05c3d4ff3cc01e06eef23ff73a3d9bcafaf3e`; TimescaleDB ID `13438956146`, GitHub digest `sha256:a572d8cefd9be7fd255bb90f9ceb2117d645211626b71bf4e5e7f233e790f74b`. Payload bytes were not independently downloaded/re-hashed; digests are GitHub upload metadata.
- PR description updated with exact-head evidence and remaining limits. Status: exact-head CI **PASS** for this source SHA; PostgreSQL writer/runtime/role acceptance and disposable TimescaleDB read-only acceptance **PASS**.
- Remaining NOT VERIFIED / NOT AUTHORIZED: real-target role provisioning, migration against canonical T0, production backup/restore, production Feeder activation, Binance connection, deployment and 24/7 reliability. No canonical DB, live exchange, Feeder, market-data sync or real order execution was used.
- No merge, no branch deletion, no change to `ai_execution_enabled=false`, and no production activation. PR remains DRAFT pending independent focused review and explicit user approval.
- Next: perform a fresh focused review of the final PR head, including migration ownership/grants, writer function transaction semantics, lease expiry/recheck, and production role provisioning assumptions; then reconcile any findings and update the PR/handoff. Do not merge without explicit approval.


## PR #134 — reserved PostgreSQL writer-role hardening (in progress)

- PR #134 branch `feature/t0-atomic-write-fencing-20261105`, base `feature/t0-centralized-data-feeder-p1-20261101`; remains OPEN / DRAFT / NOT MERGED.
- Focused self-review found that migration 003 only created `t0_feeder_writer` and `t0_candle_writer_owner` with NOLOGIN when absent. If either reserved role already existed with LOGIN/SUPERUSER/other elevated role attributes, the migration did not reject it before transferring SECURITY DEFINER function ownership or granting function execution.
- TDD test commit: `caf38160005ea69bc014056622acc7c4f9a7bfdb`, adding `test_migration_runner_rejects_preexisting_privileged_writer_roles` for both reserved roles.
- Exact-head RED run [#42077083507](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42077083507), source SHA `caf38160005ea69bc014056622acc7c4f9a7bfdb`: expected failure reproduced for both roles; `RuntimeError not raised`. PostgreSQL writer 7/7 and FeederRuntime 11/11 passed before the role test; the role test failed and read-only TimescaleDB step was skipped. This is an intentional RED baseline, not an acceptance pass.
- Implementation commits: `8c0107053b0349c5b7b1194a61faa70caf1b283c` adds migration-runner checks before and after migrations; `06cf354dc45a55a619cbbb3243f9ac41a63e615b` adds matching SQL migration checks. Both reject reserved roles with SUPERUSER, LOGIN, CREATEDB, CREATEROLE, REPLICATION, BYPASSRLS, or membership in another role. The checks are fail-closed; they do not silently demote or mutate an unsafe pre-existing role.
- Exact-head GitHub Actions run [#42077369537](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42077369537), source SHA `06cf354dc45a55a619cbbb3243f9ac41a63e615b`, event `push`: **PENDING / NOT VERIFIED** at handoff update time; no job conclusions available yet.
- No production/canonical DB, role provisioning, migration execution, Feeder, exchange, market-data sync, deployment or live execution was performed. This guard has only been applied to source and awaits disposable TimescaleDB CI proof.
- Next: obtain exact-head run #42077369537 result; if pass, inspect job logs and artifact metadata, rerun fresh Codex review on this exact head, update PR description and handoff. If failure, inspect logs and correct with a new regression cycle. Keep PR DRAFT; do not merge or activate production.


## PR #134 — reserved PostgreSQL writer-role guard exact-head acceptance

- Final PR source SHA `06cf354dc45a55a619cbbb3243f9ac41a63e615b`; base SHA `8b196d2720eab804728df7c0227c606c094b16ad`. Branch `feature/t0-atomic-write-fencing-20261105`; PR remains OPEN / DRAFT / NOT MERGED.
- Exact-head push workflow [#42077369537](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42077369537): **SUCCESS**, both jobs successful; TimescaleDB preflight recorded the exact source SHA.
- Static job `127421781268`: Gateway contracts 10/10 PASS; focused Gateway/Feeder behavior 60/60 PASS; Health/Readiness 21/21 PASS; process restart/fencing 2/2 PASS; full `market_data` suite 206 PASS / 20 SKIPPED. Counts overlap; PostgreSQL integration is separately run in the disposable TimescaleDB job.
- Disposable TimescaleDB job `127421927475`: PostgreSQL atomic writer 7/7 PASS; PostgreSQL FeederRuntime 11/11 PASS; least-privilege roles 6/6 PASS, including the new pre-existing privileged role rejection test; read-only TimescaleDB 6/6 PASS. Disposable CI DB torn down.
- RED baseline: [#42077083507](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42077083507) on `caf38160005ea69bc014056622acc7c4f9a7bfdb` reproduced both role misconfiguration cases (no RuntimeError). Implementation commits `8c0107053b0349c5b7b1194a61faa70caf1b283c` and `06cf354dc45a55a619cbbb3243f9ac41a63e615b` add fail-closed checks to both migration runner and SQL migration.
- Artifacts: static ID `13438083517`, GitHub digest `sha256:c7106d07d8ab39518f732ad83d8e2aa2d93478d0eadea80a187aebd2337f1b15`; TimescaleDB ID `13437973685`, GitHub digest `sha256:f3a352e6d3f8e2c8bac0b60aae31c3c7f5ba8a02ad0a4435b57b4491ac291d0b`. Digests are upload metadata; payload bytes not independently re-hashed.
- Earlier Codex findings for canonical lease identity, SQLite schema validation and direct candle INSERT bypass are resolved in GitHub review threads. Fresh Codex review on the final head was requested but the bot returned `Unknown error`; external automated review of final SHA remains NOT VERIFIED. Manual focused review found no further actionable code issue in this pass.
- Remaining NOT VERIFIED / NOT AUTHORIZED: production role provisioning and grants on the actual target, applying migrations to canonical T0, backup/restore, production Feeder activation, Binance access, deployment and 24/7 reliability. No canonical DB, exchange, Feeder, sync or live order execution used.
- PR description updated with exact-head evidence and limits. No merge or production activation. Next: obtain a fresh independent review of SHA `06cf354...`; if it finds no blocker, reconcile production role provisioning instructions and retain DRAFT until explicit approval. Do not merge without explicit user approval.


## 2026-11-05 — PR #134 PostgreSQL lease capability hardening

- PR: https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/134
- Branch: `feature/t0-atomic-write-fencing-20261105`; base: `feature/t0-centralized-data-feeder-p1-20261101`; base SHA: `8b196d2720eab804728df7c0227c606c094b16ad`.
- Exact current PR head: `1ec7a6223d883a63d9787dc4b98a2f16207b7840`. PR remains OPEN / DRAFT / NOT MERGED.
- Self-review found the PostgreSQL Feeder login could directly mutate `market_data.feeder_leases` and forge the tuple trusted by the SECURITY DEFINER candle writer. The first remediation also exposed two follow-on issues: PostgreSQL `SELECT ... FOR UPDATE` required direct UPDATE privilege, and the Feeder could still read the current lease tuple and pass it to the writer function.
- Implemented migration `market_data/migrations/004_t0_fenced_lease_api.sql`: SECURITY DEFINER acquire/heartbeat/release/is-current functions with fixed trusted search_path; dedicated NOLOGIN `t0_lease_manager_owner`; capability role `t0_feeder_lease_manager`; direct Feeder lease-table access revoked. The migration also separates the candle-writer and lease-manager capability roles and revokes cross-scope table privileges.
- `PostgresLeaseStore` now uses only database lease functions. `PostgresWriteGateway` delegates lease-row locking/checks to the SECURITY DEFINER candle writer and checks lease validity through the restricted function before commit. Feeder has no direct SELECT/INSERT/UPDATE/DELETE/TRUNCATE on `feeder_leases`, and no direct candle writes.
- Production runtime generates a fresh 256-bit-class opaque owner token per process with `secrets.token_urlsafe(32)`, unless `T0_FEEDER_OWNER_ID` is explicitly configured. Configured values must be high entropy, per-process and never logged. `PostgresLease` repr hides the owner token.
- Tests cover direct lease-table access denial, lease contention/takeover, heartbeat, exact-generation release, stale-owner rejection, role capability separation, owner least privilege, PUBLIC EXECUTE denial, unique owner-token generation and repr protection.
- TDD RED evidence: run [#42081334862](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42081334862) exposed the need to remove outer `SELECT ... FOR UPDATE`; run [#42081783541](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42081783541) exposed remaining direct lease reads after table SELECT was removed. Both were corrected.
- Exact-head GitHub Actions run [#42082826484](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42082826484): SUCCESS on `1ec7a6223d883a63d9787dc4b98a2f16207b7840`; static job `127440742047`, disposable TimescaleDB job `127440848323`, both SUCCESS.
- Static tests: Gateway contracts 10/10; focused Gateway/Feeder 60/60; Health/Readiness 21/21; process restart/fencing 2/2; full `market_data` suite 209 PASS / 21 SKIPPED (PostgreSQL integrations run separately).
- Disposable TimescaleDB: PostgreSQL writer 7/7; FeederRuntime 13/13; least-privilege roles 7/7; read-only TimescaleDB 6/6. All PASS. CI database was isolated and torn down.
- Artifacts: static ID `13442327281`, digest `sha256:817d6427ea7ff91c797f39f0bf323d09231c80c8b60211567898690715b20ec3`; TimescaleDB ID `13441702080`, digest `sha256:a628ee74cb9c74695ced11a45363e77da177f07dbcdf605173bff095cd6b5da9`. Upload digests only; payload bytes not independently re-hashed.
- PR description updated with this exact-head evidence. Codex independent review requested on exact head in PR comment `6665738738`; response pending, so independent review remains NOT VERIFIED. A separate pull_request merge-context run on this exact head is also NOT VERIFIED.
- Production role provisioning, applying migration 004 to canonical T0, backup/restore, VPS deployment, production Feeder activation, Binance connectivity/sync and 24/7 reliability remain NOT VERIFIED / NOT AUTHORIZED. No canonical DB, production Feeder, exchange or live execution was used.
- Next: wait for Codex review; address any actionable finding and rerun exact-head CI. Keep PR DRAFT and unmerged until independent review is clean and user explicitly approves the next gate. Do not activate canonical T0 or production Feeder.


## 2026-11-06 — PR #134 independent self-review: BLOCKED

- Reviewed exact PR head `1ec7a6223d883a63d9787dc4b98a2f16207b7840`; PR #134 remains OPEN / DRAFT / NOT MERGED.
- Review covered migrations 003/004, migration runner, PostgreSQL lease store/write gateway, production Feeder composition, disposable TimescaleDB role tests, and production security/grant documentation.
- **P1 — Canonical lease identity is not enforced inside SQL capabilities.** Both the SECURITY DEFINER lease API and `write_canonical_candle` accept arbitrary `p_lease_name`. Python pins production runtime to `binance-btcusdt-canonical`, but a holder of the Feeder DSN can call the granted functions directly with another lease name, acquire it and write canonical candles. Current tests use random lease names and do not reject this. Fix: enforce canonical lease name in database functions and add direct SQL negative tests for alternate lease names.
- **P1 — Owner-role membership guard checks only the reverse direction.** `migrations.py` and migrations 003/004 check whether reserved roles are members of other roles (`pg_auth_members.member`), but do not check whether other logins/roles are members of `t0_candle_writer_owner` or `t0_lease_manager_owner` (`pg_auth_members.roleid`). A login granted an owner role may inherit/SET ROLE to direct function-owner table privileges and bypass SECURITY DEFINER boundaries. Fix: reject all membership granted from either owner role; add disposable login negative test.
- **P1 — Migration identity described by docs is not proven and likely cannot run fresh migrations.** Migrations create capability/owner roles (requires CREATEROLE or privileged bootstrap) and transfer SECURITY DEFINER function ownership. The documented `t0_migrator` is described as member only of `t0_db_owner`; no CREATEROLE or controlled membership/SET ROLE path to function-owner roles is specified. CI runs `migrate(DSN)` using the Timescale service bootstrap identity. Fix: define safe role provisioning and ownership transfer explicitly, then test fresh migrations using the exact restricted migration identity. Do not grant broad persistent rights to Feeder.
- **P2 — Configured owner ID can be shared by multiple processes.** `build_production_runtime` uses `T0_FEEDER_OWNER_ID` unchanged when present; `acquire_feeder_lease` returns the existing active generation when owner IDs match. Two processes with the same configured value can therefore share a lease. Fix: derive a unique effective per-process identity even when a secret seed is configured, or remove the override; test two runtime builds with the same seed.
- Full findings and remediations are recorded in PR comment [#6665847524](https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/134#issuecomment-6665847524); PR description also updated.
- Existing exact-head push CI #42082826484 remains PASS for the covered test setup; it does not cover the four findings above. Migration identity test is masked by bootstrap privileges. Current-head independent Codex response remains NOT VERIFIED.
- No source code was changed during this self-review. No canonical T0 DB, production migration, VPS, Feeder, exchange sync or live execution was touched.
- **Next:** fix P1 SQL identity and owner-role-membership boundaries first, then add restricted-migrator migration acceptance. Fix process owner uniqueness in the same TDD round. Run RED before implementation, then exact-head static and disposable TimescaleDB CI. Keep PR DRAFT and unmerged; production activation remains NOT AUTHORIZED.


## 2026-11-06 — PR #134 security remediation and exact-head acceptance

- PR: https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/134
- Branch: `feature/t0-atomic-write-fencing-20261105`
- Latest source SHA: `ade2c3393260d5627e1a3879776be83b2a45375e`
- PR remains OPEN / DRAFT / NOT MERGED.
- SQL enforces the fixed canonical lease identity `binance-btcusdt-canonical` in candle writes and all lease API operations; alternate lease names fail closed.
- Migration runner and migrations 003/004 reject runtime/login memberships granted from either SECURITY DEFINER owner role. The sole direct member exception is NOLOGIN `t0_migrator`; only `t0_migrator_login` may be a member of that group. Both owner-role grants are covered by negative integration tests.
- `t0_migrator` is explicitly enforced as NOLOGIN/non-admin by both migration runner and SQL role guards. RED run #42087807396 demonstrated that a LOGIN-enabled `t0_migrator` was previously accepted; the final exact-head tests now prove it is rejected.
- Restricted migration path: bootstrap provisions NOLOGIN owner/capability roles, database and TimescaleDB extension; `t0_migrator` temporarily receives membership in `t0_db_owner` and both function-owner roles; a separate ephemeral login joins only `t0_migrator`. Fresh disposable DB migration passes under this restricted identity, not the Timescale service bootstrap login.
- `T0_FEEDER_OWNER_ID` is rejected; each production process generates a fresh high-entropy owner capability. SQL rejects alternate lease identities, independent of Python configuration.
- Production security docs deny direct Feeder lease-table access and direct candle-table writes. Role integration verifies no direct lease SELECT/INSERT/UPDATE or candle INSERT for the Feeder login.
- Exact-head GitHub Actions run [#42088085844](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42088085844): **SUCCESS** on `ade2c3393260d5627e1a3879776be83b2a45375e`; static job `127459026648`, disposable TimescaleDB job `127459171223`, both SUCCESS.
- Static evidence: Gateway contracts 10/10; behavior regressions 60/60; Health/Readiness 21/21; process restart/fencing 2/2; complete `market_data` suite 215 PASS / 26 SKIPPED.
- Disposable TimescaleDB evidence: PostgreSQL writer 7/7; FeederRuntime 14/14; least-privilege roles 12/12; read-only TimescaleDB 6/6. All PASS.
- Artifacts: static ID `13444091735`, digest `sha256:8e76468030a6f2fbca45415bf51183bc00158ebac8f6308cbca41f7fd3ff2299`; TimescaleDB ID `13442929063`, digest `sha256:40454daf769c6414b6afceeebee0ef572adc9ade150ff5b62e919dcf1894423c`. Digests are GitHub upload metadata; payload bytes not independently downloaded/re-hashed.
- TDD RED evidence: run #42084473750 reproduced shared owner-ID reuse; run #42087807396 reproduced LOGIN-enabled migrator acceptance. Both are fixed and covered by passing final-head tests.
- Codex inline review threads covering migration role provisioning, ownership transfer, both owner-role membership directions, direct Feeder table access and process owner identity were replied to and resolved. Fresh `@codex review` request for exact head was submitted in PR comment #6666464432; independent review remains **NOT VERIFIED** until response.
- A separate `pull_request` merge-context run for this exact head remains **NOT VERIFIED**.
- Production role provisioning, applying migrations to canonical T0, backup/restore, VPS deployment, production Feeder activation, Binance connectivity/sync and 24/7 reliability remain **NOT VERIFIED / NOT AUTHORIZED**. No canonical DB, production Feeder, exchange or live execution was used.
- Next: wait for Codex review of SHA `ade2c3393260d5627e1a3879776be83b2a45375e`; fix any actionable finding with TDD and rerun exact-head CI. Keep PR DRAFT and unmerged until review is clean and user explicitly approves merge.


## 2026-11-06 — Isolate ephemeral migrator LOGIN from indirect membership

- Self-review P1: previous guards restricted direct membership in `t0_migrator`, but did not prevent another role from being granted membership in `t0_migrator_login`, nor prevent the ephemeral login from receiving additional role memberships.
- Added three disposable TimescaleDB negative integration tests in `market_data/test_postgres_role_privileges.py`: reject a second LOGIN granted membership in `t0_migrator_login`, an additional role granted to `t0_migrator_login`, and ADMIN OPTION on its sole `t0_migrator` membership.
- `market_data/migrations.py` requires the ephemeral login to exist as LOGIN with no SUPERUSER/CREATEDB/CREATEROLE/REPLICATION/BYPASSRLS attributes, no members of its own, and exactly one membership: `t0_migrator` without ADMIN OPTION.
- SQL migrations 003 and 004 independently enforce the same login attributes, incoming-membership prohibition, exact single membership and no ADMIN OPTION.
- TDD order: tests first at `033cd32b6b8de7a4bc297515c8af4fac635cf029`; implementation followed; final source SHA `14647b3f9fd35edb8667eab03885dd98b339be0d`.
- Corrected workflow `pull_request.branches` filter to actual PR base `feature/t0-centralized-data-feeder-p1-20261101`. CI remains source-only plus disposable TimescaleDB.
- **RED execution evidence: NOT VERIFIED.** Tests preceded implementation, but the available GitHub run lookup exposes pull_request runs only, not the push-triggered run. Do not claim a reproduced RED failure without logs.
- **Final exact-head CI: NOT VERIFIED** on `14647b3f9fd35edb8667eab03885dd98b339be0d`; new TimescaleDB tests and SQL guards await GitHub Actions execution. PR remains OPEN / DRAFT / NOT MERGED.
- No production/canonical DB, production roles, migration, Feeder, exchange, sync, VPS deployment or live execution was touched. Next: verify exact-head push CI and disposable TimescaleDB logs, then obtain independent Codex review of this SHA. Keep production activation and merge blocked.


## 2026-11-06 — PR #134 migrator fixture correction and database-owner ADMIN OPTION preflight

- PR head: `af09483e11ed236f92c35b075983d4ac98424cfe`; branch: `feature/t0-atomic-write-fencing-20261105`; PR remains OPEN / DRAFT / NOT MERGED.
- Commit `7ee1b87f2f6a3c71c09add0dfe53d6ee837a974f` corrected three ephemeral-login integration fixtures by provisioning `t0_db_owner` and granting the expected membership to `t0_migrator`.
- PR merge-context workflow [#42121204871](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42121204871), checkout SHA `a377540fbf546a311c85fe00a8ea5ef56a8a392b` (synthetic merge of PR head `7ee1b87f2f6a3c71c09add0dfe53d6ee837a974f` into base `8b196d2720eab804728df7c0227c606c094b16ad`) completed SUCCESS: static job, paper-consumer job and disposable TimescaleDB job all passed. Static: Gateway contracts 10, behavioral regressions 60, Health/Readiness 21, process restart 2, complete `market_data` suite 220. Paper consumer: 44 tests. TimescaleDB: writer 7, FeederRuntime 14, least-privilege roles 17, read-only integration 6. Artifacts: static `13460105030` (digest `sha256:0e6cb08fd1b4590c6e1c153810b83d030a70610bd9248980dda43e28fa91ce8c`); TimescaleDB `13459535565` (digest `sha256:4f61f40fcfb1631a77074978a86ac96ed9841fbd209de182d18abc39e10e9f7c`); paper `13457833737` (digest `sha256:4de174da359dfc90c2683ee0c4d1022d1dadbc6d54eef3357542a56391efab77`). GitHub upload digests only; payload bytes were not independently re-hashed.
- Self-review found Python `_assert_writer_roles_safe()` did not include `t0_db_owner` in its ADMIN OPTION query, although SQL migrations 003/004 checked it. An earlier test combined ADMIN OPTION grants across three owner roles and could pass by detecting another role first.
- Commit `c3bb24a6649dfa6194e804ddb1ccf80409440e01` added `t0_db_owner` to the Python preflight query. The isolated test was refined in `af09483e11ed236f92c35b075983d4ac98424cfe` to call the preflight directly with ADMIN OPTION only on `t0_db_owner`, avoiding migration side effects.
- The first attempt at that isolated test in run [#42121440954](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42121440954) failed with `StoreUnavailable` because it called the full migration path; this is not valid RED evidence for the ADMIN OPTION guard. **TDD RED execution evidence: NOT VERIFIED.**
- Current exact-head PR run [#42121787389](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42121787389) on `undefined`: static job PASS; paper-consumer job PASS; disposable TimescaleDB job still IN PROGRESS at this handoff update. Final exact-head acceptance remains **PENDING** until that job completes and its logs are inspected.
- Codex independent review was requested against SHA `undefined` in PR comment `6671204172`; response is **NOT VERIFIED / PENDING**.
- No production DB, canonical migration, Feeder activation, VPS deployment, exchange connection/sync or live execution was performed. PR remains DRAFT / NOT MERGED; no merge or production activation is authorized.


## 2026-11-06 — PR #134 exact-head CI acceptance after migration ADMIN OPTION correction

- Exact PR source/head SHA: `af09483e11ed236f92c35b075983d4ac98424cfe`; branch `feature/t0-atomic-write-fencing-20261105`; base `feature/t0-centralized-data-feeder-p1-20261101`.
- Python `_assert_writer_roles_safe()` now checks ADMIN OPTION for `t0_db_owner`, `t0_candle_writer_owner` and `t0_lease_manager_owner`. The isolated regression grants ADMIN OPTION only on `t0_db_owner` and directly calls the preflight helper, avoiding migration-path side effects.
- PR merge-context workflow [#42121787389](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42121787389), checkout SHA `16c0e047d0f7caa3c93717f3bce36f45c702f5f8` (synthetic merge of PR head `af09483e11ed236f92c35b075983d4ac98424cfe` into base `8b196d2720eab804728df7c0227c606c094b16ad`): **SUCCESS**, all three jobs completed successfully.
  - Static job `127575802970`: Gateway contracts 10/10; Gateway/Feeder behavioral regressions 60/60; Health/Readiness 21/21; process restart/fencing 2/2; complete `market_data` suite 220 tests run / 31 skipped. Skips include integration cases run separately in the disposable TimescaleDB job.
  - Paper consumer job `127575802692`: 44/44 PASS.
  - Disposable TimescaleDB job `127575924316`: PostgreSQL writer 7/7; FeederRuntime 14/14; least-privilege role contracts 17/17; read-only TimescaleDB 6/6. All PASS; disposable DB stopped after job.
- PR merge-context artifacts: static ID `13460080868`, digest `sha256:666cce4caa2362d777de5bf49e2325cd8bad9d2bcbfa0824f118cf3c5371dbcf`; paper ID `13459800711`, digest `sha256:0bc91c26741f137b3037a8f05736c7f101a4d523ae6c938e2dac041276212b09`; TimescaleDB ID `13459471243`, digest `sha256:251ac663a82d3646cc37aa305cf1d0961bad74b41dc94f2f3b845939b98ab7b9`. GitHub upload digests only; payload bytes were not independently downloaded/re-hashed.
- A prior attempt to test this preflight by invoking `migrate(DSN)` failed with `StoreUnavailable` due migration-path side effects. The test was isolated to call `_assert_writer_roles_safe` directly. **Valid TDD RED execution evidence remains NOT VERIFIED**; do not claim the guard was reproduced failing before the implementation fix.
- Codex independent review requested for exact SHA `af09483e11ed236f92c35b075983d4ac98424cfe` in PR comment `6671204172`; response remains **PENDING / NOT VERIFIED**. Prior Codex receipts refer to older SHAs only.
- PR remains OPEN / DRAFT / NOT MERGED. Exact-head CI PASS does not authorize merge. No production/canonical DB migration, VPS deployment, production Feeder activation, exchange connection/sync or live execution was performed or authorized.


## 2026-11-06 — PR #134 final exact-head role-guard test coverage

- Exact PR source/head SHA: `4c28fff542f767c094e725dabc8a2698df2f39fd`; PR #134 remains OPEN / DRAFT / NOT MERGED.
- Added independent Python preflight regression coverage for ADMIN OPTION on each SECURITY DEFINER owner role (`t0_candle_writer_owner`, `t0_lease_manager_owner`) in addition to the isolated `t0_db_owner` test.
- PR merge-context workflow [#42122195912](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42122195912), checkout SHA `10f35e4fd8a30e715dd02ed8ab16e0281e468e53` (synthetic merge of PR head `4c28fff542f767c094e725dabc8a2698df2f39fd` into base `8b196d2720eab804728df7c0227c606c094b16ad`): **SUCCESS**, all 3 jobs completed successfully.
  - Static job `127577155629`: Gateway contracts 10/10; Gateway/Feeder behavior 60/60; Health/Readiness 21/21; process restart/fencing 2/2; full `market_data` suite 221 tests run / 32 skipped.
  - Paper consumer job `127577155087`: 44/44 PASS.
  - Disposable TimescaleDB job `127577275886`: PostgreSQL writer 7/7; FeederRuntime 14/14; least-privilege roles 18/18; read-only TimescaleDB 6/6. All PASS.
- Artifacts: paper `13459336497`, digest `sha256:2972f95b257f0e9d455f56833c7b22b1d9ef303f202d6cfc4f39bf70c256c303`; static `13458977120`, digest `sha256:6fb889a6eda00b680c908f477c8ab981ca1468b14c2878f0c3d62a2d539b4f92`; TimescaleDB `13457983934`, digest `sha256:bb833eb962a901a45fc68ab2bb31bfe750efece533ec51c79f2201f6ab856e47`. GitHub upload digests only; payload bytes were not independently downloaded/re-hashed.
- Three older Codex inline threads were replied to and resolved: migrator owner-role ADMIN OPTION guard, stable migration object ownership, and paper-consumer fixtures.
- Independent Codex review of exact SHA `4c28fff542f767c094e725dabc8a2698df2f39fd` was requested in PR comment `6671253268`; no Codex review receipt for this SHA is present yet. **Independent review: NOT VERIFIED / PENDING.**
- Valid TDD RED execution evidence for the ADMIN OPTION guard remains **NOT VERIFIED**. The earlier full-migration test attempt failed through migration-path side effects and is not accepted as RED proof.
- No canonical T0 DB, production migration, VPS deployment, production Feeder activation, exchange connection/sync or live execution. CI PASS does not authorize merge or production activation.


## CI provenance clarification — PR runs are merge-context, not direct-head runs

The three PR-triggered runs recorded above (#42121204871, #42121787389, #42122195912) checked out GitHub synthetic merge commits, not the branch head directly. Their merge checkout SHAs are recorded in the corresponding sections. These runs prove the PR head combined with base branch passed in merge context; they do **not** establish direct-head push verification. Direct-head-only CI remains **NOT VERIFIED**. Do not describe these PR runs as direct-head or exact-head push runs.


## 2026-11-06 — PR #134 Codex review receipt and self-review gate

- Current PR head verified unchanged: `4c28fff542f767c094e725dabc8a2698df2f39fd`; PR OPEN / DRAFT / NOT MERGED.
- Codex review receipt [comment #6671327441](https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/134#issuecomment-6671327441) explicitly says “Didn't find any major issues” and records reviewed commit `4c28fff542`, matching the current 12-character head prefix. **Codex review: PASS (no major issues reported).**
- PR merge-context CI [#42122195912](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42122195912) remains SUCCESS across static, paper-consumer and disposable TimescaleDB jobs. The checked-out synthetic merge SHA is `10f35e4fd8a30e715dd02ed8ab16e0281e468e53`, not the direct branch head.
- Current self-review of `market_data/migrations.py`, migrations 003/004 and `market_data/test_postgres_role_privileges.py`: Python preflight checks restricted role attributes, incoming/outgoing ephemeral-login membership, allowed membership of `t0_migrator`, owner-role membership direction, and ADMIN OPTION for all three stable/SECURITY DEFINER owner roles. Migration runner uses `SET ROLE t0_migrator`, transfers schema/ledger/tables to stable `t0_db_owner`, and finalizes with another role-safety check. SQL migrations independently enforce owner-role constraints and explicitly assign SECURITY DEFINER function ownership. Relevant role regressions are present and passed in disposable TimescaleDB CI. No additional actionable defect identified in this pass.
- Remaining verification limitations: direct-head push run is **NOT VERIFIED** (available workflow-run lookup only surfaced PR-triggered merge-context run); valid TDD RED execution evidence for the ADMIN OPTION guard remains **NOT VERIFIED**. Do not label either as PASS.
- Review threads: no unresolved inline threads at time of check.
- PR remains DRAFT / NOT MERGED. No merge approval inferred. No production/canonical DB migration, VPS deployment, Feeder activation, exchange sync or live execution.


## 2026-11-06 — PR #134 Codex review and self-review

- Current PR head: `4c28fff542f767c094e725dabc8a2698df2f39fd`; PR remains OPEN / DRAFT / NOT MERGED.
- Codex receipt [#6671327441](https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/134#issuecomment-6671327441) reports no major issues and reviewed commit prefix `4c28fff542`, matching current head. Codex review: PASS (no major issues reported).
- Self-review covered `market_data/migrations.py`, SQL migrations 003/004 and PostgreSQL role tests. No additional actionable defect identified. Role checks passed in disposable TimescaleDB CI.
- PR workflow [#42122195912](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42122195912) is SUCCESS but checked out synthetic merge SHA `10f35e4fd8a30e715dd02ed8ab16e0281e468e53`, not direct branch head.
- Direct-head push CI: NOT VERIFIED. Valid TDD RED execution evidence: NOT VERIFIED. Do not claim either as PASS.
- No unresolved inline review threads at check. No merge approval, production migration, canonical DB, VPS deployment, Feeder activation, exchange sync or live execution.


## 2026-11-06 — PR #134 isolated SQL ADMIN OPTION test cases

- PR head: `bcecd88e2a71b1c1bd5d3eb7577a095ebb55bc86`; PR remains OPEN / DRAFT / NOT MERGED.
- Self-review found a test coverage weakness: the SQL migration test previously granted ADMIN OPTION on all three owner roles at once, so the first guard failure could mask missing checks on the other roles.
- Replaced it with isolated subtests. For each of migrations 003 and 004, exactly one of `t0_db_owner`, `t0_candle_writer_owner`, or `t0_lease_manager_owner` receives ADMIN OPTION at a time; each case must raise `InsufficientPrivilege` mentioning ADMIN OPTION. Normal memberships remain in place for the other roles.
- Change is test-only; production Python and SQL migration logic unchanged.
- The update touched `market_data/test_postgres_role_privileges.py`, which matches the workflow push path filter. Commit-specific workflow lookup currently returns no associated run; direct-head push CI for `bcecd88e2a71b1c1bd5d3eb7577a095ebb55bc86` is PENDING / NOT VERIFIED (the available GitHub Actions connector lookup only returns PR-triggered runs).
- Independent Codex review requested in PR comment `6671399291` for exact SHA `bcecd88e2a71b1c1bd5d3eb7577a095ebb55bc86`; receipt PENDING.
- Test execution result for the new isolated subtests is NOT VERIFIED until CI logs are available. This does not establish TDD RED evidence.
- No production/canonical DB migration, VPS deployment, Feeder activation, exchange sync or live execution.


## 2026-11-06 — PR #134 SQL 004 ADMIN OPTION guard defect

- Source SHA: `9e5d99b16b1316549eacbd6091ef670d4035ac0a`; PR #134 remains OPEN / DRAFT / NOT MERGED.
- Workflow #42123326572 failed in the disposable TimescaleDB role-privilege suite: 17/18 passed; isolated case `migration=004_t0_fenced_lease_api.sql`, `owner_role=t0_candle_writer_owner` failed because `InsufficientPrivilege` was not raised.
- Root cause confirmed by comparing SQL 003, SQL 004 and Python preflight: migration 004 omitted `t0_candle_writer_owner` from its ADMIN OPTION role allowlist. Migration 003 and Python preflight already included all three owner roles.
- Fixed only the SQL 004 allowlist to include `t0_candle_writer_owner`. This is a security correctness fix, not merely a test adjustment.
- The failure above is valid RED evidence for the isolated SQL role test on prior source SHA `bcecd88e2a71b1c1bd5d3eb7577a095ebb55bc86`; GREEN on fixed SHA `9e5d99b16b1316549eacbd6091ef670d4035ac0a` is PENDING CI.
- Previous workflow run #42123326572 synthetic merge SHA `c983c189282db183755e0a73b8e0ebf7391a595a`: static contracts PASS, paper consumers PASS, TimescaleDB role suite FAIL. Artifact `13458993438` digest `sha256:7de79b5df5cd418693fd6f1eafce5b8591b8765c054e70e593306e865ced3c4e` contains the Timescale evidence. This artifact is failure evidence, not a passing release artifact.
- Direct-head push CI and new-head merge-context CI for `9e5d99b16b1316549eacbd6091ef670d4035ac0a`: NOT VERIFIED / pending run visibility. Codex review of prior test-only SHA is not sufficient for this production SQL change; new exact-SHA review requested separately.
- No production/canonical DB migration, VPS deployment, Feeder activation, exchange sync or live execution.


## 2026-11-06 — PR #134 SQL 004 ADMIN OPTION fix verified

- PR #134 current head: `9e5d99b16b1316549eacbd6091ef670d4035ac0a`; branch `feature/t0-atomic-write-fencing-20261105`; base `feature/t0-centralized-data-feeder-p1-20261101` at `8b196d2720eab804728df7c0227c606c094b16ad`.
- Corrected `market_data/migrations/004_t0_fenced_lease_api.sql`: the ADMIN OPTION guard now checks `t0_db_owner`, `t0_candle_writer_owner`, and `t0_lease_manager_owner`, matching SQL 003 and Python preflight. This closes the isolated defect detected on prior SHA `bcecd88e2a71b1c1bd5d3eb7577a095ebb55bc86`.
- PR merge-context workflow [#42123643557](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42123643557): **SUCCESS**, all three jobs passed. GitHub reports synthetic merge checkout SHA `317cabd05ab0c36bdbbf6284fbd0cee9a3d58029`, combining PR head `9e5d99b16b1316549eacbd6091ef670d4035ac0a` with base `8b196d2720eab804728df7c0227c606c094b16ad`. This is PR merge-context evidence, not a direct-head push run.
  - Static Gateway contract job `127582115842`: SUCCESS.
  - Paper consumer regression job `127582116152`: SUCCESS.
  - Disposable TimescaleDB job `127582247335`: SUCCESS. PostgreSQL least-privilege role suite: 18/18 PASS; log includes `T0_POSTGRES_ROLE_PRIVILEGES=PASS`. Read-only TimescaleDB suite: 6/6 PASS; log includes `T0_TIMESCALE_READ_ONLY_INTEGRATION=PASS`. The isolated SQL ADMIN OPTION test covering migration 004 and `t0_candle_writer_owner` passed.
- Artifacts (GitHub upload metadata; payload bytes not independently downloaded/re-hashed): TimescaleDB ID `13460028622`, name `t0-timescale-read-only-evidence-317cabd05ab0c36bdbbf6284fbd0cee9a3d58029`, digest `sha256:dfe7e6cd8e820d7c7ba89e2a2a30009b41aef0a2c50cc4739a039db0d7b5526b`; static ID `13459847146`, digest `sha256:6c5ffe8e3994307d4d23a603aec505075e53cf2b00eacb5ff94ff87bb37a12e6`; paper ID `13459043650`, digest `sha256:98ed47d845f77e6ed2e188a564cb7ced38dc1cc308555733405e357cb4a85921`.
- Codex receipt [#6671497665](https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/134#issuecomment-6671497665) says no major issues and records reviewed commit `9e5d99b16b`, matching the current head prefix. **Independent Codex review: PASS (no major issues reported).**
- Valid TDD RED evidence: prior run #42123326572 on prior source SHA reproduced the missing SQL 004 guard (17/18 role tests passed; isolated missing guard failed). GREEN merge-context verification is now PASS on current PR head context.
- Direct-head push CI: **NOT VERIFIED**. Artifact payload hash recomputation: **NOT VERIFIED**. These are not implied by the merge-context workflow or GitHub upload digests.
- PR remains OPEN / DRAFT / NOT MERGED. No merge approval inferred. No canonical T0 DB migration, production Feeder activation, VPS deployment, exchange connection/sync or live execution was performed or authorized.
- Next: preserve PR #134 pending explicit user merge approval; before any merge, resolve any remaining direct-head CI requirement only if a real push run becomes available, and retain the above provenance distinctions. No production activation follows from CI PASS.


## 2026-11-06 — PR #134 promoted to ready for review

- Current head remains `9e5d99b16b1316549eacbd6091ef670d4035ac0a`; base remains `8b196d2720eab804728df7c0227c606c094b16ad`.
- Rechecked PR state and review surface: PR mergeable=true; all 13 inline review threads resolved; no unresolved review threads. Codex receipt for current head prefix `9e5d99b16b` reports no major issues.
- PR description updated with latest workflow #42123643557 provenance, TimescaleDB 18/18 role tests, read-only 6/6, review receipt, and explicit verification limits.
- PR #134 transitioned from DRAFT to **OPEN / READY FOR REVIEW / NOT MERGED**. This is a review-readiness transition only, not merge approval.
- Direct-head push CI remains NOT VERIFIED; workflow #42123643557 checked out synthetic merge SHA `317cabd05ab0c36bdbbf6284fbd0cee9a3d58029`. Artifact payload hashes are not independently recomputed.
- No merge, canonical T0 migration, production Feeder activation, VPS deployment, exchange connection/sync or live execution.
- Next gate: human review/explicit merge approval. Do not merge automatically. If further CI evidence is required, only accept a real push-triggered run with checked-out SHA equal to current PR head.


## 2026-11-06 — PR #134 merged (T0 atomic write fencing / role security)

- **Status: MERGED.** User explicitly approved the merge. PR #134: https://github.com/kenznguyen/btcusdt-telegram-signals2/pull/134
- Source branch: `feature/t0-atomic-write-fencing-20261105`; merged into base branch `feature/t0-centralized-data-feeder-p1-20261101`.
- Exact PR head SHA: `9e5d99b16b1316549eacbd6091ef670d4035ac0a`.
- Base SHA before merge: `8b196d2720eab804728df7c0227c606c094b16ad`.
- GitHub merge commit SHA: `3b768a2aab143ee42539bddd0b5538ec3a4700ae`; merged at `2026-11-06T03:10:11Z`.
- Pre-merge checks: PR reported mergeable=true and READY FOR REVIEW; all 13 inline review threads resolved; no unresolved threads. Codex review receipt #6671497665 reviewed source prefix `9e5d99b16b` and reported no major issues.
- PR merge-context workflow #42123643557: **SUCCESS**, all 3 jobs completed successfully: Static Gateway contract verification, Paper consumer fixture regressions, and Isolated TimescaleDB read-only integration. Disposable PostgreSQL least-privilege role suite 18/18 PASS; read-only TimescaleDB suite 6/6 PASS; isolated migration 004 ADMIN OPTION regression PASS. Synthetic merge checkout SHA: `317cabd05ab0c36bdbbf6284fbd0cee9a3d58029`.
- Provenance limits retained: direct-head push CI **NOT VERIFIED**; workflow #42123643557 is PR merge-context, not a direct checkout of the branch head. Artifact payload bytes were not independently downloaded/re-hashed; GitHub upload digests remain metadata only.
- Scope boundary: merge only. No canonical/production T0 DB migration, VPS deployment, Feeder activation, exchange connection/sync, or live execution was performed or authorized. Paper-only boundary and `ai_execution_enabled=false` remain unchanged.
- Next workstream: SWG-F Paper Writer Isolation Gate. Keep it isolated from T0 lease authority; implement/test admission states, generation-bound writer tokens, in-flight accounting, bounded fail-closed drain, idempotent release, and safe reopen only after settled outcome with zero writers. Use temporary/test resources only. No canonical ingestion or deployment without a separate explicit approval.


## 2026-11-06 — PG-RUNTIME-ADAPTER post-merge verification

- Checked merged base branch `feature/t0-centralized-data-feeder-p1-20261101`. GitHub compare confirms its tip is identical to merge commit `3b768a2aab143ee42539bddd0b5538ec3a4700ae` (PR #134 merge); no post-merge source commit has moved this branch.
- Current merged source tree contains `PostgresRuntimeLeaseAdapter` in `market_data/feeder_service.py`, PostgreSQL-aware `build_runtime()`, and PostgreSQL production selection in `build_production_runtime()`. Current source blob SHAs: `feeder_service.py=db48ccb409e365d328edcbd5a673564dbf6ea638`; `postgres.py=2fe27fe2d066dda0c192a381b72d27404487b800`; `storage.py=13fe1ae01ebb5318b69e69eef3e512d207f74c49`; `test_postgres_feeder_runtime.py=1ee9c8e3576b791e9f80fd1a783bb64f643cc877`.
- Runtime adapter preserves PostgreSQL DB-clock authority: FeederRuntime's `now_ms` is not forwarded; acquire/heartbeat/current/write-authorization/release delegate to `PostgresLeaseStore`. PostgreSQL Candle Store, Lease Store and `PostgresWriteGateway` must share the same DSN. Scheduler and startup recovery use the same Gateway object. SQLite remains the default and its same-database invariant is retained.
- Production config fails closed for PostgreSQL if `T0_FEEDER_LEASE_DB` is set, lease name differs from the fixed canonical identity, or a shared `T0_FEEDER_OWNER_ID` is supplied; process owner capability is freshly generated.
- Latest PR merge-context CI [#42123643557](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42123643557) passed all 3 jobs on synthetic merge checkout `317cabd05ab0c36bdbbf6284fbd0cee9a3d58029`, which combined PR head `9e5d99b16b1316549eacbd6091ef670d4035ac0a` with base `8b196d2720eab804728df7c0227c606c094b16ad`; the merged branch tree now points to merge commit `3b768a2aab143ee42539bddd0b5538ec3a4700ae`.
- PG-specific TimescaleDB job `127582247335`: PostgreSQL writer/lease 7/7 PASS; PG runtime adapter/composition suite 14/14 PASS (13 static contract cases + 1 disposable TimescaleDB runtime integration); role/privilege suite 18/18 PASS; read-only TimescaleDB 6/6 PASS. Full static `market_data` suite: 221 tests, 32 skipped; lifecycle suite 60/60 PASS; Health/Readiness 21/21 PASS; process restart 2/2 PASS.
- The actual TimescaleDB runtime integration exercises startup recovery, closed-candle persistence through the fenced Gateway, scheduler duplicate idempotence using the identical Gateway instance, and graceful stop/release of the exact lease generation. No real exchange/network or production DB was used.
- Code review verdict: PG-RUNTIME-ADAPTER implementation/composition **PASS** in merged source; SQLite regression **PASS**; disposable PostgreSQL writer/runtime/role/read-only suites **PASS**.
- Remaining acceptance gap: no PostgreSQL-backed FeederRuntime integration test currently exercises the runtime heartbeat thread over time, lease loss/takeover while running, readiness closure on PG lease loss, shutdown drain timeout/lease retention, or restart acquiring the next PG fencing generation. SQLite lifecycle tests cover related lifecycle behavior, and PostgreSQL lease/writer tests cover their lower-level primitives, but that is not equivalent to end-to-end PostgreSQL runtime lifecycle acceptance. Mark these scenarios **NOT VERIFIED**.
- Production role/credential/TLS/network provisioning, backup/PITR, restore/RPO/RTO, canonical DB creation, VPS deployment and real Binance ingestion remain **NOT VERIFIED / NOT AUTHORIZED**. No Feeder was activated. `ai_execution_enabled=false` remains unchanged.
- Next safe increment: add the missing PostgreSQL runtime lifecycle acceptance scenarios above against disposable TimescaleDB only; preserve SQLite default. Do not provision production DB, deploy VPS, connect Binance, or activate the production Feeder.


## 2026-11-06 — PostgreSQL FeederRuntime lifecycle acceptance tests added

- Workstream: P0-PG-RUNTIME-LIFECYCLE; disposable TimescaleDB only. No production DB, VPS, exchange, or Feeder activation.
- Added `market_data/test_postgres_feeder_runtime_lifecycle.py` with four integration scenarios using real `PostgresLeaseStore` + `PostgresRuntimeLeaseAdapter` and a controlled scheduler:
  1. DB-clock heartbeat extends lease expiry while runtime remains RUNNING.
  2. Expired lease takeover advances generation; old runtime observes LEASE_LOST, stops scheduler admission, and HealthEvaluator must report not-ready.
  3. Shutdown drain timeout retains the current lease; successful drain then releases it.
  4. Restart after release acquires a strictly higher fencing generation.
- Added the lifecycle test module to the disposable TimescaleDB job in `.github/workflows/t0-single-writer-gateway-red.yml`; enabled push trigger on the active integration branch so this suite can run on direct branch updates.
- Commits on `feature/t0-centralized-data-feeder-p1-20261101`:
  - `b203ed1db37eee0451a8c2dfaf4d3d1ba3d91a08` — initial lifecycle acceptance tests.
  - `8a6c848ca80c8cc53729e9b8b99d4800ce882ba5` — workflow invocation.
  - `84f7aba002d2f6ff6e8335585f59a42ee0e0e25e` — readiness closure and clean shutdown assertion after lease loss.
- Initial lifecycle-test branch head before the CI correction/fix: `e181f2a779419c6930f043be47e43d89eb0b685f`. The final acceptance and current status are recorded in the `2026-11-06 — P0 PostgreSQL FeederRuntime lifecycle acceptance` section below.
- Initial status at this checkpoint was **NOT VERIFIED**. This was superseded by the RED/GREEN CI sequence recorded in the lifecycle acceptance section below; final exact-SHA result is **PASS**.
- The test subsequently confirmed that `FeederRuntime.stop()` raised after lease takeover when exact-generation release returned false. The regression-backed correction and GREEN verification are recorded below.
- Exact-SHA CI and artifact evidence: **PASS** on source SHA `75856f73da569a6a33e0b8b9c11340d518ad7794`; see the lifecycle acceptance section below.
- No production migration, credentials, VPS changes, Binance access/sync, or Feeder activation. `ai_execution_enabled=false` remains unchanged.
- Next: execute the new test on exact branch head in disposable TimescaleDB. If lease-loss shutdown fails, add a regression-backed fix that treats an already-lost generation as non-owned after drain, without releasing or mutating the replacement lease. Then run full regression and update evidence with exact SHA/run/artifact.

- CI visibility issue resolved: direct push run `42156876274` and its job logs/artifacts were retrieved and reconciled. Direct push exact-SHA verification is **PASS**.


## 2026-11-06 — P0 PostgreSQL FeederRuntime lifecycle acceptance

### Scope and implementation

- Continued on `feature/t0-centralized-data-feeder-p1-20261101`; no parallel branch or PR created.
- Added PostgreSQL-backed lifecycle acceptance against the disposable TimescaleDB CI service:
  - DB-clock heartbeat renewal while runtime is RUNNING.
  - Expired lease takeover advances fencing generation, marks old runtime LEASE_LOST, stops scheduler admission, and closes readiness.
  - Old runtime shutdown after takeover must complete without releasing or mutating the replacement generation.
  - Drain timeout retains the lease; successful drain releases it.
  - Restart acquires a strictly higher generation.
- RED exposed a real runtime defect: after takeover, `FeederRuntime.stop()` treated the expected failure to release the old generation as a fatal shutdown error. Fixed it so an already-lost generation is not released again; if ownership is lost during the release race, it is treated as an expected fenced shutdown. The replacement lease remains untouched. Emits `lease_release_skipped_after_loss`.
- Corrected the test fixture to use the database's fixed canonical lease identity, `binance-btcusdt-canonical`; arbitrary lease names are rejected by the database contract.
- Updated the GitHub Actions artifact manifest so the lifecycle test log and verdict are retained in the TimescaleDB artifact.

### Test-driven evidence

1. Initial CI run `42156450016`, source SHA `e181f2a779419c6930f043be47e43d89eb0b685f`: static Gateway and Paper jobs passed; TimescaleDB lifecycle tests failed because the fixture used a noncanonical lease name. This run did not verify lifecycle behavior.
2. RED reproduction after canonical lease fixture correction, run `42156715010`, source SHA `708d815473ec653e1a4b4fa6f8616d2ac9d5079d`: lifecycle suite ran 4 tests; takeover/readiness test failed exactly at shutdown with `RuntimeError: Feeder could not release its owner/generation lease`. The other 3 lifecycle tests passed. This confirmed the runtime defect.
3. Initial GREEN implementation run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42156876274. After self-review, lifecycle-test cleanup was hardened so the old runtime is always drained/joined even if an assertion fails (commit `dbf16ab31019b91a616e5b8982ee1da513eb6fce`). Final exact-HEAD revalidation: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42157325408.
   - Event: push; branch: `feature/t0-centralized-data-feeder-p1-20261101`.
   - Final exact checked-out source SHA: `dbf16ab31019b91a616e5b8982ee1da513eb6fce` (confirmed by the TimescaleDB job's `git rev-parse HEAD` output).
   - Jobs: 3/3 SUCCESS (Static Gateway contract verification, Paper consumer fixture regressions, Isolated TimescaleDB integration).
   - Static Gateway RED contracts: 10/10 PASS.
   - Existing Gateway/Feeder regression invocation: 60 tests PASS.
   - Health/readiness invocation: 21 tests PASS.
   - Process-level SIGKILL restart/fencing invocation: 2 tests PASS.
   - Full `market_data` suite: 225 tests, 36 skipped (the DB integration cases are exercised in the dedicated disposable TimescaleDB job).
   - Paper consumer regression: 44/44 PASS.
   - Dedicated disposable TimescaleDB integration:
     - PostgreSQL atomic writer: 7/7 PASS.
     - PostgreSQL FeederRuntime: 14/14 PASS.
     - PostgreSQL FeederRuntime lifecycle: 4/4 PASS.
     - PostgreSQL least-privilege roles: 18/18 PASS.
     - Read-only TimescaleDB: 6/6 PASS.
     - Disposable target preflight PASS; no exchange credentials, production DB, or external exchange access.
   - Artifacts:
     - Static Gateway: ID `13474772650`, SHA-256 digest `e25bae2244e49e56abd11aab2e130cb6e99872e11e17a3370c534b6c432c2cc4`.
     - Paper consumer: ID `13474414668`, SHA-256 digest `ac466622bab23e52ce63b26e4dcc6e3cfe52119b03b71ce415a3c20031f1d47e`.
     - TimescaleDB including lifecycle logs: ID `13475531098`, SHA-256 digest `2679d072d2e6811110574593c73e30439db9f20bf506994e0fd346b916a8f8c6`.
   - Artifact digests are GitHub upload digests; payload bytes have not been independently downloaded and re-hashed in this increment.

### Verdict and boundaries

- P0 PostgreSQL FeederRuntime lifecycle acceptance: **PASS** on final exact source SHA `dbf16ab31019b91a616e5b8982ee1da513eb6fce` (run `42157325408`, 3/3 jobs SUCCESS).
- PG Gateway + runtime adapter + lifecycle + least-privilege + read-only integration CI: **PASS** for the tested disposable TimescaleDB environment.
- Production certification: **NOT GRANTED**. These tests do not authorize provisioning or migration of a production canonical database, creating credentials, changing TLS/network/VPS settings, starting the production Feeder, connecting Binance, or syncing market data.
- `ai_execution_enabled=false`; paper-only boundary unchanged.
- No merge performed.

### Next step

- Perform a focused self-review of the shutdown state transition and the complete P0 security/recovery design against the tested source SHA; then define the next explicitly gated production-readiness increment. Keep production provisioning and Feeder activation blocked until that review and its approval gates are complete.


## 2026-11-06 — P0 production security document reconciliation

- Self-review of the P0 production security/recovery design found two stale statements:
  1. It incorrectly claimed the PostgreSQL design document still used `MARKET_DATA_DATABASE_URL`. Current code, design, and acceptance docs consistently use `MARKET_DATA_POSTGRES_DSN`; the separate `MARKET_DATA_DB` SQLite path remains the Paper ledger/fallback path.
  2. It described disposable role/grant acceptance as not yet performed, despite the exact-source TimescaleDB role suite passing 18/18.
- Corrected `docs/T0_PRODUCTION_SECURITY_BACKUP_RPO_RTO.md` in commit `a12bd374a52cc8daa0e1f09b5922d2642ed45e8c`:
  - Removed the false DSN naming blocker and explicitly disallowed an unsupported `MARKET_DATA_DATABASE_URL` alias.
  - Recorded disposable TimescaleDB 2.17.2 role/grant acceptance 18/18 PASS.
  - Preserved the boundary that production-provider grants, provider-specific TLS/credential rotation, backup/PITR, and restore/failover remain unverified.
- Documentation-only change; no tests rerun, no source/runtime/config changes, no database/VPS/credential/network/Feeder/exchange actions.
- Current production readiness remains **BLOCKED / NOT CERTIFIED** until provider/region/cost ceiling are selected and exact-provider TLS, credential rotation, backup/PITR, restore/failover, and old-primary fencing acceptance are demonstrated.
- Next technical review: inspect production runtime DSN handling against the documented TLS `verify-full` requirement; do not weaken TLS requirements or connect to any production target.

## 2026-11-06 — P0 production PostgreSQL TLS enforcement

### Review finding and implementation

- Focused review compared production runtime connection handling with the P0 security design. The design required TLS certificate and hostname verification (sslmode=verify-full), but build_production_runtime() previously accepted PostgreSQL DSNs without validating this requirement.
- Added fail-closed _require_verified_postgres_tls() in market_data/feeder_service.py. It accepts only an explicit sslmode=verify-full parameter for both PostgreSQL URI DSNs and libpq keyword DSNs; missing mode, require, disable, duplicate/conflicting URI parameters, and malformed DSNs are rejected.
- Uses Python standard-library parsing only; no new dependency. Enforcement is scoped to production runtime composition. Low-level disposable test fixtures and direct adapter construction remain usable without a production TLS policy.
- Updated production-runtime test fixtures to declare verified TLS explicitly.
- Commits on feature/t0-centralized-data-feeder-p1-20261101:
  - 6dd113f6b3d8ad46c2dc666d550792c89004d4d9 — RED TLS enforcement tests.
  - 552aaf54aaa537f849a7e461b45ac698ffbcbdf3 — initial enforcement implementation (first CI attempt exposed that psycopg is not installed in the source-only static job).
  - f302721f203ff040ac061867b244028310e81df8 — update production test fixtures to use explicit sslmode=verify-full.
  - 0ce6fce16eedebe6108fe6105c3af850da938ef8 — switch validation to standard-library parsing; no runtime import dependency.

### TDD and CI evidence

1. RED run https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42158069198, exact source SHA 6dd113f6b3d8ad46c2dc666d550792c89004d4d9:
   - Static Gateway suite failed exactly on the new negative cases: DSNs with no sslmode, sslmode=require, and sslmode=disable were accepted.
   - This confirms the prior production runtime did not enforce the documented TLS policy.
   - Paper consumer job passed; TimescaleDB job skipped because the static suite failed.
2. First GREEN attempt on SHA f302721f203ff040ac061867b244028310e81df8 exposed a test-environment compatibility issue: the source-only static job does not install psycopg, so TLS validation must not import the DB driver. This was corrected with standard-library parsing.
3. Final GREEN run https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42158215844:
   - Event: push; branch: feature/t0-centralized-data-feeder-p1-20261101.
   - Exact checked-out source SHA: 0ce6fce16eedebe6108fe6105c3af850da938ef8, confirmed by disposable TimescaleDB job log T0_TIMESCALE_SOURCE_SHA.
   - Jobs: 3/3 SUCCESS (Static Gateway contract verification, Paper consumer fixture regressions, Isolated TimescaleDB read-only integration).
   - Static Gateway / complete market_data suite: 227 tests PASS, 36 skipped.
   - Production runtime TLS tests: negative cases for absent mode, require, and disable PASS; explicit verify-full acceptance PASS.
   - PostgreSQL atomic writer: 7/7 PASS.
   - PostgreSQL FeederRuntime: 16/16 PASS.
   - PostgreSQL FeederRuntime lifecycle: 4/4 PASS.
   - PostgreSQL least-privilege roles: 18/18 PASS.
   - Read-only TimescaleDB: 6/6 PASS.
   - Paper consumer regressions: job SUCCESS.
   - Disposable TimescaleDB preflight PASS; no production DB, credentials, exchange access, or external network ingestion.
   - Artifacts (GitHub upload metadata; payload bytes not independently downloaded/re-hashed):
     - Static Gateway ID 13474813671, digest sha256:4d177a1962b5aba1f48d71dd78c907dd00aeeadb43cef99282fda0de34997610.
     - TimescaleDB ID 13474634158, digest sha256:b943fd242500ef5d2e463c736b1067ad6a4c9e72f2a83a3e7545340712052810.
     - Paper consumer ID 13474484339, digest sha256:56cf83530e78db754e8f6b8813bdd5319db9adf4c5ecb8b382dac3b0cab82643e.

### Verdict and boundaries

- Production PostgreSQL DSN TLS policy enforcement: PASS on exact source SHA 0ce6fce16eedebe6108fe6105c3af850da938ef8.
- This verifies configuration rejection/acceptance logic only. It does not prove a real provider certificate chain, hostname, CA bundle, ingress allowlist, or remote TLS handshake; those remain staging acceptance items.
- No TLS credentials/certificates, production DB, VPS, network rules, Feeder, Binance connectivity, or market-data sync were configured or activated.
- No merge. ai_execution_enabled=false; paper-only boundary unchanged.
- Next: continue focused P0 security/recovery review, especially shutdown deadline/admission ordering and production provider-specific TLS/backup acceptance. Do not provision production resources or activate Feeder.

## 2026-11-06 — P0 Feeder shutdown admission and deadline hardening

### Review finding and implementation

- Focused review of FeederRuntime.stop() found two shutdown-order defects:
  1. It waited for the heartbeat thread before stopping scheduler admission. If heartbeat shutdown blocked, new scheduled work could still be admitted during the wait.
  2. It passed the full timeout independently to heartbeat join and scheduler drain, allowing total shutdown duration to exceed the caller's timeout budget.
- Added regression tests in market_data/test_feeder_lifecycle.py for both behaviors.
- Updated FeederRuntime.stop() in market_data/feeder.py:
  - Validate timeout as a finite, nonnegative number (or None).
  - Compute one monotonic deadline and pass only the remaining budget to each wait.
  - Stop scheduler admission immediately after requesting heartbeat stop, before waiting on heartbeat.
  - Preserve fail-closed behavior: on heartbeat/drain timeout, do not release the current lease; release only after successful drain.
  - Existing LEASE_LOST generation handling remains unchanged.
- Commits:
  - 79674e823aff2cf6eb4415a677f0674bdb819a10 — RED regression tests.
  - 8cf727450efb34723da649a0e123851d7c002aae — shutdown ordering/deadline fix.

### TDD and CI evidence

1. RED run https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42158480308, source SHA 79674e823aff2cf6eb4415a677f0674bdb819a10:
   - Two new lifecycle tests failed for the intended reasons:
     - scheduler.stop() had not run before heartbeat.join();
     - scheduler drain received the full timeout (0.1s) rather than the remaining budget (0.02s).
   - Static job failed on those two tests; Paper consumer job passed; disposable TimescaleDB job skipped after static failure.
2. GREEN run https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42158536250:
   - Event: push; branch: feature/t0-centralized-data-feeder-p1-20261101.
   - Exact checked-out source SHA: 8cf727450efb34723da649a0e123851d7c002aae, confirmed by disposable TimescaleDB job log T0_TIMESCALE_SOURCE_SHA.
   - Jobs: 3/3 SUCCESS (Static Gateway contract verification, Paper consumer fixture regressions, Isolated TimescaleDB read-only integration).
   - Static Gateway / complete market_data suite: 229 tests PASS, 36 skipped.
   - New shutdown ordering/deadline tests: 2/2 PASS; existing Feeder lifecycle regression invocation: 62/62 PASS.
   - Health/readiness: 21/21 PASS.
   - Process-level SIGKILL restart/fencing: 2/2 PASS.
   - Paper consumer regressions: 44/44 PASS.
   - Disposable TimescaleDB:
     - PostgreSQL atomic writer: 7/7 PASS.
     - PostgreSQL FeederRuntime: 16/16 PASS.
     - PostgreSQL FeederRuntime lifecycle: 4/4 PASS.
     - PostgreSQL least-privilege roles: 18/18 PASS.
     - Read-only TimescaleDB: 6/6 PASS.
     - Disposable target preflight PASS; no production DB, credentials, exchange connection, or external market-data sync.
   - Artifacts (GitHub upload metadata; payload bytes not independently downloaded/re-hashed):
     - TimescaleDB ID 13475901336, digest sha256:e30bed48efc8e3fdb14645d41b0c2032004cb883d94a2a527611c32a3a8cf8f3.
     - Static Gateway ID 13475622662, digest sha256:96a2d9f2e1d996a75a017d12909265c6d642d20043dd81f3d8d66d3f56a8ea54.
     - Paper consumer ID 13474689428, digest sha256:4b85a27809b99b11d58bb885da576e6a40aeb90db17878878820cf42b7546b3d.

### Verdict and boundaries

- Feeder shutdown admission ordering and single-deadline behavior: PASS on exact source SHA 8cf727450efb34723da649a0e123851d7c002aae.
- PostgreSQL writer/runtime/lifecycle/role/read-only regression suites: PASS on the same exact source SHA.
- This does not certify production provider TLS, backups/PITR, restore/failover, VPS/network configuration, or production runtime.
- No production DB, credentials, TLS certificates, VPS/network rules, Feeder activation, Binance connection, or market-data sync.
- No merge. ai_execution_enabled=false; paper-only boundary unchanged.
- Next: complete P0 security/recovery design self-review and enumerate exact staging acceptance gates. Production provisioning remains blocked until provider, region, cost ceiling, TLS/rotation, backup/restore, and fencing evidence are selected and approved.

## 2026-11-06 — P0 PostgreSQL TLS remote-host enforcement

### Review finding and implementation

- Additional review found that sslmode=verify-full alone is insufficient if a DSN selects a Unix-domain socket: libpq does not perform a remote TLS handshake for a local socket, so the configuration could appear compliant while TLS/hostname verification is not actually in use.
- Extended _require_verified_postgres_tls() to require both explicit sslmode=verify-full and a non-empty remote hostname. Applies to PostgreSQL URI DSNs and libpq keyword DSNs. Unix-socket paths and DSNs without a host are rejected.
- Added tests for absent remote hostname, Unix-socket host, and valid keyword DSN with remote hostname.
- Commits:
  - 976e215d96a5c7e2ab6e6b2bec68de10cb2d9671 — RED remote-host tests.
  - 631b4525059f49aac7ad588177587df3cba61844 — require remote hostname in TLS DSN validation.

### TDD and CI evidence

1. RED run https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42158795002, source SHA 976e215d96a5c7e2ab6e6b2bec68de10cb2d9671:
   - Both negative cases failed as expected: a URI DSN without a hostname and a keyword DSN using a Unix socket were accepted despite sslmode=verify-full.
   - Static Gateway job failed only on the two new TLS hostname cases; Paper consumer job passed; TimescaleDB job skipped.
2. GREEN run https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42158842138:
   - Event: push; branch: feature/t0-centralized-data-feeder-p1-20261101.
   - Exact checked-out source SHA: 631b4525059f49aac7ad588177587df3cba61844, confirmed by disposable TimescaleDB job log T0_TIMESCALE_SOURCE_SHA.
   - Jobs: 3/3 SUCCESS (Static Gateway contract verification, Paper consumer fixture regressions, Isolated TimescaleDB read-only integration).
   - Static Gateway / complete market_data suite: 231 tests PASS, 36 skipped.
   - TLS DSN contract: explicit verify-full and remote hostname accepted; absent sslmode, require, disable, missing hostname, and Unix-socket host rejected.
   - PostgreSQL atomic writer: 7/7 PASS.
   - PostgreSQL FeederRuntime: 18/18 PASS.
   - PostgreSQL FeederRuntime lifecycle: 4/4 PASS.
   - PostgreSQL least-privilege roles: 18/18 PASS.
   - Read-only TimescaleDB: 6/6 PASS.
   - Paper consumer regressions: 44/44 PASS.
   - Disposable TimescaleDB preflight PASS; no production database, production credentials, external exchange access, or market-data sync.
   - Artifacts (GitHub upload metadata; payload bytes not independently downloaded/re-hashed):
     - Static Gateway ID 13476036291, digest sha256:2ce923e2970f82afae9d556d25e207b557dbe4fd68816df17c58aee40e442109.
     - Paper consumer ID 13474839626, digest sha256:ee96910806b8ab4df23635d76ce01eabc7ff8a675368691c59cc98ac9526c5e4.
     - TimescaleDB ID 13476171027, digest sha256:a416e61bcd8d60cc661f0b46461e2fa176aede17f7423329e03f010d1fe871cf.

### Verdict and boundaries

- Production PostgreSQL TLS DSN policy (explicit verify-full plus remote hostname): **PASS** on exact source SHA 631b4525059f49aac7ad588177587df3cba61844.
- This verifies fail-closed configuration parsing and disposable database regression only. Real provider CA chain, certificate validity, hostname match, ingress allowlist, and remote TLS handshake remain **NOT VERIFIED** until a provider-specific staging target is approved.
- No production database, TLS certificate/secret, VPS, network rule, Feeder activation, Binance connection, or market-data sync.
- No merge. ai_execution_enabled=false; paper-only boundary unchanged.
- Next: finalize the P0 security/recovery design review and produce a provider-neutral staging acceptance checklist with measurable evidence requirements. Production provisioning remains blocked.

## 2026-11-06 — P0 Security & Recovery Design Review / provider-neutral staging checklist

### Review outcome

- Reviewed the PostgreSQL/TimescaleDB design, production security/backup/RPO/RTO proposal, migrations 002–004, migration runner, PostgreSQL adapter, Feeder production runtime composition, role privilege acceptance tests, and the latest TLS/shutdown changes.
- No new source-code defect was confirmed in the reviewed SECURITY DEFINER search paths, fixed canonical lease identity, generation-bound lease transitions, writer fencing, role-membership guards, or shutdown admission/deadline behavior.
- TLS enforcement currently applies at production Feeder runtime composition. Provider-specific migration-login TLS handshake and endpoint policy must also be verified as part of the staging migration gate; the current disposable CI does not prove provider certificate/hostname behavior.
- Important verification boundary: the current passing TLS tests prove DSN policy rejection/acceptance only. They do not prove a live provider CA chain, SAN/hostname, network allowlist, secret rotation, or remote handshake.
- Production security/recovery proposal remains design-only. RPO <=5m, RTO <=60m and PITR >=7d are proposed acceptance targets, not measured provider guarantees.

### New provider-neutral checklist

- Added `docs/T0_STAGING_ACCEPTANCE_CHECKLIST.md`.
- Covers entry decisions before staging, provider/engine identity, TLS/network/credential rotation, effective roles and negative privilege tests, writer fencing/runtime lifecycle, SQLite parity, backup/PITR/restore, measurable RPO/RTO, old-primary fencing, operations/rollback, and final evidence bundle.
- Defines exact pass thresholds:
  - PITR history >=7 days.
  - Actual RPO <=5 minutes.
  - Actual RTO <=60 minutes.
  - 100% of recorded keys/values/hashes restored.
  - Zero successful old-writer connections after old-primary fence.
  - Restored Feeder lease generation strictly advances.
- Clearly distinguishes existing disposable TimescaleDB CI PASS from provider-specific NOT VERIFIED gates.
- Does not select a provider, VPS, region, plan, or cost; does not provision staging or production resources.

### Git and validation

- Checklist commit: `8da1cca15e7d61bcf986040da211dad968854c16`.
- Handoff update follows this entry.
- This increment changes documentation only; no runtime/test source changed and no new CI run is claimed.
- Existing source verification remains:
  - TLS remote-host enforcement GREEN run #42158842138 on source SHA `631b4525059f49aac7ad588177587df3cba61844`.
  - Feeder shutdown admission/deadline GREEN run #42158536250 on source SHA `8cf727450efb34723da649a0e123851d7c002aae`.
- Latest branch source SHA before this documentation increment: `a50034e551b6cc3c71c1084ff14ddc5fa6d7196f`; checklist and handoff commits are documentation-only descendants.

### Verdict and limits

- P0 source-level security/runtime review: **PASS for reviewed contracts**, with provider-specific verification still open.
- Provider-neutral staging checklist: **PASS — documented**.
- Staging readiness: **BLOCKED / NOT AUTHORIZED** until entry-gate provider, engine/version, region, network, secret, backup, and cost decisions are approved.
- Production certification: **NOT GRANTED**.
- No production database, staging resource, VPS, credential, TLS certificate, network rule, backup job, Binance connection, market-data sync, or Feeder activation was created.
- No merge. T0 remains separate from Paper DB and SWG-F. `ai_execution_enabled=false`; paper-only boundary unchanged.
- Next: once provider/region/plan and cost ceiling are chosen, convert Gates A–G into a provider-specific staging execution plan. Until then, do not provision resources or run real-market ingestion.

## 2026-11-06 — T0 staging provider research (no selection)

### Work completed

- Researched two provider/topology candidates against the approved provider-neutral T0 staging gates:
  1. Hetzner Cloud Singapore with self-managed PostgreSQL/TimescaleDB and a separate off-host backup failure domain.
  2. DigitalOcean Managed PostgreSQL in Singapore (SGP1) with a separate Feeder VPS.
- Added `docs/T0_STAGING_PROVIDER_RESEARCH.md` with source links, known facts, costs published by providers, operational trade-offs, unknowns, provider-specific acceptance gates, and decisions still required.
- Research date: 2026-11-06. Public price/availability pages are snapshots, not checkout quotes.
- Evidence gathered:
  - Hetzner Singapore Cloud location and current product availability are documented; June 2026 pricing lists CCX13 at USD 63.49/month excluding IPv4, with 2 cores / 8 GB / 80 GB on the Singapore product page.
  - DigitalOcean lists Managed PostgreSQL availability in Singapore SGP1.
  - DigitalOcean Standard Edition supported-extension documentation lists TimescaleDB for PG16 and PG17; exact extension version and role/function-owner compatibility must be proven on an actual staging cluster.
  - DigitalOcean documents daily full backups and WAL/PITR over the previous seven days; this does not prove measured RPO/RTO.
  - DigitalOcean published entry prices: single-node $15/month (1 GiB); HA starts at $30/month per node with a matching standby, baseline $60/month before extras.
- No vendor feature statement is accepted as proof of T0's actual TLS, least privilege, restore, failover, fencing, RPO, or RTO requirements.

### Git and validation

- Provider research doc commit: `f0bc9867faf8bd5253017e5a662b7e2000b77817`.
- Handoff update follows.
- Documentation-only change; no runtime/test code changed and no new CI run is claimed.
- Public references are embedded in the provider research document.
- No merge and no PR creation.

### Verdict and constraints

- Provider research: **PASS — preliminary candidates documented**.
- Provider selection: **NOT DECIDED**.
- Region selection: **NOT DECIDED** (Singapore is a researched candidate only).
- Monthly/temporary budget ceiling: **NOT PROVIDED**.
- Staging provisioning: **BLOCKED / NOT AUTHORIZED**.
- Production provisioning and canonical ingestion: **NOT AUTHORIZED**.
- No account, trial, VPS, managed database, DNS, network rule, credential, TLS certificate, or backup job was created.
- No Binance connection or real market-data sync. No Feeder activation. `ai_execution_enabled=false`; paper-only.
- Next: obtain the user's provider/topology choice and explicit temporary + monthly budget ceiling. Then perform a provider-specific cost/contract review and update the staging execution plan before any provisioning.

## 2026-11-06 — User selected Timescale Cloud direction

- User selected **Timescale Cloud** as the provider direction for T0 staging planning. Current product documentation uses the name **Tiger Cloud**.
- Official region documentation lists AWS Singapore `ap-southeast-1`; Azure Singapore `southeastasia` is also listed. AWS Singapore is a candidate, not yet separately confirmed.
- Current published plan comparison: Performance starts at USD 30/month with 3-day PITR; Scale starts at USD 36/month with 14-day PITR, multi-node HA and private endpoints. Storage is billed separately; compute varies by region. These are starting prices, not an estimate or quote.
- Scale is the preliminary plan to evaluate because the proposed T0 backup-history gate is at least 7 days. No plan is approved yet.
- Tiger Cloud documents `tsdbadmin` as non-superuser. Existing migrations, SECURITY DEFINER ownership, Feeder/Reader roles and least-privilege contracts must be tested on the actual provider before staging can pass.
- CI engine baseline is PostgreSQL 16 / TimescaleDB 2.17.2. Actual service `server_version` and extension version must be recorded and compatibility proven.
- Provider HA does not replace T0 writer lease/generation fencing. Old Feeder rejection and generation advancement remain required acceptance tests.
- Research sources: https://www.tigerdata.com/docs/get-started/supported-regions ; https://www.tigerdata.com/pricing ; https://www.tigerdata.com/docs/get-started/feature-comparison ; https://www.tigerdata.com/docs/deploy/tiger-cloud/tiger-cloud-aws/security/read-only-role
- Provider-specific planning: **IN PROGRESS**. AWS Singapore: **PROPOSED**. Scale: **PRELIMINARY**. Budget ceiling: **NOT PROVIDED**.
- No trial, service, database, network connection, or paid resource was created. Staging provisioning remains **NOT AUTHORIZED**; production remains **NOT AUTHORIZED**. No new CI run is claimed.
- Next: obtain explicit monthly staging budget and confirm AWS Singapore + Scale plan; then complete a costed staging plan and seek separate provisioning approval.
- Follow-up provider research document update: `docs/T0_STAGING_PROVIDER_RESEARCH.md` commit `f463f431823bd0f456ab579b4ece1c11c85034c8` (blob `0e734a82cae28931fe1a3b1b277379de39740e57`).

## 2026-11-06 — Temporary T0 staging comparison under USD 20/month

### User decision / scope

- User submitted: provider = compare; maximum monthly budget = under USD 20; scope = temporary staging only.
- This is a comparison instruction, not a provider switch. The prior Timescale Cloud / Tiger Cloud direction remains the preferred long-term managed product direction.
- No provisioning, trial activation, payment, service creation, endpoint, network rule, credential, or secret was authorized.

### Research result

- Tiger Cloud Free: USD 0, includes PostgreSQL + TimescaleDB, but free services are currently hosted in AWS us-east-1, have 750 MiB storage and limited shared resources, and omit VPC/replication/metrics and other operational capabilities. Suitable only for schema/migration compatibility experiments; not complete T0 staging.
- Tiger Cloud Performance starts at USD 30/month plus storage; Scale starts at USD 36/month plus storage. Both exceed the USD 20 cap. Scale has 14-day PITR/private endpoints/multi-node HA; Performance PITR is 3 days.
- DigitalOcean Managed PostgreSQL Standard in Singapore SGP1 is a cost-fit candidate, not selected: published single-node floor USD 15/month for 1 GiB; additional storage billed separately; TimescaleDB appears in the supported-extension lists for PG16/17; daily backup + PITR up to 7 days. Single node is not HA; superuser is unavailable; exact extension version, role/migration compatibility and checkout total remain unverified.
- Self-managed VPS may fit but was not quoted and moves TLS, patching, PITR, backup, restore and monitoring responsibility to the operator.
- Recommendation: retain CI disposable TimescaleDB as primary source-level acceptance. If provider endpoint testing is necessary, evaluate Tiger Cloud Free for schema-only or DigitalOcean SGP1 single node for limited provider compatibility, with synthetic data only. If the full acceptance requires HA/private endpoint/production-like recovery, raise the budget instead of weakening gates.

### Git and validation

- Research comparison appended to `docs/T0_STAGING_PROVIDER_RESEARCH.md`.
- Research commit: `df3be61c69782d1966f36a88466fa02bc97f6cfe`; blob `117ebea9cdd30ad48cedad1a8780e950c8cfd018`.
- Handoff update follows.
- Documentation-only; no source/tests changed; no new CI run claimed.
- Sources linked in research document include official Tiger Cloud and DigitalOcean pricing, regions, extension, feature and limit docs.

### Verdict / boundaries

- Provider comparison: **PASS — documented**.
- Budget constraint: **UNDER USD 20/month**.
- Scope: **TEMPORARY STAGING ONLY**.
- Long-term provider direction: **Timescale Cloud / Tiger Cloud remains preferred**.
- Tiger Cloud paid plans: **OVER BUDGET**.
- Tiger Cloud Free: **LIMITED — not complete staging**.
- DigitalOcean SGP1 single node: **COST-FIT CANDIDATE — NOT SELECTED**.
- Self-managed VPS: **NOT QUOTED**.
- Provisioning: **NOT AUTHORIZED**.
- No real Binance data, canonical T0 data, production credentials or Feeder activation.
- `ai_execution_enabled=false`; paper-only boundary unchanged.
- Next: decide whether a limited paid compatibility endpoint is needed at all. If yes, obtain exact checkout cost and approve the specific provider/service/maximum spend before provisioning. Otherwise continue CI-based validation and preserve the budget.


## 2026-11-06 — DigitalOcean candidate compatibility review and VPS decision reaffirmation

- User reaffirmed: VPS **NOT DECIDED**. No provider, VPS, region or configuration selection; no account, trial, payment, resource, network rule, secret or service provisioning. Continue PC + existing CI validation.
- Reviewed current T0 migration/runtime source and current official DigitalOcean Standard PostgreSQL documentation. Research details are recorded in `docs/T0_STAGING_PROVIDER_RESEARCH.md` section 9.
- DigitalOcean Standard officially lists TimescaleDB for PostgreSQL 16/17; current CI baseline is PG16/TimescaleDB 2.17.2. Exact provider extension version is not documented by the support matrix and remains NOT VERIFIED. Do not select PG18 for this candidate unless its current extension matrix changes.
- DigitalOcean documents `doadmin` as CREATEROLE but not superuser. T0 migrations 003/004 create capability/owner roles and transfer SECURITY DEFINER ownership; migration runner uses `SET ROLE t0_migrator` when that role exists. A fresh-cluster bootstrap/migration sequence must therefore be proven; public docs alone do not establish compatibility. A narrow pre-bootstrap of reserved roles/memberships is a hypothesis only, not proven or authorized.
- Provider TLS verify-full is documented with CA certificate for Standard, but actual CA/SAN handshake remains NOT VERIFIED.
- Status: source-level candidate review **PARTIAL PASS**; provider migration compatibility **NOT VERIFIED**; exact extension version **NOT VERIFIED**; TLS handshake **NOT VERIFIED**; restore/RPO/RTO/failover fencing **NOT VERIFIED**.
- No code/tests/migrations/workflows changed. Documentation-only update; no CI run claimed. No provider endpoint, VPS, database or credentials created. No Binance connection, canonical ingestion or Feeder activation.
- Research update commit: `79b705b6e74bfb79f55e950f9e3d50b8b6c89f32`; research blob: `b98446be4d408ab651da1cc72b0375d0fbd37599`.
- Next safe step: continue source-level review and design a disposable provider-compatibility acceptance script/checklist. Do not provision until the user separately approves a named provider, plan, region, exact spend cap and temporary purpose.
- Hard boundaries unchanged: T0 remains an independent data asset; PC + existing CI; no VPS decision; no canonical DB/real market data/Feeder activation; `ai_execution_enabled=false`; paper-only.


## 2026-11-06 — T0 current-state source audit

- Audited the current active branch tip `325cc4b3527442454ac15fe87ef0dc204ed3ef8d`; comparison against the branch ref returned `identical` (0 ahead / 0 behind).
- Confirmed source files and current blob identities:
  - `market_data/feeder.py`: `f782a75e01394a21f2bb3c987909951b83d23642`.
  - `market_data/feeder_service.py`: `0b7c44d538af5f2899d3d184b7d9b65ce87dd803`.
  - `market_data/postgres.py`: `2fe27fe2d066dda0c192a381b72d27404487b800`.
  - `market_data/storage.py`: `13fe1ae01ebb5318b69e69eef3e512d207f74c49`.
  - `market_data/migrations.py`: `b4574f2a867b0dae7818cd39249cfd95fe0ce1f0`.
  - `market_data/migrations/002_t0_feeder_leases.sql`: `009474f187a143381e5b29209a64709698795854`.
  - `market_data/migrations/003_t0_database_fenced_candle_writer.sql`: `1e08f77a9e6411050f370f8f14096dcbff605aea`.
  - `market_data/migrations/004_t0_fenced_lease_api.sql`: `cc79631a0c4e12010dc120413973cab7f84f6406`.
  - `market_data/test_postgres_feeder_runtime_lifecycle.py`: `75575786038d0033fae41950e4239c55b8b8de73`.
  - `market_data/test_postgres_role_privileges.py`: `7aef94df5c8d7c6ed754a3d18bcbb8bb1a0151b6`.
  - `market_data/test_postgres_write_gateway.py`: `63339efa52806cb787dea0a1dd7a6d60ffa55629`.
  - `market_data/test_postgres_feeder_runtime.py`: `1d00ef7d9cdb1447beb643bf9022f6857e377c8b`.
  - `market_data/test_feeder_health.py`: `80e0b7d042c821d4814d626b69c3196853dc49d9`.
- Source audit confirms: SQLite remains default; PostgreSQL is opt-in; constructors do not implicitly migrate; production PostgreSQL DSN requires `sslmode=verify-full` plus a remote hostname; PostgreSQL lease and candle writer use the same DSN and fenced Gateway; canonical lease identity is fixed; owner capability is generated per process; 15m/1h are the configured feeder timeframes; recovery and scheduler route through the canonical sync path.
- SQL review confirms the fenced candle function locks and validates the canonical lease, uses conflict-safe insert, rejects conflicting historical candle values, and rechecks lease expiry before commit. Lease API uses DB clock and generation-bound acquire/heartbeat/release/current checks. Runtime lifecycle integration tests exist for PostgreSQL heartbeat renewal, lease takeover/readiness closure, drain timeout retaining lease, and restart generation advancement.
- Existing recorded CI evidence remains: lifecycle/shutdown GREEN at source SHA `8cf727450efb34723da649a0e123851d7c002aae`, workflow #42158536250; TLS DSN configuration GREEN at SHA `631b4525059f49aac7ad588177587df3cba61844`, workflow #42158842138. Historical test totals/artifacts remain as recorded in preceding handoff entries. This audit did not rerun CI, and no direct-head CI result is claimed for the current docs-only tip.
- Assessment: core T0 feeder scheduling/retry/lease/health and PostgreSQL writer/runtime security implementation **SOURCE REVIEW PASS** against current source; prior CI evidence **PASS for the recorded SHAs**; current exact tip CI **NOT VERIFIED**; provider migration/TLS/restore compatibility **NOT VERIFIED**; production readiness **NOT READY / NOT AUTHORIZED**.
- Gaps still open: run a disposable PG16/TimescaleDB test of the exact restricted migration bootstrap sequence; add or run end-to-end PG lifecycle coverage on the current exact source tip; verify provider TLS CA/SAN, backup/PITR restore and measured RPO/RTO only after a provider is separately approved. No current provider endpoint exists.
- No code, migrations, credentials, workflow, VPS, database, exchange connection or feeder activation was changed/created. Documentation-only audit; no CI run claimed.
- Next safe step: implement a disposable CI bootstrap-privilege acceptance fixture for the restricted migration sequence and run all T0 suites on the exact source SHA. Preserve SQLite default and all production gates.
- VPS/provider remains **NOT DECIDED**; PC + existing CI only. T0 remains independent; no real Binance data or canonical ingestion; `ai_execution_enabled=false`.


## 2026-11-06 — Restricted provider bootstrap fixture

- Continued the active T0 workstream on `feature/t0-centralized-data-feeder-p1-20261101`; no new branch or PR was created.
- Added `test_non_superuser_bootstrap_prepares_restricted_migrator_roles` to `market_data/test_postgres_role_privileges.py`.
- The fixture models a non-SUPERUSER bootstrap login with CREATEROLE/CREATEDB, prepares the temporary migration roles and memberships, creates a disposable database owned by `t0_db_owner`, pre-enables TimescaleDB as a provider-controlled step, then runs migrations through the restricted `t0_migrator_login`.
- Test change commits: `22b5b2611d07296536fa402fa34f0243e94f1544` (initial test) and `66194a83d421050514f1d401ceff4bfd425dce81` (teardown grant cleanup). Final test blob: `ffa5d9102b15aad7792a07d9f73eb07bfeac8f2d`.
- Evidence scope report: `docs/evidence/T0_PROVIDER_BOOTSTRAP_FIXTURE_2026-11-06.md`; commit `8a7e7da5566f9f6218ffe6f6c55896b05a96d674`.
- Self-review: temporary database and role identifiers are unique; role grants are parameterized with psycopg SQL identifiers/literals; database creation uses autocommit; cleanup drops the database before revoking and dropping temporary roles. The test intentionally does not weaken role guards.
- Verification: **NOT VERIFIED**. GitHub combined status lookup for source commit `66194a83d421050514f1d401ceff4bfd425dce81` returned no status checks; no test result is claimed. Earlier CI results apply only to their recorded SHAs.
- Scope limitation: the shared CI service already has the T0 capability/owner roles from its baseline migration, so this fixture does not prove pristine-cluster creation of every reserved role. TimescaleDB extension enablement is performed by the service admin; provider-specific extension privileges remain NOT VERIFIED. The fixture is a compatibility probe, not certification for DigitalOcean/Tiger Cloud.
- No VPS/provider provisioning, external DB, credential, canonical T0 DB, Feeder activation, exchange connection, market-data sync, or live execution.
- Next: retrieve the direct-push GitHub Actions run for this branch and verify the exact checked-out SHA; run the focused new integration test and full `market_data` suite. If unavailable, mark BLOCKED/NOT VERIFIED and do not infer PASS. If the test exposes a provider permission gap, preserve logs and update the provider acceptance requirements rather than broadening migration privileges.
- VPS/provider remains **NOT DECIDED**; PC + existing CI only. T0 remains an independent data asset; `ai_execution_enabled=false`; paper-only.


## 2026-11-06 — Fresh-cluster restricted provider bootstrap acceptance

- Follow-up review found the first bootstrap probe was unsuitable for the shared TimescaleDB integration job: it attempted to create fixed cluster-wide roles after the baseline migration path had already created some of them, and its temporary bootstrap membership of `t0_db_owner` conflicted with the migration role-isolation guard. That probe was removed from `market_data/test_postgres_role_privileges.py`; no production migration or privilege rule was changed.
- Replaced it with a dedicated fresh-cluster test: `market_data/test_postgres_provider_bootstrap.py`. The test fails closed if any reserved T0 role already exists, creates a temporary non-SUPERUSER bootstrap login with CREATEROLE/CREATEDB, provisions all seven fixed T0 roles, grants the migration memberships, revokes bootstrap memberships before migration safety checks, and runs migrations using only `t0_migrator_login`.
- The dedicated test asserts schema/table ownership by `t0_db_owner`, SECURITY DEFINER function ownership by the two owner roles, restricted role attributes, exact ephemeral-login membership, and absence of unexpected owner-role memberships.
- Added independent GitHub Actions job `restricted-provider-bootstrap-integration` in `.github/workflows/t0-single-writer-gateway-red.yml`. It starts its own clean `timescale/timescaledb:2.17.2-pg16` service and does not share the pre-migrated DB from other integration jobs. Preflight pins loopback, database/user, disposable flag, and empty Paper/exchange credential variables.
- Source/test commits: new test `edc3d653c0929768dead89301622dc0e14ab75b6`; removal of unsuitable test `34efd769266472826b36bc13d9ab4a4b10eae4c2`; CI job `b2394dc97e80d7f87b5ff2e1f2138a310d02b256`; ownership assertions `3eb21368eaa4b0d46d69a1ba1a97ae5f80e226d3` and `7e6ec2dab44c954bc48ded7eda14b93a1c1c7b13`.
- Current test blob: `bc3509795d27caf75880726cb2885bc5038b9c3c`; current workflow blob: `47e8312469db0772eba52053005324314fe0baf6`; current evidence doc blob: `48b3835d91b99b65906efc31b359af000bcdf741`.
- Self-review: test uses random database/bootstrap identity, parameterized identifiers and passwords, dedicated isolated service, checks no pre-existing reserved roles, removes temporary bootstrap memberships before migration, and drops the DB before dropping roles. It intentionally does not change migration logic or role guards.
- Verification: **NOT VERIFIED**. No direct-push Actions run result has been retrieved for the new job/source. Do not treat the CI workflow definition or earlier TimescaleDB runs as test evidence for this change.
- Scope limits: a passing CI result will cover only PG16 + TimescaleDB 2.17.2 under this test fixture. It will not certify DigitalOcean/Tiger Cloud semantics, extension provisioning permissions, provider TLS CA/SAN, PITR/restore, RPO/RTO or failover fencing.
- No VPS/provider provisioning, external DB, credential, canonical T0 DB, Feeder activation, exchange connection, market-data sync, or live execution. VPS/provider remains **NOT DECIDED**; PC + existing CI only. T0 remains independent; `ai_execution_enabled=false`; paper-only.
- Next: retrieve the direct-push workflow run for this exact branch tip; verify checkout SHA, new bootstrap job result, complete `market_data` suite and artifact digest. If the job fails, preserve logs and diagnose the exact managed-role permission requirement without weakening security guards.


### Bootstrap fixture self-review follow-up — 2026-11-06

- Tightened the fresh-cluster test after review: it now asserts ownership of all four migration tables (`candles`, `feeder_leases`, `instruments`, `schema_migrations`) and all five SECURITY DEFINER functions (one candle writer plus four lease API functions).
- Hardened teardown ordering: drop the disposable database first, drop the temporary bootstrap login next (so any ADMIN memberships left by a partial setup are removed), then drop the reserved roles. This covers failure paths before the normal bootstrap-membership revocation point.
- PostgreSQL 16 official role docs confirm that non-superuser CREATEROLE users receive ADMIN OPTION membership on roles they create, with SET/INHERIT disabled by default; the test explicitly revokes these temporary memberships before invoking migration safety checks. This is only the PostgreSQL 16 baseline, not a managed-provider compatibility guarantee: https://www.postgresql.org/docs/16/role-attributes.html
- Latest source commit: `b85b6cc5f99511b11aa2eacbabeb20a87595d78e`; test blob: `4874c64101cd86929b3317d722ac462dfb7cafbf`; evidence doc blob: `800090fb7d14abefeea63127c908cdc354d9ea7c`.
- Verification remains **NOT VERIFIED** pending the exact direct-push Actions job result. Do not infer a test PASS from source review or workflow definition.


### Bootstrap fixture cleanup isolation — 2026-11-06

- Added explicit per-role creation tracking. The test teardown now drops only reserved roles that this test successfully created. If the pristine-cluster precondition fails because any T0 role already exists, cleanup leaves all pre-existing roles untouched.
- Teardown order is: drop disposable database; drop temporary bootstrap login to clear any auto-created ADMIN memberships left by an interrupted setup; then drop only fixture-created reserved roles.
- Latest bootstrap test source commit: `7d194d29ae011330b22f74d65401e68654b995f3`; test blob: `6e2f59b4b8725f15156e98e8f7360c9639be7986`; evidence doc blob: `2e28c4e29fa628fad52347130f231e4433656659`.
- Direct-push CI status remains **NOT VERIFIED**: GitHub connector's combined-status endpoint returned no status entries and its workflow-run wrapper only exposes PR-triggered runs. This is an observability limitation, not evidence of success or failure. Need obtain the direct-push run and inspect exact checkout SHA/job logs/artifact before setting PASS.

## T0 provider bootstrap fixture — syntax correction and CI rerun (2026-11-06)

- Active branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Previous source SHA `7d194d29ae011330b22f74d65401e68654b995f3` was checked out exactly by workflow run #42165196769 (push event).
- Run #42165196769: FAILURE. The new provider bootstrap test had a Python syntax error at line 185: an SQL string literal was split across physical lines without adjacent-string concatenation. The same import error caused the full `market_data` suite to fail (232 tests discovered, 1 import error, 36 skipped). The dedicated fresh-cluster job failed at `py_compile`; no PostgreSQL bootstrap logic was executed.
- Corrected only the SQL string concatenation in `market_data/test_postgres_provider_bootstrap.py`; no role grants, migration guards, runtime behavior, or workflow privileges were changed.
- Fix commit/source SHA: `92a8ba178716d73b3cdb645cc441ec99e775e962`; test blob: `0fde856def1e71c691e9f71c685814d08e3f9af7`.
- Follow-up push workflow #42165386542: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42165386542
  - Exact head SHA: `92a8ba178716d73b3cdb645cc441ec99e775e962`.
  - Static Gateway job #127720536760: SUCCESS, including Gateway contracts, behavioral/feeder regressions, health/readiness, SIGKILL restart/fencing, and complete `market_data` regression suite.
  - Paper consumer job #127720533177: SUCCESS.
  - At handoff update time, fresh-cluster restricted provider bootstrap job #127720532984 and isolated TimescaleDB read-only integration job #127720611217 were still initializing their service containers; results NOT VERIFIED / IN PROGRESS. Do not infer PASS from static success.
- Artifacts already published for run #42165386542:
  - Static evidence artifact ID `13477959914`, SHA-256 `ad2b2b1908852e84050d124f8d5996eaed444ccfb485c95c484f408d7d116df7`.
  - Paper consumer artifact ID `13478618479`, SHA-256 `631f953d8ea5b5a97dcef77f423d1a7527be5dca17662f2949016c61ecc0980d`.
  - Provider bootstrap artifact not yet listed at update time.
- Previous failed-run artifacts (not valid as passing evidence):
  - Static artifact ID `13478264153`, SHA-256 `ac4c1d524d60da075cd130f033a302c69e98ec5f18bd985a4bebb141175cf205`.
  - Provider bootstrap artifact ID `13478134662`, SHA-256 `af3693850d57c51e463daa6bb992ef5daf1419adc58ef6af0f11fc4ba6ab43c4`.
- Current verdict: syntax correction committed; static + paper CI PASS on exact SHA `92a8ba178716d73b3cdb645cc441ec99e775e962`; provider bootstrap / TimescaleDB integration NOT VERIFIED pending run completion. Managed-provider compatibility remains NOT VERIFIED.
- Safety: test uses only the workflow's disposable local TimescaleDB service. No provider/VPS provisioning, canonical T0 database, Feeder activation, exchange connection, Binance sync, Paper DB mutation, or live execution.
- Next: inspect completion and logs for run #42165386542, especially the fresh-cluster bootstrap. Diagnose permission/migration failures without broadening privileges or weakening migration guards; then update this handoff with exact job outcomes and artifact digests.

## T0 provider bootstrap fixture — second diagnosis and cleanup correction (2026-11-06)

- Follow-up source SHA `92a8ba178716d73b3cdb645cc441ec99e775e962`, workflow run #42165386542, checked out exactly.
- Run #42165386542 results:
  - Static Gateway contract verification: SUCCESS, including full `market_data` suite.
  - Paper consumer fixture regressions: SUCCESS.
  - Isolated TimescaleDB read-only integration: SUCCESS:
    - PostgreSQL atomic writer: 7/7.
    - PostgreSQL FeederRuntime + composition contracts: 18/18.
    - FeederRuntime lifecycle: 4/4.
    - Least-privilege role integration: 18/18.
    - Read-only TimescaleDB integration: 6/6.
  - Fresh-cluster restricted provider bootstrap: FAILURE, isolated to its test fixture.
- Bootstrap failure diagnosis from job #127720532984:
  1. The dedicated database already had the TimescaleDB extension, so unconditional `CREATE EXTENSION timescaledb` raised `DuplicateObject`. This is compatible with provider-managed/preinstalled extension behavior; fixture now uses `CREATE EXTENSION IF NOT EXISTS`.
  2. The bootstrap login was the grantor for membership edges `t0_migrator -> {t0_db_owner,t0_candle_writer_owner,t0_lease_manager_owner}` and `t0_migrator_login -> t0_migrator`. Dropping the bootstrap role before revoking those edges raised `DependentObjectsStillExist`. Teardown now revokes only those test-created membership edges as service admin, then drops bootstrap and reserved roles.
  3. No migration or production role policy was changed. The fix does not add privileges or weaken guards.
- Fix commit/source SHA: `3bf7f0c807c497f18ac84999d2555bed92b501fb`; test blob `c7beb4f33a27cdda0a3f5f10edc5163988598f72`.
- Fix workflow run #42165516115: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42165516115
  - Exact head SHA: `3bf7f0c807c497f18ac84999d2555bed92b501fb`.
  - Static Gateway job #127720956063: SUCCESS, including full `market_data` suite.
  - Paper consumer job #127720955939: SUCCESS.
  - Fresh-cluster bootstrap job #127720955957 and isolated TimescaleDB integration job #127721029764 were still in progress at this handoff update; bootstrap result NOT VERIFIED.
- Artifacts from the prior exact-source run #42165386542:
  - Provider bootstrap failure evidence artifact ID `13478802306`, SHA-256 `7760c1a2006c7d92f878b71b5a01f2f59c26406cc1b0811d693191915436b613`.
  - TimescaleDB integration PASS artifact ID `13478449224`, SHA-256 `cf3d0b7e29c63080784338de2147b2db1ad824231e4b7b860fb93d1590509e78`.
  - Static evidence artifact ID `13477959914`, SHA-256 `ad2b2b1908852e84050d124f8d5996eaed444ccfb485c95c484f408d7d116df7`.
  - Paper consumer artifact ID `13478618479`, SHA-256 `631f953d8ea5b5a97dcef77f423d1a7527be5dca17662f2949016c61ecc0980d`.
- Current verdict: general static + TimescaleDB read-only integration PASS on `92a8ba178716d73b3cdb645cc441ec99e775e962`; bootstrap fixture remains NOT VERIFIED until run #42165516115 completes. Managed-provider compatibility is still NOT VERIFIED.
- Next: inspect run #42165516115 exact source checkout and the bootstrap test result/logs. If it passes, verify artifact digest and update the evidence manifest. If it fails, preserve the failure and make the smallest test-only correction. No provider/VPS provisioning or production activation.

## T0 restricted provider bootstrap — run #42165516115 final result (2026-11-06)

- Active branch: `feature/t0-centralized-data-feeder-p1-20261101`; branch tip after this handoff update will be recorded by the resulting docs commit.
- Exact source SHA tested: `3bf7f0c807c497f18ac84999d2555bed92b501fb`.
- Workflow run #42165516115: FAILURE (completed), exact head SHA confirmed.
- Job outcomes:
  - Static Gateway contract verification #127720956063: SUCCESS. Includes Gateway static contracts, behavioral/feeder regressions, Health/Readiness, SIGKILL restart/fencing and complete `market_data` suite.
  - Paper consumer fixture regressions #127720955939: SUCCESS.
  - Isolated TimescaleDB read-only integration #127721029764: SUCCESS:
    - Atomic writer 7/7.
    - FeederRuntime/composition 18/18.
    - Lifecycle 4/4.
    - Least-privilege role tests 18/18.
    - Read-only integration 6/6.
  - Fresh-cluster restricted provider bootstrap #127720955957: FAILURE at `migrate(migrator_dsn)`, `market_data/migrations.py::_assert_writer_roles_safe`, raising `RuntimeError: t0_migrator may only be granted to the ephemeral t0_migrator_login role`.
- Downloaded and inspected provider bootstrap artifact #13478673154, SHA-256 `efdaa285f26ae4ce3d66dd9628618b68ebad64655f87a265c60c20657e48905a`. It confirms the test ran one case and failed at the safety guard. Teardown then also failed to drop the temporary bootstrap role because it remained the grantor of membership edges:
  - `t0_migrator` in `t0_db_owner`;
  - `t0_migrator` in `t0_candle_writer_owner`;
  - `t0_migrator` in `t0_lease_manager_owner`;
  - `t0_migrator_login` in `t0_migrator`.
- TimescaleDB integration artifact #13478966960, SHA-256 `2bc3e07f5518f64d234f2c1c5a9c742fa86c0dea6fa0ac21007beefae8dcccaf`.
- Static evidence artifact #13478946980, SHA-256 `ac35b299504ff86ae66bf48c6b190d009b97386aa674b5fb8c0134d6c2a47be0`.
- Paper consumer artifact #13478394447, SHA-256 `3024330fadae4c527895c00ab80ebe476d89146235aebadd73e529d52b3688df`.
- Diagnosis boundary: extension setup and initial SQL syntax are fixed. Current failure is a PostgreSQL 16 role-membership/grantor lifecycle mismatch in the test bootstrap. The migration guard is correctly failing closed; do not weaken it. Teardown also needs to revoke membership edges as their actual grantor (the temporary bootstrap login), not as the service admin. The exact residual membership responsible for the safety guard must be identified from PostgreSQL catalog state before changing the fixture.
- Current status: core T0 PostgreSQL runtime/read-only integration PASS on exact source SHA; fresh-cluster non-superuser provider bootstrap BLOCKED; managed-provider compatibility NOT VERIFIED.
- Next: improve the disposable fixture's diagnostic capture to record `pg_auth_members` (roleid/member/grantor/admin_option/set_option/inherit_option where supported) and effective role membership immediately before migrations, while keeping secrets redacted. Then make a test-only correction based on that evidence; teardown must connect as the temporary bootstrap grantor to revoke its own test-created membership edges before dropping it. Re-run exact-source CI. No migration guard weakening, no provider/VPS provisioning, no production database, no Feeder activation, no exchange connectivity or canonical ingestion.

## T0 provider bootstrap — PostgreSQL 16 implicit ADMIN membership confirmed (2026-11-06)

- Active branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Diagnostic source SHA: `7c41ac990a7a0842b773a2d07b8db2f1d769a855`.
- Test file blob at that SHA: `9f87e583e8d889323996aa4d507d6c50300a9f49`.
- Workflow #42166319563 completed with overall FAILURE:
  - Static Gateway contract verification job #127723514991: SUCCESS; includes Gateway contracts, feeder regressions, Health/Readiness, SIGKILL restart/fencing and complete `market_data` regression suite.
  - Paper consumer job #127723514816: SUCCESS.
  - Isolated TimescaleDB integration job #127723614595: SUCCESS:
    - PostgreSQL atomic writer 7/7.
    - FeederRuntime/composition 18/18.
    - Lifecycle 4/4.
    - Least-privilege role integration 18/18.
    - Read-only TimescaleDB 6/6.
  - Fresh-cluster restricted provider bootstrap job #127723515188: FAILURE at existing `_assert_writer_roles_safe()` guard.
- Downloaded diagnostic artifact #13478428940, SHA-256 `6e99f27f09949cf05c7cae43521d770a6ed9aeca8c562f6d490f6aa52e43c63c`. Its pre-migration catalog query records:
  - `t0_migrator` granted to bootstrap login by `t0_test`, ADMIN=true, SET=false, INHERIT=false.
  - `t0_db_owner`, `t0_candle_writer_owner`, `t0_lease_manager_owner`, and `t0_migrator_login` also have automatic bootstrap membership rows with grantor `t0_test`, ADMIN=true, SET=false, INHERIT=false.
  - Explicit intended grants from bootstrap login to `t0_migrator` (owner roles) and `t0_migrator_login` (migrator) have grantor bootstrap login and ADMIN=false, SET=true, INHERIT=true.
- Root cause is documented PostgreSQL 16 behavior, not a fixture bug: when a non-superuser CREATEROLE role creates another role, PostgreSQL automatically grants the created role back to the creator with ADMIN true, SET false, INHERIT false. The grantor is the bootstrap superuser; the CREATEROLE user cannot revoke/change this automatic membership. Official PostgreSQL 16 docs:
  - https://www.postgresql.org/docs/16/role-attributes.html
  - https://www.postgresql.org/docs/16/sql-createrole.html
- The T0 migration guard correctly rejects the extra bootstrap membership of `t0_migrator`. Do not weaken the guard or permit arbitrary ADMIN membership.
- Run #42166319563 artifacts:
  - Static evidence #13479136579, SHA-256 `b7676699ec4a497a2ae1b4d054a141b76e48606e2502a753fef01a0950585a69`.
  - Paper consumer #13478883570, SHA-256 `1e0945f9344b20a5ba7299971245fab87e63ba08d0ebe046703533d72e50ecc7`.
  - TimescaleDB integration #13479106179, SHA-256 `b0ddf990becfabd4a63d60dc7dd8c286fb7ad55ab2dafde5fdc54466ade82678`.
  - Bootstrap diagnostic #13478428940, SHA-256 `6e99f27f09949cf05c7cae43521d770a6ed9aeca8c562f6d490f6aa52e43c63c`.
- Provider compatibility consequence: using a non-superuser CREATEROLE admin (e.g. DigitalOcean `doadmin`) to create the T0 reserved roles conflicts with the current strict membership guard. Candidate status downgraded to BLOCKED unless provider offers a supported privileged pre-provisioning operation that avoids these memberships. Tiger Cloud behavior remains provider-specific and NOT VERIFIED.
- Updated `docs/T0_STAGING_PROVIDER_RESEARCH.md` section 10 with evidence and permitted paths. Research commit: `421bcc8c3d3cbc14c097ac0dc572d5703b0bf6e4`; research blob: `f511b259daf576f44037399555045a1c45a00f1f`.
- Current status: core T0 PostgreSQL runtime/read-only integration PASS; non-superuser CREATEROLE provider bootstrap BLOCKED; provider endpoint/TLS/backup/PITR/RPO/RTO/failover NOT VERIFIED.
- Next: keep the role guard unchanged. Determine from official provider documentation/support whether reserved T0 roles can be provisioned by a provider control-plane path without implicit CREATEROLE membership, or retain the provider candidate as BLOCKED. If considering an explicit trusted-admin membership exception, prepare a threat model and request user approval before any code change.
- Safety unchanged: no VPS/provider selection, no provisioning/payment, no production DB/credentials, no Feeder activation, no Binance/OKX connection, no canonical market-data sync, no Paper DB mutation and no live execution.



## 2026-11-06 — T0 PC Temporary Runtime plan

- Active branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Branch source HEAD at planning start: `a743295f7b5399f0555e8d292041a7b41b864925`; compare against that SHA confirmed the branch ref was identical before this documentation increment.
- Added `docs/T0_PC_TEMPORARY_RUNTIME_PLAN.md`, committed as `2371bf77b72c16bcb3b01e116d7998217ba58609`.
- Plan is documentation-only and **PLAN ONLY / NOT AUTHORIZED TO START**. It defines PC as a temporary validation host, not production/canonical host.
- Source review used `market_data/feeder_service.py`, `market_data/storage.py`, `.github/workflows/t0-single-writer-gateway-red.yml`, and `docs/T0_STAGING_ACCEPTANCE_CHECKLIST.md`.
- Important source-derived constraint: offline deterministic validation must use injected `build_runtime()` with a fake exchange and synthetic candles; `build_production_runtime()` constructs a Binance USD-M client and is not an offline test entrypoint. SQLite candle/lease stores must share one DB path; PostgreSQL candle/lease/gateway must share one DSN. Storage initialization/migrations remain explicit.
- The plan separates offline deterministic validation, isolated local lifecycle/fault testing, PC endurance, separately approved public market-data connectivity, and later VPS staging/cutover proof.
- Explicit non-authorizations retained: no package installation, OS configuration changes, database creation/opening, Feeder startup, exchange connection, market-data sync, provider/VPS provisioning, production credentials, Paper DB mutation or live execution.
- No tests were run, no workflow was triggered, no source/runtime code changed, and no database or Feeder was started. This increment does not establish PC operational stability.
- Plan document commit: `2371bf77b72c16bcb3b01e116d7998217ba58609`. Handoff provenance correction commit before this final note: `91c7c63e24957b97d43b5ed04fe0184b5fe01eb2`. Resolve the current branch HEAD from the GitHub branch ref at the next session boundary; the contents API does not expose working-tree state.
- CI evidence: NOT RUN. No workflow run or artifact exists for this documentation-only change.
- T0 provider bootstrap remains BLOCKED under PostgreSQL 16 non-superuser CREATEROLE semantics; keep migration guard unchanged. VPS/provider remains NOT DECIDED.
- Next safe step: read-only PC capability inventory (OS, Python, available resources, disk/filesystem and time sync) and review the exact proposed offline test scope. Before any DB creation or Feeder process startup, obtain explicit approval for that isolated test scope.


## 2026-11-06 — PC inventory deferred

- User confirmed the intended temporary PC operating system is **Windows**.
- User explicitly requested to postpone the PC capability inventory. Do not ask for or run the PowerShell inventory until the user resumes this task.
- PC Temporary Runtime remains **PLAN ONLY / NOT AUTHORIZED TO START**. No PC inventory evidence has been collected; Windows version/build, CPU, RAM, disk/filesystem, Python installation and time synchronization are all **NOT VERIFIED**.
- No package installation, Windows configuration change, database creation/opening, Feeder startup, exchange connection or market-data synchronization is authorized by this update.
- Keep the existing PC plan and all safety boundaries unchanged: PC is a proposed isolated validation host only, not yet a canonical writer; no concurrent PC/VPS writers; no provider/VPS provisioning; no weakening of lease/fencing or PostgreSQL role guards.
- No tests were run and no workflow was triggered for this update.
- Next step is **PAUSED**. Resume with read-only Windows PC inventory only when the user asks to continue.

## 2026-11-06 — T1.2 Dual Ledger / RED 1 started

- Active branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Verified branch HEAD before this increment: `f0ccaaf235c00db84e62d1cc278ecefe078d2e8b`.
- User-confirmed architecture: independent `CORE_LEDGER` and `AI_LEDGER`; one shared, fail-closed Risk Engine; no fixed position-count cap; each new ENTRY or exposure-increasing DCA reserves margin equal to 1% of current Account Equity; both strategies remain PAPER-only.
- Account-level controls remain mandatory: configured Max Exposure, Max Drawdown, Daily Loss and Kill Switch. Gross Exposure is authoritative; do not net opposing strategies to reduce risk. Exposure reductions remain allowed while new exposure is blocked.
- Reviewed existing implementation and contract: `paper_execution/ledger.py` still stores one global `paper_state`, one global `paper_strategy_state` owner/DCA record, one global pending-order gate and one global book-consumption table. Existing `paper_execution/test_ledger.py` exercises only the single-ledger behavior. This cannot support simultaneous independently attributed Core and AI positions.
- Proposed RED 1 contract: two strategy-scoped `PaperLedger` instances share one account database but expose isolated position and strategy state. Core and AI can hold opposite/same-side positions concurrently without ownership collision or cross-ledger mutation. This first test does not implement migration, shared risk admission, margin sizing, order-book reservations, or backtests.
- TDD state: **RED 1 TEST DESIGN STARTED**. No implementation change authorized in this increment. Existing test suite has not been run. The GitHub connector can update source files but does not provide a local Python execution environment; no Codemagic run has been triggered or verified. Test execution status: **NOT VERIFIED** until the configured Codemagic workflow runs against the exact test commit.
- No exchange connection, collector, backtest, live execution, or real order is authorized. No database outside isolated test fixtures is to be created or modified.
- Next: add the isolated Core/AI position contract test first; inspect its exact-source Codemagic result. Only after an observed failing test may the minimal ledger implementation begin.
- Workflow run/artifact: **NONE**. Source SHA for this handoff update will be recorded after commit creation.

### RED 1 execution attempt — blocked (2026-11-06)

- Current branch HEAD before this note: `f30667e6ea6f59eb8892a40ddb0785529f037161`.
- Test contract prepared: instantiate strategy-scoped Core and AI ledgers over one isolated SQLite fixture; submit distinct opposite-side entries using distinct book snapshots; assert each ledger and reopened instance sees only its own position.
- Attempts to add the test to `paper_execution/test_ledger.py` and as a new `paper_execution/test_dual_ledger_red.py` were blocked by the GitHub write safety gate. No test file was changed or committed.
- Therefore RED 1 is **DESIGNED / NOT ADDED / NOT EXECUTED**, not a verified RED failure. No implementation has started.
- No Codemagic workflow run or artifact exists. The available connected GitHub actions are read-only for workflow inspection; no Codemagic execution connector is available in this session.
- Next: resume the test-file write through an authorized repository editing path, then run only the focused RED 1 test on Codemagic against the exact commit. Do not implement until the failure is observed.


## 2026-11-06 — T1.2 Dual Ledger RED 1 — GitHub Actions execution

- **Status: RED OBSERVED / IMPLEMENTATION NOT STARTED.** The earlier source-write blocker is resolved for this increment; the RED test and dedicated GitHub Actions workflow were committed to the existing branch.
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Test source commit: `209be99dd104eb1b55e3484f30ef57e472723691`; test file: `paper_execution/test_dual_ledger_red.py`; blob SHA at final branch HEAD: `eb1d003601f90911fb5e70ea7e7c1a17ccd45b69`.
- Workflow commit / current branch HEAD: `554d122762a9d49a6144a1be54d178902d3db7d9`; workflow file: `.github/workflows/dual-ledger-red.yml`; blob SHA: `0ce7bf393510411bfb5be969e15f8ed33a3795d3`.
- GitHub Actions run #1: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42178592443 ; run ID `42178592443`; event `push`; exact checked-out source SHA `554d122762a9d49a6144a1be54d178902d3db7d9`; final conclusion **FAILURE**, as expected for RED.
- Preflight: **PASS** — PAPER-only, no PAPER_DB/MARKET_DATA_DB and no exchange credentials; no external services.
- Python compile: **PASS**.
- Focused RED test: **FAIL (expected)** — one test executed; Core LONG order filled, but the independent AI SHORT order returned `REJECTED` where the contract requires `FILLED`. Failure assertion: `paper_execution/test_dual_ledger_red.py:59`. This confirms the current single-owner/single-position ledger blocks the second strategy; it does not yet prove all persistence and snapshot-isolation assertions.
- Artifact: `dual-ledger-red-evidence-554d122762a9d49a6144a1be54d178902d3db7d9`; artifact ID `13484247308`; SHA-256 `fcf4c3337761abde7daeac6edb051178beebfd2ec36aee6da47e54651f7ce662`; expires `2026-11-13T07:05:37Z`.
- Workflow is scoped to this branch and `paper_execution/**`; manual `workflow_dispatch` is enabled. No production secrets or write permissions are granted to the workflow (`contents: read`).
- No ledger implementation, migration, risk-engine change, backtest, merge, exchange connection, or live execution was performed. `ai_execution_enabled=false` and PAPER-only boundary remain unchanged.
- **Next:** inspect the rejected order reason and formalize the strategy-scoped ledger contract (including per-ledger snapshot/read API and shared account-level atomic risk reservations) before writing GREEN implementation. Do not implement by merely removing the current owner guard; preserve shared risk, idempotency, pending-order and shared book-depth protections. Run the focused RED/GREEN and regression suites through GitHub Actions on exact source SHAs.


## 2026-11-06 — T1.2.1 Dual Ledger Contract frozen for design review

- Branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Source inspection reconfirmed current branch HEAD before documentation commit: `e8eb75905b42b7a72d3ac1a23379724d78e1b135`.
- Re-read `paper_execution/ledger.py`, `paper_execution/test_ledger.py`, `paper_execution/risk_control.py`, `paper_execution/equity.py`, the RED test and the dedicated GitHub Actions workflow.
- Exact RED diagnosis: `PaperLedger.submit()` reads one global `paper_state` and one global `paper_strategy_state`; after Core opens LONG, AI's independent SHORT intent is rejected by `POSITION_OWNED_BY_OTHER_STRATEGY`. The existing equity risk gate also computes projected exposure from one target position rather than aggregate gross exposure across both strategy ledgers. A storage-only split is therefore insufficient.
- Added design contract: `docs/architecture/DUAL_LEDGER_CONTRACT.md`; file blob SHA `99160908e4bc43f05374727637f482f8c3780646`; commit `6da95224349e044aa8eab382bc004adb577e2677`.
- Contract records: independent Core/AI ledger ownership; account-wide atomic Shared Risk Engine; current-equity 1% margin reservation for each ENTRY and exposure-increasing DCA; aggregate gross exposure (no netting); account-level equity/HWM/daily baseline; pending order and visible book-depth reservations; idempotency; reductions allowed under kill/risk latch; legacy unattributed migration and reconciliation; required read models and 15 test gates.
- Important correction to RED evidence: only the initial coexistence status assertion ran to failure. Snapshot isolation and reopen persistence assertions were not reached and remain NOT VERIFIED.
- Handoff update is documentation-only. No source logic, schema, migration, config or test changed in this increment. No tests/workflow were triggered; prior RED evidence remains run #1, source SHA `554d122762a9d49a6144a1be54d178902d3db7d9`, run ID `42178592443`, artifact ID `13484247308`.
- Current decision: T1.2.1 contract is **DOCUMENTED / REVIEW REQUIRED**, not implementation-approved. No GREEN work until contract review is accepted and detailed schema/migration plan is written. No merge, backtest, exchange connection or live execution.
- Next: review the contract's account equity / gross exposure definitions and migration behavior; then produce a table-by-table schema and transaction plan before adding more RED tests. Preserve PAPER-only and `ai_execution_enabled=false`.


## 2026-11-06 — User approved Dual Ledger Contract; schema/migration plan documented

- User explicitly approved `docs/architecture/DUAL_LEDGER_CONTRACT.md` in this conversation. Approval authorizes the schema/migration design step only; it is not approval for source implementation, DB migration, feature activation, backtest, merge, deployment or live execution.
- Re-verified source branch before work: `feature/t0-centralized-data-feeder-p1-20261101`; HEAD `1c29345493dc27237122ec091baa6a77e1de8c5e`.
- Re-read current `paper_execution/ledger.py`, `risk_control.py`, `equity.py`, approved architecture contract and API/interface design guidance.
- Added `docs/architecture/DUAL_LEDGER_SCHEMA_MIGRATION_PLAN.md`; commit `d1f5f1b5f76354f01da987c9555a31bcf729f5da`; plan defines additive SQLite schema, account/strategy tables, order compatibility columns, account risk state, margin/notional reservations, book-level reservations, funding/audit attribution, atomic transaction protocol, four-phase migration, read-model/API shape, test gates and hard stops.
- Verified legacy table structure from source: single `paper_state`, single-owner `paper_strategy_state`, account-global `paper_orders` and `paper_books`, one-position `paper_equity_history`, account config, daily baselines, risk latch and audit. Current inspected schema has no explicit funding event attribution and no per-level book reservations.
- Critical migration rules: preserve old tables untouched; initial capital copied once; proven owner only may receive position; ambiguous position goes to `LEGACY_UNATTRIBUTED`; realized PnL/fees without immutable strategy provenance remain account-level legacy adjustments; historical funding is unknown, not zero; old single-position equity history remains historical evidence and cannot be claimed as verified aggregate dual-ledger history.
- Open design questions explicitly recorded: historical PnL/fee attribution, funding provenance, equity cutover baseline, semantics of 1% current-equity margin reservation vs actual used margin, max exposure treatment of pending reservations, and legacy reconciliation. These are hard stops, not assumptions.
- Documentation-only increment: no source, tests, schema, database or configuration changed; no GitHub Actions run triggered. Prior RED run #1 remains the only workflow evidence (run ID `42178592443`, source SHA `554d122762a9d49a6144a1be54d178902d3db7d9`, artifact ID `13484247308`).
- Status: contract **APPROVED FOR DESIGN**; schema/migration plan **DOCUMENTED / REVIEW REQUIRED**; implementation **NOT AUTHORIZED**.
- Next: review the schema/migration plan and resolve its six open questions. Only after explicit separate approval may implementation begin, starting with additional RED tests and migration fixtures. Preserve PAPER-only and `ai_execution_enabled=false`.


## 2026-11-06 — T1.2.1 six open decisions proposed

- Re-verified active branch at start: `feature/t0-centralized-data-feeder-p1-20261101`; HEAD `a4eded4b08b94c9f90939f19a072c47d3631f786`. Re-read the approved Dual Ledger contract and current schema/migration plan.
- Added `docs/architecture/DUAL_LEDGER_OPEN_DECISIONS_PROPOSAL.md`; commit `10c28c7343a592d4cdf9713aa56e1a2c5f3cd133`. This is a proposal for the six outstanding design decisions, not implementation authorization.
- Proposed defaults: (1) known historical PnL/fees without strategy provenance remain account-level legacy adjustments and never enter Core/AI strategy statistics; unknown amounts block risk readiness; (2) missing historical funding is never assumed zero, known unowned funding remains account-level, future funding events require provenance; (3) cutover equity/HWM/daily baseline require one fresh mark and reconciled capital/PnL/fees/funding, otherwise fail closed; (4) 1% current equity is the fixed admission-time margin budget per ENTRY/DCA, with partial fills consuming proportionate reservation and unused amounts released; (5) Max Gross Exposure includes filled gross positions plus only remaining unfilled pending reservations, without netting or double-counting; (6) unknown-owner positions remain LEGACY_UNATTRIBUTED, block increases account-wide, but allow valid dedicated reduction/closure.
- Added six corresponding acceptance-test requirements to the proposal. No source code, test files, schema, DB or runtime configuration changed. No GitHub Actions run was triggered.
- Status: architecture contract **APPROVED FOR DESIGN**; schema/migration plan **DOCUMENTED / REVIEW REQUIRED**; six decision defaults **PROPOSED / AWAITING USER APPROVAL**; implementation **NOT AUTHORIZED**.
- Next: obtain explicit approval or corrections to the six proposed decisions. If approved, update the schema/migration plan and handoff as documentation only; then request separate authorization before implementation. Preserve PAPER-only and `ai_execution_enabled=false`.


## 2026-11-06 — User approved all six Dual Ledger open decisions

- User explicitly approved all six decisions in `docs/architecture/DUAL_LEDGER_OPEN_DECISIONS_PROPOSAL.md`.
- Approval is limited to normative design requirements, schema/migration plan and acceptance-test specifications. It does **not** authorize source implementation, DB migration/data rewrite, feature activation, backtests, merge, deployment, exchange connectivity or live execution.
- Updated proposal status to **APPROVED** and recorded the approval boundary.
- Updated `docs/architecture/DUAL_LEDGER_SCHEMA_MIGRATION_PLAN.md` to resolve the six open questions as normative requirements:
  1. Unowned historical realized PnL/fees remain account-level legacy adjustments, counted once and excluded from Core/AI strategy statistics; unreconciled amounts fail closed.
  2. Missing historical funding is never assumed zero; future funding requires amount/time/source/hash/strategy provenance; missing required inputs fail closed.
  3. Aggregate equity/HWM/UTC daily baseline require reconciled capital, PnL, fees, funding and one fresh mark; otherwise readiness remains false and only valid reductions/closures are allowed.
  4. Each ENTRY/DCA gets a fixed reservation of 1% of admission-time Account Equity; partial fills and unused reservations are accounted proportionately; existing reservations are not repriced after equity changes.
  5. Max Gross Exposure includes filled gross positions plus remaining unfilled pending reservations, without netting or double-counting.
  6. Unknown-owner legacy position remains `LEGACY_UNATTRIBUTED`, blocks all increases, permits dedicated reductions, and can be reassigned only with immutable evidence plus separate user approval.
- Added six corresponding acceptance-test groups to the approved plan.
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Branch HEAD before documentation updates: `5030251232e046024db2805c8ba2a10168f652cb`.
- Proposal update commit: `57580e3669f573453d2b1556567b971d68f46346`; new proposal blob: `6139fb888626843259b39e63a4585e740ba307be`.
- Schema/migration plan update commit: `db04a163dfac8a1412a69c188357bf16f33bea87`; new plan blob: `08e907818806c1628a421d1cd7fb0d6455433ad0`.
- No source, tests, runtime config, database or schema was changed. No tests or workflow were run because this increment changes documentation only.
- Existing RED 1 evidence remains unchanged: GitHub Actions run `42178592443`, source SHA `554d122762a9d49a6144a1be54d178902d3db7d9`, expected failure on AI SHORT coexistence; artifact ID `13484247308`.
- Status: six design decisions **APPROVED**; schema/migration plan **DESIGN APPROVED**; source implementation **NOT AUTHORIZED**; DB migration/feature activation/backtests/merge/deploy/live execution **NOT AUTHORIZED**.
- Next step: request separate explicit approval for T1.2.2 implementation. If approved, start with TDD RED tests and isolated migration fixtures, then run focused GitHub Actions tests against exact source SHAs. Preserve PAPER-only and `ai_execution_enabled=false`.

## 2026-11-06 — T0 regression baseline review at Dual Ledger HEAD

- Requested baseline target: branch `feature/t0-centralized-data-feeder-p1-20261101`, HEAD `faa069222bb05eb8a5fede66c15bbff58883290f`.
- Re-verified branch API HEAD exactly matches the requested SHA. Re-read this handoff before inspection.
- Current workflow inventory: `.github/workflows/t0-single-writer-gateway-red.yml` and `.github/workflows/dual-ledger-red.yml`. The T0 workflow has `workflow_dispatch`, source-only environment guards, disposable TimescaleDB services, and runs Gateway/Feeder/Health/Readiness/process-restart plus complete `market_data` tests. No workflow-dispatch action is exposed by the connected GitHub tools in this session; no exact-HEAD workflow run was triggered. No workflow configuration was changed.
- Latest T0 workflow evidence inspected: run **42166319563**, event `push`, checked-out/head SHA `7c41ac990a7a0842b773a2d07b8db2f1d769a855`, URL https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42166319563.
  - Static Gateway contract verification: SUCCESS; includes Gateway contracts, behavioral/feeder regressions, Health/Readiness, SIGKILL restart/fencing and complete `market_data` regression suite.
  - Paper consumer fixture regressions: SUCCESS.
  - Isolated TimescaleDB read-only integration: SUCCESS.
  - Fresh-cluster restricted provider bootstrap: FAILURE. The strict migration role guard rejected the disposable bootstrap membership graph; this remains a known fail-closed provider-bootstrap blocker and must not be weakened without a separate threat model and approval.
  - Overall workflow conclusion: FAILURE because provider bootstrap failed; this is not a fully green T0 workflow.
- Artifacts:
  - Gateway/static + complete `market_data` evidence: artifact **13479136579**, SHA-256 `b7676699ec4a497a2ae1b4d054a141b76e48606e2502a753fef01a0950585a69`.
  - Timescale read-only integration: artifact **13479106179**, SHA-256 `b0ddf990becfabd4a63d60dc7dd8c286fb7ad55ab2dafde5fdc54466ade82678`.
  - Paper consumer regressions: artifact **13478883570**, SHA-256 `1e0945f9344b20a5ba7299971245fab87e63ba08d0ebe046703533d72e50ecc7`.
  - Provider bootstrap failure evidence: artifact **13478428940**, SHA-256 `6e99f27f09949cf05c7cae43521d770a6ed9aeca8c562f6d490f6aa52e43c63c`.
  - Artifacts expire **2026-11-13T05:05:31Z**.
- Exact compare `7c41ac990a7a0842b773a2d07b8db2f1d769a855...faa069222bb05eb8a5fede66c15bbff58883290f`: 22 commits ahead, 0 behind. Changed files are limited to the Dual Ledger workflow/test, handoff, T0 planning/provider research documents, and Dual Ledger architecture documents. **No `market_data/**` source or test files, T0 workflow, or requirements files changed after the tested SHA.** Therefore the T0 source/test suite exercised at run 421663 is source-equivalent to the requested HEAD for those paths, although the workflow did not check out the exact HEAD.
- Baseline verdict: **CONDITIONAL PASS — T0 Gateway/Feeder/Health/Readiness/process restart, complete `market_data` suite, paper-consumer regressions and Timescale read-only integration are source-equivalent to current HEAD and passed on SHA `7c41ac9...`. Provider bootstrap remains BLOCKED. Exact-HEAD workflow execution is NOT RUN.**
- No source, tests, schema, database, runtime configuration or workflow was modified. No DB was created/opened, no Feeder started, no exchange contacted, no market-data sync, no Paper DB mutation, no live execution. `ai_execution_enabled=false` remains unchanged.
- Next: before T1.2.2 implementation, preserve the provider-bootstrap blocker and require an exact-HEAD T0 run when a workflow-dispatch path is available or when an authorized T0-path commit naturally triggers CI. Do not create a dummy source/workflow change solely to trigger CI. T1.2.2 source implementation still requires separate explicit approval.

## 2026-11-06 — T0 provider-bootstrap failure root-cause triage (read-only)

- Followed the stop-the-line debugging process; no feature/source changes made.
- Inspected failed job from T0 workflow run **42166319563**, job **127723515188** (Fresh-cluster restricted provider bootstrap).
- Exact failing test: market_data.test_postgres_provider_bootstrap.PostgresProviderBootstrapIntegrationTest.test_non_superuser_bootstrap_provisions_roles_then_restricted_migrations_run.
- Failure path: test calls migrate(migrator_dsn); market_data/migrations.py::_assert_writer_roles_safe detects that reserved role t0_migrator has a member other than the single allowed t0_migrator_login, then raises: t0_migrator may only be granted to the ephemeral t0_migrator_login role.
- Captured membership diagnostic shows bootstrap login t0_bootstrap_ed3b1beda2 remains a member of protected roles t0_db_owner, t0_candle_writer_owner, and t0_lease_manager_owner; those membership rows report grantor t0_test, with admin_option=true. The bootstrap test's REVOKE ... FROM CURRENT_USER did not remove those grant records. This is the immediate cause of the fail-closed rejection; not evidence that the safety guard should be weakened.
- Other job/container warnings (Timescale background worker/template initialization and extension version notice) are not the asserted test failure. Isolated Timescale read-only integration passed in the same workflow run.
- Diagnosis status: ROOT CAUSE LOCALIZED — membership grantor/cleanup mismatch in disposable fresh-cluster bootstrap test path. Exact PostgreSQL grantor semantics and a least-privilege cleanup/provisioning correction remain to be validated; no corrective change is authorized or made in this triage.
- Source refs inspected at HEAD faa069222bb05eb8a5fede66c15bbff58883290f: market_data/migrations.py and market_data/test_postgres_provider_bootstrap.py. No changes made to either file.
- Safety boundary: do not relax _assert_writer_roles_safe, do not grant additional membership to t0_migrator, do not use superuser for application migrations, and do not modify provider role policy merely to make CI pass.
- Next: design a minimal disposable-cluster reproduction of role creation/grantor identity and cleanup under the same PostgreSQL/Timescale image; verify grantor authority and role membership catalog before/after each revoke. Then add a regression assertion for the expected membership graph. Any source/test correction must be isolated to the provider-bootstrap test/provisioning path, reviewed for least privilege, and pass the T0 workflow before resuming feature work.
- No DB outside the disposable CI container was opened or modified. No source/test/workflow/schema/runtime change, migration, Feeder start, exchange connection, data sync, paper execution or live execution occurred. ai_execution_enabled=false remains unchanged.


## 2026-11-06 — T0 provider-bootstrap PostgreSQL 16 grantor reproduction plan (read-only)

- Re-verified branch `feature/t0-centralized-data-feeder-p1-20261101` HEAD: `e77f1c05f357c4303e35827abf1d6ab47a3f52bf`; handoff blob before this update: `b20a932a692397ad7a759a4a8e21262c43172038`.
- Re-read current `market_data/test_postgres_provider_bootstrap.py`, `market_data/migrations.py`, and `.github/workflows/t0-single-writer-gateway-red.yml`. The failing integration target is explicitly `timescale/timescaledb:2.17.2-pg16`; no code or workflow was changed.
- New evidence from PostgreSQL 16 official documentation: when a non-superuser with `CREATEROLE` creates a role, PostgreSQL automatically grants the newly created role back to the creator with ADMIN OPTION; the automatic membership is recorded as granted by the bootstrap superuser. `pg_auth_members.grantor` identifies the role that granted each membership. Sources: PostgreSQL 16 CREATE ROLE https://www.postgresql.org/docs/16/sql-createrole.html ; PostgreSQL 16 pg_auth_members https://www.postgresql.org/docs/16/catalog-pg-auth-members.html ; PostgreSQL 16 GRANT https://www.postgresql.org/docs/16/sql-grant.html.
- This explains the observed diagnostic pattern: the bootstrap login can appear as a member of each role it created, with `grantor=t0_test` and `admin_option=true`. The test currently attempts `REVOKE ... FROM CURRENT_USER` while connected as the bootstrap login, then checks the membership graph. That REVOKE does not remove the bootstrap-superuser-attributed membership; the reserved-role guard correctly fails closed when the bootstrap login remains a member of `t0_migrator`.
- Important distinction: this is now a **documented, strongly supported root-cause explanation**, but a fresh isolated SQL reproduction against the exact Timescale image has **NOT RUN**. Do not yet claim a tested correction.
- Minimal disposable reproduction to run next, using only the existing CI TimescaleDB service image and randomly named roles:
  1. Capture `session_user/current_user`, PostgreSQL server version, and `pg_auth_members` rows immediately after each `CREATE ROLE`.
  2. Capture the full membership tuple (`roleid`, `member`, `grantor`, `admin_option`, `inherit_option`, `set_option`) before and after the current `REVOKE ... FROM CURRENT_USER` attempt.
  3. In separate disposable trials, test explicit grantor-aware revocation by the authorized bootstrap/service administrator and role-drop cleanup; verify the exact membership graph after each action. Do not combine trials or infer success from command exit status alone.
  4. Confirm that the surviving graph has only `t0_migrator_login -> t0_migrator`, and no other member of `t0_migrator`; then verify the migration guard without applying schema migrations in the first reproduction pass.
  5. Destroy all randomly named roles/database resources in a `finally` cleanup and assert no test-created role/membership remains.
- Candidate correction, if reproduction confirms it: isolate cleanup/provisioning in the disposable bootstrap test so the automatically created bootstrap-to-role memberships are removed by an identity that is authorized for the actual recorded grantor. Do not weaken `_assert_writer_roles_safe`, widen runtime grants, or use superuser for application migrations.
- Status: **ROOT CAUSE EXPLANATION SUPPORTED BY PG16 DOCUMENTATION; DISPOSABLE REPRODUCTION NOT RUN; CORRECTION NOT AUTHORIZED/NOT MADE.** T0 provider-bootstrap workflow remains BLOCKED. T0 baseline remains CONDITIONAL PASS as previously recorded.
- Safety: no source/test/workflow/schema/runtime changes; no database opened or modified in this turn; no Feeder, exchange, sync, paper execution, or live execution. `ai_execution_enabled=false` unchanged.
- Next step: execute the isolated SQL reproduction in CI using the same TimescaleDB 2.17.2-pg16 image, then report the before/after catalog evidence and proposed least-privilege test-only fix for explicit approval.


## 2026-11-06 — T0 PostgreSQL 16 grantor reproduction workflow added

- User requested continuation of the previously proposed disposable PostgreSQL role-grantor reproduction. Re-verified the branch and handoff before work.
- Added isolated workflow `.github/workflows/t0-postgres16-grantor-repro.yml`, using the same disposable image as the failing acceptance test: `timescale/timescaledb:2.17.2-pg16`. It has no repository secrets, no external DB, no application migrations, no Feeder, no exchange credentials, and uses randomly named throwaway roles only.
- Workflow scope is diagnostic only: record PostgreSQL version and session identity; inspect complete `pg_auth_members` tuples; compare automatic creator membership against an explicit creator-issued membership; attempt creator `REVOKE`; verify grantor-specific rows; verify privileged cleanup removes the automatic row; drop all throwaway roles and assert cleanup.
- Workflow commits:
  - Initial workflow: `c6f805051e6c72ac2e354ec7d7f69e9015b04607`.
  - Corrected grantor-specific assertion: `6b7c5795aa97a15cde2a0cb1fcb11825568e28e2`.
  - Current workflow blob: `c7bc589ca8240edb25a9c33cce5b9a76e6193271`.
- The assertion was refined before run verification: PostgreSQL 16 can retain separate membership records for the bootstrap-superuser automatic grant and an explicit grant by the CREATEROLE user. Revoking the explicit grant must remove only the creator-granted row; the bootstrap-superuser-granted row should remain until an authorized superuser cleanup.
- PostgreSQL 16 official documentation supports the mechanism: a non-superuser with CREATEROLE automatically receives ADMIN OPTION on a role it creates, and the implicit grant is recorded as granted by the bootstrap superuser; the creator cannot revoke that implicit membership. Superusers can revoke membership in any role. Sources:
  - https://www.postgresql.org/docs/16/sql-createrole.html
  - https://www.postgresql.org/docs/16/sql-grant.html
  - https://www.postgresql.org/docs/16/catalog-pg-auth-members.html
- Branch HEAD verified after workflow update: `6b7c5795aa97a15cde2a0cb1fcb11825568e28e2`.
- GitHub Actions run ID/conclusion/artifact are **NOT VERIFIED**. The available GitHub connection exposes workflow-run detail only when a run ID is already known and does not expose a dispatch/list-runs action in this session. The workflow has a push trigger scoped to this file and a manual dispatch trigger; do not claim that it executed until a run record is retrieved.
- No application source, tests, database migrations, schema, runtime configuration, or existing T0 workflow changed. Only the new diagnostic workflow was added. No live or persistent database was accessed; no data feeder, exchange, paper order, or live order was run. `ai_execution_enabled=false` remains unchanged.
- Status at that point: **DIAGNOSTIC WORKFLOW COMMITTED; EXECUTION/RESULT NOT YET VERIFIED; PROVIDER-BOOTSTRAP FIX NOT AUTHORIZED/NOT MADE.** The subsequent result section records the successful reproduction.
- Next: obtain the run record for the new workflow, inspect its job log and artifact, and record exact run ID, source SHA, artifact ID and SHA-256. Only after evidence, propose a narrowly scoped test/provisioning correction; do not change the migration role guard or production role policy.


## 2026-11-06 — T0 PostgreSQL 16 grantor reproduction result

- Reproduction workflow ran successfully on exact source SHA `6b7c5795aa97a15cde2a0cb1fcb11825568e28e2`.
- GitHub Actions workflow run: **42182638820**, job **127775650645**, conclusion **SUCCESS**. Job URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42182638820/job/127775650645
- Artifact: `t0-pg16-grantor-reproduction-6b7c5795aa97a15cde2a0cb1fcb11825568e28e2`, artifact ID **13486036752**, size 481 bytes, SHA-256 `e4fd0377c5a624c16bc8d6247776ba81c404c62c83f236d795eb3263d43a2a56`, expires **2026-11-13T07:42:30Z**.
- Runtime evidence:
  - Exact image `timescale/timescaledb:2.17.2-pg16`; PostgreSQL server version **16.6**.
  - Disposable service admin `t0_test` is superuser; test bootstrap is a separate non-superuser CREATEROLE/CREATEDB login.
  - After bootstrap creates NOLOGIN roles, `pg_auth_members` records automatic creator membership with `grantor=t0_test`, `admin_option=true`, `inherit_option=false`, `set_option=false`.
  - `REVOKE created_role FROM CURRENT_USER` as the CREATEROLE creator leaves the automatic bootstrap-superuser-granted membership intact.
  - Superuser `t0_test` can revoke that membership; catalog inspection confirms the row disappears.
  - Adding a separate explicit creator-issued grant creates a second membership row with `grantor=bootstrap`, `admin_option=false`, `inherit_option=true`, `set_option=true`. Creator `REVOKE` removes only that explicit row; the automatic `t0_test` row remains.
  - Random test roles were dropped and cleanup assertion passed: `CLEANUP=PASS`.
  - Final markers: `T0_PG16_GRANTOR_REPRODUCTION=PASS`, `CLEANUP=PASS`.
- Initial workflow run on the earlier assertion version: run **42182579901**, job **127775371978**, failed because that first draft incorrectly expected the explicit creator REVOKE to remove the bootstrap-superuser membership too. The assertion was corrected before the successful run above. This initial failure is a diagnostic-test assertion error, not a T0 source regression.
- **Root cause confirmed**: PostgreSQL 16 CREATEROLE role creation automatically records an unrevokable-by-creator ADMIN membership from the bootstrap superuser. The existing bootstrap integration test creates reserved roles as a non-superuser and then attempts to remove the creator's automatic memberships with `REVOKE ... FROM CURRENT_USER`; that cleanup cannot remove the automatic rows. The migration guard then correctly rejects the extra membership.
- **Security implication / unresolved design constraint**: the current strict guard and a bootstrap model in which a persistent non-superuser CREATEROLE login creates all reserved roles are incompatible on PostgreSQL 16 unless an appropriately privileged provider-side operation removes the bootstrap membership or the provisioning model is redesigned. Do not weaken the guard based only on this reproduction. The automatic row has ADMIN=true even though INHERIT=false and SET=false, so it still conveys role-grant authority.
- Candidate paths requiring separate security review:
  1. Provision reserved roles through a provider-authorized privileged control-plane/bootstrap mechanism that does not leave an untrusted CREATEROLE login as a member.
  2. For providers that expose an authorized superuser-equivalent operation, explicitly remove the automatic memberships and prove the provider's privilege model; do not assume all managed providers permit this.
  3. If neither is available, mark that provider/bootstrap path unsupported and fail closed.
- No production/provider DB was accessed. The only database was the disposable CI TimescaleDB service, destroyed at job completion. No migration, application source/test, schema, runtime config, feeder, exchange, paper or live execution changed.
- Status: **POSTGRESQL 16.6 GRANTOR ROOT CAUSE REPRODUCED — PASS; T0 PROVIDER BOOTSTRAP REMAINS BLOCKED; CORRECTIVE CHANGE NOT AUTHORIZED/NOT MADE.** The broader T0 baseline remains CONDITIONAL PASS as previously recorded.
- Branch HEAD before this handoff update: `95abdf542d27967d0c7b0c9b16d534591722d5f9`.
- Next: prepare a provider-capability/security decision note comparing the three candidate paths, then request explicit approval before changing `market_data/test_postgres_provider_bootstrap.py`, migrations, or provider provisioning policy.


## 2026-11-06 — T0 PostgreSQL 16 provider capability decision note

- Added design-only decision note: `docs/architecture/T0_PG16_ROLE_PROVISIONING_PROVIDER_CAPABILITY_DECISION.md`.
- Decision note blob SHA: `f6f8fffcc05214e2fc285cf5920a413da526a9b9`; commit: `9de18543ee52ed38172bbaddf7980a68de75a772`.
- Compares three provider paths: (A) provider-authorized control-plane role provisioning; (B) provider-documented privileged cleanup of automatic PostgreSQL 16 memberships; (C) mark the provider/bootstrap path unsupported and fail closed.
- Recommendation: default to Option C until an actual provider/tier is selected and qualified; evaluate A first; evaluate B only with explicit provider documentation and disposable-instance evidence. The CI reproduction does not certify Timescale Cloud or another managed provider.
- Includes provider qualification gates and explicitly rejects weakening `_assert_writer_roles_safe`, relying on `CREATEROLE` creator REVOKE, using superuser for app migrations/runtime, or assuming `createrole_self_grant` removes the automatic membership.
- No source, test, migration, runtime, provider, database or workflow changes in this increment; architecture decision document only. No tests run because this is documentation-only.
- Status: **PROVIDER CAPABILITY DECISION NOTE RECORDED — DESIGN ONLY; NO PROVIDER QUALIFIED; NO IMPLEMENTATION AUTHORIZED.**
- Next: user chooses whether to keep Option C as the current provider policy or nominate a specific provider/tier for a documented capability review. Separate explicit approval remains required before source/test or provider provisioning changes.


## 2026-11-06 — User decision: retain T0 provider Option C (fail closed)

- User explicitly decided: **keep Option C as the default policy until a provider is qualified**.
- Normative policy: any provider/bootstrap path that cannot demonstrate supported, least-privilege provisioning of the reserved PostgreSQL roles and satisfy the T0 role-membership guards remains **UNSUPPORTED / BLOCKED**. Fail closed; do not weaken `_assert_writer_roles_safe`, accept unintended CREATEROLE memberships, or use a broad/superuser application migration identity to force compatibility.
- No provider is selected or qualified by this decision. Timescale Cloud/Tiger Cloud and DigitalOcean remain unqualified candidates; prior research or disposable PostgreSQL 16 CI evidence is not provider certification.
- Provider qualification requires provider/tier-specific documentation and disposable-instance evidence for role provisioning and membership graph, restricted migrations, TLS verify-full/hostname, writer fencing/runtime lifecycle, backup/PITR/restore, and measured recovery/failover gates. Until those checks pass, retain the existing PC + CI validation path and SQLite default.
- This decision authorizes documentation/policy recording only. It does not authorize provider evaluation against a live service, trial/provisioning/payment, database creation, migration, Feeder activation, exchange connection/data sync, VPS deployment, or production use.
- No source, test, workflow, schema, runtime configuration, or database changed; no tests/workflow run. `ai_execution_enabled=false`; paper-only boundary unchanged.
- Status: **OPTION C DEFAULT — APPROVED; NO PROVIDER QUALIFIED; T0 PROVIDER BOOTSTRAP BLOCKED UNTIL QUALIFICATION.**
- Next: preserve this policy. Reopen provider qualification only when a concrete provider and service tier are nominated; begin with a read-only capability review, then request separate approval before any disposable provider instance or provisioning.

## 2026-11-06 — T1.2.2 implementation approved; Dual Ledger RED and migration fixtures

- User explicitly approved **T1.2.2 source implementation** on 2026-11-06. Scope: PAPER-only Dual Ledger implementation under the already approved `DUAL_LEDGER_CONTRACT.md` and `DUAL_LEDGER_SCHEMA_MIGRATION_PLAN.md`. This does not authorize merge, deployment, backtests, exchange connectivity, production database migration, or live execution.
- Re-verified active branch before this increment: `feature/t0-centralized-data-feeder-p1-20261101`; branch HEAD at the end of the test increment: `bd2814595c149a3bba4a7a405264a1b8f00fda47`.
- Read the TDD and API/interface design skills before changing behavior/contracts; read CI/CD guidance before extending the focused GitHub Actions gate.
- Added isolated legacy-migration RED fixtures: `paper_execution/test_dual_ledger_migration_red.py`; commit `71ccdeb9f577ab8d6de523b37dfe61c92601b4ab`. The fixtures require: unknown/MANUAL legacy owner is migrated to `LEGACY_UNATTRIBUTED`; Core/AI remain independently zero; account risk readiness remains false when cutover provenance/funding is incomplete; legacy rows/orders/tables remain intact; migration is idempotent; corrupt legacy state stops before migration writes.
- Updated the coexistence contract test `paper_execution/test_dual_ledger_red.py` to pin strategy identity on each ledger instance and read per-instance snapshots; commit `6c324575c1f466b0b6c278805a8df7387d0a3eed`.
- Extended `.github/workflows/dual-ledger-red.yml` to compile and execute both focused RED modules; commit / current branch HEAD `bd2814595c149a3bba4a7a405264a1b8f00fda47`; workflow blob `c971fb094412d20416adc1efcd441d32739f308f`.
- Exact-source GitHub Actions evidence:
  - Run **42183689526**, source SHA `71ccdeb9f577ab8d6de523b37dfe61c92601b4ab`, expected failure from the existing AI-vs-Core owner collision; compile and paper-only preflight passed. Artifact ID **13486785952**, SHA-256 `05085bb5e44144db1e8bc9f8956aeb2a6cc561242addc8f740416f27b560fca4`.
  - Run **42183714711**, source SHA `6c324575c1f466b0b6c278805a8df7387d0a3eed`, expected failure because `PaperLedger.__init__` does not yet accept a strategy-scoped `strategy_id`; compile and paper-only preflight passed. Artifact ID **13486064239**, SHA-256 `3f446e5469c987a11fec6a44167a4ba36a920ea3b0cbe69980ec4c11636d4d65`.
  - Run **42183730008**, source SHA `bd2814595c149a3bba4a7a405264a1b8f00fda47`, expected RED: 4 focused tests executed; all 4 error at the absent strategy-scoped constructor API, before migration assertions. Compile and paper-only preflight passed. Artifact ID **13486208948**, SHA-256 `af166bba00cb30c58fc09c4f8492189bfe6282f7ea0ef239e02d9274c886d5bf`. Run URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42183730008.
- The RED fixtures are now committed and the failure is observed on exact source SHA. **No GREEN implementation has yet been committed.** The 4-test migration fixture set is not yet sufficient to certify all contract requirements; shared aggregate risk, margin reservations, per-level book-depth reservations, funding provenance, pending/partial order recovery, kill-switch reduction-only, and concurrent admission tests remain to be added.
- GitHub push also caused the repository's pre-existing Codemagic webhook checks to appear; those unrelated T0 checks were automatically cancelled during the push. No Codemagic action was deliberately invoked. GitHub Actions remains the intended T1 verification path.
- No T0 source, tests, workflow, schema or runtime was changed. No external or persistent database was opened, no migration applied to a real database, no Feeder started, no exchange contacted, no data sync/backtest/paper account execution outside isolated CI fixtures, and no live order. `ai_execution_enabled=false` remains unchanged.
- Status: **T1.2.2 APPROVED; RED COEXISTENCE + MIGRATION FIXTURES OBSERVED; GREEN IMPLEMENTATION NOT STARTED; T0 UNCHANGED.**
- Next: implement the additive, restart-safe schema migration and strategy-scoped read/write path in small GREEN increments. Preserve the legacy tables as immutable migration evidence; keep unknown ownership/funding fail-closed; add the shared account-level risk transaction and reservation behavior before claiming Dual Ledger readiness. Run focused GitHub Actions on exact SHAs, then the complete paper_execution regressions. Do not merge or backtest until all relevant gates pass and a separate approval is given.

## 2026-11-06 — T1.2.2 first GREEN increment: additive migration + scoped ledger coexistence

- Current source branch: `feature/t0-centralized-data-feeder-p1-20261101`; current HEAD at handoff update: `d469bf2e8495f3e343529731f6f983f26e23cf72`.
- Implemented versioned additive SQLite migration in `paper_execution/ledger.py`: preserves legacy tables and order rows; creates account, per-strategy ledgers, unattributed account adjustments, account risk state, risk reservation, book-level reservation, and funding-event tables; adds strategy metadata to legacy orders; stores migration checksum and source SHA; transaction remains owned by the existing ledger initialization transaction.
- Migration preserves the legacy position, DCA flag and margin attribution as `LEGACY_UNATTRIBUTED` when owner is MANUAL/unknown; realized PnL and fees are retained as account-level unattributed adjustments. Risk readiness remains false pending equity/funding/cutover reconciliation. Corrupt legacy position or inconsistent DCA/margin state fails closed.
- Added strategy-scoped snapshot reads and routed scoped ledger instances to `_submit_scoped`; scoped orders persist `account_id`, `strategy_id`, strategy event and reservation identity. Existing legacy submit path remains available to legacy/manual callers.
- Focused GitHub Actions run **42184732921** completed SUCCESS on exact source SHA `78e4b8fe345c034f087631d8d5cbe4d7f203835d`: compile passed; 4 tests passed (Core LONG + AI SHORT independent positions/reopen persistence, plus 3 migration cases). Artifact ID **13487165892**, SHA-256 `b268b8d0845c56609ef2b1cf6fc8e871710709bcc80c5fd919eab92be5102743`; URL https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42184732921.
- Follow-up test-only commit `d469bf2e8495f3e343529731f6f983f26e23cf72` adds the missing `sqlite3` import to the coexistence fixture after a transient NameError was observed on SHA `b7845e703c5c86f393389df67ded5aa19a892340`. The successful run above is on its exact SHA `78e4b8fe345c034f087631d8d5cbe4d7f203835d`, not current HEAD; current HEAD `d469bf2e8495f3e343529731f6f983f26e23cf72` has **no observed Actions run yet** and is therefore NOT VERIFIED until rerun.
- Earlier failure evidence was not hidden: run `42184469660` at SHA `221f2643cfd949e54708580bab754a5725a8d896` still showed AI rejected by the old single-owner path; run `42184646205` at SHA `b7845e703c5c86f393389df67ded5aa19a892340` exposed a missing `sqlite3` import in the test fixture. Both were corrected in subsequent commits; the green result is recorded separately above.
- This is only the first GREEN increment. Full contract remains incomplete: account-level atomic Shared Risk Engine and concurrent admission, equity aggregation from both ledgers, 1%-of-current-equity margin admission with stable partial-fill reservations, aggregate gross exposure including pending reservations, per-level book depth release/reuse, Kill Switch reduction-only, funding attribution/provenance, pending/partial restart recovery, and broader legacy reconciliation tests still require implementation and focused tests.
- T0 source, tests, workflows, provider policy and runtime were not modified. No external DB migration, backtest, exchange connection, live execution, or production activation occurred. `ai_execution_enabled=false` remains unchanged.
- Status: **T1.2.2 IMPLEMENTATION IN PROGRESS; FIRST GREEN SLICE OBSERVED ON SHA `78e4b8fe345c034f087631d8d5cbe4d7f203835d`; CURRENT HEAD `d469bf2e8495f3e343529731f6f983f26e23cf72` NOT VERIFIED; SHARED RISK CONTRACT NOT COMPLETE; T0 UNCHANGED.**
- Next: obtain an exact-HEAD GitHub Actions run for `d469bf2e8495f3e343529731f6f983f26e23cf72`; then add RED tests for aggregate equity/gross exposure and atomic concurrent reservations before implementing the next risk-engine slice. Do not merge, backtest, deploy, migrate a persistent account DB, or enable execution without separate approval.


## 2026-11-06 — T1.2.2 shared risk admission and strategy-owned cancellation increment

- Re-read the current handoff, approved Dual Ledger contract, TDD and API/interface design skills; re-verified the active branch and current source before edits.
- Branch: feature/t0-centralized-data-feeder-p1-20261101. Implementation commits in this increment:
  - Shared scoped Kill Switch fix: 7637a3e84809216c1452703b40440d5bcb0f3979.
  - Cross-ledger cancellation RED tests: 7bb9761f1777aa728581618b6abd2c1ba930600b; fixture adjustment to stay within the 1%-equity admission budget: 6b058480715d817979ced204b3ee465c2ae1d195.
  - Strategy-owned cancellation guard: 96e143c0d8123acc26ff1ab51f99597c8e238ca6.
- Shared Kill Switch: scoped admission now checks the account-wide kill/pause latch for exposure-increasing intents; valid reductions remain allowed. This corrected a real failing case where a DCA increase after enabling the kill latch was incorrectly returned as a simulation result rather than rejected with KILL_SWITCH.
- Order cancellation: added strategy ownership validation before changing an order. A STRATEGY_CORE ledger cannot cancel an AI_FREQAI order and vice versa. Existing manual/legacy cancellation path remains unchanged. Cancellation by the owning strategy releases its remaining margin/notional reservation; already-filled position and its consumed exposure remain recorded.
- Added two focused tests: cross-strategy cancellation is rejected without changing order/reservation; own-strategy cancellation of a partially filled order sets order CANCELED and releases its remaining reservation.
- Exact GitHub Actions evidence: run 42185053908, source SHA 7637a3e84809216c1452703b40440d5bcb0f3979, SUCCESS, 10 tests passed (the seven scoped coexistence/risk tests and three migration tests). URL https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42185053908. Artifact ID 13485979992, SHA-256 68df32758b475cbb3d3a7dea4fd02b2e9449e2273425c3345c2d748be4055585.
- The new cancellation RED run 42185209743 on SHA 6b058480715d817979ced204b3ee465c2ae1d195 failed as intended: cross-strategy cancellation was not rejected. The other test fixture initially exceeded the configured admission notional; it was corrected to request 0.12 base with 0.05 visible depth, which keeps the test inside the 1%-equity/13x notional cap.
- Exact GREEN GitHub Actions run 42185262864 completed SUCCESS on source SHA 96e143c0d8123acc26ff1ab51f99597c8e238ca6: compile PASS; 12/12 focused tests PASS, including both cancellation tests and all previous coexistence/risk/migration tests. URL https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42185262864. Artifact ID 13486184998, SHA-256 0414f51bbfbca33fa995c00152148fd28e1fd21165244e1d54fa99c67bc0e21f.
- Test scope is focused only. Full paper_execution regression suite and exact-HEAD verification after this handoff commit are not yet run. No claim of full Shared Risk Engine readiness.
- Remaining contract gaps: account equity snapshot/reporting reconciliation; pending/partial order restart recovery and expiry; cancellation/fill reservation invariants under all partial-fill cases; reverse intents must be explicitly split into reduction then separately admitted increase; funding event attribution/provenance; robust corrupt/stale ledger and adjustment validation; broader concurrency tests beyond the current two-entry gross-exposure case; full regression suite.
- T0 source, tests, workflow, provider policy and runtime were not changed. No persistent account database was migrated; tests use isolated temporary SQLite databases. No backtest, exchange connection, live execution, merge, deployment or production activation occurred. ai_execution_enabled=false remains unchanged.
- Status: T1.2.2 IN PROGRESS; SHARED KILL SWITCH AND STRATEGY-OWNED CANCEL GUARDS PASS 12/12 FOCUSED TESTS ON SHA 96e143c0d8123acc26ff1ab51f99597c8e238ca6; FULL REGRESSION AND ACCOUNT RISK READINESS NOT VERIFIED; T0 UNCHANGED.
- Next: add explicit RED tests for pending/partial reservation restart and account snapshot reconciliation; then implement minimal lifecycle recovery. Run focused and full paper execution regressions on exact source SHAs. Do not merge, backtest, deploy, migrate a persistent account DB, or enable execution without separate approval.


## 2026-11-06 — T1.2.2 pending reservation recovery and cross-ledger capacity test

- Added RED coverage for a partially filled Core order surviving ledger close/reopen and continuing to reserve shared account exposure against a subsequent AI entry.
- The new test confirms the reopened Core snapshot retains the PARTIALLY_FILLED order; the reservation remains PARTIAL with positive remaining notional and margin; the AI admission is rejected at MAX_EXPOSURE_LIMIT when adding its request would exceed the shared gross exposure cap.
- Exact GitHub Actions run **42185412783** completed SUCCESS on source SHA `9f0df4785c4d85c7d626adebbe5b0c376ff64c24`; compile PASS; **13/13 focused tests PASS** (10 Dual Ledger coexistence/risk/cancellation/recovery tests + 3 migration tests). URL https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42185412783. Artifact ID **13487900093**, SHA-256 `5642949dcbf47f7a2f96d11aad31487d14b75c9eaa27802c89a99664cf6ab8d9`.
- Source and test blobs at this increment: `paper_execution/ledger.py` blob `27128760248caae074aa3ded2d6b703cc6b2b136`; `paper_execution/test_dual_ledger_red.py` blob `ba8f55ab6886fe271d4c7cec35bc7c14e1125b01`.
- This test proves persisted SQLite reservation data survives a reopen and is included in the next strategy's risk admission. It does not prove process-crash recovery for every order lifecycle, reservation expiry, or reconciliation of malformed reservation rows.
- Current source HEAD before this handoff update: `9f0df4785c4d85c7d626adebbe5b0c376ff64c24`. Handoff update commit will advance HEAD; exact-HEAD workflow is still required after the docs commit.
- T0 unchanged; no persistent account DB migration, backtest, merge, deployment, exchange connection, or live execution. ai_execution_enabled=false remains.
- Status: **T1.2.2 IN PROGRESS; 13/13 FOCUSED TESTS PASS ON SOURCE SHA `9f0df4785c4d85c7d626adebbe5b0c376ff64c24`; FULL PAPER_EXECUTION REGRESSION AND ACCOUNT SNAPSHOT CONTRACT NOT VERIFIED.**
- Next: implement an explicit read-only account risk snapshot that reconciles account equity, gross exposure, active reserved exposure/margin, HWM, daily UTC loss and kill/readiness state; begin with RED tests. Then cover expiry/recovery, reversal split, funding provenance, and run the full paper_execution regression suite. No merge/backtest/deployment/persistent DB migration/live execution without separate approval.


## 2026-11-06 — T1.2.2 legacy unattributed exposure admission guard

- Added RED test proving a non-zero LEGACY_UNATTRIBUTED position blocks new Core/AI exposure even if paper_account_risk_state.risk_ready is incorrectly/stalely set to 1. This is an independent ownership hard stop, not merely a risk_ready flag.
- Initial RED run 42185535280 on source SHA 05efc0b940dfa9c343810ba1e19c07c6e6c39237 failed as expected: Core entry was FILLED despite an unattributed legacy position.
- Implemented fail-closed guard in paper_execution/ledger.py. Scoped ENTRY/DCA checks the LEGACY_UNATTRIBUTED position inside the same BEGIN IMMEDIATE transaction; non-zero exposure returns LEGACY_UNATTRIBUTED_EXPOSURE; malformed/non-finite legacy quantity returns LEGACY_UNATTRIBUTED_STATE_CORRUPT. The guard runs before account risk admission and does not infer ownership or permit a strategy to mutate the legacy ledger.
- Exact GitHub Actions run 42185623998 completed SUCCESS on source SHA a225b5e4f530286fc169213cc414b235a6678ad2: compile PASS; 14/14 focused tests PASS, including the new unattributed-legacy guard, partial reservation reopen/capacity, cancellation ownership, Kill Switch, coexistence, shared depth and migration cases. URL https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42185623998. Artifact ID 13487207433, SHA-256 5be7a9dd0940cc30cd9b3ca39ece56b138045a8da5c2fb604aed7d7e3f070681.
- Source SHA at this increment: a225b5e4f530286fc169213cc414b235a6678ad2. ledger.py blob b85cd7325d55ef9ee5166f153ace73398792b08d; test_dual_ledger_red.py blob 3b6b46995a5077c16efef401b59864640605bb57.
- This guard blocks new strategy exposure while unattributed legacy quantity exists. A dedicated LEGACY_UNATTRIBUTED reduction/flatten API and an explicit owner reconciliation workflow are still NOT IMPLEMENTED; do not try to close/reassign legacy positions via Core/AI.
- T0 remains untouched. No persistent account DB migration, backtest, merge, deployment, exchange connection or live execution. ai_execution_enabled=false remains.
- Status: T1.2.2 IN PROGRESS; 14/14 FOCUSED TESTS PASS ON SOURCE SHA a225b5e4f530286fc169213cc414b235a6678ad2; LEGACY INCREASE BLOCK VERIFIED; LEGACY REDUCTION/RECONCILIATION, ACCOUNT SNAPSHOT, FULL REGRESSION AND COMPLETE RISK READINESS NOT VERIFIED.
- Next: design and test a read-only account risk snapshot and explicit legacy-reconciliation reduction path, then expiry/restart and funding provenance. Run the full paper_execution regression suite on the exact implementation SHA. No merge/backtest/deployment/persistent DB migration/live execution without separate approval.

## 2026-11-06 — T1.2.2 read-only account risk snapshot first GREEN increment

- Re-verified branch and handoff before continuing. Active branch: `feature/t0-centralized-data-feeder-p1-20261101`; prior HEAD: `09c9e0d3c45834fd2f1702aca3ac8e2916c73e44`.
- Added a focused RED test in `paper_execution/test_dual_ledger_red.py` for an account-wide read-only snapshot aggregating Core, AI and LEGACY_UNATTRIBUTED positions; account-level legacy PnL/fee adjustments; funding attributed to each strategy ledger; filled exposure plus remaining pending reservation; remaining reserved margin; HWM drawdown; UTC daily loss; and Kill Switch state.
- RED test commit: `a54ac4259e0292478930d251b4903ac44acd552c`. Exact GitHub Actions run **42186261474** failed as expected only at the new API call: `AttributeError: module 'paper_execution.ledger' has no attribute 'read_account_risk_snapshot'`. Compile passed; 14 existing tests passed; 1 new test errored as expected. URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42186261474.
- Implemented `read_account_risk_snapshot(db_path, now_ms=...)` in `paper_execution/ledger.py`. It opens SQLite in URI read-only mode with `query_only=ON`; verifies the applied migration checksum, required account/ledger rows, finite numeric fields, fresh mark and candle timestamps, dataset identity, daily UTC baseline, and reconciliation of computed aggregate equity to the persisted account-equity value. It aggregates initial capital + Core/AI realized PnL + legacy realized adjustment - strategy/legacy fees - strategy funding + unrealized PnL. Gross exposure is absolute filled position notional across all three ledgers plus remaining ACTIVE/PARTIAL notional reservations; remaining reserved margin is reported separately. It also reports HWM drawdown, UTC daily PnL/loss, per-ledger position/accounting fields and Kill Switch state. It does not mutate ledger state or risk controls.
- GREEN implementation commit/source SHA: `a44d174c62f0550733de3dc718337d3b9ca202d1`.
- Exact GitHub Actions run **42186699153** completed SUCCESS on that exact SHA. Compile PASS; focused suite **15/15 PASS** (12 Dual Ledger tests including account snapshot + 3 migration tests). URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42186699153. Artifact ID **13487493622**, name `dual-ledger-red-evidence-a44d174c62f0550733de3dc718337d3b9ca202d1`.
- Snapshot test fixture verifies account equity 106.75 USDT, drawdown 3.25 USDT, daily loss 1.25 USDT, and that gross exposure includes remaining pending notional while reserved margin is reported separately. The test confirms the returned Kill Switch state is active.
- Scope limitations: the current focused test does not yet cover every malformed/stale/corrupt input, account equity cutover from historical funding provenance, daily rollover/recovery, or full `paper_execution` regression. A `riskReady=false` value is surfaced separately from snapshot availability; consumers must not treat a readable snapshot as permission to admit exposure. Funding provenance and ledger event reconciliation remain NOT VERIFIED.
- T0 source/tests/workflows/provider policy/runtime were not modified. No persistent account DB migration, backtest, merge, deployment, exchange connection, or live execution occurred. `ai_execution_enabled=false` remains unchanged.
- Status: **ACCOUNT RISK SNAPSHOT FIRST GREEN SLICE PASS 15/15 ON SHA `a44d174c62f0550733de3dc718337d3b9ca202d1`; BROADER CORRUPTION/STALE-INPUT COVERAGE AND FULL REGRESSION NOT VERIFIED; T1.2.2 IN PROGRESS; T0 UNCHANGED.**
- Next: add RED tests for risk_ready=false and stale/corrupt mark/equity reconciliation, then validate fail-closed snapshot behavior. Follow with dedicated LEGACY_UNATTRIBUTED reduce/flatten path, funding provenance and reservation expiry/restart lifecycle. Run full `paper_execution` regression before declaring the increment complete. Do not merge, backtest, deploy, migrate persistent account DB, or enable execution without separate approval.

## 2026-11-06 — T1 account risk snapshot fail-closed input coverage

- Continued from verified HEAD `647eb92b57b6f7a84f17b617672f5acb64a9dd56`; re-read the T1 handoff, current snapshot implementation and focused test setup before editing. TDD guidance was reviewed.
- Added four focused contract tests in `paper_execution/test_dual_ledger_red.py`:
  1. `risk_ready=0` is surfaced as `riskReady=false` with the persisted unavailable reason; a readable snapshot is not promoted to risk readiness.
  2. stale mark/candle timestamps fail closed with `ACCOUNT_RISK_MARK_STALE_OR_INVALID`.
  3. non-finite mark value fails closed with `ACCOUNT_RISK_MARK_PRICE_INVALID`.
  4. persisted Account Equity inconsistent with the independently recomputed aggregate fails closed with `ACCOUNT_EQUITY_RECONCILIATION_MISMATCH`.
- Test commit/source SHA: `25e05b64855ca905efa5f595a12823e6fd1c6ba3`.
- Exact GitHub Actions run **42187278175** completed SUCCESS on that exact SHA. Compile PASS; focused contract suite **19/19 PASS**. Test log: `Ran 19 tests in 1.318s; OK`. URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42187278175.
- Artifact ID **13488171640**, name `dual-ledger-red-evidence-25e05b64855ca905efa5f595a12823e6fd1c6ba3`, not expired at verification.
- No production behavior/source implementation changed in this increment; only focused tests were added. Existing snapshot implementation passed these four additional contract checks.
- Limitations: this is focused contract coverage, not full `paper_execution` regression. The snapshot still reports `available=true` with `riskReady=false` when the database is readable but cutover readiness is false; callers must gate all exposure admission on readiness and must not interpret snapshot availability as authorization. Tests do not yet cover every malformed ledger/reservation field, funding event provenance reconciliation, or daily UTC rollover/restart.
- T0 source, tests, workflows and Option C provider policy remain unchanged. No persistent account DB migration, backtest, merge, deployment, exchange connection or live execution. `ai_execution_enabled=false`.
- Status: **SNAPSHOT FAIL-CLOSED MARK/EQUITY INPUT TESTS PASS 19/19 ON SHA `25e05b64855ca905efa5f595a12823e6fd1c6ba3`; FULL REGRESSION AND FUNDING PROVENANCE NOT VERIFIED; T1.2.2 IN PROGRESS.**
- Next: design a dedicated `LEGACY_UNATTRIBUTED` reduce/flatten path that cannot reassign ownership or route legacy fills into Core/AI, write RED tests for close-only authorization and immutable legacy accounting, then implement a minimal PAPER-only path. Afterwards test reservation expiry/restart and funding provenance, and run full `paper_execution` regression. No merge, backtest, deployment, persistent DB migration or execution activation without separate approval.

## 2026-11-06 — T1 dedicated LEGACY_UNATTRIBUTED reduction path RED and schema blocker

- Continued from handoff commit `5be89c687540bf6b368494e6612c4e5a5c20809f`; re-read current ledger implementation and approved Dual Ledger contract before designing the legacy close-only path.
- Added two RED tests in `paper_execution/test_dual_ledger_red.py` for a dedicated `reduce_legacy_unattributed(...)` API:
  - partial close updates only the `LEGACY_UNATTRIBUTED` position/PnL/fees/margin; Core and AI positions remain unchanged; reconciliation ID and immutable evidence hash must be present in audit; no new exposure reservation is created.
  - attempted increase or reversal is rejected as `LEGACY_REDUCTION_ONLY` and leaves legacy accounting unchanged.
- RED test commit/source SHA: `7d69f17ebcdc4170b406c7c5a3f515b8ffb27d20`.
- Exact GitHub Actions run **42187428664** completed FAILURE as expected. Compile PASS; 19 existing focused tests pass; 2 new tests error because `paper_execution.ledger.reduce_legacy_unattributed` does not yet exist. URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42187428664. Artifact ID **13487857924**, name `dual-ledger-red-evidence-7d69f17ebcdc4170b406c7c5a3f515b8ffb27d20`.
- Important implementation blocker discovered during schema inspection: `paper_risk_reservations.strategy_id` currently permits only `STRATEGY_CORE` and `AI_FREQAI`, and `paper_book_level_reservations.reservation_id` has a foreign key to that table. Therefore a legacy close must not fabricate a Core/AI reservation to reuse shared order-book depth; doing so would misattribute ownership and contaminate the independent ledgers. A safe path needs an additive, versioned legacy book-consumption record and must make Core/AI book-depth admission subtract those legacy consumptions atomically. This likely requires a new migration version and corresponding migration/restart tests before implementing the close API.
- No implementation was attempted after identifying this schema constraint. No schema/migration version changed; no persistent DB was migrated. T0 unchanged; no backtest, merge, deployment, exchange connection or live execution. `ai_execution_enabled=false`.
- Status: **LEGACY RED TESTS CONFIRMED (2 EXPECTED ERRORS) ON SHA `7d69f17ebcdc4170b406c7c5a3f515b8ffb27d20`; IMPLEMENTATION BLOCKED PENDING ADDITIVE V2 SCHEMA DESIGN; T1.2.2 IN PROGRESS.**
- Next: specify additive migration v2 for legacy book-level consumption, atomic interaction with Core/AI depth reservations, immutable reconciliation evidence, and restart/idempotency. Add migration RED tests first, then implement v2 and the dedicated reduce/flatten path. Preserve owner separation, no legacy increase/reversal, Kill Switch reduce-only behavior, and no changes to T0. Do not run migration against any persistent account DB or merge/deploy without separate approval.


## 2026-11-06 — T1.2.2 Legacy close-only path and immutable book-depth v2 GREEN

- Continued on the existing branch: feature/t0-centralized-data-feeder-p1-20261101. T0 was not modified.
- Implemented additive migration v2, separate from v1 and without widening the Core/AI reservation owner constraint. New table paper_legacy_book_consumptions references paper_orders, has unique intent/book/side/price identity, an indexed book/side/price lookup, strict lowercase SHA-256 evidence format, and database triggers preventing UPDATE/DELETE.
- Added reduce_legacy_unattributed(...): PAPER-only, same-sign strict reduction/flatten only; increases and reversals return LEGACY_REDUCTION_ONLY. It records actual consumed book levels, reconciliation ID and evidence hash; uses BEGIN IMMEDIATE and idempotent intent replay; does not create Core/AI risk reservations or mutate Core/AI ledgers.
- Core/AI shared book-depth admission now subtracts both Core/AI reservations and immutable Legacy fill consumptions for the same book snapshot, side and price. Legacy reductions also subtract prior Core/AI and Legacy depth before filling. All three flows serialize through SQLite immediate write transactions.
- Kill Switch coverage confirms valid Legacy reductions remain allowed while the Kill Switch is active. New exposure remains blocked by the existing shared admission/legacy-exposure guard.
- Manual cancellation compatibility was restored: pre-v1 MANUAL databases without strategy_id remain cancellable; a MANUAL instance cannot cancel an explicitly Core/AI-owned order after Dual Ledger migration.
- Evidence-hash boundary: API validates lowercase sha256: plus 64 hex characters and persists it immutably. It does not retrieve or independently hash the external evidence bytes; external evidence provenance remains the reconciliation process's responsibility.
- RED coverage: v2 table/schema/idempotency, Legacy close-only/reversal rejection, shared book depth, intent replay, manual cancellation isolation, immutable evidence and Kill Switch reduction.
- Exact final implementation source SHA: 153437aee9fb0c88d48e44a71479778eb9772176.
- Exact GitHub Actions run 42188808296 completed SUCCESS on that exact checked-out SHA:
  - Compile PASS.
  - Focused Dual Ledger + migration tests: 25/25 PASS.
  - Full paper_execution regression: 60/60 PASS.
  - URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42188808296.
  - Artifact ID 13489205046, name dual-ledger-red-evidence-153437aee9fb0c88d48e44a71479778eb9772176, SHA-256 82a301f5a948faf83c0dc0bd7f9712f3e1712c3ea025cad0ea43490248a09831; expires 2026-11-13.
- Supporting documentation commits:
  - paper_execution/README.md: 620a66d2096c0c44c0a93872ee57797ae1c8648c.
  - docs/architecture/DUAL_LEDGER_SCHEMA_MIGRATION_PLAN.md v2 addendum: cdad6807de0e0c358ad9f8c6017fc610ba1a3214.
- No persistent account DB was opened or migrated. No backtest, merge, deployment, exchange connection, live order or feature activation occurred. ai_execution_enabled=false. T0 source/tests/workflows and provider policy unchanged.
- Status: LEGACY REDUCTION/V2 IMMUTABLE DEPTH PASS; FULL paper_execution REGRESSION PASS 60/60 ON SHA 153437aee9fb0c88d48e44a71479778eb9772176; T1.2.2 REMAINS IN PROGRESS because account cutover readiness, funding provenance and reservation expiry/restart lifecycle are not fully verified.
- Next: inspect and specify reservation expiry/restart behavior (including partial fills and remaining reservations) and funding provenance. Keep all tests on isolated temporary SQLite. No persistent DB migration, backtest, merge, deployment or execution activation without separate approval.


## 2026-11-06 — T1.2.2 reservation expiry v3 and restart recovery GREEN

- Continued on the existing branch feature/t0-centralized-data-feeder-p1-20261101. T0 remains untouched.
- Added additive migration v3, reservation_expiry_v3: nullable expires_at_ms on paper_risk_reservations plus (status,expires_at_ms) index. Requires valid v1 and v2 migrations/checksums; v1/v2 checksums remain unchanged.
- New Core/AI order documents persist validUntilMs; their risk reservations persist the same admission-time deadline. Existing pending reservations are backfilled only when a valid deadline already exists in the order document. Unknown expiry remains NULL and is not guessed.
- Added transactional expiry sweep before scoped submit/cancel. ACTIVE/PARTIAL reservations expire only when expires_at_ms < now_ms. Linked order changes to EXPIRED; reservation changes to EXPIRED; remaining margin/notional becomes zero. Already-filled position, PnL, fees and consumed book levels remain intact.
- Sweep validates reservation/order linkage and persisted order state; malformed expiry or mismatched pending order fails closed. Unknown-expiry reservations remain active and continue to block same-ledger replacement.
- Expiry is persistent across restart; retry of the same intent replays the EXPIRED order. Read-only snapshots do not mutate or sweep.
- RED tests covered migration v3 idempotency, partial fill expiry after reopening the writer, release of only unfilled capacity, preserved filled position, same-intent replay and unknown-expiry fail-closed behavior.
- Exact implementation/test source SHA: b1a9478178479a87043002a6915a56c068fcb78a.
- Exact GitHub Actions run 42189203483 completed SUCCESS on that checked-out SHA:
  - Compile PASS.
  - Focused Dual Ledger + migration tests: 28/28 PASS.
  - Full paper_execution regression: 63/63 PASS.
  - URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42189203483.
  - Artifact ID 13489605142, name dual-ledger-red-evidence-b1a9478178479a87043002a6915a56c068fcb78a, SHA-256 90554188c1dcc02b9fc932a45ee4375208679b0c0a8915f3dfc8d3ade141e879; expires 2026-11-13.
- Supporting docs:
  - paper_execution/README.md: e48b8648db77b13ddd76c680a2e864e9dc27abeb.
  - docs/architecture/DUAL_LEDGER_SCHEMA_MIGRATION_PLAN.md: 5147071f43c8fdf504d003309c895ebda96e1f26.
- No persistent account DB migration, backtest, merge, deployment, exchange connection, live order or feature activation. ai_execution_enabled=false. T0 source/tests/workflows/provider policy unchanged.
- Status: LEGACY REDUCTION/V2 IMMUTABLE DEPTH PASS; RESERVATION EXPIRY V3/RESTART PASS; FULL paper_execution REGRESSION PASS 63/63 ON SHA b1a9478178479a87043002a6915a56c068fcb78a; T1.2.2 REMAINS IN PROGRESS because account cutover readiness and funding provenance are not fully verified.
- Next: design/test funding provenance and account-equity cutover reconciliation, including historical unknown funding fail-closed behavior and future event source/snapshot identity/hash/strategy attribution. Do not run a persistent DB migration or enable execution. No backtest, merge or deployment without separate approval.


## 2026-11-06 — T1 funding provenance RED

- Re-verified current branch baseline against the prior handoff commit `85424810a568772a9dc947e3fc83b8fa0814d6db`; the branch was identical before this increment. Work remains on `feature/t0-centralized-data-feeder-p1-20261101`.
- Added three focused PAPER-only tests to `paper_execution/test_dual_ledger_red.py` for immutable/idempotent funding events, known unowned funding attribution to `LEGACY_UNATTRIBUTED`, and explicit unknown/disabled funding coverage evidence.
- Test commit/source SHA: `2af532fee6deb8daf7a337e3a42c007cb9fbf509`.
- Exact push workflow [#42192251105](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42192251105) checked out the exact source SHA. Compile PASS; 28 existing focused tests PASS; the 3 new tests ERROR as expected at missing APIs `record_funding_event` and `record_funding_coverage`. Total focused invocation: 31 tests, 3 expected RED errors. Full `paper_execution` regression was skipped after the RED step and is NOT a PASS.
- Job ID: `127806851954`. Artifact: `dual-ledger-red-evidence-2af532fee6deb8daf7a337e3a42c007cb9fbf509`, ID `13490227810`, GitHub upload digest `sha256:0a14b243a243fc49e5503503389f4d7804f244a1b9a937303cf81cdc6a33d245` (metadata/log digest; payload bytes not independently re-hashed), expires 2026-11-13.
- Evidence report: `docs/evidence/T1_FUNDING_PROVENANCE_RED_2026-11-06.md`, commit `8bbf6f674f9a0ce5ade7957e11c7ee65adfadb5d`.
- GREEN contract direction: additive migration v4 preserving v1-v3 checksums; append-only immutable event and coverage tables; signed amount semantics (positive cost, negative credit); stable idempotency; known unowned historical funding recorded under `LEGACY_UNATTRIBUTED`; unknown funding is not zero and blocks risk readiness; funding-disabled paper tests persist explicit config/version evidence.
- No T0 source/test/workflow/provider policy changed. No persistent account DB migration, backtest, merge, deployment, exchange connection, live order, or execution activation. `ai_execution_enabled=false`.
- Status: **FUNDING PROVENANCE RED CONFIRMED; GREEN NOT IMPLEMENTED; ACCOUNT EQUITY CUTOVER NOT VERIFIED; T1.2.2 IN PROGRESS.**
- Next: implement v4 and funding event/coverage APIs, then add RED/ GREEN tests for account-equity cutover (verified funding coverage, fresh mark/candle, dataset identity, exact capital/equity reconciliation, HWM and UTC daily baseline). Keep tests isolated; no persistent DB migration or backtest without separate approval.


## 2026-11-06 — T1.2.2 Funding Provenance v4 + Account Equity Cutover v5 GREEN

### Scope completed

- Added PAPER-only funding event and funding-coverage APIs in `paper_execution/funding.py`.
- Migration v4 adds immutable source/recorded timestamps to funding events and a new immutable coverage ledger. Existing funding rows without source provenance are marked `LEGACY_UNVERIFIED` and force readiness false.
- Funding event identity is idempotent; same event ID with changed economic/provenance fields fails. Duplicate payload digest fails. Positive funding is a cost; negative funding is a credit.
- Known funding with unknown strategy owner is attributed to `LEGACY_UNATTRIBUTED`, never Core or AI. UNKNOWN coverage is not zero and blocks new exposure. DISABLED coverage requires persisted `PAPER_TEST_CONFIGURATION`, source snapshot, payload digest and config version.
- Migration v5 creates an immutable one-time account cutover record. The API requires contiguous funding coverage, fresh mark and closed candle, dataset identity, source/snapshot/hash/config evidence, and explicit expected statement totals for capital, realized PnL, fees, funding and account equity.
- Cutover reconciles Core + AI + Legacy ledger totals and known legacy account adjustments; funding event totals must match each ledger. Calculated mark-to-market equity must exactly equal supplied statement equity. Successful cutover initializes HWM and UTC daily baseline from that same verified snapshot and sets risk readiness.
- Account snapshot and new exposure admission now require v4/v5 and a persisted cutover. UNKNOWN funding coverage overlapping the cutover interval blocks readiness and exposure increases even if the readiness flag is manually inconsistent. Valid reductions remain under the existing reduce-only policy.
- v4/v5 migrations are additive and were exercised only by isolated temporary SQLite CI fixtures. No persistent account DB was opened or migrated.

### Exact verification

- Exact implementation/test source SHA: `8dadd35b7e9e0174efab70c425eab53bca99fa34`.
- GitHub Actions run [#42194525276](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42194525276), push event, exact checked-out SHA confirmed in logs.
- Job ID: `127814336951`, conclusion SUCCESS.
- Compile: PASS.
- Focused Dual Ledger + migration tests: 34/34 PASS.
- Full `paper_execution` regression: 69/69 PASS.
- Artifact: [13491067898](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42194525276/artifacts/13491067898), name `dual-ledger-red-evidence-8dadd35b7e9e0174efab70c425eab53bca99fa34`, GitHub SHA-256 `3f48255660a6a6094a07d2f749d571e069ba01096f72bb5085d704c33f5d58b3`, expires 2026-11-13. This is the GitHub upload digest; artifact payload bytes were not separately downloaded and re-hashed in this increment.

### Documentation commits

- `paper_execution/README.md`: `58208cdeb1683d9bc1b41f881134ee8e0b4bfefe`.
- `docs/architecture/DUAL_LEDGER_SCHEMA_MIGRATION_PLAN.md`: `ee7370e22def77870e05d773d5fdff391cb900b5`.
- `docs/architecture/DUAL_LEDGER_CONTRACT.md`: `efa7c9b20d6a4508c3624705f94fb40e0112596a`.
- These commits are documentation-only after the tested source SHA; no source implementation changed after the 69/69 regression.

### Status and limits

- **PASS:** funding event provenance APIs; immutable funding event/coverage tables; v4 migration; known unowned funding isolation; explicit disabled-funding evidence; v5 cutover record; statement totals reconciliation; HWM/UTC daily baseline initialization; fail-closed UNKNOWN coverage; snapshot/admission gating; 69/69 full `paper_execution` regression on the exact implementation SHA.
- **NOT VERIFIED:** actual historical funding completeness and actual external statement-byte authenticity for a real account. The local ledger stores source snapshot IDs and SHA-256 fingerprints but does not retrieve or independently hash external statement bytes.
- **NOT RUN / NOT APPROVED:** persistent account DB migration, real-account cutover, backtests, merge, deployment, exchange connectivity, live execution.
- T0 source/tests/workflows/provider policy unchanged; Option C remains default. Dual Strategy remains PAPER-only; `ai_execution_enabled=false`. Core/AI separation, 1% account-equity margin per exposure-increasing ENTRY/DCA and no fixed max-position count remain unchanged.

### Next permitted work

1. Add focused RED/GREEN cases for statement-total mismatch, funding-coverage gaps/overlaps, stale/future mark/candle, corrupt funding event evidence and restart/idempotent cutover replay.
2. Build offline reconciliation fixtures from actual account-statement exports only after the user supplies/approves those files; do not open or migrate the persistent account DB.
3. Keep historical funding/fee provenance and actual-account cutover NOT VERIFIED until source evidence is reconciled. Do not run a backtest until those prerequisites are verified or separately scoped.
4. No T0 changes, persistent DB migration, merge, deployment, exchange connection or live execution without separate approval.

## 2026-11-06 — T1 funding-coverage overlap guard (verification pending)

- Continued on the existing branch `feature/t0-centralized-data-feeder-p1-20261101`; no new branch or PR created.
- Added regression test `test_account_equity_cutover_rejects_overlapping_funding_coverage` in `paper_execution/test_dual_ledger_red.py`.
- Test commit: `620a7171464acdb02160801f6b7d1ef8521e92d1`; test blob: `8b1578995cbd53c8d6892412902b813c6a705870`.
- The test creates two independently sourced VERIFIED funding-coverage intervals that overlap, then requires account cutover to reject them with `FUNDING_COVERAGE_INTERVAL_OVERLAP`.
- Added a guard in `paper_execution/funding.py`: cutover now checks each ordered interval against the previous interval end and rejects overlap. Adjacent intervals remain valid; gaps and UNKNOWN coverage continue to fail closed.
- Implementation commit: `cd21ac526b051f2878f7538b392cd1bfb40e27ab`; funding module blob: `1798a645fb060c5daf24526bec8598762e5ee50c`.
- Exact implementation commit inspection confirms only `paper_execution/funding.py` changed in the implementation commit; the preceding test commit changed only `paper_execution/test_dual_ledger_red.py`. No T0 files changed.
- Verification boundary: the GitHub connector did not expose push-triggered workflow runs for this commit; the PR-only workflow-run lookup returned no runs. The new test has **NOT BEEN EXECUTED / RED NOT VERIFIED**, and the implementation is **NOT VERIFIED**. Do not count this as a passing test or CI run. A run must be checked against exact source SHA `cd21ac526b051f2878f7538b392cd1bfb40e27ab` before promoting status.
- No artifact/run ID is recorded because none was retrievable in this increment.
- No persistent account DB was opened or migrated. No backtest, merge, deployment, exchange connection, live execution, T0 modification, or Codemagic fallback occurred. `ai_execution_enabled=false`.
- Status: **OVERLAP GUARD IMPLEMENTED; TEST/CI NOT VERIFIED; T1.2.2 IN PROGRESS.**
- Next: obtain exact-SHA GitHub Actions evidence for the RED/GREEN regression; then add and verify the remaining cutover failure cases (statement-total mismatch, coverage gaps, stale/future mark and candle, corrupt funding provenance, restart/idempotent replay). Do not run backtests until historical funding/fee provenance and real-account cutover are independently reconciled.

## 2026-11-06 — T1 cutover statement-total mismatch regression (verification pending)

- Re-verified the existing branch before work: comparison of `8b17eca13698ae287fe6ed682d30102eb821138b` against `feature/t0-centralized-data-feeder-p1-20261101` was identical (ahead 0 / behind 0).
- Read the current handoff and relevant Dual Ledger test/funding implementation before editing.
- Added `test_account_equity_cutover_rejects_statement_total_mismatch` to `paper_execution/test_dual_ledger_red.py`.
- Test commit: `d59f725de56a7e6b71b142d8831c52fb1cb0e140`; test blob: `d504020c51f0791e40ef473bc19aea2a843365b4`.
- The regression fixture uses a temporary SQLite database, verified funding coverage, and a Core realized-PnL ledger total that disagrees with the supplied account statement. It requires `ACCOUNT_EQUITY_STATEMENT_TOTALS_MISMATCH`, no cutover row, and no mutation of the pre-existing readiness flag.
- Existing implementation in `paper_execution/funding.py` already compares reconciled realized PnL, fees and funding totals before computing/recording cutover; this increment adds a direct regression test without changing production logic.
- Exact commit inspection: only `paper_execution/test_dual_ledger_red.py` changed. T0 source/tests/workflows were not touched.
- Verification: test source is committed but **NOT EXECUTED** in this increment. No exact-SHA workflow run or artifact has been obtained; do not mark this test PASS. Existing earlier v4/v5 evidence remains 69/69 only for source `8dadd35b7e9e0174efab70c425eab53bca99fa34`, not for current branch source.
- No persistent account DB opened/migrated; no backtest, merge, deployment, exchange connectivity, live execution, or Codemagic fallback. `ai_execution_enabled=false`.
- Status: **STATEMENT-MISMATCH REGRESSION ADDED; TEST/CI NOT VERIFIED.**
- Next: obtain exact-SHA GitHub Actions evidence for current branch source. Then add isolated cases for coverage gaps, future/stale mark and candle timestamps, corrupt funding provenance, and restart/idempotent cutover replay. Do not run backtests until historical funding/fee provenance and real-account cutover are independently reconciled.


## 2026-11-06 — controlled synchronization of main into T1 branch

- Owner approval received to merge `main` into `feature/t0-centralized-data-feeder-p1-20261101`, preserving Dual Ledger work; no rebase or force-push.
- Merge parents: T1 pre-merge `9032dd73672918eca0d0a89cd4f41deca3941776`; main pre-merge `1e16b437456d56eac2f7d9564ca9ab8e7d032f62`.
- The main-branch handoff is preserved verbatim as `docs/evidence/MAIN_PROJECT_SESSION_HANDOFF_2026-11-06.md` (source blob `3e021fb5f1c37392a497b1fc684e2fc388b363c8`). This T1 handoff remains the primary session handoff so T1 progress and NOT VERIFIED boundaries are not overwritten.
- Imported main-only files: four GitHub Actions workflows, the T0 PostgreSQL atomic-writer design record, and two Android/Chart Pro audit evidence documents. These are source/document imports only; they do not authorize a T0 production migration, Feeder activation, VPS deployment, exchange connection, Android release, or live execution.
- Reconciled `market_data/test_write_gateway.py`: retained main's committed-batch process-crash/restart regression and branch's invalid-existing-schema/no-side-effect regression, along with both existing gateway isolation checks. No production T0 implementation code was changed by this merge.
- Prior T1 cutover overlap and statement-total mismatch tests remain NOT VERIFIED until a workflow runs on the exact merged SHA. Earlier 69/69 evidence applies only to `8dadd35b7e9e0174efab70c425eab53bca99fa34`.
- `ai_execution_enabled=false`; paper-only boundary retained. No persistent account database was opened or migrated; no backtest, deployment, exchange connection, Feeder activation, or live order occurred.
- Next: inspect the merge commit's complete file list and run isolated CI on the exact merge SHA. Record T0 and T1 results separately. Keep all unresolved funding provenance/cutover checks NOT VERIFIED.


## 2026-11-06 — post-merge exact-SHA CI result

- Merge commit/source SHA: `8ec8f17f387742a4925d01d3c5454983455d2794`; GitHub Actions push run [#42197091587](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42197091587) checked out this exact SHA.
- Overall workflow conclusion: **FAIL** because the fresh-cluster restricted provider bootstrap job failed. Do not mark the combined run PASS.
- PASS jobs:
  - Static Gateway contract verification (job `127822957142`): complete `market_data` regression 233 tests, 37 skipped, remaining tests PASS; merged `market_data/test_write_gateway.py` regressions all PASS, including process-crash/restart and invalid-existing-schema/no-side-effect.
  - Paper consumer fixture regressions (job `127822957315`): 44/44 PASS.
  - Isolated TimescaleDB integration (job `127823076393`): atomic writer 7/7; PostgreSQL FeederRuntime integration 18/18; PostgreSQL runtime lifecycle 4/4; least-privilege roles 18/18; read-only TimescaleDB 6/6. Total 53/53 PASS against disposable CI services only.
- FAIL job:
  - Fresh-cluster restricted provider bootstrap (job `127822957489`): 1 test ERROR in `test_non_superuser_bootstrap_provisions_roles_then_restricted_migrations_run`; `migrate()` raises `RuntimeError: t0_migrator may only be granted to the ephemeral t0_migrator_login role`. This is a PostgreSQL role-membership safety contract failure. No security guard was weakened and no T0 source was modified to force green.
- Artifacts, all associated with exact SHA `8ec8f17f387742a4925d01d3c5454983455d2794`:
  - T0 Gateway evidence ID `13492172760`, SHA-256 `a73396f1e60bef4417c32779cd52add34d2683a55baa00019a1db922edee0e56`.
  - Paper consumer evidence ID `13493025206`, SHA-256 `bcc7e5faf47e06d27f003d224edf9876cf7847d72ece573af4a8009281d045f3`.
  - T0 provider bootstrap failure evidence ID `13493245380`, SHA-256 `7a18c87909a7d84ec3e428e0a4089c2f1705f9f61ac19f3a0a669595c22b34d6`.
  - TimescaleDB integration evidence ID `13492403228`, SHA-256 `108cacc0f1c31f95dc7578d971fc50653d07dc7886362188309214d6e858ea40`.
- Dual Ledger workflow `.github/workflows/dual-ledger-red.yml` did not trigger on this merge push because its path filter covers `paper_execution/**` and that workflow file; neither changed in the merge. Therefore current-merge-SHA Dual Ledger suite is **NOT RUN / NOT VERIFIED**. Earlier 69/69 remains evidence only for SHA `8dadd35b7e9e0174efab70c425eab53bca99fa34`; it must not be transferred to this merge SHA.
- Merge diff from the T1 parent contains only eight imported paths plus the two reconciled files; no T0 production source, T1 paper-execution source, persistent database, or runtime configuration was changed. The only T0 code path change is test-only `market_data/test_write_gateway.py`.
- Status: **BRANCH SYNC MERGE PASS; T0 GATEWAY/PAPER CONSUMER/TIMESCALEDB SUITES PASS; PROVIDER BOOTSTRAP BLOCKED; DUAL LEDGER CURRENT-SHA CI NOT VERIFIED.**
- Next: keep branch at the merge commit unless a separately scoped follow-up is approved. Investigate the T0 provider role-membership failure without weakening least-privilege rules. Separately arrange exact-SHA Dual Ledger CI for the unchanged T1 paper_execution source. No T0 production DB migration, VPS/Feeder activation, exchange connection, backtest, deployment or live execution. `ai_execution_enabled=false`.

## 2026-11-06 — T1 funding-coverage overlap early-exit regression fixed

- Scope: T1 `paper_execution` only. T0 investigation remains explicitly paused; no T0 source, tests, schema, workflow, provider policy, or runtime changes in this increment.
- Added regression `test_account_equity_cutover_rejects_overlap_after_coverage_is_complete` in `paper_execution/test_dual_ledger_red.py`. It creates a VERIFIED interval covering the complete cutover window plus a second VERIFIED interval nested inside it.
- RED test commit/source SHA: `aee0efcdb024c5e9e68b772f5f75c2eb4ad038bc`.
- Exact push workflow [#42197639459](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42197639459), checked out the exact RED SHA. Compile PASS; focused suite ran 37 tests and failed only the new regression with `AssertionError: ValueError not raised`; full suite skipped as designed. This confirmed the bug: the coverage loop stopped as soon as the cursor reached the requested end and never inspected later overlapping intervals.
- Minimal fix in `paper_execution/funding.py`: remove the early break after coverage reaches the cutover end. The loop now checks every interval selected for the requested window for overlap; the existing gap/UNKNOWN/DISABLED checks remain fail-closed.
- GREEN implementation/source SHA: `fe7c130c965a93c3b21bad3be1a57f7ccd662eb9`.
- Exact push workflow [#42197702019](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42197702019), checked out the exact GREEN SHA; conclusion SUCCESS. Compile PASS; isolated PAPER-only preflight PASS; focused Dual Ledger + migration tests 37/37 PASS; full `paper_execution` regression 72/72 PASS. The new nested-overlap regression PASS.
- Job ID: `127824984750`.
- Artifact ID: `13492288862`, name `dual-ledger-red-evidence-fe7c130c965a93c3b21bad3be1a57f7ccd662eb9`, GitHub upload digest `sha256:5b5da7d7c1021a8091711fe583376c5b9b763fdad3a3bc2017b3c230f8374380`, expires 2026-11-13. Digest is GitHub artifact metadata; payload bytes were not separately downloaded and re-hashed.
- Exact diff from pre-increment HEAD `09e0cd63d2df3dd184f9f0809656d612b01ac608` to tested SHA `fe7c130c965a93c3b21bad3be1a57f7ccd662eb9`: only `paper_execution/test_dual_ledger_red.py` and `paper_execution/funding.py` changed. No persistent account DB opened or migrated.
- Status: **PASS — nested funding-coverage overlap is now detected even when an earlier interval already spans the full cutover window; focused 37/37 and full 72/72 PASS on exact SHA `fe7c130...`.**
- Still NOT VERIFIED: actual historical funding completeness, external statement-byte authenticity, real-account cutover, and backtest suitability. Tests use temporary SQLite fixtures only.
- Next: add isolated cutover regressions for future/stale mark and candle timestamps, corrupt funding-event provenance, and restart/replay/immutability boundaries. Keep T0 investigation paused. No persistent DB migration, backtest, merge, deployment, exchange connection, or live execution. `ai_execution_enabled=false`.

## 2026-11-06 — T1 account cutover failure-boundary regressions

- Scope: test-only additions in `paper_execution/test_dual_ledger_red.py`; no production logic changed in this increment. T0 investigation remains paused.
- Added isolated temporary-SQLite regressions for: (1) a gap between VERIFIED funding-coverage intervals; (2) a future mark observation later than the supplied recorded-at timestamp; (3) a closed candle older than the 30-minute cutover freshness limit; and (4) a funding event whose immutable provenance is deliberately corrupted in the test fixture after dropping its update trigger.
- Test source SHA: `dd208e1a4c70b84e787e1a1961c5cc48ca144f0a`.
- Exact push workflow [#42197863770](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42197863770), checked out the exact source SHA; conclusion SUCCESS. Compile PASS; isolated PAPER-only preflight PASS; focused Dual Ledger + migration tests 41/41 PASS; full `paper_execution` regression 76/76 PASS.
- Job ID: `127825537178`.
- Artifact ID: `13493470732`, name `dual-ledger-red-evidence-dd208e1a4c70b84e787e1a1961c5cc48ca144f0a`, GitHub upload digest `sha256:4646944f53a01758b8a2c3444dbe4d80bd59a8df4c51f0b2087d4a398c402cff`, expires 2026-11-13. Digest is GitHub artifact metadata; payload bytes were not separately downloaded and re-hashed.
- All four new tests PASS against the existing fail-closed guards. No source/schema/workflow changes, no persistent account DB opened or migrated, no exchange connection, backtest, deployment, or live order.
- Status: **PASS — cutover rejects funding gaps, future mark observations, stale closed candles, and corrupted funding-event provenance; focused 41/41 and full 76/76 PASS on exact SHA `dd208e1...`.**
- Still NOT VERIFIED: actual historical funding completeness, external statement-byte authenticity, real-account cutover, and backtest suitability. These fixtures prove local guard behavior only.
- Next: exercise restart/replay/idempotency boundaries for cutover and verify read-only snapshot behavior under corrupt or incomplete provenance. Keep T0 investigation paused. No persistent DB migration, backtest, merge, deployment, exchange connection, or live execution. `ai_execution_enabled=false`.

## 2026-11-06 — T1 Account Equity Cutover restart/replay and read-only snapshot verification

- Scope: test-only additions in `paper_execution/test_dual_ledger_red.py`; no production source, schema, workflow, or T0 changes. T0 investigation remains paused.
- Added `test_account_equity_cutover_replay_after_reopen_is_idempotent_and_conflict_safe`: establishes cutover, closes/reopens database access and reconstructs Core/AI ledger handles, then replays the identical cutover request. Verifies exactly one cutover row and one cutover audit, identical replay result, and unchanged HWM/daily baseline/equity/readiness/version. A changed payload hash under the same cutover ID must raise `ACCOUNT_EQUITY_CUTOVER_ID_CONFLICT` without changing durable state.
- Added `test_read_account_risk_snapshot_leaves_database_bytes_unchanged`: compares exact SQLite file bytes before and after snapshot read and verifies snapshot remains available and risk-ready.
- Exact source SHA: `c6390a53d12a7999ab71c2a9a45cdf8aba563c24`.
- Exact push workflow [#42198245149](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42198245149), checked out exact source SHA; conclusion SUCCESS. Compile PASS; isolated PAPER-only preflight PASS; focused Dual Ledger + migration tests 43/43 PASS; full `paper_execution` regression 78/78 PASS.
- Job ID: `127826812719`.
- Artifact ID: `13493186942`, name `dual-ledger-red-evidence-c6390a53d12a7999ab71c2a9a45cdf8aba563c24`, GitHub upload digest `sha256:67dedde715226c151168ea33c168ed86f6ad555a86ab664c99e413c371567ba2`, expires 2026-11-13. Digest is GitHub artifact metadata; payload bytes were not separately downloaded and re-hashed.
- Status: **PASS — cutover replay after reopening is idempotent, conflicting replay is mutation-free, and risk snapshot leaves the SQLite file byte-identical; focused 43/43 and full 78/78 PASS on exact SHA `c6390a5...`.**
- Limits: restart is simulated by closing/reopening database access and reconstructing ledger handles within one test process; an OS/process-kill recovery test is not yet performed. Byte-identical snapshot proof is for this SQLite fixture and code path, not production DB.
- Next: add process-crash/restart coverage around cutover transaction commit boundaries if the test harness can deterministically inject a crash; otherwise review transaction atomicity and recovery semantics read-only. Keep T0 paused. No persistent account DB migration, backtest, merge, deployment, exchange connection, or live execution. `ai_execution_enabled=false`.

## 2026-11-06 — T1 Account Equity Cutover OS process-crash/restart verification

- Scope: test-only additions in `paper_execution/test_dual_ledger_red.py`; no production source, schema, workflow, or T0 changes. T0 investigation remains paused.
- Added a real child-process termination harness using `subprocess` and `os._exit` against temporary SQLite fixtures. The connection proxy forwards SQLite connection attributes and allows deterministic termination immediately after selected SQL operations or immediately after the transaction context commits.
- Pre-commit crash points tested independently: after inserting the cutover row; after updating `paper_account_risk_state` HWM/daily baseline; and after inserting the cutover audit record. In all three cases the child exits with code 71; reopening the DB shows zero cutover rows, zero cutover audit rows, and unchanged HWM/daily baseline/equity/readiness/version. Retrying the same cutover then succeeds and produces exactly one cutover and one audit record.
- Post-commit crash test: child exits with code 72 immediately after SQLite context-manager commit, before the function can return to its caller. Reopening shows exactly one committed cutover and audit, with initialized HWM/daily baseline. Replaying the same cutover returns successfully and leaves all durable state unchanged.
- Initial harness attempt at source `2b80c471d575fb740a6dac1048c7a6a008e56478` failed before reaching crash points because the proxy stored `row_factory` on itself rather than forwarding it to the SQLite connection. This was a test-harness defect, not a production failure. The harness was corrected to forward connection attribute writes; no production code changed.
- Exact GREEN source SHA: `d1eebd996025dd6b711c5ad6beb0bb367cb6cf2c`.
- Exact push workflow [#42198568561](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42198568561), checked out the exact source SHA; conclusion SUCCESS. Compile PASS; isolated PAPER-only preflight PASS; focused Dual Ledger + migration tests 45/45 PASS; full `paper_execution` regression 80/80 PASS.
- Job ID: `127827883862`.
- Artifact ID: `13493847011`, name `dual-ledger-red-evidence-d1eebd996025dd6b711c5ad6beb0bb367cb6cf2c`, GitHub upload digest `sha256:aac9d6813bada073cb208c04cbefc42e8397f072397b513c309f9ac914df32fc`, expires 2026-11-13. Digest is GitHub artifact metadata; payload bytes were not separately downloaded and re-hashed.
- Exact diff from previous handoff HEAD `0e7bebab07612cb9cabeb5f4549058bc4cd009f7` to tested source SHA `d1eebd996025dd6b711c5ad6beb0bb367cb6cf2c`: only `paper_execution/test_dual_ledger_red.py` changed. No persistent account DB opened or migrated.
- Status: **PASS — SQLite transaction is atomic across the tested process-kill points before commit; post-commit process death leaves one durable cutover/audit and replay is idempotent. Focused 45/45 and full 80/80 PASS on exact SHA `d1eebd9...`.**
- Limits: this verifies process death and SQLite recovery using temporary test databases on the GitHub Actions Linux runner. It does not verify power-loss/storage-controller behavior, production database state, historical funding completeness, external statement-byte authenticity, or real-account cutover.
- Next: perform a read-only integrity review of the complete Account Equity Cutover lifecycle and identify any remaining failure modes before considering persistent migration or backtest. Keep T0 paused. No persistent account DB migration, backtest, merge, deployment, exchange connection, or live execution. `ai_execution_enabled=false`.

## 2026-11-06 — T1 funding integrity review: HWM freeze, interval exclusivity, event provenance, and admission parity

- Scope: T1 `paper_execution` only. T0 investigation remains paused. No T0 source/schema/workflow/runtime changes.
- Read-only review found four fail-closed gaps, each reproduced by tests before implementation:
  1. `_refresh_equity` advanced HWM from 100 to 105 after a funding credit even while `risk_ready=0`; current equity may refresh, but HWM must remain frozen until readiness is restored.
  2. `record_funding_coverage` accepted a new VERIFIED interval overlapping an existing interval after cutover.
  3. `read_account_risk_snapshot` returned `riskReady=true` after a funding event's immutable provenance was deliberately corrupted.
  4. The snapshot returned `riskReady=true` when overlapping coverage rows were inserted directly into the database; the scoped admission path also had a separate weaker UNKNOWN-only check.
- Added regression tests for all four findings, plus a missing-coverage funding-event admission test. RED evidence: workflow [#42198874098](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42198874098) reproduced the first three; follow-up RED [#42199085705](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42199085705) confirmed four integrity failures; [#42199293994](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42199293994) exercised updated adjacent-interval cases before the final shared admission guard.
- Production fixes:
  - `_refresh_equity` now refreshes current equity while preserving HWM whenever persisted `risk_ready=0`; invalid readiness state fails closed.
  - `record_funding_coverage` rejects any interval overlap using half-open interval semantics; adjacent intervals remain valid. Existing tests were adjusted so UNKNOWN/DISABLED cases use non-overlapping intervals.
  - `record_funding_event` requires exactly one matching VERIFIED coverage interval, or an explicitly configured PAPER_TEST_CONFIGURATION DISABLED interval. Missing, UNKNOWN, ambiguous, or unsupported coverage rejects the event before ledger mutation.
  - Added shared read-only `_funding_provenance_ready(...)` validation. It checks coverage completeness through the current mark observation, all interval overlaps, UNKNOWN/invalid DISABLED intervals, each funding event's source/snapshot/hash/timestamps, event-to-coverage membership, and event totals against all strategy-ledger funding totals.
  - Both `read_account_risk_snapshot` and `_submit_scoped` now use the same shared validator. Thus a snapshot that detects corrupt/incomplete provenance also blocks new exposure; risk-reducing paths remain governed by their existing reduction rules.
- Exact GREEN source SHA: `653196ff0be06d391c23b5ebfd6a9bf7f5a2629e`.
- Exact push workflow [#42199474046](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42199474046), checked out the exact source SHA; conclusion SUCCESS. Compile PASS; isolated PAPER-only preflight PASS; focused Dual Ledger + migration tests 50/50 PASS; full `paper_execution` regression 85/85 PASS.
- Job ID: `127830898577`.
- Artifact ID: `13493458106`, name `dual-ledger-red-evidence-653196ff0be06d391c23b5ebfd6a9bf7f5a2629e`, GitHub upload digest `sha256:9273071dac277bf6b4b1005e6f0679374c1a5dac287f0f7dc8ae4015702dc60b`, expires 2026-11-13. Digest is GitHub artifact metadata; payload bytes were not separately downloaded and re-hashed.
- Status: **PASS — HWM no longer advances while risk is unready; overlapping coverage and uncovered funding events are rejected; read-only snapshot and new-exposure admission share fail-closed provenance validation. Focused 50/50 and full 85/85 PASS on exact SHA `653196f...`.**
- Limits: tests use temporary SQLite databases. They do not establish historical funding completeness, authenticity of external statement bytes, real-account cutover, or backtest suitability. Direct database tampering can still occur outside application controls; the read-only validator now detects the tested provenance/overlap cases and blocks readiness.
- Next: review remaining Shared Risk Engine admission/reduction paths for parity with `_funding_provenance_ready`, then add boundary tests for funding interval advancement across mark updates and day rollover. Keep T0 paused. No persistent account DB migration, backtest, merge, deployment, exchange connection, or live execution. `ai_execution_enabled=false`.

## 2026-11-06 — T1 funding coverage advancement and UTC daily-baseline boundary tests

- Scope: test-only additions in `paper_execution/test_dual_ledger_red.py`; no production source, schema, workflow, or T0 changes. T0 investigation remains paused.
- Read-only path review:
  - Core/AI ENTRY and DCA increases pass through `_submit_scoped`, which calls the same `_funding_provenance_ready(...)` validator used by `read_account_risk_snapshot`.
  - Pure reductions/flattening do not require fresh funding provenance or a clear Kill Switch, preserving the close-only escape path. Reversal has an exposure-increasing leg and is not treated as a pure reduction; it must be closed first, then separately admitted.
  - Legacy manual submission is blocked after Dual Ledger migration. `reduce_legacy_unattributed(...)` is separately constrained to strict position reduction and does not create Core/AI risk reservations.
  - UTC day rollover does not silently roll the baseline. Snapshot returns `ACCOUNT_RISK_DAILY_BASELINE_UNAVAILABLE`; scoped admission returns `RISK_INPUTS_STALE_OR_CORRUPT` until a verified daily baseline is explicitly established. No automatic reset was added.
- Added three isolated temporary-SQLite tests:
  1. `test_mark_advancement_requires_contiguous_funding_coverage_and_allows_admission`: after mark advances five minutes, an adjacent VERIFIED coverage interval keeps snapshot ready and Core admission succeeds.
  2. `test_mark_advancement_beyond_funding_coverage_blocks_new_exposure`: moving the mark beyond verified coverage makes snapshot `riskReady=false` with `FUNDING_PROVENANCE_INCOMPLETE` and rejects new Core exposure.
  3. `test_utc_day_rollover_does_not_silently_reset_daily_loss_baseline`: even with continuous funding coverage and a fresh mark on the next UTC day, the prior-day baseline is preserved; snapshot and admission fail closed rather than silently resetting it.
- First test run source SHA `00d957ce8cd2fe8b990df35c1e424c5f7166794f` failed one new test because the fixture reused an intent whose `validUntilMs` preceded the advanced mark time. This was a test-fixture error (`EXPIRED_INTENT`); no production failure. The fixture now creates a valid time window relative to the advanced mark.
- Exact GREEN source SHA: `32674c6c03f51b7544e06fee9527b9434425d5a2`.
- Exact push workflow [#42200257973](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42200257973), checked out exact source SHA; conclusion SUCCESS. Compile PASS; isolated PAPER-only preflight PASS; focused Dual Ledger + migration tests 53/53 PASS; full `paper_execution` regression 88/88 PASS.
- Job ID: `127833493915`.
- Artifact ID: `13493539446`, name `dual-ledger-red-evidence-32674c6c03f51b7544e06fee9527b9434425d5a2`, GitHub upload digest `sha256:c6d8f6ac56d02db56e043526b49d0d8d5a78891f46954dba40296ca97a723df5`, expires 2026-11-13. Digest is GitHub artifact metadata; payload bytes were not separately downloaded and re-hashed.
- Status: **PASS — mark advancement requires continuous funding provenance; uncovered time blocks new exposure; UTC day rollover preserves the previous baseline and fails closed. Focused 53/53 and full 88/88 PASS on exact SHA `32674c6...`.**
- Limits: tests use temporary SQLite and manually advance the mark fields; no live market-data writer or production DB is involved. Daily baseline rollover is intentionally NOT IMPLEMENTED; a separately verified, auditable rollover operation is still required before the next UTC day can trade. Historical funding completeness, external statement-byte authenticity, real-account cutover, and backtest suitability remain NOT VERIFIED.
- Next: specify and test an explicit, atomic, idempotent UTC daily-baseline rollover contract. It must use a verified account-equity snapshot, enforce one baseline per UTC day, preserve prior-day history, and fail closed on stale mark/funding/risk inputs. Do not silently reset on read or on order submission. Keep T0 paused. No persistent account DB migration, backtest, merge, deployment, exchange connection, or live execution. `ai_execution_enabled=false`.

## 2026-11-06 — Decision: reconstruct UTC daily-loss equity at exact 00:00 UTC

- User decision: use **historical reconstruction at exactly 00:00:00 UTC** for every daily-loss baseline. Do not use the first eligible snapshot of the day; it could omit losses incurred before that snapshot.
- Baseline must represent account-wide equity at the UTC boundary, reconstructed from a previously verified account state plus the complete ordered history of all Core, AI, and Legacy events up to (but excluding) the boundary, valued using a verified market mark assigned to that boundary.
- Boundary convention: event time uses half-open UTC day windows `[00:00:00, next 00:00:00)`. Events with `event_at_ms < boundary_ms` are included in the baseline; events exactly at the boundary belong to the new UTC day. The valuation mark must have an explicit, deterministic timestamp/interval policy and source identity; do not silently substitute the latest available price.
- Required reconstruction inputs:
  1. A previously verified starting snapshot/cutover containing account capital, each ledger's signed position and average entry, cumulative realized PnL, fees, funding, legacy adjustments, and provenance.
  2. A complete immutable execution journal for every Core/AI/Legacy fill and adjustment, including execution time, signed quantity, fill price, fee amount/currency, strategy owner, order/intent identity, and source/evidence hash. Position and realized PnL must be replayable, including partial fills, reductions, reversals, and DCA.
  3. Complete immutable funding events with economic event time, amount, owner, source snapshot and hash, plus contiguous VERIFIED funding coverage through the boundary.
  4. Verified market mark for the exact boundary under an explicit price convention, with source snapshot/hash, dataset version, and freshness/quality proof.
  5. Completeness proofs for all event streams and legacy adjustments. Unknown or unattributed events, missing fees, gaps, conflicting duplicates, or unverified source snapshots invalidate reconstruction; unknown is never zero.
- Atomic rollover contract: acquire `BEGIN IMMEDIATE`; verify previous baseline and contiguous source coverage; replay events deterministically; reconcile reconstructed positions/PnL/fees/funding and account equity; verify exact-boundary mark; insert one immutable baseline per `(account_id, utc_day_ms)` and audit record in the same transaction. Identical retry is idempotent; conflicting replay/input for the same day is rejected. Any failure rolls back and leaves the previous baseline unchanged, sets/retains risk unready, and blocks new exposure. Risk-reducing/flattening remains available.
- Late-arriving event policy: an event recorded after the boundary but whose economic `event_at_ms` precedes it invalidates the affected day's completeness proof. Recompute the baseline from source evidence under a new audited reconciliation revision; never silently overwrite an immutable baseline. Until reconciliation completes, block new exposure.
- Read-only schema review found the current Dual Ledger tables hold current aggregate position/PnL/fees/funding and immutable funding events/coverage, but no dedicated immutable time-series market-mark table or normalized fill/event journal sufficient to prove complete historical reconstruction for every strategy. `paper_equity_history` is the legacy single-strategy history and cannot be assumed to cover Core/AI/Legacy. `paper_orders`/`paper_audit` documents may contain execution detail, but completeness and deterministic replay suitability have NOT been established.
- Therefore: **architecture decision ACCEPTED; implementation BLOCKED pending a data-source completeness contract and schema design.** Do not implement a rollover that merely copies current equity, uses first-in-day snapshot, infers missing fees/funding as zero, or trusts an unverified latest mark.
- Next: inventory exact persisted fill/order/audit payloads and available historical market-data sources; define canonical append-only account event journal and exact-boundary mark contract; add RED tests for missing/gapped/late/conflicting events, partial fills/reversals, funding boundary inclusion, and missing/stale mark before implementing the new journal/rollover path.
- Restrictions unchanged: no persistent account DB migration, no production backtest, no exchange connection, no deployment, no merge, no live orders; T0 remains paused; `ai_execution_enabled=false`.

### Follow-up inventory of existing execution evidence (read-only)

- `paper_orders` stores aggregate `quantityBase`, `filledBase`, `averagePrice`, `feeQuote`, `createdAtMs`, and `updatedAtMs`; the order document does not itself preserve a normalized list of every fill.
- Core/AI `paper_audit` SUBMIT documents include `consumedLevels` with side/price/quantity and aggregate `feeQuote`; Legacy reduction audit documents also include `consumedLevels`, reconciliation ID, and evidence hash. This may be useful replay evidence, but it is not yet a canonical event stream.
- `paper_audit` has no immutable UPDATE/DELETE triggers in the current schema. `paper_orders` is intentionally updated for expiry/cancel lifecycle. Therefore audit rows cannot currently be treated as tamper-evident, append-only source history for a certified replay.
- `paper_legacy_book_consumptions` is append-only and has evidence hashes, but it only covers Legacy book consumption and does not provide the complete account event history.
- `paper_funding_events` and `paper_funding_coverage` are immutable/provenance-aware and can support the funding part, but funding completeness alone cannot prove all executions, fees, adjustments, and boundary marks.
- `paper_equity_history` is legacy single-strategy history. No dedicated immutable dual-ledger historical mark table or complete Core/AI/Legacy event-journal completeness watermark was found in the inspected `paper_execution` schema.
- Result: existing `paper_audit`/`paper_orders` are evidence inputs to reconcile/migrate, not sufficient authority for a certified 00:00 UTC replay without proving historical row completeness and protecting the history from mutation. Do not derive daily baselines directly from these tables.
- Proposed next design increment: introduce a canonical append-only account event journal populated atomically with every fill/reduction/reversal/fee/adjustment/funding event, plus immutable market-mark snapshots and source-coverage watermarks. Backfill only from verifiable existing audit/evidence; any uncovered period remains UNKNOWN and blocks rollover. Keep historical original tables unchanged.

## 2026-11-06 — UTC Equity Reconstruction v1 design + RED contract

- User selected exact historical reconstruction at 00:00:00 UTC; first-in-day snapshot is not an acceptable Daily Loss baseline.
- Design contract added: `docs/architecture/T1_UTC_EQUITY_RECONSTRUCTION_EVENT_JOURNAL_V1_2026-11-06.md`.
  - Migration v6 proposal: append-only `paper_account_event_journal`, `paper_account_history_coverage`, immutable `paper_market_mark_history`, and immutable `paper_daily_equity_baselines`.
  - Half-open event boundary: events before B included; events exactly at B excluded from baseline.
  - Separate verified coverage required for Core, AI, Legacy execution streams, market marks, and existing funding history.
  - Exact effective boundary mark required; no nearest/latest mark, interpolation, inferred fees, or synthetic fills.
  - Atomic `BEGIN IMMEDIATE` reconstruction; deterministic replay; one baseline per account/day; idempotent identical retry; conflicting digest rejected; failure preserves previous baseline and blocks increases.
  - Existing `paper_orders` aggregate fill and mutable `paper_audit` are not authoritative for complete historical replay. No backfill unless execution-level source evidence is independently verified.
- RED tests added to `paper_execution/test_dual_ledger_red.py`:
  1. migration creates the four v6 history tables and immutable triggers;
  2. event idempotency/conflict;
  3. adjacent coverage accepted and overlap rejected;
  4. exact-boundary mark persistence and immutability;
  5. missing-coverage reconstruction fails closed without baseline/readiness mutation.
- Design commit: `90ff1b468bb8865e6c164bdf7c33dbd10b71077a`.
- RED test commit/source SHA: `7a55b1242be35b35ba88ba95b6a44556acd4550f`.
- Current branch HEAD at this handoff update: pending final verification below.
- Test status: **RED CONTRACT WRITTEN / EXECUTION NOT VERIFIED**. The GitHub Actions workflow `.github/workflows/dual-ledger-red.yml` is configured for push changes under `paper_execution/**`; no workflow run for the test SHA was visible in the repository run listing at inspection time. No local checkout/runtime is available through this GitHub operation, so do not claim compile/test execution.
- No implementation or migration v6 source added yet. The tests are expected to fail against current code until the API/schema is implemented; the exact failure output remains NOT VERIFIED.
- Next: obtain a real GitHub Actions run of the RED test SHA and retain the expected failing evidence; then implement v6 minimally and atomically with per-fill journal writes inside existing ledger transactions, followed by GREEN and full `paper_execution` regression.
- Restrictions: no persistent DB migration/backfill, no production DB access, no backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; `ai_execution_enabled=false`.

### RED evidence — Account History v6 (2026-11-06)

- Exact test source SHA: `9e595b19984787d14f45f9109c0d41148adcb69a`.
- GitHub Actions run [#42201320105](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42201320105): **FAIL expected at RED stage**; exact checked-out SHA confirmed.
- Job ID: `127837017662`.
- Environment preflight: PASS (PAPER-only, no DB/network credentials).
- Python compile of RED contract: PASS.
- Focused RED contract: 58 tests executed; **1 assertion failure + 4 expected AttributeErrors** corresponding to missing v6 tables and not-yet-implemented event/coverage/mark/reconstruction APIs. Existing tests in the same focused modules passed. This establishes the expected RED state.
- Full `paper_execution` regression: SKIPPED by workflow after focused RED failed; no full-suite result for this SHA.
- Artifact ID: `13493653671`, name `dual-ledger-red-evidence-9e595b19984787d14f45f9109c0d41148adcb69a`, digest `sha256:5fc757343798756536e75e212b3d998463987d544234068860d911cbb2ec6778`, expires 2026-11-13.
- This RED run is test evidence only; it does not establish migration safety or reconstruction correctness. Next implementation must make these five tests GREEN and add broader replay/boundary/rollback tests before any full regression claim.

### GREEN slice — v6 schema and atomic fill journal (2026-11-06)

- Exact tested source SHA: `8d4b2431c95add83ed594b98fdc2f11d39667bc7`.
- GitHub Actions [#42202152930](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42202152930): SUCCESS on exact SHA.
- Job ID: `127839825999`.
- Compile: PASS. Focused Dual Ledger + migration tests: **60/60 PASS**. Full `paper_execution` suite: **95/95 PASS**.
- Artifact ID: `13494797355`, name `dual-ledger-red-evidence-8d4b2431c95add83ed594b98fdc2f11d39667bc7`, digest `sha256:28f6a9c40858bee8f33f1fbe09e1c3d82efedd7b7a20a3c9443172317d8d6831`, expires 2026-11-13.
- Migration v6 adds four account history tables and immutable UPDATE/DELETE triggers for event journal, coverage, market marks, and daily baseline. Migration checksum/version is validated on repeat open.
- Event API supports PAPER FILL / explicit LEDGER_ADJUSTMENT records, SHA-256 payload syntax, stable event IDs, idempotent identical retry, and conflict rejection.
- Coverage API enforces stream ownership, half-open intervals, adjacent interval acceptance, overlap rejection, and immutable evidence. Coverage is tracked separately for Core, AI, Legacy, and account market-mark stream.
- Market-mark API accepts only exact UTC boundary marks (`effective_at_ms` and `candle_close_ms` equal UTC midnight), with source/dataset/hash metadata; conflicting mark at same account boundary is rejected.
- Core/AI scoped submit now appends one journal event per consumed book level, including signed quantity, fill price, per-level fee, intent/order IDs, book snapshot identity, and SHA-256 digest **inside the same BEGIN IMMEDIATE transaction** as order/ledger/reservation changes.
- Legacy unattributed reduction similarly journals each consumed level inside its existing transaction; no Core/AI ledger is mutated.
- New tests prove multi-level Core fill journaling and that a journal INSERT failure rolls back the Core order/position; existing Legacy reduction test verifies separate Legacy event attribution.
- Important incomplete behavior: `reconstruct_daily_equity_baseline(...)` currently validates contiguous execution/market-mark coverage and exact boundary mark, but deliberately stops with `ACCOUNT_HISTORY_REPLAY_NOT_IMPLEMENTED` after evidence validation. It does not create a baseline, replay fills/funding, or change readiness. Baseline table currently stores only initial reconstruction metadata; full per-ledger replay result columns/digest manifest and replay engine remain to be implemented.
- Historical data ingestion/backfill, market-mark completeness, funding integration into replay, late-event invalidation, exact equity reconciliation, atomic baseline insertion/idempotency, and risk admission gate against the new baseline remain NOT VERIFIED / NOT IMPLEMENTED.
- All CI used temporary isolated SQLite databases. No persistent account DB was opened or migrated; no external exchange/network clients were used.
- Next: implement deterministic per-ledger replay from verified cutover using event journal + funding events + exact boundary mark; extend baseline schema to persist full per-ledger replay results and coverage manifest; add RED tests for event ordering, partial fills, reversals, UTC boundary inclusivity, funding boundary, late events, conflicts, and rollback. Only after this should daily risk admission consume the reconstructed baseline.
- Restrictions: no persistent DB migration/backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; `ai_execution_enabled=false`.


## 2026-11-06 — T1 migration v7: immutable per-ledger cutover snapshots

- Scope: add a versioned additive schema for the exact starting state required by deterministic replay. No existing account database was opened, migrated, or backfilled; all CI fixtures use temporary SQLite. No T0 source/runtime/provider changes.
- RED contract commit/source SHA: `1f40e416b3783bd13cc23147f39c6c7dadb005e0`.
  - Added three tests requiring one cutover snapshot for each of Core, AI, and Legacy; immutable UPDATE/DELETE; and exact cutover timestamp/source snapshot/hash.
  - GitHub Actions [#42203208768](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42203208768): expected RED confirmed (missing v7 table/metadata).
  - Artifact ID `13495406644`; SHA-256 `34551e4e0332a8cf351b616bd41030675936e64bc6870d4968c2309bd2f5a862`.
- Implementation:
  - Migration v7 creates `paper_account_cutover_ledger_snapshots`, keyed by `(cutover_id,strategy_id)`, with signed position, average entry, realized PnL, fees, funding, exact cutover mark-observation timestamp, source snapshot ID, payload hash, and canonical payload.
  - UPDATE/DELETE triggers reject mutation.
  - Migration runs after v6 as part of Dual Ledger initialization; checksum/status and schema completeness are verified on repeat opens.
  - `record_account_equity_cutover` captures all three ledger snapshots inside the same `BEGIN IMMEDIATE` transaction as the immutable account cutover and risk baseline update. It verifies the complete expected strategy set before inserting.
  - Identical cutover replay remains idempotent because the existing cutover row is checked before snapshot insertion; conflicting cutover requests reject before mutation.
- An intermediate CI run exposed three outdated migration-version assertions; these were updated to include v7. No production logic was weakened.
- Exact GREEN source SHA: `b9ea830678cd8a00e1dc5dae32e041611923e10f`.
- GitHub Actions [#42203452852](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42203452852): SUCCESS on exact SHA.
  - PAPER-only preflight: PASS.
  - Python compile: PASS.
  - Focused Dual Ledger + migration suite: 60/60 PASS.
  - Full `paper_execution` regression: 152/152 PASS.
  - Job ID: `127844144742`.
  - Artifact ID: `13494694690`, name `dual-ledger-red-evidence-b9ea830678cd8a00e1dc5dae32e041611923e10f`, GitHub upload digest `sha256:2d699dc58f4ff5653bfba3e18846a7a89fba631aa9c3af43f7902d30cb85aacf`.
- Status: **PASS — v7 per-ledger cutover snapshot schema and atomic snapshot capture verified on temporary SQLite.**
- Important limits / next:
  - This does not yet implement deterministic replay, funding cutoff selection, exact-boundary equity valuation, baseline insertion, late-event invalidation, or the exposure-admission gate.
  - Event journal API still has a default `fee_quote="0"`; this is not acceptable evidence for replay when the fee input was omitted. Next change must make fee provenance explicit and prove missing fees fail closed, while checking every writer call site.
  - Next RED tests: replay long/short partial fills, reductions, reversals and DCA in event-time order; funding at exactly boundary is excluded from prior day and included in new day; late-arriving pre-boundary event invalidates coverage; exact-boundary mark and dataset identity; missing fee/owner/coverage never treated as zero; deterministic digest and atomic/idempotent baseline insert; failure rollback and no risk-readiness promotion.
  - Snapshot state is now available only for new verified cutovers. No automatic reconstruction or historical backfill is authorized.
- Restrictions unchanged: no persistent account DB migration/opening, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — T1 migration v8: explicit fee amount and quote-currency provenance

- Scope: close the event-journal fee-provenance gap before deterministic replay. Added additive migration v8; removed the event API's implicit `fee_quote="0"` default; fee amount and fee currency are now mandatory. This is source/schema/test work only.
- RED contract commit/source SHA: `50fab449d5c8b6e2297b864dddf409e6fabab35e`.
  - GitHub Actions [#42262214928](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42262214928): expected RED; compile PASS; 63 focused tests executed with 1 failure and 4 errors at the missing explicit fee/currency contract.
  - Artifact ID `13524389670`; uploaded ZIP SHA-256 `a84e9007659135d02ca43b7fc05443ec88bc3f0b3586ea6ccf3c0a12be969c5d`.
- Implementation:
  - Migration v8 adds nullable `fee_currency` to `paper_account_event_journal`, records version/checksum, and installs an INSERT trigger requiring the BTCUSDT quote currency `USDT`.
  - `record_account_history_event` requires both `fee_quote` and `fee_currency`; it rejects missing values and currencies other than USDT. Canonical payload includes the explicit fee currency.
  - Core/AI scoped fills and Legacy reductions now persist `fee_currency='USDT'` in the same transaction as their fill journal rows; source payloads include the currency too.
  - Event API checks that v8 is applied before writing. Migration re-open verifies the column and trigger.
  - Existing rows are deliberately not assigned a guessed currency by migration. Any pre-v8 journal row with NULL fee currency remains UNKNOWN and must block replay until independently reconciled; it is not treated as USDT or zero.
- An intermediate implementation run [#42262617890](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42262617890) exposed one stale migration expectation (test still expected versions 1–7). That assertion was corrected; no production logic was weakened.
- Exact GREEN source SHA: `dc0abe734cd64012e29faa3a0b45510ca0be8df7`.
- GitHub Actions [#42262782158](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42262782158): SUCCESS on exact checked-out SHA.
  - PAPER-only preflight: PASS.
  - Python compile: PASS.
  - Focused Dual Ledger + migration tests: 64/64 PASS.
  - Full `paper_execution` regression: 160/160 PASS.
  - Job ID: `128046762304`.
  - Artifact ID: `13524769491`, name `dual-ledger-red-evidence-dc0abe734cd64012e29faa3a0b45510ca0be8df7`, GitHub upload digest `sha256:d8ec1c6156ac61b0cc44c0bf0d812138b4e0fbfe9a3d0e2822e3a5ceb45b1878`, expires 2026-11-13. Digest is GitHub artifact metadata; payload bytes were not separately downloaded and re-hashed.
- Status: **PASS — fee amount/currency are explicit for all new account-history event writes; missing or non-USDT currency is rejected at API and SQL insert boundary.**
- Limits:
  - Migration v8 was exercised only on temporary SQLite CI databases. No persistent account DB was opened or migrated.
  - Existing historical rows are not backfilled; fee currency for any old journal row remains UNKNOWN.
  - The replay engine, late-event invalidation, exact-boundary funding selection, immutable daily baseline insertion, and risk-admission gate remain NOT IMPLEMENTED / NOT VERIFIED.
  - No historical funding completeness, external statement authenticity, production account cutover, or backtest suitability is certified.
- Next: implement deterministic event replay from immutable per-ledger v7 cutover snapshots and the v6/v8 journal. First add RED tests for event-time sorting (not insertion order), signed long/short partial fills, reduction/reversal/DCA math, unknown legacy fee currency, funding exactly at boundary, late-arriving pre-boundary events, and exact boundary mark provenance. Then add replay result/coverage digest and atomic immutable baseline persistence. Keep all unknown evidence fail-closed.
- Restrictions unchanged: no persistent account DB migration/opening, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — T1 deterministic per-ledger replay core (pure calculation slice)

- Scope: add a deterministic, side-effect-free replay primitive before integrating replay with database baseline reconstruction. No account database is opened by this function; it accepts immutable snapshot/event values and returns a calculated ledger state.
- RED contract:
  - Commit/source SHA `0eaa9a5d6db959e400a7ccc8fee1697cdfec3425`.
  - GitHub Actions [#42266750473](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42266750473): PAPER-only preflight and compile PASS; focused contract correctly failed because `replay_ledger_events` did not exist.
  - Artifact ID `13528100086`, GitHub upload digest `sha256:714cb999f5ff414262508da0aebb45b0132d6a2dfa73459a91b47a38480e8b50`.
- Implementation:
  - Added `replay_ledger_events(snapshot, execution_events, funding_events, boundary_ms)` in `paper_execution/account_history.py`.
  - Sorts fills and funding by `(event_at_ms, stable event ID)`, independent of input/insertion order.
  - Applies signed fills with weighted average entry for same-direction adds; realizes PnL on reductions; handles full close and reversal with new-side average equal to reversal fill price.
  - Accumulates explicit nonnegative USDT fee amounts and signed funding amounts. Missing/non-USDT fee currency fails closed.
  - Uses half-open cutoff: only events with `event_at_ms < boundary_ms` are included. Events exactly at 00:00 UTC are excluded from prior-day replay.
  - Returns final position, average entry, realized PnL, fee/funding totals and included event IDs. It does not mutate a database.
- Test fixture correction: an intermediate test attempt used non-UTC-aligned boundaries and initially placed the “at-boundary” funding event before the actual boundary. Corrected to an exact 86,400,000 ms UTC day boundary and corrected realized PnL expectation to include both the profitable partial reduction and later reversal loss.
- Exact GREEN source SHA: `10689cbeadd654f8bea294bf9a2db2a7df540687`.
- GitHub Actions [#42267133821](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42267133821): SUCCESS on exact checked-out SHA.
  - PAPER-only preflight: PASS.
  - Python compile: PASS.
  - Focused Dual Ledger + migration + replay contract: 68/68 PASS.
  - Full `paper_execution` regression: 164/164 PASS.
  - Job ID: `128061861943`.
  - Artifact ID: `13527223127`, name `dual-ledger-red-evidence-10689cbeadd654f8bea294bf9a2db2a7df540687`, GitHub upload digest `sha256:58917092885b0cfc4b527f4f882a8e2b0231810a7f817fdb153654b217c1d05c`, expires 2026-11-13. Digest is GitHub artifact metadata; payload bytes were not separately downloaded and re-hashed.
- Status: **PASS — deterministic pure replay calculation for FILL events and funding cutoff. NOT VERIFIED — database reconstruction/baseline integration.**
- Known limits:
  - `LEDGER_ADJUSTMENT` events are not yet replayed; current helper rejects unsupported event types.
  - Replay helper currently validates fee currency and numeric amounts, but integration must additionally validate event source/snapshot/hash provenance and compare event recorded times against verified coverage watermarks to detect late-arriving pre-boundary events.
  - The helper does not yet verify funding coverage continuity, per-ledger cutover snapshot identity, exact boundary mark provenance, equity reconciliation, replay digest, immutable baseline insertion, or risk admission.
  - No database persistence is performed by this helper. No persistent account DB was opened or migrated.
- Next: integrate this pure helper into `reconstruct_daily_equity_baseline` with per-ledger v7 cutover snapshots, v6/v8 event journal, v4 funding events/coverage and exact boundary market mark. Require VERIFIED continuous coverage and provenance watermarks; reject late-arriving events and unsupported adjustments; persist immutable per-ledger replay outputs + digest + baseline + audit atomically; add rollback/idempotency/conflict and risk fail-closed tests.
- Restrictions unchanged: no persistent account DB migration/opening, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — T1 replay anchored to cutover snapshot and late-arrival watermark

- Scope: strengthen pure deterministic replay so it does not double-count events already reflected in the immutable v7 cutover snapshot and rejects late-arriving historical events. No database integration or persistent data access.
- RED evidence:
  - Contract commit `1cab91d3af4073e36248658d5a2ab4d328e25a1c`; run [#42267583128](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42267583128) correctly failed because the new cutover/watermark contract was not implemented.
  - Follow-up fixture-alignment commit `4df76ce021b59423042eaa305a49f4c86d3610f3`; run [#42267621200](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42267621200) remained RED on the missing API arguments.
  - First implementation run [#42267725989](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42267725989) exposed a fixture timestamp inconsistency (recorded_at_ms earlier than economic event time); corrected fixture only, without relaxing production validation.
- Implementation:
  - `replay_ledger_events` now requires `coverage_watermark_at_ms` and a `snapshot_at_ms` in the per-ledger snapshot.
  - Requires `snapshot_at_ms < boundary_ms <= coverage_watermark_at_ms`.
  - Execution and funding events with `event_at_ms <= snapshot_at_ms` are treated as already reflected in the cutover snapshot and excluded. If such an event was recorded after the snapshot timestamp, replay fails with `ACCOUNT_HISTORY_LATE_EVENT` because the snapshot cannot contain it.
  - Events after the snapshot and before the UTC boundary are included only when `recorded_at_ms <= coverage_watermark_at_ms`; later arrivals fail closed with `ACCOUNT_HISTORY_LATE_EVENT`.
  - All event timestamps must satisfy `event_at_ms <= recorded_at_ms`. Half-open UTC boundary semantics remain unchanged.
  - Added tests for late execution after watermark, late event at/before snapshot, and funding already included in snapshot versus funding after snapshot.
- Exact GREEN source SHA: `b59676e42ffbbcaeb6837d8137193f2798a0c8a5`.
- GitHub Actions [#42267824602](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42267824602): SUCCESS on exact checked-out SHA.
  - PAPER-only preflight: PASS.
  - Python compile: PASS.
  - Focused Dual Ledger + migration + replay contract: 71/71 PASS.
  - Full `paper_execution` regression: 167/167 PASS.
  - Job ID: `128064251218`.
  - Artifact ID: `13527886216`, name `dual-ledger-red-evidence-b59676e42ffbbcaeb6837d8137193f2798a0c8a5`, GitHub upload digest `sha256:95452998048f2608da60cccbae61359a8978bded274975381e716dd9dd87ab0b`, expires 2026-11-13. Digest is GitHub artifact metadata; payload bytes were not separately downloaded and re-hashed.
- Status: **PASS — pure replay now starts after cutover snapshot and rejects events outside the recorded completeness watermark. NOT VERIFIED — actual persisted coverage-watermark derivation and daily baseline integration.**
- Limits:
  - The watermark is currently a required caller-supplied scalar; production integration must derive it from verified per-stream/per-ledger coverage rows and prove contiguous VERIFIED intervals. It must not use an arbitrary timestamp or the current wall clock as a substitute.
  - Event source, source_snapshot_id and payload_hash are not yet revalidated by this pure helper against immutable coverage rows. Funding event provenance/coverage membership and exact boundary market mark provenance remain integration requirements.
  - `LEDGER_ADJUSTMENT` is still unsupported by the pure helper; it fails closed rather than being ignored.
  - No baseline insert, replay digest, audit row, or Risk Engine readiness mutation is implemented in this increment.
  - No persistent account DB was opened or migrated.
- Next: design and test a read-only replay input loader that joins cutover snapshots, journal rows, per-ledger EXECUTION coverage, funding coverage/events and exact boundary mark. Derive the effective watermark only from contiguous VERIFIED coverage, reject UNKNOWN/gaps/overlaps/late arrivals, validate event source/hash/snapshot provenance, then pass the proven stream to pure replay. Keep baseline persistence for a separate atomic transaction increment after loader and replay reconciliation tests pass.
- Restrictions unchanged: no persistent account DB migration/opening, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — T1 read-only daily replay input loader

- Scope: implement the read-only data-loading and provenance gate before daily equity replay. This increment does not reconstruct equity or persist a daily baseline.
- RED evidence:
  - Contract first failed because `load_daily_equity_replay_inputs` was absent: run [#42268254288](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42268254288).
  - Added explicit reconstruction-time validation; run [#42269064349](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42269064349) correctly failed because `now_ms` was not yet accepted.
  - Added a clean-transaction boundary contract; run [#42269777299](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42269777299) correctly failed because the loader did not yet reject a caller-owned transaction.
- Implementation:
  - Added `paper_execution/replay_inputs.py`; moved the loader out of `account_history.py` to keep module responsibilities and file size bounded. `account_history.py` is now 736 lines; `replay_inputs.py` is 366 lines.
  - `load_daily_equity_replay_inputs(connection, utc_day_ms, now_ms)` requires an existing SQLite connection, rejects a pre-existing transaction, enables connection-local `PRAGMA query_only=ON`, and begins a read transaction. It performs no inserts, updates, migrations, or baseline writes.
  - Requires applied v4/v5 funding, v6 account-history, v7 cutover-ledger-snapshot and v8 fee-provenance migrations.
  - Requires exactly one account cutover and exactly one immutable snapshot for each of Core, AI and Legacy; validates each snapshot timestamp, numeric state and canonical payload against the stored columns.
  - Requires contiguous VERIFIED execution coverage for each ledger from its cutover snapshot through the half-open UTC boundary. Requires contiguous VERIFIED funding coverage through the same half-open boundary and market-mark coverage including the exact boundary instant.
  - Derives stream-specific watermarks from the persisted coverage rows' `recorded_at_ms`; rejects coverage evidence recorded after caller-supplied `now_ms`.
  - Loads events in deterministic event-time/ID order. Events already reflected in the cutover snapshot are excluded only when recorded no later than the snapshot. Late-arriving pre-snapshot events, events outside verified intervals, and events recorded after their interval watermark fail closed.
  - Funding events must be covered by exactly one VERIFIED interval and must not be marked `LEGACY_UNVERIFIED`. The boundary mark must be unique, VERIFIED, effective and candle-close exactly at 00:00 UTC, observed within 30 minutes after the boundary, and recorded no later than both its coverage watermark and `now_ms`.
  - Validates source/snapshot identifiers, payload-hash format, fee currency and numeric values. External evidence bytes are not fetched or re-hashed by this loader.
  - Added tests for all three ledgers, funding and exact mark loading, coverage gaps, late execution arrival, future-dated evidence, existing caller transaction rejection, query-only write rejection and exact database-byte immutability.
- Exact GREEN source SHA: `33246b418933f3c3780679c7d1f64fcbfd85f9c4`.
- GitHub Actions [#42269875713](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42269875713): SUCCESS on exact checked-out SHA.
  - PAPER-only preflight: PASS.
  - Python compile: PASS.
  - Focused Dual Ledger + migration + replay contract: 74/74 PASS.
  - Full `paper_execution` regression: 173/173 PASS.
  - Job ID: `128071354901`.
  - Artifact ID: `13528483352`, name `dual-ledger-red-evidence-33246b418933f3c3780679c7d1f64fcbfd85f9c4`, GitHub upload digest `sha256:2d1af2a4f631e38c5d4e0d9b65aa4c2f57b576939125c2141cfdabea8ef4108d`, expires 2026-11-13. Digest is GitHub artifact metadata; payload bytes were not separately downloaded and re-hashed.
- Status: **PASS — read-only replay input loading and persisted coverage/provenance gates. NOT VERIFIED — invocation of the pure replay helper from this loader, per-ledger PnL/equity reconciliation, exact boundary mark-to-equity calculation, immutable baseline persistence, audit and risk-state rollover.**
- Limits:
  - The loader returns raw per-ledger snapshots/events, funding events and the exact boundary mark; it does not yet call `replay_ledger_events`.
  - `LEDGER_ADJUSTMENT` remains unsupported and is rejected; no unsupported event is silently ignored.
  - Hash values are syntax-checked and stored provenance fields are cross-checked where canonical snapshot data exists; external source payload bytes are not retrieved, so cryptographic authenticity against external source data is NOT VERIFIED.
  - No persistent account DB was opened or migrated. Tests use temporary SQLite fixtures only.
- Next: add a pure orchestration/reconciliation layer that consumes only this loader output, invokes replay independently for Core/AI/Legacy, handles only explicitly supported adjustment semantics, computes unrealized PnL using the exact boundary mark, and reconciles aggregate equity against the prior verified baseline/cutover. Keep all database writes out of that slice; atomic immutable baseline + audit + risk-readiness transaction remains a separate subsequent increment.
- Restrictions unchanged: no persistent account DB migration/opening, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — T1 pure daily replay orchestration and equity reconciliation

- Scope: consume the read-only daily replay loader output, independently replay Core/AI/Legacy ledgers, calculate unrealized PnL at the exact 00:00 UTC boundary mark, and reconcile the immutable cutover snapshot before producing an in-memory equity result. No database writes or baseline persistence in this increment.
- RED/diagnostic evidence:
  - Contract commit/source SHA `59b0d4ee986de83a6029650ef74fdb3f372d45ca`; run [#42270373157](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42270373157) failed as expected because the orchestration module did not exist.
  - Initial implementation SHA `480d4fb084989c14579d395b57b02796e9f37ecb`; run [#42270542419](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42270542419) exposed 3 failures + 2 errors in test fixtures; full regression was skipped.
  - Fixture corrections committed at `84a1fc8f7a3cee8ed035ba0a3a351cf40d6d64dd`; run [#42270674571](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42270674571) succeeded: focused 82/82, full `paper_execution` 181/181.
- Implementation:
  - Added `paper_execution/replay_reconciliation.py` with pure `reconcile_daily_equity_replay(inputs)`.
  - Replays each ledger independently through existing deterministic `replay_ledger_events`, using the earlier of execution/funding coverage watermarks.
  - Verifies the Core/AI/Legacy ledger set and each cutover snapshot; recomputes cutover realized PnL, unrealized PnL, fees, funding and equity and requires exact match to immutable cutover statement values.
  - Requires boundary mark effective time and candle close exactly at UTC midnight, VERIFIED quality and positive price.
  - Computes per-ledger and aggregate realized/unrealized PnL, fees, funding and equity. Unknown fee currency and unsupported event types remain fail-closed through the replay helper.
  - Added 7 pure contract tests covering aggregate calculations, cutover mismatch, ledger set mismatch, exact mark validation, fee provenance, and input immutability.
  - Added loader-to-orchestrator integration assertion using the actual read-only SQLite loader fixture; expected boundary equity is 100.14 USDT. No DB bytes are changed by this orchestration stage.
- Exact GREEN source SHA: `7b6401b0af56468bdd862410b34b54fc04ae28e0`.
- GitHub Actions [#42271183619](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42271183619): SUCCESS on exact SHA.
  - PAPER-only preflight: PASS.
  - Python compile: PASS.
  - Focused Dual Ledger + migration + replay contracts: 82/82 PASS.
  - Full `paper_execution` regression: 181/181 PASS.
  - Job ID: `128075854414`.
  - Artifact ID: `13529935225`, name `dual-ledger-red-evidence-7b6401b0af56468bdd862410b34b54fc04ae28e0`, GitHub upload digest `sha256:9399c0dc3238bbcfbf5915f5c35673c95a8f3eafb58bf51867c7c2215e4c6ccf`, expires 2026-11-13. Digest is GitHub artifact metadata; payload bytes were not separately downloaded and re-hashed.
- Status: **PASS — pure per-ledger replay orchestration and exact cutover/boundary equity reconciliation on temporary fixtures. NOT VERIFIED — atomic immutable daily baseline + audit persistence, transaction rollback/retry/conflict semantics, daily risk-state rollover, and risk admission integration.**
- Limits:
  - No persistent account DB was opened or migrated; no historical backfill.
  - No daily baseline row or audit record was written.
  - No risk readiness or daily loss baseline was mutated.
  - External source evidence bytes remain un-retrieved; the loader validates stored provenance identifiers/hashes and verified coverage but does not authenticate external payload bytes.
  - `LEDGER_ADJUSTMENT` remains unsupported and is rejected; no amount/sign is guessed.
- Next: implement a separate atomic daily-baseline persistence slice using temporary SQLite only. In one `BEGIN IMMEDIATE` transaction, revalidate cutover, boundary mark and immutable input provenance, insert exactly one immutable baseline and audit record, then update daily risk baseline/readiness only after complete reconciliation. Identical retry must be idempotent; conflicting replay digest must fail without changing prior state; any failure must roll back all writes and keep exposure increases blocked. Do not open or migrate a persistent account DB.
- Restrictions unchanged: no persistent account DB migration/opening, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — T1 atomic UTC daily equity baseline persistence

- Scope: add PAPER-only atomic persistence of a daily equity baseline using the read-only replay loader and pure replay/reconciliation layer. All tests use temporary SQLite fixtures; no persistent account database was opened or migrated.
- RED contract:
  - Added `paper_execution/test_daily_baseline_persistence.py` with tests for atomic baseline+audit+risk-state update, idempotent retry, conflicting digest rejection, rollback on risk-state write failure, immutable baseline/audit rows, and preservation of an already-unready risk state.
  - Initial RED source SHA `3325047822cb1db8f3c5fb2c0565946bb73ea601`; run [#42271964459](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42271964459) correctly failed because `paper_execution.daily_baseline` did not exist.
  - Initial implementation runs exposed only expected migration-list fixture updates and one assertion correction: [#42272294568](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42272294568), [#42272377078](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42272377078), [#42272498742](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42272498742), [#42272628100](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42272628100).
- Implementation:
  - Added migration v9 `daily_equity_baseline_audit_v9` with append-only `paper_daily_equity_baseline_audit`, unique account/day creation event, baseline foreign key, replay digest and canonical audit payload. UPDATE/DELETE are rejected by triggers.
  - Wired v9 into the existing dual-ledger migration sequence. Existing daily baseline table from v6 remains immutable and unique per account/UTC day.
  - Extended `load_daily_equity_replay_inputs` with a private transaction-owned path. Public loader behavior remains query-only and rejects caller-owned transactions; atomic writer uses the same loader after acquiring `BEGIN IMMEDIATE`, so provenance revalidation and writes share one SQLite transaction/snapshot.
  - Added `persist_daily_equity_baseline(connection, utc_day_ms, now_ms, source_sha)`. It validates a clean writable connection, applied schema, complete verified replay inputs and reconciliation; computes canonical SHA-256 digest; inserts baseline and audit; updates only daily baseline fields and version in shared risk state. It does not promote `risk_ready=0` to ready and preserves its reason.
  - Identical retries require matching baseline, audit payload/digest and risk-state fields, then return idempotently without duplicate rows. Existing digest conflict, orphan/mismatched audit, or inconsistent risk state fails closed.
  - All writes occur after `BEGIN IMMEDIATE`; any exception rolls back baseline, audit and risk-state changes together.
- Exact GREEN source SHA: `200208aa90cc19c03aa12e115185334b50d29982`.
- GitHub Actions [#42272772316](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42272772316): SUCCESS on exact SHA.
  - PAPER-only preflight: PASS; external services and DB secrets absent.
  - Python compile: PASS.
  - Focused Dual Ledger + migration + replay + daily baseline contracts: 149/149 PASS.
  - Full `paper_execution` regression: 248/248 PASS.
  - Job ID: `128081328493`.
  - Artifact ID: `13532570066`, name `dual-ledger-red-evidence-200208aa90cc19c03aa12e115185334b50d29982`, GitHub upload digest `sha256:d41b9259e48f724226155c545d393b3f075d0d4b777809976b27bc4b668135b9`, expires 2026-11-13. Digest is GitHub artifact metadata; payload bytes were not separately downloaded and re-hashed.
- Status: **PASS — atomic daily baseline + audit + daily risk baseline persistence on temporary SQLite, including retry/conflict/rollback/immutability tests. NOT VERIFIED — real historical source completeness/authenticity, OS-process crash recovery, and integration with the live risk-admission call path.**
- Limits:
  - No persistent account DB was opened or migrated; v9 migration was exercised only in isolated test databases.
  - No historical backfill, production backtest, exchange connection, deployment, merge, or live order.
  - `risk_ready` is preserved, not promoted by baseline persistence; an existing unready account remains unready.
  - The transaction revalidates database-stored provenance and coverage but does not fetch external source evidence bytes to authenticate external payload hashes.
  - `LEDGER_ADJUSTMENT` remains unsupported and rejected.
- Next: add tests and integration proving the daily baseline is consumed by the shared risk snapshot/admission path: day mismatch or missing baseline blocks exposure increases; verified baseline enables the normal risk evaluation without bypassing Kill Switch, funding, mark freshness, HWM, drawdown or exposure limits. Keep exposure increases fail-closed and use temporary SQLite only. Process-kill/reopen recovery and persistent DB migration remain separate approvals.
- Restrictions unchanged: no persistent account DB migration/opening, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — T1 daily baseline to shared risk snapshot integration

- Follow-up RED exposed a real integration gap after baseline persistence: the daily baseline row/day was updated, but shared risk state still carried the cutover mark timestamp, so `read_account_risk_snapshot` correctly rejected it as stale.
  - RED source SHA `43466302d2745f084feff7b3d3a9e409dc1c9928`; run [#42273307132](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42273307132) failed on `ACCOUNT_RISK_MARK_STALE_OR_INVALID`.
- Fixed atomic risk-state update to persist the exact verified boundary mark's price, observation time, candle close and dataset version, plus replayed boundary equity and daily baseline in the same transaction.
  - Lifetime HWM advances to `max(previous HWM,boundary equity)` only when existing `risk_ready=1`; if already unready, HWM remains frozen. Existing `risk_ready` and `unavailable_reason` are never promoted/cleared by this operation.
  - Extended fixture funding coverage through the boundary mark's observation timestamp so the normal shared risk validator can verify funding completeness at the same mark.
  - Added integration test proving `read_account_risk_snapshot` accepts the newly persisted boundary state and reports the expected UTC baseline/equity/mark. Existing test proves an unready account stays unready.
- Exact GREEN source SHA: `1926093af139a03cac0f60fad355096cbc671177`.
- GitHub Actions [#42273445520](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42273445520): SUCCESS on exact SHA.
  - PAPER-only preflight: PASS.
  - Python compile: PASS.
  - Focused contracts: 150/150 PASS.
  - Full `paper_execution` regression: 249/249 PASS.
  - Job ID: `128083624466`.
  - Artifact ID: `13532270921`, name `dual-ledger-red-evidence-1926093af139a03cac0f60fad355096cbc671177`, GitHub upload digest `sha256:c6f145d0ef90bc9b89325fa6642b34787564539c6d98a3a02c2e2bb2e378da6e`, expires 2026-11-13. Digest is GitHub artifact metadata; payload bytes were not separately downloaded and re-hashed.
- Status: **PASS — persisted UTC baseline is consumed by the shared read-only risk snapshot at the exact boundary mark. NOT VERIFIED — direct exposure-admission behavior after rollover.**
- Next: add tests around the actual Core/AI `submit` path: verified current-day baseline + fresh boundary mark permits only normal risk evaluation; missing/wrong-day baseline, stale mark, funding gap, Kill Switch and limit breaches block exposure increases; reductions remain permitted. No bypass of shared Risk Engine. Temporary SQLite only.
- Restrictions unchanged: no persistent account DB migration/opening, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — T1 daily baseline shared-risk exposure admission verification

- Scope: verify actual Core and AI `PaperLedger.submit` admission paths after daily UTC baseline persistence; no risk-engine bypass or execution logic changes.
- Added temporary-SQLite integration tests:
  - With verified current-day baseline and fresh boundary mark, Core LONG and AI SHORT both pass the normal shared risk checks and fill independently.
  - Wrong UTC baseline day blocks a new Core exposure with `RISK_INPUTS_STALE_OR_CORRUPT`.
  - Stale boundary mark blocks a new AI exposure with `RISK_INPUTS_STALE_OR_CORRUPT`.
  - Existing Core position can EXIT/reduce when daily baseline becomes unavailable; exposure reduction is not blocked by the baseline gate.
- Exact tested source SHA: `ca8a658db81d343345855b790f71787ba6e130d2`.
- GitHub Actions [#42273745481](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42273745481): SUCCESS on exact SHA.
  - PAPER-only preflight: PASS.
  - Python compile: PASS.
  - Focused contracts: 154/154 PASS.
  - Full `paper_execution` regression: 253/253 PASS.
  - Job ID: `128084644700`.
  - Artifact ID: `13532671086`, name `dual-ledger-red-evidence-ca8a658db81d343345855b790f71787ba6e130d2`, GitHub upload digest `sha256:22d3a3cf0cb26e251867e3eee51dbd0e10ff540c0311f71b9cf93eecdbf29bf6`, expires 2026-11-13. Digest is GitHub artifact metadata; payload bytes were not separately downloaded and re-hashed.
- Status: **PASS — Core/AI exposure admission consumes the verified current UTC baseline; wrong-day/stale mark gates block increases, and valid reductions remain permitted. NOT VERIFIED — all post-rollover kill-switch/funding-gap/limit combinations in the same integrated fixture and OS-process crash recovery.**
- Next: add post-rollover regression cases for missing baseline, funding coverage ending before the boundary mark's observation, Kill Switch, and max exposure/daily loss limits; verify no path bypasses shared risk checks. Then perform process-kill/reopen recovery testing against temporary SQLite. Do not use persistent account DB.
- Restrictions unchanged: no persistent account DB migration/opening, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — T1 post-rollover funding, Kill Switch and risk-limit admission gates

- Scope: expand actual Core/AI PAPER submit-path verification after a reconstructed daily baseline. No production risk logic changes in this increment.
- Added integration coverage:
  - Missing daily baseline blocks exposure increases.
  - Funding coverage that reaches 00:00 UTC but ends before the exact boundary mark's later observation blocks exposure with `RISK_INPUTS_UNAVAILABLE`; baseline existence does not bypass funding provenance.
  - Kill Switch remains effective after rollover and rejects new exposure with `KILL_SWITCH`.
  - Daily loss threshold still latches Kill Switch and rejects new exposure with `DAILY_LOSS_LIMIT`.
  - Max gross exposure limit remains enforced with `MAX_EXPOSURE_LIMIT`.
  - Prior tests in the same suite cover Core/AI admission with verified current-day baseline, wrong-day/stale-mark rejection, and reduction/EXIT while baseline is unavailable.
- One initial test run exposed a fixture issue, not a source defect: the daily-loss test advanced the mark observation one millisecond beyond the funding coverage watermark, so the expected funding fail-closed guard fired first. The fixture now keeps the mark observation within the verified funding watermark and tests the daily-loss branch independently.
- Exact GREEN source SHA: `63cfb98718fe65c4a82b3e8486c0cc24cc99c16c`.
- GitHub Actions [#42274238857](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42274238857): SUCCESS on exact SHA.
  - PAPER-only preflight: PASS.
  - Python compile: PASS.
  - Focused contracts: 159/159 PASS.
  - Full `paper_execution` regression: 258/258 PASS.
  - Job ID: `128086325865`.
  - Artifact ID: `13532736629`, name `dual-ledger-red-evidence-63cfb98718fe65c4a82b3e8486c0cc24cc99c16c`, GitHub upload digest `sha256:288debd3ae4d7723637e2a6668f09502f485287b19af6e106e3886cece332136`, expires 2026-11-13. Digest is GitHub artifact metadata; payload bytes were not separately downloaded and re-hashed.
- Status: **PASS — post-rollover missing-baseline, funding-watermark, Kill Switch, daily-loss and max-exposure gates verified through Core/AI submit path; reductions remain allowed under baseline unavailability. NOT VERIFIED — OS-process crash recovery after baseline transaction and recovery audit reconciliation.**
- Next: implement an OS-process-kill/reopen test around baseline persistence using temporary SQLite only. Verify crash before commit leaves no baseline/audit/risk update; crash after commit leaves all three durable and identical retry is idempotent. Reopen in a fresh process and verify read-only risk snapshot and submit gate. Do not open/migrate persistent account DB.
- Restrictions unchanged: no persistent account DB migration/opening, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — T1 daily baseline OS-process crash/reopen recovery

- Scope: verify SQLite transaction recovery when the process is terminated around the daily baseline commit, using only temporary SQLite databases.
- Added subprocess crash tests that invoke the actual `persist_daily_equity_baseline` implementation:
  - **Crash before commit:** a SQLite trigger invokes `os._exit(73)` during the risk-state UPDATE, after baseline and audit INSERTs but before transaction commit. A fresh parent connection reopens the database and verifies baseline count=0, audit count=0, and prior daily risk baseline/readiness unchanged. SQLite recovered the uncommitted transaction without partial state.
  - **Crash after commit:** child process runs the writer to successful commit and immediately exits via `os._exit(74)`. Parent process reopens the DB and verifies baseline, matching audit digest and daily risk state are all durable; read-only shared risk snapshot is ready; retry returns idempotent without duplicate rows.
- Exact GREEN source SHA: `02809a4e92e245f4fbb701aaea2eee57c3c40a13`.
- GitHub Actions [#42274539759](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42274539759): SUCCESS on exact SHA.
  - PAPER-only preflight: PASS.
  - Python compile: PASS.
  - Focused contracts: 161/161 PASS.
  - Full `paper_execution` regression: 260/260 PASS.
  - Job ID: `128087359791`.
  - Artifact ID: `13532062055`, name `dual-ledger-red-evidence-02809a4e92e245f4fbb701aaea2eee57c3c40a13`, GitHub upload digest `sha256:9d76e6e059f5ab38fc3cc56a2e400fd232f6f3b6bed80bd79387dfd6867ce5f8`, expires 2026-11-13. Digest is GitHub artifact metadata; payload bytes were not separately downloaded and re-hashed.
- Status: **PASS — OS-process termination before/after commit recovers atomically on temporary SQLite; fresh-process reopen, risk snapshot and retry verified. NOT VERIFIED — crash/power-loss behavior on production storage/filesystem and persistent account DB.**
- Next: review baseline persistence and migration v9 implementation for security/consistency edge cases, especially migration upgrade safety, audit/baseline row cross-integrity, replay digest canonicalization and risk-state reconciliation. Add regression tests for any findings. Persistent account DB migration remains prohibited.
- Restrictions unchanged: no persistent account DB migration/opening, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — T1 daily baseline persistence integrity review

- Scope: five-axis review of migration v9 and atomic baseline persistence, focused on schema tampering, idempotent row reconciliation and malformed risk-state inputs.
- Review findings addressed:
  - Writer previously trusted the migration marker without independently verifying immutable baseline/audit triggers. It now checks both tables, required columns, all four UPDATE/DELETE immutability triggers, and the unique account/day constraints before loading replay inputs or writing.
  - Idempotent replay now validates stored baseline source SHA and recorded timestamp, and requires the audit record timestamp to match the baseline row as well as the exact canonical payload/digest.
  - Risk-state parsing now rejects missing/non-string/oversized/non-finite/non-positive HWM and invalid version/readiness shape before writes; failures remain inside the transaction and roll back.
- Added tests prove missing audit trigger, missing baseline trigger and invalid HWM all fail closed without partial baseline/audit writes.
- Exact GREEN source SHA: `b4ae4f0d065386fd88ac2eb8473e88b1ff7f8120`.
- GitHub Actions [#42275056694](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42275056694): SUCCESS on exact SHA.
  - PAPER-only preflight: PASS.
  - Python compile: PASS.
  - Focused contracts: 164/164 PASS.
  - Full `paper_execution` regression: 263/263 PASS.
  - Job ID: `128089132770`.
  - Artifact ID: `13532802332`, name `dual-ledger-red-evidence-b4ae4f0d065386fd88ac2eb8473e88b1ff7f8120`, GitHub upload digest `sha256:1682fe45ffcdb00b11ee568ed423656ab1f0e0b40d5dc0d0310356e5afb40317`, expires 2026-11-13. Digest is GitHub artifact metadata; payload bytes were not separately downloaded and re-hashed.
- Status: **PASS — runtime schema-integrity checks, immutable row guards, canonical replay/audit reconciliation and malformed HWM fail-closed behavior verified on temporary SQLite. NOT VERIFIED — persistent database upgrade, external source payload authenticity, or production filesystem durability.**
- Next: review daily baseline recovery semantics across UTC-day sequencing and repeated/missed days. Confirm the writer cannot skip an unverified prior UTC day, overwrite an existing day, or advance the daily risk baseline from incomplete coverage. Add tests for gaps/multi-day recovery; do not backfill historical baselines without explicit approval.
- Restrictions unchanged: no persistent account DB migration/opening, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.

## 2026-11-07 — T1 sequential UTC baseline recovery and prior-day retry

- Scope: verify consecutive daily baseline creation, predecessor enforcement, and idempotent retry of an earlier day after the account has advanced to a later UTC day. Temporary SQLite only.
- Initial RED/diagnostic run at source SHA `bd0c83667783be6b4b048a432907418f704940f9`, workflow [#42276046612](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42276046612): compile and PAPER-only preflight PASS; focused contract failed one test because the test retried the first day's baseline using the first day's old `now_ms`, while the risk state had already advanced to the next day. This was an invalid recovery-time fixture, not evidence of a production logic defect.
- Corrected the retry test to use the current recovery timestamp (`next_recorded`) while retrying the original UTC day. No runtime implementation change in this increment.
- Exact GREEN source SHA: `e06b28b740590b99c4c930004bf547c8fccbaf99`.
- GitHub Actions [#42276535949](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42276535949): SUCCESS on exact SHA.
  - PAPER-only preflight: PASS; external DB/API credentials empty.
  - Python compile: PASS.
  - Focused Dual Ledger + migration + replay + daily baseline contracts: 167/167 PASS.
  - Full `paper_execution` regression: 266/266 PASS.
  - Job ID: `128094176814`.
  - Artifact ID: `13533163461`, name `dual-ledger-red-evidence-e06b28b740590b99c4c930004bf547c8fccbaf99`, GitHub upload digest `sha256:62557812142e7aa84aa238c4c6a4dd99a851c9116beeeca2dd1a1893abc0f88e`, expires 2026-11-13. Digest is GitHub artifact metadata; payload bytes were not separately downloaded and re-hashed.
- Status: **PASS — sequential baseline creation after verified predecessor, rejection of missing predecessor/day gaps, and idempotent retry of an older baseline at current recovery time. NOT VERIFIED — arbitrary multi-day outage reconciliation/backfill policy and audit payload semantic cross-check against baseline columns.**
- Next: review and test semantic integrity of persisted audit payload: replay equity, mark ID, cutover ID, UTC day and algorithm version must agree with immutable baseline row and risk state; tampered-but-canonical audit payload must fail closed. No automatic backfill of missing days.
- Restrictions unchanged: no persistent account DB migration/opening, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.

## 2026-11-07 — Daily baseline audit semantic integrity

- Scope: validate persisted daily baseline audit payload against immutable baseline columns, beyond canonical JSON and matching payload digest. PAPER-only; temporary SQLite tests.
- RED evidence: source SHA `4560944c0aad7a7af86f652e50651b2507ea6d03`, workflow [#42276682387](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42276682387): compile and PAPER-only preflight PASS; focused suite found one failure — a canonical audit payload with recomputed matching digest but a replay equity different from the immutable baseline was accepted. Full regression skipped.
- Runtime fix: `_validate_persisted_baseline` now cross-checks audit payload replay equity against `baseline_equity_quote`, market mark identity against `mark_id`, UTC day against the baseline key, and cutover/algorithm identity. It still requires canonical serialization and matching SHA-256 digest.
- Exact GREEN implementation source SHA: `912859af4160e3281e46564805e7f0483b488b9b`; workflow [#42276817521](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42276817521), SUCCESS. PAPER-only preflight PASS; compile PASS; focused contracts 168/168 PASS; full `paper_execution` 267/267 PASS. Job `128095135887`. Artifact `13532239394`, digest `sha256:7e77b3aacee459c9bf959b735e393c5ba3752fe6abaff3aa12237bb1839e0779`, expires 2026-11-13.
- Additional exact GREEN test source SHA: `c17fe13802d6182f13ecfce586d781a270dbfbb3`; workflow [#42276840973](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42276840973), SUCCESS. PAPER-only preflight PASS; compile PASS; focused contracts 168/168 PASS; full `paper_execution` 267/267 PASS. Job `128095348856`. Artifact `13532044881`, digest `sha256:0af08f446eba458a4e16096822df309f1d9321e7dbb6dbb7c7cb8b73b40849bf`, expires 2026-11-13. This run also covers a canonical payload with a recomputed digest but forged market-mark identity.
- Status: **PASS — baseline audit replay equity and mark identity are cross-checked against immutable baseline fields; canonical-but-tampered payloads tested fail closed. NOT VERIFIED — external source bytes authenticity, full risk-state semantic cross-check on all historical replay fields, and production filesystem crash durability.**
- Next: audit the complete baseline-to-risk-state invariant, including mark price/time/dataset version, daily UTC key/equity, risk version, and HWM behavior; test corruption and interrupted transaction recovery. No automatic backfill.
- Restrictions unchanged: no persistent account DB migration/opening, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.

## 2026-11-07 — T1 Daily Baseline to Risk State integrity

- Scope: bind the immutable daily baseline audit to the exact risk-state version committed in the same SQLite transaction; verify later idempotent retries cannot accept state rollback or tampering. Temporary SQLite only.
- RED evidence:
  - Source SHA `e3b619d1af978f2593b51bbfc0b1eaee39bb2ec5`, workflow [#42277186899](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42277186899): a changed `last_mark_price` with no matching baseline audit was accepted.
  - Source SHA `9a631bb55b7d8fc2ada6aee210a1fc7bb474433d`, workflow [#42277463193](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42277463193): a rollback of the account risk-state version was accepted.
- Implementation: audit payload schema v2 now stores the committed risk-state snapshot: daily UTC day/equity, last equity, mark price/observed time/candle close/dataset version, HWM, readiness, update timestamp and incremented risk-state version. Audit validator checks these values against baseline/replay/mark columns. Retry/predecessor validation requires risk version and HWM to be monotonic; if the current version still equals the baseline commit version, all captured risk-state fields must match exactly. Later legitimate risk refreshes may advance the version and update mark/equity while preserving the daily baseline, but may not roll back HWM or version.
- Additional tests cover mark price/time/candle/dataset mismatches, daily baseline day/equity corruption, risk version rollback, HWM rollback, and preservation of HWM plus exactly one version increment when the account is already unready. Idempotent retry must not increment the version again.
- Intermediate implementation diagnostics:
  - SHA `fa5c45b3ec2f04de0087e0022728fb3fb07bfbeb`, run [#42277621107](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42277621107): expected refactor regression due idempotent result referencing a removed local digest; corrected in next source.
  - SHA `4a4d3692b75c6d5f5edb8b1419107b1997ed8a33`, run [#42277650441](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42277650441): existing malformed-digest conflict fixture was rejected earlier as unverified; restored explicit invalid-digest conflict classification.
- Exact GREEN source SHA: `7cddb5eacfd70f5bc886bc03f672177cdf3f8f2a`; GitHub Actions [#42277853667](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42277853667), SUCCESS.
  - PAPER-only preflight: PASS.
  - Python compile: PASS.
  - Focused Dual Ledger + migration + replay + daily baseline contracts: 173/173 PASS.
  - Full `paper_execution` regression: 272/272 PASS.
  - Artifact ID `13533807345`, name `dual-ledger-red-evidence-7cddb5eacfd70f5bc886bc03f672177cdf3f8f2a`, GitHub upload digest `sha256:fb41913d0826f836adf7b6c460efc6bd3d41f6af41f5e976764cc099c00376c9`, expires 2026-11-13. Digest is GitHub artifact metadata; payload bytes were not separately downloaded/re-hashed.
- Status: **PASS — baseline/risk-state audit binding, mark metadata integrity, daily baseline key/equity integrity, risk version monotonicity, HWM monotonicity, unready HWM preservation, and idempotent retry are verified on temporary SQLite. NOT VERIFIED — external source payload byte authenticity, power-loss behavior on production storage, and persistent account DB migration.**
- Next: review audit schema v2 compatibility and recovery policy for pre-existing v1 daily baseline rows. Keep any legacy row without risk-state snapshot fail-closed; define an explicit evidence-based reconciliation path rather than silently synthesizing missing version/HWM history. Then inspect complete transaction crash/reopen coverage against this updated payload shape.
- Restrictions unchanged: no persistent account DB migration/opening, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.

## 2026-11-07 — Daily baseline audit v1 fail-closed compatibility and restart recovery

- Scope: validate that legacy audit payloads without the v2 Risk State snapshot cannot be treated as risk-ready or used for exposure admission; preserve current v2 atomic recovery semantics. Tests use temporary SQLite only.
- RED evidence:
  - Contract source SHA `de4af903634b09f99a038ac2312a7990ef79e24b`, workflow [#42278257817](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42278257817): 2 expected failures exposed the defect. A v1-shaped audit row still allowed `read_account_risk_snapshot` (no DatabaseError), and a Core exposure order was FILLED instead of rejected.
- Runtime fix source SHA `6847b658bace8849019e9f342d9318119eba0ce4`, workflow [#42278399537](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42278399537), SUCCESS. Added a v2 baseline-audit validator to read-only risk snapshot and to the shared order-admission path for days after the original account cutover day. It verifies the immutable baseline/audit payload, risk-state snapshot, version/HWM monotonicity, mark metadata and cutover identity. Invalid/legacy v1 audit blocks exposure increases with `RISK_INPUTS_STALE_OR_CORRUPT`; valid reductions remain governed by existing reduction path. Cutover-day initial baseline remains supported without a daily baseline audit row.
- Tightened test assertion to require the exact fail-closed reason. Exact GREEN source SHA `54fee9b3f62c4106feef899906c030fae4f4e2b2`; workflow [#42278503472](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42278503472), SUCCESS.
  - PAPER-only preflight: PASS.
  - Python compile: PASS.
  - Focused Dual Ledger + migration + replay + daily baseline contracts: 175/175 PASS.
  - Full `paper_execution` regression: 274/274 PASS.
  - Existing OS-process-kill-before-commit rollback and process-kill-after-commit reopen/retry tests passed in the full regression against audit schema v2.
  - Artifact ID `13535080519`, name `dual-ledger-red-evidence-54fee9b3f62c4106feef899906c030fae4f4e2b2`, GitHub upload digest `sha256:1de0a3fff8b42d4e66b3b40fd1928b8d02fadf969feae0fe925f865137a9294c`, expires 2026-11-13. Digest is GitHub artifact metadata; payload bytes were not separately downloaded/re-hashed.
- Status: **PASS — v1-shaped audit cannot pass the read-only account risk snapshot or admit new exposure; exact rejection reason verified. v2 crash-before-commit rollback, crash-after-commit consistency and idempotent retry regression PASS. NOT VERIFIED — a safe historical v1→v2 reconciliation procedure based on independently retained source evidence; external source payload authenticity; production filesystem/power-loss durability.**
- Compatibility decision: do not auto-upgrade, infer, synthesize, or backfill missing v1 Risk State fields (especially HWM, risk version, readiness and mark provenance). Such rows remain fail-closed. Any future v1 recovery must be a separately approved, evidence-backed reconciliation that validates the original cutover, complete event/funding/mark coverage, source snapshots and historical risk state; if any field cannot be independently proven, preserve the v1 row as unresolved and block increases. No migration/backfill is authorized by this work.
- Next: write a read-only v1 recovery evidence contract/checklist and tests for evidence completeness vs missing/contradictory evidence. Keep any conversion/migration/backfill out of scope pending separate approval.
- Restrictions unchanged: no persistent account DB migration/opening, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.

## 2026-11-07 — Read-only v1 baseline recovery evidence contract

- Scope: define a pure, read-only manifest assessor for possible historical v1 baseline recovery. It does not open SQLite, write rows, update risk state, synthesize missing history, or authorize migration.
- Contract tests added in `paper_execution/test_daily_baseline_v1_recovery.py`; workflow now explicitly compiles `daily_baseline_v1_recovery.py` and runs the new test module.
- Assessor: `paper_execution/daily_baseline_v1_recovery.py::assess_daily_baseline_v1_recovery_manifest`.
  - Returns only `BLOCKED` or `ELIGIBLE_FOR_MANUAL_REVIEW`.
  - Requires immutable baseline/audit identity and matching digest/equity/mark/cutover/algorithm; verified immutable cutover and Core/AI/Legacy cutover snapshots; continuous VERIFIED execution and funding intervals from cutover to exact half-open UTC boundary; complete event provenance, explicit USDT fees, no late events, no unknown funding; exact verified boundary mark with dataset/source/hash evidence; independently verified historical risk state with UTC day/equity/HWM/version/readiness/mark and source/hash evidence.
  - Reports missing evidence paths separately from semantic contradictions. Rejects malformed types and non-finite/non-positive amounts rather than coercing values.
  - Always returns `migration_authorized=false`, `automatic_upgrade_authorized=false`, and `mutation_performed=false`, including when eligible for manual review.
- Contract tests cover complete evidence (manual-review eligibility only), missing execution/funding/raw-byte proof, missing Legacy cutover snapshot, mismatched equity/mark/cutover, HWM/version/day/mark conflicts, malformed types/NaN, and input immutability.
- A test fixture initially used a timestamp that was not a UTC day boundary; corrected to an aligned boundary before GREEN.
- Exact GREEN source SHA: `40787c9735afe1f80d84dc6b152a0a45b10a5c6b`; workflow [#42279016838](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42279016838), SUCCESS. PAPER-only preflight PASS; compile PASS; focused contracts 182/182 PASS; full `paper_execution` 281/281 PASS. Artifact `13533384001`, digest `sha256:12e0006051820ad5c0318b6e97fa5b9296697f08c25e4b67ba440d622953be58`, expires 2026-11-13.
- Exact final CI configuration/source SHA: `fbf74c5d72ee977651b8075f13dadf9763b4b272`; workflow [#42279162334](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42279162334), SUCCESS. PAPER-only preflight PASS; explicit compile includes assessor module; focused contracts 182/182 PASS; full `paper_execution` 281/281 PASS. Artifact `13534541826`, digest `sha256:ac769ba03c657a4361d72eef3f794ac005cada4108395fc85e4719d6f1ea1ff0`, expires 2026-11-13. GitHub artifact digests are upload metadata; payload bytes were not separately downloaded/re-hashed.
- Evidence contract document: `docs/architecture/DAILY_BASELINE_V1_RECOVERY_EVIDENCE_CONTRACT_2026-11-07.md`.
- Status: **PASS — read-only evidence completeness/contradiction assessor and tests. ELIGIBLE_FOR_MANUAL_REVIEW is not migration-ready and does not permit readiness promotion. NOT VERIFIED — actual historical v1 evidence availability/authenticity and any future controlled migration.**
- Next: assess whether the actual retained repository schema and audit sources can populate this manifest without assumptions. Produce a read-only inventory only; if a required historical risk snapshot (especially HWM/version/readiness) or raw source bytes do not exist, report BLOCKED and preserve v1 rows unchanged. No automatic backfill or migration.
- Restrictions unchanged: no persistent account DB opening/migration, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.

## 2026-11-07 — Repository-only inventory for legacy v1 recovery

- Scope: read-only inspection of the current branch's T1 schema and source paths to determine whether a v1 daily baseline can be populated into the v2 recovery manifest without assumptions. No persistent account DB was opened; no real rows were inspected or modified.
- Exact source files reviewed:
  - `paper_execution/account_history.py`: `6163065798b2386e1c466650048e40b7eab0d2eb`
  - `paper_execution/ledger.py`: `0bc94ae0e704a69e253246a575991c1de436e0a4`
  - `paper_execution/funding.py`: `575758eb3223b4341ac37bad56d58e52539305c0`
  - `paper_execution/equity.py`: `40d6566294355c646839614c92f8fba6116b582c`
  - `paper_execution/risk_control.py`: `3c76e462b0b4d924c2418842d95ed74285e2315d`
- Confirmed immutable evidence sources: v6 append-only event journal, per-stream coverage and market marks; v7 immutable Core/AI/Legacy cutover snapshots; v4 funding event/coverage provenance; v5 immutable account cutover; v9 immutable daily baseline and audit rows.
- Critical gap: `paper_account_risk_state` is one mutable current-state row. No immutable risk-state history table or per-version snapshot was found. The v7 snapshots and v5 HWM/readiness are cutover-only, not snapshots at later daily baseline timestamps. Updates increment version and change HWM/readiness but do not append immutable before/after risk-state snapshots.
- Other limits: `paper_audit` has no immutable UPDATE/DELETE triggers; `paper_orders` contains mutable aggregate order/fill state; legacy `paper_equity_history` / `paper_daily_baselines` are single-strategy and not immutable; pre-v8 fee currency can remain NULL/unknown; stored payload hash syntax does not prove original source bytes were rehashed.
- Exact report: `docs/evidence/DAILY_BASELINE_V1_RECOVERY_EVIDENCE_INVENTORY_2026-11-07.md` (commit `ec638efd7e3aa3d8ca68f868b5ea38337151fe5d`).
- Status: **BLOCKED — repository schema/code alone cannot independently populate the historical v1 risk-state snapshot (especially HWM/version/readiness) or attest original external payload bytes. This is not a statement about actual persistent DB rows, which were not opened. Do not set manifest attestations to true without independently retained evidence.**
- Safe outcome: keep v1 rows immutable and fail-closed. Do not synthesize HWM/version/readiness, fee currency, missing events or source-byte authenticity. If independently retained external evidence is later supplied, manifest assessment can only qualify it for manual review; it cannot authorize migration.
- Next: add a regression proving a v1 baseline retry cannot silently rewrite/upgrade its audit payload or mutate risk state. Then leave historical recovery BLOCKED unless independent evidence is actually available. No automatic backfill.
- Restrictions unchanged: no persistent account DB opening/migration, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.

## 2026-11-07 — v1 baseline retry cannot silently upgrade immutable audit

- Added `test_v1_baseline_retry_never_upgrades_audit_or_changes_risk_state`. The fixture constructs a canonical v1-shaped audit payload with a matching recomputed digest, restores the immutable schema triggers, then retries the writer. It asserts the writer fails with `DAILY_BASELINE_PREVIOUS_BASELINE_UNVERIFIED` and baseline audit digest/payload plus daily risk day/equity/HWM/readiness/version remain unchanged.
- First RED attempt at source `ab26a31c0140ba7880fb22067991450b7bae50b6`, workflow [#42279619974](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42279619974), showed the test fixture had dropped immutable UPDATE triggers and therefore correctly failed earlier at schema integrity. The fixture now recreates those triggers before exercising the writer.
- Exact GREEN source SHA: `4eac10b704882c7f14901400be9d76465b0ffc44`; workflow [#42279706472](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42279706472), SUCCESS. PAPER-only preflight PASS; Python compile PASS; focused contracts 183/183 PASS; full `paper_execution` 282/282 PASS. Artifact ID `13534577603`, name `dual-ledger-red-evidence-4eac10b704882c7f14901400be9d76465b0ffc44`, GitHub upload digest `sha256:f098522daedc72098025bf1cdd43efb4315e68f8613cfe0a10ce3865fe09955e`, expires 2026-11-13. Digest is GitHub artifact metadata; payload bytes were not separately downloaded/re-hashed.
- Status: **PASS — v1 audit retry is rejected and the stored baseline/audit/risk-state values remain unchanged; no silent v1-to-v2 rewrite. Combined with v1 snapshot/admission fail-closed checks and v2 process-kill/reopen tests, compatibility handling is fail-closed.**
- Historical recovery remains **BLOCKED** by the repository-only inventory: no independently retained historical risk-state snapshot at later baseline timestamps was found; mutable current risk row and cutover-only snapshot cannot prove old HWM/version/readiness. External source-byte authenticity is also NOT VERIFIED.
- Next: keep v1 rows unresolved and fail-closed. Do not start any migration/backfill. The next meaningful path requires independent historical risk-state evidence from outside the inspected schema; if none exists, close v1 recovery as permanently unrecoverable from current retained evidence and continue with forward-only v2 baselines.
- Restrictions unchanged: no persistent account DB opening/migration, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.

## 2026-11-07 — Unresolved v1 predecessor blocks next UTC baseline

- Scope: regression-only verification that a historical v1 daily baseline cannot be bypassed by requesting the following UTC day's v2 baseline. No production code change; no database migration or backfill.
- Added `test_v1_predecessor_blocks_next_utc_day_without_state_mutation` to `paper_execution/test_daily_baseline_persistence.py`.
  - Creates a v2 baseline in a temporary SQLite fixture, converts its audit to a canonical v1-shaped payload, and restores the immutable schema triggers.
  - Attempts to persist the next UTC day's baseline.
  - Expects `DAILY_BASELINE_PREVIOUS_BASELINE_UNVERIFIED` from predecessor validation before loading next-day replay inputs.
  - Confirms baseline row count and audit row count remain exactly one, and the prior baseline/audit payload/digest plus daily risk day/equity/HWM/readiness/version remain byte/value-identical.
- Exact source SHA: `f7df95c2ff2008aa88923b3242b1486c096d9342`.
- GitHub Actions [#42280083080](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42280083080), SUCCESS on exact SHA. PAPER-only preflight PASS; Python compile PASS; focused contracts 184/184 PASS; full `paper_execution` regression 283/283 PASS. Artifact ID `13533829670`, name `dual-ledger-red-evidence-f7df95c2ff2008aa88923b3242b1486c096d9342`, GitHub upload digest `sha256:518596b09e16712d2c5ed157baa85168fd6c960ffbf5a7414ee9d6d547195275`, expires 2026-11-13. Digest is GitHub artifact metadata; payload bytes were not separately downloaded/re-hashed.
- Status: **PASS — v1 cannot be bypassed by UTC rollover; no next-day baseline or risk-state mutation occurs. This confirms forward-only v2 progression is blocked behind an unresolved v1 predecessor under the current chain policy.**
- Operational consequence: do not describe this as a working forward-only migration path. Before new daily baselines can resume, a separately approved recovery/re-anchor design is required; it must not fabricate historical HWM/version/readiness or rewrite v1 rows. Current schema has one immutable cutover and no independent historical risk-state snapshots after cutover, so no such re-anchor is implemented or authorized here.
- Next: architecture-only decision on whether to preserve the strict predecessor chain indefinitely or define a separately audited, evidence-backed new baseline epoch using an independently verified current account statement and fresh market/funding provenance. Any new epoch must explicitly define HWM/daily-loss semantics and be separately approved before source or persistent DB changes.
- Restrictions unchanged: no persistent account DB opening/migration, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.

## 2026-11-07 — Architecture-only proposal for a new Daily Baseline Epoch

- Scope: read-only review of current baseline writer/schema constraints and a proposal for a separately identified risk-measurement epoch. No Python source, tests, workflow, schema, or persistent database was changed/opened.
- Confirmed current design constraints from source:
  - Baseline chain requires the immediately previous UTC-day baseline to validate before creating the next.
  - A v1 audit without `riskState` is rejected by predecessor validation.
  - Current daily baseline uniqueness is `(account_id, utc_day_ms)`; baseline records reference the original account cutover.
  - Account risk state is mutable; no independently retained immutable per-day HWM/version/readiness history was found in repository schema.
- Architecture decision document: `docs/architecture/DAILY_BASELINE_EPOCH_REANCHOR_DECISION_2026-11-07.md`, commit `2af630b861ac612e0fa771a4e60fe6a1f4dfe4d4`.
- Options evaluated:
  - A: retain strict predecessor chain and keep account blocked indefinitely. This remains the current operational default and safest option absent independent evidence.
  - B: create a separately identified immutable epoch from a complete independently verified account/position/order/fee/funding/mark anchor. This is only a future proposal, not implemented or approved.
- Proposed semantics, if separately approved: anchor exactly at 00:00 UTC; new epoch HWM and first daily-loss baseline start at independently verified opening equity; explicitly label the new reference period and disclose historical drawdown continuity is unavailable. Do not claim the new HWM reconstructs old history.
- Proposed schema direction: immutable epoch record, immutable Core/AI/Legacy anchor snapshots, epoch-aware daily baseline identity, active epoch pointer in risk state, append-only transition audit. Existing v1/v2 rows remain unchanged. Exact migration/FK design still requires separate review.
- Minimum evidence includes authoritative account statement; complete Core/AI/Legacy positions; open orders/reservations; explicit fee and funding provenance/coverage; exact-boundary market mark; reconciliation report; explicit policy approval for HWM reset. Balance screenshot alone is insufficient.
- Status: **PASS — architecture options and evidence requirements documented. NOT VERIFIED — availability/authenticity of external account/position/order/funding/fee evidence; no epoch implementation or activation.**
- Recommendation: preserve Option A now. Consider Option B only after external evidence is independently available and a separate approval is granted. If no complete anchor can be obtained, keep risk increases blocked.
- Next: no source implementation until the user explicitly approves the new-epoch policy and supplies/identifies an authoritative anchor source. First technical follow-up, if approved, is a schema-only design review with migration compatibility proof; persistent DB access remains separately gated.
- Restrictions unchanged: no persistent account DB opening/migration, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.

## 2026-11-07 — Additive schema compatibility review for proposed Baseline Epoch

- Scope: architecture/schema review only, based on current source definitions for migrations v6-v9 and the existing daily baseline writer. No Python source, migration, tests, workflow, or database was changed/opened.
- Confirmed compatibility constraints:
  - v6 creates the daily baseline table with unique `(account_id, utc_day_ms)` and a foreign key to the original account cutover.
  - v7 adds immutable per-ledger cutover snapshots.
  - v8 adds explicit fee-currency provenance.
  - v9 adds immutable daily baseline audit rows, unique per account/day/event.
  - Existing writer validates the immediately preceding day and references the original cutover.
- Design review: `docs/architecture/DAILY_BASELINE_EPOCH_SCHEMA_COMPATIBILITY_REVIEW_2026-11-07.md`, commit `4231b0c0ef109ca745f4d4f578a92b102f858138`.
- Recommendation: if Option B is separately approved, use additive parallel epoch tables rather than rebuilding/re-keying existing v6/v9 baseline and audit tables. Proposed separate immutable epoch, Core/AI/Legacy anchor snapshots, epoch daily baseline/audit, and append-only activation events. Existing v1/v2 rows and old writer remain untouched and fail-closed.
- Risk integration remains a separate hard dependency: an epoch baseline table alone must not authorize exposure. A future resolver must select epoch-scoped risk reference state; legacy risk state remains read-only/unready. No mutable pointer or silent `epoch_id` backfill proposed.
- Proposed migration staging: v10 additive schema only; v11 read-only epoch risk resolver/invariants; v12 activation and epoch writer only after separate approval. Exact version sequence must be rechecked before implementation.
- Status: **PASS — additive compatibility design documented. NOT VERIFIED — implementation, SQLite-version/index concurrency behavior, migration tests, external evidence authenticity, and actual persistent DB compatibility.**
- Recommendation remains Option A operationally: unresolved v1 stays blocked; no HWM reset or new epoch activation until complete independent account/position/order/fee/funding/mark evidence and explicit policy approval exist.
- Next: await explicit approval of Option B and identification of authoritative evidence source before source implementation. Persistent DB access and epoch activation remain separately gated.
- Restrictions unchanged: no persistent account DB opening/migration, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.

## 2026-11-07 — Epoch migration auto-trigger and SQLite runtime safety review

- Scope: read-only source review of `PaperLedger.__init__`, migration calls, SQLite transaction setup and CI runtime selection. No source, tests, workflow, or database changed/opened.
- Critical finding: `PaperLedger.__init__` automatically opens/creates the ledger DB, enables WAL, and invokes existing v2-v9 migrations for Core/AI ledgers. Adding epoch migrations to this sequence would make normal ledger construction mutate the persistent DB without a separate operator approval boundary.
- Daily baseline writer uses `BEGIN IMMEDIATE`; its connection requires writable mode, foreign keys ON, and a clean transaction. Existing SQLite connections use a 10-second timeout; ledger constructor enables WAL.
- CI selects Python 3.12 but does not log/assert the linked `sqlite3.sqlite_version`. Exact production SQLite version, journal/synchronous settings, filesystem durability and production DB compatibility remain NOT VERIFIED.
- Updated design document: `docs/architecture/DAILY_BASELINE_EPOCH_SCHEMA_COMPATIBILITY_REVIEW_2026-11-07.md`, source design commit `b63e95d2bf50ff3f75ef215701c74abe872eca7e`.
- New mandatory design constraints:
  - Never add v10-v12 epoch migrations to `PaperLedger.__init__`.
  - Use a separate explicit migration entry point; normal runtime only detects missing/incomplete epoch schema and fails closed.
  - Schema installation must not activate an epoch or alter risk state.
  - CI must pin/qualify and record SQLite runtime version.
  - Before persistent DB work, require target identity, verified backup, schema/FK preflight and no-write plan; test two-writer contention, timeout, WAL recovery, process-kill/reopen and rollback.
- Status: **PASS — migration auto-trigger risk identified and documented. NOT VERIFIED — SQLite runtime qualification, concurrency/crash tests, migration implementation, and persistent DB compatibility.**
- Next: no code until explicit approval of Option B, authoritative anchor evidence source, schema strategy, and separate persistent DB/migration permissions. Operational default remains strict predecessor chain and blocked exposure.
- Restrictions unchanged: no persistent account DB opening/migration, no backfill, no production backtest, no exchange connection, no deployment, no merge, no live orders. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — Dual Reconstruction verification contract

- Scope: architecture/contract documentation only. No source code, tests, workflow, schema, persistent database, or runtime was changed or opened.
- Added `docs/architecture/DUAL_RECONSTRUCTION_VERIFICATION_CONTRACT_2026-11-07.md`.
- Contract defines:
  - Replay A over a complete immutable event stream and Reconstruction B over a separately retained immutable checkpoint/archive.
  - Independent evidence roots, byte-level SHA-256 verification, coverage manifests, provenance, and the rule that two calculations over the same mutable SQLite rows are only `INTERNAL_CONSISTENCY_ONLY`, never independent verification.
  - Required event classes: fills/partial fills, reductions/closures, reversals, DCA, fees, funding, order lifecycle, reservations, marks, Legacy adjustments, and explicit corrections.
  - Deterministic event ordering and exact UTC boundary semantics: pre-boundary events are included in opening reconstruction; events at/after the boundary belong to the new epoch; late pre-boundary events invalidate the candidate.
  - Per-ledger Core/AI/Legacy and account-level reconciliation fields; precision-derived numeric tolerances; exact matching for identities, ownership, currencies, coverage, statuses and hashes.
  - Fail-closed conditions and explicit result vocabulary: INTERNAL_CONSISTENCY_ONLY, BLOCKED, RECONCILED_CANDIDATE, and separately authorized APPROVED_FOR_ACTIVATION.
- Tolerance proposal: quote-currency residual <= one smallest supported quote unit; quantity residual <= half declared quantity step; price residual <= half declared tick; IDs/ownership/currency/coverage/status/hash exact. Undefined precision means BLOCKED. These are proposed contract thresholds, not tested implementation behavior.
- Critical independence limitation: a GitHub artifact is not verified merely because an artifact ID/digest is recorded; payload bytes must be retrieved and re-hashed. A database-stored payload hash alone does not prove original source-byte authenticity.
- Commit adding contract: `041ceeca37faa50b56bca182711505d37fe4a260`.
- Status: **PASS — verification contract documented. NOT VERIFIED — availability/authenticity of two independent evidence roots, numeric behavior in code, and any actual anchor reconciliation. No Epoch policy, source, schema, or activation approval is implied.**
- Next: identify whether independently retained event archive and checkpoint evidence actually exist, using repository/project artifacts and metadata only. Do not open the persistent account DB or import external account data. If no genuinely independent second root exists, classify dual reconstruction as unavailable and preserve Option A.
- Restrictions unchanged: no source/test implementation, schema migration, persistent account DB opening, backfill, external account import, exchange connection, production backtest, deployment, merge, Epoch activation, HWM reset, or live order. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — Independent event archive/checkpoint inventory

- Scope: read-only recursive Git tree inventory after the Dual Reconstruction contract. No persistent account DB, GitHub Actions artifact payload, private Project attachment, or external/local archive was opened or downloaded.
- Inspected recursive tree at commit `2eb17051dd93a9c36b1e9be45333168793546702`: 279 paths, not truncated.
- No tracked database/SQLite, JSONL/NDJSON, CSV, Parquet/Arrow, archive, binary event payload, checksum manifest, or equivalent raw event/checkpoint data file was found. The evidence directory contains documentation reports/manifests, not a retained event archive or independent account checkpoint.
- Existing event-journal, funding, ledger, and baseline source code describes schema capabilities; source code is not a second evidence root. Persistent DB rows and byte-level source authenticity remain NOT VERIFIED.
- Inventory update: `docs/evidence/DAILY_BASELINE_V1_RECOVERY_EVIDENCE_INVENTORY_2026-11-07.md`, commit `b69ff744654feb6d5154c2af666cee699372dd94`.
- Result: **INDEPENDENT_SECOND_ROOT_NOT_FOUND_IN_TRACKED_GIT_TREE**. This is scoped to tracked Git files only; GitHub Actions artifact payloads, Project attachments, PC/Android files, and external archives were not inspected. Do not claim that no external evidence exists.
- Consequence: Dual Reconstruction cannot currently be independently verified from tracked repository evidence. Two calculations over the same mutable account DB remain INTERNAL_CONSISTENCY_ONLY and cannot qualify an Epoch anchor.
- Next: if proceeding without external evidence, preserve Option A and keep v1 unresolved/risk increases blocked. To continue the evidence path, identify a separately retained external checkpoint/archive by its storage/source identity first; do not open the persistent account DB, download arbitrary artifacts, import account data, or implement source/schema changes without separate authorization.
- Restrictions unchanged: no source/test implementation, schema migration, persistent account DB opening, backfill, external account import, exchange connection, production backtest, deployment, merge, Epoch activation, HWM reset, or live order. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — GitHub Actions artifact metadata classification

- Scope: read-only metadata review of five known T1 CI runs. Artifact payloads were not downloaded or extracted; no persistent DB or external/local archive was opened.
- Runs and artifacts:
  - run `42277853667`, source `7cddb5eacfd70f5bc886bc03f672177cdf3f8f2a`, artifact `13533807345`, 8,452 bytes, digest `sha256:fb41913d0826f836adf7b6c460efc6bd3d41f6af41f5e976764cc099c00376c9`.
  - run `42279162334`, source `fbf74c5d72ee977651b8075f13dadf9763b4b272`, artifact `13534541826`, 8,919 bytes, digest `sha256:ac769ba03c657a4361d72eef3f794ac005cada4108395fc85e4719d6f1ea1ff0`.
  - run `42279706472`, source `4eac10b704882c7f14901400be9d76465b0ffc44`, artifact `13534577603`, 8,971 bytes, digest `sha256:f098522daedc72098025bf1cdd43efb4315e68f8613cfe0a10ce3865fe09955e`.
  - run `42280083080`, source `f7df95c2ff2008aa88923b3242b1486c096d9342`, artifact `13533829670`, 9,017 bytes, digest `sha256:518596b09e16712d2c5ed157baa85168fd6c960ffbf5a7414ee9d6d547195275`.
  - run `42276535949`, source `e06b28b740590b99c4c930004bf547c8fccbaf99`, artifact `13533163461`, 8,189 bytes, digest `sha256:62557812142e7aa84aa238c4c6a4dd99a851c9116beeeca2dd1a1893abc0f88e`.
- Artifact names are `dual-ledger-red-evidence-<source SHA>`; all five are CI evidence packages, not identified as account event archives/checkpoints. Metadata alone does not prove payload contents or original account-data authenticity. All were unexpired during inspection and expire on 2026-11-13 UTC.
- Inventory updated: `docs/evidence/DAILY_BASELINE_V1_RECOVERY_EVIDENCE_INVENTORY_2026-11-07.md`, commit `67d93ae0967383b865eb4509e17c5e7f23e5f0ff`.
- Status: **PASS — metadata classification recorded. NOT VERIFIED — artifact payload contents; no independent account evidence root found.** These artifacts remain useful for CI/test provenance, not for Replay A or Reconstruction B.
- Next: preserve the current classification. Do not download/extract artifacts absent a specific evidence-based reason and explicit scope. A genuine second root must be a retained account event archive or independently retained account checkpoint, not a CI test report.
- Restrictions unchanged: no source/test implementation, schema migration, persistent account DB opening, backfill, external account import, exchange connection, production backtest, deployment, merge, Epoch activation, HWM reset, or live order. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — CI artifact producer workflow inspection

- Inspected `.github/workflows/dual-ledger-red.yml` at branch HEAD `88a0235df85ba15eeb194e4f013d7ecab444543d`; workflow blob SHA `c7c3e16026c6b5f01b6be1a7d2f1c504a532607a`.
- The workflow explicitly blanks `PAPER_DB`, `MARKET_DATA_DB`, Binance credentials, and OKX credentials; preflight records PAPER_ONLY and EXTERNAL_SERVICES=NONE.
- Artifact upload allowlist contains only four test/provenance logs: preflight, compile, focused RED tests, and full paper_execution regression. No account DB, event export, checkpoint, market data payload, or raw trading records are uploaded by this workflow.
- Therefore the known `dual-ledger-red-evidence-<SHA>` artifacts are test logs by workflow design, not Replay A/B evidence. No artifact payload download was needed; no persistent DB was opened.
- Inventory updated: `docs/evidence/DAILY_BASELINE_V1_RECOVERY_EVIDENCE_INVENTORY_2026-11-07.md`, commit `813ef724048146e4f2642d88259638d5abfca829`.
- Result: **PASS — artifact producer classified from exact workflow source. BLOCKED — independent account evidence root still not found.** This conclusion is limited to this workflow; other workflows/private artifacts/external archives were not proven absent.
- Next: inspect remaining relevant artifact-producing workflows (if any) and their explicit upload allowlists, then stop repository-side evidence search if they also contain only CI logs. Do not download arbitrary artifacts or open the persistent account DB.
- Restrictions unchanged: no source/test implementation, schema migration, persistent account DB opening, backfill, external account import, exchange connection, production backtest, deployment, merge, Epoch activation, HWM reset, or live order. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — Complete tracked CI artifact producer inventory

- Scope: read-only inspection of all seven workflow files under `.github/workflows/` at HEAD `88a0235df85ba15eeb194e4f013d7ecab444543d`. No historical artifact payloads were downloaded, no DB was opened.
- Reviewed all artifact upload allowlists:
  - `dual-ledger-red.yml`: preflight/compile/test/regression logs only.
  - `p5-3-11-g2-integration-green.yml`: source/isolation/compile/gateway/feeder/T0/consumer test logs and verdict.
  - `paper-writer-isolation-red.yml`: static contract test log only.
  - `t0-manual-validation.yml`: source/isolation/config/component/provider/SQLite/Timescale test logs and reports.
  - `t0-postgres16-grantor-repro.yml`: PostgreSQL grantor reproduction log only.
  - `t0-single-writer-gateway-red.yml`: T0 contract/behavior/health/restart/market-data test logs; disposable Timescale integration logs; paper consumer test log.
  - `android-release-pair.yml`: APK binaries, source/release manifests, Android test results/reports; no account history.
- No tracked workflow uploads raw Core/AI/Legacy fills, position history, funding/fee history, event archive, or independent account checkpoint. T0 DB artifacts are disposable test evidence, not account history.
- Inventory updated: `docs/evidence/DAILY_BASELINE_V1_RECOVERY_EVIDENCE_INVENTORY_2026-11-07.md`, commit `b3aff2312f0b3809fb5c54bf3f39baddba72d812`.
- Result: **PASS — tracked CI artifact producer inventory completed. BLOCKED — no qualifying independent account evidence root found in tracked workflows.** This does not rule out private Project files, PC/Android exports, or external archive storage; historical payloads were not inspected.
- Next: stop searching tracked CI workflows for account history. The only useful next evidence step requires identifying a specific independent archive/checkpoint location outside the repository (Project file, PC/Android export, or external archive) and its owner/source identity. Do not open persistent account DB, import data, or download unspecified artifacts.
- Restrictions unchanged: no source/test implementation, schema migration, persistent account DB opening, backfill, external account import, exchange connection, production backtest, deployment, merge, Epoch activation, HWM reset, or live order. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — User confirms no independent account archive/checkpoint

- User explicitly confirmed that no independent event archive or account checkpoint is currently available.
- Therefore historical Dual Reconstruction is **UNAVAILABLE / BLOCKED**. This is no longer an open repository-search task. Do not export the same mutable account DB and call it an independent root; do not use CI fixtures/logs as account history.
- Preserve Option A (strict predecessor chain). No new Epoch activation, HWM/daily-baseline reset, or exposure increase based on an unverified anchor.
- Future evidence capture can establish independently retained evidence only prospectively; it cannot retroactively prove missing history.
- Inventory updated: `docs/evidence/DAILY_BASELINE_V1_RECOVERY_EVIDENCE_INVENTORY_2026-11-07.md`, commit `bbf44704521b3f1bb913039b729fc30040d6de00`.
- Next safe work: documentation-only design of a forward evidence capture/retention protocol, if requested. No source/schema/database writer or persistent storage changes are authorized.
- Restrictions unchanged: no source/test implementation, schema migration, persistent account DB opening, backfill, external account import, exchange connection, production backtest, deployment, merge, Epoch activation, HWM reset, or live order. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — Forward Evidence Capture & Retention Protocol (documentation only)

- Created `docs/architecture/FORWARD_EVIDENCE_CAPTURE_RETENTION_PROTOCOL_2026-11-07.md`, commit `8601a6922fcaa41cf35e58431480f3ae4b832088`.
- Design separates Root A (append-only, hash-linked paper execution event journal) from Root B (separate observer process, independent reducer/projection/checkpoint, separate storage namespace and credentials). Root B must consume committed event envelopes; it must not construct a checkpoint by querying mutable account DB rows.
- Assurance levels explicitly distinguish mutable-source export/internal consistency (LEVEL 0), independent retention/capture with shared upstream event-emitter limitation (LEVEL 1), and independent external economic source (LEVEL 2, not available/assumed). This is a paper-system integrity design, not exchange verification.
- Protocol covers canonical event envelope/provenance, sequence/hash continuity, idempotency, journal durability ordering, observer lag/gaps, periodic and UTC boundary checkpoints, immutable manifests/read-back hashes, retention/access controls, crash recovery, monitoring, and acceptance tests.
- Inventory indexed the new proposal in `docs/evidence/DAILY_BASELINE_V1_RECOVERY_EVIDENCE_INVENTORY_2026-11-07.md`, commit `61fb94c097fc488ed9a02b5279554c2a200170fe`.
- Status: **PASS — documentation draft created. NOT APPROVED — implementation/storage/runtime.** No source, tests, schema, workflow, persistent DB, storage provider, or runtime behavior changed. No provider/cost selected.
- Historical independent evidence remains NONE AVAILABLE; historical Dual Reconstruction remains UNAVAILABLE/BLOCKED. Option A remains current policy. Prospective capture cannot restore missing historical records.
- Next: architecture/threat-model review and explicit selection of storage, retention, access-control, and cost constraints. Do not start source implementation, schema migration, storage provisioning, DB opening, or runtime capture without separate approval.
- Restrictions unchanged: no T0 work, no exchange connection, no live orders, no epoch activation, no HWM/Daily Loss reset, no exposure increase based on unverified history, no deployment or merge. PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — Forward Evidence Threat Model Review (documentation only)

- Created `docs/architecture/FORWARD_EVIDENCE_THREAT_MODEL_REVIEW_2026-11-07.md`, commit `61c152d138336915a9e6fc68b05c04d19e6dde86`.
- Recorded 30 threats spanning upstream event fabrication, shared admin/credential compromise, observer contamination from mutable DB, hash integrity vs authenticity, signing-key compromise/loss, sequence/replay, writer/outbox split-brain, observer lag, common-mode reducer defects, clock/UTC and late-event faults, missing fee/funding/marks, ownership attribution, storage outage/retention deletion, compromised CI/build, privacy, and false-green monitoring.
- Explicit trust limitation: Root A and Root B may be separate retention/computation paths but share the upstream event emitter and may share host/operator/provider control planes. LEVEL 1 is not independent economic-source verification. SHA-256 alone is not authenticity; signed manifests require separately controlled key custody, which remains a trust dependency.
- Open decisions remain open and must not be guessed: provider/region, separate provider/account vs locked namespaces, retention/legal hold, Root B lag and outage policy, durability SLA, signing/key custody, clock skew, RPO/RTO, privacy classification, and atomic outbox design.
- Indexed in `docs/evidence/DAILY_BASELINE_V1_RECOVERY_EVIDENCE_INVENTORY_2026-11-07.md`, commit `2a792acfb9f1c2467431bfd89ed44a5802497c3e`.
- Status: **PASS — threat model documented. NOT VERIFIED — controls are not implemented and security tests are not run.** No source, tests, schema, workflow, storage, persistent DB, or runtime behavior changed.
- Next: review open storage/security decisions and define a threat acceptance boundary. No implementation or provisioning without separate approval.
- Restrictions unchanged: no T0 work, no exchange connection, no live orders, no epoch activation, no HWM/Daily Loss reset, no exposure increase based on unverified history, no deployment or merge. PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — Forward Evidence Storage Architecture Decision Review (documentation only)

- Created `docs/architecture/FORWARD_EVIDENCE_STORAGE_ARCHITECTURE_DECISION_REVIEW_2026-11-07.md`, commit `d3b9cecea912bba6172b68d2c6fa4d35842682a6`.
- Compared six patterns: local-only; two namespaces in one cloud account; separate accounts under one provider; two providers; local spool plus one remote root; local spool plus two separately controlled remote roots.
- Conditional target recommendation: Pattern F — encrypted bounded local spool plus two remote roots in separately controlled provider accounts, preferably across providers. Fallback Pattern C (separate accounts under one provider) requires explicit residual-risk acceptance. Pattern B (two buckets in one account) is insufficient for a strong independence claim. Local PC storage is not an authoritative archive.
- Defined vendor capability checklist/disqualifiers, cost measurement model, retention/access controls, outage and compromise behavior, restore requirements, and open decisions before a vendor shortlist.
- Indexed in `docs/evidence/DAILY_BASELINE_V1_RECOVERY_EVIDENCE_INVENTORY_2026-11-07.md`, commit `40e0c2bf80768a2756a49d2748c8f6909a7609b6`.
- Status: **PASS — storage architecture comparison documented. NOT APPROVED — provider selection, purchase, provisioning, credentials, storage access, or runtime capture.** No source/schema/workflow/DB/runtime changes.
- Open decisions: cross-provider vs separate-account acceptance; authorized monthly budget; retention duration/legal hold; provider account/billing/recovery owners; local spool policy; region/jurisdiction; Root B lag/outage threshold; signing-key custody.
- Next: obtain explicit decisions on these constraints. Only then prepare a vendor shortlist using current official pricing/capability documentation. No provisioning or implementation before separate approval.
- Restrictions unchanged: no T0 work, no exchange connection, no live orders, no epoch activation, no HWM/Daily Loss reset, no exposure increase based on unverified history, no deployment or merge. PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — Forward evidence storage acceptance plan

- Created `docs/architecture/FORWARD_EVIDENCE_STORAGE_ACCEPTANCE_TEST_PLAN_2026-11-07.md`.
- Commit adding the plan: `41d67ea9b57b6398506e4d539d0e62723e33bc51`.
- Inventory index update: `e34e714a32600520c9c17dc74380eec504292aba`.
- The plan defines 20 vendor-neutral acceptance tests for identity separation, least privilege, WORM/retention behavior, object versions, independent Root A/Root B restore, cross-root isolation, read-back integrity, signing-key separation, replay/gap handling, observer lag/outage, crash/partial uploads, spool bounds, single-root loss, retention/legal hold, region, cost, auditability, and provider exit.
- Candidate-specific checks are listed for AWS S3 and Cloudflare R2. Both remain candidates only; neither is selected or approved. No provider account, region, budget, retention period, lag threshold, or key custody choice is assumed.
- Proposed 5-minute warning / 15-minute exposure-block thresholds remain unapproved. They are not runtime settings.
- Status: **PASS — documentation draft committed. NOT RUN — provider tests. NOT APPROVED — purchase, account creation, credentials, provisioning, storage access, source/schema/workflow/database/runtime changes, or persistent capture.**
- No CI was run because this was documentation-only. No tests, source, workflow, database, T0 runtime, or T1 runtime were changed.
- Historical Dual Reconstruction remains **UNAVAILABLE / BLOCKED**; Option A strict predecessor chain remains unchanged. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.
- Next: review and approve/revise the qualification constraints. Only after explicit approval may disposable provider test accounts and synthetic-data tests be considered. Do not use canonical account data or open the persistent account DB.


## 2026-11-07 — P1.2 Vendor Security Deep Review

- Created `docs/architecture/FORWARD_EVIDENCE_STORAGE_VENDOR_SECURITY_REVIEW_2026-11-07.md`, commit `13c6f8b5ca63bab0950a1e0d56e0321d6fd88500`.
- Official docs reviewed: AWS S3 Object Lock (Compliance/Governance, version behavior, delete markers, replication/configuration); Cloudflare R2 Bucket Locks, API token scopes, Data Access Logs and Audit Logs v2.
- Key finding: AWS S3 Compliance Mode is the stronger Root A candidate. Protected versions cannot be permanently deleted by account root during retention, but deletion of the AWS account is a catastrophic exception. Governance Mode is insufficient for the intended assurance where bypass permission exists.
- Key finding: R2 Bucket Lock rules can be removed/replaced by authorized bucket-configuration administration. R2 is only a conditional Root B candidate and is not equivalent to S3 Compliance Mode against account-admin compromise.
- R2 Data Access Logs are best effort and omit HTTP 400+; Audit Logs v2 are retained 18 months and have documented coverage gaps. They cannot be treated as a complete immutable evidence trail.
- S3 Object Lock is version-specific. Simple DELETE can add a delete marker; a new PUT can create another version. Manifests and recovery must bind exact version IDs and never trust a mutable current-key pointer.
- Acceptance plan amended with mandatory tests for S3 account/root/admin behavior, delete markers/version IDs, immutable manifest references, R2 lock-rule administration alerts, least-privilege writer tokens, audit gaps and external audit retention. Amendment commit: `a6cbbd84771fe6b5f3943131eeafd83f05f353e4`.
- Inventory update commit: `e69ee1fc8cd5803d995990c7c06285492c0f2677`.
- Status: **PASS — documentation review and acceptance-plan amendment. NOT VERIFIED — live provider tests, region, costs, key custody and independent restore. NOT APPROVED — provider selection, purchase, accounts, credentials, provisioning or persistent capture.**
- No CI run (documentation-only). No source/schema/workflow/database/runtime changes. Historical Dual Reconstruction remains UNAVAILABLE / BLOCKED; Option A unchanged; T0 paused; PAPER-only; `ai_execution_enabled=false`.
- Next: compare a second WORM-capable provider/account option for Root B, or explicitly accept and document R2's weaker admin-resistance before any disposable provider test approval. Do not provision or use canonical account data.


## 2026-11-07 — P1.3 second WORM provider qualification review (documentation only)

- Created `docs/architecture/FORWARD_EVIDENCE_SECOND_WORM_PROVIDER_REVIEW_2026-11-07.md`, commit `952d8a4a86c25a86979d8826620375b9459de517`.
- Compared official documentation for Google Cloud Storage Bucket Lock and Azure Blob immutable storage as cross-provider Root B candidates. AWS S3 Compliance Mode remains the preferred Root A candidate; Cloudflare R2 is retained only as a lower-assurance fallback.
- GCS: locked bucket retention cannot be reduced/removed; bucket deletion is blocked while retained objects remain; a project lien blocks project deletion, but privileged project owner/organization administrator can remove the lien. Data Access audit logs must be explicitly enabled; Object Versioning alone does not protect whole-bucket deletion.
- Azure: locked time-based WORM policies cannot be shortened/deleted; Microsoft documents storage-account deletion barriers under specified locked container/version conditions. Exact container-vs-version policy scope, retention expiry, account deletion path and restore must be tested. Legal hold is not equivalent to irreversible time-based retention.
- Acceptance plan amended with GCS policy/lien/audit/generation restore tests, Azure container/version/account deletion tests, and independent admin/clean-room restore tests. Plan commit `67c8304f91f0c6e318d6cb59ff8a119342654452`.
- Evidence inventory update commit: `6ec7d47916024a2ce2ce3ad0788b75717a9f5707`.
- **Status: PASS — documentation review and test-plan amendment. NOT VERIFIED — live provider behavior, restore, audit export, region, cost, and key custody. NOT APPROVED — provider selection, account creation, purchase, credentials, provisioning, storage access, or persistent capture.** No CI run (documentation-only); no source/schema/workflow/database/runtime changes.
- Next: perform a vendor-neutral requirements and cost-input review, then prepare a bounded synthetic-data qualification proposal comparing GCS and Azure. Do not provision accounts or execute provider tests until separately approved. Do not use canonical account data.
- Historical Dual Reconstruction remains UNAVAILABLE / BLOCKED; Option A strict predecessor chain unchanged. T0 paused; PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — P1.4 Forward Evidence Storage Cost Model (documentation only)

- Created `docs/architecture/FORWARD_EVIDENCE_STORAGE_COST_MODEL_2026-11-07.md`, commit `a252fd23ff90eb0ff838a6205b7f215c94a0cdd0`.
- Model decomposes Root A and Root B costs into capacity, request/transaction classes, retrieval, egress, replication/redundancy, versioning, audit/logging, key management, restore, taxes and support. It defines measured workload inputs and retention-horizon growth; indefinite retention is explicitly unbounded.
- Reviewed official pricing for AWS S3/CloudTrail, GCS/Cloud Logging and Azure Blob/Azure Monitor. No complete comparable Singapore quote can be certified without exact region/SKU, retention, workload and billing assumptions. No invented per-GB estimate was inserted.
- Key pricing caveats: Azure immutable storage has no separate capacity surcharge, but version-level WORM may increase capacity; Azure Archive has 180-day minimum storage and early-deletion fees. GCS Data Access audit logs may incur charges. AWS CloudTrail data events have separate charges. Budget notifications are not guaranteed hard caps; AWS billing data may lag, Azure budgets do not stop consumption, and GCP spend caps are limited to eligible services and are not instantaneous.
- Acceptance Test Plan amended with measured workload, exact SKU quote, retention growth, full restore cost, budget controls and post-test bill reconciliation. Commit: `bad784a97d3eb276b37f577969c108a3d62ad566`.
- Evidence Inventory update commit: `4f5c07557168d72008797a8f06c75f0ce376f50b`.
- **Status: PASS — cost model and acceptance gates documented. NOT VERIFIED — exact Singapore prices, workload, retention and budget fit. USD 5/month is illustrative only, NOT APPROVED and not demonstrated feasible. NOT APPROVED — provider selection, accounts, purchase, credentials, provisioning, provider tests or persistent capture.** No CI run (documentation-only); no source/schema/workflow/database/runtime changes.
- Next: define the synthetic evidence envelope and minimum retention/recovery requirements from the architecture, then prepare a non-provisioning cost worksheet with measured sample sizes and candidate region/SKU quotes. Any live provider test requires separate approval and a hard test-spend authorization.
- Historical Dual Reconstruction remains UNAVAILABLE / BLOCKED; Option A strict predecessor chain unchanged. T0 paused; PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — P1.5 Forward Evidence Envelope & Minimum Recovery Requirements

### Scope and artifacts

Documentation-only continuation on the existing branch `feature/t0-centralized-data-feeder-p1-20261101`.

- Contract: `docs/architecture/FORWARD_EVIDENCE_ENVELOPE_RECOVERY_REQUIREMENTS_2026-11-07.md`
  - Commit: `7e34ae783f0cc9774169d75dbcf4b93385d4ef37`
- Acceptance Test Plan amendment: `docs/architecture/FORWARD_EVIDENCE_STORAGE_ACCEPTANCE_TEST_PLAN_2026-11-07.md`
  - Commit: `61204f2531bffa7a210945fc7951a7479d42811f`
- Evidence Inventory amendment: `docs/evidence/DAILY_BASELINE_V1_RECOVERY_EVIDENCE_INVENTORY_2026-11-07.md`
  - Commit: `5cedc28b3b74c233812ce2a67d677695e2ef0572`
- This handoff update is the final P1.5 documentation entry; its commit identity is recorded in GitHub history and the completion report.

### Contract decisions documented (proposals, not implementation)

- Immutable `event_core` plus integrity envelope; globally unique event ID, stable stream ID, monotonic 20-digit per-stream sequence, typed event/schema version, exact source build/config provenance, ledger/strategy ownership, separate occurred/committed UTC timestamps, causality/idempotency, payload provenance and previous-event hash.
- Canonical bytes: UTF-8 RFC 8785 JCS over `event_core` only, no BOM/trailing newline. Financial decimals and large integers are decimal strings; duplicate keys, unsafe numeric representations, invalid Unicode and ambiguous required/null/omission forms are rejected.
- Proposed domain-separated SHA-256 hash and Ed25519 signature message. Signature key ID/version, rotation/revocation and compromise history are part of the evidence trust chain. Key custody and exact production algorithm decision remain open.
- Append-only corrections/supersessions; identical retry is idempotent; same event ID with changed bytes, duplicate sequence, missing sequence, predecessor mismatch or invalid signature blocks readiness. Late pre-boundary events invalidate affected checkpoints.
- Recovery coverage includes Core/AI/Legacy ownership, intent/admission/reservation, order lifecycle, partial/full fills, position transitions/DCA/reversal, fee/funding, marks/valuation, strategy/risk config, Kill Switch, HWM and daily UTC baseline.
- Signed segment manifests bind exact sequence range, count, first/last hash, segment digest/length, previous manifest, exact object version/generation, retention read-back and Root A/Root B receipts.
- Root B consumes committed Root A envelopes only; it must not query mutable account DB rows. Assurance remains Level 1 at most because the upstream event emitter is shared.
- Candidate RPO/RTO definitions and reliability-first fail-closed proposal recorded. Root A/Root B failure, integrity gaps, uncertain durability, spool exhaustion or Root B lag blocks new exposure increases. Reductions/closures require a durable evidence path.
- Candidate service observation bands 1/5/15 minutes and retention comparison horizons 1/3/7 years/indefinite are planning inputs only, NOT APPROVED thresholds or retention policy.

### Standards references

- RFC 8785 JCS: canonical JSON; Informational RFC, not Internet Standards Track.
- RFC 8032 EdDSA: signature algorithm definitions; Informational RFC.
- RFC 3339 timestamps, narrowed by this proposed contract to fixed-millisecond UTC timestamps.

These references were reviewed from RFC Editor sources. They are design references only; no library or cryptographic behavior was implemented or tested.

### Verification and status

- P1.5 contract, acceptance plan and inventory updates: **PASS — documentation recorded**.
- NOT IMPLEMENTED / NOT TESTED: canonicalizer, hash/signature code, key custody, atomic journal/outbox, Root B observer/reducer, recovery/replay, RPO/RTO, retention and fail-closed runtime behavior.
- NOT RUN: deterministic synthetic size/throughput benchmark and provider acceptance tests.
- NOT SELECTED: provider pair, region, budget, retention duration, Root B lag threshold, RPO/RTO numeric targets and key custody.
- NOT AUTHORIZED: cloud account, purchase, credential issuance, provisioning, persistent capture, source/schema/database/workflow/runtime changes.
- CI: NOT RUN; documentation-only scope. No CI run ID or artifact exists for this increment.
- No persistent account DB opened; no external artifact downloaded; no exchange connection; no T0 runtime/data sync; no live order.
- Historical Dual Reconstruction remains **UNAVAILABLE / BLOCKED**; Option A strict predecessor chain remains unchanged. No Epoch activation, HWM/Daily Loss reset or exposure increase from an unverified anchor.
- T0 remains PAUSED; PAPER-only; `ai_execution_enabled=false`.

### Next step

Review the P1.5 contract and open decisions. If continuing without implementation approval, prepare a deterministic synthetic fixture specification and a measurement worksheet. Source implementation, key provisioning, provider qualification, persistent capture, runtime changes and any risk-policy change each require separate explicit approval.



## 2026-11-07 — P1.6 Deterministic Synthetic Evidence Fixture & Measurement Specification

### Scope and artifacts

Documentation-only continuation on `feature/t0-centralized-data-feeder-p1-20261101`.

- Synthetic fixture and measurement specification: `docs/architecture/FORWARD_EVIDENCE_SYNTHETIC_FIXTURE_MEASUREMENT_SPEC_2026-11-07.md`
  - Commit: `83e787730cf7a35b99aad4c92e16e4d91e0089dd`
- Acceptance Test Plan amendment: `docs/architecture/FORWARD_EVIDENCE_STORAGE_ACCEPTANCE_TEST_PLAN_2026-11-07.md`
  - Commit: `913760fabd14f7f99d4f632bf6ff0b5bff663c80`
- Evidence Inventory amendment: `docs/evidence/DAILY_BASELINE_V1_RECOVERY_EVIDENCE_INVENTORY_2026-11-07.md`
  - Commit: `465a161892323cfbf538a92133119604d08640bd`
- Handoff update: current documentation commit and blob SHA are recorded in GitHub history and final read-back.

### Specification

- Reproducibility descriptor fixes fixture spec version, future generator/build SHA, 256-bit seed, UUID namespace, UTC base time, event mix, payload profile, canonicalization/hash profile, segment policy and environment.
- Deterministic generation uses domain-separated HMAC-SHA-256 counter stream, UUIDv5 synthetic event IDs, fixed timestamps, deterministic stream sequencing/inter-stream tie-break and exact decimal strings. Wall clock, platform PRNG, filesystem order and process scheduling are excluded.
- All P1.5 event classes are represented. Negative vectors (duplicate/tamper/gap/late event, partial-fill lifecycle, UNKNOWN fee/funding, stale mark, observer crash) are separated from clean workload statistics.
- Payload cohorts: SMALL/MEDIAN/LARGE plus separate STRESS. Proposed fixture scales: 1k, 10k, 100k events, plus burst and recovery profiles.
- Event-core canonical bytes, transport envelope, segments, manifests and optional compression are measured separately. Report min/median/p90/p95/p99/max with counts and cohort identity.
- Candidate batching matrix: 100 events/1 MiB, 500/4 MiB, 1,000/8 MiB and 5,000/32 MiB. These are benchmark inputs, not runtime limits.
- Daily storage formulas use measured event mix/size; Root A and Root B are modeled independently. Cost worksheet requires exact provider/account boundary, region/SKU, retention, request/retrieval/egress, KMS, audit, restore, taxes/FX and quote provenance.
- Region-neutral decision rule: Singapore is not a default. Compare proximity from Viet Nam only after durability, admin separation, residency, restore and cost gates.

### Verification and status

- P1.6 specification and Acceptance Test Plan gates: **PASS — documentation recorded**.
- Generator implementation: NOT CREATED / NOT AUTHORIZED.
- Synthetic generation, JCS cross-implementation, event-size, segment, throughput, spool, Root B replay and clean-room restore benchmarks: NOT RUN.
- Event size, daily volume, object count, storage cost, restore time and throughput: NOT MEASURED.
- Provider/region/retention/budget/account boundary: NOT SELECTED.
- Provider accounts, credentials, purchase, provisioning, provider tests and persistent capture: NOT AUTHORIZED.
- Source/schema/workflow/database/runtime: UNCHANGED. CI: NOT RUN (documentation-only; no workflow run or artifact).
- No persistent account DB access, external artifact download, exchange connection, T0 runtime/data sync or live order.
- Historical Dual Reconstruction remains UNAVAILABLE / BLOCKED; Option A strict predecessor chain unchanged. No Epoch activation, HWM/Daily Loss reset or exposure increase from unverified history.
- T0 remains PAUSED; PAPER-only; `ai_execution_enabled=false`.

### Next step

Review P1.6 assumptions. If explicitly approved, the next bounded implementation could be a standalone deterministic synthetic fixture generator and local-only test harness, with no account DB, exchange, provider, persistent capture or runtime integration. Such approval must be separate and limited to the generator/test harness; it does not authorize provider qualification or T0/T1 runtime changes.



## 2026-11-07 — P1.7 Synthetic Fixture Readiness Review & Specification Hardening

### Scope and artifacts

Documentation-only continuation on `feature/t0-centralized-data-feeder-p1-20261101`.

- Readiness review: `docs/architecture/FORWARD_EVIDENCE_SYNTHETIC_FIXTURE_READINESS_REVIEW_2026-11-07.md`
  - Commit: `f364b178ce163898b4fd7cde6619d5a5b0283c1f`
- P1.6 specification hardened (§13): `docs/architecture/FORWARD_EVIDENCE_SYNTHETIC_FIXTURE_MEASUREMENT_SPEC_2026-11-07.md`
  - Commit: `6b5d643ea4b22f066877cdbf221dd3f01ca726d5`
- Acceptance Test Plan P1.7 gates: `docs/architecture/FORWARD_EVIDENCE_STORAGE_ACCEPTANCE_TEST_PLAN_2026-11-07.md`
  - Commit: `296518594fd192b0468c7a600657d3ca04d69f06`
- Evidence Inventory P1.7 entry: `docs/evidence/DAILY_BASELINE_V1_RECOVERY_EVIDENCE_INVENTORY_2026-11-07.md`
  - Commit: `a3238f4ca1a9452aecddad94a07d13e8ae96bc49`
- This handoff update is the final P1.7 documentation commit; exact SHA is recorded in GitHub history after read-back.

### Review findings resolved in documentation

- Exact HMAC-SHA-256 PRF byte framing, 32-byte seed, big-endian length/counter fields and multi-block output.
- Restricted synthetic stream ID grammar and exact UUIDv5 name bytes.
- Deterministic scenario/state-machine templates preserve causal/economic validity; event-mix percentages are targets, not permission to generate impossible transitions.
- Per-stream monotonic commit timestamps and sequence authority; isolated late-event fault vectors.
- One stream per segment, contiguous sequences and exact byte-cap definition.
- Immutable pre-upload manifest separated from post-upload storage receipt.
- Manifest canonicalization/hash/signature domain separated from event protocol.
- Test keys limited to published RFC vectors or ephemeral process memory; no private seed in artifacts.
- Arithmetic mean and nearest-rank quantile definitions with all raw samples retained.
- Local Root B replay explicitly labeled `LOCAL_REPLAY_SIMULATION`; cannot prove provider/admin/process independence.

### Verification and status

- P1.7 readiness review and P1.6 §13 hardening: **PASS — documentation recorded**.
- Acceptance Plan and Evidence Inventory: **PASS — updated**.
- Generator: NOT IMPLEMENTED / NOT AUTHORIZED.
- Crypto vectors, fixture generation, throughput, storage size, replay, restore and provider tests: NOT RUN.
- Provider, region, retention, budget and key custody: NOT SELECTED.
- Source/schema/workflow/database/runtime: UNCHANGED. CI: NOT RUN (documentation-only; no run ID/artifact).
- No account DB, external artifact, exchange, cloud provider or persistent capture accessed.
- Historical Dual Reconstruction remains UNAVAILABLE / BLOCKED; Option A unchanged. No Epoch activation, HWM/Daily Loss reset or exposure increase from unverified history.
- T0 remains PAUSED; PAPER-only; `ai_execution_enabled=false`.

### Next step and approval boundary

P1.8 should be a bounded approval decision for a standalone synthetic-only generator and local test harness. The current continuation request did not explicitly approve source implementation, so no generator was created. If approved later, scope must exclude T0/T1 production code, account DB, exchange connectivity, provider accounts, credentials, provisioning, persistent capture and risk-policy changes. Provider qualification requires a separate approval.


## 2026-11-07 — P1.8 Standalone Synthetic Evidence Generator

### Approval and boundary

User explicitly approved: `APPROVE P1.8 — SYNTHETIC-ONLY LOCAL GENERATOR`.

Scope implemented only as an isolated standard-library Python package and a GitHub Actions workflow. No account/T0/T1 DB, external artifact, VPS, exchange, provider, credential, cloud bucket, persistent capture, runtime integration, risk-policy change or real order was accessed or changed. `ai_execution_enabled=false` remains unchanged.

### Source and evidence commits

- Package marker: `a7cc4696192f95aacc1c305bf518ea50d248bcb5`.
- TDD test-first RED import failure and initial contracts: `2070a86d7e14916f1d38563ca48261bdcf24422e`.
- Generator implementation: `7c089273e165aeb0a8215e808d61c52cb39a6297`.
- CLI: `3321355fb311761acd34352c72e7a4f3bfc03997`.
- Usage/limitations README: `07bd28c68185b95115a7ea1e508d89a784cdaa6e`.
- GitHub Actions workflow: `a591bfb3626b3cdeaa9841b81eaf3d1a90410a2d`; expression correction: `1960e091f84fc64f2e40b4243abdbb440116a05d`.
- Replay/input hardening: `6f8b2c140ef32264496c6c8b7da3020b3babc16b`.
- Expanded replay fault tests: `9587051361e13063841a6e96c7b415fbb6ae0cf5`.
- Implementation report: `docs/architecture/FORWARD_EVIDENCE_SYNTHETIC_GENERATOR_IMPLEMENTATION_2026-11-07.md`, commit `8eefd83bca4b49ddcb531a575d2dc7030157964b`.
- P1.6 target-weight sum correction: `21cc29fb9bf1261672d8d2934f041c7411938e8d`.
- P1.8 Acceptance Test Plan: `03d81abf7347e964beb63dbaad74269da56c1844`.
- Evidence Inventory P1.8 entry: `262f67a45e48f45f37ea31da82d7fb353448544c`.
- This handoff update is the final P1.8 documentation commit; exact SHA is the resulting GitHub commit after read-back.

### Implementation

- Fixed 32-byte HMAC-SHA-256 deterministic PRF and UUIDv5 synthetic identities.
- Core, AI and Legacy synthetic streams; fixed UTC clock, sequence, causation and hash chain.
- SMALL/MEDIAN/LARGE cohorts, 13 separate negative-vector catalog entries.
- Strict JCS-compatible subset; event and manifest SHA-256; per-stream segments and unsigned local manifests.
- Exact byte-cap and nearest-rank measurement; local replay simulation; duplicate identical delivery idempotency and tamper/gap/wrong-hash rejection.
- Output writer refuses overwrite and produces SHA-256 file manifest.
- No third-party dependencies.

### Verification

- Local focused tests: **19/19 PASS**.
- Python compile: **PASS**.
- Two 1,000-event fixtures: **byte-identical**; all fixture SHA-256 manifest entries verified.
- Exploratory single-run local measurements: 1k ~2,282 events/s; 10k ~2,131 events/s. These are not production performance certification or a five-run benchmark.
- GitHub Actions workflow added with exact-SHA checkout, no package installation, blank DB/exchange credential env, explicit `AI_EXECUTION_ENABLED=false`, focused tests, two 1k fixture generation/reproducibility comparison and 7-day artifact upload.
- GitHub combined-status query returned no status records. Available workflow-run connector only exposed PR-triggered runs; exact push run ID, job conclusion, checked-out SHA from logs and artifact ID/digest remain **NOT VERIFIED**. Do not report GitHub Actions PASS until exact run evidence is available.

### Specification corrections and limits

- P1.6 event class weights add to 94, not 100. The specification now treats them as relative weights normalized by 94; actual scenario-driven counts are reported separately.
- Full RFC 8785 cross-implementation conformance NOT VERIFIED.
- Ed25519 signing/verification, key lifecycle and signed storage receipts NOT IMPLEMENTED.
- Negative vector catalog exists; not every listed fault path has executable coverage.
- 100k, burst, recovery, spool, cold restore and Root B independent-provider tests NOT RUN.
- No provider/region/retention/budget/key custody selected or authorized.
- Historical Dual Reconstruction remains UNAVAILABLE / BLOCKED; Option A unchanged; no Epoch activation, HWM/Daily Loss reset or exposure increase.
- T0 remains PAUSED; PAPER-only; `ai_execution_enabled=false`.

### Next step

Retrieve exact GitHub Actions run metadata and artifact evidence for the workflow triggered by P1.8 source/report. If no run exists, inspect GitHub Actions event/branch/path-filter configuration and correct only this isolated workflow. Do not switch CI platforms or access providers. After exact-head CI is verified, review remaining RFC 8785/crypto/fault-vector gaps as a separate local-only increment. Provider qualification and runtime integration still require separate approval.


### P1.8.1 run-descriptor environment provenance follow-up

- Generator source commit: `b55c851a5db3eb698d3ac68b073a825abcf55026`.
- Test commit: `bd558f0041302ef521ea6837e87923c17e3fceaa`.
- Implementation report update: `280437fcf73b7a34d0f0322dd0f09c1a1f73a8a2`.
- P1.6 specification update: `4f46b31bbfbfe3bac15b3fb904df01158f96f208`.
- Acceptance Plan update: `015172e0bb8050272962d03626f0290555d4faf5`.
- Evidence Inventory update: `82ec12cc50f8920d654c49f25ffd027f907d60cd`.

The run descriptor now includes OS, architecture, CPU model/count, sysconf-reported memory where available, explicit storage-medium NOT_MEASURED, runtime/tool versions and an unsigned-local hash/signature profile.

Reverification after the source change: 19/19 focused tests PASS; py_compile PASS; two 1,000-event fixture outputs byte-identical; SHA-256 manifest PASS.

The latest code/test source SHA is `bd558f0041302ef521ea6837e87923c17e3fceaa`. The workflow path filter includes the package, so this source update is eligible to trigger GitHub Actions. The GitHub Actions run ID, conclusion, checked-out SHA from job logs and artifact ID/digest remain NOT VERIFIED; no CI PASS is claimed.

No change to P1.8 approval boundary: provider qualification, persistent capture, account DB access and T0/T1 runtime integration remain unauthorized.



### P1.8 workflow-dispatch visibility fix (2026-11-07)

- User explicitly approved publishing only `.github/workflows/p1-8-synthetic-evidence.yml` to the repository default branch so GitHub exposes the manual workflow-dispatch control.
- Default branch: `main`. Before the change, the P1.8 workflow existed only on `feature/t0-centralized-data-feeder-p1-20261101`; it was absent from `main`.
- Current workflows on `main` were inspected before the change. No existing workflow was modified or removed.
- Created the exact workflow file on `main` with commit `f5b74affb8777953fa66d241784965fbb0e577ba`.
- Verified the `main` workflow blob SHA is `baec3b23057037a169a498eb4fed1e69336656f3`, identical to the feature-branch workflow blob; file contents compare byte-for-byte equal.
- Scope is workflow-dispatch discoverability only. No generator/source package, T0/T1 runtime, database, provider, credentials, execution policy, or trading behavior was copied or changed on `main`.
- No workflow run has been dispatched or verified yet. CI execution, checked-out source SHA, job results, artifact identity and digest remain **NOT VERIFIED**.
- Next: open the Actions workflow page; the Run workflow control should now be available. Select branch `feature/t0-centralized-data-feeder-p1-20261101` before dispatch so the run uses the feature-branch workflow and source. Reconcile run logs and artifact against the exact checked-out SHA.
- P1.8 remains synthetic-only; no provider qualification, persistent capture, T0/T1 runtime integration, or live execution is authorized. `ai_execution_enabled=false`.



### P1.8 GitHub Actions acceptance — PASS (2026-11-07)

- Workflow run: `42288889345`; job `128136820125`, `Deterministic local fixture contracts`; conclusion **success**.
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Exact checked-out source SHA: `90cd3cfe64bcac2f1fb238660e5264431c69d419`; checkout log, `git rev-parse HEAD`, smoke summary and run descriptor agree.
- Synthetic-only preflight PASS; database/exchange credential environment variables empty; `AI_EXECUTION_ENABLED=false`.
- Python compile PASS; focused tests **19/19 PASS**.
- Two 1,000-event fixtures byte-identical; local replay verified 1,000 events across 3 streams; 12 segments generated.
- SHA-256 fixture manifest: **17/17 PASS** in workflow logs and independently rechecked after downloading the artifact.
- Artifact ID `13539350402`, name `p1-8-synthetic-evidence-90cd3cfe64bcac2f1fb238660e5264431c69d419`, size 298,473 bytes, SHA-256 `7adee2525ab7690d8ce1792eb809b93a6a4b7cf02adb8f234bbc45793fe4dd76`, expires `2026-11-13T20:30:14Z`.
- Detailed evidence and limitations recorded in `docs/architecture/FORWARD_EVIDENCE_SYNTHETIC_GENERATOR_IMPLEMENTATION_2026-11-07.md`; report commit `9ac231467df7b4c66cab76e9cd1ba5ca2c427a09`.
- This PASS is limited to synthetic-only fixture contracts/reproducibility. Full RFC 8785 conformance, Ed25519/key lifecycle, execution of all negative vectors, 100k/burst/recovery/restore, Root B and provider durability remain NOT VERIFIED or NOT RUN. Descriptor explicitly records storage medium `NOT_MEASURED`.
- T0 remains PAUSED. No persistent capture, provider access, runtime integration, or live execution authorized; `ai_execution_enabled=false`.

Next step: a separate bounded synthetic-only increment for canonicalization/cryptographic/fault-vector gaps; do not expand to providers or runtime without explicit approval.


## 2026-11-07 — P1.8.2 Synthetic-only integrity tests

### Approval and scope

User explicitly approved: `APPROVE P1.8.2 — SYNTHETIC-ONLY INTEGRITY TESTS`.

Only `synthetic_evidence/test_generator.py` was changed for this increment; generator/runtime behavior was not changed. No T0/T1 production code, database, exchange, credentials, cloud provider, VPS, persistent capture, signing key, paper execution, or live execution was accessed or enabled. Existing GitHub Actions workflow and existing feature branch were reused; no new branch or PR was created.

### Commits and files

- First test-vector commit: `eeb68bf602d4967d769d47594337fc9f3ec38f7a` — GitHub Actions run 11 failed at Python compile due to incorrectly escaped literals in the newly authored test source. This was a test-code defect, not a generator defect.
- Corrected test source commit: `de0602dfb3daa999b06280e2044eecb1d76d45d1`.
- Evidence report update: `b5726da33f088070593deb074dcd5c442fdc4df9`, file `docs/architecture/FORWARD_EVIDENCE_SYNTHETIC_GENERATOR_IMPLEMENTATION_2026-11-07.md`.
- This handoff update is committed immediately after the evidence report; resulting commit SHA must be verified by GitHub read-back.

### Independent vectors and test coverage

- RFC 8785 §3.2.3 property ordering vector, including UTF-16 key order and non-BMP code points: https://www.rfc-editor.org/rfc/rfc8785.html
- RFC 4231 §4.2 HMAC-SHA-256 test case 1: https://www.rfc-editor.org/rfc/rfc4231.html
- SHA-256 known-answer vector; independent event/manifest hash domain separation.
- Strict-subset string escaping, nested object sorting, array-order preservation, float rejection, invalid UTF-8/JSON numeric rejection, event-hash tampering and sequence reordering.
- Focused suite increased from 19 to **29 tests**; 10 new tests cover the above cases.

### GitHub Actions evidence

- Workflow run: `42289567234`, run 12, event `push`: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42289567234
- Job: `128139126406`, `Deterministic local fixture contracts`, conclusion **success**.
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Exact checked-out/source SHA: `de0602dfb3daa999b06280e2044eecb1d76d45d1`.
- Synthetic-only preflight PASS; DB/exchange credential environment variables empty; `AI_EXECUTION_ENABLED=false`.
- Python 3.11 compile PASS; focused tests **29/29 PASS**.
- Two 1,000-event fixtures byte-identical; local replay verified 1,000 events over 3 streams; 12 segments.
- SHA-256 fixture manifest **17/17 PASS**, independently verified from downloaded artifact.
- Artifact ID `13539715524`; name `p1-8-synthetic-evidence-de0602dfb3daa999b06280e2044eecb1d76d45d1`; size 298,854 bytes; SHA-256 `4a2678b4e80aae0fc94681e42d8183f0a0a7548713dd5aed388bcca8e96c49c3`; expires `2026-11-13T20:34:57Z`.
- Downloaded ZIP independently hashed against GitHub artifact metadata; all 17 fixture manifest entries matched.

### Status and limits

**P1.8.2 synthetic-only integrity tests: PASS** for exact source SHA `de0602dfb3daa999b06280e2044eecb1d76d45d1`.

This is not full RFC 8785 certification. The implementation intentionally rejects floats; ECMAScript number-serialization vectors in RFC 8785 Appendix B are outside the current strict subset. No second-language implementation was run. Not all 13 catalogued negative vectors have executable coverage. Ed25519 signing/verification, key lifecycle, signed receipts, Root B, 100k/burst/recovery/restore, provider durability and production performance remain NOT IMPLEMENTED / NOT RUN / NOT AUTHORIZED as applicable.

T0 remains PAUSED; PAPER-only; `ai_execution_enabled=false`. No persistent capture, provider access, account DB access, T0/T1 runtime integration or live execution is authorized.

### Next step and approval boundary

P1.8.2 is complete for the bounded approved scope. Any expansion to full RFC 8785 floating-point support, signing/key custody, additional high-volume/recovery tests, provider qualification or runtime integration requires separate review and approval. Preserve current branch and evidence; do not merge without explicit approval.


## 2026-11-07 — P1.8.3 Synthetic-only Fault Injection (implementation in progress)

### Approval and scope

User explicitly approved: `APPROVE P1.8.3 — SYNTHETIC-ONLY FAULT INJECTION`.

Scope is limited to synthetic local reference models and the existing GitHub Actions workflow. No T0/T1 runtime, database, strategy, exchange, provider, VPS, credentials, persistent capture, signing/key management, or execution adapter is accessed or changed. Keep `ai_execution_enabled=false`; T0 remains PAUSED.

### Implementation commits and source

- RED test-first commit: `1a47718d28038f45d9adf0626c4d7d308262a27a` adds the fault contracts to the existing focused test module.
- Initial isolated harness commit: `d7b7f9603a7f5188aea7223d43c778c6ab95c24b`.
- Harness terminal-state correction: `d16419290a8a8e232f2e47c8218d4d0af32215a4`.
- Fault catalog naming commit: `07b4a136c5361ef4bb6b436069995a3a0e29ce95`.
- Latest test/catalog coverage commit: `16ccd8a3747ce9bf98e795d522d52a5adeca8155`.
- Evidence report update: `e4efd5c09b03b0dbca3085a5f3414b2e5df78e71`.

Files changed for the implementation:
- `synthetic_evidence/fault_injection.py`
- `synthetic_evidence/generator.py` (fault catalog identifiers only)
- `synthetic_evidence/test_generator.py`

The focused suite contains 36 tests total: 29 prior tests plus 7 new synthetic fault contracts.

### Fault contracts

- `UNKNOWN_FEE_FUNDING`: unknown fee/funding is rejected as incomplete input, not coerced to zero.
- `STALE_MARK`: missing/stale mark, unsafe future timestamp and excessive clock uncertainty are rejected.
- `CHECKPOINT_BOUNDARY`: late commit for an event at/before the checkpoint event-time boundary invalidates the checkpoint.
- `RECOVERY`: synthetic partial-fill/cancel/replace/final-fill replay, crash/restart equivalence, duplicate idempotency, changed-byte rejection and inactive-order late-fill rejection.

These tests exercise a separate synthetic reference model; they do not establish production T0/T1 ledger or recovery behavior.

### Verification state

- Latest implementation/test source SHA: `16ccd8a3747ce9bf98e795d522d52a5adeca8155`.
- Generator blob SHA: `ba179aebe14aabb177d05f36236a75d0cdfd6d88`.
- Test blob SHA: `fdb3369f916672173b681870c9f310b1872d5982`.
- Fault harness blob SHA: `0af64d3625e88e8e1334182364094b1227faec58`.
- GitHub Actions run/job/artifact identity and digest: **NOT VERIFIED**.
- Compile and 36/36 test result: **NOT VERIFIED** pending exact-source workflow evidence.

**P1.8.3 status: IMPLEMENTATION IN PROGRESS / CI NOT VERIFIED.** Do not mark PASS until the workflow checks out the exact source SHA, compilation and all tests pass, and artifact provenance is reconciled. Preserve this branch; no PR/branch split and no merge without explicit approval.


### CI failure and correction — 2026-11-07

Workflow run `42291124242` (job `128144496660`) checked out exact SHA `311e6810ab5c7388daefb34373e58b1271dcb592`. Preflight and compile passed. Of 36 tests, 35 passed and one failed: the recovery test expected order O2 to remain active after it had been fully filled. Replay correctly returned `active_order_id=None` for a terminal filled order.

Artifact `13540216092` (`p1-8-synthetic-evidence-311e6810ab5c7388daefb34373e58b1271dcb592`) was uploaded despite failure; size 2,529 bytes; SHA-256 `07ad0fa8301f16522cc671d7304f7986b0e0c65bdf9974660f5b8c4161a21674`. Reproducibility step was skipped, so this is not a successful evidence bundle. Logs confirm database/exchange credential variables empty and `AI_EXECUTION_ENABLED=false`.

Test expectation corrected in commit `101b4be4d868d64aca5c7d49c7758a52b888a83a`: terminal active ID must be null, with O2 separately asserted FILLED and quantity 7. No harness/runtime behavior changed. Awaiting push-triggered rerun.

**P1.8.3 remains BLOCKED pending exact-SHA rerun.** Do not mark PASS until the corrected source passes compile, all 36 tests, deterministic fixture/replay checks and artifact checksum reconciliation.


### P1.8.3 CI rerun — PASS (2026-11-07)

- Workflow run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42291352255
- Job: `128145290479`, `Deterministic local fixture contracts`, SUCCESS.
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Exact checkout/source SHA: `a64d7366a5d19dd0e8d70b8aa27db2b5e30aa841`; checkout log and `git rev-parse HEAD` agree.
- Corrected test blob: `7303eb823305f94cce17763acbc79dee458c59ab`; verified the corrected terminal FILLED assertions are present in this exact source.
- Synthetic-only preflight PASS; Python 3.11.18 compile PASS; **36/36 tests PASS**.
- Two 1,000-event fixtures byte-identical; each local replay verified 1,000 events across 3 streams; 12 segments; both smoke checks PASS.
- Workflow manifest validation 17/17 PASS. Downloaded artifact independently checked: 24 files, all 17 fixture manifest SHA-256 entries match.
- Artifact ID `13539157781`; name `p1-8-synthetic-evidence-a64d7366a5d19dd0e8d70b8aa27db2b5e30aa841`; size 299,039 bytes; SHA-256 `d9ea3cd456999c7948143a59b2166f702abc3e47ffd2c3a92f3bd6fea4c7321c`; expires 2026-11-13T20:47:44Z. Downloaded ZIP digest matches GitHub metadata and upload log.
- Run descriptor source SHA agrees with the workflow source SHA. It records Core 334 / AI 333 / Legacy 333; Python 3.11.18, Linux x86_64; storage medium NOT_MEASURED; JCS strict subset and unsigned local hash profile.
- DB/exchange credential variables empty; `AI_EXECUTION_ENABLED=false`.

**P1.8.3 status: PASS for the synthetic-only harness and stated CI contract.** This does not prove production T0/T1 ledger/recovery semantics, provider durability, cross-language JCS, Ed25519/signing, Root B, 100k/burst/recovery/spool/restore, performance or production readiness. T0 remains PAUSED. No persistent capture, provider/VPS, runtime integration, exchange, database or live execution authorized.


## 2026-11-07 — P1.8.4 Synthetic-only Execution Invariant Tests

- Approval: `APPROVE P1.8.4 — SYNTHETIC-ONLY EXECUTION INVARIANT TESTS`.
- Scope: standalone synthetic position transition model only. A reversal is accepted only after the prior position is explicitly reduced/closed to zero; it must reference the last closed position and use the opposite side. Duplicate identical events are idempotent; changed bytes under the same event ID are rejected. Crash/restart replay equivalence is covered.
- Test-first commit: `2d7ec90eeb9ae4e44878b42612758e9aaa6d9bdc`.
- Model commit: `584298321ec8db50b0b3bfad0e50c7e1e53d0912`.
- Current implementation/test source SHA: `cfea58b8db10b3cd5ea67f2bb1e113b06d823bd3`.
- Test blob SHA: `e325dd1ca98045ff41ecb79c8ad473d88e5d8447`.
- Model blob SHA: `2fe6a09ba0658535997ca4989fc097ef6bd37599`.
- Seven new test contracts; expected suite count 43 including the 36-test baseline.
- GitHub Actions exact-SHA compile/test/reproducibility/artifact evidence: **NOT VERIFIED**.
- The report commit `7feb357afacf0a7c602204e1a092dad3a639594b` changed the workflow-watched evidence-report path and is the expected triggering checkout SHA for the pending CI run; verify the actual checkout SHA from its logs.
- Status: **IMPLEMENTED / CI NOT VERIFIED**. Do not mark PASS until exact source checkout, all tests, deterministic fixtures/replay and artifact checksum are verified.
- Strict boundaries: synthetic-only. No T0/T1 runtime, Strategy Core, Shared Risk Engine, database, exchange, provider, VPS, credentials, persistent capture, execution adapter or live execution. `AI_EXECUTION_ENABLED=false`; T0 remains PAUSED.
- Next: inspect GitHub Actions evidence for exact SHA and reconcile artifact provenance. Preserve this branch; no merge without explicit approval.


### P1.8.4 CI correction and final status — PASS (2026-11-07)

- Failed workflow `42292467088`, job `128149126321`, exact checkout SHA `c2bd1303d13b7002184a2f23c7f90eabd72749cd`: compile passed; 42/43 tests passed. The sole failure was a test regex mismatch against the model's correct close-required error. The model was not changed.
- Test-only correction commit: `dd9f20b4269ea5f886d9470370c5279d4c7ad2ab`; test blob SHA `cd494b259e4cfa8c3b1245299072eaea31918100`. Assertions cover reduction greater than remaining quantity, reduction equal to remaining quantity (must use explicit close), and wrong active position.
- Passing workflow: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42292921593
- Job `128150725043`, `Deterministic local fixture contracts`, SUCCESS.
- Exact checkout/source SHA: `dd9f20b4269ea5f886d9470370c5279d4c7ad2ab`; checkout log, `git rev-parse HEAD`, and fixture descriptors agree.
- Synthetic-only preflight PASS; Python 3.11.18 compile PASS; **43/43 tests PASS**.
- Two byte-identical 1,000-event fixtures; each local replay verified 1,000 events over 3 streams and 12 segments; fixture manifest SHA-256 checks **17/17 PASS**.
- DB paths/exchange credentials empty; `AI_EXECUTION_ENABLED=false`.
- Artifact ID `13539664461`, name `p1-8-synthetic-evidence-dd9f20b4269ea5f886d9470370c5279d4c7ad2ab`, size 299,195 bytes, SHA-256 `17092da91d32c491be5a6b8885d7a4faa293354b69453207eec47d4f854f3050`, expires `2026-11-13T20:59:17Z`. Upload log and GitHub metadata agree; archive was not independently downloaded/re-hashed.
- Evidence report commit: `0e768c896d5e940f6a8327632e5accfab4c1d053`; report blob SHA `7bab9520dcfd6b73ccf4876358b630377b3428c6`.

**P1.8.4: PASS — synthetic-only execution invariant test scope only.** This does not certify production T0/T1 semantics, Strategy Core, Shared Risk Engine, provider durability, production readiness or live execution.

### Current boundaries and next step

T0 remains PAUSED. Keep `AI_EXECUTION_ENABLED=false`. No production runtime integration, database, exchange, provider/VPS, persistent capture or live execution is authorized. Preserve the existing branch; do not merge without explicit user approval.

Next bounded work requires a separately scoped proposal and approval. Do not infer that P1.8.4 PASS authorizes the next phase or any operational activation.


## 2026-11-07 — P1.8.6 Synthetic-only Concurrent Risk & Reservation Lifecycle

- User approval: `APPROVE P1.8.6`.
- Scope: synthetic reference model only; process-local thread serialization, concurrent reservation exposure and open-position cap tests, duplicate-intent concurrency/idempotency, release/expiry, snapshot export/restore and restart replay.
- Test-first contracts commit: `eb356050f46ec361aaa84ad3cd1cd910a3579a6b`.
- Initial implementation commit: `9b9ca8547bb341eafc44c558300027db8075c658`.
- Deterministic expiry test correction: `c2549a3259d9327d18af9d2bfcea939d5b4a0255`.
- Additional concurrent open-position-cap test: `ece18211d9c985940b91d082cf8e04613914561f`.
- Exact final passing source SHA: `ece18211d9c985940b91d082cf8e04613914561f`.
- GitHub Actions run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42299966689
- Job: `128174887497`, SUCCESS; checkout log and `git rev-parse HEAD` agree.
- Python 3.11.18 compile PASS; **63/63 tests PASS** (54 baseline + 9 P1.8.6 contracts).
- Two 1,000-event fixtures byte-identical; replay 1,000 events / 3 streams / 12 segments; fixture manifest checks PASS.
- Artifact ID `13542879430`; name `p1-8-synthetic-evidence-ece18211d9c985940b91d082cf8e04613914561f`; size 299,741 bytes; SHA-256 `b66d5f9457aeb43adff68aada1b48367c4c823db52b9028296eddac0090bae77`; expires 2026-11-13T21:50:17Z. Upload log digest agrees with GitHub metadata; ZIP was not independently downloaded/re-hashed.
- Evidence report: `docs/architecture/P1.8.6_CONCURRENT_RISK_RESERVATION_LIFECYCLE_SYNTHETIC_EVIDENCE_2026-11-07.md`; latest report commit `88eda9b965aa616991d95bfb369e5cada60fd3c4`.
- Initial RED run `42299752615` failed as expected before implementation. First implementation run `42299806573` exposed a test timestamp error (`second=60`); corrected in test-only commit. Intermediate exact-source run `42299818719` passed 62 tests; final run above adds and passes the concurrent open-position-cap contract.

**P1.8.6: PASS — synthetic reference model and exact-source CI contracts only.** The lock is process-local; no multi-process/distributed atomicity or durable persistence is proven. Snapshot serialization is not production crash-safe storage; SHA-256 is not an authenticated signature.

Restrictions: T0 remains PAUSED; PAPER-only; `AI_EXECUTION_ENABLED=false`. No Strategy Core/T1/T0 runtime integration, DB, exchange, provider/VPS, persistent capture, paper execution, or live execution. No merge. Next scope requires separate approval; specify cross-process transactional and crash-durability contracts before any production persistence or runtime integration.


## 2026-11-07 — P1.8.7 Synthetic-only Cross-Process Atomicity & Crash Consistency

- User approval: `APPROVE P1.8.7`.
- Scope: synthetic-only POSIX local-filesystem reference journal using process-shared `flock`, same-directory temp file, file `fsync`, atomic `os.replace`, and directory `fsync`.
- Test-first contracts: `91c0b535ad7a018f65ce8dbb65611403395ab42b`; initialization test correction `5cb0f92969680c496f9dfa2583e5eba4eebc47cb`.
- Initial journal implementation: `ee0419ca95188f683a314c4d3b5fc50b696112be`; missing-state correction `af2fc10277dc6f79eaeb83df1892bb89b5b94337`; after-replace test correction `8670c280d7757c77f3bd7f422c3d13a3c2840b3a`; lock syntax correction `df96c9618a36e9cee654076a64817745d29fb176`.
- Exact passing source SHA: `df96c9618a36e9cee654076a64817745d29fb176`.
- GitHub Actions run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42300485414
- Job: `128176661247`, SUCCESS; checked-out SHA agrees with source SHA in test artifact.
- Python 3.11.18 compile PASS; **69/69 tests PASS** (63 baseline + 6 new cross-process/crash contracts).
- Multiprocess exposure cap, position cap, crash-before-replace recovery, crash-after-replace idempotent replay, corrupt/missing state rejection PASS.
- Two 1,000-event fixture outputs byte-identical; replay 1,000 events / 3 streams / 12 segments; fixture manifest checks PASS.
- Artifact ID `13544390654`; name `p1-8-synthetic-evidence-df96c9618a36e9cee654076a64817745d29fb176`; size 299,837 bytes; SHA-256 `1e3748f88146c017e9a30b0b12fc013cbcbe6070e3323772ffa882e745a5b201`; expires 2026-11-13T21:54:13Z. Upload log digest agrees with GitHub metadata; ZIP was not independently downloaded/re-hashed.
- Evidence report: `docs/architecture/P1.8.7_CROSS_PROCESS_ATOMICITY_CRASH_CONSISTENCY_SYNTHETIC_EVIDENCE_2026-11-07.md`; report commit `53b30d1c41e68de90c8eb7111b1b09c9ed55cdd6`.
- Failed test-first/implementation runs retained: `42300259938` (expected RED, missing class); `42300317178` (state/init test issues); `42300401646` (compile syntax error). Final exact-source run above is the passing run.

**P1.8.7: PASS — synthetic POSIX local-filesystem reference model and exact-source CI contracts only.** This is not distributed locking, not network-filesystem validation, and not real power-loss/kernel-crash testing. No production database transaction, WAL recovery, or durable backup/restore is proven.

Restrictions: T0 remains PAUSED; PAPER-only; `AI_EXECUTION_ENABLED=false`. No T0/T1/Strategy Core runtime integration, DB, exchange, provider/VPS, persistent capture, paper execution, or live execution. No merge. Any production persistence/database integration requires a separate design and explicit approval.


## 2026-11-07 — P1.8.8 Synthetic-only Durability & Recovery Acceptance

- User approval: `phê duyệt` for P1.8.8.
- Scope: synthetic local POSIX file journal only; process-termination injection at after-temp-write, after-file-fsync, before-replace, after-replace, and before-directory-fsync; restart/reopen/recovery cycles; orphan temp cleanup; fail-closed handling of missing/corrupt authoritative journal.
- Test-first contracts commit: `cb2117b8635eaf7ac139fc41feb0390822a044d5`.
- Initial implementation attempt `41fc77bab98f7c131887a695227d7aee3e67723c` accidentally replaced existing model definitions and failed imports; corrected by restoring P1.8.7 source and applying targeted class-level changes.
- Exact passing source SHA: `c060dc061f910583f81d91bab1b0644734715d66`.
- GitHub Actions run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42300805695
- Job: `128177778298`, SUCCESS; exact checkout SHA matches source SHA.
- Python 3.11.18 compile PASS; **74/74 tests PASS** (69 baseline + 5 P1.8.8 contracts).
- Five write-boundary restart cases PASS; repeated restart ledger/exposure reconciliation PASS; orphan temp cleanup PASS; corrupt/missing state preservation and fail-closed recovery PASS.
- Two independent 1,000-event fixtures byte-identical; replay 1,000 events / 3 streams / 12 segments; fixture manifest checks PASS.
- Synthetic-only preflight PASS; DB/exchange credential variables empty; `AI_EXECUTION_ENABLED=false`.
- Artifact ID `13544470861`; name `p1-8-synthetic-evidence-c060dc061f910583f81d91bab1b0644734715d66`; size 300,085 bytes; SHA-256 `b562864af5712d957f818526549122304e25955b6abadf31d0bdf7246e121b24`; expires 2026-11-13T21:56:41Z. Upload log digest agrees with GitHub metadata; ZIP not independently downloaded/re-hashed.
- Evidence report: `docs/architecture/P1.8.8_SYNTHETIC_DURABILITY_RECOVERY_ACCEPTANCE_2026-11-07.md`; report commit `5198ac868c5219bec9b2ce13a44ec731ab32e25a`.
- Failed runs retained: `42300699235` (expected RED: missing recovery/fault API); `42300740160` (initial implementation accidentally replaced model definitions and failed imports). Final exact-source run above passes.

**P1.8.8: PASS — synthetic local POSIX journal durability/recovery acceptance only.** Process exit tests do not simulate power loss, kernel panic, controller cache loss, or filesystem corruption. No multi-host/network filesystem, production DB/WAL, backup/restore or real crash durability is proven.

Restrictions: T0 remains PAUSED; PAPER-only; `AI_EXECUTION_ENABLED=false`. No T0/T1/Strategy Core runtime integration, DB, exchange, provider/VPS, persistent capture, paper execution, or live execution. No merge. Any production persistence/database design requires a separate review and explicit approval.


## 2026-11-07 — P1.8.9 Synthetic Evidence Artifact Independent Verification

- User approval: `APPROVE P1.8.9 — SYNTHETIC EVIDENCE ARTIFACT INDEPENDENT VERIFICATION`.
- Downloaded GitHub Actions artifact `13544470861` from run `42300805695` to a local ZIP and independently computed SHA-256 from the downloaded bytes.
- Actual ZIP size: 300,085 bytes.
- Independently computed SHA-256: `b562864af5712d957f818526549122304e25955b6abadf31d0bdf7246e121b24`; GitHub artifact API digest: same value. **MATCH**.
- ZIP CRC/member integrity: PASS; no corrupt member reported.
- Artifact source SHA file, fixture run descriptor, and smoke summary all identify `c060dc061f910583f81d91bab1b0644734715d66`.
- Run `42300805695`: SUCCESS, event push, branch `feature/t0-centralized-data-feeder-p1-20261101`, exact head SHA `c060dc061f910583f81d91bab1b0644734715d66`; job `128177778298` SUCCESS.
- Artifact test log independently inspected: 74 tests, 1.306s, OK; compile and synthetic-only preflight markers PASS.
- Independently recomputed fixture A SHA-256 inventory: **17/17 PASS**; fixture A contains 1,000 event lines and 12 segments.
- Scope limitation: artifact archive contains fixture A only, not fixture B. The GitHub Actions job records the two-fixture generation/byte-comparison step as completed; fixture-B comparison was not independently repeated from the archived payload.
- Current branch head at verification: `aa4adb55ff7cbed590c43934328d327a23d8d042`. GitHub compare shows it is 2 commits ahead / 0 behind P1.8.8 source SHA; both intervening commits are documentation-only (P1.8.8 report and handoff).
- Detailed report: `docs/architecture/P1.8.9_SYNTHETIC_EVIDENCE_ARTIFACT_INDEPENDENT_VERIFICATION_2026-11-07.md`.
- **P1.8.9: PASS — downloaded artifact SHA-256, ZIP integrity, source identity and evidence-chain reconciliation.** This does not expand P1.8.8's synthetic-only assurance or prove real power-loss/production durability.
- No tests rerun, no source/runtime/workflow changes, no DB/exchange/VPS/provider, no persistent capture, no execution, no merge.
- T0 remains PAUSED; PAPER-only; `AI_EXECUTION_ENABLED=false`.



## 2026-11-07 — P1.8.10 Synthetic Fixture Independent Replay Verification

- User approval: `APPROVE P1.8.10 — SYNTHETIC FIXTURE INDEPENDENT REPLAY VERIFICATION`.
- Scope: offline independent verification of archived fixture A from P1.8.8 artifact `13544470861`; no source/runtime/workflow changes and no external service access.
- Artifact source SHA: `c060dc061f910583f81d91bab1b0644734715d66`; original GitHub Actions run `42300805695`, job `128177778298`, SUCCESS.
- Artifact ZIP SHA-256 was independently verified in P1.8.9 as `b562864af5712d957f818526549122304e25955b6abadf31d0bdf7246e121b24`.
- Separate offline verifier (not importing/calling the generator's `verify_local_replay`) parsed archived fixture A and independently recomputed canonical event hashes and manifest hashes.
- Results: fixture inventory 17/17; 1,000/1,000 event hashes; 3/3 stream sequence/hash/causation chains; global event ordering PASS; UUIDv5 event IDs 1,000/1,000; 12/12 segment byte digests; 12/12 manifest hashes; 3/3 manifest chains; segment-to-global-event byte equivalence 1,000/1,000; all stream sequence ranges gap-free; UUIDv5 manifest IDs 12/12; config SHA-256 MATCH.
- Stream counts: AI 333 events / 4 segments; Core 334 / 4; Legacy 333 / 4. Thirteen negative fault vectors remain outside the clean event denominator.
- Fixture B is not in the archived ZIP; the original workflow log records its two-fixture byte-comparison step as SUCCESS, but fixture-B comparison was not independently repeated from the artifact. No new GitHub Actions run was triggered for this offline replay.
- Detailed report: `docs/architecture/P1.8.10_SYNTHETIC_FIXTURE_INDEPENDENT_REPLAY_VERIFICATION_2026-11-07.md`; report commit `c972cfb5316714f07787e59ffb5680ee872a08b1`.
- **P1.8.10: PASS — independent offline replay/integrity verification of archived synthetic fixture A only.** This is not Root B/provider independence, signed evidence, production replay, or production durability certification.
- No runtime, DB, exchange, VPS/provider, persistent capture, paper/live execution, workflow rerun, or merge. T0 remains PAUSED; PAPER-only; `AI_EXECUTION_ENABLED=false`.


## 2026-11-07 — P1.8.11 Synthetic Dual-Fixture Reproducibility Acceptance

- User approval: `APPROVE P1.8.11 — SYNTHETIC DUAL-FIXTURE REPRODUCIBILITY ACCEPTANCE`.
- Scope: synthetic-only workflow/test change to retain both independently generated fixture A and B in one Actions artifact; no T0/T1 runtime or external services.
- Implementation SHA: `46c8904c1e7f0ac894b6133eabe7594adddb9e4c`; parent `b103ecae5314286f30cecd5b2bee20c348c8cb2d`. Files changed: `.github/workflows/p1-8-synthetic-evidence.yml` and `synthetic_evidence/test_generator.py`.
- GitHub Actions run `42301769109`, job `128181055508`, SUCCESS; exact head SHA matches implementation SHA. Python 3.11.18 compile PASS; **75/75 tests PASS**; synthetic-only preflight PASS; DB/exchange credential env vars empty; `AI_EXECUTION_ENABLED=false`.
- Workflow separately generates A/B, recursive `diff -qr`, validates each `fixture.sha256`, compares inventory files with `cmp`, records both inventory digests/counts and uploads both fixture directories.
- Artifact `13544597038`, size 596,834 bytes, SHA-256 `2bb873aa0b1f8f4d30ce9f8399851103c6d69161910c0005582bb43f0c12748c`; independently downloaded/re-hashed ZIP MATCH; ZIP integrity PASS.
- Artifact contains 42 files: A 18, B 18, top-level evidence 6. Independent comparison: complete relative paths equal; all **18/18 files byte-identical**; fixture A inventory 17/17 SHA checks; fixture B inventory 17/17 SHA checks; 1,000 event lines; 12 manifest lines. Both descriptor source SHAs match implementation SHA.
- A/B inventory-file SHA-256 both `f7679c14718ad1529fb9536379d48a7a0401c92bb552e2f22586c5ec18900ff9`; events JSONL SHA-256 `9496370af967460b9e9f8b8b87a4a88a5835deb2397b24faf31b48b74ca592ad`; manifests JSONL SHA-256 `3198fd42d036cb8902264cc4f6f2ce90d61383a275e49dfcc92fa0a7f78631e6`.
- Detailed report: `docs/architecture/P1.8.11_SYNTHETIC_DUAL_FIXTURE_REPRODUCIBILITY_ACCEPTANCE_2026-11-07.md`; report commit `29a2edb64c46b5c09e50550ad1141c6ce1476cc7`.
- **P1.8.11: PASS — dual-fixture generation, reproducibility, artifact inclusion and independent archive verification.** Does not establish Root B/provider independence, signed provenance, production durability, or production runtime correctness.
- No runtime integration, DB, exchange, VPS/provider, persistent capture, paper/live execution, or merge. T0 remains PAUSED; PAPER-only; `AI_EXECUTION_ENABLED=false`.


## 2026-11-07 — P1.8.12 Synthetic Evidence Provenance & Source Binding Acceptance

- User approval: `APPROVE P1.8.12 — SYNTHETIC EVIDENCE PROVENANCE & SOURCE BINDING ACCEPTANCE`.
- Scope: synthetic-only provenance record and fail-closed source/run/workflow/dual-fixture binding. No runtime or external data service.
- Final exact passing source SHA: `16f0edf2c93c45ef5ee479f74f6bb7a06e7358e3`.
- GitHub Actions run `42302581356`, job `128183815458`, SUCCESS; checked-out SHA exactly matches source SHA.
- Python 3.11.18 compile PASS; **81/81 tests PASS**; synthetic-only preflight PASS; DB/exchange credentials empty; `AI_EXECUTION_ENABLED=false`.
- Provenance workflow step PASS. Record binds source SHA, run ID `42302581356`, attempt 1, repository, branch ref, workflow ref, workflow SHA-256 `e4ca4bc5d968fb3c8fb36b478b830ac84ea2fd2751f375fc8365ea9b70e5de21`, and both fixture descriptor `generator_source_sha` values.
- Artifact ID `13544467848`, size 597,436 bytes, SHA-256 `f09f29e0e4ad1123264aa4925f3d3f22a0fa2a8e38107a8ced561990c8a0b040`; independently downloaded ZIP SHA-256 MATCH; ZIP integrity PASS; 43 members.
- Independent payload verification: provenance record present; fixture A/B each 18 files and 17/17 inventory checks PASS; relative path sets equal; 18/18 fixture file pairs byte-identical; both descriptors bind to exact source SHA.
- The provenance JSON marks artifact ID and payload digest `NOT_AVAILABLE_AT_BUILD_TIME` because GitHub assigns these after upload. Bind artifact ID/digest externally via GitHub metadata/report; do not claim self-referential in-archive digest.
- Initial/intermediate failed runs retained in the P1.8.12 report as audit history; final PASS applies only to exact source SHA and run above.
- Detailed report: `docs/architecture/P1.8.12_SYNTHETIC_EVIDENCE_PROVENANCE_SOURCE_BINDING_ACCEPTANCE_2026-11-07.md`.
- **P1.8.12: PASS — synthetic evidence source/run/workflow/dual-fixture provenance binding and independent artifact payload verification.** No signature, trusted timestamp, Root B/provider independence, production correctness/durability or runtime certification is implied.
- Restrictions unchanged: T0 PAUSED; PAPER-only; `AI_EXECUTION_ENABLED=false`; no DB, exchange, VPS/provider, persistent capture, runtime integration, paper/live execution, or merge.


## 2026-11-07 — P1.8.13 Synthetic Provenance Tamper & Substitution Resistance

- User approval: `APPROVE P1.8.13 — SYNTHETIC PROVENANCE TAMPER & SUBSTITUTION RESISTANCE`.
- Scope: synthetic-only hardening of provenance and artifact verification. No Strategy Core, AI Strategy, Shared Risk Engine behavior, T0/T1 runtime, DB/exchange, VPS/provider, persistent capture, paper/live execution, branch creation, PR, or merge.
- Final exact passing source SHA: `02f5857885378de1e9a385b810f7a5d2f9ccbaaf`.
- GitHub Actions run [42303757076](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42303757076), job `128187817102`, SUCCESS; checked-out SHA exactly matches final source SHA.
- Python 3.11.18 compile PASS; **88/88 tests PASS**; synthetic-only preflight PASS; DB/exchange credential env vars empty; `AI_EXECUTION_ENABLED=false`.
- Provenance schema advanced to `p1.8.synthetic-provenance.v2`. Both fixture descriptors bind exact `generator_source_sha` and SHA-256 of raw descriptor bytes. Verification rejects missing/invalid descriptor, descriptor swap, changed descriptor bytes, altered recorded digest, source mismatch, malformed provenance, run mismatch, and workflow digest mismatch.
- `verify_artifact_archive()` verifies externally anchored artifact SHA-256 and ZIP CRC/integrity; tests reject a substituted valid ZIP and corrupt ZIP.
- Workflow generates two deterministic 1,000-event fixtures, checks A/B byte equality, then verifies provenance against exact descriptor files. Provenance step marker: `PROVENANCE_SOURCE_RUN_WORKFLOW_FIXTURE_BYTES_BINDING=PASS`.
- Artifact ID `13545625743`; name `p1-8-synthetic-evidence-02f5857885378de1e9a385b810f7a5d2f9ccbaaf`; size 597,690 bytes; GitHub digest `sha256:106d4d961ebd8aecb02848a957f45cdfadae14be05681dc8134fd5db3dd87dba`. Independently downloaded ZIP SHA-256 MATCH; ZIP integrity PASS; 43 members.
- Independent payload verification: fixture A/B each 18 files; inventory 17/17 SHA checks for each; path sets identical; 18/18 file pairs byte-identical; both descriptor SHA-256 values independently recomputed and match provenance; both fixture source SHAs match exact source SHA.
- Intermediate RED/failing runs were retained as audit history; only run `42303757076` on exact source SHA above is the acceptance PASS.
- Detailed report: `docs/architecture/P1.8.13_SYNTHETIC_PROVENANCE_TAMPER_SUBSTITUTION_RESISTANCE_2026-11-07.md`; report commit `ae407475f965cb67fb0aa8291b677bbf1d474fd1`.
- **P1.8.13: PASS — synthetic provenance descriptor tamper/substitution resistance and artifact digest/ZIP integrity checks.**
- Limits: SHA-256 is integrity hashing, not a digital signature or trusted timestamp. Authenticity still depends on a trusted external expected artifact digest. Deterministic A/B fixture payloads are equal by design; distinct A/B descriptors are used in negative unit tests to prove label swapping is rejected. No Root B/provider independence or production certification is claimed.
- Restrictions unchanged: T0 PAUSED; PAPER-only; `AI_EXECUTION_ENABLED=false`; no DB/exchange, VPS/provider, persistent capture, runtime integration, paper/live execution, or merge.


## 2026-11-07 — P1.8.14 External Trust Anchor & Provenance Authenticity

- User approval: `APPROVE P1.8.14 — EXTERNAL TRUST ANCHOR & PROVENANCE AUTHENTICITY`.
- Scope: synthetic-only evidence archive signing and verification. No Strategy Core, AI Strategy, Shared Risk Engine behavior, T0/T1 runtime, DB/exchange access, VPS/provider, persistent capture, paper/live execution, branch creation, PR, or merge.
- Final exact passing source SHA: `19a6629212f2f98aaa08c4ebe6ceb68801881732`.
- GitHub Actions run [42304505004](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42304505004):
  - Build job `128190309262`: SUCCESS.
  - Independent verification job `128190419216`: SUCCESS.
  - Python 3.11 compile PASS; **94/94 tests PASS**; synthetic-only preflight PASS.
  - Dual 1,000-event fixture generation and byte equality PASS; source/run/workflow/fixture provenance binding PASS.
  - Database/exchange credential environment variables empty; `AI_EXECUTION_ENABLED=false`.
- GitHub `actions/attest@v4` created SLSA Build Provenance for `synthetic-evidence-bundle.zip`; signing certificate issued by Public Good Sigstore instance; signature uploaded to Rekor transparency log.
- Attestation ID `64691916`: https://github.com/kenznguyen/btcusdt-telegram-signals2/attestations/64691916
- Rekor log index `3725692138`: https://search.sigstore.dev?logIndex=3725692138
- Attested subject SHA-256: `b787505e8cb1949ce8294312a5a33050cc33a082412424e32cd87787344c16e6`.
- CLI verification constrains repository, exact signer workflow, source commit, source ref, GitHub OIDC issuer, and denies self-hosted runners. A separate GitHub-hosted job downloaded the artifact, verified its archive digest, then independently verified the Sigstore bundle and subject digest.
- Primary artifact ID `13546255148`, size 1,208,828 bytes, GitHub wrapper ZIP digest `sha256:14e157cd8a393a743e01e12a915ab69636cf7cb4765f8a331953daeef1987b6f`.
- Independent verification artifact ID `13545287609`, size 9,065 bytes, GitHub wrapper ZIP digest `sha256:418fff2ffa874003527db5d83d8717bf8946b489c4e3a62b023f4c5e5e6feedd`.
- Intermediate run `42304353210` failed only in independent verification because source package was not checked out; run `42304365377` failed because workspace was missing from PYTHONPATH after changing directory. Both defects were corrected. Only run `42304505004` on exact source SHA above is the final two-job acceptance PASS.
- Detailed report: `docs/architecture/P1.8.14_EXTERNAL_TRUST_ANCHOR_PROVENANCE_AUTHENTICITY_2026-11-07.md`; report commit `5d9bd56a72afd3398c2886f9a1ceb7b38bf0fea5`.
- **P1.8.14: PASS — Sigstore external trust anchor, Rekor transparency evidence, exact subject digest, signer/source identity constraints, and independent-runner verification.**
- Limits: the attestation binds the archive to the authenticated GitHub workflow identity; it does not certify correctness/safety of source or data. Workflow maintainers can still alter the workflow and what it attests. Offline verification requires a separately obtained and trusted Sigstore trusted-root bundle. No Root B/provider independence or production certification is claimed.
- Restrictions unchanged: T0 PAUSED; PAPER-only; `AI_EXECUTION_ENABLED=false`; no DB/exchange, VPS/provider, persistent capture, runtime integration, paper/live execution, or merge.


## 2026-11-07 — P1.8.15 Offline Attestation Verification & Trusted Root Pinning

- User approval: `APPROVE P1.8.15 — OFFLINE ATTESTATION VERIFICATION & TRUSTED ROOT PINNING`.
- Scope: synthetic-only Sigstore trusted-root acquisition, reviewed SHA-256 pinning, portable offline verification and network-isolated CI acceptance. No strategy, Shared Risk Engine behavior, T0/T1 runtime, DB/exchange, VPS/provider, persistent capture, paper/live execution, branch creation, PR, or merge.
- Final exact source SHA: `1f002a1769504d00c0894d67b5e1f35f46c97414`.
- GitHub Actions run [42305379372](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42305379372):
  - Build job `128193377184`: SUCCESS.
  - Independent offline verification job `128193528452`: SUCCESS.
  - Python 3.11 compile PASS; **102/102 tests PASS**.
  - Trusted-root acquisition and pin check before signing PASS.
  - Dual 1,000-event fixtures and byte comparison PASS.
  - Source/run/workflow/fixture provenance binding PASS.
  - Independent network-isolated offline verification PASS.
  - DB/exchange credential env vars empty; `AI_EXECUTION_ENABLED=false`.
- Trusted root acquired using `gh attestation trusted-root`, included in the signed subject archive with SHA sidecar. Reviewed pin in `synthetic_evidence/trusted_root_pin.py`:
  `65ca537f6ed8a47fd0e560c421baa1f6c1efb8b25fc200d8c5c02c0e92eb2b9c`.
- `synthetic_evidence/trust_anchor.py` checks raw digest against pin before parsing JSONL. `synthetic_evidence/verify_offline.sh` uses local artifact, local Sigstore bundle and local custom trusted root.
- Independent runner executes the reusable verifier inside `sudo unshare --net`; logs contain `TRUSTED_ROOT_PIN_VERIFICATION=PASS` and `OFFLINE_SIGSTORE_VERIFICATION=PASS`.
- Attestation ID `64694507`: https://github.com/kenznguyen/btcusdt-telegram-signals2/attestations/64694507
- Rekor log index `3725779480`: https://search.sigstore.dev?logIndex=3725779480
- Attested subject SHA-256: `cf62008062570e4ce296b2be67690006cf9c6459a360f1db2402eac4cfc9489d`.
- Primary artifact ID `13545188812`, size 1,219,111 bytes, GitHub artifact ZIP digest `sha256:2e7fd68f34143f5809278660498de17839e68127093d632361e596bdb1672f57`.
- Independent verification artifact ID `13546556454`, size 9,113 bytes, GitHub artifact ZIP digest `sha256:47b04a5c381a8f7b6dac372f29f8313f5068768c0b51e36088bd61d438d66cef`.
- Both artifacts expire `2026-11-13T22:31:41Z`; preserve separately for long-term retention.
- Final report: `docs/architecture/P1.8.15_OFFLINE_ATTESTATION_VERIFICATION_TRUSTED_ROOT_PINNING_2026-11-07.md`; report commit `3d4e48344c8da8def30b45669df675a88ef45ec4`.
- **P1.8.15: PASS — reviewed trusted-root SHA-256 pin, local bundle/root verification, network-isolated Sigstore verification and independent runner evidence.**
- Limits: pinned root can become stale after Sigstore rotation and cannot learn later revocations while offline. Root refresh must be separately reviewed and explicitly repinned. Offline repository-name comparison cannot detect later repository rename/name reuse. This is not Root B/provider independence or production certification.
- Restrictions unchanged: T0 PAUSED; PAPER-only; `AI_EXECUTION_ENABLED=false`; no DB/exchange, VPS/provider, persistent capture, runtime integration, paper/live execution, or merge.


## 2026-11-07 — P1.8.16 Trust Root Rotation, Revocation & Long-Term Evidence Retention

- User approval: `APPROVE P1.8.16 — TRUST ROOT ROTATION, REVOCATION & LONG-TERM EVIDENCE RETENTION`.
- Scope remained synthetic-only. No Strategy Core/AI Strategy/Shared Risk Engine changes, T0/T1 runtime, DB/exchange, VPS/provider, persistent capture, paper/live execution, new branch/PR, or merge.
- Exact tested source SHA: `99331fd263fb6840c3963d0ba316f18884f9d2c7`.
- Final GitHub Actions run [42306934521](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42306934521):
  - Build/synthetic contracts job `128198523248`: SUCCESS.
  - Independent offline Sigstore verification job `128198673591`: SUCCESS.
  - Git-history evidence archive job `128198727017`: SUCCESS.
  - Python compile PASS; **121/121 tests PASS**.
  - Current root pin PASS; root inventory comparison `UNCHANGED`; no automatic repin.
  - Snapshot history, P1.8.15 backfill, signed bundle, independent offline verification and retention manifest PASS.
- Root baseline SHA-256: `65ca537f6ed8a47fd0e560c421baa1f6c1efb8b25fc200d8c5c02c0e92eb2b9c`.
- Baseline root acquired in P1.8.15 run `42305379372`, source `1f002a1769504d00c0894d67b5e1f35f46c97414`, attestation `64694507`. Compressed snapshot and baseline metadata retained under `synthetic_evidence/trust_roots/`.
- Root rotation compares TLogs, CTLogs, certificate authorities and timestamp authorities; any byte/inventory change blocks CI. No automatic repin. Current root comparison is unchanged; a real production root rotation was not observed.
- Snapshot chain: `docs/evidence/p1-8/trust-root-snapshot-chain.json`; sequence 2; baseline snapshot SHA `4e0359abfcd28f3f118eb753f6e6260269c420dbe76f6c71fff6ea1a240d8a82`; current snapshot SHA `4220e467da161679ca6ee45cd7548e9439250d1eb3f0d39d1cfe4f6ea4d19d0e`; chain SHA `8724353e63c20f071600091b113ba2ac05b7663d6782c432e73a71a5f1e472f8`.
- Revocation policy is fail-closed:
  - offline: `NOT_CHECKED_OFFLINE`;
  - online TUF: `REVOCATION_STATUS_NOT_EXPOSED`;
  - reported revoked: `REVOKED_REPORTED / REJECT`;
  - reviewed clear: audit-only, remains blocked unless external evidence authenticity is separately verified.
  - Automated OCSP/CRL/advisory ingestion and external evidence signature verification are **NOT IMPLEMENTED / NOT VERIFIED**. The system never infers "not revoked" from missing evidence.
- P1.8.15 evidence backfill completed before artifact expiry:
  - primary artifact `13545188812`, independent artifact `13546556454`;
  - original subject SHA `cf62008062570e4ce296b2be67690006cf9c6459a360f1db2402eac4cfc9489d`;
  - offline Sigstore verification PASS;
  - combined retained archive SHA `1b8563eab22f8cff65ae98c106a9c77e31397eb9e29f80513ab2d33d88923bfe`.
- P1.8.16 attestation ID `64697921`: https://github.com/kenznguyen/btcusdt-telegram-signals2/attestations/64697921
- Rekor index `3725976921`: https://search.sigstore.dev?logIndex=3725976921
- Attested subject SHA-256: `c12671f0f54ec3983257d27eea140499a2b2941858c5e928a0351138ff80c1dd`.
- Primary artifact ID `13546338730`, size 3,710,871 bytes, outer artifact digest `sha256:467f286fee30d8340d55f5d98346c55bc1a51d7187ac67dcbafb68612ed4aae6`.
- Independent verification artifact ID `13546312762`, size 9,088 bytes, outer digest `sha256:a54e24fef24e61bbcecbafe77b69d0c81c16585ca4b0f57ddb1b230587ed6be9`.
- Retention manifest SHA-256 `9716632f116c9c5dcc80d3121cce353410649248f3e6dc4883296182e69808b2`; 12 payload entries independently rehashed.
- Artifact retention set to 90 days, subject to repository policy. Git archive is durable history but **NOT WORM**; external immutable/offline backup remains NOT VERIFIED.
- Archive path: `docs/evidence/p1-8/99331fd263fb6840c3963d0ba316f18884f9d2c7/`.
- Archive commit / branch HEAD at acceptance: `13cd69ac7959207d02c262e3f13b0a85b069af64`.
- Final report: `docs/architecture/P1.8.16_TRUST_ROOT_ROTATION_REVOCATION_LONG_TERM_RETENTION_2026-11-07.md`; report commit `5f032ac947607d25207c9f99118eda1e33a995e2`.
- **P1.8.16: PASS — trust-root rotation detection and fail-closed pinning, hash-chained snapshot history, conservative revocation semantics, P1.8.15 backfill and Git-history retention.**
- Substatus: rotation PASS; revocation fail-closed policy PASS; automated revocation source/authentication NOT VERIFIED; Git-history retention PASS; WORM/offsite backup NOT VERIFIED.
- Restrictions unchanged: T0 PAUSED; PAPER-only; `AI_EXECUTION_ENABLED=false`; no DB/exchange, VPS/provider, persistent capture, runtime integration, paper/live execution, or merge.


## 2026-11-07 — PostgreSQL Lifecycle / Provider Compatibility scope update

- Operator decision: **Backup and Disaster Recovery are DEFERRED — NOT IN CURRENT SCOPE**. No backup/PITR provisioning, backup jobs, restore drills, failover-recovery exercises, RPO/RTO measurement, offsite/WORM retention, or backup evidence collection is authorized in the current workstream.
- This is a scope deferral, **not PASS**, not a claim that backups are available, and not production-readiness certification. Earlier handoff entries and architecture documents that list Backup/DR as future production gates remain historical context; this newer decision controls the current scope.
- Current PostgreSQL work is limited to:
  1. **Lifecycle** on disposable/synthetic PostgreSQL/TimescaleDB: connection/pool behavior, explicit initialization/migrations, writer transaction atomicity/rollback, lease acquire/heartbeat/expiry/release, fencing generations and stale-writer rejection, runtime recovery/restart, readiness fail-closed, shutdown/drain, and controlled concurrency/fault injection.
  2. **Provider compatibility** only after a provider is separately selected/approved: exact PostgreSQL/TimescaleDB versions, TLS CA/SAN/verify-full, private networking/ingress, effective roles/grants, credential rotation/revocation, connection limits/timeouts, migration/extension privileges, and failover endpoint interruption/fencing compatibility. Provider-specific claims remain NOT VERIFIED until tested against that exact provider/tier.
- Transaction rollback, atomic writes, lease fencing, stale-writer prevention, readiness closure, and ordinary process restart remain in scope. These are lifecycle/data-integrity controls, not Backup/DR proof.
- Updated checklist: `docs/T0_STAGING_ACCEPTANCE_CHECKLIST.md`; documentation commit `a8c70073f6c2c9deba92c667381457695d7e7187`; new blob SHA `5beb075ea4c39c8a72751545c2e271157a98701f`.
- Checklist now marks Gate F **DEFERRED** and excludes it from the current scoped staging verdict. Gates A–E and G remain applicable to a future provider-specific staging acceptance; a scoped PASS would not imply Backup/DR or production readiness.
- Repository branch: `feature/t0-centralized-data-feeder-p1-20261101`. Branch HEAD before these documentation commits was `7eefc7f13fe29670e68a898569fb480522f390d0`.
- Work performed: documentation-only. No code, SQL migrations, workflows, runtime configuration, tests, database, credentials, VPS/provider, backup service, Feeder, exchange connection, or market-data sync was changed/run.
- Evidence status: **DOCUMENTATION UPDATE PASS** (GitHub accepted the file update). Tests/workflows: **NOT RUN**. PostgreSQL lifecycle end-to-end current-tip CI: **NOT VERIFIED**. Exact-provider compatibility: **NOT VERIFIED / PROVIDER NOT SELECTED**. Backup/DR: **DEFERRED**.
- Next permitted step: prepare a lifecycle-only disposable PostgreSQL acceptance matrix and identify the existing tests/gaps. Do not provision provider staging, activate Feeder, create/open canonical T0 storage, connect an exchange, or sync market data without separate explicit approval.
- Safety remains unchanged: T0 remains independent; paper-only; `ai_execution_enabled=false`; no live orders.

- Checklist follow-up correction: removed the retired backup/restore drill content from Gate F and removed backup-freshness dependencies from Gate G; only the explicit DEFERRED notice remains. Latest checklist commit: `873cd05c2aa36728f227522b7a2669430870520c`; blob SHA: `bece714ef5a5a5fabd847ebd012218379837fc35`.


## 2026-11-07 — PostgreSQL Lifecycle Acceptance Matrix

- Added `docs/T0_POSTGRESQL_LIFECYCLE_ACCEPTANCE_MATRIX.md` on the existing branch.
- Matrix commit: `3f11b94ef30f47146452e5676afd53bc53f6cbce`; current matrix blob SHA: `2c26ae724f61d5c2f098d6537dd1e4dc4a286475`.
- Scope is lifecycle-only and synthetic/disposable CI. Backup/DR remains DEFERRED; provider/VPS provisioning, canonical DB, production Feeder, exchange connection and market-data sync remain unauthorized.
- Mapped existing PostgreSQL tests: runtime composition/startup recovery, heartbeat, lease takeover/readiness, drain timeout, generation restart, atomic writer/rollback, role/privilege and fresh-cluster bootstrap.
- Historical evidence recorded in the matrix is limited to workflow #42166319563 at exact source SHA `7c41ac990a7a0842b773a2d07b8db2f1d769a855`: writer 7/7, FeederRuntime/composition 18/18, lifecycle 4/4, role integration 18/18, read-only integration 6/6 PASS; fresh-cluster bootstrap BLOCKED. No result is promoted to the current branch tip.
- Explicit lifecycle gaps listed as NOT VERIFIED: DB unavailable at startup; connection loss during heartbeat/lease checks; disconnect during an in-flight transaction; pool exhaustion/timeouts; safe behavior after transient outage; process kill during a PostgreSQL writer transaction; interrupted migration retry; readiness under DB connectivity loss.
- Next sequence: review runtime state transitions/timeouts, then add one focused RED lifecycle test at a time. Do not implement automatic reconnect/resume without a source-derived state-machine decision.
- Work performed: source/test/documentation inspection and matrix documentation only. No code, SQL, workflow or runtime configuration changed; no tests/workflows were run.
- Current verdict: matrix DOCUMENTED; current-tip CI NOT VERIFIED; provider compatibility NOT VERIFIED; PostgreSQL 16 non-superuser CREATEROLE bootstrap BLOCKED; Backup/DR DEFERRED.


### PostgreSQL lifecycle source review — first RED candidate (2026-11-07)

- Read-only source review of `market_data/feeder.py`, `market_data/feeder_service.py`, and `market_data/postgres.py`; source blobs: feeder `f782a75e01394a21f2bb3c987909951b83d23642`, feeder_service `0b7c44d538af5f2899d3d184b7d9b65ce87dd803`, postgres `2fe27fe2d066dda0c192a381b72d27404487b800`.
- Connection model correction: the PostgreSQL adapter opens a fresh psycopg connection per operation; it has no pool. Connection timeout is 5 seconds, statement timeout 5 seconds, lock timeout 5 seconds. Do not create a pool-exhaustion test for a pool that does not exist; test bounded connect failure/concurrent connection churn instead.
- First candidate lifecycle gap: `FeederRuntime.start()` sets state to STARTING and invokes `lease_store.acquire()` before its startup `try` block. A database connection exception therefore propagates while the runtime remains STARTING; scheduler admission does not start, but this runtime cannot be started again because start accepts only NEW. Health remains non-ready, but terminal-state handling and diagnostics are untested.
- Proposed first RED test: inject PostgreSQL `StoreUnavailable` from lease acquisition; assert fail-closed startup, scheduler never starts, no release is attempted for a lease never acquired, and runtime transitions to a deterministic terminal failure state. This is a test proposal only; no test or source behavior has been changed.
- Heartbeat and `run_once()` already route connection exceptions to `on_lease_lost()`; scheduler admission stops. Add a separate DB-disconnect regression later to prove this path, but do not implement automatic reconnect/resume without a reviewed state-machine contract.
- Updated matrix commit: `3a8413f11a1e82a73ac9ac11127846989ebf7773`; matrix blob: `3f09a46eadd59ad693c0e36fa744f5aaa3d3a488`.
- No tests/workflows were run; no runtime/database/provider/Feeder/exchange activity occurred.
- Next decision: approve or revise the focused RED test for startup DB-unavailable behavior before changing tests or runtime logic.


## 2026-11-07 — PG-LC-01 startup database-unavailable RED

- User said “tiếp theo” after the focused RED test proposal; proceeded with the test-only increment.
- Added `FeederRuntimeStartupFailureTest.test_database_unavailable_during_lease_acquire_fails_closed` in `market_data/test_postgres_feeder_runtime.py`. Test source commit: `514d22b00097f8b3af87e04904ca0f92b3a38b8d`; test file blob: `b8de3d99bbcaacfd07a49bfd999594089cec1611`.
- Test injects PostgreSQL `StoreUnavailable` from `lease_store.acquire()` and requires deterministic `FAILED`, no scheduler start, no release of an unacquired lease, and no readiness mark.
- GitHub Actions run [42321683647](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42321683647), event push, branch `feature/t0-centralized-data-feeder-p1-20261101`, head/checked-out source SHA `514d22b00097f8b3af87e04904ca0f92b3a38b8d`.
- Job `128247465461` (Static Gateway contract verification): compile PASS; 10/10 static contracts PASS; 63/63 behavioral/feeder regression PASS; 21/21 health/readiness PASS; 2/2 process restart PASS; full market_data suite **RED as intended**: 234 tests, 1 failure, 37 skipped. Failure is exact assertion at test line 474: expected state `FAILED`, observed `STARTING`.
- Artifact `13553666452`, name `t0-swg-contract-evidence-514d22b00097f8b3af87e04904ca0f92b3a38b8d`, 10,877 bytes, digest `sha256:2c1e1ab498ef0aab199f1dce0c3e4d7f8dcd4e62ab130ce481332e16e81b9b1a`; downloaded ZIP independently hashed and matched GitHub digest.
- Paper consumer job `128247465359`: SUCCESS. TimescaleDB integration job `128247550839`: SKIPPED because its dependency `shadow-contracts` failed on the intended RED test; no PostgreSQL integration PASS is claimed from this run. Fresh-cluster provider bootstrap job `128247465188` was still running at the time of evidence capture; final workflow conclusion not yet available.
- Updated matrix commit: `3e9ee0850cf59fcec48f4a11e6ea7c9f5cf9670b`; matrix blob `89bc0db0f898d3438e3a6dfe986befc14bc13f30`.
- Runtime implementation remains unchanged. No database/provider/VPS/Feeder/exchange/market-data operation occurred. The RED result is the expected proof of PG-LC-01 defect, not a regression in the existing passing focused suites.
- Next: minimal GREEN fix should catch lease-acquisition exceptions, set runtime state to terminal `FAILED`, emit a non-sensitive startup failure event, re-raise the original exception, and never release a lease that was not acquired. Then run the same exact-head GitHub Actions regression and reconcile all jobs/artifacts.


## 2026-11-07 — PG-LC-01 GREEN and disposable TimescaleDB verification

- Minimal runtime fix committed on existing branch: `market_data/feeder.py`, commit/source SHA `819d5f843e6d1d7cac9326b2173c9e2b01c89ce4`, blob `0b4362cc4b588f610e0dd5460cb4edcc9f728001`. If `lease_store.acquire()` raises, runtime now sets terminal state `FAILED` and re-raises the original exception. No lease release is attempted because no lease was acquired. Scheduler is not started; readiness is not marked ready. No reconnect/resume behavior was added.
- GREEN workflow [42321809275](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42321809275), push event, branch `feature/t0-centralized-data-feeder-p1-20261101`, exact head and checked-out SHA `819d5f843e6d1d7cac9326b2173c9e2b01c89ce4`.
- Job `128247868529` Static Gateway contract verification: SUCCESS. 234 market_data tests, 37 skipped, overall OK; static Gateway contracts 10/10; behavioral/feeder regression 63/63; health/readiness 21/21; process restart 2/2.
- Job `128247942819` Isolated TimescaleDB read-only integration: SUCCESS. Atomic writer 7/7; PostgreSQL FeederRuntime 19/19 (includes PG-LC-01); runtime lifecycle 4/4; least-privilege roles 18/18; read-only TimescaleDB 6/6. Service was disposable `timescale/timescaledb:2.17.2-pg16`, loopback-only, synthetic test data.
- Job `128247868818` Paper consumer fixture regressions: SUCCESS.
- Job `128247868783` Fresh-cluster restricted provider bootstrap: FAILURE / existing BLOCKED issue. Exact diagnostic: PostgreSQL 16 grants `t0_migrator` to bootstrap login with ADMIN OPTION, while `_assert_writer_roles_safe()` requires `t0_migrator` only be granted to ephemeral `t0_migrator_login`. This is the already-known strict role-guard conflict. Do not weaken the guard or modify grants to force green.
- Workflow overall conclusion: FAILURE due only to the known provider bootstrap job. The lifecycle/static and disposable TimescaleDB jobs passed. This is not a provider compatibility PASS.
- Independently downloaded and SHA-256 reconciled artifacts:
  - Static contracts: artifact `13553462059`, 10,665 bytes, digest `sha256:f9d7fff493ed3767759ff67d529784ff3d11a0435699033708e50c536f2ac0a2` (downloaded ZIP hash MATCH).
  - TimescaleDB integration: artifact `13553532015`, 4,286 bytes, digest `sha256:e371ec5f6cf437b9c4f4f4dca9303c8207a1528a6fdfd70465bbde4350c3ee38` (downloaded ZIP hash MATCH).
  - Provider bootstrap failure evidence: artifact `13553820702`, 1,043 bytes, digest `sha256:13ca3c7b578d21ebcc87f319c58d07746d3ab2666505a165870a36fede984b69` (downloaded ZIP hash MATCH).
- PG-LC-01 is now **PASS** with a verified RED/GREEN cycle. Matrix updated in commit `e4e86612476e9630f98fad734175e044e48bd619`, blob `f37577650c74c72916c25809d987d493accbfd6b`.
- Scope remained synthetic/disposable only. No provider/VPS, canonical T0 DB, production Feeder, exchange credentials, exchange connection, market-data sync, backup/DR, or live order activity occurred. `ai_execution_enabled=false` unchanged.
- Next: continue with PG-LC-02, a focused test proving that a PostgreSQL connection exception during heartbeat/lease validation closes readiness and scheduler admission. Keep the PostgreSQL 16 role bootstrap BLOCKED and separate from this lifecycle pass.


## 2026-11-07 — PG-LC-02 heartbeat connection-loss regression

- Added `FeederRuntimeHeartbeatFailureTest.test_database_unavailable_during_heartbeat_closes_runtime_readiness` to `market_data/test_postgres_feeder_runtime.py`, commit/source SHA `be29c78a451c23b746da1e014b7f9675d12ed23a`, test blob `dba7b3a61b3963984c58309e7d334b61c0889256`.
- The test injects `StoreUnavailable` on heartbeat after a successful synthetic lease acquisition and verifies state `LEASE_LOST`, scheduler stopped, health `mark_not_ready`, no lease release, and health snapshot `lease_valid=false`.
- GitHub Actions run [42322039770](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42322039770), push event, exact head/checked-out SHA `be29c78a451c23b746da1e014b7f9675d12ed23a`.
- Static job `128248620046`: SUCCESS; full market_data suite 235 tests, 37 skipped, OK; static contracts 10/10; behavioral/feeder regressions 63/63; health/readiness 21/21; process restart 2/2. Paper consumer job `128248620196`: SUCCESS.
- Static artifact `13553276962`, size 10,688 bytes, GitHub digest `sha256:95d849d560435e295c1543edb02ed6e7c02b67c77c14e2d92141f85c6b434c8b`; downloaded ZIP independently hashed and matched.
- Disposable TimescaleDB integration job `128248711729` had not yet progressed beyond container initialization at evidence capture. Therefore PG-LC-02 is **UNIT PASS / PostgreSQL integration NOT VERIFIED** on this SHA. Provider bootstrap continues to show the known PostgreSQL 16 role-membership blocker; do not weaken the guard.
- Matrix update commit `3ece1952899a4bfebf87ac2bd48f15e1516720ba`, blob `ac773e861a4b78eacb928775df4b519a2f73ab9f`.
- No runtime code change in this increment; no provider/VPS/canonical DB/production Feeder/exchange/data-sync/Backup-DR activity.
- Next: finish exact-SHA integration reconciliation for run `42322039770`. If the TimescaleDB job remains blocked by CI infrastructure, record it as INTERRUPTED/NOT VERIFIED rather than assuming pass. Then select PG-LC-03 (disconnect during in-flight writer transaction) only after the current run's evidence is reconciled.


### PG-LC-02 exact-SHA TimescaleDB integration reconciliation (2026-11-07)

- Workflow [42322039770](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42322039770) completed with overall FAILURE because the independent fresh-cluster PostgreSQL 16 provider-bootstrap job remains BLOCKED by the known implicit ADMIN membership issue. Do not weaken the strict role guard.
- Exact source SHA `be29c78a451c23b746da1e014b7f9675d12ed23a`.
- Disposable TimescaleDB job `128248711729`: SUCCESS. PostgreSQL writer 7/7, FeederRuntime 20/20 (includes the new heartbeat-disconnect regression), runtime lifecycle 4/4, role privileges 18/18, read-only TimescaleDB 6/6 — all PASS.
- Static job `128248620046`: SUCCESS; 235 market_data tests, 37 skipped, OK; static contracts 10/10; behavioral/feeder regressions 63/63; health/readiness 21/21; process restart 2/2. Paper consumer job `128248620196`: SUCCESS.
- TimescaleDB artifact `13552858688`, size 4,311 bytes, GitHub digest `sha256:fb6c74adafc2dbec72ad07b35425562883889871207641bd2a5e9e4f7bf6b838`; downloaded ZIP SHA-256 independently matched.
- Provider bootstrap artifact `13553895631`, digest `sha256:71200e2a7999d5af590abfb661d25aa5ab01b7977b6e0507a4b18b7d7bf1b2ae`; failure is same PostgreSQL 16 implicit ADMIN membership conflict.
- PG-LC-02 status upgraded to **PASS** for unit and disposable TimescaleDB integration. Matrix update commit `0c73efb197c2c02890a4d4195c88a649a8edf6c3`, blob `b4e27032602b41a637593f1eda6b9629465793d5`.
- No provider staging, VPS, canonical DB, production Feeder, exchange connection, data sync or Backup/DR activity.
- Next lifecycle gap: PG-LC-03 — database disconnect during an in-flight PostgreSQL writer transaction. Inspect existing gateway transaction boundaries and available fault-injection hooks before adding a deterministic test; do not add automatic retry/replay or alter idempotency/fencing semantics without evidence.


## 2026-11-07 — PG-LC-03 in-flight writer disconnect test

- Source/test commit `adcd9d369bc57b854974a3ee37689217fec89bf6`; test file `market_data/test_postgres_write_gateway.py`, blob `36f1b9c660100706cb8f19ad8131444f22206d58`.
- Added disposable TimescaleDB fault-injection test `test_connection_termination_during_batch_rolls_back_prior_rows`: a trigger delays the second candle after the first has been inserted inside the same transaction; test identifies the active writer backend, terminates that connection, expects `StoreUnavailable`, and verifies zero rows from the interrupted two-candle batch.
- Workflow [42322291792](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42322291792), exact source SHA `adcd9d369bc57b854974a3ee37689217fec89bf6). Static job `128249430994` SUCCESS; full market_data suite 236 tests, 38 skipped, OK. The new integration test is skipped in this job because no disposable DSN is configured.
- Static artifact `13552913986`, 10,716 bytes, digest `sha256:769e7feae1c7cf9cb7c52607cfdca7bc382fe20984759cd2ee3ba5cd59bfb0e3`; downloaded ZIP independently hashed and matched.
- Disposable TimescaleDB job `128249502313` was still at `Initialize containers` at documentation time. PG-LC-03 remains **NOT VERIFIED** until that job executes the new fault-injection test. No assumption of pass is allowed.
- Matrix update commit `50b6ad829dc6a57df0b6c9e7e977953354206f0a`, blob `4e1d9d31d75744a4a27fc92c8fa505a75f76ff79`.
- No production code changed in this increment. No external provider/VPS, canonical DB, production Feeder, exchange, data sync or Backup/DR activity.
