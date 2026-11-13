# D07.3 — PAPER Funding Population Model

Date: 2026-11-14  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/core-operational-proof-20261112`  
Owner decision: PAPER funding simulation approved; no real Binance account access  
Disposition: **D07.3 MODEL + CI PASS / END-TO-END NOT VERIFIED**

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
- computes amounts with up to 80 significant digits per input and a 240-digit Decimal context, with non-rounding canonical formatting and deterministic payload hashes, event IDs and population snapshot ID;
- emits the existing D07 `EXPECTED_FUNDING_EVENTS` population contract;
- caps inputs and generated event populations at 100,000.

The model's source is `paper_simulation:linear_usdt_perpetual`, and its population definition is `paper-linear-funding-v1`. This is distinct by declaration from the observed `paper_ledger:paper_funding_events` population; it does not prove real independence.

## Test-first and CI status

- Test contract was committed before the model implementation.
- Focused tests cover positive/negative rates, long/short sign, zero positions, latest as-of snapshot selection, future/missing/stale snapshots, duplicate inputs, scope/symbol checks, float rejection, invalid mark values, deterministic ordering, D07 schema compatibility, and reconciliation compatibility.
- TDD RED was observed: run [43518943218](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43518943218), source `5052de6ae1958aa8314c2573406ecc93588abb02`, failed at the focused model test because the implementation module was intentionally not yet present.
- Initial GREEN run [43518984947](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43518984947), source `84a6b0d413bb46411dc7f18d3a3feb44cc458833`: 16/16 model tests and 499/499 full regression PASS.
- Final exact-source GREEN run [43519778241](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43519778241), source `8264fef6ad257411f18b14cba6ee3fdb4fb50e65`: 18/18 focused model tests and 501/501 full PaperLedger regression PASS.
- First complete model/test source checkpoint: `bd0094764d30530d8c42ff8caab8691e2302a4d2`; latest verified implementation/test source: `8264fef6ad257411f18b14cba6ee3fdb4fb50e65`.
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


## Verification addendum — 2026-11-14

- High-precision regression RED: run [43519711137](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43519711137), source `a7e028588786f1284559636b6caa2d71df5c0dfe`. It reproduced a real identity collision: two different 40-digit position inputs produced the same population snapshot ID because Decimal normalization used the default precision.
- Fix: `_decimal_text` now formats without context rounding; each input is capped at 80 significant digits; the calculation context is 240 digits to preserve exact products. Source SHA: `8264fef6ad257411f18b14cba6ee3fdb4fb50e65`.
- GREEN exact-source workflow: [43519778241](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43519778241), SUCCESS, exact source SHA `8264fef6ad257411f18b14cba6ee3fdb4fb50e65`.
- Focused D07 PAPER funding model tests: **18/18 PASS**. Existing bootstrap, D07 reconciliation, D07.2 provenance and persistence/coverage gates also PASS. Full PaperLedger regression: **501/501 PASS** in 141.759s.
- Artifact: `14081998893`, name `dual-ledger-bootstrap-proof-8264fef6ad257411f18b14cba6ee3fdb4fb50e65`, 13,907 bytes, GitHub ZIP digest `sha256:21d20f3079197433869fdcdfc4572ca925740c548f87a642453557bb70e0c252`, expires 2026-11-20T22:30:10Z.
- D07.3 model + CI: **PASS**. D07 overall remains **PARTIAL** because there is not yet a position-history projection, a public-rate response parser/provenance ingestion path, or an end-to-end staging/reconciliation run against persisted PAPER funding events from an independent producer. No network calls or real account data were used.


### As-of multi-settlement regression — 2026-11-14
- Added coverage for two funding settlements with changing strategy positions, verifying that each settlement uses the latest snapshot at or before its own timestamp.
- Exact-source workflow [43520315661](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43520315661): SUCCESS at SHA `29ff1274ba191f37660ecaa334ae5038d3247a36`.
- Focused model tests: **19/19 PASS**. Full PaperLedger regression: **502/502 PASS**.
- Artifact `14081429446`, 13,960 bytes, digest `sha256:d7f7ce308024ab9426be728381a48797ede00c27838b052e8de8adff8e9410a3`, expires 2026-11-20T22:34:01Z.
- D07.3 remains PASS. Next code-review item: replace repeated full position-snapshot scans per settlement with indexed as-of lookup to keep the 100,000-row bound computationally safe. This is a performance hardening change, not a change to funding semantics.
