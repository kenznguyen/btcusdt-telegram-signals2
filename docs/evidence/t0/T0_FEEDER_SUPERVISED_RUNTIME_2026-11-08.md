# T0 Feeder supervised runtime verification — 2026-11-08

## Scope
Record the user-provided VPS evidence for the previously authorized, one-time supervised T0 Feeder run. Scope remained Binance USD-M perpetual BTCUSDT, M15/H1, SQLite canonical store, public market data only. No T1 runtime, API keys, other symbols/timeframes, exchange orders, or live execution. No systemd/autostart, linger, package installation, or runtime configuration changes.

## Repository context
- Repository: `kenznguyen/btcusdt-telegram-signals2`.
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Branch HEAD before this evidence commit: `ffd767556f1d843bd7e0414493f2a402e9955199`.
- Runtime checkout SHA on VPS during this launch: **NOT RECORDED in supplied terminal evidence**. Earlier recorded checkout SHA `4cf3959532024d286a76712bd93708b7a96489df` is historical and is not asserted as the exact runtime SHA for this run.
- No GitHub Actions workflow was run for this VPS runtime evidence; workflow run and artifact: NOT APPLICABLE.

## Launch and recovery evidence
- First tmux launch attempt exited immediately because `MARKET_DATA_DB` was unset; log showed `StoreConfigurationError: MARKET_DATA_DB is required for SQLite`. No Feeder remained running after that attempt.
- Corrected launch explicitly exported:
  - `MARKET_DATA_BACKEND=sqlite`
  - `MARKET_DATA_DB=/home/ubuntu/t0/app/.data/market-data.sqlite3`
- Successful launch log path: `/home/ubuntu/t0/app/.logs/feeder-20261108T035059Z.log`.
- Log start marker: `START_UTC=2026-11-08T03:50:59Z`; source directory `/home/ubuntu/t0/app`.
- Feeder PID: `5919`; verified command line from `/proc/5919/cmdline`: `/home/ubuntu/t0/venv/bin/python -m market_data.feeder_service`.
- tmux session `t0-feeder` remained active.
- After exiting SSH and reconnecting, the same PID and tmux session remained active; lease remained valid.
- The canonical SQLite file existed with mode `0600`, owner `ubuntu:ubuntu`, size 622,592 bytes at the final inspection.
- SQLite `PRAGMA integrity_check`: `ok`.

## Lease and data evidence (user-provided)
- Previous lease generation 1 was expired before corrected launch.
- New lease owner: `O6EF0eUn7tZDFFqeE-NCLLU61G4Iv6OmvnMlUefoZ0k`.
- Lease generation: `2`.
- Lease expiry was observed advancing between snapshots approximately 30 seconds over 35 seconds of wall time; final observed expiry `1794110644221` ms, not expired at inspection.
- Candle counts and latest persisted candles:
  - At 03:51 UTC: M15 2,027; H1 2,006.
  - At 04:00 UTC: M15 2,028; latest open 03:45 UTC; available 04:00:08 UTC. H1 2,007; latest open 03:00 UTC; available 04:00:09 UTC.
- This confirms one newly persisted M15 candle and one newly persisted H1 candle across the 04:00 UTC close cycle.
- Earlier M15/H1 snapshots before the close showed stable counts, as expected before the next close.
- Feeder log remained limited to the two start markers; per-cycle sync/recovery details were not emitted to that log.

## Assessment and status
| Check | Status | Evidence boundary |
|---|---|---|
| Corrected Feeder launch | PASS | User terminal: PID 5919, tmux session, start log |
| Process identity | PASS | `/proc/5919/cmdline` exact command |
| SSH disconnect/reconnect survival | PASS | Same PID/session and valid lease after reconnect |
| Lease acquisition/takeover | PASS | Owner changed, generation 1 → 2 |
| Lease heartbeat | PASS | Expiry advanced across repeated snapshots |
| SQLite integrity | PASS | `integrity_check: ok` |
| M15/H1 persisted updates | PASS | Both counts incremented by one; latest closed candles and availability timestamps supplied |
| Startup/recovery log trace | NOT VERIFIED | Log contains only START_UTC and SOURCE_DIR |
| Exact runtime source SHA | NOT VERIFIED | No `git rev-parse HEAD` captured during this run |
| Long-duration / 24x7 reliability | NOT VERIFIED | Short supervised observation only |
| Reboot/autostart recovery | NOT RUN / NOT AUTHORIZED | No systemd, linger, or autostart changes |
| Controlled shutdown and lease release | NOT RUN | Feeder intentionally left running |
| GitHub Actions tests/artifact | NOT RUN / NOT APPLICABLE | This was VPS runtime observation, not CI |

