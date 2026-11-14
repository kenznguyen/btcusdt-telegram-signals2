# SIMULATED-only Shared Order Admission V1 — Implementation and CI Evidence

Date: 2026-11-14
Branch: `feature/core-operational-proof-20261112`
Implementation source SHA: `a65025f517affbba46756d020150b4f6ddff31bb`
Test specification commit: `ff573a71e6a2c6d9d79694b4edcba8fc4c452c1f`

## Scope

Additive writer-side support for a valid SIMULATED-only account to pass the same shared PAPER risk admission checks without fabricated funded-account cutover or funding evidence. The funded-account admission path remains unchanged.

No operational database, VPS, T0, Bootstrap runtime, Runner, exchange, AI execution, live order, or real trade was used.

## Implementation

- `PaperLedger._submit_scoped` identifies a SIMULATED account only through `verify_simulated_equity_origin`.
- It validates the current UTC daily-baseline provenance chain using `verify_simulated_daily_baseline_provenance`.
- A verified SIMULATED account may proceed without a funded cutover row or funding-coverage proof. The funded branch still requires both.
- The existing shared risk checks remain in force: risk readiness, mark freshness, account equity, drawdown, daily loss, shared exposure/reservations, per-order 1% margin ceiling, and Kill Switch.
- Core ENTRY and DCA use the same writer admission and reservation path. Existing one-DCA-per-position lifecycle behavior is not changed.
- Test risk limits now match the approved simulated contract: max drawdown 10%, max daily loss 2 USDT, max exposure 10 USDT.

Source blob:
- `paper_execution/ledger.py`: `4eca46c42a54d48afe067c3acd14fe305fc188c1`

Test blob:
- `paper_execution/test_simulated_order_admission.py`: `c20e63f095ffb0460ddbcbd4a03fadcbd452b95a`

## TDD evidence

- RED test commit: `ff573a71e6a2c6d9d79694b4edcba8fc4c452c1f`.
- RED workflow run: [43608778212](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43608778212), source SHA `ff573a71e6a2c6d9d79694b4edcba8fc4c452c1f`, 4 expected failures across Core ENTRY, DCA, and Kill Switch tests. The writer returned `RISK_INPUTS_UNAVAILABLE` because it still required funded cutover.
- GREEN implementation source SHA: `a65025f517affbba46756d020150b4f6ddff31bb`.
- Simulated Capital V1 workflow: [43608805148](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43608805148), job `132489066899`, SUCCESS; `py_compile`, JSON parse and 32/32 unit tests PASS.
- PaperLedger compatibility workflow: [43608805101](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43608805101), job `132489120079`, SUCCESS; 144/144 tests PASS, including funded dual-ledger ENTRY/DCA reservation and risk-control regression.
- No workflow artifact was uploaded for these two runs.

## Disposition

- SIMULATED Core ENTRY without funded cutover: PASS within CI test scope.
- SIMULATED Core DCA through shared admission: PASS within CI test scope.
- 1% per-order margin rejection: PASS within CI test scope.
- Shared Kill Switch rejection: PASS within CI test scope.
- Funded PaperLedger compatibility: PASS within the 144-test compatibility suite.
- Bootstrap compatibility and broader operational-proof workflow: still running at time of this report; NOT VERIFIED pending terminal run results.
- AI Trusted Admission Context / admitted leverage: NOT IMPLEMENTED / BLOCKED. AI must remain fail-closed until calibrated, provenance-bound leverage in the approved 1x–3x range is supplied.
- Runtime readiness / PAPER Ledger activation: BLOCKED / NOT VERIFIED.

## Broader regression and operational-proof reconciliation — 2026-11-14

### Exact-source workflow results

All runs below were triggered from branch `feature/core-operational-proof-20261112`.

