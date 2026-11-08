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
- `3c2745a30f3cb20375a20188b5f4e10e7b7bbfef` — clarified reconnect test name/assertions so it does not imply raw-tape persistence coverage.

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

- Latest-head validation: [run 200](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42448956679), event `pull_request`, conclusion SUCCESS, all five jobs completed successfully. Collector job ID `128633858017`; exact checked-out merge SHA `3ec602e1c3508747fccb7a47e4d9e737a2239720`.

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


## 2026-11-08 — T1 Sidecar post-hard-link writer poison regression

- T1 source repo: `kenznguyen/binance-futures-collector`, branch `feature/t1-connection-sidecar-integration-20261107`, PR #1 remains OPEN / DRAFT / NOT MERGED.
- Source commit: `8892b72570d7c3f12c7d714aaeb37def63c56dcc`; changed file `crates/connection-sidecar/src/lib.rs`.
- Existing implementation was verified to set `self.poisoned = true` before the first filesystem operation in finalization. The code change adds a private publication-injection seam; production still uses hard-link, temp unlink, and parent-directory sync.
- Added regression test `post_hard_link_publication_failure_poisons_writer_and_preserves_manifest_consistency`: it creates a real writer and event stream, performs a real hard-link to publish the manifest, injects a post-link error, verifies a subsequent reconnect event is rejected with BrokenPipe, and verifies the final manifest/sidecar pair validates as SealedConsistent with 2 events.
- GitHub Actions push run #202: [42449429950](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42449429950), status IN_PROGRESS at handoff update. Collector Format PASS; Collector Clippy/Build in progress; Sidecar offline tests pending. Dashboard frontend and backend PASS. Security and Docker jobs in progress.
- Artifact inventory checked while run was in progress: empty; do not infer final artifact outcome.
- Verdict at handoff update: source change committed; regression test and full CI **NOT VERIFIED** pending run #202.
- No VPS, Binance, T0 runtime/database, live execution, PR merge, or PR draft-state change.
- Next: poll run #202; inspect Sidecar offline test output and exact checked-out SHA. If green, record exact CI evidence; if failed, diagnose only the demonstrated issue on the same branch.


## 2026-11-08 — T1 Sidecar post-hard-link writer poison regression — CI closeout

- T1 source repo/branch: `kenznguyen/binance-futures-collector` / `feature/t1-connection-sidecar-integration-20261107`; PR #1 remains OPEN / DRAFT / NOT MERGED.
- Exact source SHA: `ed126fa8ecae61d70939336d51ffd4bf86acc102`; changed file `crates/connection-sidecar/src/lib.rs`. This is the rustfmt-only correction to the regression-test commit `8892b72570d7c3f12c7d714aaeb37def63c56dcc`.
- Push CI run #203: [42449616310](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42449616310), event `push`, conclusion SUCCESS, 5/5 jobs.
- PR CI run #204: [42449619551](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42449619551), event `pull_request`, conclusion SUCCESS, 5/5 jobs. PR head `ed126fa8...`; base `bc4f0ef633fbeee4a49defd72827f17162693805`. Synthetic merge SHA not recorded in the fetched job summary; do not infer it.
- Push Collector job checked out exact source SHA `ed126fa8ecae61d70939336d51ffd4bf86acc102`.
- Push CI: Collector Format/Clippy/release Build/Test PASS; base Collector tests 43/43 library and 1/1 main. Sidecar writer format PASS; Sidecar Clippy PASS; Sidecar offline tests PASS: 9/9 in `connection_sidecar`, 27/27 in the additional sidecar test target. Regression test `create_cleanup_tests::post_hard_link_publication_failure_poisons_writer_and_preserves_manifest_consistency` explicitly PASS.
- Dashboard frontend, Dashboard backend, Security audit, and Docker build all PASS. Overall push CI 5/5 PASS; PR CI 5/5 PASS.
- Artifact: ID `13605356026`; name `t1-collector-linux-x86_64-ed126fa8ecae61d70939336d51ffd4bf86acc102`; size 4,186,964 bytes; SHA-256 `5ddee4e79c43baead94f2a01f8069e56abff090e9796903f892c9a7eb5b0eff8`; [download page](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42449616310/artifacts/13605356026); expires 2026-11-15. Artifact metadata is verified; payload bytes were not independently downloaded/rehashed.
- Verdict: source regression test + push CI + PR CI **PASS** for exact source SHA `ed126fa8...`; artifact metadata recorded. Previous run #202's format failure is superseded by the rustfmt correction and green runs #203/#204.
- Limitations remain: no Binance/VPS runtime or real filesystem fault injection against deployed process; this is deterministic offline test coverage. No T0 runtime/database/Feeder, live execution, PR merge, or PR draft-state change.
- Next: documentation/evidence closeout only, then continue with the next scoped T1 offline review item. Do not deploy/run collector or merge PR without explicit authorization.


## 2026-11-08 — T1 Linux artifact payload independent verification

- T1 source repo/branch: `kenznguyen/binance-futures-collector` / `feature/t1-connection-sidecar-integration-20261107`; PR #1 remains OPEN / DRAFT / NOT MERGED.
- Artifact downloaded from GitHub Actions run #203, artifact ID `13605356026`, exact name `t1-collector-linux-x86_64-ed126fa8ecae61d70939336d51ffd4bf86acc102`.
- Downloaded ZIP size: 4,186,964 bytes; matches GitHub artifact metadata.
- Independently computed ZIP SHA-256: `5ddee4e79c43baead94f2a01f8069e56abff090e9796903f892c9a7eb5b0eff8`; exact match with GitHub artifact metadata digest.
- Archive contents: `binance-futures-collector` (9,978,328 bytes) and `SHA256SUMS` (92 bytes); no unexpected files.
- Embedded checksum verification: `sha256sum -c SHA256SUMS` PASS; binary SHA-256 `c526d422cad2244f8041283377d5240f709f16df72502af2f508cc44a4c6b9e3`.
- Static ELF inspection: ELF64, little-endian, x86-64, position-independent executable; GNU/Linux interpreter `/lib64/ld-linux-x86-64.so.2`; dynamically linked against `libgcc_s.so.1`, `libm.so.6`, and `libc.so.6`.
- Static strings identify `binance-futures-collector 1.0.0` and its documented `--version|--help` usage. Binary was NOT executed.
- Provenance: run #203 Collector job logs had already established checkout of exact source SHA `ed126fa8ecae61d70939336d51ffd4bf86acc102`; the binary itself does not expose a verifiable embedded Git SHA. Therefore source association relies on the exact workflow checkout/build evidence plus artifact identity, not an embedded commit marker.
- Verdict: artifact download/size/SHA-256 and internal binary checksum **PASS**; archive structure **PASS**; ELF architecture **PASS**. Runtime behavior, dynamic-library availability on target host, and execution remain **NOT VERIFIED / NOT RUN**.
- No collector execution, Binance connection, VPS deployment, T0 action, live order, PR merge, or PR draft-state change.
- Next: continue bounded offline/source review on the same T1 PR branch. Do not execute or deploy the binary without separate explicit authorization.
