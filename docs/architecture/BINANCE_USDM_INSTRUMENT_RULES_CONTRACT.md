# Binance USD-M Instrument Rules Contract

**Status:** DESIGN CONTRACT PROPOSAL — GREEN-0 DOCUMENTATION ONLY  
**Date:** 2026-11-11  
**Instrument scope:** Binance USD-M BTCUSDT perpetual only  
**Authority:** owner-approved AI Strategy Contract and AI Strategy API Contract Proposal

## 1. Purpose and non-goals

Define the requirements for a future read-only provider that obtains authoritative exchange trading filters and supplies versioned BTCUSDT instrument rules to paper-order validation and sizing.

This document does not implement an adapter, make a network request, change the existing connectivity probe, submit orders, connect an execution client or activate trading. Binance USD-M `/fapi/v1/exchangeInfo` is a candidate upstream source identified during repository inspection; this contract does not claim the endpoint has been called or its current response independently verified in this work.

## 2. Source and scope

Candidate upstream:
- Public Binance USD-M exchange information endpoint: `/fapi/v1/exchangeInfo`.
- Select exactly the `BTCUSDT` symbol entry.
- Require the expected USD-M perpetual contract identity and active trading status before treating its filters as eligible for new paper ENTRY admission.

Do not use:
- order-book depth/precision as a substitute for exchange filters;
- configured decimal-place guesses;
- spot-market filters;
- values copied from old fixtures or hard-coded constants;
- a fallback to another exchange or instrument.

The adapter must be read-only and require no exchange API key for this public metadata endpoint.

## 3. Logical instrument-rules object

The future normalized object should include, at minimum:

| Field | Required meaning |
|---|---|
| `schema_version` | Normalized contract schema version |
| `source` / `endpoint` | Exact exchange metadata source |
| `symbol` | Must equal BTCUSDT |
| `contract_type` | Must match expected USD-M perpetual contract |
| `status` | Must permit new order admission |
| `base_asset` / `quote_asset` / `margin_asset` | Expected BTC/USDT contract identity |
| `price_tick_size` | Tick increment and explicit enabled/disabled state from applicable price filter |
| `quantity_step_size` | Positive quantity increment from applicable lot filter |
| `min_quantity` / `max_quantity` | Applicable quantity bounds |
| `min_notional` | Applicable minimum notional constraint, with its source filter semantics |
| `market_quantity_step_size` / bounds | Market-lot constraints if market orders are ever in scope |
| `exchange_precision` | Retained as descriptive metadata only; not a replacement for filters |
| `observed_at` | Local UTC observation time |
| `exchange_update_time` | Exchange-provided update time if present; absence must be explicit |
| `canonical_digest` | Digest of deterministic normalized rules |
| `source_payload_digest` | Digest of exact source response bytes when available |
| `provider_version` | Adapter/provider version |
| `freshness_policy_version` | Owner-approved freshness policy identity |

Exact serialized schema, digest canonicalization and freshness threshold remain to be frozen before implementation.

## 4. Required exchange-filter interpretation

The adapter must parse actual filter entries, not infer values from display precision.

- `PRICE_FILTER`: preserve `minPrice`, `maxPrice`, and `tickSize` independently. Binance documents zero for each field as disabling that individual rule; do not reject zero as malformed and do not invent a replacement. When enabled, enforce the documented price alignment `(price - minPrice) % tickSize == 0`, plus enabled min/max bounds.
- `LOT_SIZE`: validate and expose `stepSize`, `minQty`, and `maxQty` for limit/regular quantity validation. Enforce `quantity >= minQty`, `quantity <= maxQty`, and `(quantity - minQty) % stepSize == 0`. Do not replace this with `quantity % stepSize == 0` unless minQty is zero.
- `MARKET_LOT_SIZE`: preserve separately and apply only if a market-order path is explicitly in scope; do not silently substitute it for `LOT_SIZE`.
- `PERCENT_PRICE`: preserve `multiplierUp`, `multiplierDown` and `multiplierDecimal`; for limit orders, validation also needs a fresh mark-price observation because the allowed price band is dynamic.
- `MIN_NOTIONAL` or the current applicable notional filter: preserve exact filter type and semantics. For a limit ENTRY, validate notional using the contractually defined limit price and quantity. Do not assume Spot `NOTIONAL` fields or market-order averaging semantics apply to USD-M Futures without USD-M documentation.
- Preserve other symbol filters in the source evidence. If an additional filter affects the intended order type and its semantics are unsupported, fail closed rather than ignore it.

Do not assume that filter names, fields or semantics remain static across exchange API revisions. Provider version and contract tests must make supported variants explicit.

## 5. Validation requirements

Reject the metadata snapshot if:
- response or symbol entry is missing, malformed or duplicated;
- symbol, contract type, status or asset identity is unexpected;
- any required applicable filter is absent or duplicated ambiguously;
- required enabled tick size, LOT_SIZE step size, minimum quantity or applicable notional is malformed, non-finite, negative where not allowed, or unparsable; zero-valued PRICE_FILTER fields are treated as disabled per Binance's documented semantics;
- min/max bounds are inconsistent;
- a relevant filter type or semantic change is not understood;
- response is stale under the owner-approved policy;
- deterministic digest cannot be produced or verified.

