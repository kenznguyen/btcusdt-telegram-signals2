# T0 Session Handoff Addendum — Read-Only Preflight Static Audit — 2026-11-10

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact inspected baseline: `523fc541f0fba189904e8ce5adf3083b15b16778`
- Script: `ops/ssh/t0-readonly-preflight.sh`
- Script blob SHA: `39de5aa7602cdf7dc301ff6bc65a68fad417ea84`
- Report: `docs/evidence/T0_READONLY_PREFLIGHT_STATIC_SAFETY_AUDIT_2026-11-10.md`

## Result

- Static inspection only; script NOT RUN.
- Script contains no explicit service lifecycle or data mutation command.
- It reads all visible process command lines to identify Feeder PIDs; this is outside the metadata-only DEP-01–DEP-09 protocol and may read secret-bearing arguments.
- It runs SQLite `PRAGMA integrity_check` on the canonical DB through a read-only/query-only connection. This is not metadata-only and can consume I/O/CPU proportional to database size.
- Script output cannot establish systemd effective properties, API process identity, Flask provider wiring, listener owner or full deployment parity.
- Root-owned/authorized_keys forced-command security is only a comment-level assumption; effective SSH restriction is NOT VERIFIED.
- README proxy wording is ambiguous: loopback-only same-host T0 → T2 does not require Nginx, while the generic deployment sentence suggests an HTTPS reverse proxy without scoping it to remote exposure.
- No VPS/SSH access, script execution, tests, Actions dispatch, source/runtime/database/data changes.

## Decision

Do not execute the existing script as a replacement for DEP-01–DEP-09. Keep it unchanged. Any future hardened preflight requires a separate design and approval. No source edit or script replacement is authorized.

## Next step

Documentary reconciliation of launch contracts against DEP fields and clarification of the README proxy condition. Actual deployment parity remains NOT VERIFIED.

## Restrictions

No VPS/SSH/systemd/Nginx access or probes. No script execution. No service lifecycle action, source/test/workflow/runtime/database/secret/permission/network/data change. No tests or Actions dispatch. Option C — No Destructive Authority — ACTIVE. `AI_EXECUTION_ENABLED=false`; paper-only; no live orders. T0 and L4-Minimum remain BLOCKED / NOT VERIFIED.
