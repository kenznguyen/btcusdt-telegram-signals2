# T1 Native ARM64 CI, Artifact and Bounded Runtime Verification — 2026-11-13

## Scope

Record native ARM64 CI/artifact verification and the subsequently authorized, bounded, manual BTCUSDT-only runtime smoke on the current Scaleway ARM64 test host. This increment includes read-only analysis of captured CSV/log evidence and source inspection at the exact collector source SHA. It does not authorize source changes, persistent deployment, T0 access, or T1→T2 integration.

## Source and workflow provenance

- Repository: `kenznguyen/binance-futures-collector`
- Branch: `feature/t1-connection-sidecar-integration-20261107`
- Exact source SHA: `9b2af66e68206898e51f638b67497d574a7252c4`
- Changed file in that source commit: `.github/workflows/ci.yml` only
- Workflow file blob SHA: `e907972128d680d7d4b3cf0f0e1cbc533a53c869`
- Push workflow run: [43334117748](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43334117748) — completed / success
- PR workflow run: [43334123943](https://github.com/kenznguyen/binance-futures-collector/actions/runs/43334123943) — completed / success
- Both runs report the exact head SHA above.

## CI results

Push run `43334117748`:
- Native ARM64 build/test/artifact job `131585840822`: SUCCESS.
- Native ARM64 runner assertion, format, Clippy, release build, tests, sidecar offline tests, ELF verification/checksum preparation, artifact upload: all SUCCESS.
- Docker build, security checks, dashboard frontend, dashboard backend, and existing x86-64 collector job: SUCCESS.

PR run `43334123943`:
- Native ARM64 build/test job `131585861454`: SUCCESS.
- Runner assertion, format, Clippy, release build, tests and sidecar offline tests: SUCCESS.
- ELF verification and artifact upload steps were SKIPPED by workflow conditions for the PR event; the successful push-run artifact remains the verified artifact.
- Other workflow jobs: SUCCESS.

Overall push CI: PASS. Overall PR CI: PASS.

## ARM64 artifact provenance and payload verification

- Artifact ID: `13996767785`
- Artifact name: `t1-collector-linux-aarch64-9b2af66e68206898e51f638b67497d574a7252c4`
- GitHub-reported size: 3,985,895 bytes
- GitHub expiry at retrieval: `2026-11-20T00:09:20Z`
- Downloaded ZIP: `t1-arm64-9b2af66.zip`
- ZIP size: 3,985,895 bytes
- ZIP SHA-256: `a1fbb27bcdb7d47b223b3a85ed40bef0df2a2328a9ae3a0c4b735e3066a9e7b0`
- Archive members: `binance-futures-collector`, `SHA256SUMS`, `ELF-IDENTITY.txt`
- Embedded SHA256SUMS verification: PASS
- Binary SHA-256: `6dc9b691700c464784b475d2da2ffdcbb4eae62169ee31e74d8e0fba51966469`
- ELF identity: ELF64, little-endian, PIE, dynamically linked, AArch64; interpreter `/lib/ld-linux-aarch64.so.1`.
- `file`, `readelf` (on artifact verification environment), and checksum verification agree.

The x86-64 artifact from the same push run (ID `13995953595`) is not suitable for the ARM64 host.

## Current VPS and preflight evidence

Owner-provided current host observations:
- Scaleway type: `SCW-BASIC2-A2C-4G`
- Ubuntu 24.04.5 LTS, kernel `6.8.0-147-generic`
- `aarch64`, 2 CPUs, approximately 3.8 GiB RAM, no swap
- Root disk 8.0G total; approximately 5.3G available before runtime smoke
- Current host is a new test instance; it is not the previously deleted `btcquant-t0-t1-test-01`.

Preflight confirmed architecture compatibility, staging path permissions, available disk/RAM, and no existing T1 runtime paths before staging. No package installation was performed. VPS lacked `unzip` and `readelf`; neither was installed.

Artifact transfer and verification on VPS:
- ZIP SHA-256 matched `a1fbb27bcdb7d47b223b3a85ed40bef0df2a2328a9ae3a0c4b735e3066a9e7b0`.
- Extracted binary SHA-256 matched embedded `SHA256SUMS`.
- `file` identified the binary as AArch64 ELF64 PIE.
- `--version` returned `binance-futures-collector 1.0.0`, exit 0.
- `--help` returned usage successfully, exit 0.

## Runtime configuration provenance and limits

- Config source: `config.example.toml` from the exact T1 source SHA above.
- Git blob SHA of source config: `3436a8b75dc827a9299c083e9af783c8a74196c3`.
- TOML parse and targeted assertions: PASS.
- Config scope: `symbols = ["btcusdt"]`; output paths confined to `/home/ubuntu/t1/staging/runtime/`; depth limit 50; update speed 500ms; snapshot interval 600s.
- API key remains commented; proxy disabled; tracking disabled.
- Runtime executed as unprivileged `ubuntu` user, manually in foreground, for approximately 80–84 seconds, then stopped with Ctrl+C/SIGINT.
- No broad-symbol collection and no background service/autostart.

## Bounded runtime smoke results

Observed log and runtime outputs:
- Collector loaded the staged config and started BTCUSDT public/market WebSocket batches.
- Two WebSocket connections established; BTCUSDT Order Book entered LIVE after initial snapshot attach.
- Runtime produced CSV data for trades, depth updates, initial/bridge snapshots, funding rates, mark/index/premium klines, open interest, liquidations, long/short ratio and taker buy/sell ratio.
- Order Book diff CSV: 165 rows.
- Initial snapshot CSVs: 100 data rows each.
- Bridge snapshot CSV: 980 data rows.
- Trades CSV: 1,670 data rows.
- Depth updates and other market data files were present in the configured output tree.
- Stats JSON: uptime 80s; `messages_total=1738`; `connection_status=connected`; `active_connections=2`; `total_reconnects=0`; `trades_written=1576`; RSS approximately 18.16 MB; CPU approximately 0.80%; FD count 29.
- Stats log reported 0 runtime errors.
- One resnapshot gap was recorded at `2026-11-13T00:26:13Z`, reason `v1_live_sequence_or_shape_failure`.
- Log reported a live diff rejection with `source timestamp is stale`, followed by resnapshot and successful return to LIVE.
- SIGINT graceful shutdown completed; CSV buffers flushed and gap registry saved.
- No collector process remained after shutdown.
- Disk usage remained approximately 35% with 5.3G available.

## Order Book V1 evidence analysis

### Diff internal continuity

Read-only validation of all 165 depth update rows:
- `PU_MISMATCH_COUNT=0`: every current event's `prev_update_id` matched the previous row's `last_update_id`.
- `INVALID_RANGE_COUNT=0`: every row had `first_update_id <= last_update_id`.
- Result: file-internal diff continuity PASS for this captured file only.

This does not by itself prove continuity across unrecorded/reconnect boundaries or correctness of all runtime states.

### Initial snapshot/bridge

Captured values:
- Initial REST snapshot `last_update_id=12094987193882`.
- Bridge snapshot `last_update_id=12094987218439`.
- Fourth recorded diff event ended at `12094987218439`; the next event's `prev_update_id` was also `12094987218439`.

Observed initial bridge sequence alignment: PASS for the captured evidence.

### Resnapshot bootstrap

Captured second initial snapshot:
- Timestamp: `2026-11-13T00:26:14.549Z`
- `last_update_id=12094990383543`

The diff event around that point:
- Timestamp: `2026-11-13T00:26:14.543Z`
- `U=12094990344564`
- `u=12094990394031`
- `pu=12094990344184`

The snapshot update ID satisfies the bootstrap overlap condition `U <= L + 1 <= u`; the next event's `pu` matches the preceding event's `u`. This is consistent with valid snapshot/diff re-anchoring in the captured data. It does not independently prove the exact internal event-application scheduling.

### Freshness warning and source inspection

Source inspection at exact SHA `9b2af66e68206898e51f638b67497d574a7252c4`:
- `DepthUpdateWs::to_csv()` stores Binance `event_time` (E) in CSV `timestamp_ms`.
- `apply_live_diff()` validates source event timestamp against processing time with `MAX_BOOK_AGE_MS = 2,000`.
- BTCUSDT live loop drains buffered events and applies them sequentially; loop ticker interval is 500ms.
- A freshness failure is surfaced in logs as `source timestamp is stale`, but the manager records the broader gap reason `v1_live_sequence_or_shape_failure`, which conflates freshness with sequence/shape failures.
- Captured event timestamps around the gap show events approximately 502ms apart. At the gap registry timestamp `00:26:13.523Z`, the event at `00:26:11.029Z` was 2,494ms old, while the immediately preceding event at `00:26:11.531Z` was 1,992ms old.
- The gap registry timestamp is recorded after the failing freshness check; it is not the exact guard evaluation time. Therefore the exact rejected event cannot be proven from this comparison alone.

Assessment: processing backlog / consumer lag causing the 2-second source freshness guard to reject an older event is the leading hypothesis. It is not proven as the unique root cause. Sequence continuity in the captured file is intact, so the stale warning should not be treated as proof of a sequence gap.

## Disposition

- Exact-SHA native ARM64 CI: **PASS**.
- ARM64 artifact provenance, checksum and ELF architecture: **PASS**.
- VPS preflight and artifact transfer/checksum: **PASS**.
- CLI execution: **PASS**.
- BTCUSDT-only bounded runtime data capture: **PASS**.
- Graceful shutdown: **PASS**.
- Captured diff file internal continuity: **PASS**.
- Initial bridge and captured resnapshot bootstrap alignment: **PASS for captured evidence**.
- Runtime acceptance overall: **PARTIAL**.
- Order Book V1 end-to-end runtime correctness: **PARTIAL / NOT VERIFIED**; freshness rejection occurred and exact rejected event / processing lag is not proven.
- T1 → T2 integration: **BLOCKED**.

## Safety boundary observed

No source code was changed. No persistent runner, systemd unit, service, or autostart was created. No package was installed. No credentials or exchange API keys were used. No T0 database or canonical data was accessed. No T1→T2 integration was performed. No trading API or order was used. Runtime was manually started, BTCUSDT-only, bounded, and stopped. Paper-only posture remains; `AI_EXECUTION_ENABLED=false`.

## Next step and limits

Next bounded engineering step is a source-level diagnosis of consumer lag and freshness handling: inspect how the live loop scheduling, ring-buffer ingestion/drain, and processing batch size interact with the 2-second freshness limit; determine whether lag is transient or systemic; and improve failure classification in a separately approved change if warranted. Any change must be test-driven and preserve fail-closed behavior.

Do not widen symbols, repeat runtime capture, tune freshness thresholds, modify collector source, connect T0/T2, enable persistent services, or place orders without explicit approval. T1→T2 remains blocked.


## 2026-11-13 — Clock offset and deeper Order Book consumer-path audit

### Clock synchronization probe

Owner-provided read-only VPS results:
- `timedatectl`: `NTP=yes`, `NTPSynchronized=yes`.
- Five Binance USD-M `/fapi/v1/time` samples:
  - offset_ms: -20, -6, +3, -4, 0
  - RTT_ms: 268, 230, 249, 241, 253
- Median offset: -4 ms; observed range: -20 ms to +3 ms.

Disposition: VPS clock skew is **NOT A PLAUSIBLE PRIMARY EXPLANATION** for a 2,000 ms source-freshness rejection in this capture. This is a five-sample bounded comparison; it is not a continuous clock-discipline guarantee.

### Additional exact-SHA source findings

Inspected at T1 source SHA `9b2af66e68206898e51f638b67497d574a7252c4`:
- `WebSocketMessage::DepthUpdate` carries a socket-read `received_at: Instant`, but the BTCUSDT depth ring buffer stores only `DepthUpdateWs`; the receive instant is not retained with the buffered update.
- The BTCUSDT live loop drains the ring buffer every 500 ms and applies each update sequentially.
- At live application, the caller passes the same `Utc::now()` value as both `observed_at_ms` and `decision_time_ms`. Thus the V1 snapshot records application time as observation time; it cannot measure socket-to-buffer or buffer-residence delay for each event.
- `ws_latency_ms` is updated in the message handler from the socket-read `Instant`; it measures socket-read-to-handler-processing lag, not time spent waiting in the separate order-book ring buffer.
- Every `apply_live_diff()` error is currently mapped to gap reason `v1_live_sequence_or_shape_failure`, including freshness errors. The log text preserves the actual error string, but the gap registry category loses that distinction.

### Updated assessment

- Clock-skew hypothesis: **DOWN-RANKED** by the observed median -4 ms offset.
- Consumer backlog / ring-buffer residence / sequential apply delay: **PLAUSIBLE, NOT PROVEN**.
- Exact event rejected and precise delay at guard evaluation: **NOT VERIFIED**.
- Source timestamp anomaly or upstream event delay: **NOT EXCLUDED**.
- Root cause: **NOT VERIFIED**.

### Next bounded engineering step

Before changing collector behavior, design a source-level, test-first diagnostic increment that preserves fail-closed behavior and distinguishes:
1. exchange event age at apply time;
2. socket receive-to-handler delay;
3. socket receive-to-orderbook-apply delay;
4. batch size and apply-loop duration;
5. failure class (freshness vs sequence vs shape).

Do not raise `MAX_BOOK_AGE_MS`, change timestamp semantics, alter ring-buffer capacity, or repeat VPS runtime capture as part of this diagnostic design. Any source change or new runtime capture requires a separately bounded approval. T0 remains untouched; T1→T2 remains BLOCKED.
