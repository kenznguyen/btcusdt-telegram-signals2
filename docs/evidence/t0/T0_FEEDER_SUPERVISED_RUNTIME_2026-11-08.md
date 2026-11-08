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