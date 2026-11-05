# Five-Layer System — Session Handoff

Last updated: 2026-11-03 (Asia/Ho_Chi_Minh)

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
