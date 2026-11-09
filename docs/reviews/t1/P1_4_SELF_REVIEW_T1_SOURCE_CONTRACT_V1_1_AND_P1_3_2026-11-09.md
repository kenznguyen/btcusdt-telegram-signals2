# P1.4 — Same-session self-review of T1 Source Contract v1.1 / P1.3

Date: 2026-11-09
Review type: Same-session self-review; NOT independent
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

## Exact review targets

- Contract: `docs/design/t1/T1_SOURCE_FILE_CONTRACT_V1_1_PRODUCER_WATERMARK_DURABILITY_2026-11-09.md`
- Contract/P1.3 baseline commit: `0e2cbec07b1289950a7aa7ec1b99ef0ec7f6302c`
- Contract blob SHA: `1befbcbb9f9a1a489e2eec1fce43773bfb71cd04`
- P1.3 record: `docs/reviews/t1/P1_3_FAIL_CLOSED_REST_RECONCILIATION_ACCEPTANCE_PROFILE_2026-11-09.md`
- P1.3 record blob SHA: `a99cf2e21edc4519a2f2d0833c6cdf1e6d768599`
- T1 producer source: `kenznguyen/binance-futures-collector@6e20fe94f3ad64cc450e73def80a167fe371e49e`
- Producer trace: `docs/reviews/t1/T1_KLINE_PRODUCER_CALL_PATH_TRACE_2026-11-09.md`, blob `c1d4ac3fc773b20e03ad91f566e0cd4c64d5af77`

## Verdict

**REQUEST CHANGES — DESIGN IS CONSERVATIVE BUT NOT IMPLEMENTATION-READY.**

This review is explicitly a same-session self-review. It does not satisfy the independent reviewer gate in issue #138 and must not be represented as independent sign-off.

## Findings (severity-ranked)

### F01 — CRITICAL: no accepted completeness oracle; watermark must remain disabled

The proposed `/fapi/v1/klines` reconciliation source does not currently prove exact request-boundary inclusion, no-trade-minute emission, finality/immutability, correction policy or gap-free pagination. The P1.3 rule correctly treats every missing REST minute and empty response as `SOURCE_HEALTH_UNKNOWN`, not as a no-trade interval or a confirmed data gap.

This is safe fail-closed behavior, but it means the candidate endpoint cannot currently establish `RECONCILED_COMPLETE`. The contract must not publish a watermark or aggregate based on this candidate until each semantic is supported by authoritative evidence and deterministic tests. If Binance does not provide the required guarantees, a different independently justified evidence model is needed; do not relax the missing-minute rule.

### F02 — HIGH: REST-only recovery and source provenance are underspecified

The reconciliation procedure says identical REST/WS values may be accepted and mismatches quarantined, but it does not fully define the case where REST returns a valid candle that is absent from the WS-derived file. Specify whether REST may supply that missing row, how its source provenance is represented, how mixed-source generations are identified, and how the accepted row is bound to raw REST evidence and the final committed prefix. Absence of a WS row must not be treated as agreement.

### F03 — HIGH: receive-path completeness needs explicit observable failure signals

The design correctly names disconnect, reconnect, overload, writer error, crash and uncertain delivery as reconciliation triggers. It does not yet define the exact observable producer signals and durable event ordering for queue overflow/drop, task cancellation, process termination, buffer/write failure and recovery overlap. A missed event that leaves no durable health marker could otherwise be followed by an unjustified watermark. Require explicit counters/events, generation invalidation and negative fixtures for each failure boundary; unknown state must hold the watermark.

### F04 — HIGH: manifest rollback/authenticity threat model is incomplete

Prefix digests detect accidental data-prefix changes relative to a manifest, but the document does not define whether the manifest itself is protected against rollback or coordinated replacement with an older data file. State the threat model. If adversarial/local tampering is in scope, add authenticated manifests or an independently anchored monotonic generation/checkpoint; a plain digest stored beside the data is not an authenticity anchor. If only crash/accidental corruption is in scope, say so explicitly and do not claim tamper resistance.

