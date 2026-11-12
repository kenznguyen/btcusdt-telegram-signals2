# T1 BTCUSDT Order Book V1 — Implementation Specification & Test Plan

Date: 2026-11-13
Status: **DESIGN ONLY — NOT APPROVED FOR SOURCE IMPLEMENTATION OR RUNTIME ACTIVATION**
Parent contract: `T1_T2_ORDERBOOK_CONTRACT_V1_DESIGN_2026-11-13.md`
Source gap review: `T1_ORDERBOOK_V1_SOURCE_GAP_REVIEW_2026-11-13.md`

## 1. Scope and non-goals

Implement a narrowly scoped BTCUSDT Binance USD-M Order Book V1 publication path in T1, consumed read-only by T2 only after validation.

In scope for a future, separately approved implementation:
- Per-symbol state lifecycle and reconnect invalidation.
- REST snapshot + buffered WebSocket diff re-anchor.
- Exact decimal semantic validation.
- Freshness/depth/book-shape acceptance.
- Generation-fenced immutable snapshot publication.
- Deterministic offline tests and CI evidence.

Explicit non-goals:
- No changes to T0, canonical candle data, or T0 storage.
- No activation of T1 collector, VPS, systemd/autostart, exchange credentials or live exchange execution.
- No dashboard API as a trading/decision source.
- No Hummingbot integration.
- No all-symbol rollout or unrelated collector refactor.
- No T2 live reader or Core runner in this increment.
- No live orders. AI execution remains disabled.

## 2. Required state model

Use explicit per-symbol states; a state other than READY must never be exposed as a valid decision snapshot.

| State | Meaning | Snapshot readable by T2 |
|---|---|---|
| INITIALIZING | New symbol/session; no trusted book | No |
| BUFFERING | WS diffs are being collected before/while obtaining REST anchor | No |
| FETCHING_SNAPSHOT | REST anchor request in progress | No |
| REANCHORING | Rebuilding after reconnect, gap, malformed data or stale snapshot | No |
| VALIDATING | Candidate is assembled but acceptance checks are running | No |
| READY | Fully verified immutable snapshot published | Yes, read-only |
| BROKEN | Attempts exhausted or integrity cannot be proven | No |
| STOPPED | Explicit shutdown | No |

Transitions:
- Initial start: INITIALIZING → BUFFERING → FETCHING_SNAPSHOT → REANCHORING → VALIDATING → READY.
- Any WS disconnect/reconnect, sequence gap, invalid diff, buffer overflow, timestamp violation, or snapshot integrity failure: immediately READY → BROKEN → REANCHORING. Invalidate the currently published generation before processing post-event updates.
- On successful full re-anchor: VALIDATING → READY with a strictly larger generation and a new snapshotId.
- After max 3 attempts for one trigger: remain BROKEN; no stale fallback.
- A later diff alone cannot move BROKEN to READY. Only a new REST anchor and a fully verified diff chain can.

## 3. Sequence and reconnect contract

1. Tag every accepted WS message with a connection/session generation at ingestion. Messages from any older generation are discarded.
2. On reconnect, invalidate the prior READY snapshot synchronously before admitting any new-generation diff.
3. Buffer new-generation diffs, then fetch a fresh REST depth snapshot.
4. Discard buffered events with `u <= snapshotLastUpdateId`.
5. The first accepted event must satisfy exactly:
   `U <= snapshotLastUpdateId + 1 <= u`.
   Do not retain the additional legacy `PuAttach` bridge predicate as an alternative.
6. For every subsequent event, require `pu == previousAcceptedU`; require monotonic non-regression of `u`.
7. Any gap, malformed event, missing watermark, or buffer overflow invalidates the entire candidate and restarts from a fresh REST anchor. Never publish a partially applied candidate.
8. Use bounded re-anchor scheduling. For the single BTCUSDT path, allow at most one active REST anchor attempt per symbol; retain the V1 maximum of 3 attempts per trigger. Any broader multi-symbol concurrency/rate budget requires a separate capacity decision.

## 4. Decimal and book-shape validation

