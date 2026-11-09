# P1.3 — Fail-Closed REST Reconciliation Acceptance Profile

Date: 2026-11-09
Design commit: 0e2cbec07b1289950a7aa7ec1b99ef0ec7f6302c
Design blob SHA: 1befbcbb9f9a1a489e2eec1fce43773bfb71cd04
Pinned T1 source SHA: 6e20fe94f3ad64cc450e73def80a167fe371e49e

## Purpose

Resolve the unsafe interpretation of missing Binance REST Kline rows while preserving the rule that no producer watermark may advance without a defensible completeness proof.

## Documentation evidence reviewed

Official Binance USDⓈ-M documentation identifies `GET /fapi/v1/klines`, `symbol`, `interval`, optional `startTime`/`endTime`, a maximum `limit` of 1500, open-time identity and the 12-field response including close time and decimal strings:
- https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Kline-Candlestick-Data
- https://developers.binance.info/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data

The reviewed documentation does not establish all semantics needed for a completeness oracle: exact time-boundary inclusion, whether no-trade minutes are emitted, formal finality/immutability, correction behavior and an end-to-end pagination completeness guarantee.

## P1.3 contract decisions

1. `/fapi/v1/klines` remains a candidate recovery/reconciliation source, not an accepted completeness oracle.
2. For `[start_ms,end_ms)` aligned to 1m, the expected set is every minute open time in the interval.
3. `RECONCILED_COMPLETE` requires exactly one valid REST row per expected minute, verified request boundaries, proven complete pagination, authoritative finality semantics, exact source comparison, and durable evidence bound to the file generation/manifest.
4. Any missing REST minute is `SOURCE_HEALTH_UNKNOWN`. It is neither a confirmed data gap nor a no-trade minute. It blocks watermark and aggregation.
5. Empty response, uncertain boundary inclusion, duplicate/missing page data, unproven finality, or incomplete pagination all fail closed.
6. No zero-volume synthetic candle, interpolation, carry-forward or inference of no trades from silence.
7. Any post-seal discrepancy becomes an immutable correction event and quarantine; sealed source bytes are never rewritten.
8. The conservative rule can leave legitimate no-trade intervals unsealable. This is an intentional reliability trade-off until a separate authoritative no-trade proof is approved.

## Additional fixtures

C55–C62 cover exact expected-minute coverage, missing minutes, duplicate page overlap, uncertain boundaries, incomplete pagination, unproven finality, post-seal correction and empty responses. Passing C55 only makes an interval eligible for further checks; it does not bypass identity, finality or durability gates.

## Review status

This is a same-session design refinement, not an independent review. It narrows behavior safely but does not close the external API-contract gaps. `RECONCILED_COMPLETE` remains disabled. Independent review is still required before implementation consideration.

## Guardrails and execution status

Documentation only. No Binance REST call, T1 source change, adapter implementation, tests, workflow dispatch, VPS/runtime, T0/T2, strategy, AI, ledger or risk-engine change. No T1 activation. No destructive data operation.

T0 remains independent and canonical. No T1 writes to T0. Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.

**P1.3 DESIGN PROFILE RECORDED / REST COMPLETENESS ORACLE NOT VERIFIED / IMPLEMENTATION NOT AUTHORIZED / INDEPENDENT REVIEW PENDING.**

GitHub Actions: NOT DISPATCHED. Run ID: NONE. Artifact: NONE.