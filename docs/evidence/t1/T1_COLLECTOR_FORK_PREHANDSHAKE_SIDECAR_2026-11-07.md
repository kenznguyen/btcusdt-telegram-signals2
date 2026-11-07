# T1 Collector Fork — Pre-handshake Sidecar Contract Increment

Date: 2026-11-07 (Asia/Ho_Chi_Minh)

## Scope

Repository: https://github.com/kenznguyen/binance-futures-collector

- User-owned fork of `waynemason1/binance-futures-collector`.
- Upstream baseline: `bc4f0ef633fbeee4a49defd72827f17162693805`.
- Working branch: `feature/t1-connection-sidecar-integration-20261107`.
- Draft PR: https://github.com/kenznguyen/binance-futures-collector/pull/1.
- Latest observed PR head / branch SHA: `3d7d308bd63bf840d648f2cd22705477781a2557`.

## Implemented

Added `crates/connection-sidecar` as a portable offline Rust writer crate, copied from the previously tested T1 sidecar reference and extended with pre-handshake lifecycle records.

- `CONNECT_ATTEMPTED` must be durably appended before the network handshake is initiated.
- `CONNECT_FAILED` records a classified DNS, transport, timeout, handshake-rejected, shutdown, or unknown failure.
- `CONNECTED` is accepted only after a pending `CONNECT_ATTEMPTED`.
- A failed attempt transitions to a terminal state from which one bounded `RECONNECT_SCHEDULED` can be recorded.
- Every retry must use a fresh per-attempt `connectionId`.
- Finalization rejects unresolved connection attempts.
- Existing exclusive-create, append-only JSONL, per-event `sync_data`, manifest, exact subscription-set, checksum and bounds behavior is retained.
- Added 2 pre-handshake regression tests; total authored Rust tests: 11.
- Added CI commands for sidecar format, Clippy and offline tests.
- Added the feature branch to the workflow push filter.

## Exact source / GitHub state

- Initial implementation commit: `938a9df4576671266615e6d7f74866ad4dbda375`.
- Test timestamp correction: `04cfefda1459b0da3cb298424453987553dbe186`.
- Workflow update: `36046be953396d1bdd74ed1c09959b1fbbe1765e`.
- Test setup correction: `408ce65f7a7a948b9bbd2749db276271ec6e5680`.
- Workflow push-filter commit: `8fe12b7be05ee3e250af54d39deed723a65e83c1`.
- Subsequent source hygiene commits: `9e2e58f1f7357f926f2ea9f2e41d460b726caf48` (format lifecycle methods), `73d1438c85b1092787e3c65fa2ec9b3bbcdd8a9d` (format regression tests), and `3d7d308bd63bf840d648f2cd22705477781a2557` (remove unused test dependency).
- PR #1 is OPEN / DRAFT / NOT MERGED.
- Latest observed Actions query returned `total_count=0`, no workflow runs, including after adding the feature branch to the push filter.
- Latest observed commit status had zero status contexts and state `pending`.
- No workflow run ID, job ID, artifact ID, artifact digest or test log is available.

## Verification verdict

| Item | Status |
|---|---|
| Fork relation and pinned upstream baseline | PASS |
| Sidecar source/test/README added | PASS (GitHub source state only) |
| 11 Rust tests authored | PASS (authored, NOT EXECUTED) |
| Rust format / Clippy | NOT VERIFIED |
| Rust tests | NOT RUN |
| GitHub Actions execution | BLOCKED / NOT STARTED (no run visible) |
| Exact-source CI acceptance | NOT VERIFIED |
| Collector runtime integration | NOT IMPLEMENTED |
| Live exchange capture / reconnect | NOT RUN |
| T1 continuity / readiness | NOT CERTIFIED |

Do not infer that Actions are disabled from the absence of runs; the reason is not yet established. Investigate repository Actions settings / workflow activation through GitHub UI or an authorized Actions control before changing CI provider. GitHub Actions remains the required CI platform; do not switch to Codemagic.

## Safety limits