Keep exchange values as exact decimal strings from JSON decode through candidate construction and publication. No f32/f64 conversion in the trusted path.

For every REST snapshot and WS level:
- Accept only finite plain-decimal lexemes under a documented precision/length bound.
- Price must be strictly greater than zero.
- Quantity must be greater than or equal to zero; exactly zero means delete the price level.
- Reject negative values, exponent notation unless explicitly added to the contract, malformed values, overflow/overlong values and empty strings.
- Normalize only for comparison/key identity; preserve the original exact decimal lexeme for publication.
- Reject duplicate normalized price keys within one side of a single source event rather than silently overwriting.
- Reject conflicting duplicate entries and invalid side values.
- After applying a candidate, require at least 20 distinct valid bid levels and 20 distinct valid ask levels.
- Require best bid < best ask; reject locked or crossed books.
- Reject empty/incomplete sides, impossible quantities, and any candidate whose identity or sequence metadata is inconsistent.

Validation must be all-or-nothing. No mutation of the last accepted snapshot is permitted while a new candidate is being assembled.

## 5. Freshness and provenance

Each published snapshot must carry:
- `contractVersion`, `symbol`, `market`.
- `snapshotLastUpdateId`, `firstAppliedU`, `lastAppliedU`, `decisionWatermark=lastAppliedU`.
- `sourceTimestampMs`: exchange event timestamp of the last applied WS diff (source event time; document the exact Binance field used).
- `observedAtMs`: local wall-clock receive/validation publication observation time.
- `generation`, unique `snapshotId`.
- `continuity=VERIFIED`, `freshness=FRESH`, `complete=true`.
- Actual bid/ask depth and exact string levels.

Acceptance thresholds from frozen V1:
- Source age at decision time <= 2,000 ms.
- Observation age at decision time <= 2,000 ms.
- Future skew <= 250 ms.
- At least 20 bid and 20 ask levels.

The REST depth response itself does not supply a trustworthy exchange source timestamp. Therefore a REST anchor alone is not sufficient for a READY decision snapshot: the snapshot must be bridged by an exchange-timestamped WS diff, and the published source timestamp must be taken from the last applied diff. Do not substitute REST response time and label it exchange source time.

## 6. Generation fencing and immutable publication

- Maintain a monotonic per-symbol generation counter, incremented on every invalidation/re-anchor lifecycle.
- Every WS event, REST response, candidate and publish request is tagged with the generation that created it.
- Before candidate mutation and immediately before publication, verify that its generation is still current.
- A stale task or late REST response from an older generation must be rejected and must not overwrite a newer snapshot.
- Build candidate state off to the side; validate all metadata and levels; then publish one immutable snapshot in one atomic pointer/reference swap.
- Readers receive either the complete previous snapshot or the complete new snapshot, never a partially updated set of levels.
- Invalidation must make the old snapshot unavailable to decision consumers immediately; do not leave the old snapshot marked READY during re-anchor.
- Persistence/transport encoding must carry one complete snapshot envelope. If file-backed, write a temporary complete object, flush/sync as required, atomically rename/publish a manifest or equivalent commit marker, and make readers require the complete marker. Row-by-row CSV append is not a valid atomic V1 snapshot interface.
- Transport/storage technology remains OPEN; preserve the envelope, immutability, provenance and fail-closed guarantees regardless of implementation.

## 7. Read interface boundary

The V1 consumer interface must expose a single complete snapshot envelope and a read-only operation. It must not expose a reconstructed float ladder as an authoritative book.

The current dashboard `GET /api/orderbook/{symbol}` is NOT APPROVED for T2 decisions because it:
- Converts prices/quantities to binary floats.
- Omits contract version, source/observed timestamps, generation, snapshotId, sequence proof, freshness and completeness.
- Reconstructs from CSV files without enforcing `pu == previous u` in the current-book endpoint.

The exact transport/API and authentication details are deliberately left open for a separate interface-design decision. No direct T2 integration is part of this spec.

## 8. Deterministic offline test plan

All tests use synthetic fixtures, fake clocks, fake REST responses and controlled WS event sequences. No Binance network, exchange key, T0 database, VPS or persistent runtime is used.

