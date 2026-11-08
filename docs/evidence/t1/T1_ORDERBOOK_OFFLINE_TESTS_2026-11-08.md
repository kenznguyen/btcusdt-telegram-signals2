# T1 Order Book Offline Assurance Tests — 2026-11-08

## Scope and boundaries

Authorized scope: add deterministic offline tests for the Order Book snapshot/attach/reconnect behavior in `kenznguyen/binance-futures-collector`.

- No Binance connection, VPS runtime, collector launch, T0 database/Feeder action, exchange API key, live order, or execution path.
- Existing branch/PR retained: `feature/t1-connection-sidecar-integration-20261107`, PR #1 (OPEN / DRAFT / NOT MERGED).
- Existing GitHub Actions workflow reused; no new workflow or branch created.

## Source changes

Current PR head/source SHA: `684ea8bed55d6a3cf0ad50d02ee8b9586bb9e789`.

Commits:
- `efc5887de9c19e19c9150455a7d4500afc285fd0` — extracted normalized attach application into a pure helper and added three offline tests.
- `152cc04a3d7079345829144eb1e9560dcf156623` — removed a redundant reconnect fixture.
- `684ea8bed55d6a3cf0ad50d02ee8b9586bb9e789` — rustfmt correction.

Changed file: `src/collectors/orderbook_manager.rs`.

Tests added:
1. `snapshot_plus_buffered_diffs_matches_independent_reconstruction`: snapshot + covered buffered diff + accepted absolute-quantity update compared against an independently assembled expected book.
2. `initial_attach_rejects_a_missing_diff_after_the_bridge`: a pu discontinuity after the bridge returns a rejected attach result; the symbol must not be promoted to LIVE by this path.
3. `reconnect_pu_break_is_visible_in_raw_sequence_but_live_book_can_stale`: documents the intentional live-loop behavior—absolute updates heal touched levels while quiet levels may remain stale after a reconnect gap.

The attach helper preserves the prior behavior: updates before a later pu break remain applied, but the attach returns failure and does not transition to LIVE. No immediate reconnect resnapshot policy was introduced.

## CI provenance and current result

Existing workflow: `.github/workflows/ci.yml`, GitHub Actions, workflow name `CI`.

- First PR workflow run: [42448670426](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42448670426).
- PR head at that run: `152cc04a3d7079345829144eb1e9560dcf156623`.
- Checked-out synthetic merge SHA from Collector job log: `597269dc0a153e15a92ed014ac3324fb6626b4db`, merging PR head `152cc04...` with base `bc4f0ef633fbeee4a49defd72827f17162693805`.
- Result: Collector Format failed due two rustfmt-only differences. Clippy, Build, Test, Sidecar format/Clippy/tests and artifact steps were skipped. This run does not verify the new tests.
- Corrected formatting in commit `684ea8bed55d6a3cf0ad50d02ee8b9586bb9e789`.
- Follow-up PR workflow run: [42448706196](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42448706196), run number 198. It was observed IN_PROGRESS; final conclusion, checked-out merge SHA, job outcomes and artifacts were not yet available at report creation.

## Verdict

- Source change committed: PASS.
- Rust formatting on initial run: BLOCKED by formatting-only differences; correction committed.
- Focused Order Book tests: NOT VERIFIED pending follow-up CI.
- Full Collector build/Clippy/tests: NOT VERIFIED pending follow-up CI.
- Overall offline Order Book assurance: NOT VERIFIED.

No runtime or T0 changes. No artifact can be claimed from the failed first run. The follow-up run is required before promoting any test result.
