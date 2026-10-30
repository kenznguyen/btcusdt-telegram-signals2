# PR68: manual recovery for RESERVED_UNBOUND (paper only)

This is a **safety incident**, not a retryable order failure. The process may have
crashed after the DCA reservation committed but before the intent binding
committed. An absent binding **does not prove** that no order was submitted.

1. Keep all new entry/DCA submissions disabled for the affected trade.
2. Preserve a read-only, consistent backup of both DCA SQLite and PaperLedger
   databases, WAL state, logs, and any external order acknowledgements.
3. Use `DcaStore.recovery_status(symbol, trade_id)`: `RESERVED_UNBOUND`
   always means `may_submit=false`, `manual_review_required=true`.
4. Inspect the paper journal for the symbol, trade, candle, submission
   timestamp and all candidate intent identifiers. Check both active and
   terminal orders, partial fills and actual net position. Missing history is
   **not** proof of no fill.
5. If the intent/fill cannot be uniquely established, leave the reservation
   consumed and pause the strategy. Never regenerate an intent or retry a DCA
   automatically.
6. Any manual state repair requires an independently reviewed, idempotent
   migration/audit record linking the original reservation to a proven
   order and its final fill. No such repair API is enabled by PR68.

The workflow never enables real orders. Stop intrabar reports record
`actual_fill_price=null` without an authoritative execution journal.
`full_core_parity_certified` stays false pending independent signoff.
