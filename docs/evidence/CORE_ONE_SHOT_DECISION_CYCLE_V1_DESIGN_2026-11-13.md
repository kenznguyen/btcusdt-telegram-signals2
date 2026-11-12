# Core One-shot Decision Cycle v1 — Design

- Date: 2026-11-13
- Branch: `feature/core-operational-proof-20261112`
- Related frozen contract: `CORE_DECISION_INPUT_BUNDLE` v1.0.0 / schema 1.
- Status: **DESIGN SPECIFIED; IMPLEMENTATION BLOCKED ON SOURCE-ADAPTER GAPS; RUNNER NOT IMPLEMENTED**.
- Authority: automatic approval covers this design/review/evidence increment only.
- Runtime posture: PAPER; `AI_EXECUTION_ENABLED=false`; no live orders.

## 1. Scope

One invocation performs exactly one Strategy Core decision cycle from one immutable validated bundle, then returns WAIT/blocked or attempts one Core-scoped PaperLedger submission. Preserve RSI + ADX + Smart DCA unchanged. Core and AI ledgers remain separate; Shared Risk Engine and Kill Switch remain the sole admission authority.

No daemon/scheduler, VPS/provider deployment, schema/migrations, strategy/threshold/leverage changes, AI admission, exchange trading endpoints, T0 writes, canonical T0 DB access, data cleanup/deletion or live execution.

## 2. CLI/config

Entry point: `python -m core_runtime --config <explicit-json>`. Exactly one cycle; no loop, sleep, server or persistent process.

Strict config:
- `mode=PAPER`; `ai_execution_enabled=false`.
- `ledger_path`: explicit resolved path to an existing file; never create a missing DB.
- `max_book_age_ms`: explicit positive integer; bool/float/missing/zero/negative rejected; no default.
- `max_position_base`: positive decimal string passed to the existing Core producer.
- No credentials/tokens in config, CLI args, output or logs.

T0 HTTP settings remain environment-only: `T0_CANDLE_API_BASE_URL`, `T0_CANDLE_API_TOKEN`, `T0_CANDLE_MAX_LAG_MS`. No Hummingbot URL, credentials, process or adapter is part of this runner; Hummingbot remains paused/out of scope. Reject non-empty Binance/OKX exchange-trading credential variables; require process `AI_EXECUTION_ENABLED=false`; reject ledger path equal to configured canonical T0 DB path. Check the ledger file exists before any SQLite connection.

Shared risk limits remain sourced by existing `paper_execution.equity.parse_limits(os.environ)`: `PAPER_MAX_DRAWDOWN_PCT`, `PAPER_MAX_DAILY_LOSS_USDT`, `PAPER_MAX_EXPOSURE_USDT`. Missing limits fail closed for exposure increase. Do not create another risk policy or change the existing 1% order-margin budget.

## 3. Source acquisition

### T0 candles

Use read-only `GET /v1/candles` via `freqai_bridge.http_candles.CandleHttpClient` or a dedicated wrapper. No `market_window()`, `create_store_from_env()`, direct SQLite, cache, synthetic candle or venue fallback.

Fetch BTCUSDT M15 and H1, 100–2,000 closed candles, bound to one `decisionAtMs`. Preserve the exact source response `datasetVersion`, coverage, freshness and candle rows.

**C1 — BLOCKER:** current `CandleHttpClient` pages at 32 candles and synthesizes a new digest as `datasetVersion` when combining pages. This violates the frozen requirement to preserve the T0-owned identity. First runner increment must fetch exactly 100 candles per timeframe in one bounded T0 response and add a public one-page client path that returns the original envelope/identity unchanged. Keep the existing 256 KiB response cap unless measured evidence and separate review justify a change. Tests must assert one HTTP response per timeframe and exact datasetVersion preservation. Never label the locally synthesized multi-page digest as source-owned.

Retain TLS, bearer auth, no redirects, body cap, timeouts/retries, duplicate-key JSON rejection and T0 contract validation. Any source error aborts before producer invocation.

### Order book

Target T1 as the preferred Order Book source for BTCUSDT, but do not connect to the current dashboard endpoint or consume periodic float-derived snapshots. T1 currently captures raw `depth_updates` with string-valued price/quantity pairs and `U/u/pu` identifiers, plus initial and periodic `depth_snapshot` rows.

