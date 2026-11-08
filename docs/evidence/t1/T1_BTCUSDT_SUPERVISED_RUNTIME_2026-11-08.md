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
13 CSV files were present, all with a header and at least one data row:

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
| index price klines | 7 | 6 |
| premium index klines | 7 | 6 |
| orderbook snapshot | present | header and data shown in output |
| initial orderbook snapshot | present | header and data shown in output |

Note: line counts and sample headers/records were supplied by the user. The orderbook snapshot files were shown to exist and contain data, but complete row counts for both snapshots were not separately captured in the summarized terminal output.

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