## Overall verdict
**PASS for this supervised runtime verification scope only:** corrected launch, process identity, SSH reconnect survival, lease generation/heartbeat, SQLite integrity, and one M15/H1 close cycle were demonstrated by user-provided terminal evidence.

This is not production certification, not 24x7 reliability evidence, and not reboot/autostart validation. The absence of per-cycle log records and exact runtime source SHA remains an evidence limitation.

## Next step and restrictions
1. Preserve the running Feeder; do not start a duplicate process.
2. If a controlled stop/recovery test is desired, obtain separate explicit authorization before stopping the process. Review the graceful stop method, expected lease release, and restart/recovery procedure first.
3. Do not enable systemd/autostart/linger, install packages, change runtime configuration, activate T1, connect authenticated exchange endpoints, add symbols/timeframes, or enable trading without separate authorization.
4. Record a fresh `git rev-parse HEAD` only if source provenance is needed; do not assume the historical checkout SHA is the runtime SHA.
5. No GitHub Actions run or artifact was produced in this increment.

## Addendum — T0 runtime recheck (2026-11-08, user-provided VPS output)

### Scope and observations
- Rechecked the already-running T0 Feeder without restarting or modifying it.
- git rev-parse HEAD from /home/ubuntu/t0/app returned 4cf3959532024d286a76712bd93708b7a96489df.
- git status --short showed only untracked runtime directories: .logs/ and .runtime/; no tracked-file modifications were reported.
- Feeder process was present: tmux wrapper PID 6583 and Python PID 6584, command /home/ubuntu/t0/venv/bin/python -m market_data.feeder_service.
- Environment shown in the tmux command: MARKET_DATA_BACKEND=sqlite; MARKET_DATA_DB=/home/ubuntu/t0/app/.data/market-data.sqlite3.
- Active log path: /home/ubuntu/t0/app/.logs/feeder-restart-20261108T043225Z.log; visible content contained START_UTC=2026-11-08T04:32:25Z.
- Read-only SQLite check through the project's Python virtualenv returned PRAGMA integrity_check=ok and PRAGMA journal_mode=wal.
- Root filesystem at inspection: 7.9G total, 3.4G used, 4.5G available (43%).

### Verdict and evidence boundary
| Check | Status | Evidence boundary |
|---|---|---|
| Feeder process present at recheck | PASS | User-provided pgrep output, PID 6584 |
| Runtime checkout HEAD observed | PASS | User-provided git rev-parse HEAD while process was present |
| Tracked working tree clean | PASS | git status showed only untracked .logs/ and .runtime/ |
| SQLite integrity | PASS | Read-only Python SQLite integrity_check=ok |
| SQLite WAL mode | PASS | Read-only Python SQLite pragma |
| Disk reserve >=2G | PASS | 4.5G available |
| Exact process-to-source binary provenance | NOT VERIFIED | Checkout SHA observed while process was present; no executable/module hash or process launch trace binds loaded code byte-for-byte |
| Current feeder lease/heartbeat and candle progress | NOT VERIFIED in this recheck | Not included in this output |
| Long-duration reliability / reboot recovery | NOT VERIFIED | No such test performed |

The observed checkout SHA is 4cf3959532024d286a76712bd93708b7a96489df. This is stronger than the earlier historical-only reference because it was captured while the feeder process was present, but it is not a cryptographic measurement of the running Python process's loaded code.

### Restrictions and next step
- No restart, stop, config change, package installation, or database write was performed.
- Keep .logs/ and .runtime/ out of source commits; they are runtime state.
- Preserve the running Feeder. Do not stop it, configure autostart, or start another instance without separate authorization.
- GitHub Actions run/artifact: NOT RUN / NOT APPLICABLE for this VPS-only observation.

## Addendum — Controlled graceful stop, lease release, restart, and post-restart recovery (2026-11-08)

