# T1 → T2 Schema Freeze v1.0.0

Date: 2026-11-12 (Asia/Ho_Chi_Minh)

Status: **SCHEMA FROZEN — T1 CSV COMPATIBILITY PROFILE + T2 INTERPRETATION v1.0.0**  
Implementation status: **NOT IMPLEMENTED**. This freeze defines the consumer contract; it does not claim that the current T1 producer publishes immutable batches/manifests or that T2 consumes them.

T1 source reviewed: `kenznguyen/binance-futures-collector`, branch `feature/t1-connection-sidecar-integration-20261107`, source SHA `53ffed3979429ed9f28529cf27d6e508f74ba6f2`.  
Main repository branch: `feature/t0-centralized-data-feeder-p1-20261101`.

## 1. Frozen architecture and compatibility boundary

1. T0 and T1 are independent producers and independent data assets.
2. T1 has **no path to T0**. No T1 → T0 transport, canonicalization, database write, or fallback is permitted.
3. T0 → T2 remains the existing read-only Candle Contract v1 path and is unchanged.
4. T2 consumes T0 and T1 through separate source adapters. T2 may join features only after source identity, event-time semantics, availability time, and provenance are preserved.
5. This contract is a read-only interpretation of the existing T1 CSV row formats at the reviewed source SHA. It does not rename, reorder, or add CSV columns to existing T1 files.
6. New T1 row fields or changed meanings require a new schema major version. A consumer must not infer a new schema from branch name, file name, or deployment version.
7. This freeze does not authorize producer edits, adapter implementation, manifest publisher, runtime, VPS, exchange connectivity, trading, or source-data deletion.

## 2. Versioning and manifest binding

The existing CSV rows do not contain a schema-version column. Therefore the future immutable batch manifest MUST bind each file to a schema version and subtype.

Frozen identifiers:

- Contract: `T1_T2_INGESTION_V1`
- Contract version: `1.0.0`
- Exchange: `binance`
- Existing CSV market literal: `futures` (preserve as-is)
- Manifest market identity: `BINANCE_USDM`
- Market scope: `USDT_M`
- Symbol representation: lowercase Binance symbol, e.g. `btcusdt`
- Encoding: UTF-8
- CSV dialect: RFC 4180-compatible, comma delimiter, double-quote escaping, header row required
- Timestamp unit: signed integer Unix milliseconds UTC

Each manifest file entry MUST include:

- `datatype`: exact CSV datatype value;
- `record_kind`: required only for `orderbooks`, one of `depth_updates` or `depth_snapshot`;
- `schema_version`: exact version from the table below;
- `timestamp_semantics`: exact enum from the table below;
- `timestamp_unit`: `unix_ms_utc`;
- `symbol`, `market_identity`, and `market_scope`;
- immutable file path, byte length, SHA-256, data-row count, first/last row timestamp;
- source repository, source SHA, build identity, collector session ID, batch ID;
- publication/seal time and producer-declared closure state;
- configured symbol-universe identity or its content digest;
- applicable gap/continuity evidence references.

No manifest or immutable-segment publisher currently exists in the reviewed T1 source. These are frozen future transport requirements, not claims about current files.

## 3. Common row envelope

Every row MUST have the existing six-column prefix in this exact order:

| Field | Frozen meaning and validation |
|---|---|
| `exchange` | Literal `binance` |
| `market` | Literal `futures`; do not reinterpret this field as a complete market identity |
| `datatype` | Exact datatype string and matching data directory |
| `timestamp_ms` | Signed 64-bit UTC Unix milliseconds; semantic depends on datatype |
| `datetime_utc` | ISO-8601 UTC rendering of the same instant, millisecond precision, trailing `Z`; MUST equal `timestamp_ms` |
| `symbol` | Lowercase symbol; MUST match manifest symbol and configured USDT-M universe |

Unknown datatype, unknown record kind, header mismatch, duplicate header names, missing required columns, malformed CSV quoting, invalid UTF-8, or envelope mismatch is a hard reject. Parse CSV with a standards-compatible parser; never split rows on commas manually.

## 4. Decimal lexical and arithmetic contract

### 4.1 Accepted lexical form

