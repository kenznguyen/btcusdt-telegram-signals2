# T1 Order Book V1 Consumer-Lag Diagnostic — Test Specification

Date: 2026-11-13  
Status: APPROVED FOR BOUNDED IMPLEMENTATION — TEST-FIRST  
Target repository: `kenznguyen/binance-futures-collector`  
Target branch: `feature/t1-connection-sidecar-integration-20261107`  
Target source baseline: `9b2af66e68206898e51f638b67497d574a7252c4`

## 1. Purpose and boundaries

Specify a bounded, test-first diagnostic increment to distinguish exchange event age, socket receive-to-apply delay, ring-buffer residence, batch processing delay, and Order Book V1 rejection class.

This is documentation only. It does not authorize collector source changes, runtime configuration changes, another VPS capture, persistent services, T0 access, T1→T2 integration, or trading.

## 2. Exact-baseline findings

At source SHA `9b2af66e68206898e51f638b67497d574a7252c4`:

- `process_text_message()` captures a monotonic `Instant` as `received_at`.
- `process_stream_data()` sends that instant to the message-handler channel, but calls `buffer_depth_update(update.clone())` without it.
- `symbol_buffers` stores `VecDeque<DepthUpdateWs>`; the V1 consumer cannot recover the original receive instant.
- The BTCUSDT consumer drains every 500 ms and applies events sequentially.
- It passes one `Utc::now()` value as both observation and decision time.
- Existing `ws_latency_ms` measures socket-read-to-message-handler processing, not ring-buffer residence or V1 apply delay.
- All `apply_live_diff()` errors map to `v1_live_sequence_or_shape_failure`, including freshness rejection.

Inspected source blobs:
- `src/websocket/connection_manager.rs`: `9abeb85b2a10c79fbbaf86bb59e145ab59278661`
- `src/collectors/orderbook_manager.rs`: `e7d294d76def83510448282ded5b44559df3139c`
- `src/models.rs`: `ca2e23cdede536b0dd004f36257e7974d5a8245f`
- `src/orderbook_v1.rs`: `5b935bc76bf80bfe86c952e53d6bddbe73f50f6f`

## 3. Proposed diagnostic design

### 3.1 Preserve monotonic receive time

Use an internal buffered wrapper, not a wire-model or CSV change:

```rust
struct BufferedDepthUpdate {
    update: DepthUpdateWs,
    received_at: Instant,
}
```

Capture the instant immediately after the complete WebSocket frame is returned by `ws_rx.next()`, before JSON parsing, then pass it through routing into the BTCUSDT buffer. If implementation keeps the current later capture point, metric names must say process-entry-to-apply, not socket-read-to-apply.

Do not serialize `Instant`, add it to Binance models, CSV, public APIs, or persisted market data.

### 3.2 Measure separate quantities

Use monotonic time for:
- socket receive-to-apply duration;
- buffer insertion-to-apply residence (if insertion time is separately captured);
- batch processing duration.

Use UTC epoch milliseconds for:
- exchange event age at decision time;
- human-readable timestamps only.

Record bounded batch summaries:
- batch size;
- buffer depth before and after drain;
- batch processing duration;
- receive-to-apply max and bounded p50/p95 if existing metrics infrastructure supports it;
- number applied before first rejection.

Do not emit per-event logs, keep unbounded histories, create high-cardinality labels, or add persistent telemetry storage. Keep scope BTCUSDT-only.

### 3.3 Preserve time semantics

- Never compare `Instant` to Binance epoch timestamps.
- Do not substitute receive time for exchange event time in freshness validation.
- Do not backdate observation time or make stale events pass.
- Keep existing freshness decision semantics unchanged.

## 4. Typed rejection classification

Prefer typed internal error variants at the validation boundary; never classify by parsing error strings. Stable categories:

- `FRESHNESS_REJECTED`: source or observation timestamp violates existing freshness/future-skew bounds.
- `SEQUENCE_REJECTED`: update-ID ordering or `pu`/watermark continuity fails.
- `SHAPE_REJECTED`: malformed header, invalid levels/decimals, insufficient depth, crossed/locked book, or structural validation fails.
- `PUBLISH_FENCED`: snapshot generation/publisher fence rejects publication.
- `LEGACY_MIRROR_REJECTED`: legacy mirror update fails.