**C2 — BLOCKER (T1 source contract):** the T1 dashboard `GET /api/orderbook/{symbol}` path reconstructs and returns binary floats; it omits timestamp, update ID, anchor, continuity and freshness metadata; its reader does not verify the `pu` chain. T1's periodic snapshots are re-serialized from an in-memory `f64` book. The collector deliberately does not resnapshot on every WebSocket reconnect; gaps are visible in the raw diff tape, but the current endpoint does not bind its returned book to a verified contiguous range. No approved versioned read-only T1 → T2 contract currently exists. Freeze a contract that returns exact decimal strings, a trusted anchor and single update watermark, verified `U/u/pu` continuity, reconnect/gap state, source/observation timestamps, bounded depth, and consistent read semantics. Fail closed on any gap, stale/partial/corrupt input or uncertain anchor. See `docs/evidence/T1_ORDERBOOK_SOURCE_REVIEW_2026-11-13.md` for exact repository/source evidence. Hummingbot remains PAUSED and out of scope. No T1 code/runtime change is authorized by this design.

## 4. Acquisition and bundle assembly

1. Validate config, process environment and path separation.
2. Capture one `decisionAtMs`; bind all inputs to it.
3. Fetch M15/H1 over T0 HTTP and one fresh book snapshot.
4. Verify the existing paper ledger file. Read Core state via `read_snapshot(path, strategy_id="STRATEGY_CORE")` (read-only).
5. Read account-wide snapshot via `read_account_risk_snapshot(path, now_ms=decisionAtMs)`; embed exact return value and frozen RFC 8785 digest. Missing/unreadable/invalid risk snapshot aborts with exit 3; never reconstruct or substitute fields.
6. Assemble frozen Bundle v1 from unchanged T0 payloads, Decimal book, Core-scoped paper projection and exact risk snapshot; compute `bundleId`.
7. Call pure `validate_bundle(bundle, max_book_age_ms=...)`. No producer/writer/admission before validation passes.

Caller-supplied position/average/owner/DCA state is never authoritative. The read risk snapshot is observational, not an admission reservation.

## 5. Core pipeline and producer no-intent cases

After bundle validation, exactly once call:
`produce(m15, h1, paper_snapshot, core_strategy_state, book, decisionAtMs, account_equity_quote=..., max_position_base=...)`.

If the producer report has a complete intent, call `producer_report_to_signal()`, then `pipeline.core_signal.validate(report, decisionAtMs)`. Do not synthesize provenance, intent IDs, timestamps or prices. Invalid/expired signals never submit.

WAIT with no intent is terminal: no submit; output `decision=WAIT`, `admission=NOT_ATTEMPTED`, `simulation=NOT_RUN`.

Current producer may return BUY/SELL with `intent=None` for blocked outcomes. Do not send these through the strict adapter:
- `CORE_ACCOUNT_EQUITY_UNAVAILABLE`: risk blocked, no submit, exit 3.
- `CORE_SIGNAL_BLOCKED_SHARED_POSITION`: ownership blocked, no submit, completed non-trading cycle, exit 0.
- WAIT/no intent: normal WAIT, exit 0.
- Unknown non-WAIT/no-intent: invalid producer contract, exit 4.

## 6. Event classification and Shared Risk Engine

Derive event from immutable pre-cycle Core position and validated target; never trust caller-supplied event:
- ENTRY: flat to non-flat.
- DCA: non-flat to larger absolute exposure in the same direction.
- EXIT: non-flat to smaller absolute exposure in the same direction, including zero.
- Reversal/sign flip or inconsistent action/target: reject before submit, exit 4.

Only after bundle validation instantiate existing scoped writer:
`PaperLedger(path, risk_limits=parse_limits(os.environ), require_risk_limits=True, leverage=CORE_LEVERAGE, strategy_id="STRATEGY_CORE", apply_migrations=False, ...)`.
Use existing Core leverage constant, never a new hardcoded value. Verify file and dual-ledger migrations before construction. No migration, schema initialization or repair.

Submit once:
`ledger.submit(validated_signal["intent"], validated_book, decisionAtMs, strategy_event=event)`.

Existing scoped submit is authoritative: transactionally reloads current Core/account state, enforces risk limits, margin/exposure budget, reservations, intent expiry, book depth, pending-order rules and Kill Switch, then records exact paper outcome. Do not write ledger tables directly or bypass the transactional recheck. The bundle snapshot is not a reservation.

### EXIT when riskReady is false