### Scope and source identity
- User explicitly authorized a controlled graceful stop of the supervised T0 Feeder PID 5919, followed by restart and recovery observation.
- Scope remained Binance USD-M perpetual BTCUSDT, M15/H1, SQLite canonical store, public market data only. No T1 runtime, API keys, other symbols/timeframes, exchange orders, or live execution.
- VPS checkout SHA observed while the restarted process was present: `4cf3959532024d286a76712bd93708b7a96489df`. This identifies the checked-out repository state at inspection; it is not a cryptographic measurement of code already loaded into the Python process.
- Restarted process command: `/home/ubuntu/t0/venv/bin/python -m market_data.feeder_service`; Python PID `6584`; tmux wrapper PID `6583`; tmux session `t0-feeder`.
- Restart log: `/home/ubuntu/t0/app/.logs/feeder-restart-20261108T043225Z.log`. It contains the start marker `START_UTC=2026-11-08T04:32:25Z`; no detailed recovery/cycle trace was emitted in the inspected log.
- Runtime configuration remained `MARKET_DATA_BACKEND=sqlite` and `MARKET_DATA_DB=/home/ubuntu/t0/app/.data/market-data.sqlite3`.

### Controlled shutdown evidence
- Before stop: PID 5919 command line matched the Feeder module; tmux session `t0-feeder` existed; SQLite integrity was `ok`.
- Pre-stop candles: M15 2,029; H1 2,007.
- Pre-stop lease: name `binance-btcusdt-canonical`, owner `O6EF0eUn7tZDFFqeE-NCLLU61G4Iv6OmvnMlUefoZ0k`, generation 2.
- Sent Ctrl-C through tmux. PID 5919 exited within the 35-second wait; no force-kill was used. tmux session ended.
- Post-stop lease row remained but was explicitly released: owner `NULL`, generation 2, `expires_at_ms=0`.
- Post-stop SQLite integrity remained `ok`; candle counts and latest timestamps were unchanged from pre-stop (M15 2,029; H1 2,007).
- The previously referenced first-run log path was not present when inspected during shutdown; shutdown log detail is therefore NOT VERIFIED.

### Restart and recovery observations (user-provided VPS output)
- Restarted at `2026-11-08T04:32:25Z` under tmux using the same SQLite environment; no duplicate process was present at the pre-restart guard.
- New lease owner: `Qll8BuEUDWB2gmqVAQFkugHYkvTTRvUGRjHPuWMguUU`; generation increased from 2 to 3.
- Initial post-restart snapshot: M15 2,030; H1 2,007; SQLite integrity `ok`.
- Lease heartbeat observed across a 35-second interval: expiry advanced from `1794112468822` to `1794112498872` ms (30.05 seconds); process PID 6584 remained present.
- At 04:46:28 UTC, M15 count increased to 2,031; latest M15 open time `1794112200000` ms (04:30 UTC), available at `1794113109339` ms (04:45:09 UTC). H1 remained 2,007, as its next close was 05:00 UTC.
- At 07:44:31 UTC, SQLite integrity remained `ok`; M15 count was 2,042 and H1 count was 2,010. Latest M15 open time `1794122100000` ms (07:15 UTC), available at `1794123008140` ms (07:30:08 UTC). Latest H1 open time `1794117600000` ms (06:00 UTC), available at `1794121206939` ms (07:00:06 UTC).
- At 07:44:31 UTC, the lease remained owned by the restarted process identity, generation 3, expiry `1794123928559` ms; PID 6584 and tmux wrapper PID 6583 were present.
- From the first post-restart snapshot to 07:44:31 UTC, candle counts increased by 12 M15 and 3 H1. The latest persisted candle timestamps are consistent with the next M15 close at 07:45 UTC and next H1 close at 08:00 UTC; the exact 07:45/08:00 close cycles were not yet observed in the supplied output.