Keep detailed error context in logs. Make validation precedence explicit and preserve current order unless separately reviewed. A diagnostic classification must not change which candidate is published.

## 5. Required TDD cases

### A. Receive-time propagation
1. Original monotonic receive instant reaches the buffered item unchanged.
2. Buffering does not replace it with handler, drain, or apply time.
3. Non-depth routing and CSV output remain unchanged.
4. No monotonic instant is serialized.

### B. Delay measurements
5. Deterministic injected instants yield correct receive-to-apply duration.
6. Buffer residence and apply processing duration are distinct.
7. The 500 ms ticker wait contributes to residence, not exchange event age.
8. Negative/future wall-clock age never creates a negative monotonic duration.
9. Wall-clock adjustment cannot alter monotonic elapsed metrics.

### C. Batch and buffer behavior
10. Empty drain produces no apply.
11. Batch size and pre/post-drain depths are correct.
12. First failing event and count applied before it are recorded accurately.
13. Aggregation remains bounded under sustained event volume.
14. Capacity eviction remains fail-closed and invalidates V1 publisher as currently required.
15. Reconnect/resnapshot clearing cannot preserve stale metadata or make old events eligible.

### D. Failure classification
16. Source timestamp beyond existing 2,000 ms age maps to `FRESHNESS_REJECTED`.
17. Stale observation timestamp maps to `FRESHNESS_REJECTED`.
18. Future-skew violation maps to `FRESHNESS_REJECTED`.
19. `pu` mismatch and invalid update-ID ordering map to `SEQUENCE_REJECTED`.
20. Malformed header, invalid level, insufficient depth and crossed book map to `SHAPE_REJECTED`.
21. Publisher generation fence maps to `PUBLISH_FENCED`.
22. Legacy mirror failure maps to `LEGACY_MIRROR_REJECTED`.
23. Combined-invalid fixtures prove documented validation precedence.
24. No rejection publishes an invalid candidate or advances decision watermark.

### E. Regression / fail-closed
25. Existing snapshot bootstrap and live-diff tests remain green.
26. Buffer overflow, reconnect and resnapshot tests remain green.
27. `MAX_BOOK_AGE_MS` remains exactly 2,000.
28. Recent receive time cannot make an old exchange event pass.
29. An old event with a sequence failure is not mislabeled freshness solely due to age.
30. BTCUSDT-only V1 boundary and non-BTC legacy behavior remain unchanged.

## 6. Acceptance gates if separately approved

1. Add failing tests first (TDD RED) for receive-time propagation and typed rejection classification.
2. Implement the smallest internal change that satisfies those tests.
3. Run focused tests, full Rust tests, fmt, Clippy and existing CI.
4. Review diff for unrelated source/config/workflow changes.
5. Record exact source SHA, workflow runs, job/test results, artifact metadata and disposition.
6. Keep VPS runtime verification as a separate gate requiring explicit bounded authorization.

CI can prove instrumentation/classification contracts; it cannot prove the historical stale event was caused by backlog.

## 7. Explicit non-goals

- Do not raise or disable `MAX_BOOK_AGE_MS = 2,000`.
- Do not alter Binance event-time semantics or use receive time as source time.
- Do not increase ring-buffer capacity, change drop/replay/retry behavior, or alter snapshot/resnapshot policy.
- Do not weaken freshness, sequence, or shape validation.
- Do not add dependencies, credentials, services, external endpoints, or persistent telemetry.
- Do not widen beyond BTCUSDT.
- Do not access/modify T0, integrate T1→T2, enable persistent services, or place orders.
- Do not repeat VPS runtime capture under this specification.

## 8. Current disposition

