# T0 Session Handoff Addendum — Owner Evidence Collection Protocol — 2026-11-10

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Active branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact source baseline: `94e42f2725e02ee6e98a7eaef26a30caec75f4ee`
- Report: `docs/evidence/T0_OWNER_READONLY_DEPLOYMENT_EVIDENCE_PROTOCOL_2026-11-10.md`

## Result

- Defined a bounded owner-supplied / separately authorized read-only evidence protocol for deployment parity.
- Protocol covers candidate systemd units, effective unit properties, process executable/cwd identity, port 8788 listener metadata, deployed Git SHA, Flask health-app presence/provider registration, and Nginx relevance.
- Commands do not print process command lines or environment values and explicitly prohibit reading secret files.
- The protocol does not authorize ChatGPT/agent SSH or VPS access, HTTP probes, service actions, DB/data reads, tests, or Actions dispatch.
- Nginx is NOT REQUIRED for the documented same-host T0 → T2 loopback path.
- No host inspection, runtime probe, source change, test, workflow dispatch, or data operation was performed.

## Next step

Obtain sanitized DEP-01–DEP-09 evidence from the owner, or secure separate explicit authorization for a strictly read-only host inspection. Compare evidence against the repository launch contracts; do not deploy or modify services.

## Restrictions

No VPS/SSH/systemd/Nginx access or probes under this documentary scope. No service lifecycle action, source/test/workflow/runtime/database/secret/permission/network/data change. No tests or Actions dispatch. Option C — No Destructive Authority — ACTIVE. `AI_EXECUTION_ENABLED=false`; paper-only; no live orders. T0 and L4-Minimum remain BLOCKED / NOT VERIFIED.
