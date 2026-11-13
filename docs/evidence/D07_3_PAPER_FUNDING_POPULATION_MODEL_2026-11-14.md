# D07.3 — PAPER Funding Population Model

Date: 2026-11-14  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/core-operational-proof-20261112`  
Owner decision: PAPER funding simulation approved; no real Binance account access  
Disposition: **IMPLEMENTED — CI RESULT PENDING / END-TO-END NOT VERIFIED**

## Approved scope

Implement a deterministic expected funding population for the PAPER ledger using:
- explicit PAPER position snapshots for `STRATEGY_CORE`, `AI_FREQAI`, and `LEGACY_UNATTRIBUTED`;
- public BTCUSDT linear USDT-perpetual funding-rate observations, including the settlement mark price;
- exact Decimal arithmetic and deterministic event/payload identities.

No exchange credentials, private endpoints, account-specific data, network adapter, live orders, VPS, production database, T0 mutation, Runner/One-shot execution, or AI execution are in scope. `AI_EXECUTION_ENABLED=false` remains mandatory.

## Formula and sign convention

For each strategy position at each funding settlement:

`funding_cost_quote = signed_position_base × mark_price × funding_rate`

- Positive result: PAPER funding cost (deducted from equity).
- Negative result: PAPER funding credit.
- Zero position: no funding event.
- No exchange-rounding compatibility is claimed; the calculation is a deterministic internal PAPER model.

The convention matches the existing ledger's equity equation, which subtracts `funding_quote`.

## Implemented contract

Added `paper_execution/funding_model.py` and `paper_execution/test_funding_model.py`.

The builder:
- validates a closed schema for position snapshots and market funding observations;
- accepts BTCUSDT only and enforces the declared half-open interval `[startAtMs,endAtMs)`;
- selects the latest position snapshot at or before each settlement for every strategy ledger;
- fails closed if a strategy snapshot is missing or older than the default 60-second maximum age;
- rejects duplicate strategy/time snapshots, duplicate settlement observations, binary floats, non-finite values, invalid marks and unknown fields;
- computes amounts with Decimal precision 80 and deterministic canonical payload hashes, event IDs and population snapshot ID;
- emits the existing D07 `EXPECTED_FUNDING_EVENTS` population contract;
- caps inputs and generated event populations at 100,000.

The model's source is `paper_simulation:linear_usdt_perpetual`, and its population definition is `paper-linear-funding-v1`. This is distinct by declaration from the observed `paper_ledger:paper_funding_events` population; it does not prove real independence.

## Test-first and CI status

- Test contract was committed before the model implementation.
- Focused tests cover positive/negative rates, long/short sign, zero positions, latest as-of snapshot selection, future/missing/stale snapshots, duplicate inputs, scope/symbol checks, float rejection, invalid mark values, deterministic ordering, D07 schema compatibility, and reconciliation compatibility.
- TDD RED workflow result: **NOT VERIFIED** (no exact RED run has been retrieved).
- GREEN focused test result: **PENDING**.
- Full PaperLedger regression after the model change: **PENDING**.
- Exact implementation/test source at this documentation checkpoint: `bd0094764d30530d8c42ff8caab8691e2302a4d2`.
- The preceding D07.2 exact-SHA CI remains PASS: run [43517898457](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43517898457), source `831a3fc9fcaa9a59b1bdc277664ae5e5c92fcc71`, full PaperLedger 483/483 PASS, artifact `14082675019` (12,809 bytes; GitHub digest `sha256:774a8d86382f860abc1f58fa019c5a6b21f1ccdb0857c58140ba75bd481f6166`). This run predates D07.3 and does not test the new model.

## Explicit limitations / next gates

The builder currently receives position snapshots and public funding observations from its caller. It does not:
- reconstruct as-of position snapshots from the append-only execution journal/cutover snapshots;
- acquire public funding-rate history;
- persist generated expected events into the PAPER funding ledger;
- orchestrate reconciliation, VERIFIED coverage and account cutover end-to-end;
- prove public-data completeness, source freshness, issuer authenticity or true independence.

Next bounded work: implement a read-only position-history projection from the existing immutable PAPER execution journal and cutover snapshots; prove coverage/watermark sufficiency at each funding settlement; then test public funding observation ingestion using fixtures and reconcile generated expected events against persisted PAPER funding events. No runtime scheduler or live source connection is implied.

## Status

- D07.3 model implementation: **IMPLEMENTED; CI NOT VERIFIED**.
- D07 overall: **PARTIAL**.
- Actual public-source completeness/freshness/authenticity and independent provenance: **NOT VERIFIED**.
- Production bootstrap: **BLOCKED / NOT APPROVED**.
- VPS, production DB, T0, Runner/One-shot, credentials and orders: **NOT TOUCHED**.
