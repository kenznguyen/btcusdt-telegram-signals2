# T0–T1–T2 Data Consumption Architecture Decision

- Decision date: 2026-11-08
- Status: **APPROVED ARCHITECTURE TARGET — IMPLEMENTATION NOT VERIFIED**
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Decision type: documentation-only architecture clarification
- Supersedes: ambiguous wording that T0 is already a complete data provider for both T1 and T2. It does not supersede existing T0 ownership, single-writer, paper-only, or runtime restrictions.

## 1. Decision

Keep T0 as an independently owned canonical data asset. T1 and T2 are separate consumers and must receive data through explicitly versioned, controlled, read-only contracts. Neither consumer may write to T0 or obtain implicit ownership of its storage.

The architecture is intentionally **not** a shared-database architecture:

- T0 owns canonical ingestion, storage, schema/migrations, retention, integrity, and data-quality publication.
- T1 consumes eligible candle data from T0 through a controlled read-only contract, while its funding, open-interest, liquidation, Order Book, and large-trade/microstructure feeds remain separately sourced and independently identified.
- T2 may integrate against T0 through its read-only adapter/bridge and deterministic fixtures. T0 is not yet approved as T2's sole or replacement backtest/OOS market-data source.
- T1/T2 research state, strategy state, and paper ledgers remain outside T0.
- Shared Risk Engine/Kill Switch is downstream of strategy signal generation. It is not part of T0 and does not grant any strategy a bypass around risk controls.
- Paper execution remains the only permitted execution scope. `ai_execution_enabled=false`; no live orders or exchange execution.

## 2. Logical boundaries

```text
Public market-data sources
          |
          v
   T0 Data Foundation
   - canonical ownership
   - single writer / lease fencing
   - canonical storage
   - data-quality and lineage
          |
          | versioned, read-only data contracts
          +---------------------------+
          |                           |
          v                           v
   T1 Java Futures AI Bot       T2 Freqtrade + FreqAI
   - candle input               - read-only adapter/bridge
   - separate microstructure    - fixture-first validation
     source streams             - no source replacement yet
          |                           |
          +-------------+-------------+
                        |
                        v
            Strategy signal interfaces
             - Strategy Core signals
             - independent AI signals
                        |
                        v
            Shared Risk Engine / Kill Switch
                        |
                        v
                 Paper Execution
             (isolated paper state/ledger)
```

The diagram describes target boundaries, not proof that every adapter or runtime connection is implemented.

## 3. Access and ownership rules

| Resource | Owner | T1/T2 access |
|---|---|---|
| T0 canonical SQLite/database | T0 | No direct file/database access by default |
| T0 canonical write path | T0 Feeder only, under its fencing contract | Denied |
| T0 published candle interface | T0 | Read-only, scoped, versioned contract |
| T1 funding/OI/liquidation/order-book/large-trade inputs | T1 source adapters / their named providers | T1-owned; not presumed to exist in T0 |
| T2 strategy/research/backtest state | T2 | T2-owned |
| Paper ledger and paper position state | Paper execution subsystem | Separate from T0; governed by risk and paper contracts |
| Shared Risk Engine policy/state | Risk subsystem | Consumers submit signals/intents; no bypass |

Rules:

1. No T1/T2 write, migration, schema mutation, or retention operation against T0.
2. No direct access to the canonical SQLite file path as an integration shortcut. Use an approved T0 read-only interface/adapter.
3. Every consumer request must identify symbol, market type, timeframe, time window, contract version, and required candle semantics.
4. Data responses must expose source identity and enough metadata to assess freshness, completeness, and closed-candle status. Missing or ambiguous metadata fails closed for strategy use.
5. T0 must not silently combine Binance USD-M canonical candles with Kraken Spot, Bybit Shadow, OKX, or other feeds. Venue, market type, and provenance remain explicit.
6. Consumer-local caches/fixtures are permitted only when clearly marked non-canonical and traceable to their source snapshot.

## 4. T1 input decision

T0's currently evidenced contribution is Binance USD-M perpetual BTCUSDT M15/H1 OHLCV. This is a **partial base-candle input**, not a complete T1 market-data package.

T1 continues to own or explicitly integrate separate data streams for:
- Funding rate and open interest.
- Liquidations.
- Order Book snapshots and incremental updates.
- Large trades / microstructure observations.

