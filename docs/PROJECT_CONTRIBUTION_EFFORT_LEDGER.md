# Project Contribution & Effort Ledger

Last updated: 2026-11-15 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Status: **PARTIAL — PERIODIC RECONCILIATION; NOT A TIME AUDIT**

## 1. Purpose

This ledger records the human and AI contributions to BTCUSDT Quant System / the Five-Layer System. It is intended to make project effort, decisions, implementation, verification, and remaining uncertainty auditable over time.

GitHub is the source of truth. This ledger must be updated from repository history, workflow evidence, artifacts, project handoffs, and user-confirmed work records—not from conversational impressions alone.

## 2. Attribution rules

### Project owner (user)

The user is the project owner and final decision-maker. Attribute to the user:
- Product vision, goals, priorities, and scope.
- Architecture and operating constraints approved by the user.
- Acceptance/rejection of proposals and authorization gates.
- Hands-on work performed in GitHub, Git, Termux, VPS, exchange connectivity probes, and other environments when supported by user-provided or machine-generated evidence.
- Final responsibility for project direction and operational decisions.

### ChatGPT

Attribute to ChatGPT as AI-assisted work:
- Architecture options, technical analysis, design proposals, and critical review.
- Drafting code, tests, scripts, documentation, plans, and evidence matrices.
- Debugging hypotheses and interpretation of logs/test output.
- Test design, test-result analysis, risk review, and handoff preparation.
- Context synthesis across project sessions.

A suggestion or generated patch is not proof that code was applied, committed, executed, or accepted. Attribute implementation only when repository history or other evidence establishes it. Attribute a test result only to the exact source and execution context shown by its evidence.

### Joint / unallocated work

Use **JOINT** where the record shows iterative human-AI collaboration but does not support a defensible split. Do not force percentage allocations merely to make a chart look complete.

## 3. Time and effort accounting

### Current finding

**Exact cumulative hours: NOT VERIFIED.**

The available conversation and repository evidence show sustained, intensive work across multiple sessions and workstreams. They do not provide a complete time sheet, reliable session start/stop times, or a record of offline thinking and execution. Therefore:
- Do not publish a precise total-hour figure.
- Do not convert message count, token count, commit count, or elapsed calendar days into work hours.
- Do not infer that every commit or test represents a separate block of labor.
- Keep calendar span, active-session count, verified execution time, and estimated effort as separate measures.

### Evidence-supported activity window

The currently available project record contains work and repository history from at least **2026-10-24 through 2026-11-09**. This is an observed evidence window, not proof of continuous work on every day and not a duration estimate.

### Future time-recording method

For each future work session, record where possible:
- Session date and timezone.
- Start/end timestamps or a measured duration.
- Workstream and task identifier.
- Actor: USER, CHATGPT, or JOINT.
- Work performed and resulting deliverable.
- Evidence reference: commit SHA, PR, workflow run, artifact, test log, or user-confirmed offline work.
- Whether the duration is measured, user-estimated, or unknown.

Never backfill fabricated durations. Historical sessions without reliable timestamps remain **UNMEASURED**.

## 4. Contribution assessment at baseline

| Area | User contribution | ChatGPT contribution | Evidence boundary |
|---|---|---|---|
| Product vision and priorities | Owns and approves | Helps clarify and challenge | User decisions in project conversations and handoffs |
| Five-layer architecture | Approves system boundaries and sequencing | Produces analysis and design alternatives | Handoff and accepted architecture decisions |
| T0 data foundation | Sets independence/reliability requirements; performs environment operations and authorizes gates | Designs contracts, reviews lifecycle/fencing, analyzes test evidence | Repository history, CI runs, VPS/Termux evidence |
| T1/T2 and Dual-Strategy Intelligence | Defines Core/AI separation and shared risk constraints | Helps design strategy interfaces, ledger separation, risk gates, and tests | Strategy decisions and branch/test records |
| Safety and risk controls | Sets paper-only boundary and approval requirements | Helps formalize fail-closed behavior and verification cases | Explicit project constraints and test evidence |
| Implementation | Applies/approves changes and operates project environments where evidenced | Drafts code and implementation plans; may assist with patches | Commit authorship and exact source history required |
| Verification | Authorizes and performs or triggers real checks | Designs tests and interprets results | Workflow run, checked-out SHA, logs, artifacts |
| Project governance | Owns acceptance and merge/deployment decisions | Maintains checklists, evidence summaries, and handoff drafts | GitHub approvals, handoff, and PR history |

