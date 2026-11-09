# T0 Feeder Runtime Verification — 2026-11-09

## Status

**PARTIAL PASS** — runtime process, lease heartbeat, post-restart ingestion, and two bounded canonical coverage windows are verified. Scheduler window completion and full recovery-history coverage remain **NOT VERIFIED**.

This report records evidence only. It does not change runtime configuration, canonical data, schema, retention, or trading behavior.

## Scope and constraints

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Source commit under verification: `9ae2eeae4ece3d657781b68e96b6f4509cd95f24`
- VPS: `btcquant-t0-t1-test-01` (test environment; not production)
- Canonical SQLite: `/home/ubuntu/t0/app/.data/market-data.sqlite3`
- Feeder process: `22046`; tmux session: `t0-feeder`
- No source changes, database writes, schema changes, feeder restart during verification, retention changes, or trading actions were performed for this report.

## Source and CI evidence

The source change verifies canonical coverage after sync and advances a timeframe window only when `RecoveryPlanner` reports no remaining gaps. Coverage-reader exceptions or gaps fail the window; zero inserted rows are acceptable only when canonical coverage is complete.

The source commit was previously verified on the VPS and matched the remote branch SHA:
`9ae2eeae4ece3d657781b68e96b6f4509cd95f24`.

GitHub Actions runs associated with that source revision were reported successful:

| Workflow | Run ID | Result |
|---|---:|---|
| T0 Single Writer Gateway Contracts | 42508364088 | success |
| T2 Freqtrade 2026.9 Strategy Load Smoke | 42508364089 | success |
| T0 Feeder API systemd Integration | 42508364090 | success |
| T0 SQLite Read-only systemd Sandbox | 42508364114 | success |

Previously recorded artifacts:

| Evidence | Artifact ID |
|---|---:|
| Gateway contract evidence | 13627939321 |
| Provider bootstrap evidence | 13628178055 |
| TimescaleDB read-only evidence | 13628691436 |
| T0 Feeder API systemd integration | 13628521899 |
| T0 SQLite read-only sandbox | 13627924430 |
| T2 Freqtrade smoke | 13628397213 |

These are historical CI results for the source SHA, not a new workflow execution caused by this report.

## VPS runtime evidence

### Restart and process

- Feeder restarted on 2026-11-08 at `18:11:58 UTC`.
- New feeder PID: `22046`.
- Command: `/home/ubuntu/t0/venv/bin/python -m market_data.feeder_service`.
- Process was observed alive in tmux session `t0-feeder`; pane reported `dead=0`, command `python`.
- Log `.logs/feeder-restart-20261109.log` contained the startup marker and no traceback/error text in the inspected content.

**Assessment:** process survival and tmux pane status PASS. The log is sparse (startup marker only), so absence of logged errors is not proof that every scheduler operation succeeded.

### Post-restart candle ingestion

Read-only SQLite queries observed these exact canonical rows after the restart:

| Timeframe | Open time (UTC) | Available time (UTC) |
|---|---|---|
| 15m | 2026-11-08 18:15 | 2026-11-08 18:30:06.266 |
| 1h | 2026-11-08 18:00 | 2026-11-08 19:00:08.516 |

Later snapshots showed M15 advancing to open time 2026-11-09 01:35 UTC, available at 01:50:07.963 UTC. At the 02:36 UTC observation, the latest H1 candle was open time 01:00 UTC, available at 02:00:06.835 UTC; the 02:00 UTC H1 candle was still forming at that observation time.

**Assessment:** post-restart M15/H1 ingestion is verified. Later M15 progression is verified. The H1 observation is consistent with its candle interval; it does not independently prove the next H1 ingestion.

### Lease and heartbeat

Read-only lease observations:

| UTC observation | Generation | Owner present | Expiry (ms) | Remaining |
|---|---:|---|---:|---:|
| 2026-11-09 02:26:57.953 | 5 | yes | 1794191267696 | 49.74 s |
| 2026-11-09 02:27:41.496 | 5 | yes | 1794191312716 | 51.22 s |
| 2026-11-09 02:28:01.503 | 5 | yes | 1794191327723 | 46.22 s |
| 2026-11-09 02:36:14.366 | 5 | yes | 1794191822971 | 48.60 s |

Between 02:27:41.496 and 02:28:01.503 UTC, expiry advanced by 15,007 ms over 20,007 ms. Between 02:28:01.503 and 02:36:14.366 UTC, expiry advanced by 495,248 ms.

**Assessment:** lease owner remained present, generation remained 5, and expiry advanced across observations. Heartbeat renewal is PASS for the observed interval; this is not a guarantee about future availability.

## Canonical coverage verification

Coverage was checked on 2026-11-09 at 02:40:08.655 UTC using the source's `market_data.store.read_window()` function (SQLite `mode=ro`) and `RecoveryPlanner.plan()`. No sync or recovery callback was invoked.

| Timeframe | Half-open window (UTC) | Expected | Returned | Complete | Planner gaps |
|---|---|---:|---:|---|---:|
| 15m | 2026-11-09 01:45–02:30 | 3 | 3 | true | 0 |
| 1h | 2026-11-08 23:00–2026-11-09 02:00 | 3 | 3 | true | 0 |

Dataset fingerprints:

- M15: `sha256:7297654ff9b7a8bbd341f16faa502719b17561497178788abaf7fed28696baf4`
- H1: `sha256:43922096e8f0b4f91c3addb89f73ba586642e0c9864f289a7f46e78af0db541d`

**Assessment:** PASS for these two bounded windows only. This does not establish complete coverage over the full recovery lookback or all historical windows.

## Consolidated status

| Check | Status | Evidence boundary |
|---|---|---|
| Source SHA parity on VPS | PASS | Exact SHA observed |
| Existing CI workflows | PASS | Four successful runs listed above |
| Feeder restart/process survival | PASS | PID and tmux observations |
| Post-restart M15/H1 ingestion | PASS | Exact canonical rows |
| M15 progression | PASS | Later open time observed |
| Lease ownership and heartbeat | PASS | Generation 5; expiry advanced |
| M15 bounded coverage | PASS | 3/3, no planner gaps |
| H1 bounded coverage | PASS | 3/3, no planner gaps |
| Scheduler completed-window state | NOT VERIFIED | In-memory state was not inspected; sparse log |
| Full recovery-history coverage | NOT VERIFIED | Only two bounded windows checked |
| Complete fault/negative-vector inventory | NOT VERIFIED | Separate inventory remains outstanding |

## Next step and explicit limits

Next work should remain an evidence/inventory exercise: inspect scheduler observability and enumerate fault/negative vectors with existing test coverage versus missing tests. Do not infer scheduler completion from candle presence alone.

Not authorized by this report:
- source or runtime modifications;
- database/schema/data changes;
- retention, deletion, or archive policy changes;
- feeder restart or VPS service changes;
- live trading or real orders;
- dispatching workflows with Git write side effects beyond this evidence-file commit.

No new CI workflow was dispatched for this documentation-only commit.
