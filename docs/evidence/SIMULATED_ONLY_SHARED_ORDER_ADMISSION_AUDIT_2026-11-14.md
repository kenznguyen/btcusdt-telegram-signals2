# SIMULATED-only Shared Order Admission — Read-only Audit

Date: 2026-11-14
Branch: feature/core-operational-proof-20261112
Audited source SHA: 88ff9d51b845ca674a547bf27d479358a380bdcb
Current branch documentation HEAD at audit: 44b7fdd633e454776ececc8d779ba83c2d3ca19e

## Scope and safety

Read-only inspection of the simulated equity readiness path, shared PaperLedger order admission, margin reservations, risk limits, and AI admission API. No source, tests, workflow, database, VPS, T0, exchange, or runtime state was changed by this audit. No Bootstrap, Runner, AI execution, live order, or real trade was run.

## Findings

1. The simulated equity initializer intentionally creates immutable SIMULATED origin/seed/equity-origin state and initial risk state without funded-account cutover or funding evidence. The UTC daily-baseline rollover is now verified within the CI scope documented in SIMULATED_UTC_DAILY_BASELINE_ROLLOVER_V1_2026-11-14.md.

2. The read-only account risk snapshot recognizes a valid simulated origin and validates simulated daily-baseline provenance. Its readiness calculation permits a simulated account without funded cutover when the simulated provenance is valid.

3. The writer-side PaperLedger admission path is stricter. In PaperLedger._submit_scoped, exposure-increasing intents currently require a funded cutover row and complete funding provenance (cutover_row and funding_gap checks). A SIMULATED-only account has neither by design. Therefore, the existing simulated account can establish risk readiness and produce a read-only risk snapshot, but ENTRY/DCA order admission is still blocked by the funded-only gate. This is the primary integration gap.

4. The shared order-margin policy exists: risk_policy.ORDER_MARGIN_BUDGET_PCT is 0.01. The writer calculates admission_margin = equity * 1%, admission_notional = admission_margin * strategy leverage, rejects requested notional above that budget, and persists risk reservations. The dual-ledger contract suite includes a Core ENTRY/DCA test asserting reserved margin equals 1% of admission-time equity and reserved notional equals reserved margin times Core leverage. The inspected risk-limit suite also covers drawdown, daily loss, exposure, and missing configuration. This is test evidence for existing funded-path behavior, not proof that the SIMULATED-only path can admit orders or that all AI leverage cases are covered.

5. AI is independently evaluated by the API, but its candidate is deliberately not submitted while the Trusted Admission Context/admitted-leverage provider is absent. The API returns AI_ADMISSION_NOT_ESTABLISHED. The AI ledger factory requires an explicit admitted_leverage, and PaperLedger constrains AI leverage to 1x–3x. Do not remove this fail-closed gate or substitute a fixture/default leverage.

## Relevant source references

- risk_policy.py: ORDER_MARGIN_BUDGET_PCT = Decimal("0.01"); Core leverage policy.
- paper_execution/ledger.py: PaperLedger._submit_scoped; funded cutover/funding provenance gate; 1% per-order margin check and reservation creation.
- paper_execution/ledger.py: read_account_risk_snapshot; recognizes simulated origin and validates daily-baseline provenance.
- paper_execution/simulated_equity.py: verify_simulated_equity_origin; immutable simulated identity and current risk-state validation.
- paper_execution/simulated_daily_baseline.py: verify_simulated_daily_baseline_provenance.
- paper_execution/test_dual_ledger_red.py: test_entry_and_dca_reserve_one_percent_of_admission_time_equity_per_ledger.
- paper_execution/test_risk_limits.py: drawdown, daily-loss, exposure and missing-risk-limit tests.
- pipeline/api.py: ledger(strategy_id="AI_FREQAI", admitted_leverage=...) requires trusted leverage; /v1/paper/evaluate fails closed with AI_ADMISSION_NOT_ESTABLISHED for an AI candidate when dual-ledger mode is active.

## Recommended test-first contract for the next increment

Add isolated disposable-SQLite tests before changing writer code:

- SIMULATED Core ENTRY is admitted only when immutable origin, risk_ready, current mark freshness, daily-baseline hash chain, risk limits, and Kill Switch state all validate.
- SIMULATED DCA is admitted only under the same shared checks and existing DCA lifecycle constraints.
- Missing origin, missing prior-day mark, skipped UTC day, provenance tampering, stale mark, risk_ready=0, missing risk limits, Kill Switch, daily-loss breach, drawdown breach, and exposure breach all reject without mutation.
- The 1% per-order margin boundary is tested at, below, and above the limit; reservation amount, leverage, and equity basis are exact and atomic.
- Existing funded-account cutover/funding admission remains behaviorally unchanged.
- AI remains blocked until a separately trusted admission context supplies calibrated/provenance-bound leverage in the approved 1x–3x range; then its order must pass the same account-wide risk engine and 1% margin policy. No AI signal may bypass shared admission.

## Disposition

- Read-only audit: COMPLETE.
- SIMULATED-only writer admission: NOT IMPLEMENTED / NOT VERIFIED.
- Existing funded-path 1% reservation and risk-limit behavior: covered by existing tests, but this audit did not rerun those tests independently.
- AI Trusted Admission Context: NOT IMPLEMENTED / BLOCKED.
- Next permitted step: commit the test specification, run RED against current code, then implement only the additive SIMULATED-only writer admission path while preserving funded-account behavior. No runtime activation.