The normalized object must retain raw filter provenance sufficient to audit each normalized value back to its source filter.

## 6. Sizing and order validation semantics

The instrument provider supplies constraints; it does not decide strategy direction or risk.

For a future AI ENTRY:
- use the exact same execution limit price for risk sizing, notional validation and ledger admission;
- apply enabled `PRICE_FILTER` min/max constraints and align price using `(price - minPrice) / tickSize` as an integer when `tickSize` is enabled; if the corresponding rule is disabled by a zero field, do not enforce that rule;
- validate applicable `PERCENT_PRICE` against a fresh mark-price observation and fail closed if the dynamic reference is missing/stale;
- any price rounding direction must be specified by the execution contract, not improvised by the provider;
- floor quantity to the applicable quantity step so the rounded quantity does not exceed the risk budget;
- enforce min/max quantity and applicable minimum notional after rounding;
- if the rounded quantity is zero, below minimum quantity, below minimum notional or otherwise invalid, emit no AI trade intent;
- Shared Risk Engine independently recalculates account margin budget and remains final ACCEPT/REJECT authority.

No AI DCA is permitted in v1. Market-order filters are not to be used for limit ENTRY unless the order type and exchange semantics explicitly require them.

## 7. Versioning, freshness and replay

A future provider should produce an immutable snapshot with:
- source endpoint and symbol identity;
- observation time and provider version;
- normalized rules and source filter provenance;
- deterministic canonical digest;
- explicit freshness-policy version and evaluated freshness status.

Any change in relevant filter values or source semantics must produce a different snapshot digest. Historical reservation replay must refer to the exact rules snapshot used at admission; reservation snapshot persistence remains subject to the separately deferred G0-07 decision.

No maximum age or cache TTL is selected here. Stale or unverifiable metadata blocks new AI ENTRY admission. Do not use stale cache as an implicit fallback.

## 8. Failure behavior and operational isolation

- Fetch/parse/validation failure => no new AI ENTRY intent.
- Do not modify T0 canonical market data or its SQLite database.
- Do not start background polling, scheduler, systemd service or VPS process as part of this design.
- Do not store API credentials; this public metadata source is intended to be read-only and keyless.
- No order placement, exchange trading client or live execution is in scope.

## 9. Open decisions and approval gates

Still unresolved:
1. Confirm Binance USD-M `exchangeInfo` as the sole authoritative upstream for this instrument.
2. Exact supported filter variants and order-type scope.
3. Normalized schema and deterministic digest algorithm.
4. Metadata observation/freshness policy and refresh cadence.
5. Handling of exchange API revisions and unknown relevant filters.
6. Whether any later consumer requires market-order filters; v1 AI scope is limit ENTRY only unless separately approved.

**Disposition:** design proposal only. G0-05 remains BLOCKED pending owner confirmation of source/filter/freshness policy and future implementation/test gates. No adapter or network activity is authorized by this document.


## 10. Official USDⓈ-M documentation verification — 2026-11-11

The official Binance USDⓈ-M Futures common-definition page was checked (Chinese localized page, updated 2026-08-08):
- Contract type/status definitions distinguish `PERPETUAL` and `TRADING`; the provider must check the exact BTCUSDT symbol, contract type and status.
- `PRICE_FILTER` explicitly permits each of `minPrice`, `maxPrice` and `tickSize` to be zero to disable that individual condition. Enabled price alignment is `(price - minPrice) % tickSize == 0`.
- `LOT_SIZE` explicitly checks `quantity >= minQty`, `quantity <= maxQty`, and `(quantity - minQty) % stepSize == 0`.
- `MARKET_LOT_SIZE` applies to market orders, not as a replacement for the limit-order `LOT_SIZE` rule.
- `PERCENT_PRICE` constrains limit price relative to mark price, so exchangeInfo metadata alone is insufficient to validate this dynamic rule; a fresh mark-price input and separate freshness policy would be required.
- `MIN_NOTIONAL` is documented with a `notional` field; do not import Spot filter schema or assume Spot `NOTIONAL` semantics for USDⓈ-M Futures.
- The page also lists `MAX_NUM_ORDERS` and `MAX_NUM_ALGO_ORDERS`; these depend on open-order/account state and are not static lot/tick sizing rules. A future exchange-parity simulator must decide whether to model them separately.

Source: Binance Developer Documentation, Futures (USDⓈ-M), Public API Parameters / Filters: https://developers.binance.com/zh-CN/docs/products/derivatives-trading-usds-futures/common-definition

**Design correction:** the earlier proposal's blanket requirement that every tick/step/minimum field be strictly positive was too broad. Zero is explicitly a disable sentinel for PRICE_FILTER fields; LOT_SIZE remains subject to its own documented step arithmetic. Filter validation must be field- and filter-specific.

**Disposition:** documentation verified for the above semantics; live endpoint response and current BTCUSDT filter values have NOT been fetched or verified. G0-05 remains BLOCKED pending owner approval of the exact source, dynamic mark-price dependency, freshness policy, canonical schema and implementation gate.
