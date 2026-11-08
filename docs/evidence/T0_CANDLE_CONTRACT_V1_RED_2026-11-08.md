# T0 Read-only Candle Contract v1 — RED Test Increment

- Date: 2026-11-08
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Scope: add API contract tests only; no production implementation.
- Test commit: `d7bda566fdaa32f060a8d08cea9ee2250847cb3b`
- Changed file: `market_data/test_api.py`
- Test count added: 4.

## Tests added

1. `test_contract_v1_response_has_explicit_version_and_market_identity`
   - Requires contractVersion 1.0.0, schemaVersion 1, fixed Binance USD-M BTCUSDT identity, volume unit, source, request range, nullable asOfMs, and SHA-256 dataset version format.
2. `test_contract_v1_freshness_reports_exact_observation_and_close_lag`
   - Uses a deterministic server clock and asserts latest expected/returned candle, close boundary, first-observed timestamp, observation age, close lag, and evaluable state.
3. `test_contract_v1_empty_as_of_window_has_null_freshness_and_is_not_evaluable`
   - Requires empty-result freshness fields to be null and evaluable=false.
4. `test_contract_v1_candle_has_explicit_exclusive_close_and_quality_provenance`
   - Requires exclusive close boundary, FIRST_OBSERVED, VALIDATED, source identity, and decimal-string volume.

## RED assessment

- Source inspection of `market_data/api.py` at the same branch shows that its 200 response currently adds only `generatedAtMs` to the Store result.
- The current response has no `contractVersion`, `schemaVersion`, `volumeUnit`, or `freshness` envelope. Therefore the new tests are expected to fail against the current implementation.
- **Important verification limit:** the test suite was not executed in this increment. RED is **EXPECTED BY SOURCE INSPECTION / NOT EXECUTED**, not a confirmed test-run result.
- No GitHub Actions run ID, job, artifact, or test log is available for this increment. Workflow execution is **NOT RUN / NOT VERIFIED**. Do not claim a RED run or PASS.
- Repository local test command documented in README: `python3 -m unittest market_data.test_store market_data.test_sync market_data.test_api -v`.

## Safety and scope

- No production source changed.
- No T2 HTTP client or FreqAI bridge migration.
- No direct T0 canonical DB access, DB mutation, Feeder action, exchange connection, market-data sync, T0 Data Quality Gate, or T0/T1/T2 runtime activation.
- No strategy, risk, leverage, or execution behavior changed.
- `ai_execution_enabled=false`; paper-only boundary remains unchanged.

## Next step

Run the focused API test suite through the repository's approved GitHub Actions workflow and record exact checked-out SHA, run/job IDs, logs, and artifact metadata. Only after confirming the expected RED result should the next separately authorized increment implement the minimum T0 API envelope needed to turn these tests GREEN.