Each stream requires its own provider identity, timestamp semantics, continuity/recovery rules, quality state, and evidence. Do not label T1 market-data readiness PASS merely because T0 candle reads work.

Current assessment: **PARTIAL INPUT AVAILABLE**. Full T1 data readiness and runtime integration are **NOT VERIFIED**.

## 5. T2 input decision

T2 may proceed with fixture-based and controlled read-only adapter integration against T0 M15/H1 candles. The existing OKX research/backtest baseline remains unchanged.

T0 is not approved to:
- Replace OKX as the official T2 research/backtest/OOS source.
- Become the sole source for parity or model certification.
- Support claims of Binance–OKX parity without explicit reconciliation.
- Promote a strategy/OOS result based only on the current bounded Feeder runtime evidence.

Before source promotion, T2 needs data-quality evidence for gaps, duplicates, timestamp alignment, freshness/staleness, closed-candle guarantees, history coverage, recovery behavior, and lineage. Any source comparison must match venue/market semantics and exact candle windows.

Current assessment: **FIXTURE / READ-ONLY INTEGRATION ELIGIBLE; SOURCE PROMOTION BLOCKED**.

## 6. Data trust and promotion gates

Use separate gates; do not collapse them into a single "integrated" status.

| Gate | Required proof | Current status |
|---|---|---|
| Contract gate | Versioned schema/interface, read-only permissions, provenance fields, fail-closed behavior | Target approved; implementation/conformance NOT VERIFIED |
| Data-quality gate | Gaps, duplicates, timestamp alignment, freshness, closed candles, history coverage, recovery and lineage | PAUSED / NOT VERIFIED |
| Strategy parity gate | Same source/window/semantics, independently reconciled inputs and outcomes | NOT VERIFIED |

A successful Feeder restart or candle persistence observation proves only the bounded runtime behaviors recorded in the T0 evidence report. It does not establish full data quality, complete T1 feeds, T2 source parity, production readiness, or 24x7 reliability.

## 7. Shared strategy and risk boundary

T1/T2 may produce strategy signals through explicit signal contracts. For the dual-strategy direction:

- Strategy Core retains RSI + ADX + Smart DCA.
- The independent AI strategy may emit LONG/SHORT even when Strategy Core emits no signal.
- Signal origin and strategy/model version must remain explicit.
- Every candidate signal must pass the same Shared Risk Engine, portfolio exposure limits, Kill Switch, and paper-execution eligibility checks.
- No strategy may submit orders directly or bypass risk approval.
- Dynamic AI leverage remains bounded by the separately approved paper-only policy (1x–3x, linear mapping) and is not activated by this architecture document.

This section defines intended boundaries; it does not claim that the complete dual-strategy runtime has been implemented or validated.

## 8. Current operational restrictions

- Preserve the existing supervised T0 Feeder state; do not stop, restart, duplicate, or reconfigure it under this decision.
- Do not run Data Quality Gate checks while the user has paused testing.
- Do not activate T1/T2 runtime or connect additional exchange streams.
- Do not alter canonical T0 storage or grant direct consumer database access.
- Do not enable systemd/autostart/linger or deployment.
- Keep `ai_execution_enabled=false`; no live trading, real orders, or exchange execution.
- Documentation approval does not authorize code changes, migrations, tests, runtime actions, or source promotion.

## 9. Next steps when separately authorized

1. Review and version the T0 read-only candle contract, including provenance and closed-candle/freshness metadata.
2. Implement/verify T2 fixture-first adapter conformance without replacing OKX.
3. Define T1's independent stream contracts and quality requirements for funding/OI/liquidations/Order Book/large trades.
4. Resume T0 Data Quality Gate only after explicit authorization; record thresholds before execution.
5. Run source parity and strategy validation only after data-quality gates pass.
6. Keep all consumer integration and paper execution isolated from canonical T0 writes.

## 10. Evidence and change record

- Decision is based on the project handoff and T0 supervised runtime evidence dated 2026-11-08.
- T0 evidence report: `docs/evidence/t0/T0_FEEDER_SUPERVISED_RUNTIME_2026-11-08.md`.
- Runtime checkout observed during the recorded run: `4cf3959532024d286a76712bd93708b7a96489df`; this is not cryptographic proof of loaded process code.
- Documentation-only change: no tests, workflows, artifacts, runtime, database, exchange connections, or market-data synchronization are part of this decision.
