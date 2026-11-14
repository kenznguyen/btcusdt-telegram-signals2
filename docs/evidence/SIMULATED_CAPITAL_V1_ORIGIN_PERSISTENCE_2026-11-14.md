# SIMULATED_CAPITAL_V1 — immutable origin persistence increment

Date: 2026-11-14  
Branch: `feature/core-operational-proof-20261112`  
Implementation source commit: `d7be89a09c660a4a43b3de0a739d67558b65152a`

## Scope

Implement the isolated persistence primitive for the owner-approved simulated-capital origin:

- Validate exact contract bytes with the existing `SIMULATED_CAPITAL_V1` validator.
- Store the exact contract SHA-256, fixed SIMULATED/PAPER identity, 100 USDT initial amount, deterministic seed event ID, initialization timestamp, owner-approved source and record digests.
- Store the synthetic initial seed in `paper_simulated_capital_seed_events`, not in `paper_funding_events`.
- Add UPDATE/DELETE rejection triggers to both origin and seed records.
- Make duplicate initialization idempotent; restart verification uses the persisted original timestamp and fails closed on contract/schema/record mismatch.
- Use `BEGIN IMMEDIATE` when the helper owns the transaction; when composed inside an existing transaction, use a savepoint and require the caller to have acquired the write lock.

## Changed files and source evidence

| File | Blob SHA |
|---|---|
| `paper_execution/simulated_origin.py` | `6c5dd0452021b42a01189ecb09b0a2f8043dd7ef` |
| `paper_execution/test_simulated_origin.py` | `ea53ed0540ba9f84ec1c1f5e69b40014e79a62f2` |
| `.github/workflows/simulated-capital-v1-contract.yml` | `be9b90d2cd3b24b4e2babb88b6de159523c79ee2` |

Test-first evidence:
- Test specification commit: `917f69b06961b5255431c0e9d0423cb3411aadce`.
- Initial RED: workflow run `43602447934` failed because `paper_execution.simulated_origin` did not exist.
- Behavioral RED: workflow run `43602539809` exposed restart timestamp mismatch and validator error-code wrapping.
- GREEN source: `d7be89a09c660a4a43b3de0a739d67558b65152a`.
- GitHub Actions run: `43602607051` — [SUCCESS](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43602607051).
- Job: `132470399215` — SUCCESS.
- CI source SHA: `d7be89a09c660a4a43b3de0a739d67558b65152a`.
- Verification: Python 3.12 py_compile PASS; existing contract tests 6/6 PASS; simulated-origin tests 6/6 PASS; total 12/12 PASS.
- Workflow artifacts: none.

## Status

- Immutable origin/seed persistence primitive: **PASS WITHIN ISOLATED TEST SCOPE**.
- Exact-byte contract hash binding: **PASS**.
- Duplicate initialization/restart timestamp invariance: **PASS**.
- UPDATE/DELETE protection: **PASS**.
- Invalid contract and missing account fail-closed: **PASS**.
- Account creation + origin + seed + UTC daily baseline + HWM as one complete initialization transaction: **NOT IMPLEMENTED**.
- Integration into `PaperLedger` or any existing ledger: **NOT IMPLEMENTED**.
- Contract-bound 1% per-order margin admission and shared exposure/Kill Switch integration: **NOT IMPLEMENTED**.
- Existing funded-account migration/Bootstrap compatibility: **NOT VERIFIED**.
- PAPER Ledger readiness: **BLOCKED / NOT VERIFIED**.

## Safety boundary

Tests use disposable in-memory SQLite only. No existing DB, production schema, migration, Bootstrap, Runner, VPS, T0, exchange, AI execution, live trading or real order was accessed or changed. The new helper is not wired into runtime and does not authorize order admission.

## Next step

Implement test-first integration into a disposable PaperLedger fixture. The next bounded test set must prove one-time creation of account + origin + seed + daily baseline + HWM under a single `BEGIN IMMEDIATE` transaction, rollback on partial failure, restart verification, preservation of the funded-account Bootstrap/cutover path, and no synthetic seed insertion into funding history. Then wire contract-bound 1% per-order admission only after that lifecycle is proven. Do not run against an existing operational database.