- Clock sync: PASS for five-sample probe (median offset -4 ms; range -20 to +3 ms; RTT 230–268 ms).
- Consumer backlog: PLAUSIBLE, NOT PROVEN.
- Ring-buffer residence: NOT MEASURED.
- Exact rejected event and guard-evaluation delay: NOT VERIFIED.
- This specification: DESIGN ONLY.
- Source implementation: NOT STARTED.
- Runtime retest: NOT AUTHORIZED by this document.
- T1→T2: BLOCKED.
- T0: untouched and independent.

## 9. Owner decision and implementation authorization

Owner approval received in chat on 2026-11-13. Authorization covers only the test-first internal instrumentation and typed failure classification in Sections 3–6, subject to every constraint in Section 7. Any deviation requires a separate scope decision.

Implementation must begin with failing tests (RED). No runtime/VPS retest, persistent service, T0 access, T1→T2 integration, or trading is authorized.

## 10. Implementation record

- Approval: GRANTED (2026-11-13).
- Source baseline reviewed: `9b2af66e68206898e51f638b67497d574a7252c4`.
- Current implementation disposition at approval: NOT STARTED.
- Next action: implement failing tests for monotonic receive-time propagation and typed rejection classification, then verify RED through the existing GitHub Actions CI before any production implementation.
- Execution-environment check (2026-11-13): BLOCKED. The available working container has no `cargo` executable and cannot resolve `github.com` for `git clone`/remote execution. GitHub repository metadata/file operations are available, but they cannot execute Rust tests. No source/test files were changed and no RED result is claimed.
- Resume condition: obtain a checkout-capable Rust environment or use a controlled commit-driven CI RED/GREEN sequence; preserve the same target branch and verify each exact SHA before proceeding.


### 2026-11-13 CI RED evidence update

- Test-only source commit: `9aab5f7d2df656825063f0c1d1aeb11104f65329` (superseded by formatting-only follow-up below).
- Formatting-only follow-up commit: `16c5e054cc502c7cbef6bdd96b224d2dc5fc9ce5`.
- CI run #563: [43339488935](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43339488935).
- Rust x86_64 job: `131603933925`; Rust native ARM64 job: `131603933936`.
- Both Rust jobs passed formatting and failed at Clippy compilation with the expected unresolved import `super::BufferedDepthUpdate` in `src/websocket/connection_manager.rs:951`. This confirms RED for the receive-time wrapper tests, not for typed rejection classification.
- Dashboard frontend, dashboard backend, security audit and Docker build jobs: PASS.
- Rust build, Rust tests, sidecar tests and artifacts: NOT RUN / NOT GENERATED because Clippy stopped the job.
- Disposition: receive-time wrapper RED = CONFIRMED; typed rejection RED = NOT YET IMPLEMENTED/VERIFIED; overall spec = IN PROGRESS.
- Next bounded action: add test-first coverage for typed rejection classification and precedence, verify those tests fail for the intended missing typed contract, then implement receive-time propagation through ring buffer and BTCUSDT attach/live buffers, bounded monotonic timing summaries, and typed classification. Preserve all Section 7 non-goals.
- No runtime/VPS test, T0 access, T1→T2 integration, persistent service, or trading was performed or authorized.

### 2026-11-13 typed rejection RED evidence

- Typed-rejection test-only commit: `769ba7a06a32e3cc42fb2f66c64c6fdb94fcb02e`.
- Formatting-only follow-up commit: `90d0a0510a2281e25c086ad6e8f233d2381cf91e`.
- Exact T1 source file blob after formatting: `src/orderbook_v1.rs` blob `1b9a71110fb80cd3b65f97996ec93f255d199d6b`.
- CI push run #567: [43342388400](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43342388400), source SHA `90d0a0510a2281e25c086ad6e8f233d2381cf91e`.
- Rust x86_64 job: `131613562376`. Format: PASS. Clippy compile: expected RED.
- Compiler confirms the missing typed contract: `apply_live_diff_classified` and `LiveDiffRejection` are not yet implemented. It also confirms the earlier missing `BufferedDepthUpdate` wrapper test remains RED.
- Rust build, Rust unit tests, sidecar tests and collector artifact generation are skipped after the expected Clippy failure. The workflow was still running in non-Rust jobs when this evidence was recorded; do not claim overall CI completion from this entry.
- Four typed-classification test groups added: source/observation/future-skew freshness; PU/watermark sequence; malformed header/invalid levels/depth/crossed book shape; combined-invalid validation precedence.
- Explicit precedence encoded by tests to preserve current validator order: malformed header (shape) before sequence; sequence before levels/freshness; level/structural shape before freshness. Existing decision watermark remains immutable on rejection.
- Disposition: typed rejection RED = CONFIRMED at compile boundary; assertions have not executed because the typed API is intentionally absent. Receive-time wrapper RED = previously CONFIRMED. Overall source implementation remains NOT STARTED.
- Next action: implement typed validation boundary without parsing error strings, then thread original monotonic receive time and insertion time through ring and BTCUSDT attach/live buffers. Preserve all Section 7 restrictions.

