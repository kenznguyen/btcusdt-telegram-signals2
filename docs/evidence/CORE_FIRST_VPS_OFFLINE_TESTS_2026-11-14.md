# Core First — bounded offline VPS tests — 2026-11-14

## Scope
Owner-run, bounded offline test execution on replacement test VPS. Exactly two previously reviewed unittest modules; no discovery, installation, database, service, exchange, or runtime launch.

## Source identity
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/core-operational-proof-20261112`
- Exact checkout SHA: `b92bb75b00b6f91c39c1b78fafab5cd1c77d8fde`
- Test blobs:
  - `pipeline/test_core_signal.py`: `a946716604e2e1a74b0e32f0aae5d07b820f2cbf`
  - `pipeline/test_core_strategy.py`: `a0d5b46845d3fde006ed817fe21bdd8b6546c1d1`
- Producer blob:
  - `pipeline/core_strategy.py`: `0be512d99b4302077ab79879184b74949f0feaaa`

## Execution
- Interpreter: `/home/ubuntu/.venvs/btcusdt-core-runtime/bin/python`
- Environment: clean `env -i`; `PYTHONPATH=.`; `PYTHONDONTWRITEBYTECODE=1`; `AI_EXECUTION_ENABLED=false`.
- Command: `python -m unittest pipeline.test_core_signal pipeline.test_core_strategy -v`
- Result: **12/12 PASS**, 0 failures, 0 errors; elapsed `0.040s`.
- `pipeline.test_core_signal`: 6/6 PASS.
- `pipeline.test_core_strategy`: 6/6 PASS.

## Assessment
- Bounded offline Core signal/strategy contract tests on the exact VPS checkout: **PASS**.
- Covered areas include LONG/SHORT/FLAT/WAIT normalization and validation, RSI/ADX/DI warmup, incomplete market windows, missing execution book fail-closed behavior, LONG entry, Smart DCA, and protective exits.
- Shared Risk Engine / persistent PaperLedger / Kill Switch runtime behavior: **NOT VERIFIED by this test set**.
- Core one-shot runtime implementation and VPS runtime readiness: **NOT VERIFIED**.
- AI Strategy remains out of scope and not implemented; `AI_EXECUTION_ENABLED=false`.
- No workflow or artifact was produced by this owner-run VPS test.

## Non-actions
No package installation, SQLite/database access, T0 access, Bootstrap, One-shot/Runner launch, service/systemd/autostart change, exchange access, credential use, AI execution, live order, or real trading. The pre-existing untracked file on the VPS was preserved.

## Next step
Continue the remaining Core First readiness gap through a separately bounded, read-only review. Do not infer runtime readiness or authorize Bootstrap/Runner activation from this test PASS.