All market prices, quantities, rates, ratios, volumes, and notionals remain decimal strings from source through T2 persistence. T2 MUST NOT route them through IEEE-754 `f32` or `f64`.

Accepted lexical grammar (ASCII):

```regex
^[+-]?(?:[0-9]+(?:\\.[0-9]*)?|\\.[0-9]+)(?:[eE][+-]?[0-9]+)?$
```

Resource bounds for T2 parsing:

- maximum token length: 256 bytes;
- maximum total mantissa digits: 128;
- maximum absolute exponent: 64;
- maximum effective fractional scale after exponent application: 128;
- reject whitespace, separators, NaN, Infinity, hex, locale-specific notation, and trailing characters.

Preserve the original lexeme. Normalization may be used only for exact numeric comparison/keying and MUST NOT overwrite the stored source string. A malformed decimal is rejected; it is never converted to zero, null, or an empty string.

### 4.2 Arithmetic

- Use arbitrary-precision decimal/integer arithmetic.
- Exact multiplication retains the combined decimal scale; no rounding is applied in v1.
- Do not recompute exchange-provided ratios as a replacement for their source values.
- Where a derived field is checked against operands, compare exact numeric values and preserve both original operands and the original derived lexeme.
- No implicit precision truncation or rounding mode is permitted. Any future rounding rule requires a versioned schema change.

## 5. Frozen datatype schemas

The headers below are exact data columns after the common envelope. They reflect the T1 CSV writer/header definitions at the reviewed source SHA.

### 5.1 `orderbooks` / `depth_updates`

Header suffix: `first_update_id,last_update_id,prev_update_id,bids_json,asks_json`  
Timestamp semantic: `EVENT_TIME` (WebSocket event time `E`).  
Schema version: `1.0.0`.

- `first_update_id`, `last_update_id`, `prev_update_id`: unsigned 64-bit integers; require `first_update_id <= last_update_id`.
- `bids_json`, `asks_json`: JSON arrays of two-element string tuples `[price, absolute_quantity]`; validate every decimal lexeme. Quantity zero removes that price level. These are absolute replacement quantities, not deltas to add.
- Stable event identity: `(exchange, market, symbol, first_update_id, last_update_id)`. Same identity with conflicting content is a hard conflict.
- Sort/replay by update IDs, not timestamp alone.
- Continuity after an established anchor requires `prev_update_id == previous.last_update_id`. Initial snapshot bridge rules may establish the first anchor; they do not excuse later chain breaks.
- Any chain break marks the affected interval `GAPPED`; do not silently interpolate or backfill. Binance does not replay missed depth diffs.
- The manifest `record_kind=depth_updates` disambiguates this file from snapshots without changing the existing row `datatype=orderbooks`.

### 5.2 `orderbooks` / `depth_snapshot`

Header suffix: `event_type,side,price,quantity,last_update_id`  
Timestamp semantic: `SNAPSHOT_TIME`.  
Schema version: `1.0.0`.

- `event_type`: `depth_snapshot_initial`, `depth_snapshot_bridge`, or `depth_snapshot`.
- `side`: `bid` or `ask`.
- `price`, `quantity`: exact decimal strings; `last_update_id`: unsigned 64-bit integer.
- One row represents one price level. Rows in one snapshot group share symbol, timestamp, event type, and update ID.
- Frozen row-group locator: immutable source file SHA-256 plus the contiguous one-based CSV data-row range for that snapshot group. Within a file, a group is a contiguous run with identical `(timestamp_ms,event_type,last_update_id)`. T2 MUST reject an ambiguous/non-contiguous grouping rather than merge separated runs.
- A missing side means that side has no emitted levels. A file with no rows cannot represent an empty snapshot.
- `depth_snapshot_initial` is the initial REST snapshot; `depth_snapshot_bridge` is the post-bridge book; `depth_snapshot` is periodic in-memory re-serialization, not a fresh REST snapshot.
- Periodic snapshots are not independently proven correct after a WebSocket continuity break. They MUST NOT restore a trusted reconstruction state after a known gap unless a separately validated anchor is available.
- The manifest `record_kind=depth_snapshot` distinguishes this subtype while retaining `datatype=orderbooks`.

### 5.3 `trades`