Do not reuse current `_preflight()` as a blanket `riskReady=true` gate. A missing/unreadable risk snapshot blocks all actions (exit 3). If the snapshot is readable but `riskReady=false`, pass no equity to producer; ENTRY/DCA cannot be sized. A valid reduction-only EXIT may be attempted only through Core PaperLedger. Its transactional code determines whether it truly reduces; Kill Switch/pause blocks increases but does not by itself block a valid reduction. Pending orders, invalid/expired intent, invalid book and other ledger rules can still reject. No runner-level EXIT exception.

## 7. Output and exit codes

Emit one machine-readable JSON result; safe stable diagnostic codes only. No secrets, environment dump, raw provider body or DB contents. Include bundleId, source datasetVersions, decisionAtMs, strategyVersion/inputSnapshotId when present, separate decision/signalValidation/admission/simulation statuses, and exact ledger status. OPEN, PARTIALLY_FILLED and FILLED are not equivalent.

Frozen exit mapping:
| Code | Meaning |
|---:|---|
| 0 | Cycle completed (including WAIT or ownership-blocked no-submit); not a trade guarantee |
| 2 | Invalid config or bundle |
| 3 | Risk snapshot unavailable/invalid or attempted action risk-blocked |
| 4 | Invalid Core signal/producer contract or unsupported position transition |
| 5 | PaperLedger/Shared Risk Engine admission rejected |
| 6 | Infrastructure/storage/provider/unexpected runtime error |

A valid ledger REJECTED result maps to 5. Exceptions map to 6 unless explicitly risk-snapshot unavailable/invalid (3). Preserve exact order status; never call a partial/open result a fill.

## 8. Required tests

- Strict config, no defaults, bool-vs-int, PAPER/AI-off, credential and path separation.
- Invalid/missing config/ledger must not create files or DBs.
- One T0 response per 100-candle timeframe; exact source datasetVersion preserved; no fallback on auth/timeout/503/oversize/gap/stale.
- Decimal book parser preserves source precision; emits no floats; rejects invalid/stale/future/crossed depth.
- Snapshot readers remain read-only; no migration/init.
- Bundle validator runs before producer; invalid bundle prevents producer/ledger calls.
- Producer exactly once; WAIT and known no-intent cases do not submit.
- Adapter then signal validator; malformed/expired signal never submits.
- ENTRY/DCA/EXIT classification for flat/long/short/increase/reduction/flatten/reversal.
- riskReady=false blocks ENTRY/DCA but allows only attempted reduction through PaperLedger; unavailable snapshot blocks all.
- Disposable SQLite tests for kill/pause, pending orders, limits, reservations, idempotent replay and book consumption.
- Exactly one submit attempt; distinct reporting for rejection, partial/open/fill, exceptions.
- Exit codes, JSON output, secret redaction.
- Run existing Core strategy/signal, preflight, producer adapter, bundle validator, account risk, Shared Risk Engine and PaperLedger regression suites. Preserve exact SHA/artifact; never weaken tests to force green.

## 9. Additional findings

- **C1:** HTTP multi-page client synthesizes datasetVersion; one-response path required.
- **C2:** Hummingbot normalizer converts decimals to floats; Decimal-preserving source adapter required.
- **C3:** current `core_runtime.__main__` preflight rejects any `riskReady != true` and maps failures to generic exit 2. Keep it separate; runner must not reuse it as an all-actions gate.
- **C4:** producer returns BUY/SELL without intent for documented blocked reasons. Explicitly classify these before strict adapter; unknown cases fail closed.

These are findings, not permission to modify T0 API/client, T1 source/runtime, preflight, producer, ledger or runner. Hummingbot remains paused and is not a candidate source.

## 10. Disposition

- One-shot orchestration contract: **SPECIFIED**.
- Shared risk/EXIT semantics: **SPECIFIED against existing transactional ledger**.
- T0 source boundary: **SPECIFIED; C1 BLOCKS IMPLEMENTATION**.
- Order-book source boundary: **T1 PREFERRED; CONTRACT NOT FROZEN; C2 BLOCKS IMPLEMENTATION**.
- Producer/signal/ledger order: **SPECIFIED; C4 requires tested handling**.
- Preflight compatibility: **C3 identified; no change made**.
- Runner: **NOT IMPLEMENTED**.
- VPS/provider runtime: **NOT AUTHORIZED**.
- AI execution/live orders: **PROHIBITED**.

The design increment remains **BLOCKED** until C1 is resolved and the T1 → T2 Order Book contract (C2) is frozen and proven. Hummingbot is paused/out of scope. T1 is the preferred source, not yet a trusted operational input. The implementation gate remains separate. Automatic approval here does not extend to code changes, migrations, provider/runtime changes, VPS, AI execution or live trading.
