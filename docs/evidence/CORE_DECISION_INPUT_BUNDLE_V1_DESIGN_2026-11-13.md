# Core Decision Input Bundle v1 — Design Review

- Date: 2026-11-13
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/core-operational-proof-20261112`
- Design baseline HEAD: `5280a2b97ced53d1c8c12aff18610470e970a2c7`
- Status: **DRAFT — DESIGN REVIEWED; NOT FROZEN; NOT IMPLEMENTED**
- Scope: define a versioned, immutable input boundary for one Core paper decision cycle. Documentation only.

## 1. Decision boundary

The one-shot runner must consume one self-consistent bundle. It must not assemble inputs from implicit defaults, stale caches, multiple untracked sources, or direct T0 database access.

The bundle is a decision-input record, not a signal, admission, order, fill, or execution authorization. Its existence does not imply that the Core producer will emit an actionable intent or that Shared Risk Engine will admit it.

R0 remains deterministic and offline: CI fixtures and disposable paper-ledger state only. No T0 endpoint, T1 feed, Hummingbot runtime, exchange connection, or live network provider is included in this contract gate.

## 2. Proposed contract identity

- Contract name: `CORE_DECISION_INPUT_BUNDLE`
- Contract version: `1.0.0-draft`
- Schema version: `1`
- Market identity: `binance / USDT_PERPETUAL / BTCUSDT`
- Core timeframe: `15m`
- Required higher timeframe: `1h`
- Strategy identity: `STRATEGY_CORE`
- Execution mode: `PAPER`
- AI execution: `false`

Breaking changes to required fields, units, identity, or validation semantics require a new major version. Additive optional metadata may be minor-versioned. Unknown required-field extensions and unsupported major versions must fail closed.

## 3. Proposed top-level envelope

```json
{
  "contract": "CORE_DECISION_INPUT_BUNDLE",
  "contractVersion": "1.0.0-draft",
  "schemaVersion": 1,
  "bundleId": "sha256:<canonical-bundle-digest>",
  "createdAtMs": 0,
  "decisionAtMs": 0,
  "mode": "PAPER",
  "aiExecutionEnabled": false,
  "strategyId": "STRATEGY_CORE",
  "market": {
    "exchange": "binance",
    "marketType": "USDT_PERPETUAL",
    "symbol": "BTCUSDT",
    "decisionTimeframe": "15m"
  },
  "marketData": {
    "sourceContract": "T0_READ_ONLY_CANDLE_V1",
    "m15": {},
    "h1": {}
  },
  "orderBook": {},
  "paperState": {},
  "accountRisk": {}
}
```

All timestamp values are UTC Unix milliseconds. The example is structural only; zero values and placeholder digest are not valid runtime data.

## 4. Required input sections

### 4.1 Market data

Each timeframe window must preserve the T0 candle contract v1 response provenance and satisfy the existing Core producer window shape:

- `timeframe`: exactly `15m` or `1h`.
- `datasetVersion`: copied exactly from the source response; never recomputed or replaced by a consumer.
- `candles`: ascending closed candles, no duplicates, no missing intervals, no synthetic/forward-filled rows.
- `coverage`: `complete=true`, `expected=returned=len(candles)`.
- Every candle: `openTimeMs`, `closeTimeMs`, decimal-string OHLCV, `isClosed=true`, `availableAtMs`, `availabilityKind=FIRST_OBSERVED`, `quality=VALIDATED`, source identity.
- At least 100 rows per timeframe, because the current `pipeline.core_strategy._valid_window()` enforces this.
- Latest M15 and H1 candles must satisfy the existing Core closed-candle and interval freshness checks. The H1 feature used for a decision must be the latest eligible fully closed H1 candle before the current M15 bucket.

No change to T0's canonical storage or API is implied. The runner must consume through an approved read-only boundary; direct SQLite access to canonical T0 remains prohibited.

### 4.2 Order book

The existing Core producer consumes `bids`, `asks`, and `observedAtMs`; current disposable operational fixtures also carry `source`, `connector`, and `symbol`.

Proposed required fields:

- `source`: non-empty source identifier.
- `connector`: non-empty connector/market identifier.
- `symbol`: exactly `BTCUSDT`.
- `observedAtMs`: UTC Unix milliseconds, not in the future relative to `decisionAtMs`.
- `bids` and `asks`: non-empty ordered arrays of positive decimal-string `price` and `quantity`; bids descending, asks ascending; best bid must be below best ask.

The contract requires an explicit maximum book age in runner configuration and rejects missing/invalid age policy. **The numeric max-age threshold is not approved by this design** and remains a freeze blocker. Do not silently choose a threshold.

The current producer does not independently enforce full order-book provenance, ordering, or age. A bundle validator must enforce these before calling `produce()`; do not modify Strategy Core as part of the bundle-contract increment.

### 4.3 Paper strategy state

This section is derived from the read-only `read_snapshot(db_path, strategy_id="STRATEGY_CORE")` result, not caller-supplied free-form values.

Minimum producer inputs:

- `positionBase`: finite signed decimal string.
- `averageEntryPrice`: finite nonnegative decimal string; zero iff flat, positive iff a position exists.
- `strategyState.owner`: preserve the ledger value.
- `strategyState.dcaUsed`: strict boolean.
- `strategyState.strategyId`: exactly `STRATEGY_CORE`.

The full ledger snapshot may be retained in protected execution evidence, but the strategy input projection must be explicit and minimal. Do not accept a caller-injected position or DCA state that differs from the read-only ledger snapshot.

### 4.4 Account-wide risk state

This section is read from `read_account_risk_snapshot(db_path, now_ms=decisionAtMs)` and is independent of the Core strategy ledger snapshot.

Required fields for an exposure-increasing decision:

- `riskReady=true`.
- `accountEquityQuote`: positive finite decimal value with its original precision preserved.
- Current account-wide exposure/reservation and Kill Switch state must be available to the shared admission path.

A preflight snapshot is not an admission reservation. The PaperLedger/Shared Risk Engine must transactionally recheck current account state when submitting an intent.

Do not turn risk snapshot unavailability into a blanket prohibition on position-reducing EXIT behavior without verifying the existing shared-risk policy. Entry/DCA exposure increases must fail closed when account readiness/equity is unavailable. EXIT/FLAT behavior remains subject to existing transactional Kill Switch and risk controls.

## 5. Bundle identity and provenance

- `bundleId` is a SHA-256 digest of a canonical serialization of the entire immutable bundle, excluding the `bundleId` field itself.
- Canonical serialization rules (key ordering, UTF-8 encoding, number representation, decimal-string normalization and treatment of optional/null fields) must be specified and tested before implementation. **This is not yet frozen.**
- `datasetVersion` values remain source-provided T0 identities and must not be replaced by `bundleId`.
- The producer's `inputSnapshotId` remains generated by the existing Strategy Core producer from its current inputs. The runner/adapter must not synthesize or overwrite it.
- Record the exact source SHA and contract version alongside the resulting decision evidence. Never insert credentials or secrets into the bundle or evidence.

## 6. Deterministic validation order

1. Validate envelope version, required keys, PAPER mode, AI disabled, and market/strategy identity.
2. Validate both T0-derived candle windows, source provenance, coverage, ordering, closure, continuity and the existing Core timeframe constraints.
3. Validate order-book identity, decimal values, spread/order, observation timestamp and configured max age.
4. Read Core ledger state through the existing read-only snapshot path; require exact strategy scope and valid position/DCA state.
5. Read account-wide risk snapshot through the tested read-only path; require readiness and positive equity for exposure increases.
6. Build the immutable `produce()` arguments without altering source values.
7. Call `pipeline.core_strategy.produce()` exactly once.
8. Translate only known outcomes through `producer_report_to_signal()`, then call `pipeline.core_signal.validate()`.
9. If WAIT/no intent, do not submit. If actionable, submit only through Core-scoped PaperLedger so Shared Risk Engine/Kill Switch recheck transactionally.
10. Emit a result that distinguishes strategy decision, signal validation, risk admission and simulated fill.

Any invalid/missing/stale input produces `INPUT_BLOCKED` or `RISK_STATE_BLOCKED`; it must not be coerced into a valid signal or silently replaced by fallback data.

## 7. Explicit result semantics

The result record must distinguish at least:

- `decision`: Core producer action and reason.
- `validation`: validator action and reason.
- `admission`: `NOT_ATTEMPTED`, `ADMITTED`, or `REJECTED`.
- `simulation`: `NOT_RUN`, `PAPER_ORDER_CREATED`, or the actual ledger simulation result.
- `bundleId`, source `datasetVersion` values, producer `inputSnapshotId`, source SHA, decision time and stable diagnostic code.

A process exit code of zero is not proof of a trade, fill, or runtime readiness. No result may label an intent as admitted before PaperLedger returns the actual admission outcome.

## 8. Freeze blockers

The following must be decided and contract-tested before marking v1 frozen:

1. Numeric maximum age for order-book snapshot, with source cadence and decision-time semantics.
2. Canonical JSON/digest algorithm for `bundleId`, including decimal strings, optional fields and nested arrays.
3. Exact projection of `read_snapshot()` and `read_account_risk_snapshot()` into the bundle, including whether the raw risk snapshot is retained or only a minimal verified projection.
4. Exact policy for reduction-only EXIT when the account risk snapshot is unavailable or `riskReady=false`, consistent with transactional Shared Risk Engine/Kill Switch behavior.
5. Whether M15/H1 windows are embedded in the bundle artifact or referenced by immutable source response digests plus bounded fixture payloads; no unbounded payloads.
6. Stable exit-code mapping for `INPUT_BLOCKED`, `RISK_STATE_BLOCKED`, WAIT, PAPER admission rejection and infrastructure errors.

Until all six are resolved, the contract remains **DRAFT / NOT FROZEN**.

## 9. Verified source alignment

- T0 source candle interface: `docs/architecture/T0_READ_ONLY_CANDLE_CONTRACT_V1_2026-11-08.md`.
- Strategy Core producer: `pipeline/core_strategy.py`; current `_valid_window()` requires at least 100 closed, contiguous candles with complete coverage and latest timeframe freshness.
- Signal validator: `pipeline/core_signal.py`; accepts schema v1 Core LONG/SHORT/FLAT/WAIT, fixed Binance USDT perpetual BTCUSDT 15m identity, provenance and a 60-second decision validity window.
- Producer adapter: `core_runtime/adapter.py`; known mapping only BUY→LONG, SELL→SHORT, CLOSE→FLAT, WAIT→WAIT; copies existing provenance only.
- Ledger read: `paper_execution.read_snapshot(..., strategy_id="STRATEGY_CORE")`; returns Core position and DCA ownership state without creating/migrating the database.
- Account risk read: `read_account_risk_snapshot()`; read-only/fail-closed tests passed 3/3 in workflow run #87.
- Prior one-shot entrypoint contract: `docs/evidence/CORE_PAPER_RUNTIME_ENTRYPOINT_CONTRACT_2026-11-12.md`.

## 10. Safety and scope

- Documentation-only design increment; no application code, strategy thresholds, leverage, ledger schema, migration, risk policy or workflow behavior changed.
- No canonical T0 access, T1 activation, network data acquisition, exchange credentials, real orders, VPS provisioning, deployment, daemon, systemd or autostart.
- `AI_EXECUTION_ENABLED=false`; Core paper-only direction retained.
- This design does not approve implementation of the runner or any production/runtime provider.

## 11. Disposition

- Existing interface inspection: **PASS**.
- Proposed bundle shape and data ownership boundaries: **DESIGN REVIEWED**.
- Bundle v1 freeze: **BLOCKED** by six explicit decisions in Section 8.
- Bundle validator/tests: **NOT IMPLEMENTED**.
- Core one-shot decision cycle: **NOT IMPLEMENTED**.
- Next bounded step: resolve the six freeze blockers explicitly, then write RED contract tests for bundle validation before implementing any runtime integration.
