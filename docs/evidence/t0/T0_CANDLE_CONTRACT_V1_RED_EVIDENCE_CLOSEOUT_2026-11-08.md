# T0 Candle Contract v1 — RED Evidence Closeout

- Date: 2026-11-08 (Asia/Ho_Chi_Minh)
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Initial tested source SHA: `0165fcad16a422f0ba7a6b833cc87eef8a626ca7` (superseded by the corrected rerun below).
- Corrected tested source SHA: `9f5b9f12473ef5e25aa0caadf68c5230f3de2bb8`.
- Test execution environment: user-provided Termux output, Android.
- Test command: `python3 -m unittest market_data.test_api -v`.
- Corrected test result: 13 tests; 10 passed; 3 errors; 0 assertion failures; duration 0.357s.
- GitHub Actions: NOT VERIFIED for this local execution; no exact-head CI run/artifact is recorded here.

## 1. Exact source and test evidence

The first execution was detached at `0165fcad...` and is retained as historical evidence only. The volume assertion was corrected in commit `9f5b9f12473ef5e25aa0caadf68c5230f3de2bb8`; GitHub branch comparison confirmed this commit is the branch head. The user then fetched the updated remote-tracking ref and confirmed both `origin/feature/t0-centralized-data-feeder-p1-20261101` and detached HEAD equal the corrected SHA. The worktree status was clean (`## HEAD (no branch)`).

The corrected user-provided test output confirms:
- 10 tests passed, including the corrected canonical volume assertion.
- Exactly 3 contract envelope/freshness tests errored as expected.
- No remaining assertion failure.

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

- Exact P1 source identified and corrected rerun SHA confirmed: PASS.
- Local test execution evidence received: PASS (user-provided Termux output).
- Existing regression + corrected candle provenance/volume assertions: PASS (10/10).
- Contract v1 envelope/freshness RED: CONFIRMED (3 errors: missing `contractVersion`, two missing `freshness`).
- Volume precision mismatch: RESOLVED by changing the test expectation to canonical `"2.5"`; production storage semantics unchanged.
- GitHub Actions exact-SHA evidence: NOT VERIFIED / no run recorded for this local execution.
- API implementation: NOT CHANGED.
- T2 HTTP migration: NOT STARTED.
- T0 runtime, Feeder, canonical DB, exchange connection, and data sync: NOT TOUCHED / NOT AUTHORIZED.
- Live execution: DISABLED; `ai_execution_enabled=false`.

## 5. Next authorized engineering step

The corrected RED baseline is now established at exact SHA `9f5b9f12473ef5e25aa0caadf68c5230f3de2bb8`: 10 passed, 3 expected errors. The next code step is to implement the additive Contract v1 response envelope under TDD GREEN on this same branch, but the contract design explicitly requires corresponding user authorization before code changes.

Do not change storage precision semantics, create a PostgreSQL migration, run Data Quality Gate, activate T1/T2 runtime, or modify the production Feeder as part of this closeout.
