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


## 2026-11-08 — T1 Sidecar finalization/append read-only source review

- Reviewed exact T1 source SHA `ed126fa8ecae61d70939336d51ffd4bf86acc102`, file `crates/connection-sidecar/src/lib.rs` (blob `7e2b58557692386bd24699861ba4aa545863dd55`).
- Review slice: `finalize_with_publish`, `publish_manifest_with`, `cleanup_temp_manifest_with`, `append_event`, and `validate_capture`.
- Confirmed by source inspection: finalization marks the writer poisoned before filesystem work; event-write/flush/sync failure also poisons the writer; manifest publication uses hard-link without replacement; post-publication temp unlink/directory-sync errors propagate while the writer remains terminal; capture validation checks bounded regular files, JSONL object records, manifest size/schema, byte count, digest, and event count.
- No additional confirmed correctness defect found within this bounded slice. This is a read-only source review, not a new test run or full hostile-filesystem/security certification.
- Existing PR #1 state rechecked: OPEN, DRAFT, NOT MERGED; head remains `ed126fa8ecae61d70939336d51ffd4bf86acc102`. One inline review thread remains unresolved but is marked outdated; its post-hard-link writer-poison finding is addressed by the regression test and current source. Thread was not manually resolved.
- Verdict: bounded source review **PASS — no new confirmed finding**; previously green CI remains the test evidence. TOCTOU/hostile-filesystem behavior, non-Unix durability semantics, and deployed runtime behavior remain **NOT VERIFIED**.
- No source changes, tests, collector execution, Binance/VPS runtime, T0 operation, PR merge, or draft-state transition.
- Next: choose a separate bounded T1 source-review slice (connection-state/event lifecycle and limits) before any broader integration/runtime proposal.


## 2026-11-08 — T1 Sidecar connection/heartbeat lifecycle review finding

- Reviewed exact T1 source SHA `ed126fa8ecae61d70939336d51ffd4bf86acc102`:
  - `crates/connection-sidecar/src/lib.rs`, blob `7e2b58557692386bd24699861ba4aa545863dd55`.
  - `crates/connection-sidecar/tests/sidecar_writer.rs`, blob `37614ded67022b116c8d0ba7e1f33d74e0746a1c`.
  - `crates/connection-sidecar/README.md`.
- Finding — **REQUIRED DESIGN REVIEW before treating the lifecycle contract as complete**: `SidecarWriter::disconnected()` rejects every disconnect while any Ping remains outstanding. The only current ways to clear a pending Ping are a matching Pong or `heartbeat_timed_out()` after strictly more than 60,000 ms. There is no event/API for a Ping abandoned because the socket remotely closed or hit a transport error before the timeout threshold.
- The current test `refuses_to_disconnect_or_finalize_with_an_unanswered_ping` explicitly codifies rejection, but it does not provide a valid terminal path for an early `REMOTE_CLOSE` / `TRANSPORT_ERROR`. In that situation, the caller cannot truthfully record the actual disconnect and schedule reconnect without either waiting until the Ping timeout and misclassifying the disconnect as `HEARTBEAT_TIMEOUT`, or leaving the connection lifecycle unresolved and preventing finalization.
- This conflicts with the documented `DISCONNECTED` reasons (including remote close and transport error) and reconnect flow. The crate README says it is an offline reference implementation and is not integrated into the upstream collector; therefore this is a contract/API correctness gap, not evidence of a current production collector outage.
- Recommended design direction (not implemented): add an explicit terminal resolution for outstanding Ping IDs when the socket closes (for example, a bounded `PING_ABANDONED` / `PING_CANCELLED` event tied to the disconnect reason), or define and test another truthful resolution that does not fabricate a heartbeat timeout. Preserve strict Ping/Pong correlation and event timestamp ordering.
- Status: **FINDING RECORDED / NOT FIXED / NOT VERIFIED BY TEST**. No code or test changed in this increment. The prior CI PASS at `ed126fa8...` remains valid only for the tests it ran; it does not resolve this lifecycle gap.
- No collector execution, Binance/VPS runtime, T0 action, live order, PR merge, or PR draft-state transition.
- Next: obtain authorization for a narrowly scoped offline regression test that reproduces early remote close/transport error with an outstanding Ping, then implement the smallest explicit resolution contract and verify through GitHub Actions on the existing PR branch.


