# Dual Reconstruction Verification Contract — Daily Baseline Epoch (2026-11-07)

## Status

**CONTRACT PROPOSAL — DOCUMENTATION ONLY; NOT APPROVED FOR SOURCE, SCHEMA, DATABASE, OR EPOCH IMPLEMENTATION.**

This contract defines the evidence and reconciliation requirements for a possible Paper-only Dual Reconstruction Anchor. It does not authorize persistent database access, external account imports, exchange connectivity, migration, HWM reset, epoch activation, or exposure increases.

The current operational policy remains Option A: unresolved legacy v1 baseline blocks progression and risk increases.

## 1. Purpose and terminology

The proposed gate must establish that one account state at an exact UTC boundary can be reconstructed without inventing missing economic events or risk references.

- **Replay A — event replay:** deterministically replays the complete immutable event stream for Core, AI, and Legacy.
- **Reconstruction B — independent snapshot reconstruction:** independently computes the same account and ledger state from a separately retained, immutable checkpoint/archive and its source evidence.
- **Evidence root:** the retained raw bytes, canonicalization rules, source identity, coverage metadata, and cryptographic digests from which a reconstruction is derived.
- **Boundary:** an exact UTC timestamp in the form YYYY-MM-DDT00:00:00.000Z.
- **Candidate anchor:** a proposed state; it is not active and must not affect risk readiness.

Two calculations over the same mutable SQLite rows, or two exports generated from the same mutable rows without an independently retained prior copy, are **not independent evidence**. Such a comparison may be reported as internal consistency only and must fail the independent-evidence gate.

## 2. Independence and provenance requirements

Replay A and Reconstruction B must have distinct evidence roots.

Each evidence root must retain:
1. Original source bytes or a canonical immutable event/checkpoint package.
2. SHA-256 digest calculated from the bytes actually retained and read.
3. Source identity, producer/version, account identity, quote currency, and schema/canonicalization version.
4. Capture/creation timestamp and economic coverage interval.
5. Record count, first/last sequence or event identity, and explicit gap/overlap report.
6. Immutable storage identity or independently retained artifact reference.
7. A manifest binding all component digests into one root digest.

At least one evidence root must have been retained independently before the reconciliation run. A digest copied from a mutable database field is not proof that original source bytes are authentic. A GitHub Actions artifact may preserve an evidence package, but the artifact must actually be retrieved and its payload bytes re-hashed before it is treated as verified.

If either path is derived from the same mutable source rows as the other, classify the result INTERNAL_CONSISTENCY_ONLY; do not call it independently verified and do not permit anchor eligibility.

## 3. Event classes and replay treatment

Every event must have:
- stable event ID and source ID;
- ledger owner (CORE_LEDGER, AI_LEDGER, or LEGACY_UNATTRIBUTED);
- event type and schema version;
- economic time event_at_ms;
- ingestion/recorded time;
- sequence or deterministic tie-break key;
- quote currency and signed amount/quantity where applicable;
- provenance digest and correction/supersession linkage, if any.

### 3.1 Required replayable event classes

| Class | Required treatment |
|---|---|
| Position fills | Apply signed quantity and fill price in deterministic order; preserve partial fills individually. |
| Position reductions and closures | Reduce only the owning ledger position; calculate realized PnL from that ledger's position state. |
| Reversals | Close/reduce the existing owner first; admit the reverse increase as a separate event and risk decision. |
| DCA fills | Apply only to the owning ledger and preserve each fill; never infer a DCA from a target price alone. |
| Fees | Apply explicit amount, currency, event time, source ID, and owner. Unknown fee currency/amount is not zero. |
| Funding | Apply each funding event exactly once with explicit amount, currency, event time, source and coverage. Missing funding is unknown, not zero. |
| Order lifecycle | Reconstruct accepted, open, partial, canceled, rejected, and completed states; preserve remaining quantity and reservation state at the boundary. |
| Reservations | Reconstruct pending exposure reservations and release events in sequence; do not count a fill and its consumed reservation twice. |
| Mark/equity observations | Use only source-identified marks valid at the boundary; retain mark ID, instrument, timestamp, and payload digest. |
| Legacy adjustments | Include account-level historical realized PnL/fees/funding only when amount, sign, currency, and provenance are known; never assign them to Core or AI without immutable evidence. |
| Corrections/reversals of records | Apply only explicit linked correction events. Preserve original records and the correction chain; never silently overwrite history. |

