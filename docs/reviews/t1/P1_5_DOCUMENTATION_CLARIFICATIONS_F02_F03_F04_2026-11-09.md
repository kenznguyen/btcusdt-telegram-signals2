# P1.5 — Documentation clarifications for self-review findings F02/F03/F04

Date: 2026-11-09
Type: Documentation-only design update; same-session author review, NOT independent

## Pinned inputs

- T1 source: `kenznguyen/binance-futures-collector@6e20fe94f3ad64cc450e73def80a167fe371e49e`
- P1.4 self-review: `docs/reviews/t1/P1_4_SELF_REVIEW_T1_SOURCE_CONTRACT_V1_1_AND_P1_3_2026-11-09.md`, blob `f29919bc6eafc24738a1c3e55adb86b04b553643`
- Prior design/P1.3 baseline commit: `0e2cbec07b1289950a7aa7ec1b99ef0ec7f6302c`
- Updated design: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md`
- Updated design commit: `630b118fc9f8c1d9d6e97253881dc51be42bcde5`
- Updated design blob: `42d0238edc6baa5bc8990ba27022b3db7c54772b`

## Changes

### F02 — REST-only row and provenance policy

Added design section 16:
- REST row present but WS row absent is `RECONCILIATION_SOURCE_DIVERGENCE`, never implicit agreement.
- WS-only row while REST is absent remains `SOURCE_HEALTH_UNKNOWN`.
- Any value mismatch quarantines.
- Current contract forbids inserting REST-only rows into a WS-derived generation or advancing its watermark from such evidence.
- A future mixed-source mode requires a separately versioned contract, per-row provenance, raw evidence binding, conflict policy, idempotency and separate review/approval.

### F03 — Producer health evidence and watermark invalidation

Added design section 17:
- Enumerated disconnect/reconnect, queue overflow/drop, parse, writer/flush/sync, shutdown/restart and reconciliation failure events.
- Required scoped durable event metadata and ordering before any manifest can claim the affected range complete.
- Added sticky invalidation semantics; later socket health or restart cannot clear an unresolved event.
- Unclean termination is uncertainty; no dependence on a last-second shutdown callback.
- Added planned negative fixtures C63–C71.

Implementation, instrumentation and runtime behavior remain unverified.

### F04 — Manifest threat model

Added design section 18:
- Current adjacent manifest/prefix digests claim accidental corruption/inconsistency detection only.
- Explicitly disclaims protection against local attacker replacing data and manifest together, rollback, host compromise or credential compromise.
- Adversarial protection requires a separately reviewed authenticated manifest, separated key custody and independent monotonic anchor.
- Rollback, restore and unavailable-anchor behavior are fail-closed.
- Added planned negative fixtures C72–C76.

No authentication or external anchor has been implemented.

## Self-review disposition

- F02: DESIGN CLARIFIED; implementation NOT VERIFIED.
- F03: DESIGN CLARIFIED; producer instrumentation NOT IMPLEMENTED/NOT VERIFIED.
- F04: THREAT MODEL CLARIFIED; adversarial tamper/rollback protection NOT PROVIDED.
- F01: CRITICAL blocker unchanged — REST completeness oracle not accepted.
- F05: HIGH blocker unchanged — producer decimal-loss defect remains confirmed.
- F07: durability blocker unchanged — target filesystem/provider behavior not verified.

Verdict: **PARTIAL — documentation findings addressed at contract level; design remains NOT READY FOR IMPLEMENTATION.**

This is not independent review and does not close issue #138.

## Verification and authorization boundary

Documentation only. No source edits, executable tests, Binance REST request, GitHub Actions dispatch, VPS/runtime operation, T1 activation, T0/T2 change, strategy/ledger/risk change, live order, data deletion or destructive operation.

- Tests: NOT RUN.
- GitHub Actions: NOT DISPATCHED; run ID NONE; artifact NONE.
- Independent review: PENDING.
- Completeness oracle: NOT VERIFIED.
- Producer decimal fix: NOT IMPLEMENTED.
- Target filesystem durability: NOT VERIFIED.
- Implementation: NOT AUTHORIZED.
- T1 activation: NOT AUTHORIZED.
- `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.


## P1.5.1 consistency amendment

- Added the two explicit states `RECONCILIATION_SOURCE_DIVERGENCE` and `SOURCE_HEALTH_INVALIDATED` to the existing status taxonomy so the new F02/F03 rules have machine-readable contract outcomes.
- Final design commit: `630b118fc9f8c1d9d6e97253881dc51be42bcde5`.
- Final design blob SHA: `42d0238edc6baa5bc8990ba27022b3db7c54772b`.
- Static consistency check: F02 row-provenance rule aligns with P1.3 exact comparison and no-missing-minute policy; F03 sticky invalidation cannot satisfy the P1.3 seal preconditions until resolved; F04 explicitly limits checksum claims and does not alter P1.3 completeness rules.
- No contradiction identified in the reviewed clauses. This is same-session static consistency only, not independent review.
