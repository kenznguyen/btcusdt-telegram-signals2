# P1.6 — T1 contract cross-document consistency review

Date: 2026-11-09
Review type: Same-session static cross-document review; NOT independent
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

## Exact inputs reviewed

- Current T1 source: `kenznguyen/binance-futures-collector@6e20fe94f3ad64cc450e73def80a167fe371e49e`
- Original v1 design: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_AND_INGESTION_ADAPTER_DESIGN_2026-11-09.md`, blob `41a543f9772d890a47d5ebb923668609f5b1e7ea`
- Current v1.1 design: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md`, blob `42d0238edc6baa5bc8990ba27022b3db7c54772b`
- P1.3 acceptance record: `docs/reviews/t1/P1_3_FAIL_CLOSED_REST_RECONCILIATION_ACCEPTANCE_PROFILE_2026-11-09.md`, blob `a99cf2e21edc4519a2f2d0833c6cdf1e6d768599`
- P1.4 self-review: `docs/reviews/t1/P1_4_SELF_REVIEW_T1_SOURCE_CONTRACT_V1_1_AND_P1_3_2026-11-09.md`, blob `f29919bc6eafc24738a1c3e55adb86b04b553643`
- P1.5 clarification record: `docs/reviews/t1/P1_5_DOCUMENTATION_CLARIFICATIONS_F02_F03_F04_2026-11-09.md`, blob `4663ac7d86a5c16d8ae3483ed6a34f0a77d2652c`

## Verdict

**PARTIAL — core fail-closed principles are consistent, but the document set is not yet a single unambiguous implementation contract. REQUEST CHANGES before readiness assessment.**

This is a same-session review and is not independent reviewer sign-off. No issue #138 independent review is claimed.

## Findings

### F01 — HIGH: original v1 document retains superseded finality/schema requirements

The original v1 design still says the CSV schema must persist `is_closed` per row (or equivalent distinguishable interim/final records), and its proposed v1 schema adds an `is_closed` column. The current v1.1 design explicitly selects `output_mode=FINAL_ONLY`, filters provisional events before persistence, and says a per-row `is_closed` field is not required for this first mode.

The newer decision is technically coherent with the pinned producer trace, but the older document remains present and does not visibly mark those clauses as superseded. A future implementer reading both may implement the wrong schema or treat old CSV as eligible.

Required clarification:
- Mark the original v1 sections on `is_closed` and v1 schema as SUPERSEDED BY v1.1.
- Make v1.1 the sole normative contract for this scope.
- State explicitly that legacy/unversioned files remain ineligible and that FINAL_ONLY must be proven by producer regression tests and versioned manifest metadata.

### F02 — MEDIUM: `GAP_DETECTED` lacks source-specific semantics

The v1.1 manifest enum includes `source_health=GAP_DETECTED`, while P1.3 says a missing REST minute is always `SOURCE_HEALTH_UNKNOWN`, never a confirmed gap or no-trade minute. The contract also permits `WINDOW_GAP` only after a valid watermark and contiguous health proof.

These statements can coexist, but the contract does not define what evidence is allowed to set manifest `GAP_DETECTED`, whether it means a known collector transport loss, an expected minute absent after a valid seal, or an external reconciliation result. This ambiguity risks turning REST silence or a WS/REST difference into a false confirmed gap.

Required clarification:
- Define `GAP_DETECTED` as a source-specific, evidence-backed state with a precise producer and event-time scope.
- Explicitly prohibit setting it from missing/empty REST responses, absent WS rows, no-trade inference or uncertain pagination/boundaries.
- Keep `SOURCE_HEALTH_UNKNOWN` for all unresolved completeness states; keep `WINDOW_GAP` for a missing source row only after a valid seal and health proof.

### F03 — HIGH: health-event persistence failure needs an explicit fail-closed transition

P1.5 requires health events to be durably committed before a later manifest may claim completeness. However, some of the events being covered include the storage failure itself (write/flush/fsync failure, disk full, or process termination). In those cases the same storage path may be unable to persist the health event. The design says an unclean restart is uncertainty, but does not fully specify the immediate state transition when the health journal/manifest cannot durably record the invalidation.

Required clarification:
- Treat inability to durably persist a health event as an immediate, sticky invalidation in process memory and prohibit further watermark/manifest advancement.
- On restart, if the prior clean generation-close/checkpoint cannot be verified, mark the generation uncertain/quarantined; do not rely on a missing event record as evidence that no failure occurred.
- State whether health evidence requires an independent durable channel. If not provided, explicitly limit the guarantee to fail-closed detection via previously durable generation/checkpoint state and accept that uncertain ranges may remain permanently quarantined.
- Add negative fixtures for disk-full/fsync failure while recording health, health-journal corruption, and restart with no verifiable close marker.

## Cross-document checks that PASS

1. **REST completeness:** P1.3 and v1.1 both retain the endpoint as candidate only. Exact boundary semantics, no-trade behavior, finality/correction and pagination remain unproven. No watermark or `RECONCILED_COMPLETE` is authorized.
2. **Missing REST minute:** remains `SOURCE_HEALTH_UNKNOWN`; no zero-volume synthesis, interpolation, carry-forward or no-trade inference.
3. **REST-only row:** P1.5 classifies REST-present/WS-absent as `RECONCILIATION_SOURCE_DIVERGENCE`; it cannot be inserted into the WS-derived generation or advance its watermark.
4. **WS/REST mismatch:** quarantined; neither source silently overwrites the other.
5. **Sticky invalidation:** later healthy reconnect/restart cannot clear unresolved continuity failure.
6. **Manifest security:** checksum is not described as authenticated or anti-rollback; current claim is limited to accidental corruption/inconsistency detection.
7. **Decimal precision:** confirmed producer f64/12-decimal/parse-to-zero defect remains a hard blocker; acceptance is not weakened.
8. **Durability:** sync/manifest publication remains a proposed protocol, not target-filesystem proof.
9. **T0 boundary:** T0 remains independent/canonical; no T1 write/promotion path is authorized.

## Blocker register after P1.6

- F01 (P1.4): CRITICAL — no accepted REST completeness oracle.
- F05 (P1.4): HIGH — confirmed producer decimal-loss defect.
- F07 (P1.4): HIGH/operational — target filesystem/provider durability unverified.
- P1.6-F01: HIGH — superseded v1 schema/finality language remains in original document.
- P1.6-F02: MEDIUM — `GAP_DETECTED` semantics ambiguous.
- P1.6-F03: HIGH — durable health-event failure path needs explicit transition.
- Independent review issue #138 remains separate and pending.

## Verification and authorization boundary

Static document review only. No executable tests, REST request, T1 source edit, adapter implementation, GitHub Actions dispatch, VPS/runtime operation, T1 activation, T0/T2 change, strategy/ledger/risk change, live order, deletion or destructive operation.

- Tests: NOT RUN.
- GitHub Actions: NOT DISPATCHED; run ID NONE; artifact NONE.
- Independent review: PENDING.
- Completeness oracle: NOT VERIFIED.
- Producer decimal correction: NOT IMPLEMENTED.
- Target filesystem durability: NOT VERIFIED.
- Implementation: NOT AUTHORIZED.
- T1 activation: NOT AUTHORIZED.
- `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.
