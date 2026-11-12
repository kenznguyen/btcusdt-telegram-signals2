# T1 → T2 Order Book Contract V1 — Design Freeze Proposal

Date: 2026-11-13
Status: DESIGN FROZEN FOR REVIEW; NOT IMPLEMENTED OR RUNTIME-VERIFIED

## 1. Scope and safety boundary

- Source: T1 BTCUSDT Binance USD-M perpetual Order Book.
- Consumer: T2 read-only.
- Purpose: provide one internally consistent, sequence-verified, exact-decimal book snapshot for a single decision cycle.
- Hummingbot remains PAUSED / OUT OF SCOPE.
- This document authorizes documentation and isolated contract-test design only. It does not authorize T1 source changes, T1 activation, VPS/provider/runtime access, T0 access or changes, Core runner implementation, AI execution, or live orders.
- T1 PR #1 remains OPEN / DRAFT with a required review finding; this design does not waive that gate.

## 2. Frozen V1 consumer contract

Contract identifier: `T1_T2_ORDERBOOK_V1`.

Required identity and payload:
- `contractVersion`: exact literal `T1_T2_ORDERBOOK_V1`.
- `symbol`: `BTCUSDT`.
- `market`: `BINANCE_USDM_PERPETUAL`.
- `bids`, `asks`: arrays of [price, quantity], both JSON strings in canonical positive Decimal notation. No JSON number and no float/f64 conversion anywhere in the T1→T2 path.
- `snapshotLastUpdateId`: REST snapshot anchor update ID.
- `firstAppliedU`, `lastAppliedU`: inclusive update range represented by the published book.
- `sourceTimestampMs`: exchange source timestamp of the last applied update (document exact Binance event field used).
- `observedAtMs`: T1 wall-clock receive/observation timestamp of the last applied update.
- `decisionWatermark`: the `lastAppliedU` represented by this immutable snapshot.
- `generation`: monotonically increasing fencing generation for each successful rebuild/re-anchor.
- `snapshotId`: unique immutable publication identity.
- `continuity`: must equal `VERIFIED`.
- `freshness`: must equal `FRESH` at publication; T2 independently rechecks age at decision time.
- `depth`: actual number of returned bid and ask levels, declared separately.
- `complete`: must equal true.

Atomicity: every field and both sides of the book must belong to the same immutable snapshot/generation/watermark. A reader must never observe a partially written snapshot or mix files/generations. The transport/storage mechanism is deliberately not selected by this contract.

## 3. Frozen initial acceptance parameters

| Parameter | V1 value | Enforcement |
|---|---:|---|
| `requiredDepth` | 20 levels per side | T1 publishes at least 20 bids and 20 asks; T2 rejects less |
| `maxBookAgeMs` | 2,000 ms | T2 checks both source and observation age against decisionAtMs |
| `maxFutureSkewMs` | 250 ms | T2 rejects source/observation timestamps more than 250 ms in the future |
| `reanchorOnReconnect` | true | Every reconnect invalidates current trusted book until rebuild completes |
| `reanchorOnSequenceGap` | true | Any sequence discontinuity invalidates current trusted book |
| `maxReanchorAttempts` | 3 consecutive attempts per trigger | After three failures remain BROKEN; no publication |
| `publishOnlyAfterVerified` | true | No partial/intermediate publication |

Rationale and limits:
- 20 levels per side is the initial bounded depth contract, not proof of market-impact sufficiency. It must not be silently reduced.
- 2,000 ms is four 500 ms observation intervals, used as a conservative initial freshness ceiling for this integration. It is not a measured latency guarantee.
- 250 ms is a timestamp-skew rejection bound, not permission to accept stale data.
- Three attempts bound recovery work. A later independent reconnect/gap trigger may start a new bounded attempt batch; the current BROKEN state remains unusable in the meantime.
- These are frozen V1 contract values for isolated tests. Changing them requires a versioned decision/evidence update, not an undocumented runtime override.

## 4. Sequence and re-anchor algorithm

On initial start, reconnect, sequence gap, corrupt/partial source data, or loss of the source watermark:
1. Immediately mark current book BROKEN and invalidate its publication for T2. Never continue using a partially self-healed in-memory book.
2. Start a fresh bounded re-anchor attempt. Obtain a new Binance USD-M REST depth snapshot; preserve all price/quantity values as exact decimal strings and capture its `lastUpdateId`.
3. Buffer incoming depth diff events while obtaining the snapshot.
4. Discard buffered events whose final update ID `u` is not newer than the snapshot anchor.
5. The first event applied must bridge the next required update: `U <= snapshotLastUpdateId + 1 <= u`.
6. For each subsequent event, require `pu == previous last applied u`. After applying, advance the local watermark to the event's `u`.
7. Apply updates in sequence order, deleting levels with zero quantity and replacing/inserting other levels using exact Decimal arithmetic.
8. Validate positive finite prices, non-negative finite quantities, no duplicate/conflicting level representation, best bid strictly below best ask, at least 20 levels on each side, and timestamp age/skew.
9. If any sequence, parse, source, depth, or consistency check fails during rebuild, discard the entire candidate and retry from a new REST snapshot, up to three consecutive attempts.
10. Publish atomically only after every check passes. Increment generation, assign a new snapshotId and bind the snapshot to its final lastAppliedU watermark. Otherwise remain BROKEN and publish no trusted snapshot.

