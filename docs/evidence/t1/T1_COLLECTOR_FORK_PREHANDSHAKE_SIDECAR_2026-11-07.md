# T1 Collector Fork — Pre-handshake Sidecar Contract Increment

Date: 2026-11-07 (Asia/Ho_Chi_Minh)

## Scope

Repository: https://github.com/kenznguyen/binance-futures-collector

- User-owned fork of `waynemason1/binance-futures-collector`.
- Upstream baseline: `bc4f0ef633fbeee4a49defd72827f17162693805`.
- Working branch: `feature/t1-connection-sidecar-integration-20261107`.
- Draft PR: https://github.com/kenznguyen/binance-futures-collector/pull/1.
- Latest observed PR head / branch SHA: `8fe12b7be05ee3e250af54d39deed723a65e83c1`.

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
- Latest workflow branch commit: `8fe12b7be05ee3e250af54d39deed723a65e83c1`.
- PR #1 is OPEN / DRAFT / NOT MERGED.
- Latest observed Actions query returned `total_count=0`, no workflow runs.
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
