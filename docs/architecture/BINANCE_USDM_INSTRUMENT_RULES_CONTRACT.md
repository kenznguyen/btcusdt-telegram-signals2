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
| `price_tick_size` | Positive tick increment from applicable price filter |
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

- `PRICE_FILTER`: validate and expose applicable `tickSize` and any applicable min/max price bounds.
- `LOT_SIZE`: validate and expose `stepSize`, `minQty`, and `maxQty` for limit/regular quantity validation.
- `MARKET_LOT_SIZE`: preserve separately and apply only if a market-order path is explicitly in scope; do not silently substitute it for `LOT_SIZE`.
- `MIN_NOTIONAL` or the current applicable notional filter: preserve exact filter type and semantics, including whether it applies to market orders and any averaging/price-reference requirements.
- Preserve other symbol filters in the source evidence. If an additional filter affects the intended order type and its semantics are unsupported, fail closed rather than ignore it.

Do not assume that filter names, fields or semantics remain static across exchange API revisions. Provider version and contract tests must make supported variants explicit.

## 5. Validation requirements

Reject the metadata snapshot if:
- response or symbol entry is missing, malformed or duplicated;
- symbol, contract type, status or asset identity is unexpected;
- any required applicable filter is absent or duplicated ambiguously;
- tick size, step size, minimum quantity or minimum notional is non-finite, non-positive or unparsable;
- min/max bounds are inconsistent;
- a relevant filter type or semantic change is not understood;
- response is stale under the owner-approved policy;
- deterministic digest cannot be produced or verified.

The normalized object must retain raw filter provenance sufficient to audit each normalized value back to its source filter.

## 6. Sizing and order validation semantics

The instrument provider supplies constraints; it does not decide strategy direction or risk.

For a future AI ENTRY:
- use the exact same execution limit price for risk sizing, notional validation and ledger admission;
- ensure price is aligned to the applicable tick size; any rounding direction must be specified by the execution contract, not improvised by the provider;
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