### Verdict and evidence boundary
| Check | Status | Evidence boundary |
|---|---|---|
| Graceful Ctrl-C shutdown | PASS | PID 5919 exited; no force-kill |
| Lease release | PASS | owner NULL and expiry 0 after stop |
| SQLite integrity across stop | PASS | `integrity_check=ok` before/after |
| Candle preservation across stop | PASS | counts and latest timestamps unchanged |
| Restart under tmux | PASS | PID 6584, tmux session, start marker |
| Lease generation takeover | PASS | generation 2 → 3, new owner |
| Lease heartbeat after restart | PASS | expiry advanced 30.05 seconds across snapshots |
| Post-restart M15 persistence | PASS | count increased; new closed M15 timestamps observed |
| Post-restart H1 persistence | PASS | count increased by 3; later closed H1 timestamp observed |
| Sustained supervised runtime after restart | PASS — bounded observation | process/lease alive and M15/H1 data advanced through 07:44:31 UTC, approximately 3h12m after restart |
| Detailed recovery/startup log trace | NOT VERIFIED | restart log contained only START_UTC in inspected tail |
| Exact loaded-code provenance | NOT VERIFIED | checkout SHA captured while process ran; no loaded-module hash/process-to-source attestation |
| 24x7/production reliability | NOT VERIFIED | bounded supervised VPS observation only |
| Reboot/autostart recovery | NOT RUN / NOT AUTHORIZED | no systemd, linger, or autostart changes |
| GitHub Actions workflow/artifact | NOT RUN / NOT APPLICABLE | VPS operational test only; no source or workflow change |

**Overall verdict: PASS for the bounded graceful-stop, lease-release, restart, heartbeat, SQLite integrity, and post-restart M15/H1 persistence scope.** This is not production certification, not 24x7 reliability evidence, and not reboot/autostart validation. The exact loaded-code provenance and detailed startup/recovery trace remain NOT VERIFIED.

### Next step and restrictions
1. Keep the restarted Feeder running; do not start a duplicate.
2. Continue only with read-only health/quality observation or a separately authorized test.
3. Do not enable systemd/autostart/linger, alter runtime configuration, install packages, activate T1, connect authenticated exchange endpoints, add symbols/timeframes, or enable trading without separate authorization.
4. No GitHub Actions run or artifact was produced for this VPS-only increment.


## Addendum — Post-restart M15/H1 close-cycle confirmation (2026-11-08)

### Latest user-provided VPS observation
- Observation time: `2026-11-08 08:26:41 UTC`.
- Runtime checkout SHA observed on VPS: `4cf3959532024d286a76712bd93708b7a96489df`.
- Feeder Python PID `6584` and tmux wrapper PID `6583` remained present; tmux session `t0-feeder` remained active.
- SQLite `PRAGMA integrity_check` returned `ok`.
- M15: 2,045 rows; latest `open_time_ms=1794124800000` (08:00 UTC), `available_at_ms=1794125705547` (08:15:05 UTC).
- H1: 2,011 rows; latest `open_time_ms=1794121200000` (07:00 UTC), `available_at_ms=1794124809915` (08:00:09 UTC).
- Lease: `binance-btcusdt-canonical`, same restarted owner, generation 3, expiry `1794126451739` ms (08:27:31 UTC). Lease was valid at observation.
- Compared with the 07:47:50 UTC snapshot, M15 count increased from 2,043 to 2,045 and H1 from 2,010 to 2,011. The latest timestamps demonstrate persistence of the 08:00 UTC M15 candle and 07:00 UTC H1 candle after their close/availability windows.

### Updated verdict
- Graceful shutdown and explicit lease release: **PASS**.
- Restart and generation takeover (2 → 3): **PASS**.
- Heartbeat after restart: **PASS**.
- SQLite integrity: **PASS**.
- Post-restart M15/H1 persistence through the 08:00 UTC close cycle: **PASS**.
- Bounded supervised operation after restart: **PASS**, observations span from 04:32:25 to 08:26:41 UTC (approximately 3h54m); this is not 24x7 or production certification.
- Detailed startup/recovery log trace: **NOT VERIFIED**; inspected log contains only the start marker.
- Exact loaded-code provenance: **NOT VERIFIED**; checkout SHA was observed while the process ran, but no cryptographic process-to-loaded-code attestation was collected.
- Reboot/autostart: **NOT RUN / NOT AUTHORIZED**.
- GitHub Actions workflow/artifact: **NOT RUN / NOT APPLICABLE**; this was a user-operated VPS runtime observation with no source-code change.

### Next step and restrictions
- Keep the existing Feeder running; do not start a duplicate.
- Next useful bounded check is read-only T0 data-quality/continuity/age monitoring, with explicit stale-data and gap thresholds reviewed before any readiness promotion.
- Do not enable systemd/autostart/linger, change runtime configuration, install packages, activate T1, connect authenticated exchange endpoints, expand symbols/timeframes, or enable live execution without separate authorization.
