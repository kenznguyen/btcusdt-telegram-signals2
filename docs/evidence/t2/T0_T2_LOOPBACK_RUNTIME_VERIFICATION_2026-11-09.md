# T0 → T2 Loopback Runtime Verification — 2026-11-09

## Scope and authorization

Owner-approved gate: deploy T0 Candle API on the same VPS, loopback-only at `127.0.0.1:8788`, then verify authenticated M15/H1 reads and perform one bounded T2 canonical-context read.

Included: read-only API verification, two-candle M15/H1 reads, T2 HTTP client validation and one-shot context artifact generation.

Excluded: T1 activation, Feeder restart, SQLite/WAL mutation, strategy/model training, prediction/signal publication, live orders, OKX replacement, data deletion, and changes to ledgers or Shared Risk Engine.

## Source identity

- T0 VPS checkout source SHA reported before deployment: `9ae2eeae4ece3d657781b68e96b6f4509cd95f24`.
- T2 `freqai_bridge/context.py` SHA-256 observed on VPS: `e22d6c7d186b1fb9a5079eb9b4224c8acbcd835a0938dc970e9bc4b072eb75d3`.
- Runtime source identity is recorded from operator-provided VPS output; process-loaded byte identity was not independently attested.
- API service: `t0-candle-api.service`; Gunicorn bound only to `127.0.0.1:8788`; service active and disabled for boot autostart.
- API process ran as `ubuntu`; DB path was configured read-only for the service. No public listener was observed.

## Verification evidence

### API deployment and security

- systemd unit verification: PASS.
- Service start and active state: PASS.
- Listener binding: `127.0.0.1:8788` only — PASS.
- `GET /health`: HTTP 200 — PASS.
- `GET /v1/candles` without Bearer token: HTTP 401 — PASS.
- Authenticated API reads: HTTP 200 for M15 and H1 — PASS.
- Service boot autostart: disabled, consistent with the approved non-autostart posture.

### Canonical API data

Authenticated read result:

| Field | M15 | H1 |
|---|---|---|
| Contract | 1.0.0 | 1.0.0 |
| Schema | 1 | 1 |
| Symbol | BTCUSDT | BTCUSDT |
| Candles returned | 2 | 2 |
| Coverage | 2/2 complete | 2/2 complete |
| Gaps | none | none |
| Latest candle closed | true | true |
| Latest quality | VALIDATED | VALIDATED |
| Dataset version | `sha256:66b202538feb2664c176cfb60a4bfbf13aaea6c91d8d24c8d682f85863de4c32` | `sha256:e7f65e29d1872243806f2a4d8f0802afe93be644e56e944c75e8e0d42d5cc0e9` |

Freshness interpretation was statically verified in `freqai_bridge/http_candles.py`: T2 compares ingestion lag (`availableAtMs - closeTimeMs`) with `max_lag_ms`; it does not reject a candle solely because `closeLagMs` or `observationAgeMs` is greater than 120 seconds.

Latest M15 ingestion lag: 8,558 ms. Configured maximum: 120,000 ms. PASS.

### T2 one-shot canonical context

- Command: `python -m freqai_bridge.context --bars 2 --output /tmp/t2-canonical-window-20261109T112946Z.json`.
- Exit code: 0.
- Symbol/timeframe: BTCUSDT / 15m.
- Candle count: 2.
- Coverage: complete; expected 2; returned 2; gaps empty.
- Artifact JSON parse: PASS.
- Dataset version: `sha256:104e7a83286ac0b35c4665964ae29c5926e8deb18220b715e73f51b94cffb05f`.
- Local VPS artifact path: `/tmp/t2-canonical-window-20261109T112946Z.json`.
- The artifact was generated on the VPS and was not uploaded as a GitHub Actions artifact. It remains a local runtime artifact; no claim of GitHub artifact retention is made.

## Result

**PASS — T0 loopback API deployment and bounded T2 canonical-context read.**

- API authentication and loopback binding: PASS.
- M15/H1 API contract and coverage: PASS.
- T2 ingestion-lag validation: PASS.
- T2 one-shot artifact generation and JSON validation: PASS.

## Provenance and CI

- Evidence source: operator-provided VPS command output on 2026-11-09 UTC.
- GitHub Actions workflow: NOT DISPATCHED for this operator-run runtime gate.
- Workflow run ID: NONE.
- GitHub Actions artifact ID: NONE.
- The local `/tmp` JSON artifact is not a GitHub Actions artifact.
- This evidence document records the source SHA and runtime observations; it does not independently attest process memory or loaded executable bytes.

## Boundaries and next step

- T1 remains NOT ACTIVATED in this gate.
- No Feeder restart or DB/WAL mutation was performed.
- No strategy, model training, signal publication, ledger, risk-engine, OKX source, or live-trading change was performed.
- `AI_EXECUTION_ENABLED=false`; no live orders.
- No deletion, cleanup, vacuum, compaction, archive or backup expiry was performed.
- Next step: preserve this runtime gate result in the handoff, then separately review the remaining operational gates before activating T1 or expanding T2 execution.
