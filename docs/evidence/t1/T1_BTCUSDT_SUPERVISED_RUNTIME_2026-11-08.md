# T1 BTCUSDT supervised runtime and graceful shutdown — 2026-11-08

## Scope
Record user-provided VPS evidence for the first bounded T1 Collector run on BTCUSDT. The run was supervised for 300 seconds and stopped with SIGTERM. T1 data paths remained isolated under /home/ubuntu/t1. No T0 process/config/database changes were made as part of this T1 run. No live trading or exchange orders.

## Source and CI provenance
- T1 repository: kenznguyen/binance-futures-collector.
- T1 branch: feature/t1-connection-sidecar-integration-20261107.
- Exact T1 source SHA associated with the deployed release: d8ac9fc820dcf2e912e66518a1a1c73a8fa81ac7.
- GitHub Actions push run: https://github.com/kenznguyen/binance-futures-collector/actions/runs/42424240328 — SUCCESS, 5/5 jobs.
- Artifact ID: 13594961114; artifact name: t1-collector-linux-x86_64-d8ac9fc820dcf2e912e66518a1a1c73a8fa81ac7.
- Prior VPS verification: SHA256SUMS returned OK; binary identified as Linux x86_64 ELF; --version returned binance-futures-collector 1.0.0.
- This runtime increment did not trigger a new GitHub Actions run or publish a new artifact. The runtime evidence is user-provided VPS output.

## Runtime evidence
- Runtime log: /home/ubuntu/t1/logs/runtime-5m.stdout.log (12,458 bytes). A second log path, collector_rCURRENT.log, was also present (12,458 bytes).
- Start activity in log begins at approximately 2026-11-07 23:33:00 UTC; SIGTERM received at 23:38:00 UTC.
- stats.json reported timestamp 2026-11-07T23:38:00.878127427+00:00 and uptime_seconds=300.
- Stats: messages_total=1142; trades_written=542; messages_per_sec≈3.0001; ws_latency_ms≈1.3533; connection_status=connected; active_connections=2; total_reconnects=0; RSS≈18.24 MB; CPU≈1.20%; fd_count=26.
- Runtime log reported two WebSocket connections, orderbooks live 1/1, and Errors: 0 in the periodic reports shown.
- Final report before shutdown: depth messages 595, trades 542, klines 4, liquidations 1.
- At the point of a later process inspection, pgrep found no running binance-futures-collector process.
- Only BTCUSDT paths were observed under /home/ubuntu/t1/data/futures.

## Output inventory and CSV checks
13 CSV files were present in the timestamp/size inventory. The CSV structure inspection output was truncated while printing the large orderbook depth-update row; therefore only the nine stream files below have independently visible line counts and header/sample records in the supplied output:

| Stream | CSV lines | Data rows |
|---|---:|---:|
| trades | 543 | 542 |
| orderbook depth updates | 596 | 595 |
| klines | 6 | 5 |
| mark price klines | 8 | 7 |
| long/short ratio | 25 | 24 |
| taker buy/sell ratio | 9 | 8 |
| liquidations | 2 | 1 |
| funding rates | 2 | 1 |
| open interest | 2 | 1 |
| index price klines | NOT CAPTURED | File existence and size were recorded; row count/content not visible in the truncated CSV inspection output |
| premium index klines | NOT CAPTURED | File existence and size were recorded; row count/content not visible in the truncated CSV inspection output |
| orderbook snapshot | NOT CAPTURED | File existence and size were recorded; row count/content not visible in the truncated CSV inspection output |
| initial orderbook snapshot | NOT CAPTURED | File existence and size were recorded; row count/content not visible in the truncated CSV inspection output |

Note: the timestamp/size inventory confirms the remaining four CSV files exist, but the supplied CSV inspection output was truncated before their headers, samples, or line counts appeared. Do not infer their row counts or content validity from file existence alone.

## Graceful shutdown evidence
- At 2026-11-07 23:38:00 UTC the process logged: Received SIGTERM; beginning graceful shutdown.
- It then logged stopping WebSocket ingest.
- Both WebSocket batches logged a Pong timeout/disconnect while shutdown was underway. These warnings are retained as observed; available evidence does not establish an independent pre-shutdown connection failure.
- Message handler stopped at 23:38:01 UTC.
- CSV buffers were flushed and the gap registry was saved.
- Final marker: Shutdown complete at 23:38:01 UTC.

## Verdict
| Check | Status | Evidence boundary |
|---|---|---|
| Deployed binary identity | PASS | Prior VPS checksum, architecture and version checks; source SHA tied to CI artifact |
| Supervised runtime duration | PASS | stats uptime_seconds=300 and log timestamps |
| WebSocket ingestion | PASS | 1,142 messages; depth/trades and two active connections reported |
| BTCUSDT data output | PASS | 13 CSV files across the observed stream categories; headers and data rows shown |
| Runtime errors in periodic reports | PASS for observed reports | Logs show Errors: 0 in periodic summaries; does not establish zero warnings |
| Graceful SIGTERM path | PASS | Handler stopped, CSV flush, gap registry save, Shutdown complete |
| Shutdown-time Pong timeout warnings | OBSERVED / REVIEW | Coincident with SIGTERM and batch shutdown; not silently treated as a clean disconnect-free run |
| Reconnect recovery under an unplanned outage | NOT VERIFIED | total_reconnects=0 during this run; no forced network outage test |
| Long-duration continuity / 24x7 reliability | NOT VERIFIED | Five-minute supervised window only |
| Full orderbook sequence continuity and snapshot reconciliation | NOT VERIFIED | Files and sample records exist; no sequence-gap audit supplied |
| T1 process absent after run | PASS | Later pgrep output returned no matching process |
| Disk reserve | PASS at subsequent VPS check | Root filesystem showed 4.5G available; >=2G reserve policy satisfied |

