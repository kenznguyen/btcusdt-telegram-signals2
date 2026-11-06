# T0 multi-source market-data architecture assessment

## Status and decision

- Status: **Proposed — architecture assessment only; documentation-only PR**.
- Decision: retain Binance USDⓈ-M BTCUSDT as the only canonical futures feed consumed by the existing strategy pipeline.
- Kraken BTC/USDT **Spot** is an independently validated alternative-source dataset. It is not a substitute for Binance USD-M, is not a futures feed, and must not be used as Binance collector acceptance evidence.
- No source adapter, schema, API, database, migration, ingestion schedule, or runtime behavior is changed by this document.
- GitHub stores source and pull requests. All executable tests and builds remain Codemagic responsibilities.

## 1. Evidence and current implementation boundary

### Existing Binance canonical contract

The current market_data/ implementation is intentionally single-market:

- market_data/store.py defines fixed identity constants: exchange='binance', market_type='USDT_PERPETUAL', symbol='BTCUSDT'.
- Candle accepts only BTCUSDT 15m/1h and serializes the fixed Binance identity and source=ccxt.binanceusdm.
- The SQLite primary key includes exchange, market type, symbol, timeframe, and open time, but the Python domain model and serializer do not yet support arbitrary source identities.
- The PostgreSQL design and current staging constraints explicitly limit the initial dataset to Binance USD-M.
- The current API response and consumers assume the Binance USD-M futures dataset. Changing the source underneath the existing endpoint would silently change market semantics.

The schema's composite key is not sufficient by itself to make the implementation multi-source. The domain model, validation, source metadata, API contract, SQL constraints, and consumer selection must all agree.

### Kraken acceptance evidence

PR #101 and its Codemagic report establish only the following for source SHA cf88fe457fee5c6662bac6500711935a17ee3f60:

- Kraken BTC/USDT Spot OHLCV retrieval for M15 and H1.
- Closed-candle validation, 24-hour complete coverage, isolated SQLite persistence/readback, repeat-sync idempotency, and stable dataset hashes.
- M15: 96/96 candles, zero gaps, repeat insert 0.
- H1: 24/24 candles, zero gaps, repeat insert 0.

That evidence does not establish Binance API reachability, Binance USD-M collection, futures semantics, canonical PostgreSQL persistence, or the canonical /v1/candles API. The Binance live acceptance remains blocked by HTTP 451 from the current Codemagic egress.

## 2. Recommended target architecture

Use independent source adapters feeding source-isolated datasets behind a shared, explicitly typed market-data contract. Do not merge or substitute datasets merely because both instruments are labelled BTC/USDT.

### Logical layers

1. **Source adapters**
   - BinanceUsdMAdapter: Binance USD-M linear perpetual only.
   - KrakenSpotAdapter: Kraken BTC/USDT spot only.
   - Each adapter validates the exchange's active market metadata, market type, symbol mapping, timeframe, timestamps, closed status, OHLCV values, and upstream response shape before producing domain records.
   - Adapter configuration and credentials are source-scoped. Public endpoints should remain credential-free where supported.

2. **Typed market identity**

   Every candle must carry an explicit identity tuple:
   (exchange, market_type, native_market_id, canonical_symbol, timeframe, open_time_ms).

   The market type must distinguish at least USDT_PERPETUAL from SPOT. Exchange-native symbol and canonical symbol mapping must be retained, not inferred later from the display symbol.

3. **Source-isolated persistence**
   - Keep the existing Binance SQLite/PostgreSQL contract and its current identity constraints unchanged during the first integration phase.
   - Persist Kraken Spot into a separate staging dataset/table or separate database/schema with an explicit Kraken Spot identity.
   - Do not relax the existing Binance-only constraints in-place as part of a source adapter rollout.
   - Any future unified table must use the complete source/market identity key and source-specific constraints. It requires a separate schema migration and parity review.

