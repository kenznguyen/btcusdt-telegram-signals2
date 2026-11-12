# AI Ledger CANCEL — transaction-path source review

Date: 2026-11-12 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Review HEAD: `d16f29e5d98a5d9019e207a5e3e0b90663fd7003`
Parent test-contract HEAD: `4efb126748cd77b418c7a117ebd36a5404e9cc5a`
Type: read-only source/test review; no implementation authorization
Disposition: **REQUEST CHANGES — CANCEL transaction boundary is not safe to promote; GREEN implementation NOT AUTHORIZED**

## 1. Scope and exact source

Reviewed only the AI Ledger CANCEL contract and the source paths needed to understand it:

| Path | Exact Git blob |
|---|---|
| `paper_execution/ledger.py` | `84597a8815c62bcddaa63fd3d2fcd890510931b6` |
| `pipeline/api.py` | `835a17dd062a2494f1adce981b7f411167afbf45` |
| `paper_execution/test_dual_ledger_red.py` | `f612c5454ad878511f80136ed565acd4296ed2a0` |
| `paper_execution/test_dual_strategy_api_red.py` | `e6c32e6897ed3b303954a0f114be247e21dbef38` |

The branch is 11 commits ahead and 0 behind source baseline `ef97abec1b832ae553c1f4c1b461ae13073c6628`. The additional commit after the test-contract HEAD is documentation-only (`d16f29e...`). No production source changed in this review.

## 2. Existing contract and evidence

The exact-head workflow is run `43178245969`, job `131047618684`, tested source SHA `4efb126748cd77b418c7a117ebd36a5404e9cc5a`:

- Python compile: PASS.
- Focused RED contract: 0 errors; 5 distinct failing tests (the three reservation/order integrity cases, AI CANCEL without fresh leverage, and the pre-existing AI evaluate routing case).
- Account-wide expiry of an expired AI reservation triggered by Core CANCEL: PASS.
- Non-expired AI reservation isolation during Core CANCEL: PASS.
- Repeated CANCEL idempotency: PASS.
- Full `paper_execution` regression: skipped because the focused stage failed.
- Artifact ID `13925815485`; SHA-256 `d8f5c019ed93cc5d3936fea2c9db725759961b79c09eb2867927806320415a07`.

This review is static/read-only. No test or compile command was rerun.

## 3. Required findings

### R1 — Missing reservation is silently accepted for an active dual-strategy order

`PaperLedger.cancel()` reads `reservationId` from the order document, but if no reservation row is found it still commits the order as CANCELED and writes a CANCEL audit event. An active dual order without a reservation must fail closed and roll back.

### R2 — Reservation ownership is not bound to the persisted order

The current lookup reads only `remaining_notional_quote` by `reservation_id`. It does not verify the reservation's `intent_id`, `strategy_id`, or `account_id` against the order's persisted columns/document before releasing it. A reservation belonging to another strategy or intent can therefore be released by the wrong order.

The existing schema already contains the required identity fields:
- `paper_orders`: `intent_id`, `account_id`, `strategy_id`, `reservation_id`, `status`, `document`.
- `paper_risk_reservations`: `reservation_id`, `account_id`, `intent_id`, `strategy_id`, `status`, remaining margin/notional and expiry.

No schema migration is indicated for this contract.

### R3 — AI CANCEL incorrectly depends on newly admitted leverage

The API resolves the order owner, then calls `ledger(strategy_id=owner)`. The AI ledger factory requires `admitted_leverage`; CANCEL has no need to run prediction, calibration, confidence admission or leverage selection. AI CANCEL consequently fails before the DB cancellation logic is reached.

### R4 — Owner resolution is outside the cancellation transaction

`resolve_order_strategy()` reads the owner on a separate read-only connection, then the selected ledger opens another connection and starts `BEGIN IMMEDIATE`. Owner resolution and mutation are not one atomic operation. The write transaction should resolve and validate the persisted owner itself to avoid a time-of-check/time-of-use gap.

### R5 — Account-wide expiry sweep has a related integrity gap

`_expire_scoped_reservations()` enumerates active reservations and resolves orders by `intent_id`, but does not compare reservation ID, strategy ID or account ID with the persisted order row before expiring both records. Since Core CANCEL is intentionally allowed to trigger global expiry housekeeping, each expired reservation must pass the same exact ownership binding before mutation. Any mismatch must abort the whole transaction, including any earlier expiry updates.

## 4. Bounded design recommendation

Use one CANCEL-only database transaction path for dual-schema orders. Do not construct `PaperLedger(strategy_id="AI_FREQAI")` with a fabricated/default leverage value.

The path should:

