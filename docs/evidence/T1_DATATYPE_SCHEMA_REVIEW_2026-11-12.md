# T1 Datatype Schema Review — T1 → T2 Proposal

Date: 2026-11-12
T1 repository: `kenznguyen/binance-futures-collector`
T1 branch: `feature/t1-connection-sidecar-integration-20261107`
T1 source reviewed: `53ffed3979429ed9f28529cf27d6e508f74ba6f2`

Status: **READ-ONLY REVIEW / PROPOSAL. NOT OWNER-APPROVED. NOT A FROZEN CONTRACT. NO SOURCE CHANGES.**

## 1. Architectural boundary

- T0 and T1 remain independent data assets and producers.
- T1 does not feed T0. No T1 → T0 transport, canonicalization or write path is proposed.
- T0 → T2 remains the existing read-only Candle Contract v1.
- T1 → T2 requires a separate adapter and separate ingestion contract.
- This review does not authorize runtime activation, VPS, live Binance, strategy changes, or real orders.

## 2. Common row envelope currently documented

The T1 CSV schema documents these six common columns:

| Field | Current documented meaning | Review |
|---|---|---|
| exchange | `binance` | Keep literal and validate |
| market | `futures` | Clarify explicitly as USDⓈ-M / USDT-M, not generic futures |
| datatype | Data type matching directory | Keep, but distinguish order-book record subtype |
| timestamp_ms | UTC milliseconds | Preserve; semantics are datatype-specific |
| datetime_utc | ISO-8601 UTC rendering of timestamp_ms | Redundant derived field; validate exact equivalence |
| symbol | Lowercase symbol | Validate against explicit symbol format and instrument identity |

The current CSV rows do not carry a schema version. Proposed batch manifest must therefore bind each immutable segment to an explicit datatype schema version. Do not infer schema version from the current branch or filename.

## 3. Datatype-by-datatype review

### 3.1 Order-book depth diffs

Current row fields: common envelope + `first_update_id`, `last_update_id`, `prev_update_id`, `bids_json`, `asks_json`.

- Timestamp semantic: EVENT_TIME.
- Ordering identity: update ID chain, not timestamp alone.
- Each bid/ask JSON entry is an exact decimal-string pair [price, absolute quantity].
- Quantity zero removes a level.
- Continuity requires the declared bridge rule and subsequent `prev_update_id` chain.
- A reconnect can produce a detectable continuity break. T1 records diffs received; it does not guarantee every exchange diff was received across a disconnect.

Proposed validation:
- IDs are unsigned integers; require internally consistent update ranges.
- JSON must parse as arrays of two-string tuples.
- Price and quantity must pass strict decimal lexical validation; no binary float conversion.
- Preserve row order and update IDs.
- Any unanchored or discontinuous interval is marked invalid/untrusted until a valid snapshot re-anchors it.

Open decision: confirm whether the T1 producer's canonical datatype field remains `orderbooks` while `record_kind` distinguishes `depth_updates` and `depth_snapshot`. Current constants define `DATATYPE_ORDERBOOKS = "orderbooks"`, while documentation describes the two record kinds separately. The proposed manifest must not silently invent two new datatype values.

### 3.2 Order-book snapshots

Current row fields: common envelope + `event_type`, `side`, `price`, `quantity`, `last_update_id`.

- Timestamp semantic: SNAPSHOT_TIME.
- One row per price level.
- `event_type`: initial REST snapshot, bridge snapshot, or periodic re-serialization.
- Periodic snapshots are serialized from the in-memory book; they are not necessarily fresh REST snapshots.
- `last_update_id` identifies the book version.

Proposed validation:
- `event_type` and `side` are strict enums.
- Price/quantity remain decimal strings.
- All rows belonging to one snapshot share the same snapshot identity/time and update ID.
- Batch envelope needs a snapshot grouping key; current row schema has no explicit snapshot_id.
- Empty-side/empty-book representation must be specified (zero rows alone is ambiguous).

Open decision: introduce a stable `snapshot_id` / `snapshot_group_id` in a future schema version, or define a deterministic grouping rule that does not rely only on timestamp and event type.

### 3.3 Aggregated trades

Current row fields: common envelope + `trade_id`, `side`, `price`, `quantity`, `is_buyer_maker`, `first_update_id`, `last_update_id`.

- Timestamp semantic: TRADE_TIME.
- `trade_id` is the aggregate trade ID.
- `first_update_id` / `last_update_id` are documented legacy/misnomer names for aggTrade first/last trade IDs, not order-book update IDs.
- Side is aggressor side; `is_buyer_maker` must be consistent with side derivation.

