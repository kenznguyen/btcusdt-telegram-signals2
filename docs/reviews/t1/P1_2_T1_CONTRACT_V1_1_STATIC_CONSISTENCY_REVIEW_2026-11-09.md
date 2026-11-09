# P1.2 — T1 Contract v1.1 Static Consistency Review

Date: 2026-11-09
Reviewed design commit: d83e6555556e5e6482015df93c408a3669fe8120
Reviewed design blob: 746de0920e8a79eaa79dc196b2489f198edaf977
Source evidence: T1 SHA 6e20fe94f3ad64cc450e73def80a167fe371e49e
Trace record: docs/reviews/t1/T1_KLINE_PRODUCER_CALL_PATH_TRACE_2026-11-09.md

## Review type

Same-session static consistency review against the pinned source trace and earlier v1 design. This is not an independent reviewer sign-off and must not be represented as one.

## Verdict

**PARTIAL — internal contradictions corrected; producer completeness protocol remains underspecified and implementation remains blocked.**

## Findings

### P12-01 — PASS: decimal defect disposition now matches source evidence

The design now states that the current producer is a confirmed defect: write_kline parses decimal strings as f64, formats 12 fractional digits and substitutes 0.0 on parse failure. This aligns with the pinned source trace. The acceptance requirement remains lossless raw decimal preservation plus malformed-value rejection. No implementation or regression test is claimed.

### P12-02 — PASS: first-version finality semantics made coherent

The design now selects one v1 mode: output_mode=FINAL_ONLY with interval=1m, declared in versioned manifest metadata and verified by producer tests. It no longer simultaneously requires a per-row is_closed field for this first mode. A future mixed provisional/final feed requires a separate schema mode/version. This matches the inspected handler, which filters is_closed=false before CSV writing.

### P12-03 — BLOCKER: completeness reconciliation mechanism is not specified

The revised text correctly recognizes that a healthy WebSocket connection or absence of an observed disconnect does not prove every Binance final kline was received. It now requires source_health=RECONCILED_COMPLETE before watermark advancement.

However, it does not define the actual producer-owned reconciliation procedure or evidence contract. Before a watermark can be trusted, the design must specify:
- which authoritative Binance USD-M source is queried to reconcile finalized 1m candles;
- the exact time range and boundary semantics reconciled after startup, reconnect, overload, process crash and uncertain delivery;
- how the producer distinguishes a missing final candle from an API delay or an unavailable reconciliation source;
- how the reconciliation response, source identity, retrieval time, coverage and digest are bound to the file generation and manifest;
- what happens when the reconciliation source disagrees with the WebSocket-derived CSV;
- how late corrections or historical changes are handled without rewriting sealed data;
- what deterministic fixtures prove complete, missing, delayed, conflicting and unavailable reconciliation outcomes.

Until those semantics are specified and independently reviewed, RECONCILED_COMPLETE is only a status label, not an implementable proof. Watermark must remain withheld for affected windows. No aggregate or promotion may result.

### P12-04 — HIGH: final-only producer behavior still needs regression evidence

The source trace shows the current code filters provisional events, but the persisted CSV does not carry a versioned manifest declaring FINAL_ONLY. The design correctly requires a producer regression test and manifest declaration. Both remain implementation evidence, not current facts. Existing CSV must not be retroactively treated as contract-v1 FINAL_ONLY.

### P12-05 — HIGH: target filesystem durability remains unverified

The ordered sync/manifest publication protocol is a useful design target, but no target-filesystem/provider evidence exists for file sync, atomic rename, directory sync or crash recovery. Do not claim D2–D4 durability from a unit test or this design.

## Five-axis summary

| Axis | Result |
|---|---|
| Correctness | PARTIAL — decimal/finality contradictions corrected; reconciliation proof BLOCKED |
| Readability | PASS — v1 FINAL_ONLY mode and confirmed decimal defect are now explicit |
| Architecture | PARTIAL — staging isolation is retained; producer completeness proof incomplete |
| Security / integrity | PARTIAL — fail-closed identity and manifest checks; reconciliation evidence trust not specified |
| Performance | NOT VERIFIED — no implementation or representative-volume benchmark |

## Required next revision

1. Specify producer-owned authoritative reconciliation for final 1m candles and its exact evidence schema.
2. Define restart/reconnect/overload reconciliation boundaries and handling of delayed/unavailable/conflicting source responses.
3. Bind reconciliation evidence to the file generation, watermark and manifest digest.
4. Add deterministic positive/negative fixtures for reconciliation and late correction.
5. Re-review the revised contract independently before any implementation proposal.

## Guardrails

No T1 source change, adapter implementation, tests, CI dispatch, VPS/runtime, T0/T2 change, T1 activation, PR review submission or merge was performed. No data deletion, archive, cleanup, vacuum, compaction, backup expiry or destructive test.

T0 remains independent/canonical. No T1 writes to T0. Paper-only; AI_EXECUTION_ENABLED=false; no live orders; no OKX replacement/fallback.

## Final status

**P1.2 STATIC CONSISTENCY REVIEW COMPLETE / PARTIAL / WATERMARK RECONCILIATION BLOCKED / INDEPENDENT REVIEW PENDING.**

No tests were run. GitHub Actions was not dispatched. No runtime or filesystem durability claim is made.