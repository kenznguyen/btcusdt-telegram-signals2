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


## 2026-11-08 — T0 Candle Contract v1 API implementation (GREEN verification pending)

- Authorized scope: additive API response envelope/freshness only, on the existing branch `feature/t0-centralized-data-feeder-p1-20261101`.
- Exact implementation commit: `42fda132bf06edcf2cb5f5d3ea415fc3e7a47fc1` — `feat(t0): add versioned candle API envelope`.
- Follow-up self-review cleanup commit: `d88e3ddda0502708e64c4815ecae08ed707f4641` — `refactor(t0): simplify candle freshness helper`.
- Final source SHA: `d88e3ddda0502708e64c4815ecae08ed707f4641`; changed source `market_data/api.py`; final blob SHA `179c11b684b7ba28d2fe07e56c3a4a50a2b9dba1`.
- Implementation adds `contractVersion=1.0.0`, `schemaVersion=1`, `volumeUnit=BTC_BASE_ASSET`, dataset-level `source=ccxt.binanceusdm`, and the freshness object (latest expected/returned candle, close/availability times, observation age, close lag, evaluable flag).
- Public API window cap is now an independent `MAX_API_CANDLES=2000`; Store and write/sync limits are unchanged.
- Existing route, GET-only behavior, Bearer authentication, response errors, Store, DB, and Feeder code are unchanged.
- TDD RED baseline remains exact test SHA `9f5b9f12473ef5e25aa0caadf68c5230f3de2bb8`: 13 tests, 10 passed, 3 expected errors, as supplied by the user.
- **GREEN tests: NOT RUN / NOT VERIFIED.** No claim that the focused or full suite passes. The combined commit status currently exposes no checks; exact-head GitHub Actions run/job/log/artifact is **NOT VERIFIED**.
- Independent code review: additive-only diff confirmed; no Store or runtime changes. Runtime/API behavior remains unverified until tests execute.
- Verdict: **IMPLEMENTED / NOT VERIFIED** (not PASS).
- Next step: execute `python3 -m unittest market_data.test_api -v` on exact SHA `d88e3ddda0502708e64c4815ecae08ed707f4641`, then run the repository's full relevant test suite and capture exact GitHub Actions evidence where available. Fix only demonstrated failures on this branch.
- Restrictions: no T2 HTTP client/FreqAI migration in this increment; no T0 DB, Feeder, VPS, exchange, Data Quality Gate, T1/T2 runtime, deployment, promotion, or live execution. Keep `ai_execution_enabled=false`.


## 2026-11-08 — Freshness regression correction (verification pending)

- User-provided focused run at source SHA `d88e3ddda0502708e64c4815ecae08ed707f4641`: 13 tests, 12 passed, 1 failed. The sole failure was `test_contract_v1_empty_as_of_window_has_null_freshness_and_is_not_evaluable`; `latestExpectedOpenTimeMs` was incorrectly capped by the requested `endMs`.
- Root cause: `latestExpectedOpenTimeMs` is defined by the server generation clock and timeframe boundary, independent of the requested data window. Capping it at `endMs - interval` made an empty historical/as-of window report the wrong expected-candle timestamp.
- Fix commit: `e317b7dc02363db0600737a89442dd918559af3c` — `fix(t0): calculate freshness from server clock`.
- Changed file: `market_data/api.py`; blob SHA `81733c9b6de811cbebb2f5d472d41f37f337990c`.
- The helper now computes `floor(generatedAtMs / interval) * interval - interval` directly. Candle selection, `asOfMs` filtering, store, DB, and runtime are unchanged.
- Fix status: **IMPLEMENTED / NOT VERIFIED**. Required next check: `python3 -m unittest market_data.test_api -v` at exact SHA `e317b7dc02363db0600737a89442dd918559af3c`. No GREEN claim until user-provided test output and relevant CI evidence are reviewed.


## 2026-11-08 — Focused API tests GREEN on freshness fix SHA

- User-provided Termux verification checked out exact source SHA `e317b7dc02363db0600737a89442dd918559af3c`; detached worktree status was clean (`## HEAD (no branch)`).
- Command: `python3 -m unittest market_data.test_api -v`.
- Result: **13 tests, 13 PASS, 0 failures, 0 errors**, runtime 0.268s.
- The previously failing empty historical/as-of freshness case now passes, as do explicit contract identity/version, freshness timing, candle provenance, auth/read-only behavior, gaps, and storage compatibility tests in this focused module.
- Exact source tested: `e317b7dc02363db0600737a89442dd918559af3c`; `market_data/api.py` blob `81733c9b6de811cbebb2f5d472d41f37f337990c`.
- Focused test verdict: **PASS**. Overall API Contract v1 release verdict remains **NOT VERIFIED** pending broader relevant regression suite and CI evidence.
- GitHub combined status for this SHA returned no status entries; commit workflow-run lookup returned no runs. Therefore no exact-head Actions run/job/log/artifact is available to cite and CI is **NOT VERIFIED**.
- Next: run repository-wide or documented relevant regression suite on a clean checkout of this exact source SHA; record the exact command, output, and SHA. Do not infer full-suite PASS from the focused module.
- Runtime restrictions unchanged: no T2 HTTP/FreqAI migration, DB/Feeder/VPS/runtime, Data Quality Gate, consumer activation, deployment, or live execution. Keep `ai_execution_enabled=false`.