A later valid-looking diff must never transition BROKEN → VERIFIED without a new trusted REST anchor and a verified contiguous chain.

## 5. T2 acceptance rules

At decisionAtMs, T2 must independently reject the snapshot unless all are true:
- exact contract version, symbol and market match;
- complete=true and continuity=VERIFIED;
- generation and snapshotId are present and internally consistent;
- decisionWatermark equals lastAppliedU;
- exact Decimal strings parse without float conversion;
- both sides contain at least 20 levels;
- sourceTimestampMs and observedAtMs are not more than 250 ms in the future;
- source age and observation age are each no more than 2,000 ms;
- best bid < best ask;
- no missing, duplicate, malformed or non-finite levels.

T2 must not fall back to T1 dashboard API, periodic f64-derived snapshots, Hummingbot, cached book, another venue, or a synthetic book. Any failure means no trusted Order Book input and the Core decision cycle fails closed before producer/admission as specified by the one-shot design.

## 6. Isolated contract test matrix (design only)

| Test | Input/fault | Expected result |
|---|---|---|
| OB-01 | Exact REST anchor + first diff bridges anchor + continuous pu chain | VERIFIED |
| OB-02 | First diff does not cover anchor+1 | BROKEN; retry |
| OB-03 | Subsequent pu differs from previous u | BROKEN; retry |
| OB-04 | Duplicate/old event with u <= watermark | Ignore; no state regression |
| OB-05 | Reconnect after VERIFIED | Immediately BROKEN; old generation rejected |
| OB-06 | Gap during re-anchor | Candidate discarded; fresh anchor required |
| OB-07 | Three consecutive failed re-anchor attempts | Remain BROKEN; no publication |
| OB-08 | Successful re-anchor | Generation increments; new immutable snapshot |
| OB-09 | Any price/quantity represented as JSON number | Reject |
| OB-10 | Decimal precision exceeds binary-float-safe representation | Preserve exact string/value |
| OB-11 | Fewer than 20 bids or asks | Reject |
| OB-12 | Crossed or locked book (best bid >= best ask) | Reject |
| OB-13 | Source or observation age > 2,000 ms | Reject |
| OB-14 | Timestamp > decisionAtMs + 250 ms | Reject |
| OB-15 | Missing/partial/corrupt file or inconsistent watermark | Reject |
| OB-16 | Reader races writer/rotation | Reader sees old complete snapshot or new complete snapshot, never a mixture |
| OB-17 | T2 presents prior generation after re-anchor | Reject |
| OB-18 | T1 unavailable or contract version unknown | Reject; no fallback |

Test isolation:
- Use synthetic deterministic fixtures only; no Binance connection, no T1 runtime, no VPS, no T0 database, no credentials and no live trading.
- Assert T2 reader is read-only and performs no migrations, file creation, repair or mutation.
- Assert invalid input cannot invoke Core producer, PaperLedger or Shared Risk Engine admission.
- Record exact fixture hashes and test command/output if these tests are later implemented.
- This matrix is a test specification, not test execution evidence. No tests have been run by this documentation increment.

## 7. Open implementation choices (not contract ambiguities)

The contract does not choose the transport (HTTP, local read-only file API, or another bounded mechanism), T1 internal storage layout, process topology, authentication implementation, or deployment model. Those require separate source review and bounded approval. Whatever mechanism is chosen must preserve the contract's atomicity, read-only access, provenance and fail-closed behavior.

## 8. Disposition

- Contract semantics and V1 thresholds: DESIGN FROZEN FOR REVIEW.
- T1 implementation: NOT IMPLEMENTED.
- T2 reader/parser: NOT IMPLEMENTED.
- Isolated contract tests: SPECIFIED, NOT IMPLEMENTED / NOT RUN.
- T1 runtime/source trust: NOT VERIFIED.
- T2 integration: BLOCKED pending separate implementation authorization and passing isolated tests.
- Core one-shot runner: NOT IMPLEMENTED.
- No workflow/CI result is claimed by this document.