1. Validate the order identifier and timestamp before opening the write transaction.
2. Open the existing SQLite DB, enable foreign keys, and acquire `BEGIN IMMEDIATE`.
3. Confirm the already-applied dual-ledger schema without running migrations.
4. Resolve the target order and its persisted owner inside this transaction.
5. For an ACTIVE dual-strategy order, require a reservation and verify exact equality of:
   - reservation ID (order column and order document versus reservation primary key);
   - intent ID (order column/document versus reservation);
   - strategy ID (order column/document versus reservation);
   - account ID (order versus reservation);
   - persisted order status/document consistency.
6. Run account-wide expiry housekeeping in the same transaction. For each expired row, verify the same reservation/order identity before changing either record. Do not mutate non-expired reservations from the other strategy.
7. Re-read the target order after expiry housekeeping. If still active, atomically update the order and its reservation. Use a guarded reservation UPDATE with the exact reservation/intent/strategy/account identity and require exactly one affected row.
8. Preserve current release semantics: remaining margin/notional become zero; reservation status is CONSUMED when any quantity was filled, otherwise RELEASED.
9. Append one CANCEL audit event in the same transaction. Any missing/mismatched row or audit/write failure must roll back all target and expiry changes.
10. Preserve idempotency: a repeated CANCEL returns the already-canceled order without a second reservation release or CANCEL audit.
11. Keep the pre-dual MANUAL compatibility path unchanged unless a separately identified test requires otherwise.

Prefer a single shared helper used by both the API and direct dual-ledger `PaperLedger.cancel()` calls. The API must not perform a separate owner read and must not instantiate an AI ledger. The helper must not read predictions, confidence, calibration, leverage or market data.

Performance note: the current expiry sweep fetches every ACTIVE/PARTIAL reservation and filters expiry in Python. The existing expiry index can support a bounded query restricted to rows with `expires_at_ms < now`; consider this only if it preserves the NULL/unknown-expiry semantics and exact global-housekeeping contract.

## 5. Focused acceptance matrix for a future approved GREEN increment

- Active Core and AI order with valid reservation: cancel succeeds.
- Active dual order with missing reservation ID or missing reservation row: fail closed; no order/reservation/audit mutation.
- Reservation ID, intent ID, strategy ID or account ID mismatch: fail closed; no mutation.
- Order columns disagree with its JSON document: fail closed.
- Expired AI reservation is expired by Core CANCEL only after full identity validation.
- Non-expired AI reservation remains byte-for-byte/state-for-state unchanged by Core CANCEL.
- An expired reservation identity mismatch aborts and rolls back the entire account-wide sweep and target CANCEL.
- Partial fill produces CONSUMED with zero remaining reservation; no fill produces RELEASED with zero remaining reservation.
- Repeated CANCEL adds no release or audit event.
- Injected audit failure rolls back order and reservation changes.
- AI API CANCEL succeeds without prediction or newly admitted leverage and without constructing an AI PaperLedger.
- Legacy MANUAL cancellation behavior remains unchanged.

## 6. Separate issue — AI evaluate ordering

The existing AI evaluate route constructs `ledger(strategy_id="AI_FREQAI")` before `decide(...)` and before trusted admission/leverage exists. This is the separate failing test `test_ai_buy_while_core_wait_routes_only_to_ai_ledger_and_shared_risk_rejects`. Do not fix it by weakening the AI leverage requirement or by mixing it into the CANCEL-only transaction change. It requires a separate decision → admission context → admitted leverage → ledger construction → submit ordering review.

## 7. Five-axis review

| Axis | Result | Basis |
|---|---|---|
| Correctness | REQUEST CHANGES | R1–R3 reproduce the known contract gaps; R5 is a related expiry-integrity gap. |
| Readability | CONDITIONAL PASS | The current cancel method is short, but its implicit reservation fallback hides a critical invariant. |
| Architecture | REQUEST CHANGES | Cancellation should not depend on the full strategy ledger factory or AI admission context. |
| Security/integrity | REQUEST CHANGES | Reservation identity is under-validated and owner lookup is separated from mutation. |
| Performance | CONDITIONAL PASS | SQLite write transaction is bounded; expiry currently scans all active reservations rather than selecting expired rows through the existing index. |

## 8. Status and non-authorization

- Source review: complete for the four exact blobs listed above.
- Tests/compile in this review: NOT RUN; prior exact-head workflow evidence remains as recorded in §2.
- Production source changes: NONE.
- Schema/API/workflow/runtime/VPS/T0/T1/T2 changes: NONE.
- AI evaluate ordering: separate and unresolved.
- GREEN CANCEL implementation: **NOT AUTHORIZED**.
- Live trading/real orders: prohibited; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.

Next gate: Owner must explicitly approve a bounded implementation scope (exact files, shared helper/API integration, regression tests and focused/full test commands). Until then, preserve the RED tests and do not modify production source.