| ID | Test group | Required cases | Expected result |
|---|---|---|---|
| D1 | Decimal parser | precision preservation; leading/trailing zeros; malformed/exponent/NaN/Inf/overlong; negative price; zero price; negative qty; zero qty deletion | Exact strings retained; invalid semantics rejected |
| D2 | Snapshot shape | duplicate normalized levels; conflicting duplicate; unsorted levels; <20 bid; <20 ask; locked/crossed; empty side | Candidate rejected; no publish |
| S1 | Initial bridge | exact `U <= L+1 <= u`; diff fully covered by snapshot; first event starts too late; event range does not cover L+1 | Only exact bridge accepted |
| S2 | Subsequent continuity | valid `pu == previous u`; gap; duplicate; regression; malformed U/u/pu | Only contiguous chain accepted |
| R1 | Reconnect | READY → disconnect → immediate invalidation; post-reconnect diff without REST anchor | Old snapshot unavailable; no READY |
| R2 | Re-anchor | fresh REST anchor + buffered bridge; gap during re-anchor; buffer overflow; retry 1/2/3; exhaustion | Publish only after complete verified chain; exhaustion remains BROKEN |
| G1 | Generation fencing | late old-generation WS event; late old REST response; old candidate attempts publish after new generation | All stale work rejected |
| F1 | Freshness | source age 1999/2000/2001 ms; observed age 1999/2000/2001 ms; future skew 249/250/251 ms | Threshold boundaries enforced exactly |
| A1 | Atomic publication | reader during candidate construction; injected validation failure; publish race with invalidation; concurrent readers | Reader sees complete old or complete new snapshot only; never partial/stale READY |
| X1 | Fail-closed integration seam | invalid/broken/stale snapshot passed to a fake T2 admission boundary | Consumer receives unavailable/error; no producer/ledger/risk callback |
| P1 | Property/state tests | randomized valid contiguous sequences and injected single-gap/reorder/duplicate faults | Valid chains reconstruct expected book; every corrupted chain fails closed |

Test requirements:
- Each case must assert state, generation, snapshot identity and side-effect count, not only returned error text.
- Include regression tests proving the legacy reconnect stale-level behavior and legacy PuAttach bridge are rejected.
- Run Rust unit/integration tests and formatter/Clippy/build checks in GitHub Actions on exact SHA.
- Save machine-readable test output, workflow run URL/ID, exact checkout SHA, artifact ID/name and independently verified artifact digest where artifact is available.
- Do not label T1 runtime behavior PASS based only on unit tests.

## 9. Acceptance gates

A future implementation can be marked **T1 SOURCE PASS (ISOLATED)** only if:
1. All D/S/R/G/F/A/X/P tests pass.
2. Exact source SHA is recorded and CI checks out that SHA.
3. No failed or skipped required test group.
4. Artifact/evidence is read back and its digest verified.
5. Independent review confirms no dashboard float path or legacy fallback is used.
6. The T1 PR branch history is reconciled before any merge proposal.

Even after T1 SOURCE PASS:
- T1 runtime behavior remains NOT VERIFIED until separately approved controlled runtime testing.
- T1→T2 real transport/integration remains BLOCKED until a separate interface and integration gate passes.
- Core runner, AI execution and live orders remain outside scope.

## 10. Required source changes (future, not authorized by this document)

Likely T1 change areas:
- `src/collectors/orderbook_manager.rs`: explicit lifecycle, bridge/sequence enforcement, candidate validation and publish gate.
- `src/websocket/connection_manager.rs` / `message_handler.rs`: per-symbol session generation, disconnect invalidation event, generation-tagged WS ingress.
- `src/models.rs`: V1 snapshot envelope and provenance metadata.
- `src/utils/decimal.rs`: strict semantic decimal validation (retain exact string operations).
- `src/utils/csv_writer.rs` or a new snapshot store: complete atomic snapshot persistence protocol.
- Tests adjacent to each owner module plus dedicated BTCUSDT V1 integration tests.

No code in these paths has been changed by this design exercise.
