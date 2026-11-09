# P1.7 — T1 contract clarifications and static consistency review

Date: 2026-11-09
Review type: Same-session documentation consistency check; NOT independent
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

## Exact inputs

- Pinned T1 source: `kenznguyen/binance-futures-collector@6e20fe94f3ad64cc450e73def80a167fe371e49e`
- Archival v1 design: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_AND_INGESTION_ADAPTER_DESIGN_2026-11-09.md`, final blob `c64d6da7b16e608ef5ccebafabce03e51960cfcc`
- Normative v1.1 design: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md`, blob `fd640ab36efed6975f1dfaaed750f9d0ae7f708c`
- P1.6 review: `docs/reviews/t1/P1_6_CONTRACT_CROSS_DOCUMENT_CONSISTENCY_REVIEW_2026-11-09.md`, blob `2cc278c168ea86125e11fe192542d65e3dffba78`

## P1.7 changes

1. **P1.6-F01 — resolved at documentation level.** The original v1 document is explicitly archival/non-normative for the current producer contract; v1.1 is the sole normative source-file/producer contract for this scope. The old per-row `is_closed` and proposed schema language is marked superseded/do-not-implement and the contradictory requirement paragraph now points to v1.1. Current mode requires versioned `output_mode=FINAL_ONLY` and `interval=1m`, producer filtering of `is_closed=false`, and regression evidence. Legacy/unversioned or undeclared files remain ineligible.
2. **P1.6-F02 — resolved conservatively at design level.** `GAP_DETECTED` is reserved and not assignable under the current profile. It cannot be set from missing/empty REST responses, missing WS rows, no-trade inference, uncertain pagination/boundaries, transport/queue/parser/writer failures, or unsealed windows. Those remain UNKNOWN, INVALIDATED, DIVERGENCE or quarantine/pending as applicable. A future authoritative gap-evidence profile requires separate versioning, approval and independent review. `WINDOW_GAP` remains distinct and requires a valid seal plus complete health proof; it does not permit synthesis or aggregation.
3. **P1.6-F03 — resolved at design level.** If health evidence cannot be durably recorded, immediately set sticky in-process invalidation and stop committed-offset, manifest, watermark and seal advancement. On restart, missing/corrupt health evidence, an ACTIVE prior generation, or absent/unverifiable clean-close/checkpoint state requires quarantine. No independent durable health channel is assumed; this limitation is explicit. Recovery requires a new generation and accepted reconciliation; it may remain blocked indefinitely.

Added planned negative contract fixtures C77–C81 for disk-full/fsync failure, health-journal corruption, missing clean-close marker, invalid GAP_DETECTED inference, and missing FINAL_ONLY declaration/regression evidence. These fixtures are NOT implemented or executed.

## Static consistency result

**P1.7 DOCUMENTATION CLARIFICATIONS COMPLETE / SAME-SESSION STATIC CHECK PARTIAL-PASS.**

The three P1.6 findings are addressed in the normative document set. The check is not an independent review, does not prove producer behavior, and does not grant implementation readiness.

Unchanged hard blockers:
- F01 CRITICAL: Binance REST is not an accepted completeness oracle; no-trade, exact boundaries, finality/correction and pagination remain unresolved. Watermark/RECONCILED_COMPLETE remain disabled.
- F05 HIGH: pinned producer still has confirmed f64 conversion, 12-decimal formatting and parse-error-to-zero behavior. No correction is made.
- F07 HIGH/operational: target filesystem/provider durability and crash-recovery semantics remain unverified.
- Independent review requested in issue #138 remains pending; same-session review is not independent sign-off.

## Authorization and verification

- Scope: documentation only.
- Tests: NOT RUN; C77–C81 are planned fixtures only.
- GitHub Actions: NOT DISPATCHED; run ID NONE; artifact NONE.
- REST: NOT CALLED.
- T1 source/adapter: NOT MODIFIED / NOT IMPLEMENTED.
- T1 activation/VPS: NOT AUTHORIZED.
- T0/T2, strategy, AI, ledgers and risk engine: UNCHANGED.
- T0 remains independent/canonical; no T1 write or promotion path.
- Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.
- No deletion, archive, cleanup, vacuum, compaction, backup expiry, restore or destructive test.

## Next step

Request/obtain independent adversarial review against the exact final v1.1 blob SHA above and the archival v1 supersession change. Keep implementation blocked until independent review and F01/F05/F07 evidence gates are resolved. Do not implement C77–C81 or change the producer without separate explicit approval.
