# T0 Candle Contract v1 — RED Evidence Closeout

- Date: 2026-11-08 (Asia/Ho_Chi_Minh)
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Tested source SHA: `0165fcad16a422f0ba7a6b833cc87eef8a626ca7`
- Test execution environment: user-provided Termux output, Android
- Test command: `python3 -m unittest market_data.test_api -v`
- Test result: 13 tests; 9 passed; 3 errors; 1 failure; duration 0.585s.
- GitHub Actions: NOT RUN. No workflow run or artifact exists for this local execution.

## 1. Exact source and test evidence

The test worktree was created detached at the exact branch SHA above. The user-provided output confirms:
- 9 existing regression tests passed.
- 4 newly added Contract v1 assertions did not pass.

Relevant source blobs at the tested ref:
- `market_data/test_api.py`: blob `5ac29dd8ba65ae9cc13d890bdd39c6f0b3845896`
- `market_data/api.py`: blob `83b35c876e3154d6284f0bc3e7e30aff48e48ba0`
- `market_data/store.py`: blob `4e1b0c54bd56455abe5be0e5c7d0807e63e0bc78`
- Contract design: `docs/architecture/T0_READ_ONLY_CANDLE_CONTRACT_V1_2026-11-08.md`, blob `dd19fe6f933a5c8b2a192f7bc65b64a00f205e9d`

## 2. Failure classification

| Test | Observed result | Classification |
|---|---|---|
| `test_contract_v1_response_has_explicit_version_and_market_identity` | `KeyError: contractVersion` | Valid RED: API response lacks required version/identity envelope fields. |
| `test_contract_v1_freshness_reports_exact_observation_and_close_lag` | `KeyError: freshness` | Valid RED: API response lacks required freshness summary. |
| `test_contract_v1_empty_as_of_window_has_null_freshness_and_is_not_evaluable` | `KeyError: freshness` | Valid RED: empty-window response lacks required null freshness shape. |
| `test_contract_v1_candle_has_explicit_exclusive_close_and_quality_provenance` | Expected volume `2.50`, got `2.5` | Test assertion/specification mismatch; do not count as a confirmed implementation RED until reconciled. |

## 3. Volume precision reconciliation

The contract design requires decimal strings and says the API must expose the exact stored decimal representation; it does not require preservation of input trailing-zero scale.

The test fixture constructs a Candle with volume string `2.50`. In `market_data/store.py`, `_decimal()` converts the Decimal to fixed-point text and strips trailing fractional zeros. Candle validation applies this canonicalization before persistence. Therefore the stored canonical value is `2.5`, and the API returning `2.5` is consistent with the current storage representation.

The assertion `self.assertEqual(candle["volume"], "2.50")` is not supported by the documented contract or current canonical storage semantics. It should be reconciled to assert `"2.5"` (or changed only if a separately reviewed contract decision explicitly requires scale preservation). No such scale-preservation decision is present in Contract v1.

**Conclusion:** 3 valid Contract v1 RED cases; 1 test assertion mismatch requiring correction. Preserve decimal strings and do not convert through JSON floats.

## 4. Closeout verdict

- Exact P1 source identified: PASS.
- Local test execution evidence received: PASS (user-provided Termux output).
- Existing regression tests: PASS (9/9).
- Contract v1 envelope/freshness RED: CONFIRMED (3 tests).
- Volume precision RED: NOT CONFIRMED; assertion mismatch identified.
- GitHub Actions exact-SHA evidence: NOT RUN.
- API implementation: NOT CHANGED.
- T2 HTTP migration: NOT STARTED.
- T0 runtime, Feeder, canonical DB, exchange connection, and data sync: NOT TOUCHED / NOT AUTHORIZED.
- Live execution: DISABLED; `ai_execution_enabled=false`.

## 5. Next authorized engineering step

Correct the volume assertion to match the documented canonical decimal representation, then run the focused API suite again to establish a clean RED baseline with only the three genuine envelope/freshness failures. After that, implement the additive Contract v1 response envelope under TDD GREEN on this same branch.

Do not change storage precision semantics, create a PostgreSQL migration, run Data Quality Gate, activate T1/T2 runtime, or modify the production Feeder as part of this closeout.