Proposed validation:
- Dedup identity: (exchange, market, symbol, trade_id).
- IDs are nonnegative integers; first trade ID <= last trade ID.
- Validate side enum and boolean encoding (0/1).
- Exact decimal strings for price and quantity.
- Timestamps and aggregate IDs are not interchangeable ordering keys.

Open decision: retain legacy field names for backward compatibility in schema v1 and introduce clearer names only in a versioned future schema; do not silently rename.

### 3.4 1-minute klines

Current row fields: common envelope + OHLC, base volume, quote volume, trade count, taker-buy base and quote volumes.

- Timestamp semantic: BAR_OPEN_TIME.
- Producer code skips the final in-progress bucket and writes closed bars.
- Native interval is 1m.

Proposed validation:
- Unique key: (exchange, market, symbol, interval, open_time); interval is currently implicit in datatype and should be explicit in manifest/schema metadata.
- Validate OHLC relationships and nonnegative volumes/counts using decimal-safe comparisons.
- Preserve decimal lexemes.
- A closed-bar assertion requires producer evidence; consumer must not infer closure only from wall-clock time.

Open decision: define how close time / interval boundary is derived and represented; current row schema carries only open timestamp.

### 3.5 Liquidations

Current row fields: common envelope + side, price, quantity, value.

- Timestamp semantic: EVENT_TIME.
- Source is market-wide forceOrder; collector filters to its configured USDT-M symbol universe.
- Value is price × quantity.

Proposed validation:
- Validate side enum and exact decimals.
- Define whether `value` is producer-computed from exact decimal operands and whether T2 recomputes/compares it.
- Record source stream scope and market filter provenance in manifest.
- Do not interpret this as a complete liquidation tape for symbols outside the collector universe.

Open decision: event identity/deduplication key. Current documented CSV row does not show a stable liquidation order/event ID. Need inspect exact source model/wire fields before freezing idempotent row-level dedup.

### 3.6 Funding rates

Current row fields: common envelope + funding_rate, next_funding_time.

- Timestamp semantic: SAMPLE_TIME.
- `next_funding_time` is a separate UTC millisecond settlement timestamp.
- Current polling is periodic; this is a sampled observation, not a complete event stream.

Proposed validation:
- Decimal-string funding rate.
- Integer UTC-ms next funding time.
- Keep sample timestamp distinct from settlement timestamp.
- Record sampling cadence and gaps; do not treat absent samples as zero.

Open decision: instrument/funding interval identity and behavior around settlement boundaries.

### 3.7 Open interest

Current row fields: common envelope + mark_price, open_interest, oi_value.

- Timestamp semantic: SAMPLE_TIME.
- `open_interest` is base units; `oi_value` is quote terms.
- `oi_value` is derived using open_interest × mark_price.

Proposed validation:
- Exact decimal strings for all numeric values.
- Verify `oi_value` against exact decimal multiplication under a documented scale/rounding rule, or mark producer-derived value as opaque and preserve provenance.
- Distinguish sampling time from mark-price candle time.

Open decision: exact multiplication/scale semantics for oi_value must be specified before acceptance.

### 3.8 Long/short ratios

Current row fields: common envelope + period, ratio_type, long_ratio, short_ratio, long_short_ratio.

- Timestamp semantic: BUCKET_START_TIME.
- Current collector writes period `5m`.
- ratio_type enum: global, top_trader_account, top_trader_position.
- Missing source long/short account values are skipped rather than fabricated.

Proposed validation:
- Strict period and ratio_type enums/allowlists.
- Decimal-string ratios; validate allowed numeric range and ratio relationship with exact-decimal arithmetic.
- Explicit missing-bucket/gap evidence; missing records are not zero.
- Include endpoint/series identity in schema metadata.

Open decision: define ratio tolerance/rounding consistency and the exact meaning of bucket timestamp as source period start.

### 3.9 Taker buy/sell ratios

Current row fields: common envelope + period, buy_volume, sell_volume, buy_sell_ratio.

- Timestamp semantic: BUCKET_START_TIME.
- Current collector writes period `5m`.

Proposed validation:
- Strict period; decimal strings.
- Validate nonnegative volumes and ratio using exact-decimal arithmetic with explicit divide-by-zero behavior.
- Preserve missing buckets as gaps, not zeros.

Open decision: define ratio precision/rounding and zero sell-volume semantics.

### 3.10 Mark-price, index-price and premium-index klines

Current row fields: common envelope + OHLC.

- Timestamp semantic: BAR_OPEN_TIME.
- Native interval: 1m.
- Producer skips the final in-progress bucket for mark/index/premium klines.

Proposed validation:
- Treat each datatype as a distinct price series; never merge them into ordinary traded-price klines.
- Unique key includes datatype, symbol, interval and open time.
- Decimal-safe OHLC consistency validation.
- Closed-bar evidence required.