Overall: PASS for the bounded 300-second BTCUSDT supervised runtime, data writing, and graceful shutdown scope only. This is not production certification and does not establish long-duration reliability, outage recovery, or complete orderbook integrity.

## Restrictions and next step
- Do not enable autostart/systemd/linger or leave the Collector running unattended.
- Do not enable proxy/VPN, API keys, Dashboard, additional symbols, or live trading.
- Preserve at least 2 GiB free on the VPS; inspect disk growth before any separately approved longer capture.
- Keep T1 storage separate from T0. No T0 changes were authorized by this runtime test.
- Any longer run or reconnect test requires a separately reviewed bounded scope, disk guard, and explicit user authorization.
- GitHub Actions run/artifact for this runtime increment: NOT RUN / NOT APPLICABLE; source build provenance remains run 42424240328 and artifact 13594961114.

## Post-run CSV and order-book sequence audit — 2026-11-08

### User-provided read-only VPS inspection

- CSV inventory: 13 files; aggregate data rows reported by the prior scanner: 1,497.
- Long/Short Ratio file has three independent `ratio_type` groups: `global`, `top_trader_account`, and `top_trader_position`. Each group contains eight records at 5-minute intervals, from timestamp_ms `1794092100000` through `1794094200000`. The earlier apparent duplicate/backward timestamp warnings were caused by evaluating the concatenated groups as one sequence; timestamps are ordered within each group.
- Initial order-book snapshot: `last_update_id=12045456530176`; all rows in that snapshot share one timestamp and update ID, while bid/ask rows naturally repeat those snapshot-level values.
- The later depth snapshot file showed two distinct timestamp/update-ID values in the inspection sample. Its relationship to the initial snapshot was not further audited here.
- Depth Update CSV: 595 events. No invalid `U > u` ranges. All 594 adjacent event transitions had `pu == previous event's u`.
- Snapshot bridge check: the first event with `u >= snapshot last_update_id` is at zero-based row index 3:
  - `U=12045456519794`
  - `u=12045456653059`
  - `pu=12045456519789`
  - Snapshot ID: `12045456530176`
  - `U <= snapshot_id <= u`: true.
  - The three preceding events have `u < snapshot_id` and are therefore stale relative to the snapshot boundary.
- The first eligible event spans the snapshot update ID. Subsequent recorded events satisfy the previous-`u` / current-`pu` continuity check.

### Updated verdict and evidence boundary

| Check | Status | Evidence boundary |
|---|---|---|
| Long/Short Ratio timestamp ordering | PASS | Three ratio_type groups independently ordered at 5-minute intervals |
| Snapshot-to-first-eligible-event bridge | PASS | CSV update IDs satisfy `U <= snapshot_id <= u` |
| Depth Update U/u range validity | PASS | 0 invalid ranges across 595 events |
| Depth Update pu continuity | PASS | 0 mismatches across 594 adjacent transitions |
| Collector's actual in-memory snapshot application | NOT VERIFIED | CSV IDs establish a valid bridge candidate, not direct observation of the collector's internal book state |
| Full order-book correctness / sequence-gap recovery | NOT VERIFIED | No independent reconstructed-book comparison, checksum, or forced-gap recovery test |
| Later depth snapshot consistency | NOT VERIFIED | Two distinct snapshot-level timestamp/update-ID values were observed but not reconciled against the initial snapshot and update stream |

The earlier blanket statement that full order-book sequence continuity and snapshot reconciliation had no sequence audit is superseded only for the specific CSV-level checks above. The bounded CSV-level bridge and `pu` chain now PASS. This does not certify the collector's in-memory order book or outage recovery.

### Overall scope

The original 300-second supervised runtime remains PASS for bounded ingestion, CSV output, and graceful SIGTERM shutdown. This follow-up adds PASS for Long/Short Ratio per-group timestamp ordering, Depth Update U/u validity, pu continuity, and the initial-snapshot bridge condition. Production readiness, long-duration reliability, reconnect recovery, and reconstructed order-book correctness remain NOT VERIFIED.

- Source SHA remains `d8ac9fc820dcf2e912e66518a1a1c73a8fa81ac7`.
- Source CI run remains `42424240328` (SUCCESS, 5/5); artifact ID `13594961114`.
- No new workflow was run and no artifact was produced for this read-only runtime-data audit.
- No source, runtime configuration, T0 process/database, or VPS service state was changed by this audit.
- Next permitted step: documentation/evidence review only. Any new capture, forced disconnect, or longer runtime requires separate bounded scope and explicit authorization.