Header suffix: `trade_id,side,price,quantity,is_buyer_maker,first_update_id,last_update_id`  
Timestamp semantic: `TRADE_TIME` (Binance aggTrade `T`).  
Schema version: `1.0.0`.

- `trade_id` is the aggregate trade ID; it is the stable per-symbol identity.
- `first_update_id` and `last_update_id` are legacy column names for aggTrade `f` and `l` (first/last underlying trade IDs), NOT order-book update IDs. Keep the names unchanged in v1.
- `side` is aggressor side: `buy` or `sell`.
- `is_buyer_maker` is integer `0` or `1`; `1` corresponds to aggressor `sell`, `0` to aggressor `buy`.
- Require `first_update_id <= last_update_id`.
- Stable identity: `(exchange, market, symbol, trade_id)`. Exact duplicate replay is idempotent; conflicting content for the same identity is a hard conflict.

### 5.4 `klines`

Header suffix: `open,high,low,close,volume,quote_volume,trade_count,taker_buy_base,taker_buy_quote`  
Timestamp semantic: `BAR_OPEN_TIME`.  
Schema version: `1.0.0`.

- Native interval: `1m`, bound by manifest metadata.
- `timestamp_ms` is candle open time. Frozen interval is half-open `[open_time, open_time + 60_000)`; derived close timestamp is `open_time + 59_999` inclusive.
- T1 writes only WebSocket klines whose exchange `x` flag declares the bar closed. The manifest must attest the closed-bar policy; consumers must not infer closure solely from wall-clock time.
- Stable identity: `(exchange, market, symbol, interval, open_time_ms)`.
- OHLC and volumes are decimal strings; `trade_count` is a nonnegative integer. Validate `high >= max(open,close,low)`, `low <= min(open,close,high)`, and nonnegative volume fields using exact arithmetic.

### 5.5 `liquidations`

Header suffix: `side,price,quantity,value`  
Timestamp semantic: `EVENT_TIME` (forceOrder event `E`, as persisted by T1).  
Schema version: `1.0.0`.

- `side`: `buy` or `sell`; price, quantity, value are exact decimal strings.
- `value` is producer-derived `price × quantity`; validate with exact multiplication and no rounding.
- The wire order execution time `T` is not persisted in the current CSV and MUST NOT be inferred from `timestamp_ms`.
- The market-wide force-order stream is filtered to the collector's configured USDT-M symbol universe. This dataset is not a complete global liquidation tape. Manifest MUST bind the configured symbol-universe identity/digest.
- **No stable exchange event/order ID is present in the persisted row.** Therefore v1 does not define semantic cross-batch row deduplication. Use immutable batch/file digest plus one-based row ordinal as the ingestion locator. Batch replay is idempotent; do not deduplicate solely on a guessed composite of timestamp/side/price/quantity. A future producer schema may add a source event identity under a new major version.

### 5.6 `funding_rates`

Header suffix: `funding_rate,next_funding_time`  
Timestamp semantic: `OBSERVATION_TIME` (collector observation/poll time generated locally).  
Schema version: `1.0.0`.

- `funding_rate`: exact decimal string.
- `next_funding_time`: signed 64-bit UTC Unix milliseconds for the next settlement.
- This is a periodically sampled observation, not a complete funding-payment event stream. Absence is a gap, never zero.
- Stable observation identity: `(exchange, market, symbol, timestamp_ms)`. Repeated observations at different poll times are distinct.

### 5.7 `open_interest`