4. **Read/query boundary**
   - Existing Binance consumers continue to request Binance USD-M explicitly and retain their current response semantics.
   - A future multi-source read API must require an explicit exchange and marketType selector, or expose separate strongly typed endpoints. It must never silently choose the "available" source.
   - Response metadata must include exchange, market type, native market ID, canonical symbol, source adapter/version, requested window, availability cutoff, coverage, and dataset hash.
   - A source mismatch must fail closed; no automatic fallback from Binance USD-M to Kraken Spot.

5. **Consumer policy**
   - Existing futures strategies, paper execution, backtests, and risk calculations continue to consume Binance USD-M only.
   - Kraken Spot may initially be used for independent research, data-quality comparison, and a separate dashboard view.
   - Kraken Spot must not be fed into futures strategy signals, futures PnL/ROE calculations, leverage/liquidation logic, or Binance USD-M backtests unless a separately specified and validated transformation explicitly defines why that use is valid. No such transformation is approved here.

## 3. Non-negotiable data invariants

### Instrument semantics

- Spot and perpetual futures are different instruments, even when the base/quote pair is BTC/USDT.
- Do not describe Kraken Spot as a Binance futures replica or a Binance failover.
- Preserve exchange-native market identity and the market type on every stored row, query, report, and exported dataset.
- No cross-source price averaging, candle stitching, gap filling, or silent source substitution.
- Any cross-source comparison must use separately labelled series and report market type, venue, observation window, and timestamp alignment.

### Time and candle semantics

- Store UTC Unix milliseconds and use half-open query windows [start_ms, end_ms).
- Validate timeframe alignment and require the candle to be closed according to the source exchange clock and local observation clock.
- Record available_at_ms at first successful observation. Re-fetching historical data must not backdate availability.
- Missing candles remain missing. Do not forward-fill, synthesize OHLCV, or report complete coverage when gaps exist.
- Keep exchange event time, candle open/close boundaries, and local first-observed time conceptually separate.

### OHLCV and normalization

- Preserve decimal values without binary-float round trips in the canonical domain/storage boundary.
- Validate finite positive OHLC prices, non-negative volume, OHLC consistency, timestamp bounds, and source-specific volume units.
- Document the meaning and unit of volume for each adapter. Do not assume equal semantics solely because both CCXT adapters return an OHLCV array.
- Retain raw/native market identifiers and adapter provenance so later normalization changes can be audited.
- Reject malformed or ambiguous source metadata; do not guess the market type from a ticker string.

### Idempotency, conflicts, and lineage

- Idempotency is scoped to the complete source/market identity and candle open time.
- A duplicate with identical normalized values is a no-op and must preserve the original first-observed timestamp.
- A duplicate with different OHLCV for the same source identity is a conflict; reject the batch/page and retain evidence. Never overwrite history silently.
- Dataset hashes are source- and market-specific. A Kraken hash must never be compared or registered as the Binance dataset hash.
- Reports must record exact source commit SHA, adapter identity/version, exchange market metadata, requested window, expected/returned counts, gaps, persisted readback, repeat-sync result, and dataset hash.

## 4. Source selection and failure policy

| Situation | Required behavior |
| --- | --- |
| Binance USD-M succeeds | Persist/read Binance USD-M under its existing identity |
| Binance USD-M returns 451 or another upstream error | Report Binance source unavailable; do not switch futures consumers to Kraken Spot |
| Kraken Spot succeeds | Persist only in its isolated Spot dataset |
| Kraken Spot is unavailable | Report Kraken source unavailable; do not fabricate or reuse Binance rows |
| A requested source/market identity is unsupported | Fail closed with a typed configuration/validation error |
| Source rows disagree in price or coverage | Preserve both source-specific results; surface a comparison discrepancy, do not merge |
| A source produces gaps | Return incomplete coverage and exact gaps; no synthetic candles |

An operator may manually choose to inspect Kraken Spot while Binance is unavailable, but the UI/report must keep the Spot identity prominent and must not imply futures execution equivalence.

