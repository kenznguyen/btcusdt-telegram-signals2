# T1 Order Book Offline Assurance Tests — 2026-11-08

## Scope and boundaries

Authorized scope: add deterministic offline tests for the Order Book snapshot/attach/reconnect behavior in `kenznguyen/binance-futures-collector`.

- No Binance connection, VPS runtime, collector launch, T0 database/Feeder action, exchange API key, live order, or execution path.
- Existing branch/PR retained: `feature/t1-connection-sidecar-integration-20261107`, PR #1 (OPEN / DRAFT / NOT MERGED).
- Existing GitHub Actions workflow reused; no new workflow or branch created.

## Source changes

Current PR head/source SHA: `3c2745a30f3cb20375a20188b5f4e10e7b7bbfef`.

Commits:
- `efc5887de9c19e19c9150455a7d4500afc285fd0` — extracted normalized attach application into a pure helper and added three offline tests.
- `152cc04a3d7079345829144eb1e9560dcf156623` — removed a redundant reconnect fixture.
- `684ea8bed55d6a3cf0ad50d02ee8b9586bb9e789` — rustfmt correction.

Changed file: `src/collectors/orderbook_manager.rs`.

Tests added:
1. `snapshot_plus_buffered_diffs_matches_independent_reconstruction`: snapshot + covered buffered diff + accepted absolute-quantity update compared against an independently assembled expected book.
2. `initial_attach_rejects_a_missing_diff_after_the_bridge`: a pu discontinuity after the bridge returns a rejected attach result; the symbol must not be promoted to LIVE by this path.
3. `reconnect_pu_break_leaves_untouched_levels_stale_in_live_book`: documents the intentional live-loop behavior—absolute updates heal touched levels while quiet levels may remain stale after a reconnect gap. This test does not verify raw-tape persistence.

The attach helper preserves the prior behavior: updates before a later pu break remain applied, but the attach returns failure and does not transition to LIVE. No immediate reconnect resnapshot policy was introduced.

## CI provenance and current result

Existing workflow: `.github/workflows/ci.yml`, GitHub Actions, workflow name `CI`.

- First PR workflow run: [42448670426](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42448670426).
- PR head at that run: `152cc04a3d7079345829144eb1e9560dcf156623`.
- Checked-out synthetic merge SHA from Collector job log: `597269dc0a153e15a92ed014ac3324fb6626b4db`, merging PR head `152cc04...` with base `bc4f0ef633fbeee4a49defd72827f17162693805`.
- Result: Collector Format failed due two rustfmt-only differences. Clippy, Build, Test, Sidecar format/Clippy/tests and artifact steps were skipped. This run does not verify the new tests.
- Corrected formatting in commit `684ea8bed55d6a3cf0ad50d02ee8b9586bb9e789`.
- Follow-up PR workflow run: [42448706196](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42448706196), run number 198. Result: SUCCESS, 5/5 jobs; checked-out merge SHA `a3b2234fb0b113bb2a837ab6fe7ded0d45e1d7c8`, merging PR head `684ea8bed55d6a3cf0ad50d02ee8b9586bb9e789` with base `bc4f0ef633fbeee4a49defd72827f17162693805`. Collector library tests 43/43, main 1/1; all three offline Order Book tests passed. No artifacts were produced.

## Verdict

- Source change committed: PASS.
- Rust formatting on initial run: BLOCKED by formatting-only differences; correction committed.
- Source change and full CI validation at SHA `684ea8...`: PASS.
- All three Order Book tests at merge SHA `a3b2234...`: PASS (included in 43 passing library tests).
- Full Collector format/Clippy/release build/tests and all five CI jobs at run 198: PASS.
- Raw-tape persistence and real reconnect resnapshot/recovery: NOT VERIFIED by these offline unit tests.
- Latest source SHA `3c2745a30f3cb20375a20188b5f4e10e7b7bbfef`: run 200 PASS, 5/5 jobs. Collector Format, Clippy, release Build, and tests PASS; three named Order Book tests PASS; library 43/43, main 1/1. Sidecar tests 8/8 + 27/27; dashboard frontend/backend, Docker build, Security audit PASS. Checked-out synthetic merge SHA `3ec602e1c3508747fccb7a47e4d9e737a2239720`, merging PR head `3c2745...` with base `bc4f0ef633fbeee4a49defd72827f17162693805`.
- Overall offline Order Book assurance: PASS for the three explicitly tested deterministic behaviors at latest source SHA `3c2745...`.

No runtime or T0 runtime changes. No artifact was produced by runs 198 or 200; artifact preparation/upload were skipped in run 200. Raw-tape persistence and real reconnect resnapshot/recovery remain NOT VERIFIED.