## 2026-11-08 — T1 Sidecar early-disconnect heartbeat resolution — CLOSED

### Scope and implementation
- Authorized scope: deterministic offline regression test + minimal Sidecar lifecycle correction on the existing T1 PR branch only.
- T1 repo/branch: `kenznguyen/binance-futures-collector` / `feature/t1-connection-sidecar-integration-20261107`.
- Test-first sequence:
  - `12e5dfc46e003b6b1b7a0f0d8e3e659d2f4c8c53`: add early-close regression for `REMOTE_CLOSE` and `TRANSPORT_ERROR`.
  - `38f7226e30ecbcb86905f834db3c88e5a518091d`: rustfmt-only correction before behavioral RED.
  - RED confirmed in push run #207 `42450442409`: Collector Format/Clippy/Build/workspace tests passed; Sidecar writer format/Clippy passed; Sidecar offline test failed exactly at `resolves_outstanding_ping_when_socket_closes_before_timeout`, 26 passed / 1 failed. The failure was the expected `InvalidInput: cannot disconnect while heartbeat Pings remain unanswered`.
- Implementation:
  - `a4a7d46b89a0e3ae380d8b56a0f5fc8cea6166e1`: add `PING_ABANDONED` for each outstanding heartbeat when a socket closes, preserving the actual disconnect reason and avoiding fabricated `PING_TIMEOUT`; deterministic heartbeat-ID ordering; README contract update in `6411be38e89a4185f2c3116920882b2a62ffbbee`.
  - An intermediate Clippy run identified `explicit_counter_loop`; final correction uses `enumerate()` and makes the writer terminal if the disconnect event fails after abandonment events were persisted.
  - Final source/PR head SHA: `8f73459d7f1f0736f211c92b98ea9d7d6cc89df5`.
- Regression behavior now verified for both early `REMOTE_CLOSE` and `TRANSPORT_ERROR`: each outstanding Ping receives `PING_ABANDONED` with the real reason, then `DISCONNECTED`; reconnect scheduling and session finalization succeed; no `PING_TIMEOUT` is fabricated.

### Exact-source CI evidence
- PR CI run #214: [42450737104](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42450737104), **SUCCESS 5/5 jobs**, exact PR head `8f73459d7f1f0736f211c92b98ea9d7d6cc89df5`, base `bc4f0ef633fbeee4a49defd72827f17162693805`.
- Collector job: Format, Clippy, Build, workspace tests, Sidecar format, Sidecar Clippy, Sidecar offline tests all PASS.
- Test counts: Collector library 43/43; Collector binary 1/1; Sidecar unit tests 9/9; Sidecar integration tests 27/27. Regression `resolves_outstanding_ping_when_socket_closes_before_timeout` PASS.
- Dashboard backend, dashboard frontend, Security audit, Docker build all PASS in PR CI #214.
- Push CI run #213: [42450733372](https://github.com/kenznguyen/binance-futures-collector/actions/runs/42450733372), exact head SHA `8f73459d7f1f0736f211c92b98ea9d7d6cc89df5`. Collector, dashboard backend/frontend, Docker jobs PASS; Security job was still in progress at the time of this record. PR CI #214 is the complete 5/5 result.
- Linux artifact from push run #213: ID `13605197747`; name `t1-collector-linux-x86_64-8f73459d7f1f0736f211c92b98ea9d7d6cc89df5`; size 4,186,964 bytes; GitHub metadata SHA-256 `a5aa11cac5c63436e5c365700081157acfe23808d63639cc407673cd7108a311`. Metadata only; payload has not been independently downloaded/rehashed in this increment.

### Verdict and limits
- Verdict: **PASS** — heartbeat lifecycle regression fixed and exact-head PR CI #214 5/5 PASS.
- This validates the Sidecar offline reference crate only. README continues to state that the crate is not integrated into the upstream collector.
- Runtime heartbeat behavior, real WebSocket close/reconnect handling, hostile-filesystem behavior, and deployed/VPS behavior remain **NOT VERIFIED**.
- No collector execution, Binance connection, VPS deployment, database access, T0 changes, live orders, PR merge, or PR draft-state change.
- PR #1 remains **OPEN / DRAFT / NOT MERGED**.
- Next: continue a bounded offline review of Sidecar validation/event lifecycle invariants on the same PR branch; no runtime integration/deployment without separate authorization.
