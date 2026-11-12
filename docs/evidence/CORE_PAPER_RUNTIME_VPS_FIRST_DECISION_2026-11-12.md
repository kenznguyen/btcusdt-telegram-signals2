# Core Paper Runtime — VPS-First Decision

Date: 2026-11-12
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/core-operational-proof-20261112`
Decision baseline: `7bae48eff6043aa65a431845eec9748c478cfdd1`

## 1. Decision change

The user explicitly revokes the prior packaging-first direction and changes the next objective to launching the Core paper runtime on a VPS to collect real process/runtime evidence.

This supersedes the previous next-step priority to build a release package/bundle before runtime collection. The earlier packaging assessment remains historical evidence and must not be deleted or rewritten as if it never occurred. Packaging is deferred, not a current release gate for beginning a bounded VPS runtime experiment.

The one-shot runner design remains useful as a technical contract, but it is not permission to claim a runnable daemon exists. Runtime entrypoint availability must be checked against the exact source before attempting launch.

## 2. Current host availability

The last recorded environment evidence states the former Scaleway VPS was deleted on 2026-11-11 and no replacement host was established. No current VPS address, instance identity, SSH route, or operator-provided access path is present in this task.

Therefore the requested VPS launch is currently **BLOCKED — TARGET VPS NOT IDENTIFIED/AVAILABLE**. No host command has been run and no runtime evidence has been collected in this increment.

A new VPS must not be provisioned or charged without a separate explicit approval of provider/instance/cost. Once an existing or newly approved host is identified, only the bounded paper-only launch scope below is authorized.

## 3. Bounded runtime objective

Collect actual process/runtime evidence on the identified VPS for Core paper-only operation:
- exact source SHA and branch/revision;
- host OS/kernel/architecture and resource baseline;
- runtime entrypoint and configuration validation;
- process start/stop and bounded observation;
- CPU, memory, disk and process health;
- paper ledger persistence and controlled restart/recovery using a dedicated disposable ledger;
- structured runtime logs and evidence artifact with hashes;
- proof that no exchange credentials, live order path, or real orders are used.

Before launch, inspect the exact source for a runnable Core execution entrypoint. The existing `python -m paper_execution` command was previously verified as ledger initialization/snapshot utility, not a Core decision daemon. Do not present it as the Core runtime. If no safe runnable entrypoint exists, report the blocker and request approval for the minimum code change; do not improvise by running the dashboard/T0 feeder as the Core engine.

## 4. Non-negotiable guardrails

- `AI_EXECUTION_ENABLED=false`; AI remains offline.
- Core RSI + ADX + Smart DCA logic and existing Shared Risk Engine/Kill Switch are not altered by a runtime-only task.
- PAPER mode only; no exchange API keys/private credentials, no exchange order endpoint, no live trading and no real orders.
- Dedicated disposable paper ledger only; canonical T0 database remains read-only and must never be used as a paper ledger.
- No T0/T1/T2 runtime changes, no T1 activation, no AI ledger admission.
- No systemd/autostart/boot persistence, no unbounded daemon, no long-duration soak test, no package release or dependency installation beyond the explicitly approved runtime scope.
- No data deletion/cleanup, schema migration, database initialization or destructive storage operation against canonical data.
- Capture bounded logs and metrics; redact secrets; retain evidence outside the disposable runtime database.
- Stop immediately on ambiguous mode, missing/corrupt risk state, stale data, Kill Switch failure, unexpected network/exchange access, or any possibility of real order submission.

## 5. Execution gates

**Gate A — Host identity/access:** obtain VPS provider/instance identity, OS, public/private reachability and a safe operator-approved access mechanism. Do not request passwords or private keys in chat.

**Gate B — Source/runtime readiness:** verify exact deployed SHA, runnable Core entrypoint, config, dependency availability, paper flags, risk state, T0 read-only source and disposable ledger separation.

**Gate C — Controlled launch:** bounded foreground/tmux process only, no systemd/autostart; capture PID, command, start/end timestamps and logs. Do not launch if Gate B is not PASS.

**Gate D — Runtime observation:** collect bounded health/resource/persistence/restart evidence. Any restart uses disposable paper state and explicit before/after integrity checks.

**Gate E — Evidence and disposition:** write exact SHA, host fingerprint (non-secret), commands, test/observation outcomes, artifact SHA-256, PASS/BLOCKED/NOT VERIFIED, limitations and next step to GitHub. No claims of production readiness.

## 6. Current disposition

- User decision: **VPS-FIRST RUNTIME COLLECTION; PACKAGING DEFERRED**.
- Target host: **BLOCKED — former VPS deleted; replacement not identified**.
- Runtime entrypoint: **NOT VERIFIED as runnable Core execution process**; existing paper_execution module CLI is initialization-only.
- VPS runtime evidence: **NOT STARTED**.
- Live/production trading: **BLOCKED / OUT OF SCOPE**.
- No code, runtime, host, database or T0 data was changed in this decision-recording increment.

## 7. Immediate next input

Identify the VPS target that should be used (provider and instance/hostname or public IP). Do not send SSH passwords, private keys or exchange credentials. If there is no existing target, VPS provisioning requires a separate explicit approval of provider, size and cost before any creation.
