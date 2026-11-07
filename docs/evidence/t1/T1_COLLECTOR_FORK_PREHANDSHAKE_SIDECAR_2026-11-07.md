# T1 Collector Fork — Pre-handshake Sidecar Contract Increment

Date: 2026-11-07 (Asia/Ho_Chi_Minh)

## Scope

Repository: https://github.com/kenznguyen/binance-futures-collector

- User-owned fork of `waynemason1/binance-futures-collector`.
- Upstream baseline: `bc4f0ef633fbeee4a49defd72827f17162693805`.
- Working branch: `feature/t1-connection-sidecar-integration-20261107`.
- Draft PR: https://github.com/kenznguyen/binance-futures-collector/pull/1.
- Latest source SHA verified for completed run: `00cc447e6f39e3e14dfe13eaa88a7a82e40828e3`.

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

## Exact source / GitHub state

- Rustfmt-only commits: `88c0027514fc79ef9c4fae02a870f8a7c9ae5f9e` and latest source SHA `00cc447e6f39e3e14dfe13eaa88a7a82e40828e3`.
- Latest commit inspected directly: https://github.com/kenznguyen/binance-futures-collector/commit/00cc447e6f39e3e14dfe13eaa88a7a82e40828e3.
- GitHub Actions run: https://github.com/kenznguyen/binance-futures-collector/actions/runs/42344752951.
- Run ID: `42344752951`; run number 5; workflow `CI`; completed with overall conclusion **FAILURE**.
- Run is associated with the exact source SHA above. Job checkout SHA could not be independently confirmed because job-log retrieval returned HTTP 404; therefore synthetic-merge/checkout identity remains **NOT VERIFIED**.
- Rust job `128319958110`: SUCCESS. Base collector Format, Clippy, Build and Test all passed; Sidecar writer Format, Clippy and offline tests all passed.
- Sidecar offline test command completed successfully; the workflow defines 11 sidecar tests. Job step summary does not expose the numeric test count, so count from the run is recorded as **11 expected / step PASS; detailed per-test log NOT VERIFIED**.
- Security job `128319958140`: FAILURE at `cargo-audit`; npm audit steps were skipped. The current detailed audit output was not retrievable.
- Dashboard backend `128319958177`: SUCCESS.
- Dashboard frontend job `128319958091`: SUCCESS.
- Docker job `128319957980`: SUCCESS.
- Artifact query returned an empty list; no artifact ID, URL or digest exists for this run.
- Prior comparison established fork and pinned upstream baseline Cargo.toml/Cargo.lock blob hashes are identical: Cargo.lock `625a8b8af376511d1d3245fc0ab9f72b138d180e`; Cargo.toml `f373e8b32e090a76399905538742e8b34a669419`. The audit issue is therefore present in the unchanged dependency baseline; do not attribute it to sidecar source changes. No dependency changes or audit suppressions were applied.
- PR #1 remains OPEN / DRAFT / NOT MERGED.

## Verification verdict

| Item | Status |
|---|---|
| Sidecar source/test/README added | PASS |
| Collector base format / Clippy / build / tests | PASS |
| Sidecar format | PASS |
| Sidecar Clippy | PASS |
| Sidecar offline test step | PASS (11 authored tests; detailed count/log NOT VERIFIED) |
| Dashboard backend/frontend and Docker | PASS |
| Security cargo-audit gate | BLOCKED |
| npm audit | NOT RUN (skipped after cargo-audit failure) |
| Exact checked-out SHA from job logs | NOT VERIFIED (log API returned 404) |
| Run artifact / digest | NONE |
| Overall GitHub Actions run | BLOCKED / FAILURE |
| Collector runtime integration | NOT IMPLEMENTED |
| Live exchange capture / reconnect | NOT RUN |
| T1 continuity / readiness | NOT CERTIFIED |

## Next action

1. Resolve the inherited RustSec advisories by inspecting the dependency graph and advisory reachability, then propose only minimal lockfile-generated updates with compatibility tests. Do not add blanket ignores, allowlists, or weaken the security gate.
2. Re-run GitHub Actions on the resulting new source SHA and verify exact checkout identity from accessible logs.
3. Only after required security and Rust gates pass, review the next isolated implementation increment. Do not start Tokio writer-worker/runtime integration before that gate.

## Safety limits

- No upstream source modified.
- No collector binary/process started.
- No DNS/TCP/WebSocket request to Binance.
- No exchange API or market data accessed.
- No database opened, created, or modified.
- No runtime configuration or credentials changed.
- No live trading or orders; `ai_execution_enabled=false`.
- PR remains draft and unmerged.
