# T0 Feeder SSH-session termination diagnosis — 2026-11-08

## Scope
Read-only diagnosis of the previously authorized T0 Feeder runtime on VPS `btcquant-t0-t1-test-01`. No process was started or stopped in this increment. No SQLite data or lease was modified. No systemd/autostart configuration was changed.

## Source and host context
- Repository: `kenznguyen/btcusdt-telegram-signals2`.
- Existing branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Branch HEAD before this evidence commit: `fcb4309d02c084ae72aa0ded19637ed9cff00be1`.
- VPS: Ubuntu 26.04.1, host `btcquant-t0-t1-test-01`.
- Runtime source checkout previously recorded: `4cf3959532024d286a76712bd93708b7a96489df`.
- Feeder process previously observed as PID 3465, command `/home/ubuntu/t0/venv/bin/python -m market_data.feeder_service`.

## User-provided evidence
### Feeder and database
- At the later baseline check, `pgrep -af '[m]arket_data.feeder_service'` returned no process.
- SQLite candle rows remained readable:
  - M15: 2,010 rows; latest open `2026-11-07T23:15:00Z`; latest available `2026-11-07T23:30:08.400Z`.
  - H1: 2,002 rows; latest open `2026-11-07T22:00:00Z`; latest available `2026-11-07T23:00:07.135Z`.
- Lease `binance-btcusdt-canonical`, generation 1, expired at `2026-11-07T23:36:17.962Z`; inspected at `2026-11-08T03:45:17.109987Z`.
- SQLite `PRAGMA integrity_check`: `ok`.
- No dedicated Feeder log files were found by the supplied find command.

### System journal
- At `2026-11-07 23:35:23 UTC`, sshd recorded a read timeout from remote host `113.182.78.105`.
- At the same timestamp, PAM recorded the Ubuntu SSH session closing; systemd-logind recorded session 11 logging out and “Waiting for processes to exit.”
- `session-11.scope` then reported `Deactivated successfully`.
- The scope reported 1min 41.017s CPU time over 2h 35min 12.639s wall time and 583.5 MB memory peak.
- No OOM, out-of-memory, killed-process, or segfault event was returned by the kernel journal filter for the requested interval.
- The system journal contains unrelated external SSH pre-authentication probes; the supplied excerpt does not show successful authentication by those sources.

### Host resources at inspection
- RAM: 7.7 GiB total, 7.3 GiB available; swap 0.
- Root filesystem: 7.9 GB total, 3.4 GB used, 4.5 GB available (43%).

## Assessment
- **Most likely cause:** Feeder was launched in the interactive SSH session and exited when that session closed. The session timeout, logind logout, and session-scope deactivation coincide with the last known runtime window.
- **Confidence boundary:** the supplied journal excerpt does not directly map PID 3465 to `session-11.scope` at termination. Therefore the SSH-session explanation is strongly indicated but not conclusively proven.
- OOM is not supported by the supplied kernel journal output; available RAM and disk were healthy at the later inspection.
- The expired lease is consistent with the Feeder no longer heartbeating; it is not evidence of SQLite corruption.
- Database integrity remains PASS based on the user-provided `integrity: ok`.

## Status
| Item | Status |
|---|---|
| Feeder process currently running at inspection | BLOCKED / absent |
| SQLite integrity | PASS |
| Lease heartbeat after SSH session closure | BLOCKED / expired |
| SSH-session termination as root cause | LIKELY; exact PID-to-scope mapping NOT VERIFIED |
| OOM as root cause | NOT INDICATED by supplied kernel journal |
| RAM/disk capacity at inspection | PASS |
| Additional M15/H1 cycles | NOT VERIFIED |
| Controlled restart/recovery | NOT RUN; awaiting explicit authorization |
| systemd/autostart | NOT AUTHORIZED |
| T1 runtime / real orders | OUT OF SCOPE |

## Next step and limits
1. Do not restart or kill any process, clear the lease, alter SQLite, install packages, or change systemd/autostart without separate approval.
2. If restart is authorized later, first choose and review a session-independent but supervised run method, explicit log destination, PID ownership, stop procedure, and restart/recovery checks. Do not assume `nohup` alone proves survival across logind session teardown.
3. After any approved start, verify process identity, lease owner/generation/heartbeat, SQLite integrity, and at least one newly persisted M15 and H1 candle before calling runtime recovery PASS.
4. No GitHub Actions run or artifact was produced by this VPS diagnostic. This document records user-provided terminal evidence only.