### 2026-11-13 bounded implementation progress — CI pending

- Current T1 source branch head recorded: `feature/t1-connection-sidecar-integration-20261107`.
- Current T1 source SHA: `1ff34809a951b61236a0b5f6b7770cbc66b3bf34`.
- Implementation commits on the same branch:
  - `950d92b7586a1709bd5d327db29ed4b4f627a40a` — typed live-diff rejection boundary; preserves the original validation order and keeps the legacy `apply_live_diff` API as an anyhow-compatible wrapper.
  - `b0242d7d52c06fa904aa3bc4dbd6cef5c3213113` — internal buffered envelope with original receive instant and insertion instant; ring buffer retains the metadata.
  - `6bc90865c9a91b6cf4a097c9991be612243918c6` — BTCUSDT live consumer typed classes and bounded per-batch timing/depth summary.
  - `343be9fa62b184610eb7f229fa6f1b2bc47e71db` — capture receive instant for both text and binary WebSocket frames before decoding/parsing.
  - `05bb5e3d3a161a9eac032306903d6c71d17bb32a` — preserve timing metadata through BTCUSDT REST-anchor attach and measure attach batch.
  - `a5b57fdba6031e1c2a0d18211fa07e7ec3181b61` / `f55f575eb5a9671cd7ed7f58c4e427e4c87b35a8` — deterministic monotonic timing helper/tests and consumer use of the tested helper.
  - `f9191f909376cfeda0b8f669df90c5ade0d10c45` / `af65a1acf0c369346758187a0db20b296cc4e7ef` / `1ff34809a951b61236a0b5f6b7770cbc66b3bf34` — stable five-class rejection labels, typed consumer mapping, and update-ID ordering classification.
- Additional formatting-only commits are retained in the same branch; no branch rewrite or merge was performed.
- Current instrumentation uses monotonic time only for receive-to-apply and buffer residence; UTC milliseconds remain the input to existing freshness validation. No Binance event-time substitution or freshness threshold change was made.
- The ring drain reports pre/post depth atomically. BTCUSDT attach and live batches log bounded summaries only; no per-event timing logs, unbounded history, persistent telemetry, or high-cardinality labels were added.
- Rejection labels are stable: `FRESHNESS_REJECTED`, `SEQUENCE_REJECTED`, `SHAPE_REJECTED`, `PUBLISH_FENCED`, `LEGACY_MIRROR_REJECTED`. Live-diff validation order is header -> sequence -> levels/structure -> source/observation freshness.
- `MAX_BOOK_AGE_MS` remains exactly `2_000`; ring capacity, eviction, retry/replay, reconnect and resnapshot policies were not intentionally changed.
- Latest CI push run #593: [43343115774](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43343115774), head SHA `1ff34809a951b61236a0b5f6b7770cbc66b3bf34`; jobs were QUEUED when recorded. Earlier intermediate runs failed at `cargo fmt` before compile; their formatting findings were corrected in later same-branch commits. Do not treat those intermediate failures as implementation test failures.
- Current disposition: implementation = IN PROGRESS; final fmt/Clippy/build/tests = NOT VERIFIED pending run #593; artifacts = NOT GENERATED/NOT VERIFIED. No VPS runtime retest or other non-goal activity performed.
- Next action: await latest source-head CI; fix only concrete findings, then obtain Rust x86_64 + native ARM64 fmt/Clippy/build/test and artifact evidence before considering this increment PASS.