### 3.2 Events that cannot be inferred

The following must not be synthesized:
- missing fills from order intent or candle prices;
- missing fee or funding events from defaults or assumptions;
- ownership from current strategy configuration;
- canceled/rejected order quantities as executed fills;
- reservations from an order whose acceptance/state is unproven;
- a mark at the boundary by interpolating a later/earlier mark;
- missing historical HWM, daily baseline, readiness, or risk-state version;
- unknown Legacy amounts or owner attribution.

Any required unknown amount, missing event, unexplained sequence gap, or contradictory ownership blocks anchor eligibility.

## 4. Deterministic ordering and boundary semantics

For each evidence root, events are ordered by:
1. event_at_ms ascending;
2. source-defined sequence ascending;
3. stable event ID ascending as the final deterministic tie-breaker.

If two events share economic time and the source does not provide a trustworthy sequence/tie-break rule, the affected state is ambiguous and the gate is BLOCKED. Do not select an order based on database row order or retrieval order.

Boundary rules:
- Events with event_at_ms < B belong to the pre-anchor history and must be included in the opening-state reconstruction.
- Events with event_at_ms >= B belong to the new epoch.
- Events exactly at B must not be counted in both opening state and post-boundary replay.
- An event ingested after the reconciliation run but with event_at_ms < B is a late event. It invalidates the candidate until both paths are replayed and the reconciliation is repeated with a new manifest.
- All three ledgers and the account-level state must refer to the same exact boundary and compatible quote currency.

A mark must be explicitly valid at B. A nearby timestamp is not an exact-boundary mark unless a separately approved market-data contract defines and verifies that mapping.

## 5. State fields that must reconcile

For each of Core, AI, and Legacy, compare:
- instrument and signed position quantity;
- average entry price and position direction;
- isolated/cross margin attribution as represented by the paper model;
- realized PnL;
- unrealized PnL using the same verified boundary mark;
- fees by currency and provenance;
- funding by currency and provenance;
- open orders, remaining quantities, and reservation amounts;
- ledger-level equity contribution and all adjustment components.

At account level, compare:
- opening/effective equity;
- wallet/cash balance and liabilities if represented by the authoritative account model;
- aggregate Core + AI + Legacy position and exposure totals;
- aggregate realized/unrealized PnL, fees, and funding;
- total gross exposure and outstanding reservations;
- source mark identity and dataset identity;
- event counts, coverage intervals, and evidence-root digests.

Account equity must be recomputed from explicit components. It must not be accepted merely because both paths report the same precomputed equity field.

## 6. Numeric reconciliation tolerances

Tolerances must be fixed before reading candidate results. They must be derived from declared instrument/account precision, not tuned to make a candidate pass.

For each compared value:
- **Quote-currency balances, equity, realized/unrealized PnL, fees, and funding:** absolute residual no greater than one smallest supported quote-currency unit, after both paths use the same currency and rounding rule.
- **Position quantity:** absolute residual no greater than half the instrument's declared quantity step.
- **Average entry and mark price:** absolute residual no greater than half the instrument's declared price tick.
- **Reservation quantity/notional:** residual must be within the same quantity/notional precision rules, and every open order must match by stable identity and remaining quantity.
- **Counts, IDs, ownership, currency, event coverage, sequence, status, and hashes:** exact match; no numeric tolerance.
- **Gross exposure and account equity:** recompute from reconciled components; residual no greater than one quote-currency minor unit.