Open decision: represent interval explicitly in manifest/schema metadata and define the close boundary.

## 4. Cross-cutting issues before schema freeze

1. **Schema versioning:** absent from row-level CSV; add immutable manifest binding and explicit per-datatype schema version.
2. **Order-book subtype:** constants use `orderbooks`, while docs distinguish `depth_updates` and `depth_snapshot`; define `record_kind` without breaking existing datatype identity.
3. **Snapshot grouping:** no explicit snapshot ID; grouping semantics need definition.
4. **CSV correctness:** consumer must use an RFC 4180-compatible parser. Naive comma splitting is invalid for JSON arrays containing commas and quoted fields.
5. **Decimal grammar:** define accepted lexical grammar, exponent/sign policy, scale limits and rejection behavior. Preserve source lexemes; never parse through binary float.
6. **Time semantics:** manifest must declare per-datatype timestamp semantic and separately record ingestion/observation time.
7. **Identity/dedup:** define stable keys per datatype. Liquidation identity is not yet established from the reviewed schema.
8. **Coverage semantics:** distinguish transport integrity, schema validity, and market-data completeness. A collector's received raw tape may still contain exchange-stream gaps.
9. **Derived numeric fields:** define exact arithmetic/rounding for liquidation value, OI value and ratios.
10. **Universe scope:** record configured symbol universe and market scope; filtered market-wide streams are not global coverage.

## 5. Proposed schema freeze matrix

| Datatype / record kind | Timestamp semantic | Proposed stable row identity | Freeze status |
|---|---|---|---|
| orderbooks / depth_updates | EVENT_TIME + update IDs | symbol + update ID range | BLOCKED: subtype and chain rules |
| orderbooks / depth_snapshot | SNAPSHOT_TIME | symbol + snapshot group + level | BLOCKED: snapshot group identity |
| trades | TRADE_TIME | symbol + aggregate trade ID | CONDITIONAL: legacy ID names documented |
| klines | BAR_OPEN_TIME | symbol + interval + open time | CONDITIONAL: interval/closed-bar evidence |
| liquidations | EVENT_TIME | NOT ESTABLISHED | BLOCKED: event identity |
| funding_rates | SAMPLE_TIME | symbol + sample time | CONDITIONAL: sampling semantics |
| open_interest | SAMPLE_TIME | symbol + sample time | BLOCKED: derived value arithmetic |
| long_short_ratio | BUCKET_START_TIME | symbol + period + ratio_type + bucket start | CONDITIONAL: ratio semantics |
| taker_buy_sell_ratio | BUCKET_START_TIME | symbol + period + bucket start | CONDITIONAL: ratio/zero denominator |
| mark_price_klines | BAR_OPEN_TIME | symbol + interval + open time | CONDITIONAL: interval/closed-bar evidence |
| index_price_klines | BAR_OPEN_TIME | symbol + interval + open time | CONDITIONAL: interval/closed-bar evidence |
| premium_index_klines | BAR_OPEN_TIME | symbol + interval + open time | CONDITIONAL: interval/closed-bar evidence |

This matrix is a review disposition, not an approval to change the producer schema. Existing field names and file formats remain unchanged pending owner decisions.

## 6. Recommended order to resolve open decisions

1. Resolve order-book datatype vs record_kind, snapshot grouping, and continuity semantics.
2. Resolve trade and liquidation event identity/dedup keys.
3. Resolve candle interval/closed-bar semantics.
4. Resolve exact arithmetic/rounding for derived fields and ratios.
5. Freeze decimal lexical grammar and CSV parser requirements.
6. Freeze manifest schemaVersion mapping and source-universe provenance.
7. Only after explicit owner approval, write contract tests (RED first) and implement the adapter/manifest publisher on existing branches.

## 7. Evidence and limitations

Reviewed T1 source paths:
- `docs/SCHEMA.md`
- `docs/ARCHITECTURE.md`
- `docs/ORDERBOOK.md`
- `src/constants.rs`
- `src/models.rs`
- `src/collectors/rest_collector.rs`
- `src/utils/csv_writer.rs`

This is a static source/documentation review, not runtime validation or a complete audit of every collector path. The exact T1 source SHA is recorded above. No tests were run in this design-only increment.

## 8. Explicit non-goals

- No T1 → T0 path.
- No changes to T0 → T2 Candle Contract v1.
- No T1 producer/schema/dashboard/sidecar code changes.
- No T2 adapter implementation.
- No VPS, live Binance connection, runtime activation, model training, or real orders.
- No strategy, ledger, Shared Risk Engine or Kill Switch changes.
- No data deletion, retention, cleanup, compaction or raw-file mutation.
- No branch/PR creation, merge, or branch divergence.