- Core-First code-level operational proof: [run 43608805282](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43608805282), workflow `415832171`, job `132489067486`, event `push`, exact checkout SHA `a65025f517affbba46756d020150b4f6ddff31bb`, SUCCESS. All 25 workflow steps completed successfully, including disposable SQLite Core Runner integration, account-wide read-only/fail-closed risk snapshot, shared risk/PaperLedger regressions, and T1/T2 order-book HTTP integration.
- Core operational artifact: ID `14118523822`, name `core-first-code-operational-proof-43608805282`, 11,295 bytes, SHA-256 `bb8c022bd20b3bef4c7a19c3f66ceeb55bfaaf5dc0beee3aab4b49b12b0b84b9`, expires `2026-11-21T15:11:10Z`. Artifact payload has not been independently downloaded and hashed.
- Important sub-verdict limits from the successful Core workflow log: `CORE_RUNTIME_DECISION_CYCLE=NOT_VERIFIED` and `CORE_RUNTIME_ONE_SHOT=NOT_VERIFIED`. Therefore the workflow step/job success does not establish the complete Core decision-cycle/one-shot runtime contract. The workflow explicitly records `AI_EXECUTION_ENABLED=false`, no canonical T0 touch, no exchange credentials, no real orders, and no VPS/persistent runtime.
- Dual Ledger Bootstrap Contract: [run 43608805153](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43608805153), workflow `417325034`, job `132489066645`, exact checkout SHA `a65025f517affbba46756d020150b4f6ddff31bb`, FAILURE at full PaperLedger regression: 641 tests, 8 failures. Focused Bootstrap and D07 test steps before the full suite succeeded.
- The eight failures were stale test expectations, not a production-code regression: five daily-baseline persistence assertions expected 100 USDT although their shared fixture explicitly initializes the account and cutover at 1,400 USDT; three migration assertions expected only versions 1–10 although schema migration 11 (`simulated-utc-daily-baseline-rollover`) is applied by current source.
- Failed-run artifact preserved: ID `14119159143`, name `dual-ledger-bootstrap-proof-a65025f517affbba46756d020150b4f6ddff31bb`, 21,010 bytes, SHA-256 `e707e8d8a6102bed1a9306e4c7c6e0a568962d2ad8000a4e07ef08e98bb64e4c`, expires `2026-11-21T15:11:10Z`. Payload has not been independently downloaded and hashed.

### Test-only reconciliation

- Corrected daily-baseline assertions to match the actual 1,400 USDT fixture, preserving deliberate 100 USDT tamper/negative-test values.
- Updated migration-history expectations to include version 11 and its exact migration name.
- Test commits on the same branch: `43cb75b1814b01cde8c722023ebca288970477ef` (daily baseline assertions) and `b79f27aa9ea85b52370c6601d68ba1c8e6bd04ba` (migration v11 expectations).
- Final test blobs: `paper_execution/test_daily_baseline_persistence.py` = `fcbfaac46ad5cb4edbb90446ebf86cba60be0c0b`; `paper_execution/test_dual_ledger_migration_red.py` = `86b4c172d16feeb98fc60dd07656d19a37cb15e3`.
- Final exact-source Bootstrap rerun [43609479824](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43609479824), run number 138, event `push`, source SHA `b79f27aa9ea85b52370c6601d68ba1c8e6bd04ba`: PENDING at evidence update time. No PASS is claimed until terminal job/test results are inspected.

## Disposition

- SIMULATED Core ENTRY/DCA shared admission, 1% margin rejection, Kill Switch rejection: PASS within focused CI scope.
- Funded PaperLedger compatibility: PASS within the earlier 144-test suite on `a65025f517affbba46756d020150b4f6ddff31bb`; the broader 641-test suite exposed 8 stale test expectations, now corrected and pending exact-source rerun.
- Core-First operational-proof workflow: PASS at job level, with decision-cycle and one-shot sub-verdicts still NOT VERIFIED.
- Bootstrap full regression on corrected source: PENDING / NOT VERIFIED.
- AI Trusted Admission Context / admitted leverage: NOT IMPLEMENTED / BLOCKED; do not start AI implementation in this Core-First increment.
- Overall PAPER Ledger readiness: BLOCKED / NOT VERIFIED. Bootstrap and Runner activation remain NOT AUTHORIZED.

## Next step

Wait for run `43609479824` to reach a terminal state and inspect its job log and artifact metadata. If it passes, record the exact result and continue Core-First gap closure for the decision-cycle/one-shot sub-verdicts. Do not activate Bootstrap or Runner, use an operational database/VPS/T0, enable AI execution, or place live orders.


## Bootstrap regression follow-up — migration idempotency assertions