### Implementation head correction — 2026-11-13

- T1 source branch advanced after the prior progress entry; current source SHA is `40711fd013e734b3cfc30bad68656d5e7b5249ca`.
- The latest timing adjustment measures receive-to-apply and buffer-residence durations immediately after `apply_live_diff_classified` returns, so the monotonic metric includes the live apply operation rather than stopping before it.
- Latest CI push run #595: [43343313970](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43343313970), head SHA `40711fd013e734b3cfc30bad68656d5e7b5249ca`; all jobs QUEUED when recorded.
- Prior source SHA `1ff34809a951b61236a0b5f6b7770cbc66b3bf34` and its run #593 are superseded for final acceptance; do not use the earlier SHA as the tested source head.
- Current status remains implementation IN PROGRESS / final validation NOT VERIFIED. No artifacts are claimed.

### CI queue progress — 2026-11-13

- Latest run #595 [43343313970](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43343313970) remains tied to exact T1 source SHA `40711fd013e734b3cfc30bad68656d5e7b5249ca`.
- Native ARM64 job `131616595149` has started; checkout and toolchain setup passed; `Swatinem/rust-cache@v2` is still in progress. ARM64 format/Clippy/build/test have not started yet.
- Rust x86_64, Docker, security, dashboard backend and frontend jobs remain QUEUED at this observation.
- No CI conclusion is available. This is runner queue/cache delay, not a source-code PASS or FAIL.
- Review spot-check: both text and binary WebSocket frames pass the original monotonic receive instant; only BTCUSDT consumes the typed V1 result; non-BTC symbols unwrap the original `DepthUpdateWs` and retain their legacy processing path; ring capacity/eviction code is unchanged. This is a source inspection only, not compiler verification.
- Overall status remains NOT VERIFIED pending run #595's Rust checks and artifacts.


### CI #595 formatting finding and bounded correction — 2026-11-13

- T1 run #595: [43343313970](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43343313970), exact checked-out source SHA `40711fd013e734b3cfc30bad68656d5e7b5249ca`.
- Rust x86_64 job `131616594745` and native ARM64 job `131616595149`: **FAIL at `cargo fmt --all --check` only**. Both Rust jobs skipped Clippy, build, unit tests, sidecar tests and artifact generation. ARM64 log identified two formatting-only diffs in `src/collectors/orderbook_manager.rs` around the buffered-drain tuple assignment and `build_snapshot` assignment. No compile or behavioral failure was reached.
- Dashboard backend job `131616595410`: PASS. Dashboard frontend job `131616595509`: PASS. Docker job `131616595141` and security job `131616595216` were still IN_PROGRESS at the latest poll; no final conclusion claimed.
- Minimal formatting correction committed on the same T1 branch `feature/t1-connection-sidecar-integration-20261107`: commit `37c20475423d02fb4aea710232f7fc347051c3d0`, message `style: fix orderbook manager formatting from CI 595`. Updated file blob: `83441f406a0ede01df1bb1c448b378706ad9bbcf` (previous blob `64e493bdf431e044e62a6ea5d09738685ae120da`). Only the two formatter-requested line wraps were changed.
- New-source validation: **NOT VERIFIED**. The commit's combined status query returned no status checks, and the PR-run lookup returned no associated run at the time of recording. Do not rerun jobs from #595 because they would validate the old SHA, not the correction.
- Current T1 status: formatting correction COMMITTED; new-SHA Rust fmt/Clippy/build/tests and artifact **NOT VERIFIED / NOT GENERATED**. Next step: locate or await a workflow run whose checked-out SHA is exactly `37c20475423d02fb4aea710232f7fc347051c3d0`; then verify both Rust architectures and all remaining CI jobs. If no run is triggered, inspect the workflow trigger policy before taking any further action. No runtime/VPS retest, T0 access, T1→T2 integration, persistent service, or trading was performed.
