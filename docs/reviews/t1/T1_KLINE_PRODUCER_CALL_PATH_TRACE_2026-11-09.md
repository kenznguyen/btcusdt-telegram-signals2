# T1 Kline Producer Call-Path Trace — Contract v1.1 Blocking Evidence

Date: 2026-11-09
Reviewed T1 source revision: 6e20fe94f3ad64cc450e73def80a167fe371e49e
Status: STATIC SOURCE TRACE COMPLETE / LOSSLESS DECIMAL REQUIREMENT BLOCKED

## 1. Scope

Trace the actual Binance kline WebSocket path through deserialization, message handling, model conversion and CSV serialization. This is a read-only review of the pinned source revision. No source code or runtime was changed.

## 2. Source evidence

| File | Blob SHA | Observed behavior |
|---|---|---|
| src/models.rs | 993419725268d1308645e3a37c15e9779a9e92cc | KlineData receives OHLCV and taker volumes as String; includes is_closed bool from WebSocket x. KlineCsv does not include is_closed. |
| src/websocket/message_handler.rs | 7d7f221fbf4b31470049baea55584645352f61b7 | process_kline returns immediately when is_closed is false; only closed kline events are sent to write_kline. It formats all numeric source strings through format_decimal_str before constructing KlineCsv. |
| src/utils/csv_writer.rs | 2c4538dcef7dfa758a854292031239c15f7c282b | write_kline parses each numeric string as f64 and formats to exactly 12 decimal places before writing CSV. Parse failure uses unwrap_or(0.0). |
| src/collectors/symbol_discovery.rs | 34e453cbb96d5964d1f58e204bbfbe147041ced6 | Symbol discovery requires TRADING, PERPETUAL, rejects PREMARKET and requires quote_asset=USDT; the source exchange metadata model exposes symbol, status, base_asset, quote_asset, underlying_type and contract_type. |
| src/constants.rs | 0bf50b5fe02f4f196b38481cde6ecab9e2adb941 | Persisted generic market label is futures. |

## 3. Critical finding: current CSV path is not lossless

The writer explicitly performs parse::<f64>() and formats every kline decimal to 12 fractional digits. On parse failure it substitutes 0.0. This proves that the current CSV path does not preserve original Binance decimal strings byte-for-byte and can silently turn malformed numeric text into zero.

Consequences:
- Exact source decimal provenance is lost before the adapter reads the file.
- Values with meaningful precision beyond 12 fractional digits may be rounded.
- Binary floating-point conversion can change decimal values even when the source has fewer than 12 decimal places.
- A parse failure is not surfaced as a row error; it may be serialized as a plausible zero.
- No downstream decimal library or adapter can reconstruct the discarded original source text.

Disposition: R3 is CONFIRMED as a current producer defect relative to the proposed lossless contract. Producer-only source correction and regression tests are mandatory before this source can be considered for exact aggregation. Do not weaken the contract to accept the rounded CSV output.

## 4. Clarification: final-only source behavior

The WebSocket model receives the x/is_closed flag. message_handler::process_kline rejects every event with is_closed=false before constructing KlineCsv or calling write_kline. Therefore the currently persisted klines stream is intended to be final-only, not a record of every interim update.

However:
- KlineCsv and HEADER_KLINES do not persist an explicit finality field or a versioned final-only declaration.
- The adapter cannot establish this property from CSV bytes alone.
- The producer must make final-only semantics explicit in a versioned manifest (for example output_mode=FINAL_ONLY and interval=1m), and regression tests must prove provisional events never reach the writer. Alternatively, persist is_closed=true explicitly in v1 rows.
- This finding refines the earlier proposal: preserving every interim update is not required for the first canonical 1m adapter if the approved source contract deliberately defines a final-only feed. The source must still prove finality.

## 5. Product identity evidence refinement

The inspected ExchangeInfoSymbol model includes symbol, status, base_asset, quote_asset, underlying_type and contract_type. The symbol discovery path checks TRADING, PERPETUAL, excludes PREMARKET, and requires quote_asset=USDT. This supports a concrete source for eligibility fields. The generic market=futures label remains insufficient by itself; the manifest must bind the source endpoint family/configuration and the exact exchange metadata record/snapshot used.

The actual exchange-info response does not expose margin_asset in the inspected model. Do not make it a mandatory field unless a separately verified authoritative source is identified. The v1.1 design already marks it conditional.

## 6. Required contract v1.1 amendments

1. Keep R3 blocked until writer serialization no longer parses through f64 and no longer substitutes zero on parse failure.
2. Add tests proving raw decimal preservation and malformed decimal rejection at the producer boundary.
3. Explicitly choose final-only semantics for this feed, with versioned manifest declaration and tests, or persist is_closed=true per row. Do not infer finality from current code revision at runtime.
4. Record that source metadata can provide status, contract_type, base_asset, quote_asset and underlying_type; retain explicit source endpoint family to distinguish USD-M.
5. No adapter implementation, T0/T2 promotion or runtime activation until producer changes and evidence are separately approved and verified.

## 7. Guardrails and final status

Read-only static trace only. No code edits, tests, CI dispatch, VPS/runtime, T0/T1 data, strategy/risk changes, live orders or destructive operations.

**R3 BLOCKED BY CONFIRMED FLOAT CONVERSION / LOSSY SERIALIZATION. Final-only semantics identified but require explicit versioned contract and producer regression evidence.**

The v1.1 design remains a draft and requires revision plus independent review.