No percentage tolerance, relative tolerance, or broad floating-point epsilon may override these limits. Use decimal arithmetic and explicit rounding modes. If instrument precision or quote-currency minor unit is unavailable, the tolerance is undefined and the gate is BLOCKED.

A tolerance pass does not waive missing provenance, event gaps, late events, or identity mismatches.

## 7. Required fail-closed conditions

The reconciliation gate returns BLOCKED if any of the following applies:

1. Either evidence root is missing, mutable, inaccessible, or not byte-verified.
2. The two paths do not have genuinely independent retained evidence roots.
3. Account identity, quote currency, boundary, schema version, or canonicalization version differs.
4. Any required ledger (Core, AI, Legacy) is absent, duplicated, or not fully attributable.
5. Any required event stream has a gap, unexplained overlap, invalid sequence, duplicate event, or incomplete coverage.
6. A late pre-boundary event appears after the candidate was computed.
7. An open/partial order, reservation, cancellation, or fill cannot be reconstructed.
8. Fee/funding amount, currency, owner, source, or coverage is unknown where required.
9. A required mark is stale, missing, not exact-boundary-valid, or lacks source payload proof.
10. A position, PnL, fee, funding, reservation, equity, or exposure residual exceeds its predeclared tolerance.
11. Any arithmetic is non-finite, overflows, uses an implicit default, or depends on an unverified rounding rule.
12. A source digest, event identity, correction chain, or manifest digest conflicts.
13. The current account risk state is assumed to represent historical HWM/version/readiness without an immutable snapshot at the relevant time.
14. A Kill Switch, risk-state integrity, or account-readiness input is missing or contradictory.
15. A candidate is retried with conflicting evidence under the same idempotency identity.

BLOCKED means no candidate activation and no risk-increase permission. Only independently governed risk-reducing actions remain eligible under existing controls.

## 8. Gate result vocabulary

The verifier must report one of these explicit outcomes:

- INTERNAL_CONSISTENCY_ONLY: two computations share a mutable evidence root; not eligible for independent verification.
- BLOCKED: required evidence is missing, contradictory, late, unauthenticated, or outside tolerance.
- RECONCILED_CANDIDATE: both independent paths reconcile and all mechanical checks pass; this is eligibility for human review only.
- APPROVED_FOR_ACTIVATION: reserved for a separate explicit policy approval and separately authorized activation operation. The verifier itself must never emit this status.

The report must include both root digests, boundary, all per-field residuals, tolerance definitions, event coverage, late-event status, ledger breakdown, and every failed invariant. No summary PASS may hide a failed sub-check.

## 9. Relationship to Epoch, HWM, and Daily Loss

Even RECONCILED_CANDIDATE does not:
- reconstruct missing historical HWM or Max Drawdown;
- convert or rewrite v1 baseline/audit rows;
- authorize a new epoch or HWM reset;
- initialize a daily-loss baseline;
- change risk readiness or active epoch;
- permit exposure increases.

If a future policy separately approves a new epoch, its HWM and first daily-loss baseline may begin at the verified opening equity at B, explicitly labeled as a new measurement period. Historical drawdown continuity remains unavailable and must be disclosed.

## 10. Implementation and approval gates

Before any implementation proposal:
1. Identify the actual independently retained evidence sources and prove byte-level access without opening the persistent account DB.
2. Produce sample manifests and deterministic replay vectors using synthetic/temporary fixtures only.
3. Define and test canonical decimal arithmetic, ordering, event coverage, and correction handling.
4. Demonstrate the independent-root rule with a negative test using two readers over one mutable database.
5. Demonstrate fail-closed behavior for every condition in Section 7.
6. Review data retention, artifact immutability, and source authenticity.
7. Obtain separate explicit approval for source/tests, schema/migration, persistent DB access, policy/HWM reset, and activation.

## Restrictions

No source or test implementation, schema migration, persistent account DB opening, backfill, external account import, exchange connection, production backtest, deployment, merge, epoch activation, HWM reset, or live order is authorized by this contract. T0 remains paused. PAPER-only; ai_execution_enabled=false.
