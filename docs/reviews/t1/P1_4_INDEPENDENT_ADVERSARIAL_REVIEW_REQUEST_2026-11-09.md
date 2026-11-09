# P1.4 — Independent Adversarial Review Request

Date: 2026-11-09
GitHub issue: https://github.com/kenznguyen/btcusdt-telegram-signals2/issues/138

## Purpose

Obtain a genuinely independent review of T1 Source File Contract v1.1 and the P1.3 fail-closed REST reconciliation profile. The current author must not be treated as an independent reviewer; same-session self-review does not satisfy this gate.

## Exact review targets

- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Design file: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md`
- P1.3 design commit: `0e2cbec07b1289950a7aa7ec1b99ef0ec7f6302c`
- P1.3 record: `docs/reviews/t1/P1_3_FAIL_CLOSED_REST_RECONCILIATION_ACCEPTANCE_PROFILE_2026-11-09.md`
- Pinned producer source: `kenznguyen/binance-futures-collector@6e20fe94f3ad64cc450e73def80a167fe371e49e`

## Required adversarial questions

1. Can a watermark advance despite a missed final 1m candle, WebSocket disconnect, queue overflow, process crash or partial REST response?
2. Does Binance `/fapi/v1/klines` prove complete minute coverage, including no-trade minutes? Verify authoritative boundary and pagination semantics rather than assuming them.
3. Is candle finality/immutability established, or is the design limited to point-in-time observation plus correction detection?
4. Can REST and WebSocket share a common blind spot and falsely agree? What independent evidence is required?
5. Are raw decimal preservation, FINAL_ONLY declaration, exact product identity, manifest atomicity, filesystem durability and bounded active-file reads sufficiently specified?
6. Identify false-PASS paths, ambiguous states, missing deterministic fixtures and unsafe assumptions.

## Required reviewer output

Written review tied to exact design/source SHAs; reviewer identity; severity-ranked findings; evidence and rationale; explicit PASS / REQUEST CHANGES / BLOCKED verdict. Reviewer must be separate from the author of the design and current same-session reviews.

## Current disposition

The issue was created and is OPEN. No reviewer has been assigned or has submitted a review. Therefore independent review remains PENDING, not PASS.

## Guardrails

Review-only request. It does not authorize T1 source edits, adapter implementation, tests, GitHub Actions dispatch, VPS/runtime, T0/T2 changes, T1 activation, strategy/trading changes, data deletion or destructive tests. Completeness oracle remains NOT VERIFIED. Implementation and activation remain NOT AUTHORIZED.
