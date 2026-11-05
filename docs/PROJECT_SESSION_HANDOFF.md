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
