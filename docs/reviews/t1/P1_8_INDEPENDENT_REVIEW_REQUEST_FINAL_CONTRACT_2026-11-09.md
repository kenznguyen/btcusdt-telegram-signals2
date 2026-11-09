# P1.8 — Independent review request for final T1 contract

Date: 2026-11-09
Type: Review-request maintenance only; no independent review received.
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

## Purpose

The prior issue #138 targeted an earlier design baseline. After P1.7 clarified normative precedence, GAP_DETECTED and health-event persistence failure, the issue was updated to target the exact final contract SHA and require a genuinely independent adversarial review.

## Exact targets

- Normative v1.1 contract blob: `fd640ab36efed6975f1dfaaed750f9d0ae7f708c`
- Archival v1 blob: `c64d6da7b16e608ef5ccebafabce03e51960cfcc`
- Pinned producer source: `kenznguyen/binance-futures-collector@6e20fe94f3ad64cc450e73def80a167fe371e49e`
- P1.3, P1.4, P1.5, P1.6 and P1.7 review records are listed in GitHub issue #138.

## Required review

Reviewer must be independent of the author and same-session reviews. The written review must identify reviewer identity, tie findings to exact SHAs, rank severity, provide evidence/reproduction rationale and issue PASS / REQUEST CHANGES / BLOCKED. The request explicitly covers watermark false-PASS, Binance REST completeness/no-trade/boundary/pagination/finality, REST/WS shared blind spots, FINAL_ONLY and legacy rejection, GAP_DETECTED semantics, health-event persistence failure, decimal loss, product identity, manifest/cursor ordering, filesystem durability, fixtures and archival-v1 precedence.

## Issue state at request update

- Issue: [#138 — P1.8 Independent adversarial review](https://github.com/kenznguyen/btcusdt-telegram-signals2/issues/138)
- State: OPEN
- Updated title: P1.8 — Independent adversarial review of final T1 Source Contract v1.1
- No reviewer assignment or independent review response is evidenced by this record. The issue update is a request, not review completion.

## Current blockers

- F01 CRITICAL: no accepted REST completeness oracle; missing/no-trade semantics, exact boundaries, finality/correction and pagination remain unresolved.
- F05 HIGH: pinned T1 producer decimal conversion defect remains confirmed (f64, fixed 12 decimal places, parse-error-to-zero).
- F07 HIGH/operational: target filesystem/provider durability and crash recovery remain unverified.
- C77–C81 are planned only, not implemented or executed.
- Independent review: PENDING.
- Implementation: NOT AUTHORIZED.
- T1 activation: NOT AUTHORIZED.

## Guardrails and verification

Review-request/documentation only. No source edits, adapter implementation, tests, REST request, Actions dispatch, VPS/runtime, T0/T2 changes, T1 activation, strategy/AI/ledger/risk changes, trading changes, data deletion or destructive operation. Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.
