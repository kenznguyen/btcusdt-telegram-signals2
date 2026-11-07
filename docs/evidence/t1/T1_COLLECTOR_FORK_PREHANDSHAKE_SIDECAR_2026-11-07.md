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


## 2026-11-07 Addendum — Completed PR CI Run 42343825387

- PR #1 remains OPEN / DRAFT / NOT MERGED. PR head/source SHA: `e1ccc11f654082456f3ef7b728f161e475904da0`.
- GitHub Actions run: [42343825387](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42343825387), event `pull_request`, completed. The workflow checked out synthetic merge commit `25fd6c3fe1e7bbf30f59f456bd06c11ff11e4b6a`, whose parents are the PR head `e1ccc11f654082456f3ef7b728f161e475904da0` and upstream base `bc4f0ef633fbeee4a49defd72827f17162693805`. Do not label the synthetic merge SHA as the PR source SHA.
- Job results:
  - Collector job `128317128179`: FAIL. Base collector format, Clippy and build PASS; existing collector tests PASS (40 library + 1 binary = 41/41). Sidecar writer format FAIL. Sidecar writer Clippy and 11 sidecar tests SKIPPED because the format step failed.
  - Security job `128317127920`: FAIL. `cargo audit` reports 12 vulnerabilities and 2 allowed warnings; npm audit steps SKIPPED because the Rust audit command exited nonzero.
  - Dashboard backend `128317128141`: PASS.
  - Dashboard frontend `128317128165`: PASS.
  - Docker `128317128304`: PASS.
- Sidecar formatting failure is non-semantic: rustfmt requests line wrapping/import ordering in `crates/connection-sidecar/src/lib.rs` and `crates/connection-sidecar/tests/sidecar_writer.rs`. No sidecar tests ran in this attempt.
- Upstream dependency comparison: fork `Cargo.lock` blob SHA and pinned upstream baseline `Cargo.lock` blob SHA are both `625a8b8af376511d1d3245fc0ab9f72b138d180e`; fork and upstream baseline `Cargo.toml` blob SHA are both `f373e8b32e090a76399905538742e8b34a669419`. Thus the audited Rust dependency manifest and lockfile are byte-identical to upstream baseline; the audit findings are inherited baseline findings, not introduced by the sidecar PR. No dependency changes were made. Do not suppress/allowlist these advisories merely to turn CI green; any dependency remediation must be narrowly resolved, lockfile-generated, tested, and reviewed for compatibility.
- Artifact query returned no run artifacts.
- Overall verdict: **BLOCKED**. Sidecar exact-source acceptance is NOT VERIFIED because sidecar Clippy/tests were skipped; security gate remains blocked by inherited upstream dependency advisories.
- Next: make only the rustfmt-required formatting correction, then re-run GitHub Actions on the new PR head. In parallel, prepare a minimal dependency remediation plan for the inherited advisories; do not modify the dependency graph by hand or weaken cargo-audit. Only consider Tokio writer-worker integration after the complete required CI gates pass.
- Safety unchanged: no collector runtime, Binance connection, database open/create, market-data capture, or live trading. `ai_execution_enabled=false`.


## 2026-11-07 Addendum — Rustfmt Correction and CI Rerun

- Applied only rustfmt-requested formatting to `crates/connection-sidecar/src/lib.rs` and `crates/connection-sidecar/tests/sidecar_writer.rs`; no logic, test assertions, dependency, runtime, or workflow changes.
- Fork commits: implementation formatting `88c0027514fc79ef9c4fae02a870f8a7c9ae5f9e`; test formatting / latest PR source SHA `00cc447e6f39e3e14dfe13eaa88a7a82e40828e3`.
- New GitHub Actions run [42344752951](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42344752951), triggered for source SHA `00cc447e6f39e3e14dfe13eaa88a7a82e40828e3`. Rust job `128319958110`; security job `128319958140`; dashboard backend `128319958177`.
- At latest inspection: Rust base Format PASS; Clippy IN_PROGRESS; Build/Test/sidecar format/sidecar Clippy/11 sidecar tests pending. Dashboard backend PASS. Dashboard frontend, Docker, Security still in progress. Exact checkout SHA and final conclusions not yet verified.
- Overall state remains **IN PROGRESS / NOT VERIFIED**. Do not infer sidecar acceptance or security clearance until all jobs complete and logs confirm results.
- Dependency audit baseline comparison remains unchanged: fork and upstream baseline Cargo.toml/Cargo.lock blobs identical; no dependency remediation or audit suppression applied.
- Safety unchanged: no collector process, Binance connection, DB open/create, market data capture, or live trading; `ai_execution_enabled=false`. PR #1 remains OPEN / DRAFT / NOT MERGED.


## 2026-11-07 Addendum — Completed CI Run 42344752951

- Latest fork source commit: `00cc447e6f39e3e14dfe13eaa88a7a82e40828e3`; commit inspected directly on GitHub.
- GitHub Actions run [42344752951](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42344752951), run number 5, workflow `CI`, completed with overall **FAILURE**.
- Rust job `128319958110`: **SUCCESS**. Collector Format, Clippy, Build and Test passed; Sidecar writer Format, Clippy and offline test steps all passed. The suite contains 11 authored tests; the job step summary confirms the test step passed but does not expose its detailed numeric output, so per-test count/log remains NOT VERIFIED.
- Dashboard backend job `128319958177`: **SUCCESS**. Dashboard frontend job `128319958091`: **SUCCESS**. Docker job `128319957980`: **SUCCESS**.
- Security job `128319958140`: **FAILURE** at `cargo-audit`; npm audit steps were skipped. Detailed current audit output could not be retrieved.
- Artifact query returned an empty list: no artifact ID, URL or digest for this run.
- Run is associated with source SHA `00cc447e6f39e3e14dfe13eaa88a7a82e40828e3`. Job-log retrieval returned HTTP 404, so actual checked-out SHA / synthetic merge SHA is **NOT VERIFIED**.
- Prior fork/upstream baseline comparison established identical Cargo.toml and Cargo.lock blobs (`f373e8b32e090a76399905538742e8b34a669419` and `625a8b8af376511d1d3245fc0ab9f72b138d180e`). No dependency modifications or audit suppressions were made.
- Verdict: sidecar Rust checks **PASS at job-step level**; overall CI **BLOCKED** by the security gate. Exact checkout identity and detailed 11-test count remain NOT VERIFIED. PR #1 remains OPEN / DRAFT / NOT MERGED.
- Next: inspect dependency graph/advisory reachability and design the smallest compatible, lockfile-generated remediation with tests. Do not weaken cargo-audit or add blanket ignores. Re-run GitHub Actions and verify checkout SHA from accessible logs. Do not start Tokio writer-worker/runtime integration until required gates pass.
- Safety unchanged: no collector runtime, Binance connection, database access, market-data capture, credential/config change, merge, or live trading. `ai_execution_enabled=false`.
