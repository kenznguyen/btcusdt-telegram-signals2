# P1.2 Addendum — Candidate Binance REST Kline Reconciliation Source

Date: 2026-11-09
Design updated: 88d08819dc253e50eaf4ea8ccac69ea6acfa4df2
Reviewed T1 source SHA: 6e20fe94f3ad64cc450e73def80a167fe371e49e

## Evidence

A read-only inspection of the pinned T1 repository tree and `src/rest/client.rs` found methods for mark-price, index-price and premium-index klines, but no standard trade-kline method. T1 does not currently implement the reconciliation source required for a trustworthy producer watermark.

The official Binance USDⓈ-M API documentation identifies `GET /fapi/v1/klines`, with symbol and interval parameters, open-time candle identity, a 1m interval and OHLC/volume/trade-count response fields. Decimal-valued response fields are strings. See:
- https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Kline-Candlestick-Data
- https://developers.binance.info/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data

## Design update

The v1.1 contract now names this endpoint as a candidate producer-owned reconciliation source. It requires raw response retention, exact request-range binding, digest evidence, finality validation, WS-vs-REST comparison, fail-closed behavior on mismatch or unavailable/incomplete responses, and immutable handling of post-seal corrections. Additional fixtures C46–C54 are defined.

## Remaining blockers

The endpoint is not yet accepted as a completeness oracle. Authoritative verification remains required for start/end boundary inclusion, no-trade minute behavior, candle finality, historical revisions, symbol-status/maintenance behavior and pagination completeness. If no-trade minutes can be omitted and no authoritative distinction exists, absence cannot be interpreted as either a gap or a no-trade interval. A separate trade-level reconciliation design may be necessary.

Until all semantics are verified, `RECONCILED_COMPLETE` must not be emitted and the watermark must remain withheld for affected intervals. This is design only; no endpoint was called, no source code changed, no tests or workflow ran, and no VPS/runtime action occurred.

## Status

**CANDIDATE SOURCE IDENTIFIED / RECONCILIATION CONTRACT EXPANDED / COMPLETENESS ORACLE NOT VERIFIED / IMPLEMENTATION NOT AUTHORIZED.**