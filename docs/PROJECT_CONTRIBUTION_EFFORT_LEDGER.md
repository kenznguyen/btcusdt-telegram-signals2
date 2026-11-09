# Project Contribution & Effort Ledger

Last updated: 2026-11-09 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Status: **INITIAL BASELINE — PARTIAL / NOT A TIME AUDIT**

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