- No upstream source modified.
- No collector binary/process started.
- No DNS/TCP/WebSocket request to Binance.
- No exchange API or market data accessed.
- No database opened, created, or modified.
- No runtime configuration or credentials changed.
- No live trading or orders; `ai_execution_enabled=false`.
- PR remains draft and unmerged.

## Next action

Resolve why the fork has no GitHub Actions runs, then execute the exact PR head SHA `8fe12b7be05ee3e250af54d39deed723a65e83c1` through GitHub Actions. Record checked-out SHA, run ID, each job result, test totals and artifact metadata. Only after CI passes should the next increment integrate a dedicated bounded blocking writer worker, durable acknowledgements, unique heartbeat Ping/Pong payload correlation, pre-handshake failure hooks, disconnect/reconnect recording and graceful shutdown finalization.


## 2026-11-07 Addendum — Actions Enabled / Fresh Push Recheck

- User confirmed that GitHub Actions were enabled for the fork.
- Rechecked PR #1: OPEN / DRAFT / NOT MERGED; base remains `main` at upstream baseline `bc4f0ef633fbeee4a49defd72827f17162693805`.
- Workflow source `.github/workflows/ci.yml` was read at the feature branch. It declares `push` for `main` and `feature/t1-connection-sidecar-integration-20261107`, and `pull_request` without path filters.
- Since enabling Actions did not produce a run for the existing event, created and pushed a no-source-change commit to the same feature branch to generate a fresh push event. Commit: `e1ccc11f654082456f3ef7b728f161e475904da0`; parent: `3d7d308bd63bf840d648f2cd22705477781a2557`; tree unchanged: `f7023d9c05ec232b4e68f341f14ea5ec5b2953a7`.
- Exact PR head is now `e1ccc11f654082456f3ef7b728f161e475904da0`. PR body was updated to reflect this identity and current validation state.
- Recheck after the fresh push: Actions API still reports zero workflow runs; commit status has zero contexts. No run ID, job ID, artifact, digest or logs exist.
- Verdict remains **BLOCKED / NOT VERIFIED**. The reason the workflow does not start is still undetermined; do not claim the user's enablement failed or infer a specific repository setting.
- Tests: 11 authored, **NOT RUN**. Format and Clippy **NOT VERIFIED**. No collector runtime integration or exchange access occurred.
- Next: inspect the fork's Actions tab for workflow visibility, disabled/approval banners, and pending approval; if no workflow appears, verify the workflow file is present on the default branch and inspect repository Actions policy in Settings. Do not add runtime integration until exact-head CI passes.
- Safety unchanged: no collector process, Binance request, DB access, data capture, credential/config change, merge, or live execution. `ai_execution_enabled=false`.


## 2026-11-07 Addendum — GitHub Actions Run Started

- Fresh workflow run is now visible: [42343825387](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42343825387), workflow `CI`, event `pull_request`, status `in_progress`.
- Run metadata PR head SHA: `e1ccc11f654082456f3ef7b728f161e475904da0`, matching current PR head. Because this is a pull_request event, the actual checkout may be a synthetic merge SHA; checked-out SHA must be confirmed from job logs after completion.
- Jobs at latest inspection:
  - `dashboard backend · pytest`: SUCCESS.
  - `dashboard frontend · tsc · vitest`: SUCCESS.
  - `collector · fmt · clippy · test`: IN_PROGRESS; Format PASS, Clippy PASS, Build IN_PROGRESS; remaining tests/sidecar commands pending.
  - `docker · build images`: IN_PROGRESS.
  - `security · cargo-audit · npm audit`: IN_PROGRESS.
- Collector job ID: `128317128179`. Dashboard backend job ID: `128317128141`. Dashboard frontend job ID: `128317128165`. Docker job ID: `128317128304`. Security job ID: `128317127920`.
- No artifacts are available yet. Final workflow conclusion, exact checkout SHA, full Rust test count and artifact metadata remain NOT VERIFIED.
- PR #1 body updated with this run and current validation boundaries; remains OPEN / DRAFT / NOT MERGED.
- Next: wait for run completion; inspect every job, fetch logs to prove checkout SHA and test counts, inspect artifacts/digests, then update this report and handoff with final evidence. Do not start runtime integration until exact-source CI passes.
