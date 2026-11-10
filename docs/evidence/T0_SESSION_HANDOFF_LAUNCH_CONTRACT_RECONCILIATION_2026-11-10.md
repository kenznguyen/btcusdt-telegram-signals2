# T0 Session Handoff Addendum — Launch Contract Reconciliation — 2026-11-10

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Baseline: `9fb2007738c09743ae8efa72ee74a70de115e911`
- Report: `docs/evidence/T0_DEPLOYMENT_LAUNCH_CONTRACT_RECONCILIATION_2026-11-10.md`

## Result

- Feeder launch target statically mapped: `python -m market_data.feeder_service`.
- Feeder source calls `READY=1` after successful runtime start and `STOPPING=1` before draining; missing `NOTIFY_SOCKET` returns false. Effective systemd notification semantics therefore require host evidence; Type=notify is needed if systemd readiness gating is intended.
- Candle API launch target mapped: Gunicorn `market_data.api:application`, loopback `127.0.0.1:8788`.
- API `/health` is process liveness only; authenticated `/v1/candles` is the data path and requires separately authorized runtime verification.
- README wording now clearly distinguishes same-host loopback T0 → T2 (no Nginx/reverse proxy required) from separately approved remote/browser gateway access.
- DEP-01–DEP-09 mapping completed; all actual host facts remain NOT VERIFIED.
- Documentation-only; no tests, Actions, VPS/SSH, API, token, DB, data or runtime operation.

## Next step

Obtain sanitized owner-supplied DEP-01–DEP-09 evidence and compare. Do not infer host parity from source documentation.

## Restrictions

No VPS/SSH/systemd/Nginx access or probes. No script execution. No service lifecycle action, source/test/workflow/runtime/database/secret/permission/network/data change. No tests or Actions dispatch. Option C — No Destructive Authority — ACTIVE. `AI_EXECUTION_ENABLED=false`; paper-only; no live orders. T0 and L4-Minimum remain BLOCKED / NOT VERIFIED.