### F05 — HIGH: decimal-loss defect is confirmed in the pinned producer

The pinned writer parses decimal strings through `f64`, formats to 12 fractional digits and substitutes `0.0` on parse failure. The existing CSV cannot satisfy byte-preserving source decimals. This is a source defect, not a future theoretical risk. Contract strictness is correct: producer correction plus golden tests are mandatory; do not normalize acceptance to the lossy output.

### F06 — MEDIUM: FINAL_ONLY must not be conflated with immutable finality

Filtering WS messages with `is_closed=false` supports a final-only output mode, but it does not independently establish that the exchange will never revise a historical candle. Keep separate claims for (a) the producer only writes events marked closed and (b) the exchange candle is immutable. The current design mostly separates these; tests and manifest terminology must preserve that distinction.

### F07 — MEDIUM: durability protocol is a specification, not proof

The ordered data sync → manifest sync → atomic rename → directory sync sequence is a reasonable target protocol, but the actual filesystem/provider semantics and crash states remain unverified. In particular, recovery after rename but before directory sync must not guess which manifest is durable. Require target-environment evidence and quarantine on ambiguity. Unit tests alone cannot establish D2–D4 durability.

### F08 — MEDIUM: acceptance fixtures are catalogued, not executed

C01–C62 are requirements/examples in the design, not executable evidence. There is no implementation, deterministic test suite, Actions run or runtime proof for this adapter/reconciliation contract. Report them as planned fixtures only.

## Five-axis assessment

| Axis | Result | Rationale |
|---|---|---|
| Correctness | BLOCKED | Completeness oracle absent; REST-only recovery semantics incomplete; decimal loss confirmed |
| Architecture | PARTIAL | Staging isolation and no-T0-write boundary are clear; source provenance and producer health signaling need precision |
| Security / integrity | PARTIAL | Fail-closed validation is sound; manifest rollback/authenticity threat model is not stated |
| Readability | PASS | Contract sections, state taxonomy and stop conditions are understandable |
| Performance | NOT VERIFIED | No implementation or representative-volume benchmark |

## Positive controls confirmed

- T0 remains independent and canonical; no T1 write path to T0 is authorized.
- Missing REST minute is not inferred as no-trade or data gap; no synthetic candle/interpolation/carry-forward.
- REST remains a candidate, not an accepted completeness oracle.
- Post-seal mismatch is handled through immutable correction/quarantine; sealed bytes are not rewritten.
- Product identity, interval=1m, FINAL_ONLY declaration, bounded reads and generation checks are explicit design requirements.
- No implementation, runtime or promotion is authorized by this review.

## Required design changes before another readiness assessment

1. Define the REST-only missing-WS-row policy, row provenance and evidence binding.
2. Define durable producer health signals and invalidation semantics for every queue/write/process failure boundary.
3. Explicitly state the manifest threat model and rollback/tamper protection level.
4. Preserve the strict no-trade/finality/boundary/pagination blockers until authoritative proof exists.
5. Keep decimal correction and target-filesystem durability as hard gates.
6. Convert fixtures into deterministic tests only after separate implementation approval; then run them through GitHub Actions and preserve exact SHA/run/artifact evidence.

## Verification and authorization boundary

Review only. No tests were run. No Binance REST request, T1 source edit, adapter implementation, GitHub Actions dispatch, VPS/runtime operation, T0/T2 change, T1 activation, strategy/ledger/risk change, live order, data deletion or destructive operation was performed.

- Independent review: PENDING (issue #138 remains the independent-review path).
- Completeness oracle: NOT VERIFIED.
- Implementation: NOT AUTHORIZED.
- T1 activation: NOT AUTHORIZED.
- GitHub Actions: NOT DISPATCHED; run ID NONE; artifact NONE.
- `AI_EXECUTION_ENABLED=false`; no live orders; no OKX fallback/replacement.