## 5. Incremental implementation plan (not authorized by this assessment)

Implementation should be split into separately reviewed stages:

1. **Contract design PR** — approve the typed instrument/source identity, adapter interface, volume units, API selection behavior, and storage isolation. No runtime changes.
2. **Kraken adapter PR** — add adapter/domain tests first, then isolated persistence and readback tests. Keep the Binance path untouched. Execute tests in Codemagic.
3. **Source-specific acceptance PR** — manually run Kraken live acceptance in Codemagic, tie report and artifacts to exact PR head SHA, and retain the explicit evidence boundary.
4. **Read-only research access PR** — expose Kraken Spot only through an explicitly selected, separately labelled read path. Verify existing Binance API response compatibility.
5. **Unified storage proposal (optional)** — only if operationally justified, propose a new migration with source-aware constraints, immutable lineage, rollback, SQLite/PostgreSQL parity, and a source-by-source migration plan. Do not make this a prerequisite for isolated Kraken research.
6. **Consumer integration (separate approval)** — any strategy/backtest use requires a market-semantics review and independent tests. Spot data is not approved as futures input by this document.

Each stage must have its own acceptance criteria and Codemagic evidence. Do not combine adapter implementation, schema migration, API changes, and consumer switching into one large PR.

## 6. Acceptance checklist for a future multi-source implementation

### Contract and identity
- [ ] A typed identity distinguishes exchange, market type, native market ID, canonical symbol, timeframe, and open time.
- [ ] Binance USD-M and Kraken Spot identities cannot collide or be confused.
- [ ] Existing Binance identity literals and API behavior remain backward-compatible until a separately approved migration.
- [ ] Unsupported or ambiguous market metadata fails closed.

### Adapter and normalization
- [ ] Each adapter validates the active native market and expected market type.
- [ ] M15/H1 timestamps are aligned, UTC, monotonic, and within the requested half-open window.
- [ ] Only closed candles are accepted.
- [ ] OHLCV decimal, OHLC bounds, volume units, and source-specific field semantics are tested.
- [ ] First-observed availability is immutable and is not backdated on historical re-sync.

### Storage and API isolation
- [ ] Kraken Spot writes cannot alter Binance rows or Binance dataset hashes.
- [ ] Same-source identical duplicates are idempotent; conflicting duplicates fail without overwriting existing rows.
- [ ] Read queries require explicit source/market selection.
- [ ] Coverage gaps remain visible and no rows are fabricated.
- [ ] Existing Binance /v1/candles contract remains compatible.
- [ ] No automatic source fallback or cross-market candle stitching exists.

### Evidence and operations
- [ ] Unit and integration tests run on Codemagic against isolated disposable storage.
- [ ] Live acceptance is manual and records the exact tested source SHA.
- [ ] Artifacts include machine-readable coverage, gaps, row counts, hashes, source metadata, and scope boundaries.
- [ ] Kraken evidence is never used to certify Binance USD-M availability or collection.
- [ ] No production migration, data deletion, live trading, or strategy-source switch occurs without separate explicit approval.

## 7. Explicit non-goals

This assessment does not authorize:

- Replacing Binance USD-M with Kraken Spot for futures strategies or paper trading.
- Changing market_data/store.py, current schema constraints, migrations, API response semantics, or environment variables.
- Writing Kraken rows into the existing Binance canonical database/table.
- Cross-source price blending, candle stitching, gap filling, or automatic failover.
- PostgreSQL/TimescaleDB production migration or cutover.
- Changes to strategy parameters, AI models, risk management, paper ledger, or live order execution.
- Running tests/builds outside Codemagic or claiming Codemagic validation without an actual run log.

## Review decision requested

Review this architecture boundary before implementation. The immediate safe state is: Binance USD-M remains the canonical futures source; Kraken Spot remains an isolated, independently accepted alternative dataset for research only.
