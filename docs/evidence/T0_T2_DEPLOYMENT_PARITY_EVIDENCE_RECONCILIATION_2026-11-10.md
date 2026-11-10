# T0 → T2 Deployment Parity Evidence Reconciliation — 2026-11-10

## Correction to the 2026-11-10 checklist intake status

The repository already contains operator-provided runtime evidence dated 2026-11-09. The newly added deployment-parity checklist should not be read as if no historical runtime evidence exists. This reconciliation corrects that omission while preserving the time and provenance boundary.

## Evidence sources and exact Git blobs

- `docs/evidence/t2/T0_T2_LOOPBACK_DEPLOYMENT_GATE_2026-11-09.md` — blob `4919abb30afc5f6fd7a98e013633d1e19d112325`.
- `docs/evidence/t2/T0_T2_LOOPBACK_RUNTIME_VERIFICATION_2026-11-09.md` — blob `568b7d2c5ba6f606221519aba7ee4b298dff34c8`.
- `docs/evidence/T0_FEEDER_RUNTIME_VERIFICATION_20261109.md` — blob `ef632a53490e85d709026651c0af9a22d28883fb`.
- Runtime verification is explicitly based on operator-provided VPS command output, not a new probe in this review. Process-loaded byte identity was not independently attested.

## Reconciled gate status

| Gate | Historical evidence (2026-11-09) | Current status on 2026-11-10 |
|---|---|---|
| G1 source parity | T0 source SHA `9ae2eeae4ece3d657781b68e96b6f4509cd95f24`; T2 context file SHA-256 recorded; six T0 API/feeder/storage blobs matched at the historical branch HEAD | HISTORICAL PASS; current deployed checkout/process SHA NOT VERIFIED |
| G2 endpoint parity | `t0-candle-api.service` active, Gunicorn bound only to `127.0.0.1:8788`; no public listener observed | HISTORICAL PASS; current listener/service state NOT VERIFIED |
| G3 secret/config parity | Authenticated M15/H1 reads succeeded; unauthenticated request returned 401; configured max ingestion lag 120,000 ms; token value not recorded | HISTORICAL PASS for that observation; current environment/token state NOT VERIFIED |
| G4 storage ownership | API service DB path was configured read-only; no DB/WAL mutation reported | HISTORICAL PASS as operator-reported configuration; deployed storage-level enforcement not independently attested |
| G5 contract parity | Authenticated M15/H1 reads returned 2/2 complete, no gaps, closed VALIDATED candles; latest M15 ingestion lag 8,558 ms | HISTORICAL PASS for bounded sample; current response/data freshness NOT VERIFIED |
| G6 runtime observation | One-shot T2 context read succeeded for 2 M15 bars; JSON artifact parsed successfully | HISTORICAL PASS for bounded read; no new observation authorized/performed |

## Historical runtime result

- T0 API health: HTTP 200.
- Missing Bearer token: HTTP 401.
- Authenticated M15 and H1 API reads: HTTP 200.
- M15/H1: 2 candles each, complete coverage, no gaps, latest candle closed and quality `VALIDATED`.
- Latest M15 ingestion lag: 8,558 ms; configured maximum: 120,000 ms.
- T2 one-shot command: `python -m freqai_bridge.context --bars 2 --output /tmp/t2-canonical-window-20261109T112946Z.json`; exit code 0; two M15 bars; complete coverage; JSON parse PASS.
- Local artifact path was `/tmp/t2-canonical-window-20261109T112946Z.json`; it was not uploaded to GitHub Actions and is not independently retrievable from this repository.
- Runtime API service boot autostart was disabled. T1 remained NOT ACTIVATED. No Feeder restart, DB/WAL mutation, strategy/model training, signal publication, ledger/risk change, or live order occurred in that gate.

## Important limits

- These are historical observations on 2026-11-09, not proof of state on 2026-11-10 or later.
- T0 source SHA was recorded as `9ae2eeae4ece3d657781b68e96b6f4509cd95f24`; the runtime report states it matched the remote branch at that time. The current branch has since advanced. Do not infer the VPS checkout was updated to the current branch HEAD.
- T2 context file SHA-256 was recorded as `e22d6c7d186b1fb9a5079eb9b4224c8acbcd835a0938dc970e9bc4b072eb75d3`; process-loaded bytes were not independently attested.
- The two-candle T2 one-shot confirms a bounded canonical-context read, not continuous Freqtrade runtime activation, scheduled ingestion, production reliability, or a latency SLA.
- No current runtime check, new API request, SSH/VPS/DB/network probe, test, compile, workflow dispatch or artifact upload was performed for this reconciliation.

## Corrected disposition

**T0 → T2 LOOPBACK GATE: HISTORICAL PASS FOR THE BOUNDED 2026-11-09 TEST.**

**CURRENT DEPLOYMENT PARITY: PARTIAL / NOT VERIFIED.**

The next step is not to repeat already-completed historical checks as if they never happened. First compare the recorded 2026-11-09 evidence to owner-supplied current sanitized service/config/source evidence. Only if material drift or freshness is unknown and a new observation is needed should a separate bounded read-only runtime check be proposed for explicit approval.

## Safety

- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- T1 activation remains separate and NOT AUTHORIZED by this reconciliation.
- No deletion, cleanup, retention execution, vacuum, compaction or archive operation is authorized.
- T0 canonical SQLite, CORE_LEDGER, AI_LEDGER, audit/reconstruction and recovery evidence remain protected.
- Option C remains REVOKED; revocation does not itself authorize destructive operations.
- PostgreSQL/TimescaleDB remains PARKED.