Qualitative assessment: the user's contribution is **foundational and accountable** because the user supplies the project intent, makes binding decisions, provides real-environment execution, and controls acceptance. ChatGPT's contribution is **substantial technical assistance** across analysis, design, coding support, testing, and documentation. These are different kinds of contribution and should not be reduced to an unsupported numerical split.

## 5. Evidence-backed milestones known at baseline

The following are selected milestones already present in project context. They are not a complete inventory and should be expanded only after source/evidence reconciliation.

### Project direction and architecture
- Five-layer system direction established, with T0 treated as an independent data asset.
- Reliability prioritized over speed of commercialization.
- T0 → T1 → T2 sequencing established; later layers remain conditional on stability.
- Paper-only / analysis-signals boundary retained during testing; `ai_execution_enabled=false`; no live orders authorized.
- Dual-Strategy Intelligence defined with separate `CORE_LEDGER` and `AI_LEDGER`, Core RSI + ADX + Smart DCA, independent AI LONG/SHORT signals, and a shared risk engine. These decisions are architecture requirements, not proof of production readiness.

### T0 engineering and verification
- Scheduler suite: 15/15 recorded PASS.
- Retry/recovery suite: 37/37 recorded PASS.
- Lease suite: 10/10 recorded PASS (recorded TTL 60 seconds; heartbeat 15 seconds).
- Health suite: 20/20 recorded PASS.
- Binance USD-M read-only connectivity probe: REST 5/5 and WebSocket 101 recorded PASS on 2026-11-07; no credentials, database, Feeder, or persistence were used in that probe.
- PostgreSQL/TimescaleDB disposable CI evidence is recorded in the project handoff, including writer/runtime/role/read-only integration suites. This is not production provisioning or certification.
- Canonical T0 database creation, production Feeder activation, VPS deployment, backup/PITR and full restore acceptance remain subject to separate verification and authorization.

### GitHub governance and evidence discipline
- GitHub Actions is the default CI platform; Codemagic is fallback-only under a documented blocker and explicit authorization.
- Workflow conclusions must be tied to exact source/checkout SHA, run ID, event, logs, and artifact identity.
- PR merge-context runs must not be described as direct-head runs.
- Artifact metadata digests must not be described as independently recomputed payload hashes unless the payload bytes were actually downloaded and hashed.
- PR #134 T0 atomic-write-fencing / role-security change was merged with explicit user approval on 2026-11-06. Its merge commit and CI limitations are recorded in `docs/PROJECT_SESSION_HANDOFF.md`.

## 6. What this ledger does not claim

This baseline does **not** claim:
- A verified cumulative number of user hours or ChatGPT hours.
- A percentage ownership split or monetary valuation of either contribution.
- That every generated code suggestion was applied or merged.
- That a passing unit/CI suite proves production readiness.
- That recorded artifact digests were independently recomputed unless explicitly stated.
- That T0 production storage, Feeder, backup/restore, or live trading is authorized.
- That ChatGPT independently owns project decisions or operational outcomes.

## 7. Status and next work

| Item | Status |
|---|---|
| Initial contribution model and attribution rules | RECORDED |
| Evidence-supported activity window | PARTIAL |
| Historical cumulative hours | NOT VERIFIED |
| Full commit/PR/workflow/artifact inventory | NOT COMPLETED |
| Per-session time log | NOT ESTABLISHED |
| Monetary valuation / percentage split | OUT OF SCOPE |
| Production-readiness claims | NOT MADE |

### Next permitted increments

1. Reconcile repository commit and PR history into a dated milestone index, distinguishing user-authored, AI-assisted, and joint work only where authorship/evidence supports it.
2. Index workflow runs and artifacts by exact SHA and preserve the existing provenance caveats.
3. Start prospective session time recording; do not invent historical hours.
4. Update this ledger and `docs/PROJECT_SESSION_HANDOFF.md` after each meaningful increment, on the existing active branch, recording exact commit SHA and any workflow/artifact references.
5. Keep all runtime, exchange, canonical database, deployment, and live-execution boundaries unchanged unless separately authorized.

## 8. Update log

### 2026-11-09 — Initial baseline
- Created this ledger from currently available project handoff, repository metadata/history, and project context.
- Repository default branch verified as `main`; project handoff read from `docs/PROJECT_SESSION_HANDOFF.md`.
- Latest commit visible to the current GitHub history query at inspection: `f5b74affb8777953fa66d241784965fbb0e577ba` (2026-11-06, CI dispatch support for P1.8 synthetic workflow).
- Exact cumulative hours remain NOT VERIFIED.
- No code, workflow, runtime configuration, VPS, database, Feeder, exchange connection, or trading state changed by this ledger.
- CI/tests were not run for this documentation-only change.
- Next: reconcile the active branch and append this baseline to the project handoff with exact commit provenance.


