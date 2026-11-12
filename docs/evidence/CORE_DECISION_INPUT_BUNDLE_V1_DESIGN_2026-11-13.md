# Core Decision Input Bundle v1 — Frozen Contract

- Date: 2026-11-13
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/core-operational-proof-20261112`
- Approval: user approved all six design decisions on 2026-11-13.
- Contract: `CORE_DECISION_INPUT_BUNDLE`
- Contract version: `1.0.0`
- Schema version: `1`
- Status: **FROZEN — PURE VALIDATOR IMPLEMENTED AND CI-VERIFIED; ONE-SHOT RUNNER NOT IMPLEMENTED**
- Scope: immutable input contract for one Core PAPER decision cycle. This does not authorize runner implementation, runtime provider integration, VPS use or live trading.

## 1. Purpose and boundaries

One invocation consumes one self-consistent immutable bundle. The bundle is a decision input only; it is not a strategy signal, risk admission, order, fill or execution authorization.

The bundle carries T0 M15/H1 candle response payloads, one visible order-book snapshot, a Core-scoped paper-state snapshot and the account-wide risk snapshot. It preserves source provenance and does not permit implicit defaults, stale-cache fallback, synthetic candles, direct canonical T0 database access or cross-source substitution.

Strategy Core remains unchanged: RSI + ADX + Smart DCA. Core and AI ledgers remain separate. This runner contract is Core-only; `aiExecutionEnabled=false` is mandatory.

## 2. Frozen envelope

Required top-level fields:

- `contract`: exactly `CORE_DECISION_INPUT_BUNDLE`.
- `contractVersion`: exactly `1.0.0`.
- `schemaVersion`: exactly integer `1`.
- `bundleId`: `sha256:` followed by 64 lowercase hexadecimal characters.
- `createdAtMs`, `decisionAtMs`: nonnegative safe UTC Unix millisecond integers; created time cannot be after decision time.
- `mode`: exactly `PAPER`.
- `aiExecutionEnabled`: exactly boolean `false`.
- `strategyId`: exactly `STRATEGY_CORE`.
- `market`: exactly Binance / USDT perpetual / BTCUSDT / 15m.
- `marketData`: source contract `T0_READ_ONLY_CANDLE_V1`, plus complete M15 and H1 T0 response envelopes.
- `orderBook`: validated visible depth snapshot.
- `paperState`: read-only Core ledger projection.
- `accountRisk`: digest and exact account-wide risk snapshot returned by `read_account_risk_snapshot()`.

All timestamp values are integer UTC Unix milliseconds. All monetary, quantity and price values are decimal strings. JSON floating-point values are prohibited throughout the bundle. Safe integer timestamps and schema counters must be in the IEEE-754 safe integer range (absolute value <= `9007199254740991`).

Unknown top-level fields are rejected in v1. Optional/null behavior is explicit per field; absent and null are not interchangeable. Arrays preserve order.

## 3. Frozen source payloads

### 3.1 T0 M15/H1 candle envelopes

Embed the bounded T0 response payloads in the bundle; do not reference a mutable URL or only a digest. Each embedded response must conform to T0 Read-only Candle Contract v1:

- `contractVersion=1.0.0`, `schemaVersion=1`.
- `exchange=binance`, `marketType=USDT_PERPETUAL`, `symbol=BTCUSDT`.
- `timeframe=15m` or `1h`, `volumeUnit=BTC_BASE_ASSET`, `source=ccxt.binanceusdm`.
- Exact source `datasetVersion` retained unchanged.
- Candle fields: `openTimeMs`, `closeTimeMs`, decimal-string `open/high/low/close/volume`, `isClosed=true`, `availableAtMs`, `availabilityKind=FIRST_OBSERVED`, `quality=VALIDATED`, `source=ccxt.binanceusdm`.
- Strictly ascending, unique, contiguous candle sequence; no synthetic or forward-filled rows.
- `coverage.complete=true`, `expected=returned=len(candles)`, `gaps=[]`.
- At least 100 candles per timeframe to satisfy the current Core producer; no more than 2,000 candles per timeframe, matching the T0 response bound.
- Existing Core closed-candle/freshness rules must pass. H1 must be the latest eligible fully closed H1 candle before the current M15 bucket.

The T0 `datasetVersion` values remain source-owned identities; they are never replaced by the bundle digest. No direct SQLite access to canonical T0 is permitted.

### 3.2 Order book

Required fields: `source`, `connector`, `symbol=BTCUSDT`, `observedAtMs`, non-empty `bids` and `asks`.

Each level contains positive decimal-string `price` and `quantity`. Bids are descending; asks are ascending; best bid must be strictly below best ask. Observation time cannot be after `decisionAtMs`.

**Freshness decision (resolved):** runner configuration must provide explicit positive integer `maxBookAgeMs`. Missing, boolean, non-integer, zero or negative values are invalid. The bundle validator rejects an order book when `decisionAtMs - observedAtMs > maxBookAgeMs`. No built-in default or invented numeric threshold exists; the caller must choose a threshold based on the selected source cadence and operational evidence. The configured value is recorded in decision evidence.

The current Strategy Core producer does not independently enforce all book provenance, ordering or age rules. The bundle validator owns those checks before producer invocation. Strategy Core itself remains unchanged.

### 3.3 Core paper-state projection

Derived only from the existing read-only `read_snapshot(db_path, strategy_id="STRATEGY_CORE")` path; caller-supplied state is not authoritative.

Required projection:

- `positionBase`: finite signed decimal string.
- `averageEntryPrice`: finite nonnegative decimal string; zero iff flat, positive iff non-flat.
- `strategyState.owner`: exact ledger value, including null where the ledger has no owner.
- `strategyState.dcaUsed`: strict boolean.
- `strategyState.strategyId=STRATEGY_CORE`.

No caller may override this projection with manually supplied position or DCA state. The read path must remain read-only and must not create or migrate a database.

### 3.4 Account-wide risk snapshot

Embed the exact read-only return value from `read_account_risk_snapshot(db_path, now_ms=decisionAtMs)` under `accountRisk.snapshot`, unchanged. Preserve all fields returned by that reader, including:

- mode, live-trading support, availability, readiness and unavailable reason;
- account equity, gross/filled exposure, reserved notional and reserved margin;
- drawdown, daily PnL/loss, high-water mark and daily baseline;
- mark price/time and source dataset version;
- Kill Switch snapshot, per-strategy positions and update time.

`accountRisk.snapshotDigest` is SHA-256 over the RFC 8785 canonical JSON bytes of the exact snapshot object. Do not reconstruct, normalize, round or selectively rewrite financial values before digesting.

The snapshot is observational, not an admission reservation. The existing PaperLedger/Shared Risk Engine must transactionally recheck current account state on every submission. No custom bypass is permitted. If the read-only snapshot cannot be obtained or is unavailable, no decision bundle is admissible and no submission occurs. If the snapshot exists but `riskReady=false`, the runner must not bypass the existing ledger/risk admission policy: exposure-increasing ENTRY/DCA is blocked; reduction-only EXIT may be attempted only through the existing PaperLedger/Shared Risk Engine path and only if that path itself accepts it. The runner must not create a parallel EXIT exception.

## 4. Canonical bundle identity — RFC 8785

Use RFC 8785 JSON Canonicalization Scheme (JCS), implemented by the pinned `rfc8785` dependency already present in `requirements-web.txt`.

- Encode canonical JSON as UTF-8 bytes.
- Compute SHA-256 over the entire bundle object after removing only the top-level `bundleId` field.
- Format as `sha256:<64 lowercase hex>`.
- Object key ordering follows RFC 8785; arrays retain original order.
- Decimal financial values remain exact strings; do not convert them to binary floats or normalize their textual precision.
- Reject all JSON float values and unsafe integer values before canonicalization. Only safe integer timestamps/schema counters are numeric.
- Preserve explicit nulls; absent optional fields remain absent. The validator rejects unknown fields rather than silently dropping them.
- Recompute and compare `bundleId` during validation; mismatch fails closed.
- `datasetVersion` and producer `inputSnapshotId` are independent source/producer identities and must not be synthesized or overwritten by `bundleId`.

## 5. Validation and decision order

1. Validate exact envelope keys, contract/schema version, timestamp types/range, PAPER mode, AI disabled, strategy and market identity.
2. Validate both embedded T0 response envelopes, exact provenance, coverage, candle count, decimal strings, ordering, continuity, closure, OHLC bounds and existing Core timeframe freshness constraints.
3. Validate explicit `maxBookAgeMs`; then validate order-book identity, decimal levels, ordering, spread and observation age.
4. Read Core paper state through the read-only Core-scoped ledger snapshot; validate the projection.
5. Read account-wide risk snapshot through the read-only reader; preserve and digest the exact result. If unavailable, stop without invoking the producer or submitting anything.
6. Recompute and verify bundle digest.
7. Construct exact `produce()` arguments without source substitution or provenance synthesis.
8. Call `pipeline.core_strategy.produce()` once.
9. Translate only known producer outcomes through `producer_report_to_signal()`, then call `pipeline.core_signal.validate()`.
10. WAIT/no-intent never submits. Actionable intent goes only to Core-scoped PaperLedger; the Shared Risk Engine and Kill Switch recheck transactionally.
11. Emit separate decision, signal validation, admission and simulation outcomes. Never report admission/fill before the ledger returns that outcome.

Invalid input returns a stable blocked diagnostic and never silently falls back to another source. A valid bundle is not evidence that a signal exists or that admission/fill will succeed.

## 6. Stable CLI exit-code mapping

The future one-shot CLI must use this mapping:

| Code | Meaning |
|---:|---|
| 0 | Cycle completed; not a promise of trade, admission or fill |
| 2 | Invalid configuration or input bundle |
| 3 | Risk snapshot unavailable/invalid or risk state blocks the attempted action |
| 4 | Core signal invalid |
| 5 | Shared Risk Engine / PaperLedger admission rejected |
| 6 | Infrastructure/storage/unexpected runtime error |

WAIT is a completed cycle and returns 0 with explicit `decision=WAIT`, `admission=NOT_ATTEMPTED`, `simulation=NOT_RUN`. No new exit code implies a successful trade.

## 7. Implemented pure validator module

The frozen API is implemented in `core_runtime/input_bundle.py`:

- `BundleValidationError(ValueError)`: stable diagnostic code in its message.
- `compute_bundle_id(bundle) -> str`: RFC 8785 + SHA-256 as specified above.
- `validate_bundle(bundle, *, max_book_age_ms) -> dict`: validates the immutable bundle and returns a small verified summary; it performs no I/O, ledger reads/writes, network calls, producer invocation or risk admission.

Read-only ledger/risk snapshot acquisition and bundle assembly belong to a later runner orchestration increment. The pure validator must not import or initialize PaperLedger.

## 8. Contract test gate and GREEN evidence

The deterministic contract suite is `core_runtime/test_input_bundle_contract.py` (15 tests). It covers:

- valid PAPER bundle and explicit order-book age policy;
- missing/invalid max-book-age configuration;
- stale/future order-book timestamps;
- PAPER-only and AI-disabled invariants;
- candle coverage and decimal-string integrity;
- order-book level validity and spread;
- Core state identity and unavailable account-risk snapshot;
- RFC 8785 digest stability, bundleId exclusion, key-order independence;
- rejection of floats and unsafe integers;
- array order and decimal-string precision preservation.

GREEN evidence: GitHub Actions [run #95](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43269294117), exact source SHA `2248eb20cb9b93d0a56fb54e073fcc20e715e7f3`, completed SUCCESS. All 16 workflow steps succeeded; the validator suite passed 15/15 and the existing Core, account-risk, Shared Risk Engine and PaperLedger regression suites also passed. Artifact ID `13966654587`, size 6,292 bytes, upload digest `sha256:f8429f2a647774ef77a212781a7826bbe2939d56042ffb7b57457fcbba9d80ff`; the payload was not independently downloaded/re-hashed.

## 9. Safety and scope

- Core strategy RSI/ADX/Smart DCA logic, thresholds and fixed Core leverage are unchanged.
- AI strategy execution remains disabled; no AI ledger admission is included.
- Shared Risk Engine, Kill Switch and PaperLedger remain authoritative and unchanged.
- No schema/migration changes, order execution, exchange credentials, real orders, T0/T1 runtime access, canonical T0 DB access, VPS commands, persistent installation, systemd/autostart or daemon.
- No automatic data deletion or cleanup behavior.
- Tests use deterministic in-memory fixtures only; any future ledger integration tests must use disposable local DB fixtures.

## 10. Disposition

- Six design decisions: **APPROVED BY USER**.
- Core Decision Input Bundle v1 contract: **FROZEN**.
- Pure validator implementation: **IMPLEMENTED; 15/15 TESTS PASS**.
- Exact-SHA CI #95 and existing regression gates: **PASS** (source SHA `2248eb20cb9b93d0a56fb54e073fcc20e715e7f3`).
- Core one-shot decision cycle: **NOT IMPLEMENTED**.
- Runtime/provider integration and VPS runtime: **NOT STARTED / NOT AUTHORIZED**.

Next bounded increment: perform a separate design review for the Core one-shot decision cycle, including its source-acquisition boundary, read-only Core state/risk snapshot acquisition, producer invocation, signal validation, PaperLedger admission, outcome reporting and stable CLI exit codes. Do not begin runner implementation until that design gate is explicitly approved. No VPS or live-trading authorization is implied.
