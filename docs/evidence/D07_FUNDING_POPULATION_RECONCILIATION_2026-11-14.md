# D07 — Bounded Funding Population Reconciliation

Date: 2026-11-14  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/core-operational-proof-20261112`  
Implementation source SHA: `7d0d563275b693718a2a26c1069e08a78a3b0551`  
Disposition: **FOCUSED TESTS PASS; FULL REGRESSION PENDING; LIVE D07 NOT CLOSED**

## Approved scope

Owner approved implementation limited to synthetic tests and GitHub Actions. No real account statements, production DB, VPS, T0, Runner/One-shot or exchange orders are in scope.

## Implementation

Added:
- `paper_execution/funding_reconciliation.py`
- `paper_execution/test_funding_reconciliation.py`
- D07 focused test step and path filters in `.github/workflows/dual-ledger-bootstrap-contract.yml`
- Contract notes in `paper_execution/README.md`

The pure no-I/O API compares two separately declared event inventories over the same half-open time interval and quote currency. Each event requires a stable ID, timestamp, exact Decimal amount string and SHA-256 payload-hash reference. It reports MATCHED, MISSING, UNEXPECTED and DUPLICATE classifications; same-ID content mismatch appears as missing + unexpected. Unresolved discrepancy blocks `COMPLETE_WITHIN_DECLARED_POPULATION`. Inventories are capped at 100,000 events each.

TDD found and fixed two issues:
- binary float amounts were accepted by the first implementation; now only Decimal strings are accepted;
- a synthetic mismatch fixture used a non-hex digest; fixture corrected to a valid digest.

## CI evidence

- RED: [run 43509458044](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43509458044), source `c9c131b8cd419f0fc6e30a0d499963da81929f63`. Compile and bootstrap tests PASS; D07 focused tests exposed float amount acceptance and the invalid test fixture. Full regression skipped after focused failure.
- Intermediate corrected-fixture run: [43509510284](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43509510284), source `88a1d8a3afed05967aaa3947017dbafa9285c0e1`. D07 tests confirmed the fixture issue fixed; float-amount test correctly remained RED.
- GREEN candidate: [run 43509525978](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43509525978), exact source `7d0d563275b693718a2a26c1069e08a78a3b0551`. Compile PASS, bootstrap tests PASS, D07 focused tests PASS. At report creation, full PaperLedger regression step remained `in_progress`; no final workflow conclusion or artifact is claimed.

## Explicit limits

The result uses `independence=DECLARED_NOT_VERIFIED`, `globalCompleteness=NOT_VERIFIED`, `freshness=NOT_VERIFIED`, `issuerAuthenticity=NOT_VERIFIED`. Different caller-supplied population definition IDs, source labels and snapshot IDs do not prove actual independent enumeration or issuer identity. Payload hashes are compared as references; external statement bytes are not fetched or independently verified.

The API is not yet wired to `record_funding_coverage(status="VERIFIED")`, account equity cutover or `riskReady`. It writes no reconciliation audit record and cannot establish production account completeness. Therefore D07's live evidence requirement remains open, and production bootstrap remains blocked.

No VPS, production DB, T0, exchange credentials, Runner, One-shot or orders were touched. All data are synthetic CI fixtures. Paper-only restrictions remain in force.