Header suffix: `mark_price,open_interest,oi_value`  
Timestamp semantic: `SAMPLE_TIME` (the OI endpoint's `time`).  
Schema version: `1.0.0`.

- `mark_price`, `open_interest`, `oi_value`: exact decimal strings.
- `oi_value` is producer-derived as `open_interest × mark_price`, using exact multiplication and combined scale (no rounding).
- **Important limitation:** the mark price is fetched separately from the OI response, and its own timestamp is not persisted. Therefore `oi_value` is an indicative derived notional, not a strictly time-aligned exchange observation. T2 MUST preserve this qualification and MUST NOT label it an exact point-in-time notional.
- Stable observation identity: `(exchange, market, symbol, timestamp_ms)`. Do not assume separate mark-price sampling happened at precisely the OI timestamp.

### 5.8 `long_short_ratio`

Header suffix: `period,ratio_type,long_ratio,short_ratio,long_short_ratio`  
Timestamp semantic: `BUCKET_START_TIME`.  
Schema version: `1.0.0`.

- Current native period: `5m`; timestamp is the source bucket start.
- `ratio_type`: `global`, `top_trader_account`, or `top_trader_position`.
- Ratios remain exact source decimal strings. T1 omits a row if source long/short account fields are missing; absence is not zero.
- The three ratio values are source-reported values. v1 does not recompute `long_short_ratio` or enforce a tolerance-based equation because no producer rounding/tolerance contract is present.
- Stable identity: `(exchange, market, symbol, period, ratio_type, bucket_start_ms)`.

### 5.9 `taker_buy_sell_ratio`

Header suffix: `period,buy_volume,sell_volume,buy_sell_ratio`  
Timestamp semantic: `BUCKET_START_TIME`.  
Schema version: `1.0.0`.

- Current native period: `5m`; timestamp is the source bucket start.
- Volumes and ratio remain exact source decimal strings.
- `buy_sell_ratio` is the exchange-reported value; v1 does not recompute it or invent a divide-by-zero result. A zero sell volume is retained as a valid volume observation if the source row provides it; the source ratio is preserved unchanged.
- Stable identity: `(exchange, market, symbol, period, bucket_start_ms)`.

### 5.10 `mark_price_klines`, `index_price_klines`, `premium_index_klines`

Header suffix: `open,high,low,close`  
Timestamp semantic: `BAR_OPEN_TIME`.  
Schema version: `1.0.0` for each distinct datatype.

- Native interval: `1m`, bound by manifest metadata.
- Each datatype is a separate price series; never merge with traded-price `klines`.
- Timestamp interval is half-open `[open_time, open_time + 60_000)`; derived inclusive close timestamp is `open_time + 59_999`.
- T1 currently excludes the final returned (in-progress) REST bucket. This is producer behavior, not row-level proof of closure. The manifest must attest the closure policy and source endpoint/series.
- OHLC values remain exact decimals; validate OHLC ordering using exact arithmetic.
- Stable identity: `(exchange, market, symbol, datatype, interval, open_time_ms)`.

## 6. Timestamp and point-in-time rules

Frozen timestamp enum mapping:

| Datatype / record kind | `timestamp_semantics` |
|---|---|
| orderbooks / depth_updates | `EVENT_TIME` |
| orderbooks / depth_snapshot | `SNAPSHOT_TIME` |
| trades | `TRADE_TIME` |
| klines | `BAR_OPEN_TIME` |
| liquidations | `EVENT_TIME` |
| funding_rates | `OBSERVATION_TIME` |
| open_interest | `SAMPLE_TIME` |
| long_short_ratio | `BUCKET_START_TIME` |
| taker_buy_sell_ratio | `BUCKET_START_TIME` |
| mark/index/premium klines | `BAR_OPEN_TIME` |

Ingestion/observation time MUST be a separate manifest/consumer field and must never overwrite the source timestamp. Training/inference joins use point-in-time availability: a datum is eligible only if it was available by the decision cutoff. No nearest-timestamp join without a separately versioned tolerance and availability rule. Late arrivals create a dataset revision; they do not silently rewrite prior training examples.

## 7. Quality, gaps, identity, and replay

Keep four independent states:

1. `transport_integrity`: manifest/file digest, byte length, and row count match;
2. `schema_validity`: exact header, row types, decimal grammar, timestamps, and datatype invariants pass;
3. `market_data_completeness`: datatype-specific coverage and continuity checks pass or gaps are explicitly recorded;
4. `consumer_persisted`: T2 accepted rows, provenance, and checkpoint are durably committed.

No state implies another. In particular, a valid file digest does not prove market-data completeness.

Delivery semantics: at-least-once with idempotent batch ingestion. The durable checkpoint is committed atomically with accepted rows. Same batch ID + same digest is replay/no-op; same batch ID + different digest is a hard conflict. Liquidation row locator is file digest + row ordinal because source event identity is unavailable in v1.

Order-book continuity is assessed independently from transport integrity. A complete raw file may faithfully contain an exchange-stream gap. T2 marks the affected interval `GAPPED` and does not synthesize missing diffs. A periodic in-memory snapshot is not automatically a trusted recovery anchor after a gap.

Missing rows/buckets are represented as gaps/absence with explicit coverage evidence, never numeric zero. Filtered liquidations and other market-wide feeds must carry their configured universe provenance.

## 8. Frozen schema registry

| Datatype | Record kind | Version | Timestamp semantics | Identity / key | v1 disposition |
|---|---|---:|---|---|---|
| orderbooks | depth_updates | 1.0.0 | EVENT_TIME | symbol + U + u | FROZEN; chain quality separate |
| orderbooks | depth_snapshot | 1.0.0 | SNAPSHOT_TIME | file digest + contiguous row range; rows by side/price | FROZEN; periodic snapshot best-effort |
| trades | — | 1.0.0 | TRADE_TIME | symbol + trade_id | FROZEN |
| klines | — | 1.0.0 | BAR_OPEN_TIME | symbol + 1m + open time | FROZEN; closure attestation required |
| liquidations | — | 1.0.0 | EVENT_TIME | file digest + row ordinal | FROZEN; no semantic event dedup |
| funding_rates | — | 1.0.0 | OBSERVATION_TIME | symbol + observation time | FROZEN |
| open_interest | — | 1.0.0 | SAMPLE_TIME | symbol + OI sample time | FROZEN; indicative notional limitation |
| long_short_ratio | — | 1.0.0 | BUCKET_START_TIME | symbol + period + type + bucket | FROZEN |
| taker_buy_sell_ratio | — | 1.0.0 | BUCKET_START_TIME | symbol + period + bucket | FROZEN |
| mark_price_klines | — | 1.0.0 | BAR_OPEN_TIME | symbol + 1m + open time | FROZEN; closure attestation required |
| index_price_klines | — | 1.0.0 | BAR_OPEN_TIME | symbol + 1m + open time | FROZEN; closure attestation required |
| premium_index_klines | — | 1.0.0 | BAR_OPEN_TIME | symbol + 1m + open time | FROZEN; closure attestation required |

## 9. Change control

- Additive optional metadata may be introduced only when old consumers safely ignore it and the manifest contract explicitly allows it.
- Changing a field name/type/meaning, timestamp semantic, identity rule, decimal grammar, row grouping, or arithmetic rule requires a new major schema version.
- A new datatype or record kind requires a registry entry and exact-source producer evidence before acceptance.
- No consumer fallback to T0, exchange APIs, dashboard float endpoints, synthetic values, or another venue is permitted.
- Producer schema migration and T2 adapter implementation remain separate approval/work items. This freeze alone is not implementation authorization.

## 10. Verification and limits

This freeze is based on read-only inspection of T1 source/documentation at SHA `53ffed3979429ed9f28529cf27d6e508f74ba6f2`, including `src/models.rs`, `src/constants.rs`, `src/collectors/rest_collector.rs`, `src/collectors/orderbook_manager.rs`, `src/utils/csv_writer.rs`, `src/utils/decimal.rs`, `docs/SCHEMA.md`, and `docs/ORDERBOOK.md`.

No producer code was changed. No adapter, manifest publisher, runtime, VPS, exchange connection, or trading was activated. No tests were run because this increment freezes the consumer-facing schema contract only. The existing producer does not yet provide immutable sealed batches, row-level schema versions, snapshot IDs, liquidation event IDs, or timestamped mark-price provenance for OI; the contract explicitly defines safe consumer behavior around these limitations.

### Final status

- T1 CSV compatibility schema v1.0.0: **FROZEN**
- Datatype registry and timestamp semantics: **FROZEN**
- Decimal/CSV parsing rules: **FROZEN**
- Row identity, snapshot grouping, gap/replay policy: **FROZEN**
- Producer conformance to future manifest/sealed-batch requirements: **NOT VERIFIED / NOT IMPLEMENTED**
- T1 → T2 adapter: **NOT IMPLEMENTED**
- T0 → T2 Candle Contract v1: **UNCHANGED**
- T1 → T0: **PROHIBITED / NO PATH**
- Runtime and trading: **NOT AUTHORIZED**