- Run [43609479824](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43609479824), exact SHA `b79f27aa9ea85b52370c6601d68ba1c8e6bd04ba`, completed FAILURE after 641 tests with only 2 failures. Both were migration idempotency assertions in `test_dual_ledger_migration_red.py` still expecting migration history through v10; actual schema correctly contains v11.
- Corrected only those two expected migration-history lists to include v11. No production source changes.
- Test-only commit: `b5822f148c451fbf786bcf24981f672fe9ca49b6`; test blob `6ec693cee45b8d2548a25b7f8cf3f24ca2522fa8`.
- Exact-source Bootstrap rerun [43610139453](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43610139453), source SHA `b5822f148c451fbf786bcf24981f672fe9ca49b6`, was QUEUED at this update. Result NOT VERIFIED.
- Status: daily-baseline expectations and migration-v11 history assertions corrected; full 641-test regression still BLOCKED / NOT VERIFIED pending run 43610139453.
- Next: inspect the queued run's terminal outcome and focused failing test log only. If PASS, proceed to the Core Decision Cycle / One-shot gap. Do not activate Bootstrap/Runner.


## Core one-shot CI verdict-count correction — 2026-11-14

- Read-only log inspection of Core operational proof run [43608805282](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43608805282), exact test source SHA `a65025f517affbba46756d020150b4f6ddff31bb`, showed `pipeline.test_core_runtime_one_shot` actually ran 15 tests and all 15 passed. The workflow's evidence step still expected `Ran 14 tests` and wrote `CORE_RUNTIME_ONE_SHOT_TESTS=14_PASS`, causing the verdict to be incorrectly recorded as NOT_VERIFIED.
- Corrected only the workflow's expected test count and evidence label to 15. No Core runner or trading logic changed.
- Workflow commit/source SHA: `65973afea7dfb87035494298ea42c6d88ca84b8c`; workflow blob `77118f2e0537f80a5c0c5ba16cdb9af3cf5ae043`.
- Exact-source rerun [43610239885](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43610239885), source SHA `65973afea7dfb87035494298ea42c6d88ca84b8c`, was QUEUED at this update. Corrected verdict NOT VERIFIED pending run completion.
- Status: one-shot unit suite 15/15 PASS on prior run; corrected workflow evidence logic committed; end-to-end CI verdict pending. No runtime activation.
- Next: reconcile Bootstrap run 43610139453 and Core proof run 43610239885; only after both terminal results proceed to any remaining Core gate.

## Final Bootstrap and Core operational proof reconciliation — 2026-11-14

- Bootstrap full regression run [43610139453](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43610139453), workflow job `132493202759`, exact checkout/source SHA `b5822f148c451fbf786bcf24981f672fe9ca49b6`: SUCCESS; full PaperLedger regression `Ran 641 tests`, `OK`. All focused Bootstrap/D07 checks and evidence upload steps also completed successfully.
- Bootstrap artifact ID `14119822199`, name `dual-ledger-bootstrap-proof-b5822f148c451fbf786bcf24981f672fe9ca49b6`, 19,880 bytes, SHA-256 `70a7dff446506481c0f04f0adf61b2e60357697d250578c76146c38f418c875b`, expires 2026-11-21T15:25:53Z. Digest is GitHub artifact metadata; payload not independently downloaded/hashed.
- Corrected Core operational proof run [43610239885](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43610239885), workflow job `132493515240`, exact checkout/source SHA `65973afea7dfb87035494298ea42c6d88ca84b8c`: SUCCESS. One-shot tests 15/15 PASS; workflow publisher now records `CORE_RUNTIME_DECISION_CYCLE=ONE_SHOT_TESTS_PASS` and `CORE_RUNTIME_ONE_SHOT=PASS`; Core preflight and adapter verdicts PASS. All workflow steps completed.
- Core artifact ID `14120465199`, name `core-first-code-operational-proof-43610239885`, 11,292 bytes, SHA-256 `e106525735e9679528603eaa7e5343060c052feef57cf088cd612b6cc8d6d102`, expires 2026-11-21T15:27:03Z. Digest is GitHub artifact metadata; payload not independently downloaded/hashed.
- Disposition: Bootstrap broad regression PASS within CI; Core code-level operational proof and Decision Cycle/One-shot verdicts PASS within CI. This does not prove VPS/persistent runtime readiness or authorize Bootstrap/Runner activation. AI Trusted Admission Context/admitted leverage remains NOT IMPLEMENTED / BLOCKED; AI remains out of scope under Core First. Overall PAPER Ledger runtime readiness remains BLOCKED / NOT VERIFIED pending separately authorized runtime readiness gates.
- Safety: disposable CI only; `AI_EXECUTION_ENABLED=false`; no operational DB, VPS, canonical T0, exchange credentials, AI execution, live orders or real trading.
- Next: identify and close the remaining Core-first paper-runtime readiness gap through a bounded read-only/design/test increment; do not activate Bootstrap/Runner or touch VPS/operational DB/T0.