## 9. Weekly reconciliation — 2026-11-15 (Asia/Ho_Chi_Minh)

### Review scope and baseline
- Read the controlling `docs/PROJECT_SESSION_HANDOFF.md` on active branch `feature/core-operational-proof-20261112` before reviewing this ledger.
- The baseline ledger existed on `main` (blob SHA `66ad418533def584635ee557152b84c9b0c6dd20`) but was absent from the active Core First branch. This file is carried forward unchanged in substance from that baseline, with this dated reconciliation appended.
- Active branch HEAD at review: `55ac20402909fa72d43f4483cb6b228e95360a1a`.
- Tested Core First source SHA: `f9648c40f9fff82f5aef5011be9a2474ddde87a7`.
- GitHub compare confirms the active branch is 3 commits ahead / 0 behind that tested SHA; all three commits modify only `docs/PROJECT_SESSION_HANDOFF.md`. Therefore the documented test-source SHA remains the exact code source for the recorded runs; current branch HEAD is later documentation-only.
- Core First branch has no PR at this review. No parallel branch or PR was created.

### New verified work and provenance

| Date (UTC unless noted) | Work / scope | Branch and source SHA | PR | Workflow / run / job | Artifact | Outcome and evidence boundary |
|---|---|---|---|---|---|---|
| 2026-11-11 | G0.52 D01–D14 documentary closure audit and S2 readiness assessment; docs only | `feature/t0-centralized-data-feeder-p1-20261101`; baseline `7dd321f5960291873dd8f374e6dd62c6a988c7b8`; commit `b9b938b4c78f143ca63330d047a8a799ef450a13` | None identified | No tests/CI claimed | None | Audit PASS; S2 BLOCKED / NOT READY; no implementation authorized. [Commit](https://github.com/kenznguyen/btcusdt-telegram-signals2/commit/b9b938b4c78f143ca63330d047a8a799ef450a13) |
| 2026-11-11 | SSH Preflight retirement documentation and removal sequence; historical scope, not current Core First runtime | Multiple recorded refs; evidence commit `5a950eeaf7b2bf138774cfad3b7daa18c884a0e7`; handoff commit `7021e0e1a7183c201652a0168eaffc4deb798f10` | PR #139 closed unmerged; PR #140 and #144 merged earlier | No new run established by this review | None established for retirement commits | Repository readback/retirement is documented in handoff. Runtime/VPS state not verified. [Evidence commit](https://github.com/kenznguyen/btcusdt-telegram-signals2/commit/5a950eeaf7b2bf138774cfad3b7daa18c884a0e7) |
| 2026-11-15 | Core First operational proof workflow | `feature/core-operational-proof-20261112`; exact tested SHA `f9648c40f9fff82f5aef5011be9a2474ddde87a7` | No PR | Run [43664372302](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43664372302); job `132660376360` SUCCESS | ID `14141951157`, name `core-first-code-operational-proof-43664372302`, digest `sha256:9c9348f815ee2d5e9d94eb8d84d6b301b4fad1f0564aa3b8f5cfc226a4e66c7b`, expires 2026-11-22T01:42:45Z | Workflow/job metadata PASS. Handoff records exact operational-proof checks. Artifact metadata is verified; payload bytes were not independently downloaded/re-hashed in this review. [Artifact](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43664372302/artifacts/14141951157) |
| 2026-11-15 | Dual Ledger Bootstrap Contract regression | `feature/core-operational-proof-20261112`; exact tested SHA `f9648c40f9fff82f5aef5011be9a2474ddde87a7` | No PR | Run [43664372342](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43664372342); job `132660812848` SUCCESS | ID `14141667068`, name `dual-ledger-bootstrap-proof-f9648c40f9fff82f5aef5011be9a2474ddde87a7`, digest `sha256:75e79ee566b0251e1230e85365ceac2a8d2e6a9152ce24997a4f4b6ec2e62d25`, expires 2026-11-22T01:42:45Z | Workflow/job metadata PASS. Exact test outcome remains bounded to the handoff/workflow evidence; artifact payload bytes were not independently downloaded/re-hashed in this review. [Artifact](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43664372342/artifacts/14141667068) |

### Pull request reconciliation
- PR #141 — `ci(t0): expose isolated A2.2 Stage I workflow`: MERGED/CLOSED into `main`; no effect on Core First branch.
- PR #142 — `ci(t0): fix Stage I unittest summary parsing`: MERGED/CLOSED into `main`; no effect on Core First branch.
- PR #144 — `Secure Scaleway SSH preflight passphrase handling`: MERGED/CLOSED into `main`; subsequent SSH Preflight retirement is recorded separately. No VPS operation is inferred.
- Active Core First branch has no PR. PR #139 is historically CLOSED / NOT MERGED and must not be reopened without separate approval.
- This is the set of newly surfaced PRs reviewed in the available GitHub query; a complete all-pages repository-wide PR/run inventory is not established.

### Contribution attribution
- USER: owner decisions, approval gates, project priorities, and VPS offline test execution/results explicitly supplied by the owner in terminal summaries. These owner-supplied summaries are evidence of reported execution, not independent remote observation.
- GitHub commits under the repository owner account are account-attributed; where the returned record does not establish whether implementation was authored manually or AI-assisted, implementation-level human/AI split is **UNKNOWN**.
- CHATGPT: this review's reconciliation and documentation drafting assistance. This does not establish sole authorship of source implementation or test execution.
- JOINT: not assigned to individual implementation commits without evidence of iterative authorship.
- UNKNOWN: any source implementation attribution not independently supported by commit/patch/session provenance.

### Time accounting
- Measured project effort hours added this period: **0 verified** (no reliable work-session start/end or explicit duration record).
- User-estimated hours added: **none supplied**.
- Historical and current contribution hours: **UNKNOWN / UNMEASURED**.
- Test execution durations in terminal output are test runtime, not labor time; they are not counted as effort.
- No backfill or inference from commits, messages, calendar span, or timestamps.

### Status, limits, and next step
- Core First selected offline unit/contract suites reported by owner: **130/130 PASS** at tested SHA `f9648c40f9fff82f5aef5011be9a2474ddde87a7`; this is not continuous runtime proof.
- Core operational proof and Dual Ledger Bootstrap Contract workflow jobs: **PASS** for their exact CI scope.
- Persistent PAPER Ledger / Shared Risk readiness: **NOT VERIFIED**; handoff records `risk_ready=0` and `SIMULATED_INITIAL_MARK_REQUIRED`; no mark or Ledger mutation is authorized.
- Continuous actual Runner behavior, long-running stability, real-data-backed PAPER evaluation and predictive/OOS value: **NOT VERIFIED**.
- T0 data availability/reacquisition: **BLOCKED / NOT VERIFIED** pending separate owner decision. T0 remains independent and untouched.
- AI Strategy remains deferred; `AI_EXECUTION_ENABLED=false`; no live orders.
- VPS test results are owner-pasted summaries; no independently observed SSH session, retained full verbose logs, or separate VPS artifact was available to this review.
- Artifact metadata was verified from GitHub; independent payload-byte rehash was not performed.
- Next: follow the handoff's next authorized decision gate for T0 data availability/read-only Ledger readiness. Do not initialize a simulated mark, run Bootstrap or actual Runner, create services/autostart, access/mutate T0, connect to an exchange, enable AI, or trade without separate explicit approval.


### 2026-11-15 — Branch movement / source-provenance correction
- Post-commit comparison against the branch ref showed that the branch advanced beyond the earlier observed snapshot `55ac20402909fa72d43f4483cb6b228e95360a1a`.
- Current branch HEAD at this correction: `020dfb2910fe282c8a9114d1836f00f2f8189dda`.
- Compared with the earlier snapshot, GitHub reports 31 additional commits and net changes to `.github/workflows/core-live-data-operational-proof.yml`, `core_runtime/__main__.py`, `core_runtime/bundle_inputs.py`, `core_runtime/bundle_provider.py`, `core_runtime/runtime_factory.py`, and three corresponding test modules, in addition to the two documentation files. Compared with tested SHA `f9648c40f9fff82f5aef5011be9a2474ddde87a7`, GitHub reports 34 commits ahead.
- Therefore the earlier statement that the active branch delta remained documentation-only is valid only for the snapshot at `55ac204...`; it does **not** describe the current branch tip. The newly present source/workflow delta has not been inspected or tested in this weekly review. Current code-source SHA / exact source tested at branch HEAD: **NOT VERIFIED**.
- The two recorded GitHub Actions runs still apply only to exact SHA `f9648c40f9fff82f5aef5011be9a2474ddde87a7`; they do not validate the later source/workflow changes.
- No source files or workflow were modified by this ledger review. No reset, rebase, force-push, merge, or runtime operation was performed.
- Status remains **PARTIAL / NOT VERIFIED** for current branch source parity. Next: reconcile the intervening commits and exact current code SHA before relying on any prior CI evidence.
